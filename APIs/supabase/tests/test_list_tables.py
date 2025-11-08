import unittest
import copy
from datetime import datetime

from ..SimulationEngine import custom_errors, utils
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..database import list_tables


class TestListTables(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.fixed_time = datetime(2023, 10, 26, 10, 0, 0)

        self.proj1_id = "project_alpha_tables"
        self.proj2_id = "project_beta_no_db_entry"
        self.proj3_id = "project_gamma_empty_tables_list"
        self.proj4_id = "project_delta_minimal_table"

        DB["projects"] = [
            {"id": self.proj1_id, "name": "Project Alpha", "organization_id": "org1", "region": "us-east-1", "status": "ACTIVE_HEALTHY", "created_at": self.fixed_time},
            {"id": self.proj2_id, "name": "Project Beta", "organization_id": "org1", "region": "us-west-1", "status": "ACTIVE_HEALTHY", "created_at": self.fixed_time},
            {"id": self.proj3_id, "name": "Project Gamma", "organization_id": "org1", "region": "eu-central-1", "status": "ACTIVE_HEALTHY", "created_at": self.fixed_time},
            {"id": self.proj4_id, "name": "Project Delta", "organization_id": "org1", "region": "ap-south-1", "status": "ACTIVE_HEALTHY", "created_at": self.fixed_time},
        ]

        self.table1_proj1_public_users = {
            "name": "users",
            "schema": "public",
            "comment": "User information table",
            "columns": [
                {"name": "id", "data_type": "uuid", "is_nullable": False, "default_value": "gen_random_uuid()"},
                {"name": "username", "data_type": "text", "is_nullable": False, "default_value": None}
            ],
            "primary_keys": [{"name": "id"}],
            "relationships": []
        }
        self.table2_proj1_private_orders = {
            "name": "orders",
            "schema": "private_schema",
            "comment": None, # Test optional field being None
            "columns": [
                {"name": "order_id", "data_type": "integer", "is_nullable": False},
                {"name": "user_id", "data_type": "uuid", "is_nullable": False},
                {"name": "item_count", "data_type": "integer", "is_nullable": True, "default_value": "1"}
            ],
            "primary_keys": [{"name": "order_id"}],
            "relationships": [
                {
                    "constraint_name": "fk_orders_user_id",
                    "source_schema": "private_schema",
                    "source_table_name": "orders",
                    "source_column_name": "user_id",
                    "target_table_schema": "public",
                    "target_table_name": "users",
                    "target_column_name": "id"
                }
            ]
        }
        self.table3_proj1_public_products = {
            "name": "products",
            "schema": "public",
            "comment": "Product catalog",
            "columns": [{"name": "product_id", "data_type": "serial", "is_nullable": False}],
            "primary_keys": [{"name": "product_id"}],
            "relationships": []
        }
        
        self.table_minimal_proj4 = {
            "name": "config",
            "schema": "system",
            # comment, columns, primary_keys, relationships are missing in source data
        }


        DB["tables"] = {
            self.proj1_id: [
                copy.deepcopy(self.table1_proj1_public_users),
                copy.deepcopy(self.table2_proj1_private_orders),
                copy.deepcopy(self.table3_proj1_public_products)
            ],
            # self.proj2_id has no entry in DB["tables"]
            self.proj3_id: [], # Project Gamma has an entry but an empty list of tables
            self.proj4_id: [copy.deepcopy(self.table_minimal_proj4)]
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_table_structure(self, table_dict):
        self.assertIn("name", table_dict)
        self.assertIsInstance(table_dict["name"], str)
        self.assertIn("schema", table_dict) # Asserting 'schema', not 'schema'
        self.assertIsInstance(table_dict["schema"], str)
        self.assertIn("comment", table_dict) # Can be str or None
        self.assertIn("columns", table_dict)
        self.assertIsInstance(table_dict["columns"], list)
        for col in table_dict["columns"]:
            self.assertIsInstance(col, dict)
            self.assertIn("name", col)
            self.assertIn("data_type", col)
            self.assertIn("is_nullable", col)
            self.assertIn("default_value", col) # Can be str or None
        self.assertIn("primary_keys", table_dict)
        self.assertIsInstance(table_dict["primary_keys"], list)
        for pk in table_dict["primary_keys"]:
            self.assertIsInstance(pk, dict)
            self.assertIn("name", pk)
        self.assertIn("relationships", table_dict)
        self.assertIsInstance(table_dict["relationships"], list)
        for rel in table_dict["relationships"]:
            self.assertIsInstance(rel, dict)
            self.assertIn("constraint_name", rel)
            self.assertIn("source_schema", rel)

    def test_list_tables_success_no_schema_filter(self):
        tables = list_tables(project_id=self.proj1_id)
        self.assertEqual(len(tables), 3)
        for table in tables:
            self._assert_table_structure(table)
        
        # Check specific table details and schema transformation
        user_table_data = next(t for t in tables if t["name"] == "users")
        self.assertEqual(user_table_data["schema"], "public") # Check transformed key
        self.assertEqual(user_table_data["comment"], self.table1_proj1_public_users["comment"])
        self.assertEqual(len(user_table_data["columns"]), len(self.table1_proj1_public_users["columns"]))

        orders_table_data = next(t for t in tables if t["name"] == "orders")
        self.assertEqual(orders_table_data["schema"], "private_schema")
        self.assertIsNone(orders_table_data["comment"]) # Was None in source
        self.assertEqual(len(orders_table_data["relationships"]), 1)


    def test_list_tables_success_with_single_schema_filter(self):
        tables = list_tables(project_id=self.proj1_id, schemas=["public"])
        self.assertEqual(len(tables), 2)
        for table in tables:
            self._assert_table_structure(table)
            self.assertEqual(table["schema"], "public")
        table_names = {t["name"] for t in tables}
        self.assertIn("users", table_names)
        self.assertIn("products", table_names)

    def test_list_tables_success_with_multiple_schema_filter(self):
        tables = list_tables(project_id=self.proj1_id, schemas=["public", "private_schema"])
        self.assertEqual(len(tables), 3) # All tables from proj1
        for table in tables:
            self._assert_table_structure(table)
        schemas_found = {t["schema"] for t in tables}
        self.assertIn("public", schemas_found)
        self.assertIn("private_schema", schemas_found)

    def test_list_tables_success_with_schema_filter_no_match(self):
        tables = list_tables(project_id=self.proj1_id, schemas=["non_existent_schema"])
        self.assertEqual(len(tables), 0)

    def test_list_tables_success_empty_schema_list_filter(self):
        tables = list_tables(project_id=self.proj1_id, schemas=[])
        self.assertEqual(len(tables), 0)

    def test_list_tables_success_project_with_no_tables_in_db_tables_key(self):
        # proj2_id exists in DB["projects"] but not as a key in DB["tables"]
        tables = list_tables(project_id=self.proj2_id)
        self.assertEqual(len(tables), 0)

    def test_list_tables_success_project_with_empty_table_list_in_db_tables(self):
        # proj3_id exists in DB["projects"] and DB["tables"][self.proj3_id] is []
        tables = list_tables(project_id=self.proj3_id)
        self.assertEqual(len(tables), 0)

    def test_list_tables_success_minimal_table_data_populates_defaults(self):
        # Tests if a table with minimal data in DB results in a full structure output
        # (comment: None, columns: [], primary_keys: [], relationships: [])
        tables = list_tables(project_id=self.proj4_id)
        self.assertEqual(len(tables), 1)
        minimal_table_output = tables[0]
        self._assert_table_structure(minimal_table_output)

        self.assertEqual(minimal_table_output["name"], self.table_minimal_proj4["name"])
        self.assertEqual(minimal_table_output["schema"], self.table_minimal_proj4["schema"]) # Transformed
        self.assertIsNone(minimal_table_output["comment"])
        self.assertEqual(minimal_table_output["columns"], [])
        self.assertEqual(minimal_table_output["primary_keys"], [])
        self.assertEqual(minimal_table_output["relationships"], [])

    def test_list_tables_error_project_not_found(self):
        self.assert_error_behavior(
            func_to_call=list_tables,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Project with ID 'non_existent_project' not found.", # Example message
            project_id="non_existent_project"
        )

    def test_list_tables_error_invalid_project_id_type(self):
        # Assuming the function or a framework wrapper validates input types
        # and raises custom_errors.ValidationError for type mismatches.
        self.assert_error_behavior(
            func_to_call=list_tables,
            expected_exception_type=custom_errors.ValidationError,
            # Message might depend on how Pydantic error is translated
            expected_message="Input validation failed: project_id must be a string.", 
            project_id=12345 
        )

    def test_list_tables_error_invalid_schemas_type_not_list(self):
        self.assert_error_behavior(
            func_to_call=list_tables,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: schemas must be a list of strings or None.",
            project_id=self.proj1_id,
            schemas="not_a_list" 
        )

    def test_list_tables_error_invalid_schemas_element_type_not_string(self):
        self.assert_error_behavior(
            func_to_call=list_tables,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: all elements in schemas list must be strings.",
            project_id=self.proj1_id,
            schemas=["public", 123, "private_schema"]
        )
    

    def test_list_tables_all_fields_present_in_output(self):
        # Check a complex table to ensure all documented fields are there
        tables = list_tables(project_id=self.proj1_id, schemas=["private_schema"])
        self.assertEqual(len(tables), 1)
        orders_table = tables[0]
        
        self.assertEqual(orders_table["name"], self.table2_proj1_private_orders["name"])
        self.assertEqual(orders_table["schema"], self.table2_proj1_private_orders["schema"])
        self.assertIsNone(orders_table["comment"]) # Was None in source
        
        self.assertEqual(len(orders_table["columns"]), len(self.table2_proj1_private_orders["columns"]))
        # Deep check one column
        db_user_id_col = next(c for c in self.table2_proj1_private_orders["columns"] if c["name"] == "user_id")
        out_user_id_col = next(c for c in orders_table["columns"] if c["name"] == "user_id")
        self.assertEqual(out_user_id_col["data_type"], db_user_id_col["data_type"])
        self.assertEqual(out_user_id_col["is_nullable"], db_user_id_col["is_nullable"])
        self.assertIsNone(out_user_id_col["default_value"]) # Assuming default_value not set for user_id

        self.assertEqual(len(orders_table["primary_keys"]), len(self.table2_proj1_private_orders["primary_keys"]))
        self.assertEqual(orders_table["primary_keys"][0]["name"], self.table2_proj1_private_orders["primary_keys"][0]["name"])

        self.assertEqual(len(orders_table["relationships"]), len(self.table2_proj1_private_orders["relationships"]))
        # Deep check one relationship
        db_rel = self.table2_proj1_private_orders["relationships"][0]
        out_rel = orders_table["relationships"][0]
        self.assertEqual(out_rel["constraint_name"], db_rel["constraint_name"])
        self.assertEqual(out_rel["source_schema"], db_rel["source_schema"])
        self.assertEqual(out_rel["source_table_name"], db_rel["source_table_name"])
        self.assertEqual(out_rel["source_column_name"], db_rel["source_column_name"])
        self.assertEqual(out_rel["target_table_schema"], db_rel["target_table_schema"])
        self.assertEqual(out_rel["target_table_name"], db_rel["target_table_name"])
        self.assertEqual(out_rel["target_column_name"], db_rel["target_column_name"])

if __name__ == '__main__':
    unittest.main()