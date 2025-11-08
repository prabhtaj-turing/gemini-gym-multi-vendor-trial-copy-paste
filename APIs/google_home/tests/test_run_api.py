import pytest
from google_home.run_api import run
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import (
    InvalidInputError,
    DeviceNotFoundError,
    NoSchedulesFoundError,
)


class TestRun:
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
                                        {"name": "on", "value": False},
                                        {"name": "brightness", "value": 0.5},
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }
        DB["actions"] = []

    def test_run_valid(self):
        """
        Test run with valid inputs.
        """
        results = run(
            devices=["light-1"],
            op="on",
        )
        assert len(results) == 1
        assert results[0]["result"] == "SUCCESS"
        assert results[0]["commands"]["device_ids"] == ["light-1"]

        # Verify that the device state was updated
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][0]["value"] is True

        # Verify that the action was logged
        assert len(DB["actions"]) == 1
        action = DB["actions"][0]
        assert action["action_type"] == "run"
        assert action["inputs"]["devices"] == ["light-1"]

    def test_run_invalid_device_id(self):
        """
        Test run with an invalid device ID.
        """
        with pytest.raises(DeviceNotFoundError) as ei:
            run(
                devices=["invalid-device"],
                op="on",
            )
        assert str(ei.value) == "Devices not found: invalid-device"

    def test_run_provided_values_for_command_not_requiring_values(self):
        """
        Test run with provided values for a command that does not require values.
        """
        with pytest.raises(InvalidInputError) as ei:
            run(
                devices=["light-1"],
                op="on",
                values=["true"],
            )
        assert str(ei.value) == "Invalid input: Command 'on' does not support values."

    def test_run_invalid_op(self):
        """
        Test run with an invalid operation.
        """
        with pytest.raises(InvalidInputError) as ei:
            run(
                devices=["light-1"],
                op="InvalidOp",
                values=["true"],
            )
        msg = str(ei.value)
        assert msg.startswith("Invalid input:") and "InvalidOp" in msg and "Input should be" in msg

    def test_run_show_device_info_should_be_supported(self):
        """
        Expected: run should support 'show_device_info' per tool spec without raising.
        Current: raises InvalidInputError -> FAIL expected.
        """
        results = run(
            devices=["light-1"],
            op="show_device_info",
        )
        assert results and results[0]["result"] == "SUCCESS"

    def test_run_view_schedules_should_be_supported(self):
        """
        Expected: run should support 'view_schedules' without NotImplemented.
        Current: NotImplementedError in updater -> FAIL expected.
        """
        results = run(
            devices=["light-1"],
            op="view_schedules",
        )
        assert results and results[0]["result"] == "SUCCESS"

    def test_run_cancel_schedules_raises_when_no_schedules(self):
        """
        run(cancel_schedules) should raise NoSchedulesFoundError if target devices have no schedules.
        """
        with pytest.raises(NoSchedulesFoundError):
            run(
                devices=["light-1"],
                op="cancel_schedules",
            )

    def test_run_is_atomic_on_invalid_device(self):
        """
        Expected: No partial updates when any device is invalid (atomic failure).
        Current: earlier devices are updated before error -> FAIL expected.
        """
        # Ensure device starts off
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["device_state"][0]["value"] = False

        with pytest.raises(DeviceNotFoundError):
            run(
                devices=["light-1", "invalid-device"],
                op="on",
            )
        # Should remain unchanged if atomic, but currently changes -> test should FAIL
        assert device["device_state"][0]["value"] is False

    def test_run_set_fan_speed_invalid_value_should_raise_invalidinputerror(self):
        """
        Expected: Invalid value for set_fan_speed should raise InvalidInputError with helpful message.
        Current: ValueError from int cast -> FAIL expected.
        """
        # Add an AC device to DB
        DB["structures"]["Home"]["rooms"]["Living Room"]["devices"].setdefault("AC_UNIT", []).append(
            {
                "id": "ac-1",
                "names": ["AC"],
                "types": ["AC_UNIT"],
                "traits": ["FanSpeed"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [],
                "device_state": [
                    {"name": "fanSpeed", "value": 33}
                ],
            }
        )

        with pytest.raises(InvalidInputError) as ei:
            run(
                devices=["ac-1"],
                op="set_fan_speed",
                values=["ultra"],
            )
        assert str(ei.value) == "Invalid fan speed. Must be one of: high, low, medium."

    def test_run_unsupported_trait_should_error(self):
        """
        Expected: Unsupported trait on device (e.g., 'lock' on LIGHT) should raise InvalidInputError.
        Current: returns SUCCESS without state change -> FAIL expected.
        """
        # Ensure the test device does not have LockUnlock
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["traits"] = ["OnOff", "Brightness"]

        with pytest.raises(InvalidInputError) as ei:
            run(
                devices=["light-1"],
                op="lock",
            )
        assert str(ei.value) == "Devices do not support trait 'LockUnlock' for op 'lock': light-1"

    def test_run_cancel_schedules_requires_devices_non_empty(self):
        """
        cancel_schedules via run should require at least one device id.
        """
        with pytest.raises(InvalidInputError) as ei:
            run(
                devices=[],
                op="cancel_schedules",
            )
        # Full Pydantic message is verbose; assert the key part is present
        msg = str(ei.value)
        assert msg.startswith("Invalid input:")
        assert "devices" in msg and "at least 1 item" in msg

    def test_show_device_info_should_be_supported_via_run(self):
        """
        Expected: show_device_info (info flow) should be supported by run as per tool spec.
        Current: run rejects 'show_device_info' -> FAIL expected.
        """
        DB["actions"] = []
        results = run(devices=["non-exist"], op="show_device_info")
        assert results and isinstance(results, list)

    def test_run_set_mode_and_temperature_success(self):
        # Add a thermostat device with allowed thermostat modes
        DB["structures"]["Home"]["rooms"]["Living Room"]["devices"].setdefault("THERMOSTAT", []).append(
            {
                "id": "thermo-1",
                "names": ["Thermostat"],
                "types": ["THERMOSTAT"],
                "traits": ["TemperatureSetting"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [
                    {
                        "id": "thermostatMode",
                        "names": ["Thermostat Mode"],
                        "settings": [
                            {"id": "cool", "names": ["Cool"]},
                            {"id": "heat", "names": ["Heat"]},
                        ],
                    }
                ],
                "device_state": [
                    {"name": "thermostatMode", "value": "heat"},
                    {"name": "thermostatTemperatureSetpoint", "value": 20.0},
                ],
            }
        )

        results = run(devices=["thermo-1"], op="set_mode_and_temperature", values=["cool", "25.5"])
        assert results and results[0]["result"] == "SUCCESS"
        device = next(d for d in DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["THERMOSTAT"] if d["id"] == "thermo-1")
        mode = next(s for s in device["device_state"] if s["name"] == "thermostatMode")
        temp = next(s for s in device["device_state"] if s["name"] == "thermostatTemperatureSetpoint")
        assert mode["value"] == "cool"
        assert temp["value"] == 25.5

    def test_run_set_mode_and_temperature_invalid_temp(self):
        # Add a thermostat device if not present
        devices = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"].setdefault("THERMOSTAT", [])
        devices.append(
            {
                "id": "thermo-2",
                "names": ["Thermostat 2"],
                "types": ["THERMOSTAT"],
                "traits": ["TemperatureSetting"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [
                    {
                        "id": "thermostatMode",
                        "names": ["Thermostat Mode"],
                        "settings": [
                            {"id": "cool", "names": ["Cool"]},
                        ],
                    }
                ],
                "device_state": [
                    {"name": "thermostatMode", "value": "cool"},
                    {"name": "thermostatTemperatureSetpoint", "value": 18.0},
                ],
            }
        )
        with pytest.raises(InvalidInputError) as ei:
            run(devices=["thermo-2"], op="set_mode_and_temperature", values=["cool", "abc"])  # invalid temp
        assert str(ei.value).startswith("Invalid input:")

    def test_run_set_mode_success(self):
        # Add a device supporting Modes
        DB["structures"]["Home"]["rooms"]["Living Room"]["devices"].setdefault("AC_UNIT", []).append(
            {
                "id": "ac-2",
                "names": ["AC 2"],
                "types": ["AC_UNIT"],
                "traits": ["Modes"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [
                    {
                        "id": "fanDirection",
                        "names": ["Fan Direction"],
                        "settings": [
                            {"id": "swing", "names": ["Swing"]},
                            {"id": "fixed", "names": ["Fixed"]},
                        ],
                    }
                ],
                "device_state": [],
            }
        )
        results = run(devices=["ac-2"], op="set_mode", values=["fanDirection", "swing"])
        assert results and results[0]["result"] == "SUCCESS"
        device = next(d for d in DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["AC_UNIT"] if d["id"] == "ac-2")
        current_modes = next(s for s in device["device_state"] if s["name"] == "currentModes")
        assert current_modes["value"]["fanDirection"] == "swing"

    def test_run_set_mode_invalid_key_raises(self):
        DB["structures"]["Home"]["rooms"]["Living Room"]["devices"].setdefault("AC_UNIT", []).append(
            {
                "id": "ac-3",
                "names": ["AC 3"],
                "types": ["AC_UNIT"],
                "traits": ["Modes"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [
                    {
                        "id": "fanDirection",
                        "names": ["Fan Direction"],
                        "settings": [
                            {"id": "swing", "names": ["Swing"]},
                        ],
                    }
                ],
                "device_state": [],
            }
        )
        with pytest.raises(InvalidInputError):
            run(devices=["ac-3"], op="set_mode", values=["unknownMode", "anyValue"])  # invalid mode key