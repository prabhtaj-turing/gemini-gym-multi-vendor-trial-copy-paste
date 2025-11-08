import unittest
from unittest.mock import patch
from pydantic import ValidationError

from workday.SpendCategories import post
from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.SimulationEngine.custom_errors import ValidationError as CustomValidationError, DuplicateExternalIdError

# Mock database for testing
test_db = {
    "DB": {
        "spend_categories": {
            "SC001": {
                "id": "SC001",
                "name": "Office Supplies",
                "external_id": "EXT001",
                "usages": ["procurement", "expense"]
            },
            "SC002": {
                "id": "SC002", 
                "name": "IT Equipment",
                "external_id": "EXT002",
                "usages": ["procurement"]
            },
            "SC003": {
                "id": "SC003",
                "name": "Marketing",
                "external_id": None,
                "usages": ["expense"]
            }
        }
    }
}


class TestSpendCategoriesPost(BaseTestCaseWithErrorHandler):
    """
    Test suite for the SpendCategories.post function.
    
    This suite covers successful creation of spend categories,
    as well as error handling for various invalid inputs and edge cases.
    """

    def setUp(self):
        """
        Set up a clean, predictable database state before each test.
        This ensures that tests are isolated and repeatable.
        """
        # Reset test database to known state
        global test_db
        test_db["DB"]["spend_categories"] = {
            "SC001": {
                "id": "SC001",
                "name": "Office Supplies",
                "external_id": "EXT001",
                "usages": ["procurement", "expense"]
            },
            "SC002": {
                "id": "SC002", 
                "name": "IT Equipment",
                "external_id": "EXT002",
                "usages": ["procurement"]
            },
            "SC003": {
                "id": "SC003",
                "name": "Marketing",
                "external_id": None,
                "usages": ["expense"]
            }
        }

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_success_all_fields(self, mock_db):
        """Test successful creation of spend category with all fields provided."""
        result = post(
            name="Professional Services",
            external_id="EXT004",
            usages=["procurement", "expense", "ad_hoc_payment"]
        )
        
        # Verify return format matches JSON:API specification
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "spend_categories")
        self.assertEqual(result["id"], "SC004")  # Should be next in sequence
        self.assertIn("attributes", result)
        
        # Verify attributes
        attributes = result["attributes"]
        self.assertEqual(attributes["name"], "Professional Services")
        self.assertEqual(attributes["external_id"], "EXT004")
        self.assertEqual(attributes["usages"], ["procurement", "expense", "ad_hoc_payment"])
        
        # Verify data was saved to database
        self.assertIn("SC004", test_db["DB"]["spend_categories"])
        saved_category = test_db["DB"]["spend_categories"]["SC004"]
        self.assertEqual(saved_category["name"], "Professional Services")
        self.assertEqual(saved_category["external_id"], "EXT004")

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_success_minimal_fields(self, mock_db):
        """Test successful creation with only required name field."""
        result = post(name="Travel & Lodging")
        
        # Verify return format
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "spend_categories")
        self.assertEqual(result["id"], "SC004")
        
        # Verify attributes
        attributes = result["attributes"]
        self.assertEqual(attributes["name"], "Travel & Lodging")
        self.assertIsNone(attributes["external_id"])
        self.assertIsNone(attributes["usages"])
        
        # Verify database entry
        saved_category = test_db["DB"]["spend_categories"]["SC004"]
        self.assertEqual(saved_category["name"], "Travel & Lodging")
        self.assertIsNone(saved_category["external_id"])
        self.assertIsNone(saved_category["usages"])

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_success_with_single_usage(self, mock_db):
        """Test successful creation with single usage type."""
        result = post(
            name="Security Services",
            external_id="SEC001",
            usages=["supplier_invoice"]
        )
        
        self.assertEqual(result["attributes"]["usages"], ["supplier_invoice"])
        self.assertEqual(result["id"], "SC004")

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_success_empty_database(self, mock_db):
        """Test ID generation when database is empty."""
        # Clear the database
        test_db["DB"]["spend_categories"] = {}
        
        result = post(name="First Category")
        
        # Should generate SC001 for first entry
        self.assertEqual(result["id"], "SC001")
        self.assertEqual(result["attributes"]["name"], "First Category")

    def test_post_validation_error_empty_name(self):
        """Test that empty name raises ValidationError."""
        with self.assertRaises(CustomValidationError) as context:
            post(name="")
        
        self.assertIn("Input validation failed", str(context.exception))

    def test_post_validation_error_whitespace_name(self):
        """Test that whitespace-only name raises ValidationError."""
        with self.assertRaises(CustomValidationError) as context:
            post(name="   ")
        
        self.assertIn("Input validation failed", str(context.exception))

    def test_post_validation_error_name_too_long(self):
        """Test that name exceeding 255 characters raises ValidationError."""
        long_name = "a" * 256  # 256 characters
        
        with self.assertRaises(CustomValidationError) as context:
            post(name=long_name)
        
        self.assertIn("Input validation failed", str(context.exception))

    def test_post_validation_error_external_id_too_long(self):
        """Test that external_id exceeding 255 characters raises ValidationError."""
        long_external_id = "a" * 256  # 256 characters
        
        with self.assertRaises(CustomValidationError) as context:
            post(name="Valid Name", external_id=long_external_id)
        
        self.assertIn("Input validation failed", str(context.exception))

    def test_post_validation_error_empty_external_id(self):
        """Test that empty external_id raises ValidationError."""
        with self.assertRaises(CustomValidationError) as context:
            post(name="Valid Name", external_id="")
        
        self.assertIn("Input validation failed", str(context.exception))

    def test_post_validation_error_whitespace_external_id(self):
        """Test that whitespace-only external_id raises ValidationError."""
        with self.assertRaises(CustomValidationError) as context:
            post(name="Valid Name", external_id="   ")
        
        self.assertIn("Input validation failed", str(context.exception))

    def test_post_validation_error_invalid_usage(self):
        """Test that invalid usage values raise ValidationError."""
        with self.assertRaises(CustomValidationError) as context:
            post(name="Valid Name", usages=["invalid_usage"])
        
        self.assertIn("Input validation failed", str(context.exception))
        self.assertIn("Invalid usage", str(context.exception))

    def test_post_validation_error_mixed_valid_invalid_usages(self):
        """Test that mix of valid and invalid usages raises ValidationError."""
        with self.assertRaises(CustomValidationError) as context:
            post(name="Valid Name", usages=["procurement", "invalid_usage", "expense"])
        
        self.assertIn("Input validation failed", str(context.exception))
        self.assertIn("invalid_usage", str(context.exception))

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_duplicate_external_id_error(self, mock_db):
        """Test that duplicate external_id raises DuplicateExternalIdError."""
        with self.assertRaises(DuplicateExternalIdError) as context:
            post(name="New Category", external_id="EXT001")  # EXT001 already exists
        
        self.assertIn("external_id 'EXT001' already exists", str(context.exception))
        self.assertIn("category ID: SC001", str(context.exception))

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_duplicate_external_id_case_sensitive(self, mock_db):
        """Test that external_id comparison is case-sensitive."""
        # This should succeed as case is different
        result = post(name="New Category", external_id="ext001")  # lowercase
        
        self.assertEqual(result["attributes"]["external_id"], "ext001")
        self.assertEqual(result["id"], "SC004")

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_id_generation_with_gaps(self, mock_db):
        """Test ID generation works correctly when there are gaps in sequence."""
        # Create a database with gaps (SC001, SC003, SC005)
        test_db["DB"]["spend_categories"] = {
            "SC001": {"id": "SC001", "name": "Cat1", "external_id": "EXT001", "usages": None},
            "SC003": {"id": "SC003", "name": "Cat3", "external_id": "EXT003", "usages": None},
            "SC005": {"id": "SC005", "name": "Cat5", "external_id": "EXT005", "usages": None}
        }
        
        result = post(name="New Category")
        
        # Should generate SC006 (next after highest existing number)
        self.assertEqual(result["id"], "SC006")

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_id_generation_with_invalid_ids(self, mock_db):
        """Test ID generation handles invalid ID formats gracefully."""
        # Database with some invalid ID formats
        test_db["DB"]["spend_categories"] = {
            "SC001": {"id": "SC001", "name": "Valid", "external_id": None, "usages": None},
            "INVALID": {"id": "INVALID", "name": "Invalid", "external_id": None, "usages": None},
            "SC_X": {"id": "SC_X", "name": "Invalid2", "external_id": None, "usages": None}
        }
        
        result = post(name="New Category")
        
        # Should generate SC002 (next after valid SC001)
        self.assertEqual(result["id"], "SC002")

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_name_whitespace_trimming(self, mock_db):
        """Test that names with leading/trailing whitespace are trimmed."""
        result = post(name="  Trimmed Name  ", external_id="  EXT004  ")
        
        # Verify trimming occurred
        self.assertEqual(result["attributes"]["name"], "Trimmed Name")
        self.assertEqual(result["attributes"]["external_id"], "EXT004")
        
        # Verify database contains trimmed values
        saved_category = test_db["DB"]["spend_categories"]["SC004"]
        self.assertEqual(saved_category["name"], "Trimmed Name")
        self.assertEqual(saved_category["external_id"], "EXT004")

    @patch("workday.SpendCategories.db.DB", new_callable=lambda: test_db["DB"])
    def test_post_all_valid_usages(self, mock_db):
        """Test creation with all valid usage types."""
        all_usages = ["procurement", "expense", "ad_hoc_payment", "supplier_invoice"]
        
        result = post(
            name="All Usages Category",
            external_id="ALL001",
            usages=all_usages
        )
        
        self.assertEqual(result["attributes"]["usages"], all_usages)
        self.assertEqual(len(result["attributes"]["usages"]), 4)


if __name__ == '__main__':
    unittest.main()