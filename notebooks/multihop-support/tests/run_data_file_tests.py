#!/usr/bin/env python3
"""
Test runner for data file tests.
Runs comprehensive tests for Google Sheets, Docs, and Slides converters
using real data files from the tests/data folder.
"""

import os
import sys
import unittest
import subprocess

def run_data_file_tests():
    """Run all data file tests for Google services."""
    # Add the current directory to the path so we can import the test modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Define test modules
    test_modules = [
        'test_gsheets_data_files',
        'test_gdocs_data_files', 
        'test_gslides_data_files'
    ]
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests from each module
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            print(f"✓ Loaded tests from {module_name}")
        except ImportError as e:
            print(f"✗ Failed to import {module_name}: {e}")
            continue
        except Exception as e:
            print(f"✗ Error loading {module_name}: {e}")
            continue
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("DATA FILE TESTS SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace}")
    
    if result.skipped:
        print(f"\nSKIPPED:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

def check_data_files():
    """Check that required data files exist."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    required_files = [
        '2025_Inventory.xlsx',
        '2025_Inventory.xlsx.json',
        'kids_craft_camp_2025_business_information.docx',
        'kids_craft_camp_2025_business_information.docx.json',
        'Summer_Spark!_2025_seasonal_overview.pptx',
        'Summer_Spark!_2025_seasonal_overview.pptx.json'
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = os.path.join(data_dir, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
    
    if missing_files:
        print("✗ Missing required data files:")
        for file_name in missing_files:
            print(f"  - {file_name}")
        print(f"\nPlease ensure all data files are present in {data_dir}")
        return False
    
    print("✓ All required data files found")
    return True

def main():
    """Main function to run data file tests."""
    print("Running Data File Tests for Google Services")
    print("=" * 50)
    
    # Check data files first
    if not check_data_files():
        return 1
    
    # Run tests
    return run_data_file_tests()

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 