import pytest
import copy
from retail import modify_user_address_tool
from retail.SimulationEngine.custom_errors import UserNotFoundError, InvalidInputError
from retail.SimulationEngine import db


class TestModifyUserAddress:
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

    def test_modify_user_address_success(self):
        user_id = "test_user"
        address1 = "456 Oak St"
        address2 = "Apt 2"
        city = "New York"
        state = "NY"
        country = "USA"
        zip_code = "10001"

        updated_user = modify_user_address_tool.modify_user_address(
            user_id, address1, address2, city, state, country, zip_code
        )

        assert updated_user["address"]["address1"] == address1
        assert updated_user["address"]["address2"] == address2
        assert updated_user["address"]["city"] == city
        assert updated_user["address"]["state"] == state
        assert updated_user["address"]["country"] == country
        assert updated_user["address"]["zip"] == zip_code

    def test_modify_user_address_not_found(self):
        with pytest.raises(UserNotFoundError, match="Error: user not found"):
            modify_user_address_tool.modify_user_address(
                "non_existent_user", "123 Main St", "Apt 2K", "Anytown", "CA", "USA", "12345"
            )

    def test_modify_user_address_input_validation(self):
        with pytest.raises(InvalidInputError):
            modify_user_address_tool.modify_user_address(
                123, "123 Main St", "", "Anytown", "CA", "USA", "12345"
            )
