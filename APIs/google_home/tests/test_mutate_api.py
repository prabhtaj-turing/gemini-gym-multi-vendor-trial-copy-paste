import pytest
from google_home.mutate_api import mutate
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import (
    InvalidInputError,
    DeviceNotFoundError,
)
from pydantic import ValidationError


class TestMutate:
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

    def test_mutate_valid(self):
        """
        Test mutate with valid inputs.
        """
        # The new validation requires that "on" does NOT have values
        results = mutate(
            devices=["light-1"],
            traits=["OnOff"],
            commands=["on"],
            values=[],  # No values for "on"
        )
        assert len(results) == 1
        assert results[0]["result"] == "SUCCESS"
        assert results[0]["commands"]["device_ids"] == ["light-1"]

        # Verify that the device state was updated
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        on_state = next(s for s in device["device_state"] if s["name"] == "on")
        assert on_state["value"] is True

        # Verify that the action was logged
        assert len(DB["actions"]) == 1
        action = DB["actions"][0]
        assert action["action_type"] == "mutate"
        assert action["inputs"]["devices"] == ["light-1"]

    def test_mutate_invalid_device_id(self):
        """
        Test mutate with an invalid device ID.
        """
        # The new validation will fail on input if values are provided for "on"
        with pytest.raises(DeviceNotFoundError) as ei:
            mutate(
                devices=["invalid-device"],
                traits=["OnOff"],
                commands=["on"],
                values=[],  # No values for "on"
            )
        assert str(ei.value) == "Devices not found: invalid-device"

    def test_mutate_invalid_trait(self):
        """
        Test mutate with an invalid trait.
        """
        # The new model validation may raise ValidationError or InvalidInputError
        with pytest.raises(InvalidInputError) as ei:
            mutate(
                devices=["light-1"],
                traits=["InvalidTrait"],
                commands=["on"],
                values=[],  # No values for "on"
            )
        assert str(ei.value).startswith("Invalid input:")

    def test_mutate_invalid_command(self):
        """
        Test mutate with an invalid command.
        """
        # The new model validation may raise ValidationError or InvalidInputError
        with pytest.raises(InvalidInputError) as ei:
            mutate(
                devices=["light-1"],
                traits=["OnOff"],
                commands=["InvalidCommand"],
                values=[],  # No values for "on"
            )
        assert str(ei.value).startswith("Invalid input:")

    def test_mutate_multiple_traits_command_mapped_correctly(self):
        """
        Passing multiple traits with a command should group under the valid trait(s).
        """
        # Add a device that supports OnOff and Brightness
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert "OnOff" in device["traits"] and "Brightness" in device["traits"]

        # Command set_brightness should be grouped under Brightness even if both traits provided
        # With index-based mapping, inputs must be aligned 1:1. Provide the correct pair.
        results = mutate(
            devices=["light-1"],
            traits=["Brightness"],
            commands=["set_brightness"],
            values=["0.6"],
        )
        assert results[0]["result"] == "SUCCESS"
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        brightness_state = next(s for s in device["device_state"] if s["name"] == "brightness")
        assert brightness_state["value"] == 0.6

    def test_mutate_nonvalued_command_rejects_values(self):
        """
        Non-valued command (pause) must reject any provided values, including empty strings.
        """
        # Add a TV with TransportControl
        DB["structures"]["Home"]["rooms"]["Living Room"]["devices"].setdefault("TV", []).append(
            {
                "id": "tv-1",
                "names": ["TV"],
                "types": ["TV"],
                "traits": ["TransportControl"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [],
                "device_state": [
                    {"name": "isPaused", "value": False},
                    {"name": "isStopped", "value": True},
                ],
            }
        )

        with pytest.raises((InvalidInputError, ValidationError)) as ei:
            mutate(
                devices=["tv-1"],
                traits=["TransportControl"],
                commands=["pause"],
                values=[""],
            )
        assert "does not support values" in str(ei.value)

    def test_mutate_brightness_out_of_range_shows_range_error(self):
        """
        set_brightness with -1 should surface a clear range error message.
        """
        with pytest.raises((InvalidInputError, ValidationError)) as ei:
            mutate(
                devices=["light-1"],
                traits=["Brightness"],
                commands=["set_brightness"],
                values=["-1"],
            )
        msg = str(ei.value)
        assert msg.startswith("Invalid input:") and "set_brightness" in msg and "between" in msg

    def test_mutate_nonvalued_none_ok(self):
        """
        Non-valued command should accept None (no values provided).
        """
        results = mutate(
            devices=["light-1"],
            traits=["OnOff"],
            commands=["on"],
            values=None,
        )
        assert results[0]["result"] == "SUCCESS"

    def test_mutate_valued_missing_values_error(self):
        """
        Valued command should error clearly when no values provided.
        """
        with pytest.raises((InvalidInputError, ValidationError)) as ei:
            mutate(
                devices=["light-1"],
                traits=["Brightness"],
                commands=["set_brightness"],
                values=None,
            )
        msg = str(ei.value)
        assert msg.startswith("Invalid input:")

    def test_mutate_multiple_pairs_mixed(self):
        """
        Multiple zip pairs: OnOff/on (no value) and Brightness/set_brightness (valued).
        """
        # Reset device state
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["device_state"] = [
            {"name": "on", "value": False},
            {"name": "brightness", "value": 0.0},
        ]

        # Perform two single-pair mutations per new behavior
        r1 = mutate(
            devices=["light-1"],
            traits=["OnOff"],
            commands=["on"],
            values=None,
        )
        assert r1[0]["result"] == "SUCCESS"
        r2 = mutate(
            devices=["light-1"],
            traits=["Brightness"],
            commands=["set_brightness"],
            values=["0.4"],
        )
        assert r2[0]["result"] == "SUCCESS"

        # Verify DB state reflects both mutations
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        on_state = next(s for s in device["device_state"] if s["name"] == "on")
        bright_state = next(s for s in device["device_state"] if s["name"] == "brightness")
        assert on_state["value"] is True
        assert bright_state["value"] == 0.4

    def test_mutate_extra_traits_rejected(self):
        with pytest.raises(InvalidInputError) as ei:
            mutate(
                devices=["light-1"],
                traits=["OnOff", "Brightness"],
                commands=["on"],
                values=[None],
            )
        assert "only supported one trait and command at a time" in str(ei.value)

    def test_mutate_extra_commands_rejected(self):
        with pytest.raises(InvalidInputError) as ei:
            mutate(
                devices=["light-1"],
                traits=["OnOff"],
                commands=["on", "set_brightness"],
                values=[None, "0.8"],
            )
        assert "only supported one trait and command at a time" in str(ei.value)

    def test_mutate_extra_values_rejected(self):
        with pytest.raises(InvalidInputError) as ei:
            mutate(
                devices=["light-1"],
                traits=["OnOff"],
                commands=["on"],
                values=[None, "0.9", "1.0"],
            )
        assert str(ei.value).startswith("Invalid input:")

    def test_mutate_on_rejects_empty_string_value(self):
        with pytest.raises((InvalidInputError, ValidationError)) as ei:
            mutate(
                devices=["light-1"],
                traits=["OnOff"],
                commands=["on"],
                values=[""],
            )
        assert "does not support values" in str(ei.value)

    def test_mutate_set_brightness_empty_string_number_error(self):
        with pytest.raises((InvalidInputError, ValidationError)) as ei:
            mutate(
                devices=["light-1"],
                traits=["Brightness"],
                commands=["set_brightness"],
                values=[""],
            )
        assert "valid number" in str(ei.value)

    def test_mutate_multiple_devices_multi_pairs(self):
        # Add a second light device
        DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"].append(
            {
                "id": "light-2",
                "names": ["Living Room Light 2"],
                "types": ["LIGHT"],
                "traits": ["OnOff", "Brightness"],
                "room_name": "Living Room",
                "structure": "Home",
                "toggles_modes": [],
                "device_state": [
                    {"name": "on", "value": False},
                    {"name": "brightness", "value": 0.0},
                ],
            }
        )

        r1 = mutate(
            devices=["light-1", "light-2"],
            traits=["OnOff"],
            commands=["on"],
            values=None,
        )
        assert len(r1) == 2 and all(r["result"] == "SUCCESS" for r in r1)
        r2 = mutate(
            devices=["light-1", "light-2"],
            traits=["Brightness"],
            commands=["set_brightness"],
            values=["0.55"],
        )
        assert len(r2) == 2 and all(r["result"] == "SUCCESS" for r in r2)
        for light_id in ["light-1", "light-2"]:
            d = next(d for d in DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"] if d["id"] == light_id)
            on_state = next(s for s in d["device_state"] if s["name"] == "on")
            bright_state = next(s for s in d["device_state"] if s["name"] == "brightness")
            assert on_state["value"] is True
            assert bright_state["value"] == 0.55