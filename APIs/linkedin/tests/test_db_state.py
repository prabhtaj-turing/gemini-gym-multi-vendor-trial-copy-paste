"""
Comprehensive test suite for LinkedIn Database utilities.

This module tests all database utility functions in the SimulationEngine.db module,
ensuring proper state management, file I/O operations, and error handling for
database persistence operations.
"""

import json
import os
import tempfile
import unittest
import threading
import time
from unittest.mock import patch, mock_open, MagicMock
from linkedin.SimulationEngine.db import DB, save_state, load_state, get_minified_state
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestDatabaseStateManagement(BaseTestCaseWithErrorHandler):
    """Test cases for database state management operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_state.json")
        
        # Store original DB state to restore after tests
        self.original_db = DB.copy()
        
        # Standard test state structure
        self.standard_state = {
            "people": {
                "1": {
                    "id": "1",
                    "firstName": "Alice",
                    "lastName": "Johnson",
                    "emailAddress": "alice@linkedin.com",
                    "headline": "Senior Software Engineer",
                    "location": {"country": "USA", "postalCode": "94105"}
                },
                "2": {
                    "id": "2", 
                    "firstName": "Bob",
                    "lastName": "Smith",
                    "emailAddress": "bob@linkedin.com",
                    "headline": "Product Manager"
                }
            },
            "organizations": {
                "1": {
                    "id": "1",
                    "name": "LinkedIn Corporation",
                    "vanityName": "linkedin",
                    "description": "Professional networking platform",
                    "website": "https://linkedin.com"
                },
                "2": {
                    "id": "2",
                    "name": "Microsoft",
                    "vanityName": "microsoft", 
                    "description": "Technology company"
                }
            },
            "organizationAcls": {
                "1": {
                    "id": "1",
                    "organization": "urn:li:organization:1",
                    "roleAssignee": "urn:li:person:1",
                    "role": "ADMINISTRATOR"
                },
                "2": {
                    "id": "2",
                    "organization": "urn:li:organization:2", 
                    "roleAssignee": "urn:li:person:2",
                    "role": "MANAGER"
                }
            },
            "posts": {
                "1": {
                    "id": "1",
                    "author": "urn:li:person:1",
                    "commentary": "Excited to share our latest product updates!",
                    "visibility": "PUBLIC"
                },
                "2": {
                    "id": "2",
                    "author": "urn:li:organization:1",
                    "commentary": "Join us for our upcoming tech conference.",
                    "visibility": "PUBLIC"
                }
            },
            "next_person_id": 3,
            "next_org_id": 3,
            "next_acl_id": 3,
            "next_post_id": 3,
            "current_person_id": "1"
        }

    def tearDown(self):
        """Clean up test fixtures and restore DB state."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db)

    def test_database_initialization_structure(self):
        """Test that database initializes with proper structure."""
        # Reset to empty state
        DB.clear()
        
        # Verify empty state
        self.assertEqual(len(DB), 0)
        self.assertIsInstance(DB, dict)
        
        # Initialize with standard structure
        DB.update(self.standard_state)
        
        # Verify all required collections exist
        required_collections = [
            "people", "organizations", "organizationAcls", "posts"
        ]
        for collection in required_collections:
            self.assertIn(collection, DB)
            self.assertIsInstance(DB[collection], dict)
        
        # Verify counter fields exist and are correct type
        counter_fields = [
            "next_person_id", "next_org_id", "next_acl_id", "next_post_id"
        ]
        for field in counter_fields:
            self.assertIn(field, DB)
            self.assertIsInstance(DB[field], int)
            self.assertGreaterEqual(DB[field], 0)

    def test_state_persistence_save_operations(self):
        """Test comprehensive state saving operations."""
        # Load test state
        DB.clear()
        DB.update(self.standard_state)
        
        # Test basic save operation
        save_state(self.test_file_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(self.test_file_path))
        self.assertGreater(os.path.getsize(self.test_file_path), 0)
        
        # Verify file content is valid JSON
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, self.standard_state)
        
        # Test save with different paths (create directories first)
        nested_dir = os.path.join(self.temp_dir, "nested", "deep")
        os.makedirs(nested_dir, exist_ok=True)
        nested_path = os.path.join(nested_dir, "state.json")
        save_state(nested_path)
        self.assertTrue(os.path.exists(nested_path))

    def test_state_persistence_load_operations(self):
        """Test comprehensive state loading operations."""
        # Create test file with state data
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.standard_state, f, indent=2)
        
        # Clear DB and load state
        DB.clear()
        load_state(self.test_file_path)
        
        # Verify state was loaded correctly
        self.assertEqual(DB, self.standard_state)
        
        # Verify specific data integrity
        integrity_checks = [
            (DB["people"]["1"]["firstName"], "Alice"),
            (DB["organizations"]["1"]["name"], "LinkedIn Corporation"),
            (DB["posts"]["1"]["commentary"], "Excited to share our latest product updates!"),
            (DB["current_person_id"], "1")
        ]
        for actual, expected in integrity_checks:
            self.assertEqual(actual, expected)

    def test_state_load_overwrites_existing_data(self):
        """Test that loading state completely overwrites existing data."""
        # Set initial state
        initial_state = {
            "people": {"99": {"id": "99", "name": "Initial User"}},
            "organizations": {},
            "posts": {},
            "temporary_field": "should be removed"
        }
        DB.clear()
        DB.update(initial_state)
        
        # Create different state file
        different_state = {
            "people": {"1": {"id": "1", "firstName": "New", "lastName": "User"}},
            "organizations": {"1": {"id": "1", "name": "New Org"}},
            "posts": {},
            "next_person_id": 2
        }
        
        with open(self.test_file_path, 'w') as f:
            json.dump(different_state, f)
        
        # Load new state
        load_state(self.test_file_path)
        
        # Verify complete replacement
        self.assertEqual(DB, different_state)
        self.assertNotIn("99", DB.get("people", {}))
        self.assertNotIn("temporary_field", DB)
        self.assertIn("1", DB["people"])

    def test_get_minified_state_returns_current_state(self):
        """Test that get_minified_state returns current database state."""
        # Set up test state
        DB.clear()
        DB.update(self.standard_state)
        
        # Get minified state
        result = get_minified_state()
        
        # Verify it returns current state
        state_checks = [(result, self.standard_state), (result, DB)]
        for actual, expected in state_checks:
            self.assertEqual(actual, expected)
        
        # Verify it's the actual DB reference (not a copy)
        self.assertIs(result, DB)
        
        # Modify DB and verify minified state reflects changes
        DB["test_field"] = "test_value"
        updated_result = get_minified_state()
        self.assertEqual(updated_result["test_field"], "test_value")

    def test_state_integrity_validation(self):
        """Test state integrity validation during operations."""
        # Test with valid state
        DB.clear()
        DB.update(self.standard_state)
        
        # Verify state integrity
        collection_lengths = [
            (len(DB["people"]), 2),
            (len(DB["organizations"]), 2),
            (len(DB["organizationAcls"]), 2),
            (len(DB["posts"]), 2)
        ]
        for actual, expected in collection_lengths:
            self.assertEqual(actual, expected)
        
        # Verify counter consistency
        max_person_id = max(int(pid) for pid in DB["people"].keys())
        self.assertLessEqual(max_person_id, DB["next_person_id"] - 1)
        
        max_org_id = max(int(oid) for oid in DB["organizations"].keys())
        self.assertLessEqual(max_org_id, DB["next_org_id"] - 1)

    def test_state_modifications_and_persistence(self):
        """Test state modifications followed by persistence operations."""
        # Start with standard state
        DB.clear()
        DB.update(self.standard_state)
        
        # Perform various modifications
        modifications = [
            # Add new person
            ("people", "3", {
                "id": "3",
                "firstName": "Charlie",
                "lastName": "Brown",
                "emailAddress": "charlie@example.com"
            }),
            # Add new organization
            ("organizations", "3", {
                "id": "3", 
                "name": "Example Corp",
                "vanityName": "example-corp"
            }),
            # Update existing post
            ("posts", "1", {
                "id": "1",
                "author": "urn:li:person:1",
                    "commentary": "Updated: Exciting news about our product!",
                "visibility": "PUBLIC"
            })
        ]
        
        for collection, item_id, data in modifications:
            DB[collection][item_id] = data
        
        # Update counters
        DB["next_person_id"] = 4
        DB["next_org_id"] = 4
        
        # Save modified state
        save_state(self.test_file_path)
        
        # Clear and reload
        original_state = DB.copy()
        DB.clear()
        load_state(self.test_file_path)
        
        # Verify modifications were persisted
        modification_checks = [
            (DB, original_state),
            (DB["people"]["3"]["firstName"], "Charlie"),
            (DB["organizations"]["3"]["name"], "Example Corp")
        ]
        for actual, expected in modification_checks:
            self.assertEqual(actual, expected)
        self.assertIn("Updated:", DB["posts"]["1"]["commentary"])

    def test_error_handling_invalid_file_operations(self):
        """Test error handling for invalid file operations."""
        # Test loading non-existent file
        non_existent_path = os.path.join(self.temp_dir, "does_not_exist.json")
        
        self.assert_error_behavior(
            func_to_call=lambda: load_state(non_existent_path),
            expected_exception_type=FileNotFoundError,
            expected_message=f"[Errno 2] No such file or directory: '{non_existent_path}'"
        )
        
        # Test loading corrupted JSON file
        corrupted_path = os.path.join(self.temp_dir, "corrupted.json")
        with open(corrupted_path, 'w') as f:
            f.write('{"invalid": "json" // comment breaks JSON}')
        
        self.assert_error_behavior(
            func_to_call=lambda: load_state(corrupted_path),
            expected_exception_type=json.JSONDecodeError,
            expected_message="Expecting ',' delimiter: line 1 column 20 (char 19)"
        )
        
        # Test loading empty file
        empty_path = os.path.join(self.temp_dir, "empty.json")
        with open(empty_path, 'w') as f:
            f.write('')
        
        self.assert_error_behavior(
            func_to_call=lambda: load_state(empty_path),
            expected_exception_type=json.JSONDecodeError,
            expected_message="Expecting value: line 1 column 1 (char 0)"
        )

    def test_error_handling_permission_denied(self):
        """Test error handling for permission denied scenarios."""
        # Test saving to read-only location (if possible)
        readonly_path = "/dev/null/readonly_test.json"  # This should cause an error
        
        try:
            save_state(readonly_path)
            self.fail("Expected an error when saving to invalid path")
        except (PermissionError, FileNotFoundError, OSError) as e:
            # Any of these errors are acceptable for this test scenario
            error_msg = str(e).lower()
            self.assertTrue(
                "permission denied" in error_msg or 
                "no such file or directory" in error_msg or
                "not a directory" in error_msg,
                f"Should get a meaningful error: {e}"
            )

    def test_unicode_and_special_character_handling(self):
        """Test handling of Unicode and special characters in state data."""
        unicode_state = {
            "people": {
                "1": {
                    "id": "1",
                    "firstName": "José María", 
                    "lastName": "García-López",
                    "emailAddress": "jose@español.com",
                    "headline": "Ingeniero de Software",
                    "bio": "Desarrollador con experiencia en múltiples tecnologías"
                },
                "2": {
                    "id": "2",
                    "firstName": "李",
                    "lastName": "小明",
                    "emailAddress": "xiaoming@中文.com",
                    "headline": "产品经理",
                    "bio": "专注于用户体验和产品创新"
                }
            },
            "organizations": {
                "1": {
                    "id": "1",
                    "name": "Café & Código S.A.",
                    "vanityName": "cafe-codigo",
                    "description": "Empresa de desarrollo de software"
                }
            },
            "posts": {
                "1": {
                    "id": "1", 
                    "author": "urn:li:person:1",
                    "commentary": "¡Emocionado de compartir nuestro nuevo producto!",
                    "visibility": "PUBLIC"
                }
            },
            "organizationAcls": {},
            "next_person_id": 3,
            "next_org_id": 2,
            "next_acl_id": 1,
            "next_post_id": 2,
            "current_person_id": "1"
        }
        
        # Set Unicode state
        DB.clear()
        DB.update(unicode_state)
        
        # Save and reload
        save_state(self.test_file_path)
        DB.clear()
        load_state(self.test_file_path)
        
        # Verify Unicode characters are preserved
        unicode_checks = [
            (DB["people"]["1"]["firstName"], "José María"),
            (DB["people"]["2"]["firstName"], "李")
        ]
        for actual, expected in unicode_checks:
            self.assertEqual(actual, expected)
        
        # Verify content is preserved (without emoticons)
        self.assertIn("Empresa de desarrollo", DB["organizations"]["1"]["description"])
        self.assertIn("compartir nuestro nuevo producto", DB["posts"]["1"]["commentary"])

    def test_concurrent_access_scenarios(self):
        """Test concurrent access to database state."""
        # Set initial state
        DB.clear()
        DB.update(self.standard_state)
        
        results = []
        errors = []
        
        def concurrent_save_operation(thread_id):
            """Concurrent save operation for testing."""
            try:
                # Modify state slightly for this thread
                DB[f"thread_{thread_id}_marker"] = f"thread_{thread_id}_value"
                
                # Save state
                thread_file = os.path.join(self.temp_dir, f"thread_{thread_id}.json")
                save_state(thread_file)
                
                # Verify file was created
                if os.path.exists(thread_file):
                    results.append(f"thread_{thread_id}_success")
                    
            except Exception as e:
                errors.append(f"thread_{thread_id}: {str(e)}")
        
        # Create multiple threads for concurrent access
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_save_operation, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify results
        result_checks = [
            (len(errors), 0, f"Concurrent access errors: {errors}"),
            (len(results), 5, "All threads should complete successfully")
        ]
        for actual, expected, msg in result_checks:
            self.assertEqual(actual, expected, msg)

    def test_large_state_performance(self):
        """Test performance with large state data."""
        # Create large state data
        large_state = {
            "people": {},
            "organizations": {}, 
            "organizationAcls": {},
            "posts": {},
            "next_person_id": 1001,
            "next_org_id": 101,
            "next_acl_id": 1001,
            "next_post_id": 1001,
            "current_person_id": "1"
        }
        
        # Generate large number of people
        for i in range(1, 1001):
            large_state["people"][str(i)] = {
                "id": str(i),
                "firstName": f"Person{i}",
                "lastName": f"User{i}",
                "emailAddress": f"user{i}@example.com",
                "headline": f"Professional {i}",
                "bio": f"Long biography for user {i} " * 10  # Make it longer
            }
        
        # Generate organizations
        for i in range(1, 101):
            large_state["organizations"][str(i)] = {
                "id": str(i),
                "name": f"Organization {i}",
                "vanityName": f"org-{i}",
                "description": f"Description for organization {i} " * 5
            }
        
        # Set large state
        DB.clear()
        DB.update(large_state)
        
        # Test save performance
        start_time = time.time()
        save_state(self.test_file_path)
        save_duration = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(save_duration, 10.0, "Save operation should complete within 10 seconds")
        
        # Test load performance
        DB.clear()
        start_time = time.time()
        load_state(self.test_file_path)
        load_duration = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(load_duration, 5.0, "Load operation should complete within 5 seconds")
        
        # Verify data integrity after performance test
        performance_checks = [
            (len(DB["people"]), 1000),
            (len(DB["organizations"]), 100),
            (DB["people"]["500"]["firstName"], "Person500")
        ]
        for actual, expected in performance_checks:
            self.assertEqual(actual, expected)

    def test_state_versioning_and_migration(self):
        """Test state versioning and migration scenarios."""
        # Create old version state format
        old_version_state = {
            "people": {
                "1": {
                    "id": "1",
                    "name": "John Doe",  # Old format: single name field
                    "email": "john@example.com"  # Old format: email instead of emailAddress
                }
            },
            "organizations": {
                "1": {
                    "id": "1", 
                    "name": "Old Corp",
                    "vanity_name": "old-corp"  # Old format: underscore instead of camelCase
                }
            },
            "posts": {
                "1": {
                    "id": "1",
                    "author": "urn:li:person:1",
                    "content": "Old content field name",  # Old format: content instead of commentary
                    "visibility": "PUBLIC"
                }
            },
            "next_person_id": 2
            # Missing some modern fields
        }
        
        # Save old version state
        with open(self.test_file_path, 'w') as f:
            json.dump(old_version_state, f)
        
        # Load old version state
        DB.clear()
        load_state(self.test_file_path)
        
        # Verify old format is preserved and system doesn't crash
        legacy_format_checks = [
            (DB["people"]["1"]["name"], "John Doe"),
            (DB["people"]["1"]["email"], "john@example.com"),
            (DB["organizations"]["1"]["vanity_name"], "old-corp"),
            (DB["posts"]["1"]["content"], "Old content field name")
        ]
        for actual, expected in legacy_format_checks:
            self.assertEqual(actual, expected)
        
        # Missing fields should be handled gracefully
        self.assertNotIn("organizationAcls", DB)
        self.assertNotIn("current_person_id", DB)

    def test_state_backup_and_recovery(self):
        """Test state backup and recovery operations."""
        # Set initial state
        DB.clear()
        DB.update(self.standard_state)
        
        # Store original state for comparison
        original_state = self.standard_state.copy()
        
        # Create backup
        backup_path = os.path.join(self.temp_dir, "backup.json")
        save_state(backup_path)
        
        # Modify state significantly
        DB["people"].clear()
        DB["organizations"].clear()
        DB["posts"]["corrupted"] = {"invalid": "data"}
        
        # Verify state is modified
        modified_state_checks = [
            (len(DB["people"]), 0),
            (len(DB["organizations"]), 0)
        ]
        for actual, expected in modified_state_checks:
            self.assertEqual(actual, expected)
        self.assertIn("corrupted", DB["posts"])
        
        # Recover from backup
        load_state(backup_path)
        
        # Verify recovery
        recovery_checks = [
            (len(DB["people"]), 2),
            (len(DB["organizations"]), 2),
            (DB["people"]["1"]["firstName"], "Alice"),
            (DB["organizations"]["1"]["name"], "LinkedIn Corporation")
        ]
        for actual, expected in recovery_checks:
            self.assertEqual(actual, expected)
        self.assertNotIn("corrupted", DB["posts"])

    def test_empty_and_minimal_states(self):
        """Test handling of empty and minimal state configurations."""
        # Test completely empty state
        empty_state = {}
        DB.clear()
        DB.update(empty_state)
        
        save_state(self.test_file_path)
        DB.clear()
        load_state(self.test_file_path)
        
        self.assertEqual(DB, {})
        
        # Test minimal valid state
        minimal_state = {
            "people": {},
            "organizations": {},
            "organizationAcls": {},
            "posts": {},
            "next_person_id": 1,
            "next_org_id": 1,
            "next_acl_id": 1, 
            "next_post_id": 1,
            "current_person_id": None
        }
        
        DB.clear()
        DB.update(minimal_state)
        
        save_state(self.test_file_path)
        DB.clear()
        load_state(self.test_file_path)
        
        self.assertEqual(DB, minimal_state)
        self.assertIsNone(DB["current_person_id"])

    def test_state_validation_edge_cases(self):
        """Test state validation with edge cases and boundary conditions."""
        edge_case_scenarios = [
            # Very long string values
            {
                "people": {
                    "1": {
                        "id": "1",
                        "firstName": "A" * 1000,
                        "lastName": "B" * 1000,
                        "bio": "C" * 10000
                    }
                },
                "organizations": {},
                "organizationAcls": {},
                "posts": {},
                "next_person_id": 2
            },
            # Numeric edge cases
            {
                "people": {},
                "organizations": {},
                "organizationAcls": {},
                "posts": {},
                "next_person_id": 999999999,
                "next_org_id": 0,
                "next_acl_id": 1,
                "next_post_id": 1
            },
            # Special characters and symbols
            {
                "people": {
                    "1": {
                        "id": "1",
                        "firstName": "User\x00\x01\x02",
                        "lastName": "Test\n\r\t",
                        "emailAddress": "test@example.com"
                    }
                },
                "organizations": {},
                "organizationAcls": {},
                "posts": {},
                "next_person_id": 2
            }
        ]
        
        for i, scenario in enumerate(edge_case_scenarios):
            with self.subTest(scenario=i):
                # Test save/load cycle with edge case data
                DB.clear()
                DB.update(scenario)
                
                edge_case_path = os.path.join(self.temp_dir, f"edge_case_{i}.json")
                save_state(edge_case_path)
                
                # Verify file was created and is valid JSON
                self.assertTrue(os.path.exists(edge_case_path))
                
                with open(edge_case_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                self.assertEqual(loaded_data, scenario)


if __name__ == '__main__':
    unittest.main(verbosity=2)
