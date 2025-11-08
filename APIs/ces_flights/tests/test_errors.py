import unittest
import sys
import os

# Add the parent directory to the path to fix imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ces_flights.SimulationEngine.custom_errors import (
    FlightBookingError,
    ValidationError,
    DatabaseError,
    BookingError,
    InvalidDateError,
    FlightDataError,
    EmptyFieldError
)


class TestErrorHierarchy(BaseTestCaseWithErrorHandler):
    """Test the error hierarchy and inheritance."""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(ValidationError, FlightBookingError))
        self.assertTrue(issubclass(DatabaseError, FlightBookingError))
        self.assertTrue(issubclass(BookingError, FlightBookingError))
        self.assertTrue(issubclass(InvalidDateError, FlightBookingError))
        self.assertTrue(issubclass(FlightDataError, FlightBookingError))
        self.assertTrue(issubclass(EmptyFieldError, FlightBookingError))


if __name__ == "__main__":
    unittest.main()