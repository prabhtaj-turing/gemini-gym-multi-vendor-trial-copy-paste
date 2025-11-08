import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestToggleOnOff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_toggle_light(self):
        devices = ["007"]
        # ensure off
        gh_run(devices=devices, op="off")  # type: ignore
        gh_run(devices=devices, op="toggle_on_off")  # type: ignore
        states = json.loads(gh_details(devices=devices)["devices_info"])["007"]  # type: ignore
        on_state = next(s for s in states if s["name"] == "on")
        self.assertTrue(on_state["value"]) 
        gh_run(devices=devices, op="toggle_on_off")  # type: ignore
        states = json.loads(gh_details(devices=devices)["devices_info"])["007"]  # type: ignore
        on_state = next(s for s in states if s["name"] == "on")
        self.assertFalse(on_state["value"]) 


