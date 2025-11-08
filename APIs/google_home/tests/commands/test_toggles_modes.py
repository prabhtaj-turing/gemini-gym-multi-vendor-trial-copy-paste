import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home import run as gh_run, details as gh_details


class TestTogglesAndModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_device_with_toggles_modes(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("LIGHT", []).append(
            {
                "id": "light-3",
                "names": ["Light 3"],
                "types": ["LIGHT"],
                "traits": ["Toggles", "Modes"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [
                    {"id": "nightLight", "names": ["Night Light"], "settings": []},
                    {"id": "lightEffect", "names": ["Light Effect"], "settings": [
                        {"id": "sleep", "names": ["Sleep"]},
                        {"id": "wake", "names": ["Wake"]},
                    ]},
                ],
                "device_state": [
                    {"name": "activeToggles", "value": {}},
                    {"name": "currentModes", "value": {}},
                ],
            }
        )
        return "light-3"

    def test_toggle_setting_sets_bool(self):
        did = self._add_device_with_toggles_modes()
        gh_run(devices=[did], op="toggle_setting", values=["nightLight", "true"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "activeToggles")
        self.assertEqual(st["value"], {"nightLight": True})

    def test_set_mode_validates_mode_and_value(self):
        did = self._add_device_with_toggles_modes()
        with self.assertRaises(InvalidInputError) as cm1:
            gh_run(devices=[did], op="set_mode", values=["badMode", "sleep"])  # type: ignore
        self.assertIn("Invalid input:", str(cm1.exception))
        self.assertIn("Invalid mode. Must be one of", str(cm1.exception))

        with self.assertRaises(InvalidInputError) as cm2:
            gh_run(devices=[did], op="set_mode", values=["lightEffect", "unknown"])  # type: ignore
        self.assertIn("Invalid input:", str(cm2.exception))
        self.assertIn("Invalid mode. Must be one of", str(cm2.exception))

        gh_run(devices=[did], op="set_mode", values=["lightEffect", "sleep"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "currentModes")
        self.assertEqual(st["value"], {"lightEffect": "sleep"})


