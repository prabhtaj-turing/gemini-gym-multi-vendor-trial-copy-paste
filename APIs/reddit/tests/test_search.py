import unittest
from datetime import datetime
import reddit as RedditAPI
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestSearch(BaseTestCaseWithErrorHandler):
    """
    Test cases for the Search class methods.
    Tests search functionality including basic search, filtering, sorting,
    pagination, and error handling.
    """

    def setUp(self):
        """
        Set up the test environment before each test.
        Resets the database and populates it with test data.
        """
        reset_db()

        # Set up test data
        RedditAPI.DB["links"] = [
            {
                "id": "1",
                "name": "t3_1",
                "title": "Python programming tutorial",
                "subreddit": "python",
                "created_utc": int(datetime.now().timestamp()) - 3600,  # 1 hour ago
                "num_comments": 10,
                "score": 100,
            },
            {
                "id": "2",
                "name": "t3_2",
                "title": "Advanced Python concepts",
                "subreddit": "python",
                "created_utc": int(datetime.now().timestamp()) - 86400,  # 1 day ago
                "num_comments": 5,
                "score": 50,
            },
            {
                "id": "3",
                "name": "t3_3",
                "title": "Java vs Python comparison",
                "subreddit": "programming",
                "created_utc": int(datetime.now().timestamp()) - 172800,  # 2 days ago
                "num_comments": 15,
                "score": 75,
            },
        ]

        RedditAPI.DB["subreddits"] = {
            "python": {
                "id": "t5_1",
                "name": "python",
                "display_name": "Python",
                "created_utc": int(datetime.now().timestamp()) - 2592000,  # 30 days ago
                "description": "A subreddit about Python programming",
            },
            "programming": {
                "id": "t5_2",
                "name": "programming",
                "display_name": "Programming",
                "created_utc": int(datetime.now().timestamp()) - 2592000,  # 30 days ago
                "description": "A subreddit about programming",
            },
        }

        RedditAPI.DB["users"] = {
            "python_dev": {
                "id": "t2_1",
                "name": "python_dev",
                "created_utc": int(datetime.now().timestamp()) - 2592000,  # 30 days ago
            }
        }

    def test_basic_search(self):
        """Test basic search functionality."""
        result = RedditAPI.Search.get_search(q="python")
        self.assertEqual(result["kind"], "Listing")
        self.assertIn("data", result)
        self.assertIn("children", result["data"])
        self.assertIn("modhash", result["data"])
        self.assertIn("after", result["data"])
        self.assertIn("before", result["data"])
        self.assertEqual(
            len(result["data"]["children"]), 5
        )  # All links containing "python"

    def test_time_filtering(self):
        """Test search with time filtering."""
        result = RedditAPI.Search.get_search(q="python", t="day")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 2)  # Posts from last day

    def test_time_filtering_comprehensive(self):
        """Test search with all time filtering options."""
        # Test hour filter
        result = RedditAPI.Search.get_search(q="python", t="hour")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 1)  # Only 1 hour old post
        
        # Test week filter
        result = RedditAPI.Search.get_search(q="python", t="week")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 3)  # All posts within week
        
        # Test month filter (includes subreddits and users created 30 days ago)
        result = RedditAPI.Search.get_search(q="python", t="month")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # All posts, subreddits, and users within month
        
        # Test year filter
        result = RedditAPI.Search.get_search(q="python", t="year")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # All items within year
        
        # Test all filter (no time restriction)
        result = RedditAPI.Search.get_search(q="python", t="all")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # All results

    def test_search_with_dictionary_format_links(self):
        """Test search when links are stored in dictionary format (new format)."""
        # Convert links to dictionary format
        old_links = RedditAPI.DB["links"]
        RedditAPI.DB["links"] = {
            "t3_1": old_links[0],
            "t3_2": old_links[1], 
            "t3_3": old_links[2]
        }
        
        result = RedditAPI.Search.get_search(q="python")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # Should still find all results
        
        # Check that IDs are preserved from dictionary keys
        link_results = [r for r in result["data"]["children"] if r["kind"] == "t3"]
        self.assertTrue(any(r["data"]["id"] == "t3_1" for r in link_results))

    def test_search_with_missing_fields(self):
        """Test search with posts missing optional fields."""
        # Add a post with minimal fields
        RedditAPI.DB["links"].append({
            "id": "4",
            "title": "Minimal Python post"
            # Missing created_utc, score, num_comments, etc.
        })
        
        result = RedditAPI.Search.get_search(q="python")
        self.assertEqual(result["kind"], "Listing")
        self.assertGreaterEqual(len(result["data"]["children"]), 5)

    def test_search_with_malformed_data(self):
        """Test search with malformed data in database."""
        # Add non-dictionary items to test robustness
        RedditAPI.DB["links"].extend(["invalid", None, 123])
        
        result = RedditAPI.Search.get_search(q="python")
        self.assertEqual(result["kind"], "Listing")
        # Should still work and ignore malformed entries
        self.assertGreaterEqual(len(result["data"]["children"]), 5)

    def test_sorting(self):
        """Test search with different sorting options."""
        # Test new sort
        result = RedditAPI.Search.get_search(q="python", sort="new")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(
            result["data"]["children"][0]["data"]["id"], "1"
        )  # Most recent first

        # Test top sort
        result = RedditAPI.Search.get_search(q="python", sort="top")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(
            result["data"]["children"][0]["data"]["id"], "1"
        )  # Highest score first

        # Test comments sort
        result = RedditAPI.Search.get_search(q="python", sort="comments")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(
            result["data"]["children"][0]["data"]["id"], "3"
        )  # Most comments first

        # Test hot sort
        result = RedditAPI.Search.get_search(q="python", sort="hot")
        self.assertEqual(result["kind"], "Listing")

    def test_relevance_sorting(self):
        """Test relevance sorting with multiple term matches."""
        # Add a post with many matching terms to outrank subreddit
        RedditAPI.DB["links"].append({
            "id": "4",
            "title": "Python Python Python Programming Programming Tutorial",  # 5 matches
            "text": "Learn Python programming with Python programming examples for Python development",  # 5 more matches
            "created_utc": int(datetime.now().timestamp()) - 1800,
            "score": 25,
            "num_comments": 8
        })
        
        result = RedditAPI.Search.get_search(q="python programming", sort="relevance")
        self.assertEqual(result["kind"], "Listing")
        # Post with multiple matches should rank higher than subreddit
        # Note: The subreddit "python" has ID "python" in test data
        # The new post has significantly more matches and should rank first
        self.assertEqual(result["data"]["children"][0]["data"]["id"], "4")

    def test_pagination(self):
        """Test search pagination functionality."""
        # Test limit parameter
        result = RedditAPI.Search.get_search(q="python", limit=2)
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 2)
        self.assertIsNotNone(result["data"]["after"])  # Should have next page

        # Test after parameter
        result = RedditAPI.Search.get_search(q="python", after="1")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 3)

        # Test before parameter
        result = RedditAPI.Search.get_search(q="python", before="3")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(
            len(result["data"]["children"]), 3
        )  # All results before id "3"

        # Test count parameter
        result = RedditAPI.Search.get_search(q="python", count=2)
        self.assertEqual(result["kind"], "Listing")

    def test_pagination_edge_cases(self):
        """Test pagination with edge cases."""
        # Test after with non-existent ID
        result = RedditAPI.Search.get_search(q="python", after="nonexistent")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # Should return all results
        
        # Test before with non-existent ID
        result = RedditAPI.Search.get_search(q="python", before="nonexistent")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # Should return all results
        
        # Test after with actual last item ID
        # First get all results to find the last item
        full_result = RedditAPI.Search.get_search(q="python", limit=100)
        if full_result["data"]["children"]:
            last_item_id = full_result["data"]["children"][-1]["data"]["id"]
            result = RedditAPI.Search.get_search(q="python", after=last_item_id)
            self.assertEqual(result["kind"], "Listing")
            self.assertEqual(len(result["data"]["children"]), 0)  # Should return empty

    def test_type_filtering(self):
        """Test search with type filtering."""
        result = RedditAPI.Search.get_search(q="python", type="sr")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 1)  # Only subreddits

    def test_type_filtering_comprehensive(self):
        """Test search with all type filtering options."""
        # Test link only
        result = RedditAPI.Search.get_search(q="python", type="link")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 3)  # Only links
        
        # Test user only  
        result = RedditAPI.Search.get_search(q="python", type="user")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 1)  # Only users
        
        # Test multiple types
        result = RedditAPI.Search.get_search(q="python", type="link,user")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 4)  # Links + users
        
        # Test with spaces in type parameter
        result = RedditAPI.Search.get_search(q="python", type="link, user, sr")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # All types

    def test_empty_query(self):
        """Test search with empty query."""
        result = RedditAPI.Search.get_search(q="")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 0)

    def test_no_results_query(self):
        """Test search with query that returns no results."""
        result = RedditAPI.Search.get_search(q="nonexistentterm12345")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 0)
        self.assertIsNone(result["data"]["after"])
        self.assertIsNone(result["data"]["before"])

    def test_search_in_text_fields(self):
        """Test search that matches in text fields of posts."""
        # Add a post with searchable text
        RedditAPI.DB["links"].append({
            "id": "5",
            "title": "Web Development Tutorial",
            "text": "Learn Python for web development using Flask and Django",
            "created_utc": int(datetime.now().timestamp()) - 3600,
            "score": 30,
            "num_comments": 7
        })
        
        result = RedditAPI.Search.get_search(q="flask")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 1)  # Should find the text match

    def test_case_insensitive_search(self):
        """Test that search is case insensitive."""
        result_lower = RedditAPI.Search.get_search(q="python")
        result_upper = RedditAPI.Search.get_search(q="PYTHON")
        result_mixed = RedditAPI.Search.get_search(q="PyThOn")
        
        self.assertEqual(len(result_lower["data"]["children"]), 
                        len(result_upper["data"]["children"]))
        self.assertEqual(len(result_lower["data"]["children"]), 
                        len(result_mixed["data"]["children"]))

    def test_empty_database(self):
        """Test search with empty database."""
        # Clear all data
        RedditAPI.DB["links"] = []
        RedditAPI.DB["subreddits"] = {}
        RedditAPI.DB["users"] = {}
        
        result = RedditAPI.Search.get_search(q="anything")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 0)

    def test_database_with_non_dict_collections(self):
        """Test search when database collections are not dictionaries."""
        # Test with missing collections
        del RedditAPI.DB["subreddits"]
        del RedditAPI.DB["users"]
        
        result = RedditAPI.Search.get_search(q="python")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 3)  # Only links

    def test_limit_boundary_values(self):
        """Test search with boundary limit values."""
        # Test minimum limit
        result = RedditAPI.Search.get_search(q="python", limit=1)
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 1)
        
        # Test maximum limit
        result = RedditAPI.Search.get_search(q="python", limit=100)
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)  # All available results

    def test_count_parameter_variations(self):
        """Test search with different count parameter values."""
        # Test zero count
        result = RedditAPI.Search.get_search(q="python", count=0)
        self.assertEqual(result["kind"], "Listing")
        
        # Test positive count
        result = RedditAPI.Search.get_search(q="python", count=10)
        self.assertEqual(result["kind"], "Listing")

    def test_all_optional_parameters(self):
        """Test search with all optional parameters set."""
        result = RedditAPI.Search.get_search(
            q="python",
            after=None,
            before=None,
            category="prog",
            count=0,
            include_facets=True,
            limit=10,
            restrict_sr=False,
            show="all",
            sort="relevance",
            sr_detail=True,
            t="all",
            type="link,sr,user"
        )
        self.assertEqual(result["kind"], "Listing")
        self.assertGreaterEqual(len(result["data"]["children"]), 0)

    def test_invalid_parameters(self):
        """Test search with invalid parameters."""
        with self.assertRaises(ValueError):
            RedditAPI.Search.get_search(q="python", sort="invalid")

        with self.assertRaises(ValueError):
            RedditAPI.Search.get_search(q="python", t="invalid")

        with self.assertRaises(ValueError):
            RedditAPI.Search.get_search(q="python", limit=101)  # Max limit is 100

        with self.assertRaises(ValueError):
            RedditAPI.Search.get_search(q="python", limit=0)  # Min limit is 1

        with self.assertRaises(ValueError):
            RedditAPI.Search.get_search(q="python", category="toolong")  # Max 5 chars

        with self.assertRaises(ValueError):
            RedditAPI.Search.get_search(q="python", count=-1)

        with self.assertRaises(ValueError):
            RedditAPI.Search.get_search(q="a" * 513)  # Max length is 512

    def test_query_length_boundary(self):
        """Test search with maximum query length."""
        result = RedditAPI.Search.get_search(q="a" * 512)
        self.assertEqual(result["kind"], "Listing")

    def test_additional_parameters(self):
        """Test search with additional parameters."""
        # Test category parameter
        result = RedditAPI.Search.get_search(q="python", category="prog")
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)

        # Test include_facets parameter
        result = RedditAPI.Search.get_search(q="python", include_facets=True)
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)

        # Test restrict_sr parameter
        result = RedditAPI.Search.get_search(q="python", restrict_sr=True)
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)

        # Test sr_detail parameter
        result = RedditAPI.Search.get_search(q="python", sr_detail=True)
        self.assertEqual(result["kind"], "Listing")
        self.assertEqual(len(result["data"]["children"]), 5)


if __name__ == "__main__":
    unittest.main()
