import unittest
import copy
import json
from decimal import Decimal, InvalidOperation
from .. import cancel_order
from ..SimulationEngine.db import DB, DEFAULT_DB_PATH
from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestCancelOrder(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a fresh DB for each test by reloading from the default JSON file."""
        DB.clear()
        with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
            DB.update(json.load(f))

    def tearDown(self):
        """Clean up DB after each test."""
        DB.clear()

    def test_cancel_order_successfully(self):
        """Test that an order can be successfully cancelled."""
        # Using order '20002' which is closed but not cancelled in the default DB
        order_id = '20002'
        response = cancel_order(order_id)
        
        self.assertIn('order', response)
        cancelled_order = response['order']
        
        self.assertIsNotNone(cancelled_order.get('cancelled_at'))
        self.assertEqual(cancelled_order['id'], order_id)

    def test_cancel_already_cancelled_order(self):
        """Test that trying to cancel an already cancelled order raises an error."""
        # Using order '20003' which is already cancelled
        with self.assertRaises(custom_errors.OrderProcessingError):
            cancel_order('20003')

    def test_cancel_non_existent_order(self):
        """Test that trying to cancel a non-existent order raises a NotFoundError."""
        with self.assertRaises(custom_errors.NotFoundError):
            cancel_order('99999')

    def test_cancel_with_invalid_reason(self):
        """Test that cancelling with an invalid reason raises an InvalidInputError."""
        with self.assertRaises(custom_errors.InvalidInputError):
            cancel_order('20002', reason='bad_reason')

    def test_cancel_with_refund(self):
        """Test cancelling an order with a full refund."""
        order_id = '20002'
        # The original order has refunds, so a new one should be added.
        original_refund_count = len(DB.get('orders', {}).get(order_id, {}).get('refunds', []))

        amount = '10.00' # Partial refund
        response = cancel_order(order_id, amount=amount)
        
        cancelled_order = response['order']
        self.assertEqual(cancelled_order['financial_status'], 'partially_refunded')
        self.assertEqual(len(cancelled_order.get('refunds', [])), original_refund_count + 1)
        self.assertEqual(cancelled_order['refunds'][-1]['transactions'][0]['amount'], amount)

    def test_cancel_with_email(self):
        """Test that the email flag is correctly recorded."""
        order_id = '20002'
        response = cancel_order(order_id, email=True)
        
        cancelled_order = response['order']
        self.assertTrue(cancelled_order.get('send_cancellation_receipt'))

    def test_cancel_with_restock(self):
        """Test that restock flag updates line item fulfillment status."""
        order_id = '20002'
        response = cancel_order(order_id, restock=True)
        
        cancelled_order = response['order']
        self.assertEqual(cancelled_order['line_items'][0]['fulfillment_status'], 'restocked')

    def test_cancel_with_detailed_refund(self):
        """Test cancelling with a detailed refund object."""
        order_id = '20001' # Has multiple line items
        refund_details = {
            "note": "Detailed refund for a specific item.",
            "refund_line_items": [{
                "line_item_id": "30001",
                "quantity": 1,
                "restock_type": "return"
            }],
            "transactions": [{
                "parent_id": "40001",
                "amount": "12.99",
                "kind": "refund",
                "gateway": "shopify_payments"
            }]
        }
        response = cancel_order(order_id, refund=refund_details)
        cancelled_order = response['order']

        self.assertEqual(len(cancelled_order['refunds']), 1)
        self.assertEqual(cancelled_order['refunds'][0]['note'], "Detailed refund for a specific item.")
        self.assertEqual(cancelled_order['line_items'][0]['fulfillment_status'], 'restocked')
        self.assertEqual(cancelled_order['financial_status'], 'partially_refunded')

    def test_cancel_with_refund_currency_mismatch(self):
        """Test that a refund with a mismatched currency raises a RefundError."""
        with self.assertRaises(custom_errors.RefundError):
            cancel_order('20001', amount="10.00", currency="EUR")

    def test_cancel_with_invalid_refund_object(self):
        """Test that a malformed refund object raises an InvalidInputError."""
        order_id = '20001'
        invalid_refund_details = {
            "note": "This is missing required transaction fields."
        }
        with self.assertRaises(custom_errors.InvalidInputError):
            cancel_order(order_id, refund=invalid_refund_details)

    def test_cancel_with_refund_object_strict_type_checking(self):
        """Test that passing an incorrect type to refund object raises an error with strict mode."""
        order_id = '20001'
        # Pass an integer for parent_id where a string is expected
        invalid_type_refund = {
            "transactions": [{
                "parent_id": 40001, # Incorrect type
                "amount": "12.99",
                "kind": "refund",
                "gateway": "shopify_payments"
            }]
        }
        with self.assertRaises(custom_errors.InvalidInputError):
            cancel_order(order_id, refund=invalid_type_refund)

    def test_cancel_with_full_simple_refund_populates_line_items(self):
        """Test that a full simple refund correctly populates refund_line_items."""
        order_id = '20001' # Has 2 line items
        order_data = DB['orders'][order_id]
        full_amount = order_data['total_price']
        
        response = cancel_order(order_id, amount=full_amount)

        cancelled_order = response['order']
        self.assertEqual(cancelled_order['financial_status'], 'refunded')
        
        latest_refund = cancelled_order['refunds'][-1]
        self.assertIn('refund_line_items', latest_refund)
        self.assertEqual(len(latest_refund['refund_line_items']), len(order_data['line_items']))
        
        # Check if the refunded line items match the original ones
        original_li_ids = {str(li['id']) for li in order_data['line_items']}
        refunded_li_ids = {str(rli['line_item_id']) for rli in latest_refund['refund_line_items']}
        self.assertEqual(original_li_ids, refunded_li_ids)

    def test_cancel_with_manual_refund_updates_gift_card_balance(self):
        """Test that a manual refund during cancellation credits the customer's gift card balance."""
        order_id = '20001'
        order = DB['orders'][order_id]
        customer_id = order['customer']['id']
        initial_balance = Decimal(DB['customers'][customer_id]['gift_card_balance'])

        refund_amount = '12.50'
        # Provide a detailed refund object with manual gateway to trigger gift card credit
        refund_details = {
            "transactions": [{
                "parent_id": "40001",
                "amount": refund_amount,
                "kind": "refund",
                "gateway": "manual"
            }]
        }

        response = cancel_order(order_id, refund=refund_details)
        self.assertIn('order', response)

        updated_balance = Decimal(DB['customers'][customer_id]['gift_card_balance'])
        self.assertEqual(updated_balance, initial_balance + Decimal(refund_amount))

    def test_cancel_with_non_manual_refund_also_updates_gift_card_balance(self):
        """Refunds via non-manual gateway during cancellation should also credit gift card balance."""
        order_id = '20001'
        order = DB['orders'][order_id]
        customer_id = order['customer']['id']
        initial_balance = Decimal(DB['customers'][customer_id]['gift_card_balance'])

        refund_amount = '7.25'
        refund_details = {
            "transactions": [{
                "parent_id": "40001",
                "amount": refund_amount,
                "kind": "refund",
                "gateway": "shopify_payments"
            }]
        }

        response = cancel_order(order_id, refund=refund_details)
        self.assertIn('order', response)

        updated_balance = Decimal(DB['customers'][customer_id]['gift_card_balance'])
        self.assertEqual(updated_balance, initial_balance + Decimal(refund_amount))

if __name__ == '__main__':
    unittest.main()
