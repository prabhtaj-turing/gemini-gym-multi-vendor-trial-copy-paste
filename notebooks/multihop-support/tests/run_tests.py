#!/usr/bin/env python3
"""
Test runner for the multihop hydrate_db tests.
This script runs the comprehensive tests for Google Drive, Docs, Sheets, and Slides loading.
"""

import os
import sys
import subprocess
import unittest

def run_tests():
    """Run the multihop hydrate_db tests."""
    # Add the current directory to the path so we can import the test module
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Import the test module
    try:
        from test_multihop_hydrate_db import TestMultihopHydrateDB
        
        # Create a test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestMultihopHydrateDB)
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
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
        
    except ImportError as e:
        print(f"Error importing test module: {e}")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code) 