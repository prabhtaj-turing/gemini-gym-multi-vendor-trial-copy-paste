import pytest
from google_home.see_devices_api import see_devices
from google_home.SimulationEngine.db import restore_default_data, DB


class TestSeeDevices:
    @classmethod
    def setup_class(cls):
        """
        Restore the default database state before any tests run.
        """
        restore_default_data()

    def test_see_devices_no_state(self):
        """
        Test see_devices with state=False.
        """
        result = see_devices(state=False)
        assert "| ID | Name | Type | Room|" in result["devices_info"]
        assert "State" not in result["devices_info"]

    def test_see_devices_with_state(self):
        """
        Test see_devices with state=True.
        """
        result = see_devices(state=True)
        assert "| ID | Name | Type | Room | State|" in result["devices_info"]

    def test_see_devices_no_devices(self):
        """
        Test see_devices with no devices in the database.
        """
        DB.clear()
        result = see_devices()
        assert result["devices_info"] == "No devices found."
        restore_default_data()
