import unittest
from stripe.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestImports(BaseTestCaseWithErrorHandler):

    def test_imports_stripe_models_success(self):
        try:
            from APIs.stripe import SimulationEngine
            self.assertEqual(True, True)
        except ImportError:
            self.fail("Failed to import stripe models")

    def test_imports_stripe_utils_success(self):
        try:
            from APIs.stripe.SimulationEngine import utils
            self.assertEqual(True, True)
        except ImportError:
            self.fail("Failed to import stripe utils")
    
    def test_imports_stripe_db_success(self):
        try:
            from APIs.stripe.SimulationEngine.db import DB
            self.assertEqual(True, True)
        except ImportError:
            self.fail("Failed to import stripe db")

    def test_imports_common_utils_success(self):
        try:
            from common_utils.base_case import BaseTestCaseWithErrorHandler
            self.assertEqual(True, True)
        except ImportError:
            self.fail("Failed to import common utils")

    def test_imports_stripe_models_success(self):
        try:
            from APIs.stripe.SimulationEngine.models import Customer, Product, StripeDB, Price, PaymentLink, Invoice, InvoiceItem, Balance, Refund, PaymentIntent, Subscription, Coupon, Dispute
            from APIs.stripe.SimulationEngine.models import ListSubscriptionsResponseItem, ListSubscriptionsResponse, UpdateSubscriptionItem, generate_id, get_current_timestamp
            self.assertEqual(True, True)
        except ImportError:
            self.fail("Failed to import stripe models")

    def test_imports_stripe_utils_success(self):
        try:
            from APIs.stripe.SimulationEngine.utils import _recalculate_invoice_totals, _update_subscription_items_and_status, _get_object_by_id, _get_objects, get_customer_by_email, get_prices_for_product, get_active_subscriptions_for_customer, create_customer_in_db, create_product_in_db, create_price_in_db, create_subscription_item_for_db, create_subscription_in_db, add_product_to_db, add_dispute_to_db
            from APIs.stripe.SimulationEngine.utils import dispute_status_is_updatable, subscription_status_is_cancelable
            from APIs.stripe.SimulationEngine.utils import _construct_response_discount_dict, _construct_response_price_dict
            self.assertEqual(True, True)
        except ImportError:
            self.fail("Failed to import stripe utils")

    def test_imports_stripe_customer_is_callable_success(self):
        try:
            from APIs.stripe.customer import create_customer, list_customers
            self.assertEqual(callable(create_customer), True)
            self.assertEqual(callable(list_customers), True)

        except ImportError:
            self.fail("Failed to import stripe customer")

    def test_imports_stripe_product_is_callable_success(self):
        try:
            from APIs.stripe.product import create_product, list_products
            self.assertEqual(callable(create_product), True)
            self.assertEqual(callable(list_products), True)

        except ImportError:
            self.fail("Failed to import stripe product")

    def test_imports_stripe_subscription_is_callable_success(self):
        try:
            from APIs.stripe.subscription import list_subscriptions, cancel_subscription, update_subscription
            self.assertEqual(callable(list_subscriptions), True)
            self.assertEqual(callable(cancel_subscription), True)
            self.assertEqual(callable(update_subscription), True)

        except ImportError:
            self.fail("Failed to import stripe subscription")

    def test_imports_stripe_price_is_callable_success(self):
        try:
            from APIs.stripe.price import create_price, list_prices
            self.assertEqual(callable(create_price), True)
            self.assertEqual(callable(list_prices), True)

        except ImportError:
            self.fail("Failed to import stripe price")

    def test_imports_stripe_coupon_is_callable_success(self):
        try:
            from APIs.stripe.coupon import create_coupon, list_coupons
            self.assertEqual(callable(create_coupon), True)
            self.assertEqual(callable(list_coupons), True)

        except ImportError:
            self.fail("Failed to import stripe coupon")

    def test_imports_stripe_dispute_is_callable_success(self):
        try:
            from APIs.stripe.dispute import update_dispute, list_disputes
            self.assertEqual(callable(update_dispute), True)
            self.assertEqual(callable(list_disputes), True)

        except ImportError:
            self.fail("Failed to import stripe dispute")

    def test_imports_stripe_refund_is_callable_success(self):
        try:
            from APIs.stripe.refund import create_refund
            self.assertEqual(callable(create_refund), True)

        except ImportError:
            self.fail("Failed to import stripe refund")

    def test_imports_stripe_invoice_is_callable_success(self):
        try:
            from APIs.stripe.invoice import create_invoice
            self.assertEqual(callable(create_invoice), True)

        except ImportError:
            self.fail("Failed to import stripe invoice")

    def test_imports_stripe_balance_is_callable_success(self):
        try:
            from APIs.stripe.balance import retrieve_balance
            self.assertEqual(callable(retrieve_balance), True)

        except ImportError:
            self.fail("Failed to import stripe balance")

    def test_simulation_engine_imports(self):
        """
        Test that the simulation engine can be imported successfully.
        """
        try:
            from APIs.stripe.SimulationEngine import models
            from APIs.stripe.SimulationEngine import db
            from APIs.stripe.SimulationEngine import custom_errors
            from APIs.stripe.SimulationEngine import utils
        except ImportError as e:
            self.fail(f"Failed to import simulation engine: {e}")

    def test_simulation_engine_functions_callable(self):
        """
        Test that the simulation engine functions are callable.
        """
        from APIs.stripe.SimulationEngine import models
        from APIs.stripe.SimulationEngine import db
        from APIs.stripe.SimulationEngine import custom_errors
        from APIs.stripe.SimulationEngine import utils


        # test that the models are classes
        self.assertTrue(isinstance(models.Customer, type))
        self.assertTrue(isinstance(models.Product, type))
        self.assertTrue(isinstance(models.Price, type))
        self.assertTrue(isinstance(models.PaymentLink, type))
        self.assertTrue(isinstance(models.Invoice, type))
        self.assertTrue(isinstance(models.InvoiceItem, type))
        self.assertTrue(isinstance(models.Balance, type))
        self.assertTrue(isinstance(models.Refund, type))
        self.assertTrue(isinstance(models.PaymentIntent, type))
        self.assertTrue(isinstance(models.Subscription, type))
        self.assertTrue(isinstance(models.Coupon, type))
        self.assertTrue(isinstance(models.Dispute, type))
        self.assertTrue(callable(models.generate_id))
        self.assertTrue(callable(models.get_current_timestamp))

        # test that the functions are callable
        self.assertTrue(callable(utils._get_object_by_id))
        self.assertTrue(callable(utils._get_objects))
        self.assertTrue(callable(utils.get_customer_by_email))
        self.assertTrue(callable(utils.get_prices_for_product))
        self.assertTrue(callable(utils.get_active_subscriptions_for_customer))
        self.assertTrue(callable(utils.create_customer_in_db))
        self.assertTrue(callable(utils.create_product_in_db))
        self.assertTrue(callable(utils.create_price_in_db))
        self.assertTrue(callable(utils.create_subscription_item_for_db))
        self.assertTrue(callable(utils.create_subscription_in_db))
        self.assertTrue(callable(utils.add_product_to_db))
        self.assertTrue(callable(utils.add_dispute_to_db))
        self.assertTrue(callable(utils.dispute_status_is_updatable))
        self.assertTrue(callable(utils.subscription_status_is_cancelable))
        self.assertTrue(callable(utils._construct_response_discount_dict))
        self.assertTrue(callable(utils._construct_response_price_dict))

        # test usability of the simulation engine
        self.assertTrue(type(DB) == dict)
        self.assertTrue(hasattr(utils, '_get_object_by_id'))
        self.assertTrue(hasattr(utils, '_get_objects'))
        self.assertTrue(hasattr(utils, 'get_customer_by_email'))
        self.assertTrue(hasattr(utils, 'get_prices_for_product'))
        self.assertTrue(hasattr(utils, 'get_active_subscriptions_for_customer'))
        self.assertTrue(hasattr(utils, 'create_customer_in_db'))
        self.assertTrue(hasattr(utils, 'create_product_in_db'))
        self.assertTrue(hasattr(utils, 'create_price_in_db'))
        self.assertTrue(hasattr(utils, 'create_subscription_item_for_db'))
        self.assertTrue(hasattr(utils, 'create_subscription_in_db'))
        self.assertTrue(hasattr(utils, 'add_product_to_db'))
        self.assertTrue(hasattr(utils, 'add_dispute_to_db'))
        self.assertTrue(hasattr(utils, 'dispute_status_is_updatable'))
        self.assertTrue(hasattr(utils, 'subscription_status_is_cancelable'))
        self.assertTrue(hasattr(utils, '_construct_response_discount_dict'))
        self.assertTrue(hasattr(utils, '_construct_response_price_dict'))

if __name__ == '__main__':
    unittest.main()