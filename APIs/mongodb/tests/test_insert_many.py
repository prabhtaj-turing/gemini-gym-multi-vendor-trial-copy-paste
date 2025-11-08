# test_insert_many.py

import unittest
from unittest.mock import patch, MagicMock

from pydantic import ValidationError
from pymongo.errors import (
    InvalidOperation, 
    BulkWriteError as PyMongoBulkWriteError,
    OperationFailure
)
from pymongo.results import InsertManyResult

from ..data_operations import insert_many 
from ..SimulationEngine.custom_errors import (
    InvalidDocumentError,
    BulkWriteError 
)
from common_utils.base_case import BaseTestCaseWithErrorHandler 

PATCH_TARGET_FOR_UTILS_GET_CONNECTION = "mongodb.data_operations.utils.get_active_connection"


class TestInsertManyOperation(BaseTestCaseWithErrorHandler):

    # --- Input Validation Error Tests (Pydantic) ---
    def test_pydantic_validation_error_missing_database_arg(self):
        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=TypeError, 
            expected_message="insert_many() missing 1 required positional argument: 'database'",
            collection="mycoll", documents=[{"a":1}]
        )

    def test_pydantic_validation_error_missing_collection_arg(self):
        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=TypeError,
            expected_message="insert_many() missing 1 required positional argument: 'collection'",
            database="mydb", documents=[{"a":1}]
        )
    
    def test_pydantic_validation_error_missing_documents_arg(self):
        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=TypeError,
            expected_message="insert_many() missing 1 required positional argument: 'documents'",
            database="mydb", collection="mycoll"
        )

    def test_pydantic_validation_error_documents_empty_list(self):
        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=ValidationError,
            expected_message="documents",
            database="mydb", collection="mycoll", documents=[]
        )

    def test_pydantic_validation_error_documents_not_list_of_dicts(self):
        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=ValidationError,
            expected_message="documents",
            database="mydb", collection="mycoll", documents=["not a dict"]
        )

    # --- MongoDB Operation Error Tests ---
    @patch(PATCH_TARGET_FOR_UTILS_GET_CONNECTION)
    def test_invalid_document_error_on_pymongo_invalid_operation(self, mock_get_active_connection):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection_obj = MagicMock()
        mock_get_active_connection.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection_obj
        
        pymongo_err_msg = "document must be an instance of dict" 
        mock_collection_obj.insert_many.side_effect = InvalidOperation(pymongo_err_msg)

        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=InvalidDocumentError,
            expected_message=pymongo_err_msg,
            database="mydb", collection="mycoll", documents=[{"_id": object()}]
        )

    @patch(PATCH_TARGET_FOR_UTILS_GET_CONNECTION)
    def test_custom_bulk_write_error_on_pymongo_bulk_write_error(self, mock_get_active_connection):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection_obj = MagicMock()
        mock_get_active_connection.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection_obj
        
        mock_pymongo_bwe_details = {
            'writeErrors': [{'index': 0, 'code': 11000, 'errmsg': 'E11000 duplicate key error'}],
            'nInserted': 0,
        }
        pymongo_bwe_instance = PyMongoBulkWriteError(
            results=mock_pymongo_bwe_details # The full details document
        )
        mock_collection_obj.insert_many.side_effect = pymongo_bwe_instance

        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=BulkWriteError,
            expected_message=str(mock_pymongo_bwe_details), 
            database="mydb", collection="mycoll", documents=[{"_id": 1}, {"_id": 1}] 
        )

    @patch(PATCH_TARGET_FOR_UTILS_GET_CONNECTION)
    def test_operation_failure_reraised(self, mock_get_active_connection):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection_obj = MagicMock()
        mock_get_active_connection.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection_obj
        
        op_failure_msg = "Invalid collection name: my$coll"
        op_failure_exception = OperationFailure(op_failure_msg, code=73)
        mock_collection_obj.insert_many.side_effect = op_failure_exception

        self.assert_error_behavior(
            func_to_call=insert_many,
            expected_exception_type=OperationFailure, 
            expected_message=op_failure_msg, # Corrected: str(OperationFailure) is often just the message
            database="mydb", collection="my$coll", documents=[{"a":1}]
        )

    # --- Success Path Test ---
    @patch(PATCH_TARGET_FOR_UTILS_GET_CONNECTION)
    def test_success_insert_many(self, mock_get_active_connection):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection_obj = MagicMock()
        mock_insert_result = MagicMock(spec=InsertManyResult)

        mock_get_active_connection.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection_obj

        inserted_ids = [MagicMock(), MagicMock()]
        inserted_ids[0].__str__ = MagicMock(return_value="id_1")
        inserted_ids[1].__str__ = MagicMock(return_value="id_2")
        
        mock_insert_result.inserted_ids = inserted_ids
        mock_collection_obj.insert_many.return_value = mock_insert_result

        documents_to_insert = [{"name": "doc1"}, {"name": "doc2"}]
        result = insert_many(
            database="test_db", 
            collection="test_coll", 
            documents=documents_to_insert
        )
        
        expected_message_line1 = "Inserted 2 document(s) into collection \"test_coll\""
        expected_message_line2 = "Inserted IDs: id_1, id_2"
        
        self.assertEqual(len(result["content"]), 2)
        self.assertEqual(result["content"][0]["text"], expected_message_line1)
        self.assertEqual(result["content"][0]["type"], "text")
        self.assertEqual(result["content"][1]["text"], expected_message_line2)
        self.assertEqual(result["content"][1]["type"], "text")

        mock_get_active_connection.assert_called_once()
        mock_client.__getitem__.assert_called_once_with("test_db")
        mock_db.__getitem__.assert_called_once_with("test_coll")
        mock_collection_obj.insert_many.assert_called_once_with(
            documents_to_insert,
            ordered=True 
        )
    
    @patch(PATCH_TARGET_FOR_UTILS_GET_CONNECTION)
    def test_success_insert_single_document_in_list(self, mock_get_active_connection):
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection_obj = MagicMock()
        mock_insert_result = MagicMock(spec=InsertManyResult)

        mock_get_active_connection.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection_obj

        inserted_id_mock = MagicMock()
        inserted_id_mock.__str__ = MagicMock(return_value="single_id_123")
        
        mock_insert_result.inserted_ids = [inserted_id_mock]
        mock_collection_obj.insert_many.return_value = mock_insert_result

        documents_to_insert = [{"item": "single"}]
        result = insert_many(
            database="single_db", 
            collection="single_coll", 
            documents=documents_to_insert
        )
        
        expected_message_line1 = "Inserted 1 document(s) into collection \"single_coll\""
        expected_message_line2 = "Inserted IDs: single_id_123"
        
        self.assertEqual(result["content"][0]["text"], expected_message_line1)
        self.assertEqual(result["content"][1]["text"], expected_message_line2)
        mock_collection_obj.insert_many.assert_called_once_with(
            documents_to_insert,
            ordered=True
        )

if __name__ == '__main__':
    unittest.main()