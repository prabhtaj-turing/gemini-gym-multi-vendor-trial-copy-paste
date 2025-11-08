from linkedin.Posts import get_post, create_post
import linkedin as LinkedinAPI
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler

Posts_get_post = get_post
create_post = create_post

class TestPostsGetPost(BaseTestCaseWithErrorHandler):
    """Test suite for the refactored get_post function."""

    def setUp(self):
        """Reset DB state before each test and add a sample post."""
        reset_db()
        LinkedinAPI.DB["posts"] = {
            "urn:li:ugcPost:1": {
                "id": "urn:li:ugcPost:1",
                "author": "urn:li:person:test_author",
                "commentary": "This is a test post.",
                "visibility": "PUBLIC"
            },
            "urn:li:ugcPost:2": {
                "id": "urn:li:ugcPost:2",
                "author": "urn:li:organization:test_org",
                "commentary": "Another test post.",
                "visibility": "CONNECTIONS"
            }
        }

    def test_valid_input_post_found(self):
        """Test successful retrieval of an existing post with default parameters."""
        result = Posts_get_post(post_id="urn:li:ugcPost:1")     
        self.assertEqual(result["data"]["id"], "urn:li:ugcPost:1")
        self.assertEqual(result["data"]["commentary"], "This is a test post.")

    def test_valid_input_post_found_with_all_params(self):
        """Test successful retrieval with all optional parameters specified."""
        result = Posts_get_post(
            post_id="urn:li:ugcPost:2",
            projection="id,author", # Projection itself is not validated for format here beyond type
            start=0,
            count=5
        )
        self.assertEqual(result["data"]["id"], "urn:li:ugcPost:2")
        self.assertEqual(result["data"]["author"], "urn:li:organization:test_org")

    def test_post_not_found(self):
        """Test retrieval of a non-existent post."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=KeyError,
            expected_message="'Post not found with id: urn:li:ugcPost:999'",
            post_id="urn:li:ugcPost:999"
        )

    def test_invalid_post_id_type(self):
        """Test get_post with non-string post_id."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=TypeError,
            expected_message="post_id must be a string.",
            post_id=12345
        )

    def test_invalid_post_id_urn_format(self):
        """Test get_post with invalid URN format."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=ValueError,
            expected_message="post_id must be in URN format (e.g., 'urn:li:ugcPost:1'), but got 'invalid_id'.",
            post_id="invalid_id"
        )

    def test_invalid_post_id_wrong_urn_prefix(self):
        """Test get_post with wrong URN prefix."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=ValueError,
            expected_message="post_id must be in URN format (e.g., 'urn:li:ugcPost:1'), but got 'urn:li:person:1'.",
            post_id="urn:li:person:1"
        )

    def test_invalid_projection_type(self):
        """Test get_post with non-string projection."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=TypeError,
            expected_message="projection must be a string or None.",
            post_id="urn:li:ugcPost:1",
            projection=["id", "author"] # List instead of string
        )

    def test_valid_projection_none(self):
        """Test get_post with projection explicitly set to None."""
        result = Posts_get_post(post_id="urn:li:ugcPost:1", projection=None)
        self.assertEqual(result["data"]["id"], "urn:li:ugcPost:1")

    def test_invalid_start_type(self):
        """Test get_post with non-integer start."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=TypeError,
            expected_message="start must be an integer.",
            post_id="urn:li:ugcPost:1",
            start="0" # String instead of int
        )

    def test_invalid_start_value_negative(self):
        """Test get_post with negative start value."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=ValueError,
            expected_message="start must be a non-negative integer.",
            post_id="urn:li:ugcPost:1",
            start=-1
        )

    def test_valid_start_value_zero(self):
        """Test get_post with start value as 0."""
        result = Posts_get_post(post_id="urn:li:ugcPost:1", start=0)
        self.assertEqual(result["data"]["id"], "urn:li:ugcPost:1")

    def test_invalid_count_type(self):
        """Test get_post with non-integer count."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=TypeError,
            expected_message="count must be an integer.",
            post_id="urn:li:ugcPost:1",
            count="10" # String instead of int
        )

    def test_invalid_count_value_zero(self):
        """Test get_post with count value as 0."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=ValueError,
            expected_message="count must be a positive integer.",
            post_id="urn:li:ugcPost:1",
            count=0
        )

    def test_invalid_count_value_negative(self):
        """Test get_post with negative count value."""
        self.assert_error_behavior(
            func_to_call=Posts_get_post,
            expected_exception_type=ValueError,
            expected_message="count must be a positive integer.",
            post_id="urn:li:ugcPost:1",
            count=-5
        )
    
    def test_valid_count_value_positive(self):
        """Test get_post with a valid positive count."""
        result = Posts_get_post(post_id="urn:li:ugcPost:1", count=1)
        self.assertEqual(result["data"]["id"], "urn:li:ugcPost:1")

    def test_default_parameters_used(self):
        """Test that default parameters for projection, start, and count are used."""
        # This implicitly tests default by comparing to a call where defaults are explicit
        result_default = Posts_get_post(post_id="urn:li:ugcPost:1")
        result_explicit_defaults = Posts_get_post(
            post_id="urn:li:ugcPost:1",
            projection=None,
            start=0,
            count=10
        )
        self.assertEqual(result_default, result_explicit_defaults)
        self.assertEqual(result_default["data"]["id"], "urn:li:ugcPost:1")
    
    def test_valid_projection_with_square_brackets(self):
        """Test get_post with projection containing square brackets."""
        valid_data = {
            "author": "urn:li:person:12345",
            "commentary": "This is a valid post.",
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED"
        }
        post = create_post(
            post_data = valid_data
        )
        result = Posts_get_post(post_id=post["id"], projection="(id,author)")
        self.assertEqual(result["data"]["id"], post["id"])
        self.assertEqual(result["data"]["author"], valid_data["author"])

# Example of how to run tests if this script is executed directly (optional)
# if __name__ == '__main__':
#     unittest.main()
