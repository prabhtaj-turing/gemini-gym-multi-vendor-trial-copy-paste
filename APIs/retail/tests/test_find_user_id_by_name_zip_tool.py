import pytest
import copy
from retail import find_user_id_by_name_zip_tool
from retail.SimulationEngine.custom_errors import UserNotFoundError, InvalidInputError
from retail.SimulationEngine import db


class TestFindUserIdByNameZip:
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

    def test_find_user_id_by_name_zip_success(self):
        result = find_user_id_by_name_zip_tool.find_user_id_by_name_zip(
            "Test", "User", "12345"
        )
        assert result == "test_user"

    def test_find_user_id_by_name_zip_not_found(self):
        with pytest.raises(UserNotFoundError, match="Error: user not found"):
            find_user_id_by_name_zip_tool.find_user_id_by_name_zip(
                "Non", "Existent", "54321"
            )

    def test_find_user_id_by_name_zip_input_validation(self):
        with pytest.raises(InvalidInputError):
            find_user_id_by_name_zip_tool.find_user_id_by_name_zip(
                123, "User", "12345"
            )
