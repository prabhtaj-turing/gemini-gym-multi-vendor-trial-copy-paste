import pytest
from google_home.devices_api import devices
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import InvalidInputError


class TestDevices:
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
                            ],
                            "THERMOSTAT": [
                                {
                                    "id": "thermostat-1",
                                    "names": ["Living Room Thermostat"],
                                    "types": ["THERMOSTAT"],
                                    "traits": ["TemperatureSetting"],
                                    "room_name": "Living Room",
                                    "structure": "Home",
                                    "toggles_modes": [],
                                    "device_state": [
                                        {
                                            "name": "thermostatTemperatureSetpoint",
                                            "value": 22,
                                        }
                                    ],
                                }
                            ],
                        },
                    }
                },
            }
        }

    def test_devices_no_filters(self):
        """
        Test devices with no filters, expecting all devices to be returned.
        """
        result = devices()
        assert len(result["devices"]) == 2

    def test_devices_with_trait_filter(self):
        """
        Test devices with a trait filter, expecting only devices with that trait.
        """
        result = devices(traits=["OnOff"])
        assert len(result["devices"]) == 1
        assert "OnOff" in result["devices"][0]["traits"]

    def test_devices_with_non_matching_filters(self):
        """
        Test devices with filters that don't match any devices.
        """
        result = devices(traits=["ColorSetting"])
        assert len(result["devices"]) == 0

    def test_devices_include_state_true(self):
        """
        Test devices with include_state=True.
        """
        result = devices(state=True)
        assert len(result["devices"]) == 2
        assert len(result["devices"][0]["device_state"]) > 0

    def test_devices_include_state_false(self):
        """
        Test devices with include_state=False.
        """
        result = devices(state=False)
        assert len(result["devices"]) == 2
        assert len(result["devices"][0]["device_state"]) == 0

    def test_devices_with_invalid_trait_filter(self):
        """
        Test devices with an invalid trait filter.
        """
        with pytest.raises(InvalidInputError):
            devices(traits=["InvalidTrait"])