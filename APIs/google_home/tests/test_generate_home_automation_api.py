import pytest
from google_home.generate_home_automation_api import generate_home_automation
from google_home.SimulationEngine.custom_errors import InvalidInputError


class TestGenerateHomeAutomation:
    def test_generate_home_automation_valid(self):
        """
        Test generate_home_automation with valid inputs.
        """
        result = generate_home_automation(
            query="Turn on the lights at 7pm", home_name="My Home"
        )
        assert "automation_script_code" in result
        assert "user_instructions" in result

    def test_generate_home_automation_missing_query(self):
        """
        Test generate_home_automation with a missing query.
        """
        with pytest.raises(InvalidInputError):
            generate_home_automation(query=None)
