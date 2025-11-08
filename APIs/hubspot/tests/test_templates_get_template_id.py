import unittest
from hubspot.SimulationEngine.custom_errors import (
    InvalidTemplateIdTypeError,
    EmptyTemplateIdError,
    TemplateNotFoundError,
)
from hubspot.Templates import get_template_by_id
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGetTemplateById(BaseTestCaseWithErrorHandler):

    def test_invalid_template_id_type(self):
        """Test that InvalidTemplateIdTypeError is raised for non-string template_id."""
        self.assert_error_behavior(
            func_to_call=get_template_by_id,
            expected_exception_type=InvalidTemplateIdTypeError,
            expected_message="template_id must be a string.",
            template_id=12345  # Passing a non-string type
        )

    def test_empty_template_id(self):
        """Test that EmptyTemplateIdError is raised for empty or whitespace template_id."""
        self.assert_error_behavior(
            func_to_call=get_template_by_id,
            expected_exception_type=EmptyTemplateIdError,
            expected_message="template_id cannot be an empty string.",
            template_id="   "  # Passing a whitespace string
        )

    def test_template_not_found(self):
        """Test that TemplateNotFoundError is raised for non-existent template_id."""
        self.assert_error_behavior(
            func_to_call=get_template_by_id,
            expected_exception_type=TemplateNotFoundError,
            expected_message="Template with id non_existent_id not found.",
            template_id="non_existent_id"  # Passing a non-existent ID
        )


if __name__ == "__main__":
    unittest.main() 