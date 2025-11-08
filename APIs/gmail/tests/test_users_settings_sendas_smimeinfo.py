# tests/test_users_settings_sendas_smimeinfo.py
import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from .. import insert_send_as_smime_info, list_send_as_smime_info, get_send_as_smime_info, update_send_as_smime_info, patch_send_as_smime_info, delete_send_as_smime_info, set_default_send_as_smime_info, create_send_as_alias


class TestUsersSettingsSendAsSmimeInfo(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        # Create a send-as alias to use
        create_send_as_alias("me", {"sendAsEmail": "alias.jane.doe@gmail.com"})

    def test_smimeinfo_crud(self):
        smime_info = insert_send_as_smime_info(
            "me", "alias.jane.doe@gmail.com", {"encryptedKey": "AAA"}
        )
        self.assertIn("id", smime_info)

        all_smime = list_send_as_smime_info("me", "alias.jane.doe@gmail.com")
        self.assertEqual(len(all_smime["smimeInfo"]), 1)

        fetched = get_send_as_smime_info("me", "alias.jane.doe@gmail.com", smime_info["id"])
        self.assertEqual(fetched["encryptedKey"], "AAA")

        updated = update_send_as_smime_info(
            "me", "alias.jane.doe@gmail.com", smime_info["id"], {"encryptedKey": "BBB"}
        )
        self.assertEqual(updated["encryptedKey"], "BBB")

        patched = patch_send_as_smime_info(
            "me",
            "alias.jane.doe@gmail.com",
            smime_info["id"],
            {"encryptedKey": "PATCHED"},
        )
        self.assertEqual(patched["encryptedKey"], "PATCHED")

        defaulted = set_default_send_as_smime_info(
            "me", "alias.jane.doe@gmail.com", smime_info["id"]
        )
        self.assertTrue(defaulted.get("default", False))

        delete_send_as_smime_info("me", "alias.jane.doe@gmail.com", smime_info["id"])
        all_smime = list_send_as_smime_info("me", "alias.jane.doe@gmail.com")
        self.assertEqual(len(all_smime["smimeInfo"]), 0)

    def test_smimeinfo_patch(self):
        # Create another alias and test patching
        create_send_as_alias(
            "me", {"sendAsEmail": "alias.jack.smith@gmail.com"}
        )
        smime_info = insert_send_as_smime_info(
            "me", "alias.jack.smith@gmail.com", {"encryptedKey": "AAA"}
        )
        smime_id = smime_info["id"]
        patched = patch_send_as_smime_info(
            "me", "alias.jack.smith@gmail.com", smime_id, {"encryptedKey": "PATCHED"}
        )
        self.assertIsNotNone(patched)
        self.assertEqual(patched["encryptedKey"], "PATCHED")


if __name__ == "__main__":
    unittest.main()
