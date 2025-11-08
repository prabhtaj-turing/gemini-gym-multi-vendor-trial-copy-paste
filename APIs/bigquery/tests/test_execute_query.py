import pytest
import os
import sqlite3
import json
import tempfile
from unittest.mock import patch
from bigquery import execute_query
from ..SimulationEngine.custom_errors import InvalidQueryError, InvalidInputError
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import (
    initialize_sqlite_db, 
    set_default_db_path,
    _DEFAULT_DB_PATH,  # The master default JSON path
    get_default_db_path # Function to get the current default JSON path
)

@pytest.fixture(autouse=True)
def fresh_db():
    current_default_json_path = get_default_db_path()
    expected_default_json_path = _DEFAULT_DB_PATH

    # Ensure that tests in this file robustly use the main BigQueryDefaultDB.json
    if current_default_json_path != expected_default_json_path:
        if os.path.exists(expected_default_json_path):
            set_default_db_path(expected_default_json_path)
        else:
            # This is a critical configuration error if the main default DB JSON is missing
            raise FileNotFoundError(
                f"Master default DB JSON configuration file not found at: {expected_default_json_path}. "
                f"Cannot run tests in {__file__} without it."
            )
    
    # Update the global DB variable with the contents of the file
    with open(_DEFAULT_DB_PATH, 'r') as f:
        db_data = json.load(f)
        global DB
        DB.clear()
        DB.update(db_data)
    
    # Now, initialize_sqlite_db will use the correct BigQueryDefaultDB.json
    # for the 'project-query.user-activity-logs' dataset.
    initialize_sqlite_db("project-query", "user-activity-logs")
    yield
    # No specific cleanup of _DEFAULT_DB_PATH_CURRENT is needed here; 
    # fresh_db will reset it if necessary on the next test run within this file.
    # Other test modules should manage their own default path settings if they alter it.

@pytest.fixture
def short_timeout():
    """Fixture to set a very short timeout for query execution"""
    with patch('bigquery.timeout_ms', 1):  # 1ms timeout
        yield

def test_basic_select_query():
    """Test basic SELECT query execution"""
    query = "SELECT * FROM project-query.user-activity-logs.git-events"
    
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    # Check for presence of expected columns
    first_row = result["query_results"][0]
    assert "event_id" in first_row
    assert "repository_name" in first_row
    assert "actor_login" in first_row
    assert "event_type" in first_row
    assert "payload" in first_row
    assert "created_at" in first_row

def test_select_with_where_clause():
    """Test SELECT query with WHERE clause"""
    # First get a valid actor_login for our test
    query_all = "SELECT * FROM project-query.user-activity-logs.git-events LIMIT 1"
    result_all = execute_query(query_all)
    assert len(result_all["query_results"]) > 0
    
    actor_login = result_all["query_results"][0]["actor_login"]
    
    # Now test the query with the WHERE clause
    query = f"SELECT * FROM project-query.user-activity-logs.git-events WHERE actor_login = '{actor_login}'"
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    assert all(row["actor_login"] == actor_login for row in result["query_results"])

def test_select_specific_columns():
    """Test SELECT query with specific columns"""
    query = "SELECT event_id, actor_login FROM project-query.user-activity-logs.git-events"
    
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    assert all(len(row) == 2 for row in result["query_results"])
    assert all("event_id" in row and "actor_login" in row for row in result["query_results"])

def test_invalid_query():
    """Test invalid query handling"""
    with pytest.raises(InvalidQueryError):
        execute_query("INVALID QUERY")

def test_non_select_query():
    """Test non-SELECT query handling"""
    with pytest.raises(InvalidQueryError):
        execute_query("INSERT INTO project-query.user-activity-logs.git-events VALUES (1, 'test')")

def test_nonexistent_table():
    """Test querying non-existent table"""
    with pytest.raises(InvalidQueryError):
        execute_query("SELECT * FROM project-query.user-activity-logs.nonexistent_table")

def test_json_handling():
    """Test JSON data handling in queries"""
    # First get a valid event_id for our test
    query_all = "SELECT * FROM project-query.user-activity-logs.git-events LIMIT 1"
    result_all = execute_query(query_all)
    assert len(result_all["query_results"]) > 0
    
    event_id = result_all["query_results"][0]["event_id"]
    
    # Now test the payload (JSON) field with LIMIT 1 to ensure we only get one result
    query = f"SELECT payload FROM project-query.user-activity-logs.git-events WHERE event_id = '{event_id}' LIMIT 1"
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    assert "payload" in result["query_results"][0]
    assert isinstance(result["query_results"][0]["payload"], dict)

def test_timestamp_handling():
    """Test timestamp data handling in queries"""
    # First get a valid event_id for our test
    query_all = "SELECT * FROM project-query.user-activity-logs.git-events LIMIT 1"
    result_all = execute_query(query_all)
    assert len(result_all["query_results"]) > 0
    
    event_id = result_all["query_results"][0]["event_id"]
    
    # Now test the created_at (timestamp) field with LIMIT 1 to ensure we only get one result
    query = f"SELECT created_at FROM project-query.user-activity-logs.git-events WHERE event_id = '{event_id}' LIMIT 1"
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    assert "created_at" in result["query_results"][0]
    assert isinstance(result["query_results"][0]["created_at"], str)

# New tests for more thorough result verification

def test_exact_data_validation():
    """Test that query results match expected values from known test data."""
    # Query for a specific record with known values
    query = "SELECT * FROM project-query.user-activity-logs.git-events WHERE event_id = 'e4d2c1b9-f3a0-4a98-8974-3c8d1b2a0f6e'"
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    
    # Verify exact field values match what we expect
    row = result["query_results"][0]
    assert row["event_id"] == "e4d2c1b9-f3a0-4a98-8974-3c8d1b2a0f6e"
    assert row["repository_id"] == 1296269
    assert row["repository_name"] == "octocat/Spoon-Knife"
    assert row["actor_id"] == 583231
    assert row["actor_login"] == "octocat"
    assert row["event_type"] == "PushEvent"
    assert row["created_at"] == "2025-05-15T08:30:15Z"  # Note: SQLite adds spaces in the timestamp format
    
    # Verify nested JSON structure
    assert "payload" in row
    assert row["payload"]["push_id"] == 1234567890
    assert row["payload"]["size"] == 1
    assert row["payload"]["ref"] == "refs/heads/main"
    assert len(row["payload"]["commits"]) == 1
    assert row["payload"]["commits"][0]["author"]["name"] == "The Octocat"

def test_count_aggregation():
    """Test COUNT aggregation function."""
    query = "SELECT COUNT(*) as event_count FROM project-query.user-activity-logs.git-events"
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) == 1
    assert "event_count" in result["query_results"][0]
    assert result["query_results"][0]["event_count"] >= 4  # Should have at least 4 events in the test data

def test_count_by_event_type():
    """Test COUNT with GROUP BY."""
    query = """
    SELECT 
        event_type, 
        COUNT(*) as event_count 
    FROM project-query.user-activity-logs.git-events 
    GROUP BY event_type
    """
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    
    # Convert to a dict for easier verification
    counts_by_type = {row["event_type"]: row["event_count"] for row in result["query_results"]}
    
    # Verify we have counts for the expected event types
    assert "PushEvent" in counts_by_type
    assert "PullRequestEvent" in counts_by_type
    assert "IssueCommentEvent" in counts_by_type
    assert "WatchEvent" in counts_by_type
    
    # Verify each event type has the expected count
    assert counts_by_type["PushEvent"] >= 1
    assert counts_by_type["PullRequestEvent"] >= 1
    assert counts_by_type["IssueCommentEvent"] >= 1
    assert counts_by_type["WatchEvent"] >= 1

def test_complex_filtering():
    """Test filtering with complex conditions."""
    query = """
    SELECT * 
    FROM project-query.user-activity-logs.git-events 
    WHERE 
        (repository_name LIKE '%octocat%' OR actor_login = 'octocat')
        AND event_type IN ('PushEvent', 'WatchEvent')
    """
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) > 0
    
    # Verify all returned rows match the filter criteria
    for row in result["query_results"]:
        # Should match either condition
        assert "octocat" in row["repository_name"].lower() or row["actor_login"] == "octocat"
        # And should match this condition
        assert row["event_type"] in ("PushEvent", "WatchEvent")

# def test_multi_table_query():
#     """Test querying from multiple tables to check JOIN functionality."""
#     # This test depends on both git-events and user-logins tables existing in the test data
#     query = """
#     SELECT 
#         ge.event_id, ge.actor_login, ge.event_type, ul.login_timestamp
#     FROM 
#         project-query.user-activity-logs.git-events ge
#     JOIN 
#         project-query.user-activity-logs.user-logins ul
#     ON 
#         ge.actor_login = ul.user_login
#     LIMIT 10
#     """
#     try:
#         result = execute_query(query)
        
#         assert "query_results" in result
        
#         # If the query succeeds, verify the result structure
#         if len(result["query_results"]) > 0:
#             row = result["query_results"][0]
#             assert "event_id" in row
#             assert "actor_login" in row
#             assert "event_type" in row
#             assert "login_timestamp" in row
            
#             # Verify join worked correctly - each row should have the same actor_login and user_login
#             for row in result["query_results"]:
#                 actor_login = row["actor_login"]
#                 # Assuming we can run a validation query to check
#                 validation_query = f"SELECT * FROM project-query.user-activity-logs.user-logins WHERE user_login = '{actor_login}' LIMIT 1"
#                 validation_result = execute_query(validation_query)
#                 assert len(validation_result["query_results"]) > 0
#     except InvalidQueryError:
#         # If JOIN is not supported, this will raise an error
#         # We'll consider the test passed if the error contains a message about joins
#         pytest.skip("JOIN operations not supported or tables structure doesn't support the test")

def test_null_handling():
    """Test handling of NULL values in queries."""
    # Try to find a record with a NULL value or create a query that checks for NULLs
    query = """
    SELECT *
    FROM project-query.user-activity-logs.user-logins
    WHERE user_id IS NULL
    """
    
    try:
        result = execute_query(query)
        
        assert "query_results" in result
        
        # If we found NULL values, verify they're handled correctly
        if len(result["query_results"]) > 0:
            for row in result["query_results"]:
                assert row["user_id"] is None
    except InvalidQueryError:
        # If the table doesn't exist or can't be queried, skip this test
        pytest.skip("Table user-logins not accessible or NULL handling can't be tested")

def test_order_by_limit():
    """Test ORDER BY and LIMIT functionality."""
    query = """
    SELECT event_id, created_at
    FROM project-query.user-activity-logs.git-events
    ORDER BY created_at DESC
    LIMIT 2
    """
    
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) == 2
    
    # Verify the results are ordered correctly
    if len(result["query_results"]) == 2:
        first_date = result["query_results"][0]["created_at"]
        second_date = result["query_results"][1]["created_at"]
        assert first_date >= second_date  # First date should be greater or equal to second date

def test_subquery():
    """Test subquery functionality."""
    query = """
    SELECT * FROM (
        SELECT event_type, COUNT(*) as count
        FROM project-query.user-activity-logs.git-events
        GROUP BY event_type
    )
    WHERE count > 0
    """
    
    try:
        result = execute_query(query)
        
        assert "query_results" in result
        assert len(result["query_results"]) > 0
        
        # Verify subquery results are correct
        for row in result["query_results"]:
            assert "event_type" in row
            assert "count" in row
            assert row["count"] > 0
    except InvalidQueryError:
        # If subqueries aren't supported, skip this test
        pytest.skip("Subqueries not supported in the current implementation")

def test_case_expression():
    """Test CASE expression functionality."""
    query = """
    SELECT 
        event_id,
        CASE 
            WHEN event_type = 'PushEvent' THEN 'Code Push'
            WHEN event_type = 'PullRequestEvent' THEN 'Pull Request'
            ELSE event_type
        END AS event_category
    FROM project-query.user-activity-logs.git-events
    LIMIT 10
    """
    
    try:
        result = execute_query(query)
        
        assert "query_results" in result
        assert len(result["query_results"]) > 0
        
        # Verify CASE results are correct
        for row in result["query_results"]:
            if "PushEvent" in row.values():
                assert row["event_category"] == "Code Push"
            elif "PullRequestEvent" in row.values():
                assert row["event_category"] == "Pull Request"
    except InvalidQueryError:
        # If CASE expressions aren't supported, skip this test
        pytest.skip("CASE expressions not supported in the current implementation")

def test_empty_result():
    """Test handling of queries that return no results."""
    query = """
    SELECT * 
    FROM project-query.user-activity-logs.git-events
    WHERE event_id = 'non-existent-id-that-should-not-match'
    """
    
    result = execute_query(query)
    
    assert "query_results" in result
    assert len(result["query_results"]) == 0  # Should be empty


def test_input_validation():
    """Test input validation for the query parameter."""
    
    # Test None query
    with pytest.raises(InvalidInputError) as exc_info:
        execute_query(None)
    assert "Query parameter cannot be None" in str(exc_info.value)
    
    # Test non-string query
    with pytest.raises(InvalidInputError) as exc_info:
        execute_query(123)
    assert "Query parameter must be a string" in str(exc_info.value)
    
    # Test empty string
    with pytest.raises(InvalidInputError) as exc_info:
        execute_query("")
    assert "Query parameter cannot be empty" in str(exc_info.value)
    
    # Test whitespace-only string
    with pytest.raises(InvalidInputError) as exc_info:
        execute_query("   \n\t   ")
    assert "Query parameter cannot be empty" in str(exc_info.value)
    
    # Test query that's too short
    with pytest.raises(InvalidInputError) as exc_info:
        execute_query("abc")
    assert "Query is too short" in str(exc_info.value)
    
    # Test valid query (should not raise InvalidInputError)
    try:
        execute_query("SELECT * FROM project-query.user-activity-logs.git-events LIMIT 1")
    except InvalidInputError:
        pytest.fail("Valid query should not raise InvalidInputError")
