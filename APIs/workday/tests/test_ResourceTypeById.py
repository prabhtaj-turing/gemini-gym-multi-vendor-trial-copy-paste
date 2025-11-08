#!/usr/bin/env python3
"""
Fixed Unit Tests for ResourceTypeById Module

This module provides corrected testing for the ResourceTypeById module which 
actually works with SCIM resource types, not project resource types.

Author: AI Assistant
Created: 2024-12-28
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional

# Import the module under test
from ..ResourceTypeById import get
from ..SimulationEngine import db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestResourceTypeByIdFixed(BaseTestCaseWithErrorHandler):
    """Fixed tests for ResourceTypeById module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        db.reset_db()
        
        # Setup test SCIM resource type data
        self.test_resource_data = {
            "resource": "User",
            "id": "User",
            "name": "User",
            "description": "User account",
            "endpoint": "/Users",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
        }
        
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        db.reset_db()
        
    def test_get_existing_resource_type_success(self):
        """Test successful retrieval of existing SCIM resource type."""
        # Add test data
        db.DB["scim"]["resource_types"] = [self.test_resource_data.copy()]
        
        result = get("User")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["resource"], "User")
        self.assertEqual(result["name"], "User")
        self.assertEqual(result["description"], "User account")
        
    def test_get_nonexistent_resource_type_returns_none(self):
        """Test that retrieving non-existent resource type returns None."""
        db.DB["scim"]["resource_types"] = [self.test_resource_data.copy()]
        
        result = get("NonExistent")
        self.assertIsNone(result)
        
    def test_invalid_parameter_types_raise_errors(self):
        """Test that invalid parameter types raise appropriate errors."""
        # Test None parameter
        with self.assertRaises(ValueError):
            get(None)
            
        # Test non-string parameter
        with self.assertRaises(TypeError):
            get(123)
            
        # Test empty string
        with self.assertRaises(ValueError):
            get("")
            
        # Test whitespace-only string
        with self.assertRaises(ValueError):
            get("   ")
            
    def test_multiple_resource_types(self):
        """Test with multiple resource types in database."""
        resource_types = [
            {"resource": "User", "name": "User", "description": "User account"},
            {"resource": "Group", "name": "Group", "description": "Group resource"},
            {"resource": "Schema", "name": "Schema", "description": "Schema resource"}
        ]
        
        db.DB["scim"]["resource_types"] = resource_types
        
        # Test retrieving each one
        for resource_type in resource_types:
            result = get(resource_type["resource"])
            self.assertIsNotNone(result)
            self.assertEqual(result["resource"], resource_type["resource"])
            self.assertEqual(result["name"], resource_type["name"])
            
    def test_empty_database_returns_none(self):
        """Test behavior when database is empty."""
        db.DB["scim"]["resource_types"] = []
        
        result = get("User")
        self.assertIsNone(result)
        
    def test_performance_single_lookup(self):
        """Test performance of single resource type lookup."""
        db.DB["scim"]["resource_types"] = [self.test_resource_data.copy()]
        
        # Measure performance
        start_time = time.time()
        result = get("User")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        self.assertIsNotNone(result)
        self.assertLess(execution_time, 0.01)  # Should complete in less than 10ms


class TestResourceTypeByIdSmokeTests(BaseTestCaseWithErrorHandler):
    """Smoke tests for ResourceTypeById module."""
    
    def setUp(self):
        """Set up smoke test fixtures."""
        super().setUp()
        db.reset_db()
        
    def tearDown(self):
        """Clean up after smoke tests."""
        super().tearDown()
        db.reset_db()
        
    def test_module_import_and_basic_functionality(self):
        """Smoke test: module imports and basic function works."""
        # Test import
        from ..ResourceTypeById import get
        self.assertTrue(callable(get))
        
        # Test basic functionality
        result = get("NonExistent")  # Non-existent resource
        self.assertIsNone(result)
        
        # Test with valid data
        db.DB["scim"]["resource_types"] = [
            {"resource": "User", "name": "User", "description": "Test user"}
        ]
        
        result = get("User")
        self.assertIsNotNone(result)
        self.assertEqual(result["resource"], "User")
        
    def test_function_signature_compatibility(self):
        """Smoke test: function signature works as expected."""
        # Test with string parameter
        result = get("NonExistent")
        self.assertIsNone(result)  # Should not raise exception
        
        # Test that function accepts string parameter
        db.DB["scim"]["resource_types"] = [
            {"resource": "Test", "name": "Test Resource"}
        ]
        result = get("Test")
        self.assertIsNotNone(result)
        
    def test_error_handling_robustness(self):
        """Smoke test: error handling works for common error cases."""
        error_test_cases = [
            # None parameter
            (None, ValueError),
            # Non-string parameter
            (123, TypeError),
            # Empty string
            ("", ValueError),
            # Whitespace only
            ("   ", ValueError)
        ]
        
        for test_input, expected_error in error_test_cases:
            with self.subTest(test_input=test_input):
                with self.assertRaises(expected_error):
                    get(test_input)


if __name__ == '__main__':
    unittest.main()
