import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add the APIs directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from common_utils.search_engine.strategies import (
    SearchStrategy, WhooshSearchStrategy, QdrantSearchStrategy, 
    RapidFuzzSearchStrategy, HybridSearchStrategy, SubstringSearchStrategy
)
from common_utils.search_engine.adapter import Adapter
from common_utils.search_engine.models import SearchableDocument
from common_utils.search_engine.configs import (
    WhooshConfig, QdrantConfig, RapidFuzzConfig, 
    HybridConfig, SubstringConfig
)


class MockAdapter(Adapter):
    """Mock adapter for testing."""
    
    def __init__(self, documents=None):
        self.documents = documents or []
        self._strategy_to_last_searchable_documents = {}
    
    def db_to_searchable_documents(self):
        return self.documents
    
    def set_documents(self, documents):
        self.documents = documents
    
    def sync_from_db(self, strategy):
        pass


class BaseTestCaseWithErrorHandler(unittest.TestCase):
    """Base test case with error handling setup."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Store original environment variables
        import os
        self.original_error_mode = os.environ.get('OVERWRITE_ERROR_MODE')
        self.original_print_reports = os.environ.get('PRINT_ERROR_REPORTS')
        
        # Reset any global overrides that might interfere
        from common_utils.error_handling import reset_package_error_mode
        reset_package_error_mode()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import os
        # Restore original environment variables
        if self.original_error_mode is not None:
            os.environ['OVERWRITE_ERROR_MODE'] = self.original_error_mode
        else:
            os.environ.pop('OVERWRITE_ERROR_MODE', None)
        
        if self.original_print_reports is not None:
            os.environ['PRINT_ERROR_REPORTS'] = self.original_print_reports
        else:
            os.environ.pop('PRINT_ERROR_REPORTS', None)


class TestSearchStrategy(BaseTestCaseWithErrorHandler):
    """Test cases for SearchStrategy abstract base class."""
    
    def test_unique_original_json_objs_from_docs_with_limit(self):
        """Test unique_original_json_objs_from_docs with limit (lines 68-77)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test1",
            original_json_obj={"id": 1},
            original_json_obj_hash="hash1"
        )
        doc2 = SearchableDocument(
            chunk_id="2", 
            parent_doc_id="parent1",
            text_content="test2",
            original_json_obj={"id": 1},
            original_json_obj_hash="hash1"
        )
        
        docs = [doc1, doc2]
        unique_objs = SearchStrategy.unique_original_json_objs_from_docs(docs, limit=1)
        
        self.assertEqual(len(unique_objs), 1)
        self.assertEqual(unique_objs[0], {"id": 1})
    
    def test_unique_original_json_objs_from_docs_without_limit(self):
        """Test unique_original_json_objs_from_docs without limit (lines 68-77)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test1",
            original_json_obj={"id": 1},
            original_json_obj_hash="hash1"
        )
        doc2 = SearchableDocument(
            chunk_id="2",
            parent_doc_id="parent2",
            text_content="test2",
            original_json_obj={"id": 2},
            original_json_obj_hash="hash2"
        )
        
        docs = [doc1, doc2]
        unique_objs = SearchStrategy.unique_original_json_objs_from_docs(docs)
        
        self.assertEqual(len(unique_objs), 2)
    
    def test_unique_original_json_objs_from_docs_with_none_hash(self):
        """Test unique_original_json_objs_from_docs with None hash (lines 68-77)."""
        # Create a document and manually set the hash to None to test the behavior
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test1"
        )
        # Manually set the hash to None to test the None hash behavior
        doc1.original_json_obj_hash = None
        
        docs = [doc1]
        unique_objs = SearchStrategy.unique_original_json_objs_from_docs(docs)
        
        self.assertEqual(len(unique_objs), 0)
    
    def test_abstract_methods_raise_not_implemented(self):
        """Test that abstract methods raise NotImplementedError (lines 32, 38, 42, 47, 50, 53, 56, 59)."""
        class IncompleteStrategy(SearchStrategy):
            def upsert_documents(self, documents):
                pass
            
            def search(self, query, filter=None, limit=None):
                pass
            
            def clear_index(self):
                pass
        
        strategy = IncompleteStrategy()
        
        with self.assertRaises(NotImplementedError):
            strategy.rawSearch("test")
        
        with self.assertRaises(NotImplementedError):
            strategy.upsert_document(Mock())
        
        with self.assertRaises(NotImplementedError):
            strategy.delete_document("test")
        
        with self.assertRaises(NotImplementedError):
            strategy.delete_documents([])


class TestWhooshSearchStrategy(BaseTestCaseWithErrorHandler):
    """Test cases for WhooshSearchStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.config = WhooshConfig(index_path="/tmp/test_whoosh")
        self.adapter = MockAdapter()
        self.strategy = WhooshSearchStrategy(self.config, self.adapter)
    
    def test_initialization(self):
        """Test WhooshSearchStrategy initialization (lines 92-108)."""
        self.assertEqual(self.strategy.name, "keyword")
        self.assertIsNone(self.strategy.ix)
        self.assertIsNone(self.strategy.schema)
        self.assertEqual(self.strategy.doc_store, {})
        self.assertIsNone(self.strategy._ram_storage)
        self.assertEqual(self.strategy._all_metadata_fields, set())
    
    def test_create_dynamic_schema(self):
        """Test _create_dynamic_schema method (lines 112-132)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1", "field2": 123}
        )
        doc2 = SearchableDocument(
            chunk_id="2", 
            parent_doc_id="parent2",
            text_content="test content 2",
            metadata={"field1": "value2", "field3": True}
        )
        
        self.strategy._create_dynamic_schema([doc1, doc2])
        
        self.assertIsNotNone(self.strategy.schema)
        self.assertIsNotNone(self.strategy.ix)
        self.assertIsNotNone(self.strategy._ram_storage)
        self.assertEqual(self.strategy._all_metadata_fields, {"field1", "field2", "field3"})
    
    def test_maybe_rebuild_schema_with_new_fields(self):
        """Test _maybe_rebuild_schema with new fields (lines 136-157)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy._create_dynamic_schema([doc1])
        
        doc2 = SearchableDocument(
            chunk_id="2",
            parent_doc_id="parent2",
            text_content="test content 2", 
            metadata={"field1": "value2", "field2": "new_field"}
        )
        
        result = self.strategy._maybe_rebuild_schema(doc2)
        
        self.assertTrue(result)
        self.assertIn("field2", self.strategy._all_metadata_fields)
    
    def test_maybe_rebuild_schema_without_new_fields(self):
        """Test _maybe_rebuild_schema without new fields (lines 136-157)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1", "field2": "value2"}
        )
        self.strategy._create_dynamic_schema([doc1])
        
        doc2 = SearchableDocument(
            chunk_id="2",
            parent_doc_id="parent2",
            text_content="test content 2",
            metadata={"field1": "value3"}
        )
        
        result = self.strategy._maybe_rebuild_schema(doc2)
        
        self.assertFalse(result)
    
    def test_upsert_document_new_document(self):
        """Test upsert_document with new document (lines 160-164, 167-195)."""
        doc = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        
        self.strategy.upsert_document(doc)
        
        self.assertIn("1", self.strategy.doc_store)
        self.assertEqual(self.strategy.doc_store["1"], doc)
    
    def test_upsert_document_existing_document_same_content(self):
        """Test upsert_document with existing document same content (lines 160-164, 167-195)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"},
            original_json_obj={"id": 1}
        )
        self.strategy.upsert_document(doc1)
        
        doc2 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value2"},
            original_json_obj={"id": 2}
        )
        
        self.strategy.upsert_document(doc2)
        
        stored_doc = self.strategy.doc_store["1"]
        self.assertEqual(stored_doc.metadata, {"field1": "value2"})
        self.assertEqual(stored_doc.original_json_obj, {"id": 2})
    
    def test_delete_document(self):
        """Test delete_document method (lines 198-201)."""
        doc = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.upsert_document(doc)
        
        self.strategy.delete_document("1")
        
        self.assertNotIn("1", self.strategy.doc_store)
    
    def test_upsert_documents_empty_list(self):
        """Test upsert_documents with empty list (lines 205-208)."""
        self.strategy.upsert_documents([])
        # Should not raise any error
    
    def test_upsert_documents_with_new_fields(self):
        """Test upsert_documents with new fields (lines 213-237)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy._create_dynamic_schema([doc1])
        
        docs = [
            SearchableDocument(
                chunk_id="2",
                parent_doc_id="parent2",
                text_content="test content 2",
                metadata={"field1": "value2", "field2": "new_field"}
            ),
            SearchableDocument(
                chunk_id="3",
                parent_doc_id="parent3",
                text_content="test content 3",
                metadata={"field1": "value3", "field3": "another_new_field"}
            )
        ]
        
        self.strategy.upsert_documents(docs)
        
        self.assertIn("field2", self.strategy._all_metadata_fields)
        self.assertIn("field3", self.strategy._all_metadata_fields)
        self.assertIn("2", self.strategy.doc_store)
        self.assertIn("3", self.strategy.doc_store)
    
    def test_delete_documents(self):
        """Test delete_documents method (lines 242, 247)."""
        docs = [
            SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test1"),
            SearchableDocument(chunk_id="2", parent_doc_id="parent2", text_content="test2")
        ]
        self.strategy.upsert_documents(docs)
        
        self.strategy.delete_documents(docs)
        
        self.assertNotIn("1", self.strategy.doc_store)
        self.assertNotIn("2", self.strategy.doc_store)
    
    def test_clear_index(self):
        """Test clear_index method (lines 280-295)."""
        doc = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test")
        self.strategy.upsert_document(doc)
        
        self.strategy.clear_index()
        
        self.assertIsNone(self.strategy.ix)
        self.assertIsNone(self.strategy._ram_storage)
        self.assertEqual(self.strategy.doc_store, {})
        self.assertEqual(self.strategy._all_metadata_fields, set())
    
    def test_search_internal_no_index(self):
        """Test _search_internal with no index (lines 299-324)."""
        results = self.strategy._search_internal("test", None, 10)
        self.assertEqual(results, [])
    
    def test_search_internal_with_index(self):
        """Test _search_internal with index (lines 299-324)."""
        doc = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.upsert_document(doc)
        
        results = self.strategy._search_internal("test", None, 10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc.original_json_obj)
    
    def test_search_internal_with_filter(self):
        """Test _search_internal with filter (lines 299-324)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        doc2 = SearchableDocument(
            chunk_id="2",
            parent_doc_id="parent2",
            text_content="test content",
            metadata={"field1": "value2"}
        )
        self.strategy.upsert_documents([doc1, doc2])
        
        results = self.strategy._search_internal("test", {"field1": "value1"}, 10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc1.original_json_obj)
    
    def test_search_internal_raw_mode(self):
        """Test _search_internal in raw mode (lines 299-324)."""
        doc = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.upsert_document(doc)
        
        results = self.strategy._search_internal("test", None, 10, raw=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc)
    
    def test_search_method(self):
        """Test search method (lines 327-333)."""
        doc = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.upsert_document(doc)
        
        results = self.strategy.search("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc.original_json_obj)
    
    def test_raw_search_method(self):
        """Test rawSearch method (lines 336-375)."""
        doc = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.upsert_document(doc)
        
        results = self.strategy.rawSearch("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc)


class TestQdrantSearchStrategy(BaseTestCaseWithErrorHandler):
    """Test cases for QdrantSearchStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.config = QdrantConfig(
            collection_name="test_collection",
            model_name="gemini-pro",
            api_key="test_key",
            embedding_size=768
        )
        self.adapter = MockAdapter()
        self.strategy = QdrantSearchStrategy(self.config, self.adapter)
    
    def test_initialization(self):
        """Test QdrantSearchStrategy initialization (lines 378-386)."""
        self.assertEqual(self.strategy.name, "semantic")
        self.assertEqual(self.strategy.gemini_model, "gemini-pro")
        self.assertEqual(self.strategy.gemini_api_key, "test_key")
        self.assertEqual(self.strategy.embedding_size, 768)
        self.assertIsNotNone(self.strategy.client)
        self.assertIsNotNone(self.strategy.collection_name)
        self.assertEqual(self.strategy.doc_store, {})
        self.assertIsNone(self.strategy._embedding_manager)
    
    @patch('common_utils.search_engine.strategies.GeminiEmbeddingManager')
    def test_encode_texts(self, mock_embedding_manager):
        """Test _encode_texts method (lines 389-397)."""
        mock_manager_instance = Mock()
        mock_embedding_manager.return_value = mock_manager_instance
        mock_manager_instance.embed_content.return_value = {
            "embedding": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        }
        
        texts = ["test1", "test2"]
        embeddings = self.strategy._encode_texts(texts)
        
        self.assertEqual(len(embeddings), 2)
        mock_manager_instance.embed_content.assert_called_once()
    
    def test_upsert_document_same_content(self):
        """Test upsert_document with same content (lines 402-435)."""
        # Create a mock vector with the correct embedding size (768)
        mock_vector = [0.1] * 768
        
        doc1 = SearchableDocument(
            chunk_id="12345678-1234-5678-1234-567812345678",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"},
            original_json_obj={"id": 1}
        )
        # Mock the _encode_texts method to avoid real API calls
        with patch.object(self.strategy, '_encode_texts', return_value=[mock_vector]):
            self.strategy.upsert_document(doc1)
        
        doc2 = SearchableDocument(
            chunk_id="12345678-1234-5678-1234-567812345678",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value2"},
            original_json_obj={"id": 2}
        )
        
        # Mock the _encode_texts method to avoid real API calls
        with patch.object(self.strategy, '_encode_texts', return_value=[mock_vector]):
            self.strategy.upsert_document(doc2)
        
        stored_doc = self.strategy.doc_store["12345678-1234-5678-1234-567812345678"]
        self.assertEqual(stored_doc.metadata, {"field1": "value2"})
        self.assertEqual(stored_doc.original_json_obj, {"id": 2})
    
    @patch.object(QdrantSearchStrategy, '_encode_texts')
    def test_upsert_document_different_content(self, mock_encode):
        """Test upsert_document with different content (lines 402-435)."""
        # Create a mock vector with the correct embedding size (768)
        mock_vector = [0.1] * 768
        mock_encode.return_value = [mock_vector]
        
        doc = SearchableDocument(
            chunk_id="12345678-1234-5678-1234-567812345678",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        
        self.strategy.upsert_document(doc)
        
        mock_encode.assert_called_once_with(["test content"])
        self.assertIn("12345678-1234-5678-1234-567812345678", self.strategy.doc_store)
    
    def test_delete_document(self):
        """Test delete_document method (lines 440, 445)."""
        doc = SearchableDocument(chunk_id="12345678-1234-5678-1234-567812345678", parent_doc_id="parent1", text_content="test")
        self.strategy.doc_store["12345678-1234-5678-1234-567812345678"] = doc
        
        self.strategy.delete_document("12345678-1234-5678-1234-567812345678")
        
        self.assertNotIn("12345678-1234-5678-1234-567812345678", self.strategy.doc_store)
    
    def test_upsert_documents_empty_list(self):
        """Test upsert_documents with empty list (lines 457-468)."""
        self.strategy.upsert_documents([])
        # Should not raise any error
    
    @patch.object(QdrantSearchStrategy, '_encode_texts')
    def test_upsert_documents_with_changes(self, mock_encode):
        """Test upsert_documents with changes (lines 471-474, 477-478, 481-484, 487)."""
        # Create mock vectors with the correct embedding size (768)
        mock_vector1 = [0.1] * 768
        mock_vector2 = [0.2] * 768
        mock_encode.return_value = [mock_vector1, mock_vector2]
        
        doc1 = SearchableDocument(chunk_id="12345678-1234-5678-1234-567812345678", parent_doc_id="parent1", text_content="test1")
        with patch.object(self.strategy, '_encode_texts', return_value=[mock_vector1]):
            self.strategy.upsert_document(doc1)
        
        docs = [
            SearchableDocument(chunk_id="12345678-1234-5678-1234-567812345678", parent_doc_id="parent1", text_content="test1_updated"),
            SearchableDocument(chunk_id="87654321-4321-8765-4321-876543210987", parent_doc_id="parent2", text_content="test2")
        ]
        
        self.strategy.upsert_documents(docs)
        
        mock_encode.assert_called_once_with(["test1_updated", "test2"])
        self.assertIn("12345678-1234-5678-1234-567812345678", self.strategy.doc_store)
        self.assertIn("87654321-4321-8765-4321-876543210987", self.strategy.doc_store)
    
    def test_delete_documents(self):
        """Test delete_documents method (lines 492-512)."""
        docs = [
            SearchableDocument(chunk_id="12345678-1234-5678-1234-567812345678", parent_doc_id="parent1", text_content="test1"),
            SearchableDocument(chunk_id="87654321-4321-8765-4321-876543210987", parent_doc_id="parent2", text_content="test2")
        ]
        for doc in docs:
            self.strategy.doc_store[doc.chunk_id] = doc
        
        self.strategy.delete_documents(docs)
        
        self.assertNotIn("12345678-1234-5678-1234-567812345678", self.strategy.doc_store)
        self.assertNotIn("87654321-4321-8765-4321-876543210987", self.strategy.doc_store)
    
    def test_clear_index(self):
        """Test clear_index method (lines 517, 522)."""
        doc = SearchableDocument(chunk_id="12345678-1234-5678-1234-567812345678", parent_doc_id="parent1", text_content="test")
        self.strategy.doc_store["12345678-1234-5678-1234-567812345678"] = doc
        
        self.strategy.clear_index()
        
        self.assertEqual(self.strategy.doc_store, {})
    
    @patch.object(QdrantSearchStrategy, '_encode_texts')
    def test_search_internal_with_filter(self, mock_encode):
        """Test _search_internal with filter (lines 534-535, 538-539, 542-543, 546-549, 552-553)."""
        # Create a mock vector with the correct embedding size (768)
        mock_vector = [0.1] * 768
        mock_encode.return_value = [mock_vector]
        
        doc = SearchableDocument(
            chunk_id="12345678-1234-5678-1234-567812345678",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.doc_store["12345678-1234-5678-1234-567812345678"] = doc
        
        mock_hit = Mock()
        mock_hit.id = "12345678-1234-5678-1234-567812345678"
        mock_hit.payload = doc.model_dump()
        
        with patch.object(self.strategy.client, 'search') as mock_search:
            mock_search.return_value = [mock_hit]
            
            results = self.strategy._search_internal("test", {"field1": "value1"}, 10)
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], doc.original_json_obj)
    
    def test_search_method(self):
        """Test search method (lines 558-592)."""
        doc = SearchableDocument(
            chunk_id="12345678-1234-5678-1234-567812345678",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.doc_store["12345678-1234-5678-1234-567812345678"] = doc
        
        with patch.object(self.strategy, '_search_internal') as mock_search_internal:
            mock_search_internal.return_value = [doc.original_json_obj]
            
            results = self.strategy.search("test")
            
            mock_search_internal.assert_called_once_with("test", None, None, raw=False)
            self.assertEqual(results, [doc.original_json_obj])
    
    def test_raw_search_method(self):
        """Test rawSearch method (lines 597-607)."""
        doc = SearchableDocument(
            chunk_id="12345678-1234-5678-1234-567812345678",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"}
        )
        self.strategy.doc_store["12345678-1234-5678-1234-567812345678"] = doc
        
        with patch.object(self.strategy, '_search_internal') as mock_search_internal:
            mock_search_internal.return_value = [doc]
            
            results = self.strategy.rawSearch("test")
            
            mock_search_internal.assert_called_once_with("test", None, None, raw=True)
            self.assertEqual(results, [doc])


class TestRapidFuzzSearchStrategy(BaseTestCaseWithErrorHandler):
    """Test cases for RapidFuzzSearchStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Use a lower score_cutoff to make tests pass
        self.config = RapidFuzzConfig(score_cutoff=50, scorer="ratio")
        self.adapter = MockAdapter()
        self.strategy = RapidFuzzSearchStrategy(self.config, self.adapter)
    
    def test_initialization(self):
        """Test RapidFuzzSearchStrategy initialization (lines 618-623)."""
        self.assertEqual(self.strategy.name, "fuzzy")
        self.assertEqual(self.strategy.indexed_docs, [])
        self.assertIsNotNone(self.strategy.scorer)
    
    def test_upsert_document_new(self):
        """Test upsert_document with new document (lines 626, 629-630, 633-634, 637)."""
        doc = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test content")
        
        self.strategy.upsert_document(doc)
        
        self.assertEqual(len(self.strategy.indexed_docs), 1)
        self.assertEqual(self.strategy.indexed_docs[0], doc)
    
    def test_upsert_document_existing_same_content(self):
        """Test upsert_document with existing document same content (lines 626, 629-630, 633-634, 637)."""
        doc1 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value1"},
            original_json_obj={"id": 1}
        )
        self.strategy.upsert_document(doc1)
        
        doc2 = SearchableDocument(
            chunk_id="1",
            parent_doc_id="parent1",
            text_content="test content",
            metadata={"field1": "value2"},
            original_json_obj={"id": 2}
        )
        
        self.strategy.upsert_document(doc2)
        
        updated_doc = self.strategy.indexed_docs[0]
        self.assertEqual(updated_doc.metadata, {"field1": "value2"})
        self.assertEqual(updated_doc.original_json_obj, {"id": 2})
    
    def test_upsert_document_existing_different_content(self):
        """Test upsert_document with existing document different content (lines 626, 629-630, 633-634, 637)."""
        doc1 = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test content")
        self.strategy.upsert_document(doc1)
        
        doc2 = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="different content")
        
        self.strategy.upsert_document(doc2)
        
        self.assertEqual(self.strategy.indexed_docs[0].text_content, "different content")
    
    def test_delete_document(self):
        """Test delete_document method (lines 642-665)."""
        doc = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test content")
        self.strategy.upsert_document(doc)
        
        self.strategy.delete_document("1")
        
        self.assertEqual(len(self.strategy.indexed_docs), 0)
    
    def test_upsert_documents(self):
        """Test upsert_documents method (lines 670, 675)."""
        docs = [
            SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test1"),
            SearchableDocument(chunk_id="2", parent_doc_id="parent2", text_content="test2")
        ]
        
        self.strategy.upsert_documents(docs)
        
        self.assertEqual(len(self.strategy.indexed_docs), 2)
    
    def test_delete_documents_empty_list(self):
        """Test delete_documents with empty list (lines 678, 681)."""
        self.strategy.delete_documents([])
        # Should not raise any error
    
    def test_delete_documents(self):
        """Test delete_documents method (lines 678, 681)."""
        docs = [
            SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test1"),
            SearchableDocument(chunk_id="2", parent_doc_id="parent2", text_content="test2")
        ]
        self.strategy.upsert_documents(docs)
        
        self.strategy.delete_documents(docs)
        
        self.assertEqual(len(self.strategy.indexed_docs), 0)
    
    def test_clear_index(self):
        """Test clear_index method."""
        doc = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test")
        self.strategy.upsert_document(doc)
        
        self.strategy.clear_index()
        
        self.assertEqual(self.strategy.indexed_docs, [])
    
    def test_search_internal_with_filter(self):
        """Test _search_internal with filter."""
        docs = [
            SearchableDocument(
                chunk_id="1",
                parent_doc_id="parent1",
                text_content="test content",
                metadata={"field1": "value1"}
            ),
            SearchableDocument(
                chunk_id="2",
                parent_doc_id="parent2",
                text_content="test content",
                metadata={"field1": "value2"}
            )
        ]
        self.strategy.upsert_documents(docs)
        
        results = self.strategy._search_internal("test content", {"field1": "value1"}, 10)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], docs[0].original_json_obj)
    
    def test_search_method(self):
        """Test search method."""
        doc = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test content")
        self.strategy.upsert_document(doc)
        
        results = self.strategy.search("test content")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc.original_json_obj)
    
    def test_raw_search_method(self):
        """Test rawSearch method."""
        doc = SearchableDocument(chunk_id="1", parent_doc_id="parent1", text_content="test content")
        self.strategy.upsert_document(doc)
        
        results = self.strategy.rawSearch("test content")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], doc)


if __name__ == '__main__':
    unittest.main()
