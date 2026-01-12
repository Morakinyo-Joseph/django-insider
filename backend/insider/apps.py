import logging
from django.apps import AppConfig
from django.conf import settings as django_settings
from insider.utils import is_celery_available

logger = logging.getLogger(__name__)


class InsiderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insider'

    def ready(self):
        if not is_celery_available():
            return

        try:
            from celery import current_app
            from celery.schedules import crontab
            from .settings import settings as insider_settings
            
            try:
                hour, minute = insider_settings.DAILY_REPORT_TIME.split(':')
                hour = int(hour)
                minute = int(minute)
            except ValueError:
                hour, minute = 9, 0

            
            # DATA CLEANUP (Run at 3 AM daily)
            if insider_settings.DATA_RETENTION_DAYS > 0:
                current_app.conf.beat_schedule['insider-daily-cleanup'] = {
                    'task': 'insider.tasks.cleanup_old_data_task',
                    'schedule': crontab(hour=3, minute=0),
                }

            # DAILY REPORT (Run at configured time)
            if insider_settings.ENABLE_DAILY_REPORT:
                current_app.conf.beat_schedule['insider-daily-report'] = {
                    'task': 'insider.tasks.daily_report_task',
                    'schedule': crontab(hour=hour, minute=minute),
                }

        except ImportError:
            pass

        except Exception as e:
            logger.error(f"INSIDER: Failed to register periodic tasks: {e}")