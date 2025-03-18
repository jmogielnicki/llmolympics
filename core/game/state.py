# core/state.py
import os
import json
import time
import copy

class GameState:
    """
    Represents and manages the state of a game.

    Handles player state, shared state, hidden state, and history
    tracking throughout the game. Provides methods for state updates
    and history snapshots.
    """

    def __init__(self, config, game_session=None):
        """
        Initialize a game state from a configuration.

        Args:
            config (dict): The game configuration
            game_session: Optional GameSession for unified logging
        """
        self.config = config
        self.game_session = game_session
        self.players = self._initialize_players()
        self.shared_state = self._initialize_shared_state()
        self.hidden_state = self._initialize_hidden_state()
        self.history_state = self._initialize_history_state()

        # Set initial phase to the first phase in the configuration
        self.current_phase = config['phases'][0]['id']
        self.game_over = False
        self.history = []

        # These will be set by GameEngine
        self.chat_logger = None
        self.llm_client_class = None

        # Store phase result for conditional phase transitions
        self.phase_result = None

    def _initialize_players(self):
        """
        Initialize player state based on configuration.

        Returns:
            list: List of player objects with initial state
        """
        player_count = self.config['players'].get('max', 2)
        players = []

        # Create player objects
        for i in range(player_count):
            player = {
                'id': f"player_{i+1}",
                'state': {},
                'roles': []  # Support multiple roles per player
            }

            # Apply initial state values from config
            for state_item in self.config['state'].get('player_state', []):
                player['state'][state_item['name']] = state_item.get('initial', None)

            players.append(player)

        # Handle role assignments if present
        if 'setup' in self.config and 'assignments' in self.config['setup']:
            assignments = self.config['setup']['assignments']

            # Process all assignments
            for assignment in assignments:
                role = assignment.get('role')
                target = assignment.get('assignment_to')

                if target == 'random_player':
                    import random
                    selected_player = random.choice(players)
                    if role not in selected_player['roles']:
                        selected_player['roles'].append(role)
                    selected_player['state']['role'] = role  # Legacy support
                    # logger.info(f"Assigned role '{role}' to random player {selected_player['id']}")

                elif target == 'all_players':
                    for player in players:
                        if role not in player['roles']:
                            player['roles'].append(role)
                        # Only set state.role if not already set to preserve primary role
                        if not player['state'].get('role'):
                            player['state']['role'] = role
                    # logger.info(f"Assigned role '{role}' to all players")

                else:
                    # Direct assignment to specific player
                    for player in players:
                        if player['id'] == target:
                            if role not in player['roles']:
                                player['roles'].append(role)
                            player['state']['role'] = role  # Legacy support
                            # logger.info(f"Assigned role '{role}' to player {player['id']}")
                            break

            # For backward compatibility, set the 'role' field to the primary role
            for player in players:
                if player['roles']:
                    # Use the first (presumably most important) role as the primary
                    player['role'] = player['roles'][0]
                else:
                    player['role'] = None

                # logger.info(f"Player {player['id']} has roles: {player['roles']}, primary: {player['role']}")

        return players

    def _initialize_shared_state(self):
        """
        Initialize shared game state.

        Returns:
            dict: Shared state with initial values
        """
        shared_state = {}

        for state_item in self.config['state'].get('shared_state', []):
            shared_state[state_item['name']] = state_item.get('initial', None)

        return shared_state

    def _initialize_hidden_state(self):
        """
        Initialize hidden game state.

        Returns:
            dict: Hidden state with initial values
        """
        hidden_state = {}

        for state_item in self.config['state'].get('hidden_state', []):
            hidden_state[state_item['name']] = state_item.get('initial', None)

        return hidden_state

    def _initialize_history_state(self):
        """
        Initialize history tracking.

        Returns:
            dict: History state containers
        """
        history_state = {}

        for track_item in self.config['state'].get('history_state', []):
            history_state[track_item['name']] = []

        return history_state

    def save_snapshot(self, is_initial=False):
        """
        Save a snapshot of the current game state.

        Creates a JSON-serializable snapshot of the current state
        and appends it to the history. Also writes the snapshot to
        a file for persistence.

        Args:
            is_initial (bool): Whether this is the initial state

        Returns:
            int: Snapshot ID
        """
        # Create a JSON-serializable snapshot
        snapshot = {
            'timestamp': time.time(),
            'players': copy.deepcopy(self.players),
            'shared_state': copy.deepcopy(self.shared_state),
            'hidden_state': copy.deepcopy(self.hidden_state),
            'history_state': copy.deepcopy(self.history_state),
            'current_phase': is_initial and 'initial' or self.current_phase,
            'game_over': self.game_over,
            'config': {
                'game_name': self.config['game']['name'],
                'player_count': len(self.players)
            }
        }
        self.history.append(snapshot)

        # If we have a game session, use it
        if self.game_session:
            snapshot_id = self.game_session.save_snapshot(snapshot)
            return snapshot_id

    def get_active_players(self):
        """
        Get all active (non-eliminated) players.

        Returns:
            list: List of active player objects
        """
        return [p for p in self.players if p['state'].get('active', True)]

    def get_active_player_count(self):
        """
        Get the count of active players.

        Returns:
            int: Number of active players
        """
        return len(self.get_active_players())

    def eliminate_player(self, player_id):
        """
        Mark a player as eliminated.

        Args:
            player_id (str): ID of the player to eliminate

        Returns:
            bool: True if player was found and eliminated, False otherwise
        """
        for player in self.players:
            if player['id'] == player_id:
                player['state']['active'] = False

                # Record elimination in history if tracking exists
                if 'elimination_record' in self.history_state:
                    self.history_state['elimination_record'].append({
                        'player': player_id,
                        'round': self.shared_state.get('current_round', 0),
                        'timestamp': time.time()
                    })
                return True
        return False

    def get_votes(self):
        """
        Get the current voting state.

        Returns:
            dict: Current votes mapping player IDs to their vote choices
        """
        return self.shared_state.get('votes', {})

    def set_action_responses(self, responses):
        """
        Store action responses in appropriate history tracker.

        Args:
            responses (dict): Map of player IDs to their responses
        """
        # Determine where to store based on current phase
        current_phase = self.current_phase

        for history_item in self.config['state'].get('history_state', []):
            tracking = history_item.get('tracking')

            # Skip if tracking is not configured
            if not tracking:
                continue

            # Check if tracking is a list or a string
            if isinstance(tracking, list) and current_phase in tracking:
                # Handle list of tracking phases
                self.history_state[history_item['name']].append({
                    'round': self.shared_state.get('current_round', 0),
                    'responses': responses,
                    'timestamp': time.time()
                })
            elif isinstance(tracking, str) and tracking == current_phase:
                # Handle string tracking phase (original behavior)
                self.history_state[history_item['name']].append({
                    'round': self.shared_state.get('current_round', 0),
                    'responses': responses,
                    'timestamp': time.time()
                })
            # If tracking isn't a list or string that matches, do nothing

        # Store in shared state for current round processing
        self.shared_state[f"{current_phase}_responses"] = responses

    def is_game_over(self):
        """
        Check if the game is over.

        Returns:
            bool: True if the game is over, False otherwise
        """
        return self.game_over

    def get_winner(self):
        """
        Get the winner of the game based on win condition.

        Returns:
            dict or None: The winning player object, a special 'tie' object, or None if no winner
        """
        if not self.game_over:
            return None

        win_condition = self.config.get('win_condition', {})
        win_type = win_condition.get('type')

        if win_type == 'last_player_standing':
            active_players = self.get_active_players()
            if len(active_players) == 1:
                return active_players[0]

        elif win_type == 'highest_score':
            score_field = win_condition.get('score_field', 'score')
            active_players = self.get_active_players()

            if not active_players:
                return None

            # Find the maximum score
            max_score = max((p['state'].get(score_field, 0) for p in active_players), default=0)

            # Find all players with the maximum score
            players_with_max_score = [p for p in active_players if p['state'].get(score_field, 0) == max_score]

            # If only one player has the max score, they win
            if len(players_with_max_score) == 1:
                return players_with_max_score[0]
            else:
                # Return a tie object with the tied players
                return {
                    'id': 'tie',
                    'state': {'score': max_score},
                    'tied_players': [p['id'] for p in players_with_max_score]
                }

        return None

    def save_results(self):
        """
        Save the final game results to a file.

        Returns:
            str: Path to the results file
        """
        if not self.game_over:
            raise ValueError("Cannot save results for a game that's not over")

        winner = self.get_winner()
        winner_data = None if not winner else (
            {'id': winner['id'], 'tied_players': winner.get('tied_players')}
            if winner['id'] == 'tie'
            else {'id': winner['id']}
        )

        # Create results object
        results = {
            'game': self.config['game']['name'],
            'timestamp': time.time(),
            'players': [
                {
                    'id': p['id'],
                    'final_state': p['state'],
                    'role': p.get('role')
                }
                for p in self.players
            ],
            'winner': winner_data,
            'rounds_played': self.shared_state.get('current_round', 0),
            'history_summary': {
                key: len(value) for key, value in self.history_state.items()
            }
        }

        # If we have a game session, use it
        if self.game_session:
            results_path = self.game_session.save_results(results)
            return results_path