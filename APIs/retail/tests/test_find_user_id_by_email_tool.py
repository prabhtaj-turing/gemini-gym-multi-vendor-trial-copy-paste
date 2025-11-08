import pytest
import copy
from retail import find_user_id_by_email_tool
from retail.SimulationEngine.custom_errors import UserNotFoundError, InvalidInputError
from retail.SimulationEngine import db


class TestFindUserIdByEmail:
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
            "payment_methods": {},
            "orders": [],
        }

    def teardown_method(self):
        db.DB = self.original_db

    def test_find_user_id_by_email_success(self):
        email = "test.user@example.com"
        result = find_user_id_by_email_tool.find_user_id_by_email(email)
        assert result == "test_user"

    def test_find_user_id_by_email_not_found(self):
        with pytest.raises(UserNotFoundError, match="Error: user not found"):
            find_user_id_by_email_tool.find_user_id_by_email("non.existent@example.com")

    def test_find_user_id_by_email_input_validation(self):
        with pytest.raises(InvalidInputError):
            find_user_id_by_email_tool.find_user_id_by_email(123)
