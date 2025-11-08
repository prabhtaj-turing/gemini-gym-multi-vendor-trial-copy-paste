import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from call_llm.SimulationEngine.models import (
    ParameterSchema,
    ParametersDefinition,
    Tool,
    ToolContainer
)
from pydantic import ValidationError

class TestModels(BaseTestCaseWithErrorHandler):
    """Test cases for Pydantic models in the SimulationEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_parameter_schema = {
            "type": "string",
            "description": "A test parameter"
        }
        
        self.valid_parameters_definition = {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "The username"
                },
                "email": {
                    "type": "string", 
                    "description": "The email address"
                }
            },
            "required": ["username", "email"]
        }
        
        self.valid_tool = {
            "name": "create_user",
            "description": "Creates a new user account",
            "parameters": self.valid_parameters_definition
        }
        
        self.valid_tool_container = {
            "tool": [self.valid_tool]
        }

    def test_parameter_schema_valid(self):
        """Test creating a valid ParameterSchema."""
        schema = ParameterSchema(**self.valid_parameter_schema)
        
        self.assertEqual(schema.type, "string")
        self.assertEqual(schema.description, "A test parameter")

    def test_parameter_schema_missing_fields(self):
        """Test ParameterSchema validation with missing required fields."""
        with self.assertRaises(ValidationError):
            ParameterSchema(type="string")  # Missing description
            
        with self.assertRaises(ValidationError):
            ParameterSchema(description="A test")  # Missing type

    def test_parameter_schema_invalid_type(self):
        """Test ParameterSchema with invalid type."""
        # Pydantic doesn't validate enum values for str fields by default
        # So this should actually work
        schema = ParameterSchema(type="invalid_type", description="A test")
        self.assertEqual(schema.type, "invalid_type")

    def test_parameters_definition_valid(self):
        """Test creating a valid ParametersDefinition."""
        params_def = ParametersDefinition(**self.valid_parameters_definition)
        
        self.assertEqual(params_def.type, "object")
        self.assertIn("username", params_def.properties)
        self.assertIn("email", params_def.properties)
        self.assertEqual(params_def.required, ["username", "email"])

    def test_parameters_definition_default_type(self):
        """Test ParametersDefinition uses default type when not specified."""
        params_data = {
            "properties": {
                "test": {
                    "type": "string",
                    "description": "A test parameter"
                }
            }
        }
        
        params_def = ParametersDefinition(**params_data)
        self.assertEqual(params_def.type, "OBJECT")  # Default value

    def test_parameters_definition_no_required(self):
        """Test ParametersDefinition without required parameters."""
        params_data = {
            "properties": {
                "optional_param": {
                    "type": "string",
                    "description": "An optional parameter"
                }
            }
        }
        
        params_def = ParametersDefinition(**params_data)
        self.assertIsNone(params_def.required)

    def test_parameters_definition_empty_properties(self):
        """Test ParametersDefinition with empty properties."""
        params_data = {
            "properties": {}
        }
        
        params_def = ParametersDefinition(**params_data)
        self.assertEqual(len(params_def.properties), 0)

    def test_tool_valid(self):
        """Test creating a valid Tool."""
        tool = Tool(**self.valid_tool)
        
        self.assertEqual(tool.name, "create_user")
        self.assertEqual(tool.description, "Creates a new user account")
        self.assertIsInstance(tool.parameters, ParametersDefinition)

    def test_tool_missing_fields(self):
        """Test Tool validation with missing required fields."""
        with self.assertRaises(ValidationError):
            Tool(name="test")  # Missing description and parameters
            
        with self.assertRaises(ValidationError):
            Tool(description="test")  # Missing name and parameters

    def test_tool_empty_name(self):
        """Test Tool with empty name."""
        # Pydantic doesn't validate empty strings by default
        # So this should actually work
        tool = Tool(
            name="",
            description="A test tool",
            parameters=self.valid_parameters_definition
        )
        self.assertEqual(tool.name, "")

    def test_tool_empty_description(self):
        """Test Tool with empty description."""
        # Pydantic doesn't validate empty strings by default
        # So this should actually work
        tool = Tool(
            name="test_tool",
            description="",
            parameters=self.valid_parameters_definition
        )
        self.assertEqual(tool.description, "")

    def test_tool_container_valid(self):
        """Test creating a valid ToolContainer."""
        container = ToolContainer(**self.valid_tool_container)
        
        self.assertEqual(len(container.tool), 1)
        self.assertEqual(container.tool[0].name, "create_user")

    def test_tool_container_empty_tool_list(self):
        """Test ToolContainer with empty tool list."""
        with self.assertRaises(ValidationError):
            ToolContainer(tool=[])

    def test_tool_container_multiple_tools(self):
        """Test ToolContainer with multiple tools."""
        # This should fail because ToolContainer has max_items=1
        multiple_tools = {
            "tool": [
                self.valid_tool,
                {
                    "name": "delete_user",
                    "description": "Deletes a user account",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The user ID to delete"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            ]
        }
        
        with self.assertRaises(ValidationError):
            ToolContainer(**multiple_tools)

    def test_tool_container_too_many_tools(self):
        """Test ToolContainer with more than one tool (should fail)."""
        multiple_tools = {
            "tool": [
                self.valid_tool,
                {
                    "name": "delete_user",
                    "description": "Deletes a user account",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
        
        # Should fail because max_items=1
        with self.assertRaises(ValidationError):
            ToolContainer(**multiple_tools)

    def test_model_serialization(self):
        """Test that models can be serialized to dictionaries."""
        # Test ParameterSchema serialization
        schema = ParameterSchema(**self.valid_parameter_schema)
        schema_dict = schema.model_dump()
        self.assertEqual(schema_dict["type"], "string")
        self.assertEqual(schema_dict["description"], "A test parameter")
        
        # Test Tool serialization
        tool = Tool(**self.valid_tool)
        tool_dict = tool.model_dump()
        self.assertEqual(tool_dict["name"], "create_user")
        self.assertEqual(tool_dict["description"], "Creates a new user account")
        
        # Test ToolContainer serialization
        container = ToolContainer(**self.valid_tool_container)
        container_dict = container.model_dump()
        self.assertIn("tool", container_dict)
        self.assertEqual(len(container_dict["tool"]), 1)

    def test_model_validation_with_complex_types(self):
        """Test model validation with complex parameter types."""
        complex_params = {
            "type": "object",
            "properties": {
                "string_param": {
                    "type": "string",
                    "description": "A string parameter"
                },
                "number_param": {
                    "type": "number",
                    "description": "A number parameter"
                },
                "boolean_param": {
                    "type": "boolean",
                    "description": "A boolean parameter"
                },
                "array_param": {
                    "type": "array",
                    "description": "An array parameter"
                },
                "object_param": {
                    "type": "object",
                    "description": "An object parameter"
                }
            },
            "required": ["string_param", "number_param"]
        }
        
        params_def = ParametersDefinition(**complex_params)
        self.assertEqual(len(params_def.properties), 5)
        self.assertEqual(params_def.required, ["string_param", "number_param"])

    def test_model_field_descriptions(self):
        """Test that model fields have proper descriptions."""
        # Check that ParameterSchema fields have descriptions
        schema_fields = ParameterSchema.model_fields
        self.assertIn("data type", schema_fields["type"].description)
        self.assertIn("description", schema_fields["description"].description)
        
        # Check that ParametersDefinition fields have descriptions
        params_fields = ParametersDefinition.model_fields
        self.assertIn("type", params_fields["type"].description)
        self.assertIn("parameter names", params_fields["properties"].description)
        self.assertIn("required", params_fields["required"].description)
        
        # Check that Tool fields have descriptions
        tool_fields = Tool.model_fields
        self.assertIn("parameters", tool_fields["parameters"].description)
        
        # Check that ToolContainer fields have descriptions
        container_fields = ToolContainer.model_fields
        self.assertIn("function declaration", container_fields["tool"].description)

if __name__ == '__main__':
    unittest.main()
