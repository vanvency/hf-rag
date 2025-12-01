#!/usr/bin/env python
"""
Run document processing and query test suite.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Run the test suite with progress reporting."""
    print("=" * 70)
    print("RAG System Test Suite")
    print("=" * 70)
    print()
    
    # Test files to run
    test_files = [
        "tests/test_document_processing.py",
        "tests/test_document_query.py",
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_file in test_files:
        print(f"\n{'=' * 70}")
        print(f"Running: {test_file}")
        print(f"{'=' * 70}\n")
        
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--color=yes",
            ],
            capture_output=False,
        )
        
        if result.returncode == 0:
            total_passed += 1
            print(f"\n✅ {test_file} - PASSED")
        else:
            total_failed += 1
            print(f"\n❌ {test_file} - FAILED")
    
    print("\n" + "=" * 70)
    print("Test Suite Summary")
    print("=" * 70)
    print(f"Total test files: {len(test_files)}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print("=" * 70)
    
    if total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

