import sys, os
sys.path.append("APIs")

from typing import Dict, Any

import google_cloud_storage

Buckets = google_cloud_storage.Buckets
DB = google_cloud_storage.DB  # convenience


def _create_dummy_buckets(project: str, count: int) -> None:
    for _ in range(count):
        Buckets.insert(project)


def test_pagination_next_page_token():
    project = "pag-project"
    DB["buckets"].clear()
    _create_dummy_buckets(project, 5)

    # Page 1
    result1 = Buckets.list(project, max_results=2)
    assert len(result1["items"]) == 2
    assert "nextPageToken" in result1
    token = result1["nextPageToken"]

    # Page 2
    result2 = Buckets.list(project, max_results=2, page_token=token)
    assert len(result2["items"]) == 2
    assert "nextPageToken" in result2
    token2 = result2["nextPageToken"]

    # Page 3 (remaining 1 item)
    result3 = Buckets.list(project, max_results=2, page_token=token2)
    assert len(result3["items"]) == 1
    assert "nextPageToken" not in result3


def test_invalid_projection_value():
    DB["buckets"].clear()
    Buckets.insert("proj")
    try:
        Buckets.list("proj", projection="invalid")
    except google_cloud_storage.SimulationEngine.custom_errors.InvalidProjectionValueError:
        assert True
    else:
        assert False, "Expected InvalidProjectionValueError"


def test_negative_max_results():
    DB["buckets"].clear()
    Buckets.insert("proj")
    try:
        Buckets.list("proj", max_results=-5)
    except ValueError as e:
        assert "max_results" in str(e)
    else:
        assert False, "Expected ValueError for negative max_results"


def test_invalid_page_token():
    DB["buckets"].clear()
    Buckets.insert("proj")
    # Non-integer token should default to start (no error raised)
    result = Buckets.list("proj", page_token="abc")
    # Should list from start despite invalid token
    assert len(result["items"]) >= 1 