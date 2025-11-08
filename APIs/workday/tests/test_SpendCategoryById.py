import unittest
import workday
from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.SimulationEngine import custom_errors

class TestSpendCategoryByIdDelete(BaseTestCaseWithErrorHandler):
    """
    Test suite for the SpendCategoryById.delete function.
    
    This suite covers the successful deletion of a spend category,
    as well as error handling for various invalid inputs and edge cases.
    """

    def setUp(self):
        """
        Set up a clean, predictable database state before each test.
        This ensures that tests are isolated and repeatable.
        """
        # Initialize the database with a known set of spend categories
        workday.SimulationEngine.db.DB = {
            'spend_categories': {
                123: {'name': 'Office Supplies', 'external_id': 'cat-001'},
                456: {'name': 'Software Licenses', 'external_id': 'cat-002'},
                789: {'name': 'Marketing Services', 'external_id': 'cat-003'}
            }
        }

    def test_delete_success(self):
        """
        Test the successful deletion of an existing spend category.
        """
        # Ensure the category exists before deletion
        self.assertIn(123, workday.SimulationEngine.db.DB['spend_categories'])
        
        # Call the delete function
        result = workday.SpendCategoryById.delete(123)
        
        # Assert that the function returns True on success
        self.assertTrue(result)
        
        # Assert that the category has been removed from the database
        self.assertNotIn(123, workday.SimulationEngine.db.DB['spend_categories'])
        
        # Verify that other categories remain untouched
        self.assertIn(456, workday.SimulationEngine.db.DB['spend_categories'])

    def test_delete_not_found(self):
        """
        Test that deleting a non-existent spend category ID raises a NotFoundError.
        """
        non_existent_id = 999
        self.assert_error_behavior(
            workday.SpendCategoryById.delete,
            custom_errors.NotFoundError,
            f"Spend category with ID {non_existent_id} not found.",
            None,  # No additional fields expected in the error dictionary
            non_existent_id
        )

    ### Edge Cases for ID Validation ###

    def test_delete_invalid_id_zero(self):
        """
        Test that passing zero as an ID raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.SpendCategoryById.delete,
            custom_errors.InvalidInputError,
            "ID must be a positive integer.",
            None,
            0
        )

    def test_delete_invalid_id_negative(self):
        """
        Test that passing a negative number as an ID raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.SpendCategoryById.delete,
            custom_errors.InvalidInputError,
            "ID must be a positive integer.",
            None,
            -50
        )

    def test_delete_invalid_id_type_string(self):
        """
        Test that passing a string as an ID raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.SpendCategoryById.delete,
            custom_errors.InvalidInputError,
            "ID must be a positive integer.",
            None,
            'not-an-integer'
        )

    def test_delete_invalid_id_type_none(self):
        """
        Test that passing None as an ID raises an InvalidInputError.
        """
        self.assert_error_behavior(
            workday.SpendCategoryById.delete,
            custom_errors.InvalidInputError,
            "ID must be a positive integer.",
            None,
            None
        )


if __name__ == '__main__':
    # This allows the test suite to be run directly from the command line
    unittest.main()