#!/usr/bin/env python3
"""
Script to run tests with proper directory naming.
This temporarily creates a symlink to allow tests to run without breaking HACS.
"""
import os
import subprocess
import sys


def run_tests():
    """Run tests with temporary directory setup."""
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Check if marstek_local_api already exists (symlink)
    symlink_path = os.path.join(project_root, "custom_components", "marstek_local_api")
    symlink_existed = os.path.exists(symlink_path)

    try:
        # Create symlink if it doesn't exist
        if not symlink_existed:
            original_path = os.path.join(
                project_root, "custom_components", "marstek-local-api"
            )
            os.symlink(original_path, symlink_path)
            print("Created temporary symlink for testing")

        # Run pytest with all arguments passed to this script
        pytest_args = ["python", "-m", "pytest"] + sys.argv[1:]
        result = subprocess.run(pytest_args, cwd=project_root)

        return result.returncode

    finally:
        # Clean up symlink if we created it
        if not symlink_existed and os.path.exists(symlink_path):
            os.unlink(symlink_path)
            print("Removed temporary symlink")


if __name__ == "__main__":
    sys.exit(run_tests())
