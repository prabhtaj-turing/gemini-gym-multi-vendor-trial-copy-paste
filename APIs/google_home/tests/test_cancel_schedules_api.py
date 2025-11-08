import pytest
from google_home.cancel_schedules_api import cancel_schedules
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import (
    InvalidInputError,
    DeviceNotFoundError,
    NoSchedulesFoundError,
)


class TestCancelSchedules:
    @classmethod
    def setup_class(cls):
        """
        Clear the database and set up with test-specific data.
        """
        DB.clear()
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
                                        {"name": "on", "value": True},
                                        {"name": "brightness", "value": 0.5},
                                        {
                                            "name": "schedules",
                                            "value": [
                                                {
                                                    "start_time": "2025-07-15T19:00:00",
                                                    "action": "on",
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

    def test_cancel_schedules_all_devices(self):
        """
        Test cancel_schedules with no devices specified.
        """
        result = cancel_schedules()
        assert result["success"] is True
        assert result["operation_type"] == "CANCEL_SCHEDULES"
        assert result.get("tts") == "Successfully canceled 1 schedule.\nDetails:\n- light-1: on @ 2025-07-15T19:00:00"
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert len(device["device_state"][2]["value"]) == 0

    def test_cancel_schedules_valid_devices(self):
        """
        Test cancel_schedules with valid device IDs.
        """
        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules(devices=["light-1"])
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert len(device["device_state"][2]["value"]) == 0

    def test_cancel_schedules_invalid_device_id(self):
        """
        Test cancel_schedules with an invalid device ID.
        """
        with pytest.raises(DeviceNotFoundError) as ei:
            cancel_schedules(devices=["invalid-device"])
        assert str(ei.value) == "Device with ID 'invalid-device' not found."

    def test_cancel_schedules_mixed_valid_and_invalid_devices(self):
        """
        Test cancel_schedules with a mix of valid and invalid device IDs.
        """
        with pytest.raises(DeviceNotFoundError) as ei:
            cancel_schedules(devices=["light-1", "invalid-device"])
        assert str(ei.value) == "Device with ID 'invalid-device' not found."

    def test_cancel_schedules_invalid_input_type(self):
        """
        Test cancel_schedules with invalid input type for devices.
        """
        with pytest.raises(InvalidInputError) as ei:
            cancel_schedules(devices="not-a-list")
        msg = str(ei.value)
        assert msg.startswith("Invalid input:") and "valid list" in msg

    def test_cancel_schedules_no_schedules_to_cancel(self):
        """
        Test cancel_schedules when there are no schedules to cancel.
        """
        # Clear existing schedules
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["device_state"][2]["value"] = []

        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules(devices=["light-1"])
        assert len(device["device_state"][2]["value"]) == 0

    def test_cancel_schedules_multiple_devices(self):
        """
        Test cancel_schedules with multiple devices.
        """
        DB["structures"]["Home"]["rooms"]["Bedroom"] = {
            "name": "Bedroom",
            "devices": {
                "LIGHT": [
                    {
                        "id": "light-2",
                        "names": ["Bedroom Light"],
                        "types": ["LIGHT"],
                        "traits": ["OnOff"],
                        "room_name": "Bedroom",
                        "structure": "Home",
                        "toggles_modes": [],
                        "device_state": [
                            {"name": "on", "value": False},
                            {
                                "name": "schedules",
                                "value": [
                                    {
                                        "start_time": "2025-07-15T22:00:00",
                                        "action": "off",
                                    }
                                ],
                            },
                        ],
                    }
                ]
            },
        }
        # Add another device with two schedules
        DB["structures"]["Home"]["rooms"]["Bedroom"]["devices"]["LIGHT"].append(
            {
                "id": "light-3",
                "names": ["Bedroom Lamp"],
                "types": ["LIGHT"],
                "traits": ["OnOff"],
                "room_name": "Bedroom",
                "structure": "Home",
                "toggles_modes": [],
                "device_state": [
                    {"name": "on", "value": True},
                    {
                        "name": "schedules",
                        "value": [
                            {
                                "start_time": "2025-07-16T08:00:00",
                                "action": "on",
                            },
                            {
                                "start_time": "2025-07-16T09:00:00",
                                "action": "off",
                            },
                        ],
                    },
                ],
            }
        )

        result = cancel_schedules(devices=["light-2", "light-3"])
        assert result["success"] is True
        assert result["operation_type"] == "CANCEL_SCHEDULES"
        expected_tts = (
            "Successfully canceled 3 schedules.\nDetails:\n"
            "- light-2: off @ 2025-07-15T22:00:00\n"
            "- light-3: on @ 2025-07-16T08:00:00, off @ 2025-07-16T09:00:00"
        )
        assert result.get("tts") == expected_tts
        # Validate schedules cleared for targeted devices
        living_room_device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        bedroom_device_1 = DB["structures"]["Home"]["rooms"]["Bedroom"]["devices"]["LIGHT"][0]
        bedroom_device_2 = DB["structures"]["Home"]["rooms"]["Bedroom"]["devices"]["LIGHT"][1]
        assert len(living_room_device["device_state"][2]["value"]) == 0
        assert len(bedroom_device_1["device_state"][1]["value"]) == 0
        assert len(bedroom_device_2["device_state"][1]["value"]) == 0

    def test_cancel_schedules_empty_devices_list(self):
        """
        Test cancel_schedules with an empty list of devices.
        """
        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules(devices=[])
        # No schedules should be canceled if devices list is empty
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert len(device["device_state"][2]["value"]) == 0
        
    def test_cancel_schedules_no_devices_in_db(self):
        """
        Test cancel_schedules when there are no devices in the database.
        """
        original_structures = DB.get("structures")
        DB["structures"] = {}

        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules()

        DB["structures"] = original_structures

    def test_cancel_schedules_device_without_schedules_trait(self):
        """
        Test cancel_schedules for a device that does not have a 'schedules' trait.
        """
        DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["THERMOSTAT"] = [
            {
                "id": "thermostat-1",
                "names": ["Living Room Thermostat"],
                "types": ["THERMOSTAT"],
                "traits": ["TemperatureSetting"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [],
                "device_state": [{"name": "temperature", "value": 22}],
            }
        ]

        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules(devices=["thermostat-1"])
        
        del DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["THERMOSTAT"]

    def test_cancel_schedules_device_with_empty_schedules(self):
        """
        Test cancel_schedules for a device with an empty 'schedules' list.
        """
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["device_state"][2]["value"] = []

        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules(devices=["light-1"])
        assert len(device["device_state"][2]["value"]) == 0
        
        # Restore the schedule for other tests
        device["device_state"][2]["value"] = [
            {"start_time": "2025-07-15T19:00:00", "action": "on"}
        ]

    def test_cancel_schedules_no_rooms_in_structure(self):
        """
        Test cancel_schedules with a structure that has no rooms.
        """
        original_structures = DB.get("structures")
        DB["structures"] = {"Home": {"name": "Home", "rooms": {}}}

        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules()

        DB["structures"] = original_structures

    def test_cancel_schedules_no_devices_in_room(self):
        """
        Test cancel_schedules with a room that has no devices.
        """
        original_structures = DB.get("structures")
        DB["structures"] = {
            "Home": {
                "name": "Home",
                "rooms": {"Living Room": {"name": "Living Room", "devices": {}}},
            }
        }

        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules()

        DB["structures"] = original_structures

    def test_cancel_schedules_no_structures(self):
        """
        Test cancel_schedules with no structures in the database.
        """
        original_structures = DB.get("structures")
        DB["structures"] = {}

        with pytest.raises(NoSchedulesFoundError):
            cancel_schedules()

        DB["structures"] = original_structures
