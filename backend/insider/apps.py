from django.apps import AppConfig
from insider.utils import is_celery_available


class InsiderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insider'

    def ready(self):
        if not is_celery_available():
            return
        
        try:
            from insider.settings import settings
            from celery import current_app
            from celery.schedules import crontab
            
            if settings.DATA_RETENTION_DAYS > 0:
                current_app.conf.beat_schedule.update({
                    'insider-cleanup': {
                        'task': 'insider.tasks.cleanup_old_data',
                        'schedule': crontab(hour=3, minute=0) # Run daily at 3:00 AM
                    }
                })
        except ImportError:
            pass

