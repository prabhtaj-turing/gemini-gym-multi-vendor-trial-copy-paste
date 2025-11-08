import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home import run as gh_run, details as gh_details


class TestFanSpeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_fan(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("FAN", []).append(
            {
                "id": "fan-1",
                "names": ["Fan"],
                "types": ["FAN"],
                "traits": ["FanSpeed"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "fanSpeed", "value": 0}
                ],
            }
        )
        return "fan-1"

    def test_set_fan_speed_text_requires_valid_value(self):
        did = self._add_fan()
        with self.assertRaises(InvalidInputError) as cm:
            gh_run(devices=[did], op="set_fan_speed", values=["fast"])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid fan speed. Must be one of: high, low, medium.")

    def test_set_fan_speed_text_sets_value(self):
        did = self._add_fan()
        gh_run(devices=[did], op="set_fan_speed", values=["medium"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "fanSpeed")
        self.assertEqual(st["value"], 66)

    def test_set_fan_speed_percentage_sets_exact(self):
        did = self._add_fan()
        gh_run(devices=[did], op="set_fan_speed_percentage", values=["35"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "fanSpeed")
        self.assertEqual(st["value"], 35)

    def test_fan_up_down_percentage_clamps(self):
        did = self._add_fan()
        gh_run(devices=[did], op="fan_up_percentage", values=["80"])  # -> 80
        gh_run(devices=[did], op="fan_up_percentage", values=["50"])  # -> 100
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "fanSpeed")
        self.assertEqual(st["value"], 100)

        gh_run(devices=[did], op="fan_down_percentage", values=["100"])  # -> 0
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "fanSpeed")
        self.assertEqual(st["value"], 0)

    def test_fan_up_down_ambiguous_steps(self):
        did = self._add_fan()
        gh_run(devices=[did], op="fan_up_ambiguous", values=["3"])  # +30
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "fanSpeed")
        self.assertEqual(st["value"], 30)
        gh_run(devices=[did], op="fan_down_ambiguous", values=["2"])  # -20 -> 10
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "fanSpeed")
        self.assertEqual(st["value"], 10)


