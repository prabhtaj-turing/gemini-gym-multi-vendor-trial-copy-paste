import unittest
import copy
from datetime import datetime, timezone
from unittest import mock

import pytest  # Add proper mock import

from supabase.edge import deploy_edge_function

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from .. import edge

class TestDeployEdgeFunction(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.org_id_features_enabled = "org_features_enabled_uuid_5a9b3c1d"
        self.org_id_features_disabled = "org_features_disabled_uuid_7e2f8a0b"

        self.project_id_enabled = "proj_enabled_uuid_1c4d7e8f"
        self.project_id_disabled = "proj_disabled_uuid_9b3a6f2c"
        self.project_id_existing_func = "proj_existing_func_uuid_4d8e1g5h"
        self.project_id_no_org = "proj_no_org_uuid_00000000"

        self.fixed_timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        DB['organizations'] = [
            {
                "id": self.org_id_features_enabled, "name": "Org Alpha",
                "created_at": self.fixed_timestamp,
                "subscription_plan": {
                    "id": "plan_pro", "name": "Pro", "price": 20, "currency": "USD",
                    "features": ["edge_functions_enabled"]
                }
            },
            {
                "id": self.org_id_features_disabled, "name": "Org Beta",
                "created_at": self.fixed_timestamp,
                "subscription_plan": {
                    "id": "plan_free", "name": "Free", "price": 0, "currency": "USD",
                    "features": []
                }
            }
        ]
        DB['projects'] = [
            {
                "id": self.project_id_enabled, "name": "Project X",
                "organization_id": self.org_id_features_enabled, "region": "us-west-1",
                "status": "ACTIVE_HEALTHY", "created_at": self.fixed_timestamp
            },
            {
                "id": self.project_id_disabled, "name": "Project Y",
                "organization_id": self.org_id_features_disabled, "region": "us-east-1",
                "status": "ACTIVE_HEALTHY", "created_at": self.fixed_timestamp
            },
            {
                "id": self.project_id_existing_func, "name": "Project Z",
                "organization_id": self.org_id_features_enabled, "region": "eu-central-1",
                "status": "ACTIVE_HEALTHY", "created_at": self.fixed_timestamp
            },
            {
                "id": self.project_id_no_org, "name": "Project NoOrg",
                "organization_id": "non_existent_org_uuid", "region": "us-east-1",
                "status": "ACTIVE_HEALTHY", "created_at": self.fixed_timestamp
            }
        ]
        DB['edge_functions'] = {
            self.project_id_existing_func: [
                {
                    "id": "func_id_for_my_existing_function",
                    "slug": "my-existing-function",
                    "name": "My Existing Function",
                    "version": "version_id_1_abc",
                    "status": "ACTIVE",
                    "created_at": self.fixed_timestamp,
                    "updated_at": self.fixed_timestamp,
                    "entrypoint_path": "index.js",
                    "import_map_path": None,
                    "files": [{"name": "index.js", "content": "console.log('v1');"}]
                }
            ],
            self.project_id_enabled: [],
            self.project_id_disabled: [],
            self.project_id_no_org: [],
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_function_response_valid(self, response, expected_name, expected_slug):
        self.assertIsInstance(response, dict)
        self.assertIn("id", response)
        self.assertIsInstance(response["id"], str)
        self.assertTrue(response["id"])
        self.assertEqual(response["name"], expected_name)
        self.assertEqual(response["slug"], expected_slug)
        self.assertIn("version", response)
        self.assertIsInstance(response["version"], str)
        self.assertTrue(response["version"])
        self.assertIn("status", response)
        self.assertIn(response["status"], ["THROTTLED", "ACTIVE", "REMOVED"])
        self.assertEqual(response["status"], "ACTIVE") # New deployments should start as ACTIVE
        self.assertIn("deployment_id", response)
        self.assertIsInstance(response["deployment_id"], str)
        self.assertTrue(response["deployment_id"])

    def _get_db_function_version(self, project_id, version_id):
        if project_id not in DB['edge_functions']:
            return None
        for f_version in DB['edge_functions'][project_id]:
            if f_version.get("version") == version_id:
                return f_version
        return None

    # Success Scenarios
    def test_deploy_new_function_success(self):
        project_id = self.project_id_enabled
        func_name = "My New Function"
        func_slug = "my-new-function" # Assuming slugification
        files = [{"name": "index.ts", "content": "export default () => 'Hello'"}]

        response = deploy_edge_function(ref=project_id, slug=func_name, files=files)
        self._assert_function_response_valid(response, func_name, func_slug)

        db_func = self._get_db_function_version(project_id, response["version"])
        self.assertIsNotNone(db_func, "Newly deployed version not found in DB")

        self.assertEqual(db_func["id"], response["id"])
        self.assertEqual(db_func["slug"], func_slug)
        self.assertEqual(db_func["name"], func_name)
        self.assertEqual(db_func["status"], response["status"])
        self.assertEqual(db_func["entrypoint_path"], "index.ts") # Default
        self.assertIsNone(db_func["import_map_path"])
        self.assertEqual(db_func["files"], files)
        self.assertIsInstance(db_func["created_at"], datetime)
        self.assertIsInstance(db_func["updated_at"], datetime)
        self.assertGreaterEqual(db_func["updated_at"], db_func["created_at"])

    def test_deploy_existing_function_new_version_success(self):
        project_id = self.project_id_existing_func
        func_name = "My Existing Function"
        func_slug = "my-existing-function"
        new_content = "export default () => 'Hello V2'"
        files = [{"name": "index.js", "content": new_content}]

        initial_versions = [f for f in DB['edge_functions'][project_id] if f["slug"] == func_slug]
        original_func_id = initial_versions[0]["id"]
        original_version_id = initial_versions[0]["version"]

        response = deploy_edge_function(ref=project_id, slug=func_name, files=files, entrypoint_path="index.js")
        self._assert_function_response_valid(response, func_name, func_slug)

        self.assertEqual(response["id"], original_func_id)
        self.assertNotEqual(response["version"], original_version_id)

        all_db_versions = DB['edge_functions'][project_id]
        self.assertEqual(len([v for v in all_db_versions if v["slug"] == func_slug]), 2)

        new_db_version = self._get_db_function_version(project_id, response["version"])
        self.assertIsNotNone(new_db_version)
        self.assertEqual(new_db_version["id"], original_func_id)
        self.assertEqual(new_db_version["name"], func_name)
        self.assertEqual(new_db_version["status"], "ACTIVE")
        self.assertEqual(new_db_version["entrypoint_path"], "index.js")
        self.assertEqual(new_db_version["files"], files)

        old_db_version = self._get_db_function_version(project_id, original_version_id)
        self.assertIsNotNone(old_db_version)
        self.assertEqual(old_db_version["status"], "ACTIVE") # Original status unchanged

    def test_deploy_with_custom_entrypoint_and_import_map_success(self):
        project_id = self.project_id_enabled
        func_name = "Custom Setup Func"
        func_slug = "custom-setup-func"
        entrypoint = "src/main.ts"
        import_map = "import_map.json"
        files = [
            {"name": entrypoint, "content": "import util from './util.ts'; export default util;"},
            {"name": "src/util.ts", "content": "export default () => 'Util output';"},
            {"name": import_map, "content": "{ \"imports\": {} }"}
        ]

        response = deploy_edge_function(
            ref=project_id, slug=func_name, files=files,
            entrypoint_path=entrypoint, import_map_path=import_map
        )
        self._assert_function_response_valid(response, func_name, func_slug)

        db_func = self._get_db_function_version(project_id, response["version"])
        self.assertIsNotNone(db_func)
        self.assertEqual(db_func["entrypoint_path"], entrypoint)
        self.assertEqual(db_func["import_map_path"], import_map)
        self.assertEqual(db_func["files"], files)

    def test_deploy_default_entrypoint_must_exist_in_files(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Entrypoint file 'index.ts' not found in provided files.",
            ref=self.project_id_enabled,
            slug="Test Default Entrypoint",
            files=[{"name": "main.ts", "content": "export default () => 'Hello'"}]
        )

    # Error Scenarios - NotFoundError
    def test_deploy_project_not_found_raises_notfounderror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Project with ID 'non_existent_project_id' not found.",
            ref="non_existent_project_id",
            slug="Test Func",
            files=[{"name": "index.ts", "content": "..."}]
        )

    # Error Scenarios - InvalidInputError
    def test_deploy_empty_function_name_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Function slug cannot be empty.",
            ref=self.project_id_enabled,
            slug="",
            files=[{"name": "index.ts", "content": "..."}]
        )

    def test_deploy_empty_files_list_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Files list cannot be empty.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[]
        )

    def test_deploy_files_item_missing_name_key_raises_invalidinputerror(self):
        """Test that deploying with a file entry missing the 'name' key raises InvalidInputError."""
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            deploy_edge_function(
                ref=self.project_id_enabled,
                slug="test-function",
                files=[{"content": "console.log('test');"}]  # Missing 'name' key
            )
        self.assertEqual(str(context.exception), "File entry at index 0 is missing 'name' key.")

    def test_deploy_files_item_missing_content_key_raises_invalidinputerror(self):
        """Test that deploying with a file entry missing the 'content' key raises InvalidInputError."""
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            deploy_edge_function(
                ref=self.project_id_enabled,
                slug="test-function",
                files=[{"name": "index.ts"}]  # Missing 'content' key
            )
        self.assertEqual(str(context.exception), "File entry at index 0 is missing 'content' key.")

    def test_deploy_entrypoint_not_in_files_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Entrypoint file 'non_existent.ts' not found in provided files.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "..."}],
            entrypoint_path="non_existent.ts"
        )

    def test_deploy_import_map_not_in_files_raises_invalidinputerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Import map file 'non_existent_map.json' not found in provided files.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "..."}],
            import_map_path="non_existent_map.json"
        )

    # Error Scenarios - FeatureNotEnabledError
        
    def test_deploy_project_org_not_found_then_featurenotenabled(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.FeatureNotEnabledError, # Or NotFoundError for org
            expected_message="Failed to determine feature availability: Organization 'non_existent_org_uuid' not found or feature check failed.",
            ref=self.project_id_no_org,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "..."}]
        )

    # Error Scenarios - ValidationError (using custom_errors.ValidationError)
    def test_deploy_missing_required_arg_project_id_raises_typeerror(self):
        # This tests Python's own TypeError for missing required arguments
        with self.assertRaises(TypeError):
            deploy_edge_function(slug="Test", files=[{"name":"f.ts", "content":""}]) # project_id missing

    def test_deploy_missing_required_arg_name_raises_typeerror(self):
        with self.assertRaises(TypeError):
            deploy_edge_function(ref=self.project_id_enabled, files=[{"name":"f.ts", "content":""}]) # name missing

    def test_deploy_missing_required_arg_files_raises_typeerror(self):
        with self.assertRaises(TypeError):
            deploy_edge_function(ref=self.project_id_enabled, slug="Test") # files missing

    def test_deploy_project_id_not_string_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: project_id must be a string.",
            ref=123,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "..."}]
        )

    def test_deploy_name_not_string_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: name must be a string.",
            ref=self.project_id_enabled,
            slug=123,
            files=[{"name": "index.ts", "content": "..."}]
        )

    def test_deploy_files_not_list_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: files must be a list.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files="not_a_list"
        )

    def test_deploy_files_item_not_dict_raises_validationerror(self):
        """Test that deploying with a file entry that is not a dict raises ValidationError."""
        with self.assertRaises(custom_errors.ValidationError) as context:
            deploy_edge_function(
                ref=self.project_id_enabled,
                slug="test-function",
                files=["not-a-dict"]
            )
        self.assertEqual(str(context.exception), "Input validation failed: file entry at index 0 must be a dictionary.")

    def test_deploy_files_item_name_not_string_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: file name at index 0 must be a string.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": 123, "content": "..."}]
        )

    def test_deploy_files_item_content_not_string_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: file content at index 0 must be a string.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": 123}]
        )

    def test_deploy_entrypoint_path_not_string_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: entrypoint_path must be a string or null.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "..."}],
            entrypoint_path=123
        )

    def test_deploy_import_map_path_not_string_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: import_map_path must be a string or null.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "..."}],
            import_map_path=123
        )

    def test_deploy_function_name_with_various_chars_slugifies_correctly(self):
        project_id = self.project_id_enabled
        test_cases = [
            ("Simple Name", "simple-name"),
            ("Name with_underscores", "name-with-underscores"),
            ("Name--with--multiple-hyphens", "name-with-multiple-hyphens"),
            (" Name with leading/trailing spaces ", "name-with-leading-trailing-spaces"),
            ("Name with !@#$%^&*() special chars", "name-with-special-chars"), # Assuming non-alphanum (excluding hyphen) are removed
            ("UPPERCASE NAME", "uppercase-name"),
        ]
        files = [{"name": "index.ts", "content": "export default () => 'Hello'"}]

        for i, (input_name, expected_slug) in enumerate(test_cases):
            # Create a unique name for each subtest to avoid conflicts if slugs are not perfectly unique
            # or if the test runs multiple times without full DB reset between subtests (though setUp/tearDown handles class level)
            current_func_name = f"{input_name} {i}"
            # The expected slug should be based on how `name_to_slug` (from utils context) would process `current_func_name`
            # For simplicity, we'll assume the provided `expected_slug` is the base and append `i`
            # A more accurate test would re-calculate the expected slug for `current_func_name`
            # based on the known `name_to_slug` logic.
            # Let's use the original input_name and expected_slug, and manage DB cleanup.
            
            original_db_functions_for_project = copy.deepcopy(DB['edge_functions'].get(project_id, []))

            with self.subTest(input_slug=input_name, expected_slug=expected_slug):
                response = deploy_edge_function(ref=project_id, slug=input_name, files=files)
                self._assert_function_response_valid(response, input_name, expected_slug)
                
                db_func = self._get_db_function_version(project_id, response["version"])
                self.assertIsNotNone(db_func)
                self.assertEqual(db_func["name"], input_name)
                self.assertEqual(db_func["slug"], expected_slug)
            
            # Restore DB state for this project's functions to avoid interference between subtests
            DB['edge_functions'][project_id] = original_db_functions_for_project

    def test_deploy_unmapped_pydantic_error_raises_validationerror(self):
        """Test that unmapped Pydantic errors are properly handled."""
        # Create a mock ValidationError with an unmapped error type
        class MockValidationError(Exception):
            def errors(self):
                return [{
                    'loc': ('unknown_field',),
                    'type': 'unknown_error_type',
                    'msg': 'Some unknown error'
                }]
        
        # Mock the DeployEdgeFunctionInputArgs to raise our custom error
        with mock.patch('supabase.edge.DeployEdgeFunctionInputArgs', autospec=True) as mock_args:
            mock_args.side_effect = MockValidationError()
            with self.assertRaises(custom_errors.ValidationError) as cm:
                deploy_edge_function(
                    ref=self.project_id_enabled,
                    slug="Test Func",
                    files=[{"name": "index.ts", "content": "..."}]
                )
            self.assertEqual(
                str(cm.exception),
                "Input validation failed: loc=('unknown_field',), type=unknown_error_type, msg=Some unknown error"
            )

    def test_deploy_empty_file_content_raises_invalidinputerror(self):
        """Test that empty file content is rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File content for 'index.ts' cannot be empty or consist only of whitespace.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "   "}]  # Whitespace-only content
        )

    def test_deploy_duplicate_file_names_raises_invalidinputerror(self):
        """Test that duplicate file names are rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Duplicate file name 'index.ts' found in 'files' list.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[
                {"name": "index.ts", "content": "..."},
                {"name": "index.ts", "content": "..."}  # Duplicate name
            ]
        )

    def test_deploy_file_with_whitespace_only_content(self):
        """Test that files with only whitespace content are rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File content for 'index.ts' cannot be empty or consist only of whitespace.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "   \n\t  "}]  # Only whitespace
        )

    def test_deploy_file_with_empty_content(self):
        """Test that files with empty content are rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File content for 'index.ts' cannot be empty or consist only of whitespace.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": ""}]  # Empty content
        )

    def test_deploy_file_model_dict_fallback(self):
        """Test the fallback from model_dump() to dict() for file models."""
        # Create a mock file model that raises AttributeError for model_dump()
        class MockFileModel:
            def __init__(self, name, content):
                self.name = name
                self.content = content
            
            def dict(self):
                return {"name": self.name, "content": self.content}
        
        # Create a mock for DeployEdgeFunctionInputArgs that returns our custom file model
        mock_args = mock.MagicMock()
        mock_args.files = [MockFileModel("index.ts", "export default () => 'Hello'")]
        mock_args.entrypoint_path = "index.ts"
        mock_args.import_map_path = None
        mock_args.project_id = self.project_id_enabled
        mock_args.name = "Test Func"
        mock_args.slug = "Test Func"
        
        with mock.patch('supabase.edge.DeployEdgeFunctionInputArgs', return_value=mock_args):
            response = deploy_edge_function(
                ref=self.project_id_enabled,
                slug="Test Func",
                files=[{"name": "index.ts", "content": "export default () => 'Hello'"}]
            )
            self._assert_function_response_valid(response, "Test Func", "test-func")

    def test_deploy_edge_functions_not_in_db(self):
        """Test deployment when edge_functions is not in DB."""
        # Remove edge_functions from DB
        if 'edge_functions' in DB:
            del DB['edge_functions']
        
        response = deploy_edge_function(
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "export default () => 'Hello'"}]
        )
        self._assert_function_response_valid(response, "Test Func", "test-func")
        self.assertIn('edge_functions', DB)
        self.assertIsInstance(DB['edge_functions'], dict)
        self.assertIn(self.project_id_enabled, DB['edge_functions'])
        self.assertIsInstance(DB['edge_functions'][self.project_id_enabled], list)

    def test_deploy_edge_functions_not_list(self):
        """Test deployment when edge_functions[project_id] is not a list."""
        # Create a mock DB with all necessary structure
        mock_db = {
            'projects': [
                {
                    'id': self.project_id_enabled,
                    'name': 'Project X',
                    'organization_id': self.org_id_features_enabled,
                    'region': 'us-west-1',
                    'status': 'ACTIVE_HEALTHY',
                    'created_at': self.fixed_timestamp
                }
            ],
            'organizations': [
                {
                    'id': self.org_id_features_enabled,
                    'name': 'Org Alpha',
                    'created_at': self.fixed_timestamp,
                    'subscription_plan': {
                        'id': 'plan_pro',
                        'name': 'Pro',
                        'price': 20,
                        'currency': 'USD',
                        'features': ['edge_functions_enabled']
                    }
                }
            ],
            'edge_functions': {
                self.project_id_enabled: "not a list"  # Set non-list value directly
            }
        }
        
        # Mock the DB to use our custom structure
        with mock.patch('supabase.edge.DB', mock_db):
            response = deploy_edge_function(
                ref=self.project_id_enabled,
                slug="Test Func",
                files=[{"name": "index.ts", "content": "export default () => 'Hello'"}]
            )
            self._assert_function_response_valid(response, "Test Func", "test-func")
            # Verify that the DB was updated with a list
            self.assertIsInstance(mock_db['edge_functions'][self.project_id_enabled], list)
            self.assertEqual(len(mock_db['edge_functions'][self.project_id_enabled]), 1)

    def test_deploy_file_with_invalid_function_syntax(self):
        """Test that files with invalid function syntax are rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File 'index.ts' contains invalid function syntax. Functions must have proper parameter parentheses.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "function invalid { return true; }"}]  # Missing parentheses
        )

        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File 'index.ts' contains invalid function syntax. Functions must have a body enclosed in curly braces.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "function invalid() return true;"}]  # Missing curly braces
        )

    def test_deploy_file_with_non_javascript_content(self):
        """Test that files with non-JavaScript content are rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File 'index.ts' does not contain valid JavaScript/TypeScript code. The content appears to be non-code text.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[{"name": "index.ts", "content": "This is just plain text, not JavaScript code."}]
        )

    def test_deploy_file_with_invalid_extension(self):
        """Test that files with invalid extensions are rejected."""
        # First test with a valid entrypoint file to ensure we reach the extension validation
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File 'main.py' must have a .ts or .js extension.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[
                {"name": "index.ts", "content": "export default () => 'Hello'"},  # Valid entrypoint
                {"name": "main.py", "content": "def hello(): return 'world'"}    # Invalid extension
            ]
        )

    def test_deploy_with_validator_initialization_failure(self):
        """Test that deployment fails when TypeScript validator fails to initialize."""
        # Mock the get_validator function to raise an exception
        with mock.patch('supabase.edge.get_validator', side_effect=Exception("Failed to download TypeScript compiler")):
            self.assert_error_behavior(
                func_to_call=deploy_edge_function,
                expected_exception_type=custom_errors.InvalidInputError,
                expected_message="Failed to initialize TypeScript validator: Failed to download TypeScript compiler",
                ref=self.project_id_enabled,
                slug="Test Func",
                files=[{"name": "index.ts", "content": "export default () => 'Hello'"}]
            )

    def test_deploy_edge_functions_db_entry_not_list(self):
        """Test that if DB['edge_functions'][project_id] is not a list, it is reset to a list and function is deployed."""
        # Set up DB with a non-list entry
        edge.DB.setdefault("edge_functions", {})[self.project_id_enabled] = "not-a-list"
        result = deploy_edge_function(
            ref=self.project_id_enabled,
            slug="test-function-reset-db",
            files=[{"name": "index.ts", "content": "export const x = 1;"}],
        )
        self.assertIn("id", result)
        self.assertIn("version", result)

    def test_deploy_with_typescript_diagnostics_error(self):
        """Test that TypeScript diagnostic errors are properly formatted."""
        # Create a mock TypeScript diagnostic error
        mock_diagnostic = {
            'messageText': 'Type error',
            'file': {'fileName': 'index.ts'},
            'start': 10,
            'length': 5,
            'category': 1,  # Error category
            'code': 2345
        }
        
        # Mock the TypeScript validator to return our diagnostic error
        with mock.patch('supabase.edge.get_validator') as mock_validator:
            # Mock the validator to return a tuple of (False, [diagnostics])
            mock_validator.return_value.validate.return_value = (False, [mock_diagnostic])
            
            self.assert_error_behavior(
                func_to_call=deploy_edge_function,
                expected_exception_type=custom_errors.InvalidInputError,
                expected_message="File 'index.ts' contains invalid TypeScript/JavaScript code: Type error",
                ref=self.project_id_enabled,
                slug="Test Func",
                files=[{"name": "index.ts", "content": "let x: number = 'string';"}]  # Type error
            )

    def test_deploy_with_multiple_typescript_diagnostics(self):
        """Test that multiple TypeScript diagnostic errors are properly formatted."""
        # Create multiple mock TypeScript diagnostic errors
        mock_diagnostics = [
            {
                'messageText': 'Type error 1',
                'file': {'fileName': 'index.ts'},
                'start': 10,
                'length': 5,
                'category': 1,
                'code': 2345
            },
            {
                'messageText': 'Type error 2',
                'file': {'fileName': 'index.ts'},
                'start': 20,
                'length': 5,
                'category': 1,
                'code': 2346
            }
        ]
        
        # Mock the TypeScript validator to return multiple diagnostic errors
        with mock.patch('supabase.edge.get_validator') as mock_validator:
            # Mock the validator to return a tuple of (False, [diagnostics])
            mock_validator.return_value.validate.return_value = (False, mock_diagnostics)
            
            self.assert_error_behavior(
                func_to_call=deploy_edge_function,
                expected_exception_type=custom_errors.InvalidInputError,
                expected_message="File 'index.ts' contains invalid TypeScript/JavaScript code: Type error 1; Type error 2",
                ref=self.project_id_enabled,
                slug="Test Func",
                files=[{"name": "index.ts", "content": "let x: number = 'string'; let y: string = 42;"}]  # Multiple type errors
            )

    def test_deploy_json_file_with_whitespace_content(self):
        """Test that JSON files with only whitespace content are rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File content for 'import_map.json' cannot be empty or consist only of whitespace.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[
                {"name": "index.ts", "content": "export default () => 'Hello'"},
                {"name": "import_map.json", "content": "   \n\t  "}  # Only whitespace
            ],
            import_map_path="import_map.json"
        )

    def test_deploy_json_file_with_empty_content(self):
        """Test that JSON files with empty content are rejected."""
        self.assert_error_behavior(
            func_to_call=deploy_edge_function,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File content for 'import_map.json' cannot be empty or consist only of whitespace.",
            ref=self.project_id_enabled,
            slug="Test Func",
            files=[
                {"name": "index.ts", "content": "export default () => 'Hello'"},
                {"name": "import_map.json", "content": ""}  # Empty content
            ],
            import_map_path="import_map.json"
        )


if __name__ == '__main__':
    unittest.main()