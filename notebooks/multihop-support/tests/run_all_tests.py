#!/usr/bin/env python3
"""
Comprehensive test runner for all hydrate_db API tests.
This script runs tests for Google Drive, Google Sheets, Google Slides, and Google Docs.
"""

import os
import sys
import subprocess
import unittest
import time

def run_all_api_tests():
    """Run all API-specific hydrate_db tests."""
    print("="*80)
    print("COMPREHENSIVE HYDRATE_DB TESTS FOR ALL APIS")
    print("="*80)
    print()
    
    # Add the current directory to the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Test modules to run
    test_modules = [
        {
            'name': 'Google Drive',
            'module': 'test_gdrive_hydrate_db',
            'class': 'TestGDriveHydrateDB'
        },
        {
            'name': 'Google Sheets',
            'module': 'test_gsheets_hydrate_db',
            'class': 'TestGSheetsHydrateDB'
        },
        {
            'name': 'Google Slides',
            'module': 'test_gslides_hydrate_db',
            'class': 'TestGSlidesHydrateDB'
        },
        {
            'name': 'Google Docs',
            'module': 'test_gdocs_hydrate_db',
            'class': 'TestGDocsHydrateDB'
        }
    ]
    
    all_results = []
    
    for test_info in test_modules:
        print(f"\n{'='*60}")
        print(f"RUNNING {test_info['name'].upper()} TESTS")
        print(f"{'='*60}")
        
        try:
            # Import the test module
            module = __import__(test_info['module'])
            test_class = getattr(module, test_info['class'])
            
            # Create a test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(test_class)
            
            # Run the tests
            runner = unittest.TextTestRunner(verbosity=2)
            start_time = time.time()
            result = runner.run(suite)
            end_time = time.time()
            
            # Store results
            all_results.append({
                'name': test_info['name'],
                'result': result,
                'duration': end_time - start_time
            })
            
        except ImportError as e:
            print(f"❌ Error importing {test_info['name']} test module: {e}")
            all_results.append({
                'name': test_info['name'],
                'result': None,
                'error': str(e),
                'duration': 0
            })
        except Exception as e:
            print(f"❌ Error running {test_info['name']} tests: {e}")
            all_results.append({
                'name': test_info['name'],
                'result': None,
                'error': str(e),
                'duration': 0
            })
    
    # Print comprehensive summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    total_duration = 0
    
    for test_result in all_results:
        name = test_result['name']
        result = test_result['result']
        duration = test_result['duration']
        total_duration += duration
        
        print(f"\n{name} Tests:")
        if result is None:
            if 'error' in test_result:
                print(f"  ❌ Failed to run: {test_result['error']}")
            else:
                print(f"  ❌ Failed to run")
        else:
            tests_run = result.testsRun
            failures = len(result.failures)
            errors = len(result.errors)
            skipped = len(result.skipped)
            
            total_tests += tests_run
            total_failures += failures
            total_errors += errors
            total_skipped += skipped
            
            print(f"  Tests run: {tests_run}")
            print(f"  Failures: {failures}")
            print(f"  Errors: {errors}")
            print(f"  Skipped: {skipped}")
            print(f"  Duration: {duration:.2f}s")
            
            if result.wasSuccessful() and tests_run > 0:
                print(f"  ✅ All tests passed!")
            elif tests_run == 0:
                print(f"  ⚠️  No tests were run")
            else:
                print(f"  ❌ Some tests failed")
    
    # Overall summary
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    print(f"Total APIs tested: {len(test_modules)}")
    print(f"Total tests run: {total_tests}")
    print(f"Total failures: {total_failures}")
    print(f"Total errors: {total_errors}")
    print(f"Total skipped: {total_skipped}")
    print(f"Total duration: {total_duration:.2f}s")
    
    # Success determination
    success_count = 0
    for test_result in all_results:
        if (test_result['result'] is not None and 
            test_result['result'].wasSuccessful() and 
            test_result['result'].testsRun > 0):
            success_count += 1
    
    if success_count == len(test_modules):
        print(f"\n🎉 ALL API TESTS PASSED!")
        print("The hydrate_db function is working correctly for:")
        for test_info in test_modules:
            print(f"  ✅ {test_info['name']}")
        return 0
    elif success_count > 0:
        print(f"\n⚠️  PARTIAL SUCCESS: {success_count}/{len(test_modules)} APIs passed")
        print("Working APIs:")
        for i, test_result in enumerate(all_results):
            if (test_result['result'] is not None and 
                test_result['result'].wasSuccessful() and 
                test_result['result'].testsRun > 0):
                print(f"  ✅ {test_result['name']}")
        print("Failed/Skipped APIs:")
        for i, test_result in enumerate(all_results):
            if not (test_result['result'] is not None and 
                   test_result['result'].wasSuccessful() and 
                   test_result['result'].testsRun > 0):
                print(f"  ❌ {test_result['name']}")
        return 1
    else:
        print(f"\n❌ ALL API TESTS FAILED!")
        return 1

if __name__ == '__main__':
    exit_code = run_all_api_tests()
    sys.exit(exit_code) 