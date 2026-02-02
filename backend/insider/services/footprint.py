import logging
from datetime import timedelta
from django.db import models
from django.utils import timezone
from insider.models import Footprint, Incidence
from insider.utils import generate_fingerprint
from insider.registry import get_active_integrations, INTEGRATION_REGISTRY
from insider.settings import settings as insider_settings

logger = logging.getLogger(__name__)


def save_footprint(footprint_data: dict):
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
                title = f"{footprint_data['exception_name']} at {footprint_data['request_path']}"
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

                active_integrations = get_active_integrations()
                
                for integration in active_integrations:
                    try:
                        IntegrationClass = INTEGRATION_REGISTRY.get(integration.identifier)
                        
                        if not IntegrationClass:
                            logger.warning(f"INSIDER: Found active integration '{integration.identifier}' in DB but no code class found.")
                            continue

                        integration_instance = IntegrationClass(db_instance=integration)
                        result = integration_instance.run(footprint, shared_context)
                        
                        if result and isinstance(result, dict):
                            shared_context.update(result)
                                
                    except Exception as e:
                        logger.error(f"INSIDER: Integration '{integration.identifier}' failed: {e}")
            
    except Exception as e:
        logger.error(f"INSIDER: Critical error in save_footprint_task: {e}", exc_info=True)
