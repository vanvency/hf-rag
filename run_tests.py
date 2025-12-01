#!/usr/bin/env python
"""
Test runner script for RAG system tests.
"""
import sys
import subprocess
from pathlib import Path


def main():
    """Run tests with appropriate options."""
    test_dir = Path(__file__).parent / "tests"
    
    # Default test arguments
    args = [
        "python", "-m", "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
        "--color=yes",
    ]
    
    # Add any command line arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    else:
        # Default: run all tests
        print("Running all tests...")
        print("Use --help to see available options")
        print("Examples:")
        print("  python run_tests.py tests/test_document_processing.py")
        print("  python run_tests.py tests/test_document_query.py -k test_vector_search")
        print("  python run_tests.py -m 'not slow'  # Skip slow tests")
        print()
    
    result = subprocess.run(args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

