import unittest
from hubspot.Templates import create_template
from hubspot.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from hubspot.SimulationEngine.custom_errors import (
    EmptyTemplatePathError,
    EmptyTemplateSourceError,
    InvalidCategoryIdError,
    InvalidIsAvailableForNewContentError,
    InvalidTemplateTypeError,
    InvalidTimestampError,
)

class TestCreateTemplate(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up for test cases."""
        super().setUp()
        if 'templates' in DB:
            DB['templates'].clear()

    def test_create_template_success(self):
        """Test successful creation of a template."""
        source = "<html><body><h1>Test Template</h1></body></html>"
        result = create_template(source=source)
        self.assertIn("id", result)
        self.assertEqual(result["source"], source)
        self.assertEqual(result["category_id"], 2)
        self.assertEqual(result["template_type"], 2)
        template_id = result["id"]
        self.assertIn(template_id, DB["templates"])
        self.assertEqual(DB["templates"][template_id]["source"], source)

    def test_create_template_empty_source(self):
        """Test error when source is empty."""
        self.assert_error_behavior(
            create_template,
            EmptyTemplateSourceError,
            "Template source cannot be empty.",
            None,
            source=""
        )

    def test_create_template_invalid_template_type(self):
        """Test error on invalid template_type."""
        self.assert_error_behavior(
            create_template,
            InvalidTemplateTypeError,
            "Invalid template_type: 99. Must be an integer from the valid set.",
            None,
            source="some source",
            template_type=99
        )

    def test_create_template_invalid_category_id(self):
        """Test error on invalid category_id."""
        self.assert_error_behavior(
            create_template,
            InvalidCategoryIdError,
            "Invalid category_id: 99. Must be an integer from the valid set.",
            None,
            source="some source",
            category_id=99
        )

    def test_create_template_empty_folder(self):
        """Test error when folder path is empty."""
        self.assert_error_behavior(
            create_template,
            EmptyTemplatePathError,
            "Folder path must be a string and cannot be empty.",
            None,
            source="some source",
            folder=""
        )

    def test_create_template_empty_path(self):
        """Test error when template path is empty."""
        self.assert_error_behavior(
            create_template,
            EmptyTemplatePathError,
            "Template path must be a string and cannot be empty.",
            None,
            source="some source",
            path=""
        )

    def test_create_template_invalid_created_timestamp(self):
        """Test error on invalid 'created' timestamp."""
        self.assert_error_behavior(
            create_template,
            InvalidTimestampError,
            "The 'created' timestamp must be a string of milliseconds since the epoch.",
            None,
            source="some source",
            created="not-a-timestamp"
        )

    def test_create_template_invalid_is_available_for_new_content(self):
        """Test error on invalid 'is_available_for_new_content' type."""
        self.assert_error_behavior(
            create_template,
            InvalidIsAvailableForNewContentError,
            "The 'is_available_for_new_content' parameter must be a boolean.",
            None,
            source="some source",
            is_available_for_new_content="not-a-boolean"
        )

if __name__ == '__main__':
    unittest.main() 