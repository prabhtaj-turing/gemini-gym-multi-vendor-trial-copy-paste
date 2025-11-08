import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db
from google_home import run as gh_run, details as gh_details


class TestSetBrightness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def test_set_brightness_valid(self):
        gh_run(devices=["006"], op="set_brightness", values=["0.6"])  # type: ignore
        states = json.loads(gh_details(devices=["006"])["devices_info"])["006"]  # type: ignore
        st = next(s for s in states if s["name"] == "brightness")
        self.assertAlmostEqual(st["value"], 0.6, places=3)

    def test_set_brightness_invalid_number(self):
        with self.assertRaises(ValueError) as cm:
            gh_run(devices=["006"], op="set_brightness", values=["abc"])  # type: ignore
        self.assertIn("could not convert string to float", str(cm.exception))

    def test_set_brightness_out_of_range(self):
        with self.assertRaises(ValueError) as cm:
            gh_run(devices=["006"], op="set_brightness", values=["1.5"])  # type: ignore
        self.assertEqual(str(cm.exception), "Value for set_brightness must be between 0.0 and 1.0")


