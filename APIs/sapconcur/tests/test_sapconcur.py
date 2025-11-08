from APIs.sapconcur.flights import search_direct_flight, search_onestop_flight
from APIs.sapconcur.users import get_user_details
from unittest.mock import patch
import json
from common_utils.base_case import BaseTestCaseWithErrorHandler
from datetime import datetime, time


class TestDefaultDBFlightScenarios(BaseTestCaseWithErrorHandler): 
    def setUp(self):
        self.DB = json.load(open("DBs/SAPConcurDefaultDB.json"))
    
    def test_direct_flight_search(self):
        with patch("APIs.sapconcur.SimulationEngine.utils.DB", self.DB):
            result = search_direct_flight(
                departure_airport="ORD",
                arrival_airport="PHL",
                departure_date="2024-05-26"
            )
            assert result
            assert len(result) > 0
    
    def test_onestop_flight_search(self):
        with patch("APIs.sapconcur.SimulationEngine.utils.DB", self.DB):
            result = search_onestop_flight(
                departure_airport="ATL",
                arrival_airport="PHL",
                departure_date="2024-05-24"
            )
            assert result
            assert len(result) > 0
    
    def test_one_stop_agent_1(self):
        with patch("APIs.sapconcur.SimulationEngine.utils.DB", self.DB):
            result = search_onestop_flight(
                departure_airport="JFK",
                arrival_airport="SEA",
                departure_date="2024-05-20"
            )
            assert result
            assert len(result) > 0
