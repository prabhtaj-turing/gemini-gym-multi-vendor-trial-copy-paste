import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home import run as gh_run, details as gh_details


class TestChangeColorAndDock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_light(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("LIGHT", []).append(
            {
                "id": "light-2",
                "names": ["Light 2"],
                "types": ["LIGHT"],
                "traits": ["ColorSetting"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "color", "value": "white"}
                ],
            }
        )
        return "light-2"

    def _add_vacuum(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("VACUUM", []).append(
            {
                "id": "vac-2",
                "names": ["Vacuum 2"],
                "types": ["VACUUM"],
                "traits": ["Dock"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "isDocked", "value": False}
                ],
            }
        )
        return "vac-2"

    def test_change_color_sets_slug(self):
        did = self._add_light()
        gh_run(devices=[did], op="change_color", values=["blue"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "color")
        self.assertEqual(st["value"], "blue")

    def test_change_color_requires_value(self):
        did = self._add_light()
        with self.assertRaises(Exception) as cm:
            gh_run(devices=[did], op="change_color", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'change_color' requires values.")

    def test_dock_sets_true(self):
        did = self._add_vacuum()
        gh_run(devices=[did], op="dock")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "isDocked")
        self.assertTrue(st["value"]) 


