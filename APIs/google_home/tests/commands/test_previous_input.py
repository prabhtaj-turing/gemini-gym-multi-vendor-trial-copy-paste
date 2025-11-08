import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestPreviousInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_previous_input_tv(self):
        gh_run(devices=["001"], op="previous_input")  # type: ignore
        states = json.loads(gh_details(devices=["001"])["devices_info"])["001"]  # type: ignore
        st = next(s for s in states if s["name"] == "currentInput")
        self.assertIn(st["value"], ["hdmi_1", "hdmi_2", "hdmi_3", "tv", "av"]) 


