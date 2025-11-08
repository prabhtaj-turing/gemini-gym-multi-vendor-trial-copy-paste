# tests/test_users_settings_vacation.py
import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from .. import get_vacation_settings, update_vacation_settings, get_language_settings, update_language_settings


class TestUsersSettingsVacation(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()

    def test_get_update_vacation(self):
        vac_settings = get_vacation_settings("me")
        self.assertFalse(vac_settings.get("enableAutoReply"))
        updated = update_vacation_settings(
            "me", {"enableAutoReply": True, "responseBodyPlainText": "On vacation"}
        )
        self.assertTrue(updated.get("enableAutoReply"))
        self.assertEqual(updated.get("responseBodyPlainText"), "On vacation")

    def test_vacation_language_combined(self):
        # Update vacation settings
        updated_vac = update_vacation_settings(
            "me", {"enableAutoReply": True, "responseBodyPlainText": "On vacation"}
        )
        # Update language settings
        updated_lang = update_language_settings("me", {"displayLanguage": "es"})
        self.assertTrue(updated_vac.get("enableAutoReply"))
        self.assertEqual(updated_vac.get("responseBodyPlainText"), "On vacation")
        self.assertEqual(updated_lang.get("displayLanguage"), "es")


if __name__ == "__main__":
    unittest.main()
