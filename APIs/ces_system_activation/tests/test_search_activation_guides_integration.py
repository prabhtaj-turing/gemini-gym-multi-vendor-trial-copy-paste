import unittest
import os
import sys
import importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
from APIs.ces_system_activation.ces_system_activation import search_activation_guides
from APIs.ces_system_activation.SimulationEngine import search_engine

class TestSearchActivationGuidesIntegration(unittest.TestCase):
    def setUp(self):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.pinecone_api_key = os.environ.get("PINECONE_API_KEY")

        if not self.gemini_api_key or not self.pinecone_api_key:
            self.skipTest("GEMINI_API_KEY and PINECONE_API_KEY must be set to run integration tests.")
        
        reset_db()
        DB['activation_guides'] = {
            "TestGuide": "This is a test guide for semantic search."
        }
        # Reload the search_engine module to re-initialize the searcher with the new DB data
        importlib.reload(search_engine)

    def tearDown(self):
        reset_db()

    def test_semantic_search_on_db(self):
        # Perform a search and assert the results
        result = search_activation_guides("semantic search")
        self.assertIn("This is a test guide for semantic search.", result["answer"])
        self.assertGreaterEqual(len(result["snippets"]), 1)
        self.assertEqual(result["snippets"][0]["text"], "This is a test guide for semantic search.")
        self.assertEqual(result["snippets"][0]['title'], 'TestGuide')

if __name__ == '__main__':
    unittest.main()

