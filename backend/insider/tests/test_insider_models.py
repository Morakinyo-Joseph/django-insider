from django.test import TransactionTestCase
from django.core.management import call_command
from unittest.mock import patch
from insider.models import Footprint, Incidence, InsiderSetting
from insider.services.footprint import save_footprint
from insider.settings import settings as insider_settings

class InsiderModelsCreationTest(TransactionTestCase):
    # 1. Essential for multi-db tests with threads or manual transactions
    serialized_rollback = True
    databases = {'default', insider_settings.DB_ALIAS}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 2. Force the tables to exist on the specific insider DB alias
        print(f"\n🚜 Forcing migrations on '{insider_settings.DB_ALIAS}'...")
        call_command('migrate', 'insider', 'zero', database=insider_settings.DB_ALIAS, verbosity=0)
        call_command('migrate', 'insider', database=insider_settings.DB_ALIAS, verbosity=0)

    def setUp(self):
        self.footprint_data = {
            "request_id": "test-req-123",
            "request_user": "anonymous",
            "request_path": "/test",
            "request_method": "get",
            "status_code": 200,
            "response_time": 123.45,
            "db_query_count": 5,
        }
        self.incidence_data = {
            "fingerprint": "hash123",
            "title": "Test Error"
        }
        self.setting_data = {
            "key": "TEST_SETTING",
            "value": {"foo": "bar"},
            "field_type": "STRING",
            "description": "A test setting"
        }

    def test_incidence_creation(self):
        """Sanity check: Do tables exist?"""
        incidence = Incidence.objects.create(**self.incidence_data)
        self.assertIsNotNone(incidence.id)
        self.assertEqual(incidence.status, "OPEN")

    def test_footprint_creation_with_incidence(self):
        """Sanity check: Can we write footprints directly?"""
        incidence = Incidence.objects.create(**self.incidence_data)
        self.footprint_data["incidence"] = incidence
        footprint = Footprint.objects.create(**self.footprint_data)
        self.assertEqual(footprint.incidence, incidence)

    def test_insidersetting_creation(self):
        setting = InsiderSetting.objects.create(**self.setting_data)
        self.assertEqual(setting.key, "TEST_SETTING")

    # -------------------------------------------------------------------------
    # 🔧 CRITICAL FIX: Patch where the function is USED, not DEFINED.
    # If insider/services/footprint.py says: "from insider.utils import is_celery_available"
    # Then you MUST patch "insider.services.footprint.is_celery_available"
    # -------------------------------------------------------------------------
    @patch("insider.utils.is_celery_available", return_value=True) 
    @patch("insider.tasks.save_footprint_task.delay")
    def test_footprint_creation_via_celery(self, mock_delay, mock_is_celery):
        """Test Footprint creation path when Celery is available."""
        
        print(f"\n🧪 Testing Celery Path. DB Alias: {insider_settings.DB_ALIAS}")
        
        # This calls the service function
        save_footprint(self.footprint_data)
        
        # Assertions
        mock_delay.assert_called_once()
        args_passed = mock_delay.call_args[0][0]
        self.assertEqual(args_passed["request_path"], "/test")

    @patch("insider.utils.is_celery_available", return_value=False)
    def test_footprint_creation_via_thread(self, mock_is_celery):
        """Test Footprint creation path when Celery is NOT available (Thread fallback)."""
        
        print(f"\n🧪 Testing Thread Path.")
        
        # We patch Thread.start so we don't actually spawn a thread (which hides errors)
        # We just want to know if the code TRIED to start a thread.
        with patch("threading.Thread.start") as mock_thread_start:
            save_footprint(self.footprint_data)
            mock_thread_start.assert_called_once()

    def test_footprint_and_incidence_relationship(self):
        incidence = Incidence.objects.create(**self.incidence_data)
        footprint = Footprint.objects.create(**self.footprint_data)
        footprint.incidence = incidence
        footprint.save(update_fields=["incidence"])
        footprint.refresh_from_db()
        self.assertEqual(footprint.incidence, incidence)