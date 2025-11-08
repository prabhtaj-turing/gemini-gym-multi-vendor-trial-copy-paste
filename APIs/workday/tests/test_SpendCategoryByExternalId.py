import unittest
import workday
from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.SimulationEngine.custom_errors import ValidationError, NotFoundError, ConflictError

class TestSpendCategoryByExternalIdAPI(BaseTestCaseWithErrorHandler):
    """
    Test suite for the Spend Category by External ID API, focusing on the patch function.
    """

    def setUp(self):
        """Set up a clean database state before each test."""
        # Set a known state for the database before each test
        workday.SimulationEngine.db.DB['spend_categories'] = {
            "1": {
                "id": "1",
                "name": "Office Supplies",
                "external_id": "EXT-OFFICE-001",
                "usages": ["procurement", "expense"]
            },
            "2": {
                "id": "2",
                "name": "Software Licenses",
                "external_id": "EXT-SOFTWARE-002",
                "usages": ["procurement"]
            }
        }
        # In a real scenario, you would set the error mode, e.g.,
        # workday.SimulationEngine.error_handling.set_package_error_mode("RAISE")

    def test_patch_success_update_all_fields(self):
        """Test a successful update of all fields for an existing spend category."""
        response = workday.SpendCategoryByExternalId.patch(
            external_id="EXT-OFFICE-001",
            name="Corporate Office Supplies",
            new_external_id="EXT-OFFICE-NEW-001",
            usages=["procurement", "ad_hoc_payment"]
        )

        # 1. Verify the response structure and content
        self.assertIsNotNone(response)
        self.assertIn("data", response)
        data = response["data"]
        self.assertEqual(data["type"], "spend_categories")
        self.assertEqual(data["id"], "1")

        attributes = data["attributes"]
        self.assertEqual(attributes["name"], "Corporate Office Supplies")
        self.assertEqual(attributes["external_id"], "EXT-OFFICE-NEW-001")
        self.assertCountEqual(attributes["usages"], ["procurement", "ad_hoc_payment"])

        # 2. Verify the data was actually updated in the database
        db_category = workday.SimulationEngine.db.DB['spend_categories']["1"]
        self.assertEqual(db_category["name"], "Corporate Office Supplies")
        self.assertEqual(db_category["external_id"], "EXT-OFFICE-NEW-001")
        self.assertCountEqual(db_category["usages"], ["procurement", "ad_hoc_payment"])

    def test_patch_success_update_single_field(self):
        """Test a successful update of only a single field."""
        response = workday.SpendCategoryByExternalId.patch(
            external_id="EXT-SOFTWARE-002",
            name="Enterprise Software"
        )

        # Verify response
        self.assertEqual(response["data"]["attributes"]["name"], "Enterprise Software")
        # Verify other fields remain unchanged
        self.assertEqual(response["data"]["attributes"]["external_id"], "EXT-SOFTWARE-002")

        # Verify database state
        db_category = workday.SimulationEngine.db.DB['spend_categories']["2"]
        self.assertEqual(db_category["name"], "Enterprise Software")
        self.assertEqual(db_category["external_id"], "EXT-SOFTWARE-002")


    def test_patch_not_found(self):
        """Test failure when the external_id does not exist."""
        self.assert_error_behavior(
            workday.SpendCategoryByExternalId.patch,
            NotFoundError,
            "Spend category with external_id 'NON-EXISTENT-ID' not found.",
            None,
            external_id="NON-EXISTENT-ID",
            name="New Name"
        )

    def test_patch_conflict_error(self):
        """Test failure when new_external_id is already in use by another category."""
        self.assert_error_behavior(
            workday.SpendCategoryByExternalId.patch,
            ConflictError,
            "Conflict: External ID 'EXT-SOFTWARE-002' is already in use.",
            None,
            external_id="EXT-OFFICE-001",
            new_external_id="EXT-SOFTWARE-002" # This ID belongs to category "2"
        )

    def test_patch_validation_no_payload(self):
        """Test failure when no update parameters are provided."""
        self.assert_error_behavior(
            workday.SpendCategoryByExternalId.patch,
            ValidationError,
            "At least one field to update must be provided.",
            None,
            external_id="EXT-OFFICE-001"
        )

    def test_patch_validation_name_too_long(self):
        """Test failure when the provided name exceeds 255 characters."""
        long_name = "a" * 256
        with self.assertRaises(ValidationError) as context:
            workday.SpendCategoryByExternalId.patch(
                external_id="EXT-OFFICE-001",
                name=long_name
            )
        self.assertIn("Input validation failed", str(context.exception))
        self.assertIn("String should have at most 255 characters", str(context.exception))


    def test_patch_validation_name_empty(self):
        """Test failure when the provided name is an empty string."""
        with self.assertRaises(ValidationError) as context:
            workday.SpendCategoryByExternalId.patch(
                external_id="EXT-OFFICE-001",
                name=""
            )
        self.assertIn("Input validation failed", str(context.exception))
        self.assertIn("String should have at least 1 character", str(context.exception))


    def test_patch_validation_new_external_id_too_long(self):
        """Test failure when the new_external_id exceeds 255 characters."""
        long_id = "a" * 256
        with self.assertRaises(ValidationError) as context:
            workday.SpendCategoryByExternalId.patch(
                external_id="EXT-OFFICE-001",
                new_external_id=long_id
            )
        self.assertIn("Input validation failed", str(context.exception))
        self.assertIn("String should have at most 255 characters", str(context.exception))


    def test_patch_validation_invalid_usage_value(self):
        """Test failure when usages list contains an invalid value."""
        with self.assertRaises(ValidationError) as context:
            workday.SpendCategoryByExternalId.patch(
                external_id="EXT-OFFICE-001",
                usages=["procurement", "invalid_usage"]
            )
        self.assertIn("Input validation failed", str(context.exception))
        self.assertIn("Input should be 'procurement', 'expense', 'ad_hoc_payment' or 'supplier_invoice'", str(context.exception))


    def test_patch_validation_usages_empty_list(self):
        """Test failure when usages is an empty list."""
        with self.assertRaises(ValidationError) as context:
            workday.SpendCategoryByExternalId.patch(
                external_id="EXT-OFFICE-001",
                usages=[]
            )
        self.assertIn("Input validation failed", str(context.exception))
        self.assertIn("List should have at least 1 item", str(context.exception))


if __name__ == '__main__':
    # This allows the test to be run from the command line
    unittest.main()