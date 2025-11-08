import pytest
import copy
from retail import return_delivered_order_items_tool
from retail.SimulationEngine.custom_errors import (
    OrderNotFoundError,
    NonDeliveredOrderError,
    PaymentMethodNotFoundError,
    InvalidReturnPaymentMethodError,
    ItemNotFoundError,
    InvalidInputError,
)
from retail.SimulationEngine import db


class TestReturnDeliveredOrderItems:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_return_delivered_order_items_success(self):
        order_id = "#W4817420"
        item_ids = ["6777246137"]
        payment_method_id = "gift_card_8168843"

        updated_order = (
            return_delivered_order_items_tool.return_delivered_order_items(
                order_id, item_ids, payment_method_id
            )
        )

        assert updated_order["status"] == "return requested"
        assert updated_order["return_items"] == sorted(item_ids)
        assert updated_order["return_payment_method_id"] == payment_method_id

    def test_return_order_not_found(self):
        with pytest.raises(OrderNotFoundError, match="Error: order not found"):
            return_delivered_order_items_tool.return_delivered_order_items(
                "#W1234567", ["1"], "gift_card_123"
            )

    def test_return_non_delivered_order(self):
        with pytest.raises(NonDeliveredOrderError, match="Error: non-delivered order cannot be returned"):
            return_delivered_order_items_tool.return_delivered_order_items(
                "#W5918442", ["1"], "credit_card_5051208"
            )

    def test_return_payment_method_not_found(self):
        with pytest.raises(PaymentMethodNotFoundError, match="Error: payment method not found"):
            return_delivered_order_items_tool.return_delivered_order_items(
                "#W4817420", ["6777246137"], "invalid_payment_method"
            )

    def test_return_invalid_payment_method(self):
        user_id = "ava_moore_2033"
        payment_method_id = "credit_card_5051208"
        db.DB["users"][user_id]["payment_methods"][payment_method_id] = {
            "id": payment_method_id
        }
        with pytest.raises(InvalidReturnPaymentMethodError, match="Error: payment method should be either the original payment method or a gift card"):
            return_delivered_order_items_tool.return_delivered_order_items(
                "#W4817420", ["6777246137"], "credit_card_5051208"
            )

    def test_return_item_not_found(self):
        with pytest.raises(ItemNotFoundError, match="Error: some item not found"):
            return_delivered_order_items_tool.return_delivered_order_items(
                "#W4817420", ["123"], "gift_card_8168843"
            )

    def test_return_delivered_order_items_input_validation(self):
        with pytest.raises(InvalidInputError):
            return_delivered_order_items_tool.return_delivered_order_items(
                123, ["1"], "gift_card_123"
            )
