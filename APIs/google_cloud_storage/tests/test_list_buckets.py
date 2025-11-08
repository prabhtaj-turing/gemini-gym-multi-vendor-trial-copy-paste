import pytest

# Ensure APIs package is importable when tests run in isolation
import sys, os
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from google_cloud_storage import Buckets  # type: ignore
from google_cloud_storage.SimulationEngine.custom_errors import InvalidProjectionValueError  # type: ignore


def _bucket_store() -> dict:  # Helper to access the single source of truth
    return Buckets.DB.setdefault("buckets", {})


@pytest.fixture(autouse=True)
def _clean_db():
    """Clear the in-memory database before every test case."""
    _bucket_store().clear()
    yield
    _bucket_store().clear()


def _create_sample_buckets():
    """Populate DB with five buckets; mark one as soft-deleted."""
    for _ in range(4):
        Buckets.insert("projA")
    soft_bucket = Buckets.insert("projA")["bucket"]["name"]
    _bucket_store()[soft_bucket]["softDeleted"] = True


# ---------------------------------------------------------------------------
# Validation error paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs, exc",
    [
        ({"project": 123}, TypeError),  # project not str
        ({"project": "   "}, ValueError),  # project empty/whitespace
        ({"project": "projA", "max_results": "10"}, TypeError),  # max_results not int
        ({"project": "projA", "max_results": 0}, ValueError),  # max_results non-positive
        ({"project": "projA", "page_token": 999}, TypeError),  # page_token not str/None
        ({"project": "projA", "prefix": 55}, TypeError),  # prefix not str/None
        ({"project": "projA", "soft_deleted": "false"}, TypeError),  # soft_deleted not bool
        ({"project": "projA", "projection": 1}, TypeError),  # projection not str
        ({"project": "projA", "projection": "invalid"}, InvalidProjectionValueError),  # bad projection
        ({"project": "projA", "user_project": 5}, TypeError),  # user_project not str/None
    ],
)
def test_list_validation_errors(kwargs, exc):
    """Each invalid argument combination must raise the expected error."""
    with pytest.raises(exc):
        Buckets.list(**kwargs)


# ---------------------------------------------------------------------------
# Functional behaviour paths
# ---------------------------------------------------------------------------


def test_list_happy_path_default_projection():
    """Listing without optional arguments returns all non-soft-deleted buckets."""
    _create_sample_buckets()

    result = Buckets.list("projA")
    # Four of the five inserted buckets are not softDeleted
    assert len(result["items"]) == 4
    # Default projection omits ACL keys
    for bucket in result["items"]:
        assert "acl" not in bucket and "defaultObjectAcl" not in bucket


def test_list_projection_full_includes_acl():
    _create_sample_buckets()
    # Add an acl field so we can see it come through
    any_bucket_name = next(iter(_bucket_store()))
    _bucket_store()[any_bucket_name]["acl"] = "private"

    result = Buckets.list("projA", projection="full")
    assert len(result["items"]) == 4  # soft-deleted bucket is excluded by default
    assert "acl" in result["items"][0]  # acl key present under full projection


def test_list_soft_deleted_filter():
    _create_sample_buckets()

    result = Buckets.list("projA", soft_deleted=True)
    # Only the single soft-deleted bucket should be returned
    assert len(result["items"]) == 1
    assert result["items"][0]["softDeleted"] is True


def test_list_prefix_filter():
    # Create buckets with different prefixes
    Buckets.insert("projA")  # bucket-1
    Buckets.insert("projA")  # bucket-2
    Buckets.insert("projA")  # bucket-3

    result = Buckets.list("projA", prefix="bucket-1")
    assert len(result["items"]) == 1
    assert result["items"][0]["name"].startswith("bucket-1")


def test_list_pagination_and_next_token():
    # Create six buckets to trigger pagination (max_results = 2)
    for _ in range(6):
        Buckets.insert("projA")

    first_page = Buckets.list("projA", max_results=2)
    assert len(first_page["items"]) == 2
    assert "nextPageToken" in first_page

    second_page = Buckets.list("projA", max_results=2, page_token=first_page["nextPageToken"])
    assert len(second_page["items"]) == 2
    assert "nextPageToken" in second_page

    third_page = Buckets.list("projA", max_results=2, page_token=second_page["nextPageToken"])
    assert len(third_page["items"]) == 2
    assert "nextPageToken" not in third_page  # no more pages


def test_list_invalid_page_token_gracefully_defaults():
    for _ in range(3):
        Buckets.insert("projA")

    # page_token that cannot convert to int should be treated as 0 and not raise
    result = Buckets.list("projA", page_token="not-a-number")
    assert len(result["items"]) == 3 