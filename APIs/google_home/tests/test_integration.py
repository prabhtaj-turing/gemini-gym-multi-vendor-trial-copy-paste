import unittest
from datetime import datetime, timedelta, timezone
from common_utils.base_case import BaseTestCaseWithErrorHandler

from google_home.SimulationEngine.db import DB
from google_home.devices_api import devices
from google_home.get_devices_api import get_devices
from google_home.get_all_devices_api import get_all_devices
from google_home.run_api import run
from google_home.mutate_api import mutate
from google_home.mutate_traits_api import mutate_traits
from google_home.view_schedules_api import view_schedules
from google_home.cancel_schedules_api import cancel_schedules
from google_home.SimulationEngine.models import GoogleHomeDB


class TestIntegration(BaseTestCaseWithErrorHandler):

    def setUp(self):
        DB.clear()
        DB.update({
            "structures": {
                "Home": {
                    "name": "Home",
                    "rooms": {
                        "Living": {
                            "name": "Living",
                            "devices": {
                                "LIGHT": [
                                    {
                                        "id": "light-1",
                                        "names": ["Lamp"],
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff", "Brightness", "ViewSchedules"],
                                        "room_name": "Living",
                                        "structure": "Home",
                                        "toggles_modes": [],
                                        "device_state": [
                                            {"name": "on", "value": False},
                                            {"name": "brightness", "value": 0.5},
                                            {"name": "schedules", "value": []},
                                        ],
                                    }
                                ]
                            },
                        }
                    },
                }
            },
            "actions": [],
        })

        # Validate test DB
        GoogleHomeDB.model_validate(DB)

    def tearDown(self):
        DB.clear()

    def test_device_discovery_and_state_flow(self):
        # devices() without state returns device with empty state
        d_no_state = devices()
        self.assertEqual(len(d_no_state["devices"]), 1)
        self.assertEqual(d_no_state["devices"][0]["device_state"], [])

        # get_devices(include_state=True) returns state
        d_with_state = get_devices(include_state=True)
        self.assertEqual(len(d_with_state["devices"]), 1)
        self.assertGreater(len(d_with_state["devices"][0]["device_state"]), 0)

        # get_all_devices returns raw list
        all_devices = get_all_devices()
        self.assertEqual(len(all_devices), 1)

        # run a command to turn light on
        run_results = run(devices=["light-1"], op="on")
        self.assertEqual(run_results[0]["result"], "SUCCESS")

        # verify state changed
        with_state_after = get_devices(include_state=True)
        self.assertTrue(next(s for s in with_state_after["devices"][0]["device_state"] if s["name"] == "on")["value"])

    def test_schedules_end_to_end(self):
        # Initially, no schedules
        view = view_schedules()
        self.assertIn("Found 0 schedules.", view["tts"])

        # Add a schedule to turn on later by mutating schedules state directly for integration simplicity
        device = DB["structures"]["Home"]["rooms"]["Living"]["devices"]["LIGHT"][0]
        future_start_time = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
        device["device_state"][2]["value"].append({
            "start_time": future_start_time,
            "action": "on",
            "values": ["true"],
        })

        # view schedules should now find 1
        view2 = view_schedules()
        self.assertIn("Found 1 schedules.", view2["tts"])

        # cancel schedules and verify none remain
        cancel = cancel_schedules()
        self.assertTrue(cancel["success"])
        view3 = view_schedules()
        self.assertIn("Found 0 schedules.", view3["tts"])

    def test_mutate_and_mutate_traits(self):
        # mutate OnOff on
        m1 = mutate(devices=["light-1"], traits=["OnOff"], commands=["on"], values=[])
        self.assertEqual(m1[0]["result"], "SUCCESS")

        # mutate_traits OnOff off
        m2 = mutate_traits(device_ids=["light-1"], trait_names=["OnOff"], command_names=["off"], command_values=[])
        self.assertEqual(m2[0]["result"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()


