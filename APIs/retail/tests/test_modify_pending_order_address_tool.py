import pytest
import copy
from retail import modify_pending_order_address_tool
from retail.SimulationEngine.custom_errors import (
    OrderNotFoundError,
    NonPendingOrderError,
    InvalidInputError,
)
from retail.SimulationEngine import db


class TestModifyPendingOrderAddress:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_modify_pending_order_address_success(self):
        order_id = "#W5918442"
        address1 = "456 Oak St"
        address2 = "Apt 2B"
        city = "New York"
        state = "NY"
        country = "USA"
        zip_code = "10001"

        updated_order = (
            modify_pending_order_address_tool.modify_pending_order_address(
                order_id, address1, address2, city, state, country, zip_code
            )
        )

        assert updated_order["address"]["address1"] == address1
        assert updated_order["address"]["address2"] == address2
        assert updated_order["address"]["city"] == city
        assert updated_order["address"]["state"] == state
        assert updated_order["address"]["country"] == country
        assert updated_order["address"]["zip"] == zip_code

    def test_modify_pending_order_address_not_found(self):
        with pytest.raises(OrderNotFoundError, match="Error: order not found"):
            modify_pending_order_address_tool.modify_pending_order_address(
                "#W1234567", "123 Main St", "Apt 2D", "Anytown", "CA", "USA", "12345"
            )

    def test_modify_non_pending_order(self):
        with pytest.raises(NonPendingOrderError, match="Error: non-pending order cannot be modified"):
            modify_pending_order_address_tool.modify_pending_order_address(
                "#W4817420", "123 Main St", "Apt 2C", "Anytown", "CA", "USA", "12345"
            )

    def test_modify_pending_order_address_input_validation(self):
        with pytest.raises(InvalidInputError):
            modify_pending_order_address_tool.modify_pending_order_address(
                123, "123 Main St", "", "Anytown", "CA", "USA", "12345"
            )

    def test_modify_address_when_status_pending_item_modified(self):
        order_id = "#W5918442"
        # Force status to 'pending (item modified)' to ensure address modification is allowed
        db.DB["orders"][order_id]["status"] = "pending (item modified)"

        address1 = "789 Pine St"
        address2 = "Suite 300"
        city = "Boston"
        state = "MA"
        country = "USA"
        zip_code = "02110"

        updated_order = (
            modify_pending_order_address_tool.modify_pending_order_address(
                order_id, address1, address2, city, state, country, zip_code
            )
        )

        assert updated_order["address"]["address1"] == address1
        assert updated_order["address"]["address2"] == address2
        assert updated_order["address"]["city"] == city
        assert updated_order["address"]["state"] == state
        assert updated_order["address"]["country"] == country
        assert updated_order["address"]["zip"] == zip_code
