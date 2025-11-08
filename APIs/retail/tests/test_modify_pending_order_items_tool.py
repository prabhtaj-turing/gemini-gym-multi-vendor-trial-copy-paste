import pytest
import copy
from retail import modify_pending_order_items_tool
from retail.SimulationEngine.custom_errors import (
    OrderNotFoundError,
    NonPendingOrderError,
    ItemNotFoundError,
    ItemMismatchError,
    ItemNotAvailableError,
    PaymentMethodNotFoundError,
    InsufficientGiftCardBalanceError,
    InvalidInputError,
)
from retail.SimulationEngine import db


class TestModifyPendingOrderItems:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)
        product_id = "1968349452"
        if "6956751343" not in db.DB["products"][product_id]["variants"]: # pragma: no cover
            db.DB["products"][product_id]["variants"]["6956751343"] = {
                "item_id": "6956751343",
                "options": {
                    "deck material": "bamboo",
                    "length": "34 inch",
                    "design": "custom",
                },
                "available": True,
                "price": 217.06,
            }
        db.DB["products"][product_id]["variants"]["6956751343"]["available"] = True

    def teardown_method(self):
        db.DB = self.original_db

    def test_modify_pending_order_items_success(self):
        order_id = "#W5918442"
        item_ids = ["5312063289"]
        new_item_ids = ["6956751343"]
        payment_method_id = "credit_card_5051208"

        updated_order = modify_pending_order_items_tool.modify_pending_order_items(
            order_id, item_ids, new_item_ids, payment_method_id
        )

        assert updated_order["status"] == "pending (item modified)"
        assert new_item_ids[0] in [item["item_id"] for item in updated_order["items"]]

    def test_modify_order_not_found(self):
        with pytest.raises(OrderNotFoundError, match="Error: order not found"):
            modify_pending_order_items_tool.modify_pending_order_items(
                "#W1234567", ["1"], ["2"], "gift_card_123"
            )

    def test_modify_non_pending_order(self):
        with pytest.raises(NonPendingOrderError, match="Error: non-pending order cannot be modified"):
            modify_pending_order_items_tool.modify_pending_order_items(
                "#W4817420", ["1"], ["2"], "credit_card_5051208"
            )

    def test_modify_item_not_found(self):
        with pytest.raises(ItemNotFoundError, match="Error: 123 not found"):
            modify_pending_order_items_tool.modify_pending_order_items(
                "#W5918442", ["123"], ["456"], "credit_card_5051208"
            )

    def test_modify_item_mismatch(self):
        with pytest.raises(ItemMismatchError, match="Error: the number of items to be exchanged should match"):
            modify_pending_order_items_tool.modify_pending_order_items(
                "#W5918442", ["1725100896", "5312063289"], ["6956751343"], "credit_card_5051208"
            )

    def test_modify_new_item_not_available(self):
        db.DB["products"]["1968349452"]["variants"]["6956751343"]["available"] = False
        with pytest.raises(ItemNotAvailableError, match="Error: new item 6956751343 not found or available"):
            modify_pending_order_items_tool.modify_pending_order_items(
                "#W5918442", ["5312063289"], ["6956751343"], "credit_card_5051208"
            )

    def test_modify_payment_method_not_found(self):
        with pytest.raises(PaymentMethodNotFoundError, match="Error: payment method not found"):
            modify_pending_order_items_tool.modify_pending_order_items(
                "#W5918442", ["5312063289"], ["6956751343"], "invalid_payment_method"
            )

    def test_modify_insufficient_gift_card_balance(self):
        order_id = "#W6779827"
        item_ids = ["7896397433"]
        new_item_ids = ["3877338112"]
        payment_method_id = "gift_card_7219486"
        db.DB["users"]["ethan_lopez_6291"]["payment_methods"][payment_method_id][
            "balance"
        ] = 0
        with pytest.raises(
            InsufficientGiftCardBalanceError,
            match="Error: insufficient gift card balance to pay for the new item",
        ):
            modify_pending_order_items_tool.modify_pending_order_items(
                order_id, item_ids, new_item_ids, payment_method_id
            )

    def test_modify_pending_order_items_input_validation(self):
        with pytest.raises(InvalidInputError):
            modify_pending_order_items_tool.modify_pending_order_items(
                123, ["1"], ["2"], "gift_card_123"
            )

    def test_modify_pending_order_items_with_gift_card_refund(self):
        order_id = "#W6779827"
        item_ids = ["7896397433"]
        new_item_ids = ["6130713659"]
        payment_method_id = "gift_card_7219486"
        user_id = "ethan_lopez_6291"

        db.DB["products"]["7233192239"]["variants"]["6130713659"]["available"] = True

        original_balance = db.DB["users"][user_id]["payment_methods"][payment_method_id]["balance"]
        
        old_item_price = db.DB["orders"][order_id]["items"][0]["price"]
        new_item_price = db.DB["products"]["7233192239"]["variants"]["6130713659"]["price"]
        price_diff = new_item_price - old_item_price

        updated_order = modify_pending_order_items_tool.modify_pending_order_items(
            order_id, item_ids, new_item_ids, payment_method_id
        )

        assert updated_order["status"] == "pending (item modified)"
        updated_balance = db.DB["users"][user_id]["payment_methods"][payment_method_id]["balance"]
        assert updated_balance == round(original_balance - price_diff, 2)

    def test_modify_items_when_status_pending_item_modified(self):
        order_id = "#W5918442"
        # Force status to 'pending (item modified)' and ensure variant availability via setup
        db.DB["orders"][order_id]["status"] = "pending (item modified)"

        item_ids = ["5312063289"]
        new_item_ids = ["6956751343"]
        payment_method_id = "credit_card_5051208"

        updated_order = modify_pending_order_items_tool.modify_pending_order_items(
            order_id, item_ids, new_item_ids, payment_method_id
        )

        assert updated_order["status"] == "pending (item modified)"
        assert new_item_ids[0] in [item["item_id"] for item in updated_order["items"]]
