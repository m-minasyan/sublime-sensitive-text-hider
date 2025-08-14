#!/usr/bin/env python3

import unittest
import sys

def run_extended_tests():
    print("=" * 70)
    print("Running Extended Test Suite")
    print("=" * 70)
    
    test_modules = [
        'test_edge_cases',
        'test_concurrent_operations', 
        'test_large_files',
        'test_custom_patterns',
        'test_performance'
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(f'tests.{module}')
            suite.addTests(tests)
        except Exception as e:
            print(f"Error loading {module}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("EXTENDED TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailed Tests:")
        for test, _ in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nTests with Errors:")
        for test, _ in result.errors:
            print(f"  - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print("\n✅ All extended tests passed!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} tests failed")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(run_extended_tests())