#!/usr/bin/env python
"""
Run ParlourBench integration tests.

This script provides a convenient way to run the integration tests
with various options and filters.
"""

import os
import sys
import argparse
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RunTests")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run ParlourBench integration tests.")

    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--benchmarks", action="store_true", help="Run all benchmark tests")
    parser.add_argument("--games", action="store_true", help="Run all game tests")
    parser.add_argument("--benchmark", type=str, help="Run a specific benchmark test")
    parser.add_argument("--game", type=str, help="Run a specific game test")
    parser.add_argument("--update-snapshots", action="store_true", help="Update test snapshots")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--create", type=str, help="Create a new test (benchmark:name or game:name)")
    parser.add_argument("--models", nargs="+", default=["openai:gpt-4o", "anthropic:claude-3-7-sonnet"],
                       help="Models to include in mock responses when creating a test")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with PDB")

    return parser.parse_args()

def run_tests(args):
    """Run tests based on command line arguments."""
    # Determine pytest command and arguments
    pytest_cmd = ["pytest"]

    # Determine test targets
    if args.all:
        pytest_cmd.append("tests/")
    elif args.benchmarks:
        pytest_cmd.append("tests/test_benchmarks.py")
    elif args.games:
        pytest_cmd.append("tests/test_games.py")
    elif args.benchmark:
        pytest_cmd.extend(["tests/test_benchmarks.py", f"--benchmark={args.benchmark}"])
    elif args.game:
        pytest_cmd.extend(["tests/test_games.py", f"--game={args.game}"])
    else:
        # Default to running all tests
        pytest_cmd.append("tests/")

    # Add optional arguments
    if args.update_snapshots:
        pytest_cmd.append("--update-snapshots")

    if args.verbose:
        pytest_cmd.extend(["-v", "--log-cli-level=INFO"])

    if args.debug:
        pytest_cmd.extend(["--pdb", "--no-header"])

    # Run the tests
    logger.info(f"Running tests with command: {' '.join(pytest_cmd)}")
    result = subprocess.run(pytest_cmd)

    return result.returncode

def create_test(args):
    """Create a new test using the helper script."""
    if not args.create:
        logger.error("Must specify --create argument")
        return 1

    # Parse the create argument (format: type:name)
    try:
        test_type, test_name = args.create.split(":")
        if test_type not in ["benchmark", "game"]:
            logger.error(f"Invalid test type: {test_type}. Must be 'benchmark' or 'game'")
            return 1
    except ValueError:
        logger.error("Invalid --create format. Use 'benchmark:name' or 'game:name'")
        return 1

    # Build the command
    create_cmd = ["python", "tests/create_test.py", f"--{test_type}", test_name]

    # Add models if specified
    if args.models:
        create_cmd.append("--models")
        create_cmd.extend(args.models)

    # Run the command
    logger.info(f"Creating new test with command: {' '.join(create_cmd)}")
    result = subprocess.run(create_cmd)

    return result.returncode

def main():
    """Main entry point."""
    args = parse_args()

    # Check if we need to create a test
    if args.create:
        return create_test(args)

    # Otherwise run tests
    return run_tests(args)

if __name__ == "__main__":
    sys.exit(main())