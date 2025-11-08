import pytest
import copy
from retail import get_user_details_tool
from retail.SimulationEngine.custom_errors import UserNotFoundError, InvalidInputError
from retail.SimulationEngine import db


class TestGetUserDetails:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)
        db.DB["users"]["test_user"] = {
            "name": {"first_name": "Test", "last_name": "User"},
            "address": {
                "address1": "123 Main St",
                "city": "Anytown",
                "country": "USA",
                "state": "CA",
                "zip": "12345",
            },
            "email": "test.user@example.com",
            "payment_methods": {
                "credit_card_123": {
                    "id": "credit_card_123",
                    "source": "credit_card",
                    "brand": "Visa",
                    "last_four": "1234",
                }
            },
            "orders": [],
        }

    def teardown_method(self):
        db.DB = self.original_db

    def test_get_user_details_success(self):
        user_id = "test_user"
        result = get_user_details_tool.get_user_details(user_id)
        assert result["name"]["first_name"] == "Test"

    def test_get_user_details_not_found(self):
        with pytest.raises(UserNotFoundError, match="Error: user not found"):
            get_user_details_tool.get_user_details("non_existent_user")

    def test_get_user_details_input_validation(self):
        with pytest.raises(InvalidInputError):
            get_user_details_tool.get_user_details(123)
