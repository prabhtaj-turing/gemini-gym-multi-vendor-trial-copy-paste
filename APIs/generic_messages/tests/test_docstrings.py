import unittest
import generic_messages


class TestDocstrings(unittest.TestCase):
    """Test that all functions have proper docstrings."""

    def test_send_docstring(self):
        """Test that send function has a docstring."""
        self.assertIsNotNone(generic_messages.send.__doc__)
        self.assertIn("Send a message", generic_messages.send.__doc__)

    def test_show_message_recipient_choices_docstring(self):
        """Test that show_message_recipient_choices function has a docstring."""
        self.assertIsNotNone(generic_messages.show_message_recipient_choices.__doc__)
        self.assertIn("Display potential recipients", generic_messages.show_message_recipient_choices.__doc__)

    def test_ask_for_message_body_docstring(self):
        """Test that ask_for_message_body function has a docstring."""
        self.assertIsNotNone(generic_messages.ask_for_message_body.__doc__)
        self.assertIn("Display recipient", generic_messages.ask_for_message_body.__doc__)

    def test_show_message_recipient_not_found_or_specified_docstring(self):
        """Test that show_message_recipient_not_found_or_specified function has a docstring."""
        self.assertIsNotNone(generic_messages.show_message_recipient_not_found_or_specified.__doc__)
        self.assertIn("Inform the user", generic_messages.show_message_recipient_not_found_or_specified.__doc__)


if __name__ == "__main__":
    unittest.main()

