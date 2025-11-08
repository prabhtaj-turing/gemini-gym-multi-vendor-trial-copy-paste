import unittest.mock as mock

from workday.SimulationEngine.custom_errors import (InvalidAttributeError, InvalidPaginationParameterError,
                                                    InvalidSortByValueError, InvalidSortOrderValueError)
from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.BidLineItems import get as get_bid_line_items

_BASE_DB_MOCK_DATA_STORE = {
    "events": {
    "bid_line_items": {
      1: {
        "type": "bid_line_items",
        "id": 1,
        "bid_id": 1,
        "event_id": "EVT001",
        "description": "Office Supplies",
        "amount": 5000,
        "attributes": {
          "data": {
            "column_1": "Quantity: 100",
            "column_2": "Unit Price: $50"
          },
          "updated_at": "2024-01-15T10:30:00Z"
        },
        "relationships": {
          "event": {
            "type": "events",
            "id": 1
          },
          "bid": {
            "type": "bids",
            "id": 1
          },
          "line_item": {
            "type": "line_items",
            "id": "LI001"
          },
          "worksheets": {
            "type": "worksheets",
            "id": "WS001"
          }
        }
      },
      2: {
        "type": "bid_line_items",
        "id": 2,
        "bid_id": 2,
        "event_id": "EVT002",
        "description": "IT Equipment",
        "amount": 15000,
        "attributes": {
          "data": {
            "column_1": "Quantity: 10",
            "column_2": "Unit Price: $1500"
          },
          "updated_at": "2024-01-16T14:45:00Z"
        },
        "relationships": {
          "event": {
            "type": "events",
            "id": 2
          },
          "bid": {
            "type": "bids",
            "id": 2
          },
          "line_item": {
            "type": "line_items",
            "id": "LI002"
          },
          "worksheets": {
            "type": "worksheets",
            "id": "WS002"
          }
        }
      }
    }
}
}

class TestBidLineItems(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Patch the 'db' object for each test with a fresh copy."""
        # Create a fresh copy of the base data for each test
        import copy
        self.db_mock_data_store = copy.deepcopy(_BASE_DB_MOCK_DATA_STORE)
        self.patcher = mock.patch('workday.Users.db.DB', self.db_mock_data_store)
        self.mock_db = self.patcher.start()

    def tearDown(self):
        """Stop the patcher after each test."""
        self.patcher.stop()

    def test_valid_input(self):
        result = get_bid_line_items(1)
        expected = [{
            "type": "bid_line_items",
            "id": 1,
            "bid_id": 1,
            "event_id": "EVT001",
            "description": "Office Supplies",
            "amount": 5000,
            "attributes": {
                "data": {
                    "column_1": "Quantity: 100",
                    "column_2": "Unit Price: $50"
                },
                "updated_at": "2024-01-15T10:30:00Z"
            },
            "relationships": {
                "event": {
                    "type": "events",
                    "id": 1
                },
                "bid": {
                    "type": "bids",
                    "id": 1
                },
                "line_item": {
                    "type": "line_items",
                    "id": "LI001"
                },
                "worksheets": {
                    "type": "worksheets",
                    "id": "WS001"
                }
            }
        }]
        self.assertEqual(result, expected)

    def test_invalid_input_none(self):
        self.assert_error_behavior(
            get_bid_line_items, ValueError, "Bid ID is required",
            bid_id=None
        )

    def test_invalid_input_type(self):
        self.assert_error_behavior(
            get_bid_line_items, TypeError, "Bid ID must be an integer",
            bid_id="1"
        )
        

    def test_invalid_input_value(self):
        result = get_bid_line_items(99)
        self.assertEqual(result, [])
        