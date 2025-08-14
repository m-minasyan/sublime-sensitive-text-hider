#!/usr/bin/env python3

import unittest
import sys
import os

def run_tests():
    """Run all test suites and report results"""
    
    print("=" * 70)
    print("Running Sublime Sensitive Text Hider Test Suite")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_modules = []
    
    try:
        from tests import test_standalone_script
        test_modules.append(('Standalone Script Tests', test_standalone_script))
    except ImportError as e:
        print(f"Warning: Could not import standalone script tests: {e}")
    
    try:
        from tests import test_sublime_plugin
        test_modules.append(('Sublime Plugin Tests', test_sublime_plugin))
    except ImportError as e:
        print(f"Warning: Could not import sublime plugin tests: {e}")
    
    if not test_modules:
        print("Error: No test modules found!")
        return False
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    for test_name, test_module in test_modules:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        module_suite = loader.loadTestsFromModule(test_module)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(module_suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        total_skipped += len(result.skipped) if hasattr(result, 'skipped') else 0
        
        print(f"\nResults: {result.testsRun} tests, "
              f"{len(result.failures)} failures, "
              f"{len(result.errors)} errors")
    
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)
    print(f"Total Tests Run: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Skipped: {total_skipped}")
    
    if total_failures == 0 and total_errors == 0:
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        return False

def run_standalone_tests_only():
    """Run only standalone script tests (no Sublime dependencies)"""
    
    print("=" * 70)
    print("Running Standalone Script Tests Only")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    
    try:
        from tests import test_standalone_script
        suite = loader.loadTestsFromModule(test_standalone_script)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Tests Run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if len(result.failures) == 0 and len(result.errors) == 0:
            print("\n✅ ALL STANDALONE TESTS PASSED!")
            return True
        else:
            print("\n❌ SOME TESTS FAILED")
            return False
            
    except ImportError as e:
        print(f"Error: Could not import test module: {e}")
        return False

def main():
    """Main entry point for test runner"""
    
    import argparse
    parser = argparse.ArgumentParser(description='Run tests for Sublime Sensitive Text Hider')
    parser.add_argument('--standalone', action='store_true', 
                       help='Run only standalone script tests (no Sublime dependencies)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.standalone:
        success = run_standalone_tests_only()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()