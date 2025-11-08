import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home import run as gh_run, details as gh_details


class TestClose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_blinds(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("BLINDS", []).append(
            {
                "id": "blind-2",
                "names": ["Blinds 2"],
                "types": ["BLINDS"],
                "traits": ["OpenClose"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "openPercent", "value": 75.0}
                ],
            }
        )
        return "blind-2"

    def test_close_sets_0(self):
        did = self._add_blinds()
        gh_run(devices=[did], op="close")  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "openPercent")
        self.assertEqual(st["value"], 0)

    def test_close_percent_requires_value(self):
        did = self._add_blinds()
        with self.assertRaises(Exception) as cm:
            gh_run(devices=[did], op="close_percent", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'close_percent' requires values.")

    def test_close_percent_decreases_and_clamps_0(self):
        did = self._add_blinds()
        gh_run(devices=[did], op="close_percent", values=["50"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "openPercent")
        self.assertEqual(st["value"], 25)

        gh_run(devices=[did], op="close_percent", values=["50"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "openPercent")
        self.assertEqual(st["value"], 0)

    def test_close_percent_invalid_range_raises_invalidinputerror(self):
        did = self._add_blinds()
        with self.assertRaises(InvalidInputError) as cm:
            gh_run(devices=[did], op="close_percent", values=["150"])  # type: ignore
        self.assertIn("Invalid input:", str(cm.exception))
        self.assertIn("less than or equal to 100", str(cm.exception))

    def test_close_percent_type_error_raises_invalidinputerror(self):
        did = self._add_blinds()
        with self.assertRaises(InvalidInputError) as cm:
            gh_run(devices=[did], op="close_percent", values=["abc"])  # type: ignore
        self.assertIn("Invalid input:", str(cm.exception))
        self.assertIn("valid number", str(cm.exception))

    def test_close_percent_absolute_sets_exact_value(self):
        did = self._add_blinds()
        gh_run(devices=[did], op="close_percent_absolute", values=["40"])  # type: ignore
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "openPercent")
        self.assertEqual(st["value"], 40)

    def test_close_percent_absolute_invalid_range(self):
        did = self._add_blinds()
        with self.assertRaises(InvalidInputError) as cm:
            gh_run(devices=[did], op="close_percent_absolute", values=["-1"])  # type: ignore
        self.assertIn("Invalid input:", str(cm.exception))
        self.assertIn("greater than or equal to 0", str(cm.exception))

    def test_close_ambiguous_amount_requires_value(self):
        did = self._add_blinds()
        with self.assertRaises(Exception) as cm:
            gh_run(devices=[did], op="close_ambiguous_amount", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'close_ambiguous_amount' requires values.")

    def test_close_ambiguous_amount_zero_invalid(self):
        did = self._add_blinds()
        with self.assertRaises(InvalidInputError) as cm:
            gh_run(devices=[did], op="close_ambiguous_amount", values=["0"])  # type: ignore
        self.assertIn("Invalid input:", str(cm.exception))
        self.assertIn("Ambiguous amount cannot be zero.", str(cm.exception))

    def test_close_ambiguous_amount_steps_and_clamps(self):
        did = self._add_blinds()
        gh_run(devices=[did], op="close_ambiguous_amount", values=["3"])  # -45 => 30
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "openPercent")
        self.assertEqual(st["value"], 30)

        gh_run(devices=[did], op="close_ambiguous_amount", values=["3"])  # -45 => clamp 0
        states = json.loads(gh_details(devices=[did])["devices_info"])[did]  # type: ignore
        st = next(s for s in states if s["name"] == "openPercent")
        self.assertEqual(st["value"], 0)


