#!/usr/bin/env python3
"""
Simple test runner for the standalone hydrate_db tests.
This script runs the working tests that don't require complex API setup.
"""

import os
import sys
import subprocess
import unittest

def run_standalone_tests():
    """Run the standalone hydrate_db tests."""
    print("="*80)
    print("HYDRATE_DB STANDALONE TESTS")
    print("="*80)
    print()
    
    # Add the current directory to the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Import and run the standalone test
    try:
        from test_hydrate_db_standalone import TestHydrateDBStandalone
        
        # Create a test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestHydrateDBStandalone)
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")
        
        if result.failures:
            print(f"\nFAILURES:")
            for test, trace in result.failures:
                print(f"  - {test}")
                print(f"    {trace}")
        
        if result.errors:
            print(f"\nERRORS:")
            for test, trace in result.errors:
                print(f"  - {test}")
                print(f"    {trace}")
        
        if result.skipped:
            print(f"\nSKIPPED:")
            for test, reason in result.skipped:
                print(f"  - {test}: {reason}")
        
        if result.wasSuccessful():
            print(f"\n✅ ALL TESTS PASSED!")
            print("The hydrate_db function is working correctly for:")
            print("  - Google Drive files")
            print("  - Google Sheets files")
            print("  - Google Slides files")
            print("  - Google Docs files")
            print("  - Error handling")
            print("  - File metadata integrity")
        else:
            print(f"\n❌ SOME TESTS FAILED!")
        
        return 0 if result.wasSuccessful() else 1
        
    except ImportError as e:
        print(f"❌ Error importing test module: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == '__main__':
    exit_code = run_standalone_tests()
    sys.exit(exit_code) 