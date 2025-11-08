import unittest
import os


from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, load_state, save_state, DEFAULT_DB_PATH
from ..SimulationEngine import utils
import json
from ..SimulationEngine.models import DesignTypeInputModel
from pydantic import ValidationError
class TestModels(BaseTestCaseWithErrorHandler):
    """Test the models of the canva DB."""

    def setUp(self):
        """Set up test environment."""
        
        self.valid_design_type = {
            "type": "preset",
            "name": "doc",
        }


    def test_valid_design_type(self):
        """Test that the design type is valid."""
        design_type = DesignTypeInputModel(**self.valid_design_type)
        self.assertEqual(design_type.type, "preset")
        self.assertEqual(design_type.name, "doc")

    def test_invalid_design_type(self):
        """Test that the design type is invalid."""
        invalid_design_type = {
            "type": "preset",
            "name": "invalid",
        }

        with self.assertRaises(ValidationError):
            DesignTypeInputModel(**invalid_design_type)
    
    def test_model_json_serialization(self):
        """Test that the model can be serialized to JSON."""
        design_type = DesignTypeInputModel(**self.valid_design_type)
        json_data = design_type.model_dump()
        self.assertEqual(json_data, self.valid_design_type)
    
    def test_empty_design_type(self):
        """Test that empty design type is valid."""
        empty_design_type = {}
        design_type = DesignTypeInputModel(**empty_design_type)
        self.assertIsNone(design_type.type)
        self.assertIsNone(design_type.name)
    
    def test_design_type_with_only_type(self):
        """Test design type with only type field."""
        design_type_data = {"type": "preset"}
        design_type = DesignTypeInputModel(**design_type_data)
        self.assertEqual(design_type.type, "preset")
        self.assertIsNone(design_type.name)
    
    def test_design_type_with_only_name(self):
        """Test design type with only name field."""
        design_type_data = {"name": "doc"}
        design_type = DesignTypeInputModel(**design_type_data)
        self.assertIsNone(design_type.type)
        self.assertEqual(design_type.name, "doc")
    
    def test_design_type_whiteboard(self):
        """Test design type with whiteboard preset."""
        design_type_data = {"type": "preset", "name": "whiteboard"}
        design_type = DesignTypeInputModel(**design_type_data)
        self.assertEqual(design_type.type, "preset")
        self.assertEqual(design_type.name, "whiteboard")
    
    def test_design_type_presentation(self):
        """Test design type with presentation preset."""
        design_type_data = {"type": "preset", "name": "presentation"}
        design_type = DesignTypeInputModel(**design_type_data)
        self.assertEqual(design_type.type, "preset")
        self.assertEqual(design_type.name, "presentation")
    
    def test_invalid_design_type_value(self):
        """Test that invalid type value raises ValidationError."""
        invalid_design_type = {"type": "custom", "name": "doc"}
        with self.assertRaises(ValidationError):
            DesignTypeInputModel(**invalid_design_type)
    
    def test_invalid_design_name(self):
        """Test that invalid name value raises ValidationError."""
        invalid_design_type = {"type": "preset", "name": "invalid_preset"}
        with self.assertRaises(ValidationError):
            DesignTypeInputModel(**invalid_design_type)
    
    def test_extra_fields_forbidden(self):
        """Test that extra fields are rejected."""
        invalid_design_type = {
            "type": "preset",
            "name": "doc",
            "extra_field": "should_fail"
        }
        with self.assertRaises(ValidationError):
            DesignTypeInputModel(**invalid_design_type)
    
    def test_model_immutability(self):
        """Test that model validates on assignment."""
        design_type = DesignTypeInputModel(**self.valid_design_type)
        self.assertEqual(design_type.type, "preset")
        self.assertEqual(design_type.name, "doc")
    
if __name__ == '__main__':
    unittest.main() 