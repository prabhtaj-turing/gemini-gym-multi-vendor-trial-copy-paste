#!/usr/bin/env python3
"""
Database Model Validation Tests for Workday Strategic Sourcing API

This module provides comprehensive testing for database structure validation and 
test data validation to ensure data integrity and consistency across test cases.

Based on the patterns identified:
1. Unit Test Case has Data Model Validation
2. Test data added to DB is properly validated

Author: AI Assistant
Created: 2024-12-28
"""

import unittest
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError, validator, ConfigDict
from datetime import datetime

# Import the components under test
from ..SimulationEngine import db
from ..SimulationEngine.models import (
    # Database Structure Models
    WorkdayDBModel, AttachmentsDBModel, AwardsDBModel, ContractsDBModel,
    EventsDBModel, FieldsDBModel, PaymentsDBModel, ProjectsDBModel, 
    ReportsDBModel, SCIMDBModel, SuppliersDBModel,
    # Data Validation Models 
    UserValidationModel, AttachmentValidationModel, SupplierValidationModel,
    ContractValidationModel, EventValidationModel
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestDatabaseModelValidation(BaseTestCaseWithErrorHandler):
    """Test class for database structure and test data validation."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        db.reset_db()

    def tearDown(self):
        """Clean up after each test method."""
        super().tearDown()
        db.reset_db()

    # =========================================================================
    # Database Structure Validation Tests
    # =========================================================================

    def test_db_module_harmony(self):
        """
        Test that the database used by the db module is in harmony with the sample DB.
        This ensures that tests are running against the expected data structure.
        
        This is the equivalent of the NotificationsDB(**DB) validation pattern.
        """
        try:
            validated_db = WorkdayDBModel(**db.DB)
            self.assertIsInstance(validated_db, WorkdayDBModel)
            print("✅ Database structure validation passed")
        except ValidationError as e:
            self.fail(f"DB module data structure validation failed: {e}")
        except Exception as e:
            self.fail(f"DB module data structure validation failed: {e}")

    def test_db_attachments_structure(self):
        """Test that the attachments section has correct structure."""
        try:
            validated_attachments = AttachmentsDBModel(**db.DB['attachments'])
            self.assertIsInstance(validated_attachments, AttachmentsDBModel)
        except Exception as e:
            self.fail(f"Attachments DB structure validation failed: {e}")

    def test_db_awards_structure(self):
        """Test that the awards section has correct structure."""
        try:
            validated_awards = AwardsDBModel(**db.DB['awards'])
            self.assertIsInstance(validated_awards, AwardsDBModel)
        except Exception as e:
            self.fail(f"Awards DB structure validation failed: {e}")

    def test_db_contracts_structure(self):
        """Test that the contracts section has correct structure."""
        try:
            validated_contracts = ContractsDBModel(**db.DB['contracts'])
            self.assertIsInstance(validated_contracts, ContractsDBModel)
        except Exception as e:
            self.fail(f"Contracts DB structure validation failed: {e}")

    def test_db_events_structure(self):
        """Test that the events section has correct structure."""
        try:
            validated_events = EventsDBModel(**db.DB['events'])
            self.assertIsInstance(validated_events, EventsDBModel)
        except Exception as e:
            self.fail(f"Events DB structure validation failed: {e}")

    def test_db_scim_structure(self):
        """Test that the SCIM section has correct structure."""
        try:
            validated_scim = SCIMDBModel(**db.DB['scim'])
            self.assertIsInstance(validated_scim, SCIMDBModel)
        except Exception as e:
            self.fail(f"SCIM DB structure validation failed: {e}")

    def test_db_suppliers_structure(self):
        """Test that the suppliers section has correct structure."""
        try:
            validated_suppliers = SuppliersDBModel(**db.DB['suppliers'])
            self.assertIsInstance(validated_suppliers, SuppliersDBModel)
        except Exception as e:
            self.fail(f"Suppliers DB structure validation failed: {e}")

    def test_db_after_reset_is_valid(self):
        """Test that DB structure is valid after reset."""
        db.reset_db()
        try:
            validated_db = WorkdayDBModel(**db.DB)
            self.assertIsInstance(validated_db, WorkdayDBModel)
        except Exception as e:
            self.fail(f"DB structure invalid after reset: {e}")

    # =========================================================================
    # Test Data Validation Tests
    # =========================================================================

    def test_validated_user_test_data(self):
        """
        Test that user test data is properly validated before adding to DB.
        This addresses the issue where unverified entries like self.test_player
        are added to the DB without validation.
        """
        # Create validated test user data
        test_user_data = {
            "id": "test_user_001",
            "userName": "testuser@example.com",
            "name": {
                "givenName": "Test",
                "familyName": "User"
            },
            "active": True,
            "externalId": "EXT123",
            "roles": []
        }
        
        # Validate the test data BEFORE adding to DB
        try:
            validated_user = UserValidationModel(**test_user_data)
            self.assertIsInstance(validated_user, UserValidationModel)
            
            # Only add to DB AFTER validation
            db.DB['scim']['users'].append(validated_user.model_dump())
            
            # Verify it was added correctly
            self.assertEqual(len(db.DB['scim']['users']), 1)
            self.assertEqual(db.DB['scim']['users'][0]['userName'], "testuser@example.com")
            print("✅ User test data validation and insertion passed")
            
        except ValidationError as e:
            self.fail(f"User test data validation failed: {e}")

    def test_invalid_user_test_data_rejected(self):
        """Test that invalid user test data is properly rejected."""
        # Invalid test data (missing required fields)
        invalid_user_data = {
            "id": "test_user_002",
            "userName": "invalid-email",  # Invalid email format
            "name": {
                "givenName": "Test"
                # Missing familyName
            }
        }
        
        # Validation should fail
        with self.assertRaises(ValidationError):
            UserValidationModel(**invalid_user_data)

    def test_validated_attachment_test_data(self):
        """Test that attachment test data is properly validated."""
        test_attachment_data = {
            "id": "attachment_001",
            "name": "test_document.pdf",
            "external_id": "EXT_ATT_001"
        }
        
        try:
            validated_attachment = AttachmentValidationModel(**test_attachment_data)
            self.assertIsInstance(validated_attachment, AttachmentValidationModel)
            
            # Add to DB after validation
            db.DB['attachments']['attachment_001'] = validated_attachment.model_dump()
            
            # Verify
            self.assertIn('attachment_001', db.DB['attachments'])
            self.assertEqual(db.DB['attachments']['attachment_001']['name'], "test_document.pdf")
            print("✅ Attachment test data validation passed")
            
        except ValidationError as e:
            self.fail(f"Attachment test data validation failed: {e}")

    def test_validated_supplier_test_data(self):
        """Test that supplier test data is properly validated."""
        test_supplier_data = {
            "name": "Test Supplier Corp",
            "status": "active"
        }
        
        try:
            validated_supplier = SupplierValidationModel(**test_supplier_data)
            self.assertIsInstance(validated_supplier, SupplierValidationModel)
            
            # Add to DB after validation
            db.DB['suppliers']['supplier_companies']['supplier_001'] = validated_supplier.model_dump()
            
            # Verify
            self.assertIn('supplier_001', db.DB['suppliers']['supplier_companies'])
            self.assertEqual(db.DB['suppliers']['supplier_companies']['supplier_001']['status'], "active")
            print("✅ Supplier test data validation passed")
            
        except ValidationError as e:
            self.fail(f"Supplier test data validation failed: {e}")

    def test_invalid_supplier_status_rejected(self):
        """Test that invalid supplier status is properly rejected."""
        invalid_supplier_data = {
            "name": "Test Supplier Corp",
            "status": "invalid_status"  # Invalid status
        }
        
        with self.assertRaises(ValidationError):
            SupplierValidationModel(**invalid_supplier_data)

    def test_validated_contract_test_data(self):
        """Test that contract test data is properly validated."""
        test_contract_data = {
            "id": "contract_001",
            "status": "draft"
        }
        
        try:
            validated_contract = ContractValidationModel(**test_contract_data)
            self.assertIsInstance(validated_contract, ContractValidationModel)
            
            # Add to DB after validation
            db.DB['contracts']['contracts']['contract_001'] = validated_contract.model_dump()
            
            # Verify
            self.assertIn('contract_001', db.DB['contracts']['contracts'])
            self.assertEqual(db.DB['contracts']['contracts']['contract_001']['status'], "draft")
            print("✅ Contract test data validation passed")
            
        except ValidationError as e:
            self.fail(f"Contract test data validation failed: {e}")

    def test_validated_event_test_data(self):
        """Test that event test data is properly validated."""
        test_event_data = {
            "name": "Test Sourcing Event",
            "type": "sourcing"
        }
        
        try:
            validated_event = EventValidationModel(**test_event_data)
            self.assertIsInstance(validated_event, EventValidationModel)
            
            # Add to DB after validation
            db.DB['events']['events']['event_001'] = validated_event.model_dump()
            
            # Verify
            self.assertIn('event_001', db.DB['events']['events'])
            self.assertEqual(db.DB['events']['events']['event_001']['name'], "Test Sourcing Event")
            print("✅ Event test data validation passed")
            
        except ValidationError as e:
            self.fail(f"Event test data validation failed: {e}")

    # =========================================================================
    # Test Setup Validation Helper Methods
    # =========================================================================

    def create_validated_test_user(self, user_id: str, username: str, given_name: str, family_name: str) -> Dict[str, Any]:
        """
        Helper method to create validated test users.
        This replaces the pattern of directly adding unvalidated dictionaries to DB.
        """
        test_user_data = {
            "id": user_id,
            "userName": username,
            "name": {
                "givenName": given_name,
                "familyName": family_name
            },
            "active": True
        }
        
        validated_user = UserValidationModel(**test_user_data)
        return validated_user.model_dump()

    def create_validated_test_attachment(self, attachment_id: str, name: str, external_id: str = None) -> Dict[str, Any]:
        """
        Helper method to create validated test attachments.
        """
        test_attachment_data = {
            "id": attachment_id,
            "name": name
        }
        if external_id:
            test_attachment_data["external_id"] = external_id
            
        validated_attachment = AttachmentValidationModel(**test_attachment_data)
        return validated_attachment.model_dump()

    def create_validated_test_supplier(self, name: str, status: str = "active") -> Dict[str, Any]:
        """
        Helper method to create validated test suppliers.
        """
        test_supplier_data = {
            "name": name,
            "status": status
        }
        
        validated_supplier = SupplierValidationModel(**test_supplier_data)
        return validated_supplier.model_dump()

    def test_helper_methods_work_correctly(self):
        """Test that the helper methods create valid test data."""
        # Test user helper
        user_data = self.create_validated_test_user("001", "test@example.com", "John", "Doe")
        self.assertEqual(user_data['userName'], "test@example.com")
        
        # Test attachment helper
        attachment_data = self.create_validated_test_attachment("att001", "document.pdf", "EXT001")
        self.assertEqual(attachment_data['name'], "document.pdf")
        
        # Test supplier helper
        supplier_data = self.create_validated_test_supplier("Test Supplier Inc", "active")
        self.assertEqual(supplier_data['status'], "active")
        
        print("✅ Helper methods validation passed")

    # =========================================================================
    # Integration Tests with Real DB Operations
    # =========================================================================

    def test_db_operations_maintain_structure_validity(self):
        """Test that common DB operations maintain structure validity."""
        # Reset and validate initial state
        db.reset_db()
        validated_db_initial = WorkdayDBModel(**db.DB)
        self.assertIsInstance(validated_db_initial, WorkdayDBModel)
        
        # Add some validated test data
        validated_user = self.create_validated_test_user("u001", "user1@test.com", "User", "One")
        db.DB['scim']['users'].append(validated_user)
        
        validated_attachment = self.create_validated_test_attachment("a001", "doc1.pdf")
        db.DB['attachments']['a001'] = validated_attachment
        
        # Validate DB structure is still valid after additions
        try:
            validated_db_after = WorkdayDBModel(**db.DB)
            self.assertIsInstance(validated_db_after, WorkdayDBModel)
            print("✅ DB structure remains valid after data additions")
        except Exception as e:
            self.fail(f"DB structure became invalid after data additions: {e}")

    def test_save_load_maintains_validity(self):
        """Test that save/load operations maintain DB structure validity."""
        import tempfile
        import os
        
        # Add validated test data
        validated_user = self.create_validated_test_user("u002", "user2@test.com", "User", "Two")
        db.DB['scim']['users'].append(validated_user)
        
        # Validate before save
        validated_db_before = WorkdayDBModel(**db.DB)
        self.assertIsInstance(validated_db_before, WorkdayDBModel)
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            temp_filepath = tmp_file.name
            
        try:
            db.save_state(temp_filepath)
            db.reset_db()
            db.load_state(temp_filepath)
            
            # Validate after load
            validated_db_after = WorkdayDBModel(**db.DB)
            self.assertIsInstance(validated_db_after, WorkdayDBModel)
            print("✅ DB structure remains valid after save/load cycle")
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)


if __name__ == '__main__':
    unittest.main()
