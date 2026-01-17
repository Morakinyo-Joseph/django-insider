import logging
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from .models import Footprint, Incidence
from .settings import settings as insider_settings
from insider.services.footprint import save_footprint

logger = logging.getLogger(__name__)


@shared_task(
    name="insider.save_footprint_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def save_footprint_task(footprint_data: dict):
    return save_footprint(footprint_data)


@shared_task
def cleanup_old_data():
    """
    Deletes footprints older than the configured retention days.
    """

    days = insider_settings.DATA_RETENTION_DAYS
    if days <= 0:
        return "Cleanup Disabled (Days=0)"

    cutoff_date = timezone.now() - timedelta(days=days)
    
    footprint_deleted, _ = Footprint.objects.filter(created_at__lt=cutoff_date).delete()
    incidences_deleted, _ = Incidence.objects.filter(created_at__lt=cutoff_date).delete()    

    return (
        f"INSIDER: Cleanup Completed -  Deleted {footprint_deleted} footprints" \
        f" and {incidences_deleted} incidences older than {days} days."
    )