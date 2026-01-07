import logging
from celery import shared_task
from django.db import transaction, models
from .models import Footprint, Issue
from .utils import generate_fingerprint
from .registry import get_active_publishers, get_active_notifiers

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

            if not created:
                Issue.objects.filter(id=issue.id).update(
                    occurrence_count=models.F('occurrence_count') + 1,
                    last_seen=models.functions.Now()
                )
                return
            
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


    except Exception as e:
        logger.error(f"INSIDER: Critical error in save_footprint_task: {e}", exc_info=True)
