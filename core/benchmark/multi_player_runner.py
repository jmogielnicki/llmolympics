# core/benchmark/multi_player_runner.py
import os
import yaml
import json
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Set, Tuple, Any
import itertools
import numpy as np

# Import from core modules
from core.benchmark.config import BenchmarkConfig
from core.game.engine import GameEngine
from core.game.config import ConfigLoader

logger = logging.getLogger("MultiPlayerBenchmarkRunner")

class MultiPlayerBenchmarkRunner:
    """
    Manages the execution of multi-player model benchmarks.

    This extends the standard BenchmarkRunner to support games
    with more than 2 players, using the "opponent diversity first"
    selection strategy.
    """

    def __init__(self, benchmark_config: BenchmarkConfig):
        """
        Initialize the multi-player benchmark runner.

        Args:
            benchmark_config (BenchmarkConfig): The benchmark configuration
        """
        self.benchmark_config = benchmark_config
        self.output_dir = benchmark_config.get_output_dir()
        self.log_path = os.path.join(self.output_dir, "benchmark_log.jsonl")
        self.state_path = os.path.join(self.output_dir, "benchmark_state.json")

        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Load the base game configuration
        self.base_game_config_path = benchmark_config.get_base_game_config_path()
        self.base_game_config = ConfigLoader.load(self.base_game_config_path)

        # Get multi-player specific settings
        self.players_per_game = benchmark_config.config['benchmark'].get('players_per_game', 4)
        self.sessions = benchmark_config.config['benchmark'].get('sessions', 50)

        # Get selection strategy
        self.selection = benchmark_config.config['benchmark'].get('selection', {})
        self.prompter_selection = self.selection.get('prompter_selection', 'weighted_inverse')

        # Get models
        self.models = benchmark_config.get_models()

        # Initialize tracking state
        self.opponent_matrix = {}  # Maps model -> set of opponents faced
        self.game_counts = {}      # Maps model -> number of games played
        self.prompter_counts = {}  # Maps model -> number of times as prompter
        self.sessions_run = 0

        # Load existing state if available
        self._load_state()

        logger.info(f"Initialized multi-player benchmark runner for {benchmark_config.get_benchmark_id()}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Models: {len(self.models)}, Players per game: {self.players_per_game}")

    def _load_state(self) -> None:
        """
        Load the existing benchmark state if it exists.
        """
        if not os.path.exists(self.state_path):
            # Initialize fresh state
            for model in self.models:
                self.opponent_matrix[model] = set()
                self.game_counts[model] = 0
                self.prompter_counts[model] = 0
            logger.info("No existing benchmark state found, starting fresh")
            return

        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)

            # Reload state
            self.opponent_matrix = {model: set(opponents) for model, opponents in state.get('opponent_matrix', {}).items()}
            self.game_counts = state.get('game_counts', {})
            self.prompter_counts = state.get('prompter_counts', {})
            self.sessions_run = state.get('sessions_run', 0)

            # Handle new models that weren't in the previous state
            for model in self.models:
                if model not in self.opponent_matrix:
                    self.opponent_matrix[model] = set()
                if model not in self.game_counts:
                    self.game_counts[model] = 0
                if model not in self.prompter_counts:
                    self.prompter_counts[model] = 0

            logger.info(f"Loaded benchmark state: {self.sessions_run} sessions run")

        except Exception as e:
            logger.error(f"Error loading benchmark state: {str(e)}")
            # Initialize fresh state as fallback
            for model in self.models:
                self.opponent_matrix[model] = set()
                self.game_counts[model] = 0
                self.prompter_counts[model] = 0

    def _save_state(self) -> None:
        """
        Save the current benchmark state.
        """
        try:
            state = {
                'opponent_matrix': {model: list(opponents) for model, opponents in self.opponent_matrix.items()},
                'game_counts': self.game_counts,
                'prompter_counts': self.prompter_counts,
                'sessions_run': self.sessions_run
            }

            with open(self.state_path, 'w') as f:
                json.dump(state, f, indent=2)

            logger.info(f"Saved benchmark state after {self.sessions_run} sessions")

        except Exception as e:
            logger.error(f"Error saving benchmark state: {str(e)}")

    def _select_models_for_session(self) -> List[str]:
        """
        Select models for the next session using the opponent diversity first strategy.

        Returns:
            List[str]: List of selected model identifiers
        """
        # Calculate opponent diversity percentage for each model
        diversity_scores = {}
        for model in self.models:
            # Consider only models the current model hasn't faced yet
            if len(self.opponent_matrix[model]) == 0:
                # If model hasn't played any games, give it highest priority
                diversity_scores[model] = 0
            else:
                # Calculate percentage of unique opponents faced
                diversity_scores[model] = len(self.opponent_matrix[model]) / (len(self.models) - 1)

        # Select the anchor model (with lowest diversity score)
        anchor_model = min(diversity_scores, key=diversity_scores.get)
        logger.info(f"Selected anchor model: {anchor_model} with diversity score {diversity_scores[anchor_model]:.2f}")

        # Start with the anchor model
        selected_models = [anchor_model]

        # Find all models the anchor hasn't faced yet
        unfaced_opponents = [model for model in self.models
                             if model != anchor_model and model not in self.opponent_matrix[anchor_model]]

        # If we have enough unfaced opponents to fill the game, sort by games_played and take top N
        if len(unfaced_opponents) >= self.players_per_game - 1:
            # Sort by lowest game count
            unfaced_opponents.sort(key=lambda model: self.game_counts.get(model, 0))
            # Take the top N-1 models
            selected_models.extend(unfaced_opponents[:self.players_per_game - 1])
        else:
            # Add all unfaced opponents
            selected_models.extend(unfaced_opponents)

            # Fill remaining slots with models that have been faced the least
            remaining_slots = self.players_per_game - len(selected_models)
            if remaining_slots > 0:
                # Get models not already selected
                remaining_models = [model for model in self.models if model not in selected_models]

                # Sort by game count and diversity score
                remaining_models.sort(key=lambda model: (
                    self.game_counts.get(model, 0),
                    diversity_scores.get(model, 1.0)
                ))

                # Add remaining models
                selected_models.extend(remaining_models[:remaining_slots])

        # Ensure we have exactly players_per_game models
        if len(selected_models) < self.players_per_game:
            logger.warning(f"Not enough models to fill game: {len(selected_models)}/{self.players_per_game}")
            # Add random models to fill (this shouldn't normally happen)
            available_models = [model for model in self.models if model not in selected_models]
            selected_models.extend(random.sample(available_models,
                                               min(self.players_per_game - len(selected_models),
                                                  len(available_models))))

        # Ensure we have at most players_per_game models
        selected_models = selected_models[:self.players_per_game]

        logger.info(f"Selected models for session: {selected_models}")
        return selected_models

    def _select_prompter(self, models: List[str]) -> str:
        """
        Select a prompter from the models using weighted inverse selection.

        Args:
            models (List[str]): List of models to choose from

        Returns:
            str: The selected prompter model
        """
        if self.prompter_selection == 'weighted_inverse':
            # Calculate weights: 1 / (prompter_count + 1)
            weights = [1.0 / (self.prompter_counts.get(model, 0) + 1.0) for model in models]

            # Normalize weights
            total_weight = sum(weights)
            probabilities = [w / total_weight for w in weights]

            # Weighted random selection
            prompter = np.random.choice(models, p=probabilities)
            logger.info(f"Selected prompter {prompter} using weighted selection")
            return prompter
        else:
            # Default to random selection
            prompter = random.choice(models)
            logger.info(f"Selected prompter {prompter} using random selection")
            return prompter

    def run_benchmark(self) -> None:
        """
        Run the benchmark for the specified number of sessions.
        """
        logger.info(f"Starting benchmark with {self.sessions - self.sessions_run} sessions remaining")
        start_time = time.time()

        # Run remaining sessions
        for i in range(self.sessions_run, self.sessions):
            logger.info(f"Running session {i+1}/{self.sessions}")
            try:
                # Select models for this session
                selected_models = self._select_models_for_session()

                # Select prompter
                prompter_model = self._select_prompter(selected_models)

                # Run the session
                session_id, session_dir = self._run_session(selected_models, prompter_model)

                # Update state
                self._update_state_after_session(selected_models, prompter_model)

                # Save current state
                self._save_state()

                # Log the result
                self._log_session_result(selected_models, prompter_model, session_id, session_dir)

                # Update counter
                self.sessions_run += 1

            except Exception as e:
                logger.error(f"Error running session {i+1}: {str(e)}")
                # Continue with the next session
                continue

        # Calculate benchmark stats
        elapsed_time = time.time() - start_time
        logger.info(f"Benchmark complete. Ran {self.sessions_run} sessions in {elapsed_time:.2f} seconds")

    def _update_state_after_session(self, models: List[str], prompter: str) -> None:
        """
        Update tracking state after a session.

        Args:
            models (List[str]): Models that participated in the session
            prompter (str): Model that was the prompter
        """
        # Update opponent matrix for each model
        for model in models:
            # Add all other models in the session as opponents
            for opponent in models:
                if opponent != model:
                    self.opponent_matrix[model].add(opponent)

            # Increment game count
            self.game_counts[model] = self.game_counts.get(model, 0) + 1

        # Increment prompter count
        self.prompter_counts[prompter] = self.prompter_counts.get(prompter, 0) + 1

    def _run_session(self, models: List[str], prompter: str) -> Tuple[str, str]:
        """
        Run a single poetry slam session with the specified models.

        Args:
            models (List[str]): Models participating in the session
            prompter (str): Model designated as the prompter

        Returns:
            tuple: (session_id, session_dir) of the completed session
        """
        # Create a modified game config with the specified models
        game_config = self.base_game_config.copy()

        # Ensure llm_integration section exists
        if 'llm_integration' not in game_config:
            game_config['llm_integration'] = {}

        # Set player models
        if 'player_models' not in game_config['llm_integration']:
            game_config['llm_integration']['player_models'] = {}

        # Assign models to player slots
        for i, model in enumerate(models, 1):
            player_id = f"player_{i}"
            game_config['llm_integration']['player_models'][player_id] = model

        # Set up roles - make one model the prompter
        # First, ensure all players are authors
        for i in range(1, len(models) + 1):
            game_config['llm_integration']['player_models'][f"player_{i}"] = models[i-1]

        # Find which player has the prompter model
        prompter_player_id = None
        for i, model in enumerate(models, 1):
            if model == prompter:
                prompter_player_id = f"player_{i}"
                break

        # Update setup to assign prompter role
        if 'setup' not in game_config:
            game_config['setup'] = {}

        if 'assignments' not in game_config['setup']:
            game_config['setup']['assignments'] = []

        # Clear existing assignments
        prompter_assignments = [a for a in game_config['setup']['assignments'] if a.get('role') == 'prompter']
        for assignment in prompter_assignments:
            game_config['setup']['assignments'].remove(assignment)

        # Add new prompter assignment
        game_config['setup']['assignments'].append({
            'role': 'prompter',
            'assignment_to': prompter_player_id
        })

        # Create a temp config file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_config_path = os.path.join(self.output_dir, f"temp_config_{timestamp}.yaml")

        with open(temp_config_path, 'w') as f:
            yaml.dump(game_config, f)

        try:
            # Initialize and run the game
            engine = GameEngine(temp_config_path, base_output_dir=self.output_dir)
            engine.run_game()

            # Get the session ID and directory
            session_id = engine.game_session.session_id
            session_dir = engine.game_session.session_dir

            # Clean up the temp config file
            os.remove(temp_config_path)

            return session_id, session_dir
        except Exception as e:
            # Clean up the temp config file on error
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)
            raise

    def _log_session_result(self, models: List[str], prompter: str, session_id: str, session_dir: str) -> None:
        """
        Log the result of a session to the benchmark log.

        Args:
            models (List[str]): Models that participated in the session
            prompter (str): Model that was the prompter
            session_id (str): Session ID of the completed game
            session_dir (str): Directory of the session
        """
        # Find the game results file
        results_path = os.path.join(session_dir, "results.json")

        if not os.path.exists(results_path):
            logger.error(f"Results file not found: {results_path}")
            return

        try:
            # Load the game results
            with open(results_path, 'r') as f:
                results = json.load(f)

            # Build player results
            player_results = []
            for i, model in enumerate(models, 1):
                player_id = f"player_{i}"
                player_data = next((p for p in results.get('players', []) if p.get('id') == player_id), {})

                player_results.append({
                    "id": player_id,
                    "model": model,
                    "score": player_data.get('final_state', {}).get('score'),
                    "is_prompter": (model == prompter)
                })

            # Create the log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "game_config_hash": self.benchmark_config.get_base_game_config_hash(),
                "session_id": session_id,
                "session_number": self.sessions_run + 1,
                "players": player_results,
                "winner": results.get('winner', {}).get('id') if results.get('winner') else "tie",
                "prompter": prompter,
                "benchmark_id": self.benchmark_config.get_benchmark_id()
            }

            # Append to the log file
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")

            logger.info(f"Logged result for session {self.sessions_run + 1}, winner: {log_entry['winner']}")
        except Exception as e:
            logger.error(f"Error logging session result: {str(e)}")