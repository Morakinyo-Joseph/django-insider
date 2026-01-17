from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from insider.models import Footprint, Incidence
from insider.tasks import cleanup_old_data
from insider.settings import settings as insider_settings
from celery import current_app

class CleanupTaskTest(TestCase):
    databases = {'default', insider_settings.DB_ALIAS}
    
    def setUp(self):
        self.retention_days = insider_settings.DATA_RETENTION_DAYS
        if self.retention_days <= 0:
            self.retention_days = 30
            
    def test_cleanup_deletes_only_old_records(self):
        """
        Verify that records older than the cutoff are deleted,
        and recent records are preserved.
        """
        
        now = timezone.now()
        old_date = now - timedelta(days=self.retention_days + 5) # 5 days older than limit

        fresh_fp = Footprint.objects.create(
            request_path="/fresh",
            request_method="GET"
        )
        expired_fp = Footprint.objects.create(
            request_path="/expired",
            request_method="GET"
        )
        Footprint.objects.filter(id=expired_fp.id) \
                         .update(created_at=old_date)

        expired_inc = Incidence.objects.create(
            title="Old Error",
            fingerprint="old_hash"
        )
        Incidence.objects.filter(id=expired_inc.id) \
                         .update(created_at=old_date)

        result = cleanup_old_data()
        print(result)
        
        self.assertTrue(
            Footprint.objects.filter(id=fresh_fp.id).exists(), 
            "FRESH data was accidentally deleted!"
        )

        self.assertFalse(
            Footprint.objects.filter(id=expired_fp.id).exists(), 
            "OLD Footprint was NOT deleted."
        )
        self.assertFalse(
            Incidence.objects.filter(id=expired_inc.id).exists(), 
            "OLD Incidence was NOT deleted."
        )

    def test_celery_schedule_registration(self):
        """
        Verify that the task registers in Celery Beat IF Celery is available.
        """

        # Force the 'ready' logic to run manually
        from django.apps import apps
        
        app_config = apps.get_app_config('insider')
        
        import insider.apps
        original_check = insider.apps.is_celery_available
        insider.apps.is_celery_available = lambda: True
        
        try:
            app_config.ready()
            
            schedule = current_app.conf.beat_schedule
            self.assertIn(
                'insider-cleanup', 
                schedule, 
                "Task failed to register even when Celery was 'available'."
            )
            
            # Check the schedule time
            from celery.schedules import crontab
            expected_schedule = schedule['insider-cleanup']['schedule']
            self.assertEqual(expected_schedule, crontab(hour=3, minute=0))
            
        finally:
            insider.apps.is_celery_available = original_check