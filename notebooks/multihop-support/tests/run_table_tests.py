#!/usr/bin/env python3
"""
Test runner for Google Drive table extraction functionality.

This script runs the table extraction tests to verify that the new table handling
code in gdrive.py works correctly.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the gdrive module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def run_table_extraction_tests():
    """Run the table extraction unit tests."""
    print("Running Google Drive Table Extraction Tests")
    print("=" * 50)
    
    # Import and run the table extraction tests
    from test_gdrive_table_extraction import TestGDriveTableExtraction
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGDriveTableExtraction)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_integration_tests():
    """Run the integration tests that include table functionality."""
    print("\nRunning Google Drive Integration Tests (including table functionality)")
    print("=" * 70)
    
    # Import and run the integration tests
    from test_gdrive_hydrate_db import TestGDriveHydrateDB
    
    # Create test suite for table-related tests only
    suite = unittest.TestSuite()
    
    # Add only the table-related test methods
    test_case = TestGDriveHydrateDB()
    test_case.setUp()
    
    table_tests = [
        'test_google_docs_table_content_extraction',
        'test_table_content_data_integrity', 
        'test_mixed_content_extraction'
    ]
    
    for test_name in table_tests:
        if hasattr(test_case, test_name):
            suite.addTest(TestGDriveHydrateDB(test_name))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Main function to run all table-related tests."""
    print("Google Drive Table Extraction Test Suite")
    print("=" * 40)
    
    # Run unit tests
    unit_success = run_table_extraction_tests()
    
    # Run integration tests
    integration_success = run_integration_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Unit Tests: {'✓ PASSED' if unit_success else '✗ FAILED'}")
    print(f"Integration Tests: {'✓ PASSED' if integration_success else '✗ FAILED'}")
    
    overall_success = unit_success and integration_success
    print(f"\nOverall Result: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == '__main__':
    sys.exit(main()) 