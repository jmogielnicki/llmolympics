import pytest
import os
import yaml
import logging
import time
from pathlib import Path

from tests.validation.snapshot import compare_with_snapshot, update_snapshot
from tests.validation.assertions import validate_assertions
import core.game.handlers.common  # Import handlers to ensure they are registered


logger = logging.getLogger("BenchmarkTest")

def test_benchmark(mock_llm, deterministic_environment, update_snapshots):
    """
    Run a benchmark test with mock LLM responses and deterministic environment.

    This test runs complete benchmarks end-to-end, verifying that the output
    matches the expected snapshot.

    Args:
        mock_llm: Mock LLM client (fixture)
        deterministic_environment: Deterministic environment (fixture)
        update_snapshots: Flag to update snapshots instead of comparing (fixture)
    """
    # Get the test configuration from the mock_llm
    config_path = mock_llm.test_config_path

    # Load the test configuration
    with open(config_path, 'r') as f:
        test_config = yaml.safe_load(f)

    # Extract key paths from test configuration
    benchmark_config_path = test_config['benchmark_config']

    logger.info(f"Running benchmark test with config: {benchmark_config_path}")

    # Import here to use the patched environment
    from core.benchmark.config import BenchmarkConfig
    from core.benchmark.runner import BenchmarkRunner

    # Initialize the benchmark
    benchmark_config = BenchmarkConfig(benchmark_config_path)

    # Initialize the runner
    runner = BenchmarkRunner(benchmark_config)

    # Run the benchmark
    start_time = time.time()
    runner.run_benchmark()
    elapsed_time = time.time() - start_time

    logger.info(f"Benchmark execution completed in {elapsed_time:.2f} seconds")

    # Get output directory
    output_dir = benchmark_config.get_output_dir()
    logger.info(f"Benchmark output directory: {output_dir}")

    # Determine validation method
    validation_config = test_config.get('validation', {})
    validation_type = validation_config.get('type', 'snapshot')

    if validation_type == 'snapshot':
        # Get expected output directory
        expected_dir = validation_config.get('snapshot_dir')
        if not expected_dir:
            # Default to a directory next to the test config
            test_config_dir = os.path.dirname(config_path)
            expected_dir = os.path.join(test_config_dir, "expected")

        logger.info(f"Validating against snapshot at: {expected_dir}")

        # Validate or update snapshot
        success, message = compare_with_snapshot(output_dir, expected_dir, update=update_snapshots)

        if not success and not update_snapshots:
            pytest.fail(message)
        else:
            logger.info(message)

    elif validation_type == 'assertion':
        # Get assertions
        assertions = validation_config.get('assertions', [])

        if not assertions:
            pytest.fail("No assertions specified in validation configuration")

        logger.info(f"Validating with {len(assertions)} assertions")

        # Validate assertions
        success, message = validate_assertions(output_dir, assertions)

        if not success:
            pytest.fail(message)
        else:
            logger.info(message)

    else:
        pytest.fail(f"Unsupported validation type: {validation_type}")

    # Test passes if we reach here
    assert True