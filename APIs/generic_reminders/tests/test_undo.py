import unittest
from ..SimulationEngine.custom_errors import ValidationError, OperationNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import generic_reminders


class TestUndo(BaseCase):
    def setUp(self):
        super().setUp()
        # Create a test reminder to work with
        self.create_result = generic_reminders.create_reminder(
            title="Test Reminder for Undo",
            description="This will be used for undo testing",
            start_date="2025-12-25",
            time_of_day="10:00:00",
            am_pm_or_unknown="AM",
        )
        self.reminder_id = self.create_result["reminders"][0]["id"]
        self.create_operation_id = self.create_result["undo_operation_ids"][0]

    def test_undo_create_operation_success(self):
        """Test successfully undoing a create operation."""
        # Verify reminder exists before undo
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertEqual(len(result["reminders"]), 1)

        # Undo the creation
        undo_result = generic_reminders.undo(
            undo_operation_ids=[self.create_operation_id]
        )

        self.assertIsInstance(undo_result, str)
        self.assertIn("Successfully reverted 1 operation", undo_result)

        # Verify reminder is removed after undo
        try:
            generic_reminders.show_matching_reminders(reminder_ids=[self.reminder_id])
            self.fail("Expected ReminderNotFoundError after undo")
        except:
            pass  # Expected behavior

    def test_undo_modify_operation_success(self):
        """Test successfully undoing a modify operation."""
        # Modify the reminder
        modify_result = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id],
            title="Modified Title",
            description="Modified Description",
            is_bulk_mutation=False,
        )
        modify_operation_id = modify_result["undo_operation_ids"][0]

        # Verify modification was applied
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertEqual(result["reminders"][0]["title"], "Modified Title")
        self.assertEqual(result["reminders"][0]["description"], "Modified Description")

        # Undo the modification
        undo_result = generic_reminders.undo(undo_operation_ids=[modify_operation_id])

        self.assertIsInstance(undo_result, str)
        self.assertIn("Successfully reverted 1 operation", undo_result)

        # Verify original values are restored
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertEqual(result["reminders"][0]["title"], "Test Reminder for Undo")
        self.assertEqual(
            result["reminders"][0]["description"], "This will be used for undo testing"
        )

    def test_undo_completion_operation_success(self):
        """Test successfully undoing a completion operation."""
        # Mark reminder as completed
        modify_result = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id], completed=True, is_bulk_mutation=False
        )
        completion_operation_id = modify_result["undo_operation_ids"][0]

        # Verify reminder is completed
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertTrue(result["reminders"][0]["completed"])

        # Undo the completion
        undo_result = generic_reminders.undo(
            undo_operation_ids=[completion_operation_id]
        )

        self.assertIsInstance(undo_result, str)
        self.assertIn("Successfully reverted 1 operation", undo_result)

        # Verify reminder is no longer completed
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertFalse(result["reminders"][0]["completed"])

    def test_undo_multiple_operations_success(self):
        """Test successfully undoing multiple operations."""
        # Perform multiple operations
        modify_result1 = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id],
            title="First Modification",
            is_bulk_mutation=False,
        )

        modify_result2 = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id],
            description="Second Modification",
            is_bulk_mutation=False,
        )

        operation_ids = [
            modify_result1["undo_operation_ids"][0],
            modify_result2["undo_operation_ids"][0],
        ]

        # Undo both operations
        undo_result = generic_reminders.undo(undo_operation_ids=operation_ids)

        self.assertIsInstance(undo_result, str)
        self.assertIn("Successfully reverted 2 operations", undo_result)

    def test_undo_nonexistent_operation(self):
        """Test undoing non-existent operation."""
        self.assert_error_behavior(
            generic_reminders.undo,
            OperationNotFoundError,
            "Operation non_existent_operation not found",
            undo_operation_ids=["non_existent_operation"],
        )

    def test_undo_empty_operation_list(self):
        """Test undoing with empty operation list."""
        result = generic_reminders.undo(undo_operation_ids=[])

        self.assertIsInstance(result, str)
        self.assertEqual(result, "No operations to undo")

    def test_undo_none_operation_list(self):
        """Test undoing with None operation list."""
        result = generic_reminders.undo(undo_operation_ids=None)

        self.assertIsInstance(result, str)
        self.assertEqual(result, "No operations to undo")

    def test_undo_invalid_operation_id_type(self):
        """Test undoing with invalid operation ID type."""
        self.assert_error_behavior(
            generic_reminders.undo,
            ValidationError,
            "Input validation failed: All undo_operation_ids must be strings",
            undo_operation_ids=[123],
        )

    def test_undo_mixed_success_failure(self):
        """Test undoing with mix of valid and invalid operation IDs."""
        # This should test the partial failure scenario
        # First create another operation to have a valid one
        modify_result = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id],
            title="Another Modification",
            is_bulk_mutation=False,
        )
        valid_operation_id = modify_result["undo_operation_ids"][0]

        # Try to undo one valid and one invalid operation
        result = generic_reminders.undo(
            undo_operation_ids=[valid_operation_id, "invalid_operation"]
        )

        self.assertIsInstance(result, str)
        # Should indicate partial success
        self.assertIn("Reverted 1 operation", result)
        self.assertIn("failed to revert 1", result)

    def test_undo_already_undone_operation(self):
        """Test undoing an operation that was already undone."""
        # Undo an operation first
        generic_reminders.undo(undo_operation_ids=[self.create_operation_id])

        # Try to undo the same operation again
        self.assert_error_behavior(
            generic_reminders.undo,
            OperationNotFoundError,
            f"Operation {self.create_operation_id} not found",
            undo_operation_ids=[self.create_operation_id],
        )

    def test_undo_delete_operation(self):
        """Test undoing a delete operation."""
        # Delete the reminder
        delete_result = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id], deleted=True, is_bulk_mutation=False
        )
        delete_operation_id = delete_result["undo_operation_ids"][0]

        # Verify reminder is marked as deleted (but still shown when using reminder_ids)
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertEqual(len(result["reminders"]), 1)
        self.assertTrue(result["reminders"][0]["deleted"])

        # Undo the delete operation
        undo_result = generic_reminders.undo(undo_operation_ids=[delete_operation_id])
        self.assertEqual(undo_result, "Successfully reverted 1 operation")

        # Verify reminder is restored and not deleted
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertEqual(len(result["reminders"]), 1)
        self.assertFalse(result["reminders"][0]["deleted"])

    def test_undo_operation_sequence(self):
        """Test undoing operations in sequence."""
        original_title = self.create_result["reminders"][0]["title"]

        # Perform a sequence of modifications
        modify1 = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id],
            title="First Change",
            is_bulk_mutation=False,
        )

        modify2 = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id],
            title="Second Change",
            is_bulk_mutation=False,
        )

        modify3 = generic_reminders.modify_reminder(
            reminder_ids=[self.reminder_id],
            title="Third Change",
            is_bulk_mutation=False,
        )

        # Undo the last modification
        generic_reminders.undo(undo_operation_ids=[modify3["undo_operation_ids"][0]])

        # Check that we're back to "Second Change"
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertEqual(result["reminders"][0]["title"], "Second Change")

        # Undo the second modification
        generic_reminders.undo(undo_operation_ids=[modify2["undo_operation_ids"][0]])

        # Check that we're back to "First Change"
        result = generic_reminders.show_matching_reminders(
            reminder_ids=[self.reminder_id]
        )
        self.assertEqual(result["reminders"][0]["title"], "First Change")


if __name__ == "__main__":
    unittest.main()
