import pytest
from unittest.mock import patch
from youtube.Comment import list as list_comments

# Sample comments to be used in tests
SAMPLE_COMMENTS = {
    "comment1": {
        "id": "comment1",
        "snippet": {"textDisplay": "This is the first comment.", "parentId": None},
        "moderationStatus": "published",
        "bannedAuthor": False,
    },
    "comment2": {
        "id": "comment2",
        "snippet": {
            "textDisplay": "A <b>second</b> comment with <br/> HTML.",
            "parentId": None,
        },
        "moderationStatus": "heldForReview",
        "bannedAuthor": True,
    },
    "reply1_to_comment1": {
        "id": "reply1_to_comment1",
        "snippet": {"textDisplay": "This is a reply.", "parentId": "comment1"},
        "moderationStatus": "published",
        "bannedAuthor": False,
    },
}


@pytest.fixture
def mock_db():
    """Fixture to mock the DB before each test."""
    with patch("youtube.Comment.DB", {"comments": SAMPLE_COMMENTS.copy()}) as _mock_db:
        yield _mock_db


def test_list_all_comments_with_all_parts(mock_db):
    """Test retrieving all comments with all parts specified."""
    result = list_comments(part="id,snippet,moderationStatus,bannedAuthor")
    assert "items" in result
    assert len(result["items"]) == 3
    # Check if all parts are present in the first item
    first_item = result["items"][0]
    assert "id" in first_item
    assert "snippet" in first_item
    assert "moderationStatus" in first_item
    assert "bannedAuthor" in first_item


def test_list_with_single_id_part(mock_db):
    """Test retrieving comments with only the 'id' part."""
    result = list_comments(part="id")
    assert "items" in result
    assert len(result["items"]) == 3
    first_item = result["items"][0]
    assert list(first_item.keys()) == ["id"]


def test_list_with_specific_comment_id(mock_db):
    """Test filtering by a single comment ID."""
    result = list_comments(part="id,snippet", comment_id="comment2")
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == "comment2"


def test_list_with_multiple_comment_ids(mock_db):
    """Test filtering by a comma-separated list of comment IDs."""
    result = list_comments(part="id", comment_id="comment1,reply1_to_comment1")
    assert "items" in result
    assert len(result["items"]) == 2
    ids = {item["id"] for item in result["items"]}
    assert ids == {"comment1", "reply1_to_comment1"}


def test_list_replies_with_parent_id(mock_db):
    """Test retrieving replies for a specific parent comment."""
    result = list_comments(part="id,snippet", parent_id="comment1")
    assert "items" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == "reply1_to_comment1"
    assert result["items"][0]["snippet"]["parentId"] == "comment1"


def test_list_with_max_results(mock_db):
    """Test limiting the number of results with max_results."""
    result = list_comments(part="id", max_results=2)
    assert "items" in result
    assert len(result["items"]) == 2


def test_list_with_pagination(mock_db):
    """Test pagination using the page_token."""
    # Assuming page_token is the index to start from
    result = list_comments(part="id", page_token="1")
    assert "items" in result
    assert len(result["items"]) == 2
    # The first result should be the second item from the sample data
    # Note: dict.items() order is not guaranteed before Python 3.7, but this is a simple mock
    # A more robust test would not depend on insertion order.
    # In this case, we check that the returned IDs are a subset of the expected ones.
    returned_ids = {item["id"] for item in result["items"]}
    assert "comment1" not in returned_ids


def test_list_with_text_format_plain(mock_db):
    """Test text_format 'plainText' to strip HTML."""
    result = list_comments(
        part="snippet", comment_id="comment2", text_format="plainText"
    )
    assert "items" in result
    assert len(result["items"]) == 1
    text = result["items"][0]["snippet"]["textDisplay"]
    assert "<b>" not in text
    assert "<br/>" not in text
    assert text == "A second comment with \n HTML."


# --- Error Handling and Validation Tests ---


def test_list_with_empty_part(mock_db):
    """Test that an empty 'part' parameter returns an error."""
    result = list_comments(part="")
    assert "error" in result
    assert result["error"] == "Part parameter is required and cannot be empty"


def test_list_with_invalid_part(mock_db):
    """Test that an invalid 'part' parameter returns an error."""
    result = list_comments(part="id,invalid_part")
    assert "error" in result
    assert "Invalid part parameter: invalid_part" in result["error"]


def test_list_with_invalid_max_results_type(mock_db):
    """Test error for non-integer max_results."""
    result = list_comments(part="id", max_results="two")
    assert "error" in result
    assert result["error"] == "max_results parameter must be an integer"


def test_list_with_negative_max_results(mock_db):
    """Test error for non-positive max_results."""
    result = list_comments(part="id", max_results=-1)
    assert "error" in result
    assert result["error"] == "max_results parameter must be a positive integer"


def test_list_with_invalid_text_format(mock_db):
    """Test error for invalid text_format value."""
    result = list_comments(part="id", text_format="xml")
    assert "error" in result
    assert result["error"] == "text_format parameter must be 'html' or 'plainText'"


def test_list_with_invalid_page_token(mock_db):
    """Test error for a non-integer page_token."""
    result = list_comments(part="id", page_token="abc")
    assert "error" in result
    assert result["error"] == "Invalid page_token format"


def test_list_no_comments_found(mock_db):
    """Test behavior when no comments match the filter."""
    result = list_comments(part="id", comment_id="nonexistent_id")
    assert "items" in result
    assert len(result["items"]) == 0


def test_list_empty_database(mock_db):
    """Test behavior with an empty comments database."""
    mock_db["comments"] = {}
    result = list_comments(part="id")
    assert "items" in result
    assert len(result["items"]) == 0
