import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestOpenApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_open_app_tv(self):
        gh_run(devices=["001"], op="open_app", values=["netflix"])  # type: ignore
        devices_info = json.loads(gh_details(devices=["001"])["devices_info"])  # type: ignore
        states = devices_info["001"]
        st = next(s for s in states if s["name"] == "currentApp")
        self.assertEqual(st["value"], "netflix")

    def test_open_app_requires_value(self):
        with self.assertRaises(Exception) as cm:
            gh_run(devices=["001"], op="open_app", values=[])  # type: ignore
        self.assertEqual(str(cm.exception), "Invalid input: Command 'open_app' requires values.")


