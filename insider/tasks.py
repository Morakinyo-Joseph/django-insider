import logging
from celery import shared_task
from .models import Footprint
from django.db import transaction


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
        Footprint.objects.using(db_alias).create(**footprint_data)
    except Exception as e:
        logger = logging.getLogger('insider')
        logger.error(f"Failed to save Footprint in background task: {e}", exc_info=True)
