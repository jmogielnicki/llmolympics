# tests/integration_test.py
import os
import sys
import logging
import argparse
import json
import yaml
import shutil
import glob
from pathlib import Path
from datetime import datetime

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


# Define deterministic expected test outcomes for different games
# Based on the fixed responses in the MockLLMClient
EXPECTED_OUTCOMES = {
    "prisoner's dilemma": {
        # For a 5-round game with deterministic responses
        "exact_snapshots": 11,  # Initial + (decision + resolution) * 5
        "rounds_played": 5,
        "player_scores": {
            "player_1": 8,  # 3+3+0+1+1 = 8
            "player_2": 13   # 3+3+5+1+1 = 13
        },
        "expected_winner": "player_2",  # Player 2 has higher score
        "phases": ["decision", "resolution"],
        "expected_phase_counts": {
            "decision": 5,   # One per round
            "resolution": 5  # One per round
        },
        "expected_decisions": {
            # Round 1: Both cooperate
            1: {"player_1": "cooperate", "player_2": "cooperate"},
            # Round 2: Both cooperate
            2: {"player_1": "cooperate", "player_2": "cooperate"},
            # Round 3: P1 cooperates, P2 defects
            3: {"player_1": "cooperate", "player_2": "defect"},
            # Round 4: Both defect
            4: {"player_1": "defect", "player_2": "defect"},
            # Round 5: Both defect
            5: {"player_1": "defect", "player_2": "defect"}
        }
    },
    "diplomacy": {
        # For a 6-player game with elimination
        "min_snapshots": 15,  # At least 3 per elimination round
        "max_snapshots": 50,  # Upper bound
        "min_players_eliminated": 5,  # All but winner should be eliminated
        "phases": ["discussion", "voting", "elimination", "check_win_condition"],
        "expected_eliminations": ["player_3", "player_1", "player_5", "player_4", "player_2"],
        "expected_winner": "player_6"  # Last player standing
    },
    # Add other games as needed
}


def setup_test_environment(clean=True):
    """
    Set up the test environment with test data directories.

    Args:
        clean (bool): Whether to clean existing test data
    """
    # Create test data directories
    os.makedirs(TEST_SNAPSHOTS_DIR, exist_ok=True)
    os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

    # Clean existing test data
    if clean:
        for file in glob.glob(os.path.join(TEST_SNAPSHOTS_DIR, "*.json")):
            os.remove(file)
        for file in glob.glob(os.path.join(TEST_RESULTS_DIR, "*.json")):
            os.remove(file)
        logger.info("Cleaned existing test data")

    # Set environment variables for test
    os.environ["PARLOURBENCH_SNAPSHOT_DIR"] = TEST_SNAPSHOTS_DIR
    os.environ["PARLOURBENCH_RESULTS_DIR"] = TEST_RESULTS_DIR
    os.environ["PARLOURBENCH_USE_MOCK"] = "1"

    logger.info(f"Test environment setup complete. Using test directories: {TEST_DATA_DIR}")

    # This is important - explicitly import the modules with handler definitions
    try:
        import handlers.common
        logger.info("Imported handlers from handlers.common")

    except Exception as e:
        logger.error(f"Error setting up handlers: {str(e)}")


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

def verify_test_results(game_name, snapshots, results_file):
    """
    Verify that test results meet expected conditions.

    Args:
        game_name (str): Name of the game
        snapshots (list): List of snapshot file paths
        results_file (str): Path to the results file

    Returns:
        tuple: (bool, list) - Success flag and list of test results
    """
    # Normalize game name for lookup
    game_key = None
    for key in EXPECTED_OUTCOMES.keys():
        if key.lower() in game_name.lower():
            game_key = key
            break

    if not game_key:
        logger.warning(f"No expected outcomes defined for game: {game_name}")
        return False, [f"UNKNOWN: No expected outcomes for {game_name}"]

    expected = EXPECTED_OUTCOMES[game_key]
    test_results = []
    all_passed = True

    # Load the results file
    with open(results_file, 'r') as f:
        result_data = json.load(f)

    # Test 1: Number of snapshots (exact or range)
    snapshot_count = len(snapshots)
    if "exact_snapshots" in expected:
        if snapshot_count != expected["exact_snapshots"]:
            test_results.append(f"FAIL: Incorrect snapshot count. Expected exactly {expected['exact_snapshots']}, got {snapshot_count}")
            all_passed = False
        else:
            test_results.append(f"PASS: Snapshot count exactly {snapshot_count} as expected")
    elif "min_snapshots" in expected and "max_snapshots" in expected:
        if snapshot_count < expected["min_snapshots"]:
            test_results.append(f"FAIL: Too few snapshots. Expected at least {expected['min_snapshots']}, got {snapshot_count}")
            all_passed = False
        elif snapshot_count > expected["max_snapshots"]:
            test_results.append(f"FAIL: Too many snapshots. Expected at most {expected['max_snapshots']}, got {snapshot_count}")
            all_passed = False
        else:
            test_results.append(f"PASS: Snapshot count ({snapshot_count}) within expected range")

    # Test 2: Rounds played (for games with fixed rounds)
    if "rounds_played" in expected:
        actual_rounds = result_data.get("rounds_played", 0)
        if actual_rounds != expected["rounds_played"]:
            test_results.append(f"FAIL: Incorrect number of rounds. Expected {expected['rounds_played']}, got {actual_rounds}")
            all_passed = False
        else:
            test_results.append(f"PASS: Completed the expected {actual_rounds} rounds")

    # Test 3: Player scores (exact deterministic values)
    if "player_scores" in expected:
        player_map = {p['id']: p.get('final_state', {}).get('score', 0) for p in result_data.get('players', [])}

        for player_id, expected_score in expected["player_scores"].items():
            actual_score = player_map.get(player_id, None)
            if actual_score is None:
                test_results.append(f"FAIL: Player {player_id} not found in results")
                all_passed = False
            elif actual_score != expected_score:
                test_results.append(f"FAIL: Player {player_id} score incorrect. Expected {expected_score}, got {actual_score}")
                all_passed = False
            else:
                test_results.append(f"PASS: Player {player_id} has correct score of {actual_score}")

    # Test 4: Winner determination
    if "expected_winner" in expected:
        winner_id = result_data.get("winner")
        if winner_id != expected["expected_winner"]:
            test_results.append(f"FAIL: Incorrect winner. Expected {expected['expected_winner']}, got {winner_id}")
            all_passed = False
        else:
            test_results.append(f"PASS: Correct winner {winner_id}")

    # Test 5: Phase progression (check snapshots for phase sequence)
    if snapshots and "phases" in expected:
        # Load all snapshots and analyze phase progression
        phase_counts = {}
        phase_sequence = []

        # Sort snapshots by timestamp
        sorted_snapshots = sorted(snapshots, key=os.path.getmtime)

        for snapshot_file in sorted_snapshots:
            with open(snapshot_file, 'r') as f:
                snapshot = json.load(f)
                phase = snapshot.get("current_phase")
                if phase:
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1
                    phase_sequence.append(phase)

        # Check that all expected phases were encountered
        missing_phases = [p for p in expected["phases"] if p not in phase_counts]
        if missing_phases:
            test_results.append(f"FAIL: Missing expected phases: {missing_phases}")
            all_passed = False
        else:
            test_results.append(f"PASS: All expected phases encountered")

        # Check phase counts if specified
        if "expected_phase_counts" in expected:
            for phase, expected_count in expected["expected_phase_counts"].items():
                actual_count = phase_counts.get(phase, 0)
                if actual_count != expected_count:
                    test_results.append(f"FAIL: Phase '{phase}' count incorrect. Expected {expected_count}, got {actual_count}")
                    all_passed = False
                else:
                    test_results.append(f"PASS: Phase '{phase}' occurred expected {actual_count} times")

    # Test 6: Check for eliminated players (for elimination games)
    if "min_players_eliminated" in expected:
        active_count = 0
        eliminated_count = 0

        for player in result_data.get("players", []):
            if player.get("final_state", {}).get("active", True):
                active_count += 1
            else:
                eliminated_count += 1

        if eliminated_count < expected["min_players_eliminated"]:
            test_results.append(f"FAIL: Too few players eliminated. Expected at least {expected['min_players_eliminated']}, got {eliminated_count}")
            all_passed = False
        else:
            test_results.append(f"PASS: {eliminated_count} players eliminated (expected at least {expected['min_players_eliminated']})")

    # Test 7: Check elimination order (for games with elimination sequence)
    if "expected_eliminations" in expected and snapshots:
        # We'd need to extract the elimination order from history snapshots
        # This is more complex and might require game-specific logic
        # For now, just note that this check would be performed
        test_results.append(f"INFO: Elimination order check not implemented yet")

    return all_passed, test_results

def run_test(config_path):
    """
    Run the integration test with a specific configuration.

    Args:
        config_path (str): Path to the game configuration file

    Returns:
        bool: True if the test passes, False otherwise
    """
    logger.info(f"Running integration test with config: {config_path}")
    from core.engine import GameEngine
    try:
        # Load the config to get the game name
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        game_name = config.get('game', {}).get('name', 'Unknown Game')
        logger.info(f"Testing game: {game_name}")

        # Initialize and run the game
        engine = GameEngine(config_path)
        start_time = datetime.now()
        engine.run_game()
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        logger.info(f"Game execution completed in {elapsed:.2f} seconds")

        # Check if game completed
        if not engine.state.game_over:
            logger.error("Game did not complete properly")
            return False

        # Get snapshots
        snapshots = sorted(glob.glob(os.path.join(TEST_SNAPSHOTS_DIR, "*.json")))

        if not snapshots:
            logger.error("No snapshots were created")
            return False

        logger.info(f"Found {len(snapshots)} snapshots")

        # Get results
        results = sorted(glob.glob(os.path.join(TEST_RESULTS_DIR, "*.json")))

        if not results:
            logger.error("No results file was created")
            return False

        logger.info(f"Found {len(results)} results files")

        # Get the latest result
        latest_result = max(results, key=os.path.getmtime)

        # Verify test outcomes
        success, test_results = verify_test_results(game_name, snapshots, latest_result)

        # Print test results
        logger.info("\n=== Test Results ===")
        for result in test_results:
            if result.startswith("PASS:"):
                logger.info(result)
            elif result.startswith("FAIL:"):
                logger.error(result)
            else:
                logger.warning(result)

        if success:
            logger.info("\nAll test conditions passed!")
        else:
            logger.error("\nSome test conditions failed.")

        return success

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
        # Clean up environment variables
        if "PARLOURBENCH_SNAPSHOT_DIR" in os.environ:
            del os.environ["PARLOURBENCH_SNAPSHOT_DIR"]
        if "PARLOURBENCH_RESULTS_DIR" in os.environ:
            del os.environ["PARLOURBENCH_RESULTS_DIR"]
        if "PARLOURBENCH_USE_MOCK" in os.environ:
            del os.environ["PARLOURBENCH_USE_MOCK"]

if __name__ == "__main__":
    sys.exit(main())