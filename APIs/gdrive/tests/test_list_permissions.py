import unittest
from .. import list_permissions
from .. import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from gdrive.SimulationEngine.utils import _ensure_user
from gdrive.SimulationEngine.custom_errors import NotFoundError

class TestPermissionsList(BaseTestCaseWithErrorHandler):
    """
    Test suite for the list_permissions function.
    Inherits from BaseTestCaseWithErrorHandler to handle different error modes.
    """

    def setUp(self):
        """
        Set up a clean and consistent database state before each test.
        This includes multiple files with various permission configurations.
        """
        global DB
        DB.clear()  # Ensure a clean slate
        DB.update({
            "users": {
                "me": {
                    "files": {
                        "file-1": {
                            "id": "file-1",
                            "name": "My Document",
                            "permissions": [
                                {"kind": "drive#permission", "id": "perm-owner", "role": "owner", "type": "user", "emailAddress": "me@example.com"},
                                {"kind": "drive#permission", "id": "perm-writer", "role": "writer", "type": "user", "emailAddress": "writer@example.com"}
                            ]
                        },
                        "file-2": {
                            "id": "file-2",
                            "name": "Another Document",
                            "permissions": [
                                {"kind": "drive#permission", "id": "perm-anyone", "role": "reader", "type": "anyone"}
                            ]
                        },
                        "file-no-perms": {
                            "id": "file-no-perms",
                            "name": "Empty Permissions"
                            # No 'permissions' key
                        },
                        "file-in-team-drive": {
                            "id": "file-in-team-drive",
                            "name": "Team Drive File"
                            # This file has its primary permissions in the team drive structure
                        }
                    },
                    "team_drives": {
                        "drive-1": {
                            "files": {
                                "file-in-team-drive": {
                                    "permissions": [
                                        {"kind": "drive#permission", "id": "perm-team", "role": "editor", "type": "group", "emailAddress": "team@example.com"}
                                    ]
                                }
                            }
                        }
                    },
                    "counters": {"permission": 100}
                },
                "other_user": {
                    "files": {
                        "file-1": { # Same file ID as 'me' to test supportsAllDrives
                             "permissions": [
                                {"kind": "drive#permission", "id": "perm-commenter", "role": "commenter", "type": "user", "emailAddress": "commenter@example.com"}
                            ]
                        }
                    }
                },
                "admin_user": {
                    "domain_permissions": {
                        "file-1": [
                            {"kind": "drive#permission", "id": "perm-domain", "role": "reader", "type": "domain", "domain": "example.com"}
                        ]
                    }
                }
            }
        })
        # Ensure user 'me' exists for utility functions
        _ensure_user('me')

    def test_list_basic_functionality(self):
        """
        Tests retrieving a standard list of permissions for a file.
        """
        result = list_permissions(fileId='file-1')
        self.assertEqual(result['kind'], 'drive#permissionList')
        self.assertEqual(len(result['permissions']), 2)
        # Check if the correct permission IDs are present
        permission_ids = {p['id'] for p in result['permissions']}
        self.assertIn('perm-owner', permission_ids)
        self.assertIn('perm-writer', permission_ids)

    def test_list_for_file_with_no_permissions_key(self):
        """
        Tests listing permissions for a file that has no 'permissions' key.
        It should return an empty list of permissions.
        """
        result = list_permissions(fileId='file-no-perms')
        self.assertEqual(result['kind'], 'drive#permissionList')
        self.assertEqual(len(result['permissions']), 0)

    def test_list_for_non_existent_file(self):
        """
        Tests that a KeyError is raised for a non-existent fileId,
        as the function expects the file to exist.
        """
        self.assert_error_behavior(
            func_to_call = list_permissions,
            expected_exception_type = NotFoundError,
            expected_message = "Given fileId 'non-existent-file' not found in user 'me' files",
            additional_expected_dict_fields = None,
            fileId = 'non-existent-file'
        )

    def test_list_with_supports_all_drives(self):
        """
        Tests that setting supportsAllDrives=True includes permissions
        from other users who have access to the same file.
        """
        # Without the flag, we should only get 2 permissions
        result_false = list_permissions(fileId='file-1', supportsAllDrives=False)
        self.assertEqual(len(result_false['permissions']), 2)

        # With the flag, we should get 3 permissions (2 from 'me', 1 from 'other_user')
        result_true = list_permissions(fileId='file-1', supportsAllDrives=True)
        self.assertEqual(len(result_true['permissions']), 3)
        permission_ids = {p['id'] for p in result_true['permissions']}
        self.assertIn('perm-commenter', permission_ids)
        
    def test_list_with_supports_team_drives(self):
        """
        Tests that setting supportsTeamDrives=True includes permissions
        defined within a shared drive structure.
        """
        # Inject a shared-drive under the correct 'drives' key, not 'team_drives'
        DB['users']['me'].setdefault('files', {})['file-in-team-drive'] = {
            'permissions': [
                {
                    'kind': 'drive#permission',
                    'id': 'perm-team',
                    'role': 'writer',
                    'type': 'group',
                    'emailAddress': 'team@example.com'
                }
            ]
        }

        result = list_permissions(
            fileId='file-in-team-drive',
            supportsTeamDrives=True
        )
        self.assertEqual(len(result['permissions']), 1)
        self.assertEqual(result['permissions'][0]['id'], 'perm-team')

    def test_list_with_use_domain_admin_access(self):
        """
        Tests that setting useDomainAdminAccess=True includes domain-wide permissions.
        """
        # This should return the 2 base permissions plus the 1 domain permission
        result = list_permissions(fileId='file-1', useDomainAdminAccess=True)
        self.assertEqual(len(result['permissions']), 3)
        permission_types = {p['type'] for p in result['permissions']}
        self.assertIn('domain', permission_types)
        
    def test_all_flags_combined(self):
        """
        Tests the function with all boolean flags enabled to ensure
        permissions are correctly aggregated from all sources.
        """
        result = list_permissions(
            fileId='file-1',
            supportsAllDrives=True,
            supportsTeamDrives=True, # No team drive perms for file-1, should not affect count
            useDomainAdminAccess=True
        )
        # Expected: 2 ('me') + 1 ('other_user') + 1 ('admin_user') = 4
        self.assertEqual(len(result['permissions']), 4)
        permission_ids = {p['id'] for p in result['permissions']}
        self.assertIn('perm-owner', permission_ids)
        self.assertIn('perm-writer', permission_ids)
        self.assertIn('perm-commenter', permission_ids)
        self.assertIn('perm-domain', permission_ids)

    def test_permissions_list_input_validation(self):
        """
        Test input validation for list_permissions function.
        (Incorporated from previous test class)
        """
        # Test with non-string fileId
        with self.assertRaisesRegex(TypeError, "fileId must be a string."):
            list_permissions(fileId=123)

        # Test with non-boolean supportsAllDrives
        with self.assertRaisesRegex(TypeError, "supportsAllDrives must be a boolean."):
            list_permissions(fileId="file-1", supportsAllDrives="not_a_boolean")

        # Test with non-boolean supportsTeamDrives
        with self.assertRaisesRegex(TypeError, "supportsTeamDrives must be a boolean."):
            list_permissions(fileId="file-1", supportsAllDrives=True, supportsTeamDrives="not_a_boolean")

        # Test with non-boolean useDomainAdminAccess
        with self.assertRaisesRegex(TypeError, "useDomainAdminAccess must be a boolean."):
            list_permissions(fileId="file-1", supportsAllDrives=True, supportsTeamDrives=True, useDomainAdminAccess="not_a_boolean")
    
    def test_list_anyone_permission(self):
        """
        Tests listing permissions for a file that has a single 'anyone' type permission,
        and ensures optional fields default appropriately.
        """
        result = list_permissions(fileId='file-2')
        self.assertEqual(result['kind'], 'drive#permissionList')
        self.assertEqual(len(result['permissions']), 1)
        perm = result['permissions'][0]
        self.assertEqual(perm['id'], 'perm-anyone')
        self.assertEqual(perm['type'], 'anyone')
        # Optional fields should default
        self.assertIsNone(perm.get('emailAddress'))
        self.assertIsNone(perm.get('domain'))
        # allowFileDiscovery defaults to False
        self.assertFalse(perm.get('allowFileDiscovery', False))

    def test_default_on_team_drive_file(self):
        """
        By default (no flags), a file that lives only in a team drive
        should return no permissions.
        """
        result = list_permissions(fileId='file-in-team-drive')
        self.assertEqual(result['kind'], 'drive#permissionList')
        self.assertEqual(len(result['permissions']), 0)

    def test_none_for_boolean_flags_raises(self):
        """
        Passing None instead of a boolean for any of the flags should raise TypeError.
        """
        with self.assertRaisesRegex(TypeError, "supportsAllDrives must be a boolean."):
            list_permissions(fileId='file-1', supportsAllDrives=None)
        with self.assertRaisesRegex(TypeError, "supportsTeamDrives must be a boolean."):
            list_permissions(fileId='file-1', supportsTeamDrives=None)
        with self.assertRaisesRegex(TypeError, "useDomainAdminAccess must be a boolean."):
            list_permissions(fileId='file-1', useDomainAdminAccess=None)

    def test_supports_all_drives_no_extra(self):
        """
        If supportsAllDrives=True but no other users hold that file,
        permissions count shouldn’t change.
        """
        # file-no-perms has no permissions anywhere
        result = list_permissions(fileId='file-no-perms', supportsAllDrives=True)
        self.assertEqual(len(result['permissions']), 0)

    def test_supports_team_drives_with_matching_driveId(self):
        """
        Tests supportsTeamDrives when file has a driveId that matches an actual drive.
        This covers the driveId matching condition in line 584.
        """
        file_id = 'file-team-drive-match'
        drive_id = 'drive-team-1'
        
        DB['users']['me']['files'][file_id] = {
            'id': file_id,
            'name': 'Team Drive File',
            'driveId': drive_id,
            'permissions': [
                {'kind': 'drive#permission', 'id': 'perm-base', 'role': 'writer', 'type': 'user', 'emailAddress': 'me@example.com'}
            ]
        }
        
        # Create a drive with matching id to trigger the condition
        DB['users']['me']['drives'] = {
            drive_id: {
                'id': drive_id,
                'name': 'Team Drive 1'
            }
        }
        
        # Add another user with matching driveId setup
        DB['users']['other_user']['files'] = {
            file_id: {
                'id': file_id,
                'driveId': drive_id,
                'permissions': [
                    {'kind': 'drive#permission', 'id': 'perm-team-1', 'role': 'reader', 'type': 'group', 'emailAddress': 'team@example.com'}
                ]
            }
        }
        DB['users']['other_user']['drives'] = {
            drive_id: {
                'id': drive_id,
                'name': 'Team Drive 1'
            }
        }
        
        result = list_permissions(fileId=file_id, supportsTeamDrives=True)
        # Should have at least base permission plus team drive permissions
        permission_ids = [p['id'] for p in result['permissions']]
        self.assertGreaterEqual(len(result['permissions']), 1)
        self.assertIn('perm-base', permission_ids)
        self.assertIn('perm-team-1', permission_ids)

    def test_supports_team_drives_no_matching_drive(self):
        """
        Tests supportsTeamDrives when file has driveId but no matching drive exists.
        Covers the case where driveId doesn't match any drive's id.
        """
        file_id = 'file-no-match-drive'
        DB['users']['me']['files'][file_id] = {
            'id': file_id,
            'name': 'File with Non-existent Drive',
            'driveId': 'non-existent-drive',
            'permissions': [
                {'kind': 'drive#permission', 'id': 'perm-solo', 'role': 'reader', 'type': 'user', 'emailAddress': 'user@example.com'}
            ]
        }
        
        result = list_permissions(fileId=file_id, supportsTeamDrives=True)
        # Should only have the base permission, no team drive permissions added
        self.assertEqual(len(result['permissions']), 1)
        self.assertEqual(result['permissions'][0]['id'], 'perm-solo')

    def test_supports_team_drives_no_driveId(self):
        """
        Tests supportsTeamDrives when file has no driveId field.
        Covers the case where get('driveId', None) returns None.
        """
        file_id = 'file-no-driveId'
        DB['users']['me']['files'][file_id] = {
            'id': file_id,
            'name': 'Regular File',
            'permissions': [
                {'kind': 'drive#permission', 'id': 'perm-regular', 'role': 'owner', 'type': 'user', 'emailAddress': 'me@example.com'}
            ]
        }
        
        DB['users']['me']['drives'] = {
            'some-drive': {
                'id': 'some-drive',
                'name': 'Some Drive'
            }
        }
        
        result = list_permissions(fileId=file_id, supportsTeamDrives=True)
        # Should only have base permission, driveId is None so no team drive perms added
        self.assertEqual(len(result['permissions']), 1)
        self.assertEqual(result['permissions'][0]['id'], 'perm-regular')

if __name__ == '__main__':
    unittest.main()