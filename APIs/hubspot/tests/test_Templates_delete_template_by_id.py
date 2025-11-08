import unittest
from unittest.mock import patch
from hubspot.Templates import delete_template_by_id
from hubspot.SimulationEngine.db import DB
import time
from hubspot.SimulationEngine.custom_errors import (
    InvalidTemplateIdTypeError,
    EmptyTemplateIdError,
    TemplateNotFoundError,
    InvalidTimestampError,
)
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestDeleteTemplateById(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Set up a mock database before each test
        DB.clear()
        DB["templates"] = {
            "123": {
                "id": "123",
                "source": "<html>Test</html>",
                "deleted_at": None,
            },
            "456": {
                "id": "456",
                "source": "<html>Another Test</html>",
                "deleted_at": None,
            },
        }

    def test_delete_template_successfully(self):
        """
        Test that a template is successfully marked as deleted.
        """
        template_id = "123"
        
        with patch('time.time', return_value=1678886400):
            delete_template_by_id(template_id)

        self.assertIsNotNone(DB["templates"][template_id]["deleted_at"])
        self.assertEqual(DB["templates"][template_id]["deleted_at"], "1678886400000")

    def test_delete_template_with_valid_deleted_at(self):
        """
        Test that a template is successfully deleted with a specific timestamp.
        """
        template_id = "456"
        deleted_at_timestamp = "1678886401000"
        delete_template_by_id(template_id, deleted_at=deleted_at_timestamp)

        self.assertEqual(DB["templates"][template_id]["deleted_at"], deleted_at_timestamp)

    def test_delete_template_invalid_id_type(self):
        """
        Test that a TypeError is raised for an invalid template_id type.
        """
        self.assert_error_behavior(
            func_to_call=delete_template_by_id,
            expected_exception_type=InvalidTemplateIdTypeError,
            expected_message="template_id must be a string.",
            template_id=12345
        )

    def test_delete_template_empty_id(self):
        """
        Test that an error is raised for an empty template_id.
        """
        self.assert_error_behavior(
            func_to_call=delete_template_by_id,
            expected_exception_type=EmptyTemplateIdError,
            expected_message="template_id cannot be an empty string.",
            template_id="  "
        )

    def test_delete_template_not_found(self):
        """
        Test that an error is raised for a non-existent template_id.
        """
        self.assert_error_behavior(
            func_to_call=delete_template_by_id,
            expected_exception_type=TemplateNotFoundError,
            expected_message="Template with id 999 not found.",
            template_id="999"
        )

    def test_delete_template_with_invalid_deleted_at(self):
        """
        Test that an error is raised for an invalid 'deleted_at' timestamp.
        """
        self.assert_error_behavior(
            func_to_call=delete_template_by_id,
            expected_exception_type=InvalidTimestampError,
            expected_message="The 'deleted_at' timestamp must be a string of milliseconds since the epoch.",
            template_id="123",
            deleted_at="not-a-timestamp"
        )

if __name__ == "__main__":
    unittest.main() 