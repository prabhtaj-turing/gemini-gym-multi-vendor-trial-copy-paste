import unittest
import inspect
from common_utils.base_case import BaseTestCaseWithErrorHandler
from call_llm import llm_execution
from call_llm.SimulationEngine import utils, models, custom_errors

class TestDocstrings(BaseTestCaseWithErrorHandler):
    """Test cases for validating docstrings in the call_llm module."""

    def test_make_tool_from_docstring_has_docstring(self):
        """Test that make_tool_from_docstring has a proper docstring."""
        docstring = llm_execution.make_tool_from_docstring.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)
        
        # Check for key sections
        self.assertIn("Args:", docstring)
        self.assertIn("Returns:", docstring)
        self.assertIn("Raises:", docstring)

    def test_generate_llm_response_has_docstring(self):
        """Test that generate_llm_response has a proper docstring."""
        docstring = llm_execution.generate_llm_response.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)
        
        # Check for key sections
        self.assertIn("Args:", docstring)
        self.assertIn("Returns:", docstring)
        self.assertIn("Raises:", docstring)

    def test_generate_llm_response_with_tools_has_docstring(self):
        """Test that generate_llm_response_with_tools has a proper docstring."""
        docstring = llm_execution.generate_llm_response_with_tools.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)
        
        # Check for key sections
        self.assertIn("Args:", docstring)
        self.assertIn("Returns:", docstring)
        self.assertIn("Raises:", docstring)

    def test_docstring_to_fcspec_has_docstring(self):
        """Test that docstring_to_fcspec has a proper docstring."""
        docstring = utils.docstring_to_fcspec.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_map_type_has_docstring(self):
        """Test that map_type has a proper docstring."""
        docstring = utils.map_type.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_is_optional_type_string_has_docstring(self):
        """Test that is_optional_type_string has a proper docstring."""
        docstring = utils.is_optional_type_string.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_validation_error_has_docstring(self):
        """Test that ValidationError has a proper docstring."""
        docstring = custom_errors.ValidationError.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_llm_execution_error_has_docstring(self):
        """Test that LLMExecutionError has a proper docstring."""
        docstring = custom_errors.LLMExecutionError.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_parameter_schema_has_docstring(self):
        """Test that ParameterSchema has a proper docstring."""
        docstring = models.ParameterSchema.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_parameters_definition_has_docstring(self):
        """Test that ParametersDefinition has a proper docstring."""
        docstring = models.ParametersDefinition.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_tool_has_docstring(self):
        """Test that Tool has a proper docstring."""
        docstring = models.Tool.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_tool_container_has_docstring(self):
        """Test that ToolContainer has a proper docstring."""
        docstring = models.ToolContainer.__doc__
        
        self.assertIsNotNone(docstring)
        self.assertIsInstance(docstring, str)
        self.assertGreater(len(docstring.strip()), 0)

    def test_docstring_quality_make_tool_from_docstring(self):
        """Test the quality of make_tool_from_docstring docstring."""
        docstring = llm_execution.make_tool_from_docstring.__doc__
        
        # Check for comprehensive description
        self.assertIn("Converts", docstring)
        self.assertIn("docstring", docstring)
        self.assertIn("Tool", docstring)
        
        # Check for parameter descriptions
        self.assertIn("docstring", docstring)
        self.assertIn("function_name", docstring)
        
        # Check for return value description
        self.assertIn("Dict", docstring)
        self.assertIn("JSON-serializable", docstring)

    def test_docstring_quality_generate_llm_response(self):
        """Test the quality of generate_llm_response docstring."""
        docstring = llm_execution.generate_llm_response.__doc__
        
        # Check for comprehensive description
        self.assertIn("Generates", docstring)
        self.assertIn("text response", docstring)
        self.assertIn("Google", docstring)
        
        # Check for parameter descriptions
        self.assertIn("prompt", docstring)
        self.assertIn("api_key", docstring)
        self.assertIn("files", docstring)
        self.assertIn("system_prompt", docstring)
        self.assertIn("model_name", docstring)
        
        # Check for return value description
        self.assertIn("str", docstring)
        self.assertIn("text response", docstring)

    def test_docstring_quality_generate_llm_response_with_tools(self):
        """Test the quality of generate_llm_response_with_tools docstring."""
        docstring = llm_execution.generate_llm_response_with_tools.__doc__
        
        # Check for comprehensive description
        self.assertIn("function calling", docstring)
        self.assertIn("capabilities", docstring)
        self.assertIn("Google", docstring)
        
        # Check for parameter descriptions
        self.assertIn("prompt", docstring)
        self.assertIn("api_key", docstring)
        self.assertIn("files", docstring)
        self.assertIn("model_name", docstring)
        self.assertIn("system_prompt", docstring)
        self.assertIn("tools", docstring)
        
        # Check for return value description
        self.assertIn("Dict", docstring)
        self.assertIn("function_call", docstring)
        self.assertIn("response_text", docstring)

    def test_docstring_parameter_descriptions(self):
        """Test that all function parameters have descriptions in docstrings."""
        functions_to_test = [
            llm_execution.make_tool_from_docstring,
            llm_execution.generate_llm_response,
            llm_execution.generate_llm_response_with_tools
        ]
        
        for func in functions_to_test:
            docstring = func.__doc__
            sig = inspect.signature(func)
            
            for param_name in sig.parameters:
                if param_name != 'self':  # Skip self parameter
                    self.assertIn(param_name, docstring, 
                                f"Parameter '{param_name}' missing from {func.__name__} docstring")

    def test_docstring_return_descriptions(self):
        """Test that all functions have return value descriptions."""
        functions_to_test = [
            llm_execution.make_tool_from_docstring,
            llm_execution.generate_llm_response,
            llm_execution.generate_llm_response_with_tools
        ]
        
        for func in functions_to_test:
            docstring = func.__doc__
            self.assertIn("Returns:", docstring, 
                         f"Missing 'Returns:' section in {func.__name__} docstring")

    def test_docstring_raises_descriptions(self):
        """Test that all functions have raises descriptions."""
        functions_to_test = [
            llm_execution.make_tool_from_docstring,
            llm_execution.generate_llm_response,
            llm_execution.generate_llm_response_with_tools
        ]
        
        for func in functions_to_test:
            docstring = func.__doc__
            self.assertIn("Raises:", docstring, 
                         f"Missing 'Raises:' section in {func.__name__} docstring")

    def test_model_field_descriptions(self):
        """Test that all Pydantic model fields have descriptions."""
        models_to_test = [
            models.ParameterSchema,
            models.ParametersDefinition,
            models.Tool,
            models.ToolContainer
        ]
        
        for model in models_to_test:
            for field_name, field in model.model_fields.items():
                # Some fields might not have descriptions, which is okay
                if field.description is not None:
                    self.assertGreater(len(field.description.strip()), 0,
                                     f"Field '{field_name}' in {model.__name__} has empty description")

    def test_error_class_descriptions(self):
        """Test that error classes have meaningful descriptions."""
        error_classes = [
            custom_errors.ValidationError,
            custom_errors.LLMExecutionError
        ]
        
        for error_class in error_classes:
            docstring = error_class.__doc__
            self.assertIsNotNone(docstring)
            self.assertGreater(len(docstring.strip()), 0)
            # Check that the description is meaningful (not just a generic exception description)
            self.assertNotIn("Exception", docstring)  # Should have specific description

if __name__ == '__main__':
    unittest.main()
