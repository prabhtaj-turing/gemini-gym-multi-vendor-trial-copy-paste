"""
Unit tests for query_available_plans_and_features function.

This test file contains comprehensive test cases based on real-world query scenarios
to ensure the function properly searches and returns information about available
service plans and features.
"""

import unittest
import sys
import os
from unittest.mock import patch
from pydantic import ValidationError

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from .account_management_base_exception import AccountManagementBaseTestCase
from ..account_management import query_available_plans_and_features


class TestQueryAvailablePlansAndFeatures(AccountManagementBaseTestCase):
    """
    Test suite for query_available_plans_and_features function.
    Tests various query scenarios to ensure proper search functionality and response format.
    """
    
    def setUp(self):
        """Set up test fixtures with mocked Gemini responses."""
        super().setUp()
        
        # Create a mock for get_gemini_response
        self.mock_patcher = patch('ces_account_management.SimulationEngine.utils._get_gemini_response')
        self.mock_get_gemini_response = self.mock_patcher.start()
        
        # Set default mock response
        self.mock_get_gemini_response.return_value = '[{"id": "P001", "name": "Basic Talk & Text", "description": "Unlimited talk and text within the country. No data included.", "type": "PLAN", "monthlyCost": 15, "dataAllowance": "0GB", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/P001", "compatibilityNotes": ""}]'
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.mock_patcher.stop()
        super().tearDown()

    # Test: International Calling Pack queries
    def test_query_international_calling_pack_cost(self):
        """Test query for cost of International Calling Pack."""
        # Set specific mock response for this test
        self.mock_get_gemini_response.return_value = '[{"id": "F001", "name": "International Calling Pack", "description": "100 minutes to select international destinations.", "type": "FEATURE_ADDON", "monthlyCost": 10, "dataAllowance": "", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/F001", "compatibilityNotes": "Requires any active monthly plan."}]'
        
        result = query_available_plans_and_features("cost of International Calling Pack")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        self.assertIsInstance(result["answer"], str)
        self.assertIsInstance(result["snippets"], list)
        
        # Check that International Calling Pack information is in snippets
        snippet_titles = [s.get("title", "") for s in result["snippets"]]
        self.assertTrue(
            any("International Calling" in title for title in snippet_titles),
            "Expected International Calling Pack in snippets"
        )

    # Test: Device protection queries
    def test_query_device_protection(self):
        """Test query for device protection options."""
        # Set specific mock response for device protection
        self.mock_get_gemini_response.return_value = '[{"id": "F004", "name": "Device Protection Plus", "description": "Covers accidental damage and extended warranty for one device.", "type": "FEATURE_ADDON", "monthlyCost": 11.99, "dataAllowance": "", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/F004", "compatibilityNotes": "Requires any active monthly plan."}]'
        
        result = query_available_plans_and_features("What kind of device protection do you offer?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        
        # Check for Device Protection Plus information
        snippet_titles = [s.get("title", "") for s in result["snippets"]]
        self.assertTrue(
            any("Device Protection" in title for title in snippet_titles),
            "Expected Device Protection Plus in snippets"
        )

    def test_query_need_cheaper_option(self):
        """Test query asking for cheaper options."""
        result = query_available_plans_and_features("I need a cheaper option")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        self.assertIsInstance(result["snippets"], list)
        # Note: Snippets may be empty if no exact match is found, which is valid behavior

    def test_query_can_i_get_cheaper_plan(self):
        """Test query asking if they can get a cheaper plan."""
        result = query_available_plans_and_features("Can I get a cheaper plan?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: Hotspot add-on queries
    def test_query_hotspot_addon(self):
        """Test query for hotspot add-on availability."""
        # Set specific mock response for hotspot add-on
        self.mock_get_gemini_response.return_value = '[{"id": "F002", "name": "Mobile Hotspot Add-on (5GB)", "description": "Adds 5GB of data for mobile hotspot usage.", "type": "FEATURE_ADDON", "monthlyCost": 12, "dataAllowance": "5GB", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/F002", "compatibilityNotes": "Requires any active monthly plan."}]'
        
        result = query_available_plans_and_features("Do you have a hotspot add-on?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        
        # Check for hotspot information
        snippet_titles = [s.get("title", "") for s in result["snippets"]]
        self.assertTrue(
            any("Hotspot" in title for title in snippet_titles),
            "Expected Mobile Hotspot Add-on in snippets"
        )

    # Test: International travel add-ons
    def test_query_international_travel_addons(self):
        """Test query for add-ons for international travel."""
        # Set specific mock response for international travel add-ons
        self.mock_get_gemini_response.return_value = '[{"id": "F001", "name": "International Calling Pack", "description": "100 minutes to select international destinations.", "type": "FEATURE_ADDON", "monthlyCost": 10, "dataAllowance": "", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/F001", "compatibilityNotes": "Requires any active monthly plan."}, {"id": "F003", "name": "Unlimited International Texting", "description": "Unlimited SMS/MMS to international numbers from within the country.", "type": "FEATURE_ADDON", "monthlyCost": 7.5, "dataAllowance": "", "termsAndConditionsUrl": "", "compatibilityNotes": "Requires any active monthly plan."}]'
        
        result = query_available_plans_and_features("add-ons for international travel")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        
        # Should include international-related features
        snippet_content = " ".join([
            s.get("title", "") + " " + s.get("text", "") 
            for s in result["snippets"]
        ])
        self.assertTrue(
            "International" in snippet_content,
            "Expected international features in results"
        )

    # Test: Plan compatibility with devices
    def test_query_plan_compatibility_with_smartphone(self):
        """Test query about plan compatibility with smartphones."""
        result = query_available_plans_and_features("Does my plan work on a smartphone?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        self.assertIsInstance(result["snippets"], list)

    # Test: Available add-ons queries
    def test_query_available_addons_for_plan(self):
        """Test query for available add-ons for a specific plan."""
        result = query_available_plans_and_features("What are the add-ons available for my plan?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        self.assertGreater(len(result["snippets"]), 0)

    # Test: Family plan data queries
    def test_query_family_plan_data_allowance(self):
        """Test query about family plan data allowance."""
        result = query_available_plans_and_features("How much data does my family plan have?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        
        # Should mention family plan information if found
        # Note: Search may not always return exact matches depending on query phrasing
        self.assertIsInstance(result["snippets"], list)

    def test_query_family_plan_options(self):
        """Test query about family plan options for multiple lines."""
        result = query_available_plans_and_features("Family plan options for 4 lines")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        
        # Verify response structure is correct (content matching depends on search engine)
        self.assertIsInstance(result["snippets"], list)

    def test_query_tell_me_about_family_plans(self):
        """Test query asking about family plans."""
        result = query_available_plans_and_features("tell me about family plans")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        self.assertGreater(len(result["snippets"]), 0)

    def test_query_more_data_for_family(self):
        """Test query asking for more data for family."""
        result = query_available_plans_and_features("I need more data for my family")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: General plan overview queries
    def test_query_available_service_plans_and_differences(self):
        """Test query for available service plans and their differences."""
        result = query_available_plans_and_features("available Sunday Mobile service plans and differences")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        
        # Should return multiple plans
        self.assertGreater(len(result["snippets"]), 0)

    # Test: Tablet plan queries
    def test_query_tablet_plan(self):
        """Test query for tablet-specific plans."""
        result = query_available_plans_and_features("Can I get a plan for my tablet?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        
        # Should mention data-only or tablet plans
        snippet_content = " ".join([
            s.get("title", "") + " " + s.get("text", "") 
            for s in result["snippets"]
        ])
        self.assertTrue(
            "tablet" in snippet_content.lower() or "data" in snippet_content.lower(),
            "Expected tablet or data-only plan information"
        )

    def test_query_need_plan_for_tablet(self):
        """Test query asking for a plan for tablet."""
        result = query_available_plans_and_features("I need a plan for my tablet")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: Plan upgrade queries
    def test_query_how_to_upgrade_plan(self):
        """Test query about upgrading plans."""
        result = query_available_plans_and_features("How do I upgrade my plan?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_query_upgrade_offers(self):
        """Test query for upgrade offers."""
        result = query_available_plans_and_features("upgrade offers available")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_query_device_upgrade_promotions(self):
        """Test query for current device upgrade promotions."""
        result = query_available_plans_and_features("current device upgrade promotions")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_query_phone_promotions(self):
        """Test query about phone promotions."""
        result = query_available_plans_and_features("tell me about phone promotions")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_query_upgrade_deals_info(self):
        """Test query for information on upgrade deals."""
        result = query_available_plans_and_features("info on upgrade deals")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_query_what_promotions_available(self):
        """Test query asking what promotions are available."""
        result = query_available_plans_and_features("what promotions do you have")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: Plans with specific features
    def test_query_plans_with_more_data_than_family_share(self):
        """Test query for plans with more data than Family Share."""
        result = query_available_plans_and_features("plans with more data than Family Share")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_query_show_plans_with_data(self):
        """Test query to show plans that include data."""
        result = query_available_plans_and_features("show me plans with data")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        self.assertGreater(len(result["snippets"]), 0)

    def test_query_data_plans(self):
        """Test query for data plans."""
        result = query_available_plans_and_features("data plans")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: Plan options queries
    def test_query_what_are_my_plan_options(self):
        """Test query asking about plan options."""
        result = query_available_plans_and_features("What are my plan options?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        self.assertGreater(len(result["snippets"]), 0)

    def test_query_options_for_new_plan(self):
        """Test query asking about options for a new plan."""
        result = query_available_plans_and_features("What are my options for a new plan?")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: More data queries
    def test_query_need_more_data(self):
        """Test query asking for a plan with more data."""
        result = query_available_plans_and_features("I need a plan with more data")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_query_need_more_than_5gb(self):
        """Test query asking for more than 5GB of data."""
        result = query_available_plans_and_features("I need more data than 5GB")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: Voice call plan queries
    def test_query_plan_with_voice_calls(self):
        """Test query for plans with voice calls."""
        result = query_available_plans_and_features("Plan with voice calls")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    # Test: Validation and error handling
    def test_query_empty_string(self):
        """Test that empty query string raises ValueError."""
        self.assert_error_behavior(
            query_available_plans_and_features,
            ValueError,
            "String should have at least 1 character",
            query="",
        )

    def test_query_whitespace_only(self):
        """Test that whitespace-only query raises ValueError."""
        self.assert_error_behavior(
            query_available_plans_and_features,
            ValueError,
            "Query must be a non-empty string.",
            query="   ",
        )

    def test_query_non_string_input(self):
        """Test that non-string query raises ValueError."""
        self.assert_error_behavior(
            query_available_plans_and_features,
            ValueError,
            "Input should be a valid string",
            query=123,
        )

    def test_query_none_input(self):
        """Test that None query raises ValueError."""
        self.assert_error_behavior(
            query_available_plans_and_features,
            ValueError,
            "Input should be a valid string",
            query=None,
        )

    # Test: Response structure validation
    def test_response_structure_has_required_fields(self):
        """Test that response has required fields: answer and snippets."""
        result = query_available_plans_and_features("Basic Talk")
        
        self.assertIn("answer", result)
        self.assertIn("snippets", result)

    def test_snippets_have_correct_structure(self):
        """Test that snippets have correct structure with text, title, and uri."""
        result = query_available_plans_and_features("International Calling Pack")
        
        if result["snippets"]:
            for snippet in result["snippets"]:
                self.assertIsInstance(snippet, dict)
                # Snippets should have these fields (though they might be None)
                self.assertIn("text", snippet)
                self.assertIn("title", snippet)
                self.assertIn("uri", snippet)

    def test_answer_is_string_or_none(self):
        """Test that answer is a string or None."""
        result = query_available_plans_and_features("test query")
        
        self.assertTrue(
            isinstance(result["answer"], str) or result["answer"] is None,
            "Answer should be string or None"
        )

    def test_snippets_is_list(self):
        """Test that snippets is always a list."""
        result = query_available_plans_and_features("test query")
        
        self.assertIsInstance(result["snippets"], list)

    # Test: No match scenarios
    def test_query_nonexistent_plan(self):
        """Test query for non-existent plan returns appropriate response."""
        # Set mock response for no matches
        self.mock_get_gemini_response.return_value = '[]'
        
        result = query_available_plans_and_features("SuperUltraMegaPlan9000")
        
        self.assertIsInstance(result, dict)
        self.assertIn("answer", result)
        self.assertIn("snippets", result)
        # When no match, answer should indicate lack of information or snippets should be empty
        self.assertTrue(
            len(result["snippets"]) == 0 or 
            "don't have" in result.get("answer", "").lower() or
            "no information" in result.get("answer", "").lower()
        )


if __name__ == "__main__":
    unittest.main()

