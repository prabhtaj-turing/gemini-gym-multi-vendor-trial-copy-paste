import unittest
import copy
from datetime import datetime, timezone
from bson import ObjectId, Binary

# CRITICAL IMPORT FOR CUSTOM ERRORS
from ..SimulationEngine import custom_errors

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..collection_management import collection_schema
from ..SimulationEngine.db import DB
from pydantic import ValidationError as PydanticValidationError

class TestCollectionSchema(BaseTestCaseWithErrorHandler):

    def setUp(self):
        DB.connections = {}
        DB.current_conn = None
        DB.current_db = None
        DB.switch_connection("test_conn_schema")

        self.client = DB.connections[DB.current_conn]

        db1 = self.client["db1"]
        
        coll_empty = db1["coll_empty"] # Created, but no docs

        coll_simple = db1["coll_simple"]
        coll_simple.insert_many([
            {'_id': ObjectId("605c72300000000000000000"), 'name': 'Alice', 'age': 30, 'score': 95.5, 'isActive': True, 'meta': None},
            {'_id': ObjectId(), 'name': 'Bob', 'age': 25, 'score': 88.0, 'isActive': False, 'tags': ['dev', 'test']},
            {'_id': ObjectId(), 'name': 'Charlie', 'age': 30, 'score': 95.5, 'isActive': True, 'address': {'street': '123 Main', 'city': 'Anytown'}}
        ])

        coll_types = db1["coll_types"]
        coll_types.insert_many([
            {'_id': ObjectId(), 'field_int': 100},
            {'_id': ObjectId(), 'field_int': 200, 'field_str': 'hello'},
            {'_id': ObjectId(), 'field_str': 'world', 'field_float': 3.14},
            {'_id': ObjectId(), 'field_bool': True, 'field_null': None},
            {'_id': ObjectId(), 'field_date': datetime(2023, 1, 15, 10, 30, 0, tzinfo=timezone.utc)},
            {'_id': ObjectId(), 'field_oid': ObjectId("605c72300000000000000001")},
            {'_id': ObjectId(), 'field_binary': Binary(b'\x01\x02\x03', 0)},
            {'_id': ObjectId(), 'field_array_simple': [1, 2, 3]},
            {'_id': ObjectId(), 'field_array_docs': [{'a':1}, {'b':2}]},
            {'_id': ObjectId(), 'field_doc': {'nested_key': 'value', 'nested_num': 123}},
            {'_id': ObjectId(), 'mixed_field': 123},
            {'_id': ObjectId(), 'mixed_field': "a_string"},
            {'_id': ObjectId(), 'mixed_field': True},
            {'_id': ObjectId(), 'mixed_field': None},
            {'_id': ObjectId("605c72300000000000000002")},
            {'_id': ObjectId()} 
        ])

    def tearDown(self):
        if DB.current_conn and DB.current_conn in DB.connections:
            client_to_clean = DB.connections[DB.current_conn]
            # List of DBs potentially created in setUp
            dbs_to_drop_if_exist = ["db1", "db_for_errors"] 
            for db_name_to_drop in dbs_to_drop_if_exist:
                if db_name_to_drop in client_to_clean.list_database_names():
                    client_to_clean.drop_database(db_name_to_drop)
        
        DB.connections = {}
        DB.current_conn = None
        DB.current_db = None


    def test_empty_collection(self):
        self.assert_error_behavior(
            func_to_call=collection_schema,
            expected_exception_type=custom_errors.CollectionNotFoundError,
            expected_message="Collection 'coll_empty' not found in database 'db1'.",
            database='db1',
            collection='coll_empty'
        )

    def test_collection_with_only_id_document(self):
        self.client["db1"]["only_id_coll"].insert_many([{'_id': ObjectId("605c72300000000000000010")}])
        result = collection_schema('db1', 'only_id_coll')
        expected = {
            'num_documents_sampled': 1,
            'fields': {'_id': {'types_count': {'oid': 1}, 'count': 1, 'type': 'oid', 'prop_in_object': 1.0}}
        }
        self.assertDictEqual(result, expected)

    def test_collection_with_truly_empty_document(self):
        # --- Test with a single empty document ---
        coll_name_single = 'truly_empty_coll'
        db1 = self.client["db1"] # Get db instance from client
        
        # Ensure collection is clean for this specific test run part
        if coll_name_single in db1.list_collection_names():
            db1.drop_collection(coll_name_single)
        
        single_empty_coll = db1[coll_name_single]
        insert_result_single = single_empty_coll.insert_one({}) # Insert one empty document

        result_single = collection_schema('db1', coll_name_single)
        
        expected_single = {
            'num_documents_sampled': 1,
            'fields': {'_id': {'types_count': {'oid': 1}, 'count': 1, 'type': 'oid', 'prop_in_object': 1.0}}
        }
        self.assertDictEqual(result_single, expected_single)
        
        # --- Test with multiple empty documents ---
        coll_name_multiple = 'truly_empty_coll_multiple'
        
        # Ensure collection is clean for this specific test run part
        if coll_name_multiple in db1.list_collection_names():
            db1.drop_collection(coll_name_multiple)

        multiple_empty_coll = db1[coll_name_multiple]
        insert_results_multiple = multiple_empty_coll.insert_many([{}, {}])

        result_multiple = collection_schema('db1', coll_name_multiple)
        
        expected_multiple = {
            'num_documents_sampled': 2,
            'fields': {'_id': {'types_count': {'oid': 2}, 'count': 2, 'type': 'oid', 'prop_in_object': 1.0}}
        }
        self.assertDictEqual(result_multiple, expected_multiple)

    def test_simple_collection_analysis(self):
        result = collection_schema('db1', 'coll_simple')
        
        all_ids = [doc["_id"] for doc in self.client["db1"]["coll_simple"].find({}, {"_id": 1})]
        # 3 documents in coll_simple
        num_docs = 3
        expected = {"fields": {'_id': {'types_count': {'oid': 3}, 'count': 3, 'type': 'oid', 'prop_in_object': 1.0}, 'name': {'types_count': {'string': 3}, 'count': 3, 'type': 'string', 'prop_in_object': 1.0}, 'age': {'types_count': {'integer': 3}, 'count': 3, 'type': 'integer', 'prop_in_object': 1.0}, 'score': {'types_count': {'float': 3}, 'count': 3, 'type': 'float', 'prop_in_object': 1.0}, 'isActive': {'types_count': {'boolean': 3}, 'count': 3, 'type': 'boolean', 'prop_in_object': 1.0}, 'tags': {'types_count': {'ARRAY': 1}, 'count': 1, 'array_types_count': {'string': 2}, 'type': 'ARRAY', 'array_type': 'string', 'prop_in_object': 0.3333}, 'meta': {'types_count': {'null': 1}, 'count': 1, 'type': 'null', 'prop_in_object': 0.3333}, 'address': {'types_count': {'OBJECT': 1}, 'count': 1, 'object': {'street': {'types_count': {'string': 1}, 'count': 1, 'type': 'string', 'prop_in_object': 1.0}, 'city': {'types_count': {'string': 1}, 'count': 1, 'type': 'string', 'prop_in_object': 1.0}}, 'type': 'OBJECT', 'prop_in_object': 0.3333}},
                    "num_documents_sampled": 3}
        self.assertDictEqual(result, expected)

    def test_comprehensive_types_collection(self):
        num_docs = 16 # As per setUp for coll_types

        result = collection_schema('db1', 'coll_types')

        expected = {
            'num_documents_sampled': num_docs,
            'fields': {'_id': {'types_count': {'oid': 16}, 'count': 16, 'type': 'oid', 'prop_in_object': 1.0}, 'field_array_docs': {'types_count': {'ARRAY': 1}, 'count': 1, 'array_types_count': {'OBJECT': 2}, 'object': {'a': {'types_count': {'integer': 1}, 'count': 1, 'type': 'integer', 'prop_in_object': 1.0}, 'b': {'types_count': {'integer': 1}, 'count': 1, 'type': 'integer', 'prop_in_object': 1.0}}, 'type': 'ARRAY', 'array_type': 'OBJECT', 'prop_in_object': 0.0625}, 'field_str': {'types_count': {'string': 2}, 'count': 2, 'type': 'string', 'prop_in_object': 0.125}, 'field_float': {'types_count': {'float': 1}, 'count': 1, 'type': 'float', 'prop_in_object': 0.0625}, 'mixed_field': {'types_count': {'null': 1, 'string': 1, 'boolean': 1, 'integer': 1}, 'count': 4, 'type': 'general_scalar', 'prop_in_object': 0.25}, 'field_oid': {'types_count': {'oid': 1}, 'count': 1, 'type': 'oid', 'prop_in_object': 0.0625}, 'field_binary': {'types_count': {'unknown': 1}, 'count': 1, 'type': 'unknown', 'prop_in_object': 0.0625}, 'field_array_simple': {'types_count': {'ARRAY': 1}, 'count': 1, 'array_types_count': {'integer': 3}, 'type': 'ARRAY', 'array_type': 'integer', 'prop_in_object': 0.0625}, 'field_doc': {'types_count': {'OBJECT': 1}, 'count': 1, 'object': {'nested_key': {'types_count': {'string': 1}, 'count': 1, 'type': 'string', 'prop_in_object': 1.0}, 'nested_num': {'types_count': {'integer': 1}, 'count': 1, 'type': 'integer', 'prop_in_object': 1.0}}, 'type': 'OBJECT', 'prop_in_object': 0.0625}, 'field_date': {'types_count': {'date': 1}, 'count': 1, 'type': 'date', 'prop_in_object': 0.0625}, 'field_int': {'types_count': {'integer': 2}, 'count': 2, 'type': 'integer', 'prop_in_object': 0.125}, 'field_bool': {'types_count': {'boolean': 1}, 'count': 1, 'type': 'boolean', 'prop_in_object': 0.0625}, 'field_null': {'types_count': {'null': 1}, 'count': 1, 'type': 'null', 'prop_in_object': 0.0625}}
        }
        
        self.assertDictEqual(result, expected)

    def test_database_not_found(self):
        self.assert_error_behavior(
            func_to_call=collection_schema,
            expected_exception_type=custom_errors.DatabaseNotFoundError,
            expected_message="Database name 'non_existent_db' is invalid or could not be accessed",
            database='non_existent_db',
            collection='any_coll'
        )

    def test_collection_not_found(self):
        self.assert_error_behavior(
            func_to_call=collection_schema,
            expected_exception_type=custom_errors.CollectionNotFoundError,
            expected_message="Collection 'non_existent_coll' not found in database 'db1'.",
            database='db1',
            collection='non_existent_coll'
        )

    def test_invalid_database_name_empty(self):
        self.assert_error_behavior(
            func_to_call=collection_schema,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character", # Substring for Pydantic
            database='',
            collection='some_coll'
        )

    def test_invalid_database_name_too_long(self):
        long_db_name = 'a' * 64
        self.assert_error_behavior(
            func_to_call=collection_schema,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 63 characters", # Substring
            database=long_db_name,
            collection='some_coll'
        )

    def test_invalid_collection_name_empty(self):
        self.assert_error_behavior(
            func_to_call=collection_schema,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at least 1 character", # Substring
            database='db1',
            collection=''
        )

    def test_invalid_collection_name_too_long(self):
        long_coll_name = 'a' * 256
        self.assert_error_behavior(
            func_to_call=collection_schema,
            expected_exception_type=PydanticValidationError,
            expected_message="String should have at most 255 characters", # Substring
            database='db1',
            collection=long_coll_name
        )

    def test_field_value_is_list_of_mixed_types(self):
        db1 = self.client["db1"]
        coll_name = 'mixed_array_coll'

        # Ensure collection is clean for this test
        if coll_name in db1.list_collection_names():
            db1.drop_collection(coll_name)
        
        mixed_array_coll_instance = db1[coll_name]
        inserted_docs_result = mixed_array_coll_instance.insert_many([
            {'tags': [1, "two", True, None, {"sub": "doc"}, [10, 20]]}
        ])

        result = collection_schema('db1', coll_name)
        
        expected = {
            'num_documents_sampled': 1,
            'fields': {'tags': {'types_count': {'ARRAY': 1}, 'count': 1, 'array_types_count': {'integer': 1, 'string': 1, 'boolean': 1, 'null': 1, 'OBJECT': 1, 'ARRAY': 1}, 'object': {'sub': {'types_count': {'string': 1}, 'count': 1, 'type': 'string', 'prop_in_object': 1.0}}, 'type': 'ARRAY', 'array_type': 'mixed_scalar_object', 'prop_in_object': 1.0}, '_id': {'types_count': {'oid': 1}, 'count': 1, 'type': 'oid', 'prop_in_object': 1.0}}
        }

        self.assertDictEqual(result, expected)

    def test_field_value_is_datetime_with_timezone(self):
        dt_aware = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        inserted = self.client['db1']['datetime_aware_coll'].insert_one({'event_time': dt_aware})
        inserted_id = inserted.inserted_id
        result = collection_schema('db1', 'datetime_aware_coll')
        expected_dt_naive_utc = dt_aware.replace(tzinfo=None) 

        expected = {
            'num_documents_sampled': 1,
            'fields': {'event_time': {'types_count': {'date': 1}, 'count': 1, 'type': 'date', 'prop_in_object': 1.0}, '_id': {'types_count': {'oid': 1}, 'count': 1, 'type': 'oid', 'prop_in_object': 1.0}}
        }
        self.assertDictEqual(result, expected)

    def test_field_only_null(self):
        insert_result = self.client['db1']['only_null_field_coll'].insert_one({'optional_field': None})
        inserted_id = insert_result.inserted_id 

        result = collection_schema('db1', 'only_null_field_coll')
        expected = {
            'num_documents_sampled': 1,
            'fields': {'optional_field': {'types_count': {'null': 1}, 'count': 1, 'type': 'null', 'prop_in_object': 1.0}, '_id': {'types_count': {'oid': 1}, 'count': 1, 'type': 'oid', 'prop_in_object': 1.0}}
        }
        self.assertDictEqual(result, expected)


if __name__ == '__main__':
    unittest.main()