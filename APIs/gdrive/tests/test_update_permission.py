from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import update_permission
from gdrive.SimulationEngine.custom_errors import MissingEmailForOwnershipTransferError
from pydantic import ValidationError
import copy
from unittest.mock import MagicMock, patch

MOCK_DB_INITIAL_STATE = {
    "users": {
        "me": {
            "files": {
                "file1": {
                    "id": "file1",
                    "name": "File 1",
                    "owners": ["current_owner@example.com"],
                    "permissions": [
                        {"id": "perm_owner", "role": "owner", "type": "user", "emailAddress": "current_owner@example.com"},
                        {"id": "perm_viewer", "role": "viewer", "type": "user", "emailAddress": "viewer@example.com"},
                        {"id": "perm_no_email", "role": "viewer", "type": "anyone"}
                    ]
                },
                # NEW: Added for testing multi-owner demotion
                "file_multi_owner": {
                    "id": "file_multi_owner",
                    "name": "Multi-Owner File",
                    "owners": ["owner1@example.com", "owner2@example.com"],
                    "permissions": [
                        {"id": "mo_perm1", "role": "owner", "type": "user", "emailAddress": "owner1@example.com"},
                        {"id": "mo_perm2", "role": "owner", "type": "user", "emailAddress": "owner2@example.com"},
                        {"id": "mo_perm3", "role": "editor", "type": "user", "emailAddress": "editor@example.com"}
                    ]
                }
            }
        }
    }
}

class TestUpdatePermission(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a clean, mocked environment for each test."""
        self.mock_db = copy.deepcopy(MOCK_DB_INITIAL_STATE)

        # Patch the module-level DB to use our controlled version
        self.db_patch = patch('gdrive.Permissions.DB', self.mock_db)
        self.db_module = self.db_patch.start()

        # Mock _ensure_user - its internal logic isn't being tested here
        self.ensure_user_patch = patch('gdrive.Permissions._ensure_user', MagicMock())
        self.mock_ensure_user = self.ensure_user_patch.start()

        # Mock _ensure_file to return the correct file entry
        def mock_ensure_file_func(userId, fileId):
            if fileId in self.mock_db["users"][userId]["files"]:
                return self.mock_db["users"][userId]["files"][fileId]
            raise LookupError(f"File '{fileId}' not found.")

        self.ensure_file_patch = patch('gdrive.Permissions._ensure_file', side_effect=mock_ensure_file_func)
        self.mock_ensure_file = self.ensure_file_patch.start()


    def tearDown(self):
        """Stop all patches after each test."""
        self.db_patch.stop()
        self.ensure_user_patch.stop()
        self.ensure_file_patch.stop()

    # --- Standard Update Tests (No Ownership Change) ---

    def test_update_permission_role_success(self):
        """Test successful update of a permission's role from reader to writer."""
        body = {"role": "writer"}
        updated_perm = update_permission(fileId="file1", permissionId="perm_viewer", body=body)

        self.assertIsNotNone(updated_perm)
        self.assertEqual(updated_perm['id'], "perm_viewer")
        self.assertEqual(updated_perm['role'], "writer")

        # Verify the change in the mock database
        db_perm = next(p for p in self.mock_db['users']['me']['files']['file1']['permissions'] if p['id'] == 'perm_viewer')
        self.assertEqual(db_perm['role'], 'writer')

    def test_update_non_existent_permission_raises_permission_not_found_error(self):
        """
        Test that updating a non-existent permissionId raises PermissionNotFoundError.
        """
        # Define arguments for a standard update on a permission that doesn't exist
        file_id = "file1"
        non_existent_perm_id = "non_existent_perm_id"
        body = {"role": "writer"}

        # Use the custom error handler to assert that the correct exception is raised
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=LookupError,
            expected_message=f"Permission with ID '{non_existent_perm_id}' not found on file '{file_id}'.",
            # Arguments to pass to the update function:
            fileId=file_id,
            permissionId=non_existent_perm_id,
            body=body,
            transferOwnership=False # Ensure we are in standard update mode
        )

    def test_cannot_set_role_to_owner_without_flag(self):
        """Test that setting role to 'owner' directly raises a ValueError."""
        body = {"role": "owner"}
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=ValueError,
            expected_message="Cannot set role to 'owner' directly. Use the transferOwnership=True flag.",
            fileId="file1",
            permissionId="perm_viewer",
            body=body
        )

    def test_body_is_none_or_empty_makes_no_changes(self):
        """Test that a None or empty body results in no changes."""
        original_permission = copy.deepcopy(
            next(p for p in self.mock_db['users']['me']['files']['file1']['permissions'] if p['id'] == 'perm_viewer')
        )

        # Test with None
        result_none = update_permission(fileId="file1", permissionId="perm_viewer", body=None)
        self.assertEqual(result_none, original_permission)

        # Test with empty dict
        result_empty = update_permission(fileId="file1", permissionId="perm_viewer", body={})
        self.assertEqual(result_empty, original_permission)

    # --- Ownership Transfer Tests ---

    def test_transfer_ownership_success(self):
        """Test successful ownership transfer to an existing user."""
        new_owner_perm_id = "perm_viewer"
        new_owner_email = "viewer@example.com"
        body = {"allowFileDiscovery": True}

        result_permission = update_permission(
            fileId="file1",
            permissionId=new_owner_perm_id,
            body=body,
            transferOwnership=True
        )

        self.assertIsNotNone(result_permission)
        self.assertEqual(result_permission['emailAddress'], new_owner_email)
        self.assertEqual(result_permission['role'], "owner")
        self.assertTrue(result_permission['allowFileDiscovery'])

        # Verify DB state
        file_entry = self.mock_db['users']['me']['files']['file1']
        self.assertEqual(file_entry['owners'], [new_owner_email])
        old_owner_perm = next(p for p in file_entry['permissions'] if p['id'] == 'perm_owner')
        self.assertEqual(old_owner_perm['role'], 'writer')
        new_owner_perm = next(p for p in file_entry['permissions'] if p['id'] == new_owner_perm_id)
        self.assertEqual(new_owner_perm['role'], 'owner')

    def test_transfer_ownership_invalid_permissionid_raises_lookup_error(self):
        """Test transferOwnership with an invalid permissionId raises LookupError."""
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=LookupError,
            expected_message="Permission with ID 'invalid_id' not found, cannot transfer ownership.",
            fileId="file1",
            permissionId="invalid_id",
            transferOwnership=True
        )

    def test_transfer_ownership_to_user_without_email_raises_value_error(self):
        """Test transferOwnership to a permission without an email raises ValueError."""
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=ValueError,
            expected_message="Ownership can only be transferred to a permission with a valid email address.",
            fileId="file1",
            permissionId="perm_no_email",
            transferOwnership=True
        )

    # --- Input Validation Tests (Refactored to use assert_error_behavior) ---

    def test_invalid_fileid_type(self):
        """Test that invalid fileId type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=TypeError,
            expected_message="fileId must be a string.",
            fileId=123,
            permissionId="perm_viewer",
            body={}
        )

    def test_invalid_permissionid_type(self):
        """Test that invalid permissionId type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=TypeError,
            expected_message="permissionId must be a string.",
            fileId="file1",
            permissionId=123,
            body={}
        )

    def test_invalid_transferownership_type(self):
        """Test that invalid transferOwnership type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=TypeError,
            expected_message="transferOwnership must be a boolean.",
            fileId="file1",
            permissionId="perm_viewer",
            transferOwnership="not_a_bool"
        )

    def test_body_with_invalid_field_raises_validation_error(self):
        """Test that an invalid field in the body raises a Pydantic ValidationError."""
        invalid_body = {"role": "not_a_valid_role"}
        # For pydantic, the exact message can be long, so we just check for the exception type
        self.assert_error_behavior(
            func_to_call=update_permission,
            expected_exception_type=ValidationError,
            expected_message="", # Message check is loose for ValidationError in the helper
            fileId="file1",
            permissionId="perm_viewer",
            body=invalid_body
        )
    
    def test_transfer_ownership_to_current_owner(self):
        """Test that transferring ownership to the current owner results in no effective change."""
        current_owner_id = "perm_owner"
        current_owner_email = "current_owner@example.com"

        # Get the state of permissions before the call
        original_permissions = copy.deepcopy(self.mock_db['users']['me']['files']['file1']['permissions'])

        result = update_permission(
            fileId="file1",
            permissionId=current_owner_id,
            transferOwnership=True
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['role'], 'owner')
        self.assertEqual(result['emailAddress'], current_owner_email)

        # Verify the database state is effectively unchanged
        file_entry = self.mock_db['users']['me']['files']['file1']
        self.assertEqual(file_entry['owners'], [current_owner_email])
        self.assertEqual(file_entry['permissions'], original_permissions)

    def test_role_in_body_is_ignored_during_transfer(self):
        """Test that the 'role' in the body is ignored when transferOwnership is true."""
        result = update_permission(
            fileId="file1",
            permissionId="perm_viewer",
            body={'role': 'writer'},  # Attempt to set role to writer
            transferOwnership=True
        )

        # The role should be 'owner' because transferOwnership overrides the body
        self.assertEqual(result['role'], 'owner')

    def test_transfer_ownership_demotes_multiple_owners(self):
        """Test that a transfer correctly demotes all previous owners in a multi-owner file."""
        new_owner_id = "mo_perm3"
        new_owner_email = "editor@example.com"

        result = update_permission(
            fileId="file_multi_owner",
            permissionId=new_owner_id,
            transferOwnership=True
        )

        self.assertEqual(result['role'], 'owner')
        self.assertEqual(result['emailAddress'], new_owner_email)

        # Verify DB state
        file_entry = self.mock_db['users']['me']['files']['file_multi_owner']
        self.assertEqual(file_entry['owners'], [new_owner_email]) # New owner is now the only one

        # Check that BOTH previous owners were demoted to 'writer'
        old_owner1 = next(p for p in file_entry['permissions'] if p['id'] == 'mo_perm1')
        old_owner2 = next(p for p in file_entry['permissions'] if p['id'] == 'mo_perm2')

        self.assertEqual(old_owner1['role'], 'writer')
        self.assertEqual(old_owner2['role'], 'writer')

    def test_update_permission_invalid_email(self):
        """Test that updating a permission with invalid email raises a ValidationError."""
        self.assert_error_behavior(
            update_permission,
            ValidationError,
            "value is not a valid email address: An email address must have an @-sign.",
            fileId="file1",
            permissionId="perm_viewer",
            body={"emailAddress": "invalid_email"}
        )
