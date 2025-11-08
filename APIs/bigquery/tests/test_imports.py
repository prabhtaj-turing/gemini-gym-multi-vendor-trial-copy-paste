"""
Import and package health tests for BigQuery API.

This module tests that all BigQuery API modules can be imported without errors,
public functions are available and callable, and all required dependencies are installed.
Following the Service Engineering Test Framework Guideline for import & package tests.
"""

import unittest
import importlib
import sys
from typing import List, Dict, Any
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestBigQueryImports(BaseTestCaseWithErrorHandler):
    """
    Test suite for BigQuery API imports and package health.
    
    Tests that all modules can be imported without errors, public functions
    are available and callable, and all required dependencies are installed.
    """

    def test_bigquery_api_import(self):
        """Test that the main BigQuery API module can be imported."""
        try:
            from bigquery import bigqueryAPI
            self.assertIsNotNone(bigqueryAPI)
        except ImportError as e:
            self.fail(f"Failed to import bigqueryAPI: {e}")

    def test_bigquery_functions_import(self):
        """Test that all public BigQuery functions can be imported."""
        try:
            from bigquery.bigqueryAPI import (
                list_tables,
                describe_table,
                execute_query
            )
            
            # Verify functions are callable
            self.assertTrue(callable(list_tables))
            self.assertTrue(callable(describe_table))
            self.assertTrue(callable(execute_query))
            
        except ImportError as e:
            self.fail(f"Failed to import BigQuery functions: {e}")

    def test_simulation_engine_imports(self):
        """Test that all SimulationEngine modules can be imported."""
        modules_to_test = [
            "bigquery.SimulationEngine.db",
            "bigquery.SimulationEngine.utils",
            "bigquery.SimulationEngine.custom_errors",
            "bigquery.SimulationEngine.models",
            "bigquery.SimulationEngine.file_utils"
        ]
        
        for module_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_custom_errors_import(self):
        """Test that all custom error classes can be imported."""
        try:
            from bigquery.SimulationEngine.custom_errors import (
                BigQueryClientError,
                InvalidQueryError,
                InvalidInputError,
                ProjectNotFoundError,
                DatasetNotFoundError,
                TableNotFoundError
            )
            
            # Verify error classes are defined
            self.assertTrue(issubclass(BigQueryClientError, Exception))
            self.assertTrue(issubclass(InvalidQueryError, Exception))
            self.assertTrue(issubclass(InvalidInputError, BigQueryClientError))
            self.assertTrue(issubclass(ProjectNotFoundError, BigQueryClientError))
            self.assertTrue(issubclass(DatasetNotFoundError, BigQueryClientError))
            self.assertTrue(issubclass(TableNotFoundError, BigQueryClientError))
            
        except ImportError as e:
            self.fail(f"Failed to import custom errors: {e}")

    def test_utils_functions_import(self):
        """Test that utility functions can be imported and are callable."""
        try:
            from bigquery.SimulationEngine.utils import (
                bq_type_to_sqlite_type,
                parse_full_table_name,
                load_db_dict_to_sqlite,
                get_default_db_path,
                set_default_db_path
            )
            
            # Verify utility functions are callable
            self.assertTrue(callable(bq_type_to_sqlite_type))
            self.assertTrue(callable(parse_full_table_name))
            self.assertTrue(callable(load_db_dict_to_sqlite))
            self.assertTrue(callable(get_default_db_path))
            self.assertTrue(callable(set_default_db_path))
            
        except ImportError as e:
            self.fail(f"Failed to import utility functions: {e}")

    def test_models_import(self):
        """Test that data models can be imported."""
        try:
            from bigquery.SimulationEngine.models import (
                BigQueryDatabase,
                Table,
                FieldMode
            )
            
            # Verify models are defined
            self.assertTrue(hasattr(BigQueryDatabase, '__annotations__'))
            self.assertTrue(hasattr(Table, '__annotations__'))
            self.assertTrue(hasattr(FieldMode, '__annotations__'))
            
        except ImportError as e:
            self.fail(f"Failed to import data models: {e}")

    def test_db_structure_import(self):
        """Test that database structure can be imported."""
        try:
            from bigquery.SimulationEngine.db import DB
            
            # Verify DB is a dictionary with expected structure
            self.assertIsInstance(DB, dict)
            self.assertIn('projects', DB)
            
        except ImportError as e:
            self.fail(f"Failed to import database structure: {e}")

    def test_common_utils_dependencies(self):
        """Test that common_utils dependencies are available."""
        try:
            from common_utils.error_handling import get_package_error_mode, handle_api_errors
            from common_utils.base_case import BaseTestCaseWithErrorHandler
            
            # Verify common_utils functions are callable
            self.assertTrue(callable(get_package_error_mode))
            self.assertTrue(callable(handle_api_errors))
            
        except ImportError as e:
            self.fail(f"Failed to import common_utils dependencies: {e}")

    def test_required_standard_library_imports(self):
        """Test that required standard library modules are available."""
        required_modules = [
            'json',
            're',
            'datetime',
            'sqlite3',
            'tempfile',
            'os',
            'typing'
        ]
        
        for module_name in required_modules:
            try:
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)
            except ImportError as e:
                self.fail(f"Required standard library module {module_name} not available: {e}")

    def test_package_public_interface(self):
        """Test that the package's public interface is properly defined."""
        try:
            import bigquery
            
            # Check if __all__ is defined (optional but good practice)
            if hasattr(bigquery, '__all__'):
                self.assertIsInstance(bigquery.__all__, list)
                
            # Check if main functions are accessible
            self.assertTrue(hasattr(bigquery, 'bigqueryAPI'))
            
        except ImportError as e:
            self.fail(f"Failed to import bigquery package: {e}")

    def test_smoke_test_basic_functionality(self):
        """Smoke test: basic functionality without errors."""
        try:
            # Import main components
            from bigquery.bigqueryAPI import list_tables
            from bigquery.SimulationEngine.db import DB
            
            # Basic smoke test - should not raise import errors
            self.assertIsNotNone(list_tables)
            self.assertIsNotNone(DB)
            
        except Exception as e:
            self.fail(f"Smoke test failed: {e}")


if __name__ == "__main__":
    unittest.main()
