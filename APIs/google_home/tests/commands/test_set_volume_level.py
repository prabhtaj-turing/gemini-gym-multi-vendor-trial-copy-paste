import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home import run as gh_run, details as gh_details


class TestSetVolumeLevel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_set_volume_level_speaker(self):
        # Add a speaker with Volume trait
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("SPEAKER", []).append(
            {
                "id": "sp-1",
                "names": ["Speaker"],
                "types": ["SPEAKER"],
                "traits": ["Volume"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "currentVolume", "value": 0},
                    {"name": "isMuted", "value": False},
                ],
            }
        )
        gh_run(devices=["sp-1"], op="set_volume_level", values=["30"])  # type: ignore
        devices_info = json.loads(gh_details(devices=["sp-1"])["devices_info"])  # type: ignore
        states = devices_info["sp-1"]
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 30)

    def test_set_volume_level_requires_value(self):
        # Add a speaker with Volume trait
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("SPEAKER", []).append(
            {
                "id": "sp-2",
                "names": ["Speaker 2"],
                "types": ["SPEAKER"],
                "traits": ["Volume"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "currentVolume", "value": 0},
                    {"name": "isMuted", "value": False},
                ],
            }
        )
        with self.assertRaises(Exception) as cm:
            gh_run(devices=["sp-2"], op="set_volume_level", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'set_volume_level' requires values.")


