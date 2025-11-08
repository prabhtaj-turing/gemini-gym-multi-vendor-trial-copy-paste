import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestSetTemperature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _get_device_state(self, device_id: str):
        devices_info = json.loads(gh_details(devices=[device_id])["devices_info"])  # type: ignore
        return devices_info[device_id]

    def test_set_temperature_with_unit_c(self):
        gh_run(devices=["002"], op="set_temperature", values=["22.0", "C"])  # type: ignore
        state = self._get_device_state("002")
        tset = next(s for s in state if s["name"] == "thermostatTemperatureSetpoint")
        # Unit should be preserved from DB (default F); value converted accordingly
        self.assertEqual(tset["unit"], "F")
        self.assertAlmostEqual(tset["value"], (22.0 * 9.0 / 5.0) + 32.0, places=3)  # 71.6 F
        self.assertIn("value_metric", tset)
        self.assertIn("value_imperial", tset)

    def test_set_temperature_with_unit_f(self):
        gh_run(devices=["002"], op="set_temperature", values=["70", "F"])  # type: ignore
        state = self._get_device_state("002")
        tset = next(s for s in state if s["name"] == "thermostatTemperatureSetpoint")
        # Unit should be preserved from DB
        self.assertAlmostEqual(tset["value"], 70.0, places=3)
        self.assertIn("value_metric", tset)
        self.assertIn("value_imperial", tset)

    def test_change_relative_temperature_respects_existing_unit(self):
        gh_run(devices=["002"], op="set_temperature_celsius", values=["20"])  # type: ignore
        gh_run(devices=["002"], op="change_relative_temperature", values=["1", "F"])  # type: ignore
        state = self._get_device_state("002")
        tset = next(s for s in state if s["name"] == "thermostatTemperatureSetpoint")
        # Stored in DB's unit (F). 20C -> 68F, +1F => 69F
        self.assertEqual(tset["unit"], "F")
        self.assertAlmostEqual(tset["value"], 69.0, places=3)
        # Enrichment exposes both units rounded to 2 decimals
        expected_metric = round((69.0 - 32.0) * 5.0 / 9.0, 2)
        self.assertEqual(tset["value_metric"], expected_metric)


