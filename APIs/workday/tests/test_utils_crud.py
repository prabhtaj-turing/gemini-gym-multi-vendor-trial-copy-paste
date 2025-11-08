"""
Test suite for CRUD utility functions in the Workday Strategic Sourcing API Simulation.
"""

import unittest
import json
import os
import tempfile
import shutil
from typing import Dict, Any
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import db, models
from pydantic import ValidationError as PydanticValidationError


class TestWorkdayUtilsCrud(BaseTestCaseWithErrorHandler):
    
    def setUp(self):
        """Set up a clean test environment before each test."""
        # Reset database to clean state (this properly initializes all structures)
        db.reset_db()
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_state.json")

    def tearDown(self):
        """Clean up after each test."""
        # Reset database to clean state
        db.reset_db()
        
        # Clean up test files
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def validate_db_structure(self):
        """Validate the current state of the database structure."""
        try:
            models.WorkdayDBModel(**db.DB)
        except PydanticValidationError as e:
            self.fail(f"Database validation failed: {e}")

    # region Database State Management Tests
    def test_reset_db_initializes_correct_structure(self):
        """Test that reset_db initializes the correct database structure."""
        # Modify the database first
        db.DB['attachments']['test'] = 'modified'
        
        # Reset and check structure
        db.reset_db()
        
        # Verify all expected top-level keys exist
        expected_keys = {
            'attachments', 'awards', 'contracts', 'events', 'fields',
            'payments', 'projects', 'reports', 'scim', 'spend_categories', 'suppliers'
        }
        self.assertEqual(set(db.DB.keys()), expected_keys)
        
        # Verify structure is clean
        self.assertEqual(db.DB['attachments'], {})
        self.assertNotIn('test', db.DB['attachments'])
        
        # Validate with Pydantic model
        self.validate_db_structure()

    def test_reset_db_clears_all_data(self):
        """Test that reset_db clears all existing data."""
        # Add some test data to various sections
        db.DB['attachments']['test_attachment'] = {'name': 'test.pdf'}
        db.DB['projects']['projects']['test_project'] = {'name': 'Test Project'}
        db.DB['scim']['users'].append({'id': 'test_user', 'userName': 'test@example.com'})
        db.DB['suppliers']['supplier_companies']['test_company'] = {'name': 'Test Company'}
        
        # Reset database
        db.reset_db()
        
        # Verify all data is cleared
        self.assertEqual(db.DB['attachments'], {})
        self.assertEqual(db.DB['projects']['projects'], {})
        self.assertEqual(db.DB['scim']['users'], [])
        self.assertEqual(db.DB['suppliers']['supplier_companies'], {})
        
        self.validate_db_structure()

    def test_save_state_creates_file(self):
        """Test that save_state creates a JSON file with current database state."""
        # Add some test data
        db.DB['attachments']['test'] = {'name': 'test_attachment'}
        db.DB['projects']['projects']['proj1'] = {'name': 'Project 1'}
        
        # Save state
        db.save_state(self.test_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.test_file))
        
        # Verify content
        with open(self.test_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['attachments']['test']['name'], 'test_attachment')
        self.assertEqual(saved_data['projects']['projects']['proj1']['name'], 'Project 1')

    def test_save_state_overwrites_existing_file(self):
        """Test that save_state overwrites existing files."""
        # Create initial file with different content
        initial_data = {'test': 'initial'}
        with open(self.test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Add data to DB and save
        db.DB['attachments']['new_test'] = {'name': 'new_attachment'}
        db.save_state(self.test_file)
        
        # Verify file was overwritten
        with open(self.test_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertNotIn('test', saved_data)
        self.assertIn('attachments', saved_data)
        self.assertEqual(saved_data['attachments']['new_test']['name'], 'new_attachment')

    def test_load_state_from_existing_file(self):
        """Test loading state from an existing file."""
        # Create test data file
        test_data = {
            'attachments': {'loaded_test': {'name': 'loaded_attachment'}},
            'projects': {'projects': {'loaded_proj': {'name': 'Loaded Project'}}},
            'scim': {'users': [{'id': 'loaded_user', 'userName': 'loaded@example.com'}]}
        }
        
        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Reset DB first to ensure clean state
        db.reset_db()
        
        # Load state
        db.load_state(self.test_file)
        
        # Verify data was loaded
        self.assertEqual(db.DB['attachments']['loaded_test']['name'], 'loaded_attachment')
        self.assertEqual(db.DB['projects']['projects']['loaded_proj']['name'], 'Loaded Project')
        self.assertEqual(len(db.DB['scim']['users']), 1)
        self.assertEqual(db.DB['scim']['users'][0]['userName'], 'loaded@example.com')

    def test_load_state_merges_with_existing_data(self):
        """Test that load_state merges data with existing database content."""
        # Add some initial data to DB
        db.DB['attachments']['existing'] = {'name': 'existing_attachment'}
        db.DB['projects']['projects']['existing'] = {'name': 'Existing Project'}
        
        # Create file with additional data that includes both existing and new keys
        test_data = {
            'attachments': {
                'existing': {'name': 'existing_attachment'},  # Keep existing
                'loaded': {'name': 'loaded_attachment'}       # Add new
            },
            'projects': {
                'projects': {
                    'existing': {'name': 'Existing Project'},  # Keep existing  
                    'loaded': {'name': 'Loaded Project'}       # Add new
                }
            }
        }
        
        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load state
        db.load_state(self.test_file)
        
        # Verify both existing and loaded data are present
        self.assertEqual(db.DB['attachments']['existing']['name'], 'existing_attachment')
        self.assertEqual(db.DB['attachments']['loaded']['name'], 'loaded_attachment')
        self.assertEqual(db.DB['projects']['projects']['existing']['name'], 'Existing Project')
        self.assertEqual(db.DB['projects']['projects']['loaded']['name'], 'Loaded Project')

    def test_load_state_nonexistent_file(self):
        """Test loading state from a non-existent file (should not raise error)."""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.json")
        
        # Add some data to verify it remains unchanged
        db.DB['attachments']['test'] = {'name': 'test_attachment'}
        original_attachments = db.DB['attachments'].copy()
        
        # Attempt to load from non-existent file
        try:
            db.load_state(nonexistent_file)
        except Exception as e:
            self.fail(f"load_state raised an exception for non-existent file: {e}")
        
        # Verify original data is unchanged
        self.assertEqual(db.DB['attachments'], original_attachments)

    def test_load_state_invalid_json(self):
        """Test loading state from a file with invalid JSON."""
        # Create file with invalid JSON
        with open(self.test_file, 'w') as f:
            f.write("invalid json content {")
        
        # Add some data to verify it remains unchanged
        db.DB['attachments']['test'] = {'name': 'test_attachment'}
        original_attachments = db.DB['attachments'].copy()
        
        # Attempt to load invalid JSON
        try:
            db.load_state(self.test_file)
        except Exception as e:
            self.fail(f"load_state raised an exception for invalid JSON: {e}")
        
        # Verify original data is unchanged
        self.assertEqual(db.DB['attachments'], original_attachments)

    def test_load_state_empty_file(self):
        """Test loading state from an empty file."""
        # Create empty file
        with open(self.test_file, 'w') as f:
            f.write('')
        
        # Add some data to verify it remains unchanged
        db.DB['attachments']['test'] = {'name': 'test_attachment'}
        original_attachments = db.DB['attachments'].copy()
        
        # Attempt to load from empty file
        try:
            db.load_state(self.test_file)
        except Exception as e:
            self.fail(f"load_state raised an exception for empty file: {e}")
        
        # Verify original data is unchanged
        self.assertEqual(db.DB['attachments'], original_attachments)
    # endregion

    # region Database Structure Tests
    def test_initial_database_structure(self):
        """Test that the initial database structure is correctly set up."""
        db.reset_db()
        
        # Test top-level structure
        self.assertIsInstance(db.DB['attachments'], dict)
        self.assertIsInstance(db.DB['awards'], dict)
        self.assertIsInstance(db.DB['contracts'], dict)
        self.assertIsInstance(db.DB['events'], dict)
        self.assertIsInstance(db.DB['fields'], dict)
        self.assertIsInstance(db.DB['payments'], dict)
        self.assertIsInstance(db.DB['projects'], dict)
        self.assertIsInstance(db.DB['reports'], dict)
        self.assertIsInstance(db.DB['scim'], dict)
        self.assertIsInstance(db.DB['spend_categories'], dict)
        self.assertIsInstance(db.DB['suppliers'], dict)

    def test_awards_structure(self):
        """Test the awards database structure."""
        self.assertIn('award_line_items', db.DB['awards'])
        self.assertIn('awards', db.DB['awards'])
        self.assertIsInstance(db.DB['awards']['award_line_items'], list)
        self.assertIsInstance(db.DB['awards']['awards'], list)

    def test_contracts_structure(self):
        """Test the contracts database structure."""
        expected_keys = {'award_line_items', 'awards', 'contract_types', 'contracts'}
        self.assertEqual(set(db.DB['contracts'].keys()), expected_keys)
        
        self.assertIsInstance(db.DB['contracts']['award_line_items'], list)
        self.assertIsInstance(db.DB['contracts']['awards'], dict)
        self.assertIsInstance(db.DB['contracts']['contract_types'], dict)
        self.assertIsInstance(db.DB['contracts']['contracts'], dict)

    def test_events_structure(self):
        """Test the events database structure."""
        expected_keys = {'bid_line_items', 'bids', 'event_templates', 'events', 'line_items', 'worksheets'}
        self.assertEqual(set(db.DB['events'].keys()), expected_keys)
        
        for key in expected_keys:
            self.assertIsInstance(db.DB['events'][key], dict)

    def test_fields_structure(self):
        """Test the fields database structure."""
        expected_keys = {'field_groups', 'field_options', 'fields'}
        self.assertEqual(set(db.DB['fields'].keys()), expected_keys)
        
        for key in expected_keys:
            self.assertIsInstance(db.DB['fields'][key], dict)

    def test_payments_structure(self):
        """Test the payments database structure."""
        expected_keys = {
            'payment_currencies', 'payment_currency_id_counter',
            'payment_term_id_counter', 'payment_terms',
            'payment_type_id_counter', 'payment_types'
        }
        self.assertEqual(set(db.DB['payments'].keys()), expected_keys)
        
        # List fields
        list_fields = ['payment_currencies', 'payment_terms', 'payment_types']
        for field in list_fields:
            self.assertIsInstance(db.DB['payments'][field], list)
        
        # Counter fields
        counter_fields = ['payment_currency_id_counter', 'payment_term_id_counter', 'payment_type_id_counter']
        for field in counter_fields:
            self.assertIsInstance(db.DB['payments'][field], str)

    def test_projects_structure(self):
        """Test the projects database structure."""
        expected_keys = {'project_types', 'projects'}
        self.assertEqual(set(db.DB['projects'].keys()), expected_keys)
        
        for key in expected_keys:
            self.assertIsInstance(db.DB['projects'][key], dict)

    def test_scim_structure(self):
        """Test the SCIM database structure."""
        expected_keys = {'resource_types', 'schemas', 'service_provider_config', 'users'}
        self.assertEqual(set(db.DB['scim'].keys()), expected_keys)
        
        # List fields
        list_fields = ['resource_types', 'schemas', 'users']
        for field in list_fields:
            self.assertIsInstance(db.DB['scim'][field], list)
        
        # Dict fields
        self.assertIsInstance(db.DB['scim']['service_provider_config'], dict)

    def test_suppliers_structure(self):
        """Test the suppliers database structure."""
        expected_keys = {'contact_types', 'supplier_companies', 'supplier_company_segmentations', 'supplier_contacts'}
        self.assertEqual(set(db.DB['suppliers'].keys()), expected_keys)
        
        for key in expected_keys:
            self.assertIsInstance(db.DB['suppliers'][key], dict)

    def test_reports_structure_completeness(self):
        """Test that reports structure includes all expected report types."""
        reports_keys = set(db.DB['reports'].keys())
        
        # Check for all expected report entries and schemas
        expected_report_types = [
            'contract_milestone_reports',
            'contract_reports', 
            'event_reports',
            'performance_review_answer_reports',
            'performance_review_reports',
            'project_milestone_reports',
            'project_reports',
            'savings_reports',
            'supplier_reports',
            'supplier_review_reports'
        ]
        
        for report_type in expected_report_types:
            entries_key = f'{report_type}_entries'
            schema_key = f'{report_type}_schema'
            
            self.assertIn(entries_key, reports_keys)
            self.assertIn(schema_key, reports_keys)
            self.assertIsInstance(db.DB['reports'][entries_key], list)
            self.assertIsInstance(db.DB['reports'][schema_key], dict)
    # endregion

    # region Data Manipulation Tests  
    def test_database_crud_attachments(self):
        """Test CRUD operations on attachments."""
        # Create
        attachment_id = "test_attachment_123"
        attachment_data = {
            'name': 'test_document.pdf',
            'size': 1024,
            'content_type': 'application/pdf'
        }
        db.DB['attachments'][attachment_id] = attachment_data
        
        # Read
        retrieved = db.DB['attachments'][attachment_id]
        self.assertEqual(retrieved['name'], 'test_document.pdf')
        
        # Update
        db.DB['attachments'][attachment_id]['name'] = 'updated_document.pdf'
        self.assertEqual(db.DB['attachments'][attachment_id]['name'], 'updated_document.pdf')
        
        # Delete
        del db.DB['attachments'][attachment_id]
        self.assertNotIn(attachment_id, db.DB['attachments'])
        
        self.validate_db_structure()

    def test_database_crud_scim_users(self):
        """Test CRUD operations on SCIM users."""
        # Create
        user_data = {
            'id': 'test_user_123',
            'userName': 'test.user@example.com',
            'active': True,
            'name': {'givenName': 'Test', 'familyName': 'User'}
        }
        db.DB['scim']['users'].append(user_data)
        
        # Read
        self.assertEqual(len(db.DB['scim']['users']), 1)
        self.assertEqual(db.DB['scim']['users'][0]['userName'], 'test.user@example.com')
        
        # Update
        db.DB['scim']['users'][0]['active'] = False
        self.assertFalse(db.DB['scim']['users'][0]['active'])
        
        # Delete
        db.DB['scim']['users'].clear()
        self.assertEqual(len(db.DB['scim']['users']), 0)
        
        self.validate_db_structure()

    def test_database_crud_projects(self):
        """Test CRUD operations on projects."""
        # Create
        project_id = "proj_123"
        project_data = {
            'name': 'Test Project',
            'status': 'active',
            'description': 'A test project'
        }
        db.DB['projects']['projects'][project_id] = project_data
        
        # Read
        retrieved = db.DB['projects']['projects'][project_id]
        self.assertEqual(retrieved['name'], 'Test Project')
        
        # Update
        db.DB['projects']['projects'][project_id]['status'] = 'completed'
        self.assertEqual(db.DB['projects']['projects'][project_id]['status'], 'completed')
        
        # Delete
        del db.DB['projects']['projects'][project_id]
        self.assertNotIn(project_id, db.DB['projects']['projects'])
        
        self.validate_db_structure()

    def test_database_crud_suppliers(self):
        """Test CRUD operations on suppliers."""
        # Create supplier company
        company_id = "company_123"
        company_data = {
            'name': 'Test Supplier Company',
            'industry': 'Technology',
            'status': 'active'
        }
        db.DB['suppliers']['supplier_companies'][company_id] = company_data
        
        # Create supplier contact
        contact_id = "contact_123"
        contact_data = {
            'name': 'John Doe',
            'email': 'john.doe@supplier.com',
            'company_id': company_id
        }
        db.DB['suppliers']['supplier_contacts'][contact_id] = contact_data
        
        # Read
        retrieved_company = db.DB['suppliers']['supplier_companies'][company_id]
        retrieved_contact = db.DB['suppliers']['supplier_contacts'][contact_id]
        
        self.assertEqual(retrieved_company['name'], 'Test Supplier Company')
        self.assertEqual(retrieved_contact['name'], 'John Doe')
        self.assertEqual(retrieved_contact['company_id'], company_id)
        
        # Update
        db.DB['suppliers']['supplier_companies'][company_id]['status'] = 'inactive'
        db.DB['suppliers']['supplier_contacts'][contact_id]['email'] = 'new.email@supplier.com'
        
        self.assertEqual(db.DB['suppliers']['supplier_companies'][company_id]['status'], 'inactive')
        self.assertEqual(db.DB['suppliers']['supplier_contacts'][contact_id]['email'], 'new.email@supplier.com')
        
        # Delete
        del db.DB['suppliers']['supplier_companies'][company_id]
        del db.DB['suppliers']['supplier_contacts'][contact_id]
        
        self.assertNotIn(company_id, db.DB['suppliers']['supplier_companies'])
        self.assertNotIn(contact_id, db.DB['suppliers']['supplier_contacts'])
        
        self.validate_db_structure()

    def test_database_crud_events_and_bids(self):
        """Test CRUD operations on events and bids."""
        # Create event
        event_id = "event_123"
        event_data = {
            'name': 'Test Sourcing Event',
            'type': 'RFP',
            'status': 'draft'
        }
        db.DB['events']['events'][event_id] = event_data
        
        # Create bid
        bid_id = "bid_123"
        bid_data = {
            'event_id': event_id,
            'supplier_id': 'supplier_123',
            'amount': 10000,
            'currency': 'USD'
        }
        db.DB['events']['bids'][bid_id] = bid_data
        
        # Read
        retrieved_event = db.DB['events']['events'][event_id]
        retrieved_bid = db.DB['events']['bids'][bid_id]
        
        self.assertEqual(retrieved_event['name'], 'Test Sourcing Event')
        self.assertEqual(retrieved_bid['event_id'], event_id)
        self.assertEqual(retrieved_bid['amount'], 10000)
        
        # Update
        db.DB['events']['events'][event_id]['status'] = 'published'
        db.DB['events']['bids'][bid_id]['amount'] = 9500
        
        self.assertEqual(db.DB['events']['events'][event_id]['status'], 'published')
        self.assertEqual(db.DB['events']['bids'][bid_id]['amount'], 9500)
        
        # Delete
        del db.DB['events']['events'][event_id]
        del db.DB['events']['bids'][bid_id]
        
        self.assertNotIn(event_id, db.DB['events']['events'])
        self.assertNotIn(bid_id, db.DB['events']['bids'])
        
        self.validate_db_structure()
    # endregion

    # region State Persistence Integration Tests
    def test_full_state_persistence_cycle(self):
        """Test a complete save and load cycle with complex data."""
        # Reset to clean state
        db.reset_db()
        
        # Add complex test data across multiple collections
        test_data = {
            'attachments': {
                'att1': {'name': 'document1.pdf', 'size': 1024}
            },
            'scim': {
                'users': [
                    {'id': 'user1', 'userName': 'user1@example.com', 'active': True},
                    {'id': 'user2', 'userName': 'user2@example.com', 'active': False}
                ]
            },
            'projects': {
                'projects': {
                    'proj1': {'name': 'Project Alpha', 'status': 'active'},
                    'proj2': {'name': 'Project Beta', 'status': 'completed'}
                }
            },
            'suppliers': {
                'supplier_companies': {
                    'comp1': {'name': 'Supplier A', 'industry': 'Tech'}
                },
                'supplier_contacts': {
                    'cont1': {'name': 'Contact 1', 'company_id': 'comp1'}
                }
            }
        }
        
        # Populate database
        for key, value in test_data.items():
            if key == 'scim':
                db.DB[key]['users'] = value['users']
            else:
                db.DB[key].update(value)
        
        # Save state
        db.save_state(self.test_file)
        
        # Reset database
        db.reset_db()
        
        # Verify data is cleared
        self.assertEqual(len(db.DB['scim']['users']), 0)
        self.assertEqual(len(db.DB['projects']['projects']), 0)
        
        # Load state
        db.load_state(self.test_file)
        
        # Verify all data was restored correctly
        self.assertEqual(db.DB['attachments']['att1']['name'], 'document1.pdf')
        self.assertEqual(len(db.DB['scim']['users']), 2)
        self.assertEqual(db.DB['scim']['users'][0]['userName'], 'user1@example.com')
        self.assertEqual(len(db.DB['projects']['projects']), 2)
        self.assertEqual(db.DB['projects']['projects']['proj1']['name'], 'Project Alpha')
        self.assertEqual(db.DB['suppliers']['supplier_companies']['comp1']['name'], 'Supplier A')
        self.assertEqual(db.DB['suppliers']['supplier_contacts']['cont1']['company_id'], 'comp1')
        
        self.validate_db_structure()

    def test_partial_state_loading(self):
        """Test loading state with only partial data."""
        # Reset and add some initial data
        db.reset_db()
        db.DB['attachments']['existing'] = {'name': 'existing.pdf'}
        db.DB['projects']['projects']['existing_proj'] = {'name': 'Existing Project'}
        
        # Create partial state file (only some collections)
        partial_data = {
            'attachments': {
                'new_att': {'name': 'new_document.pdf'}
            },
            'suppliers': {
                'supplier_companies': {
                    'new_comp': {'name': 'New Supplier'}
                }
            }
        }
        
        with open(self.test_file, 'w') as f:
            json.dump(partial_data, f)
        
        # Load partial state
        db.load_state(self.test_file)
        
        # Verify existing data is preserved and new data is added
        self.assertIn('existing', db.DB['attachments'])
        self.assertIn('new_att', db.DB['attachments'])
        self.assertEqual(db.DB['attachments']['existing']['name'], 'existing.pdf')
        self.assertEqual(db.DB['attachments']['new_att']['name'], 'new_document.pdf')
        
        self.assertIn('existing_proj', db.DB['projects']['projects'])
        self.assertIn('new_comp', db.DB['suppliers']['supplier_companies'])
        
        self.validate_db_structure()
    # endregion


if __name__ == "__main__":
    unittest.main()
