#!/usr/bin/env python3
"""
Test Runner - Run All Scaling Tests
====================================
Runs all test suites and provides comprehensive validation.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all test modules
from test_scaling_with_frontmatter import run_all_tests as run_unit_tests
from test_scaling_validation import run_all_validation_tests as run_validation_tests
from test_scaling_visual_validation import run_visual_tests as run_visual_tests
from test_reporting_manager_layout import run_reporting_manager_visual_test

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HEADER = f"{Fore.CYAN}{Style.BRIGHT}"
    OK = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
    FAIL = f"{Fore.RED}[FAIL]{Style.RESET_ALL}"
    RESET = Style.RESET_ALL
except ImportError:
    HEADER = ""
    OK = "[OK]"
    FAIL = "[FAIL]"
    RESET = ""


async def main():
    """Run all test suites"""
    print(f"\n{HEADER}{'='*70}")
    print("COMPREHENSIVE SCALING TEST SUITE")
    print("="*70 + RESET)
    
    results = {}
    
    # Run unit tests
    print(f"\n{HEADER}[1/3] Unit Tests (Front Matter Logic){RESET}")
    print("-" * 70)
    try:
        results['unit'] = await run_unit_tests()
    except Exception as e:
        print(f"{FAIL} Unit tests failed: {e}")
        results['unit'] = False
    
    # Run validation tests
    print(f"\n{HEADER}[2/3] Validation Tests (Measurement Accuracy){RESET}")
    print("-" * 70)
    try:
        results['validation'] = await run_validation_tests()
    except Exception as e:
        print(f"{FAIL} Validation tests failed: {e}")
        results['validation'] = False
    
    # Run visual tests
    print(f"\n{HEADER}[3/4] Visual Tests (PDF Generation){RESET}")
    print("-" * 70)
    try:
        results['visual'] = await run_visual_tests()
    except Exception as e:
        print(f"{FAIL} Visual tests failed: {e}")
        results['visual'] = False
    
    # Reporting Manager doc-specific test
    print(f"\n{HEADER}[4/4] Reporting Manager Layout (Document-Specific){RESET}")
    print("-" * 70)
    try:
        results['reporting_manager'] = await run_reporting_manager_visual_test()
    except Exception as e:
        print(f"{FAIL} Reporting Manager layout test failed: {e}")
        results['reporting_manager'] = False
    
    # Final summary
    print(f"\n{HEADER}{'='*70}")
    print("FINAL TEST SUMMARY")
    print("="*70 + RESET)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, result in results.items():
        status = OK if result else FAIL
        print(f"  {name.capitalize():15} {status}")
    
    print(f"\n  Total: {passed}/{total} test suites passed")
    
    if passed == total:
        print(f"\n{OK} All test suites passed! Scaling logic is working correctly.")
        print(f"\n{HEADER}Next Steps:{RESET}")
        print("  1. Review generated PDFs in tests/test_outputs/")
        print("  2. Test with your actual documents")
        print("  3. Verify diagrams scale appropriately")
        return True
    else:
        print(f"\n{FAIL} Some test suites failed. Review output above.")
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

