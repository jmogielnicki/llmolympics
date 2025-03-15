#!/usr/bin/env python3
# scripts/process_data.py
import os
import json
import yaml
import pandas as pd
import numpy as np
from collections import defaultdict
from pathlib import Path
from common_utils import extract_model_name, get_session_directory


def load_benchmark_log(benchmark_dir):
    """Load the benchmark log JSONL file."""
    log_path = os.path.join(benchmark_dir, "benchmark_log.jsonl")
    logs = []

    with open(log_path, 'r') as f:
        for line in f:
            logs.append(json.loads(line))

    return logs


class GameProcessor:
    """Base class for game-specific processing logic."""

    def can_process(self, session_id):
        """Determine if this processor can handle this game type."""
        return False

    def generate_leaderboard(self, benchmark_logs, benchmark_dir):
        """Generate leaderboard data for this game type."""
        raise NotImplementedError

    def generate_matchup_matrix(self, benchmark_logs):
        """Generate matchup matrix for this game type."""
        raise NotImplementedError

    def analyze_game_decisions(self, session_dir, model_id):
        """Analyze decisions for a specific game."""
        raise NotImplementedError

    def generate_model_profiles(self, benchmark_logs, benchmark_dir):
        """Generate detailed model profiles."""
        raise NotImplementedError

    def analyze_round_progression(self, benchmark_logs, benchmark_dir):
        """Analyze progression across rounds."""
        raise NotImplementedError

    def get_decision_context(self, decision):
        """Get UI context for a decision."""
        return {
            "css_class": "bg-gray-500",
            "display_text": str(decision),
            "icon": "circle",
            "color": "gray"
        }


class PrisonersDilemmaProcessor(GameProcessor):
    """Processor for Prisoner's Dilemma game."""

    def can_process(self, session_id):
        """Determine if this processor can handle this game type."""
        return 'prisoner' in session_id.lower()

    def generate_leaderboard(self, benchmark_logs, benchmark_dir):
        """Generate leaderboard data for Prisoner's Dilemma."""
        models = {}

        # First pass: collect statistics
        for game in benchmark_logs:
            session_id = game.get('session_id', '')
            session_dir = get_session_directory(benchmark_dir, session_id)

            model1 = game['player1']['model']
            model2 = game['player2']['model']

            first_defector = self.analyze_first_to_defect(session_dir, [model1, model2])
            player1 = game['player1']
            player2 = game['player2']

            # Process player 1
            if model1 not in models:
                models[model1] = {
                    'full_name': model1,
                    'name': extract_model_name(model1),
                    'wins': 0,
                    'losses': 0,
                    'ties': 0,
                    'total_score': 0,
                    'games': 0,
                    'first_to_defect': 0
                }

            models[model1]['games'] += 1
            models[model1]['total_score'] += player1['score']

            # Process player 2
            if model2 not in models:
                models[model2] = {
                    'full_name': model2,
                    'name': extract_model_name(model2),
                    'wins': 0,
                    'losses': 0,
                    'ties': 0,
                    'total_score': 0,
                    'games': 0,
                    'first_to_defect': 0
                }

            models[model2]['games'] += 1
            models[model2]['total_score'] += player2['score']

            # Update win/loss/tie stats
            if game['winner'] == 'tie':
                models[model1]['ties'] += 1
                models[model2]['ties'] += 1
            elif game['winner'] == player1['id']:
                models[model1]['wins'] += 1
                models[model2]['losses'] += 1
            else:
                models[model1]['losses'] += 1
                models[model2]['wins'] += 1

            if first_defector == model1:
                models[model1]['first_to_defect'] += 1
            elif first_defector == model2:
                models[model2]['first_to_defect'] += 1

        # Format for output
        leaderboard = self._format_leaderboard(models)

        return {
            'leaderboard': leaderboard,
            'game_count': len(benchmark_logs)
        }

    def _format_leaderboard(self, models):
        """Format model data for leaderboard."""
        leaderboard = []
        for model_id, stats in models.items():
            winrate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            avg_score = stats['total_score'] / stats['games'] if stats['games'] > 0 else 0
            first_to_defect_count = stats['first_to_defect']
            first_to_defect_rate = first_to_defect_count / stats['games'] if stats['games'] > 0 else 0

            leaderboard.append({
                'model_id': model_id,
                'model_name': stats['name'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'ties': stats['ties'],
                'games': stats['games'],
                'winrate': round(winrate, 3),
                'avg_score': round(avg_score, 2),
                'first_to_defect_count': first_to_defect_count,
                'first_to_defect_rate': round(first_to_defect_rate, 3),
                'total_score': stats['total_score']
            })

        # Sort leaderboard by win rate (primary) and average score (secondary)
        leaderboard = sorted(leaderboard, key=lambda x: (x['winrate'], x['avg_score']), reverse=True)

        # Add rank
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1

        return leaderboard

    def generate_matchup_matrix(self, benchmark_logs):
        """Generate matchup matrix for Prisoner's Dilemma."""
        # Extract unique models
        models = set()
        for game in benchmark_logs:
            models.add(game['player1']['model'])
            models.add(game['player2']['model'])

        models = sorted(list(models))
        model_names = [extract_model_name(m) for m in models]

        # Initialize matchup data
        matchups = {}
        for model1 in models:
            matchups[model1] = {}
            for model2 in models:
                if model1 != model2:
                    matchups[model1][model2] = {
                        'wins': 0,
                        'losses': 0,
                        'ties': 0,
                        'games': 0
                    }

        # Populate matchup data
        for game in benchmark_logs:
            model1 = game['player1']['model']
            model2 = game['player2']['model']

            if model1 == model2:
                continue  # Skip same-model matchups

            matchups[model1][model2]['games'] += 1
            matchups[model2][model1]['games'] += 1

            if game['winner'] == 'tie':
                matchups[model1][model2]['ties'] += 1
                matchups[model2][model1]['ties'] += 1
            elif game['winner'] == game['player1']['id']:
                matchups[model1][model2]['wins'] += 1
                matchups[model2][model1]['losses'] += 1
            else:
                matchups[model1][model2]['losses'] += 1
                matchups[model2][model1]['wins'] += 1

        # Create matrix format (for heatmap)
        win_matrix = []
        winrate_matrix = []

        for model1 in models:
            win_row = []
            winrate_row = []

            for model2 in models:
                if model1 == model2:
                    win_row.append(None)  # Diagonal
                    winrate_row.append(None)
                else:
                    data = matchups[model1][model2]
                    # Count wins and half of ties
                    effective_wins = data['wins'] + (0.5 * data['ties'])
                    win_row.append(effective_wins)
                    winrate = effective_wins / data['games'] if data['games'] > 0 else 0
                    winrate_row.append(round(winrate, 2))

            win_matrix.append(win_row)
            winrate_matrix.append(winrate_row)

        return {
            'models': models,
            'model_names': model_names,
            'win_matrix': win_matrix,
            'winrate_matrix': winrate_matrix,
            'raw_matchups': matchups
        }

    def analyze_game_decisions(self, session_dir, model_id):
        """Analyze decisions for Prisoner's Dilemma."""
        # Map model ID to player ID
        with open(os.path.join(session_dir, "game_config.yaml"), 'r') as f:
            config = yaml.safe_load(f)

        player_id = None
        player_models = config.get('llm_integration', {}).get('player_models', {})
        for pid, mid in player_models.items():
            if mid == model_id:
                player_id = pid
                break

        if player_id is None:
            return None

        # Load snapshots to analyze decision pattern
        decisions = []
        decision_history = []

        with open(os.path.join(session_dir, "snapshots.jsonl"), 'r') as f:
            for line in f:
                data = json.loads(line)
                if data.get("record_type") == "snapshot":
                    # Look for decision history
                    history = data.get("history_state", {}).get("decision_history", [])
                    if history:
                        decision_history = history

        # Extract decisions for this player
        for round_data in decision_history:
            round_num = round_data.get("round", 0)
            decisions_dict = round_data.get("decisions", {})
            my_decision = decisions_dict.get(player_id)

            # Find opponent decision
            opponent_id = None
            opponent_decision = None
            for pid, decision in decisions_dict.items():
                if pid != player_id:
                    opponent_id = pid
                    opponent_decision = decision
                    break

            if my_decision:
                decisions.append({
                    "round": round_num,
                    "decision": my_decision,
                    "opponent_decision": opponent_decision
                })

        return decisions

    def generate_model_profiles(self, benchmark_logs, benchmark_dir):
        """Generate model profiles for Prisoner's Dilemma."""
        models = {}

        # Initial pass to identify all models
        for game in benchmark_logs:
            model1 = game['player1']['model']
            model2 = game['player2']['model']

            for model in [model1, model2]:
                if model not in models:
                    models[model] = {
                        'model_id': model,
                        'model_name': extract_model_name(model),
                        'games': [],
                        'stats': {}
                    }

        # For each game, gather data about the models
        for game in benchmark_logs:
            session_id = game.get('session_id', '')
            session_dir = get_session_directory(benchmark_dir, session_id)
            first_defector = self.analyze_first_to_defect(session_dir, [game['player1']['model'], game['player2']['model']])

            # Add game info to player 1's model
            model1 = game['player1']['model']
            models[model1]['games'].append({
                'session_id': session_id,
                'opponent': game['player2']['model'],
                'score': game['player1']['score'],
                'opponent_score': game['player2']['score'],
                'result': 'win' if game['winner'] == game['player1']['id'] else
                         'tie' if game['winner'] == 'tie' else 'loss',
                'decisions': self.analyze_game_decisions(session_dir, model1),
                'was_first_defector': first_defector == model1
            })

            # Add game info to player 2's model
            model2 = game['player2']['model']
            models[model2]['games'].append({
                'session_id': session_id,
                'opponent': game['player1']['model'],
                'score': game['player2']['score'],
                'opponent_score': game['player1']['score'],
                'result': 'win' if game['winner'] == game['player2']['id'] else
                         'tie' if game['winner'] == 'tie' else 'loss',
                'decisions': self.analyze_game_decisions(session_dir, model2),
                'was_first_defector': first_defector == model2
            })

        # Calculate statistics for each model
        self._calculate_pd_model_stats(models)

        return {
            'game_type': 'prisoners_dilemma',
            'models': list(models.values())
        }

    def _calculate_pd_model_stats(self, models):
        """Calculate Prisoner's Dilemma specific stats for models."""
        for model_id, profile in models.items():
            games = profile['games']
            cooperate_count = 0
            defect_count = 0
            first_move_cooperate = 0
            retaliation_rate = 0
            potential_retaliation = 0
            total_decisions = 0
            total_first_defections = 0

            for game in games:
                decisions = game.get('decisions', [])
                if not decisions:
                    continue

                # First move statistics
                if len(decisions) > 0 and decisions[0]['round'] == 1:
                    if decisions[0]['decision'] == 'cooperate':
                        first_move_cooperate += 1

                # Cooperation and defection counts
                for decision in decisions:
                    if decision['decision'] == 'cooperate':
                        cooperate_count += 1
                    else:
                        defect_count += 1
                    total_decisions += 1

                # Retaliation analysis - how often model defects after opponent defects
                for i in range(1, len(decisions)):
                    if decisions[i-1]['opponent_decision'] == 'defect':
                        potential_retaliation += 1
                        if decisions[i]['decision'] == 'defect':
                            retaliation_rate += 1
                if game.get('was_first_defector'):
                    total_first_defections += 1

            # Calculate rates
            cooperation_rate = cooperate_count / total_decisions if total_decisions > 0 else 0
            first_move_coop_rate = first_move_cooperate / len(games) if len(games) > 0 else 0
            retaliation = retaliation_rate / potential_retaliation if potential_retaliation > 0 else 0
            first_to_defect_rate = total_first_defections / len(games) if len(games) > 0 else 0

            profile['stats'] = {
                'cooperation_rate': round(cooperation_rate, 3),
                'defection_rate': round(1 - cooperation_rate, 3),
                'first_move_cooperation_rate': round(first_move_coop_rate, 3),
                'retaliation_rate': round(retaliation, 3),
                'total_decisions': total_decisions,
                'first_to_defect_rate': first_to_defect_rate
            }

    def analyze_first_to_defect(self, session_dir, model_ids):
        """Determine which model was first to defect in a game session."""
        # Load snapshots to analyze decision pattern
        decision_history = []

        with open(os.path.join(session_dir, "snapshots.jsonl"), 'r') as f:
            for line in f:
                data = json.loads(line)
                if data.get("record_type") == "snapshot":
                    # Look for decision history
                    history = data.get("history_state", {}).get("decision_history", [])
                    if history:
                        decision_history = history

        # Sort decisions by round
        decision_history.sort(key=lambda x: x.get('round', 0))

        # Find first defection
        for round_data in decision_history:
            decisions = round_data.get("decisions", {})
            for player_id, decision in decisions.items():
                if decision == "defect":
                    # Find which model this player_id maps to
                    with open(os.path.join(session_dir, "game_config.yaml"), 'r') as f:
                        config = yaml.safe_load(f)

                    player_models = config.get('llm_integration', {}).get('player_models', {})
                    model_id = player_models.get(player_id)

                    if model_id in model_ids:
                        return model_id

        return None  # No defection found

    def analyze_round_progression(self, benchmark_logs, benchmark_dir):
        """Analyze how cooperation/defection changes across rounds."""
        # For Prisoner's Dilemma, track cooperation by round
        round_stats = {}
        max_rounds = 0

        # Process all sessions
        for game in benchmark_logs:
            session_id = game.get('session_id', '')
            session_dir = get_session_directory(benchmark_dir, session_id)

            print(f"Looking for snapshots in: {session_dir}")

            # Load snapshots to get decision history
            snapshot_path = os.path.join(session_dir, "snapshots.jsonl")
            if not os.path.exists(snapshot_path):
                print(f"Snapshots file not found: {snapshot_path}")
                continue

            with open(snapshot_path, 'r') as f:
                # Find the last snapshot with complete history
                last_snapshot = None
                for line in f:
                    data = json.loads(line)
                    if data.get("record_type") == "snapshot":
                        # Look for decision history
                        if data.get("history_state", {}).get("decision_history"):
                            last_snapshot = data

                # Process the last snapshot with complete history
                if last_snapshot:
                    history = last_snapshot.get("history_state", {}).get("decision_history", [])
                    for round_data in history:
                        round_num = round_data.get("round", 0)
                        max_rounds = max(max_rounds, round_num)

                        if round_num not in round_stats:
                            round_stats[round_num] = {
                                'cooperation_count': 0,
                                'defection_count': 0,
                                'total_decisions': 0
                            }

                        decisions = round_data.get("decisions", {})
                        for player_id, decision in decisions.items():
                            if decision == 'cooperate':
                                round_stats[round_num]['cooperation_count'] += 1
                            else:
                                round_stats[round_num]['defection_count'] += 1
                            round_stats[round_num]['total_decisions'] += 1

        # Calculate cooperation rates by round
        round_progression = []
        for round_num in range(1, max_rounds + 1):
            if round_num in round_stats:
                stats = round_stats[round_num]
                coop_rate = stats['cooperation_count'] / stats['total_decisions'] if stats['total_decisions'] > 0 else 0

                round_progression.append({
                    'round': round_num,
                    'cooperation_rate': round(coop_rate, 3),
                    'defection_rate': round(1 - coop_rate, 3),
                    'cooperation_count': stats['cooperation_count'],
                    'defection_count': stats['defection_count'],
                    'total_decisions': stats['total_decisions']
                })

        return {
            'round_progression': round_progression,
            'max_rounds': max_rounds
        }

    def get_decision_context(self, decision):
        """Get UI context for a Prisoner's Dilemma decision."""
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


class PoetryProcessor(GameProcessor):
    """Processor for Poetry Slam game."""

    def can_process(self, session_id):
        """Determine if this processor can handle this game type."""
        return 'poetry' in session_id.lower() or 'slam' in session_id.lower()

    def generate_leaderboard(self, benchmark_logs, benchmark_dir):
        """Generate leaderboard data for Poetry Slam."""
        models = {}

        # First pass: collect statistics
        for game in benchmark_logs:
            players = game.get('players', [])
            winner_id = game.get('winner')

            # Handle tie case
            is_tie = winner_id == 'tie'

            # Process each player
            for player in players:
                model_id = player['model']
                player_id = player['id']

                if model_id not in models:
                    models[model_id] = {
                        'full_name': model_id,
                        'name': extract_model_name(model_id),
                        'wins': 0,
                        'losses': 0,
                        'ties': 0,
                        'total_score': 0,
                        'games': 0,
                        'first_to_defect': 0  # Keeping for consistency
                    }

                models[model_id]['games'] += 1
                models[model_id]['total_score'] += player.get('score', 0)

                # Update win/loss/tie stats
                if is_tie:
                    models[model_id]['ties'] += 1
                elif winner_id == player_id:
                    models[model_id]['wins'] += 1
                else:
                    models[model_id]['losses'] += 1

        # Format for output
        leaderboard = self._format_leaderboard(models)

        return {
            'leaderboard': leaderboard,
            'game_count': len(benchmark_logs)
        }

    def _format_leaderboard(self, models):
        """Format model data for leaderboard."""
        leaderboard = []
        for model_id, stats in models.items():
            winrate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            avg_score = stats['total_score'] / stats['games'] if stats['games'] > 0 else 0

            leaderboard.append({
                'model_id': model_id,
                'model_name': stats['name'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'ties': stats['ties'],
                'games': stats['games'],
                'winrate': round(winrate, 3),
                'avg_score': round(avg_score, 2),
                'first_to_defect_count': 0,  # N/A for Poetry Slam
                'first_to_defect_rate': 0.0,  # N/A for Poetry Slam
                'total_score': stats['total_score']
            })

        # Sort leaderboard by win rate (primary) and average score (secondary)
        leaderboard = sorted(leaderboard, key=lambda x: (x['winrate'], x['avg_score']), reverse=True)

        # Add rank
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1

        return leaderboard

    def generate_matchup_matrix(self, benchmark_logs):
        """Generate matchup matrix for Poetry Slam."""
        # Skip generating matchup matrix for Poetry Slam as requested
        return {
            'models': [],
            'model_names': [],
            'win_matrix': [],
            'winrate_matrix': [],
            'raw_matchups': {}
        }

    def analyze_game_decisions(self, session_dir, model_id):
        """Analyze voting decisions for Poetry Slam."""
        # Map model ID to player ID
        with open(os.path.join(session_dir, "game_config.yaml"), 'r') as f:
            config = yaml.safe_load(f)

        player_id = None
        player_models = config.get('llm_integration', {}).get('player_models', {})
        for pid, mid in player_models.items():
            if mid == model_id:
                player_id = pid
                break

        if player_id is None:
            return None

        # For Poetry Slam, analyze voting pattern
        decisions = []

        # Load chat logs to get voting information
        try:
            chat_logs = []
            with open(os.path.join(session_dir, "chat_logs.jsonl"), 'r') as f:
                for line in f:
                    try:
                        log = json.loads(line)
                        chat_logs.append(log)
                    except:
                        continue

            # Find voting phase logs for this player
            voting_logs = [log for log in chat_logs if log.get('player_id') == player_id and log.get('phase_id') == 'voting']

            # Find snapshots to get final votes
            snapshots = []
            with open(os.path.join(session_dir, "snapshots.jsonl"), 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get("record_type") == "snapshot":
                            snapshots.append(data)
                    except:
                        continue

            # Find the snapshot with voting results
            voting_results = None
            for snapshot in sorted(snapshots, key=lambda x: x.get('snapshot_id', 0), reverse=True):
                if 'voting_responses' in snapshot.get('shared_state', {}):
                    voting_results = snapshot.get('shared_state', {}).get('voting_responses', {})
                    break

            if voting_results:
                # Get this player's vote
                voted_for = voting_results.get(player_id)

                # Get votes received by this player
                votes_received = []
                for voter, vote in voting_results.items():
                    if vote == player_id:
                        votes_received.append(voter)

                decisions = {
                    "voted_for": voted_for,
                    "votes_received": votes_received,
                    "vote_count": len(votes_received)
                }
        except:
            pass

        return decisions

    def generate_model_profiles(self, benchmark_logs, benchmark_dir):
        """Generate model profiles for Poetry Slam."""
        models = {}

        # Initial pass to identify all models
        for game in benchmark_logs:
            players = game.get('players', [])
            for player in players:
                model = player['model']
                if model not in models:
                    models[model] = {
                        'model_id': model,
                        'model_name': extract_model_name(model),
                        'games': [],
                        'stats': {}
                    }

        # For each game, gather data about the models
        for game in benchmark_logs:
            session_id = game.get('session_id', '')
            session_dir = get_session_directory(benchmark_dir, session_id)

            players = game.get('players', [])
            winner_id = game.get('winner')
            is_tie = winner_id == 'tie'

            # Extract all player models in this game
            game_models = {player['id']: player['model'] for player in players}

            for player in players:
                model_id = player['model']
                player_id = player['id']

                # Create a list of other players in this game
                other_players = [p for p in players if p['id'] != player_id]
                other_models = [p['model'] for p in other_players]

                # Get voting decisions
                voting_data = self.analyze_game_decisions(session_dir, model_id)

                # Add game info to model's profile
                models[model_id]['games'].append({
                    'session_id': session_id,
                    'role': 'prompter' if player.get('is_prompter') else 'author',
                    'score': player.get('score', 0),
                    'result': 'win' if winner_id == player_id else 'tie' if is_tie else 'loss',
                    'other_players': other_models,
                    'voting': voting_data
                })

        # Calculate statistics for each model
        self._calculate_poetry_model_stats(models)

        return {
            'game_type': 'poetry_slam',
            'models': list(models.values())
        }

    def _calculate_poetry_model_stats(self, models):
        """Calculate Poetry Slam specific stats for models."""
        for model_id, profile in models.items():
            games = profile['games']

            # Poetry Slam specific stats
            prompter_count = 0
            total_votes_received = 0
            total_vote_actions = 0

            for game in games:
                if game.get('role') == 'prompter':
                    prompter_count += 1

                voting_data = game.get('voting', {})
                if isinstance(voting_data, dict):
                    # Count votes received
                    votes_received = len(voting_data.get('votes_received', []))
                    total_votes_received += votes_received

                    # Count vote actions (when this model voted for someone)
                    if voting_data.get('voted_for'):
                        total_vote_actions += 1

            # Calculate aggregate stats
            prompter_rate = prompter_count / len(games) if len(games) > 0 else 0
            avg_votes_received = total_votes_received / len(games) if len(games) > 0 else 0

            profile['stats'] = {
                'prompter_rate': round(prompter_rate, 3),
                'avg_votes_received': round(avg_votes_received, 3),
                'total_votes_received': total_votes_received,
                'total_vote_actions': total_vote_actions,
                'total_games': len(games)
            }

    def analyze_round_progression(self, benchmark_logs, benchmark_dir):
        """Analyze round progression for Poetry Slam (empty implementation)."""
        # Skip round progression for Poetry Slam as requested
        return {
            'round_progression': [],
            'max_rounds': 0
        }

    def get_decision_context(self, decision):
        """Get UI context for a Poetry Slam decision (voting)."""
        return {
            "css_class": "bg-blue-500",
            "display_text": f"Voted for {decision}",
            "icon": "thumb-up",
            "color": "blue"
        }


class GameProcessorFactory:
    """Factory for creating game-specific processors."""

    def __init__(self):
        self.processors = [
            PrisonersDilemmaProcessor(),
            PoetryProcessor()
        ]

    def get_processor(self, session_id):
        """Get the appropriate processor for the game type."""
        for processor in self.processors:
            if processor.can_process(session_id):
                return processor
        return None


def process_benchmark(benchmark_dir, output_dir="data/processed"):
    """
    Process a complete benchmark directory to generate visualization data.

    Args:
        benchmark_dir: Path to benchmark directory
        output_dir: Output directory for processed data
    """
    print(f"Processing benchmark: {benchmark_dir}")

    # Load benchmark logs
    benchmark_logs = load_benchmark_log(benchmark_dir)
    print(f"Loaded {len(benchmark_logs)} game logs")

    # Extract benchmark ID
    benchmark_id = os.path.basename(benchmark_dir)

    # Get appropriate processor
    factory = GameProcessorFactory()
    session_id = benchmark_logs[0].get('session_id', '') if benchmark_logs else ''
    processor = factory.get_processor(session_id)

    if not processor:
        print(f"No processor found for game type: {session_id}")
        return None

    # Create high-level visualization datasets
    print("Generating leaderboard...")
    leaderboard = processor.generate_leaderboard(benchmark_logs, benchmark_dir)

    print("Generating matchup matrix...")
    matchup_matrix = processor.generate_matchup_matrix(benchmark_logs)

    print("Generating model profiles...")
    model_profiles = processor.generate_model_profiles(benchmark_logs, benchmark_dir)

    print("Analyzing round progression...")
    round_progression = processor.analyze_round_progression(benchmark_logs, benchmark_dir)

    # Create output directory
    os.makedirs(os.path.join(output_dir, benchmark_id), exist_ok=True)

    # Save processed data
    with open(os.path.join(output_dir, benchmark_id, "leaderboard.json"), 'w') as f:
        json.dump(leaderboard, f, indent=2)

    with open(os.path.join(output_dir, benchmark_id, "matchup_matrix.json"), 'w') as f:
        json.dump(matchup_matrix, f, indent=2)

    with open(os.path.join(output_dir, benchmark_id, "model_profiles.json"), 'w') as f:
        json.dump(model_profiles, f, indent=2)

    with open(os.path.join(output_dir, benchmark_id, "round_progression.json"), 'w') as f:
        json.dump(round_progression, f, indent=2)

    # Generate metadata
    game_type = 'poetry_slam' if 'poetry' in benchmark_id else 'prisoners_dilemma'

    if game_type == 'poetry_slam':
        unique_models = set([player['model'] for game in benchmark_logs for player in game.get('players', [])])
        num_models = len(unique_models)
    else:
        num_models = len(matchup_matrix['models'])

    metadata = {
        "benchmark_id": benchmark_id,
        "game_count": len(benchmark_logs),
        "models": num_models,
        "processed_at": pd.Timestamp.now().isoformat(),
    }

    with open(os.path.join(output_dir, benchmark_id, "metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Processing complete! Data saved to {os.path.join(output_dir, benchmark_id)}")
    return metadata


def process_all_benchmarks(data_dir="data", output_dir="data/processed"):
    """
    Process all benchmarks in the data directory.

    Args:
        data_dir: Base data directory
        output_dir: Output directory for processed data
    """
    benchmark_dir = os.path.join(data_dir, "benchmark")

    # List all benchmark directories
    benchmarks = []
    for item in os.listdir(benchmark_dir):
        full_path = os.path.join(benchmark_dir, item)
        if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "benchmark_log.jsonl")):
            benchmarks.append(full_path)

    print(f"Found {len(benchmarks)} benchmarks to process")

    # Process each benchmark
    results = []
    for benchmark_path in benchmarks:
        result = process_benchmark(benchmark_path, output_dir)
        if result:
            results.append(result)

    # Create an index of all processed benchmarks
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "index.json"), 'w') as f:
        json.dump({
            "benchmarks": results,
            "updated_at": pd.Timestamp.now().isoformat()
        }, f, indent=2)

    print(f"All benchmarks processed successfully!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process ParlourBench benchmark data for visualization")
    parser.add_argument("--benchmark", help="Process a specific benchmark directory")
    parser.add_argument("--all", action="store_true", help="Process all benchmarks")
    parser.add_argument("--output", default="data/processed", help="Output directory for processed data")

    args = parser.parse_args()

    if args.benchmark:
        process_benchmark(args.benchmark, args.output)
    elif args.all:
        process_all_benchmarks(output_dir=args.output)
    else:
        print("Please specify either --benchmark or --all")