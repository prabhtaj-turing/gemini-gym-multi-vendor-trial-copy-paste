import os
import sys
import importlib

from pydantic import ValidationError

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import create_shared_drive
from pydantic import ValidationError

from gdrive.SimulationEngine.custom_errors import InvalidPageSizeError
from gdrive.SimulationEngine.db import DB
from .. import _ensure_user

class TestCreateSharedDrive(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset DB before each test and ensure user 'me' exists."""
        DB.update(
            {
                "users": {
                    "me": {
                        "about": {}, # Simplified for brevity
                        "files": {},
                        "drives": {},
                        "comments": {},
                        "replies": {},
                        "labels": {},
                        "accessproposals": {},
                        "apps": {},
                        "channels": {},
                        "changes": {"startPageToken": "1", "changes": []},
                        "counters": {
                            "file": 0,
                            "drive": 0,
                            "comment": 0,
                            "reply": 0,
                            "label": 0,
                            "accessproposal": 0,
                            "revision": 0,
                            "change_token": 0,
                        },
                    }
                }
            }
        )
        _ensure_user("me") # Ensures 'me' user and its sub-dictionaries like 'drives', 'counters' are initialized

    def test_valid_input_with_request_id_and_full_body(self):
        """Test creating a drive with a specific requestId and a full body."""
        request_id = "test_drive_123"
        drive_body = {
            "name": "My Test Drive",
            "restrictions": {
                "adminManagedRestrictions": True,
                "copyRequiresWriterPermission": False,
                "domainUsersOnly": True,
                "driveMembersOnly": False,
            },
            "hidden": True,
            "themeId": "theme_abc",
        }
        drive = create_shared_drive(requestId=request_id, body=drive_body)
        self.assertEqual(drive["id"], request_id)
        self.assertEqual(drive["name"], "My Test Drive")
        self.assertEqual(drive["kind"], "drive#drive")
        # Check if it's stored (core logic part)
        self.assertIn(request_id, DB['users']['me']['drives'])
        # Verify all properties are stored correctly
        stored_drive = DB['users']['me']['drives'][request_id]
        self.assertEqual(stored_drive['name'], "My Test Drive")
        self.assertEqual(stored_drive['restrictions']['adminManagedRestrictions'], True)
        self.assertEqual(stored_drive['restrictions']['copyRequiresWriterPermission'], False)
        self.assertEqual(stored_drive['restrictions']['domainUsersOnly'], True)
        self.assertEqual(stored_drive['restrictions']['driveMembersOnly'], False)
        self.assertEqual(stored_drive['hidden'], True)
        self.assertEqual(stored_drive['themeId'], "theme_abc")

    def test_valid_input_with_request_id_only(self):
        """Test creating a drive with only a requestId (body is None)."""
        request_id = "test_drive_456"
        drive = create_shared_drive(requestId=request_id, body=None)
        self.assertEqual(drive["id"], request_id)
        self.assertEqual(drive["name"], f"Drive_{request_id}") # Default name logic
        self.assertIn(request_id, DB['users']['me']['drives'])

    def test_valid_input_with_body_only(self):
        """Test creating a drive with only a body (requestId is None)."""
        drive_body = {"name": "Another Test Drive"}
        # Mock _next_counter behavior for predictable ID
        original_counter = DB['users']['me']['counters']['drive']
        DB['users']['me']['counters']['drive'] = 0 # Reset for predictability
        
        drive = create_shared_drive(requestId=None, body=drive_body)
        
        expected_drive_id = "drive_1" # Assumes _next_counter starts at 1 after reset or for the first call
        self.assertEqual(drive["id"], expected_drive_id)
        self.assertEqual(drive["name"], "Another Test Drive")
        self.assertIn(expected_drive_id, DB['users']['me']['drives'])
        DB['users']['me']['counters']['drive'] = original_counter # Restore counter

    def test_valid_input_no_optional_args(self):
        """Test creating a drive with no optional arguments (requestId and body are None)."""
        original_counter = DB['users']['me']['counters']['drive']
        DB['users']['me']['counters']['drive'] = 99 # Set for predictability

        drive = create_shared_drive() # requestId=None, body=None
        
        expected_drive_id = "drive_100" 
        self.assertEqual(drive["id"], expected_drive_id)
        self.assertEqual(drive["name"], "Drive_100") # Default name logic
        self.assertIn(expected_drive_id, DB['users']['me']['drives'])
        DB['users']['me']['counters']['drive'] = original_counter

    def test_valid_body_empty_dict(self):
        """Test creating a drive with body as an empty dictionary."""
        original_counter = DB['users']['me']['counters']['drive']
        DB['users']['me']['counters']['drive'] = 1 # For predictable ID "drive_2"
        
        drive = create_shared_drive(body={})
        
        expected_drive_id = "drive_2"
        self.assertEqual(drive["id"], expected_drive_id)
        self.assertEqual(drive["name"], f"Drive_2")
        self.assertIn(expected_drive_id, DB['users']['me']['drives'])
        DB['users']['me']['counters']['drive'] = original_counter

    def test_idempotency_with_request_id(self):
        """Test that creating a drive with an existing requestId returns the existing drive."""
        request_id = "idempotent_drive_789"
        drive_body = {"name": "First Drive"}
        
        # Create drive for the first time
        drive1 = create_shared_drive(requestId=request_id, body=drive_body)
        self.assertEqual(drive1["name"], "First Drive")

        # Attempt to create with same requestId, potentially different body (should be ignored)
        drive2_body = {"name": "Second Drive Attempt"}
        drive2 = create_shared_drive(requestId=request_id, body=drive2_body)
        
        self.assertEqual(drive2["id"], request_id)
        self.assertEqual(drive2["name"], "First Drive") # Should return the original drive's name
        self.assertEqual(drive1, drive2) # Should be the exact same dictionary object if returned from DB

    def test_invalid_request_id_type(self):
        """Test that providing a non-string requestId raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_shared_drive,
            expected_exception_type=TypeError,
            expected_message="requestId must be a string if provided.",
            requestId=12345, # Invalid type
            body=None
        )

    def test_invalid_body_structure_name_type(self):
        """Test invalid type for 'name' in body."""
        invalid_body = {"name": 123} # name should be string
        exact_error_message = (
            "1 validation error for CreateDriveBodyInputModel\n"
            "name\n"
            "  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n"
            "    For further information visit https://errors.pydantic.dev/2.11/v/string_type"
        )

        self.assert_error_behavior(
            func_to_call=create_shared_drive,
            expected_exception_type=ValidationError,
            expected_message=exact_error_message,
            body=invalid_body
        )

    def test_invalid_body_structure_hidden_type(self):
        """Test invalid type for 'hidden' in body."""
        invalid_body = {"hidden": "not-a-boolean"}
        self.assert_error_behavior(
            create_shared_drive,
            ValidationError,
            "Input should be a valid boolean", # Pydantic error substring
            body=invalid_body
        )

    def test_invalid_body_structure_theme_id_type(self):
        """Test invalid type for 'themeId' in body."""
        invalid_body = {"themeId": True} # themeId should be string
        self.assert_error_behavior(
            create_shared_drive,
            ValidationError,
            "Input should be a valid string", # Pydantic error substring
            body=invalid_body
        )
        
    def test_invalid_body_restrictions_not_dict(self):
        """Test invalid type for 'restrictions' (should be a dict)."""
        invalid_body = {"restrictions": "not-a-dict"}
        self.assert_error_behavior(
            create_shared_drive,
            ValidationError,
            "Input should be a valid dictionary", # Pydantic error substring
            body=invalid_body
        )

    def test_invalid_body_restrictions_missing_required_field(self):
        """Test 'restrictions' dict with invalid field type."""
        invalid_body = {
            "restrictions": {
                "adminManagedRestrictions": "not-a-boolean", # Wrong type
                "copyRequiresWriterPermission": False,
                "domainUsersOnly": True,
                "driveMembersOnly": False,
            }
        }
        self.assert_error_behavior(
            create_shared_drive,
            ValidationError,
            "Input should be a valid boolean", # Pydantic error substring for invalid boolean
            body=invalid_body
        )