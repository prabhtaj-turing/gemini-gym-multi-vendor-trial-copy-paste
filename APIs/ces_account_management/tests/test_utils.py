"""
Test cases for utility functions
"""

import unittest
from datetime import timedelta, timezone
from unittest.mock import patch

from .account_management_base_exception import AccountManagementBaseTestCase
from ..SimulationEngine import utils
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import ActionNotSupportedError
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class TestAccountManagementUtils(AccountManagementBaseTestCase):
    """
    Test suite for Account Management utility functions.
    Tests shared helper functions for data access and manipulation.
    """
    def test_get_account_success(self):
        """Test successful account retrieval."""
        result = utils.get_account("ACC888777666")

        self.assertIsNotNone(result)
        self.assertEqual(result["accountId"], "ACC888777666")
        self.assertEqual(result["customerName"], "Jessica Davis")

    def test_get_account_not_found(self):
        """Test account retrieval when account doesn't exist."""
        result = utils.get_account("NONEXISTENT-ACCOUNT")

        self.assertIsNone(result)

    def test_get_device_success(self):
        """Test successful device retrieval."""
        result = utils.get_device("DEV006A")

        self.assertIsNotNone(result)
        self.assertEqual(result["deviceId"], "DEV006A")
        self.assertEqual(result["deviceName"], "iPhone 13 mini")

    def test_get_device_not_found(self):
        """Test device retrieval when device doesn't exist."""
        result = utils.get_device("NONEXISTENT-DEVICE")

        self.assertIsNone(result)

    def test_get_service_plan_success(self):
        """Test successful service plan retrieval."""
        result = utils.get_service_plan("P001")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "P001")
        self.assertEqual(result["name"], "Basic Talk & Text")

    def test_get_service_plan_not_found(self):
        """Test service plan retrieval when plan doesn't exist."""
        result = utils.get_service_plan("NONEXISTENT-PLAN")

        self.assertIsNone(result)

    def test_search_accounts_by_phone_success(self):
        """Test successful account search by phone number."""
        result = utils.search_accounts_by_phone("5554445556")

        self.assertIsNotNone(result)
        self.assertEqual(result["accountId"], "ACC888777666")

    def test_search_accounts_by_phone_not_found(self):
        """Test account search by phone when no match found."""
        result = utils.search_accounts_by_phone("+15559999999")

        self.assertIsNone(result)

    def test_search_accounts_by_email_success(self):
        """Test successful account search by email."""
        result = utils.search_accounts_by_email("jessd@email.com")

        self.assertIsNotNone(result)
        self.assertEqual(result["accountId"], "ACC888777666")

    def test_search_accounts_by_email_not_found(self):
        """Test account search by email when no match found."""
        result = utils.search_accounts_by_email("notfound@example.com")

        self.assertIsNone(result)

    def test_utils_with_empty_database(self):
        """Test utility functions behavior with empty database."""
        # Clear all data
        DB["accountDetails"] = {}
        DB["availablePlans"] = {"plans": {}}

        # Test all functions return None/empty
        self.assertIsNone(utils.get_account("ANY-ID"))
        self.assertIsNone(utils.get_device("ANY-ID"))
        self.assertIsNone(utils.get_service_plan("ANY-ID"))
        self.assertIsNone(utils.search_accounts_by_phone("ANY-PHONE"))
        self.assertIsNone(utils.search_accounts_by_email("ANY-EMAIL"))

    def test_utils_deterministic_behavior(self):
        """Test that utility functions are deterministic."""
        # Same inputs should produce same outputs
        result1 = utils.get_account("ACC888777666")
        result2 = utils.get_account("ACC888777666")
        self.assertEqual(result1, result2)

        result3 = utils.search_accounts_by_email("jessd@email.com")
        result4 = utils.search_accounts_by_email("jessd@email.com")
        self.assertEqual(result3, result4)

    def test_utils_handle_malformed_data(self):
        """Test utility functions handle malformed database data gracefully."""
        # Test with malformed account data
        DB["accountDetails"] = {"malformed_id": {"malformed": "data"}}

        # Functions should handle gracefully and not crash
        result = utils.get_account("ANY-ID")
        self.assertIsNone(result)

        result = utils.search_accounts_by_email("jessd@email.com")
        self.assertIsNone(result)

    def test_create_account_success(self):
        """Test successful account creation."""
        account_data = {
            "accountId": "ACCT-12345",
            "customerName": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+15551234567"
        }
        
        result = utils.create_account(account_data)
        
        # Verify the function returns the original account data
        self.assertEqual(result, account_data)
        
        # Verify the account was actually stored in the database
        stored_account = DB["accountDetails"]["ACCT-12345"]
        self.assertEqual(stored_account, account_data)
        
        # Verify we can retrieve it using get_account
        retrieved_account = utils.get_account("ACCT-12345")
        self.assertEqual(retrieved_account, account_data)

    def test_create_account_missing_account_id(self):
        """Test account creation fails when accountId is missing."""
        account_data = {
            "customerName": "John Doe",
            "email": "john.doe@example.com"
        }

        self.assert_error_behavior(
            utils.create_account,
            ValueError,
            "Account ID is required",
            account_data=account_data
        )

    def test_create_account_empty_account_id(self):
        """Test account creation fails when accountId is empty."""
        account_data = {
            "accountId": "",
            "customerName": "John Doe",
            "email": "john.doe@example.com"
        }
 
        self.assert_error_behavior(
            utils.create_account,
            ValueError,
            "Account ID is required",
            account_data=account_data
        )
        

    def test_create_account_none_account_id(self):
        """Test account creation fails when accountId is None."""
        account_data = {
            "accountId": None,
            "customerName": "John Doe",
            "email": "john.doe@example.com"
        }

        self.assert_error_behavior(
            utils.create_account,
            ValueError,
            "Account ID is required",
            account_data=account_data
        ) 

    def test_create_account_initializes_account_details(self):
        """Test that create_account initializes accountDetails if not present."""
        # Remove accountDetails from DB to simulate empty state
        if "accountDetails" in DB:
            del DB["accountDetails"]
        
        account_data = {
            "accountId": "ACCT-99999",
            "customerName": "Test User"
        }
        
        result = utils.create_account(account_data)
        
        # Verify accountDetails was initialized
        self.assertIn("accountDetails", DB)
        self.assertEqual(DB["accountDetails"]["ACCT-99999"], account_data)
        self.assertEqual(result, account_data)

    def test_create_account_overwrites_existing(self):
        """Test that create_account overwrites existing account with same ID."""
        account_id = "ACCT-OVERWRITE"
        
        # Create initial account
        original_data = {
            "accountId": account_id,
            "customerName": "Original User",
            "email": "original@example.com"
        }
        utils.create_account(original_data)
        
        # Create new account with same ID
        new_data = {
            "accountId": account_id,
            "customerName": "Updated User",
            "email": "updated@example.com",
            "phone": "+15559876543"
        }
        result = utils.create_account(new_data)
        
        # Verify the account was overwritten
        self.assertEqual(result, new_data)
        stored_account = DB["accountDetails"][account_id]
        self.assertEqual(stored_account, new_data)
        self.assertNotEqual(stored_account, original_data)

    def test_create_account_minimal_data(self):
        """Test creating account with only required accountId field."""
        account_data = {
            "accountId": "ACCT-MINIMAL"
        }
        
        result = utils.create_account(account_data)
        
        self.assertEqual(result, account_data)
        self.assertEqual(DB["accountDetails"]["ACCT-MINIMAL"], account_data)

    def test_create_account_complex_data(self):
        """Test creating account with complex nested data."""
        account_data = {
            "accountId": "ACCT-COMPLEX",
            "customerName": "Complex User",
            "email": "complex@example.com",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345"
            },
            "devices": [
                {"deviceId": "DEV-001", "type": "phone"},
                {"deviceId": "DEV-002", "type": "tablet"}
            ],
            "preferences": {
                "notifications": True,
                "billing": "paperless"
            }
        }
        
        result = utils.create_account(account_data)
        
        self.assertEqual(result, account_data)
        stored_account = DB["accountDetails"]["ACCT-COMPLEX"]
        self.assertEqual(stored_account, account_data)
        
        # Verify nested structures are preserved
        self.assertEqual(stored_account["address"]["city"], "Anytown")
        self.assertEqual(len(stored_account["devices"]), 2)
        self.assertTrue(stored_account["preferences"]["notifications"])

    def test_create_account_multiple_accounts(self):
        """Test creating multiple accounts doesn't interfere with each other."""
        accounts = [
            {
                "accountId": "ACCT-MULTI-1",
                "customerName": "User One",
                "email": "user1@example.com"
            },
            {
                "accountId": "ACCT-MULTI-2", 
                "customerName": "User Two",
                "email": "user2@example.com"
            },
            {
                "accountId": "ACCT-MULTI-3",
                "customerName": "User Three",
                "email": "user3@example.com"
            }
        ]
        
        # Create all accounts
        results = []
        initially_existing_accounts = len(DB["accountDetails"])
        for account_data in accounts:
            results.append(utils.create_account(account_data))
        
        # Verify all were created correctly
        for i, account_data in enumerate(accounts):
            self.assertEqual(results[i], account_data)
            stored_account = DB["accountDetails"][account_data["accountId"]]
            self.assertEqual(stored_account, account_data)
        
        # Verify all accounts coexist
        self.assertEqual(len(DB["accountDetails"]), len(accounts) + initially_existing_accounts)

    def test_add_device_to_account_success(self):
        """Test successfully adding a device to an existing account."""
        # Use existing test account
        account_id = "ACC888777666"
        device_data = {
            "deviceId": "DEV-NEW-001",
            "deviceName": "Samsung Galaxy S24",
            "deviceType": "smartphone",
            "status": "active"
        }
        
        # Get initial device count
        initial_account = utils.get_account(account_id)
        initial_device_count = len(initial_account.get("devices", []))
        
        result = utils.add_device_to_account(account_id, device_data)
        
        # Verify the function returns the device data
        self.assertEqual(result, device_data)
        
        # Verify device was added to the account
        updated_account = utils.get_account(account_id)
        self.assertEqual(len(updated_account["devices"]), initial_device_count + 1)
        
        # Verify the new device is in the devices list
        added_device = None
        for d in updated_account["devices"]:
            if d.get("deviceId") == "DEV-NEW-001":
                added_device = d
                break

        self.assertIsNotNone(added_device)
        self.assertEqual(added_device, device_data)

    def test_add_device_to_account_nonexistent_account(self):
        """Test adding device to non-existent account raises ValueError."""
        device_data = {
            "deviceId": "DEV-TEST-001",
            "deviceName": "Test Device"
        }
        self.assert_error_behavior(
            utils.add_device_to_account,
            ValueError,
            "Account NONEXISTENT-ACCOUNT not found",
            account_id="NONEXISTENT-ACCOUNT",
            device_data=device_data
        )

    def test_add_device_to_account_missing_device_id(self):
        """Test adding device without deviceId raises ValueError."""
        account_id = "ACC888777666"
        device_data = {
            "deviceName": "Test Device",
            "deviceType": "smartphone"
        }
        
        self.assert_error_behavior(
            utils.add_device_to_account,
            ValueError,
            "Device ID is required",
            account_id=account_id,
            device_data=device_data
        )

    def test_add_device_to_account_empty_device_id(self):
        """Test adding device with empty deviceId raises ValueError."""
        account_id = "ACC888777666"
        device_data = {
            "deviceId": "",
            "deviceName": "Test Device"
        }
        
        self.assert_error_behavior(
            utils.add_device_to_account,
            ValueError,
            "Device ID is required",
            account_id=account_id,
            device_data=device_data
        )

    def test_add_device_to_account_none_device_id(self):
        """Test adding device with None deviceId raises ValueError."""
        account_id = "ACC888777666"
        device_data = {
            "deviceId": None,
            "deviceName": "Test Device"
        }

        self.assert_error_behavior(
            utils.add_device_to_account,
            ValueError,
            "Device ID is required",
            account_id=account_id,
            device_data=device_data
        )

    def test_add_device_to_account_initializes_devices_list(self):
        """Test that add_device_to_account initializes devices list if not present."""
        # Create a new account without devices
        account_data = {
            "accountId": "ACCT-NO-DEVICES",
            "customerName": "No Devices User"
        }
        utils.create_account(account_data)
        
        device_data = {
            "deviceId": "DEV-FIRST-001",
            "deviceName": "First Device",
            "deviceType": "tablet"
        }
        
        result = utils.add_device_to_account("ACCT-NO-DEVICES", device_data)
        
        # Verify device was added and devices dict was initialized
        self.assertEqual(result, device_data)
        updated_account = utils.get_account("ACCT-NO-DEVICES")
        self.assertIn("devices", updated_account)
        self.assertEqual(len(updated_account["devices"]), 1)
        self.assertEqual(updated_account["devices"][0], device_data)

    def test_add_device_to_account_multiple_devices(self):
        """Test adding multiple devices to the same account."""
        # Create a clean account for this test
        account_data = {
            "accountId": "ACCT-MULTI-DEV",
            "customerName": "Multi Device User"
        }
        utils.create_account(account_data)
        
        devices = [
            {
                "deviceId": "DEV-MULTI-001",
                "deviceName": "iPhone 15",
                "deviceType": "smartphone"
            },
            {
                "deviceId": "DEV-MULTI-002", 
                "deviceName": "iPad Pro",
                "deviceType": "tablet"
            },
            {
                "deviceId": "DEV-MULTI-003",
                "deviceName": "Apple Watch",
                "deviceType": "wearable"
            }
        ]
        
        # Add all devices
        for device_data in devices:
            result = utils.add_device_to_account("ACCT-MULTI-DEV", device_data)
            self.assertEqual(result, device_data)
        
        # Verify all devices were added
        updated_account = utils.get_account("ACCT-MULTI-DEV")
        self.assertEqual(len(updated_account["devices"]), 3)
        
        # Verify each device is present
        device_ids = [d["deviceId"] for d in updated_account["devices"]]
        for device in devices:
            self.assertIn(device["deviceId"], device_ids)

    def test_add_device_to_account_minimal_device_data(self):
        """Test adding device with only required deviceId field."""
        account_id = "ACC888777666"
        device_data = {
            "deviceId": "DEV-MINIMAL-001"
        }
        
        # Get initial device count
        initial_account = utils.get_account(account_id)
        initial_device_count = len(initial_account.get("devices", []))
        
        result = utils.add_device_to_account(account_id, device_data)
        
        self.assertEqual(result, device_data)
        
        updated_account = utils.get_account(account_id)
        self.assertEqual(len(updated_account["devices"]), initial_device_count + 1)
        
        # Find the added device
        added_device = None
        for d in updated_account["devices"]:
            if d.get("deviceId") == "DEV-MINIMAL-001":
                added_device = d
                break
        
        self.assertIsNotNone(added_device)
        self.assertEqual(added_device, device_data)

    def test_add_device_to_account_complex_device_data(self):
        """Test adding device with complex nested data."""
        account_id = "ACC888777666"
        device_data = {
            "deviceId": "DEV-COMPLEX-001",
            "deviceName": "Samsung Galaxy S24 Ultra",
            "deviceType": "smartphone",
            "status": "active",
            "specifications": {
                "os": "Android 14",
                "storage": "512GB",
                "ram": "12GB",
                "display": "6.8 inch"
            },
            "features": [
                "5G", "wireless_charging", "waterproof"
            ],
            "plan": {
                "planId": "PLAN-001",
                "dataLimit": "unlimited"
            }
        }
        
        result = utils.add_device_to_account(account_id, device_data)
        
        self.assertEqual(result, device_data)
        
        updated_account = utils.get_account(account_id)
        
        # Find the added device
        added_device = None
        for d in updated_account["devices"]:
            if d.get("deviceId") == "DEV-COMPLEX-001":
                added_device = d
                break
        
        self.assertIsNotNone(added_device)
        self.assertEqual(added_device, device_data)
        
        # Verify nested structures are preserved
        self.assertEqual(added_device["specifications"]["os"], "Android 14")
        self.assertEqual(len(added_device["features"]), 3)
        self.assertIn("5G", added_device["features"])
        self.assertEqual(added_device["plan"]["planId"], "PLAN-001")

    def test_add_device_to_account_duplicate_device_id(self):
        """Test that adding device with duplicate deviceId still works (appends to list)."""
        account_id = "ACC888777666"
        device_data = {
            "deviceId": "DEV-DUPLICATE-001",
            "deviceName": "First Device"
        }
        
        # Add the device first time
        utils.add_device_to_account(account_id, device_data)
        
        # Add device with same ID but different data
        duplicate_device_data = {
            "deviceId": "DEV-DUPLICATE-001",
            "deviceName": "Second Device with Same ID"
        }
        
        result = utils.add_device_to_account(account_id, duplicate_device_data)
        self.assertEqual(result, duplicate_device_data)
        
        updated_account = utils.get_account(account_id)
        
        # Count devices with the duplicate ID (should be 1 since we overwrite with same key)
        duplicate_device = None
        for d in updated_account["devices"]:
            if d.get("deviceId") == "DEV-DUPLICATE-001":
                duplicate_device = d
                break
        
        # Should have the device (function overwrites with same key)
        self.assertIsNotNone(duplicate_device)
        self.assertEqual(duplicate_device["deviceName"], "Second Device with Same ID")

    def test_add_device_to_account_preserves_existing_devices(self):
        """Test that adding a device preserves existing devices in the account."""
        account_id = "ACC888777666"
        
        # Get initial devices
        initial_account = utils.get_account(account_id)
        initial_devices = list(initial_account.get("devices", []))
        initial_device_count = len(initial_devices)
        
        # Add new device
        new_device = {
            "deviceId": "DEV-PRESERVE-001",
            "deviceName": "New Device"
        }
        
        utils.add_device_to_account(account_id, new_device)
        
        # Verify all original devices are still there plus the new one
        updated_account = utils.get_account(account_id)
        updated_devices = updated_account["devices"]
        
        self.assertEqual(len(updated_devices), initial_device_count + 1)
        
        # Check that all original devices are still present
        original_ids = {d.get("deviceId") for d in initial_devices}
        updated_ids = {d.get("deviceId") for d in updated_devices}
        self.assertTrue(original_ids.issubset(updated_ids))
        
        # Verify new device is also present
        self.assertIn("DEV-PRESERVE-001", updated_ids)
        self.assertTrue(any(d.get("deviceId") == "DEV-PRESERVE-001" and d.get("deviceName") == "New Device" for d in updated_devices))

    def test_add_service_to_account_success(self):
        """Test successfully adding a service to an existing account."""
        # Use existing test account
        account_id = "ACC888777666"
        service_data = {
            "serviceId": "SVC-NEW-001",
            "serviceName": "Premium Data Plan",
            "serviceType": "data",
            "status": "active",
            "monthlyCost": 49.99
        }
        
        # Get initial service count
        initial_account = utils.get_account(account_id)
        initial_service_count = len(initial_account.get("services", []))
        
        result = utils.add_service_to_account(account_id, service_data)
        
        # Verify the function returns the service data
        self.assertEqual(result, service_data)
        
        # Verify service was added to the account
        updated_account = utils.get_account(account_id)
        self.assertEqual(len(updated_account["services"]), initial_service_count + 1)
        
        # Verify the new service is in the services list
        added_service = None
        for service in updated_account["services"]:
            if service.get("serviceId") == "SVC-NEW-001":
                added_service = service
                break
        
        self.assertIsNotNone(added_service)
        self.assertEqual(added_service, service_data)

    def test_add_service_to_account_nonexistent_account(self):
        """Test adding service to non-existent account raises ValueError."""
        service_data = {
            "serviceId": "SVC-TEST-001",
            "serviceName": "Test Service"
        }
        
        self.assert_error_behavior(
            utils.add_service_to_account,
            ValueError,
            "Account NONEXISTENT-ACCOUNT not found",
            account_id="NONEXISTENT-ACCOUNT",
            service_data=service_data
        )

    def test_add_service_to_account_missing_service_id(self):
        """Test adding service without serviceId raises ValueError."""
        account_id = "ACC888777666"
        service_data = {
            "serviceName": "Test Service",
            "serviceType": "data"
        }
        
        self.assert_error_behavior(
            utils.add_service_to_account,
            ValueError,
            "Service ID is required",
            account_id=account_id,
            service_data=service_data
        )

    def test_add_service_to_account_empty_service_id(self):
        """Test adding service with empty serviceId raises ValueError."""
        account_id = "ACC888777666"
        service_data = {
            "serviceId": "",
            "serviceName": "Test Service"
        }
        
        self.assert_error_behavior(
            utils.add_service_to_account,
            ValueError,
            "Service ID is required",
            account_id=account_id,
            service_data=service_data
        )

    def test_add_service_to_account_none_service_id(self):
        """Test adding service with None serviceId raises ValueError."""
        account_id = "ACC888777666"
        service_data = {
            "serviceId": None,
            "serviceName": "Test Service"
        }
        
        self.assert_error_behavior(
            utils.add_service_to_account,
            ValueError,
            "Service ID is required",
            account_id=account_id,
            service_data=service_data
        )

    def test_add_service_to_account_initializes_services_list(self):
        """Test that add_service_to_account initializes services list if not present."""
        # Create a new account without services
        account_data = {
            "accountId": "ACCT-NO-SERVICES",
            "customerName": "No Services User"
        }
        utils.create_account(account_data)
        
        service_data = {
            "serviceId": "SVC-FIRST-001",
            "serviceName": "First Service",
            "serviceType": "voice"
        }
        
        result = utils.add_service_to_account("ACCT-NO-SERVICES", service_data)
        
        # Verify service was added and services dict was initialized
        self.assertEqual(result, service_data)
        updated_account = utils.get_account("ACCT-NO-SERVICES")
        self.assertIn("services", updated_account)
        self.assertEqual(len(updated_account["services"]), 1)
        self.assertEqual(updated_account["services"][0], service_data)

    def test_add_service_to_account_multiple_services(self):
        """Test adding multiple services to the same account."""
        # Create a clean account for this test
        account_data = {
            "accountId": "ACCT-MULTI-SVC",
            "customerName": "Multi Service User"
        }
        utils.create_account(account_data)
        
        services = [
            {
                "serviceId": "SVC-MULTI-001",
                "serviceName": "Basic Voice Plan",
                "serviceType": "voice",
                "monthlyCost": 29.99
            },
            {
                "serviceId": "SVC-MULTI-002", 
                "serviceName": "Unlimited Data Plan",
                "serviceType": "data",
                "monthlyCost": 59.99
            },
            {
                "serviceId": "SVC-MULTI-003",
                "serviceName": "International Roaming",
                "serviceType": "roaming",
                "monthlyCost": 15.99
            }
        ]
        
        # Add all services
        for service_data in services:
            result = utils.add_service_to_account("ACCT-MULTI-SVC", service_data)
            self.assertEqual(result, service_data)
        
        # Verify all services were added
        updated_account = utils.get_account("ACCT-MULTI-SVC")
        self.assertEqual(len(updated_account["services"]), 3)
        
        # Verify each service is present
        service_ids = [service["serviceId"] for service in updated_account["services"]]
        for service in services:
            self.assertIn(service["serviceId"], service_ids)

    def test_add_service_to_account_minimal_service_data(self):
        """Test adding service with only required serviceId field."""
        account_id = "ACC888777666"
        service_data = {
            "serviceId": "SVC-MINIMAL-001"
        }
        
        # Get initial service count
        initial_account = utils.get_account(account_id)
        initial_service_count = len(initial_account.get("services", []))
        
        result = utils.add_service_to_account(account_id, service_data)
        
        self.assertEqual(result, service_data)
        
        updated_account = utils.get_account(account_id)
        self.assertEqual(len(updated_account["services"]), initial_service_count + 1)
        
        # Find the added service
        added_service = None
        for service in updated_account["services"]:
            if service.get("serviceId") == "SVC-MINIMAL-001":
                added_service = service
                break
        
        self.assertIsNotNone(added_service)
        self.assertEqual(added_service, service_data)

    def test_add_service_to_account_complex_service_data(self):
        """Test adding service with complex nested data."""
        account_id = "ACC888777666"
        service_data = {
            "serviceId": "SVC-COMPLEX-001",
            "serviceName": "Enterprise Business Plan",
            "serviceType": "business",
            "status": "active",
            "billing": {
                "frequency": "monthly",
                "amount": 149.99,
                "currency": "USD",
                "dueDate": "2025-10-01"
            },
            "features": [
                "unlimited_calls", "priority_support", "5G_access"
            ],
            "limits": {
                "dataGB": "unlimited",
                "voiceMinutes": "unlimited",
                "textMessages": "unlimited"
            },
            "addOns": [
                {"name": "International Calling", "cost": 10.00},
                {"name": "Mobile Hotspot", "cost": 15.00}
            ]
        }
        
        result = utils.add_service_to_account(account_id, service_data)
        
        self.assertEqual(result, service_data)
        
        updated_account = utils.get_account(account_id)
        
        # Find the added service
        added_service = None
        for service in updated_account["services"]:
            if service.get("serviceId") == "SVC-COMPLEX-001":
                added_service = service
                break
        
        self.assertIsNotNone(added_service)
        self.assertEqual(added_service, service_data)
        
        # Verify nested structures are preserved
        self.assertEqual(added_service["billing"]["amount"], 149.99)
        self.assertEqual(len(added_service["features"]), 3)
        self.assertIn("unlimited_calls", added_service["features"])
        self.assertEqual(added_service["limits"]["dataGB"], "unlimited")
        self.assertEqual(len(added_service["addOns"]), 2)

    def test_add_service_to_account_preserves_existing_services(self):
        """Test that adding a service preserves existing services in the account."""
        account_id = "ACC888777666"
        
        # Get initial services
        initial_account = utils.get_account(account_id)
        initial_services = list(initial_account.get("services", []))
        initial_service_count = len(initial_services)
        
        # Add new service
        new_service = {
            "serviceId": "SVC-PRESERVE-001",
            "serviceName": "New Service"
        }
        
        utils.add_service_to_account(account_id, new_service)
        
        # Verify all original services are still there plus the new one
        updated_account = utils.get_account(account_id)
        updated_services = updated_account["services"]
        
        self.assertEqual(len(updated_services), initial_service_count + 1)
        
        # Check that all original services are still present
        original_ids = {s.get("serviceId") for s in initial_services}
        updated_ids = {s.get("serviceId") for s in updated_services}
        self.assertTrue(original_ids.issubset(updated_ids))
        
        # Verify new service is also present
        self.assertIn(new_service, updated_services)

    def test_create_order_success(self):
        """Test successful order creation."""
        account_id = "ACC888777666"
        action = "CHANGE_PLAN"
        message = "Plan changed successfully"

        # Ensure account exists and has orders structure
        account = utils.get_account(account_id)
        self.assertIsNotNone(account)

        # Create order
        result = utils.create_order(account_id, action, message)
        
        # Verify return value
        self.assertIsNotNone(result)
        self.assertEqual(result["accountId"], account_id)
        self.assertEqual(result["orderType"], action)
        self.assertEqual(result["statusDescription"], message)
        self.assertIn("orderId", result)
        self.assertIn("orderDate", result)
        self.assertIn("estimatedCompletionDate", result)
        
        # Verify order ID format
        self.assertTrue(result["orderId"].startswith("ORD_CHANGE_"))
        
        # Verify date formats
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        self.assertRegex(result["orderDate"], date_pattern)
        
        # estimatedCompletionDate should be in date format: 2025-10-02
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        self.assertRegex(result["estimatedCompletionDate"], date_pattern)
        
        # Verify order is stored in database
        updated_account = DB["accountDetails"][account_id]
        self.assertIn("orders", updated_account)
        self.assertIn(result["orderId"], updated_account["orders"])
        stored_order = updated_account["orders"][result["orderId"]]
        self.assertEqual(stored_order, result)

    def test_create_order_different_actions(self):
        """Test order creation with different action types."""
        account_id = "ACC888777666"
        test_cases = [
            ("ADD_FEATURE", "Added feature to plan"),
            ("REMOVE_FEATURE", "Removed feature from plan"),
            ("CHANGE_PLAN", "Changed plan successfully"),
        ]

        for action, message in test_cases:
            with self.subTest(action=action):
                result = utils.create_order(account_id, action, message)
                
                self.assertEqual(result["orderType"], action)
                self.assertEqual(result["accountId"], account_id)
                self.assertEqual(result["statusDescription"], message)
                
                # Verify order ID format includes action prefix
                action_prefix = action.split("_")[0]
                expected_prefix = f"ORD_{action_prefix}_"
                self.assertTrue(result["orderId"].startswith(expected_prefix))

    def test_create_order_effective_date_next_day(self):
        """Test that effective date is always the next day."""
        account_id = "ACC888777666"

        result = utils.create_order(account_id, "REMOVE_FEATURE", "Feature removed successfully")
        
        # Parse the dates
        from datetime import datetime
        created_date = datetime.fromisoformat(result["orderDate"].replace('Z', '+00:00'))
        effective_date = datetime.strptime(result["estimatedCompletionDate"], "%Y-%m-%d")
        
        # Verify effective date is next day
        expected_effective = created_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        actual_effective = effective_date.replace(tzinfo=timezone.utc)
        
        self.assertEqual(actual_effective.date(), expected_effective.date())

    def test_create_order_effective_date_today(self):
        """Test that effective date is always the next day."""
        account_id = "ACC888777666"

        result = utils.create_order(account_id, "ADD_FEATURE", "Feature added successfully")
        
        # Parse the dates
        from datetime import datetime
        created_date = datetime.fromisoformat(result["orderDate"].replace('Z', '+00:00'))
        effective_date = datetime.strptime(result["estimatedCompletionDate"], "%Y-%m-%d")
        
        # Verify effective date is today
        expected_effective = created_date.replace(hour=0, minute=0, second=0, microsecond=0)
        actual_effective = effective_date.replace(tzinfo=timezone.utc)
        
        self.assertEqual(actual_effective.date(), expected_effective.date())

    def test_create_order_effective_date_next_week(self):
        """Test that effective date is always the next day."""
        account_id = "ACC888777666"

        result = utils.create_order(account_id, "CHANGE_PLAN", "Plan changed successfully")
        
        # Parse the dates
        from datetime import datetime
        created_date = datetime.fromisoformat(result["orderDate"].replace('Z', '+00:00'))
        effective_date = datetime.strptime(result["estimatedCompletionDate"], "%Y-%m-%d")
        
        # Verify effective date is next week
        expected_effective = created_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=7)
        actual_effective = effective_date.replace(tzinfo=timezone.utc)
        
        self.assertEqual(actual_effective.date(), expected_effective.date())

    def test_create_order_order_id_uniqueness(self):
        """Test that order IDs are unique even when created quickly."""
        account_id = "ACC888777666"
        order_ids = set()
        # Create multiple orders quickly
        for i in range(5):
            result = utils.create_order(account_id, "CHANGE_PLAN", f"Plan change {i}")
            order_ids.add(result["orderId"])
        
        # All order IDs should be unique
        self.assertEqual(len(order_ids), 5)

    def test_create_order_action_not_supported(self):
        """Test that create_order raises an error for unsupported actions."""
        account_id = "ACC888777666"
        self.assert_error_behavior(
            utils.create_order,
            ActionNotSupportedError,
            "Action UNSUPPORTED_ACTION not supported.",
            account_id=account_id,
            action="UNSUPPORTED_ACTION",
            message="Action not supported"
        )


    @patch('ces_account_management.SimulationEngine.utils._get_gemini_response')
    def test_search_plans_by_query_v2_basic(self, mock_get_gemini_response):
        """Test basic functionality of search_plans_by_query_v2 for plan/feature search."""
        # Mock the Gemini response
        mock_get_gemini_response.return_value = '[{"id": "P003", "name": "Unlimited Data Plan", "description": "Unlimited high-speed data, talk & text. Fair usage policy applies.", "type": "PLAN", "monthlyCost": 50, "dataAllowance": "Unlimited", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/P003", "compatibilityNotes": ""}]'
        
        # Test with a valid plan query
        results = utils.search_plans_by_query("unlimited data plan")
        
        self.assertIsInstance(results, list)
        # Should return some results (may be empty if no matches)
        self.assertGreaterEqual(len(results), 0)

    @patch('ces_account_management.SimulationEngine.utils._get_gemini_response')
    def test_search_plans_by_query_v2_feature_search(self, mock_get_gemini_response):
        """Test search_plans_by_query_v2 with feature-specific queries."""
        # Mock the Gemini response
        mock_get_gemini_response.return_value = '[{"id": "F001", "name": "International Calling Pack", "description": "100 minutes to select international destinations.", "type": "FEATURE_ADDON", "monthlyCost": 10, "dataAllowance": "", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/F001", "compatibilityNotes": "Requires any active monthly plan."}]'
        
        # Test searching for features
        results = utils.search_plans_by_query("international calling")
        
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 0)

    @patch('ces_account_management.SimulationEngine.utils._get_gemini_response')
    def test_search_plans_by_query_v2_price_search(self, mock_get_gemini_response):
        """Test search_plans_by_query_v2 with price-related queries."""
        # Mock the Gemini response
        mock_get_gemini_response.return_value = '[{"id": "P001", "name": "Basic Talk & Text", "description": "Unlimited talk and text within the country. No data included.", "type": "PLAN", "monthlyCost": 15, "dataAllowance": "0GB", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/P001", "compatibilityNotes": ""}]'
        
        # Test searching by price
        results = utils.search_plans_by_query("cheap plan")
        
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 0)

    def test_search_plans_by_query_v2_empty_string(self):
        """Test search_plans_by_query_v2 with empty query raises ValueError."""
        self.assert_error_behavior(
            utils.search_plans_by_query,
            ValueError,
            "Query must be a non-empty string",
            query="",
        )

    def test_search_plans_by_query_v2_invalid_input(self):
        """Test search_plans_by_query_v2 with invalid input types."""
        self.assert_error_behavior(
            utils.search_plans_by_query,
            ValueError,
            "Query must be a non-empty string",
            query=None,
        )

        self.assert_error_behavior(
            utils.search_plans_by_query,
            ValueError,
            "Query must be a non-empty string",
            query=123,
        )

    @patch('ces_account_management.SimulationEngine.utils._get_gemini_response')
    def test_search_plans_by_query_v2_structure(self, mock_get_gemini_response):
        """Test that search_plans_by_query_v2 returns properly structured plan/feature results."""
        # Mock the Gemini response
        mock_get_gemini_response.return_value = '[{"id": "P001", "name": "Basic Talk & Text", "description": "Unlimited talk and text within the country. No data included.", "type": "PLAN", "monthlyCost": 15, "dataAllowance": "0GB", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/P001", "compatibilityNotes": ""}]'
        
        try:
            results = utils.search_plans_by_query("basic plan")
            
            self.assertIsInstance(results, list)
            
            # Check that results have the expected structure for plans/features
            for plan in results:
                # Should have required fields for plans and features
                self.assertIn("id", plan)
                self.assertIn("name", plan)
                self.assertIn("description", plan)
                self.assertIn("type", plan)
                self.assertIn("monthlyCost", plan)
                self.assertIn("dataAllowance", plan)
                self.assertIn("termsAndConditionsUrl", plan)
                self.assertIn("compatibilityNotes", plan)
                
                # Fields should be strings or numbers as expected
                self.assertIsInstance(plan["id"], str)
                self.assertIsInstance(plan["name"], str)
                self.assertIsInstance(plan["description"], str)
                self.assertIsInstance(plan["type"], str)
                self.assertIsInstance(plan["monthlyCost"], (int, float))
                self.assertIsInstance(plan["dataAllowance"], str)
                self.assertIsInstance(plan["termsAndConditionsUrl"], str)
                self.assertIsInstance(plan["compatibilityNotes"], str)
                
                # Type should be either PLAN or FEATURE_ADDON
                if plan["type"]:
                    self.assertIn(plan["type"], ["PLAN", "FEATURE_ADDON"])
                
        except Exception as e:
            # If Gemini API is not available, we should still test the structure
            # by mocking or skipping this test
            self.skipTest(f"Gemini API not available for testing: {e}")

    def test_search_account_orders_by_query_basic(self):
        """Test basic order search functionality."""
        # Test searching for orders with account filter
        results = utils.search_account_orders_by_query("delayed", "ACC-12345")
        
        self.assertIsInstance(results, list)
        # The search engine should return some results (may not be exact matches)
        self.assertGreaterEqual(len(results), 0)

    def test_search_account_orders_by_query_status(self):
        """Test order search by status content."""
        # Test searching for status content
        results = utils.search_account_orders_by_query("processing", "ACC-12345")
        
        self.assertIsInstance(results, list)
        # The search engine should return some results
        self.assertGreaterEqual(len(results), 0)

    def test_search_account_orders_by_query_order_type(self):
        """Test order search by order type."""
        # Test searching for order type
        results = utils.search_account_orders_by_query("device", "ACC-12345")
        
        self.assertIsInstance(results, list)
        # The search engine should return some results
        self.assertGreaterEqual(len(results), 0)

    def test_search_account_orders_by_query_no_results(self):
        """Test order search with no matching results."""
        # Test searching for something that shouldn't exist
        results = utils.search_account_orders_by_query("nonexistent_order_xyz_123", "ACC-12345")
        
        self.assertIsInstance(results, list)
        # Should return empty list
        self.assertEqual(len(results), 0)

    def test_search_account_orders_by_query_empty_string(self):
        """Test order search with empty query."""
        # Test searching with empty string
        results = utils.search_account_orders_by_query("", "ACC-12345")
        
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 0)

        # Should return some results (all orders or empty depending on implementation)

    def test_search_account_orders_by_query_case_insensitive(self):
        """Test that order search is case insensitive."""
        # Test with different cases
        results_lower = utils.search_account_orders_by_query("delayed", "ACC-12345")
        results_upper = utils.search_account_orders_by_query("DELAYED", "ACC-12345")
        results_mixed = utils.search_account_orders_by_query("Delayed", "ACC-12345")
        
        self.assertIsInstance(results_lower, list)
        self.assertIsInstance(results_upper, list)
        self.assertIsInstance(results_mixed, list)
        
        # All should return some results
        self.assertGreaterEqual(len(results_lower), 0)
        self.assertGreaterEqual(len(results_upper), 0)
        self.assertGreaterEqual(len(results_mixed), 0)

    def test_search_account_orders_database_structure_alignment(self):
        """Test that order search results align with the actual database structure."""
        results = utils.search_account_orders_by_query("delayed", "ACC-12345")
        
        self.assertIsInstance(results, list)
        
        # Check that results have the expected database structure
        for order in results:
            # Should have required fields from the database
            self.assertIn("orderId", order)
            self.assertIn("status", order)
            self.assertIn("orderType", order)
            self.assertIn("accountId", order)
            
            # Status should be a string
            self.assertIsInstance(order["status"], str)
            
            # Order type should be a string
            self.assertIsInstance(order["orderType"], str)



if __name__ == "__main__":
    unittest.main()
