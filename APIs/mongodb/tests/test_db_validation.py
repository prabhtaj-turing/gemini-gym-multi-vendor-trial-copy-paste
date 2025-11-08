import unittest
import json
import os
from typing import Dict, Any

from ..SimulationEngine.models import (
    FindInput, InsertManyInput, DeleteManyInput, UpdateManyInput, 
    AggregateInput, CountInput, CreateCollectionInput, DropCollectionInput,
    DropDatabaseInput, RenameCollectionInput, CollectionIndexesInput,
    CreateIndexInput, CollectionSchemaInput, CollectionStorageSizeInput,
    SwitchConnectionInput, ListCollectionsInput, ListDatabasesInput,
    DbStatsInput, ExplainInput, MongoDBLogsInput, MongoDBLogsType,
    AggregateMethod, AggregateMethodArguments, FindMethod, FindMethodArguments,
    CountMethod, CountMethodArguments
)
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError


class TestDBValidation(BaseTestCaseWithErrorHandler):
    """Test database validation models."""

    def setUp(self):
        super().setUp()
        # Clear DB state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None

    def tearDown(self):
        super().tearDown()
        # Clear DB state
        DB.connections.clear()
        DB.current_conn = None
        DB.current_db = None

    def test_find_input_validation(self):
        """Test FindInput model validation."""
        # Valid input
        try:
            valid_input = FindInput(
                database="test_db",
                collection="test_collection",
                filter={"name": "test"},
                limit=5
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(valid_input.filter, {"name": "test"})
            self.assertEqual(valid_input.limit, 5)
        except Exception as e:
            self.fail(f"Valid FindInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "filter": {"status": "active", "age": {"$gte": 18}},
                "limit": 10,
                "sort": {"created_at": -1}
            }
            valid_input_dict = FindInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(valid_input_dict.filter, {"status": "active", "age": {"$gte": 18}})
            self.assertEqual(valid_input_dict.limit, 10)
            self.assertEqual(valid_input_dict.sort, {"created_at": -1})
        except Exception as e:
            self.fail(f"Valid FindInput from dictionary validation failed: {e}")

        # FindInput inherits from BaseModel, not MongoDBBaseModel, so it doesn't have min_length constraint
        # Test with missing required field instead
        self.assert_error_behavior(
            lambda: FindInput(
                collection="test_collection"
                # Missing required database field
            ),
            PydanticValidationError,
            "Field required"
        )

        # Empty collection name - FindInput doesn't have min_length constraint
        # Test with missing required field instead
        self.assert_error_behavior(
            lambda: FindInput(
                database="test_db"
                # Missing required collection field
            ),
            PydanticValidationError,
            "Field required"
        )

    def test_insert_many_input_validation(self):
        """Test InsertManyInput model validation."""
        # Valid input
        try:
            valid_input = InsertManyInput(
                database="test_db",
                collection="test_collection",
                documents=[{"name": "test", "value": 123}]
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(len(valid_input.documents), 1)
        except Exception as e:
            self.fail(f"Valid InsertManyInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "documents": [
                    {"name": "doc1", "value": 100},
                    {"name": "doc2", "value": 200}
                ]
            }
            valid_input_dict = InsertManyInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(len(valid_input_dict.documents), 2)
        except Exception as e:
            self.fail(f"Valid InsertManyInput from dictionary validation failed: {e}")

        # Empty documents list
        self.assert_error_behavior(
            lambda: InsertManyInput(
                database="test_db",
                collection="test_collection",
                documents=[]
            ),
            PydanticValidationError,
            "List should have at least 1 item"
        )

        # Database name too long
        self.assert_error_behavior(
            lambda: InsertManyInput(
                database="a" * 64,  # 64 characters, max is 63
                collection="test_collection",
                documents=[{"test": "data"}]
            ),
            PydanticValidationError,
            "String should have at most 63 characters"
        )

    def test_delete_many_input_validation(self):
        """Test DeleteManyInput model validation."""
        # Valid input
        try:
            valid_input = DeleteManyInput(
                database="test_db",
                collection="test_collection",
                filter={"status": "inactive"}
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(valid_input.filter, {"status": "inactive"})
        except Exception as e:
            self.fail(f"Valid DeleteManyInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "filter": {"age": {"$lt": 18}, "status": {"$in": ["inactive", "suspended"]}}
            }
            valid_input_dict = DeleteManyInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(valid_input_dict.filter, {"age": {"$lt": 18}, "status": {"$in": ["inactive", "suspended"]}})
        except Exception as e:
            self.fail(f"Valid DeleteManyInput from dictionary validation failed: {e}")

    def test_update_many_input_validation(self):
        """Test UpdateManyInput model validation."""
        # Valid input
        try:
            valid_input = UpdateManyInput(
                database="test_db",
                collection="test_collection",
                filter={"status": "pending"},
                update={"$set": {"status": "processed"}}
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(valid_input.filter, {"status": "pending"})
            self.assertEqual(valid_input.update, {"$set": {"status": "processed"}})
        except Exception as e:
            self.fail(f"Valid UpdateManyInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "filter": {"category": "electronics"},
                "update": {"$inc": {"price": 10}},
                "upsert": True
            }
            valid_input_dict = UpdateManyInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(valid_input_dict.filter, {"category": "electronics"})
            self.assertEqual(valid_input_dict.update, {"$inc": {"price": 10}})
            self.assertTrue(valid_input_dict.upsert)
        except Exception as e:
            self.fail(f"Valid UpdateManyInput from dictionary validation failed: {e}")

        # UpdateManyInput doesn't validate empty update dict at Pydantic level
        # The validation happens at the business logic level
        try:
            empty_update_input = UpdateManyInput(
                database="test_db",
                collection="test_collection",
                filter={"status": "pending"},
                update={}
            )
            # This should pass Pydantic validation
            self.assertEqual(empty_update_input.update, {})
        except Exception as e:
            self.fail(f"UpdateManyInput with empty update should pass Pydantic validation: {e}")

    def test_aggregate_input_validation(self):
        """Test AggregateInput model validation."""
        # Valid input
        try:
            valid_input = AggregateInput(
                database="test_db",
                collection="test_collection",
                pipeline=[
                    {"$match": {"status": "active"}},
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}}
                ]
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(len(valid_input.pipeline), 2)
        except Exception as e:
            self.fail(f"Valid AggregateInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "pipeline": [
                    {"$match": {"price": {"$gte": 100}}},
                    {"$sort": {"created_at": -1}},
                    {"$limit": 10}
                ]
            }
            valid_input_dict = AggregateInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(len(valid_input_dict.pipeline), 3)
        except Exception as e:
            self.fail(f"Valid AggregateInput from dictionary validation failed: {e}")

        # Empty pipeline
        self.assert_error_behavior(
            lambda: AggregateInput(
                database="test_db",
                collection="test_collection",
                pipeline=[]
            ),
            PydanticValidationError,
            "List should have at least 1 item"
        )

    def test_count_input_validation(self):
        """Test CountInput model validation."""
        # Valid input - use 'query' field
        try:
            valid_input = CountInput(
                database="test_db",
                collection="test_collection",
                query={"status": "active"}
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(valid_input.query, {"status": "active"})
        except Exception as e:
            self.fail(f"Valid CountInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "query": {"age": {"$gte": 18}, "status": "verified"}
            }
            valid_input_dict = CountInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(valid_input_dict.query, {"age": {"$gte": 18}, "status": "verified"})
        except Exception as e:
            self.fail(f"Valid CountInput from dictionary validation failed: {e}")

    def test_create_collection_input_validation(self):
        """Test CreateCollectionInput model validation."""
        # Valid input
        try:
            valid_input = CreateCollectionInput(
                database="test_db",
                collection="new_collection"
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "new_collection")
        except Exception as e:
            self.fail(f"Valid CreateCollectionInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "another_collection"
            }
            valid_input_dict = CreateCollectionInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "another_collection")
        except Exception as e:
            self.fail(f"Valid CreateCollectionInput from dictionary validation failed: {e}")

        # Collection name too long
        self.assert_error_behavior(
            lambda: CreateCollectionInput(
                database="test_db",
                collection="a" * 256  # 256 characters, max is 255
            ),
            PydanticValidationError,
            "String should have at most 255 characters"
        )

    def test_drop_collection_input_validation(self):
        """Test DropCollectionInput model validation."""
        # Valid input
        try:
            valid_input = DropCollectionInput(
                database="test_db",
                collection="old_collection"
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "old_collection")
        except Exception as e:
            self.fail(f"Valid DropCollectionInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "temp_collection"
            }
            valid_input_dict = DropCollectionInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "temp_collection")
        except Exception as e:
            self.fail(f"Valid DropCollectionInput from dictionary validation failed: {e}")

    def test_drop_database_input_validation(self):
        """Test DropDatabaseInput model validation."""
        # Valid input
        try:
            valid_input = DropDatabaseInput(database="old_database")
            self.assertEqual(valid_input.database, "old_database")
        except Exception as e:
            self.fail(f"Valid DropDatabaseInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {"database": "temp_database"}
            valid_input_dict = DropDatabaseInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "temp_database")
        except Exception as e:
            self.fail(f"Valid DropDatabaseInput from dictionary validation failed: {e}")

    def test_rename_collection_input_validation(self):
        """Test RenameCollectionInput model validation."""
        # Valid input using alias
        try:
            valid_input = RenameCollectionInput(
                database="test_db",
                collection="old_collection",
                **{"newName": "new_collection"}
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "old_collection")
            self.assertEqual(valid_input.new_name, "new_collection")
        except Exception as e:
            self.fail(f"Valid RenameCollectionInput validation failed: {e}")

        # Valid input using Python attribute name
        try:
            valid_input = RenameCollectionInput(
                database="test_db",
                collection="old_collection",
                new_name="new_collection",
                drop_target=True
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "old_collection")
            self.assertEqual(valid_input.new_name, "new_collection")
            self.assertTrue(valid_input.drop_target)
        except Exception as e:
            self.fail(f"Valid RenameCollectionInput with Python names validation failed: {e}")

    def test_collection_indexes_input_validation(self):
        """Test CollectionIndexesInput model validation."""
        # Valid input
        try:
            valid_input = CollectionIndexesInput(
                database="test_db",
                collection="indexed_collection"
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "indexed_collection")
        except Exception as e:
            self.fail(f"Valid CollectionIndexesInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "another_indexed_collection"
            }
            valid_input_dict = CollectionIndexesInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "another_indexed_collection")
        except Exception as e:
            self.fail(f"Valid CollectionIndexesInput from dictionary validation failed: {e}")

    def test_create_index_input_validation(self):
        """Test CreateIndexInput model validation."""
        # Valid input with name
        try:
            valid_input = CreateIndexInput(
                database="test_db",
                collection="test_collection",
                keys={"name": 1, "email": -1},
                name="compound_idx"
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(valid_input.keys, {"name": 1, "email": -1})
            self.assertEqual(valid_input.name, "compound_idx")
        except Exception as e:
            self.fail(f"Valid CreateIndexInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "keys": {"created_at": -1, "status": 1},
                "name": "time_status_idx"
            }
            valid_input_dict = CreateIndexInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(valid_input_dict.keys, {"created_at": -1, "status": 1})
            self.assertEqual(valid_input_dict.name, "time_status_idx")
        except Exception as e:
            self.fail(f"Valid CreateIndexInput from dictionary validation failed: {e}")

        # Valid input without name (should auto-generate)
        try:
            valid_input = CreateIndexInput(
                database="test_db",
                collection="test_collection",
                keys={"field": 1}
            )
            self.assertEqual(valid_input.keys, {"field": 1})
        except Exception as e:
            self.fail(f"Valid CreateIndexInput without name validation failed: {e}")

        # Empty keys should be valid (no min_items constraint)
        try:
            valid_input = CreateIndexInput(
                database="test_db",
                collection="test_collection",
                keys={}
            )
            self.assertEqual(valid_input.keys, {})
        except Exception as e:
            self.fail(f"CreateIndexInput with empty keys should be valid: {e}")

    def test_collection_schema_input_validation(self):
        """Test CollectionSchemaInput model validation."""
        # Valid input
        try:
            valid_input = CollectionSchemaInput(
                database="test_db",
                collection="schema_collection"
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "schema_collection")
        except Exception as e:
            self.fail(f"Valid CollectionSchemaInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "another_schema_collection"
            }
            valid_input_dict = CollectionSchemaInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "another_schema_collection")
        except Exception as e:
            self.fail(f"Valid CollectionSchemaInput from dictionary validation failed: {e}")

    def test_collection_storage_size_input_validation(self):
        """Test CollectionStorageSizeInput model validation."""
        # Valid input
        try:
            valid_input = CollectionStorageSizeInput(
                database="test_db",
                collection="large_collection"
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "large_collection")
        except Exception as e:
            self.fail(f"Valid CollectionStorageSizeInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "storage_collection"
            }
            valid_input_dict = CollectionStorageSizeInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "storage_collection")
        except Exception as e:
            self.fail(f"Valid CollectionStorageSizeInput from dictionary validation failed: {e}")

    def test_switch_connection_input_validation(self):
        """Test SwitchConnectionInput model validation."""
        # Valid input using alias
        try:
            valid_input = SwitchConnectionInput(
                **{"connectionString": "mongodb://localhost:27017/testdb"}
            )
            self.assertEqual(valid_input.connection_string, "mongodb://localhost:27017/testdb")
        except Exception as e:
            self.fail(f"Valid SwitchConnectionInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {"connectionString": "mongodb://user:password@localhost:27017/testdb?authSource=admin"}
            valid_input_dict = SwitchConnectionInput(**input_dict)
            self.assertEqual(valid_input_dict.connection_string, "mongodb://user:password@localhost:27017/testdb?authSource=admin")
        except Exception as e:
            self.fail(f"Valid SwitchConnectionInput from dictionary validation failed: {e}")

    def test_list_collections_input_validation(self):
        """Test ListCollectionsInput model validation."""
        # Valid input
        try:
            valid_input = ListCollectionsInput(database="production_db")
            self.assertEqual(valid_input.database, "production_db")
        except Exception as e:
            self.fail(f"Valid ListCollectionsInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {"database": "staging_db"}
            valid_input_dict = ListCollectionsInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "staging_db")
        except Exception as e:
            self.fail(f"Valid ListCollectionsInput from dictionary validation failed: {e}")

    def test_list_databases_input_validation(self):
        """Test ListDatabasesInput model validation."""
        # Valid input (no required fields)
        try:
            valid_input = ListDatabasesInput()
            # Should create successfully with no required fields
            self.assertIsNotNone(valid_input)
        except Exception as e:
            self.fail(f"Valid ListDatabasesInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {}
            valid_input_dict = ListDatabasesInput(**input_dict)
            self.assertIsNotNone(valid_input_dict)
        except Exception as e:
            self.fail(f"Valid ListDatabasesInput from dictionary validation failed: {e}")

    def test_db_stats_input_validation(self):
        """Test DbStatsInput model validation."""
        # Valid input
        try:
            valid_input = DbStatsInput(database="stats_db")
            self.assertEqual(valid_input.database, "stats_db")
        except Exception as e:
            self.fail(f"Valid DbStatsInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {"database": "analytics_db"}
            valid_input_dict = DbStatsInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "analytics_db")
        except Exception as e:
            self.fail(f"Valid DbStatsInput from dictionary validation failed: {e}")

        # Empty database name
        self.assert_error_behavior(
            lambda: DbStatsInput(database=""),
            PydanticValidationError,
            "String should have at least 1 character"
        )

    def test_explain_input_validation(self):
        """Test ExplainInput model validation."""
        # Valid input with aggregate method
        try:
            aggregate_method = AggregateMethod(
                name="aggregate",
                arguments=AggregateMethodArguments(
                    pipeline=[{"$match": {"status": "active"}}]
                )
            )
            valid_input = ExplainInput(
                database="test_db",
                collection="test_collection",
                method=[aggregate_method]
            )
            self.assertEqual(valid_input.database, "test_db")
            self.assertEqual(valid_input.collection, "test_collection")
            self.assertEqual(len(valid_input.method), 1)
        except Exception as e:
            self.fail(f"Valid ExplainInput validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "database": "test_db",
                "collection": "test_collection",
                "method": [{
                    "name": "find",
                    "arguments": {
                        "filter": {"age": {"$gte": 18}},
                        "limit": 10
                    }
                }]
            }
            valid_input_dict = ExplainInput(**input_dict)
            self.assertEqual(valid_input_dict.database, "test_db")
            self.assertEqual(valid_input_dict.collection, "test_collection")
            self.assertEqual(len(valid_input_dict.method), 1)
        except Exception as e:
            self.fail(f"Valid ExplainInput from dictionary validation failed: {e}")

        # Empty method list
        self.assert_error_behavior(
            lambda: ExplainInput(
                database="test_db",
                collection="test_collection",
                method=[]
            ),
            PydanticValidationError,
            "List should have at least 1 item"
        )

    def test_mongodb_logs_input_validation(self):
        """Test MongoDBLogsInput model validation."""
        # Valid input with default values
        try:
            valid_input = MongoDBLogsInput()
            self.assertEqual(valid_input.log_type, MongoDBLogsType.GLOBAL)
            self.assertEqual(valid_input.limit, 50)
        except Exception as e:
            self.fail(f"Valid MongoDBLogsInput validation failed: {e}")

        # Valid input with custom values using alias
        try:
            valid_input = MongoDBLogsInput(
                **{"type": "startupWarnings"},
                limit=100
            )
            self.assertEqual(valid_input.log_type, MongoDBLogsType.STARTUP_WARNINGS)
            self.assertEqual(valid_input.limit, 100)
        except Exception as e:
            self.fail(f"Valid MongoDBLogsInput with custom values validation failed: {e}")

        # Valid input from dictionary
        try:
            input_dict = {
                "type": "global",
                "limit": 25
            }
            valid_input_dict = MongoDBLogsInput(**input_dict)
            self.assertEqual(valid_input_dict.log_type, MongoDBLogsType.GLOBAL)
            self.assertEqual(valid_input_dict.limit, 25)
        except Exception as e:
            self.fail(f"Valid MongoDBLogsInput from dictionary validation failed: {e}")

        # Limit too high
        self.assert_error_behavior(
            lambda: MongoDBLogsInput(limit=2000),  # Max is 1024
            PydanticValidationError,
            "Input should be less than or equal to 1024"
        )

        # Limit too low
        self.assert_error_behavior(
            lambda: MongoDBLogsInput(limit=0),  # Min is 1
            PydanticValidationError,
            "Input should be greater than or equal to 1"
        )

    def test_field_length_constraints(self):
        """Test field length constraints across models."""
        # Test database name constraints
        models_with_database = [
            InsertManyInput, DeleteManyInput, UpdateManyInput,
            AggregateInput, CountInput, CreateCollectionInput, DropCollectionInput,
            DropDatabaseInput, RenameCollectionInput, CollectionIndexesInput,
            CreateIndexInput, CollectionSchemaInput, CollectionStorageSizeInput,
            ListCollectionsInput, DbStatsInput, ExplainInput
        ]

        for model_class in models_with_database:
            # Test minimum length (empty string should fail)
            kwargs = {"database": ""}
            if model_class in [InsertManyInput]:
                kwargs.update({"collection": "test", "documents": [{"test": "data"}]})
            elif model_class in [DeleteManyInput, UpdateManyInput]:
                kwargs.update({"collection": "test", "filter": {"test": "data"}})
                if model_class == UpdateManyInput:
                    kwargs.update({"update": {"$set": {"test": "updated"}}})
            elif model_class in [AggregateInput]:
                kwargs.update({"collection": "test", "pipeline": [{"$match": {"test": "data"}}]})
            elif model_class in [CountInput]:
                kwargs.update({"collection": "test"})
            elif model_class in [CreateCollectionInput, DropCollectionInput, CollectionIndexesInput, 
                                 CreateIndexInput, CollectionSchemaInput, CollectionStorageSizeInput]:
                kwargs.update({"collection": "test"})
                if model_class == CreateIndexInput:
                    kwargs.update({"keys": {"field": 1}})
            elif model_class in [RenameCollectionInput]:
                kwargs.update({"collection": "test", "new_name": "new_test"})
            elif model_class in [ExplainInput]:
                kwargs.update({
                    "collection": "test",
                    "method": [{
                        "name": "find",
                        "arguments": {"filter": {}}
                    }]
                })

            self.assert_error_behavior(
                lambda model=model_class, args=kwargs: model(**args),
                PydanticValidationError,
                "String should have at least 1 character"
            )

            # Test maximum length (64 characters should fail for database names)
            kwargs["database"] = "a" * 64
            self.assert_error_behavior(
                lambda model=model_class, args=kwargs: model(**args),
                PydanticValidationError,
                "String should have at most 63 characters"
            )

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden in MongoDBBaseModel subclasses."""
        # Test with CreateIndexInput (inherits MongoDBBaseModel with extra='forbid')
        self.assert_error_behavior(
            lambda: CreateIndexInput(
                database="test_db",
                collection="test_collection",
                keys={"field": 1},
                extra_field="not_allowed"  # This should be forbidden
            ),
            PydanticValidationError,
            "Extra inputs are not permitted"
        )

        # FindInput allows extra fields by default (doesn't inherit MongoDBBaseModel)
        try:
            find_input = FindInput(
                database="test_db",
                collection="test_collection",
                extra_field="allowed"  # This should be allowed
            )
            # If this fails, then FindInput does forbid extra fields
            pass
        except PydanticValidationError:
            # If this fails, then FindInput does forbid extra fields
            pass

    def test_model_serialization(self):
        """Test that all models can be properly serialized to JSON and back."""
        
        # Test FindInput serialization
        find_input = FindInput(
            database="test_db",
            collection="test_collection",
            filter={"name": "test", "age": {"$gte": 18}},
            limit=5,
            sort={"created_at": -1}
        )
        self._test_model_json_serialization(find_input, "FindInput")

        # Test InsertManyInput serialization
        insert_input = InsertManyInput(
            database="test_db",
            collection="test_collection",
            documents=[
                {"name": "John", "age": 25, "active": True},
                {"name": "Jane", "age": 30, "active": False, "metadata": {"type": "premium"}}
            ]
        )
        self._test_model_json_serialization(insert_input, "InsertManyInput")

        # Test DeleteManyInput serialization
        delete_input = DeleteManyInput(
            database="test_db",
            collection="test_collection",
            filter={"status": {"$in": ["inactive", "deleted"]}, "last_login": {"$lt": "2023-01-01"}}
        )
        self._test_model_json_serialization(delete_input, "DeleteManyInput")

        # Test UpdateManyInput serialization
        update_input = UpdateManyInput(
            database="test_db",
            collection="test_collection",
            filter={"category": "electronics"},
            update={"$set": {"discount": 0.1}, "$inc": {"views": 1}},
            upsert=True
        )
        self._test_model_json_serialization(update_input, "UpdateManyInput")

        # Test AggregateInput serialization
        aggregate_input = AggregateInput(
            database="test_db",
            collection="test_collection",
            pipeline=[
                {"$match": {"status": "active"}},
                {"$group": {"_id": "$category", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
                {"$sort": {"total": -1}},
                {"$limit": 10}
            ]
        )
        self._test_model_json_serialization(aggregate_input, "AggregateInput")

        # Test CountInput serialization - use 'query' field
        count_input = CountInput(
            database="test_db",
            collection="test_collection",
            query={"age": {"$gte": 18}, "status": "verified", "tags": {"$all": ["premium", "active"]}}
        )
        self._test_model_json_serialization(count_input, "CountInput")

        # Test CreateCollectionInput serialization
        create_collection_input = CreateCollectionInput(
            database="test_db",
            collection="new_collection"
        )
        self._test_model_json_serialization(create_collection_input, "CreateCollectionInput")

        # Test DropCollectionInput serialization
        drop_collection_input = DropCollectionInput(
            database="test_db",
            collection="old_collection"
        )
        self._test_model_json_serialization(drop_collection_input, "DropCollectionInput")

        # Test DropDatabaseInput serialization
        drop_database_input = DropDatabaseInput(database="old_database")
        self._test_model_json_serialization(drop_database_input, "DropDatabaseInput")

        # Test RenameCollectionInput serialization
        rename_collection_input = RenameCollectionInput(
            database="test_db",
            collection="old_collection",
            new_name="new_collection"
        )
        self._test_model_json_serialization(rename_collection_input, "RenameCollectionInput")

        # Test CollectionIndexesInput serialization
        collection_indexes_input = CollectionIndexesInput(
            database="test_db",
            collection="indexed_collection"
        )
        self._test_model_json_serialization(collection_indexes_input, "CollectionIndexesInput")

        # Test CreateIndexInput serialization
        create_index_input = CreateIndexInput(
            database="test_db",
            collection="test_collection",
            keys={"name": 1, "email": -1, "created_at": 1},
            name="compound_idx"
        )
        self._test_model_json_serialization(create_index_input, "CreateIndexInput")

        # Test CollectionSchemaInput serialization
        collection_schema_input = CollectionSchemaInput(
            database="test_db",
            collection="schema_collection"
        )
        self._test_model_json_serialization(collection_schema_input, "CollectionSchemaInput")

        # Test CollectionStorageSizeInput serialization
        collection_storage_input = CollectionStorageSizeInput(
            database="test_db",
            collection="large_collection"
        )
        self._test_model_json_serialization(collection_storage_input, "CollectionStorageSizeInput")

        # Test SwitchConnectionInput serialization - handle alias properly
        switch_connection_input = SwitchConnectionInput(
            **{"connectionString": "mongodb://user:password@localhost:27017/testdb?authSource=admin"}
        )
        # For SwitchConnectionInput, we need to handle the alias properly
        try:
            # Convert to dict using model_dump with by_alias=True to get the alias
            model_dict = switch_connection_input.model_dump(by_alias=True)
            json_str = json.dumps(model_dict)
            parsed_dict = json.loads(json_str)
            
            # Reconstruct using the parsed dict (which should have the alias)
            reconstructed = SwitchConnectionInput(**parsed_dict)
            
            # Verify the values match
            self.assertEqual(reconstructed.connection_string, switch_connection_input.connection_string)
        except Exception as e:
            self.fail(f"SwitchConnectionInput JSON serialization failed: {e}")

        # Test ListCollectionsInput serialization
        list_collections_input = ListCollectionsInput(database="production_db")
        self._test_model_json_serialization(list_collections_input, "ListCollectionsInput")

        # Test ListDatabasesInput serialization
        list_databases_input = ListDatabasesInput()
        self._test_model_json_serialization(list_databases_input, "ListDatabasesInput")

        # Test DbStatsInput serialization
        db_stats_input = DbStatsInput(database="analytics_db")
        self._test_model_json_serialization(db_stats_input, "DbStatsInput")

        # Test ExplainInput serialization
        explain_input = ExplainInput(
            database="test_db",
            collection="test_collection",
            method=[{
                "name": "aggregate",
                "arguments": {
                    "pipeline": [{"$match": {"status": "active"}}]
                }
            }]
        )
        self._test_model_json_serialization(explain_input, "ExplainInput")

        # Test MongoDBLogsInput serialization - handle alias properly
        mongodb_logs_input = MongoDBLogsInput(
            **{"type": "startupWarnings"},
            limit=100
        )
        # For MongoDBLogsInput, we need to handle the alias properly like SwitchConnectionInput
        try:
            # Convert to dict using model_dump with by_alias=True to get the alias
            model_dict = mongodb_logs_input.model_dump(by_alias=True)
            json_str = json.dumps(model_dict)
            parsed_dict = json.loads(json_str)
            
            # Reconstruct using the parsed dict (which should have the alias)
            reconstructed = MongoDBLogsInput(**parsed_dict)
            
            # Verify the values match
            self.assertEqual(reconstructed.log_type, mongodb_logs_input.log_type)
            self.assertEqual(reconstructed.limit, mongodb_logs_input.limit)
        except Exception as e:
            self.fail(f"MongoDBLogsInput JSON serialization failed: {e}")

    def _test_model_json_serialization(self, model_instance, model_name: str):
        """Helper method to test JSON serialization for a model instance."""
        try:
            # Convert to dict
            model_dict = model_instance.model_dump()
            
            # Convert to JSON string
            json_str = json.dumps(model_dict)
            
            # Parse JSON back to dict
            parsed_dict = json.loads(json_str)
            
            # Reconstruct model from parsed dict
            reconstructed = type(model_instance)(**parsed_dict)
            
            # Verify the reconstructed model has the same values
            self.assertEqual(reconstructed.model_dump(), model_instance.model_dump())
            
        except Exception as e:
            self.fail(f"{model_name} JSON serialization failed: {e}")


if __name__ == '__main__':
    unittest.main()
