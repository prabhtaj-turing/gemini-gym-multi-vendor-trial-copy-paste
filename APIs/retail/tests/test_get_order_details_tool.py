import pytest
import copy
from retail import get_order_details_tool, exchange_delivered_order_items_tool, return_delivered_order_items_tool
from retail.SimulationEngine.custom_errors import OrderNotFoundError, InvalidInputError
from retail.SimulationEngine import db


class TestGetOrderDetails:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_get_order_details_success(self):
        order_id = "#W5918442"
        result = get_order_details_tool.get_order_details(order_id)
        assert result["order_id"] == order_id

    def test_get_order_details_not_found(self):
        with pytest.raises(OrderNotFoundError, match="Error: order not found"):
            get_order_details_tool.get_order_details("#W1234567")

    def test_get_order_details_input_validation(self):
        with pytest.raises(InvalidInputError):
            get_order_details_tool.get_order_details(123)
