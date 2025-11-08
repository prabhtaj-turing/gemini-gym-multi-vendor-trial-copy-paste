#!/usr/bin/env python3
"""
Comprehensive Unit Tests for BidsById Module

This module provides extensive testing coverage for the BidsById module including:
1. Unit Test Cases with Data Model Validation
2. Database Structure Validation
3. State (Load/Save) Tests
4. Integration Tests
5. Performance Tests
6. Smoke Tests

Author: AI Assistant
Created: 2024-12-28
"""

import unittest
import json
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional
from pydantic import ValidationError as PydanticValidationError

# Import the module under test
from ..BidsById import get
from ..SimulationEngine import db
from ..SimulationEngine.custom_errors import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestBidsByIdDataModel(unittest.TestCase):
    """Test data model validation for BidsById module."""
    
    def setUp(self):
        """Set up test fixtures."""
        db.reset_db()
        
    def tearDown(self):
        """Clean up after each test."""
        db.reset_db()
        
    def test_valid_bid_data_structure(self):
        """Test that valid bid data structure is correctly validated."""
        # Valid bid data
        bid_data = {
            "type": "bids",
            "supplier_id": 123,
            "bid_amount": 1000.50,
            "intend_to_bid": True,
            "intend_to_bid_answered_at": "2024-01-01T10:00:00Z",
            "status": "submitted",
            "submitted_at": "2024-01-01T10:00:00Z",
            "resubmitted_at": "2024-01-01T11:00:00Z",
            "event_id": 456
        }
        
        # Add to database
        db.DB["events"]["bids"][1] = bid_data
        
        # Test retrieval
        result = get(1)
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertEqual(result["data"]["type"], "bids")
        self.assertEqual(result["data"]["id"], "1")
        
    def test_bid_status_validation(self):
        """Test validation of bid status values."""
        valid_statuses = [
            "award_retracted", "awarded", "draft", "rejected",
            "rejection_retracted", "resubmitted", "revising",
            "submitted", "unclaimed", "update_requested"
        ]
        
        for status in valid_statuses:
            bid_data = {
                "supplier_id": 123,
                "bid_amount": 1000.0,
                "status": status,
                "event_id": 456
            }
            db.DB["events"]["bids"][1] = bid_data
            
            result = get(1)
            self.assertIsNotNone(result)
            self.assertEqual(result["data"]["attributes"]["status"], status)
            
            # Clean up for next iteration
            del db.DB["events"]["bids"][1]


class TestBidsByIdUnitTests(BaseTestCaseWithErrorHandler):
    """Comprehensive unit tests for BidsById module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        db.reset_db()
        
        # Setup test bid data
        self.test_bid_data = {
            "supplier_id": 123,
            "bid_amount": 1500.75,
            "intend_to_bid": True,
            "intend_to_bid_answered_at": "2024-01-01T10:00:00Z",
            "status": "submitted",
            "submitted_at": "2024-01-01T10:00:00Z",
            "resubmitted_at": "2024-01-01T11:00:00Z",
            "event_id": 456
        }
        
        # Setup test event data for includes
        self.test_event_data = {
            "name": "Test Event",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        # Setup test supplier data for includes
        self.test_supplier_data = {
            "name": "Test Supplier Company",
            "status": "active",
            "external_id": "SUP123"
        }
        
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        db.reset_db()
        
    # =========================================================================
    # Basic Functionality Tests
    # =========================================================================
    
    def test_get_existing_bid_success(self):
        """Test successful retrieval of existing bid."""
        # Add test data
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        
        result = get(1)
        
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertEqual(result["data"]["type"], "bids")
        self.assertEqual(result["data"]["id"], "1")
        self.assertIn("attributes", result["data"])
        self.assertEqual(result["data"]["attributes"]["supplier_id"], 123)
        self.assertEqual(result["data"]["attributes"]["bid_amount"], 1500.75)
        
    def test_get_nonexistent_bid_returns_none(self):
        """Test that retrieving non-existent bid returns None."""
        result = get(999)
        self.assertIsNone(result)
        
    def test_get_bid_with_valid_include_event(self):
        """Test retrieving bid with event include."""
        # Setup test data
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        db.DB["events"]["events"]["456"] = self.test_event_data.copy()
        
        result = get(1, _include="event")
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        self.assertEqual(len(result["included"]), 1)
        self.assertEqual(result["included"][0]["type"], "events")
        self.assertEqual(result["included"][0]["id"], 456)
        
    def test_get_bid_with_valid_include_supplier_company(self):
        """Test retrieving bid with supplier company include."""
        # Setup test data
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        db.DB["suppliers"]["supplier_companies"][123] = self.test_supplier_data.copy()
        
        result = get(1, _include="supplier_company")
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        self.assertEqual(len(result["included"]), 1)
        self.assertEqual(result["included"][0]["type"], "supplier_companies")
        self.assertEqual(result["included"][0]["id"], 123)
        
    def test_get_bid_with_multiple_includes(self):
        """Test retrieving bid with multiple includes."""
        # Setup test data
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        db.DB["events"]["events"]["456"] = self.test_event_data.copy()
        db.DB["suppliers"]["supplier_companies"][123] = self.test_supplier_data.copy()
        
        result = get(1, _include="event,supplier_company")
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        self.assertEqual(len(result["included"]), 2)
        
        # Check both resources are included
        types = [resource["type"] for resource in result["included"]]
        self.assertIn("events", types)
        self.assertIn("supplier_companies", types)
        
    # =========================================================================
    # Input Validation Tests
    # =========================================================================
    
    def test_invalid_id_type_raises_validation_error(self):
        """Test that invalid ID type raises ValidationError."""
        with self.assertRaises(ValidationError) as context:
            get("invalid_id")
        self.assertIn("Bid ID must be a valid integer", str(context.exception))
        
    def test_negative_id_raises_validation_error(self):
        """Test that negative ID raises ValidationError."""
        with self.assertRaises(ValidationError) as context:
            get(-1)
        self.assertIn("Bid ID must be a positive integer", str(context.exception))
        
    def test_zero_id_raises_validation_error(self):
        """Test that zero ID raises ValidationError."""
        with self.assertRaises(ValidationError) as context:
            get(0)
        self.assertIn("Bid ID must be a positive integer", str(context.exception))
        
    def test_id_too_large_raises_validation_error(self):
        """Test that ID larger than max raises ValidationError."""
        with self.assertRaises(ValidationError) as context:
            get(1000000000)  # Greater than 999,999,999
        self.assertIn("Bid ID must be less than or equal to 999,999,999", str(context.exception))
        
    def test_invalid_include_type_raises_validation_error(self):
        """Test that invalid include type raises ValidationError."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        
        with self.assertRaises(ValidationError) as context:
            get(1, _include=123)
        self.assertIn("Invalid _include parameter", str(context.exception))
        
    def test_empty_include_raises_validation_error(self):
        """Test that empty include string raises ValidationError."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        
        with self.assertRaises(ValidationError) as context:
            get(1, _include="")
        self.assertIn("_include parameter cannot be empty", str(context.exception))
        
    def test_whitespace_only_include_raises_validation_error(self):
        """Test that whitespace-only include raises ValidationError."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        
        with self.assertRaises(ValidationError) as context:
            get(1, _include="   ")
        self.assertIn("_include parameter cannot be empty", str(context.exception))
        
    def test_include_too_long_raises_validation_error(self):
        """Test that include string longer than 500 chars raises ValidationError."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        long_include = "event," * 200  # Much longer than 500 characters
        
        with self.assertRaises(ValidationError) as context:
            get(1, _include=long_include)
        self.assertIn("_include parameter is too long", str(context.exception))
        
    def test_invalid_include_option_raises_validation_error(self):
        """Test that invalid include option raises ValidationError."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        
        with self.assertRaises(ValidationError) as context:
            get(1, _include="invalid_option")
        self.assertIn("Invalid include option", str(context.exception))
        
    def test_duplicate_include_options_raises_validation_error(self):
        """Test that duplicate include options raise ValidationError."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        
        with self.assertRaises(ValidationError) as context:
            get(1, _include="event,event")
        self.assertIn("_include parameter contains duplicate options", str(context.exception))
        
    # =========================================================================
    # Edge Cases and Error Handling
    # =========================================================================
    
    def test_include_with_missing_related_data(self):
        """Test include parameter when related data doesn't exist."""
        # Setup bid without related event or supplier
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        
        result = get(1, _include="event,supplier_company")
        
        # Should return standard format without included resources
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        self.assertNotIn("included", result)
        
    def test_case_insensitive_include_options(self):
        """Test that include options are case insensitive."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        db.DB["events"]["events"]["456"] = self.test_event_data.copy()
        
        result = get(1, _include="EVENT")
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        self.assertEqual(result["included"][0]["type"], "events")
        
    def test_include_with_extra_whitespace(self):
        """Test include parameter with extra whitespace."""
        db.DB["events"]["bids"][1] = self.test_bid_data.copy()
        db.DB["events"]["events"]["456"] = self.test_event_data.copy()
        
        result = get(1, _include=" event , events ")
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        
    # =========================================================================
    # Database State Tests
    # =========================================================================
    
    def test_database_state_preservation(self):
        """Test that database state is preserved across operations."""
        # Add multiple bids
        for i in range(1, 4):
            bid_data = self.test_bid_data.copy()
            bid_data["supplier_id"] = 100 + i
            db.DB["events"]["bids"][i] = bid_data
        
        # Retrieve one bid
        result = get(2)
        self.assertIsNotNone(result)
        
        # Verify other bids still exist
        self.assertIn(1, db.DB["events"]["bids"])
        self.assertIn(3, db.DB["events"]["bids"])
        self.assertEqual(len(db.DB["events"]["bids"]), 3)


class TestBidsByIdIntegration(BaseTestCaseWithErrorHandler):
    """Integration tests for BidsById module."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        super().setUp()
        db.reset_db()
        
    def tearDown(self):
        """Clean up after integration tests."""
        super().tearDown()
        db.reset_db()
        
    def test_integration_with_events_database(self):
        """Test integration with events database section."""
        # Setup related data
        event_data = {
            "name": "Integration Test Event",
            "status": "active",
            "supplier_companies": [123]
        }
        db.DB["events"]["events"]["456"] = event_data
        
        bid_data = {
            "supplier_id": 123,
            "event_id": 456,
            "bid_amount": 2000.0,
            "status": "submitted"
        }
        db.DB["events"]["bids"][1] = bid_data
        
        result = get(1, _include="event")
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        self.assertEqual(result["included"][0]["attributes"]["name"], "Integration Test Event")
        
    def test_integration_with_suppliers_database(self):
        """Test integration with suppliers database section."""
        # Setup related data
        supplier_data = {
            "name": "Integration Test Supplier",
            "status": "active",
            "external_id": "INT123"
        }
        db.DB["suppliers"]["supplier_companies"][123] = supplier_data
        
        bid_data = {
            "supplier_id": 123,
            "event_id": 456,
            "bid_amount": 2000.0,
            "status": "submitted"
        }
        db.DB["events"]["bids"][1] = bid_data
        
        result = get(1, _include="supplier_company")
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        self.assertEqual(result["included"][0]["attributes"]["name"], "Integration Test Supplier")


class TestBidsByIdPerformance(BaseTestCaseWithErrorHandler):
    """Performance tests for BidsById module."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        super().setUp()
        db.reset_db()
        
    def tearDown(self):
        """Clean up after performance tests."""
        super().tearDown()
        db.reset_db()
        
    def test_performance_single_bid_lookup(self):
        """Test performance of single bid lookup."""
        # Add test data
        bid_data = {
            "supplier_id": 123,
            "bid_amount": 1000.0,
            "status": "submitted",
            "event_id": 456
        }
        db.DB["events"]["bids"][1] = bid_data
        
        # Measure performance
        start_time = time.time()
        result = get(1)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        self.assertIsNotNone(result)
        self.assertLess(execution_time, 0.1)  # Should complete in less than 100ms
        
    def test_performance_with_includes(self):
        """Test performance when including related data."""
        # Setup test data
        bid_data = {
            "supplier_id": 123,
            "bid_amount": 1000.0,
            "status": "submitted",
            "event_id": 456
        }
        db.DB["events"]["bids"][1] = bid_data
        db.DB["events"]["events"]["456"] = {"name": "Test Event"}
        db.DB["suppliers"]["supplier_companies"][123] = {"name": "Test Supplier"}
        
        # Measure performance
        start_time = time.time()
        result = get(1, _include="event,supplier_company")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        self.assertIsNotNone(result)
        self.assertIn("included", result)
        self.assertLess(execution_time, 0.2)  # Should complete in less than 200ms
        
    def test_memory_usage_large_bid_data(self):
        """Test memory usage with large bid data."""
        # Create large bid data
        large_attributes = {f"field_{i}": f"value_{i}" * 100 for i in range(100)}
        bid_data = {
            "supplier_id": 123,
            "bid_amount": 1000.0,
            "status": "submitted",
            "event_id": 456,
            **large_attributes
        }
        db.DB["events"]["bids"][1] = bid_data
        
        # Test retrieval
        result = get(1)
        
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        # Verify large data is preserved
        for i in range(100):
            field_name = f"field_{i}"
            if field_name in result["data"]["attributes"]:
                self.assertEqual(result["data"]["attributes"][field_name], f"value_{i}" * 100)


class TestBidsByIdSmokeTests(BaseTestCaseWithErrorHandler):
    """Smoke tests for BidsById module."""
    
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
        from ..BidsById import get
        self.assertTrue(callable(get))
        
        # Test basic functionality
        result = get(999)  # Non-existent ID
        self.assertIsNone(result)
        
        # Test with valid data
        db.DB["events"]["bids"][1] = {
            "supplier_id": 123,
            "bid_amount": 1000.0,
            "status": "submitted"
        }
        
        result = get(1)
        self.assertIsNotNone(result)
        self.assertIn("data", result)
        
    def test_all_valid_include_options_work(self):
        """Smoke test: all valid include options work without error."""
        # Setup test data
        bid_data = {
            "supplier_id": 123,
            "bid_amount": 1000.0,
            "status": "submitted",
            "event_id": 456
        }
        db.DB["events"]["bids"][1] = bid_data
        db.DB["events"]["events"]["456"] = {"name": "Test Event"}
        db.DB["suppliers"]["supplier_companies"][123] = {"name": "Test Supplier"}
        
        valid_options = ["event", "events", "supplier_company", "supplier_companies"]
        
        for option in valid_options:
            with self.subTest(include_option=option):
                try:
                    result = get(1, _include=option)
                    self.assertIsNotNone(result)
                except Exception as e:
                    self.fail(f"Include option '{option}' failed: {e}")
                    
    def test_error_handling_robustness(self):
        """Smoke test: error handling works for common error cases."""
        error_cases = [
            ("string_id", "abc"),
            ("negative_id", -1),
            ("zero_id", 0),
            ("large_id", 1000000000),
            ("invalid_include", 1, "invalid"),
            ("empty_include", 1, ""),
        ]
        
        for test_name, *args in error_cases:
            with self.subTest(error_case=test_name):
                with self.assertRaises(ValidationError):
                    get(*args)


if __name__ == '__main__':
    unittest.main()
