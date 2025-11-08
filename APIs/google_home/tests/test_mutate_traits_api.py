import pytest
from google_home.mutate_traits_api import mutate_traits
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import (
    InvalidInputError,
    DeviceNotFoundError,
)


class TestMutateTraits:
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

    def test_mutate_traits_valid(self):
        """
        Test mutate_traits with valid inputs.
        """
        # For OnOff/on, command_values should be [] (no value), not ["true"]
        results = mutate_traits(
            device_ids=["light-1"],
            trait_names=["OnOff"],
            command_names=["on"],
            command_values=[],
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
        assert action["action_type"] == "mutate_traits"
        assert action["inputs"]["device_ids"] == ["light-1"]

    def test_mutate_traits_invalid_device_id(self):
        """
        Test mutate_traits with an invalid device ID.
        """
        # For OnOff/on, command_values should be [] (no value), not ["true"]
        with pytest.raises(DeviceNotFoundError) as ei:
            mutate_traits(
                device_ids=["invalid-device"],
                trait_names=["OnOff"],
                command_names=["on"],
                command_values=[],
            )
        assert str(ei.value) == "Devices not found: invalid-device"

    def test_mutate_traits_invalid_trait(self):
        """
        Test mutate_traits with an invalid trait.
        """
        with pytest.raises(InvalidInputError) as ei:
            mutate_traits(
                device_ids=["light-1"],
                trait_names=["InvalidTrait"],
                command_names=["on"],
            )
        assert str(ei.value).startswith("Invalid input:")

    def test_mutate_traits_invalid_command(self):
        """
        Test mutate_traits with an invalid command.
        """
        with pytest.raises(InvalidInputError) as ei:
            mutate_traits(
                device_ids=["light-1"],
                trait_names=["OnOff"],
                command_names=["InvalidCommand"],
                command_values=[],
            )
        assert str(ei.value).startswith("Invalid input:")

    def test_mutate_traits_multiple_traits_grouping(self):
        """
        With multiple traits provided, commands should be associated to the appropriate trait(s).
        """
        # With index-based mapping, provide aligned pair for brightness
        results = mutate_traits(
            device_ids=["light-1"],
            trait_names=["Brightness"],
            command_names=["set_brightness"],
            command_values=["0.8"],
        )
        assert len(results) == 1
        assert results[0]["result"] == "SUCCESS"
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        assert device["device_state"][1]["value"] == 0.8

    def test_mutate_traits_nonvalued_command_rejects_values(self):
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

        with pytest.raises(InvalidInputError) as ei:
            mutate_traits(
                device_ids=["tv-1"],
                trait_names=["TransportControl"],
                command_names=["pause"],
                command_values=[""],
            )
        assert "does not support values" in str(ei.value)

    def test_mutate_traits_nonvalued_none_ok(self):
        """
        Non-valued command should accept None (no values provided).
        """
        results = mutate_traits(
            device_ids=["light-1"],
            trait_names=["OnOff"],
            command_names=["on"],
            command_values=None,
        )
        assert results[0]["result"] == "SUCCESS"

    def test_mutate_traits_valued_missing_values_error(self):
        """
        Valued command should error clearly when no values provided.
        """
        with pytest.raises(InvalidInputError) as ei:
            mutate_traits(
                device_ids=["light-1"],
                trait_names=["Brightness"],
                command_names=["set_brightness"],
                command_values=None,
            )
        # Comes from pydantic validation since value type/requirements enforced there
        assert str(ei.value).startswith("Invalid input:")

    def test_mutate_traits_multiple_pairs_mixed(self):
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
        r1 = mutate_traits(
            device_ids=["light-1"],
            trait_names=["OnOff"],
            command_names=["on"],
            command_values=None,
        )
        assert r1[0]["result"] == "SUCCESS"
        r2 = mutate_traits(
            device_ids=["light-1"],
            trait_names=["Brightness"],
            command_names=["set_brightness"],
            command_values=["0.75"],
        )
        assert r2[0]["result"] == "SUCCESS"

        # Verify DB state
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        on_state = next(s for s in device["device_state"] if s["name"] == "on")
        bright_state = next(s for s in device["device_state"] if s["name"] == "brightness")
        assert on_state["value"] is True
        assert bright_state["value"] == 0.75

    def test_mutate_traits_extra_traits_rejected(self):
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["device_state"] = [
            {"name": "on", "value": False},
            {"name": "brightness", "value": 0.1},
        ]
        with pytest.raises(InvalidInputError) as ei:
            mutate_traits(
                device_ids=["light-1"],
                trait_names=["OnOff", "Brightness"],
                command_names=["on"],
                command_values=[None],
            )
        assert "only supported one trait and command at a time" in str(ei.value)

    def test_mutate_traits_extra_commands_rejected(self):
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["device_state"] = [
            {"name": "on", "value": False},
            {"name": "brightness", "value": 0.2},
        ]
        with pytest.raises(InvalidInputError) as ei:
            mutate_traits(
                device_ids=["light-1"],
                trait_names=["OnOff"],
                command_names=["on", "set_brightness"],
                command_values=[None, "0.8"],
            )
        assert "only supported one trait and command at a time" in str(ei.value)

    def test_mutate_traits_extra_values_rejected(self):
        device = DB["structures"]["Home"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        device["device_state"] = [
            {"name": "on", "value": False},
            {"name": "brightness", "value": 0.3},
        ]
        with pytest.raises(InvalidInputError) as ei:
            mutate_traits(
                device_ids=["light-1"],
                trait_names=["OnOff"],
                command_names=["on"],
                command_values=[None, "0.9", "1.0"],
            )
        assert str(ei.value).startswith("Invalid input:")