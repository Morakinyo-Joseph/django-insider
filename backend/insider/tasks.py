import logging
from celery import shared_task
from celery.schedules import crontab
from datetime import timedelta
from django.db import transaction, models
from django.utils import timezone
from .models import Footprint, Incidence
from .utils import generate_fingerprint
from .registry import get_active_publishers, get_active_notifiers
from .settings import settings as insider_settings
from .services.email import EmailManager

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
            incidence, created = Incidence.objects.get_or_create(
                fingerprint=fingerprint_hash,
                defaults={'title': title}
            )

            footprint.incidence = incidence
            footprint.save(update_fields=['incidence'])

            # update count and last seen for this incidence instance
            if not created:
                Incidence.objects.filter(id=incidence.id).update(
                    occurrence_count=models.F('occurrence_count') + 1,
                    last_seen=timezone.now()
                )

                incidence.refresh_from_db()

            should_notify = False

            if created:
                should_notify = True

            # Recurring Incidence
            else:
                # Notify if incidence was already marked resolved.
                if incidence.status == 'RESOLVED':
                    incidence.status = 'OPEN'
                    incidence.save(update_fields=['status'])
                    should_notify = True

                # Notify if the cooldown has passed.
                else:
                    time_since_notification = timezone.now() - incidence.last_notified
                    if time_since_notification > timedelta(hours=insider_settings.COOLDOWN_HOURS):
                        should_notify = True

            if should_notify:
                incidence.last_notified = timezone.now()
                incidence.save(update_fields=["last_notified"])

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


@shared_task
def daily_report_task():
    """
    Generates statistics for the last 24 hours and sends an email.
    """

    if not insider_settings.ENABLE_DAILY_REPORT:
        return "Daily Report Disabled"

    now = timezone.now()
    yesterday = now - timedelta(hours=24)
    
    # Gather Stats
    new_incidences = Incidence.objects.filter(created_at__gte=yesterday).count()
    resolved_incidences = Incidence.objects.filter(status='RESOLVED', updated_at__gte=yesterday).count()
    
    footprints = Footprint.objects.filter(created_at__gte=yesterday)
    errors_500 = footprints.filter(status_code__gte=500).count()
    
    top_offenders_qs = Incidence.objects.filter(
        footprint__created_at__gte=yesterday
    ).annotate(
        daily_count=models.Count('footprint')
    ).order_by('-daily_count')[:5]

    top_offenders = [
        {'title': inc.title, 'count': inc.daily_count} 
        for inc in top_offenders_qs
    ]

    context = {
        'date': now.strftime('%Y-%m-%d'),
        'new_issues': new_incidences,
        'resolved': resolved_incidences,
        'errors_500': errors_500,
        'top_offenders': top_offenders
    }

    # Send Email
    manager = EmailManager()
    manager.send_daily_report(context)
    
    return f"Report sent to {len(manager.recipients)} recipients"


@shared_task
def cleanup_old_data_task():
    """
    Deletes footprints older than the configured retention days.
    """

    days = insider_settings.DATA_RETENTION_DAYS
    if days <= 0:
        return "Cleanup Disabled (Days=0)"

    cutoff = timezone.now() - timedelta(days=days)
    
    count, _ = Footprint.objects.filter(created_at__lt=cutoff).delete()
    
    # NOTE: Clean up Incidences that have 0 footprints left?
    
    return f"Cleaned up {count} old footprint records."