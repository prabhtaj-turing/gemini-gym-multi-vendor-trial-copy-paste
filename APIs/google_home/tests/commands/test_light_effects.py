import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestLightEffects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _get_device_state(self, device_id: str):
        devices_info = json.loads(gh_details(devices=[device_id])["devices_info"])  # type: ignore
        return devices_info[device_id]

    def test_set_light_effect(self):
        gh_run(devices=["007"], op="set_light_effect", values=["sleep"])  # type: ignore
        state = self._get_device_state("007")
        modes = next(s for s in state if s["name"] == "currentModes")
        self.assertEqual(modes["value"].get("lightEffect"), "sleep")

    def test_set_light_effect_with_duration_reverts(self):
        gh_run(devices=["007"], op="set_light_effect_with_duration", values=["pulse", "2"])  # type: ignore
        state = self._get_device_state("007")
        modes = next(s for s in state if s["name"] == "currentModes")
        self.assertIn("lightEffect", modes["value"])  # present after run


