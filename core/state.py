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

    def __init__(self, config):
        """
        Initialize a game state from a configuration.

        Args:
            config (dict): The game configuration
        """
        self.config = config
        self.players = self._initialize_players()
        self.shared_state = self._initialize_shared_state()
        self.hidden_state = self._initialize_hidden_state()
        self.history_state = self._initialize_history_state()

        # Set initial phase to the first phase in the configuration
        self.current_phase = config['phases'][0]['id']
        self.game_over = False
        self.history = []

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
                'state': {}
            }

            # Apply initial state values from config
            for state_item in self.config['state'].get('player_state', []):
                player['state'][state_item['name']] = state_item.get('initial', None)

            # Handle role assignments if present
            if 'setup' in self.config and 'assignments' in self.config['setup']:
                for assignment in self.config['setup'].get('assignments', []):
                    if assignment.get('assignment_to') == f"player_{i+1}":
                        player['role'] = assignment.get('role')

            players.append(player)

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

    def save_snapshot(self):
        """
        Save a snapshot of the current game state.

        Creates a JSON-serializable snapshot of the current state
        and appends it to the history. Also writes the snapshot to
        a file for persistence.
        """
        # Create a JSON-serializable snapshot
        snapshot = {
            'timestamp': time.time(),
            'players': copy.deepcopy(self.players),
            'shared_state': copy.deepcopy(self.shared_state),
            'hidden_state': copy.deepcopy(self.hidden_state),
            'history_state': copy.deepcopy(self.history_state),
            'current_phase': self.current_phase,
            'game_over': self.game_over,
            'config': {
                'game_name': self.config['game']['name'],
                'player_count': len(self.players)
            }
        }
        self.history.append(snapshot)

        # Get directory from environment variable or use default
        snapshots_dir = os.environ.get("PARLOURBENCH_SNAPSHOT_DIR", "data/snapshots")

        # Ensure directory exists
        os.makedirs(snapshots_dir, exist_ok=True)

        # Generate a unique filename
        snapshot_id = int(time.time() * 1000)
        game_name = self.config['game']['name'].lower().replace(' ', '_')
        filename = f"{game_name}_snapshot_{snapshot_id}.json"

        # Write to file
        with open(f"{snapshots_dir}/{filename}", 'w') as f:
            json.dump(snapshot, f, indent=2)

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
            if history_item.get('tracking') == current_phase:
                self.history_state[history_item['name']].append({
                    'round': self.shared_state.get('current_round', 0),
                    'responses': responses,
                    'timestamp': time.time()
                })
                break

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
            dict or None: The winning player object, or None if no winner
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

            return max(
                active_players,
                key=lambda p: p['state'].get(score_field, 0)
            )

        return None

    def save_results(self):
        """
        Save the final game results to a file.

        Args:
            results_dir (str): Directory to save results to
        """
        if not self.game_over:
            raise ValueError("Cannot save results for a game that's not over")

        results_dir = os.environ.get("PARLOURBENCH_RESULTS_DIR", "data/results")

        # Ensure directory exists
        os.makedirs(results_dir, exist_ok=True)

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
            'winner': self.get_winner()['id'] if self.get_winner() else None,
            'rounds_played': self.shared_state.get('current_round', 0),
            'history_summary': {
                key: len(value) for key, value in self.history_state.items()
            }
        }

        # Generate a unique filename
        result_id = int(time.time() * 1000)
        game_name = self.config['game']['name'].lower().replace(' ', '_')
        filename = f"{game_name}_result_{result_id}.json"

        # Write to file
        with open(f"{results_dir}/{filename}", 'w') as f:
            json.dump(results, f, indent=2)

        return filename