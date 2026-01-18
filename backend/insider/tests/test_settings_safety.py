from unittest import mock
from rest_framework.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from insider.models import InsiderSetting
from insider.api.views import SettingsViewSet
from insider.api.serializers import InsiderSettingSerializer
from insider.settings import settings as insider_settings


class SettingsSafetyTest(TestCase):
    databases = {'default', insider_settings.DB_ALIAS}

    def setUp(self):
        self.factory = RequestFactory()
        self.view = SettingsViewSet()

        InsiderSetting.objects.all().delete()

    def test_seeding_respects_user_config(self):
        """
        CRITICAL TEST: Ensures that when the dashboard first loads,
        it uses the ACTIVE configuration (from settings.py), not just 
        hardcoded package defaults.
        """
        
        # Pick a setting and give it a non-default value (Simulating settings.py)
        test_key = "MAX_RESPONSE_LENGTH"
        fake_user_value = 9999
        
        with mock.patch.object(insider_settings, test_key, fake_user_value):
            
            # Simulate the Dashboard 'List' request (which triggers seeding)
            request = self.factory.get('/insider/settings/')
            self.view.request = request
            self.view.format_kwarg = None
            self.view.list(request)
            
            # 4. Verify the Database has the USER's value, not the DEFAULT
            saved_setting = InsiderSetting.objects.get(key=test_key)
            
            self.assertEqual(
                saved_setting.value, 
                fake_user_value,
                f"Seeding Poisoning detected! Expected user value {fake_user_value}, but got default {saved_setting.value}"
            )

    def test_db_alias_is_hidden_from_api(self):
        """
        Ensures DB_ALIAS is excluded from the API list to prevent users
        from changing the database location via the UI.
        """
        
        InsiderSetting.objects.create(key="DB_ALIAS", value="insider_db", field_type="STRING")
        InsiderSetting.objects.create(key="OTHER_SETTING", value="foo", field_type="STRING")
        
        queryset = self.view.get_queryset()
        
        self.assertFalse(
            queryset.filter(key="DB_ALIAS").exists(),
            "Security Flaw: DB_ALIAS is visible in the API! Users could break the app."
        )
        
        # Assert other settings are visible
        self.assertTrue(queryset.filter(key="OTHER_SETTING").exists())

    def test_db_alias_is_write_protected(self):
        """
        Ensures that even if a user tries to force-update DB_ALIAS,
        the backend raises a Validation Error.
        """
        
        setting = InsiderSetting(key="DB_ALIAS", value="old_val", field_type="STRING")
        
        data = {'key': 'DB_ALIAS', 'value': 'malicious_new_db'}
        
        serializer = InsiderSettingSerializer(instance=setting, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Attempt to run perform_update
        with self.assertRaises(ValidationError) as cm:
            self.view.perform_update(serializer)
            
        self.assertIn("cannot be changed at runtime", str(cm.exception))