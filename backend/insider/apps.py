from django.apps import AppConfig
from insider.utils import is_celery_available


class InsiderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insider'

    def ready(self):
        if not is_celery_available():
            return
        
        try:
            from django.conf import settings as django_settings
            from celery import current_app
            from celery.schedules import crontab
            
            # Check Django settings directly to avoid triggering a database query \
            # (lazy load) during app initialization, which causes a RuntimeWarning.
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

