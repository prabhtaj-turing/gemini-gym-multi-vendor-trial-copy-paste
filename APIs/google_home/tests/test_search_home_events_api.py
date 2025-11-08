import pytest
from google_home.search_home_events_api import search_home_events
from google_home.SimulationEngine.custom_errors import InvalidInputError


class TestSearchHomeEvents:
    def test_search_home_events_valid(self):
        """
        Test search_home_events with valid inputs.
        """
        result = search_home_events(
            query="Did I get any packages today?", home_name="My Home"
        )
        assert "search_home_events_response" in result
        assert "camera_clip_urls" in result

    def test_search_home_events_missing_query(self):
        """
        Test search_home_events with a missing query.
        """
        with pytest.raises(InvalidInputError):
            search_home_events(query=None)
