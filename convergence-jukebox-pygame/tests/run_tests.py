"""
Test Runner - Execute all tests and generate report
"""

import unittest
import sys
import os
from io import StringIO
import time


def run_all_tests(verbosity=2):
    """Run all tests and return results"""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=verbosity)
    start_time = time.time()
    result = runner.run(suite)
    elapsed_time = time.time() - start_time

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Time elapsed: {elapsed_time:.2f}s")
    print("="*70)

    # Print detailed failure/error info if any
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)

    return result


def run_specific_test(test_module, test_class=None, test_method=None):
    """Run a specific test"""
    if test_class and test_method:
        suite = unittest.TestSuite()
        suite.addTest(getattr(
            __import__(f'test_{test_module}', fromlist=[test_class]),
            test_class
        )(test_method))
    elif test_class:
        suite = unittest.TestLoader().loadTestsFromName(
            f'test_{test_module}.{test_class}'
        )
    else:
        suite = unittest.TestLoader().loadTestsFromName(f'test_{test_module}')

    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--specific':
            # Run specific test: python run_tests.py --specific module [class] [method]
            if len(sys.argv) >= 3:
                module = sys.argv[2]
                test_class = sys.argv[3] if len(sys.argv) > 3 else None
                test_method = sys.argv[4] if len(sys.argv) > 4 else None
                run_specific_test(module, test_class, test_method)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Usage: python run_tests.py [--specific module [class] [method]]")
    else:
        result = run_all_tests()
        sys.exit(0 if result.wasSuccessful() else 1)
