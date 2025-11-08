import copy
import datetime
from datetime import timezone, timedelta, datetime
from typing import Optional
import time
from stripe import create_invoice, create_invoice_item, list_invoices
from ..SimulationEngine import custom_errors
from ..SimulationEngine.custom_errors import (
    ResourceNotFoundError,
    InvalidRequestError,
    ValidationError,
)
from ..SimulationEngine.db import DB
from ..SimulationEngine.models import (
    Invoice,
    InvoiceLineItem,
    InvoiceLineItemPrice,
    InvoiceLines,
    InvoiceItem,
    InvoiceItemPrice,
)
from .. import finalize_invoice
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCreateInvoice(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            'customers': {},
            'products': {},
            'prices': {},
            'payment_links': {},
            'invoices': {},
            'invoice_items': {},
            'balance': {'object': 'balance', 'available': [], 'pending': [], 'livemode': False},
            'refunds': {},
            'payment_intents': {},
            'subscriptions': {},
            'coupons': {},
            'disputes': {}
        })

        self.valid_customer_id = "cus_valid_123abc"
        DB['customers'][self.valid_customer_id] = {
            'id': self.valid_customer_id,
            'object': 'customer',
            'name': 'Valid Customer',
            'email': 'valid@example.com',
            'created': int(datetime.now(timezone.utc).timestamp()),  # Added timezone.utc
            'livemode': False,
            'metadata': None  # Customer metadata, not invoice metadata
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_invoice_structure(self, invoice_data: dict, customer_id: str, expected_due_date: Optional[int]):
        self.assertIsInstance(invoice_data, dict)

        self.assertIn('id', invoice_data)
        self.assertIsInstance(invoice_data['id'], str)
        self.assertTrue(invoice_data['id'].startswith("inv_"))  # Assuming Pydantic model uses "inv_"

        self.assertEqual(invoice_data.get('object'), "invoice")
        self.assertEqual(invoice_data.get('customer'), customer_id)
        self.assertEqual(invoice_data.get('status'), "draft")
        self.assertEqual(invoice_data.get('total'), 0)
        self.assertEqual(invoice_data.get('amount_due'), 0)
        self.assertEqual(invoice_data.get('currency'), "usd")

        self.assertIn('created', invoice_data)
        self.assertIsInstance(invoice_data['created'], int)
        # Loosened delta slightly for CI environments or slower machines if now() is called separately
        self.assertAlmostEqual(invoice_data['created'], int(datetime.now(timezone.utc).timestamp()), delta=15)

        if expected_due_date is None:
            # If due_date is None and model_dump(exclude_none=True) is used, key might be absent
            self.assertIsNone(invoice_data.get('due_date'))
        else:
            self.assertIsNotNone(invoice_data.get('due_date'))
            self.assertIsInstance(invoice_data['due_date'], int)
            self.assertAlmostEqual(invoice_data['due_date'], expected_due_date, delta=5)  # Increased delta slightly

        self.assertEqual(invoice_data.get('livemode'), False)

        # For metadata, if it's None and model_dump(exclude_none=True) is used, the key will be absent.
        # So, invoice_data.get('metadata') will return None.
        self.assertIsNone(invoice_data.get('metadata'))

        self.assertIn('lines', invoice_data)
        self.assertIsInstance(invoice_data['lines'], dict)
        lines = invoice_data['lines']
        self.assertEqual(lines.get('object'), "list")
        self.assertIn('data', lines)
        self.assertIsInstance(lines['data'], list)
        self.assertEqual(len(lines['data']), 0)
        self.assertEqual(lines.get('has_more'), False)

    def test_create_invoice_success_customer_only(self):
        initial_invoice_count = len(DB.get('invoices', {}))

        invoice = create_invoice(customer=self.valid_customer_id)

        self._assert_invoice_structure(invoice, self.valid_customer_id, expected_due_date=None)

        self.assertEqual(len(DB['invoices']), initial_invoice_count + 1)
        self.assertIn(invoice['id'], DB['invoices'])
        self.assertEqual(DB['invoices'][invoice['id']], invoice)

    def test_create_invoice_success_with_days_until_due(self):
        days_due = 7
        initial_invoice_count = len(DB.get('invoices', {}))
        # The test calculates expected_due_date based on the *returned* 'created' time.
        invoice = create_invoice(customer=self.valid_customer_id, days_until_due=days_due)

        # Let's calculate the expected due date based on the returned 'created' field,
        # which is the most reliable way to test the *offset* given the current implementation.
        created_timestamp_for_calc = invoice['created']
        expected_due_dt = datetime.fromtimestamp(created_timestamp_for_calc, timezone.utc) + timedelta(days=days_due)
        expected_due_timestamp = int(expected_due_dt.timestamp())

        self._assert_invoice_structure(invoice, self.valid_customer_id, expected_due_date=expected_due_timestamp)

        self.assertEqual(len(DB['invoices']), initial_invoice_count + 1)
        self.assertIn(invoice['id'], DB['invoices'])

    def test_create_invoice_success_with_zero_days_until_due(self):
        days_due = 0
        invoice = create_invoice(customer=self.valid_customer_id, days_until_due=days_due)

        created_timestamp_for_calc = invoice['created']
        expected_due_dt = datetime.fromtimestamp(created_timestamp_for_calc, timezone.utc) + timedelta(days=days_due)
        expected_due_timestamp = int(expected_due_dt.timestamp())

        self._assert_invoice_structure(invoice, self.valid_customer_id, expected_due_date=expected_due_timestamp)

    def test_create_invoice_customer_not_found_raises_resource_not_found_error(self):
        non_existent_customer_id = "cus_non_existent_xyz"
        self.assert_error_behavior(
            func_to_call=create_invoice,
            expected_exception_type=ResourceNotFoundError,
            expected_message=f"Customer with ID '{non_existent_customer_id}' not found.",
            customer=non_existent_customer_id
        )

    def test_create_invoice_customer_id_not_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_invoice,
            expected_exception_type=ValidationError,
            expected_message="Customer ID must be a string.",
            customer=12345  # type: ignore
        )

    def test_create_invoice_customer_id_none_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_invoice,
            expected_exception_type=ValidationError,
            expected_message="Customer ID must be a string.",
            customer=None  # type: ignore
        )

    def test_create_invoice_customer_id_empty_string_raises_invalid_request_error(self):
        self.assert_error_behavior(
            func_to_call=create_invoice,
            expected_exception_type=InvalidRequestError,
            expected_message="Customer ID cannot be empty.",
            customer=""
        )

    def test_create_invoice_days_until_due_not_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_invoice,
            expected_exception_type=ValidationError,
            expected_message="Days until due must be an integer.",
            customer=self.valid_customer_id,
            days_until_due="abc"  # type: ignore
        )

    def test_create_invoice_days_until_due_float_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_invoice,
            expected_exception_type=ValidationError,
            expected_message="Days until due must be an integer.",
            customer=self.valid_customer_id,
            days_until_due=7.5  # type: ignore
        )

    def test_create_invoice_days_until_due_negative_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=create_invoice,
            expected_exception_type=ValidationError,
            expected_message="Days until due cannot be negative.",
            customer=self.valid_customer_id,
            days_until_due=-5
        )

    def test_create_invoice_id_is_unique(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)

        # Ensuring a slight delay if generate_id is time-sensitive to microseconds
        import time
        time.sleep(0.000001)

        invoice2 = create_invoice(customer=self.valid_customer_id)

        self.assertIsNotNone(invoice1.get('id'))
        self.assertIsNotNone(invoice2.get('id'))
        self.assertNotEqual(invoice1['id'], invoice2['id'])
        self.assertTrue(invoice1['id'] in DB['invoices'])
        self.assertTrue(invoice2['id'] in DB['invoices'])

    def test_list_invoices_for_customer_success(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id)
        self.assertEqual(len(invoices['data']), 2)
        self.assertEqual(invoices['data'][0]['id'], invoice1['id'])
        self.assertEqual(invoices['data'][1]['id'], invoice2['id'])

    def test_list_invoices_for_customer_success_with_status(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, status="draft")
        self.assertEqual(len(invoices['data']), 2)
        self.assertEqual(invoices['data'][0]['id'], invoice1['id'])
        self.assertEqual(invoices['data'][1]['id'], invoice2['id'])
    
    def test_list_invoices_for_customer_success_with_starting_after(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        time.sleep(1)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, starting_after=invoice1['id'])
        self.assertEqual(len(invoices['data']), 1)
        self.assertEqual(invoices['data'][0]['id'], invoice2['id'])
    
    def test_list_invoices_for_customer_success_with_ending_before(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        time.sleep(1)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, ending_before=invoice2['id'])
        self.assertEqual(len(invoices['data']), 1)
        self.assertEqual(invoices['data'][0]['id'], invoice1['id'])

    def test_list_invoices_for_customer_success_with_limit(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, limit=1)
        self.assertEqual(len(invoices['data']), 1)
        self.assertEqual(invoices['data'][0]['id'], invoice1['id'])

    def test_list_invoices_for_customer_success_with_starting_after_and_ending_before(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, starting_after=invoice1['id'], ending_before=invoice2['id'])
        self.assertEqual(len(invoices['data']), 0)

    def test_list_invoices_for_customer_success_with_starting_after_and_limit(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, starting_after=invoice1['id'], limit=1)
        self.assertEqual(len(invoices['data']), 1)
        self.assertEqual(invoices['data'][0]['id'], invoice2['id'])

    def test_list_invoices_for_customer_success_with_created(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        time.sleep(1)
        invoice2 = create_invoice(customer=self.valid_customer_id)
        invoices = list_invoices(customer=self.valid_customer_id, created={'gte': invoice2['created']})
        self.assertEqual(len(invoices['data']), 1)
        self.assertEqual(invoices['data'][0]['id'], invoice2['id'])

    def test_list_invoices_for_customer_success_with_created_and_limit(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        time.sleep(1)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, created={'gte': invoice2['created']}, limit=1)
        self.assertEqual(len(invoices['data']), 1)
        self.assertEqual(invoices['data'][0]['id'], invoice2['id'])
    
    def test_list_invoices_for_customer_success_with_created_lte(self):
        invoice2 = create_invoice(customer=self.valid_customer_id)
        time.sleep(3)
        invoice3 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(created={'lte': invoice3['created']})
        self.assertEqual(len(invoices['data']), 2)

    def test_list_invoices_for_customer_success_with_created_lt(self):
        invoice2 = create_invoice(customer=self.valid_customer_id)
        time.sleep(3)
        invoice3 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(created={'lt': invoice3['created']})
        self.assertEqual(len(invoices['data']), 1)

    def test_list_invoices_for_customer_success_with_created_gt(self):
        invoice2 = create_invoice(customer=self.valid_customer_id)
        time.sleep(3)
        invoice3 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(created={'gt': invoice2['created']})
        self.assertEqual(len(invoices['data']), 1)

    def test_list_invoices_for_customer_success_with_created_gt_limit_none(self):
        invoice2 = create_invoice(customer=self.valid_customer_id)
        time.sleep(3)
        invoice3 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(created={'gt': invoice2['created']}, limit=None)
        self.assertEqual(len(invoices['data']), 1)
        self.assertEqual(invoices['has_more'], False)

    def test_list_invoices_for_customer_success_with_created_and_starting_after(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        time.sleep(1)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, created={'gte': invoice1['created']}, starting_after=invoice2['id'])
        self.assertEqual(len(invoices['data']), 0)

    def test_list_invoices_for_customer_success_with_created_and_ending_before(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        time.sleep(1)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, created={'gte': invoice2['created']}, ending_before=invoice2['id'])
        self.assertEqual(len(invoices['data']), 0)

    def test_list_invoices_for_customer_success_with_created_and_starting_after_and_ending_before(self):
        invoice1 = create_invoice(customer=self.valid_customer_id)
        invoice2 = create_invoice(customer=self.valid_customer_id)

        invoices = list_invoices(customer=self.valid_customer_id, created={'gte': invoice1['created']}, starting_after=invoice2['id'], ending_before=invoice1['id'])
        self.assertEqual(len(invoices['data']), 0)

    def test_list_invoices_for_customer_customer_id_not_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Customer must be a string.",
            customer=12345  # type: ignore
        )

    def test_list_invoices_for_customer_customer_id_empty_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=ValueError,
            expected_message="Customer cannot be empty.",
            customer=""
        )

    def test_list_invoices_for_customer_customer_not_found_raises_resource_not_found_error(self):
        non_existent_customer_id = "cus_non_existent_xyz"
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=ValueError,
            expected_message=f"Customer {non_existent_customer_id} not found.",
            customer=non_existent_customer_id
        )
    
    def test_list_invoices_for_customer_status_not_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Status must be a string.",
            customer=self.valid_customer_id,
            status=12345  # type: ignore
        )
    
    def test_list_invoices_for_customer_status_not_valid_status_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=ValueError,
            expected_message="Invalid status: 12345. Allowed values are: draft, open, paid, uncollectible, void.",
            customer=self.valid_customer_id,
            status="12345"
        )
    
    def test_list_invoices_for_customer_limit_not_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Limit must be an integer.",
            customer=self.valid_customer_id,
            limit="12345"  # type: ignore
        )
    
    def test_list_invoices_for_customer_limit_negative_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=ValueError,
            expected_message="Limit must be at least 1.",
            customer=self.valid_customer_id,
            limit=-5
        )
    
    def test_list_invoices_for_customer_limit_exceeds_100_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=ValueError,
            expected_message="Limit cannot exceed 100.",
            customer=self.valid_customer_id,
            limit=101
        )
    
    def test_list_invoices_for_customer_starting_after_not_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Starting after must be a string.",
            customer=self.valid_customer_id,
            starting_after=12345
        )

    def test_list_invoices_for_customer_starting_after_empty_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=ValueError,
            expected_message="Starting after cannot be empty.",
            customer=self.valid_customer_id,
            starting_after=" "
        )

    def test_list_invoices_for_customer_ending_before_empty_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=ValueError,
            expected_message="Ending before cannot be empty.",
            customer=self.valid_customer_id,
            ending_before=" "
        )   

    def test_list_invoices_for_customer_ending_before_not_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Ending before must be a string.",
            customer=self.valid_customer_id,
            ending_before=12345  # type: ignore
        )
    
    def test_list_invoices_for_customer_ending_before_not_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Ending before must be a string.",
            customer=self.valid_customer_id,
            ending_before=12345  # type: ignore
        )
    
    def test_list_invoices_for_customer_ending_before_not_string_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Ending before must be a string.",
            customer=self.valid_customer_id,
            ending_before=12345  # type: ignore
        )

    def test_list_invoices_for_customer_created_not_dict_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Created must be a dictionary.",
            customer=self.valid_customer_id,
            created=12345  # type: ignore
        )
    
    def test_list_invoices_for_customer_created_gte_not_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Created gte must be an integer.",
            customer=self.valid_customer_id,
            created={'gte': '12345'}  # type: ignore
        )
    
    def test_list_invoices_for_customer_created_lte_not_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Created lte must be an integer.",
            customer=self.valid_customer_id,
            created={'lte': '12345'}  # type: ignore
        )
    
    def test_list_invoices_for_customer_created_gt_not_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Created gt must be an integer.",
            customer=self.valid_customer_id,
            created={'gt': '12345'}  # type: ignore
        )
    
    def test_list_invoices_for_customer_created_lt_not_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Created lt must be an integer.",
            customer=self.valid_customer_id,
            created={'lt': '12345'}  # type: ignore
        )
    
    def test_list_invoices_for_customer_created_not_dict_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_invoices,
            expected_exception_type=TypeError,
            expected_message="Created must be a dictionary.",
            customer=self.valid_customer_id,
            created=12345  # type: ignore
        )

    def test_create_invoice_pydantic_validation_error(self):
        """Test that Pydantic validation errors are properly caught and converted to ValidationError."""
        from unittest.mock import patch
        from pydantic import ValidationError as PydanticValidationError
        from stripe.SimulationEngine.models import Invoice
        
        # Create a real PydanticValidationError by passing invalid data
        try:
            Invoice(customer=None)  # customer is required and must be str
        except PydanticValidationError as real_error:
            with patch('stripe.invoice.Invoice') as mock_invoice:
                mock_invoice.side_effect = real_error
                self.assert_error_behavior(
                    func_to_call=create_invoice,
                    expected_exception_type=ValidationError,
                    expected_message=f"Invoice data validation failed by model: {real_error.errors()}",
                    customer=self.valid_customer_id
                )

class TestCreateInvoiceItem(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self.DB = DB  # Assign global DB to self.DB
        self.DB.clear()

        self.customer_id_1 = "cus_default_123"
        self.product_id_1 = "prod_default_abc"
        self.price_id_1_usd = "price_default_usd_1000"
        self.price_id_2_eur = "price_default_eur_500"
        self.price_id_3_inactive_usd = "price_default_inactive_usd"
        self.price_id_4_usd_zero_amount = "price_default_usd_0"

        self.invoice_id_1_draft_usd = "inv_default_draft_usd"
        self.invoice_id_2_paid_usd = "inv_default_paid_usd"
        self.invoice_id_3_draft_eur = "inv_default_draft_eur"
        self.invoice_id_4_open_usd = "inv_default_open_usd"

        self.DB['customers'] = {
            self.customer_id_1: {
                'id': self.customer_id_1, 'object': 'customer', 'name': 'Test Customer 1',
                'email': 'test@example.com', 'created': 1678886400, 'livemode': False, 'metadata': None,
            }
        }
        self.DB['products'] = {
            self.product_id_1: {
                'id': self.product_id_1, 'object': 'product', 'name': 'Test Product 1',
                'active': True, 'created': 1678886400, 'updated': 1678886400,
                'livemode': False, 'metadata': None, 'description': 'A test product'
            }
        }
        self.DB['prices'] = {
            self.price_id_1_usd: {
                'id': self.price_id_1_usd, 'object': 'price', 'active': True, 'product': self.product_id_1,
                'unit_amount': 1000, 'currency': 'usd', 'type': 'one_time', 'livemode': False,
                'created': 1678886400, 'recurring': None, 'metadata': {'source': 'test_setup_usd'},
                'billing_scheme': "per_unit",
            },
            self.price_id_2_eur: {
                'id': self.price_id_2_eur, 'object': 'price', 'active': True, 'product': self.product_id_1,
                'unit_amount': 500, 'currency': 'eur', 'type': 'one_time', 'livemode': False,
                'created': 1678886400, 'recurring': None, 'metadata': None,
                'billing_scheme': "per_unit",
            },
            self.price_id_3_inactive_usd: {
                'id': self.price_id_3_inactive_usd, 'object': 'price', 'active': False,  # Inactive
                'product': self.product_id_1, 'unit_amount': 2000, 'currency': 'usd',
                'type': 'one_time', 'livemode': False, 'created': 1678886400,
                'recurring': None, 'metadata': None, 'billing_scheme': "per_unit",
            },
            self.price_id_4_usd_zero_amount: {
                'id': self.price_id_4_usd_zero_amount, 'object': 'price', 'active': True,
                'product': self.product_id_1, 'unit_amount': 0, 'currency': 'usd',  # Zero amount
                'type': 'one_time', 'livemode': False, 'created': 1678886400,
                'recurring': None, 'metadata': None, 'billing_scheme': "per_unit",
            }
        }
        self.DB['invoices'] = {
            self.invoice_id_1_draft_usd: {
                'id': self.invoice_id_1_draft_usd, 'object': 'invoice', 'customer': self.customer_id_1,
                'status': 'draft', 'total': 0, 'amount_due': 0, 'currency': 'usd',
                'created': 1678886400, 'livemode': False,
                'lines': {'object': 'list', 'data': [], 'has_more': False},
                'metadata': None, 'due_date': None,
            },
            self.invoice_id_2_paid_usd: {
                'id': self.invoice_id_2_paid_usd, 'object': 'invoice', 'customer': self.customer_id_1,
                'status': 'paid', 'total': 500, 'amount_due': 0, 'currency': 'usd',
                'created': 1678886400, 'livemode': False,
                'lines': {'object': 'list', 'data': [], 'has_more': False},
                'metadata': None, 'due_date': None,
            },
            self.invoice_id_3_draft_eur: {
                'id': self.invoice_id_3_draft_eur, 'object': 'invoice', 'customer': self.customer_id_1,
                'status': 'draft', 'total': 0, 'amount_due': 0, 'currency': 'eur',
                'created': 1678886400, 'livemode': False,
                'lines': {'object': 'list', 'data': [], 'has_more': False},
                'metadata': None, 'due_date': None,
            },
            self.invoice_id_4_open_usd: {
                'id': self.invoice_id_4_open_usd, 'object': 'invoice', 'customer': self.customer_id_1,
                'status': 'open', 'total': 100, 'amount_due': 100, 'currency': 'usd',
                'created': 1678886401, 'livemode': False,
                'lines': {'object': 'list', 'data': [  # Pre-existing line item
                    {
                        'id': 'ii_existing_item', 'amount': 100, 'quantity': 1,
                        'price': {'id': 'price_existing', 'product': 'prod_existing'},
                        'description': 'Existing item'
                    }
                ], 'has_more': False},
                'metadata': None, 'due_date': None,
            }
        }
        self.DB['invoice_items'] = {
            'ii_existing_item': {  # Corresponds to the line item in invoice_id_4_open_usd
                'id': 'ii_existing_item', 'object': 'invoiceitem', 'customer': self.customer_id_1,
                'invoice': self.invoice_id_4_open_usd,
                'price': {'id': 'price_existing', 'product': 'prod_existing', 'unit_amount': 100, 'currency': 'usd'},
                'amount': 100, 'currency': 'usd', 'quantity': 1, 'livemode': False, 'metadata': None
            }
        }

    def test_create_invoice_item_success_on_draft_invoice(self):
        customer_id = self.customer_id_1
        price_id = self.price_id_1_usd
        invoice_id = self.invoice_id_1_draft_usd

        price_data = self.DB['prices'][price_id]
        initial_invoice_state = copy.deepcopy(self.DB['invoices'][invoice_id])

        result = create_invoice_item(customer=customer_id, price=price_id, invoice=invoice_id)

        self.assertIsInstance(result, dict)
        self.assertTrue(result['id'].startswith("inv_"))
        self.assertEqual(result['object'], "invoiceitem")
        self.assertEqual(result['customer'], customer_id)
        self.assertEqual(result['invoice'], invoice_id)
        self.assertIsNotNone(result['price'])

        expected_price_details = {
            'id': price_id, 'product': price_data['product'],
            'unit_amount': price_data['unit_amount'], 'currency': price_data['currency']
        }
        # Validate structure of result['price'] against InvoiceItemPrice fields
        self.assertIsInstance(result['price'], dict)
        for key, value in expected_price_details.items():
            self.assertEqual(result['price'][key], value, f"Price field '{key}' mismatch.")

        self.assertEqual(result['amount'], price_data['unit_amount'])
        self.assertEqual(result['currency'], price_data['currency'])
        self.assertEqual(result['quantity'], 1)
        self.assertEqual(result['livemode'], False)
        self.assertIsNone(result['metadata'])

        self.assertIn(result['id'], self.DB['invoice_items'])
        created_item_in_db = self.DB['invoice_items'][result['id']]
        self.assertEqual(created_item_in_db['customer'], customer_id)
        self.assertEqual(created_item_in_db['invoice'], invoice_id)
        self.assertEqual(created_item_in_db['price']['id'], price_id)
        self.assertEqual(created_item_in_db['amount'], price_data['unit_amount'])

        updated_invoice = self.DB['invoices'][invoice_id]
        self.assertEqual(updated_invoice['total'], initial_invoice_state['total'] + price_data['unit_amount'])
        self.assertEqual(updated_invoice['amount_due'], initial_invoice_state['amount_due'] + price_data['unit_amount'])
        self.assertEqual(len(updated_invoice['lines']['data']), 1)

        invoice_line_item = updated_invoice['lines']['data'][0]
        self.assertEqual(invoice_line_item['id'], result['id'])
        self.assertEqual(invoice_line_item['amount'], price_data['unit_amount'])
        self.assertEqual(invoice_line_item['quantity'], 1)
        self.assertEqual(invoice_line_item['price']['id'], price_id)
        self.assertEqual(invoice_line_item['price']['product'], price_data['product'])
        self.assertEqual(invoice_line_item['description'], f"Item from price {price_id}")

    def test_create_invoice_item_success_on_open_invoice_with_existing_items(self):
        customer_id = self.customer_id_1
        price_id = self.price_id_1_usd  # 1000 USD
        invoice_id = self.invoice_id_4_open_usd  # Has 1 existing item of 100 USD

        price_data = self.DB['prices'][price_id]
        initial_invoice_state = copy.deepcopy(self.DB['invoices'][invoice_id])
        initial_total_items = len(initial_invoice_state['lines']['data'])

        result = create_invoice_item(customer=customer_id, price=price_id, invoice=invoice_id)

        updated_invoice = self.DB['invoices'][invoice_id]
        expected_new_total = initial_invoice_state['total'] + price_data['unit_amount']
        self.assertEqual(updated_invoice['total'], expected_new_total)
        self.assertEqual(updated_invoice['amount_due'],
                         expected_new_total)  # Assuming amount_due tracks total for open invoices
        self.assertEqual(len(updated_invoice['lines']['data']), initial_total_items + 1)

        # Check that the new item is the last one in the lines
        new_invoice_line_item = updated_invoice['lines']['data'][-1]
        self.assertEqual(new_invoice_line_item['id'], result['id'])
        self.assertEqual(new_invoice_line_item['amount'], price_data['unit_amount'])

    def test_create_invoice_item_with_zero_amount_price(self):
        customer_id = self.customer_id_1
        price_id = self.price_id_4_usd_zero_amount  # 0 USD
        invoice_id = self.invoice_id_1_draft_usd

        price_data = self.DB['prices'][price_id]
        result = create_invoice_item(customer=customer_id, price=price_id, invoice=invoice_id)

        self.assertEqual(result['amount'], 0)
        self.assertEqual(result['price']['unit_amount'], 0)

        updated_invoice = self.DB['invoices'][invoice_id]
        self.assertEqual(updated_invoice['total'], 0)
        self.assertEqual(updated_invoice['amount_due'], 0)
        self.assertEqual(len(updated_invoice['lines']['data']), 1)
        self.assertEqual(updated_invoice['lines']['data'][0]['amount'], 0)

    def test_create_invoice_item_customer_not_found(self):
        self.assert_error_behavior(
            func_to_call=create_invoice_item,
            expected_exception_type=ResourceNotFoundError,
            expected_message="Customer with ID 'cus_nonexistent' not found.",
            customer="cus_nonexistent", price=self.price_id_1_usd, invoice=self.invoice_id_1_draft_usd
        )

    def test_create_invoice_item_price_not_found(self):
        self.assert_error_behavior(
            func_to_call=create_invoice_item,
            expected_exception_type=ResourceNotFoundError,
            expected_message="Price with ID 'price_nonexistent' not found.",
            customer=self.customer_id_1, price="price_nonexistent", invoice=self.invoice_id_1_draft_usd
        )

    def test_create_invoice_item_invoice_not_found(self):
        self.assert_error_behavior(
            func_to_call=create_invoice_item,
            expected_exception_type=ResourceNotFoundError,
            expected_message="Invoice with ID 'inv_nonexistent' not found.",
            customer=self.customer_id_1, price=self.price_id_1_usd, invoice="inv_nonexistent"
        )

    def test_create_invoice_item_price_inactive(self):
        self.assert_error_behavior(
            func_to_call=create_invoice_item,
            expected_exception_type=InvalidRequestError,
            expected_message="Price with ID 'price_default_inactive_usd' is not active and cannot be used.",
            customer=self.customer_id_1, price=self.price_id_3_inactive_usd, invoice=self.invoice_id_1_draft_usd
        )

    def test_create_invoice_item_malformed_customer_id_empty(self):
        self.assert_error_behavior(
            func_to_call=create_invoice_item,
            expected_exception_type=InvalidRequestError,
            expected_message='Customer ID must be a non-empty string.',
            customer="", price=self.price_id_1_usd, invoice=self.invoice_id_1_draft_usd
        )

    def test_create_invoice_item_malformed_price_id_empty(self):
        self.assert_error_behavior(
            func_to_call=create_invoice_item,
            expected_exception_type=InvalidRequestError,
            expected_message='Price ID must be a non-empty string.',
            customer=self.customer_id_1, price="", invoice=self.invoice_id_1_draft_usd
        )

    def test_create_invoice_item_malformed_invoice_id_empty(self):
        self.assert_error_behavior(
            func_to_call=create_invoice_item,
            expected_exception_type=InvalidRequestError,
            expected_message='Invoice ID must be a non-empty string.',
            customer=self.customer_id_1, price=self.price_id_1_usd, invoice=""
        )

    def test_create_invoice_item_idempotency_check_not_part_of_this_function(self):
        customer_id = self.customer_id_1
        price_id = self.price_id_1_usd
        invoice_id = self.invoice_id_1_draft_usd

        result1 = create_invoice_item(customer=customer_id, price=price_id, invoice=invoice_id)
        result2 = create_invoice_item(customer=customer_id, price=price_id, invoice=invoice_id)

        self.assertNotEqual(result1['id'], result2['id'])
        self.assertIn(result1['id'], self.DB['invoice_items'])
        self.assertIn(result2['id'], self.DB['invoice_items'])

        updated_invoice = self.DB['invoices'][invoice_id]
        price_data = self.DB['prices'][price_id]
        self.assertEqual(updated_invoice['total'], price_data['unit_amount'] * 2)
        self.assertEqual(len(updated_invoice['lines']['data']), 2)


class TestFinalizeInvoice(BaseTestCaseWithErrorHandler):
    # Globally available: DB, finalize_invoice, BaseTestCaseWithErrorHandler

    # Test data constants for clarity and consistency (static class variables)
    CUSTOMER_ID = "cus_test_finalize_default"
    PRODUCT_ID = "prod_test_finalize_default"
    PRICE_ID = "price_test_finalize_default"
    # A different price ID for variety in invoice items, if needed for more complex scenarios.
    # For current tests, one price_id is sufficient for product association.
    # PRICE_ID_ALT = "price_test_finalize_alt"

    DRAFT_INVOICE_VALID_ID = "inv_final_draft_valid"
    DRAFT_INVOICE_VALID_WITH_DUE_DATE_ID = "inv_final_draft_valid_due"
    DRAFT_INVOICE_NO_LINES_ID = "inv_final_draft_no_lines"
    OPEN_INVOICE_ID = "inv_final_open"
    PAID_INVOICE_ID = "inv_final_paid"
    VOID_INVOICE_ID = "inv_final_void"
    UNCOLLECTIBLE_INVOICE_ID = "inv_final_uncollectible"

    ITEM_1_FOR_VALID_ID = "ii_final_item1_valid"
    ITEM_2_FOR_VALID_ID = "ii_final_item2_valid"
    ITEM_FOR_DUE_DATE_INVOICE_ID = "ii_final_item_due_date"

    DEFAULT_CURRENCY = "usd"
    FIXED_CREATED_TIMESTAMP = 1678880000
    FIXED_DUE_DATE_TIMESTAMP = 1679880000

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['customers'] = {
            self.CUSTOMER_ID: {
                "id": self.CUSTOMER_ID, "object": "customer", "name": "Test Customer Finalize",
                "email": "test_finalize@example.com", "created": self.FIXED_CREATED_TIMESTAMP, "livemode": False,
                "metadata": None,
            }
        }
        DB['products'] = {
            self.PRODUCT_ID: {
                "id": self.PRODUCT_ID, "object": "product", "name": "Test Product Finalize", "active": True,
                "description": "A product for testing invoice finalization.",
                "created": self.FIXED_CREATED_TIMESTAMP, "updated": self.FIXED_CREATED_TIMESTAMP, "livemode": False,
                "metadata": None,
            }
        }
        DB['prices'] = {
            self.PRICE_ID: {
                "id": self.PRICE_ID, "object": "price", "active": True, "product": self.PRODUCT_ID,
                "unit_amount": 1000, "currency": self.DEFAULT_CURRENCY, "type": "one_time",
                "recurring": None, "livemode": False, "metadata": None, "billing_scheme": "per_unit",
                "created": self.FIXED_CREATED_TIMESTAMP, "custom_unit_amount": None, "lookup_key": None,
                "nickname": None, "tax_behavior": None, "tiers": None, "tiers_mode": None,
                "transform_quantity": None, "unit_amount_decimal": None,
            }
        }

        # Create invoice items using pydantic models for validation
        invoice_item_1 = InvoiceItem(
            id=self.ITEM_1_FOR_VALID_ID,
            customer=self.CUSTOMER_ID,
            invoice=self.DRAFT_INVOICE_VALID_ID,
            price=InvoiceItemPrice(
                id=self.PRICE_ID,
                product=self.PRODUCT_ID,
                unit_amount=1000,
                currency=self.DEFAULT_CURRENCY
            ),
            amount=1000,
            currency=self.DEFAULT_CURRENCY,
            quantity=1
        )

        invoice_item_2 = InvoiceItem(
            id=self.ITEM_2_FOR_VALID_ID,
            customer=self.CUSTOMER_ID,
            invoice=self.DRAFT_INVOICE_VALID_ID,
            price=InvoiceItemPrice(
                id=self.PRICE_ID,
                product=self.PRODUCT_ID,
                unit_amount=500,
                currency=self.DEFAULT_CURRENCY
            ),
            amount=500,
            currency=self.DEFAULT_CURRENCY,
            quantity=1
        )

        invoice_item_due_date = InvoiceItem(
            id=self.ITEM_FOR_DUE_DATE_INVOICE_ID,
            customer=self.CUSTOMER_ID,
            invoice=self.DRAFT_INVOICE_VALID_WITH_DUE_DATE_ID,
            price=InvoiceItemPrice(
                id=self.PRICE_ID,
                product=self.PRODUCT_ID,
                unit_amount=2000,
                currency=self.DEFAULT_CURRENCY
            ),
            amount=2000,
            currency=self.DEFAULT_CURRENCY,
            quantity=2
        )

        DB['invoice_items'] = {
            self.ITEM_1_FOR_VALID_ID: invoice_item_1.model_dump(),
            self.ITEM_2_FOR_VALID_ID: invoice_item_2.model_dump(),
            self.ITEM_FOR_DUE_DATE_INVOICE_ID: invoice_item_due_date.model_dump(),
        }

        # Create invoices using pydantic models
        draft_invoice_valid = Invoice(
            id=self.DRAFT_INVOICE_VALID_ID,
            customer=self.CUSTOMER_ID,
            status="draft",
            total=0,
            amount_due=0,
            currency=self.DEFAULT_CURRENCY,
            created=self.FIXED_CREATED_TIMESTAMP,
            due_date=None
        )

        draft_invoice_with_due_date = Invoice(
            id=self.DRAFT_INVOICE_VALID_WITH_DUE_DATE_ID,
            customer=self.CUSTOMER_ID,
            status="draft",
            total=0,
            amount_due=0,
            currency=self.DEFAULT_CURRENCY,
            created=self.FIXED_CREATED_TIMESTAMP,
            due_date=self.FIXED_DUE_DATE_TIMESTAMP
        )

        draft_invoice_no_lines = Invoice(
            id=self.DRAFT_INVOICE_NO_LINES_ID,
            customer=self.CUSTOMER_ID,
            status="draft",
            total=0,
            amount_due=0,
            currency=self.DEFAULT_CURRENCY,
            created=self.FIXED_CREATED_TIMESTAMP,
            due_date=None
        )

        DB['invoices'] = {
            self.DRAFT_INVOICE_VALID_ID: draft_invoice_valid.model_dump(),
            self.DRAFT_INVOICE_VALID_WITH_DUE_DATE_ID: draft_invoice_with_due_date.model_dump(),
            self.DRAFT_INVOICE_NO_LINES_ID: draft_invoice_no_lines.model_dump(),
            self.OPEN_INVOICE_ID: self._create_stub_invoice(self.OPEN_INVOICE_ID, "open", 100, 100),
            self.PAID_INVOICE_ID: self._create_stub_invoice(self.PAID_INVOICE_ID, "paid", 100, 0),
            self.VOID_INVOICE_ID: self._create_stub_invoice(self.VOID_INVOICE_ID, "void", 100, 0),
            self.UNCOLLECTIBLE_INVOICE_ID: self._create_stub_invoice(self.UNCOLLECTIBLE_INVOICE_ID, "uncollectible",
                                                                     100, 100),
        }

    def _create_stub_invoice(self, inv_id: str, status: str, total: int, amount_due: int) -> dict:
        # Helper to create minimal invoice structures for non-draft states using pydantic models
        invoice = Invoice(
            id=inv_id,
            customer=self.CUSTOMER_ID,
            status=status,
            total=total,
            amount_due=amount_due,
            currency=self.DEFAULT_CURRENCY,
            created=self.FIXED_CREATED_TIMESTAMP,
            due_date=None,
            lines=InvoiceLines(
                data=[
                    InvoiceLineItem(
                        id="il_stub_" + inv_id,
                        amount=total,
                        description="Stub line item",
                        price=InvoiceLineItemPrice(
                            id=self.PRICE_ID,
                            product=self.PRODUCT_ID
                        ),
                        quantity=1
                    )
                ]
            )
        )
        return invoice.model_dump()

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_finalize_draft_invoice_success(self):
        result = finalize_invoice(invoice=self.DRAFT_INVOICE_VALID_ID)

        # Validate result using pydantic model
        invoice_result = Invoice(**result)

        self.assertEqual(invoice_result.id, self.DRAFT_INVOICE_VALID_ID)
        self.assertEqual(invoice_result.object, "invoice")
        self.assertEqual(invoice_result.status, "open")
        self.assertEqual(invoice_result.customer, self.CUSTOMER_ID)
        self.assertEqual(invoice_result.currency, self.DEFAULT_CURRENCY)
        self.assertIsNone(invoice_result.due_date)
        self.assertEqual(invoice_result.livemode, False)

        expected_total = (DB['invoice_items'][self.ITEM_1_FOR_VALID_ID]['amount'] +
                          DB['invoice_items'][self.ITEM_2_FOR_VALID_ID]['amount'])
        self.assertEqual(invoice_result.total, expected_total)
        self.assertEqual(invoice_result.amount_due, expected_total)

        self.assertEqual(invoice_result.lines.object, "list")
        self.assertEqual(len(invoice_result.lines.data), 2)
        self.assertFalse(invoice_result.lines.has_more)

        line_item_ids_in_result = {item.id for item in invoice_result.lines.data}
        self.assertIn(self.ITEM_1_FOR_VALID_ID, line_item_ids_in_result)
        self.assertIn(self.ITEM_2_FOR_VALID_ID, line_item_ids_in_result)

        for line_item_data in invoice_result.lines.data:
            original_ii = DB['invoice_items'][line_item_data.id]
            self.assertEqual(line_item_data.amount, original_ii['amount'])
            self.assertEqual(line_item_data.quantity, original_ii['quantity'])
            self.assertIsNotNone(line_item_data.description)  # Description is auto-generated
            self.assertEqual(line_item_data.price.id, original_ii['price']['id'])
            self.assertEqual(line_item_data.price.product, original_ii['price']['product'])

        # Validate updated invoice in DB
        updated_invoice_in_db = Invoice(**DB['invoices'][self.DRAFT_INVOICE_VALID_ID])
        self.assertEqual(updated_invoice_in_db.status, "open")
        self.assertEqual(updated_invoice_in_db.total, expected_total)
        self.assertEqual(updated_invoice_in_db.amount_due, expected_total)
        self.assertEqual(len(updated_invoice_in_db.lines.data), 2)

    def test_finalize_draft_invoice_with_due_date_success(self):
        result = finalize_invoice(invoice=self.DRAFT_INVOICE_VALID_WITH_DUE_DATE_ID)

        # Validate result using pydantic model
        invoice_result = Invoice(**result)

        self.assertEqual(invoice_result.id, self.DRAFT_INVOICE_VALID_WITH_DUE_DATE_ID)
        self.assertEqual(invoice_result.status, "open")
        self.assertEqual(invoice_result.due_date, self.FIXED_DUE_DATE_TIMESTAMP)

        expected_total = DB['invoice_items'][self.ITEM_FOR_DUE_DATE_INVOICE_ID]['amount']
        self.assertEqual(invoice_result.total, expected_total)
        self.assertEqual(invoice_result.amount_due, expected_total)
        self.assertEqual(len(invoice_result.lines.data), 1)
        self.assertEqual(invoice_result.lines.data[0].id, self.ITEM_FOR_DUE_DATE_INVOICE_ID)

        # Validate updated invoice in DB
        updated_invoice_in_db = Invoice(**DB['invoices'][self.DRAFT_INVOICE_VALID_WITH_DUE_DATE_ID])
        self.assertEqual(updated_invoice_in_db.status, "open")
        self.assertEqual(updated_invoice_in_db.due_date, self.FIXED_DUE_DATE_TIMESTAMP)

    def test_finalize_non_existent_invoice(self):
        non_existent_id = "inv_does_not_exist"
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.ResourceNotFoundError,
            expected_message=f"invoice {non_existent_id} does not exist",
            invoice=non_existent_id
        )

    def test_finalize_already_open_invoice(self):
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice must be in draft status to be finalized",
            invoice=self.OPEN_INVOICE_ID
        )
        self.assertEqual(DB['invoices'][self.OPEN_INVOICE_ID]['status'], "open")  # Status unchanged

    def test_finalize_already_paid_invoice(self):
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice must be in draft status to be finalized",
            invoice=self.PAID_INVOICE_ID
        )
        self.assertEqual(DB['invoices'][self.PAID_INVOICE_ID]['status'], "paid")

    def test_finalize_void_invoice(self):
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice must be in draft status to be finalized",
            invoice=self.VOID_INVOICE_ID
        )
        self.assertEqual(DB['invoices'][self.VOID_INVOICE_ID]['status'], "void")

    def test_finalize_uncollectible_invoice(self):
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice must be in draft status to be finalized",
            invoice=self.UNCOLLECTIBLE_INVOICE_ID
        )
        self.assertEqual(DB['invoices'][self.UNCOLLECTIBLE_INVOICE_ID]['status'], "uncollectible")

    def test_finalize_draft_invoice_with_no_line_items(self):
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice cannot be finalized without line items",
            invoice=self.DRAFT_INVOICE_NO_LINES_ID
        )
        self.assertEqual(DB['invoices'][self.DRAFT_INVOICE_NO_LINES_ID]['status'], "draft")
        self.assertEqual(DB['invoices'][self.DRAFT_INVOICE_NO_LINES_ID]['total'],
                         0)  # Should remain 0 after failed attempt
        self.assertEqual(len(DB['invoices'][self.DRAFT_INVOICE_NO_LINES_ID]['lines']['data']), 0)

    def test_finalize_invoice_invalid_id_type_integer(self):
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice must be a string and not empty",
            invoice=123
        )

    def test_finalize_invoice_invalid_id_type_none(self):
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice must be a string and not empty",
            invoice=None
        )

    def test_finalize_invoice_empty_id_string(self):
        # Assuming empty string is an invalid ID format caught by input validation.
        # If it were to pass initial validation, it might result in ResourceNotFoundError
        # or InvalidRequestError depending on deeper logic.
        self.assert_error_behavior(
            func_to_call=finalize_invoice,
            expected_exception_type=custom_errors.InvalidRequestError,
            expected_message="invoice must be a string and not empty",
            invoice=""
        )
