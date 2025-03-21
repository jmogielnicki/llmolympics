#!/usr/bin/env python3

import json
import os
from collections import defaultdict
import argparse
from pathlib import Path

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

def extract_players(snapshots, player_models=None):
    """Extract player information."""
    # Find snapshot with player role information
    players = {}

    # First, find debaters and judges
    for snapshot in snapshots:
        snapshot_players = snapshot.get('players', [])
        for player in snapshot_players:
            player_id = player.get('id')
            if player_id not in players:
                players[player_id] = {
                    "player_id": player_id,
                    "role": player.get('role'),
                    "model": player_models.get(player_id, "Unknown Model") if player_models else f"Model {player_id}"
                }

    # Then, find side assignments
    for snapshot in snapshots:
        if snapshot.get('current_phase') == 'side_assignment' and not snapshot.get('shared_state', {}).get('sides_swapped', False):
            snapshot_players = snapshot.get('players', [])
            for player in snapshot_players:
                player_id = player.get('id')
                if player_id in players and players[player_id]["role"] == "debater":
                    players[player_id]["pre_swap_side"] = player.get('state', {}).get('side_id', '')

    # Find post-swap assignments
    for snapshot in snapshots:
        if snapshot.get('shared_state', {}).get('sides_swapped', False):
            snapshot_players = snapshot.get('players', [])
            for player in snapshot_players:
                player_id = player.get('id')
                if player_id in players and players[player_id]["role"] == "debater":
                    players[player_id]["post_swap_side"] = player.get('state', {}).get('side_id', '')

    # Organize into debaters and judges
    debaters = []
    judges = []

    for player_id, player_data in players.items():
        if player_data["role"] == "debater":
            debaters.append({
                "player_id": player_id,
                "model": player_data["model"],
                "pre_swap_side": player_data.get("pre_swap_side", ""),
                "post_swap_side": player_data.get("post_swap_side", "")
            })
        elif player_data["role"] == "judge":
            judges.append({
                "player_id": player_id,
                "model": player_data["model"]
            })

    return {
        "debaters": debaters,
        "judges": judges
    }

def find_swap_transition(snapshots, events):
    """Find index where the sides are swapped."""
    # First try to find the side_swap event
    swap_event = next((e for e in events if e.get('event_type') == 'side_swap'), None)
    if swap_event:
        swap_timestamp = swap_event.get('timestamp')
        for i, snapshot in enumerate(snapshots):
            snapshot_time = snapshot.get('timestamp', 0)
            # Find the first snapshot after the swap event
            if str(snapshot_time) > str(swap_timestamp):
                return i

    # Fall back to checking snapshots directly
    for i, snapshot in enumerate(snapshots):
        if snapshot.get('shared_state', {}).get('sides_swapped', False):
            return i

    return len(snapshots)  # Default to end if no swap found

def extract_round_data(round_snapshots, round_events, round_num, max_round=False):
    """Extract data for a single debate round."""
    # Find debater arguments
    debater_arguments = []
    judge_votes = []

    # Extract arguments from opening_arguments or round_discussion
    for snapshot in round_snapshots:
        shared_state = snapshot.get('shared_state', {})

        # Look for arguments in various places
        if round_num == 1:
            # Round 1 arguments are in opening_arguments_responses
            arguments = shared_state.get('opening_arguments_responses', {})
        else:
            # Later rounds use round_discussion_responses
            arguments = shared_state.get('round_discussion_responses', {})

        # Extract all debater arguments
        players = snapshot.get('players', [])
        for player in players:
            player_id = player.get('id')
            if player.get('role') == 'debater' and player_id in arguments:
                argument = arguments.get(player_id)
                side_id = player.get('state', {}).get('side_id', '')
                position = player.get('state', {}).get('position', '')

                # Only add if we have actual argument content
                if argument and not any(arg['player_id'] == player_id for arg in debater_arguments):
                    debater_arguments.append({
                        "player_id": player_id,
                        "side_id": side_id,
                        "position": position,
                        "argument": argument
                    })

        # Extract judge votes
        judge_opinions = shared_state.get('judge_opinions', {}).get('rounds', {}).get(str(round_num), {})
        if judge_opinions:
            for judge_id, vote in judge_opinions.items():
                if not any(v['player_id'] == judge_id for v in judge_votes):
                    judge_votes.append({
                        "player_id": judge_id,
                        "vote": vote
                    })

    # If no arguments were found, try to find them in current_arguments
    if not debater_arguments:
        for snapshot in round_snapshots:
            shared_state = snapshot.get('shared_state', {})
            current_args = shared_state.get('current_arguments', {})

            if current_args:
                players = snapshot.get('players', [])
                for player in players:
                    player_id = player.get('id')
                    if player.get('role') == 'debater' and player_id in current_args:
                        arg_data = current_args.get(player_id, {})
                        side_id = arg_data.get('side_id', player.get('state', {}).get('side_id', ''))
                        argument = arg_data.get('argument', '')
                        position = player.get('state', {}).get('position', '')

                        if argument and not any(arg['player_id'] == player_id for arg in debater_arguments):
                            debater_arguments.append({
                                "player_id": player_id,
                                "side_id": side_id,
                                "position": position,
                                "argument": argument
                            })

    # Extract judge votes from events
    phase_ids_to_check = ['round_judging']
    if max_round:
        # For the final round, also check final_judging events
        phase_ids_to_check.append('final_judging')

    for event in round_events:
        if (event.get('event_type') == 'player_action_complete' and
            event.get('phase_id') in phase_ids_to_check):
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

def extract_final_votes(snapshots, events, is_pre_swap=True):
    """Extract final votes for pre_swap or post_swap."""
    # Try to get votes from events first
    judge_breakdown = {}

    # Filter events to final_judging for the appropriate phase
    swap_event = next((e for e in events if e.get('event_type') == 'side_swap'), None)

    if swap_event:
        swap_timestamp = swap_event.get('timestamp')
        final_events = []

        for event in events:
            if event.get('phase_id') == 'final_judging':
                event_timestamp = event.get('timestamp')
                # Pre-swap events are before swap timestamp
                if (is_pre_swap and event_timestamp < swap_timestamp) or \
                   (not is_pre_swap and event_timestamp > swap_timestamp):
                    final_events.append(event)
    else:
        # If no swap event, assume all final_judging events are pre-swap
        final_events = [e for e in events if e.get('phase_id') == 'final_judging']

    # Extract votes from player_action_complete events
    for event in final_events:
        if event.get('event_type') == 'player_action_complete':
            player_id = event.get('data', {}).get('player_id')
            vote = event.get('data', {}).get('action')

            if player_id and vote:
                judge_breakdown[player_id] = vote

    # If we found votes from events, calculate totals
    if judge_breakdown:
        vote_counts = defaultdict(int)
        for vote in judge_breakdown.values():
            vote_counts[vote] += 1

        return {
            "votes": dict(vote_counts),
            "judge_breakdown": judge_breakdown
        }

    # Fall back to snapshot method if events don't have the data
    for snapshot in reversed(snapshots):  # Start from the latest and work backwards
        shared_state = snapshot.get('shared_state', {})
        sides_swapped = shared_state.get('sides_swapped', False)

        # We're looking for the final judging phase results
        if (is_pre_swap and not sides_swapped) or (not is_pre_swap and sides_swapped):
            judge_opinions = shared_state.get('judge_opinions', {}).get('final', {})

            if judge_opinions:
                # Calculate vote totals
                vote_counts = defaultdict(int)
                for vote in judge_opinions.values():
                    vote_counts[vote] += 1

                return {
                    "votes": dict(vote_counts),
                    "judge_breakdown": judge_opinions
                }

            # Try the hidden state for pre-swap results when looking at post-swap data
            if not is_pre_swap:
                hidden_state = snapshot.get('hidden_state', {}).get('complete_history', {})
                first_debate = hidden_state.get('first_debate', {})
                judge_opinions = first_debate.get('judge_opinions', {}).get('final', {})

                if judge_opinions:
                    vote_counts = defaultdict(int)
                    for vote in judge_opinions.values():
                        vote_counts[vote] += 1

                    return {
                        "votes": dict(vote_counts),
                        "judge_breakdown": judge_opinions
                    }

    # If we can't find final votes, try to use the last round's votes
    empty_result = {"votes": {}, "judge_breakdown": {}}

    for snapshot in reversed(snapshots):
        shared_state = snapshot.get('shared_state', {})
        sides_swapped = shared_state.get('sides_swapped', False)

        if (is_pre_swap and not sides_swapped) or (not is_pre_swap and sides_swapped):
            rounds = shared_state.get('judge_opinions', {}).get('rounds', {})
            if rounds:
                # Get the votes from the last round
                last_round = max(int(r) for r in rounds.keys() if r.isdigit())
                judge_opinions = rounds.get(str(last_round), {})

                vote_counts = defaultdict(int)
                for vote in judge_opinions.values():
                    vote_counts[vote] += 1

                return {
                    "votes": dict(vote_counts),
                    "judge_breakdown": judge_opinions
                }

    return empty_result

def process_pre_swap(snapshots, events):
    """Process pre-swap debate rounds."""
    # Find where the swap happens
    swap_index = find_swap_transition(snapshots, events)
    pre_swap_snapshots = snapshots[:swap_index]

    # Find pre-swap events
    swap_event = next((e for e in events if e.get('event_type') == 'side_swap'), None)
    pre_swap_events = []
    if swap_event:
        swap_timestamp = swap_event.get('timestamp')
        for event in events:
            event_timestamp = event.get('timestamp')
            if str(event_timestamp) < str(swap_timestamp):
                pre_swap_events.append(event)
    else:
        pre_swap_events = events  # If no swap event found, use all events

    # Group snapshots by round
    rounds_data = {}
    rounds_events = {}
    for snapshot in pre_swap_snapshots:
        current_round = snapshot.get('shared_state', {}).get('current_round', 0)
        if current_round > 0:
            if current_round not in rounds_data:
                rounds_data[current_round] = []
            rounds_data[current_round].append(snapshot)

    # Group events by round
    for event in pre_swap_events:
        round_num = event.get('round_num')
        if round_num and round_num > 0:
            if round_num not in rounds_events:
                rounds_events[round_num] = []
            rounds_events[round_num].append(event)

    # Process each round
    processed_rounds = []
    max_round = max(rounds_data.keys()) if rounds_data else 0

    for round_num in sorted(rounds_data.keys()):
        is_max_round = (round_num == max_round)
        round_data = extract_round_data(
            rounds_data[round_num],
            rounds_events.get(round_num, []),
            round_num,
            max_round=is_max_round
        )
        processed_rounds.append(round_data)

    # Get final votes
    final_votes = extract_final_votes(pre_swap_snapshots, pre_swap_events, is_pre_swap=True)

    return {
        "rounds": processed_rounds,
        "final_votes": final_votes
    }

def process_post_swap(snapshots, events):
    """Process post-swap debate rounds."""
    # Find where the swap happens
    swap_index = find_swap_transition(snapshots, events)
    post_swap_snapshots = snapshots[swap_index:]

    # Find post-swap events
    swap_event = next((e for e in events if e.get('event_type') == 'side_swap'), None)
    post_swap_events = []
    if swap_event:
        swap_timestamp = swap_event.get('timestamp')
        for event in events:
            event_timestamp = event.get('timestamp')
            if str(event_timestamp) > str(swap_timestamp):
                post_swap_events.append(event)
    else:
        post_swap_events = []  # If no swap event found, assume no post-swap events

    # Group snapshots by round
    rounds_data = {}
    rounds_events = {}
    for snapshot in post_swap_snapshots:
        current_round = snapshot.get('shared_state', {}).get('current_round', 0)
        if current_round > 0:
            if current_round not in rounds_data:
                rounds_data[current_round] = []
            rounds_data[current_round].append(snapshot)

    # Group events by round
    for event in post_swap_events:
        round_num = event.get('round_num')
        if round_num and round_num > 0:
            if round_num not in rounds_events:
                rounds_events[round_num] = []
            rounds_events[round_num].append(event)

    # Process each round
    processed_rounds = []
    max_round = max(rounds_data.keys()) if rounds_data else 0

    for round_num in sorted(rounds_data.keys()):
        is_max_round = (round_num == max_round)
        round_data = extract_round_data(
            rounds_data[round_num],
            rounds_events.get(round_num, []),
            round_num,
            max_round=is_max_round
        )
        processed_rounds.append(round_data)

    # Get final votes
    final_votes = extract_final_votes(post_swap_snapshots, post_swap_events, is_pre_swap=False)

    return {
        "rounds": processed_rounds,
        "final_votes": final_votes
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

    # Sort snapshots by timestamp for chronological order
    snapshots.sort(key=lambda x: x.get('timestamp', 0))

    # Sort events chronologically - handle various timestamp formats safely
    def safe_event_time(event):
        timestamp = event.get('timestamp', 0)
        if isinstance(timestamp, (int, float)):
            return timestamp
        elif isinstance(timestamp, str):
            # For ISO format timestamps, use the raw string for sorting (lexicographically)
            # This works because ISO timestamps sort correctly as strings
            return timestamp
        return 0

    events.sort(key=safe_event_time)

    # Extract metadata
    metadata = extract_metadata(snapshots, events)

    # Extract player information
    players = extract_players(snapshots, player_models)

    # Process pre-swap and post-swap rounds
    pre_swap_data = process_pre_swap(snapshots, events)
    post_swap_data = process_post_swap(snapshots, events)

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
                model_name = model.split('/')[-1] if '/' in model else model
                player_models[player_id] = model_name
        except Exception as e:
            if verbose:
                print(f"Error loading config: {e}")

    # Verify this is a debate slam game by checking first few snapshots
    is_debate_slam = False
    try:
        with open(snapshots_file, 'r') as f:
            for i, line in enumerate(f):
                if i > 5:  # Check first few lines
                    break

                record = json.loads(line)
                if record.get("record_type") == "snapshot":
                    config = record.get("config", {})
                    game_name = config.get("game_name", "")
                    if "debate" in game_name.lower() or "slam" in game_name.lower():
                        is_debate_slam = True
                        break
                elif record.get("record_type") == "event" and record.get("event_type") == "game_start":
                    game_name = record.get("data", {}).get("game_name", "")
                    if "debate" in game_name.lower() or "slam" in game_name.lower():
                        is_debate_slam = True
                        break
    except Exception:
        pass

    if not is_debate_slam:
        if verbose:
            print(f"Not a Debate Slam game in {session_dir}")
        return False

    # Process the snapshots
    try:
        result = process_debate_slam(snapshots_file, player_models)

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Write the result to the output file
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        if verbose:
            print(f"Processed data written to {output_file}")
        return True
    except Exception as e:
        if verbose:
            print(f"Error processing {session_dir}: {e}")
        return False

def process_all_sessions(benchmark_dir, output_dir="data/processed", verbose=True):
    """Process all debate slam sessions in a benchmark directory."""
    if verbose:
        print(f"Processing all debate slam sessions in: {benchmark_dir}")

    # Get benchmark ID from directory name
    benchmark_id = os.path.basename(benchmark_dir)

    # Create output directory
    detail_dir = os.path.join(output_dir, benchmark_id, "detail")
    os.makedirs(detail_dir, exist_ok=True)

    # Find all session directories
    processed_count = 0
    total_count = 0

    for item in os.listdir(benchmark_dir):
        session_dir = os.path.join(benchmark_dir, item)
        if os.path.isdir(session_dir):
            total_count += 1
            output_file = os.path.join(detail_dir, f"{os.path.basename(session_dir)}.json")

            if process_single_session(session_dir, output_file, verbose):
                processed_count += 1

    if verbose:
        print(f"Processed {processed_count} out of {total_count} sessions in {benchmark_dir}")

    return processed_count

def main():
    parser = argparse.ArgumentParser(description="Process Debate Slam data")
    parser.add_argument('--snapshots', help='Path to snapshots.jsonl file')
    parser.add_argument('--output', default='debate_slam_processed.json', help='Output JSON file path')
    parser.add_argument('--config', help='Optional path to game_config.yaml for model names')
    parser.add_argument('--benchmark', help='Path to benchmark directory containing multiple sessions')
    parser.add_argument('--all', action='store_true', help='Process all sessions in the benchmark')
    parser.add_argument('--session', help='Process a specific session directory')
    parser.add_argument('--output-dir', default='data/processed', help='Output directory for processed data')

    args = parser.parse_args()

    # Validate arguments
    if not (args.snapshots or args.benchmark or args.session):
        parser.error("You must provide either --snapshots, --benchmark, or --session argument")

    # If benchmark is specified, --all or --session is required
    if args.benchmark and not (args.all or args.session):
        parser.error("When using --benchmark, you must also specify either --all or --session")

    args = parser.parse_args()

    # Process single snapshots file
    if args.snapshots:
        player_models = None
        if args.config and os.path.exists(args.config):
            import yaml
            try:
                with open(args.config, 'r') as f:
                    config = yaml.safe_load(f)

                player_models = {}
                llm_integration = config.get('llm_integration', {})
                for player_id, model in llm_integration.get('player_models', {}).items():
                    # Extract friendly model name
                    model_name = model.split('/')[-1] if '/' in model else model
                    player_models[player_id] = model_name
            except Exception as e:
                print(f"Error loading config: {e}")

        # Process the snapshots
        result = process_debate_slam(args.snapshots, player_models)

        # Create output directory if needed
        os.makedirs(os.path.dirname(args.output), exist_ok=True)

        # Write the result to the output file
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"Processed data written to {args.output}")

    # Process a specific session directory
    elif args.session:
        benchmark_dir = args.benchmark or os.path.dirname(args.session)
        benchmark_id = os.path.basename(benchmark_dir)

        session_dir = args.session
        output_dir = args.output_dir
        detail_dir = os.path.join(output_dir, benchmark_id, "detail")
        output_file = os.path.join(detail_dir, f"{os.path.basename(session_dir)}.json")

        process_single_session(session_dir, output_file)

    # Process all sessions in a benchmark directory
    elif args.benchmark and args.all:
        process_all_sessions(args.benchmark, args.output_dir)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()