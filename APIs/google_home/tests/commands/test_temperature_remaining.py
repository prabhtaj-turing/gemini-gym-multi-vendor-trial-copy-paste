import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestRemainingTemperature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _get_device_state(self, device_id: str):
        devices_info = json.loads(gh_details(devices=[device_id])["devices_info"])  # type: ignore
        return devices_info[device_id]

    def test_set_temperature_fahrenheit(self):
        gh_run(devices=["002"], op="set_temperature_fahrenheit", values=["72"])  # type: ignore
        state = self._get_device_state("002")
        tset = next(s for s in state if s["name"] == "thermostatTemperatureSetpoint")
        self.assertEqual(tset["unit"], "F")
        self.assertAlmostEqual(tset["value"], 72.0, places=3)

    def test_set_mode_and_temperature_celsius(self):
        gh_run(devices=["002"], op="set_mode_and_temperature_celsius", values=["cool", "18"])  # type: ignore
        state = self._get_device_state("002")
        mode = next(s for s in state if s["name"] == "thermostatMode")
        tset = next(s for s in state if s["name"] == "thermostatTemperatureSetpoint")
        self.assertEqual(mode["value"], "cool")
        # Stored in DB's F: 18C -> 64.4F
        self.assertAlmostEqual(tset["value"], 64.4, places=3)
        # DB unit preserved; default is F per default DB
        self.assertEqual(tset.get("unit"), "F")

    def test_set_mode_and_temperature_fahrenheit(self):
        gh_run(devices=["002"], op="set_mode_and_temperature_fahrenheit", values=["heat", "70"])  # type: ignore
        state = self._get_device_state("002")
        mode = next(s for s in state if s["name"] == "thermostatMode")
        tset = next(s for s in state if s["name"] == "thermostatTemperatureSetpoint")
        self.assertEqual(mode["value"], "heat")
        self.assertAlmostEqual(tset["value"], 70.0, places=3)
        self.assertEqual(tset.get("unit"), "F")

    def test_cooler_warmer_ambiguous_with_unit(self):
        gh_run(devices=["002"], op="set_temperature_celsius", values=["20"])  # type: ignore
        gh_run(devices=["002"], op="cooler_ambiguous", values=["2", "F"])  # type: ignore
        state = self._get_device_state("002")
        tset = next(s for s in state if s["name"] == "thermostatTemperatureSetpoint")
        # Store remains in F: 20C -> 68F; cooler by 2F => 66F
        self.assertAlmostEqual(tset["value"], 66.0, places=3)
        self.assertEqual(tset.get("unit"), "F")


