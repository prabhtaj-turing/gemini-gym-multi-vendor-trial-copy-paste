import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home import run as gh_run, details as gh_details


class TestLockUnlockAndModesMisc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_lock(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("LOCK", []).append(
            {
                "id": "lock-1",
                "names": ["Door Lock"],
                "types": ["LOCK"],
                "traits": ["LockUnlock"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "isLocked", "value": False}
                ],
            }
        )
        return "lock-1"

    def test_lock_unlock(self):
        did = self._add_lock()
        gh_run(devices=[did], op="lock")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isLocked")
        self.assertTrue(st["value"])

        gh_run(devices=[did], op="unlock")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isLocked")
        self.assertFalse(st["value"]) 


