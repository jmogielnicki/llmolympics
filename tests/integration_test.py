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
TEST_SESSIONS_DIR = os.path.join(TEST_DATA_DIR, "sessions")

# Define deterministic expected test outcomes for different games
# Based on the fixed responses in the MockLLMClient
EXPECTED_OUTCOMES = {
    "prisoner's dilemma": {
        # For a 5-round game with deterministic responses
        "min_snapshots": 10,  # Initial + (decision + resolution) * 5 (now as JSONL entries)
        "rounds_played": 5,
        "player_scores": {
            "player_1": 8,  # 3+3+0+1+1 = 8
            "player_2": 13   # 3+3+5+1+1 = 13
        },
        "expected_winner": {'id': 'player_2'},  # Player 2 has higher score
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
    os.makedirs(TEST_SESSIONS_DIR, exist_ok=True)

    # Clean existing test data
    if clean:
        # Clean session directories but create the parent directory
        shutil.rmtree(TEST_SESSIONS_DIR, ignore_errors=True)
        os.makedirs(TEST_SESSIONS_DIR, exist_ok=True)

        logger.info("Cleaned existing test data")

    # Set environment variables for test
    os.environ["PARLOURBENCH_USE_MOCK"] = "1"

    logger.info(f"Test environment setup complete. Using test directories: {TEST_DATA_DIR}")

    # This is important - explicitly import the modules with handler definitions
    try:
        import handlers.common
        logger.info("Imported handlers from handlers.common")

    except Exception as e:
        logger.error(f"Error setting up handlers: {str(e)}")


def find_latest_session_dir():
    """
    Find the most recently created session directory.

    Returns:
        str: Path to the latest session directory, or None if not found
    """
    session_dirs = glob.glob(os.path.join(TEST_SESSIONS_DIR, "*"))
    if not session_dirs:
        return None

    # Get the most recent directory by modification time
    latest_dir = max(session_dirs, key=os.path.getmtime)
    return latest_dir


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


def load_snapshots_from_jsonl(jsonl_path):
    """
    Load snapshots from a JSONL file.

    Args:
        jsonl_path (str): Path to the JSONL file

    Returns:
        list: List of snapshot dictionaries
    """
    snapshots = []

    try:
        with open(jsonl_path, 'r') as f:
            for line in f:
                record = json.loads(line)
                if record.get('record_type') == 'snapshot':
                    snapshots.append(record)
    except Exception as e:
        logger.error(f"Error loading snapshots from {jsonl_path}: {str(e)}")
        return []

    return snapshots


def load_events_from_jsonl(jsonl_path):
    """
    Load events from a JSONL file.

    Args:
        jsonl_path (str): Path to the JSONL file

    Returns:
        list: List of event dictionaries
    """
    events = []

    try:
        with open(jsonl_path, 'r') as f:
            for line in f:
                record = json.loads(line)
                if record.get('record_type') == 'event':
                    events.append(record)
    except Exception as e:
        logger.error(f"Error loading events from {jsonl_path}: {str(e)}")
        return []

    return events


def verify_test_results(game_name, session_dir, results_file):
    """
    Verify that test results meet expected conditions.

    Args:
        game_name (str): Name of the game
        session_dir (str): Path to the session directory
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

    # Load snapshots from the JSONL file
    snapshots_file = os.path.join(session_dir, "snapshots.jsonl")
    if not os.path.exists(snapshots_file):
        logger.error(f"Snapshots file not found: {snapshots_file}")
        return False, ["FAIL: Snapshots file not found"]

    snapshots = load_snapshots_from_jsonl(snapshots_file)
    events = load_events_from_jsonl(snapshots_file)

    logger.info(f"Loaded {len(snapshots)} snapshots and {len(events)} events from {snapshots_file}")

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

    # Test 5: Phase progression (check events for phase sequence)
    if "phases" in expected:
        # Extract phases from events
        phase_starts = [e for e in events if e.get('event_type') == 'phase_start']
        phase_sequence = [e.get('phase_id') for e in phase_starts]
        phase_counts = {}

        for phase in phase_sequence:
            if phase:
                phase_counts[phase] = phase_counts.get(phase, 0) + 1

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

    # Test 7: Check decisions (for Prisoner's Dilemma)
    if "expected_decisions" in expected:
        # Extract decisions from history
        final_snapshot = snapshots[-1] if snapshots else None
        if final_snapshot:
            decision_history = final_snapshot.get('history_state', {}).get('decision_history', [])

            for expected_round, expected_decisions in expected["expected_decisions"].items():
                # Find the matching round in history
                round_decisions = None
                for entry in decision_history:
                    if entry.get('round') == expected_round:
                        round_decisions = entry.get('decisions', {})
                        break

                if not round_decisions:
                    test_results.append(f"FAIL: Decision history for round {expected_round} not found")
                    all_passed = False
                    continue

                # Check each player's decision
                for player_id, expected_decision in expected_decisions.items():
                    actual_decision = round_decisions.get(player_id)
                    if actual_decision != expected_decision:
                        test_results.append(f"FAIL: Round {expected_round}, Player {player_id} decision incorrect. Expected '{expected_decision}', got '{actual_decision}'")
                        all_passed = False
                    else:
                        test_results.append(f"PASS: Round {expected_round}, Player {player_id} correctly chose '{expected_decision}'")

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

    # Import here to use the modified environment variables
    from core.engine import GameEngine
    import time

    try:
        # Load the config to get the game name
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        game_name = config.get('game', {}).get('name', 'Unknown Game')
        logger.info(f"Testing game: {game_name}")

        # Create engine with test directory
        engine = GameEngine(config_path, base_output_dir=TEST_SESSIONS_DIR)
        start_time = datetime.now()
        engine.run_game()
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        logger.info(f"Game execution completed in {elapsed:.2f} seconds")

        # Check if game completed
        if not engine.state.game_over:
            logger.error("Game did not complete properly")
            return False

        # Find the latest session directory
        session_dir = find_latest_session_dir()
        if not session_dir:
            logger.error("No session directory found")
            return False

        logger.info(f"Found session directory: {session_dir}")

        # Check if snapshots file exists
        snapshots_file = os.path.join(session_dir, "snapshots.jsonl")
        if not os.path.exists(snapshots_file):
            logger.error("No snapshots were created")
            return False

        logger.info(f"Found snapshots file: {snapshots_file}")

        # Get results
        results_file = os.path.join(session_dir, "results.json")
        if not os.path.exists(results_file):
            logger.error("No results file was created")
            return False

        logger.info(f"Found results file: {results_file}")

        import time

        # Verify test outcomes
        success, test_results = verify_test_results(game_name, session_dir, results_file)

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
        if "PARLOURBENCH_USE_MOCK" in os.environ:
            del os.environ["PARLOURBENCH_USE_MOCK"]

if __name__ == "__main__":
    sys.exit(main())