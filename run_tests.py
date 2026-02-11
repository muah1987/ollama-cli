#!/usr/bin/env python3
"""
Test runner for ollama-cli unit tests.
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run all unit tests with pytest."""
    test_dir = Path(__file__).parent / "tests"
    
    if not test_dir.exists():
        print(f"Error: Test directory not found at {test_dir}")
        return 1
        
    # Run pytest on the tests directory
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir),
            "-v",
            "--tb=short"
        ], cwd=test_dir.parent)
        
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install pytest:")
        print("  pip install pytest")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
