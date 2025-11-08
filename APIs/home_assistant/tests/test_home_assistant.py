import unittest
import json
import tempfile
import os
from home_assistant.devices import list_devices, get_state, toggle_device, get_device_info, set_device_property, get_id_by_name
from home_assistant.SimulationEngine.db import load_state, DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

# --- Test Data ---
initial_ha_devices_config = {
    "environment": {
        "home_assistant": {
            "devices": {
                "light.living_room": {"type": "light", "attributes": {"state": "off"}},
                "switch.kitchen": {"type": "switch", "attributes": {"state": "on"}},
                "sensor.temperature": {"type": "sensor", "attributes": {"state": "22"}},
                "light.bedroom": {"type": "Light", "attributes": {"state": "on"}},
                "cover.garage": {"type": "cover", "attributes": {"state": "closed"}, "name": "Garage Door"},
                "device.no_type": {"attributes": {"state": "unknown"}},
                "device.no_attributes": {"type": "light"},
                "device.no_state": {"type": "light", "attributes": {}},
            }
        }
    }
}

initial_automations_config = {
    "automation.morning_routine": {"triggered": False, "description": "Turns on lights and coffee"},
    "automation.night_mode": {"triggered": False, "description": "Turns off all lights"}
}

# --- End of Test Data ---

class TestHomeAssistantFunctions(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Create a temporary JSON file for load_state
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        test_db = {
            "environment": initial_ha_devices_config["environment"],
            "automations": initial_automations_config
        }
        json.dump(test_db, self.temp_file)
        self.temp_file.close()
        load_state(self.temp_file.name)

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.temp_file.name)

    def test_list_devices_no_domain(self):
        result = list_devices()
        self.assertIn("entities", result)
        self.assertEqual(len(result["entities"]), 8)

    def test_list_devices_with_domain_filter(self):
        result = list_devices(domain="light")
        self.assertEqual(len(result["entities"]), 4)
        self.assertEqual(list(result["entities"][0].keys())[0], "light.living_room")

    def test_list_devices_with_invalid_domain(self):
        result = list_devices(domain="invalid_domain")
        self.assertEqual(len(result["entities"]), 0)

    def test_get_state_success(self):
        result = get_state("light.living_room")
        self.assertEqual(result["entity_id"], "light.living_room")
        self.assertEqual(result["state"], "off")

    def test_get_state_device_not_found(self):
        self.assert_error_behavior(
            get_state,
            ValueError,
            "entity_id must be a valid device ID.",
            "nonexistent_device",
            entity_id="nonexistent_device"
        )

    def test_get_state_device_has_no_attributes_key(self):
        result = get_state("device.no_attributes")
        self.assertEqual(result["entity_id"], "device.no_attributes")
        self.assertEqual(result["state"], {})

    def test_get_state_device_has_attributes_but_no_state_key(self):
        result = get_state("device.no_state")
        self.assertEqual(result["entity_id"], "device.no_state")
        self.assertEqual(result["state"], {})

    def test_toggle_device_success_on(self):
        result = toggle_device("light.living_room", "on")
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(DB.get('environment', {}).get('home_assistant', {}).get("devices", {}).get("light.living_room", {}).get("attributes", {}).get("state"), "On")

    def test_toggle_device_success_off(self):
        result = toggle_device("light.living_room", "off")
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(DB.get('environment', {}).get('home_assistant', {}).get("devices", {}).get("light.living_room", {}).get("attributes", {}).get("state"), "Off")

    def test_toggle_device_missing_entity_id(self):
        self.assert_error_behavior(
            toggle_device,
            ValueError,
            "Missing required field: entity_id",
            None,
            entity_id=None,
            state="on"
        )

    def test_toggle_device_entity_not_found(self):
        self.assert_error_behavior(
            toggle_device,
            ValueError,
            "Entity 'nonexistent_entity' not found.",
            "nonexistent_entity",
            entity_id="nonexistent_entity",
            state="on"
        )

    def test_toggle_device_invalid_state_value(self):
        self.assert_error_behavior(
            toggle_device,
            ValueError,
            "Invalid state 'invalid_state' for device type 'light'. Allowed states are: ['On', 'Off'].",
            "light.living_room",
            entity_id="light.living_room",
            state="invalid_state"
        )

    def test_toggle_device_device_missing_attributes_key_raises_keyerror(self):
        self.assert_error_behavior(
            toggle_device,
            KeyError,
            "'attributes'",
            "device.no_attributes",
            entity_id="device.no_attributes",
            state="on"
        )

    def test_get_device_info_success(self):
        result = get_device_info("light.living_room")
        self.assertEqual(result["entity_id"], "light.living_room")
        self.assertIn("type", result["state"])
        self.assertIn("attributes", result["state"])
        self.assertEqual(result["state"]["type"].lower(), "light")
        self.assertIn(result["state"]["attributes"]["state"].lower(), ["on", "off"])

    def test_get_device_info_device_not_found(self):
        self.assert_error_behavior(
            get_device_info,
            KeyError,
            "'device_id must be a valid device ID.'",
            "nonexistent_device",
            device_id="nonexistent_device"
        )

    def test_set_device_property_success(self):
        result = set_device_property("light.living_room", {"brightness": 70})
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(DB.get('environment', {}).get('home_assistant', {}).get("devices", {}).get("light.living_room", {}).get("attributes", {}).get("brightness"), 70)

    def test_set_device_property_missing_entity_id(self):
        self.assert_error_behavior(
            set_device_property,
            ValueError,
            "Missing required field: entity_id",
            None,
            entity_id=None,
            new_attributes={"brightness": 70}
        )

    def test_set_device_property_entity_not_found(self):
        self.assert_error_behavior(
            set_device_property,
            ValueError,
            "Entity 'nonexistent_entity' not found.",
            "nonexistent_entity",
            entity_id="nonexistent_entity",
            new_attributes={"brightness": 70}
        )

    def test_set_device_property_missing_new_attributes(self):
        self.assert_error_behavior(
            set_device_property,
            ValueError,
            "Missing required field: new_attributes",
            "light.living_room",
            entity_id="light.living_room",
            new_attributes=None
        )

    def test_set_device_property_new_attributes_not_dict(self):
        self.assert_error_behavior(
            set_device_property,
            TypeError,
            "new_attributes must be a dictionary.",
            "light.living_room",
            entity_id="light.living_room",
            new_attributes=[1,2,3]
        )

    def test_set_device_property_device_missing_attributes_key(self):
        # Remove 'attributes' key from a device
        DB["environment"]["home_assistant"]["devices"]["device.no_attributes"].pop("attributes", None)
        self.assert_error_behavior(
            set_device_property,
            KeyError,
            "'attributes'",
            "device.no_attributes",
            entity_id="device.no_attributes",
            new_attributes={"brightness": 50}
        )

    def test_get_id_by_name_success(self):
        # Add a name to a device for this test
        DB["environment"]["home_assistant"]["devices"]["light.living_room"]["name"] = "Living Room Light"
        result = get_id_by_name("Living Room Light")
        self.assertEqual(result, "light.living_room")

    def test_get_id_by_name_not_found(self):
        self.assert_error_behavior(
            get_id_by_name,
            ValueError,
            "No device found with name 'Nonexistent Device'.",
            "Nonexistent Device",
            name="Nonexistent Device"
        )

    def test_get_id_by_name_missing_name(self):
        # Only test for empty string, not None
        self.assert_error_behavior(
            get_id_by_name,
            ValueError,
            "No device found with name ''.",
            "",
            name=""
        )

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False, verbosity=2)