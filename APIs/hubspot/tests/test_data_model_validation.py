import unittest
import pytest
from hubspot.SimulationEngine.db import DB
from hubspot.SimulationEngine.utils import generate_hubspot_object_id
import json


class TestHubspotDataModelValidation(unittest.TestCase):
    """Test data model validation for Hubspot entities."""
    
    def setUp(self):
        """Set up test environment with sample data."""
        self.sample_data = {
            "marketing_emails": {
                "email_1": {
                    "name": "Test Marketing Email",
                    "subject": "Test Subject",
                    "email_id": "email_1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            },
            "transactional_emails": {
                "tx_1": {
                    "to": "test@example.com",
                    "from": "sender@example.com",
                    "subject": "Test Transactional",
                    "htmlBody": "<p>Test content</p>",
                    "email_id": "tx_1",
                    "sent_at": "2024-01-01T00:00:00Z"
                }
            },
            "campaigns": {
                "camp_1": {
                    "name": "Test Campaign",
                    "type": "email",
                    "campaign_id": "camp_1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "status": "active"
                }
            },
            "forms": {
                "form_1": {
                    "name": "Test Form",
                    "form_id": "form_1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            },
            "templates": {
                "template_1": {
                    "name": "Test Template",
                    "template_id": "template_1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            },
            "marketing_events": {
                "event_1": {
                    "name": "Test Event",
                    "event_id": "event_1",
                    "start_date": "2024-01-01T00:00:00Z",
                    "end_date": "2024-01-01T23:59:59Z",
                    "status": "scheduled"
                }
            },
            "form_global_events": {
                "subscription_1": {
                    "subscription_id": "sub_1",
                    "event_type": "form_submission",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            }
        }
        
        # Clear and initialize DB
        DB.clear()
        DB.update(self.sample_data)
    
    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
    
    def test_marketing_emails_structure_validation(self):
        """Test that marketing emails have valid structure."""
        emails = DB.get("marketing_emails", {})
        
        for email_id, email in emails.items():
            # Test required fields exist
            self.assertIn("name", email, f"Marketing email {email_id} missing 'name' field")
            self.assertIn("subject", email, f"Marketing email {email_id} missing 'subject' field")
            self.assertIn("email_id", email, f"Marketing email {email_id} missing 'email_id' field")
            
            # Test field types
            self.assertIsInstance(email["name"], str, f"Marketing email {email_id} name must be string")
            self.assertIsInstance(email["subject"], str, f"Marketing email {email_id} subject must be string")
            self.assertIsInstance(email["email_id"], str, f"Marketing email {email_id} email_id must be string")
            
            # Test field values
            self.assertTrue(email["name"].strip(), f"Marketing email {email_id} name cannot be empty")
            self.assertTrue(email["subject"].strip(), f"Marketing email {email_id} subject cannot be empty")
    
    def test_transactional_emails_structure_validation(self):
        """Test that transactional emails have valid structure."""
        emails = DB.get("transactional_emails", {})
        
        for email_id, email in emails.items():
            # Test required fields exist
            self.assertIn("to", email, f"Transactional email {email_id} missing 'to' field")
            self.assertIn("from", email, f"Transactional email {email_id} missing 'from' field")
            self.assertIn("subject", email, f"Transactional email {email_id} missing 'subject' field")
            self.assertIn("htmlBody", email, f"Transactional email {email_id} missing 'htmlBody' field")
            
            # Test field types
            self.assertIsInstance(email["to"], str, f"Transactional email {email_id} 'to' must be string")
            self.assertIsInstance(email["from"], str, f"Transactional email {email_id} 'from' must be string")
            self.assertIsInstance(email["subject"], str, f"Transactional email {email_id} subject must be string")
            self.assertIsInstance(email["htmlBody"], str, f"Transactional email {email_id} htmlBody must be string")
            
            # Test field values
            self.assertTrue(email["to"].strip(), f"Transactional email {email_id} 'to' cannot be empty")
            self.assertTrue(email["from"].strip(), f"Transactional email {email_id} 'from' cannot be empty")
            self.assertTrue(email["subject"].strip(), f"Transactional email {email_id} subject cannot be empty")
            self.assertTrue(email["htmlBody"].strip(), f"Transactional email {email_id} htmlBody cannot be empty")
    
    def test_campaigns_structure_validation(self):
        """Test that campaigns have valid structure."""
        campaigns = DB.get("campaigns", {})
        
        for campaign_id, campaign in campaigns.items():
            # Test required fields exist
            self.assertIn("name", campaign, f"Campaign {campaign_id} missing 'name' field")
            self.assertIn("type", campaign, f"Campaign {campaign_id} missing 'type' field")
            self.assertIn("campaign_id", campaign, f"Campaign {campaign_id} missing 'campaign_id' field")
            
            # Test field types
            self.assertIsInstance(campaign["name"], str, f"Campaign {campaign_id} name must be string")
            self.assertIsInstance(campaign["type"], str, f"Campaign {campaign_id} type must be string")
            self.assertIsInstance(campaign["campaign_id"], str, f"Campaign {campaign_id} campaign_id must be string")
            
            # Test field values
            self.assertTrue(campaign["name"].strip(), f"Campaign {campaign_id} name cannot be empty")
            self.assertTrue(campaign["type"].strip(), f"Campaign {campaign_id} type cannot be empty")
    
    def test_forms_structure_validation(self):
        """Test that forms have valid structure."""
        forms = DB.get("forms", {})
        
        for form_id, form in forms.items():
            # Test required fields exist
            self.assertIn("name", form, f"Form {form_id} missing 'name' field")
            self.assertIn("form_id", form, f"Form {form_id} missing 'form_id' field")
            
            # Test field types
            self.assertIsInstance(form["name"], str, f"Form {form_id} name must be string")
            self.assertIsInstance(form["form_id"], str, f"Form {form_id} form_id must be string")
            
            # Test field values
            self.assertTrue(form["name"].strip(), f"Form {form_id} name cannot be empty")
    
    def test_templates_structure_validation(self):
        """Test that templates have valid structure."""
        templates = DB.get("templates", {})
        
        for template_id, template in templates.items():
            # Test required fields exist
            self.assertIn("name", template, f"Template {template_id} missing 'name' field")
            self.assertIn("template_id", template, f"Template {template_id} missing 'template_id' field")
            
            # Test field types
            self.assertIsInstance(template["name"], str, f"Template {template_id} name must be string")
            self.assertIsInstance(template["template_id"], str, f"Template {template_id} template_id must be string")
            
            # Test field values
            self.assertTrue(template["name"].strip(), f"Template {template_id} name cannot be empty")
    
    def test_marketing_events_structure_validation(self):
        """Test that marketing events have valid structure."""
        events = DB.get("marketing_events", {})
        
        for event_id, event in events.items():
            # Test required fields exist
            self.assertIn("name", event, f"Marketing event {event_id} missing 'name' field")
            self.assertIn("event_id", event, f"Marketing event {event_id} missing 'event_id' field")
            self.assertIn("start_date", event, f"Marketing event {event_id} missing 'start_date' field")
            self.assertIn("end_date", event, f"Marketing event {event_id} missing 'end_date' field")
            
            # Test field types
            self.assertIsInstance(event["name"], str, f"Marketing event {event_id} name must be string")
            self.assertIsInstance(event["event_id"], str, f"Marketing event {event_id} event_id must be string")
            self.assertIsInstance(event["start_date"], str, f"Marketing event {event_id} start_date must be string")
            self.assertIsInstance(event["end_date"], str, f"Marketing event {event_id} end_date must be string")
            
            # Test field values
            self.assertTrue(event["name"].strip(), f"Marketing event {event_id} name cannot be empty")
    
    def test_form_global_events_structure_validation(self):
        """Test that form global events have valid structure."""
        subscriptions = DB.get("form_global_events", {})
        
        for sub_id, subscription in subscriptions.items():
            # Test required fields exist
            self.assertIn("subscription_id", subscription, f"Subscription {sub_id} missing 'subscription_id' field")
            self.assertIn("event_type", subscription, f"Subscription {sub_id} missing 'event_type' field")
            
            # Test field types
            self.assertIsInstance(subscription["subscription_id"], str, f"Subscription {sub_id} subscription_id must be string")
            self.assertIsInstance(subscription["event_type"], str, f"Subscription {sub_id} event_type must be string")
            
            # Test field values
            self.assertTrue(subscription["subscription_id"].strip(), f"Subscription {sub_id} subscription_id cannot be empty")
            self.assertTrue(subscription["event_type"].strip(), f"Subscription {sub_id} event_type cannot be empty")
    
    def test_database_schema_consistency(self):
        """Test that the database schema is consistent across all entities."""
        # Test that all expected top-level keys exist
        expected_keys = {
            "marketing_emails", "transactional_emails", "campaigns", 
            "forms", "templates", "marketing_events", "form_global_events"
        }
        
        actual_keys = set(DB.keys())
        missing_keys = expected_keys - actual_keys
        unexpected_keys = actual_keys - expected_keys
        
        self.assertEqual(missing_keys, set(), f"Missing expected database keys: {missing_keys}")
        self.assertEqual(unexpected_keys, set(), f"Unexpected database keys: {unexpected_keys}")
    
    def test_entity_id_format_validation(self):
        """Test that entity IDs follow proper format."""
        # Test marketing email IDs
        emails = DB.get("marketing_emails", {})
        for email_id in emails.keys():
            self.assertIsInstance(email_id, str, f"Marketing email ID {email_id} must be string")
            self.assertTrue(email_id.strip(), f"Marketing email ID {email_id} cannot be empty")
        
        # Test transactional email IDs
        tx_emails = DB.get("transactional_emails", {})
        for tx_id in tx_emails.keys():
            self.assertIsInstance(tx_id, str, f"Transactional email ID {tx_id} must be string")
            self.assertTrue(tx_id.strip(), f"Transactional email ID {tx_id} cannot be empty")
        
        # Test campaign IDs
        campaigns = DB.get("campaigns", {})
        for camp_id in campaigns.keys():
            self.assertIsInstance(camp_id, str, f"Campaign ID {camp_id} must be string")
            self.assertTrue(camp_id.strip(), f"Campaign ID {camp_id} cannot be empty")
    
    def test_data_integrity_validation(self):
        """Test that data integrity is maintained across the database."""
        # Test that all entities have consistent ID references
        emails = DB.get("marketing_emails", {})
        for email_id, email in emails.items():
            # Email ID in data should match the key
            self.assertEqual(email["email_id"], email_id, 
                           f"Marketing email ID mismatch: key={email_id}, data={email['email_id']}")
        
        campaigns = DB.get("campaigns", {})
        for campaign_id, campaign in campaigns.items():
            # Campaign ID in data should match the key
            self.assertEqual(campaign["campaign_id"], campaign_id,
                           f"Campaign ID mismatch: key={campaign_id}, data={campaign['campaign_id']}")
    
    def test_required_field_validation(self):
        """Test that all required fields are present and valid."""
        # Test marketing emails
        emails = DB.get("marketing_emails", {})
        for email_id, email in emails.items():
            required_fields = ["name", "subject", "email_id"]
            for field in required_fields:
                self.assertIn(field, email, f"Marketing email {email_id} missing required field: {field}")
                self.assertIsNotNone(email[field], f"Marketing email {email_id} field {field} cannot be None")
        
        # Test transactional emails
        tx_emails = DB.get("transactional_emails", {})
        for tx_id, tx_email in tx_emails.items():
            required_fields = ["to", "from", "subject", "htmlBody"]
            for field in required_fields:
                self.assertIn(field, tx_email, f"Transactional email {tx_id} missing required field: {field}")
                self.assertIsNotNone(tx_email[field], f"Transactional email {tx_id} field {field} cannot be None")


if __name__ == '__main__':
    unittest.main()
