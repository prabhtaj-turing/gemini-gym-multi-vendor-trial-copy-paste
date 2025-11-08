import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestImports(BaseTestCaseWithErrorHandler):
    """Test that all modules can be imported without errors."""

    def test_import_call_llm_package(self):
        """Test importing the main call_llm package."""
        try:
            import call_llm
            self.assertIsNotNone(call_llm)
        except ImportError as e:
            self.fail(f"Failed to import call_llm package: {e}")

    def test_import_llm_execution_module(self):
        """Test importing the llm_execution module."""
        try:
            from call_llm import llm_execution
            self.assertIsNotNone(llm_execution)
        except ImportError as e:
            self.fail(f"Failed to import llm_execution module: {e}")

    def test_import_simulation_engine(self):
        """Test importing the SimulationEngine package."""
        try:
            from call_llm import SimulationEngine
            self.assertIsNotNone(SimulationEngine)
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine package: {e}")

    def test_import_simulation_engine_modules(self):
        """Test importing individual SimulationEngine modules."""
        try:
            from call_llm.SimulationEngine import utils, models, custom_errors
            self.assertIsNotNone(utils)
            self.assertIsNotNone(models)
            self.assertIsNotNone(custom_errors)
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine modules: {e}")

    def test_import_public_functions(self):
        """Test that all public functions are available."""
        try:
            from call_llm import (
                make_tool_from_docstring,
                generate_llm_response,
                generate_llm_response_with_tools
            )
            self.assertIsNotNone(make_tool_from_docstring)
            self.assertIsNotNone(generate_llm_response)
            self.assertIsNotNone(generate_llm_response_with_tools)
        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")

    def test_import_custom_errors(self):
        """Test importing custom error classes."""
        try:
            from call_llm.SimulationEngine.custom_errors import ValidationError, LLMExecutionError
            self.assertIsNotNone(ValidationError)
            self.assertIsNotNone(LLMExecutionError)
        except ImportError as e:
            self.fail(f"Failed to import custom errors: {e}")

    def test_import_models(self):
        """Test importing Pydantic models."""
        try:
            from call_llm.SimulationEngine.models import (
                ParameterSchema,
                ParametersDefinition,
                Tool,
                ToolContainer
            )
            self.assertIsNotNone(ParameterSchema)
            self.assertIsNotNone(ParametersDefinition)
            self.assertIsNotNone(Tool)
            self.assertIsNotNone(ToolContainer)
        except ImportError as e:
            self.fail(f"Failed to import models: {e}")

    def test_import_utils_functions(self):
        """Test importing utility functions."""
        try:
            from call_llm.SimulationEngine.utils import (
                docstring_to_fcspec,
                map_type,
                is_optional_type_string
            )
            self.assertIsNotNone(docstring_to_fcspec)
            self.assertIsNotNone(map_type)
            self.assertIsNotNone(is_optional_type_string)
        except ImportError as e:
            self.fail(f"Failed to import utility functions: {e}")

    def test_package_all_attribute(self):
        """Test that __all__ attribute is properly defined."""
        try:
            import call_llm
            self.assertIsNotNone(call_llm.__all__)
            self.assertIsInstance(call_llm.__all__, list)
            expected_functions = [
                "make_tool_from_docstring",
                "generate_llm_response", 
                "generate_llm_response_with_tools"
            ]
            for func in expected_functions:
                self.assertIn(func, call_llm.__all__)
        except AttributeError as e:
            self.fail(f"Failed to access __all__ attribute: {e}")

    def test_package_dir_function(self):
        """Test that __dir__ function returns expected attributes."""
        try:
            import call_llm
            dir_result = call_llm.__dir__()
            self.assertIsInstance(dir_result, list)
            self.assertIsInstance(dir_result, list)
            
            # Check that all expected functions are in dir result
            expected_functions = [
                "make_tool_from_docstring",
                "generate_llm_response", 
                "generate_llm_response_with_tools"
            ]
            for func in expected_functions:
                self.assertIn(func, dir_result)
                
            # Check that the result is sorted
            self.assertEqual(dir_result, sorted(dir_result))
            
        except AttributeError as e:
            self.fail(f"Failed to access __dir__ function: {e}")

if __name__ == '__main__':
    unittest.main()
