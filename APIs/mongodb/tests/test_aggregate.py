import unittest
import copy
# from datetime import datetime # Not strictly needed for these specific tests
from ..SimulationEngine import custom_errors
from ..data_operations import aggregate
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from pydantic import ValidationError


class TestAggregateFunction(BaseTestCaseWithErrorHandler):
    def setUp(self):
        DB.connections = {}
        DB.current_conn = None
        DB.current_db = None
        connection_name = "test_agg_conn"
        DB.switch_connection(connection_name) 
        if DB.current_conn not in DB.connections:
            # This should not happen if switch_connection worked, but good to be defensive
            raise Exception(f"Connection '{DB.current_conn}' not established in setUp.")
        
        # 'self.client' will be the mongomock.MongoClient instance
        self.client = DB.connections[DB.current_conn]

        # --- Setup for "test_db" within self.client ---
        self.db_test = self.client["sales_db"] 
        
        orders_collection = self.db_test["orders"] # Get/create 'orders' collection
        orders_collection.insert_many([
            {"_id": 1, "item": "apple", "price": 1.0, "quantity": 10, "customer_id": "C1"},
            {"_id": 2, "item": "banana", "price": 0.5, "quantity": 20, "customer_id": "C2"},
            {"_id": 3, "item": "apple", "price": 1.0, "quantity": 5, "customer_id": "C1"},
            {"_id": 4, "item": "orange", "price": 0.75, "quantity": 15, "customer_id": "C3"},
            {"_id": 5, "item": "banana", "price": 0.5, "quantity": 10, "customer_id": "C1"},
        ])
        
        # To create an empty collection that will be listed by list_collection_names():
        self.db_test.create_collection("empty_collection")

        customers_collection = self.db_test["customers"]
        customers_collection.insert_many([
            {"_id": "C1", "name": "Customer Alpha"},
            {"_id": "C2", "name": "Customer Beta"},
            {"_id": "C3", "name": "Customer Gamma"},
        ])
        
        # --- Setup for "inventory_db" within self.client ---
        db_inventory = self.client["inventory_db"] # Get/create 'inventory_db'
        
        products_collection = db_inventory["products"]
        products_collection.insert_many([
            {"_id": "P1", "name": "Product A", "stock": 100},
            {"_id": "P2", "name": "Product B", "stock": 0},
        ])

        # --- Setup for "db_for_errors" within self.client ---
        db_for_errors = self.client["db_for_errors"] # Get/create 'db_for_errors'
        
        errors_collection = db_for_errors["collection_for_errors"]
        errors_collection.insert_many([
            {"_id": 1, "value_field": "not_a_number", "another_value": 10}
        ])


    def tearDown(self):
        pass

    # --- Success Cases ---
    def test_aggregate_match_stage(self):
        pipeline = [{"$match": {"item": "apple"}}]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        self.assertEqual(len(result), 2)
        result_ids = sorted([doc["_id"] for doc in result])
        self.assertEqual(result_ids, [1, 3])
        for doc in result:
            self.assertEqual(doc["item"], "apple")

    def test_aggregate_group_sum_avg_stage(self):
        pipeline = [
            {"$group": {
                "_id": "$item",
                "total_quantity": {"$sum": "$quantity"},
                "average_price": {"$avg": "$price"}
            }},
            {"$sort": {"_id": 1}}
        ]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        expected_results = [
            {"_id": "apple", "total_quantity": 15, "average_price": 1.0},
            {"_id": "banana", "total_quantity": 30, "average_price": 0.5},
            {"_id": "orange", "total_quantity": 15, "average_price": 0.75},
        ]
        self.assertEqual(len(result), len(expected_results))
        for res_doc, exp_doc in zip(result, expected_results):
            self.assertEqual(res_doc["_id"], exp_doc["_id"])
            self.assertEqual(res_doc["total_quantity"], exp_doc["total_quantity"])
            self.assertAlmostEqual(res_doc["average_price"], exp_doc["average_price"], places=2)


    def test_aggregate_project_stage(self):
        pipeline = [
            {"$match": {"item": "orange"}},
            {"$project": {"_id": 0, "product_name": "$item", "total_value": {"$multiply": ["$price", "$quantity"]}}}
        ]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {"product_name": "orange", "total_value": 0.75 * 15})

    def test_aggregate_multiple_stages_match_group_sort(self):
        pipeline = [
            {"$match": {"customer_id": "C1"}},
            {"$group": {"_id": "$item", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        expected_results = [
            {"_id": "apple", "count": 2},
            {"_id": "banana", "count": 1}
        ]
        self.assertEqual(result, expected_results)

    def test_aggregate_empty_collection_returns_empty_list(self):
        pipeline = [{"$match": {"item": "anything"}}]
        result = aggregate(database="sales_db", collection="empty_collection", pipeline=pipeline)
        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])

    def test_aggregate_no_matching_documents_returns_empty_list(self):
        pipeline = [{"$match": {"item": "grape"}}] 
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])

    def test_aggregate_complex_result_structure(self):
        self.db_test["orders"].insert_one(
            {"_id": 7, "item": "apple", "price": 1.2, "quantity": 3, "customer_id": "C2", "tags": ["organic", "fresh"]}
        )
        pipeline = [
            {"$match": {"tags": "organic"}},
            {"$project": {
                "_id": 0,
                "itemName": "$item",
                "saleDetails": {
                    "pricePerUnit": "$price",
                    "unitsSold": "$quantity",
                    "customerId": "$customer_id"
                }
            }}
        ]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        self.assertEqual(len(result), 1)
        expected_doc = {
            "itemName": "apple",
            "saleDetails": {
                "pricePerUnit": 1.2,
                "unitsSold": 3,
                "customerId": "C2"
            }
        }
        self.assertEqual(result[0], expected_doc)

    def test_aggregate_with_lookup_unwind_project_sort(self):
        pipeline = [
            {"$match": {"item": "banana"}},
            {"$lookup": {
                "from": "customers",
                "localField": "customer_id",
                "foreignField": "_id",
                "as": "customer_info"
            }},
            {"$unwind": "$customer_info"},
            {"$project": {
                "_id": 0,
                "item": 1,
                "customerName": "$customer_info.name"
            }},
            {"$sort": {"customerName": 1}}
        ]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        expected_results = [
            {"item": "banana", "customerName": "Customer Alpha"},
            {"item": "banana", "customerName": "Customer Beta"},
        ]
        self.assertEqual(result, expected_results)

    def test_aggregate_lookup_to_non_existent_foreign_collection(self):
        pipeline = [
            {"$lookup": {
                "from": "non_existent_foreign_collection",
                "localField": "customer_id",
                "foreignField": "_id",
                "as": "customer_data"
            }}
        ]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        self.assertEqual(len(result), 5)
        for doc in result:
            self.assertIn("customer_data", doc)
            self.assertEqual(doc["customer_data"], [])

    def test_aggregate_on_different_database_and_collection(self):
        pipeline = [
            {"$match": {"stock": {"$gt": 0}}},
            {"$project": {"_id": 0, "productName": "$name"}}
        ]
        result = aggregate(database="inventory_db", collection="products", pipeline=pipeline)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {"productName": "Product A"})

    def test_aggregate_sort_stage_explicitly(self):
        pipeline = [{"$sort": {"price": -1, "quantity": 1}}]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        expected_ids_ordered = [3, 1, 4, 5, 2]
        result_ids_ordered = [doc["_id"] for doc in result]
        self.assertEqual(result_ids_ordered, expected_ids_ordered)

    def test_aggregate_limit_stage(self):
        pipeline = [{"$sort": {"_id": 1}}, {"$limit": 2}]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["_id"], 1)
        self.assertEqual(result[1]["_id"], 2)

    def test_aggregate_skip_stage(self):
        pipeline = [{"$sort": {"_id": 1}}, {"$skip": 3}]
        result = aggregate(database="sales_db", collection="orders", pipeline=pipeline)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["_id"], 4)
        self.assertEqual(result[1]["_id"], 5)

    # --- Error Cases ---

    # ValidationError
    def test_aggregate_invalid_database_name_type(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=ValidationError,
            expected_message="database", 
            database=123, collection="orders", pipeline=[{"$match": {}}]
        )

    def test_aggregate_empty_database_name_string(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=ValidationError,
            expected_message="database",
            database="", collection="orders", pipeline=[{"$match": {}}]
        )

    def test_aggregate_invalid_collection_name_type(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=ValidationError,
            expected_message="collection",
            database="sales_db", collection=123, pipeline=[{"$match": {}}]
        )

    def test_aggregate_empty_collection_name_string(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=ValidationError,
            expected_message="collection",
            database="sales_db", collection="", pipeline=[{"$match": {}}]
        )

    def test_aggregate_invalid_pipeline_argument_type(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=ValidationError,
            expected_message="pipeline",
            database="sales_db", collection="orders", pipeline="not_a_list"
        )

    def test_aggregate_empty_pipeline_list(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=ValidationError,
            expected_message="pipeline",
            database="sales_db", collection="orders", pipeline=[]
        )

    def test_aggregate_pipeline_with_non_dict_element(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=ValidationError,
            expected_message="pipeline",
            database="sales_db", collection="orders", pipeline=[{"$match": {}}, "not_a_dict"]
        )

    # InvalidPipelineError
    def test_aggregate_invalid_pipeline_stage_operator_unknown(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=custom_errors.InvalidPipelineError,
            expected_message="Invalid aggregation pipeline: $invalidStage is not a valid operator for the aggregation pipeline. See http://docs.mongodb.org/manual/meta/aggregation-quick-reference/ for a complete list of valid operators.", 
            database="sales_db", collection="orders", pipeline=[{"$invalidStage": {}}]
        )

    def test_aggregate_malformed_pipeline_stage_value_type(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=custom_errors.AggregationError,
            expected_message="Aggregation failed during execution: the match filter must be an expression in an object",
            database="sales_db", collection="orders", pipeline=[{"$match": "not_a_dict"}]
        )


    def test_aggregate_pipeline_stage_key_not_an_operator(self):
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=custom_errors.InvalidPipelineError,
            expected_message="Invalid aggregation pipeline: not_an_operator is not a valid operator for the aggregation pipeline. See http://docs.mongodb.org/manual/meta/aggregation-quick-reference/ for a complete list of valid operators.",
            database="sales_db", collection="orders", pipeline=[{"not_an_operator": "value"}]
        )

    # AggregationError
    def test_aggregate_aggregation_error_due_to_type_mismatch(self):
        pipeline = [
            {"$match": {"_id": 1}},
            {"$project": {"total": {"$multiply": ["$value_field", "$another_value"]}}} # "not_a_number" * 10
        ]
        self.assert_error_behavior(
            func_to_call=aggregate,
            expected_exception_type=custom_errors.AggregationError,
            expected_message="Aggregation failed during execution: $multiply only uses numbers", 
            database="db_for_errors", collection="collection_for_errors", pipeline=pipeline
        )

if __name__ == '__main__':
    unittest.main()