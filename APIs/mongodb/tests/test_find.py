import unittest
import copy
from datetime import datetime # Not strictly used by current test data, but good for future extension
from bson import ObjectId, json_util
import mongomock # For test setup: simulating MongoDB client
from pydantic import ValidationError

# CRITICAL IMPORT FOR CUSTOM ERRORS
from ..SimulationEngine import custom_errors
from ..data_operations import find
from ..SimulationEngine.models import FindInput
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import get_active_connection
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestFindFunction(BaseTestCaseWithErrorHandler):

    def setUp(self):

        self.mock_client = mongomock.MongoClient()

        DB.current_conn = 'test_conn_find'
        DB.connections = {
            'test_conn_find': self.mock_client
        }
        DB.current_db = 'test_find_db'

        self.db_name = "test_find_db"
        self.coll_name = "test_find_coll"
        self.empty_coll_name = "test_empty_coll"
        self.another_db_name = "another_find_db" 

        self.db_instance = get_active_connection()
        self.collection = self.db_instance[DB.current_db][self.coll_name]
        
        # Ensure empty collection exists
        _ = self.db_instance[self.empty_coll_name]

        # Sample documents
        self.doc1_id = ObjectId()
        self.doc1 = {"_id": self.doc1_id, "name": "Alice", "age": 30, "city": "New York", "tags": ["A", "B"]}
        
        self.doc2_id = ObjectId()
        self.doc2 = {"_id": self.doc2_id, "name": "Bob", "age": 24, "city": "Paris", "tags": ["B", "C"], "active": True}
        
        self.doc3_id = ObjectId()
        self.doc3 = {"_id": self.doc3_id, "name": "Charlie", "age": 35, "city": "New York", "tags": ["A", "C"]}
        
        self.doc4_id = ObjectId()
        self.doc4 = {"_id": self.doc4_id, "name": "David", "age": 24, "city": "London", "tags": ["D"], "active": False}
        
        self.doc5_id = ObjectId()
        self.doc5 = {"_id": self.doc5_id, "name": "Eve", "age": 40, "city": "Berlin", "tags": ["E"], "nested": {"value": 100}}

        # Default insertion order, used for tests that don't specify sort or where sort is ambiguous
        self.all_docs_in_insertion_order = [
            copy.deepcopy(self.doc1), 
            copy.deepcopy(self.doc2), 
            copy.deepcopy(self.doc3), 
            copy.deepcopy(self.doc4), 
            copy.deepcopy(self.doc5)
        ]
        
        self.collection.insert_many(copy.deepcopy(self.all_docs_in_insertion_order))

    
    def _assert_find_results(self, results, expected_num_docs_in_summary, expected_docs_list):
        self.assertIsInstance(results, list, "Results should be a list.")
        self.assertTrue(len(results) >= 1, "Results list should have at least the summary block.")

        summary_block = results[0]
        self.assertEqual(summary_block.get('type'), 'text', "Summary block type should be 'text'.")
        expected_summary_text = f"Found {expected_num_docs_in_summary} document{'s' if expected_num_docs_in_summary != 1 else ''}."
        self.assertEqual(summary_block.get('text'), expected_summary_text,
                         f"Summary text mismatch. Expected: '{expected_summary_text}', Got: '{summary_block.get('text')}'.")

        returned_doc_blocks = results[1:]
        self.assertEqual(len(returned_doc_blocks), len(expected_docs_list),
                         f"Mismatch in number of document blocks. Expected {len(expected_docs_list)}, got {len(returned_doc_blocks)}.")

        for i, block in enumerate(returned_doc_blocks):
            self.assertEqual(block.get('type'), 'text', f"Document block {i} type is not 'text'.")
            actual_doc_text = block.get('text')
            self.assertIsInstance(actual_doc_text, str, f"Document block {i} text should be a string (EJSON).")
            
            try:
                actual_doc = json_util.loads(actual_doc_text)
            except Exception as e:
                self.fail(f"Failed to parse EJSON string for document block {i}: '{actual_doc_text}'. Error: {e}")
            
            expected_doc = expected_docs_list[i]
            
            self.assertEqual(set(actual_doc.keys()), set(expected_doc.keys()),
                             f"Key mismatch in document {i}.\nActual keys: {set(actual_doc.keys())}\nExpected keys: {set(expected_doc.keys())}\nActual doc: {actual_doc}\nExpected doc: {expected_doc}")
            
            for key in expected_doc:
                self.assertEqual(actual_doc[key], expected_doc[key],
                                 f"Value mismatch for key '{key}' in document {i}.\nActual value: {actual_doc[key]} (type: {type(actual_doc[key])})\nExpected value: {expected_doc[key]} (type: {type(expected_doc[key])})\nActual doc: {actual_doc}\nExpected doc: {expected_doc}")

    # --- Success Cases ---

    def test_find_no_args_default_limit(self):
        results = find(database=self.db_name, collection=self.coll_name)
        self._assert_find_results(results, 5, self.all_docs_in_insertion_order)

    def test_find_with_simple_filter(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"age": 24})
        expected = [self.doc2, self.doc4] # Based on insertion order for ties
        self._assert_find_results(results, 2, expected)

    def test_find_with_oid_filter(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"_id": self.doc1_id})
        self._assert_find_results(results, 1, [self.doc1])
        
    def test_find_with_nested_field_filter(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"nested.value": 100})
        self._assert_find_results(results, 1, [self.doc5])

    def test_find_with_projection_include(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"name": "Alice"}, projection={"name": 1, "age": 1})
        expected = [{"_id": self.doc1_id, "name": "Alice", "age": 30}]
        self._assert_find_results(results, 1, expected)

    def test_find_with_projection_exclude_id(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"name": "Alice"}, projection={"name": 1, "age": 1, "_id": 0})
        expected = [{"name": "Alice", "age": 30}]
        self._assert_find_results(results, 1, expected)

    def test_find_with_projection_exclude_fields(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"name": "Bob"}, projection={"city": 0, "tags": 0})
        expected = [{"_id": self.doc2_id, "name": "Bob", "age": 24, "active": True}] 
        self._assert_find_results(results, 1, expected)

    def test_find_with_empty_projection_dict(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"name": "Alice"}, projection={})
        self._assert_find_results(results, 1, [self.doc1])
        
    def test_find_with_projection_none(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"name": "Alice"}, projection=None)
        self._assert_find_results(results, 1, [self.doc1])

    def test_find_with_limit_less_than_matches(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"city": "New York"}, limit=1) 
        self._assert_find_results(results, 1, [self.doc1]) # Assumes doc1 is first by insertion order

    def test_find_with_limit_equal_to_matches(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"age": 24}, limit=2) 
        expected = [self.doc2, self.doc4] # Insertion order
        self._assert_find_results(results, 2, expected)

    def test_find_with_limit_more_than_matches(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"age": 30}, limit=5) 
        self._assert_find_results(results, 1, [self.doc1])

    def test_find_with_limit_zero_means_no_limit(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"city": "New York"}, limit=0) 
        expected = [self.doc1, self.doc3] # Insertion order
        self._assert_find_results(results, 2, expected)

    def test_find_with_sort_ascending(self):
        results = find(database=self.db_name, collection=self.coll_name, sort={"age": 1})
        # Create a fresh copy for sorting to avoid modifying self.all_docs_in_insertion_order
        docs_copy = copy.deepcopy(self.all_docs_in_insertion_order)
        expected_sorted = sorted(docs_copy, key=lambda x: (x["age"], str(x["_id"]))) # Stable sort by age, then _id for tie-breaking
        self._assert_find_results(results, 5, expected_sorted)


    def test_find_with_sort_descending(self):
        results = find(database=self.db_name, collection=self.coll_name, sort={"age": -1})
        docs_copy = copy.deepcopy(self.all_docs_in_insertion_order)
        expected_sorted = sorted(docs_copy, key=lambda x: (x["age"]), reverse=True) # Stable sort by age desc, then _id desc for tie-breaking
        self._assert_find_results(results, 5, expected_sorted)


    def test_find_with_multiple_sort_keys(self):
        results = find(database=self.db_name, collection=self.coll_name, sort={"age": 1, "name": -1})
        # Expected order: (David, 24), (Bob, 24), (Alice, 30), (Charlie, 35), (Eve, 40)
        expected_final_sort = [self.doc4, self.doc2, self.doc1, self.doc3, self.doc5]
        self._assert_find_results(results, 5, expected_final_sort)

    def test_find_all_parameters_combined(self):
        results = find(
            database=self.db_name,
            collection=self.coll_name,
            filter={"age": {"$gt": 25}}, 
            projection={"name": 1, "city": 1, "_id": 0},
            sort={"name": 1}, 
            limit=1
        )
        expected = [{"name": "Alice", "city": "New York"}]
        self._assert_find_results(results, 1, expected)

    def test_find_no_documents_match_filter(self):
        results = find(database=self.db_name, collection=self.coll_name, filter={"name": "NonExistent"})
        self._assert_find_results(results, 0, [])

    def test_find_on_empty_collection(self):
        results = find(database=self.db_name, collection=self.empty_coll_name)
        self._assert_find_results(results, 0, [])

    def test_find_sort_on_nonexistent_field(self):
        results = find(database=self.db_name, collection=self.coll_name, sort={"non_existent_field": 1})
        # Order of all_docs_in_insertion_order is preserved as they all effectively have null for non_existent_field
        self._assert_find_results(results, 5, self.all_docs_in_insertion_order)

    # --- Error Cases ---

    def test_find_invalid_database_name_type(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValidationError,
            expected_message="Input should be a valid string",
            database=123, 
            collection=self.coll_name
        )

    def test_find_empty_database_name(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValueError,
            expected_message="Database name must not be empty",
            database="",
            collection=self.coll_name
        )

    def test_find_invalid_collection_name_type(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValidationError,
            expected_message="Input should be a valid string",
            database=self.db_name,
            collection=123 
        )

    def test_find_empty_collection_name(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValueError,
            expected_message="Collection name must not be empty",
            database=self.db_name,
            collection=""
        )


    def test_find_invalid_filter_type(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValidationError, 
            expected_message="Input should be a valid dictionary",
            database=self.db_name,
            collection=self.coll_name,
            filter="not_a_dict"
        )

    def test_find_malformed_filter_operator(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=custom_errors.InvalidQueryError,
            expected_message="MongoDB query execution failed: unknown operator: $invalidOp",
            database=self.db_name,
            collection=self.coll_name,
            filter={"name": {"$invalidOp": "Alice"}}
        )

    def test_find_invalid_projection_type(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValidationError, 
            expected_message="Input should be a valid dictionary",
            database=self.db_name,
            collection=self.coll_name,
            projection="not_a_dict"
        )

    def test_find_with_mongomock_permissive_projection_value(self): # Renamed to reflect new understanding
        """
        Tests how mongomock handles a projection value that would be invalid in MongoDB (e.g., {"name": 100}).
        Based on debug output, mongomock does not raise an OperationFailure for this.
        This test verifies that the find operation completes and checks the output.
        """
        results = find(
            database=self.db_name,
            collection=self.coll_name,
            filter={},
            projection={"name": 100} # Invalid value for MongoDB, but mongomock seems to accept it
        )
        expected_num_docs = 5
        
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0)
        summary_block = results[0]
        self.assertEqual(summary_block.get('type'), 'text')
        self.assertIn(f"Found {expected_num_docs} document", summary_block.get('text'))
        self.assertEqual(len(results), expected_num_docs + 1)

    def test_find_invalid_limit_type(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValidationError,
            expected_message="Input should be a valid integer",
            database=self.db_name,
            collection=self.coll_name,
            limit="not_an_int"
        )

    def test_find_negative_limit(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValueError, 
            expected_message="Input should be greater than or equal to 0",
            database=self.db_name,
            collection=self.coll_name,
            limit=-1
        )

    def test_find_invalid_sort_type(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValidationError, 
            expected_message="Input should be a valid dictionary",
            database=self.db_name,
            collection=self.coll_name,
            sort="not_a_dict"
        )

    def test_find_malformed_sort_value(self):
        self.assert_error_behavior(
            func_to_call=find,
            expected_exception_type=ValueError,
            expected_message="Input should be a valid integer",
            database=self.db_name,
            collection=self.coll_name,
            sort={"age": "ascending"} 
        )

if __name__ == '__main__':
    unittest.main()