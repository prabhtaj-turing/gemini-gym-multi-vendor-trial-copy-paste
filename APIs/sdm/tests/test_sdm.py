import unittest
import json
import tempfile
import os
import sdm.SimulationEngine
from sdm.devices import execute_command, get_device_info, list_devices, get_events_list
from sdm.SimulationEngine.db import load_state, update_state_dict
from sdm.SimulationEngine.events import set_cameras_events
from sdm.SimulationEngine import db
from common_utils.base_case import BaseTestCaseWithErrorHandler
from sdm.devices.errors import CameraNotAvailableError, CommandNotSupportedError, IncorrectEventError

# --- Test Data ---
correct_sdm_devices_config = {
    "project_id": "Project_001",
    "environment": {
        "sdm": {
            "devices": {
                "display-123": {"name": "display-123", "type": "display", "attributes": {"state": "off", "model": "Nest Hub Max"}},
                "camera-456": {"name": "camera-456", "type": "camera", "attributes": {"state": "on", "model": "Google Nest Cam IQ Indoor"}},
                "sensor-789": {"name": "sensor-789", "type": "sensor", "attributes": {"state": "22", "model": "Nest Doorbell (legacy)"}},
            }
        }
    }
}

complete_sdm_devices_config = {
    "project_id": "Project_001",
    "environment": {
        "sdm": {
            "devices": {
                "display-123": {"name": "display-123", "type": "display", "attributes": {"state": "off", "model": "Nest Hub Max"}},
                "camera-456": {"name": "camera-456", "type": "camera", "attributes": {"state": "on", "model": "Google Nest Cam IQ Indoor"}},
                "sensor-789": {"name": "sensor-789", "type": "sensor", "attributes": {"state": "22", "model": "Nest Doorbell (legacy)"}},
                "device.no_name": {"attributes": {"state": "unknown"}},
                "device.no_type": {"name": "no_type", "attributes": {"state": "unknown"}},
                "device.no_attributes": {"name": "no_attributes", "type": "thermostat"},
                "device.no_state": {"name": "no_state", "type": "camera", "attributes": {"model": "Nest Cam with floodlight"}},
                "device.no_model": {"name": "no_model", "type": "camera", "attributes": {"state": "on"}},
            }
        }
    }
}

test_image_path = os.path.join(os.path.dirname(__file__), "test_image.png")
complete_image_mapping_config = {
    "cameras": {
        "camera-456": [
            {
                "state": {
                    "camera": "on"
                },
                "image_path": test_image_path
            }
        ]
    },
    "events": [
        {
            "trigger": "Motion",
            "timestamp": "2025-05-16 17:21:00",
            "camera_id": "camera-456",
            "image_path": test_image_path
        }
    ]
}

# --- End of Test Data ---

class TestSDMFunctions(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Create a temporary JSON file for load_state
        self.correct_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.complete_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        
        correct_db = {
            "project_id": correct_sdm_devices_config["project_id"],
            "environment": correct_sdm_devices_config["environment"]
        }
        complete_db = {
            "project_id": complete_sdm_devices_config["project_id"],
            "environment": complete_sdm_devices_config["environment"]
        }
        json.dump(correct_db, self.correct_file)
        json.dump(complete_db, self.complete_file)
        self.correct_file.close()
        self.complete_file.close()
        load_state(self.complete_file.name)
        self.project_id = "Project_001"
        update_state_dict(complete_image_mapping_config)
        set_cameras_events(complete_image_mapping_config, self.project_id)

    def tearDown(self):
        # Clean up the temporary file
        os.unlink(self.complete_file.name)

    def test_list_devices_correct_db(self):
        load_state(self.correct_file.name)
        result = list_devices()
        self.assertIsInstance(result, dict)
        self.assertIn("devices", result)
        self.assertEqual(len(result["devices"]), 3)

    def test_list_devices_incorrect_db(self):
        load_state(self.complete_file.name)
        self.assert_error_behavior(
            list_devices,
            ValueError,
            f"sdm device device.no_name model is not one of Google allowed models.\nUse one of following: ['Google Nest Cam Indoor', 'Google Nest Cam (indoor, wired)', 'Google Nest Cam (outdoor or indoor, battery)', 'Google Nest Cam IQ Indoor', 'Google Nest Cam IQ Outdoor', 'Google Nest Cam Outdoor', 'Nest Cam with floodlight', 'Nest Doorbell (battery)', 'Nest Doorbell (legacy)', 'Nest Doorbell (wired)', 'Nest Hub Max']",
            None,
        )

    def test_get_device_info_success(self):
        result = get_device_info("display-123", project_id=self.project_id)
        self.assertEqual(result["type"], "sdm.devices.types.DISPLAY")
        self.assertEqual(result["traits"]["sdm.devices.traits.Info"]["customName"], "display-123")
        # Check DB state
        self.assertIn("display-123", db.DB.get("environment", {}).get("sdm", {}).get("devices", {}))

    def test_get_device_info_device_not_found(self):
        with self.assertRaises(ValueError) as context:
            get_device_info("nonexistent_device", project_id=self.project_id)
        self.assertEqual(str(context.exception), "Device nonexistent_device not found")

    def test_get_device_info_device_has_no_attributes_key(self):
        self.assert_error_behavior(
            get_device_info,
            ValueError,
            f"sdm device device.no_name model is not one of Google allowed models.\nUse one of following: ['Google Nest Cam Indoor', 'Google Nest Cam (indoor, wired)', 'Google Nest Cam (outdoor or indoor, battery)', 'Google Nest Cam IQ Indoor', 'Google Nest Cam IQ Outdoor', 'Google Nest Cam Outdoor', 'Nest Cam with floodlight', 'Nest Doorbell (battery)', 'Nest Doorbell (legacy)', 'Nest Doorbell (wired)', 'Nest Hub Max']",
            None,
            'device.no_name',
            self.project_id,
        )

    def test_get_device_info_device_has_attributes_but_no_state_key(self):
        result = get_device_info("device.no_state", project_id=self.project_id)
        self.assertEqual(result["type"], "sdm.devices.types.CAMERA")
        self.assertIn("traits", result)
        self.assertNotIn("state", result["traits"])

    def test_get_device_info_device_has_attributes_but_no_model_key(self):
        self.assert_error_behavior(
            get_device_info,
            ValueError,
            f"sdm device device.no_model model is not one of Google allowed models.\nUse one of following: ['Google Nest Cam Indoor', 'Google Nest Cam (indoor, wired)', 'Google Nest Cam (outdoor or indoor, battery)', 'Google Nest Cam IQ Indoor', 'Google Nest Cam IQ Outdoor', 'Google Nest Cam Outdoor', 'Nest Cam with floodlight', 'Nest Doorbell (battery)', 'Nest Doorbell (legacy)', 'Nest Doorbell (wired)', 'Nest Hub Max']",
            None,
            'device.no_model',
            self.project_id,
        )

    def test_get_events_list(self):
        result = get_events_list()
        self.assertIsInstance(result, list)
        self.assertIn("eventId", result[0])
        self.assertIn("sdm.devices.events.CameraMotion.Motion", result[0].get("resourceUpdate").get("events"))

    def test_generate_camera_event_image(self):
        events = get_events_list()
        event_id = events[0].get("resourceUpdate").get("events").get("sdm.devices.events.CameraMotion.Motion").get("eventId")
        generate_image_command = {"command": "sdm.devices.commands.generate_camera_event_image",
                          "params": {
                              "event_id": event_id
                              }
                          }
        result = execute_command(device_id="camera-456", project_id=self.project_id, command_request=generate_image_command)
        self.assertIsInstance(result, str)
        self.assertEqual("Image base64: ", result[:14])

    def test_generate_camera_event_image_with_wrong_event_id(self):
        event_id = "wrong_fake_event_id"
        generate_image_command = {"command": "sdm.devices.commands.generate_camera_event_image",
                          "params": {
                              "event_id": event_id
                              }
                          }
        self.assert_error_behavior(
            execute_command,
            IncorrectEventError,
            "Event id does not belong to the camera. (RPC: FAILED_PRECONDITION) (Error code: 400)",
            None,
            "camera-456",
            self.project_id,
            generate_image_command
        )

    def test_generate_camera_event_image_with_wrong_device_id(self):
        events = get_events_list()
        event_id = events[0].get("resourceUpdate").get("events").get("sdm.devices.events.CameraMotion.Motion").get("eventId")
        generate_image_command = {"command": "sdm.devices.commands.generate_camera_event_image",
                          "params": {
                              "event_id": event_id
                              }
                          }
        self.assert_error_behavior(
            execute_command,
            IncorrectEventError,
            "Event id does not belong to the camera. (RPC: FAILED_PRECONDITION) (Error code: 400)",
            None,
            "display-123",
            self.project_id,
            generate_image_command
        )

    def test_generate_rtsp_stream(self):
        generate_stream_command = {"command": "sdm.devices.commands.generate_rtsp_stream",
                           "params": {}
                           }
        result = execute_command(device_id="camera-456", project_id=self.project_id, command_request=generate_stream_command)
        self.assertIsInstance(result, dict)
        self.assertIn("streamUrls", result.get("results"))

    def test_generate_rtsp_stream_with_off_device(self):
        generate_stream_command = {"command": "sdm.devices.commands.generate_rtsp_stream",
                           "params": {}
                           }
        self.assert_error_behavior(
            execute_command,
            CameraNotAvailableError,
            "The camera is not available for streaming. (RPC: FAILED_PRECONDITION) (Error code: 400)",
            None,
            "display-123",
            self.project_id,
            generate_stream_command
        )

    def test_stream_command_not_supported(self):
        generate_stream_command = {"command": "sdm.devices.commands.generate_web_rtc_stream",
                           "params": {
                               "offer_sdp": "offer"
                           }
                           }
        self.assert_error_behavior(
            execute_command,
            CommandNotSupportedError,
            "Command not supported. (RPC: INVALID_ARGUMENT) (Error code: 400)",
            None,
            "camera-456",
            self.project_id,
            generate_stream_command
        )

    def test_generate_image_from_rtsp_stream(self):
        generate_stream_command = {"command": "sdm.devices.commands.generate_rtsp_stream",
                           "params": {}
                           }
        generate_stream_output = execute_command(device_id="camera-456", project_id=self.project_id, command_request=generate_stream_command)
        generate_image_command = {"command": "sdm.devices.commands.generate_image_from_rtsp_stream",
                          "params": {
                              "rtsp_url": generate_stream_output.get("results", {}).get("streamUrls", "").get("rtspUrl", "")
                              }
                          }
        result = execute_command(device_id='camera-456', project_id=self.project_id, command_request=generate_image_command)
        self.assertIsInstance(result, str)
        self.assertEqual("Image base64: ", result[:14])

    def test_generate_image_from_wrong_device(self):
        generate_stream_command = {"command": "sdm.devices.commands.generate_rtsp_stream",
                           "params": {}
                           }
        generate_stream_output = execute_command(device_id="camera-456", project_id=self.project_id, command_request=generate_stream_command)
        generate_image_command = {"command": "sdm.devices.commands.generate_image_from_rtsp_stream",
                          "params": {
                              "rtsp_url": generate_stream_output.get("results", {}).get("streamUrls", "").get("rtspUrl", "")
                              }
                          }
        self.assert_error_behavior(
            execute_command,
            IncorrectEventError,
            "Event id does not belong to the camera. (RPC: FAILED_PRECONDITION) (Error code: 400)",
            None,
            "display-123",
            self.project_id,
            generate_image_command
        )

    def test_execute_command_missing_device_id(self):
        with self.assertRaises(ValueError) as context:
            execute_command(None, self.project_id, {"command": "sdm.devices.commands.generate_camera_image", "params": {}})
        self.assertEqual(str(context.exception), "device_id is required")

    def test_execute_command_missing_command(self):
        with self.assertRaises(ValueError) as context:
            execute_command("display-123", self.project_id, {})
        self.assertEqual(str(context.exception), "command_request is required")

    def test_execute_command_invalid_command(self):
        self.assert_error_behavior(
            execute_command,
            ValueError,
            "Command invalid_command not found",
            None,
            "display-123",
            self.project_id,
            {"command": "invalid_command", "params": {}}
        )

    # Test flattened function names in sdm/__init__.py
    def test_flattened_list_devices(self):
        load_state(self.correct_file.name)
        import sdm
        result = sdm.list_devices()
        self.assertIsInstance(result, dict)
        self.assertIn("devices", result)
        device_names = [device["name"] for device in result["devices"]]
        self.assertIn("enterprises/Project_001/devices/display-123", device_names)

    def test_flattened_get_device_info(self):
        import sdm
        result = sdm.get_device_info("display-123", project_id=self.project_id)
        self.assertEqual(result["type"], "sdm.devices.types.DISPLAY")
        self.assertEqual(result["traits"]["sdm.devices.traits.Info"]["customName"], "display-123")

    def test_get_device_info_missing_project_id(self):
        self.assert_error_behavior(
            get_device_info,
            ValueError,
            "project_id is required",
            None,
            "display-123",
            project_id=None
        )
        self.assert_error_behavior(
            get_device_info,
            ValueError,
            "project_id is required",
            None,
            "display-123",
            project_id=""
        )

    def test_get_device_info_missing_device_id(self):
        self.assert_error_behavior(
            get_device_info,
            ValueError,
            "device_id is required",
            None,
            None,
            project_id=self.project_id
        )
        self.assert_error_behavior(
            get_device_info,
            ValueError,
            "device_id is required",
            None,
            "",
            project_id=self.project_id
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)