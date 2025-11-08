"""
Test suite for execution functionalities in the Blender API simulation.
"""
import unittest
import copy
import uuid
from datetime import datetime, timezone
import re # For checking ISO timestamp format

from pydantic import ValidationError as PydanticValidationError # Alias to avoid name clash

from common_utils.base_case import BaseTestCaseWithErrorHandler
from blender.execution import execute_blender_code
from blender.SimulationEngine import custom_errors 
from blender.SimulationEngine.db import DB
from blender.SimulationEngine.models import BlenderCodeExecutionOutcomeModel 
from .. import object as object_module # Import for monkeypatching
from .. import scene as scene_module # Import for monkeypatching utility

# Initial DB state for execute_blender_code function tests
EXECUTE_BLENDER_CODE_INITIAL_DB_STATE = {
    "execution_logs": [],
    "current_scene": { # Minimal scene for bpy.context.scene.name tests
        "name": "TestScene"
    },
    "polyhaven_assets_db": {}, # Add other necessary minimal structures if tests require
    "materials": {}
}


class TestExecuteBlenderCode(BaseTestCaseWithErrorHandler):
    """
    Test suite for the execute_blender_code function.
    """

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(EXECUTE_BLENDER_CODE_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Reset DB to initial state before each test."""
        DB.clear()
        DB.update(copy.deepcopy(EXECUTE_BLENDER_CODE_INITIAL_DB_STATE))

    def _validate_log_entry(self, log_entry_dict, expected_code, expected_status_str, expect_output_contains=None, expect_error_contains=None, expected_return_str=None):

        try:

            parsed_log_entry = BlenderCodeExecutionOutcomeModel(**log_entry_dict)
        except PydanticValidationError as e:
            self.fail(f"Log entry dictionary does not match BlenderCodeExecutionOutcomeModel schema:\n{e}\nLog entry: {log_entry_dict}")

        # 2. Validate specific field values from the parsed model or original dict
        # Using parsed_log_entry attributes for checks now where appropriate.
        self.assertIsInstance(parsed_log_entry.id, uuid.UUID)
        self.assertTrue(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})", parsed_log_entry.timestamp),
                        f"Timestamp {parsed_log_entry.timestamp} is not in valid ISO format.")

        self.assertEqual(parsed_log_entry.code_executed, expected_code)
        # The model stores status as an enum, so compare its string value
        self.assertEqual(str(parsed_log_entry.status.value), expected_status_str) 

        if expect_output_contains:
            self.assertIn(expect_output_contains, parsed_log_entry.output or "")
        elif expected_status_str == "success" and not expected_return_str and not parsed_log_entry.output:
            pass # ok if no specific output and it's None/empty

        if expect_error_contains:
            self.assertIn(expect_error_contains, parsed_log_entry.error_message or "")
        else:
            if expected_status_str == "success":
                 self.assertIsNone(parsed_log_entry.error_message)


        if expected_return_str:
            self.assertEqual(parsed_log_entry.return_value_str, expected_return_str)
        else:

            self.assertTrue(parsed_log_entry.return_value_str is None or parsed_log_entry.return_value_str == 'None')


    def test_simple_print_statement(self):
        code = 'print("Hello Blender")'
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success')
        self.assertIn("Hello Blender", result['output'])
        self.assertIsNone(result.get('error_message'))
        self.assertIsNone(result.get('return_value'))

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "success", expect_output_contains="Hello Blender")

    def test_expression_evaluation(self):
        code = '5 + 10'
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['return_value'], 15)
        self.assertTrue(result['output'] is None or result['output'] == "") # No print

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "success", expected_return_str="15")

    def test_multiline_code_execution(self):
        code = '''
a = 10
b = 20
c = a + b
print(f"Sum: {c}")
c
'''
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success')
        self.assertIn("Sum: 30", result['output'])
        self.assertEqual(result['return_value'], 30)

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "success", expect_output_contains="Sum: 30", expected_return_str="30")

    def test_blender_context_access(self):
        # Relies on EXECUTE_BLENDER_CODE_INITIAL_DB_STATE providing current_scene.name
        code = '''
import bpy
name = bpy.context.scene.name
print(f"Scene: {name}")
name
'''
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'error')
        self.assertIsNotNone(result['error_message'])
        self.assertTrue("ModuleNotFoundError" in result['error_message'] or "ImportError" in result['error_message'])
        self.assertIsNone(result.get('return_value'))

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        # Check for either error type in the log as well
        error_in_log = "ModuleNotFoundError" in logs[0].get("error_message", "") or \
                       "ImportError" in logs[0].get("error_message", "")
        self.assertTrue(error_in_log, "Expected ModuleNotFoundError or ImportError in log error message")
        self._validate_log_entry(logs[0], code, "error", expect_error_contains=logs[0].get("error_message").split(':')[0], expected_return_str=None)


    def test_mathutils_usage(self):
        # This test previously assumed mathutils.Vector was mocked.
        # Now, it should fail with an ImportError/ModuleNotFoundError.
        code = '''
from mathutils import Vector
v = Vector((1.0, 2.0, 3.0))
print(str(v))
v_tuple = (v.x, v.y, v.z)
v_tuple
'''
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'error')
        self.assertIsNotNone(result['error_message'])
        self.assertTrue("ModuleNotFoundError" in result['error_message'] or "ImportError" in result['error_message'])
        self.assertIsNone(result.get('return_value'))

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        error_in_log = "ModuleNotFoundError" in logs[0].get("error_message", "") or \
                       "ImportError" in logs[0].get("error_message", "")
        self.assertTrue(error_in_log, "Expected ModuleNotFoundError or ImportError in log error message")
        self._validate_log_entry(logs[0], code, "error", expect_error_contains=logs[0].get("error_message").split(':')[0], expected_return_str=None)


    def test_syntax_error_handling(self):
        code = 'a = 1 +'
        # According to docstring, malformed code raises InvalidInputError
        # This error should be caught by the error handler decorator.
        self.assert_error_behavior(
            execute_blender_code,
            custom_errors.InvalidInputError,
            "Provided code has syntax errors: invalid syntax on line 1", # More specific based on implementation
            code=code  # Pass 'code' directly as a keyword argument
        )
        # Check if logs are still made for pre-execution failures (depends on implementation)
        # Generally, if execute_blender_code raises before full execution, it might not log.
        # If it's caught and returned as a dict by execute_blender_code itself, it should log.
        # The docstring implies an exception is raised, so logging is unlikely here.
        # Let's assume no log for compile-time InvalidInputError from decorator.
        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 0, "Syntax errors caught before execution ideally shouldn't create an execution log entry unless handled internally then logged.")


    def test_runtime_error_handling(self):
        code = '''
print("About to divide by zero")
x = 1 / 0
print("This will not be printed")
'''
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'error')
        self.assertIn("About to divide by zero", result['output'])
        self.assertIn("ZeroDivisionError", result['error_message'])
        self.assertIsNone(result.get('return_value'))

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "error", expect_output_contains="About to divide by zero", expect_error_contains="ZeroDivisionError")


    def test_empty_code_string(self):
        code = ''
        self.assert_error_behavior(
            execute_blender_code,
            custom_errors.InvalidInputError,
            "Code string cannot be empty.",
            code=code  # Pass 'code' directly as a keyword argument
        )
        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 0, "Empty code string error ideally shouldn't create an execution log.")

    def test_access_simulation_db_read_and_write(self):
        # Setup initial state in DB for this test
        DB["test_key"] = 100
        DB["another_key"] = {"nested": "value"}

        code = '''
val = DB.get("test_key") # Use DB directly
DB["test_key"] = val + 1
# Test creating a new key
DB["new_key_from_script"] = "created"
# Test modifying nested
DB["another_key"]["nested"] = "changed"
print(f"Old value: {val}, New value: {DB['test_key']}")
DB["test_key"] # return new value
'''
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['return_value'], 101)
        self.assertIn("Old value: 100, New value: 101", result['output'])

        # Verify changes in the actual DB
        self.assertEqual(DB["test_key"], 101)
        self.assertEqual(DB["new_key_from_script"], "created")
        self.assertEqual(DB["another_key"]["nested"], "changed")

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "success", expect_output_contains="New value: 101", expected_return_str="101")

    def test_successful_execution_logging_no_return_no_output(self):
        code = 'a = 1' # No output, no explicit return from script
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['output'] is None or result['output'] == "") # No print
        self.assertIsNone(result.get('return_value')) # Assignment itself doesn't make it a Python return

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        # The last expression 'a=1' does not result in a return_value from eval(), so it's None.
        # The log should store actual None for return_value_str in this case.
        self._validate_log_entry(logs[0], code, "success", expected_return_str=None)


    def test_complex_data_type_return_logging(self):
        code = '''
my_dict = {"a": 1, "b": [1,2,3]}
my_list = [True, None, "string"]
(my_dict, my_list) # Return a tuple of complex types
'''
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success')
        expected_return = ({"a": 1, "b": [1,2,3]}, [True, None, "string"])
        self.assertEqual(result['return_value'], expected_return)

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "success", expected_return_str=str(expected_return))

    def test_invalid_code_argument_type(self):
        """Test passing a non-string type as the code argument"""
        invalid_code_inputs = [
            (123, "int"),
            (None, "NoneType"),
            (['print("hello")'], "list"),
            ({"code": 'print("hi")'}, "dict")
        ]
        for invalid_input, type_name in invalid_code_inputs:
            with self.subTest(input=invalid_input):
                with self.assertRaises(custom_errors.ValidationError) as cm:
                    execute_blender_code(invalid_input)
                self.assertEqual(
                    str(cm.exception),
                    f"Input 'code' must be a string, got {type_name}"
                )
        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 0, "Invalid argument type errors should not create execution logs.")

    def test_code_with_null_byte_compile_error(self):
        """Test code containing a null byte, which raises ValueError, wrapped as InvalidInputError.
        """
        code_with_null_byte = 'print("hello\0world")'
        expected_msg = "Provided code has syntax errors: source code string cannot contain null bytes"

        with self.assertRaises(custom_errors.InvalidInputError) as cm:
            execute_blender_code(code_with_null_byte)
        self.assertEqual(str(cm.exception), expected_msg)

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 0, "Compile-time ValueError (like null byte) should not create execution logs.")

    def test_execution_of_pass_statement(self):
        """Test execution of a simple 'pass' statement (to ensure line 106 coverage)."""
        code = 'pass'
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['output'] is None or result['output'] == "")
        self.assertIsNone(result.get('return_value'))

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "success", expected_return_str=None)

    def test_execution_of_comment_only_code(self):
        """Test execution of code that only contains comments (targets line 106)."""
        code = '''
# This is a comment
# So is this
'''
        result = execute_blender_code(code)
        self.assertEqual(result['status'], 'success', "Comment-only code should execute successfully.")
        self.assertTrue(result['output'] is None or result['output'] == "", "Comment-only code should produce no output.")
        self.assertIsNone(result.get('return_value'), "Comment-only code should have no return value.")

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1, "Comment-only code execution should be logged.")
        self._validate_log_entry(logs[0], code, "success", expected_return_str=None)

    def test_execution_with_dynamically_imported_function(self):
        """Test that functions from API modules (e.g., object.add_numbers) are available,
           where the function is dynamically added to the module for this test.
        """
        # Define the function to be injected
        def add_numbers_for_test(a: float, b: float) -> float:
            return a + b

        # Temporarily add the function to the object_module
        original_add_numbers = getattr(object_module, 'add_numbers', None)
        object_module.add_numbers = add_numbers_for_test

        # Ensure the function is removed after the test
        def cleanup_add_numbers():
            if original_add_numbers is not None:
                object_module.add_numbers = original_add_numbers
            else:
                del object_module.add_numbers
        self.addCleanup(cleanup_add_numbers)
        
        # The add_numbers function is expected to be injected into the global scope
        # by execute_blender_code because it now exists in object_module.
        code = 'add_numbers(10, 5)' 
        result = execute_blender_code(code)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['return_value'], 15)
        self.assertTrue(result['output'] is None or result['output'] == "")

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code, "success", expected_return_str="15")

    def test_dynamic_function_modifying_db(self):
        """Test dynamically injected function calling another dynamic utility to modify DB."""
        db_key_to_set = "test_dynamic_db_key"
        db_value_to_set = "dynamic_value_set_via_exec"

        # 1. Define the utility function to modify DB (to be injected into scene_module)
        def util_set_db_val(key: str, value: str):
            # DB will be in the global scope of the executed util
            DB[key] = value # type: ignore[name-defined] # Use DB directly
            return f"Set {key} to {value}"

        # 2. Define the main function (to be injected into object_module)
        # This function will call the utility function.
        def main_action_on_object(k: str, v: str):
            # util_set_db_val will be in the global scope of this executed function
            return util_set_db_val(k, v) # type: ignore[name-defined]

        # 3. Monkeypatch: Temporarily add functions to respective modules
        original_util = getattr(scene_module, 'util_set_db_val', None)
        scene_module.util_set_db_val = util_set_db_val
        self.addCleanup(lambda: setattr(scene_module, 'util_set_db_val', original_util) if original_util else delattr(scene_module, 'util_set_db_val'))

        original_main_action = getattr(object_module, 'main_action_on_object', None)
        object_module.main_action_on_object = main_action_on_object
        self.addCleanup(lambda: setattr(object_module, 'main_action_on_object', original_main_action) if original_main_action else delattr(object_module, 'main_action_on_object'))

        # 4. Execute code that calls the main injected function
        code_to_execute = f'main_action_on_object("{db_key_to_set}", "{db_value_to_set}")'
        result = execute_blender_code(code_to_execute)

        # 5. Assertions
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['return_value'], f"Set {db_key_to_set} to {db_value_to_set}")
        
        # Crucially, check if the DB was actually modified
        self.assertIn(db_key_to_set, DB, "DB key should have been set.")
        self.assertEqual(DB[db_key_to_set], db_value_to_set, "DB value was not set correctly.")

        logs = DB.get("execution_logs", [])
        self.assertEqual(len(logs), 1)
        self._validate_log_entry(logs[0], code_to_execute, "success", expected_return_str=result['return_value'])


if __name__ == '__main__':
    unittest.main() 