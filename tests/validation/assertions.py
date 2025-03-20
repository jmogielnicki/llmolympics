import os
import glob
import json
import logging
import re

logger = logging.getLogger("AssertionValidation")

def extract_benchmark_data(output_dir):
    """
    Extract essential data from benchmark results for assertion checking.

    Args:
        output_dir (str): Directory containing benchmark results

    Returns:
        dict: Structured data from benchmark results
    """
    data = {
        'games_completed': 0,
        'player_scores': {},
        'winners': [],
        'player_counts': {},
        'session_data': [],
        'model_outcomes': {}
    }

    # Read benchmark log
    benchmark_log_path = os.path.join(output_dir, "benchmark_log.jsonl")
    if not os.path.exists(benchmark_log_path):
        logger.warning(f"Benchmark log not found: {benchmark_log_path}")
        return data

    try:
        # Parse benchmark log
        entries = []
        with open(benchmark_log_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        # Count games completed
        data['games_completed'] = len(entries)

        # Process each entry
        for entry in entries:
            # Track winners
            winner_id = entry.get('winner', {})
            if winner_id:
                if isinstance(winner_id, dict):
                    winner_id = winner_id.get('id', 'unknown')
                data['winners'].append(winner_id)

            # Track player scores
            players = entry.get('players', [])
            for player in players:
                player_id = player.get('id', 'unknown')
                score = player.get('score')

                if score is not None:
                    if player_id not in data['player_scores']:
                        data['player_scores'][player_id] = []
                    data['player_scores'][player_id].append(score)

            # Track model outcomes
            if 'player1' in entry and 'player2' in entry:
                # For pairwise benchmarks
                model1 = entry.get('player1', {}).get('model', 'unknown')
                model2 = entry.get('player2', {}).get('model', 'unknown')

                # Initialize model stats if not present
                for model in [model1, model2]:
                    if model not in data['model_outcomes']:
                        data['model_outcomes'][model] = {
                            'wins': 0,
                            'losses': 0,
                            'ties': 0,
                            'total_games': 0
                        }

                # Track outcome
                if winner_id == 'player_1':
                    data['model_outcomes'][model1]['wins'] += 1
                    data['model_outcomes'][model2]['losses'] += 1
                elif winner_id == 'player_2':
                    data['model_outcomes'][model1]['losses'] += 1
                    data['model_outcomes'][model2]['wins'] += 1
                else:
                    data['model_outcomes'][model1]['ties'] += 1
                    data['model_outcomes'][model2]['ties'] += 1

                data['model_outcomes'][model1]['total_games'] += 1
                data['model_outcomes'][model2]['total_games'] += 1

        # Get session data
        session_dirs = [d for d in glob.glob(f"{output_dir}/*")
                        if os.path.isdir(d) and not d.endswith("expected")]

        for session_dir in session_dirs:
            results_path = os.path.join(session_dir, "results.json")
            if os.path.exists(results_path):
                try:
                    with open(results_path, 'r') as f:
                        results = json.load(f)
                        data['session_data'].append(results)

                        # Count players
                        player_count = len(results.get('players', []))
                        data['player_counts'][player_count] = data['player_counts'].get(player_count, 0) + 1
                except json.JSONDecodeError:
                    continue

        # Calculate average scores
        for player_id, scores in data['player_scores'].items():
            data['player_scores'][player_id] = sum(scores) / len(scores) if scores else 0

        return data

    except Exception as e:
        logger.error(f"Error extracting benchmark data: {str(e)}")
        return data

def evaluate_assertion(assertion, data):
    """
    Evaluate an assertion against benchmark data.

    Args:
        assertion (str): Assertion string in Python syntax
        data (dict): Benchmark data

    Returns:
        tuple: (bool, str) - Success flag and error message
    """
    # Create a safe environment with only the data variables
    env = {
        'games_completed': data.get('games_completed', 0),
        'player_scores': data.get('player_scores', {}),
        'winners': data.get('winners', []),
        'player_counts': data.get('player_counts', {}),
        'model_outcomes': data.get('model_outcomes', {})
    }

    try:
        # Evaluate the assertion
        result = eval(assertion, {"__builtins__": {}}, env)

        if bool(result):
            return True, f"Assertion passed: {assertion}"
        else:
            return False, f"Assertion failed: {assertion}"

    except Exception as e:
        return False, f"Error evaluating assertion '{assertion}': {str(e)}"

def validate_assertions(output_dir, assertions):
    """
    Validate benchmark results against a list of assertions.

    Args:
        output_dir (str): Directory containing benchmark results
        assertions (list): List of assertion strings

    Returns:
        tuple: (bool, str) - Overall success flag and error messages
    """
    # Extract data from benchmark results
    data = extract_benchmark_data(output_dir)

    # Validate each assertion
    results = []
    for assertion in assertions:
        success, message = evaluate_assertion(assertion, data)
        results.append((success, message))

    # Check if all assertions passed
    all_passed = all(success for success, _ in results)

    # Summarize results
    if all_passed:
        return True, "All assertions passed"
    else:
        # Collect failed assertion messages
        failed_messages = [message for success, message in results if not success]
        return False, "Assertion failures:\n" + "\n".join(failed_messages)