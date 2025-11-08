import unittest
import copy
import json
from datetime import datetime, timezone
from decimal import Decimal
from shopify.orders import shopify_modify_pending_order_items
from shopify.SimulationEngine.db import DB, DEFAULT_DB_PATH
from shopify.SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestModifyPendingOrderItems(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a fresh DB for each test by reloading from the default JSON file."""
        DB.clear()
        with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
            DB.update(json.load(f))

    def tearDown(self):
        """Clean up DB after each test."""
        DB.clear()

    def test_modify_pending_order_items_successfully(self):
        """Test that an order's line items can be successfully modified."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        original_line_items = copy.deepcopy(original_order['line_items'])
        original_total_price = original_order['total_price']
        original_updated_at = original_order['updated_at']

        # Use the first line item's variant_id for update
        variant_id = str(original_line_items[0]['variant_id'])
        new_quantity = 5

        line_items_update = [{
            'variant_id': variant_id,
            'quantity': new_quantity,
        }]

        import time
        time.sleep(0.01)

        response = shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        self.assertIn('order', response)
        updated_order = response['order']

        # Find the updated line item by variant_id
        updated_line_item = next(item for item in updated_order['line_items'] if str(item.get('variant_id')) == str(variant_id))
        self.assertEqual(updated_line_item['quantity'], new_quantity)

        # Price should be the product variant's price from DB
        expected_price = None
        for product in DB['products'].values():
            for variant in product['variants']:
                if str(variant['id']) == str(variant_id):
                    expected_price = str(variant['price'])
                    break
            if expected_price is not None:
                break

        self.assertEqual(updated_line_item['price'], expected_price)
        expected_line_price = "{:.2f}".format(Decimal(expected_price) * new_quantity)
        self.assertEqual(updated_line_item['line_price'], expected_line_price)

        self.assertNotEqual(updated_order['total_price'], original_total_price)
        self.assertNotEqual(updated_order['updated_at'], original_updated_at)

        db_order = DB['orders'][order_id]
        db_line_item = next(item for item in db_order['line_items'] if str(item.get('variant_id')) == str(variant_id))
        self.assertEqual(db_line_item['quantity'], new_quantity)
        self.assertEqual(db_line_item['price'], expected_price)

    def test_modify_pending_order_items_remove_line_item(self):
        """Test removing a line item by setting quantity to 0."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        original_line_items = copy.deepcopy(original_order['line_items'])
        variant_id = str(original_line_items[0]['variant_id'])
        original_quantity = original_line_items[0]['quantity']

        # Get original inventory quantity
        original_inventory_quantity = 0
        for product in DB['products'].values():
            for variant in product.get('variants', []):
                if str(variant.get('id')) == variant_id:
                    original_inventory_quantity = variant.get('inventory_quantity', 0)
                    break

        line_items_update = [{'variant_id': variant_id, 'quantity': 0}]
        response = shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        updated_order = response['order']

        # The line item should be removed
        self.assertNotIn(variant_id, [str(item.get('variant_id')) for item in updated_order['line_items']])

        # Check if inventory is restocked
        for product in DB['products'].values():
            for variant in product.get('variants', []):
                if str(variant.get('id')) == variant_id:
                    self.assertEqual(variant.get('inventory_quantity'), original_inventory_quantity + original_quantity)
                    break

    def test_modify_pending_order_items_add_new_line_item(self):
        """Test adding a new line item by variant_id."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        # Find a variant_id not in the order
        all_variant_ids = set()
        for product in DB['products'].values():
            for variant in product['variants']:
                all_variant_ids.add(str(variant['id']))
        order_variant_ids = set(str(item.get('variant_id')) for item in original_order['line_items'])
        new_variant_id = next(vid for vid in all_variant_ids if vid not in order_variant_ids)

        # Ensure the new variant has enough inventory
        for product in DB['products'].values():
            for variant in product.get('variants', []):
                if str(variant.get('id')) == new_variant_id:
                    variant['inventory_quantity'] = 10
                    break

        line_items_update = [{'variant_id': new_variant_id, 'quantity': 2}]
        response = shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        updated_order = response['order']

        # The new line item should be present
        self.assertIn(new_variant_id, [str(item.get('variant_id')) for item in updated_order['line_items']])

    def test_modify_pending_order_items_nonexistent_order(self):
        """Test that modifying a non-existent order raises ResourceNotFoundError."""
        nonexistent_order_id = '99999'
        with self.assertRaises(custom_errors.ResourceNotFoundError) as context:
            shopify_modify_pending_order_items(nonexistent_order_id, line_items=[])
        self.assertIn(nonexistent_order_id, str(context.exception))

    def test_modify_pending_order_items_cancelled_order(self):
        """Test that modifying a cancelled order raises InvalidInputError."""
        cancelled_order_id = '20003'
        order = DB['orders'][cancelled_order_id]
        if order.get('cancelled_at') is None:
            order['cancelled_at'] = datetime.now(timezone.utc).isoformat()
            order['status'] = 'cancelled'
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(cancelled_order_id, line_items=[])
        self.assertIn("cancelled", str(context.exception))

    def test_modify_pending_order_items_closed_order(self):
        """Test that modifying a closed order raises InvalidInputError."""
        order_id = '20002'
        order = DB['orders'][order_id]
        if order.get('closed_at') is None:
            order['closed_at'] = datetime.now(timezone.utc).isoformat()
            order['status'] = 'closed'
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=[])
        self.assertIn("closed", str(context.exception))

    def test_modify_pending_order_items_fulfilled_order(self):
        """Test that modifying a fulfilled order raises InvalidInputError."""
        order_id = '20001'
        order = DB['orders'][order_id]
        order['fulfillment_status'] = 'fulfilled'
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=[])
        self.assertIn("fulfilled", str(context.exception))

    def test_modify_pending_order_items_invalid_line_items_format(self):
        """Test that passing invalid line_items format raises an error."""
        order_id = '20001'
        # The function expects a list of dicts.
        # A string is not a dict and will cause an InvalidInputError.
        invalid_line_items = ["this is not a dict"]
        with self.assertRaises(custom_errors.InvalidInputError):
            shopify_modify_pending_order_items(order_id, line_items=invalid_line_items)

    def test_modify_pending_order_items_invalid_line_item_id(self):
        """Test that using invalid variant_id raises InvalidInputError."""
        order_id = '20001'
        invalid_line_items = [{'variant_id': 'nonexistent_id', 'quantity': 1}]
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=invalid_line_items)
        self.assertIn("not found in products DB", str(context.exception))

    def test_modify_pending_order_items_missing_line_item_id(self):
        """Test that missing variant_id raises InvalidInputError."""
        order_id = '20001'
        invalid_line_items = [{'quantity': 1}]  # Missing 'variant_id'
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=invalid_line_items)
        self.assertIn("Field required", str(context.exception))

    def test_modify_pending_order_items_missing_quantity(self):
        """Test that missing quantity raises InvalidInputError."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        variant_id = str(original_order['line_items'][0]['variant_id'])
        invalid_line_items = [{'variant_id': variant_id}]
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=invalid_line_items)
        self.assertIn("Field required", str(context.exception))

    def test_modify_pending_order_items_zero_price(self):
        """Test that price is set from DB and line_item is removed if quantity is zero."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        variant_id = str(original_order['line_items'][0]['variant_id'])
        # Remove the item
        line_items_update = [{'variant_id': variant_id, 'quantity': 0}]
        response = shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        updated_order = response['order']
        self.assertNotIn(variant_id, [str(item.get('variant_id')) for item in updated_order['line_items']])

    def test_modify_pending_order_items_preserves_other_data(self):
        """Test that modifying items doesn't affect other order data."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        original_shipping_address = copy.deepcopy(original_order['shipping_address'])
        original_transactions = copy.deepcopy(original_order.get('transactions', []))
        original_customer = copy.deepcopy(original_order.get('customer', {}))
        # Update a line item
        variant_id = str(original_order['line_items'][0]['variant_id'])
        line_items_update = [{'variant_id': variant_id, 'quantity': 2}]
        response = shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        updated_order = response['order']
        self.assertEqual(updated_order['shipping_address'], original_shipping_address)
        # Only check that transactions and customer are still present (not necessarily unchanged, as refund may be added)
        self.assertIn('transactions', updated_order)
        self.assertIn('customer', updated_order)

    def test_modify_pending_order_items_decimal_precision(self):
        """Test that decimal calculations maintain proper precision."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        variant_id = str(original_order['line_items'][0]['variant_id'])
        # Set quantity to 3, price is from DB
        line_items_update = [{'variant_id': variant_id, 'quantity': 3}]
        response = shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        updated_order = response['order']
        updated_line_item = next(item for item in updated_order['line_items'] if str(item.get('variant_id')) == str(variant_id))
        # Get price from DB
        price = None
        for product in DB['products'].values():
            for variant in product['variants']:
                if str(variant['id']) == str(variant_id):
                    price = Decimal(str(variant['price']))
                    break
            if price is not None:
                break
        expected_line_price = "{:.2f}".format(price * 3)
        self.assertEqual(updated_line_item['line_price'], expected_line_price)

    def test_modify_pending_order_items_large_quantities(self):
        """Test handling of large quantities."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        variant_id = str(original_order['line_items'][0]['variant_id'])
        large_quantity = 999999

        # Ensure the variant has enough inventory
        for product in DB['products'].values():
            for variant in product.get('variants', []):
                if str(variant.get('id')) == variant_id:
                    variant['inventory_quantity'] = large_quantity
                    break

        line_items_update = [{'variant_id': variant_id, 'quantity': large_quantity}]
        response = shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        updated_order = response['order']
        updated_line_item = next(item for item in updated_order['line_items'] if str(item.get('variant_id')) == str(variant_id))
        self.assertEqual(updated_line_item['quantity'], large_quantity)

    def test_modify_pending_order_items_none_values(self):
        """Test handling of None values for optional parameters."""
        order_id = '20001'
        # Should succeed and not modify anything
        response = shopify_modify_pending_order_items(order_id, line_items=None)
        self.assertIn('order', response)

    def test_modify_pending_order_items_timestamp_update(self):
        """Test that updated_at timestamp is properly updated."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        original_updated_at = original_order['updated_at']
        import time
        time.sleep(0.001)
        response = shopify_modify_pending_order_items(order_id, line_items=None)
        updated_order = response['order']
        self.assertNotEqual(updated_order['updated_at'], original_updated_at)
        try:
            datetime.fromisoformat(updated_order['updated_at'])
        except ValueError:
            self.fail("updated_at timestamp is not in valid ISO 8601 format")

    def test_modify_pending_order_items_payment_method_validation(self):
        """Test that payment_method_id is validated for the customer."""
        order_id = '20001'
        order = DB['orders'][order_id]
        customer_id = order['customer']['id']
        customer = DB['customers'][customer_id]
        # Use a valid payment method
        if customer['payment_methods']:
            valid_payment_method_id = customer['payment_methods'][0]['id']
            # Should succeed
            response = shopify_modify_pending_order_items(order_id, line_items=None, payment_method_id=valid_payment_method_id)
            self.assertIn('order', response)
        # Use an invalid payment method
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=None, payment_method_id="not_a_real_pm")
        self.assertIn("Payment method", str(context.exception))

    def test_modify_pending_order_items_customer_missing(self):
        """Test that missing customer raises InvalidInputError."""
        order_id = '20001'
        order = DB['orders'][order_id]
        order['customer'] = {}
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=None)
        self.assertIn("customer assigned", str(context.exception))

    def test_modify_pending_order_items_customer_not_found(self):
        """Test that non-existent customer raises InvalidInputError."""
        order_id = '20001'
        order = DB['orders'][order_id]
        order['customer'] = {'id': 'not_a_real_customer'}
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=None)
        self.assertIn("Customer 'not_a_real_customer' not found", str(context.exception))

    def test_modify_pending_order_items_insufficient_stock(self):
        """Test that modifying an order with insufficient stock raises InvalidInputError."""
        order_id = '20001'
        original_order = DB['orders'][order_id]
        variant_id = str(original_order['line_items'][0]['variant_id'])

        # Find the variant and set its inventory to a low number
        for product in DB['products'].values():
            for variant in product.get('variants', []):
                if str(variant.get('id')) == variant_id:
                    variant['inventory_quantity'] = 1
                    break

        line_items_update = [{'variant_id': variant_id, 'quantity': 2}]
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            shopify_modify_pending_order_items(order_id, line_items=line_items_update)
        self.assertIn("Insufficient stock", str(context.exception))

if __name__ == '__main__':
    unittest.main()