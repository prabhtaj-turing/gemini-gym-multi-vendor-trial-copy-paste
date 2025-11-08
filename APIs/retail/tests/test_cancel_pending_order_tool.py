import pytest
import copy
from retail import cancel_pending_order_tool
from retail.SimulationEngine.custom_errors import (
    InvalidCancelReasonError,
    NonPendingOrderError,
    OrderNotFoundError,
    InvalidInputError,
)
from retail.SimulationEngine import db


class TestCancelPendingOrder:
    original_db = None

    def setup_method(self):
        self.original_db = copy.deepcopy(db.DB)

    def teardown_method(self):
        db.DB = self.original_db

    def test_cancel_pending_order_success(self):
        order_id = "#W5918442"
        reason = "no longer needed"
        original_order = db.DB["orders"][order_id]
        original_user = db.DB["users"][original_order["user_id"]]
        payment_method_id = original_order["payment_history"][0]["payment_method_id"]
        original_balance = original_user["payment_methods"].get(payment_method_id, {}).get("balance")

        updated_order = cancel_pending_order_tool.cancel_pending_order(order_id, reason)

        assert updated_order["status"] == "cancelled"
        assert updated_order["cancel_reason"] == reason
        assert len(updated_order["payment_history"]) == 2

        refund_transaction = updated_order["payment_history"][-1]
        assert refund_transaction["transaction_type"] == "refund"
        assert refund_transaction["amount"] == original_order["payment_history"][0]["amount"]

    def test_cancel_pending_order_not_found(self):
        with pytest.raises(OrderNotFoundError, match="Error: order not found"):
            cancel_pending_order_tool.cancel_pending_order("#W1234567", "no longer needed")

    def test_cancel_non_pending_order(self):
        order_id = "#W4817420"
        with pytest.raises(NonPendingOrderError, match="Error: non-pending order cannot be cancelled"):
            cancel_pending_order_tool.cancel_pending_order(order_id, "no longer needed")

    def test_cancel_with_invalid_reason(self):
        order_id = "#W5918442"
        with pytest.raises(InvalidCancelReasonError, match="Error: invalid reason"):
            cancel_pending_order_tool.cancel_pending_order(order_id, "invalid reason")

    def test_cancel_pending_order_input_validation(self):
        with pytest.raises(InvalidInputError):
            cancel_pending_order_tool.cancel_pending_order(123, "no longer needed")

    def test_cancel_pending_order_with_gift_card(self):
        order_id = "#W6779827"
        reason = "no longer needed"
        original_order = db.DB["orders"][order_id]
        user_id = original_order["user_id"]
        payment_method_id = original_order["payment_history"][0]["payment_method_id"]
        original_balance = db.DB["users"][user_id]["payment_methods"][payment_method_id]["balance"]

        updated_order = cancel_pending_order_tool.cancel_pending_order(order_id, reason)

        assert updated_order["status"] == "cancelled"
        assert updated_order["cancel_reason"] == reason
        
        updated_balance = db.DB["users"][user_id]["payment_methods"][payment_method_id]["balance"]
        refund_amount = original_order["payment_history"][0]["amount"]
        assert updated_balance == original_balance + refund_amount

    def test_cancel_order_when_status_pending_item_modified(self):
        order_id = "#W5918442"
        reason = "no longer needed"
        # Set order status to 'pending (item modified)' to ensure cancellation is allowed
        db.DB["orders"][order_id]["status"] = "pending (item modified)"

        updated_order = cancel_pending_order_tool.cancel_pending_order(order_id, reason)

        assert updated_order["status"] == "cancelled"
        assert updated_order["cancel_reason"] == reason
