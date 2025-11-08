import pytest
import copy
from retail import modify_pending_order_payment_tool
from retail.SimulationEngine.custom_errors import (
    OrderNotFoundError,
    NonPendingOrderError,
    PaymentMethodNotFoundError,
    InvalidPaymentInfoError,
    SamePaymentMethodError,
    InsufficientGiftCardBalanceError,
    InvalidInputError,
)
from retail.SimulationEngine import db


class TestModifyPendingOrderPayment:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_modify_pending_order_payment_success(self):
        order_id = "#W5918442"
        payment_method_id = "paypal_7916550"
        user_id = "sofia_rossi_8776"
        db.DB["users"][user_id]["payment_methods"][payment_method_id] = {
            "id": payment_method_id
        }

        updated_order = (
            modify_pending_order_payment_tool.modify_pending_order_payment(
                order_id, payment_method_id
            )
        )

        assert len(updated_order["payment_history"]) == 3
        assert updated_order["payment_history"][1]["payment_method_id"] == payment_method_id

    def test_modify_order_not_found(self):
        with pytest.raises(OrderNotFoundError, match="Error: order not found"):
            modify_pending_order_payment_tool.modify_pending_order_payment(
                "#W1234567", "paypal_7916550"
            )

    def test_modify_non_pending_order(self):
        with pytest.raises(NonPendingOrderError, match="Error: non-pending order cannot be modified"):
            modify_pending_order_payment_tool.modify_pending_order_payment(
                "#W4817420", "paypal_7916550"
            )

    def test_modify_payment_method_not_found(self):
        with pytest.raises(PaymentMethodNotFoundError, match="Error: payment method not found"):
            modify_pending_order_payment_tool.modify_pending_order_payment(
                "#W5918442", "invalid_payment_method"
            )

    def test_modify_invalid_payment_info(self):
        order_id = "#W5918442"
        payment_method_id = "paypal_7916550"
        user_id = "sofia_rossi_8776"
        db.DB["users"][user_id]["payment_methods"][payment_method_id] = {
            "id": payment_method_id
        }
        db.DB["orders"][order_id]["payment_history"].append(
            {"transaction_type": "refund", "amount": 10.0, "payment_method_id": "paypal_7916550"}
        )
        with pytest.raises(InvalidPaymentInfoError, match="Error: there should be exactly one payment for a pending order"):
            modify_pending_order_payment_tool.modify_pending_order_payment(
                order_id, payment_method_id
            )

    def test_modify_same_payment_method(self):
        with pytest.raises(SamePaymentMethodError, match="Error: the new payment method should be different from the current one"):
            modify_pending_order_payment_tool.modify_pending_order_payment(
                "#W5918442", "credit_card_5051208"
            )

    def test_modify_insufficient_gift_card_balance(self):
        order_id = "#W6779827"
        payment_method_id = "gift_card_4855547"
        user_id = "ethan_lopez_6291"
        db.DB["users"][user_id]["payment_methods"][payment_method_id] = {
            "id": payment_method_id,
            "balance": 0,
        }
        with pytest.raises(
            InsufficientGiftCardBalanceError,
            match="Error: insufficient gift card balance to pay for the order",
        ):
            modify_pending_order_payment_tool.modify_pending_order_payment(
                order_id, payment_method_id
            )

    def test_modify_pending_order_payment_input_validation(self):
        with pytest.raises(InvalidInputError):
            modify_pending_order_payment_tool.modify_pending_order_payment(
                123, "paypal_7916550"
            )

    def test_modify_payment_from_gift_card(self):
        order_id = "#W6779827"
        new_payment_method_id = "credit_card_1234567"
        user_id = "ethan_lopez_6291"
        db.DB["users"][user_id]["payment_methods"][new_payment_method_id] = {
            "id": new_payment_method_id, "source": "credit_card", "brand": "Visa", "last_four": "1234"
        }
        
        original_balance = db.DB["users"][user_id]["payment_methods"]["gift_card_7219486"]["balance"]
        order_amount = db.DB["orders"][order_id]["payment_history"][0]["amount"]

        updated_order = modify_pending_order_payment_tool.modify_pending_order_payment(
            order_id, new_payment_method_id
        )

        assert len(updated_order["payment_history"]) == 3
        updated_balance = db.DB["users"][user_id]["payment_methods"]["gift_card_7219486"]["balance"]
        assert updated_balance == original_balance + order_amount

    def test_modify_payment_to_gift_card(self):
        order_id = "#W5918442"
        new_payment_method_id = "gift_card_1234567"
        user_id = "sofia_rossi_8776"
        db.DB["users"][user_id]["payment_methods"][new_payment_method_id] = {
            "id": new_payment_method_id, "source": "gift_card", "balance": 5000
        }

        original_balance = db.DB["users"][user_id]["payment_methods"][new_payment_method_id]["balance"]
        order_amount = db.DB["orders"][order_id]["payment_history"][0]["amount"]

        updated_order = modify_pending_order_payment_tool.modify_pending_order_payment(
            order_id, new_payment_method_id
        )

        assert len(updated_order["payment_history"]) == 3
        updated_balance = db.DB["users"][user_id]["payment_methods"][new_payment_method_id]["balance"]
        assert updated_balance == original_balance - order_amount

    def test_modify_payment_when_status_pending_item_modified(self):
        order_id = "#W5918442"
        # Force status to 'pending (item modified)'
        db.DB["orders"][order_id]["status"] = "pending (item modified)"

        new_payment_method_id = "paypal_9999999"
        user_id = "sofia_rossi_8776"
        db.DB["users"][user_id]["payment_methods"][new_payment_method_id] = {
            "id": new_payment_method_id
        }

        updated_order = (
            modify_pending_order_payment_tool.modify_pending_order_payment(
                order_id, new_payment_method_id
            )
        )

        assert len(updated_order["payment_history"]) == 3
        assert updated_order["payment_history"][1]["payment_method_id"] == new_payment_method_id
