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
        complete_history, player_sides = extract_history_and_sides(snapshots_path)
        if not complete_history:
            print(f"  Could not extract vote data from {snapshots_path}")
            continue

        # Fix the player scores, sides, and remove current_argument
        fixed = fix_player_data(results, complete_history, player_sides)

        if fixed:
            # Save the updated results
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"  ✓ Fixed and saved")
        else:
            print(f"  ✗ No changes needed or couldn't fix")

def extract_history_and_sides(snapshots_path):
    """Extract complete vote history and side assignments from snapshots file."""
    complete_history = None
    player_sides = {}

    # Read all snapshots to track side changes
    snapshots = []
    with open(snapshots_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('record_type') == 'snapshot':
                    snapshots.append(data)
            except json.JSONDecodeError:
                continue

    # Get final complete history
    for snapshot in reversed(snapshots):
        if snapshot.get('game_over', False) and 'hidden_state' in snapshot and 'complete_history' in snapshot['hidden_state']:
            complete_history = snapshot['hidden_state']['complete_history']
            break

    # IMPROVED APPROACH: Look for side assignments more carefully

    # Find the side assignment events
    side_assignments = {}
    with open(snapshots_path, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('record_type') == 'event' and data.get('event_type') == 'side_assignment':
                    # First debate assignments
                    side_assignments['pre_swap'] = data.get('data', {}).get('assignments', [])
                elif data.get('record_type') == 'event' and data.get('event_type') == 'side_swap':
                    # Second debate assignments after swap
                    side_assignments['post_swap'] = data.get('data', {}).get('new_assignments', [])
            except json.JSONDecodeError:
                continue

    # Process side assignments for both debates
    if 'pre_swap' in side_assignments:
        for assignment in side_assignments['pre_swap']:
            player_id = assignment.get('player_id')
            side_id = assignment.get('side_id')

            if player_id and side_id:
                if player_id not in player_sides:
                    player_sides[player_id] = {}

                player_sides[player_id]['first_side_id'] = side_id

                # Look up the position from sides info in a snapshot
                for snapshot in snapshots:
                    sides = snapshot.get('shared_state', {}).get('sides', [])
                    for side in sides:
                        if side.get('side_id') == side_id:
                            player_sides[player_id]['first_position'] = side.get('position', '')
                            break
                    if 'first_position' in player_sides[player_id]:
                        break

    if 'post_swap' in side_assignments:
        for assignment in side_assignments['post_swap']:
            player_id = assignment.get('player_id')
            side_id = assignment.get('side_id')

            if player_id and side_id:
                if player_id not in player_sides:
                    player_sides[player_id] = {}

                player_sides[player_id]['second_side_id'] = side_id

                # Look up the position from sides info in a snapshot
                for snapshot in snapshots:
                    sides = snapshot.get('shared_state', {}).get('sides', [])
                    for side in sides:
                        if side.get('side_id') == side_id:
                            player_sides[player_id]['second_position'] = side.get('position', '')
                            break
                    if 'second_position' in player_sides[player_id]:
                        break

    return complete_history, player_sides

def fix_player_data(results, complete_history, player_sides):
    """Fix player scores and data structure using pre_swap/post_swap objects."""
    if not complete_history or 'first_debate' not in complete_history or 'second_debate' not in complete_history:
        return False

    first_debate = complete_history['first_debate']
    second_debate = complete_history['second_debate']

    # Get all debaters
    debaters = [p for p in results['players'] if p.get('final_state', {}).get('role') == 'debater']
    if len(debaters) != 2:
        return False

    # Get vote counts from each debate
    first_votes = first_debate['votes']
    second_votes = second_debate['votes']

    made_changes = False

    # Update each player's data
    for player in debaters:
        # Make sure final_state exists
        if 'final_state' not in player:
            player['final_state'] = {}

        final_state = player['final_state']

        # Initialize pre_swap and post_swap objects
        if 'pre_swap' not in final_state:
            final_state['pre_swap'] = {}
        if 'post_swap' not in final_state:
            final_state['post_swap'] = {}

        pre_swap = final_state['pre_swap']
        post_swap = final_state['post_swap']

        # Preserve role
        role = final_state.get('role', '')

        # Determine sides and positions from existing data or player_sides
        first_side_id = final_state.get('first_side_id') or player_sides.get(player['id'], {}).get('first_side_id', '')
        first_position = final_state.get('first_position') or player_sides.get(player['id'], {}).get('first_position', '')
        first_debate_votes = final_state.get('first_debate_votes', 0)

        second_side_id = final_state.get('second_side_id') or player_sides.get(player['id'], {}).get('second_side_id', '')
        second_position = final_state.get('second_position') or player_sides.get(player['id'], {}).get('second_position', '')
        second_debate_votes = final_state.get('second_debate_votes', 0)

        # If we have side IDs but not scores, try to get them from complete_history
        if first_side_id and not first_debate_votes and first_side_id in first_votes:
            first_debate_votes = first_votes[first_side_id]

        if second_side_id and not second_debate_votes and second_side_id in second_votes:
            second_debate_votes = second_votes[second_side_id]

        # Populate pre_swap data
        pre_swap['side_id'] = first_side_id
        pre_swap['position'] = first_position
        pre_swap['score'] = first_debate_votes

        # Populate post_swap data
        post_swap['side_id'] = second_side_id
        post_swap['position'] = second_position
        post_swap['score'] = second_debate_votes

        # Calculate total score
        total_score = pre_swap['score'] + post_swap['score']

        # Update basic fields
        final_state['role'] = role
        final_state['score'] = total_score

        # Remove old flat fields and current_argument
        fields_to_remove = [
            'first_side_id', 'first_position', 'first_debate_votes',
            'second_side_id', 'second_position', 'second_debate_votes',
            'current_argument', 'side_id', 'position'
        ]

        for field in fields_to_remove:
            if field in final_state:
                del final_state[field]
                made_changes = True

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