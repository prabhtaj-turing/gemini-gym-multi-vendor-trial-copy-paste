import unittest
import importlib

class TestPackage(unittest.TestCase):
    """Test suite for package health, ensuring modules and tools are importable."""

    def test_google_calendar_import(self):
        """Test that the main google_calendar package can be imported."""
        try:
            import google_calendar
            self.assertIsNotNone(google_calendar)
        except ImportError as e:
            self.fail(f"Failed to import google_calendar: {e}")

    def test_function_imports(self):
        """Test that a sample of functions can be imported from the service."""
        try:
            from google_calendar import create_event, list_events, delete_event
            self.assertTrue(callable(create_event))
            self.assertTrue(callable(list_events))
            self.assertTrue(callable(delete_event))
        except ImportError as e:
            self.fail(f"Failed to import functions from google_calendar: {e}")

    def test_dynamic_function_access(self):
        """Test accessing functions dynamically via __getattr__."""
        google_calendar = importlib.import_module('google_calendar')
        self.assertTrue(hasattr(google_calendar, 'create_event'))
        self.assertTrue(hasattr(google_calendar, 'list_events'))
        self.assertTrue(hasattr(google_calendar, 'delete_event'))
        
        create_event_func = getattr(google_calendar, 'create_event')
        self.assertTrue(callable(create_event_func))

if __name__ == '__main__':
    unittest.main()
