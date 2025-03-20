#!/usr/bin/env python
"""
Helper script for creating new integration tests.

This script creates the necessary directory structure and template files
for a new benchmark or game test.
"""

import os
import sys
import argparse
import shutil
import yaml
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CreateTest")

# Get project root directory
project_root = Path(__file__).parent.parent

# Template content
TEST_CONFIG_TEMPLATE = """name: "{name} Test"
description: "Integration test for {type} {name}"

# Configuration paths
{config_key}: "{config_path}"

# Mock LLM responses
mock_responses:
  - "{response_path}"

# Validation configuration
validation:
  type: "snapshot"
  snapshot_dir: "{expected_dir}"
"""

MOCK_RESPONSE_TEMPLATE = """model: "{model}"
responses:
  # Example responses for the {model} model
  {response_examples}

  # Add more responses as needed
"""

RESPONSE_EXAMPLES_TEMPLATES = {
    "prisoners_dilemma": """- "I'll [[COOPERATE]] to establish trust."
  - "I'll continue to [[COOPERATE]] since they cooperated."
  - "Let me try [[DEFECT]] and see how they respond."
  - "Back to [[COOPERATE]] to rebuild trust."
  - "Final round, I'll [[DEFECT]] for maximum points." """,
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Create a new integration test.")
    parser.add_argument("--game", help="Name of the game to test (e.g., prisoners_dilemma)")
    parser.add_argument("--benchmark", help="Name of the benchmark to test (e.g., pd_benchmark)")
    parser.add_argument("--models", nargs="+", default=["openai:gpt-4o", "anthropic:claude-3-7-sonnet"],
                       help="Models to include in mock responses")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--example", choices=list(RESPONSE_EXAMPLES_TEMPLATES.keys()),
                       help="Use specific example response template")
    return parser.parse_args()

def create_directory_structure(test_type, name, force=False):
    """
    Create the necessary directory structure for a test.

    Args:
        test_type (str): Type of test ('game' or 'benchmark')
        name (str): Name of the game or benchmark
        force (bool): Whether to overwrite existing files

    Returns:
        tuple: (test_dir, response_dir) - Paths to test and response directories
    """
    # Determine directories
    test_data_dir = project_root / "tests" / "test_data"
    test_dir = test_data_dir / f"{test_type}s" / name
    response_dir = test_data_dir / "responses" / f"{name}_responses"

    # Create directories
    for directory in [test_dir, response_dir]:
        if os.path.exists(directory) and not force:
            logger.warning(f"Directory already exists: {directory}")
            choice = input(f"Overwrite existing directory? (y/n): ")
            if choice.lower() != 'y':
                logger.info("Aborting")
                sys.exit(1)

        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

    return test_dir, response_dir

def find_original_config(test_type, name):
    """
    Find the original configuration file for a game or benchmark.

    Args:
        test_type (str): Type of test ('game' or 'benchmark')
        name (str): Name of the game or benchmark

    Returns:
        str: Path to the original configuration file, or None if not found
    """
    # Check common locations
    locations = [
        project_root / "config" / f"{test_type}s" / f"{name}.yaml",
        project_root / "config" / f"{test_type}s" / f"{name}_config.yaml",
        project_root / "config" / f"{test_type}s" / f"{name}_benchmark.yaml"
    ]

    for location in locations:
        if os.path.exists(location):
            return str(location)

    return None

def create_test_config(test_dir, test_type, name, config_path, response_dir):
    """
    Create a test configuration file.

    Args:
        test_dir (Path): Test directory
        test_type (str): Type of test ('game' or 'benchmark')
        name (str): Name of the game or benchmark
        config_path (str): Path to the original configuration file
        response_dir (Path): Response directory

    Returns:
        str: Path to the created test configuration file
    """
    # Determine paths
    test_config_path = test_dir / "test_config.yaml"
    expected_dir = test_dir / "expected"

    # Set appropriate configuration key
    if test_type == 'game':
        config_key = "game_config"
    else:
        config_key = "benchmark_config"

    # Create test configuration
    config_content = TEST_CONFIG_TEMPLATE.format(
        name=name,
        type=test_type,
        config_key=config_key,
        config_path=config_path,
        response_path=os.path.join(response_dir, f"model1.yaml"),
        expected_dir=expected_dir
    )

    # Write configuration file
    with open(test_config_path, 'w') as f:
        f.write(config_content)

    logger.info(f"Created test configuration: {test_config_path}")

    return test_config_path

def create_test_config_copy(test_dir, original_config_path, test_type):
    """
    Create a copy of the original configuration for testing.

    Args:
        test_dir (Path): Test directory
        original_config_path (str): Path to the original configuration file
        test_type (str): Type of test ('game' or 'benchmark')

    Returns:
        str: Path to the copied configuration file
    """
    # Determine destination path
    if test_type == 'game':
        dest_path = test_dir / "game_config.yaml"
    else:
        dest_path = test_dir / "benchmark_config.yaml"

    # Copy configuration file
    shutil.copy(original_config_path, dest_path)
    logger.info(f"Copied configuration from {original_config_path} to {dest_path}")

    # Modify the configuration for testing
    try:
        with open(dest_path, 'r') as f:
            config = yaml.safe_load(f)

        # Make test-specific modifications
        if test_type == 'benchmark':
            # Reduce number of games/sessions for faster testing
            if 'benchmark' in config:
                if 'games_per_pair' in config['benchmark']:
                    config['benchmark']['games_per_pair'] = min(2, config['benchmark']['games_per_pair'])
                if 'sessions' in config['benchmark']:
                    config['benchmark']['sessions'] = min(2, config['benchmark']['sessions'])

                # Update output directory
                config['benchmark']['output_dir'] = "data/test_output"

                # Update ID
                config['benchmark']['id'] = f"{config['benchmark']['id']}_test"

        # Write modified configuration
        with open(dest_path, 'w') as f:
            yaml.dump(config, f)

        logger.info(f"Modified configuration for testing")
    except Exception as e:
        logger.warning(f"Failed to modify configuration: {str(e)}")

    return str(dest_path)

def create_mock_responses(response_dir, models, example_type):
    """
    Create mock response files for each model.

    Args:
        response_dir (Path): Response directory
        models (list): List of model identifiers
        example_type (str): Type of example responses to use

    Returns:
        list: Paths to the created response files
    """
    # Get example responses template
    if example_type in RESPONSE_EXAMPLES_TEMPLATES:
        response_examples = RESPONSE_EXAMPLES_TEMPLATES[example_type]
    else:
        response_examples = RESPONSE_EXAMPLES_TEMPLATES['default']

    # Create response files
    response_files = []
    for i, model in enumerate(models, 1):
        response_file = response_dir / f"model{i}.yaml"

        # Create response content
        response_content = MOCK_RESPONSE_TEMPLATE.format(
            model=model,
            response_examples=response_examples
        )

        # Write response file
        with open(response_file, 'w') as f:
            f.write(response_content)

        logger.info(f"Created mock response file for {model}: {response_file}")
        response_files.append(str(response_file))

    return response_files

def main():
    """Main entry point."""
    args = parse_args()

    # Validate arguments
    if not args.game and not args.benchmark:
        logger.error("Must specify either --game or --benchmark")
        sys.exit(1)

    if args.game and args.benchmark:
        logger.error("Cannot specify both --game and --benchmark")
        sys.exit(1)

    # Determine test type and name
    if args.game:
        test_type = 'game'
        name = args.game
    else:
        test_type = 'benchmark'
        name = args.benchmark

    # Create directory structure
    test_dir, response_dir = create_directory_structure(test_type, name, force=args.force)

    # Find original configuration
    original_config_path = find_original_config(test_type, name)
    if not original_config_path:
        logger.warning(f"Could not find original {test_type} configuration for {name}")
        original_config_path = input(f"Enter path to {test_type} configuration file: ")
        if not os.path.exists(original_config_path):
            logger.error(f"Configuration file not found: {original_config_path}")
            sys.exit(1)

    # Create test configuration copy
    config_copy_path = create_test_config_copy(test_dir, original_config_path, test_type)

    # Create test configuration
    test_config_path = create_test_config(test_dir, test_type, name, config_copy_path, response_dir)

    # Determine example type
    example_type = args.example or name
    if example_type not in RESPONSE_EXAMPLES_TEMPLATES:
        logger.warning(f"No example template for {example_type}, using default")
        example_type = 'default'

    # Create mock responses
    response_files = create_mock_responses(response_dir, args.models, example_type)

    # Print instructions
    logger.info("\nTest creation complete!")
    logger.info(f"\nTo run the test:")
    logger.info(f"  pytest tests/test_{test_type}s.py -v --{test_type}={name}")
    logger.info(f"\nTo update snapshots:")
    logger.info(f"  pytest tests/test_{test_type}s.py -v --{test_type}={name} --update-snapshots")
    logger.info(f"\nConfigure your test by editing:")
    logger.info(f"  - Test config: {test_config_path}")
    logger.info(f"  - {test_type.capitalize()} config: {config_copy_path}")
    logger.info(f"  - Mock responses: {', '.join(response_files)}")

if __name__ == "__main__":
    main()