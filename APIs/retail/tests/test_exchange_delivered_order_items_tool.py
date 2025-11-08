import pytest
import copy
from retail import exchange_delivered_order_items_tool
from retail.SimulationEngine.custom_errors import (
    InsufficientGiftCardBalanceError,
    ItemMismatchError,
    ItemNotAvailableError,
    ItemNotFoundError,
    NonDeliveredOrderError,
    OrderNotFoundError,
    PaymentMethodNotFoundError,
    InvalidInputError,
)
from retail.SimulationEngine import db

class TestExchangeDeliveredOrderItems:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)
        product_id = "8310926033"
        db.DB["products"][product_id]["variants"]["6469567736"]["available"] = True


    def teardown_method(self):
        db.DB = self.original_db

    def test_exchange_delivered_order_items_success(self):
        order_id = "#W4817420"
        item_ids = ["6777246137"]
        new_item_ids = ["6469567736"]
        payment_method_id = "gift_card_8168843"

        updated_order = exchange_delivered_order_items_tool.exchange_delivered_order_items(
            order_id, item_ids, new_item_ids, payment_method_id
        )

        assert updated_order["status"] == "exchange requested"
        assert updated_order["exchange_items"] == sorted(item_ids)
        assert updated_order["exchange_new_items"] == sorted(new_item_ids)
        assert updated_order["exchange_payment_method_id"] == payment_method_id
        assert "exchange_price_difference" in updated_order

    def test_exchange_order_not_found(self):
        with pytest.raises(OrderNotFoundError, match="Error: order not found"):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                "#W1234567", ["1"], ["2"], "gift_card_123"
            )

    def test_exchange_non_delivered_order(self):
        with pytest.raises(NonDeliveredOrderError, match="Error: non-delivered order cannot be exchanged"):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                "#W5918442", ["1"], ["2"], "credit_card_5051208"
            )

    def test_exchange_item_not_found(self):
        with pytest.raises(ItemNotFoundError, match="Error: 123 not found"):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                "#W4817420", ["123"], ["456"], "gift_card_8168843"
            )

    def test_exchange_item_mismatch(self):
        with pytest.raises(ItemMismatchError, match="Error: the number of items to be exchanged should match"):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                "#W4817420", ["6777246137"], [], "gift_card_8168843"
            )

    def test_exchange_new_item_not_available(self):
        db.DB["products"]["8310926033"]["variants"]["6469567736"]["available"] = False
        with pytest.raises(ItemNotAvailableError, match="Error: new item 6469567736 not found or available"):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                "#W4817420", ["6777246137"], ["6469567736"], "gift_card_8168843"
            )

    def test_exchange_payment_method_not_found(self):
        with pytest.raises(PaymentMethodNotFoundError, match="Error: payment method not found"):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                "#W4817420", ["6777246137"], ["6469567736"], "invalid_payment_method"
            )

    def test_exchange_insufficient_gift_card_balance(self):
        db.DB["users"]["ava_moore_2033"]["payment_methods"]["gift_card_8168843"]["balance"] = 0
        with pytest.raises(
            InsufficientGiftCardBalanceError,
            match="Error: insufficient gift card balance to pay for the price difference",
        ):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                "#W4817420", ["6777246137"], ["6469567736"], "gift_card_8168843"
            )

    def test_exchange_delivered_order_items_input_validation(self):
        with pytest.raises(InvalidInputError):
            exchange_delivered_order_items_tool.exchange_delivered_order_items(
                123, ["1"], ["2"], "gift_card_123"
            )
