import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestSubredditsMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Subreddits class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create a test subreddit for use across tests
        adm = RedditAPI.Subreddits.post_api_site_admin("MyTestSub", "A Title")
        self.subreddit_name = "MyTestSub"

    def test_get_about_banned(self):
        """Test getting banned users."""
        banned = RedditAPI.Subreddits.get_about_banned()
        self.assertIsInstance(banned, list)

    def test_get_about_contributors(self):
        """Test getting contributors."""
        cont = RedditAPI.Subreddits.get_about_contributors()
        self.assertIsInstance(cont, list)

    def test_get_about_moderators(self):
        """Test getting moderators."""
        mods = RedditAPI.Subreddits.get_about_moderators()
        self.assertIsInstance(mods, list)

    def test_get_about_muted(self):
        """Test getting muted users."""
        muted = RedditAPI.Subreddits.get_about_muted()
        self.assertIsInstance(muted, list)

    def test_get_about_wikibanned(self):
        """Test getting wiki banned users."""
        wb = RedditAPI.Subreddits.get_about_wikibanned()
        self.assertIsInstance(wb, list)

    def test_get_about_wikicontributors(self):
        """Test getting wiki contributors."""
        wc = RedditAPI.Subreddits.get_about_wikicontributors()
        self.assertIsInstance(wc, list)

    def test_get_about_where(self):
        """Test getting users by where parameter."""
        wh = RedditAPI.Subreddits.get_about_where("banned")
        self.assertEqual(wh["where"], "banned")
        self.assertIn("users", wh)

    def test_delete_banner(self):
        """Test deleting subreddit banner."""
        del_ban = RedditAPI.Subreddits.post_api_delete_sr_banner()
        self.assertEqual(del_ban["status"], "sr_banner_deleted")

    def test_delete_header(self):
        """Test deleting subreddit header."""
        del_hdr = RedditAPI.Subreddits.post_api_delete_sr_header()
        self.assertEqual(del_hdr["status"], "sr_header_deleted")

    def test_delete_icon(self):
        """Test deleting subreddit icon."""
        del_icon = RedditAPI.Subreddits.post_api_delete_sr_icon()
        self.assertEqual(del_icon["status"], "sr_icon_deleted")

    def test_delete_image(self):
        """Test deleting subreddit image."""
        del_img = RedditAPI.Subreddits.post_api_delete_sr_img("banner.png")
        self.assertEqual(del_img["status"], "sr_image_deleted")

    def test_get_recommendations(self):
        """Test getting subreddit recommendations."""
        rec = RedditAPI.Subreddits.get_api_recommend_sr_srnames(
            "python,learnprogramming"
        )
        self.assertIn("recommendations_for", rec)

    def test_search_reddit_names(self):
        """Test searching reddit names."""
        srn = RedditAPI.Subreddits.get_api_search_reddit_names("sometest")
        self.assertTrue(srn["available"])

    def test_search_subreddits(self):
        """Test searching subreddits."""
        srsub = RedditAPI.Subreddits.post_api_search_subreddits("something")
        self.assertIn("results", srsub)

    def test_search_subreddits_validation_empty_input(self):
        """Test validation for empty input."""
        with self.assertRaises(ValueError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits("")
        self.assertEqual(str(context.exception), "No search query provided.")

    def test_search_subreddits_validation_none_input(self):
        """Test validation for None input."""
        with self.assertRaises(TypeError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits(None)  # type: ignore
        self.assertEqual(str(context.exception), "Query must be a string.")

    def test_search_subreddits_validation_integer_input(self):
        """Test validation for integer input."""
        with self.assertRaises(TypeError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits(123)  # type: ignore
        self.assertEqual(str(context.exception), "Query must be a string.")

    def test_search_subreddits_validation_list_input(self):
        """Test validation for list input."""
        with self.assertRaises(TypeError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits(["test"])  # type: ignore
        self.assertEqual(str(context.exception), "Query must be a string.")

    def test_search_subreddits_validation_dict_input(self):
        """Test validation for dictionary input."""
        with self.assertRaises(TypeError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits({"query": "test"})  # type: ignore
        self.assertEqual(str(context.exception), "Query must be a string.")

    def test_search_subreddits_validation_whitespace_only(self):
        """Test validation for whitespace-only input."""
        with self.assertRaises(ValueError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits("   ")
        self.assertEqual(str(context.exception), "No search query provided.")

    def test_search_subreddits_validation_too_long(self):
        """Test validation for query that is too long (over 50 characters)."""
        long_query = "a" * 51
        with self.assertRaises(ValueError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits(long_query)
        self.assertEqual(str(context.exception), "Search query too long. Maximum 50 characters allowed.")

    def test_search_subreddits_validation_exact_length_limit(self):
        """Test validation for query at exact length limit (50 characters)."""
        exact_length_query = "a" * 50
        result = RedditAPI.Subreddits.post_api_search_subreddits(exact_length_query)
        self.assertIn("query", result)
        self.assertEqual(result["query"], exact_length_query)

    def test_search_subreddits_validation_non_printable_characters(self):
        """Test validation for non-printable characters."""
        # Test with null character
        non_printable_query = "python\x00test"
        with self.assertRaises(ValueError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits(non_printable_query)
        self.assertEqual(str(context.exception), "Search query contains invalid characters.")

    def test_search_subreddits_validation_control_characters(self):
        """Test validation for control characters."""
        # Test with truly non-printable control characters
        control_chars_query = "python\x00test\x01\x02"
        with self.assertRaises(ValueError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits(control_chars_query)
        self.assertEqual(str(context.exception), "Search query contains invalid characters.")

    def test_search_subreddits_validation_valid_printable_characters(self):
        """Test validation for valid printable characters."""
        # Test with various printable characters
        printable_chars = "python123!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = RedditAPI.Subreddits.post_api_search_subreddits(printable_chars)
        self.assertIn("query", result)
        self.assertEqual(result["query"], printable_chars)

    def test_search_subreddits_validation_whitespace_handling(self):
        """Test validation for whitespace handling."""
        result = RedditAPI.Subreddits.post_api_search_subreddits("  python  ")
        self.assertIn("query", result)
        self.assertEqual(result["query"], "python")

    def test_search_subreddits_validation_special_characters(self):
        """Test validation for special characters in query."""
        special_chars = "python@reddit#test"
        result = RedditAPI.Subreddits.post_api_search_subreddits(special_chars)
        self.assertIn("query", result)
        self.assertEqual(result["query"], special_chars)

    def test_search_subreddits_validation_numbers(self):
        """Test validation for numeric query."""
        numeric_query = "12345"
        result = RedditAPI.Subreddits.post_api_search_subreddits(numeric_query)
        self.assertIn("query", result)
        self.assertEqual(result["query"], numeric_query)

    def test_search_subreddits_validation_mixed_content(self):
        """Test validation for mixed content query."""
        mixed_query = "python123_test"
        result = RedditAPI.Subreddits.post_api_search_subreddits(mixed_query)
        self.assertIn("query", result)
        self.assertEqual(result["query"], mixed_query)

    def test_search_subreddits_validation_single_character(self):
        """Test validation for single character query."""
        single_char = "a"
        result = RedditAPI.Subreddits.post_api_search_subreddits(single_char)
        self.assertIn("query", result)
        self.assertEqual(result["query"], single_char)

    def test_search_subreddits_search_by_name(self):
        """Test searching subreddits by name."""
        # Create test subreddits
        RedditAPI.Subreddits.post_api_site_admin("python", "Python Programming")
        RedditAPI.Subreddits.post_api_site_admin("javascript", "JavaScript Programming")
        
        # Search for "python" - should find matches since we're searching by name
        result = RedditAPI.Subreddits.post_api_search_subreddits("python")
        self.assertIn("query", result)
        self.assertEqual(result["query"], "python")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "python")
        self.assertEqual(result["results"][0]["title"], "Python Programming")

    def test_search_subreddits_search_by_title(self):
        """Test searching subreddits by title."""
        # Create test subreddits
        RedditAPI.Subreddits.post_api_site_admin("coding", "Programming Community")
        RedditAPI.Subreddits.post_api_site_admin("gaming", "Gaming Community")
        
        # Search for "programming" - should find one match by title
        result = RedditAPI.Subreddits.post_api_search_subreddits("programming")
        self.assertIn("query", result)
        self.assertEqual(result["query"], "programming")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "coding")

    def test_search_subreddits_search_by_description(self):
        """Test searching subreddits by description."""
        # Create test subreddits with descriptions
        subreddits = RedditAPI.DB.get("subreddits", {})
        subreddits["tech"] = {"title": "Technology", "description": "Latest tech news and discussions"}
        subreddits["science"] = {"title": "Science", "description": "Scientific discoveries and research"}
        RedditAPI.DB["subreddits"] = subreddits
        
        # Search for "discussions" - should find one match in the description
        result = RedditAPI.Subreddits.post_api_search_subreddits("discussions")
        self.assertIn("query", result)
        self.assertEqual(result["query"], "discussions")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "tech")

    def test_search_subreddits_case_insensitive(self):
        """Test that search is case insensitive."""
        # Create test subreddit
        RedditAPI.Subreddits.post_api_site_admin("Python", "Python Programming")
        
        # Search with different cases
        result = RedditAPI.Subreddits.post_api_search_subreddits("python")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "Python")

    def test_search_subreddits_no_matches(self):
        """Test search when no subreddits match the query."""
        result = RedditAPI.Subreddits.post_api_search_subreddits("nonexistent")
        self.assertIn("query", result)
        self.assertEqual(result["query"], "nonexistent")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 0)

    def test_search_subreddits_multiple_matches(self):
        """Test search when multiple subreddits match the query."""
        # Create test subreddits
        RedditAPI.Subreddits.post_api_site_admin("python", "Python Programming")
        RedditAPI.Subreddits.post_api_site_admin("python_help", "Python Help")
        RedditAPI.Subreddits.post_api_site_admin("javascript", "JavaScript Programming")
        
        # Search for "python"
        result = RedditAPI.Subreddits.post_api_search_subreddits("python")
        self.assertIn("query", result)
        self.assertEqual(result["query"], "python")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 2)
        
        # Check that both python subreddits are returned
        names = [r["name"] for r in result["results"]]
        self.assertIn("python", names)
        self.assertIn("python_help", names)

    def test_search_subreddits_exact_match(self):
        """Test exact search for subreddits."""
        RedditAPI.Subreddits.post_api_site_admin("python", "Python Programming")
        RedditAPI.Subreddits.post_api_site_admin("python_help", "Python Help")
        
        result = RedditAPI.Subreddits.post_api_search_subreddits("python", exact=True)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "python")

    def test_search_subreddits_exact_no_match(self):
        """Test exact search with no matching subreddits."""
        RedditAPI.Subreddits.post_api_site_admin("python_help", "Python Help")
        
        result = RedditAPI.Subreddits.post_api_search_subreddits("python", exact=True)
        self.assertEqual(len(result["results"]), 0)

    def test_search_subreddits_include_over18_true(self):
        """Test search including over-18 subreddits."""
        subreddits = RedditAPI.DB.get("subreddits", {})
        subreddits["nsfw_python"] = {"title": "NSFW Python", "over18": True, "description": ""}
        RedditAPI.DB["subreddits"] = subreddits
        
        result = RedditAPI.Subreddits.post_api_search_subreddits("python", include_over18=True)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "nsfw_python")

    def test_search_subreddits_include_over18_false(self):
        """Test search excluding over-18 subreddits."""
        subreddits = RedditAPI.DB.get("subreddits", {})
        subreddits["nsfw_python"] = {"title": "NSFW Python", "over18": True, "description": ""}
        subreddits["sfw_python"] = {"title": "SFW Python", "over18": False, "description": ""}
        RedditAPI.DB["subreddits"] = subreddits
        
        result = RedditAPI.Subreddits.post_api_search_subreddits("python", include_over18=False)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "sfw_python")

    def test_search_subreddits_validation_invalid_exact_type(self):
        """Test validation for invalid type for 'exact' parameter."""
        with self.assertRaises(TypeError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits("test", exact="true")  # type: ignore
        self.assertEqual(str(context.exception), "'exact' must be a boolean.")

    def test_search_subreddits_validation_invalid_include_over18_type(self):
        """Test validation for invalid type for 'include_over18' parameter."""
        with self.assertRaises(TypeError) as context:
            RedditAPI.Subreddits.post_api_search_subreddits("test", include_over18="true")  # type: ignore
        self.assertEqual(str(context.exception), "'include_over18' must be a boolean.")

    def test_search_subreddits_empty_database(self):
        """Test search when database is empty."""
        # Clear the database
        RedditAPI.DB["subreddits"] = {}
        
        result = RedditAPI.Subreddits.post_api_search_subreddits("anything")
        self.assertIn("query", result)
        self.assertEqual(result["query"], "anything")
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 0)

    def test_create_subreddit(self):
        """Test creating a subreddit."""
        adm = RedditAPI.Subreddits.post_api_site_admin("MyTestSub", "A Title")
        self.assertEqual(adm["status"], "subreddit_created_or_edited")
        # Verify creation in DB
        self.assertIn("MyTestSub", RedditAPI.DB["subreddits"])
        self.assertEqual(RedditAPI.DB["subreddits"]["MyTestSub"]["title"], "A Title")

    def test_get_submit_text(self):
        """Test getting submit text."""
        stxt = RedditAPI.Subreddits.get_api_submit_text("MyTestSub")
        self.assertIn("submit_text", stxt)

    def test_get_autocomplete(self):
        """Test getting subreddit autocomplete."""
        auto = RedditAPI.Subreddits.get_api_subreddit_autocomplete("myquery")
        self.assertIsInstance(auto, list)

    def test_get_autocomplete_v2(self):
        """Test getting subreddit autocomplete v2."""
        auto_v2 = RedditAPI.Subreddits.get_api_subreddit_autocomplete_v2()
        self.assertIsInstance(auto_v2, list)

    def test_save_stylesheet(self):
        """Test saving subreddit stylesheet."""
        style = RedditAPI.Subreddits.post_api_subreddit_stylesheet(
            "save", "body{color:red}"
        )
        self.assertEqual(style["status"], "stylesheet_saved")

    def test_subscribe(self):
        """Test subscribing to a subreddit."""
        sub_ = RedditAPI.Subreddits.post_api_subscribe("sub", "MyTestSub")
        self.assertEqual(sub_["status"], "subscribed")

    def test_upload_image(self):
        """Test uploading subreddit image."""
        mock_file = {
            "filename": "header.jpg",
            "content_type": "image/jpeg",
            "data": b"...",
        }
        upl = RedditAPI.Subreddits.post_api_upload_sr_img("image_name", file=mock_file)
        self.assertEqual(upl["status"], "image_uploaded")

    def test_get_post_requirements(self):
        """Test getting post requirements."""
        req = RedditAPI.Subreddits.get_api_v1_subreddit_post_requirements("MyTestSub")
        self.assertIn("requirements", req)

    def test_get_about(self):
        """Test getting subreddit about info."""
        abt = RedditAPI.Subreddits.get_r_subreddit_about("MyTestSub")
        self.assertIn("info", abt)
        self.assertEqual(abt["info"]["title"], "A Title")

    def test_get_about_edit(self):
        """Test getting subreddit about edit info."""
        abt_ed = RedditAPI.Subreddits.get_r_subreddit_about_edit()
        self.assertIn("edit_info", abt_ed)

    def test_get_about_rules(self):
        """Test getting subreddit rules."""
        abt_rules = RedditAPI.Subreddits.get_r_subreddit_about_rules()
        self.assertIsInstance(abt_rules, list)

    def test_get_about_traffic(self):
        """Test getting subreddit traffic stats."""
        abt_traffic = RedditAPI.Subreddits.get_r_subreddit_about_traffic()
        self.assertIn("traffic_stats", abt_traffic)

    def test_get_sidebar(self):
        """Test getting subreddit sidebar."""
        sbar = RedditAPI.Subreddits.get_sidebar()
        self.assertIn("Sidebar", sbar)

    def test_get_sticky(self):
        """Test getting subreddit sticky posts."""
        stk = RedditAPI.Subreddits.get_sticky()
        self.assertTrue(len(stk) >= 1)

    def test_get_default_subreddits(self):
        """Test getting default subreddits."""
        defs = RedditAPI.Subreddits.get_subreddits_default()
        self.assertIsInstance(defs, list)

    def test_get_gold_subreddits(self):
        """Test getting gold subreddits."""
        gold = RedditAPI.Subreddits.get_subreddits_gold()
        self.assertIsInstance(gold, list)

    def test_get_my_contributor_subreddits(self):
        """Test getting my contributor subreddits."""
        contr_list = RedditAPI.Subreddits.get_subreddits_mine_contributor()
        self.assertIsInstance(contr_list, list)

    def test_get_my_moderator_subreddits(self):
        """Test getting my moderator subreddits."""
        mod_list = RedditAPI.Subreddits.get_subreddits_mine_moderator()
        self.assertIsInstance(mod_list, list)

    def test_get_my_streams(self):
        """Test getting my streams."""
        streams = RedditAPI.Subreddits.get_subreddits_mine_streams()
        self.assertIsInstance(streams, list)

    def test_get_my_subscriber_subreddits(self):
        """Test getting my subscriber subreddits."""
        subscr = RedditAPI.Subreddits.get_subreddits_mine_subscriber()
        self.assertIsInstance(subscr, list)

    def test_get_my_subreddits_where(self):
        """Test getting my subreddits by where parameter."""
        mswhere = RedditAPI.Subreddits.get_subreddits_mine_where("moderator")
        self.assertIsInstance(mswhere, list)

    def test_get_new_subreddits(self):
        """Test getting new subreddits."""
        newsubs = RedditAPI.Subreddits.get_subreddits_new()
        self.assertIsInstance(newsubs, list)

    def test_get_popular_subreddits(self):
        """Test getting popular subreddits."""
        pop = RedditAPI.Subreddits.get_subreddits_popular()
        self.assertIsInstance(pop, list)

    def test_search_subreddits_list(self):
        """Test searching subreddits list."""
        ssearch = RedditAPI.Subreddits.get_subreddits_search("test")
        self.assertIsInstance(ssearch, list)

    def test_get_subreddits_where(self):
        """Test getting subreddits by where parameter."""
        swhere = RedditAPI.Subreddits.get_subreddits_where("popular")
        self.assertIsInstance(swhere, list)

    def test_get_new_users(self):
        """Test getting new users."""
        unew = RedditAPI.Subreddits.get_users_new()
        self.assertIsInstance(unew, list)

    def test_get_popular_users(self):
        """Test getting popular users."""
        upop = RedditAPI.Subreddits.get_users_popular()
        self.assertIsInstance(upop, list)

    def test_search_users(self):
        """Test searching users."""
        usearch = RedditAPI.Subreddits.get_users_search()
        self.assertIsInstance(usearch, list)

    def test_get_users_where(self):
        """Test getting users by where parameter."""
        uwhere = RedditAPI.Subreddits.get_users_where("new")
        self.assertIsInstance(uwhere, list)


if __name__ == "__main__":
    unittest.main()
