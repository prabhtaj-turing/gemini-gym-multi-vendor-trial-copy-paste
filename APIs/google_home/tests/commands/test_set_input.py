import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestSetInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_set_input_tv(self):
        gh_run(devices=["001"], op="set_input", values=["hdmi_2"])  # type: ignore
        devices_info = json.loads(gh_details(devices=["001"])["devices_info"])  # type: ignore
        states = devices_info["001"]
        st = next(s for s in states if s["name"] == "currentInput")
        self.assertEqual(st["value"], "hdmi_2")

    def test_set_input_requires_value(self):
        with self.assertRaises(Exception) as cm:
            gh_run(devices=["001"], op="set_input", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'set_input' requires values.")


