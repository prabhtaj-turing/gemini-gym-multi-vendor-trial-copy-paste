import json
import unittest

from google_home.SimulationEngine.db import restore_default_data, clear_db, DB
from google_home import run as gh_run, details as gh_details


class TestMiscStatelessAndSchedules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        restore_default_data()

    def tearDown(self):
        clear_db()
        restore_default_data()

    def _add_camera_and_sensor(self):
        # Camera (stateless)
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("CAMERA", []).append(
            {
                "id": "cam-1",
                "names": ["Camera"],
                "types": ["CAMERA"],
                "traits": ["CameraStream"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [],
            }
        )
        # Humidity + ArmDisarm stateless
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("SWITCH", []).append(
            {
                "id": "sens-1",
                "names": ["Sensor"],
                "types": ["SWITCH"],
                "traits": ["HumiditySetting", "ArmDisarm"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [],
            }
        )

    def test_stateless_commands_succeed(self):
        self._add_camera_and_sensor()
        r1 = gh_run(devices=["cam-1"], op="camera_stream")  # type: ignore
        r2 = gh_run(devices=["sens-1"], op="humidity_setting")  # type: ignore
        r3 = gh_run(devices=["sens-1"], op="arm_disarm")  # type: ignore
        self.assertEqual(r1[0]["result"], "SUCCESS")
        self.assertEqual(r2[0]["result"], "SUCCESS")
        self.assertEqual(r3[0]["result"], "SUCCESS")

    def _add_simple_device(self) -> str:
        DB["structures"]["house"]["rooms"]["Living Room"]["devices"].setdefault("LIGHT", []).append(
            {
                "id": "sched-1",
                "names": ["Sched Light"],
                "types": ["LIGHT"],
                "traits": ["OnOff"],
                "room_name": "Living Room",
                "structure": "house",
                "toggles_modes": [],
                "device_state": [
                    {"name": "on", "value": False},
                    {"name": "schedules", "value": []},
                ],
            }
        )
        return "sched-1"

    def test_view_schedules_stateless(self):
        did = self._add_simple_device()
        r = gh_run(devices=[did], op="view_schedules")  # type: ignore
        self.assertEqual(r[0]["result"], "SUCCESS")

    def test_cancel_schedules_stateless(self):
        did = self._add_simple_device()
        # cancel_schedules raises when no schedules exist; expecting SUCCESS via view or after adding none
        # Here we assert that invoking cancel_schedules without schedules raises, matching API contract
        with self.assertRaises(Exception):
            gh_run(devices=[did], op="cancel_schedules")  # type: ignore

    def test_show_device_info_stateless(self):
        did = self._add_simple_device()
        r = gh_run(devices=[did], op="show_device_info")  # type: ignore
        self.assertEqual(r[0]["result"], "SUCCESS")


