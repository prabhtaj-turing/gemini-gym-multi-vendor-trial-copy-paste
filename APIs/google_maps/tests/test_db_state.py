"""
Database state test suite for Google Maps API module.

This test suite validates database persistence functionality including:
1. Data save and load operations with various data formats
2. Backward compatibility with legacy data structures  
3. Data integrity validation across save/load cycles
4. Error handling for invalid file operations
5. State management and consistency verification

Purpose: Ensure database operations are reliable and maintain compatibility
across different data formats and versions.

Author: Auto-generated database state test suite
"""

import unittest
import os
import tempfile
import json
import shutil
from typing import Dict, Any
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGoogleMapsDataSaveLoad(BaseTestCaseWithErrorHandler):
    """
    Test suite for database save and load operations.
    
    Purpose: Verify that data can be reliably saved to and loaded from files,
    maintaining data integrity and supporting various data formats.
    """
    
    def setUp(self):
        """Set up test fixtures for database save/load tests."""
        # Path to test assets directory
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        # Temporary directory for test output files
        self.temp_dir = tempfile.mkdtemp()
        
        # Store original database state to restore after tests
        from google_maps.SimulationEngine.db import get_minified_state
        self.original_db_state = get_minified_state().copy()
        
        # Test file paths
        self.test_files = {
            'modern': os.path.join(self.assets_dir, 'modern_test_data.json'),
            'legacy': os.path.join(self.assets_dir, 'legacy_test_data.json'),
            'empty': os.path.join(self.assets_dir, 'empty_test_data.json'),
            'mixed': os.path.join(self.assets_dir, 'mixed_format_data.json')
        }
        
        # Temporary output file for save/load testing
        self.temp_output_file = os.path.join(self.temp_dir, 'test_output.json')
    
    def tearDown(self):
        """Clean up test fixtures and restore original database state."""
        # Restore original database state
        from google_maps.SimulationEngine.db import DB
        DB.clear()
        DB.update(self.original_db_state)
        
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_current_state_to_file(self):
        """
        Test saving current database state to a file.
        
        Purpose: Verify save_state function can write current DB contents to a file.
        Critical because: Data persistence requires reliable save operations.
        """
        from google_maps.SimulationEngine.db import save_state, get_minified_state
        
        # Get current state before saving
        current_state = get_minified_state()
        
        # Save state to temporary file
        save_state(self.temp_output_file)
        
        # Verify file was created and has content
        self.assertTrue(os.path.exists(self.temp_output_file))
        self.assertGreater(os.path.getsize(self.temp_output_file), 0)
        
        # Verify file contains valid JSON
        with open(self.temp_output_file, 'r') as f:
            saved_data = json.load(f)
        
        # Verify saved data matches current state
        self.assertEqual(saved_data, current_state)
        self.assertIsInstance(saved_data, dict)
    
    def test_load_modern_format_data(self):
        """
        Test loading modern format data from file.
        
        Purpose: Verify load_state can correctly import modern data format.
        Critical because: Modern format is the current standard for data storage.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load modern format test data
        load_state(self.test_files['modern'])
        
        # Get loaded state
        loaded_state = get_minified_state()
        
        # Verify expected modern format places are loaded
        self.assertIn('test_place_modern', loaded_state)
        self.assertIn('test_place_modern_2', loaded_state)
        
        # Verify modern format structure
        modern_place = loaded_state['test_place_modern']
        self.assertEqual(modern_place['id'], 'test_place_modern')
        self.assertEqual(modern_place['name'], 'Modern Test Restaurant')
        self.assertEqual(modern_place['rating'], 4.5)
        self.assertEqual(modern_place['userRatingCount'], 125)
        
        # Verify modern location format
        self.assertIn('location', modern_place)
        self.assertEqual(modern_place['location']['latitude'], 37.7749)
        self.assertEqual(modern_place['location']['longitude'], -122.4194)
        
        # Verify modern types format
        self.assertIn('types', modern_place)
        self.assertIsInstance(modern_place['types'], list)
        self.assertIn('restaurant', modern_place['types'])
    
    def test_load_empty_data_file(self):
        """
        Test loading empty data file.
        
        Purpose: Verify system handles empty databases gracefully.
        Critical because: Empty states should not cause system failures.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load empty test data
        load_state(self.test_files['empty'])
        
        # Get loaded state
        loaded_state = get_minified_state()
        
        # Verify database is empty
        self.assertEqual(loaded_state, {})
        self.assertEqual(len(loaded_state), 0)
    
    def test_save_and_load_roundtrip_data_integrity(self):
        """
        Test complete save and load cycle maintains data integrity.
        
        Purpose: Verify data remains unchanged through save/load operations.
        Critical because: Data corruption during persistence would be catastrophic.
        """
        from google_maps.SimulationEngine.db import save_state, load_state, get_minified_state, DB
        from google_maps.SimulationEngine.utils import _create_place
        
        # Create test data in database
        test_place_data = {
            'id': 'roundtrip_test_place',
            'name': 'Roundtrip Test Restaurant',
            'rating': 4.6,
            'userRatingCount': 250,
            'formattedAddress': '999 Roundtrip Avenue, Test City, TC 99999',
            'location': {'latitude': 37.7999, 'longitude': -122.3999},
            'primaryType': 'restaurant',
            'types': ['restaurant', 'food', 'establishment'],
            'businessStatus': 'OPERATIONAL',
            'paymentOptions': {
                'acceptsCreditCards': True,
                'acceptsDebitCards': True,
                'acceptsCashOnly': False
            }
        }
        
        # Add test place to database
        _create_place(test_place_data)
        
        # Get state before save
        state_before_save = get_minified_state().copy()
        
        # Save current state
        save_state(self.temp_output_file)
        
        # Clear database and load from file
        DB.clear()
        load_state(self.temp_output_file)
        
        # Get state after load
        state_after_load = get_minified_state()
        
        # Verify complete data integrity
        self.assertEqual(state_before_save, state_after_load)
        
        # Verify specific test place data integrity
        loaded_place = state_after_load['roundtrip_test_place']
        self.assertEqual(loaded_place['id'], test_place_data['id'])
        self.assertEqual(loaded_place['name'], test_place_data['name'])
        self.assertEqual(loaded_place['rating'], test_place_data['rating'])
        self.assertEqual(loaded_place['location'], test_place_data['location'])
        self.assertEqual(loaded_place['paymentOptions'], test_place_data['paymentOptions'])
    
    def test_load_mixed_format_data_handling(self):
        """
        Test loading file containing mixed modern and legacy format data.
        
        Purpose: Verify system can handle mixed data formats in single file.
        Critical because: Real-world data may contain mixed formats during transitions.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load mixed format test data
        load_state(self.test_files['mixed'])
        
        # Get loaded state
        loaded_state = get_minified_state()
        
        # Verify both modern and legacy places are loaded
        self.assertIn('modern_place', loaded_state)
        self.assertIn('legacy_place', loaded_state)
        
        # Verify modern format place structure
        modern_place = loaded_state['modern_place']
        self.assertEqual(modern_place['id'], 'modern_place')
        self.assertIn('location', modern_place)
        self.assertIn('primaryType', modern_place)
        
        # Verify legacy format place structure is preserved
        legacy_place = loaded_state['legacy_place']
        self.assertEqual(legacy_place['place_id'], 'legacy_place')
        self.assertIn('lat', legacy_place)
        self.assertIn('lng', legacy_place)
        self.assertIn('type', legacy_place)
    
    def test_multiple_save_load_operations_consistency(self):
        """
        Test multiple consecutive save/load operations maintain consistency.
        
        Purpose: Verify repeated operations don't introduce data drift or corruption.
        Critical because: Systems may perform many save/load cycles over time.
        """
        from google_maps.SimulationEngine.db import save_state, load_state, get_minified_state
        
        # Load initial test data
        load_state(self.test_files['modern'])
        initial_state = get_minified_state().copy()
        
        # Perform multiple save/load cycles
        for cycle in range(3):
            cycle_file = os.path.join(self.temp_dir, f'cycle_{cycle}.json')
            
            # Save current state
            save_state(cycle_file)
            
            # Load state back
            load_state(cycle_file)
            
            # Verify state remains consistent
            current_state = get_minified_state()
            self.assertEqual(
                current_state, 
                initial_state,
                f"Data inconsistency detected after save/load cycle {cycle}"
            )


class TestGoogleMapsBackwardCompatibility(BaseTestCaseWithErrorHandler):
    """
    Test suite for backward compatibility with legacy data formats.
    
    Purpose: Ensure new implementations can still work with older data formats
    and that legacy data structures are properly handled.
    """
    
    def setUp(self):
        """Set up test fixtures for backward compatibility tests."""
        # Path to test assets directory
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        # Store original database state
        from google_maps.SimulationEngine.db import get_minified_state
        self.original_db_state = get_minified_state().copy()
        
        # Legacy data format file
        self.legacy_data_file = os.path.join(self.assets_dir, 'legacy_test_data.json')
        
        # Expected legacy data structure for validation
        self.expected_legacy_structure = {
            'place_id_field': 'place_id',  # Legacy uses place_id instead of id
            'location_fields': ['lat', 'lng'],  # Legacy uses lat/lng instead of location object
            'rating_field': 'rating_count',  # Legacy uses rating_count instead of userRatingCount
            'category_field': 'categories',  # Legacy uses categories instead of types
            'address_field': 'address',  # Legacy uses address instead of formattedAddress
            'status_field': 'status',  # Legacy uses status instead of businessStatus
            'type_field': 'type'  # Legacy uses type instead of primaryType
        }
    
    def tearDown(self):
        """Clean up test fixtures and restore original database state."""
        # Restore original database state
        from google_maps.SimulationEngine.db import DB
        DB.clear()
        DB.update(self.original_db_state)
    
    def test_load_legacy_data_format_compatibility(self):
        """
        Test loading legacy data format and verify structure preservation.
        
        Purpose: Ensure legacy data formats can be loaded without modification.
        Critical because: Backward compatibility prevents data loss during upgrades.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load legacy format data
        load_state(self.legacy_data_file)
        loaded_state = get_minified_state()
        
        # Verify legacy places are loaded
        self.assertIn('test_place_legacy', loaded_state)
        self.assertIn('test_place_legacy_minimal', loaded_state)
        
        # Verify legacy field structure is preserved
        legacy_place = loaded_state['test_place_legacy']
        
        # Check legacy ID field
        self.assertIn('place_id', legacy_place)
        self.assertEqual(legacy_place['place_id'], 'test_place_legacy')
        
        # Check legacy location fields
        self.assertIn('lat', legacy_place)
        self.assertIn('lng', legacy_place)
        self.assertEqual(legacy_place['lat'], 37.7649)
        self.assertEqual(legacy_place['lng'], -122.4294)
        
        # Check legacy rating field
        self.assertIn('rating_count', legacy_place)
        self.assertEqual(legacy_place['rating_count'], 98)
        
        # Check legacy category field
        self.assertIn('categories', legacy_place)
        self.assertIsInstance(legacy_place['categories'], list)
        self.assertIn('restaurant', legacy_place['categories'])
        
        # Check legacy address field
        self.assertIn('address', legacy_place)
        self.assertEqual(legacy_place['address'], '789 Legacy Boulevard, Old City, OC 98765')
    
    def test_legacy_minimal_data_structure_support(self):
        """
        Test support for minimal legacy data structures.
        
        Purpose: Verify minimal legacy records with fewer fields are handled correctly.
        Critical because: Early data may have minimal field sets.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load legacy format data
        load_state(self.legacy_data_file)
        loaded_state = get_minified_state()
        
        # Verify minimal legacy place
        minimal_place = loaded_state['test_place_legacy_minimal']
        
        # Check minimal required fields are present
        self.assertIn('place_id', minimal_place)
        self.assertIn('name', minimal_place)
        self.assertIn('rating', minimal_place)
        self.assertIn('address', minimal_place)
        self.assertIn('lat', minimal_place)
        self.assertIn('lng', minimal_place)
        self.assertIn('type', minimal_place)
        
        # Verify minimal data values
        self.assertEqual(minimal_place['place_id'], 'test_place_legacy_minimal')
        self.assertEqual(minimal_place['name'], 'Minimal Legacy Place')
        self.assertEqual(minimal_place['rating'], 3.8)
        self.assertEqual(minimal_place['type'], 'shop')
    
    def test_legacy_nested_structure_preservation(self):
        """
        Test preservation of legacy nested data structures.
        
        Purpose: Verify complex nested legacy structures remain intact.
        Critical because: Legacy data may have different nesting patterns.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load legacy format data
        load_state(self.legacy_data_file)
        loaded_state = get_minified_state()
        
        legacy_place = loaded_state['test_place_legacy']
        
        # Verify legacy hours nested structure
        self.assertIn('hours', legacy_place)
        hours = legacy_place['hours']
        
        self.assertIn('open_now', hours)
        self.assertIn('schedule', hours)
        self.assertTrue(hours['open_now'])
        self.assertIsInstance(hours['schedule'], list)
        self.assertGreater(len(hours['schedule']), 0)
        
        # Verify legacy payments nested structure
        self.assertIn('payments', legacy_place)
        payments = legacy_place['payments']
        
        self.assertIn('credit_cards', payments)
        self.assertIn('cash_only', payments)
        self.assertTrue(payments['credit_cards'])
        self.assertFalse(payments['cash_only'])
    
    def test_legacy_data_field_mapping_consistency(self):
        """
        Test consistency of legacy field mappings across different records.
        
        Purpose: Verify legacy field usage is consistent across all legacy records.
        Critical because: Inconsistent field usage could indicate data corruption.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load legacy format data
        load_state(self.legacy_data_file)
        loaded_state = get_minified_state()
        
        # Get all legacy places
        legacy_places = [
            loaded_state['test_place_legacy'],
            loaded_state['test_place_legacy_minimal']
        ]
        
        # Verify consistent field usage across legacy records
        for place in legacy_places:
            # All legacy places should use place_id
            self.assertIn('place_id', place)
            
            # All should use lat/lng for location
            self.assertIn('lat', place)
            self.assertIn('lng', place)
            
            # All should use address for address info
            self.assertIn('address', place)
            
            # All should use type for primary type
            self.assertIn('type', place)
            
            # Verify location values are numeric
            self.assertIsInstance(place['lat'], (int, float))
            self.assertIsInstance(place['lng'], (int, float))
    
    def test_legacy_data_value_range_validation(self):
        """
        Test validation of legacy data value ranges and types.
        
        Purpose: Verify legacy data values are within expected ranges and types.
        Critical because: Invalid legacy data could cause application errors.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load legacy format data
        load_state(self.legacy_data_file)
        loaded_state = get_minified_state()
        
        legacy_place = loaded_state['test_place_legacy']
        
        # Validate rating range
        self.assertIsInstance(legacy_place['rating'], (int, float))
        self.assertGreaterEqual(legacy_place['rating'], 0.0)
        self.assertLessEqual(legacy_place['rating'], 5.0)
        
        # Validate latitude range
        self.assertGreaterEqual(legacy_place['lat'], -90.0)
        self.assertLessEqual(legacy_place['lat'], 90.0)
        
        # Validate longitude range
        self.assertGreaterEqual(legacy_place['lng'], -180.0)
        self.assertLessEqual(legacy_place['lng'], 180.0)
        
        # Validate rating count
        self.assertIsInstance(legacy_place['rating_count'], int)
        self.assertGreaterEqual(legacy_place['rating_count'], 0)
        
        # Validate string fields are non-empty
        self.assertIsInstance(legacy_place['name'], str)
        self.assertGreater(len(legacy_place['name']), 0)
        self.assertIsInstance(legacy_place['address'], str)
        self.assertGreater(len(legacy_place['address']), 0)


class TestGoogleMapsDbStateErrorHandling(BaseTestCaseWithErrorHandler):
    """
    Test suite for error handling in database state operations.
    
    Purpose: Verify database operations handle error conditions gracefully
    and provide appropriate error responses.
    """
    
    def setUp(self):
        """Set up test fixtures for error handling tests."""
        # Temporary directory for error test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Store original database state
        from google_maps.SimulationEngine.db import get_minified_state
        self.original_db_state = get_minified_state().copy()
        
        # Invalid file paths for error testing
        self.nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        self.invalid_json_file = os.path.join(self.temp_dir, 'invalid.json')
        self.readonly_file = os.path.join(self.temp_dir, 'readonly.json')
        
        # Create invalid JSON file
        with open(self.invalid_json_file, 'w') as f:
            f.write('{ invalid json content }')
    
    def tearDown(self):
        """Clean up test fixtures and restore original database state."""
        # Restore original database state
        from google_maps.SimulationEngine.db import DB
        DB.clear()
        DB.update(self.original_db_state)
        
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_state_nonexistent_directory_error(self):
        """
        Test save_state error handling for nonexistent directory.
        
        Purpose: Verify appropriate error when saving to invalid path.
        Critical because: Invalid paths should produce clear error messages.
        """
        from google_maps.SimulationEngine.db import save_state
        from common_utils.error_handling import get_package_error_mode
        
        nonexistent_dir_file = '/nonexistent/directory/file.json'
        
        # Since OSError message varies by system, we test error type directly
        current_error_mode = get_package_error_mode()
        
        if current_error_mode == "raise":
            # Test that OSError is raised (message content varies by system)
            error_occurred = False
            try:
                save_state(nonexistent_dir_file)
            except OSError:
                error_occurred = True
            
            self.assertTrue(error_occurred, "Expected OSError when saving to nonexistent directory")
        elif current_error_mode == "error_dict":
            # Test error dict response
            result = save_state(nonexistent_dir_file)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("exceptionType"), "OSError")
    
    def test_load_state_nonexistent_file_error(self):
        """
        Test load_state error handling for nonexistent file.
        
        Purpose: Verify appropriate error when loading from invalid file.
        Critical because: Missing files should produce clear error messages.
        """
        from google_maps.SimulationEngine.db import load_state
        from common_utils.error_handling import get_package_error_mode
        
        # Since OSError message varies by system, we test error type directly
        current_error_mode = get_package_error_mode()
        
        if current_error_mode == "raise":
            # Test that OSError is raised (message content varies by system)
            error_occurred = False
            try:
                load_state(self.nonexistent_file)
            except OSError:
                error_occurred = True
            
            self.assertTrue(error_occurred, "Expected OSError when loading nonexistent file")
        elif current_error_mode == "error_dict":
            # Test error dict response
            result = load_state(self.nonexistent_file)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("exceptionType"), "OSError")
    
    def test_load_state_invalid_json_error(self):
        """
        Test load_state error handling for invalid JSON content.
        
        Purpose: Verify appropriate error when loading malformed JSON.
        Critical because: Corrupted files should not crash the system.
        """
        from google_maps.SimulationEngine.db import load_state
        from common_utils.error_handling import get_package_error_mode
        
        # Since JSONDecodeError message varies, we test error type directly
        current_error_mode = get_package_error_mode()
        
        if current_error_mode == "raise":
            # Test that JSONDecodeError is raised
            error_occurred = False
            try:
                load_state(self.invalid_json_file)
            except json.JSONDecodeError:
                error_occurred = True
            
            self.assertTrue(error_occurred, "Expected JSONDecodeError when loading invalid JSON")
        elif current_error_mode == "error_dict":
            # Test error dict response
            result = load_state(self.invalid_json_file)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("exceptionType"), "JSONDecodeError")
    
    def test_save_state_permission_error_handling(self):
        """
        Test save_state error handling for permission denied scenarios.
        
        Purpose: Verify appropriate error when write permissions are denied.
        Critical because: Permission issues should be clearly reported.
        
        Note: This test may be skipped on systems where chmod doesn't restrict permissions.
        """
        from google_maps.SimulationEngine.db import save_state
        
        # Create a file and make directory read-only (if possible)
        readonly_dir = os.path.join(self.temp_dir, 'readonly_dir')
        os.makedirs(readonly_dir, exist_ok=True)
        readonly_file_path = os.path.join(readonly_dir, 'readonly.json')
        
        # Try to make directory read-only
        os.chmod(readonly_dir, 0o444)
        
        # Test save to read-only directory may raise OSError
        # Note: Behavior varies by system, so we test that some error occurs
        permission_error_occurred = False
        error_message = None
        
        # Use a direct call to check for permission error
        from google_maps.SimulationEngine.db import get_minified_state
        current_error_mode = None
        
        # Get the current error mode to handle appropriately
        from common_utils.error_handling import get_package_error_mode
        current_error_mode = get_package_error_mode()
        
        if current_error_mode == "raise":
            # In raise mode, we expect an exception
            try:
                save_state(readonly_file_path)
            except (OSError, PermissionError):
                permission_error_occurred = True
            
            # We verify some kind of permission/OS error occurred
            # (exact error type may vary by system)
            self.assertTrue(
                permission_error_occurred,
                "Expected permission or OS error when writing to read-only directory"
            )
        
        # Restore directory permissions for cleanup
        os.chmod(readonly_dir, 0o755)


class TestGoogleMapsDbStateIntegration(BaseTestCaseWithErrorHandler):
    """
    Test suite for database state integration scenarios.
    
    Purpose: Verify database state operations work correctly in complex
    integration scenarios combining multiple operations.
    """
    
    def setUp(self):
        """Set up test fixtures for integration tests."""
        # Path to test assets
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.temp_dir = tempfile.mkdtemp()
        
        # Store original database state
        from google_maps.SimulationEngine.db import get_minified_state
        self.original_db_state = get_minified_state().copy()
        
        # Test files
        self.modern_file = os.path.join(self.assets_dir, 'modern_test_data.json')
        self.legacy_file = os.path.join(self.assets_dir, 'legacy_test_data.json')
    
    def tearDown(self):
        """Clean up test fixtures and restore original database state."""
        # Restore original database state
        from google_maps.SimulationEngine.db import DB
        DB.clear()
        DB.update(self.original_db_state)
        
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_sequential_load_operations_data_integrity(self):
        """
        Test sequential loading of different data formats maintains integrity.
        
        Purpose: Verify loading multiple files sequentially works correctly.
        Critical because: Applications may need to load multiple data sources.
        """
        from google_maps.SimulationEngine.db import load_state, get_minified_state
        
        # Load modern format first
        load_state(self.modern_file)
        modern_loaded_state = get_minified_state().copy()
        
        # Verify modern data is loaded
        self.assertIn('test_place_modern', modern_loaded_state)
        self.assertIn('test_place_modern_2', modern_loaded_state)
        
        # Load legacy format (should replace modern data)
        load_state(self.legacy_file)
        legacy_loaded_state = get_minified_state()
        
        # Verify legacy data replaced modern data
        self.assertIn('test_place_legacy', legacy_loaded_state)
        self.assertIn('test_place_legacy_minimal', legacy_loaded_state)
        self.assertNotIn('test_place_modern', legacy_loaded_state)
    
    def test_load_save_load_with_data_modification(self):
        """
        Test load -> modify -> save -> load cycle maintains modifications.
        
        Purpose: Verify modifications persist through save/load operations.
        Critical because: Applications need to modify and persist data changes.
        """
        from google_maps.SimulationEngine.db import load_state, save_state, get_minified_state, DB
        
        # Load initial data
        load_state(self.modern_file)
        
        # Modify loaded data
        DB['test_place_modern']['rating'] = 4.8
        DB['test_place_modern']['userRatingCount'] = 300
        DB['modified_place'] = {
            'id': 'modified_place',
            'name': 'Modified Test Place',
            'rating': 4.9
        }
        
        # Save modified state
        modified_file = os.path.join(self.temp_dir, 'modified_data.json')
        save_state(modified_file)
        
        # Clear and reload
        DB.clear()
        load_state(modified_file)
        
        # Verify modifications persisted
        reloaded_state = get_minified_state()
        
        self.assertEqual(reloaded_state['test_place_modern']['rating'], 4.8)
        self.assertEqual(reloaded_state['test_place_modern']['userRatingCount'], 300)
        self.assertIn('modified_place', reloaded_state)
        self.assertEqual(reloaded_state['modified_place']['name'], 'Modified Test Place')
    
    def test_state_consistency_across_operations(self):
        """
        Test state consistency across multiple database operations.
        
        Purpose: Verify database state remains consistent during complex operations.
        Critical because: State corruption could lead to data loss or errors.
        """
        from google_maps.SimulationEngine.db import load_state, save_state, get_minified_state
        from google_maps.SimulationEngine.utils import _create_place
        
        # Load initial data
        load_state(self.modern_file)
        
        # Perform multiple operations
        operations_log = []
        
        # Operation 1: Add new place
        new_place = {
            'id': 'consistency_test_place',
            'name': 'Consistency Test Place',
            'rating': 4.4
        }
        _create_place(new_place)
        operations_log.append('create_place')
        
        # Operation 2: Save state
        temp_file1 = os.path.join(self.temp_dir, 'consistency1.json')
        save_state(temp_file1)
        operations_log.append('save_state')
        
        # Operation 3: Load different data
        load_state(self.legacy_file)
        operations_log.append('load_legacy')
        
        # Operation 4: Save again
        temp_file2 = os.path.join(self.temp_dir, 'consistency2.json')
        save_state(temp_file2)
        operations_log.append('save_legacy')
        
        # Operation 5: Reload first saved state
        load_state(temp_file1)
        operations_log.append('reload_modern')
        
        # Verify final state contains expected data
        final_state = get_minified_state()
        
        # Should have modern data plus our added place
        self.assertIn('test_place_modern', final_state)
        self.assertIn('consistency_test_place', final_state)
        self.assertNotIn('test_place_legacy', final_state)  # Legacy should not be present
        
        # Verify our added place data integrity
        added_place = final_state['consistency_test_place']
        self.assertEqual(added_place['id'], 'consistency_test_place')
        self.assertEqual(added_place['name'], 'Consistency Test Place')
        self.assertEqual(added_place['rating'], 4.4)


if __name__ == '__main__':
    # Run all database state test suites
    unittest.main(verbosity=2)
