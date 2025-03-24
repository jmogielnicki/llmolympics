#!/usr/bin/env python3
# scripts/process_game_detail.py
import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from common_utils import extract_model_name

from debate_slam_processor import process_single_session as process_debate_session


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


class GameDetailGenerator:
    """Base class for game detail timeline generation."""

    def can_process(self, config):
        """Determine if this generator can process this game type."""
        return False

    def generate_timeline(self, session_dir, config, results, chat_logs, snapshots, events, player_models):
        """Generate timeline for the game."""
        raise NotImplementedError


class PrisonersDilemmaDetailGenerator(GameDetailGenerator):
    """Detail generator for Prisoner's Dilemma game."""

    def can_process(self, config):
        """Determine if this generator can process this game type."""
        game_name = config.get('game', {}).get('name', '')
        return 'prisoner' in game_name.lower()

    def get_decision_context(self, decision):
        """Get UI context for a decision."""
        decision_contexts = {
            "cooperate": {
                "css_class": "bg-green-500",
                "display_text": "Cooperated",
                "icon": "check",
                "color": "green"
            },
            "defect": {
                "css_class": "bg-red-500",
                "display_text": "Defected",
                "icon": "x",
                "color": "red"
            }
        }

        return decision_contexts.get(decision.lower() if isinstance(decision, str) else decision, {
            "css_class": "bg-gray-500",
            "display_text": str(decision),
            "icon": "circle",
            "color": "gray"
        })

    def generate_timeline(self, session_dir, config, results, chat_logs, snapshots, events, player_models):
        """Generate timeline for Prisoner's Dilemma."""
        timeline = []
        running_scores = {}

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

        # Organize events by phase and round
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
                        "message": f"Round {round_num} started",
                        "running_scores": running_scores.copy()  # Include current scores at round start
                    })

                # Get player actions
                player_actions = {}
                for event in round_events:
                    if event.get('event_type') == 'player_action_complete':
                        player_id = event.get('data', {}).get('player_id')
                        action = event.get('data', {}).get('action')

                        if player_id and action:
                            model_id = player_models.get(player_id, {}).get('model_id', "unknown")
                            model_name = player_models.get(player_id, {}).get('model_name', "Unknown Model")

                            player_actions[player_id] = {
                                "action": action,
                                "timestamp": parse_timestamp(event.get('timestamp', '')),
                                "player_id": player_id,
                                "model_id": model_id,
                                "model_name": model_name,
                                "decision_context": self.get_decision_context(action)
                            }

                            # Add reasoning from chat logs if available
                            if player_id in chat_logs and 'decision' in chat_logs[player_id]:
                                if round_key in chat_logs[player_id]['decision']:
                                    chat_log = chat_logs[player_id]['decision'][round_key]
                                    reasoning = chat_log.get('response', '')
                                    player_actions[player_id]["reasoning"] = reasoning

                # Add player actions to timeline
                for player_id, action_data in player_actions.items():
                    timeline.append({
                        "type": "player_decision",
                        "timestamp": action_data["timestamp"],
                        "round": round_num,
                        "player_id": player_id,
                        "model_id": action_data["model_id"],
                        "model_name": action_data["model_name"],
                        "decision": action_data["action"],
                        "decision_context": action_data["decision_context"],
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
                                # Update running scores
                                running_scores[player_id] = score

                        # Extract decisions from history
                        decisions = {}
                        decision_history = snapshot_after.get('history_state', {}).get('decision_history', [])

                        for history_entry in decision_history:
                            if history_entry.get('round') == round_num:
                                decisions = history_entry.get('decisions', {})
                                break

                        # Enhance the decisions with context
                        decisions_with_context = {}
                        for player_id, decision in decisions.items():
                            decisions_with_context[player_id] = {
                                "decision": decision,
                                "context": self.get_decision_context(decision)
                            }

                        # Add resolution event to timeline
                        timeline.append({
                            "type": "round_resolution",
                            "timestamp": parse_timestamp(phase_end.get('timestamp', '')),
                            "round": round_num,
                            "scores": player_scores,
                            "running_scores": running_scores.copy(),  # Include updated scores
                            "decisions": decisions,
                            "decisions_with_context": decisions_with_context,
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
                "data": game_end_event.get('data', {}),
                "final_scores": running_scores.copy()
            })

        return timeline


class PoetryDetailGenerator(GameDetailGenerator):
    """Detail generator for Poetry Slam game."""

    def can_process(self, config):
        """Determine if this generator can process this game type."""
        game_name = config.get('game', {}).get('name', '')
        return 'poetry' in game_name.lower()

    def get_decision_context(self, decision):
        """Get UI context for a Poetry Slam decision (voting)."""
        return {
            "css_class": "bg-blue-500",
            "display_text": f"Voted for {decision}",
            "icon": "thumb-up",
            "color": "blue"
        }

    def generate_timeline(self, session_dir, config, results, chat_logs, snapshots, events, player_models):
        """Generate timeline for Poetry Slam."""
        timeline = []
        running_scores = {}

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

        # Organize events by phase and round
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

        # 1. Process prompt creation phase
        if 'prompt_creation' in phase_events:
            for round_key, round_events in sorted(phase_events['prompt_creation'].items(), key=lambda x: x[0]):
                try:
                    round_num = int(round_key) if round_key != "unknown" else 0
                except:
                    round_num = 0

                # Get phase start event
                phase_start = next((e for e in round_events if e.get('event_type') == 'phase_start'), None)
                if phase_start:
                    timestamp = parse_timestamp(phase_start.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_start",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "prompt_creation",
                        "message": "Prompt creation phase started",
                    })

                # Get player action (prompter)
                for event in round_events:
                    if event.get('event_type') == 'player_action_complete':
                        player_id = event.get('data', {}).get('player_id')
                        action = event.get('data', {}).get('action')

                        if player_id and action:
                            model_id = player_models.get(player_id, {}).get('model_id', "unknown")
                            model_name = player_models.get(player_id, {}).get('model_name', "Unknown Model")

                            # Get the prompt text from chat logs if available
                            prompt_text = action
                            if player_id in chat_logs and 'prompt_creation' in chat_logs[player_id]:
                                if round_key in chat_logs[player_id]['prompt_creation']:
                                    chat_log = chat_logs[player_id]['prompt_creation'][round_key]
                                    prompt_text = chat_log.get('response', action)

                            timeline.append({
                                "type": "prompt_creation",
                                "timestamp": parse_timestamp(event.get('timestamp', '')),
                                "round": round_num,
                                "player_id": player_id,
                                "model_id": model_id,
                                "model_name": model_name,
                                "prompt": prompt_text,
                                "message": f"Prompt created by {model_name}"
                            })

                # Get phase end event
                phase_end = next((e for e in round_events if e.get('event_type') == 'phase_end'), None)
                if phase_end:
                    timestamp = parse_timestamp(phase_end.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_end",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "prompt_creation",
                        "message": "Prompt creation phase ended"
                    })

        # 2. Process content creation phase (poem writing)
        if 'content_creation' in phase_events:
            for round_key, round_events in sorted(phase_events['content_creation'].items(), key=lambda x: x[0]):
                try:
                    round_num = int(round_key) if round_key != "unknown" else 0
                except:
                    round_num = 0

                # Get phase start event
                phase_start = next((e for e in round_events if e.get('event_type') == 'phase_start'), None)
                if phase_start:
                    timestamp = parse_timestamp(phase_start.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_start",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "content_creation",
                        "message": "Poem writing phase started",
                    })

                # Get player actions (poem submissions)
                for event in round_events:
                    if event.get('event_type') == 'player_action_complete':
                        player_id = event.get('data', {}).get('player_id')
                        action = event.get('data', {}).get('action')

                        if player_id and action:
                            model_id = player_models.get(player_id, {}).get('model_id', "unknown")
                            model_name = player_models.get(player_id, {}).get('model_name', "Unknown Model")

                            # Get the full poem from chat logs if available
                            poem_text = action
                            if player_id in chat_logs and 'content_creation' in chat_logs[player_id]:
                                if round_key in chat_logs[player_id]['content_creation']:
                                    chat_log = chat_logs[player_id]['content_creation'][round_key]
                                    poem_text = chat_log.get('response', action)

                            timeline.append({
                                "type": "poem_submission",
                                "timestamp": parse_timestamp(event.get('timestamp', '')),
                                "round": round_num,
                                "player_id": player_id,
                                "model_id": model_id,
                                "model_name": model_name,
                                "poem": poem_text,
                                "message": f"Poem submitted by {model_name}"
                            })

                # Get phase end event
                phase_end = next((e for e in round_events if e.get('event_type') == 'phase_end'), None)
                if phase_end:
                    timestamp = parse_timestamp(phase_end.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_end",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "content_creation",
                        "message": "Poem writing phase ended"
                    })

        # 3. Process voting phase
        if 'voting' in phase_events:
            for round_key, round_events in sorted(phase_events['voting'].items(), key=lambda x: x[0]):
                try:
                    round_num = int(round_key) if round_key != "unknown" else 0
                except:
                    round_num = 0

                # Get phase start event
                phase_start = next((e for e in round_events if e.get('event_type') == 'phase_start'), None)
                if phase_start:
                    timestamp = parse_timestamp(phase_start.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_start",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "voting",
                        "message": "Voting phase started",
                    })

                # Get player actions (votes)
                for event in round_events:
                    if event.get('event_type') == 'player_action_complete':
                        player_id = event.get('data', {}).get('player_id')
                        action = event.get('data', {}).get('action')

                        if player_id and action:
                            model_id = player_models.get(player_id, {}).get('model_id', "unknown")
                            model_name = player_models.get(player_id, {}).get('model_name', "Unknown Model")

                            # Find which model was voted for
                            voted_for_player = action
                            voted_for_model = player_models.get(voted_for_player, {}).get('model_name', "Unknown Model")

                            # Get reasoning from chat logs if available
                            reasoning = ""
                            if player_id in chat_logs and 'voting' in chat_logs[player_id]:
                                if round_key in chat_logs[player_id]['voting']:
                                    chat_log = chat_logs[player_id]['voting'][round_key]
                                    reasoning = chat_log.get('response', "")

                            timeline.append({
                                "type": "player_vote",
                                "timestamp": parse_timestamp(event.get('timestamp', '')),
                                "round": round_num,
                                "player_id": player_id,
                                "model_id": model_id,
                                "model_name": model_name,
                                "voted_for": voted_for_player,
                                "voted_for_model": voted_for_model,
                                "decision_context": self.get_decision_context(voted_for_player),
                                "reasoning": reasoning,
                                "message": f"{model_name} voted for {voted_for_model}"
                            })

                # Get phase end event
                phase_end = next((e for e in round_events if e.get('event_type') == 'phase_end'), None)
                if phase_end:
                    timestamp = parse_timestamp(phase_end.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_end",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "voting",
                        "message": "Voting phase ended"
                    })

        # 4. Process resolution phase
        if 'resolution' in phase_events:
            for round_key, round_events in sorted(phase_events['resolution'].items(), key=lambda x: x[0]):
                try:
                    round_num = int(round_key) if round_key != "unknown" else 0
                except:
                    round_num = 0

                # Get phase start event
                phase_start = next((e for e in round_events if e.get('event_type') == 'phase_start'), None)
                if phase_start:
                    timestamp = parse_timestamp(phase_start.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_start",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "resolution",
                        "message": "Resolution phase started",
                    })

                # Find the snapshot after this phase's resolution to get vote tallies and scores
                phase_end = next((e for e in round_events if e.get('event_type') == 'phase_end'), None)
                if phase_end:
                    timestamp = phase_end.get('timestamp')

                    # Find the first snapshot after this timestamp
                    snapshot_after = None
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
                                # Update running scores
                                running_scores[player_id] = score

                        # Extract voting results
                        vote_counts = {}
                        winners = snapshot_after.get('shared_state', {}).get('winners', [])

                        # Get vote_counts from snapshot
                        for player_id, votes in snapshot_after.get('shared_state', {}).get('vote_counts', {}).items():
                            vote_counts[player_id] = votes

                        # Add resolution event to timeline
                        timeline.append({
                            "type": "voting_resolution",
                            "timestamp": parse_timestamp(phase_end.get('timestamp', '')),
                            "round": round_num,
                            "scores": player_scores,
                            "running_scores": running_scores.copy(),
                            "vote_counts": vote_counts,
                            "winners": winners,
                            "message": "Votes tallied and points awarded"
                        })

                # Get phase end event
                if phase_end:
                    timestamp = parse_timestamp(phase_end.get('timestamp', ''))
                    timeline.append({
                        "type": "phase_end",
                        "timestamp": timestamp,
                        "round": round_num,
                        "phase": "resolution",
                        "message": "Resolution phase ended"
                    })

        # Add game end event
        game_end_event = next((e for e in events if e.get('event_type') == 'game_end'), None)
        if game_end_event:
            timestamp = parse_timestamp(game_end_event.get('timestamp', ''))
            timeline.append({
                "type": "game_end",
                "timestamp": timestamp,
                "message": "Game ended",
                "data": game_end_event.get('data', {}),
                "final_scores": running_scores.copy()
            })

        return timeline


class GameDetailGeneratorFactory:
    """Factory for creating game detail generators."""

    def __init__(self):
        self.generators = [
            PrisonersDilemmaDetailGenerator(),
            PoetryDetailGenerator(),
        ]

    def get_generator(self, config):
        """Get the appropriate generator for the game type."""
        for generator in self.generators:
            if generator.can_process(config):
                return generator
        return None


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

    # Get player models with both ID and friendly name
    player_models = {}
    llm_integration = config.get('llm_integration', {})
    for player_id, model in llm_integration.get('player_models', {}).items():
        player_models[player_id] = {
            'model_id': model,
            'model_name': extract_model_name(model)
        }

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
                    if record.get("record_type") == 'snapshot':
                        snapshots.append(record)
                    elif record.get("record_type") == 'event':
                        events.append(record)
                except:
                    continue
    except:
        return {"error": f"Failed to parse snapshots in {session_dir}"}

    # Get appropriate generator
    factory = GameDetailGeneratorFactory()
    generator = factory.get_generator(config)

    if not generator:
        return {"error": f"No generator found for game type: {config.get('game', {}).get('name')}"}

    # Generate timeline
    timeline = generator.generate_timeline(session_dir, config, results, chat_logs, snapshots, events, player_models)

    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x.get('timestamp', ''))

    # Create player information with both raw IDs and friendly names
    players_info = []
    for player_id, model_info in player_models.items():
        player_score = 0
        player_role = None

        for p in results.get('players', []):
            if p.get('id') == player_id:
                player_score = p.get('final_state', {}).get('score', 0)
                player_role = p.get('role')
                break

        players_info.append({
            "id": player_id,
            "model_id": model_info.get('model_id'),
            "model_name": model_info.get('model_name'),
            "final_score": player_score,
            "role": player_role
        })

    # Determine winning model name
    winning_model_name = None
    winner_id = results.get('winner', {}).get('id') if results.get('winner') else None
    if winner_id:
        for player in players_info:
            if player.get('id') == winner_id:
                winning_model_name = player.get('model_name')
                break

    # Gather additional game metadata
    game_data = {
        "session_id": os.path.basename(session_dir),
        "game_name": config.get('game', {}).get('name', "Unknown Game"),
        "player_models": player_models,
        "players": players_info,
        "rounds_played": results.get('rounds_played', 0),
        "winner": results.get('winner', {}).get('id'),
        "final_scores": {p.get('id'): p.get('final_state', {}).get('score')
                         for p in results.get('players', [])
                         if p.get('id') and p.get('final_state', {}).get('score') is not None}
    }

    # Add game summary for easy consumption by UI
    game_data["summary"] = {
        "outcome": "win" if winner_id else "tie",
        "winning_player_id": winner_id,
        "winning_model_name": winning_model_name,
        "final_scores_display": ", ".join([f"{p['model_name']}: {p['final_score']}" for p in players_info])
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
        if '_' in session_id and not any(game in session_id.lower() for game in ['prisoner', 'ghost', 'poetry', 'slam']):
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

    # Extract benchmark ID from benchmark_dir path
    benchmark_id = os.path.basename(benchmark_dir)

    # Create output directory
    detail_dir = os.path.join(output_dir, benchmark_id, "detail")
    os.makedirs(detail_dir, exist_ok=True)

    # Output file path
    output_file = os.path.join(detail_dir, f"{os.path.basename(session_dir)}.json")

    timeline_data = None
    # Check if this is a debate slam game
    if "debate_slam" in benchmark_id:
        print(f"Detected Debate Slam game, using debate_slam_processor")
        timeline_data = process_debate_session(session_dir, output_file, verbose=True)
    else:
        # Standard processing for non-debate games or if debate processor failed
        timeline_data = generate_game_timeline(session_dir)

    # Save detail data
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