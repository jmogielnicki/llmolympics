# test_integration.py
import os
import sys
import logging
import argparse
import json
import yaml
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntegrationTest")

# Make sure the current directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary components
from core.engine import GameEngine
from core.config import ConfigLoader
from core.state import GameState
from utils.mock_llm import MockLLMClient
import core.llm

def setup_test_environment():
    """Set up the test environment with required directories."""
    # Create necessary directories
    os.makedirs("config/games", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("data/snapshots", exist_ok=True)
    os.makedirs("data/results", exist_ok=True)

    logger.info("Test environment set up")

def install_mock_llm():
    """Install the mock LLM by monkey patching the original implementation."""
    # Replace the original LLMClient with our MockLLMClient
    core.llm.LLMClient = MockLLMClient
    logger.info("Installed mock LLM client")

def verify_files_exist(required_files):
    """Verify that all required files exist."""
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"Required file not found: {file_path}")
            return False

    logger.info("All required files verified")
    return True

def run_test(config_path):
    """Run the integration test with a specific configuration."""
    logger.info(f"Running integration test with config: {config_path}")

    try:
        # Initialize and run the game
        engine = GameEngine(config_path)
        engine.run_game()

        # Check if game completed
        if not engine.state.game_over:
            logger.error("Game did not complete properly")
            return False

        # Check if snapshots were created
        snapshots_dir = Path("data/snapshots")
        snapshots = list(snapshots_dir.glob("*.json"))

        if not snapshots:
            logger.error("No snapshots were created")
            return False

        logger.info(f"Found {len(snapshots)} snapshots")

        # Examine the last snapshot for results
        latest_snapshot = max(snapshots, key=os.path.getmtime)
        with open(latest_snapshot, 'r') as f:
            final_state = json.load(f)

        logger.info(f"Final game state: phase={final_state['current_phase']}, game_over={final_state['game_over']}")

        # Check for results file
        results_dir = Path("data/results")
        results = list(results_dir.glob("*.json"))

        if not results:
            logger.error("No results file was created")
            return False

        logger.info(f"Found {len(results)} results files")

        # Examine the results
        latest_result = max(results, key=os.path.getmtime)
        with open(latest_result, 'r') as f:
            result_data = json.load(f)

        logger.info(f"Game result: winner={result_data['winner']}")
        logger.info(f"Player states: {[{'id': p['id'], 'score': p['final_state'].get('score', 'N/A')} for p in result_data['players']]}")

        # Test passed successfully
        logger.info("Integration test completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point for the integration test."""
    parser = argparse.ArgumentParser(description="Run integration tests for ParlourBench")
    parser.add_argument("--config", default="config/games/prisoners_dilemma.yaml",
                        help="Path to the game configuration file")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting ParlourBench integration test")

    # Setup test environment
    setup_test_environment()

    # Install mock LLM
    install_mock_llm()

    # Verify required files
    required_files = [
        args.config,
        "templates/pd_decision.txt",
    ]

    if not verify_files_exist(required_files):
        logger.error("Required files missing, cannot continue")
        return 1

    # Run the test
    success = run_test(args.config)

    if success:
        logger.info("Integration test PASSED ✅")
        return 0
    else:
        logger.error("Integration test FAILED ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())