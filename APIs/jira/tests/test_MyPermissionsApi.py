from ..import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
import jira as JiraAPI

class TestMyPermissionsApi(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Reset the global DB state before each test
        DB.clear()
        DB.update({
            "projects": {
                "TEST": {
                    "key": "TEST",
                    "name": "Test Project",
                    "permissionScheme": {
                        "id": "1",
                        "name": "Default Scheme"
                    }
                }
            },
            "issues": {
                "TEST-1": {
                    "key": "TEST-1",
                    "projectKey": "TEST",
                    "type": "Bug"
                }
            },
            "permissions": {
                "CREATE_ISSUE": True,
                "EDIT_ISSUE": True,
                "DELETE_ISSUE": True,
                "ASSIGN_ISSUE": True,
                "CLOSE_ISSUE": True
            }
        })

    def test_get_current_user_permissions_basic(self):
        """Test getting current user permissions without project or issue context."""
        perms = JiraAPI.MyPermissionsApi.get_current_user_permissions()
        
        # Check basic structure
        self.assertIn("permissions", perms)
        self.assertIsInstance(perms["permissions"], list)
        self.assertIn("CREATE_ISSUE", perms["permissions"])
        self.assertIn("EDIT_ISSUE", perms["permissions"])
        self.assertIn("DELETE_ISSUE", perms["permissions"])
        self.assertIn("ASSIGN_ISSUE", perms["permissions"])
        self.assertIn("CLOSE_ISSUE", perms["permissions"])

    def test_get_current_user_permissions_with_project(self):
        """Test getting current user permissions with project context."""
        perms = JiraAPI.MyPermissionsApi.get_current_user_permissions(projectKey="TEST")
        
        # Check basic structure
        self.assertIn("permissions", perms)
        self.assertIsInstance(perms["permissions"], list)
        self.assertIn("CREATE_ISSUE", perms["permissions"])
        self.assertIn("EDIT_ISSUE", perms["permissions"])
        self.assertIn("DELETE_ISSUE", perms["permissions"])
        self.assertIn("ASSIGN_ISSUE", perms["permissions"])
        self.assertIn("CLOSE_ISSUE", perms["permissions"])

    def test_get_current_user_permissions_with_issue(self):
        """Test getting current user permissions with issue context."""
        perms = JiraAPI.MyPermissionsApi.get_current_user_permissions(issueKey="TEST-1")
        
        # Check basic structure
        self.assertIn("permissions", perms)
        self.assertIsInstance(perms["permissions"], list)
        self.assertIn("CREATE_ISSUE", perms["permissions"])
        self.assertIn("EDIT_ISSUE", perms["permissions"])
        self.assertIn("DELETE_ISSUE", perms["permissions"])
        self.assertIn("ASSIGN_ISSUE", perms["permissions"])
        self.assertIn("CLOSE_ISSUE", perms["permissions"])

    def test_get_current_user_permissions_with_project_and_issue(self):
        """Test getting current user permissions with both project and issue context."""
        perms = JiraAPI.MyPermissionsApi.get_current_user_permissions(
            projectKey="TEST",
            issueKey="TEST-1"
        )
        
        # Check basic structure
        self.assertIn("permissions", perms)
        self.assertIsInstance(perms["permissions"], list)
        self.assertIn("CREATE_ISSUE", perms["permissions"])
        self.assertIn("EDIT_ISSUE", perms["permissions"])
        self.assertIn("DELETE_ISSUE", perms["permissions"])
        self.assertIn("ASSIGN_ISSUE", perms["permissions"])
        self.assertIn("CLOSE_ISSUE", perms["permissions"])

    def test_get_current_user_permissions_invalid_project(self):
        """Test getting current user permissions with invalid project."""
        self.assert_error_behavior(
            func_to_call=JiraAPI.MyPermissionsApi.get_current_user_permissions,
            expected_exception_type=ValueError,
            expected_message="Project 'INVALID' not found.",
            projectKey="INVALID"
        )

    def test_get_current_user_permissions_invalid_issue(self):
        """Test getting current user permissions with invalid issue."""
        self.assert_error_behavior(
            func_to_call=JiraAPI.MyPermissionsApi.get_current_user_permissions,
            expected_exception_type=ValueError,
            expected_message="Issue 'INVALID-1' not found.",
            issueKey="INVALID-1"
        )

    def test_get_current_user_permissions_empty_project(self):
        """Test getting current user permissions with empty project key."""
        self.assert_error_behavior(
            func_to_call=JiraAPI.MyPermissionsApi.get_current_user_permissions,
            expected_exception_type=ValueError,
            expected_message="projectKey",
            projectKey=""
        )

    def test_get_current_user_permissions_empty_issue(self):
        """Test getting current user permissions with empty issue key."""
        self.assert_error_behavior(
            func_to_call=JiraAPI.MyPermissionsApi.get_current_user_permissions,
            expected_exception_type=ValueError,
            expected_message="issueKey",
            issueKey=""
        )

    def test_get_current_user_permissions_empty_db(self):
        """Test getting current user permissions when DB is empty."""
        DB.clear()
        perms = JiraAPI.MyPermissionsApi.get_current_user_permissions()
        self.assertIn("permissions", perms)
        self.assertIsInstance(perms["permissions"], list)
        self.assertEqual(len(perms["permissions"]), 0)

    def test_get_current_user_permissions_none_project(self):
        """Test getting current user permissions with None project key."""
        perms = JiraAPI.MyPermissionsApi.get_current_user_permissions(projectKey=None)
        self.assertIn("permissions", perms)
        self.assertIsInstance(perms["permissions"], list)
        self.assertIn("CREATE_ISSUE", perms["permissions"])

    def test_get_current_user_permissions_none_issue(self):
        """Test getting current user permissions with None issue key."""
        perms = JiraAPI.MyPermissionsApi.get_current_user_permissions(issueKey=None)
        self.assertIn("permissions", perms)
        self.assertIsInstance(perms["permissions"], list)
        self.assertIn("CREATE_ISSUE", perms["permissions"])

    def test_get_current_user_permissions_invalid_project_type(self):
        """Test getting current user permissions with invalid project key type."""
        self.assert_error_behavior(
            func_to_call=JiraAPI.MyPermissionsApi.get_current_user_permissions,
            expected_exception_type=TypeError,
            expected_message="projectKey must be a string.",
            projectKey=123
        )

    def test_get_current_user_permissions_invalid_issue_type(self):
        """Test getting current user permissions with invalid issue key type."""
        self.assert_error_behavior(
            func_to_call=JiraAPI.MyPermissionsApi.get_current_user_permissions,
            expected_exception_type=TypeError,
            expected_message="issueKey must be a string.",
            issueKey=123
        )



