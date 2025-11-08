"""
Comprehensive TDD test cases for Google Home porting functionality.
Tests critical data transformations and validation contracts.
"""

import json
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
ROOT = Path(__file__).resolve().parents[3]
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

# Import the function under test
from Scripts.porting.port_google_home import port_google_home


class TestGoogleHomePortingTDD:
    """Google Home porting tests written with TDD principles - testing critical transformations"""

    def get_minimal_valid_structure(self):
        """Get minimal valid Google Home structure for testing."""
        return {
            "structures": {
                "house": {
                    "name": "house",
                    "rooms": {
                        "Living Room": {
                            "name": "Living Room",
                            "devices": {
                                "LIGHT": [
                                    {
                                        "id": "light_001",
                                        "names": ["Living Room Light"],
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff"],
                                        "room_name": "Living Room",
                                        "structure": "house",
                                        "toggles_modes": [],
                                        "device_state": [
                                            {"name": "on", "value": False}
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

    # Test Case 1: Structure extraction must get the first structure only (TDD)
    def test_structure_extraction_takes_first_structure_only(self):
        """Structure extraction must consistently take the first structure from vendor data"""
        test_data = {
            "structures": {
                "first_house": {
                    "name": "First House",
                    "rooms": {
                        "Room1": {
                            "name": "Room1",
                            "devices": {"LIGHT": []}
                        }
                    }
                },
                "second_house": {
                    "name": "Second House", 
                    "rooms": {
                        "Room2": {
                            "name": "Room2",
                            "devices": {"LIGHT": []}
                        }
                    }
                },
                "third_house": {
                    "name": "Third House",
                    "rooms": {
                        "Room3": {
                            "name": "Room3", 
                            "devices": {"LIGHT": []}
                        }
                    }
                }
            }
        }

        result, message = port_google_home(json.dumps(test_data))
        assert result is not None, f"Structure extraction should not fail: {message}"
        
        # MUST use only the first structure
        assert "first_house" in result["structures"], "Must use first structure key"
        assert "second_house" not in result["structures"], "Must not include second structure"
        assert "third_house" not in result["structures"], "Must not include third structure"
        
        # MUST preserve the structure name
        assert result["structures"]["first_house"]["name"] == "First House"
        
        # MUST include only rooms from first structure
        assert "Room1" in result["structures"]["first_house"]["rooms"]
        assert "Room2" not in result["structures"]["first_house"]["rooms"]
        assert "Room3" not in result["structures"]["first_house"]["rooms"]

    def test_structure_extraction_handles_missing_structures(self):
        """Structure extraction must fail gracefully when structures are missing"""
        invalid_inputs = [
            {},  # No structures key
            {"structures": {}},  # Empty structures
            {"other_key": "value"},  # Wrong top-level key
            {"structures": None},  # Null structures
        ]

        for invalid_input in invalid_inputs:
            result, message = port_google_home(json.dumps(invalid_input))
            
            # MUST fail gracefully with clear error message
            assert result is None, f"Missing structures should be rejected: {invalid_input}"
            assert "structure" in message.lower(), f"Error should mention structures: {message}"

    # Test Case 2: Device state transformation must handle "off" to "on" conversion (TDD)
    def test_device_state_off_to_on_transformation(self):
        """Device state 'off' must be converted to 'on' with inverted boolean value"""
        test_data = self.get_minimal_valid_structure()
        
        # Test various "off" state scenarios
        off_state_cases = [
            ({"name": "off", "value": True}, {"name": "on", "value": False}),   # True off -> False on
            ({"name": "off", "value": False}, {"name": "on", "value": True}),  # False off -> True on
            ({"name": "off", "value": 1}, {"name": "on", "value": False}),     # Truthy off -> False on
            ({"name": "off", "value": 0}, {"name": "on", "value": True}),      # Falsy off -> True on
            ({"name": "off", "value": "yes"}, {"name": "on", "value": False}), # String truthy -> False on
            ({"name": "off", "value": ""}, {"name": "on", "value": True}),     # String falsy -> True on
        ]

        for input_state, expected_state in off_state_cases:
            test_data["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"] = [input_state]
            
            result, message = port_google_home(json.dumps(test_data))
            assert result is not None, f"Off->On transformation should not fail: {message}"
            
            device_states = result["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"]
            
            # MUST convert "off" to "on" with inverted boolean
            assert len(device_states) == 1, "Should have exactly one transformed state"
            assert device_states[0]["name"] == expected_state["name"], f"State name should be 'on', got {device_states[0]['name']}"
            assert device_states[0]["value"] == expected_state["value"], \
                f"Value should be inverted boolean: expected {expected_state['value']}, got {device_states[0]['value']}"

    def test_device_state_preserves_non_off_states(self):
        """Device state transformation must preserve all non-'off' states unchanged"""
        test_data = self.get_minimal_valid_structure()
        
        # Test various non-off states that should be preserved (using valid state names and matching traits)
        preserved_state_cases = [
            # OnOff trait states
            ({"name": "on", "value": True}, ["OnOff"]),
            ({"name": "on", "value": False}, ["OnOff"]),
            # Brightness trait states (need both OnOff and Brightness traits)
            # Brightness must be 0.0-1.0 range per model validation
            ({"name": "brightness", "value": 0.5}, ["OnOff", "Brightness"]),
            ({"name": "brightness", "value": 1.0}, ["OnOff", "Brightness"]),
        ]

        for original_state, required_traits in preserved_state_cases:
            # Update device traits to match the state being tested
            test_data["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["traits"] = required_traits
            test_data["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"] = [original_state]
            
            result, message = port_google_home(json.dumps(test_data))
            assert result is not None, f"State preservation should not fail for {original_state}: {message}"
            
            device_states = result["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"]
            
            # MUST preserve non-off states exactly
            assert len(device_states) == 1, "Should have exactly one preserved state"
            assert device_states[0] == original_state, \
                f"Non-off state should be preserved exactly: expected {original_state}, got {device_states[0]}"

    # Test Case 3: Float conversion must happen for specific state names (TDD)
    def test_float_conversion_for_numeric_states(self):
        """Numeric values must be converted to float for brightness, thermostatTemperatureAmbient, thermostatTemperatureSetpoint, openPercent"""
        # Test float conversion for specific state names with appropriate device types and traits
        float_conversion_cases = [
            # Brightness state (LIGHT device with Brightness trait) - normalized to 0.0-1.0
            ("brightness", 50, 0.5, "LIGHT", ["OnOff", "Brightness"]),  # 50% -> 0.5
            ("brightness", 75.5, 0.755, "LIGHT", ["OnOff", "Brightness"]),  # 75.5% -> 0.755
            # Note: String values for numeric states will fail validation, which is correct behavior
            # Thermostat temperature (THERMOSTAT device with TemperatureSetting trait)
            ("thermostatTemperatureAmbient", 72, 72.0, "THERMOSTAT", ["TemperatureSetting"]),
            ("thermostatTemperatureAmbient", 68.5, 68.5, "THERMOSTAT", ["TemperatureSetting"]),
            ("thermostatTemperatureSetpoint", 75, 75.0, "THERMOSTAT", ["TemperatureSetting"]),
            # openPercent state (BLINDS device with OpenClose trait)
            ("openPercent", 50, 50.0, "BLINDS", ["OpenClose"]),
            ("openPercent", 45.7, 45.7, "BLINDS", ["OpenClose"]),
        ]

        for state_name, input_value, expected_value, device_type, device_traits in float_conversion_cases:
            # Create test data with appropriate device type and traits
            test_data = {
                "structures": {
                    "house": {
                        "name": "house",
                        "rooms": {
                            "Living Room": {
                                "name": "Living Room",
                                "devices": {
                                    device_type: [
                                        {
                                            "id": f"{device_type.lower()}_001",
                                            "names": [f"Living Room {device_type}"],
                                            "types": [device_type],
                                            "traits": device_traits,
                                            "room_name": "Living Room",
                                            "structure": "house",
                                            "toggles_modes": [],
                                            "device_state": [{"name": state_name, "value": input_value}]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
            
            result, message = port_google_home(json.dumps(test_data))
            assert result is not None, f"Float conversion should not fail for {state_name}: {message}"
            
            device_states = result["structures"]["house"]["rooms"]["Living Room"]["devices"][device_type][0]["device_state"]
            actual_value = device_states[0]["value"]
            
            # MUST convert to float for numeric states
            assert actual_value == expected_value, \
                f"State {state_name} should convert {input_value} to {expected_value}, got {actual_value}"
            if state_name in ["brightness", "thermostatTemperatureAmbient", "thermostatTemperatureSetpoint", "openPercent"]:
                assert isinstance(actual_value, float), \
                    f"State {state_name} should be float type, got {type(actual_value)}"

    def test_float_conversion_ignores_non_float_states(self):
        """Float conversion must only apply to specific state names, not all numeric values"""
        # Test that other numeric states are NOT converted to float (using valid state names and device types)
        non_float_state_cases = [
            # OnOff states should remain as booleans
            ("on", True, "LIGHT", ["OnOff"]),
            ("on", False, "LIGHT", ["OnOff"]),
            # Note: integers for boolean states will fail validation, which is correct
            # Thermostat mode (string state, should not be converted)
            ("thermostatMode", "heat", "THERMOSTAT", ["TemperatureSetting"]),
            ("thermostatMode", "cool", "THERMOSTAT", ["TemperatureSetting"]),
            # Integer states (fanSpeed, currentVolume, humiditySetting) should become ints
            ("fanSpeed", 3, "FAN", ["FanSpeed"]),
            ("currentVolume", 50, "SPEAKER", ["Volume"]),
            ("humiditySetting", 45, "THERMOSTAT", ["HumiditySetting"]),
            # Boolean states that should not be converted
            ("isMuted", True, "SPEAKER", ["Volume"]),
            ("isMuted", False, "SPEAKER", ["Volume"]),
        ]

        for state_name, input_value, device_type, device_traits in non_float_state_cases:
            # Create test data with appropriate device type and traits
            test_data = {
                "structures": {
                    "house": {
                        "name": "house",
                        "rooms": {
                            "Living Room": {
                                "name": "Living Room",
                                "devices": {
                                    device_type: [
                                        {
                                            "id": f"{device_type.lower()}_001",
                                            "names": [f"Living Room {device_type}"],
                                            "types": [device_type],
                                            "traits": device_traits,
                                            "room_name": "Living Room",
                                            "structure": "house",
                                            "toggles_modes": [],
                                            "device_state": [{"name": state_name, "value": input_value}]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
            
            result, message = port_google_home(json.dumps(test_data))
            assert result is not None, f"Non-float state processing should not fail for {state_name}: {message}"
            
            device_states = result["structures"]["house"]["rooms"]["Living Room"]["devices"][device_type][0]["device_state"]
            actual_value = device_states[0]["value"]
            
            # MUST NOT convert to float for non-float states
            # Integer states (fanSpeed, currentVolume, humiditySetting) should be converted to int
            if state_name in ["fanSpeed", "currentVolume", "humiditySetting"]:
                assert isinstance(actual_value, int), \
                    f"State {state_name} should be int type, got {type(actual_value)}"
                assert actual_value == input_value, \
                    f"Integer state {state_name} should preserve value: expected {input_value}, got {actual_value}"
            else:
                assert actual_value == input_value, \
                    f"Non-float state {state_name} should preserve original value: expected {input_value}, got {actual_value}"
                assert type(actual_value) == type(input_value), \
                    f"Non-float state {state_name} should preserve original type: expected {type(input_value)}, got {type(actual_value)}"

    # Test Case 4: Device property copying must exclude device_state only (TDD)
    def test_device_property_copying_excludes_device_state_only(self):
        """Device property copying must preserve all valid DeviceInfo properties except device_state"""
        test_data = self.get_minimal_valid_structure()
        
        # Add comprehensive device properties (only valid DeviceInfo fields)
        device_with_all_properties = {
            "id": "complex_device_001",
            "names": ["Complex Device", "Alias Device"],
            "types": ["LIGHT"],
            "traits": ["OnOff", "Brightness"],
            "room_name": "Living Room", 
            "structure": "house",
            "toggles_modes": [
                {
                    "id": "lightMode",
                    "names": ["Light Mode"],
                    "settings": [
                        {"id": "normal", "names": ["Normal"]},
                        {"id": "dim", "names": ["Dim"]}
                    ]
                }
            ],
            "device_state": [  # This should be excluded and transformed
                {"name": "on", "value": True},
                {"name": "brightness", "value": 75}
            ]
        }
        
        test_data["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0] = device_with_all_properties
        
        result, message = port_google_home(json.dumps(test_data))
        assert result is not None, f"Property copying should not fail: {message}"
        
        result_device = result["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        
        # MUST preserve all valid DeviceInfo properties except device_state
        expected_properties = {k: v for k, v in device_with_all_properties.items() if k != "device_state"}
        
        for prop_name, expected_value in expected_properties.items():
            assert prop_name in result_device, f"Property {prop_name} should be preserved"
            assert result_device[prop_name] == expected_value, \
                f"Property {prop_name} should be preserved exactly: expected {expected_value}, got {result_device[prop_name]}"
        
        # MUST transform device_state separately (not copy original)
        assert "device_state" in result_device, "device_state should exist but be transformed"
        # Check that brightness was converted to float and normalized (75 -> 0.75)
        brightness_state = next(s for s in result_device["device_state"] if s["name"] == "brightness")
        assert isinstance(brightness_state["value"], float), "brightness value should be converted to float"
        assert brightness_state["value"] == 0.75, "brightness value should be 0.75 (normalized from 75)"

    def test_device_property_copying_handles_missing_toggles_modes(self):
        """Device property copying must add empty toggles_modes if missing"""
        test_data = self.get_minimal_valid_structure()
        
        # Remove toggles_modes from device
        device = test_data["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        if "toggles_modes" in device:
            del device["toggles_modes"]
        
        result, message = port_google_home(json.dumps(test_data))
        assert result is not None, f"Missing toggles_modes handling should not fail: {message}"
        
        result_device = result["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]
        
        # MUST add empty toggles_modes if missing
        assert "toggles_modes" in result_device, "toggles_modes should be added if missing"
        assert result_device["toggles_modes"] == [], "toggles_modes should be empty list when added"

    # Test Case 5: Multiple device state transformations must work correctly (TDD)
    def test_multiple_device_state_transformations(self):
        """Multiple device states must be transformed according to their individual rules"""
        # Use a THERMOSTAT device which can have multiple different state types
        test_data = {
            "structures": {
                "house": {
                    "name": "house",
                    "rooms": {
                        "Living Room": {
                            "name": "Living Room",
                            "devices": {
                                "THERMOSTAT": [
                                    {
                                        "id": "thermo_001",
                                        "names": ["Living Room Thermostat"],
                                        "types": ["THERMOSTAT"],
                                        "traits": ["TemperatureSetting", "OnOff"],
                                        "room_name": "Living Room",
                                        "structure": "house",
                                        "toggles_modes": [],
                                        "device_state": [
                                            {"name": "off", "value": True},                        # Should become on: False
                                            {"name": "thermostatTemperatureAmbient", "value": 72}, # Should become 72.0 (float)
                                            {"name": "on", "value": False},                        # Should remain on: False
                                            {"name": "thermostatMode", "value": "heat"},           # Should remain unchanged (string)
                                            {"name": "off", "value": False},                       # Should become on: True
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        
        result, message = port_google_home(json.dumps(test_data))
        assert result is not None, f"Multiple state transformation should not fail: {message}"
        
        result_states = result["structures"]["house"]["rooms"]["Living Room"]["devices"]["THERMOSTAT"][0]["device_state"]
        
        # MUST transform each state according to its specific rules
        expected_states = [
            {"name": "on", "value": False},                         # off: True -> on: False
            {"name": "thermostatTemperatureAmbient", "value": 72.0}, # temp: 72 -> temp: 72.0 (float)
            {"name": "on", "value": False},                         # on: False -> on: False (unchanged)
            {"name": "thermostatMode", "value": "heat"},            # mode: "heat" -> unchanged (string)
            {"name": "on", "value": True},                          # off: False -> on: True
        ]
        
        assert len(result_states) == len(expected_states), \
            f"Should have {len(expected_states)} transformed states, got {len(result_states)}"
        
        for i, (actual, expected) in enumerate(zip(result_states, expected_states)):
            assert actual == expected, \
                f"State {i} transformation failed: expected {expected}, got {actual}"

    # Test Case 6: Required fields must be added to output structure (TDD)
    def test_required_fields_added_to_output(self):
        """Output structure must include all required fields for GoogleHomeDB validation"""
        test_data = self.get_minimal_valid_structure()
        
        result, message = port_google_home(json.dumps(test_data))
        assert result is not None, f"Required fields addition should not fail: {message}"
        
        # MUST have top-level structures
        assert "structures" in result, "Missing required top-level 'structures'"
        assert isinstance(result["structures"], dict), "structures must be a dict"
        
        # MUST have actions array for GoogleHomeDB
        assert "actions" in result, "Missing required top-level 'actions'"
        assert isinstance(result["actions"], list), "actions must be a list"
        assert result["actions"] == [], "actions should be empty list by default"
        
        # MUST preserve structure hierarchy
        structure_key = list(result["structures"].keys())[0]
        structure = result["structures"][structure_key]
        
        assert "name" in structure, "Structure missing 'name'"
        assert "rooms" in structure, "Structure missing 'rooms'"
        assert isinstance(structure["rooms"], dict), "Structure rooms must be dict"
        
        # MUST preserve room hierarchy
        room_key = list(structure["rooms"].keys())[0]
        room = structure["rooms"][room_key]
        
        assert "name" in room, "Room missing 'name'"
        assert "devices" in room, "Room missing 'devices'"
        assert isinstance(room["devices"], dict), "Room devices must be dict"

    def test_required_fields_structure_validation(self):
        """Structure hierarchy must exactly match GoogleHomeDB schema requirements"""
        test_data = {
            "structures": {
                "multi_room_house": {
                    "name": "Multi Room House",
                    "rooms": {
                        "Kitchen": {
                            "name": "Kitchen",
                            "devices": {
                                "THERMOSTAT": [
                                    {
                                        "id": "thermo_001",
                                        "names": ["Kitchen Thermostat"],
                                        "types": ["THERMOSTAT"],
                                        "traits": ["TemperatureSetting"],
                                        "room_name": "Kitchen",
                                        "structure": "multi_room_house",
                                        "device_state": [
                                            {"name": "thermostatMode", "value": "heat"},
                                            {"name": "thermostatTemperatureAmbient", "value": 68}
                                        ]
                                    }
                                ],
                                "LIGHT": [
                                    {
                                        "id": "light_002",
                                        "names": ["Kitchen Light"],
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff", "Brightness"],
                                        "room_name": "Kitchen",
                                        "structure": "multi_room_house",
                                        "device_state": [
                                            {"name": "on", "value": True},
                                            {"name": "brightness", "value": 90}
                                        ]
                                    }
                                ]
                            }
                        },
                        "Bedroom": {
                            "name": "Bedroom",
                            "devices": {
                                "FAN": [
                                    {
                                        "id": "fan_001",
                                        "names": ["Bedroom Fan"],
                                        "types": ["FAN"],
                                        "traits": ["OnOff", "FanSpeed"],
                                        "room_name": "Bedroom",
                                        "structure": "multi_room_house",
                                        "device_state": [
                                            {"name": "off", "value": True},  # Should be transformed
                                            {"name": "fanSpeed", "value": 3}  # Should be float
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        
        result, message = port_google_home(json.dumps(test_data))
        assert result is not None, f"Complex structure validation should not fail: {message}"
        
        # MUST validate against GoogleHomeDB schema (implicit via pydantic)
        # If we reach here, pydantic validation passed
        
        # MUST preserve all rooms and devices
        structure = result["structures"]["multi_room_house"]
        assert len(structure["rooms"]) == 2, "Should preserve both rooms"
        assert "Kitchen" in structure["rooms"], "Should preserve Kitchen"
        assert "Bedroom" in structure["rooms"], "Should preserve Bedroom"
        
        # MUST preserve device types within rooms
        kitchen_devices = structure["rooms"]["Kitchen"]["devices"]
        assert "THERMOSTAT" in kitchen_devices, "Should preserve THERMOSTAT devices"
        assert "LIGHT" in kitchen_devices, "Should preserve LIGHT devices"
        assert len(kitchen_devices["THERMOSTAT"]) == 1, "Should have one thermostat"
        assert len(kitchen_devices["LIGHT"]) == 1, "Should have one light"
        
        bedroom_devices = structure["rooms"]["Bedroom"]["devices"]
        assert "FAN" in bedroom_devices, "Should preserve FAN devices"
        assert len(bedroom_devices["FAN"]) == 1, "Should have one fan"
        
        # MUST apply transformations correctly across all devices
        # Check thermostat (temperature should be float if it was an integer)
        thermo_states = kitchen_devices["THERMOSTAT"][0]["device_state"]
        temp_state = next(s for s in thermo_states if s["name"] == "thermostatTemperatureAmbient")
        # Note: The original value was 68 (int), so it should be converted to 68.0 (float)
        assert isinstance(temp_state["value"], float), "Temperature should be converted to float"
        assert temp_state["value"] == 68.0, "Temperature value should be preserved as float"
        
        # Check light (brightness should be float and normalized)
        light_states = kitchen_devices["LIGHT"][0]["device_state"]
        brightness_state = next(s for s in light_states if s["name"] == "brightness")
        assert isinstance(brightness_state["value"], float), "Brightness should be converted to float"
        assert brightness_state["value"] == 0.9, "Brightness value should be 0.9 (normalized from 90)"
        
        # Check fan (off->on transformation and fanSpeed int conversion)
        fan_states = bedroom_devices["FAN"][0]["device_state"]
        on_state = next(s for s in fan_states if s["name"] == "on")
        fanspeed_state = next(s for s in fan_states if s["name"] == "fanSpeed")
        
        assert on_state["value"] == False, "off: True should become on: False"
        assert isinstance(fanspeed_state["value"], int), "fanSpeed should be converted to int"
        assert fanspeed_state["value"] == 3, "fanSpeed value should be preserved as int"

    # Test Case 7: Error handling must be comprehensive and helpful (TDD)
    def test_error_handling_invalid_json(self):
        """Error handling must provide clear messages for invalid JSON input"""
        invalid_json_cases = [
            '{"invalid": json}',           # Malformed JSON
            '{"structures": {"house": {',  # Incomplete JSON
            '{"structures":}',             # Syntax error
            '',                            # Empty string
            'not json at all',             # Plain text
        ]

        for invalid_json in invalid_json_cases:
            result, message = port_google_home(invalid_json)
            
            # MUST fail gracefully with helpful error
            assert result is None, f"Invalid JSON should be rejected: {invalid_json[:20]}..."
            assert "JSON" in message or "json" in message, f"Error should mention JSON: {message}"
            assert len(message) > 0, "Error message should not be empty"

    def test_error_handling_missing_required_data(self):
        """Error handling must validate required data structure"""
        missing_data_cases = [
            ({}, "No structures"),
            ({"structures": {}}, "Empty structures"),
            ({"structures": None}, "Null structures"),
            ({"wrong_key": {}}, "Wrong top-level key"),
        ]

        for invalid_data, description in missing_data_cases:
            result, message = port_google_home(json.dumps(invalid_data))
            
            # MUST fail gracefully with descriptive error
            assert result is None, f"Missing data should be rejected: {description}"
            assert len(message) > 0, f"Error message should not be empty for: {description}"
            
        # Test cases that should succeed but create empty structures
        acceptable_empty_cases = [
            ({"structures": {"house": {}}}, "Missing rooms"),
            ({"structures": {"house": {"rooms": {}}}}, "Empty rooms"),
        ]
        
        for valid_data, description in acceptable_empty_cases:
            result, message = port_google_home(json.dumps(valid_data))
            
            # These should succeed and create valid empty structures
            assert result is not None, f"Empty but valid data should succeed: {description}"
            assert "structures" in result, f"Should have structures: {description}"
            assert "actions" in result, f"Should have actions: {description}"

    def test_error_handling_pydantic_validation_failure(self):
        """Error handling must catch and report pydantic validation failures"""
        # Create data that will pass JSON parsing but fail pydantic validation
        invalid_structure_data = {
            "structures": {
                "house": {
                    "name": "house",
                    "rooms": {
                        "Living Room": {
                            "name": "Living Room",
                            "devices": {
                                "LIGHT": [
                                    {
                                        "id": "light_001",
                                        "names": "invalid_names_should_be_list",  # Should be list, not string
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff"],
                                        "room_name": "Living Room",
                                        "structure": "house",
                                        "device_state": [
                                            {"name": "on", "value": "invalid_boolean"}  # Should be boolean
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }

        result, message = port_google_home(json.dumps(invalid_structure_data))
        
        # MUST catch pydantic validation errors gracefully
        assert result is None, "Pydantic validation failure should be caught"
        assert "Validation error" in message or "validation" in message.lower(), \
            f"Error should mention validation: {message}"

    # Test Case 8: Edge cases and boundary conditions (TDD)
    def test_edge_case_empty_device_states(self):
        """Empty device states must be handled correctly"""
        test_data = self.get_minimal_valid_structure()
        test_data["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"] = []
        
        result, message = port_google_home(json.dumps(test_data))
        assert result is not None, f"Empty device states should not fail: {message}"
        
        result_states = result["structures"]["house"]["rooms"]["Living Room"]["devices"]["LIGHT"][0]["device_state"]
        assert result_states == [], "Empty device states should remain empty"

    def test_edge_case_deeply_nested_room_structure(self):
        """Complex nested room structures must be preserved correctly"""
        complex_data = {
            "structures": {
                "mansion": {
                    "name": "Luxury Mansion",
                    "rooms": {
                        "Master Suite": {
                            "name": "Master Suite",
                            "devices": {
                                "THERMOSTAT": [
                                    {
                                        "id": "thermo_master",
                                        "names": ["Master Thermostat", "Bedroom Climate"],
                                        "types": ["THERMOSTAT"],
                                        "traits": ["TemperatureSetting", "HumiditySetting", "OnOff"],
                                        "room_name": "Master Suite",
                                        "structure": "mansion",
                                        "toggles_modes": [
                                            {
                                                "id": "thermostatMode",
                                                "names": ["Thermostat Mode"],
                                                "settings": [
                                                    {"id": "off", "names": ["Off"]},
                                                    {"id": "heat", "names": ["Heat"]},
                                                    {"id": "cool", "names": ["Cool"]}
                                                ]
                                            }
                                        ],
                                        "device_state": [
                                            {"name": "thermostatMode", "value": "heat"},
                                            {"name": "thermostatTemperatureAmbient", "value": 72},
                                            {"name": "humiditySetting", "value": 45},
                                            {"name": "off", "value": False}  # Should be transformed
                                        ]
                                    }
                                ],
                                "LIGHT": [
                                    {
                                        "id": "light_master_main",
                                        "names": ["Master Ceiling Light"],
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff", "Brightness", "ColorSetting"],
                                        "room_name": "Master Suite",
                                        "structure": "mansion",
                                        "device_state": [
                                            {"name": "on", "value": True},
                                            {"name": "brightness", "value": 85},
                                            {"name": "color", "value": "warm_white"}
                                        ]
                                    },
                                    {
                                        "id": "light_master_accent",
                                        "names": ["Master Accent Lights"],
                                        "types": ["LIGHT"],
                                        "traits": ["OnOff", "Brightness"],
                                        "room_name": "Master Suite",
                                        "structure": "mansion",
                                        "device_state": [
                                            {"name": "off", "value": True},  # Should be transformed
                                            {"name": "brightness", "value": 30}
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        
        result, message = port_google_home(json.dumps(complex_data))
        assert result is not None, f"Complex nested structure should not fail: {message}"
        
        # MUST preserve all nested structure
        mansion = result["structures"]["mansion"]
        assert mansion["name"] == "Luxury Mansion", "Structure name should be preserved"
        
        master_suite = mansion["rooms"]["Master Suite"]
        assert master_suite["name"] == "Master Suite", "Room name should be preserved"
        
        devices = master_suite["devices"]
        assert len(devices["THERMOSTAT"]) == 1, "Should have one thermostat"
        assert len(devices["LIGHT"]) == 2, "Should have two lights"
        
        # MUST apply transformations correctly to all devices
        thermo = devices["THERMOSTAT"][0]
        thermo_states = thermo["device_state"]
        
        # Check temperature float conversion
        temp_ambient = next(s for s in thermo_states if s["name"] == "thermostatTemperatureAmbient")
        assert isinstance(temp_ambient["value"], float), "Temperature should be float"
        assert temp_ambient["value"] == 72.0, "Temperature value should be correct"
        
        # Check off->on transformation
        on_state = next(s for s in thermo_states if s["name"] == "on")
        assert on_state["value"] == True, "off: False should become on: True"
        
        # Check light transformations
        main_light = devices["LIGHT"][0]
        main_brightness = next(s for s in main_light["device_state"] if s["name"] == "brightness")
        assert isinstance(main_brightness["value"], float), "Main light brightness should be float"
        
        accent_light = devices["LIGHT"][1]
        accent_states = accent_light["device_state"]
        accent_on = next(s for s in accent_states if s["name"] == "on")
        accent_brightness = next(s for s in accent_states if s["name"] == "brightness")
        
        assert accent_on["value"] == False, "Accent light off: True should become on: False"
        assert isinstance(accent_brightness["value"], float), "Accent light brightness should be float"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
