import unittest
import importlib
import sys
import os

# Add the APIs directory to the path to avoid import issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class ImportTest(unittest.TestCase):
    def test_import_mongodb_package(self):
        """Test that the main mongodb package can be imported."""
        try:
            # Import directly from the local path to avoid the problematic genai import
            import mongodb
        except ImportError as e:
            # If direct import fails, try the full path
            try:
                import APIs.mongodb
            except ImportError:
                self.fail(f"Failed to import mongodb package: {e}")

    def test_import_public_functions(self):
        """Test that public functions can be imported from the mongodb module."""
        try:
            from APIs.mongodb import switch_connection
            from APIs.mongodb import list_databases
            from APIs.mongodb import drop_database
            from APIs.mongodb import list_collections
            from APIs.mongodb import create_collection
            from APIs.mongodb import rename_collection
            from APIs.mongodb import drop_collection
            from APIs.mongodb import collection_schema
            from APIs.mongodb import collection_storage_size
            from APIs.mongodb import collection_indexes
            from APIs.mongodb import create_index
            from APIs.mongodb import find
            from APIs.mongodb import count
            from APIs.mongodb import aggregate
            from APIs.mongodb import insert_many
            from APIs.mongodb import update_many
            from APIs.mongodb import delete_many
        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")

    def test_public_functions_are_callable(self):
        """Test that the public functions are callable."""
        from APIs.mongodb import switch_connection
        from APIs.mongodb import list_databases
        from APIs.mongodb import drop_database
        from APIs.mongodb import list_collections
        from APIs.mongodb import create_collection
        from APIs.mongodb import rename_collection
        from APIs.mongodb import drop_collection
        from APIs.mongodb import collection_schema
        from APIs.mongodb import collection_storage_size
        from APIs.mongodb import collection_indexes
        from APIs.mongodb import create_index
        from APIs.mongodb import find
        from APIs.mongodb import count
        from APIs.mongodb import aggregate
        from APIs.mongodb import insert_many
        from APIs.mongodb import update_many
        from APIs.mongodb import delete_many

        # Test that all functions are callable
        self.assertTrue(callable(switch_connection))
        self.assertTrue(callable(list_databases))
        self.assertTrue(callable(drop_database))
        self.assertTrue(callable(list_collections))
        self.assertTrue(callable(create_collection))
        self.assertTrue(callable(rename_collection))
        self.assertTrue(callable(drop_collection))
        self.assertTrue(callable(collection_schema))
        self.assertTrue(callable(collection_storage_size))
        self.assertTrue(callable(collection_indexes))
        self.assertTrue(callable(create_index))
        self.assertTrue(callable(find))
        self.assertTrue(callable(count))
        self.assertTrue(callable(aggregate))
        self.assertTrue(callable(insert_many))
        self.assertTrue(callable(update_many))
        self.assertTrue(callable(delete_many))

    def test_import_simulation_engine_components(self):
        """Test that components from SimulationEngine can be imported."""
        try:
            from APIs.mongodb.SimulationEngine import utils
            from APIs.mongodb.SimulationEngine.custom_errors import ValidationError
            from APIs.mongodb.SimulationEngine.custom_errors import InvalidQueryError
            from APIs.mongodb.SimulationEngine.custom_errors import DatabaseNotFoundError
            from APIs.mongodb.SimulationEngine.custom_errors import CollectionNotFoundError
            from APIs.mongodb.SimulationEngine.db import DB
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine components: {e}")

    def test_simulation_engine_components_are_usable(self):
        """Test that imported SimulationEngine components are usable."""
        from APIs.mongodb.SimulationEngine import utils
        from APIs.mongodb.SimulationEngine.custom_errors import ValidationError
        from APIs.mongodb.SimulationEngine.custom_errors import InvalidQueryError
        from APIs.mongodb.SimulationEngine.custom_errors import DatabaseNotFoundError
        from APIs.mongodb.SimulationEngine.custom_errors import CollectionNotFoundError
        from APIs.mongodb.SimulationEngine.db import DB

        # Test that utils has expected functions
        self.assertTrue(hasattr(utils, 'log_operation'))
        self.assertTrue(hasattr(utils, 'maintain_index_metadata'))
        self.assertTrue(hasattr(utils, 'validate_document_references'))
        self.assertTrue(hasattr(utils, 'update_collection_metrics'))
        self.assertTrue(hasattr(utils, 'get_active_connection'))
        self.assertTrue(hasattr(utils, 'get_active_database'))
        self.assertTrue(hasattr(utils, 'generate_object_id'))
        self.assertTrue(hasattr(utils, 'sanitize_document'))

        # Test that custom errors are proper exception classes
        self.assertTrue(issubclass(ValidationError, Exception))
        self.assertTrue(issubclass(InvalidQueryError, Exception))
        self.assertTrue(issubclass(DatabaseNotFoundError, Exception))
        self.assertTrue(issubclass(CollectionNotFoundError, Exception))

        # Test that DB is a MongoDB instance with expected attributes
        self.assertTrue(hasattr(DB, 'connections'))
        self.assertTrue(hasattr(DB, 'current_conn'))
        self.assertTrue(hasattr(DB, 'current_db'))
        self.assertTrue(hasattr(DB, 'switch_connection'))
        self.assertTrue(hasattr(DB, 'use_database'))

    def test_import_module_components(self):
        """Test that individual module components can be imported."""
        try:
            from APIs.mongodb import collection_management
            from APIs.mongodb import connection_server_management
            from APIs.mongodb import database_operations
            from APIs.mongodb import data_operations
        except ImportError as e:
            self.fail(f"Failed to import module components: {e}")

    def test_module_components_have_expected_functions(self):
        """Test that module components have their expected functions."""
        from APIs.mongodb import collection_management
        from APIs.mongodb import connection_server_management
        from APIs.mongodb import database_operations
        from APIs.mongodb import data_operations

        # Test collection_management functions
        expected_collection_functions = [
            'list_collections', 'create_collection', 'rename_collection', 
            'drop_collection', 'collection_schema', 'collection_storage_size',
            'collection_indexes', 'create_index'
        ]
        for func_name in expected_collection_functions:
            self.assertTrue(hasattr(collection_management, func_name))

        # Test connection_server_management functions
        expected_connection_functions = ['switch_connection']
        for func_name in expected_connection_functions:
            self.assertTrue(hasattr(connection_server_management, func_name))

        # Test database_operations functions
        expected_database_functions = ['list_databases', 'drop_database']
        for func_name in expected_database_functions:
            self.assertTrue(hasattr(database_operations, func_name))

        # Test data_operations functions
        expected_data_functions = [
            'find', 'count', 'aggregate', 'insert_many', 'update_many', 'delete_many'
        ]
        for func_name in expected_data_functions:
            self.assertTrue(hasattr(data_operations, func_name))

    def test_import_models(self):
        """Test that models can be imported from SimulationEngine."""
        try:
            from APIs.mongodb.SimulationEngine.models import AggregateInput
            from APIs.mongodb.SimulationEngine.models import DeleteManyInput
            from APIs.mongodb.SimulationEngine.models import FindInput
            from APIs.mongodb.SimulationEngine.models import UpdateManyInput
            from APIs.mongodb.SimulationEngine.models import CountInput
            from APIs.mongodb.SimulationEngine.models import InsertManyInput
        except ImportError as e:
            self.fail(f"Failed to import models: {e}")

    def test_models_are_pydantic_models(self):
        """Test that imported models are proper Pydantic models."""
        from APIs.mongodb.SimulationEngine.models import AggregateInput
        from APIs.mongodb.SimulationEngine.models import DeleteManyInput
        from APIs.mongodb.SimulationEngine.models import FindInput
        from APIs.mongodb.SimulationEngine.models import UpdateManyInput
        from APIs.mongodb.SimulationEngine.models import CountInput
        from APIs.mongodb.SimulationEngine.models import InsertManyInput

        # Test that models have expected Pydantic model attributes
        models = [AggregateInput, DeleteManyInput, FindInput, UpdateManyInput, CountInput, InsertManyInput]
        for model in models:
            self.assertTrue(hasattr(model, '__fields__') or hasattr(model, 'model_fields'))
            self.assertTrue(hasattr(model, '__init__'))

    def test_function_map_completeness(self):
        """Test that all functions in _function_map are importable."""
        import APIs.mongodb as mongodb_module
        
        # Get the function map from the module
        function_map = mongodb_module._function_map
        
        # Test that each function in the map can be accessed
        for func_name in function_map.keys():
            self.assertTrue(hasattr(mongodb_module, func_name), 
                          f"Function {func_name} not accessible from mongodb module")
            
            # Test that the function is callable
            func = getattr(mongodb_module, func_name)
            self.assertTrue(callable(func), 
                          f"Function {func_name} is not callable")


if __name__ == '__main__':
    unittest.main()
