# figma/tests/test_set_current_file.py

import unittest
import copy
from ..SimulationEngine.db import DB
from figma.file_management import set_current_file 
from ..SimulationEngine.custom_errors import InvalidInputError

from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestSetCurrentFile(BaseTestCaseWithErrorHandler): 

    def setUp(self):
        """Set up a clean DB state for each test."""
        self.DB = DB
        self.DB.clear()

        self.file_key_alpha = "file_alpha_001"
        self.file_key_beta = "file_beta_002"
        self.non_existent_key = "file_omega_999"
        self.initial_current_file_key = self.file_key_alpha

        self.DB['files'] = [
            {'fileKey': self.file_key_alpha, 'name': 'Alpha Document'},
            {'fileKey': self.file_key_beta, 'name': 'Beta Presentation'},
        ]
        self.DB['current_file_key'] = self.initial_current_file_key
        self.DB['projects'] = [] # Example, if other parts of the system expect it

    # --- SUCCESS CASES ---
    def test_set_current_file_success_valid_key(self):
        """Test successfully setting the current_file_key to a new, valid key."""
        result = set_current_file(self.file_key_beta)
        self.assertTrue(result, "set_current_file should return True on success.")
        self.assertEqual(self.DB['current_file_key'], self.file_key_beta)

    def test_set_current_file_idempotency_set_same_key(self):
        """Test setting the current_file_key to its current value should succeed."""
        result = set_current_file(self.file_key_alpha)
        self.assertTrue(result, "set_current_file should return True even if key is already set.")
        self.assertEqual(self.DB['current_file_key'], self.file_key_alpha)

    # --- KEY NOT FOUND CASES (Expecting InvalidInputError as per the updated code) ---
    def test_set_current_file_raises_invalid_input_error_for_key_not_found(self):
        """Test an InvalidInputError is raised for a key that does not exist."""
        initial_key = self.DB['current_file_key']
        
        # Use assertRaisesRegex to check the exception type and message
        with self.assertRaisesRegex(InvalidInputError, f"Error: File with key '{self.non_existent_key}' not found in the database."):
            set_current_file(self.non_existent_key)
        
        self.assertEqual(self.DB['current_file_key'], initial_key, "DB key should not change on failure.")

    def test_set_current_file_raises_invalid_input_error_for_empty_files_list(self):
        """Test an InvalidInputError is raised if DB['files'] is empty and key is sought."""
        self.DB['files'] = [] # Make the files list empty
        initial_key = self.DB['current_file_key']
        
        with self.assertRaisesRegex(InvalidInputError, f"Error: File with key '{self.file_key_alpha}' not found in the database."):
            set_current_file(self.file_key_alpha) # Try to set a key that was previously valid
            
        self.assertEqual(self.DB['current_file_key'], initial_key, "DB key should not change if files list is empty and key not found.")

    # --- INPUT VALIDATION CASES (Expecting InvalidInputError) ---
    def test_set_current_file_raises_invalid_input_error_for_none(self):
        """Test InvalidInputError is raised for None input."""
        initial_key = self.DB['current_file_key']
        with self.assertRaisesRegex(InvalidInputError, "Error: Invalid input type for file_key. Expected string, got NoneType."):
            set_current_file(None)
        self.assertEqual(self.DB['current_file_key'], initial_key)

    def test_set_current_file_raises_invalid_input_error_for_empty_string(self):
        """Test InvalidInputError is raised for an empty string input."""
        initial_key = self.DB['current_file_key']
        with self.assertRaisesRegex(InvalidInputError, "Error: Invalid input. file_key cannot be an empty string."):
            set_current_file("")
        self.assertEqual(self.DB['current_file_key'], initial_key)

    def test_set_current_file_raises_invalid_input_error_for_integer(self):
        """Test InvalidInputError is raised for an integer input."""
        initial_key = self.DB['current_file_key']
        with self.assertRaisesRegex(InvalidInputError, "Error: Invalid input type for file_key. Expected string, got int."):
            set_current_file(12345)
        self.assertEqual(self.DB['current_file_key'], initial_key)

    def test_set_current_file_raises_invalid_input_error_for_list(self):
        """Test InvalidInputError is raised for a list input."""
        initial_key = self.DB['current_file_key']
        with self.assertRaisesRegex(InvalidInputError, "Error: Invalid input type for file_key. Expected string, got list."):
            set_current_file(["not_a_key"])
        self.assertEqual(self.DB['current_file_key'], initial_key)

    # --- ROBUSTNESS CASES (Function should succeed despite malformed data if target key is valid) ---
    def test_set_current_file_succeeds_with_malformed_none_entry_in_list(self):
        """Test that the function succeeds by skipping a None entry in the files list if target key is valid."""
        self.DB['files'].append(None) # Add a malformed entry (not a dict)
        
        result = set_current_file(self.file_key_beta) # Target a valid key
        self.assertTrue(result)
        self.assertEqual(self.DB['current_file_key'], self.file_key_beta)

    def test_set_current_file_succeeds_with_malformed_string_entry_in_list(self):
        """Test that the function succeeds by skipping a string entry in the files list if target key is valid."""
        self.DB['files'].append("not_a_dictionary") # Add another malformed entry
        
        result = set_current_file(self.file_key_beta) # Target a valid key
        self.assertTrue(result)
        self.assertEqual(self.DB['current_file_key'], self.file_key_beta)

    def test_set_current_file_succeeds_with_entry_missing_filekey_or_non_string_filekey(self):
        """Test the function skips entries missing 'fileKey' or with non-string 'fileKey' and still finds valid ones."""
        self.DB['files'].append({'name': 'File Without Key Attribute'}) # Missing 'fileKey'
        self.DB['files'].append({'fileKey': 123, 'name': 'File With Non-String Key'}) # 'fileKey' is int
        
        result = set_current_file(self.file_key_beta) # Target a valid key
        self.assertTrue(result)
        self.assertEqual(self.DB['current_file_key'], self.file_key_beta)


if __name__ == '__main__':
    unittest.main()

