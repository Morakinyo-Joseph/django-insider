from django.test import TestCase
from django.utils import timezone
from django.core import mail
from datetime import timedelta
from unittest.mock import patch

from insider.models import Footprint
from insider.tasks import cleanup_old_data_task, daily_report_task
from insider.settings import settings as insider_settings

class TaskTests(TestCase):
    
    def test_cleanup_deletes_old_data(self):
        # Setup: Ensure retention is 30 days
        insider_settings.DATA_RETENTION_DAYS = 30
        
        now = timezone.now()
        
        # Create Data: 1 Fresh, 1 Old
        fresh = Footprint.objects.create(request_path="/fresh", status_code=200)
        
        old = Footprint.objects.create(request_path="/old", status_code=200)
        old.created_at = now - timedelta(days=31) # 31 days old
        old.save()

        # Action
        cleanup_old_data_task()

        # Assert
        self.assertTrue(Footprint.objects.filter(id=fresh.id).exists())
        self.assertFalse(Footprint.objects.filter(id=old.id).exists())

    def test_daily_report_sends_email(self):
        # Setup: Enable reporting
        insider_settings.ENABLE_DAILY_REPORT = True
        insider_settings.DAILY_REPORT_EMAILS = ["admin@test.com"]

        # Action
        msg = daily_report_task()

        # Assert logic
        self.assertIn("Report sent", msg)
        
        # Assert Email Sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Daily Stability Report", mail.outbox[0].subject)
        self.assertIn("admin@test.com", mail.outbox[0].to)