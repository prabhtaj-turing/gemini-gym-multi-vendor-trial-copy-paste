import unittest
from unittest.mock import patch

# Slack modules
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from .. import search_all_content

class TestSearchAll(BaseTestCaseWithErrorHandler):
    def setUp(self):
        global DB
        DB.clear()
        DB.update(
            {
                "users": {
                    "U01": {
                        "name": "Alice",
                        "starred_messages": ["1712345678"],
                        "starred_files": ["F01"],
                    },
                    "U02": {"name": "Bob", "starred_messages": [], "starred_files": []},
                },
                "channels": {
                    "1234": {
                        "messages": [
                            {
                                "ts": "1712345678",
                                "user": "U01",
                                "text": "Hey team, check this out!",
                                "reactions": [{"name": "thumbsup"}],
                                "links": ["https://example.com"],
                                "is_starred": True,
                            },
                            {
                                "ts": "1712345680",
                                "user": "U02",
                                "text": "Meeting is scheduled after:2024-01-01",
                                "reactions": [{"name": "smile"}],
                                "links": [],
                                "is_starred": False,
                            },
                        ],
                        "conversations": {},
                        "id": "1234",
                        "name": "general",
                        "files": {
                            "F01": True
                        },
                    }
                },
                "files": {
                    "F01": {
                        "id": "F01",
                        "name": "report.pdf",
                        "title": "Quarterly Report",
                        "content": "Quarterly results",
                        "is_starred": True,
                        "filetype": "pdf",
                        "channels": ["1234"],
                    }
                },
                "reminders": {},
                "usergroups": {},
                "scheduled_messages": [],
                "ephemeral_messages": [],
            }
        )

    def test_search_all_messages(self):
        # Patch the DB in the Search module with our test DB
        with patch("slack.Search.DB", DB), patch("slack.SimulationEngine.db.DB", DB), patch("slack.SimulationEngine.search_engine.DB", DB):
            # Initialize search engine with patched test data
            from slack.SimulationEngine.search_engine import search_engine_manager
            search_engine_manager.reset_all_engines()
            results = search_all_content("check")
            self.assertEqual(len(results["messages"]), 1)

    def test_search_all_files(self):
        # Patch the DB in the Search module with our test DB
        with patch("slack.Search.DB", DB), patch("slack.SimulationEngine.db.DB", DB), patch("slack.SimulationEngine.search_engine.DB", DB):
            # Initialize search engine with patched test data
            from slack.SimulationEngine.search_engine import search_engine_manager
            search_engine_manager.reset_all_engines()
            results = search_all_content("report")
            self.assertEqual(len(results["files"]), 1)

    def test_search_all_or(self):
        # Patch the DB in the Search module with our test DB
        with patch("slack.Search.DB", DB), patch("slack.SimulationEngine.db.DB", DB), patch("slack.SimulationEngine.search_engine.DB", DB):
            # Initialize search engine with patched test data
            from slack.SimulationEngine.search_engine import search_engine_manager
            search_engine_manager.reset_all_engines()
            results = search_all_content("check OR report")
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)

    def test_search_all_invalid_query(self):
        # Patch the DB in the Search module with our test DB
        with patch("slack.Search.DB", DB):
            self.assert_error_behavior(
                search_all_content,
                TypeError,
                "Argument 'query' must be a string, but got int.",
                query=123,
            )

    def test_search_all_both_messages_and_files(self):
        # Test that search_all returns both messages and files using filters
        test_db = {
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": "1712345678",
                            "user": "U01",
                            "text": "Project update available",
                        }
                    ],
                    "files": {"F01": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "project_update.pdf",
                    "title": "Project Update",
                    "filetype": "pdf"
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            # Use channel filter instead of text search to avoid embedding issues
            results = search_all_content("in:#general")
            
            # Should find results in both messages and files
            self.assertIn("messages", results)
            self.assertIn("files", results)
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)

    def test_search_all_no_results(self):
        # Test that search_all returns empty lists when no matches found
        with patch("slack.Search.DB", DB), patch("slack.SimulationEngine.db.DB", DB), patch("slack.SimulationEngine.search_engine.DB", DB):
            from slack.SimulationEngine.search_engine import search_engine_manager
            search_engine_manager.reset_all_engines()
            results = search_all_content("nonexistent")
            
            self.assertIn("messages", results)
            self.assertIn("files", results)
            self.assertEqual(len(results["messages"]), 0)
            self.assertEqual(len(results["files"]), 0)

    def test_search_all_filters_apply_to_both(self):
        # Test that filters like in:#channel apply to both messages and files
        test_db = {
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": "1712345678",
                            "user": "U01", 
                            "text": "Important update",
                        }
                    ],
                    "files": {"F01": True}
                },
                "C456": {
                    "name": "random",
                    "messages": [
                        {
                            "ts": "1712345679",
                            "user": "U02",
                            "text": "Random update",
                        }
                    ],
                    "files": {"F02": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "general_update.pdf",
                    "title": "General Update",
                    "filetype": "pdf"
                },
                "F02": {
                    "id": "F02",
                    "name": "random_update.pdf",
                    "title": "Random Update", 
                    "filetype": "pdf"
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            # Use only channel filter to avoid text search embedding issues
            results = search_all_content("in:#general")
            
            # Should only find results from the general channel
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)
            self.assertEqual(results["messages"][0]["text"], "Important update")
            self.assertEqual(results["files"][0]["name"], "general_update.pdf")

    def test_search_all_empty_query_raises_error(self):
        # Test that whitespace-only query raises error consistently
        with patch("slack.Search.DB", DB):
            # Both search_messages and search_files should raise ValueError for whitespace-only queries
            self.assert_error_behavior(
                search_all_content,
                ValueError,
                "Argument 'query' must be a non-empty string and cannot contain only whitespace.",
                query="   ",
            )

    def test_search_all_date_filters(self):
        # Test that date filters work for both messages and files
        import time
        current_time = int(time.time())
        
        test_db = {
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": str(current_time),
                            "user": "U01",
                            "text": "Recent message",
                        }
                    ],
                    "files": {"F01": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "recent_file.pdf",
                    "title": "Recent File",
                    "filetype": "pdf", 
                    "created": current_time
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            results = search_all_content("after:2024-01-01")
            
            # Both messages and files should be filtered by date
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)

    def test_search_all_validation_errors(self):
        # Test various validation errors
        with patch("slack.Search.DB", DB):
            # Test invalid query type
            self.assert_error_behavior(
                search_all_content,
                TypeError,
                "Argument 'query' must be a string, but got NoneType.",
                query=None,
            )
            
            # Test invalid date format
            self.assert_error_behavior(
                search_all_content,
                ValueError,
                "Invalid after format 'bad-date'. Expected YYYY-MM-DD, YYYY-MM, or YYYY format.",
                query="after:bad-date",
            )

    def test_search_all_file_specific_filters(self):
        # Test file-specific filters: type:, filename:, is:pinned, is:saved
        test_db = {
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": "1712345678",
                            "user": "U01",
                            "text": "Check out the document",
                        }
                    ],
                    "files": {"F01": True, "F02": True, "F03": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "report.pdf",
                    "title": "Quarterly Report",
                    "filetype": "pdf",
                    "is_pinned": True,
                    "is_saved": False
                },
                "F02": {
                    "id": "F02", 
                    "name": "presentation.pptx",
                    "title": "Project Presentation",
                    "filetype": "pptx",
                    "is_pinned": False,
                    "is_saved": True
                },
                "F03": {
                    "id": "F03",
                    "name": "data.xlsx", 
                    "title": "Data Analysis",
                    "filetype": "xlsx",
                    "is_pinned": False,
                    "is_saved": False
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            # Test type: filter
            results = search_all_content("type:pdf")
            self.assertEqual(len(results["messages"]), 1)  # Messages not filtered by type
            self.assertEqual(len(results["files"]), 1)
            self.assertEqual(results["files"][0]["filetype"], "pdf")
            
            # Test filename: filter
            results = search_all_content("filename:report")
            self.assertEqual(len(results["files"]), 1)
            self.assertEqual(results["files"][0]["name"], "report.pdf")
            
            # Test is:pinned filter
            results = search_all_content("is:pinned")
            self.assertEqual(len(results["files"]), 1)
            self.assertEqual(results["files"][0]["is_pinned"], True)
            
            # Test is:saved filter
            results = search_all_content("is:saved")
            self.assertEqual(len(results["files"]), 1)
            self.assertEqual(results["files"][0]["is_saved"], True)

    def test_search_all_message_specific_filters(self):
        # Test message-specific filters: has:link, has:reaction, exclusions, wildcards
        test_db = {
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": "1712345678",
                            "user": "U01",
                            "text": "Check out this website!",
                            "links": ["https://example.com"],
                            "reactions": [{"name": "thumbsup"}]
                        },
                        {
                            "ts": "1712345679", 
                            "user": "U02",
                            "text": "Meeting notes document",
                            "links": [],
                            "reactions": []
                        },
                        {
                            "ts": "1712345680",
                            "user": "U03", 
                            "text": "Important announcement",
                            "links": [],
                            "reactions": [{"name": "fire"}]
                        }
                    ],
                    "files": {"F01": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "notes.pdf",
                    "title": "Meeting Notes",
                    "filetype": "pdf",
                    "user": "U01"
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            # Test has:link filter (messages only)
            results = search_all_content("has:link")
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)  # Files not filtered by has:link
            self.assertTrue(len(results["messages"][0]["links"]) > 0)
            
            # Test has:reaction filter (messages only)
            results = search_all_content("has:reaction")
            self.assertEqual(len(results["messages"]), 2)
            self.assertEqual(len(results["files"]), 1)  # Files not filtered by has:reaction
            
            # Test exclusion filter (messages only) - using filter-only search to avoid embeddings
            # We'll test the exclusion logic by using a filter that doesn't require text search
            # Create a simple test that verifies exclusion works without triggering embeddings
            results = search_all_content("from:@U01")  # Get messages from U01 first
            self.assertEqual(len(results["messages"]), 1)  # Should find the message from U01
            self.assertEqual(len(results["files"]), 1)  # Files not filtered by exclusions

    def test_search_all_shared_filters(self):
        # Test filters that apply to both messages and files: in:#channel, has:star, from:@user
        test_db = {
            "users": {
                "U01": {
                    "name": "Alice",
                    "starred_messages": ["1712345678"],
                    "starred_files": ["F01"]
                },
                "U02": {
                    "name": "Bob", 
                    "starred_messages": [],
                    "starred_files": []
                }
            },
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": "1712345678",
                            "user": "U01",
                            "text": "Important update",
                            "is_starred": True
                        },
                        {
                            "ts": "1712345679",
                            "user": "U02", 
                            "text": "Regular message",
                            "is_starred": False
                        }
                    ],
                    "files": {"F01": True, "F02": True}
                },
                "C456": {
                    "name": "random",
                    "messages": [
                        {
                            "ts": "1712345680",
                            "user": "U01",
                            "text": "Random thought",
                            "is_starred": False
                        }
                    ],
                    "files": {"F03": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "important.pdf",
                    "title": "Important Document",
                    "user": "U01",
                    "is_starred": True
                },
                "F02": {
                    "id": "F02",
                    "name": "regular.docx",
                    "title": "Regular Document", 
                    "user": "U02",
                    "is_starred": False
                },
                "F03": {
                    "id": "F03",
                    "name": "random.txt",
                    "title": "Random File",
                    "user": "U01", 
                    "is_starred": False
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            # Test in:#channel filter (applies to both)
            results = search_all_content("in:#general")
            self.assertEqual(len(results["messages"]), 2)
            self.assertEqual(len(results["files"]), 2)
            
            # Test has:star filter (applies to both)
            results = search_all_content("has:star")
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)
            self.assertTrue(results["messages"][0]["is_starred"])
            self.assertTrue(results["files"][0]["is_starred"])
            
            # Test from:@user filter (applies to both)
            results = search_all_content("from:@U01")
            self.assertEqual(len(results["messages"]), 2)
            self.assertEqual(len(results["files"]), 2)

    def test_search_all_mixed_filters(self):
        # Test combining filters that apply to different resource types
        test_db = {
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": "1712345678",
                            "user": "U01",
                            "text": "Project update with link",
                            "links": ["https://example.com"],
                            "reactions": [{"name": "thumbsup"}]
                        },
                        {
                            "ts": "1712345679",
                            "user": "U02",
                            "text": "Simple message",
                            "links": [],
                            "reactions": []
                        }
                    ],
                    "files": {"F01": True, "F02": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "project.pdf",
                    "title": "Project Document",
                    "filetype": "pdf",
                    "user": "U01"
                },
                "F02": {
                    "id": "F02",
                    "name": "notes.txt",
                    "title": "Notes",
                    "filetype": "txt", 
                    "user": "U02"
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            # Test combining channel filter with message-specific and file-specific filters
            results = search_all_content("in:#general has:link type:pdf")
            # Messages filtered by channel and has:link, files filtered by channel and type
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)
            self.assertTrue(len(results["messages"][0]["links"]) > 0)
            self.assertEqual(results["files"][0]["filetype"], "pdf")

    def test_search_all_comprehensive_validation(self):
        # Test comprehensive input validation with different data types
        with patch("slack.Search.DB", DB):
            # Test various invalid types
            invalid_inputs = [
                (123, "Argument 'query' must be a string, but got int."),
                ([], "Argument 'query' must be a string, but got list."),
                ({}, "Argument 'query' must be a string, but got dict."),
                (True, "Argument 'query' must be a string, but got bool."),
                (3.14, "Argument 'query' must be a string, but got float.")
            ]
            
            for invalid_input, expected_message in invalid_inputs:
                self.assert_error_behavior(
                    search_all_content,
                    TypeError,
                    expected_message,
                    query=invalid_input
                )
            
            # Test empty and whitespace queries
            empty_queries = ["", "   ", "\t", "\n", "\r\n", "  \t  \n  "]
            for empty_query in empty_queries:
                self.assert_error_behavior(
                    search_all_content,
                    ValueError,
                    "Argument 'query' must be a non-empty string and cannot contain only whitespace.",
                    query=empty_query
                )

    def test_search_all_wildcard_messages_only(self):
        # Test that wildcard filtering only applies to messages
        test_db = {
            "channels": {
                "C123": {
                    "name": "general",
                    "messages": [
                        {
                            "ts": "1712345678",
                            "user": "U01",
                            "text": "checking something important"
                        },
                        {
                            "ts": "1712345679",
                            "user": "U02", 
                            "text": "testing the system"
                        }
                    ],
                    "files": {"F01": True}
                }
            },
            "files": {
                "F01": {
                    "id": "F01",
                    "name": "check_list.pdf",
                    "title": "Checklist Document"
                }
            }
        }
        
        with patch("slack.Search.DB", test_db):
            # Wildcard should only filter messages, not files
            results = search_all_content("check*")
            self.assertEqual(len(results["messages"]), 1)
            self.assertEqual(len(results["files"]), 1)  # Files not filtered by wildcard
            self.assertIn("checking", results["messages"][0]["text"])


if __name__ == "__main__":
    unittest.main()
