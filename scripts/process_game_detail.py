#!/usr/bin/env python3
# scripts/process_game_detail.py
import os
import json
import yaml
from datetime import datetime
from pathlib import Path


def parse_timestamp(timestamp_str):
    """Convert ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def load_chat_logs(session_dir):
    """Load chat logs from a session directory."""
    chat_logs = []
    chat_log_path = os.path.join(session_dir, "chat_logs.jsonl")

    if not os.path.exists(chat_log_path):
        return {}

    try:
        with open(chat_log_path, 'r') as f:
            for line in f:
                try:
                    chat_log = json.loads(line)
                    chat_logs.append(chat_log)
                except:
                    continue
    except:
        return {}

    # Organize by player, phase, and round for easy lookup
    organized_logs = {}
    for log in chat_logs:
        player_id = log.get('player_id')
        phase_id = log.get('phase_id')
        round_num = log.get('round_num')

        if not player_id or not phase_id:
            continue

        if player_id not in organized_logs:
            organized_logs[player_id] = {}

        if phase_id not in organized_logs[player_id]:
            organized_logs[player_id][phase_id] = {}

        key = str(round_num) if round_num is not None else "unknown"
        organized_logs[player_id][phase_id][key] = log

    return organized_logs


def extract_model_reasoning(chat_log):
    """Extract model reasoning from a chat log entry."""
    response = chat_log.get('response', '')
    if not response:
        return ''

    # Clean up and extract the thinking part
    # In Prisoner's Dilemma, the thinking is before the [[DECISION]]
    parts = response.split('[[')
    if len(parts) > 1:
        reasoning = parts[0].strip()

        # Truncate if too long
        max_len = 500
        if len(reasoning) > max_len:
            reasoning = reasoning[:max_len] + "..."

        return reasoning

    return response[:200]  # Return a small preview if no clear reasoning/decision split


def generate_game_timeline(session_dir):
    """
    Generate a detailed timeline of game events.

    Args:
        session_dir: Path to the session directory

    Returns:
        dict: Detailed game timeline with events
    """
    # Load game config to get player models
    config_path = os.path.join(session_dir, "game_config.yaml")
    if not os.path.exists(config_path):
        return {"error": f"Game config not found in {session_dir}"}

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except:
        return {"error": f"Failed to parse game config in {session_dir}"}

    # Get player models
    player_models = {}
    llm_integration = config.get('llm_integration', {})
    for player_id, model in llm_integration.get('player_models', {}).items():
        player_models[player_id] = model

    # Load final results
    results_path = os.path.join(session_dir, "results.json")
    if not os.path.exists(results_path):
        return {"error": f"Results not found in {session_dir}"}

    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
    except:
        return {"error": f"Failed to parse results in {session_dir}"}

    # Load chat logs
    chat_logs = load_chat_logs(session_dir)

    # Load snapshots and events from snapshots.jsonl
    snapshots_path = os.path.join(session_dir, "snapshots.jsonl")
    if not os.path.exists(snapshots_path):
        return {"error": f"Snapshots not found in {session_dir}"}

    snapshots = []
    events = []

    try:
        with open(snapshots_path, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if record.get('record_type') == 'snapshot':
                        snapshots.append(record)
                    elif record.get('record_type') == 'event':
                        events.append(record)
                except:
                    continue
    except:
        return {"error": f"Failed to parse snapshots in {session_dir}"}

    # Build a timeline of events
    timeline = []

    # Add game start event
    game_start_event = next((e for e in events if e.get('event_type') == 'game_start'), None)
    if game_start_event:
        timestamp = parse_timestamp(game_start_event.get('timestamp', ''))
        timeline.append({
            "type": "game_start",
            "timestamp": timestamp,
            "message": "Game started",
            "data": game_start_event.get('data', {})
        })

    # Add phase events in chronological order
    # First, organize all events by phase and round
    phase_events = {}

    for event in events:
        event_type = event.get('event_type')
        phase_id = event.get('phase_id')
        round_num = event.get('round_num')
        timestamp = event.get('timestamp')

        if not event_type or not timestamp:
            continue

        if phase_id not in phase_events:
            phase_events[phase_id] = {}

        round_key = str(round_num) if round_num is not None else "unknown"
        if round_key not in phase_events[phase_id]:
            phase_events[phase_id][round_key] = []

        phase_events[phase_id][round_key].append(event)

    # Process decision phases
    if 'decision' in phase_events:
        for round_key, round_events in sorted(phase_events['decision'].items(), key=lambda x: x[0]):
            try:
                round_num = int(round_key)
            except:
                round_num = 0

            # Get phase start event
            phase_start = next((e for e in round_events if e.get('event_type') == 'phase_start'), None)
            if phase_start:
                timestamp = parse_timestamp(phase_start.get('timestamp', ''))
                timeline.append({
                    "type": "round_start",
                    "timestamp": timestamp,
                    "round": round_num,
                    "message": f"Round {round_num} started"
                })

            # Get player actions
            player_actions = {}

            for event in round_events:
                if event.get('event_type') == 'player_action_complete':
                    player_id = event.get('data', {}).get('player_id')
                    action = event.get('data', {}).get('action')

                    if player_id and action:
                        player_actions[player_id] = {
                            "action": action,
                            "timestamp": parse_timestamp(event.get('timestamp', '')),
                            "player_id": player_id,
                            "model": player_models.get(player_id, "unknown")
                        }

                        # Add reasoning from chat logs if available
                        if player_id in chat_logs and 'decision' in chat_logs[player_id]:
                            if round_key in chat_logs[player_id]['decision']:
                                chat_log = chat_logs[player_id]['decision'][round_key]
                                reasoning = extract_model_reasoning(chat_log)
                                player_actions[player_id]["reasoning"] = reasoning

            # Add player actions to timeline
            for player_id, action_data in player_actions.items():
                timeline.append({
                    "type": "player_decision",
                    "timestamp": action_data["timestamp"],
                    "round": round_num,
                    "player_id": player_id,
                    "model": action_data["model"],
                    "decision": action_data["action"],
                    "reasoning": action_data.get("reasoning", "")
                })

            # Get phase end event (resolution will come next)
            phase_end = next((e for e in round_events if e.get('event_type') == 'phase_end'), None)
            if phase_end:
                timestamp = parse_timestamp(phase_end.get('timestamp', ''))
                timeline.append({
                    "type": "round_decisions_complete",
                    "timestamp": timestamp,
                    "round": round_num,
                    "message": f"Round {round_num} decisions completed"
                })

    # Process resolution phases (scoring)
    if 'resolution' in phase_events:
        for round_key, round_events in sorted(phase_events['resolution'].items(), key=lambda x: x[0]):
            try:
                round_num = int(round_key)
            except:
                round_num = 0

            # Find the snapshot after this round's resolution to get scores
            phase_end = next((e for e in round_events if e.get('event_type') == 'phase_end'), None)
            if phase_end:
                timestamp = phase_end.get('timestamp')

                # Find the first snapshot after this timestamp
                snapshot_after = None
                # Convert timestamp to float for comparison if it's a string
                timestamp_float = float(datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()) if isinstance(timestamp, str) else timestamp

                for snapshot in snapshots:
                    snapshot_time = snapshot.get('timestamp', 0)
                    if isinstance(snapshot_time, (int, float)) and snapshot_time > timestamp_float:
                        snapshot_after = snapshot
                        break

                if snapshot_after:
                    # Extract player scores
                    players = snapshot_after.get('players', [])
                    player_scores = {}

                    for player in players:
                        player_id = player.get('id')
                        score = player.get('state', {}).get('score')

                        if player_id and score is not None:
                            player_scores[player_id] = score

                    # Extract decisions from history
                    decisions = {}
                    decision_history = snapshot_after.get('history_state', {}).get('decision_history', [])

                    for history_entry in decision_history:
                        if history_entry.get('round') == round_num:
                            decisions = history_entry.get('decisions', {})
                            break

                    # Add resolution event to timeline
                    timeline.append({
                        "type": "round_resolution",
                        "timestamp": parse_timestamp(phase_end.get('timestamp', '')),
                        "round": round_num,
                        "scores": player_scores,
                        "decisions": decisions,
                        "message": f"Round {round_num} resolved"
                    })

    # Add game end event
    game_end_event = next((e for e in events if e.get('event_type') == 'game_end'), None)
    if game_end_event:
        timestamp = parse_timestamp(game_end_event.get('timestamp', ''))
        timeline.append({
            "type": "game_end",
            "timestamp": timestamp,
            "message": "Game ended",
            "data": game_end_event.get('data', {})
        })

    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x.get('timestamp', ''))

    # Gather additional game metadata
    game_data = {
        "session_id": os.path.basename(session_dir),
        "game_name": config.get('game', {}).get('name', "Unknown Game"),
        "player_models": player_models,
        "rounds_played": results.get('rounds_played', 0),
        "winner": results.get('winner', {}).get('id'),
        "final_scores": {p.get('id'): p.get('final_state', {}).get('score')
                         for p in results.get('players', [])
                         if p.get('id') and p.get('final_state', {}).get('score') is not None}
    }

    return {
        "game": game_data,
        "timeline": timeline
    }


def process_game_detail(benchmark_dir, session_id, output_dir="data/processed"):
    """
    Process a specific game session to generate detailed visualization data.

    Args:
        benchmark_dir: Path to benchmark directory
        session_id: Session ID or directory name
        output_dir: Output directory for processed data

    Returns:
        Path to the generated detail file
    """
    print(f"Processing game detail: {session_id}")

    # Handle if session_id is a full path or just the directory name
    if os.path.isdir(session_id):
        session_dir = session_id
        session_id = os.path.basename(session_dir)
    else:
        # Check if this is a timestamp-only ID or a full session ID
        if '_' in session_id and not session_id.startswith('prisoner') and not session_id.startswith('ghost'):
            # This is likely just the timestamp portion (e.g., 20250311_144154)
            session_dir = os.path.join(benchmark_dir, session_id)
        else:
            # This is a full session ID, extract the timestamp part
            timestamp_parts = session_id.split('_')
            if len(timestamp_parts) >= 2:
                timestamp = '_'.join(timestamp_parts[-2:])
                session_dir = os.path.join(benchmark_dir, timestamp)
            else:
                return {"error": f"Invalid session ID format: {session_id}"}

    # Check if directory exists
    if not os.path.isdir(session_dir):
        return {"error": f"Session directory not found: {session_dir}"}

    # Generate timeline
    timeline_data = generate_game_timeline(session_dir)

    # Extract benchmark ID from benchmark_dir path
    benchmark_id = os.path.basename(benchmark_dir)

    # Create output directory
    detail_dir = os.path.join(output_dir, benchmark_id, "detail")
    os.makedirs(detail_dir, exist_ok=True)

    # Save detail data
    output_file = os.path.join(detail_dir, f"{os.path.basename(session_dir)}.json")
    with open(output_file, 'w') as f:
        json.dump(timeline_data, f, indent=2)

    print(f"Game detail processed and saved to {output_file}")
    return output_file


def process_all_games(benchmark_dir, output_dir="data/processed"):
    """
    Process all game sessions in a benchmark to generate detailed visualization data.

    Args:
        benchmark_dir: Path to benchmark directory
        output_dir: Output directory for processed data
    """
    print(f"Processing all games in benchmark: {benchmark_dir}")

    # Get all session directories
    sessions = []
    for item in os.listdir(benchmark_dir):
        session_dir = os.path.join(benchmark_dir, item)
        if os.path.isdir(session_dir) and os.path.exists(os.path.join(session_dir, "results.json")):
            sessions.append(session_dir)

    print(f"Found {len(sessions)} game sessions to process")

    # Process each session
    for session_dir in sessions:
        process_game_detail(benchmark_dir, session_dir, output_dir)

    print(f"All game sessions processed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process detailed game data for visualization")
    parser.add_argument("--benchmark", required=True, help="Path to benchmark directory")
    parser.add_argument("--session", help="Process a specific session (directory name or ID)")
    parser.add_argument("--all", action="store_true", help="Process all sessions in the benchmark")
    parser.add_argument("--output", default="data/processed", help="Output directory for processed data")

    args = parser.parse_args()

    if args.session:
        process_game_detail(args.benchmark, args.session, args.output)
    elif args.all:
        process_all_games(args.benchmark, args.output)
    else:
        print("Please specify either --session or --all")