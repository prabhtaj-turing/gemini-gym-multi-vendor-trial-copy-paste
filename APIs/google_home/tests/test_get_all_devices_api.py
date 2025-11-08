import pytest
from google_home.get_all_devices_api import get_all_devices
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import InvalidInputError


class TestGetAllDevices:
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

    def test_get_all_devices_no_filters(self):
        """
        Test get_all_devices with no filters, expecting all devices to be returned.
        """
        devices = get_all_devices()
        assert len(devices) == 2

    def test_get_all_devices_with_trait_filter(self):
        """
        Test get_all_devices with a trait filter, expecting only devices with that trait.
        """
        devices = get_all_devices(trait_hints=["OnOff"])
        assert len(devices) == 1
        assert "OnOff" in devices[0]["traits"]

    def test_get_all_devices_with_type_filter(self):
        """
        Test get_all_devices with a type filter, expecting only devices of that type.
        """
        devices = get_all_devices(type_hints=["THERMOSTAT"])
        assert len(devices) == 1
        assert "THERMOSTAT" in devices[0]["types"]

    def test_get_all_devices_with_trait_and_type_filters(self):
        """
        Test get_all_devices with both trait and type filters.
        """
        devices = get_all_devices(trait_hints=["OnOff"], type_hints=["LIGHT"])
        assert len(devices) == 1
        assert "OnOff" in devices[0]["traits"]
        assert "LIGHT" in devices[0]["types"]

    def test_get_all_devices_with_non_matching_filters(self):
        """
        Test get_all_devices with filters that don't match any devices.
        """
        devices = get_all_devices(
            trait_hints=["ColorSetting"], type_hints=["GARAGE"]
        )
        assert len(devices) == 0

    def test_get_all_devices_with_invalid_trait_filter(self):
        """
        Test get_all_devices with an invalid trait filter.
        """
        with pytest.raises(InvalidInputError):
            get_all_devices(trait_hints=["InvalidTrait"])

    def test_get_all_devices_with_invalid_type_filter(self):
        """
        Test get_all_devices with an invalid type filter.
        """
        with pytest.raises(InvalidInputError):
            get_all_devices(type_hints=["InvalidType"])