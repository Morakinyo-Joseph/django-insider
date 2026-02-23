import sys
import logging
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from insider.utils import is_celery_available

logger = logging.getLogger(__name__)


class InsiderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insider'

    def ready(self):
        post_migrate.connect(sync_integrations_callback, sender=self)

        if any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'help', 'test']):
            return
        
        self._setup_celery_schedule()

    def _setup_celery_schedule(self):
        if not is_celery_available():
            return
        
        try:
            from django.conf import settings as django_settings
            from celery import current_app
            from celery.schedules import crontab
            
            insider_cfg = getattr(django_settings, "INSIDER", {})
            retention_days = insider_cfg.get("DATA_RETENTION_DAYS")

            if retention_days is None:
                retention_days = getattr(django_settings, "INSIDER_DATA_RETENTION_DAYS", 30)

            if retention_days > 0:
                current_app.conf.beat_schedule.update({
                    'insider-cleanup': {
                        'task': 'insider.tasks.cleanup_old_data',
                        'schedule': crontab(hour=3, minute=0) # Run daily at 3:00 AM
                    }
                })
        except ImportError:
            pass


def sync_integrations_callback(sender, **kwargs):
    """
    Signal receiver that runs ONLY after migrations are successfully applied.
    This prevents 'relation does not exist' errors during startup.   
    """
    if sender.name != 'insider':
        return
    
    db_alias = kwargs.get('using', 'default')

    try:
        from insider.registry import INTEGRATION_REGISTRY
        from insider.models import InsiderIntegration, InsiderIntegrationKey

        for identifier, integration_class in INTEGRATION_REGISTRY.items():
            logo = getattr(integration_class, 'logo_url', None)
            integration_obj, _ = InsiderIntegration.objects.using(db_alias).get_or_create(
                identifier=identifier,
                defaults={
                    'name': identifier.capitalize(),
                    'is_active': False,
                    'logo_url': logo,
                }
            )

            # existing logo change for future update
            if integration_obj.logo_url != logo:
                integration_obj.logo_url = logo
                integration_obj.save(using=db_alias)

            # Sync Configuration Keys
            defined_configs = getattr(integration_class, 'config_definition', {})
            
            for key, meta in defined_configs.items():
                InsiderIntegrationKey.objects.using(db_alias).get_or_create(
                    integration=integration_obj,
                    key=key,
                    defaults={
                        'label': meta.get('label', key),
                        'field_type': meta.get('type', 'STRING'),
                        'is_required': meta.get('required', False),
                        'value': meta.get('default', ''),
                        'help_text': meta.get('help_text', '')
                    }
                )
    except Exception as e:
        logger.warning(f"INSIDER: Integration Sync skipped (DB not ready): {e}")
