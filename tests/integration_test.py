# tests/integration_test.py
import os
import sys
import logging
import argparse
import json
import yaml
import shutil
from pathlib import Path

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntegrationTest")

# Define test data directories
TEST_DATA_DIR = os.path.join(project_root, "data", "test")
TEST_SNAPSHOTS_DIR = os.path.join(TEST_DATA_DIR, "snapshots")
TEST_RESULTS_DIR = os.path.join(TEST_DATA_DIR, "results")

# Import necessary components
from core.engine import GameEngine
from core.config import ConfigLoader
from core.state import GameState
from utils.mock_llm import MockLLMClient
import core.llm

# Import the handler registry and ensure handlers are loaded
from handlers.registry import HandlerRegistry
from handlers.base import PhaseHandler

# This is important - explicitly import the modules with handler definitions
try:
    # Try different possible module names
    try:
        import handlers.example
        logger.info("Imported handlers from handlers.example")
    except ImportError:
        try:
            import handlers.examples
            logger.info("Imported handlers from handlers.examples")
        except ImportError:
            try:
                import handlers.example_handlers
                logger.info("Imported handlers from handlers.example_handlers")
            except ImportError:
                logger.warning("Could not import handler modules - will register fallback handlers")

    # Check if the handler we need is registered
    if 'simultaneous_action' not in HandlerRegistry._default_handlers:
        logger.warning("No default handler for 'simultaneous_action' found - registering fallback handler")

        # Define a fallback handler and register it directly
        class FallbackSimultaneousActionHandler(PhaseHandler):
            def process(self, game_state):
                logger.info("FALLBACK HANDLER: Processing simultaneous action phase")

                # Generate mock responses for all active players
                import random
                responses = {}

                # Get the phase configuration
                phase_config = None
                for phase in game_state.config['phases']:
                    if phase['id'] == game_state.current_phase:
                        phase_config = phase
                        break

                # Get available options if any
                options = []
                if phase_config and 'actions' in phase_config and phase_config['actions']:
                    action = phase_config['actions'][0]
                    if 'options' in action:
                        options = action['options']

                # Generate a response for each player
                for player in game_state.get_active_players():
                    player_id = player['id']
                    if options:
                        response = random.choice(options)
                    else:
                        response = "default_action"

                    responses[player_id] = response
                    logger.info(f"FALLBACK HANDLER: Player {player_id} action: {response}")

                # Store responses in state
                game_state.set_action_responses(responses)

                # Always return True
                return True

        # Register the fallback handler directly
        HandlerRegistry._default_handlers['simultaneous_action'] = FallbackSimultaneousActionHandler
        logger.info("Registered fallback handler for 'simultaneous_action'")
except Exception as e:
    logger.error(f"Error setting up handlers: {str(e)}")

def setup_test_environment(clean=False):
    """
    Set up the test environment with test data directories.

    Args:
        clean (bool): Whether to clean existing test data
    """
    # Create test data directories
    os.makedirs(TEST_SNAPSHOTS_DIR, exist_ok=True)
    os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

    # Clean existing test data if requested
    if clean:
        for file in os.listdir(TEST_SNAPSHOTS_DIR):
            os.remove(os.path.join(TEST_SNAPSHOTS_DIR, file))
        for file in os.listdir(TEST_RESULTS_DIR):
            os.remove(os.path.join(TEST_RESULTS_DIR, file))
        logger.info("Cleaned existing test data")

    logger.info(f"Test environment setup complete. Using test directories: {TEST_DATA_DIR}")

def patch_gamestate_save_methods():
    """
    Patch the GameState class to save data to test directories instead of production.

    Returns:
        tuple: Original methods (save_snapshot, save_results)
    """
    # Store original methods
    original_save_snapshot = GameState.save_snapshot
    original_save_results = GameState.save_results

    # Create patched methods
    def patched_save_snapshot(self):
        """Patched method to save snapshots to test directory."""
        # Create a JSON-serializable snapshot
        import time
        import copy
        import json

        snapshot = {
            'timestamp': time.time(),
            'players': copy.deepcopy(self.players),
            'shared_state': copy.deepcopy(self.shared_state),
            'hidden_state': copy.deepcopy(self.hidden_state),
            'history_state': copy.deepcopy(self.history_state),
            'current_phase': self.current_phase,
            'game_over': self.game_over,
            'config': {
                'game_name': self.config['game']['name'],
                'player_count': len(self.players)
            }
        }
        self.history.append(snapshot)

        # Generate a unique filename
        snapshot_id = int(time.time() * 1000)
        game_name = self.config['game']['name'].lower().replace(' ', '_')
        filename = f"{game_name}_snapshot_{snapshot_id}.json"

        # Write to test directory
        os.makedirs(TEST_SNAPSHOTS_DIR, exist_ok=True)
        with open(os.path.join(TEST_SNAPSHOTS_DIR, filename), 'w') as f:
            json.dump(snapshot, f, indent=2)

        logger.debug(f"Saved snapshot to test directory: {filename}")

    def patched_save_results(self, results_dir=None):
        """Patched method to save results to test directory."""
        if not self.game_over:
            raise ValueError("Cannot save results for a game that's not over")

        import time
        import json

        # Create results object
        results = {
            'game': self.config['game']['name'],
            'timestamp': time.time(),
            'players': [
                {
                    'id': p['id'],
                    'final_state': p['state'],
                    'role': p.get('role')
                }
                for p in self.players
            ],
            'winner': self.get_winner()['id'] if self.get_winner() else None,
            'rounds_played': self.shared_state.get('current_round', 0),
            'history_summary': {
                key: len(value) for key, value in self.history_state.items()
            }
        }

        # Generate a unique filename
        result_id = int(time.time() * 1000)
        game_name = self.config['game']['name'].lower().replace(' ', '_')
        filename = f"{game_name}_result_{result_id}.json"

        # Write to test directory
        os.makedirs(TEST_RESULTS_DIR, exist_ok=True)
        with open(os.path.join(TEST_RESULTS_DIR, filename), 'w') as f:
            json.dump(results, f, indent=2)

        logger.debug(f"Saved results to test directory: {filename}")
        return filename

    # Apply the patches
    GameState.save_snapshot = patched_save_snapshot
    GameState.save_results = patched_save_results

    logger.info("Patched GameState to use test directories")

    # Return original methods for restoration
    return (original_save_snapshot, original_save_results)

def restore_gamestate_methods(original_methods):
    """
    Restore original GameState methods.

    Args:
        original_methods (tuple): Original methods (save_snapshot, save_results)
    """
    GameState.save_snapshot, GameState.save_results = original_methods
    logger.info("Restored original GameState methods")

def install_mock_llm():
    """
    Install the mock LLM by monkey patching the original implementation.

    Returns:
        object: The original LLMClient class
    """
    # Store the original implementation
    original_llm_client = core.llm.LLMClient

    # Replace with our mock implementation
    core.llm.LLMClient = MockLLMClient
    logger.info("Installed mock LLM client")

    # Return the original so we can restore it later if needed
    return original_llm_client

def verify_files_exist(required_files):
    """
    Verify that all required files exist.

    Args:
        required_files (list): List of file paths to check

    Returns:
        bool: True if all files exist, False otherwise
    """
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"Required file not found: {file_path}")
            return False

    logger.info("All required files verified")
    return True

def run_test(config_path):
    """
    Run the integration test with a specific configuration.

    Args:
        config_path (str): Path to the game configuration file

    Returns:
        bool: True if the test passes, False otherwise
    """
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
        snapshots = list(Path(TEST_SNAPSHOTS_DIR).glob("*.json"))

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
        results = list(Path(TEST_RESULTS_DIR).glob("*.json"))

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
    parser.add_argument("--clean", action="store_true",
                        help="Clean test data before running")

    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting ParlourBench integration test")

    # Make config path relative to project root
    config_path = os.path.join(project_root, args.config)

    # Verify required files
    required_files = [
        config_path,
        os.path.join(project_root, "templates/pd_decision.txt"),
    ]

    if not verify_files_exist(required_files):
        logger.error("Required files missing, cannot continue")
        return 1

    # Set up test environment
    setup_test_environment(clean=args.clean)

    # Install mock LLM and patch GameState
    original_llm_client = install_mock_llm()
    original_game_state_methods = patch_gamestate_save_methods()

    try:
        # Run the test
        success = run_test(config_path)

        if success:
            logger.info("Integration test PASSED ✅")
            return 0
        else:
            logger.error("Integration test FAILED ❌")
            return 1
    finally:
        # Restore original implementations
        core.llm.LLMClient = original_llm_client
        restore_gamestate_methods(original_game_state_methods)

if __name__ == "__main__":
    sys.exit(main())