import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home import run as gh_run, details as gh_details


class TestVolume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_speaker(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("SPEAKER", []).append(
            {
                "id": "spk-1",
                "names": ["Speaker"],
                "types": ["SPEAKER"],
                "traits": ["Volume"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "currentVolume", "value": 10},
                    {"name": "isMuted", "value": False},
                ],
            }
        )
        return "spk-1"

    def test_set_volume_level_requires_value(self):
        did = self._add_speaker()
        with self.assertRaises(Exception) as cm:
            gh_run(devices=[did], op="set_volume_level", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'set_volume_level' requires values.")

    def test_set_volume_level_type_and_range(self):
        did = self._add_speaker()
        with self.assertRaises(InvalidInputError) as cm:
            gh_run(devices=[did], op="set_volume_level", values=["abc"])  # type: ignore
        self.assertIn("Invalid input:", str(cm.exception))
        msg = str(cm.exception)
        self.assertTrue(("valid integer" in msg) or ("valid number" in msg))

        with self.assertRaises(InvalidInputError) as cm2:
            gh_run(devices=[did], op="set_volume_level", values=["101"])  # type: ignore
        self.assertIn("Invalid input:", str(cm2.exception))
        self.assertIn("less than or equal to 100", str(cm2.exception))

    def test_set_volume_level_sets_exact(self):
        did = self._add_speaker()
        gh_run(devices=[did], op="set_volume_level", values=["55"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 55)

    def test_set_volume_percentage_sets_exact(self):
        did = self._add_speaker()
        gh_run(devices=[did], op="set_volume_percentage", values=["35"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 35)

    def test_volume_up_down_require_values(self):
        did = self._add_speaker()
        with self.assertRaises(Exception) as cm1:
            gh_run(devices=[did], op="volume_up", values=[])  # type: ignore
        self.assertEqual(str(cm1.exception), "Invalid input: Command 'volume_up' requires values.")
        with self.assertRaises(Exception) as cm2:
            gh_run(devices=[did], op="volume_down", values=[])  # type: ignore
        self.assertEqual(str(cm2.exception), "Invalid input: Command 'volume_down' requires values.")

    def test_volume_up_down_clamps(self):
        did = self._add_speaker()
        gh_run(devices=[did], op="volume_up", values=["95"])  # -> 100
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 100)

        gh_run(devices=[did], op="volume_down", values=["100"])  # -> 0
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 0)

    def test_volume_up_down_percentage_and_ambiguous(self):
        did = self._add_speaker()
        gh_run(devices=[did], op="volume_up_percentage", values=["60"])  # -> 70
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 70)

        gh_run(devices=[did], op="volume_down_percentage", values=["80"])  # -> 0
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 0)

        gh_run(devices=[did], op="volume_up_ambiguous", values=["3"])  # +15 -> 15
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 15)

        gh_run(devices=[did], op="volume_down_ambiguous", values=["2"])  # -10 -> 5
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentVolume")
        self.assertEqual(st["value"], 5)

    def test_mute_unmute(self):
        did = self._add_speaker()
        gh_run(devices=[did], op="mute")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isMuted")
        self.assertTrue(st["value"])

        gh_run(devices=[did], op="unmute")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isMuted")
        self.assertFalse(st["value"]) 


