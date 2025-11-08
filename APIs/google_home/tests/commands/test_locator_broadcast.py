import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home import run as gh_run, details as gh_details


class TestLocatorBroadcast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_phone(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("SWITCH", []).append(
            {
                "id": "phone-1",
                "names": ["Phone"],
                "types": ["SWITCH"],
                "traits": ["Locator", "Broadcast"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "isRinging", "value": False}
                ],
            }
        )
        return "phone-1"

    def test_find_device_sets_ringing(self):
        did = self._add_phone()
        gh_run(devices=[did], op="find_device")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isRinging")
        self.assertTrue(st["value"])

    def test_silence_ringing_sets_false(self):
        did = self._add_phone()
        gh_run(devices=[did], op="silence_ringing")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isRinging")
        self.assertFalse(st["value"])

    def test_broadcast_requires_message(self):
        did = self._add_phone()
        with self.assertRaises(Exception) as cm:
            gh_run(devices=[did], op="broadcast", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'broadcast' requires values.")

        with self.assertRaises(InvalidInputError) as cm2:
            gh_run(devices=[did], op="broadcast", values=[""])  # type: ignore
        self.assertIn("Invalid input:", str(cm2.exception))
        self.assertIn("at least 1 character", str(cm2.exception))


