import logging
from celery import shared_task
from datetime import timedelta
from django.db import transaction, models
from django.utils import timezone
from .models import Footprint, Issue
from .utils import generate_fingerprint
from .registry import get_active_publishers, get_active_notifiers
from .settings import settings as insider_settings

logger = logging.getLogger(__name__)


@shared_task
@transaction.atomic
def save_footprint_task(footprint_data: dict):
    """
    Saves the collected footprint data in a background Celery task,
    respecting the configured DB_ALIAS.
    """

    db_alias = footprint_data.pop('__db_alias', None)
    if not db_alias:
        db_alias = 'default'

    try:
        footprint = Footprint.objects.using(db_alias).create(**footprint_data)

        if footprint.status_code >= 400:
            fingerprint_hash = generate_fingerprint(footprint_data)

            if footprint_data.get("exception_name"):
                title = f"{footprint_data["exception_name"]} at {footprint_data["request_path"]}"
            else:
                title = f"Error {footprint.status_code} at {footprint.request_path}"

            # Aggregate
            issue, created = Issue.objects.get_or_create(
                fingerprint=fingerprint_hash,
                defaults={'title': title}
            )

            footprint.issue = issue
            footprint.save(update_fields=['issue'])

            should_notify = False
            if created:
                should_notify = True

            # Recurring Issue
            else:
                # Notify if issue was already marked resolved.
                if issue.status == 'RESOLVED':
                    issue.status = 'OPEN'
                    issue.save(update_fields=['status'])
                    should_notify = True

                # Notify if the cooldown has passed.
                else:
                    time_since_notification = timezone.now() - issue.last_notified
                    if time_since_notification > timedelta(hours=insider_settings.COOLDOWN_HOURS):
                        should_notify = True

            if should_notify:
                issue.last_notified = timezone.now()
                issue.save(update_fields=["last_notified"])

                shared_context = {}
            
                if footprint.status_code == 500:
                    # Run publishers
                    for publisher in get_active_publishers():
                        try:
                            result = publisher.publish(footprint)
                            if result:
                                shared_context.update(result)
                        except Exception as e:
                            logger.error(f"INSIDER: Publisher failed: {e}")

                # Run Notifiers
                for notifier in get_active_notifiers():
                    try:
                        notifier.notify(footprint, context=shared_context)
                    except Exception as e:
                        logger.error(f"INSIDER: Notifier failed: {e}")

            else:
                # aggregate silently
                Issue.objects.filter(id=issue.id).update(
                    occurrence_count=models.F('occurrence_count') + 1,
                    last_seen=models.functions.Now()
                )            

    except Exception as e:
        logger.error(f"INSIDER: Critical error in save_footprint_task: {e}", exc_info=True)
