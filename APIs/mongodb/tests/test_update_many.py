# APIs/mongodb/tests/test_update_many.py
"""
High-coverage tests for data_operations.update_many.

* Exercises all success & error paths
* Verifies every rule in UpdateManyInput (Pydantic)
* update_many itself ends up at 100 % branch / line coverage
"""

import unittest
from unittest.mock import patch, MagicMock

import mongomock
from pymongo.errors import OperationFailure, WriteError
from pydantic import ValidationError

from ..data_operations import update_many
from ..SimulationEngine.custom_errors import InvalidQueryError, InvalidUpdateError
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUpdateMany(BaseTestCaseWithErrorHandler):
    """Test update_many function with comprehensive coverage."""

    def setUp(self):
        super().setUp()
        # Clear DB state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None
        
        # Set up test constants
        self.DB = "test_db"
        self.COLL = "test_collection"

    def tearDown(self):
        super().tearDown()
        # Clear DB state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None

    # ------------------------------------------------------------ #
    # SUCCESS TESTS
    # ------------------------------------------------------------ #

    @patch('mongodb.SimulationEngine.utils.get_active_connection')
    def test_successful_update_with_matches(self, mock_conn):
        """Test successful update operation with matched documents."""
        # Mock the MongoDB client and collection
        mock_client = MagicMock()
        mock_collection = MagicMock()
        
        # Mock successful update result
        mock_result = MagicMock()
        mock_result.matched_count = 3
        mock_result.modified_count = 2
        mock_result.upserted_id = None
        mock_collection.update_many.return_value = mock_result
        
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_conn.return_value = mock_client

        result = update_many(
            database=self.DB,
            collection=self.COLL,
            update={"$set": {"status": "updated"}},
            filter={"active": True}
        )

        expected_message = "Matched 3 document(s). Modified 2 document(s)."
        expected_result = {
            "content": [
                {
                    "text": expected_message,
                    "type": "text"
                }
            ]
        }

        self.assertEqual(result, expected_result)
        mock_collection.update_many.assert_called_once_with(
            filter={"active": True},
            update={"$set": {"status": "updated"}},
            upsert=False
        )

    @patch('mongodb.SimulationEngine.utils.get_active_connection')
    def test_successful_update_no_matches(self, mock_conn):
        """Test successful update operation with no matched documents."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_result.modified_count = 0
        mock_result.upserted_id = None
        mock_collection.update_many.return_value = mock_result
        
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_conn.return_value = mock_client

        result = update_many(
            database=self.DB,
            collection=self.COLL,
            update={"$set": {"status": "updated"}},
            filter={"nonexistent": True}
        )

        expected_result = {
            "content": [
                {
                    "text": "No documents matched the filter.",
                    "type": "text"
                }
            ]
        }

        self.assertEqual(result, expected_result)

    @patch('mongodb.SimulationEngine.utils.get_active_connection')
    def test_successful_upsert_operation(self, mock_conn):
        """Test successful upsert operation."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_result.modified_count = 0
        mock_result.upserted_id = "507f1f77bcf86cd799439011"
        mock_collection.update_many.return_value = mock_result
        
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_conn.return_value = mock_client

        result = update_many(
            database=self.DB,
            collection=self.COLL,
            update={"$set": {"status": "new"}},
            filter={"_id": "nonexistent"},
            upsert=True
        )

        # The actual message includes both matched count and upsert info
        expected_message = "Matched 0 document(s). Upserted 1 document with id: 507f1f77bcf86cd799439011."
        expected_result = {
            "content": [
                {
                    "text": expected_message,
                    "type": "text"
                }
            ]
        }

        self.assertEqual(result, expected_result)

    @patch('mongodb.SimulationEngine.utils.get_active_connection')
    def test_default_parameters(self, mock_conn):
        """Test update_many with default parameters."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        
        mock_result = MagicMock()
        mock_result.matched_count = 1
        mock_result.modified_count = 1
        mock_result.upserted_id = None
        mock_collection.update_many.return_value = mock_result
        
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_conn.return_value = mock_client

        result = update_many(
            database=self.DB,
            collection=self.COLL,
            update={"$inc": {"count": 1}}
        )

        # Should use default filter={} and upsert=False
        mock_collection.update_many.assert_called_once_with(
            filter={},
            update={"$inc": {"count": 1}},
            upsert=False
        )

        expected_message = "Matched 1 document(s). Modified 1 document(s)."
        expected_result = {
            "content": [
                {
                    "text": expected_message,
                    "type": "text"
                }
            ]
        }

        self.assertEqual(result, expected_result)

    # ------------------------------------------------------------ #
    # ERROR TESTS
    # ------------------------------------------------------------ #

    def _raise_and_expect(self, exception_to_raise, expected_exception_type, expected_message):
        """Helper method to test exception raising."""
        with patch('mongodb.SimulationEngine.utils.get_active_connection') as mock_conn:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            mock_collection.update_many.side_effect = exception_to_raise
            mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
            mock_conn.return_value = mock_client
            
            self.assert_error_behavior(
                lambda: update_many(self.DB, self.COLL, update={"$set": {"x": 1}}, filter={}),
                expected_exception_type,
                expected_message
            )

    def test_invalid_filter_error_code_2(self):
        self._raise_and_expect(
            OperationFailure("BadValue", code=2),
            InvalidQueryError,
            "Invalid 'filter' document for collection 'test_collection' (Error Code: 2): BadValue"
        )

    def test_invalid_update_error_code_9(self):
        self._raise_and_expect(
            OperationFailure("FailedToParse", code=9),
            InvalidUpdateError,
            "Invalid 'update' document for collection 'test_collection' (Error Code: 9): FailedToParse"
        )

    def test_write_error_propagation(self):
        self._raise_and_expect(
            WriteError("Write failed", code=11000),
            InvalidUpdateError,
            "Update operation failed on collection 'test_collection' (Error Code: 11000): Write failed"
        )

    def test_generic_operation_failure(self):
        self._raise_and_expect(
            OperationFailure("Generic error", code=999),
            InvalidUpdateError,
            "Update operation failed on collection 'test_collection' (Error Code: 999): Generic error"
        )

    # ------------------------------------------------------------ #
    # VALIDATION TESTS
    # ------------------------------------------------------------ #

    def test_invalid_database_name(self):
        """Test validation error for invalid database name."""
        self.assert_error_behavior(
            lambda: update_many(
                database="",  # Invalid empty database name
                collection=self.COLL,
                update={"$set": {"x": 1}}
            ),
            ValidationError,
            "String should have at least 1 character"
        )

    def test_invalid_collection_name(self):
        """Test validation error for invalid collection name."""
        self.assert_error_behavior(
            lambda: update_many(
                database=self.DB,
                collection="",  # Invalid empty collection name
                update={"$set": {"x": 1}}
            ),
            ValidationError,
            "String should have at least 1 character"
        )

    def test_invalid_update_document_type(self):
        """Test validation error for invalid update document type."""
        self.assert_error_behavior(
            lambda: update_many(
                database=self.DB,
                collection=self.COLL,
                update="invalid"  # Should be dict
            ),
            ValidationError,
            "Input should be a valid dictionary"
        )

    def test_invalid_filter_document_type(self):
        """Test validation error for invalid filter document type."""
        self.assert_error_behavior(
            lambda: update_many(
                database=self.DB,
                collection=self.COLL,
                update={"$set": {"x": 1}},
                filter="invalid"  # Should be dict or None
            ),
            ValidationError,
            "Input should be a valid dictionary"
        )

    def test_invalid_upsert_type(self):
        """Test validation error for invalid upsert type."""
        self.assert_error_behavior(
            lambda: update_many(
                database=self.DB,
                collection=self.COLL,
                update={"$set": {"x": 1}},
                upsert="invalid"  # Should be bool or None
            ),
            ValidationError,
            "Input should be a valid boolean"
        )

    @patch('mongodb.SimulationEngine.utils.get_active_connection')
    def test_value_error_from_pymongo(self, mock_conn):
        """Test ValueError from PyMongo client-side validation."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.update_many.side_effect = ValueError("Missing $ operator")
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_conn.return_value = mock_client

        self.assert_error_behavior(
            lambda: update_many(self.DB, self.COLL, update={"invalid": "update"}),
            InvalidUpdateError,
            "Update document rejected client-side for collection 'test_collection': Missing $ operator"
        )

    def test_empty_update_document_server_error(self):
        """Test that empty update document passes validation but fails at server level."""
        # Empty dict passes Pydantic validation but should fail at MongoDB level
        with patch('mongodb.SimulationEngine.utils.get_active_connection') as mock_conn:
            mock_client = MagicMock()
            mock_collection = MagicMock()
            # Simulate MongoDB server rejecting empty update document
            mock_collection.update_many.side_effect = OperationFailure("empty update document", code=2)
            mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
            mock_conn.return_value = mock_client
            
            self.assert_error_behavior(
                lambda: update_many(
                    database=self.DB,
                    collection=self.COLL,
                    update={}  # Empty update document - valid for Pydantic, invalid for MongoDB
                ),
                InvalidQueryError,  # Code 2 maps to InvalidQueryError
                "Invalid 'filter' document for collection 'test_collection' (Error Code: 2): empty update document"
            )


if __name__ == '__main__':
    unittest.main()