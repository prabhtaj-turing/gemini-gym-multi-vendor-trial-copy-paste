# cursor/tests/test_utils.py
import unittest
import copy
import os
from unittest.mock import patch
import sys
# Ensure parent directory is in path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the utils module to test its functions
from ..SimulationEngine import utils
from .. import DB as GlobalDBSource
# Import call_llm to ensure its path is correct for mocking
from ..SimulationEngine.llm_interface import GEMINI_API_KEY_FROM_ENV
from ..SimulationEngine.llm_interface import call_llm
from common_utils.base_case import BaseTestCaseWithErrorHandler

# --- Helper to check if API key is available for integration tests ---
GEMINI_API_KEY_IS_AVAILABLE = bool(GEMINI_API_KEY_FROM_ENV)

class TestProposeCodeEditMocked(BaseTestCaseWithErrorHandler):
    """
    Unit tests for the propose_code_edits utility function,
    with the external LLM call MOCKED.
    """

    def setUp(self):
        """Prepares an isolated database state for each test method."""
        self.pristine_db_state = copy.deepcopy(GlobalDBSource)
        self.db_for_test = copy.deepcopy(self.pristine_db_state)
        
        self.db_for_test["file_system"] = {}
        self.ws_root = self.db_for_test.get("workspace_root", "/test_ws_propose_mock")
        self.db_for_test["workspace_root"] = self.ws_root
        self._add_dir_to_db(self.ws_root) # Use instance method
        self.db_for_test["cwd"] = self.ws_root

        self.utils_db_patcher = patch('cursor.SimulationEngine.utils.DB', self.db_for_test)
        self.utils_db_patcher.start()
        
        # Create a patch for the call_llm function directly where it's used in the utils module
        # This ensures we're replacing the actual function that's being called
        self.call_llm_patcher = patch.object(utils, 'call_llm')
        self.mock_call_llm = self.call_llm_patcher.start()
        
    def tearDown(self):
        """Restores original state after each test."""
        self.utils_db_patcher.stop()
        self.call_llm_patcher.stop()

    def _add_dir_to_db(self, path: str):
        """Adds a directory to this test's DB instance if it doesn't exist."""
        # Simplified for test setup, assumes path is relative to ws_root or absolute
        abs_path = path
        if not os.path.isabs(path):
             abs_path = os.path.normpath(os.path.join(self.ws_root, path))

        if abs_path not in self.db_for_test["file_system"]:
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path, "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "T_SETUP_DIR"
            }
        # Simplified parent creation for tests; production utils has more robust logic
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path and parent_dir != self.ws_root and \
           parent_dir not in self.db_for_test["file_system"]:
            self._add_dir_to_db(parent_dir) # Recursive call for parent
        return abs_path

    def _add_file_to_db(self, path: str, content_lines_raw: list[str]):
        """Adds a file with specified content to this test's DB instance."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.ws_root, path))
        
        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.ws_root and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_db(dir_name) # Ensure parent directory exists

        # Normalize content lines using the actual utility function
        content_lines = utils._normalize_lines(content_lines_raw, ensure_trailing_newline=True)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path, "is_directory": False,
            "content_lines": content_lines,
            "size_bytes": utils.calculate_size_bytes(content_lines),
            "last_modified": "T_SETUP_FILE"
        }
        return abs_path

    def test_propose_for_new_file_mocked(self):
        """Verify proposal generation for a new file (mocked LLM)."""
        target_file = "new_service.py" # Relative to ws_root for this test
        user_instructions = "Create a Python service with a health check endpoint."
        
        # The expected instruction string that will be returned by the mocked LLM
        expected_llm_instructions = "I will create a new Python Flask service with a `/health` endpoint."
        
        expected_llm_code_edit = (
            "from flask import Flask\n\n"
            "app = Flask(__name__)\n\n"
            "@app.route('/health')\n"
            "def health_check():\n"
            "    return {'status': 'healthy'}, 200\n\n"
            "if __name__ == '__main__':\n"
            "    app.run(host='0.0.0.0', port=8080)" 
        )
        
        # Set up the mock with a fixed return value
        mock_llm_response = (
            f"Instructions String: {expected_llm_instructions}\n"
            f"----EDIT_SEPARATOR----\n"
            f"Code Edit String: {expected_llm_code_edit}"
        )
        
        # Important: Configure the mock properly
        self.mock_call_llm.return_value = mock_llm_response

        result = utils.propose_code_edits(target_file, user_instructions)

        # Assertions
        self.assertEqual(result["instructions"], expected_llm_instructions)
        self.assertEqual(result["code_edit"], expected_llm_code_edit) # Assuming no markdown here
        
        # Verify call and prompt details
        self.mock_call_llm.assert_called_once()
        prompt_text_args = self.mock_call_llm.call_args[1] # Get kwargs of the call
        prompt_text = prompt_text_args.get('prompt_text', '') # Get 'prompt_text' kwarg

        self.assertIn(f"TARGET FILE: {target_file}", prompt_text)
        self.assertIn(f"USER REQUEST: \"{user_instructions}\"", prompt_text)
        self.assertIn("# This is a new file or the existing file is empty.", prompt_text, 
                      "Prompt should indicate context for a new file.")

    def test_propose_for_existing_file_modification_mocked(self):
        """Verify proposal generation for modifying an existing file (mocked LLM)."""
        
        target_file_rel = "module.py" # Relative to ws_root
        original_content = ["def greet(name):\n", "    print(f'Hello, {name}')\n"]
        self._add_file_to_db(target_file_rel, original_content) # Use the corrected helper name
        user_instructions = "Change greeting to be formal, add docstring."

        # The expected instruction string that will be returned by the mocked LLM
        expected_llm_instructions = "I will change the greeting to be formal and add a docstring to the `greet` function."
        
        expected_llm_code_edit = (
            "# ... existing code ...\n"
            "def greet(name):\n"
            "    \"\"\"Greets formally.\"\"\"\n"
            "    print(f'Greetings, {name}!')\n"
            "# ... existing code ...\n"
        )
        
        # Set up the mock with a fixed return value
        mock_llm_response = (
            f"Instructions String: {expected_llm_instructions}\n"
            f"----EDIT_SEPARATOR----\n"
            f"Code Edit String:\n```python\n{expected_llm_code_edit}```"
        )
        
        # Important: Configure the mock properly
        self.mock_call_llm.return_value = mock_llm_response
        
        # Make the call to the function under test
        result = utils.propose_code_edits(target_file_rel, user_instructions)
        
        # Assertions
        self.assertEqual(result["instructions"], expected_llm_instructions)
        self.assertEqual(result["code_edit"], expected_llm_code_edit.strip(), 
                         "Parsed code_edit string should match the expected, stripped of markdown.")
        
        # Verify call and prompt details
        self.mock_call_llm.assert_called_once()
        prompt_text = self.mock_call_llm.call_args[1]['prompt_text']
        self.assertIn("".join(original_content), prompt_text, 
                      "Original file content should be part of the prompt to the LLM.")
        self.assertIn("CURRENT CONTENT:", prompt_text,
                      "Prompt should include the current content of the file.")

    # (Include other mocked tests like parsing errors, missing inputs, error propagation from call_llm)


class TestProposeCommandMocked(BaseTestCaseWithErrorHandler):
    """
    Unit tests for the propose_command utility function,
    with the external LLM call MOCKED.
    """

    def setUp(self):
        """Prepares an isolated database state for each test method."""
        self.pristine_db_state = copy.deepcopy(GlobalDBSource)
        self.db_for_test = copy.deepcopy(self.pristine_db_state)

        # Setup a predictable DB state for tests
        self.ws_root = "/test_ws_propose_cmd_mock"
        self.db_for_test["workspace_root"] = self.ws_root
        self.db_for_test["cwd"] = os.path.join(self.ws_root, "src")
        self.db_for_test["file_system"] = {
             self.ws_root: {"path": self.ws_root, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "T_SETUP"},
             self.db_for_test["cwd"]: {"path": self.db_for_test["cwd"], "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "T_SETUP"}
        }

        self.utils_db_patcher = patch('cursor.SimulationEngine.utils.DB', self.db_for_test)
        self.utils_db_patcher.start()

        # Patch call_llm used within the utils module
        self.call_llm_patcher = patch.object(utils, 'call_llm')
        self.mock_call_llm = self.call_llm_patcher.start()

    def tearDown(self):
        """Restores original state after each test."""
        self.utils_db_patcher.stop()
        self.call_llm_patcher.stop()

    def test_propose_simple_command_mocked(self):
        """Verify proposal for a simple command (mocked LLM)."""
        user_objective = "List files in the current directory with details."
        expected_explanation = "This command lists files with details."
        expected_command = "ls -l"
        expected_is_background = False

        mock_llm_response = (
            f"{expected_explanation}\n"
            f"----CMD_SEPARATOR----\n"
            f"{expected_command}\n"
            f"----CMD_SEPARATOR----\n"
            f"{str(expected_is_background).lower()}"
        )
        self.mock_call_llm.return_value = mock_llm_response

        result = utils.propose_command(user_objective)

        self.assertEqual(result["explanation"], expected_explanation)
        self.assertEqual(result["command"], expected_command)
        self.assertEqual(result["is_background"], expected_is_background)

        self.mock_call_llm.assert_called_once()
        prompt_text = self.mock_call_llm.call_args[1]['prompt_text']
        self.assertIn(user_objective, prompt_text)
        self.assertIn(f'Current Working Directory: "{self.db_for_test["cwd"]}"', prompt_text)

    def test_propose_interactive_command_mocked(self):
        """Verify proposal adds '| cat' for interactive commands (mocked LLM)."""
        user_objective = "Show the git commit history."
        expected_explanation = "This command shows git history non-interactively."
        expected_command = "git log | cat" # Expecting '| cat'
        expected_is_background = False

        mock_llm_response = (
            f"{expected_explanation}\n"
            f"----CMD_SEPARATOR----\n"
            f"{expected_command}\n"
            f"----CMD_SEPARATOR----\n"
            f"{str(expected_is_background).lower()}"
        )
        self.mock_call_llm.return_value = mock_llm_response

        result = utils.propose_command(user_objective)

        self.assertEqual(result["explanation"], expected_explanation)
        self.assertEqual(result["command"], expected_command)
        self.assertEqual(result["is_background"], expected_is_background)
        self.assertIn("| cat", result["command"], "Command should include '| cat' for git log.")

    def test_propose_background_command_mocked(self):
        """Verify proposal suggests background execution (mocked LLM)."""
        user_objective = "Start a development server using npm."
        expected_explanation = "This command starts the npm dev server in the background."
        expected_command = "npm run dev"
        expected_is_background = True # Expecting True

        mock_llm_response = (
            f"{expected_explanation}\n"
            f"----CMD_SEPARATOR----\n"
            f"{expected_command}\n"
            f"----CMD_SEPARATOR----\n"
            f"{str(expected_is_background).lower()}"
        )
        self.mock_call_llm.return_value = mock_llm_response

        result = utils.propose_command(user_objective)

        self.assertEqual(result["explanation"], expected_explanation)
        self.assertEqual(result["command"], expected_command)
        self.assertEqual(result["is_background"], expected_is_background)

    def test_propose_command_llm_format_error_mocked(self):
        """Verify handling of incorrect LLM response format (mocked LLM)."""
        user_objective = "Find python files."
        # Malformed response (missing separators)
        mock_llm_response = "Just run find . -name '*.py'"
        self.mock_call_llm.return_value = mock_llm_response

        result = utils.propose_command(user_objective)

        self.assertEqual(result["command"], "")
        self.assertTrue("format error" in result["explanation"].lower())
        self.assertEqual(result["is_background"], False)

    def test_propose_command_llm_empty_command_mocked(self):
        """Verify handling when LLM proposes an empty command (mocked LLM)."""
        user_objective = "Do nothing."
        expected_explanation = "This command does nothing."
        expected_command = "" # Empty command
        expected_is_background = False

        mock_llm_response = (
            f"{expected_explanation}\n"
            f"----CMD_SEPARATOR----\n"
            f"{expected_command}\n"
            f"----CMD_SEPARATOR----\n"
            f"{str(expected_is_background).lower()}"
        )
        self.mock_call_llm.return_value = mock_llm_response

        result = utils.propose_command(user_objective)

        self.assertEqual(result["command"], "")
        self.assertTrue("empty command" in result["explanation"].lower())
        self.assertEqual(result["is_background"], False)


@unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
class TestProposeCodeEditIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration tests for propose_code_edits, making actual LLM calls.
    Requires GEMINI_API_KEY to be set in the environment.
    """
    def setUp(self):
        """Prepares an isolated database state."""
        self.pristine_db_state = copy.deepcopy(GlobalDBSource)
        self.db_for_test = copy.deepcopy(self.pristine_db_state)
        self.db_for_test["file_system"] = {}
        self.ws_root = self.db_for_test.get("workspace_root", "/test_ws_propose_live")
        self.db_for_test["workspace_root"] = self.ws_root
        self._add_dir_to_db(self.ws_root) # Use instance method
        self.db_for_test["cwd"] = self.ws_root
        
        self.utils_db_patcher = patch('cursor.SimulationEngine.utils.DB', self.db_for_test)
        self.utils_db_patcher.start()

    def tearDown(self):
        """Restores original state."""
        self.utils_db_patcher.stop()

    def _add_dir_to_db(self, path: str):
        """Adds a directory to this test's DB instance if it doesn't exist."""
        abs_path = path
        if not os.path.isabs(path):
             abs_path = os.path.normpath(os.path.join(self.ws_root, path))
        if abs_path not in self.db_for_test["file_system"]:
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path, "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "T_SETUP_DIR"
            }
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path and parent_dir != self.ws_root and \
           parent_dir not in self.db_for_test["file_system"] and \
           parent_dir != os.path.dirname(self.ws_root):
                self._add_dir_to_db(parent_dir)
        return abs_path

    def _add_file_to_db(self, path: str, content_lines_raw: list[str]):
        """Adds a file with specified content to this test's DB instance."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.ws_root, path))
        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.ws_root and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_db(dir_name)
        content_lines = utils._normalize_lines(content_lines_raw, ensure_trailing_newline=True)
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path, "is_directory": False,
            "content_lines": content_lines,
            "size_bytes": utils.calculate_size_bytes(content_lines),
            "last_modified": "T_SETUP_FILE_LIVE"
        }

    def test_propose_new_python_function_live(self):
        """Integration test: Propose creating a new Python function."""
        target_file_rel = "new_math_utils.py" # Relative to ws_root
        user_instructions = "Create a new python file with a function 'add' taking two numbers, returning their sum. Include a docstring."
        
        result = utils.propose_code_edits(target_file_rel, user_instructions)

        print(f"\n[LIVE TEST - NEW FILE '{target_file_rel}']\nInstructions: {result['instructions']}\nCode Edit:\n{result['code_edit']}")

        self.assertIsInstance(result["instructions"], str)
        self.assertTrue(len(result["instructions"]) > 10, "Instructions string seems too short.")
        self.assertRegex(result["code_edit"], r"def add\s*\(\s*[\w\d_]+\s*,\s*[\w\d_]+\s*\):", "Function 'add' with two parameters not found or has unexpected format.")
        self.assertIn("sum", result["code_edit"].lower())
        self.assertIn("\"\"\"", result["code_edit"]) 

    def test_propose_modify_existing_python_function_live(self):
        """Integration test: Propose modifying an existing Python function."""
        target_file_rel = "existing_module.py" # Relative to ws_root
        original_content = ["def calculate_area(length, width):\n", "    return length * width\n"]
        self._add_file_to_db(target_file_rel, original_content)
        user_instructions = "Modify 'calculate_area' to print dimensions before returning area."

        result = utils.propose_code_edits(target_file_rel, user_instructions)

        print(f"\n[LIVE TEST - MODIFY FILE '{target_file_rel}']\nInstructions: {result['instructions']}\nCode Edit:\n{result['code_edit']}")

        self.assertIsInstance(result["instructions"], str)
        self.assertTrue(len(result["instructions"]) > 10)
        self.assertIn("def calculate_area", result["code_edit"])
        self.assertIn("print(f", result["code_edit"]) 
        self.assertIn("length * width", result["code_edit"])

    def test_propose_complex_refactor_live(self):
        """Integration test: Propose a more complex refactoring task involving multiple functions."""
        target_file_rel = "data_processor.py" # Relative to ws_root
        original_content = [
            "def process_records(records):\n",
            "    results = []\n",
            "    for r_id, r_data in records.items():\n",
            "        # Validate data before processing\n",
            "        if r_data is None or not isinstance(r_data, dict):\n",
            "            print(f\"Skipping invalid record: {r_id}\")\n",
            "            continue\n",
            "        \n",
            "        # Transform data\n",
            "        transformed_value = r_data.get('value', 0) * 2 + r_data.get('bonus', 0)\n",
            "        results.append({'id': r_id, 'processed': transformed_value})\n",
            "    \n",
            "    # Log summary\n",
            "    print(f\"Processed {len(results)} records successfully.\")\n",
            "    return results\n"
        ]
        self._add_file_to_db(target_file_rel, original_content)
        user_instructions = (
            "Refactor 'process_records' in data_processor.py. "
            "Extract the data validation logic into a new private helper function called '_is_record_valid(record_id, record_data)'. "
            "Extract the data transformation logic into another new private helper function called '_transform_record_data(record_data)'. "
            "Update 'process_records' to use these two new helper functions."
        )

        # Make the actual LLM call via propose_code_edits
        result = utils.propose_code_edits(
            target_file_path_str=target_file_rel,
            user_edit_instructions=user_instructions
        )

        # Print for manual review - very important for complex live tests
        print(f"\n[LIVE TEST - COMPLEX REFACTOR '{target_file_rel}']")
        print(f"User Instructions: {user_instructions}")
        print(f"LLM Instructions: {result['instructions']}")
        print(f"LLM Code Edit:\n{result['code_edit']}")
        print("-" * 30)

        # Assertions are more about structure and key elements due to LLM variability
        self.assertIsInstance(result["instructions"], str, "Instructions should be a string.")
        self.assertTrue(len(result["instructions"]) > 20, "Instructions string seems too short for a refactor.")
        self.assertIsInstance(result["code_edit"], str, "Code edit should be a string.")
        
        # Check for expected new function definitions
        self.assertIn("def _is_record_valid(", result["code_edit"], "Expected '_is_record_valid' function definition.")
        self.assertIn("def _transform_record_data(", result["code_edit"], "Expected '_transform_record_data' function definition.")
        
        # Check for calls to the new helper functions within the main function
        self.assertIn("_is_record_valid(r_id, r_data)", result["code_edit"], "Expected call to '_is_record_valid'.")
        self.assertIn("_transform_record_data(r_data)", result["code_edit"], "Expected call to '_transform_record_data'.")


@unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
class TestProposeCommandIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration tests for propose_command, making actual LLM calls.
    Requires GEMINI_API_KEY to be set in the environment.
    """
    def setUp(self):
        """Prepares an isolated database state."""
        self.pristine_db_state = copy.deepcopy(GlobalDBSource)
        self.db_for_test = copy.deepcopy(self.pristine_db_state)

        # Setup a predictable DB state for tests
        self.ws_root = "/test_ws_propose_cmd_live"
        self.db_for_test["workspace_root"] = self.ws_root
        self.db_for_test["cwd"] = os.path.join(self.ws_root, "project_a")
        self.db_for_test["file_system"] = {
             self.ws_root: {"path": self.ws_root, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "T_SETUP"},
             self.db_for_test["cwd"]: {"path": self.db_for_test["cwd"], "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "T_SETUP"}
        }

        self.utils_db_patcher = patch('cursor.SimulationEngine.utils.DB', self.db_for_test)
        self.utils_db_patcher.start()

    def tearDown(self):
        """Restores original state."""
        self.utils_db_patcher.stop()

    def test_propose_simple_command_live(self):
        """Integration test: Propose a simple listing command."""
        user_objective = "List all files and directories here, including hidden ones."
        result = utils.propose_command(user_objective)

        print(f"\n[LIVE TEST - Simple Cmd] Objective: {user_objective}")
        print(f"Result: {result}")

        self.assertIsInstance(result, dict)
        self.assertIn("command", result)
        self.assertIsInstance(result["command"], str)
        self.assertTrue(len(result["command"]) > 1, "Command string seems too short.")
        self.assertIn("ls", result["command"]) # Check for core command
        self.assertIn("a", result["command"])  # Check for flag for hidden files
        self.assertIn("explanation", result)
        self.assertIsInstance(result["explanation"], str)
        self.assertIn("is_background", result)
        self.assertIsInstance(result["is_background"], bool)
        # Simple commands are unlikely to be background
        self.assertFalse(result["is_background"], "Simple ls should not be background.")

    def test_propose_interactive_command_live(self):
        """Integration test: Propose a command that typically needs piping."""
        user_objective = "Show the difference between the current branch and 'main' branch using git."
        result = utils.propose_command(user_objective)

        print(f"\n[LIVE TEST - Interactive Cmd] Objective: {user_objective}")
        print(f"Result: {result}")

        self.assertIsInstance(result, dict)
        self.assertIn("command", result)
        self.assertIsInstance(result["command"], str)
        self.assertIn("git diff", result["command"])
        self.assertIn("| cat", result["command"], "Expected '| cat' for git diff.")
        self.assertIn("explanation", result)
        self.assertIsInstance(result["explanation"], str)
        self.assertIn("is_background", result)
        self.assertIsInstance(result["is_background"], bool)
        self.assertFalse(result["is_background"], "Git diff should not be background.")

    def test_propose_background_command_live(self):
        """Integration test: Propose a command likely run in the background."""
        user_objective = "Run a simple python web server on port 8000."
        result = utils.propose_command(user_objective)

        print(f"\n[LIVE TEST - Background Cmd] Objective: {user_objective}")
        print(f"Result: {result}")

        self.assertIsInstance(result, dict)
        self.assertIn("command", result)
        self.assertIsInstance(result["command"], str)
        # Check for common patterns, LLM might choose different modules
        self.assertTrue("python" in result["command"] and ("http.server" in result["command"] or "SimpleHTTPServer" in result["command"]))
        self.assertIn("8000", result["command"])
        self.assertIn("explanation", result)
        self.assertIsInstance(result["explanation"], str)
        self.assertIn("is_background", result)
        self.assertIsInstance(result["is_background"], bool)
        # This type of command should be recommended for background
        self.assertTrue(result["is_background"], "HTTP server should likely be background.")

class TestGetMemories(BaseTestCaseWithErrorHandler):
    """Unit tests for the get_memories utility function."""

    def setUp(self):
        """Prepare isolated DB state for each test."""
        self.pristine_db_state = copy.deepcopy(GlobalDBSource)
        self.db_for_test = copy.deepcopy(self.pristine_db_state)
        self.db_for_test["knowledge_base"] = {}
        self.utils_db_patcher = patch('cursor.SimulationEngine.utils.DB', self.db_for_test)
        self.utils_db_patcher.start()

    def tearDown(self):
        """Restore DB state after each test."""
        self.utils_db_patcher.stop()

    def test_get_memories_empty(self):
        """Test get_memories returns empty dict when no knowledge is stored."""
        self.db_for_test["knowledge_base"] = {}
        memories = utils.get_memories()
        self.assertIsInstance(memories, dict)
        self.assertEqual(memories, {})

    def test_get_memories_with_entries(self):
        """Test get_memories returns all stored knowledge entries correctly."""
        test_kb = {
            "k_001": {"title": "How to list files", "knowledge_to_store": "Use `ls -a` to list all files."},
            "k_002": {"title": "How to check Python version", "knowledge_to_store": "Run `python --version`."}
        }
        self.db_for_test["knowledge_base"] = copy.deepcopy(test_kb)
        memories = utils.get_memories()
        self.assertIsInstance(memories, dict)
        self.assertEqual(memories, test_kb)
        # Check structure
        for k, v in memories.items():
            self.assertIn("title", v)
            self.assertIn("knowledge_to_store", v)
            self.assertIsInstance(v["title"], str)
            self.assertIsInstance(v["knowledge_to_store"], str)



if __name__ == '__main__':
    unittest.main()