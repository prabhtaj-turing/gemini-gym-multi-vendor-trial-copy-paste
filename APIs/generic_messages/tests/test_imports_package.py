import unittest


class TestImports(unittest.TestCase):
    """Test that the package imports work correctly."""

    def test_import_package(self):
        """Test that we can import the generic_messages package."""
        import generic_messages
        self.assertIsNotNone(generic_messages)

    def test_import_functions(self):
        """Test that we can import all the main functions."""
        from generic_messages import (
            send,
            show_message_recipient_choices,
            ask_for_message_body,
            show_message_recipient_not_found_or_specified
        )
        self.assertIsNotNone(send)
        self.assertIsNotNone(show_message_recipient_choices)
        self.assertIsNotNone(ask_for_message_body)
        self.assertIsNotNone(show_message_recipient_not_found_or_specified)

    def test_import_models(self):
        """Test that we can import models."""
        from generic_messages.SimulationEngine.models import (
            Recipient,
            Endpoint,
            MediaAttachment,
            Observation
        )
        self.assertIsNotNone(Recipient)
        self.assertIsNotNone(Endpoint)
        self.assertIsNotNone(MediaAttachment)
        self.assertIsNotNone(Observation)

    def test_import_custom_errors(self):
        """Test that we can import custom errors."""
        from generic_messages.SimulationEngine.custom_errors import (
            InvalidRecipientError,
            InvalidEndpointError,
            MessageBodyRequiredError,
            InvalidMediaAttachmentError
        )
        self.assertIsNotNone(InvalidRecipientError)
        self.assertIsNotNone(InvalidEndpointError)
        self.assertIsNotNone(MessageBodyRequiredError)
        self.assertIsNotNone(InvalidMediaAttachmentError)

    def test_import_utils(self):
        """Test that we can import utilities."""
        from generic_messages.SimulationEngine import utils
        self.assertIsNotNone(utils)


if __name__ == "__main__":
    unittest.main()

