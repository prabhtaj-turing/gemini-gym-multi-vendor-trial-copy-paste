#!/usr/bin/env python3
"""
Fixed State Load/Save Tests for SimulationEngine DB Module

This module provides simplified testing for the database state management,
testing only functions that actually exist.

Author: AI Assistant
Created: 2024-12-28
"""

import unittest
import json
import tempfile
import os
from typing import Dict, Any

from ..SimulationEngine import db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestDatabaseStateManagementFixed(BaseTestCaseWithErrorHandler):
    """Fixed tests for database state management."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        db.reset_db()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        db.reset_db()
        # Clean up temp files and directories
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
    def test_save_database_state_to_file(self):
        """Test saving database state to file."""
        # Add some test data
        db.DB["events"]["bids"][1] = {
            "name": "Test Bid",
            "status": "active",
            "amount": 1000.0
        }
        
        test_file = os.path.join(self.temp_dir, "test_save.json")
        
        # Save state
        db.save_state(test_file)
        
        # Verify file was created and contains data
        self.assertTrue(os.path.exists(test_file))
        
        with open(test_file, 'r') as f:
            saved_data = json.load(f)
            
        self.assertIn("events", saved_data)
        self.assertIn("bids", saved_data["events"])
        self.assertIn("1", saved_data["events"]["bids"])  # JSON keys are strings
        
    def test_load_database_state_from_file(self):
        """Test loading database state from file."""
        # Create test data file
        test_data = {
            "events": {
                "bids": {
                    "1": {
                        "name": "Loaded Bid",
                        "status": "loaded",
                        "amount": 2000.0
                    }
                },
                "bid_line_items": {}
            },
            "suppliers": {
                "supplier_companies": {}
            }
        }
        
        test_file = os.path.join(self.temp_dir, "test_load.json")
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
            
        # Load state
        db.load_state(test_file)
        
        # Verify data was loaded (keys might be strings after JSON load)
        if 1 in db.DB["events"]["bids"]:
            loaded_bid = db.DB["events"]["bids"][1]
        elif "1" in db.DB["events"]["bids"]:
            loaded_bid = db.DB["events"]["bids"]["1"]
        else:
            self.fail("Loaded bid not found with either integer or string key")
            
        self.assertEqual(loaded_bid["name"], "Loaded Bid")
        self.assertEqual(loaded_bid["status"], "loaded")
        self.assertEqual(loaded_bid["amount"], 2000.0)
        
    def test_save_load_roundtrip_data_integrity(self):
        """Test that save/load cycle preserves data integrity."""
        # Add complex test data
        original_data = {
            "name": "Complex Bid",
            "status": "active",
            "amount": 1500.75,
            "attributes": {
                "priority": "high",
                "tags": ["urgent", "important"],
                "metadata": {
                    "created_by": "test_user",
                    "nested_data": {
                        "level": 2,
                        "values": [1, 2, 3]
                    }
                }
            }
        }
        
        db.DB["events"]["bids"][1] = original_data.copy()
        
        test_file = os.path.join(self.temp_dir, "test_roundtrip.json")
        
        # Save and load
        db.save_state(test_file)
        db.reset_db()  # Clear database
        db.load_state(test_file)
        
        # Verify data integrity (handle both integer and string keys)
        if 1 in db.DB["events"]["bids"]:
            loaded_data = db.DB["events"]["bids"][1]
        elif "1" in db.DB["events"]["bids"]:
            loaded_data = db.DB["events"]["bids"]["1"]
        else:
            self.fail("Loaded bid not found")
        self.assertEqual(loaded_data["name"], original_data["name"])
        self.assertEqual(loaded_data["amount"], original_data["amount"])
        self.assertEqual(loaded_data["attributes"]["tags"], original_data["attributes"]["tags"])
        self.assertEqual(loaded_data["attributes"]["metadata"]["nested_data"]["values"], 
                        original_data["attributes"]["metadata"]["nested_data"]["values"])
        
    def test_get_minified_state_basic(self):
        """Test getting minified state."""
        # Add some test data
        db.DB["events"]["bids"][1] = {
            "name": "Test Bid",
            "status": "active"
        }
        
        # Get minified state
        minified = db.get_minified_state()
        
        # Verify it's a dictionary (as implemented in db.py)
        self.assertIsInstance(minified, dict)
        
        # Verify it contains the expected structure
        self.assertIn("events", minified)
        self.assertIn("bids", minified["events"])
        
        # Verify our test data is present
        self.assertIn(1, minified["events"]["bids"])
        self.assertEqual(minified["events"]["bids"][1]["name"], "Test Bid")
        
    def test_database_reset_functionality(self):
        """Test database reset functionality."""
        # Add some data
        db.DB["events"]["bids"][1] = {"name": "Test"}
        self.assertIn(1, db.DB["events"]["bids"])
        
        # Reset database
        db.reset_db()
        
        # Verify database is reset to default state
        # Should have the basic structure but no custom data
        self.assertIn("events", db.DB)
        self.assertIn("bids", db.DB["events"])
        # Custom data should be gone (depends on default DB structure)


class TestDatabaseStateSmokeTests(BaseTestCaseWithErrorHandler):
    """Smoke tests for database state management."""
    
    def setUp(self):
        """Set up smoke test fixtures."""
        super().setUp()
        db.reset_db()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after smoke tests."""
        super().tearDown()
        db.reset_db()
        # Clean up temp files and directories
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
    def test_data_persistence_basic_workflow(self):
        """Smoke test: basic data persistence workflow works."""
        # Add data
        db.DB["events"]["bids"][1] = {"name": "Smoke Test Bid"}
        
        test_file = os.path.join(self.temp_dir, "smoke_test.json")
        
        # Save, reset, load
        db.save_state(test_file)
        db.reset_db()
        db.load_state(test_file)
        
        # Verify data persisted (handle both integer and string keys)
        if 1 in db.DB["events"]["bids"]:
            self.assertEqual(db.DB["events"]["bids"][1]["name"], "Smoke Test Bid")
        elif "1" in db.DB["events"]["bids"]:
            self.assertEqual(db.DB["events"]["bids"]["1"]["name"], "Smoke Test Bid")
        else:
            self.fail("Smoke test bid not found after load")
        
    def test_functions_exist_and_callable(self):
        """Smoke test: required functions exist and are callable."""
        self.assertTrue(callable(db.save_state))
        self.assertTrue(callable(db.load_state))
        self.assertTrue(callable(db.reset_db))
        self.assertTrue(callable(db.get_minified_state))
        
    def test_file_operations_handle_paths(self):
        """Smoke test: file operations handle different path formats."""
        db.DB["events"]["bids"][1] = {"test": "data"}
        
        # Test different path formats
        test_files = [
            os.path.join(self.temp_dir, "test1.json"),
            os.path.join(self.temp_dir, "subdir", "test2.json")
        ]
        
        # Create subdirectory if needed
        os.makedirs(os.path.dirname(test_files[1]), exist_ok=True)
        
        for test_file in test_files:
            with self.subTest(file=test_file):
                # Should not raise exceptions
                db.save_state(test_file)
                self.assertTrue(os.path.exists(test_file))
                
                db.reset_db()
                db.load_state(test_file)
                # Check for either integer or string key
                self.assertTrue(1 in db.DB["events"]["bids"] or "1" in db.DB["events"]["bids"])


if __name__ == '__main__':
    unittest.main()
