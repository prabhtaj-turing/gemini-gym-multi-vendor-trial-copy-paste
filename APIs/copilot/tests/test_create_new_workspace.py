import copy
import unittest
import os
from unittest.mock import patch, MagicMock

from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from .. import create_new_workspace
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestCreateNewWorkspace(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Store original DB state
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()  # Clear the actual global DB

        # Populate DB directly for this test class
        DB['workspace_root'] = '/test_workspace'
        DB['cwd'] = '/test_workspace'
        DB['file_system'] = {
            DB['workspace_root']: {
                'path': DB['workspace_root'],
                'is_directory': True,
                'content_lines': [],
                'size_bytes': 0,
                'last_modified': '2023-01-01T00:00:00Z'
            }
        }

    def tearDown(self):
        # Restore original DB state
        DB.clear()
        DB.update(self._original_DB_state)

    @patch('copilot.project_setup.utils.call_llm')
    def test_successful_workspace_creation_basic_query(self, mock_call_llm):
        # Mock the LLM response in the expected format
        mock_call_llm.return_value = """Summary: Create a simple Python hello world script

----STEPS_SEPARATOR----

[
    {
        "type": "file_creation",
        "description": "Create main.py file with print statement",
        "details": {
            "file_path": "main.py",
            "content": "print('Hello, World!')"
        }
    },
    {
        "type": "instruction",
        "description": "Set up basic project structure",
        "details": {
            "text": "Your Python hello world script is ready to run!"
        }
    }
]"""
        
        query = "Create a simple Python script that prints hello world."
        result = create_new_workspace(query=query)

        self.assertIsInstance(result, dict, "Result should be a dictionary.")
        self.assertIn("query", result, "Result should contain the original query.")
        self.assertEqual(result["query"], query)

        self.assertIn("summary", result, "Result should contain a 'summary' field.")
        self.assertIsInstance(result["summary"], str, "'summary' field should be a string.")

        self.assertIn("steps", result, "Result should contain a 'steps' field.")
        self.assertIsInstance(result["steps"], list, "'steps' field should be a list.")
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()

    @patch('copilot.project_setup.utils.call_llm')
    def test_successful_workspace_creation_complex_query(self, mock_call_llm):
        # Mock the LLM response for complex query in the expected format
        mock_call_llm.return_value = """Summary: Set up Next.js project with TypeScript and Tailwind CSS

----STEPS_SEPARATOR----

[
    {
        "type": "terminal_command",
        "description": "Initialize Next.js project with TypeScript template",
        "details": {
            "command": "npx create-next-app@latest my-app --typescript"
        }
    },
    {
        "type": "terminal_command",
        "description": "Install and configure Tailwind CSS",
        "details": {
            "command": "cd my-app && npm install -D tailwindcss postcss autoprefixer"
        }
    },
    {
        "type": "terminal_command",
        "description": "Set up Git repository",
        "details": {
            "command": "cd my-app && git init"
        }
    }
]"""
        
        query = "Set up a new Next.js project with TypeScript and Tailwind CSS, including initial git setup."
        result = create_new_workspace(query=query)

        self.assertIsInstance(result, dict, "Result should be a dictionary.")
        self.assertIn("query", result, "Result should contain the original query.")
        self.assertEqual(result["query"], query)

        self.assertIn("summary", result, "Result should contain a 'summary' field.")
        self.assertIsInstance(result["summary"], str, "'summary' field should be a string.")

        self.assertIn("steps", result, "Result should contain a 'steps' field.")
        self.assertIsInstance(result["steps"], list, "'steps' field should be a list.")
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()

    def test_query_empty_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_new_workspace,
            query="",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_query_whitespace_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_new_workspace,
            query="   ",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_query_none_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_new_workspace,
            query=None,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_query_invalid_type_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_new_workspace,
            query=123,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_query_invalid_type_list_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_new_workspace,
            query=["list", "item"],
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_workspace_root_missing_in_db_raises_workspace_not_available_error(self):
        # This test assumes that create_new_workspace (or utils it calls and error-handles)
        # requires DB['workspace_root'] and raises WorkspaceNotAvailableError if it's missing.
        DB.pop('workspace_root', None)

        # Clean up file_system if workspace_root was used as a key, to avoid downstream issues
        # if the function attempts to access file_system with a now-missing root path.
        # This specific path '/test_workspace' was tied to the original DB['workspace_root'].
        if '/test_workspace' in DB.get('file_system', {}):
            del DB['file_system']['/test_workspace']

        self.assert_error_behavior(
            func_to_call=create_new_workspace,
            query="A valid query.",
            expected_exception_type=custom_errors.WorkspaceNotAvailableError,
            expected_message="Workspace root is not configured."
        )

    @patch('copilot.project_setup.utils.call_llm')
    def test_cwd_missing_in_db_still_succeeds_if_workspace_root_exists(self, mock_call_llm):
        # Mock the LLM response in the expected format
        mock_call_llm.return_value = """Summary: Create a small utility script

----STEPS_SEPARATOR----

[
    {
        "type": "file_creation",
        "description": "Create utility.py file",
        "details": {
            "file_path": "utility.py",
            "content": "def main():\\n    print('Utility script running!')\\n\\nif __name__ == '__main__':\\n    main()"
        }
    },
    {
        "type": "instruction",
        "description": "Add main function with utility logic",
        "details": {
            "text": "Your utility script is ready with a main function!"
        }
    }
]"""
        
        # Assumes that if 'cwd' is missing, it might default to 'workspace_root' internally,
        # allowing the function to proceed if 'workspace_root' is available.
        DB.pop('cwd', None)
        query = "Create a small utility script."

        result = create_new_workspace(query=query)

        self.assertIsInstance(result, dict, "Result should be a dictionary even if cwd was missing but defaulted.")
        self.assertEqual(result.get("query"), query)
        self.assertIn("summary", result)
        self.assertIsInstance(result["summary"], str)
        self.assertIn("steps", result)
        self.assertIsInstance(result["steps"], list)
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()


if __name__ == '__main__':
    unittest.main()
