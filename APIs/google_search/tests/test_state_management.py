#!/usr/bin/env python3
"""
Test cases for Google Search state management functions.
"""

import unittest
import tempfile
import json
import os
import sys

# Add APIs path to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from google_search.SimulationEngine.db import DB, save_state, load_state, get_database, reset_db
from google_search.SimulationEngine.db_models import GoogleSearchDB, WebContent, SearchIndexEntry
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGoogleSearchStateManagement(BaseTestCaseWithErrorHandler):
    """Test cases for Google Search state management functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear the database to ensure clean state for each test
        reset_db()
        
        # Create test data
        self.test_data = {
            "web_content": {
                "content_001": {
                    "url": "https://example.com/article1",
                    "title": "Test Article 1",
                    "snippet": "This is a test article about technology",
                    "content": "Full content of the test article about technology and innovation.",
                    "publication_time": "2024-01-15T10:30:00Z",
                    "tags": ["technology", "innovation"],
                    "keywords": ["tech", "AI", "innovation"]
                },
                "content_002": {
                    "url": "https://example.com/article2",
                    "title": "Test Article 2",
                    "snippet": "Another test article about science",
                    "content": "Full content of the second test article about science and research.",
                    "publication_time": "2024-01-16T14:45:00Z",
                    "tags": ["science", "research"],
                    "keywords": ["science", "research", "discovery"]
                }
            },
            "search_index": {
                "technology": {
                    "query_terms": ["technology"],
                    "content_ids": ["content_001"],
                    "relevance_scores": {"content_001": 0.95}
                },
                "science": {
                    "query_terms": ["science"],
                    "content_ids": ["content_002"],
                    "relevance_scores": {"content_002": 0.88}
                }
            },
            "recent_searches": [
                {"query": "technology trends", "result": "Found 5 articles about technology trends"},
                {"query": "science news", "result": "Found 3 articles about science news"}
            ]
        }

    def test_load_state_success(self):
        """Test successful loading of state from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            load_state(temp_file)
            
            # Verify the data was loaded correctly
            self.assertEqual(len(DB["web_content"]), 2)
            self.assertEqual(len(DB["search_index"]), 2)
            self.assertEqual(len(DB["recent_searches"]), 2)
            
            # Verify specific content
            self.assertIn("content_001", DB["web_content"])
            self.assertEqual(DB["web_content"]["content_001"]["title"], "Test Article 1")
            
        finally:
            os.unlink(temp_file)

    def test_load_state_file_not_found(self):
        """Test loading state from non-existent file."""
        original_db = DB.copy()
        load_state("nonexistent.json")
        self.assertEqual(DB, original_db)

    def test_load_state_invalid_json(self):
        """Test loading state from file with invalid JSON."""
        original_db = DB.copy()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{'invalid': json}")
            temp_file = f.name

        try:
            load_state(temp_file)
            self.assertEqual(DB, original_db)
        finally:
            os.unlink(temp_file)

    # def test_load_state_invalid_schema(self):
    #     """Test loading state with invalid schema."""
    #     invalid_data = {
    #         "web_content": {
    #             "invalid_content": {
    #                 "url": "https://example.com",
    #                 # Missing required fields: title, snippet, content
    #             }
    #         }
    #     }
        
    #     with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    #         json.dump(invalid_data, f)
    #         temp_file = f.name

    #     try:
    #         with self.assertRaises(ValueError) as context:
    #             load_state(temp_file)
    #         self.assertIn("Invalid database schema", str(context.exception))
    #     finally:
    #         os.unlink(temp_file)

    def test_save_state_success(self):
        """Test successful saving of state to file."""
        # Set up test data
        DB.clear()
        DB.update(self.test_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            save_state(temp_file)
            
            # Verify the file was created and contains correct data
            self.assertTrue(os.path.exists(temp_file))
            
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(len(saved_data["web_content"]), 2)
            self.assertEqual(len(saved_data["search_index"]), 2)
            self.assertEqual(len(saved_data["recent_searches"]), 2)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_state_invalid_path(self):
        """Test saving state to invalid path."""
        DB.clear()
        DB.update(self.test_data)
        
        with self.assertRaises(FileNotFoundError):
            save_state("/invalid/path/state.json")

    def test_get_database_returns_validated_model(self):
        """Test that get_database returns a validated Pydantic model."""
        # Set up test data
        DB.clear()
        DB.update(self.test_data)
        
        db_model = get_database()
        
        # Verify it's the correct type
        self.assertIsInstance(db_model, GoogleSearchDB)
        
        # Verify the data structure
        self.assertEqual(len(db_model.web_content), 2)
        self.assertEqual(len(db_model.search_index), 2)
        self.assertEqual(len(db_model.recent_searches), 2)

    def test_get_database_validates_data(self):
        """Test that get_database validates data against schema."""
        # Set up invalid data
        DB.clear()
        DB["web_content"] = {
            "invalid": {
                "url": "https://example.com",
                # Missing required fields
            }
        }
        
        with self.assertRaises(Exception):
            get_database()

    def test_get_database_with_empty_database(self):
        """Test get_database with empty database."""
        DB.clear()
        
        db_model = get_database()
        
        self.assertIsInstance(db_model, GoogleSearchDB)
        self.assertEqual(len(db_model.web_content), 0)
        self.assertEqual(len(db_model.search_index), 0)
        self.assertEqual(len(db_model.recent_searches), 0)

    def test_save_and_load_state_roundtrip(self):
        """Test saving and loading state maintains data integrity."""
        # Set up test data
        DB.clear()
        DB.update(self.test_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            # Save state
            save_state(temp_file)
            
            # Clear database
            DB.clear()
            self.assertEqual(len(DB), 0)
            
            # Load state
            load_state(temp_file)
            
            # Verify data integrity
            self.assertEqual(len(DB["web_content"]), 2)
            self.assertEqual(len(DB["search_index"]), 2)
            self.assertEqual(len(DB["recent_searches"]), 2)
            
            # Verify specific content
            self.assertEqual(DB["web_content"]["content_001"]["title"], "Test Article 1")
            self.assertEqual(DB["search_index"]["technology"]["query_terms"], ["technology"])
            self.assertEqual(DB["recent_searches"][0]["query"], "technology trends")
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_get_database_web_content_operations(self):
        """Test database model web content operations."""
        # Set up test data
        DB.clear()
        DB.update(self.test_data)
        
        db_model = get_database()
        
        # Test web content access
        web_content = db_model.web_content
        self.assertIn("content_001", web_content)
        self.assertIn("content_002", web_content)
        
        # Test web content structure
        content_001 = web_content["content_001"]
        self.assertEqual(content_001.title, "Test Article 1")
        self.assertEqual(content_001.url, "https://example.com/article1")
        self.assertEqual(content_001.tags, ["technology", "innovation"])

    def test_get_database_search_index_operations(self):
        """Test database model search index operations."""
        # Set up test data
        DB.clear()
        DB.update(self.test_data)
        
        db_model = get_database()
        
        # Test search index access
        search_index = db_model.search_index
        self.assertIn("technology", search_index)
        self.assertIn("science", search_index)
        
        # Test search index structure
        tech_index = search_index["technology"]
        self.assertEqual(tech_index.query_terms, ["technology"])
        self.assertEqual(tech_index.content_ids, ["content_001"])
        self.assertEqual(tech_index.relevance_scores["content_001"], 0.95)

    def test_get_database_recent_searches_operations(self):
        """Test database model recent searches operations."""
        # Set up test data
        DB.clear()
        DB.update(self.test_data)
        
        db_model = get_database()
        
        # Test recent searches access
        recent_searches = db_model.recent_searches
        self.assertEqual(len(recent_searches), 2)
        
        # Test recent searches structure
        first_search = recent_searches[0]
        self.assertEqual(first_search["query"], "technology trends")
        self.assertEqual(first_search["result"], "Found 5 articles about technology trends")

    def test_get_database_preserves_data_structure(self):
        """Test that get_database preserves the original data structure."""
        # Set up test data
        DB.clear()
        DB.update(self.test_data)
        
        db_model = get_database()
        
        # Verify the structure is preserved
        self.assertIsInstance(db_model.web_content, dict)
        self.assertIsInstance(db_model.search_index, dict)
        self.assertIsInstance(db_model.recent_searches, list)
        
        # Verify web content items are WebContent instances
        for content in db_model.web_content.values():
            self.assertIsInstance(content, WebContent)
        
        # Verify search index items are SearchIndexEntry instances
        for index in db_model.search_index.values():
            self.assertIsInstance(index, SearchIndexEntry)


if __name__ == "__main__":
    unittest.main()
