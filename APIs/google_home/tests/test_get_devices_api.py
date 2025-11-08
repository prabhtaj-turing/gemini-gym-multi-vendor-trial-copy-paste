import pytest
from google_home.get_devices_api import get_devices
from google_home.SimulationEngine.db import DB, restore_default_data
from google_home.SimulationEngine.custom_errors import InvalidInputError


class TestGetDevices:
    @classmethod
    def setup_class(cls):
        """
        Restore the default database state before any tests run.
        """
        restore_default_data()

    def test_get_devices_no_filters(self):
        """
        Test get_devices with no filters, expecting all devices to be returned.
        """
        result = get_devices()
        assert isinstance(result["devices"], list)
        assert len(result["devices"]) >= 1

    def test_get_devices_with_trait_filter(self):
        """
        Test get_devices with a trait filter, expecting only devices with that trait.
        """
        result = get_devices(trait_hints=["OnOff"])
        assert len(result["devices"]) >= 1
        assert all("OnOff" in d["traits"] for d in result["devices"])

    def test_get_devices_with_type_filter(self):
        """
        Test get_devices with a type filter, expecting only devices of that type.
        """
        result = get_devices(type_hints=["THERMOSTAT"])
        assert len(result["devices"]) >= 1
        assert all("THERMOSTAT" in d["types"] for d in result["devices"])

    def test_get_devices_with_trait_and_type_filters(self):
        """
        Test get_devices with both trait and type filters.
        """
        result = get_devices(trait_hints=["OnOff"], type_hints=["LIGHT"])
        assert len(result["devices"]) >= 1
        assert all("OnOff" in d["traits"] and "LIGHT" in d["types"] for d in result["devices"])

    def test_get_devices_with_non_matching_filters(self):
        """
        Test get_devices with filters that don't match any devices.
        """
        result = get_devices(
            trait_hints=["ColorSetting"], type_hints=["GARAGE"]
        )
        assert len(result["devices"]) == 0

    def test_get_devices_include_state_true(self):
        """
        Test get_devices with include_state=True.
        """
        result = get_devices(include_state=True)
        assert len(result["devices"]) >= 1
        assert all(isinstance(d.get("device_state"), list) and len(d["device_state"]) >= 0 for d in result["devices"])  # type: ignore[index]
        # At least one device should have non-empty state when include_state=True
        assert any(len(d["device_state"]) > 0 for d in result["devices"])  # type: ignore[index]

    def test_get_devices_include_state_false(self):
        """
        Test get_devices with include_state=False.
        """
        result = get_devices(include_state=False)
        assert len(result["devices"]) >= 1
        assert all(d.get("device_state") == [] for d in result["devices"])  # type: ignore[index]

    def test_get_devices_with_invalid_trait_filter(self):
        """
        Test get_devices with an invalid trait filter.
        """
        with pytest.raises(InvalidInputError):
            get_devices(trait_hints=["InvalidTrait"])

    def test_get_devices_with_invalid_type_filter(self):
        """
        Test get_devices with an invalid type filter.
        """
        with pytest.raises(InvalidInputError):
            get_devices(type_hints=["InvalidType"])