import pytest
import os
import yaml
import logging
import time
from pathlib import Path

from tests.validation.snapshot import compare_with_snapshot, update_snapshot
from tests.validation.assertions import validate_assertions
import core.game.handlers.common  # Import handlers to ensure they are registered


logger = logging.getLogger("GameTest")

def test_game(mock_llm, deterministic_environment, update_snapshots):
    """
    Run a single game test with mock LLM responses and deterministic environment.

    This test runs individual games end-to-end, verifying that the output
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
    game_config_path = test_config.get('game_config')

    if not game_config_path:
        # If no game_config specified, use the benchmark's base_config
        if 'benchmark_config' in test_config:
            benchmark_config_path = test_config['benchmark_config']
            with open(benchmark_config_path, 'r') as f:
                benchmark_config = yaml.safe_load(f)
                if 'benchmark' in benchmark_config and 'base_config' in benchmark_config['benchmark']:
                    game_config_path = benchmark_config['benchmark']['base_config']

    if not game_config_path:
        pytest.fail("No game_config found in test configuration or related benchmark config")

    logger.info(f"Running game test with config: {game_config_path}")

    # Import here to use the patched environment
    from core.game.engine import GameEngine

    # Set output directory
    output_dir = test_config.get('output_dir', 'data/test_output')
    os.makedirs(output_dir, exist_ok=True)

    # Initialize the game engine
    engine = GameEngine(game_config_path, base_output_dir=output_dir)

    # Run the game
    start_time = time.time()
    engine.run_game()
    elapsed_time = time.time() - start_time

    logger.info(f"Game execution completed in {elapsed_time:.2f} seconds")

    # Get session directory
    session_dir = engine.game_session.session_dir
    logger.info(f"Game session directory: {session_dir}")

    # Determine validation method
    validation_config = test_config.get('validation', {})
    validation_type = validation_config.get('type', 'snapshot')

    if validation_type == 'snapshot':
        # Get expected output directory
        expected_dir = validation_config.get('snapshot_dir')
        if not expected_dir:
            # Default to a directory next to the test config
            test_config_dir = os.path.dirname(config_path)
            expected_dir = os.path.join(test_config_dir, "expected_game")

        logger.info(f"Validating against snapshot at: {expected_dir}")

        # Validate or update snapshot
        success, message = compare_with_snapshot(session_dir, expected_dir, update=update_snapshots)

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

        # For single games, validate assertions on the session directory
        success, message = validate_assertions(session_dir, assertions)

        if not success:
            pytest.fail(message)
        else:
            logger.info(message)

    else:
        pytest.fail(f"Unsupported validation type: {validation_type}")

    # Verify game completed successfully
    assert engine.state.is_game_over(), "Game did not complete"

    # Test passes if we reach here
    assert True