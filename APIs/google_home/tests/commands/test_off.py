import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestOff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_off_light(self):
        # first turn on
        gh_run(devices=["007"], op="on")  # type: ignore
        gh_run(devices=["007"], op="off")  # type: ignore
        devices_info = json.loads(gh_details(devices=["007"])["devices_info"])  # type: ignore
        states = devices_info["007"]
        on_state = next(s for s in states if s["name"] == "on")
        self.assertFalse(on_state["value"]) 


