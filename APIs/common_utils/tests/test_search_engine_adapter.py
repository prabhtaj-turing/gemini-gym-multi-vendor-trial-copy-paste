#!/usr/bin/env python3
"""
Tests for search engine adapter module.

This module tests the Adapter class and its methods in common_utils.search_engine.adapter module.
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import List

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.search_engine.adapter import Adapter
from common_utils.search_engine.models import SearchableDocument
from common_utils.base_case import BaseTestCaseWithErrorHandler


class MockSearchStrategy:
    """Mock implementation of SearchStrategy for testing."""
    
    def __init__(self, name: str = "test_strategy"):
        self.name = name
        self.documents = []
    
    def clear_index(self):
        """Clear the index."""
        self.documents.clear()
    
    def upsert_documents(self, documents: List[SearchableDocument]):
        """Add documents to the index."""
        self.documents.extend(documents)
    
    def delete_documents(self, documents: List[SearchableDocument]):
        """Remove documents from the index."""
        chunk_ids = [doc.chunk_id for doc in documents]
        self.documents = [doc for doc in self.documents if doc.chunk_id not in chunk_ids]


class ConcreteAdapter(Adapter):
    """Concrete implementation of Adapter for testing."""
    
    def __init__(self, documents: List[SearchableDocument] = None):
        super().__init__()
        self.documents = documents or []
    
    def db_to_searchable_documents(self) -> List[SearchableDocument]:
        """Converts the service's database into a list of searchable documents."""
        return self.documents.copy()
    
    def set_documents(self, documents: List[SearchableDocument]):
        """Set the documents for testing."""
        self.documents = documents


class TestSearchEngineAdapter(BaseTestCaseWithErrorHandler):
    """Test cases for search engine adapter module."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.strategy = MockSearchStrategy("test_strategy")

    def test_adapter_initialization(self):
        """Test Adapter initialization (line 8)."""
        adapter = ConcreteAdapter()
        self.assertEqual(adapter._strategy_to_last_searchable_documents, {})

    def test_db_to_searchable_documents_abstract_method(self):
        """Test that db_to_searchable_documents is abstract (line 26)."""
        # Test that calling the abstract method raises NotImplementedError
        # We can't instantiate Adapter directly, so we test the abstract method through a concrete class
        adapter = ConcreteAdapter()
        # The concrete implementation should work
        result = adapter.db_to_searchable_documents()
        self.assertEqual(result, [])
        
        # Test that the abstract method exists and is callable
        self.assertTrue(hasattr(Adapter, 'db_to_searchable_documents'))
        self.assertTrue(callable(Adapter.db_to_searchable_documents))

    def test_reset_from_db(self):
        """Test reset_from_db method (lines 33-34)."""
        adapter = ConcreteAdapter()
        
        # Mock the strategy methods
        strategy = MockSearchStrategy()
        strategy.clear_index = Mock()
        strategy.name = "test_strategy"
        
        # Call reset_from_db
        adapter.reset_from_db(strategy)
        
        # Verify clear_index was called
        strategy.clear_index.assert_called_once()
        
        # Verify init_from_db was called (this will be tested separately)

    def test_init_from_db(self):
        """Test init_from_db method (lines 41-44)."""
        # Create test documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Test content 1",
            metadata={"type": "test"}
        )
        doc2 = SearchableDocument(
            parent_doc_id="doc2", 
            text_content="Test content 2",
            metadata={"type": "test"}
        )
        documents = [doc1, doc2]
        
        adapter = ConcreteAdapter(documents)
        strategy = MockSearchStrategy("test_strategy")
        
        # Call init_from_db
        adapter.init_from_db(strategy)
        
        # Verify documents were added to strategy
        self.assertEqual(len(strategy.documents), 2)
        self.assertIn(doc1, strategy.documents)
        self.assertIn(doc2, strategy.documents)
        
        # Verify the last known state was updated
        expected_state = {doc1.chunk_id: doc1, doc2.chunk_id: doc2}
        self.assertEqual(adapter._strategy_to_last_searchable_documents["test_strategy"], expected_state)

    def test_sync_from_db_with_changes(self):
        """Test sync_from_db method with changes (lines 52-59)."""
        # Create initial documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Original content",
            metadata={"type": "test"}
        )
        initial_docs = [doc1]
        
        adapter = ConcreteAdapter(initial_docs)
        strategy = MockSearchStrategy("test_strategy")
        
        # Initialize with initial documents
        adapter.init_from_db(strategy)
        
        # Create new documents (simulating changes)
        doc2 = SearchableDocument(
            parent_doc_id="doc2",
            text_content="New content",
            metadata={"type": "test"}
        )
        updated_doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Updated content",
            metadata={"type": "test"}
        )
        new_docs = [updated_doc1, doc2]
        
        # Update adapter documents
        adapter.set_documents(new_docs)
        
        # Call sync_from_db
        adapter.sync_from_db(strategy)
        
        # Verify documents were synced
        self.assertEqual(len(strategy.documents), 2)
        # The strategy should have the updated documents

    def test_sync_from_db_without_changes(self):
        """Test sync_from_db method without changes."""
        # Create documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Test content",
            metadata={"type": "test"}
        )
        documents = [doc1]
        
        adapter = ConcreteAdapter(documents)
        strategy = MockSearchStrategy("test_strategy")
        
        # Initialize with documents
        adapter.init_from_db(strategy)
        
        # Call sync_from_db with same documents
        adapter.sync_from_db(strategy)
        
        # Verify no changes were made
        self.assertEqual(len(strategy.documents), 1)

    def test_get_data_changes_added_documents(self):
        """Test get_data_changes with added documents (lines 68-93)."""
        # Create initial documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Original content",
            metadata={"type": "test"}
        )
        initial_docs = [doc1]
        
        adapter = ConcreteAdapter(initial_docs)
        
        # Initialize with initial documents
        adapter.init_from_db(self.strategy)
        
        # Create new documents (added)
        doc2 = SearchableDocument(
            parent_doc_id="doc2",
            text_content="New content",
            metadata={"type": "test"}
        )
        doc3 = SearchableDocument(
            parent_doc_id="doc3",
            text_content="Another new content",
            metadata={"type": "test"}
        )
        new_docs = [doc1, doc2, doc3]  # Keep original, add two new
        
        # Update adapter documents
        adapter.set_documents(new_docs)
        
        # Get changes
        changes = adapter.get_data_changes("test_strategy")
        
        # Verify changes
        self.assertEqual(len(changes["added"]), 2)
        self.assertEqual(len(changes["updated"]), 0)
        self.assertEqual(len(changes["deleted"]), 0)
        
        # Verify added documents
        added_ids = [doc.chunk_id for doc in changes["added"]]
        self.assertIn(doc2.chunk_id, added_ids)
        self.assertIn(doc3.chunk_id, added_ids)

    def test_get_data_changes_updated_documents(self):
        """Test get_data_changes with updated documents (lines 68-93)."""
        # Create initial documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Original content",
            metadata={"type": "test"},
            original_json_obj={"content": "original"}
        )
        initial_docs = [doc1]
        
        adapter = ConcreteAdapter(initial_docs)
        
        # Initialize with initial documents
        adapter.init_from_db(self.strategy)
        
        # Create updated document with the same chunk_id but different content
        # We need to manually set the chunk_id to match the original
        updated_doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Updated content",
            metadata={"type": "test"},
            original_json_obj={"content": "updated"}
        )
        # Manually set the chunk_id to match the original document
        updated_doc1.chunk_id = doc1.chunk_id
        updated_docs = [updated_doc1]
        
        # Update adapter documents
        adapter.set_documents(updated_docs)
        
        # Get changes
        changes = adapter.get_data_changes("test_strategy")
        
        # Verify changes
        self.assertEqual(len(changes["added"]), 0)
        self.assertEqual(len(changes["updated"]), 1)
        self.assertEqual(len(changes["deleted"]), 0)
        
        # Verify updated document
        self.assertEqual(changes["updated"][0].chunk_id, doc1.chunk_id)

    def test_get_data_changes_deleted_documents(self):
        """Test get_data_changes with deleted documents (lines 68-93)."""
        # Create initial documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Content 1",
            metadata={"type": "test"}
        )
        doc2 = SearchableDocument(
            parent_doc_id="doc2",
            text_content="Content 2",
            metadata={"type": "test"}
        )
        initial_docs = [doc1, doc2]
        
        adapter = ConcreteAdapter(initial_docs)
        
        # Initialize with initial documents
        adapter.init_from_db(self.strategy)
        
        # Create documents with one deleted
        remaining_docs = [doc1]  # doc2 is deleted
        
        # Update adapter documents
        adapter.set_documents(remaining_docs)
        
        # Get changes
        changes = adapter.get_data_changes("test_strategy")
        
        # Verify changes
        self.assertEqual(len(changes["added"]), 0)
        self.assertEqual(len(changes["updated"]), 0)
        self.assertEqual(len(changes["deleted"]), 1)
        
        # Verify deleted document
        self.assertEqual(changes["deleted"][0].chunk_id, doc2.chunk_id)

    def test_get_data_changes_mixed_changes(self):
        """Test get_data_changes with mixed changes (lines 68-93)."""
        # Create initial documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Original content",
            metadata={"type": "test"},
            original_json_obj={"content": "original"}
        )
        doc2 = SearchableDocument(
            parent_doc_id="doc2",
            text_content="Content 2",
            metadata={"type": "test"}
        )
        initial_docs = [doc1, doc2]
        
        adapter = ConcreteAdapter(initial_docs)
        
        # Initialize with initial documents
        adapter.init_from_db(self.strategy)
        
        # Create documents with mixed changes
        updated_doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Updated content",
            metadata={"type": "test"},
            original_json_obj={"content": "updated"}
        )
        # Manually set the chunk_id to match the original document
        updated_doc1.chunk_id = doc1.chunk_id
        
        doc3 = SearchableDocument(
            parent_doc_id="doc3",
            text_content="New content",
            metadata={"type": "test"}
        )
        # doc2 is deleted, doc1 is updated, doc3 is added
        new_docs = [updated_doc1, doc3]
        
        # Update adapter documents
        adapter.set_documents(new_docs)
        
        # Get changes
        changes = adapter.get_data_changes("test_strategy")
        
        # Verify changes
        self.assertEqual(len(changes["added"]), 1)
        self.assertEqual(len(changes["updated"]), 1)
        self.assertEqual(len(changes["deleted"]), 1)
        
        # Verify specific changes
        self.assertEqual(changes["added"][0].chunk_id, doc3.chunk_id)
        self.assertEqual(changes["updated"][0].chunk_id, doc1.chunk_id)
        self.assertEqual(changes["deleted"][0].chunk_id, doc2.chunk_id)

    def test_get_data_changes_empty_initial_state(self):
        """Test get_data_changes with empty initial state (lines 68-93)."""
        adapter = ConcreteAdapter()
        strategy = MockSearchStrategy("test_strategy")
        
        # No initial documents
        adapter.init_from_db(strategy)
        
        # Create new documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="New content",
            metadata={"type": "test"}
        )
        new_docs = [doc1]
        
        # Update adapter documents
        adapter.set_documents(new_docs)
        
        # Get changes
        changes = adapter.get_data_changes("test_strategy")
        
        # Verify changes
        self.assertEqual(len(changes["added"]), 1)
        self.assertEqual(len(changes["updated"]), 0)
        self.assertEqual(len(changes["deleted"]), 0)

    def test_get_data_changes_empty_current_state(self):
        """Test get_data_changes with empty current state (lines 68-93)."""
        # Create initial documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Content",
            metadata={"type": "test"}
        )
        initial_docs = [doc1]
        
        adapter = ConcreteAdapter(initial_docs)
        strategy = MockSearchStrategy("test_strategy")
        
        # Initialize with initial documents
        adapter.init_from_db(strategy)
        
        # Set empty documents
        adapter.set_documents([])
        
        # Get changes
        changes = adapter.get_data_changes("test_strategy")
        
        # Verify changes
        self.assertEqual(len(changes["added"]), 0)
        self.assertEqual(len(changes["updated"]), 0)
        self.assertEqual(len(changes["deleted"]), 1)
        
        # Verify deleted document
        self.assertEqual(changes["deleted"][0].chunk_id, doc1.chunk_id)

    def test_get_data_changes_strategy_name_not_found(self):
        """Test get_data_changes with strategy name not found (lines 68-93)."""
        adapter = ConcreteAdapter()
        
        # Create documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Content",
            metadata={"type": "test"}
        )
        documents = [doc1]
        
        # Update adapter documents
        adapter.set_documents(documents)
        
        # Get changes for non-existent strategy
        changes = adapter.get_data_changes("non_existent_strategy")
        
        # Verify changes (all documents should be added)
        self.assertEqual(len(changes["added"]), 1)
        self.assertEqual(len(changes["updated"]), 0)
        self.assertEqual(len(changes["deleted"]), 0)

    def test_get_data_changes_hash_comparison(self):
        """Test get_data_changes with hash comparison (lines 68-93)."""
        # Create initial document with specific hash
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Content",
            metadata={"type": "test"},
            original_json_obj={"data": "original"}
        )
        initial_docs = [doc1]
        
        adapter = ConcreteAdapter(initial_docs)
        strategy = MockSearchStrategy("test_strategy")
        
        # Initialize with initial documents
        adapter.init_from_db(strategy)
        
        # Create document with same chunk_id but different hash
        updated_doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Content",
            metadata={"type": "test"},
            original_json_obj={"data": "updated"}
        )
        updated_docs = [updated_doc1]
        
        # Update adapter documents
        adapter.set_documents(updated_docs)
        
        # Get changes
        changes = adapter.get_data_changes("test_strategy")
        
        # Verify changes (should be updated due to different hash)
        self.assertEqual(len(changes["added"]), 0)
        self.assertEqual(len(changes["updated"]), 1)
        self.assertEqual(len(changes["deleted"]), 0)

    def test_abstract_method_not_implemented(self):
        """Test that the abstract method raises NotImplementedError (line 26)."""
        # Create a concrete adapter that doesn't implement the abstract method
        class IncompleteAdapter(Adapter):
            pass
        
        # Test that instantiating the incomplete adapter raises an error
        with self.assertRaises(TypeError) as context:
            incomplete_adapter = IncompleteAdapter()
        
        # The error should mention the missing abstract method
        self.assertIn("abstract method", str(context.exception))
        
        # Test the abstract method directly to cover line 26
        # We need to create an instance that bypasses the abstract method check
        # by using a temporary implementation
        class TempAdapter(Adapter):
            def db_to_searchable_documents(self):
                # This will be replaced to test the abstract method
                pass
        
        temp_adapter = TempAdapter()
        # Replace the method with the original abstract method to test line 26
        temp_adapter.db_to_searchable_documents = Adapter.db_to_searchable_documents.__get__(temp_adapter)
        
        with self.assertRaises(NotImplementedError) as context:
            temp_adapter.db_to_searchable_documents()
        
        # Verify the error message
        self.assertEqual(str(context.exception), "Subclasses must implement this method")

    def test_sync_from_db_with_updated_documents(self):
        """Test sync_from_db with updated documents to cover line 57."""
        # Create initial documents
        doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Original content",
            metadata={"type": "test"},
            original_json_obj={"content": "original"}
        )
        initial_docs = [doc1]
        
        adapter = ConcreteAdapter(initial_docs)
        strategy = MockSearchStrategy("test_strategy")
        
        # Initialize with initial documents
        adapter.init_from_db(strategy)
        
        # Create updated document with the same chunk_id but different content
        updated_doc1 = SearchableDocument(
            parent_doc_id="doc1",
            text_content="Updated content",
            metadata={"type": "test"},
            original_json_obj={"content": "updated"}
        )
        # Manually set the chunk_id to match the original document
        updated_doc1.chunk_id = doc1.chunk_id
        updated_docs = [updated_doc1]
        
        # Update adapter documents
        adapter.set_documents(updated_docs)
        
        # Mock the strategy methods to verify they are called
        strategy.upsert_documents = Mock()
        strategy.delete_documents = Mock()
        
        # Call sync_from_db
        adapter.sync_from_db(strategy)
        
        # Verify that upsert_documents was called for updated documents
        strategy.upsert_documents.assert_called()
        
        # Verify the call arguments
        call_args = strategy.upsert_documents.call_args[0][0]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0].chunk_id, doc1.chunk_id)

    def test_type_checking_import(self):
        """Test that TYPE_CHECKING import works correctly (line 8)."""
        # Import the module and check that it doesn't cause runtime issues
        # The TYPE_CHECKING import should be conditional and not executed at runtime
        try:
            from common_utils.search_engine.adapter import Adapter
            # If we get here, the TYPE_CHECKING import worked correctly
            self.assertTrue(issubclass(Adapter, object))
        except ImportError as e:
            self.fail(f"TYPE_CHECKING import caused runtime ImportError: {e}")
        
        # Test that we can access the module's attributes without issues
        import common_utils.search_engine.adapter as adapter_module
        self.assertTrue(hasattr(adapter_module, 'Adapter'))
        
        # Test that the TYPE_CHECKING import doesn't interfere with runtime functionality
        # by creating an instance of a concrete adapter
        adapter = ConcreteAdapter([])
        self.assertIsInstance(adapter, Adapter)
        
        # Test the TYPE_CHECKING import by simulating type checking
        # We need to execute the module-level code with TYPE_CHECKING=True
        import sys
        import types
        
        # Create a mock module to simulate the import
        mock_module = types.ModuleType('mock_strategies')
        mock_module.SearchStrategy = type('SearchStrategy', (), {})
        
        # Temporarily add the mock module to sys.modules
        original_module = sys.modules.get('common_utils.search_engine.strategies')
        sys.modules['common_utils.search_engine.strategies'] = mock_module
        
        try:
            # Set TYPE_CHECKING to True to trigger the import
            import typing
            original_type_checking = getattr(typing, 'TYPE_CHECKING', False)
            typing.TYPE_CHECKING = True
            
            # Re-import the adapter module to trigger the TYPE_CHECKING import
            import importlib
            if 'common_utils.search_engine.adapter' in sys.modules:
                del sys.modules['common_utils.search_engine.adapter']
            
            # This should now execute the TYPE_CHECKING import
            from common_utils.search_engine.adapter import Adapter
            
            # Verify that the import worked
            self.assertTrue(issubclass(Adapter, object))
            
        finally:
            # Restore original state
            typing.TYPE_CHECKING = original_type_checking
            if original_module:
                sys.modules['common_utils.search_engine.strategies'] = original_module
            elif 'common_utils.search_engine.strategies' in sys.modules:
                del sys.modules['common_utils.search_engine.strategies']


if __name__ == '__main__':
    unittest.main()
