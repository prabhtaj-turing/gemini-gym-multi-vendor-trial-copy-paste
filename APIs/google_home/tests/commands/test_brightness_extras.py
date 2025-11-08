import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home import run as gh_run, details as gh_details


class TestBrightnessExtras(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_light(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("LIGHT", []).append(
            {
                "id": "light-1",
                "names": ["Light"],
                "types": ["LIGHT"],
                "traits": ["Brightness"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "brightness", "value": 0.5}
                ],
            }
        )
        return "light-1"

    def test_brighter_ambiguous_requires_value(self):
        did = self._add_light()
        with self.assertRaises(Exception) as cm:
            gh_run(devices=[did], op="brighter_ambiguous", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'brighter_ambiguous' requires values.")

    def test_brighter_ambiguous_increases_and_clamps(self):
        did = self._add_light()
        gh_run(devices=[did], op="brighter_ambiguous", values=["2"])  # +0.16
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "brightness")
        self.assertAlmostEqual(st["value"], 0.66, places=2)

        gh_run(devices=[did], op="brighter_ambiguous", values=["5"])  # +0.40 => clamp 1.0
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "brightness")
        self.assertEqual(st["value"], 1.0)

    def test_brighter_percentage_increases(self):
        did = self._add_light()
        gh_run(devices=[did], op="brighter_percentage", values=["10"])  # +0.10
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "brightness")
        self.assertAlmostEqual(st["value"], 0.6, places=2)

    def test_dimmer_ambiguous_decreases_and_clamps(self):
        did = self._add_light()
        gh_run(devices=[did], op="dimmer_ambiguous", values=["5"])  # -0.40 -> 0.10
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "brightness")
        self.assertAlmostEqual(st["value"], 0.10, places=2)

        gh_run(devices=[did], op="dimmer_ambiguous", values=["5"])  # -0.40 -> clamp 0.0
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "brightness")
        self.assertEqual(st["value"], 0.0)

    def test_dimmer_percentage_decreases(self):
        did = self._add_light()
        gh_run(devices=[did], op="dimmer_percentage", values=["10"])  # -0.10
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "brightness")
        self.assertAlmostEqual(st["value"], 0.4, places=2)

    def test_percentage_invalid_range_and_type(self):
        did = self._add_light()
        with self.assertRaises(InvalidInputError) as cm:
            gh_run(devices=[did], op="brighter_percentage", values=["200"])  # type: ignore
        self.assertIn("Invalid input:", str(cm.exception))
        self.assertIn("less than or equal to 100", str(cm.exception))

        with self.assertRaises(InvalidInputError) as cm2:
            gh_run(devices=[did], op="dimmer_percentage", values=["abc"])  # type: ignore
        self.assertIn("Invalid input:", str(cm2.exception))
        self.assertIn("valid number", str(cm2.exception))


