import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestOn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_on_light(self):
        gh_run(devices=["007"], op="on")  # type: ignore
        devices_info = json.loads(gh_details(devices=["007"])["devices_info"])  # type: ignore
        states = devices_info["007"]
        on_state = next(s for s in states if s["name"] == "on")
        self.assertTrue(on_state["value"]) 

    def test_on_rejects_values(self):
        with self.assertRaises(Exception) as cm:
            gh_run(devices=["007"], op="on", values=["true"])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'on' does not support values.")


