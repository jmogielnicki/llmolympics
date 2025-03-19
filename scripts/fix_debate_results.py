import os
import json
import glob

def fix_debate_slam_results(root_directory):
    """
    Correct the results.json files for all Debate Slam sessions.
    """
    # Find all results.json files
    results_files = glob.glob(os.path.join(root_directory, "**/results.json"), recursive=True)

    for results_path in results_files:
        session_dir = os.path.dirname(results_path)
        snapshots_path = os.path.join(session_dir, "snapshots.jsonl")

        if not os.path.exists(snapshots_path):
            print(f"Skipping {results_path}: No snapshots file found")
            continue

        # Load the results file
        with open(results_path, 'r') as f:
            results = json.load(f)

        # Check if this is a Debate Slam game
        if results.get('game') != 'Debate Slam':
            continue

        print(f"Processing: {results_path}")

        # Extract complete voting data from snapshots
        complete_history = extract_vote_history(snapshots_path)
        if not complete_history:
            print(f"  Could not extract vote data from {snapshots_path}")
            continue

        # Fix the player scores
        fixed = fix_player_scores(results, complete_history)

        if fixed:
            # Save the updated results
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"  ✓ Fixed and saved")
        else:
            print(f"  ✗ No changes needed or couldn't fix")

def extract_vote_history(snapshots_path):
    """Extract complete vote history from snapshots file."""
    complete_history = None

    # Read the file from bottom up to get the final state
    with open(snapshots_path, 'r') as f:
        lines = f.readlines()

    # Process snapshots in reverse to find the final state
    for line in reversed(lines):
        try:
            data = json.loads(line)
            if data.get('record_type') == 'snapshot' and data.get('game_over', False):
                if 'hidden_state' in data and 'complete_history' in data['hidden_state']:
                    complete_history = data['hidden_state']['complete_history']
                    break
        except json.JSONDecodeError:
            continue

    return complete_history

def fix_player_scores(results, complete_history):
    """Fix player scores based on the complete voting history."""
    if not complete_history or 'first_debate' not in complete_history or 'second_debate' not in complete_history:
        return False

    first_debate = complete_history['first_debate']
    second_debate = complete_history['second_debate']

    # Get all debaters
    debaters = [p for p in results['players'] if p.get('final_state', {}).get('role') == 'debater']
    if len(debaters) != 2:
        return False

    # Identify which player had which side in each debate
    player_sides = {}

    # In first debate, we can use the sides directly from first_debate
    first_sides = {}
    for player in debaters:
        if 'first_debate_votes' in player['final_state']:
            # This player's votes are stored for first debate
            for side, votes in first_debate['votes'].items():
                if votes == player['final_state']['first_debate_votes']:
                    first_sides[side] = player['id']

    # In second debate, we can use the sides directly from second_debate
    second_sides = {}
    for player in debaters:
        if 'second_debate_votes' in player['final_state']:
            # This player's votes are stored for second debate
            for side, votes in second_debate['votes'].items():
                if votes == player['final_state']['second_debate_votes']:
                    second_sides[side] = player['id']

    # Now we have the mapping of sides to players for both debates
    made_changes = False

    # Update the player scores
    for player in debaters:
        # Fill in missing first_debate_votes
        if 'first_debate_votes' not in player['final_state']:
            for side, player_id in first_sides.items():
                if player_id != player['id']:  # Find the side this player didn't have
                    # Find the opposite side
                    opposite_sides = [s for s in first_debate['votes'].keys() if s != side]
                    if opposite_sides:
                        player['final_state']['first_debate_votes'] = first_debate['votes'][opposite_sides[0]]
                        made_changes = True

        # Fill in missing second_debate_votes
        if 'second_debate_votes' not in player['final_state']:
            for side, player_id in second_sides.items():
                if player_id != player['id']:  # Find the side this player didn't have
                    # Find the opposite side
                    opposite_sides = [s for s in second_debate['votes'].keys() if s != side]
                    if opposite_sides:
                        player['final_state']['second_debate_votes'] = second_debate['votes'][opposite_sides[0]]
                        made_changes = True

        # Update the total score
        first_votes = player['final_state'].get('first_debate_votes', 0)
        second_votes = player['final_state'].get('second_debate_votes', 0)
        total_votes = first_votes + second_votes

        if player['final_state'].get('score', 0) != total_votes:
            player['final_state']['score'] = total_votes
            made_changes = True

    # Update the winner determination
    if made_changes:
        # Sort debaters by score
        sorted_debaters = sorted(debaters, key=lambda d: d['final_state'].get('score', 0), reverse=True)
        if len(sorted_debaters) >= 2 and sorted_debaters[0]['final_state'].get('score', 0) == sorted_debaters[1]['final_state'].get('score', 0):
            # It's a tie
            results['winner'] = {'id': 'tie'}
        else:
            # Clear winner
            results['winner'] = {'id': sorted_debaters[0]['id']}

    return made_changes

# Usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fix_debate_slam_results(sys.argv[1])
    else:
        print("Please provide the directory containing session folders")
        print("Usage: python fix_debate_results.py /path/to/sessions")