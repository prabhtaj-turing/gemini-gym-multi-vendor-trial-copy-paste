from unittest.mock import patch
import pytest
from freezegun import freeze_time
from datetime import datetime, timezone, timedelta
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home.SimulationEngine.utils import (
    process_schedules, 
    parse_duration_to_timedelta, 
    calculate_start_time, 
    add_schedule_to_device,
    update_device_state,
    process_schedules_and_get_structures,
)
from google_home.SimulationEngine.models import CommandName, StateName, TraitName

@pytest.fixture(autouse=True)
def clear_db():
    DB.clear()
    yield

class TestUtils:
    def test_process_schedules(self):
        """
        Test that process_schedules correctly updates device states based on past schedules.
        """
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
                                        {"name": StateName.ON, "value": False},
                                        {"name": StateName.BRIGHTNESS, "value": 0.5},
                                        {
                                            "name": "schedules",
                                            "value": [
                                                {
                                                    "start_time": "2025-07-15T18:00:00+00:00",
                                                    "action": CommandName.ON.value,
                                                    "values": ["true"],
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

        with freeze_time("2025-07-15T19:00:00Z"):
            process_schedules()

        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][0]["value"] is True
        # schedules stored under device_state
        assert len(device["device_state"][2]["value"]) == 0

    def test_process_schedules_with_on_off_duration(self):
        """
        Test that process_schedules correctly handles OnOff schedules with a duration
        by creating a revert-action schedule.
        """
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
                                    "traits": ["OnOff"],
                                    "room_name": "Living Room",
                                    "structure": "Home",
                                    "toggles_modes": [],
                                    "device_state": [
                                        {"name": StateName.ON, "value": False},
                                        {
                                            "name": "schedules",
                                            "value": [
                                                {
                                                    "start_time": "2025-07-15T18:00:00+00:00",
                                                    "action": CommandName.ON.value,
                                                    "values": ["true"],
                                                    "duration": "1h",
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

        with freeze_time("2025-07-15T18:00:01Z"):
            process_schedules()

        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][0]["value"] is True
        assert len(device["device_state"][1]["value"]) == 1
        revert_schedule = device["device_state"][1]["value"][0]
        assert revert_schedule["action"] == CommandName.OFF.value
        assert revert_schedule["values"] == []
        assert revert_schedule["start_time"] == "2025-07-15T19:00:00+00:00"

    def test_process_schedules_with_toggle_duration(self):
        """
        Test that process_schedules correctly handles ToggleOnOff schedules with a duration
        by creating a revert-action schedule.
        """
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
                                    "traits": ["OnOff"],
                                    "room_name": "Living Room",
                                    "structure": "Home",
                                    "toggles_modes": [],
                                    "device_state": [
                                        {"name": StateName.ON, "value": False},
                                        {
                                            "name": "schedules",
                                            "value": [
                                                {
                                                    "start_time": "2025-07-15T18:00:00+00:00",
                                                    "action": CommandName.TOGGLE_ON_OFF.value,
                                                    "values": [],
                                                    "duration": "30m",
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

        with freeze_time("2025-07-15T18:00:01Z"):
            process_schedules()

        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][0]["value"] is True
        assert len(device["device_state"][1]["value"]) == 1
        revert_schedule = device["device_state"][1]["value"][0]
        assert revert_schedule["action"] == CommandName.TOGGLE_ON_OFF.value
        assert revert_schedule["values"] == []
        assert revert_schedule["start_time"] == "2025-07-15T18:30:00+00:00"

    def test_process_schedules_with_duration_no_revert(self):
        """
        Test that process_schedules correctly handles schedules with a duration
        for commands that do not have a revert action.
        """
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
                                    "traits": ["Brightness"],
                                    "room_name": "Living Room",
                                    "structure": "Home",
                                    "toggles_modes": [],
                                    "device_state": [
                                        {"name": StateName.BRIGHTNESS, "value": 0},
                                        {
                                            "name": "schedules",
                                            "value": [
                            {
                                "start_time": "2025-07-15T18:00:00+00:00",
                                "action": CommandName.SET_BRIGHTNESS.value,
                                "values": ["0.5"],
                                "duration": "1h",
                            }
                        ],
                                        },
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

        with freeze_time("2025-07-15T18:00:01Z"):
            process_schedules()

        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][0]["value"] == 0.5
        assert len(device["device_state"][1]["value"]) == 0


    def test_process_schedules_future_schedule(self):
        """
        Test that process_schedules does not process schedules set for the future.
        """
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
                                    "traits": ["OnOff"],
                                    "room_name": "Living Room",
                                    "structure": "Home",
                                    "toggles_modes": [],
                                    "device_state": [{"name": StateName.ON, "value": False}],
                                    "schedules": [
                                        {
                                            "start_time": "2025-07-16T18:00:00Z",
                                            "action": CommandName.ON.value,
                                            "values": ["true"],
                                        }
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

        with freeze_time("2025-07-15T19:00:00Z"):
            process_schedules()

        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][0]["value"] is False
        assert len(device["schedules"]) == 1

    @pytest.mark.parametrize("duration_str, expected_td", [
        ("5s", timedelta(seconds=5)),
        ("20m", timedelta(minutes=20)),
        ("1h", timedelta(hours=1)),
        (None, timedelta(0)),
    ])
    def test_parse_duration_to_timedelta(self, duration_str, expected_td):
        assert parse_duration_to_timedelta(duration_str) == expected_td

    def test_parse_duration_to_timedelta_invalid(self):
        with pytest.raises(ValueError):
            parse_duration_to_timedelta("10x")

    @freeze_time("2025-07-15T12:00:00Z")
    @pytest.mark.parametrize("time_of_day, date, am_pm, delay, expected_time_str", [
        ("14:30:00", "2025-07-16", None, None, "2025-07-16T14:30:00+00:00"),
        ("02:30:00", None, "PM", None, "2025-07-15T14:30:00+00:00"),
        ("10:00:00", None, "AM", "1h", "2025-07-16T11:00:00+00:00"), # Past time, so next day
        (None, None, None, "30m", "2025-07-15T12:30:00+00:00"),
        (None, None, None, None, "2025-07-15T12:00:00+00:00"),
        ("01:00:00", None, "UNKNOWN", None, "2025-07-16T01:00:00+00:00"), # Past time, so next day
        ("12:00:00", None, "AM", None, "2025-07-16T00:00:00+00:00"), # 12 AM is midnight of next day
        ("12:30:00", None, "PM", None, "2025-07-15T12:30:00+00:00"), # 12:30 PM is in the afternoon
        (None, "2025-07-16", None, None, "2025-07-16T00:00:00+00:00"),
    ])
    def test_calculate_start_time(self, time_of_day, date, am_pm, delay, expected_time_str):
        expected_time = datetime.fromisoformat(expected_time_str)
        assert calculate_start_time(time_of_day, date, am_pm, delay) == expected_time

    def test_add_schedule_to_device(self):
        device = {"id": "test-device"}
        add_schedule_to_device(
            device, CommandName.ON, ["true"], "14:00:00", "2025-07-20", "PM", None, "5m"
        )
        # schedules are maintained under device_state only
        schedules_state = next(s for s in device["device_state"] if s["name"] == "schedules")
        assert len(schedules_state["value"]) == 1
        schedule = schedules_state["value"][0]
        assert schedule["action"] == CommandName.ON.value
        assert schedule["values"] == ["true"]
        assert schedule["start_time"] == "2025-07-20T14:00:00+00:00"
        assert schedule["duration"] == "5m"

    def test_update_device_state_unimplemented(self):
        with pytest.raises(NotImplementedError):
            update_device_state({"device_state": []}, "invalid.command", [])

    def test_update_device_state_missing_values(self):
        with pytest.raises(ValueError):
            update_device_state({"device_state": []}, CommandName.SET_BRIGHTNESS, [])

    def test_update_device_state_toggle(self):
        device = {
            "id": "d1",
            "names": ["Device"],
            "types": ["LIGHT"],
            "traits": ["OnOff"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.ON, "value": False}],
        }
        update_device_state(device, CommandName.TOGGLE_ON_OFF, [])
        assert device["device_state"][0]["value"] is True

    def test_update_device_state_set_mode_and_temp(self):
        device = {
            "id": "t1",
            "names": ["Thermostat"],
            "types": ["THERMOSTAT"],
            "traits": ["TemperatureSetting"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [
                {"name": StateName.THERMOSTAT_MODE, "value": "off"},
                {"name": StateName.THERMOSTAT_TEMPERATURE_SETPOINT, "value": 20.0},
            ],
        }
        update_device_state(device, CommandName.SET_MODE_AND_TEMPERATURE, ["cool", "25.5"])
        assert device["device_state"][0]["value"] == "cool"
        assert device["device_state"][1]["value"] == 25.5

    def test_update_device_state_fan_speed_string(self):
        device = {
            "id": "f1",
            "names": ["Fan"],
            "types": ["FAN"],
            "traits": ["FanSpeed"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.FAN_SPEED, "value": 0}],
        }
        update_device_state(device, CommandName.SET_FAN_SPEED, ["high"])
        assert device["device_state"][0]["value"] == 100

    def test_update_device_state_range_error(self):
        device = {
            "id": "l1",
            "names": ["Light"],
            "types": ["LIGHT"],
            "traits": ["Brightness"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.BRIGHTNESS, "value": 50}],
        }
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            update_device_state(device, CommandName.SET_BRIGHTNESS, ["1.5"])

    def test_update_device_state_type_error(self):
        device = {
            "id": "l2",
            "names": ["Light"],
            "types": ["LIGHT"],
            "traits": ["Brightness"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.BRIGHTNESS, "value": 50}],
        }
        with pytest.raises(ValueError, match="could not convert string to float"):
            update_device_state(device, CommandName.SET_BRIGHTNESS, ["abc"])

    def test_update_device_state_no_value_type(self):
        device = {
            "id": "c1",
            "names": ["Color Bulb"],
            "types": ["LIGHT"],
            "traits": ["ColorSetting"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.COLOR, "value": "red"}],
        }
        update_device_state(device, CommandName.CHANGE_COLOR, ["blue"])
        assert device["device_state"][0]["value"] == "blue"
        
    def test_update_device_state_not_in_command_value_map(self):
        device = {
            "id": "l3",
            "names": ["Light"],
            "types": ["LIGHT"],
            "traits": ["Brightness"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.BRIGHTNESS, "value": 0}],
        }
        update_device_state(device, CommandName.SET_BRIGHTNESS, ["0.5"])
        assert device["device_state"][0]["value"] == 0.5

    def test_update_device_state_in_command_value_map(self):
        device = {
            "id": "l4",
            "names": ["Light"],
            "types": ["LIGHT"],
            "traits": ["OnOff"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.ON, "value": False}],
        }
        update_device_state(device, CommandName.ON, ["true"])
        assert device["device_state"][0]["value"] is True

    def test_update_device_state_no_value_type(self):
        device = {
            "id": "c2",
            "names": ["Color Bulb"],
            "types": ["LIGHT"],
            "traits": ["ColorSetting"],
            "room_name": "R",
            "structure": "S",
            "toggles_modes": [],
            "device_state": [{"name": StateName.COLOR, "value": "red"}],
        }
        update_device_state(device, CommandName.CHANGE_COLOR, ["blue"])
        assert device["device_state"][0]["value"] == "blue"

    def test_process_schedules_and_get_structures(self):
        """
        Test that process_schedules_and_get_structures returns the updated structures.
        """
        db_state = {
            "structures": {
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
                                        "traits": ["OnOff"],
                                        "room_name": "Living Room",
                                        "structure": "Home",
                                        "toggles_modes": [],
                                        "device_state": [
                                            {"name": StateName.ON, "value": False},
                                            {
                                                "name": "schedules",
                                                "value": [
                                                    {
                                                        "start_time": "2025-07-15T18:00:00+00:00",
                                                        "action": CommandName.ON.value,
                                                        "values": ["true"],
                                                    }
                                                ],
                                            },
                                        ],
                                    }
                                ]
                            },
                        }
                    },
                }
            }
        }
        DB.update(db_state)

        with freeze_time("2025-07-15T19:00:00Z"):
            structures = process_schedules_and_get_structures()

        assert structures["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"][0]["value"] is True
        # expect schedules removed from device_state
        ds = structures["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"]
        schedules_state = next(s for s in ds if s["name"] == "schedules")
        assert len(schedules_state["value"]) == 0

    def test_process_schedules_with_off_duration(self):
        """
        Test that process_schedules correctly handles Off schedules with a duration
        by creating a revert-action schedule.
        """
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
                                    "traits": ["OnOff"],
                                    "room_name": "Living Room",
                                    "structure": "Home",
                                    "toggles_modes": [],
                                    "device_state": [
                                        {"name": StateName.ON, "value": True},
                                        {
                                            "name": "schedules",
                                            "value": [
                                                {
                                                    "start_time": "2025-07-15T18:00:00+00:00",
                                                    "action": CommandName.OFF.value,
                                                    "values": ["false"],
                                                    "duration": "1h",
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

        with freeze_time("2025-07-15T18:00:01Z"):
            process_schedules()

        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][0]["value"] is False
        assert len(device["device_state"][1]["value"]) == 1
        revert_schedule = device["device_state"][1]["value"][0]
        assert revert_schedule["action"] == CommandName.ON.value
        assert revert_schedule["values"] == []
        assert revert_schedule["start_time"] == "2025-07-15T19:00:00+00:00"
