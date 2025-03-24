#!/usr/bin/env python3

import json
import os
from collections import defaultdict
import argparse
from pathlib import Path
from common_utils import extract_model_name

def split_events_by_swap(events):
    """Split events into pre-swap and post-swap collections."""
    # Find the swap event
    swap_event = next((e for e in events if e.get('event_type') == 'side_swap'), None)

    pre_swap_events = []
    post_swap_events = []

    if swap_event:
        swap_timestamp = swap_event.get('timestamp')

        for event in events:
            event_timestamp = event.get('timestamp')

            # Handle string timestamps (most common case)
            if isinstance(event_timestamp, str) and isinstance(swap_timestamp, str):
                if event_timestamp < swap_timestamp:
                    pre_swap_events.append(event)
                else:
                    post_swap_events.append(event)
            # Handle numeric timestamps
            elif event_timestamp is not None and swap_timestamp is not None:
                if float(event_timestamp) < float(swap_timestamp):
                    pre_swap_events.append(event)
                else:
                    post_swap_events.append(event)
    else:
        # If no swap event found, all events are pre-swap
        pre_swap_events = events

    return pre_swap_events, post_swap_events


def extract_round_data(round_events, round_num, player_roles):
    """Extract data for a single debate round using only events."""
    debater_arguments = []
    judge_votes = []

    # Get debater arguments from round_discussion or opening_arguments
    for event in round_events:
        if (event.get('event_type') == 'player_action_complete' and
            (event.get('phase_id') == 'round_discussion' or event.get('phase_id') == 'opening_arguments')):

            player_id = event.get('data', {}).get('player_id')
            argument = event.get('data', {}).get('action')

            if player_id and argument and not any(arg['player_id'] == player_id for arg in debater_arguments):
                # Get side_id and role from player_roles dictionary
                side_id = player_roles.get(player_id, {}).get('side_id', '')
                position = player_roles.get(player_id, {}).get('position', '')

                debater_arguments.append({
                    "player_id": player_id,
                    "side_id": side_id,
                    "position": position,
                    "argument": argument
                })

    # Get judge votes from round_judging or final_judging
    for event in round_events:
        if (event.get('event_type') == 'player_action_complete' and
            (event.get('phase_id') == 'round_judging' or event.get('phase_id') == 'final_judging')):

            player_id = event.get('data', {}).get('player_id')
            vote = event.get('data', {}).get('action')

            if player_id and vote and not any(v['player_id'] == player_id for v in judge_votes):
                judge_votes.append({
                    "player_id": player_id,
                    "vote": vote
                })

    # Calculate vote tally
    vote_tally = defaultdict(int)
    for vote_data in judge_votes:
        vote_tally[vote_data['vote']] += 1

    return {
        "round_number": round_num,
        "debater_arguments": debater_arguments,
        "judge_votes": judge_votes,
        "vote_tally": dict(vote_tally)
    }


def extract_final_votes(events):
    """Extract final votes using only events."""
    # Get votes from final_judging events
    judge_breakdown = {}

    for event in events:
        if (event.get('event_type') == 'player_action_complete' and
            event.get('phase_id') == 'final_judging'):

            player_id = event.get('data', {}).get('player_id')
            vote = event.get('data', {}).get('action')

            if player_id and vote:
                judge_breakdown[player_id] = vote

    # Calculate vote totals
    vote_counts = defaultdict(int)
    for vote in judge_breakdown.values():
        vote_counts[vote] += 1

    return {
        "votes": dict(vote_counts),
        "judge_breakdown": judge_breakdown
    }


def extract_player_roles(events, snapshots):
    """Extract player roles, side assignments and positions split into pre-swap and post-swap."""
    # Initialize structure with pre-swap and post-swap sections
    result = {
        "pre-swap": {},
        "post-swap": {}
    }

    # First capture basic role information that's common to both phases
    base_roles = {}
    for snapshot in snapshots:
        players = snapshot.get('players', [])
        for player in players:
            player_id = player.get('id')
            if player_id:
                role = player.get('role')
                if player_id not in base_roles:
                    base_roles[player_id] = {'role': role}

    # Find pre-swap side assignments - look at early snapshots before any swap
    pre_swap_sides = {}
    for snapshot in snapshots:
        # Stop once we detect a side swap
        if snapshot.get('shared_state', {}).get('sides_swapped', False):
            break

        players = snapshot.get('players', [])
        for player in players:
            player_id = player.get('id')
            if player_id and player_id in base_roles:
                side_id = player.get('state', {}).get('side_id', '')
                position = player.get('state', {}).get('position', '')

                if side_id and player_id not in pre_swap_sides:
                    pre_swap_sides[player_id] = {
                        'side_id': side_id,
                        'position': position
                    }

    # Create pre-swap roles by combining base roles with pre-swap side info
    for player_id, base_data in base_roles.items():
        result["pre-swap"][player_id] = base_data.copy()
        if player_id in pre_swap_sides:
            result["pre-swap"][player_id].update(pre_swap_sides[player_id])

    # Find post-swap side assignments - look at snapshots after the swap
    post_swap_found = False
    for snapshot in snapshots:
        if snapshot.get('shared_state', {}).get('sides_swapped', False):
            post_swap_found = True
            players = snapshot.get('players', [])
            for player in players:
                player_id = player.get('id')
                if player_id and player_id in base_roles:
                    # For post-swap, copy the sides directly
                    result["post-swap"][player_id] = base_roles[player_id].copy()

                    # Add side information for debaters
                    if base_roles[player_id]['role'] == 'debater':
                        side_id = player.get('state', {}).get('side_id', '')
                        position = player.get('state', {}).get('position', '')
                        result["post-swap"][player_id]['side_id'] = side_id
                        result["post-swap"][player_id]['position'] = position

    # If no post-swap was found, make post-swap the same as pre-swap
    if not post_swap_found:
        result["post-swap"] = result["pre-swap"]

    return result


def process_debate_phase(phase_events, player_roles):
    """Process debate rounds for a phase (pre-swap or post-swap)."""
    # Group events by round
    rounds_events = {}
    for event in phase_events:
        round_num = event.get('round_num')
        if round_num and round_num > 0:
            if round_num not in rounds_events:
                rounds_events[round_num] = []
            rounds_events[round_num].append(event)

    # Process each round
    processed_rounds = []

    for round_num in sorted(rounds_events.keys()):
        round_data = extract_round_data(
            rounds_events[round_num],
            round_num,
            player_roles
        )
        processed_rounds.append(round_data)

    # Get final votes
    final_votes = extract_final_votes(phase_events)

    return {
        "rounds": processed_rounds,
        "final_votes": final_votes
    }


def extract_metadata(snapshots, events):
    """Extract debate metadata."""
    # Find the first snapshot with debate_topic
    for snapshot in snapshots:
        shared_state = snapshot.get('shared_state', {})
        debate_topic = shared_state.get('debate_topic')
        if debate_topic:
            sides = shared_state.get('sides', [])
            session_id = snapshot.get('session_id', '')

            # Count debaters and judges
            player_info = snapshot.get('players', [])
            debater_count = sum(1 for p in player_info if p.get('role') == 'debater')
            judge_count = sum(1 for p in player_info if p.get('role') == 'judge')

            max_rounds = shared_state.get('max_rounds', 3)

            return {
                "topic": debate_topic,
                "session_id": session_id,
                "rounds_per_side": max_rounds,
                "debater_count": debater_count,
                "judge_count": judge_count
            }

    return {"topic": "Unknown", "session_id": "Unknown"}


def extract_players(player_roles, player_models=None):
    """Extract player information from the split player_roles structure."""
    debaters = []
    judges = []

    # Get player ids from pre-swap roles (all players should be here)
    pre_swap_roles = player_roles.get("pre-swap", {})
    post_swap_roles = player_roles.get("post-swap", {})

    for player_id, role_data in pre_swap_roles.items():
        role = role_data.get('role')
        model_name = player_models.get(player_id, f"Model {player_id}") if player_models else f"Model {player_id}"

        if role == 'debater':
            # Get side assignments from both phases
            pre_swap_side = role_data.get("side_id", "")
            post_swap_side = post_swap_roles.get(player_id, {}).get("side_id", "")

            debaters.append({
                "player_id": player_id,
                "model": model_name,
                "pre_swap_side": pre_swap_side,
                "post_swap_side": post_swap_side
            })
        elif role == 'judge':
            judges.append({
                "player_id": player_id,
                "model": model_name
            })

    return {
        "debaters": debaters,
        "judges": judges
    }


def calculate_summary(pre_swap_data, post_swap_data, players):
    """Calculate summary and determine winner."""
    # Extract voting data
    pre_swap_votes = pre_swap_data.get('final_votes', {}).get('votes', {})
    post_swap_votes = post_swap_data.get('final_votes', {}).get('votes', {})

    # Map sides to players for pre and post swap
    debaters = players.get('debaters', [])

    player_scores = {}
    for debater in debaters:
        player_id = debater.get('player_id')
        pre_swap_side = debater.get('pre_swap_side')
        post_swap_side = debater.get('post_swap_side')

        # Calculate scores from votes
        pre_swap_score = pre_swap_votes.get(pre_swap_side, 0)
        post_swap_score = post_swap_votes.get(post_swap_side, 0)
        total_score = pre_swap_score + post_swap_score

        player_scores[player_id] = total_score

    # Determine winner
    winner_id = max(player_scores.items(), key=lambda x: x[1])[0] if player_scores else None
    winner_model = next((d.get('model') for d in debaters if d.get('player_id') == winner_id), "Unknown")
    winner_score = player_scores.get(winner_id, 0)

    return {
        "winner": {
            "player_id": winner_id,
            "model_name": winner_model,
            "total_score": winner_score
        },
        "voting_summary": {
            "pre_swap": pre_swap_votes,
            "post_swap": post_swap_votes,
            "total": player_scores
        }
    }


def process_debate_slam(snapshots_file, player_models=None):
    """Process debate slam data from snapshots file."""
    # Read snapshots and events
    snapshots = []
    events = []

    with open(snapshots_file, 'r') as f:
        for line in f:
            record = json.loads(line)
            if record.get("record_type") == 'snapshot':
                snapshots.append(record)
            elif record.get("record_type") == 'event':
                events.append(record)

    # Sort events chronologically
    def safe_event_time(event):
        timestamp = event.get('timestamp', 0)
        if isinstance(timestamp, (int, float)):
            return timestamp
        elif isinstance(timestamp, str):
            return timestamp
        return 0

    events.sort(key=safe_event_time)

    # Split events into pre-swap and post-swap
    pre_swap_events, post_swap_events = split_events_by_swap(events)

    # Extract player roles and side assignments - now split by phase
    player_roles = extract_player_roles(events, snapshots)
    pre_swap_roles = player_roles["pre-swap"]
    post_swap_roles = player_roles["post-swap"]

    # Extract metadata
    metadata = extract_metadata(snapshots, events)

    # Extract player information
    players = extract_players(player_roles, player_models)

    # Process pre-swap and post-swap rounds with their respective roles
    pre_swap_data = process_debate_phase(pre_swap_events, pre_swap_roles)
    post_swap_data = process_debate_phase(post_swap_events, post_swap_roles)

    # Calculate summary and determine winner
    summary = calculate_summary(pre_swap_data, post_swap_data, players)

    # Construct final data structure
    result = {
        "metadata": metadata,
        "summary": summary,
        "players": players,
        "pre_swap": pre_swap_data,
        "post_swap": post_swap_data
    }

    return result


def process_single_session(session_dir, output_file, verbose=True):
    """Process a single debate slam session directory."""
    if verbose:
        print(f"Processing session: {session_dir}")

    # Look for snapshots file
    snapshots_file = os.path.join(session_dir, "snapshots.jsonl")
    if not os.path.exists(snapshots_file):
        if verbose:
            print(f"No snapshots.jsonl found in {session_dir}")
        return False

    # Look for config file for model names
    config_file = os.path.join(session_dir, "game_config.yaml")
    player_models = None

    if os.path.exists(config_file):
        import yaml
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            player_models = {}
            llm_integration = config.get('llm_integration', {})
            for player_id, model in llm_integration.get('player_models', {}).items():
                # Extract friendly model name
                model_name = extract_model_name(model)
                player_models[player_id] = model_name
        except Exception as e:
            if verbose:
                print(f"Error loading config: {e}")

    # Process the snapshots
    result = process_debate_slam(snapshots_file, player_models)
    return result