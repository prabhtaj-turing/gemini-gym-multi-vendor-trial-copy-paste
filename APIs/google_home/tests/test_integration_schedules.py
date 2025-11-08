import pytest
from google_home.run_api import run
from google_home.view_schedules_api import view_schedules
from google_home.cancel_schedules_api import cancel_schedules
from google_home.SimulationEngine.db import DB


class TestIntegrationSchedules:
    @classmethod
    def setup_class(cls):
        DB.clear()
        DB["actions"] = []
        DB["structures"] = {
            "Home": {
                "name": "Home",
                "rooms": {
                    "Living Room": {
                        "name": "Living Room",
                        "devices": {
                            "LIGHT": [
                                {
                                    "id": "light-1",
                                    "names": ["Living Room Light"],
                                    "types": ["LIGHT"],
                                    "traits": ["OnOff", "Brightness"],
                                    "room_name": "Living Room",
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
        }
        DB["actions"] = []

    def test_run_schedules_reflected_in_view_and_canceled_by_cancel(self):
        """
        Expected: A schedule created via run() should be visible in view_schedules() and
        removed by cancel_schedules().
        Current: Not reflected/canceled due to storage mismatch -> FAIL expected.
        """
        # Create schedule via run
        run(devices=["light-1"], op="on", delay="10m", duration="5m")

        # Should see at least 1 schedule
        result_view = view_schedules(devices=["light-1"])
        assert "Found 1 schedules." in result_view["tts"]

        # Cancel and expect zero schedules
        cancel_schedules(devices=["light-1"])
        result_view_after = view_schedules(devices=["light-1"])
        assert "Found 0 schedules." in result_view_after["tts"]
