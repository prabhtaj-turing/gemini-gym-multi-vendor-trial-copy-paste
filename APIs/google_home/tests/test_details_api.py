import json
import pytest
from google_home.details_api import details
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import (
    InvalidInputError,
    DeviceNotFoundError,
)
from google_home.SimulationEngine.models import DetailsParams
from pydantic import ValidationError
import json


class TestDetails:
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
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

    def test_details_valid_devices(self):
        """
        Test details with valid device IDs.
        """
        result = details(devices=["light-1"])
        assert "light-1" in result["devices_info"]

    def test_details_returns_parsed_json_for_valid_device(self):
        """
        Ensure the API returns JSON that can be parsed and matches expected structure for a valid device.
        """
        result = details(devices=["light-1"])
        parsed = json.loads(result["devices_info"])
        assert isinstance(parsed, dict)
        assert "light-1" in parsed
        # The state should be a list of name/value dicts
        assert isinstance(parsed["light-1"], list)
        assert any(s.get("name") == "on" for s in parsed["light-1"])

    def test_details_invalid_device_id(self):
        """
        Test details with an invalid device ID.
        """
        with pytest.raises(DeviceNotFoundError) as excinfo:
            details(devices=["invalid-device"])
        msg = str(excinfo.value)
        assert "invalid-device" in msg
        assert "not found" in msg

    def test_details_empty_device_list(self):
        """
        Test details with an empty list of device IDs.
        Should return all devices' state.
        """
        result = details(devices=[])
        # Should be a JSON string of all devices' state
        devices_info = json.loads(result["devices_info"])
        assert isinstance(devices_info, dict)
        # Should contain all device ids in the DB
        assert "light-1" in devices_info
        # Should match the device_state for light-1
        assert devices_info["light-1"] == [
            {"name": "on", "value": True},
            {"name": "brightness", "value": 0.5},
        ]

    def test_details_empty_list_returns_all_device_states(self):
        """
        Passing an empty list should return a mapping of device_id -> device_state.
        """
        result = details(devices=[])
        parsed = json.loads(result["devices_info"])
        from google_home.SimulationEngine.db import DB
        expected = {}
        for structure in DB["structures"].values():
            for room in structure.get("rooms", {}).values():
                for device_list in room.get("devices", {}).values():
                    for device in device_list:
                        expected[device["id"]] = device["device_state"]
        assert parsed == expected

    def test_details_mixed_valid_and_invalid_devices(self):
        """
        Test details with a mix of valid and invalid device IDs.
        """
        with pytest.raises(DeviceNotFoundError) as excinfo:
            details(devices=["light-1", "invalid-device"])

    def test_details_multiple_valid_devices(self):
        """
        When multiple valid device IDs are provided, all should be returned.
        """
        from google_home.SimulationEngine.db import DB
        # Add a second device temporarily
        second_device = {
            "id": "light-2",
            "names": ["Living Room Light 2"],
            "types": ["LIGHT"],
            "traits": ["OnOff"],
            "room_name": "Living Room",
            "structure": "Home",
            "toggles_modes": [],
            "device_state": [
                {"name": "on", "value": False}
            ],
        }
        devices_list = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"]
        devices_list.append(second_device)
        try:
            result = details(devices=["light-1", "light-2"])
            parsed = json.loads(result["devices_info"])
            assert set(parsed.keys()) == {"light-1", "light-2"}
        finally:
            # Clean up
            devices_list.pop()

    def test_details_invalid_none_input(self):
        """
        None is not a valid input for devices.
        """
        with pytest.raises(InvalidInputError):
            details(devices=None)