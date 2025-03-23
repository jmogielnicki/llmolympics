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

    Supports configurable role assignments and selection strategies
    for games with complex role relationships.
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
        self.player_selection_strategy = benchmark_config.config['benchmark'].get('player_selection_strategy', 'opponent_diversity')
        self.player_selection_strategy_role = benchmark_config.config['benchmark'].get('player_selection_strategy_role', '')

        # Get roles configuration
        self.roles_config = benchmark_config.config['benchmark'].get('roles', {})

        # Validate role configuration
        self._validate_roles_config()

        # Get models
        self.models = benchmark_config.get_models()

        # Initialize tracking state
        self.opponent_matrix = {}  # Maps model -> set of opponents faced
        self.game_counts = {}      # Maps model -> number of games played
        self.role_counts = {}      # Maps model -> {role -> count}
        self.sessions_run = 0

        # Load existing state if available
        self._load_state()

        logger.info(f"Initialized multi-player benchmark runner for {benchmark_config.get_benchmark_id()}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Models: {len(self.models)}, Players per game: {self.players_per_game}")
        logger.info(f"Roles: {list(self.roles_config.keys())}")

    def _validate_roles_config(self):
        """
        Validate the roles configuration.

        Checks:
        1. Total role counts match players_per_game
        2. Role relationships are valid
        """
        # Check that we have a roles configuration
        if not self.roles_config:
            raise ValueError("No roles configuration found in benchmark config")

        # Prepare to track roles
        required_player_slots = 0
        inherited_slots = 0

        # Track which roles inherit others
        inheritance_graph = {}

        # Check each role
        for role_name, role_config in self.roles_config.items():
            # Ensure count is present
            if 'count' not in role_config:
                raise ValueError(f"Role {role_name} missing required 'count' field")

            role_count = role_config['count']

            # Track inheritance relationships
            if 'inherits' in role_config:
                inheritance_graph[role_name] = role_config['inherits']
                # These slots are filled by players who already have other roles
                inherited_slots += role_count
            else:
                # If no inheritance, this requires dedicated players
                required_player_slots += role_count

        # Check for inheritance cycles
        for role in inheritance_graph:
            visited = set()
            self._check_inheritance_cycle(role, inheritance_graph, visited)

        # Validate player counts - accounting for inheritance
        if required_player_slots != self.players_per_game:
            logger.warning(f"Sum of dedicated role counts ({required_player_slots}) doesn't match players_per_game ({self.players_per_game})")

    def _check_inheritance_cycle(self, role, inheritance_graph, visited):
        """
        Check for cycles in role inheritance graph.

        Args:
            role: The current role to check
            inheritance_graph: Map of role -> list of inherited roles
            visited: Set of visited roles in current path
        """
        if role in visited:
            raise ValueError(f"Cycle detected in role inheritance graph involving {role}")

        visited.add(role)

        # Check all inherited roles
        for inherited_role in inheritance_graph.get(role, []):
            if inherited_role in inheritance_graph:
                self._check_inheritance_cycle(inherited_role, inheritance_graph, visited.copy())

    def _load_state(self) -> None:
        """
        Load the existing benchmark state if it exists.
        """
        if not os.path.exists(self.state_path):
            # Initialize fresh state
            for model in self.models:
                self.opponent_matrix[model] = set()
                self.game_counts[model] = 0
                self.role_counts[model] = {role: 0 for role in self.roles_config}
            logger.info("No existing benchmark state found, starting fresh")
            return

        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)

            # Reload state
            self.opponent_matrix = {model: set(opponents) for model, opponents in state.get('opponent_matrix', {}).items()}
            self.game_counts = state.get('game_counts', {})
            self.role_counts = state.get('role_counts', {})
            self.sessions_run = state.get('sessions_run', 0)

            # Handle new models that weren't in the previous state
            for model in self.models:
                if model not in self.opponent_matrix:
                    self.opponent_matrix[model] = set()
                if model not in self.game_counts:
                    self.game_counts[model] = 0
                if model not in self.role_counts:
                    self.role_counts[model] = {role: 0 for role in self.roles_config}
                # Add any new roles to existing models
                else:
                    for role in self.roles_config:
                        if role not in self.role_counts[model]:
                            self.role_counts[model][role] = 0

            logger.info(f"Loaded benchmark state: {self.sessions_run} sessions run")

        except Exception as e:
            logger.error(f"Error loading benchmark state: {str(e)}")
            # Initialize fresh state as fallback
            for model in self.models:
                self.opponent_matrix[model] = set()
                self.game_counts[model] = 0
                self.role_counts[model] = {role: 0 for role in self.roles_config}

    def _save_state(self) -> None:
        """
        Save the current benchmark state.
        """
        try:
            state = {
                'opponent_matrix': {model: sorted(list(opponents)) for model, opponents in self.opponent_matrix.items()},
                'game_counts': self.game_counts,
                'role_counts': self.role_counts,
                'sessions_run': self.sessions_run
            }

            with open(self.state_path, 'w') as f:
                json.dump(state, f, indent=2)

            logger.info(f"Saved benchmark state after {self.sessions_run} sessions")

        except Exception as e:
            logger.error(f"Error saving benchmark state: {str(e)}")


    def _select_models_for_session_prioritize_role(self, role):
        """
        Select models for debate slam, prioritizing models with fewer debater opportunities.

        Returns:
            List[str]: List of selected model identifiers with debaters first, then judges
        """
        # Get role counts from state
        all_roles_counts = getattr(self, 'role_counts', {})

        # If role_counts not initialized, create it
        if not all_roles_counts:
            for model in self.models:
                self.role_counts[model] = {role: 0 for role in self.roles_config}

        # Get debater counts for all models
        specified_role_counts = {model: self.role_counts.get(model, {}).get(role, 0) for model in self.models}

        # Sort models by debater count (ascending)
        sorted_models = sorted(self.models, key=lambda model: specified_role_counts.get(model, 0))

        # Select the 2 models with fewest debater roles as debaters
        selected_debaters = sorted_models[:2]

        logger.info(f"Selected debaters: {selected_debaters}")

        # Exclude the selected debaters from judge selection
        judge_candidates = [model for model in self.models if model not in selected_debaters]

        # Randomly select 3 judges
        num_judges = self.players_per_game - 2  # Should be 3 for debate slam
        selected_judges = random.sample(judge_candidates, min(num_judges, len(judge_candidates)))

        logger.info(f"Selected judges: {selected_judges}")

        # Return debaters first, then judges (order matters for role assignment)
        selected_models = selected_debaters + selected_judges

        return selected_models


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

        # Calculate a combined score that considers both diversity and game count
        combined_scores = {}
        for model in self.models:
            diversity_factor = diversity_scores[model]
            game_count_factor = self.game_counts.get(model, 0) / max(1, max(self.game_counts.values()))
            combined_scores[model] = diversity_factor + game_count_factor

        # Select the anchor model with the lowest combined score
        anchor_model = min(combined_scores.keys(), key=lambda k: combined_scores[k])

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

    def _select_models_for_role(self, role: str, count: int, eligible_models: List[str],
                                assigned_roles: Dict[str, List[str]]) -> List[str]:
        """
        Select models for a specific role using the configured selection strategy.

        Args:
            role (str): Role to select models for
            count (int): Number of models to select
            eligible_models (List[str]): Available models to choose from
            assigned_roles (Dict[str, List[str]]): Current role assignments

        Returns:
            List[str]: Selected models for this role
        """
        role_config = self.roles_config[role]
        selection_strategy = role_config.get('selection', 'random')

        # Filter out models that have incompatible roles already assigned
        incompatible_roles = role_config.get('incompatible_with', [])

        filtered_models = []
        for model in eligible_models:
            # Skip if model already has this role
            if model in assigned_roles and role in assigned_roles[model]:
                continue

            # Check incompatible roles
            has_incompatible_role = False
            if model in assigned_roles:
                for incompatible_role in incompatible_roles:
                    if incompatible_role in assigned_roles[model]:
                        has_incompatible_role = True
                        break

            if not has_incompatible_role:
                filtered_models.append(model)

        # Check if we have enough eligible models
        if len(filtered_models) < count:
            logger.warning(f"Not enough eligible models for role {role}: {len(filtered_models)}/{count}")
            # If we're short on models, we'll need to pick from all available models
            filtered_models = eligible_models

        # Apply selection strategy
        if selection_strategy == 'weighted_inverse':
            # Power factor to increase the strength of the inverse weighting
            # Higher values create stronger bias toward models with fewer role assignments
            power_factor = 5.0  # Adjust this to control strength (was effectively 1.0 before)

            # Calculate weights: 1 / (role_count + 1)^power_factor
            weights = [1.0 / ((self.role_counts.get(model, {}).get(role, 0) + 1.0) ** power_factor) for model in filtered_models]

            # Normalize weights
            total_weight = sum(weights)
            probabilities = [w / total_weight for w in weights]

            # Weighted random selection
            selected = []
            remaining_models = filtered_models.copy()
            remaining_probs = probabilities.copy()

            for _ in range(min(count, len(filtered_models))):
                if not remaining_models:
                    break

                # Normalize remaining probabilities
                if sum(remaining_probs) > 0:
                    remaining_probs = [p / sum(remaining_probs) for p in remaining_probs]
                    chosen_idx = np.random.choice(len(remaining_models), p=remaining_probs)
                else:
                    chosen_idx = random.randrange(len(remaining_models))

                selected.append(remaining_models[chosen_idx])
                remaining_models.pop(chosen_idx)
                remaining_probs.pop(chosen_idx)

            logger.info(f"Selected models for role {role} using weighted selection: {selected}")
            return selected

        else:
            # Default to random selection
            if len(filtered_models) <= count:
                selected = filtered_models
            else:
                selected = random.sample(filtered_models, count)

            logger.info(f"Selected models for role {role} using random selection: {selected}")
            return selected

    def _assign_roles_to_models(self, selected_models: List[str]) -> Tuple[Dict[str, Dict[str, str]], Dict[str, List[str]]]:
        """
        Assign roles to models based on the configuration.

        Args:
            selected_models (List[str]): Models to assign roles to

        Returns:
            Tuple containing:
                - Dict[str, Dict[str, str]]: Maps roles to {player_id: model}
                - Dict[str, List[str]]: Maps models to their assigned roles
        """
        # Initialize tracking structures
        assigned_roles = {model: [] for model in selected_models}  # model -> [roles]
        role_assignments = {}  # role -> {player_id: model}
        player_lookup = {f"player_{i+1}": model for i, model in enumerate(selected_models)}

        # Order roles for processing - base roles first, then roles with inheritance
        base_roles = []
        dependent_roles = []

        for role, config in self.roles_config.items():
            if 'inherits' not in config or not config['inherits']:
                base_roles.append(role)
            else:
                dependent_roles.append(role)

        # Process base roles first, then dependent roles
        ordered_roles = base_roles + dependent_roles
        logger.info(f"Processing roles in order: {ordered_roles}")

        # Assign each role
        for role in ordered_roles:
            role_config = self.roles_config[role]
            count = role_config.get('count', 0)

            # Skip if no models needed for this role
            if count <= 0:
                continue

            # Check exclusive flag
            is_exclusive = role_config.get('exclusive', False)

            # Get models eligible for this role
            if is_exclusive:
                # Only models with no roles yet
                eligible_models = [m for m in selected_models if not assigned_roles[m]]
            else:
                # All models are eligible, filtered by incompatibility in selection method
                eligible_models = selected_models

            # Select models for this role
            selected_for_role = self._select_models_for_role(
                role, count, eligible_models, assigned_roles
            )

            # Assign role to selected models
            role_assignments[role] = {}
            for i, model in enumerate(selected_for_role):
                # Find player_id corresponding to this model
                player_id = next((pid for pid, mod in player_lookup.items() if mod == model), None)
                if not player_id:
                    logger.error(f"Could not find player_id for model {model}")
                    continue

                role_assignments[role][player_id] = model

                # Record assignment
                assigned_roles[model].append(role)

                # If this role inherits other roles, assign those too
                if 'inherits' in role_config:
                    for inherited_role in role_config['inherits']:
                        if inherited_role not in assigned_roles[model]:
                            assigned_roles[model].append(inherited_role)

                            # Add to role assignments if not already present
                            if inherited_role not in role_assignments:
                                role_assignments[inherited_role] = {}
                            role_assignments[inherited_role][player_id] = model

        # Validate all roles have been assigned
        for role, config in self.roles_config.items():
            required_count = config.get('count', 0)
            assigned_count = len(role_assignments.get(role, {}))

            if assigned_count < required_count:
                logger.warning(f"Insufficient assignments for role {role}: {assigned_count}/{required_count}")

        logger.info(f"Role assignments: {role_assignments}")
        logger.info(f"Model roles: {assigned_roles}")

        return role_assignments, assigned_roles

    def run_benchmark(self) -> None:
        """
        Run the benchmark for the specified number of sessions.
        """
        logger.info(f"Starting benchmark with {self.sessions - self.sessions_run} sessions remaining")
        start_time = time.time()

        # Run remaining sessions
        for i in range(self.sessions_run, self.sessions):
            logger.info(f"Running session {i+1}/{self.sessions}")

            if self.player_selection_strategy == 'least_games_with_role':
                selected_models = self._select_models_for_session_prioritize_role(self.player_selection_strategy_role)
            else:
                selected_models = self._select_models_for_session()

            # Assign roles to models
            role_assignments, model_roles = self._assign_roles_to_models(selected_models)

            # Run the session
            session_id, session_dir = self._run_session(selected_models, role_assignments, model_roles)

            # Update state
            self._update_state_after_session(selected_models, model_roles)

            # Save current state
            self._save_state()

            # Log the result
            self._log_session_result(selected_models, model_roles, session_id, session_dir)

            # Update counter
            self.sessions_run += 1


        # Calculate benchmark stats
        elapsed_time = time.time() - start_time
        logger.info(f"Benchmark complete. Ran {self.sessions_run} sessions in {elapsed_time:.2f} seconds")

    def _update_state_after_session(self, models: List[str], model_roles: Dict[str, List[str]]) -> None:
        """
        Update tracking state after a session.

        Args:
            models (List[str]): Models that participated in the session
            model_roles (Dict[str, List[str]]): Roles assigned to each model
        """
        # Update opponent matrix for each model
        for model in models:
            # Add all other models in the session as opponents
            for opponent in models:
                if opponent != model:
                    self.opponent_matrix[model].add(opponent)

            # Increment game count
            self.game_counts[model] = self.game_counts.get(model, 0) + 1

            # Increment role counts
            for role in model_roles.get(model, []):
                if model not in self.role_counts:
                    self.role_counts[model] = {}
                if role not in self.role_counts[model]:
                    self.role_counts[model][role] = 0
                self.role_counts[model][role] += 1

    def _run_session(self, models: List[str], role_assignments: Dict[str, Dict[str, str]],
                    model_roles: Dict[str, List[str]]) -> Tuple[str, str]:
        """
        Run a single game session with the specified models and role assignments.

        Args:
            models (List[str]): Models participating in the session
            role_assignments (Dict[str, Dict[str, str]]): Maps roles to {player_id: model}
            model_roles (Dict[str, List[str]]): Maps models to their assigned roles

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

        # Update player count
        game_config['players']['min'] = len(models)
        game_config['players']['max'] = len(models)

        # Update setup to assign roles
        if 'setup' not in game_config:
            game_config['setup'] = {}

        if 'assignments' not in game_config['setup']:
            game_config['setup']['assignments'] = []

        # Clear existing assignments
        game_config['setup']['assignments'] = []

        # Add role assignments
        for role, assignments in role_assignments.items():
            for player_id, model in assignments.items():
                game_config['setup']['assignments'].append({
                    'role': role,
                    'assignment_to': player_id
                })

        # Create a temp config file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_config_path = os.path.join(self.output_dir, f"temp_config_{timestamp}.yaml")

        with open(temp_config_path, 'w') as f:
            yaml.dump(game_config, f)

        try:
            # Initialize and run the game
            engine = GameEngine(
                temp_config_path,
                base_output_dir=self.output_dir,
                benchmark_config=self.benchmark_config
            )
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

    def _log_session_result(self, models: List[str], model_roles: Dict[str, List[str]],
                           session_id: str, session_dir: str) -> None:
        """
        Log the result of a session to the benchmark log.

        Args:
            models (List[str]): Models that participated in the session
            model_roles (Dict[str, List[str]]): Roles assigned to each model
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
                    "roles": model_roles.get(model, [])
                })

            # Create the log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "game_config_hash": self.benchmark_config.get_base_game_config_hash(),
                "session_id": session_id,
                "session_number": self.sessions_run + 1,
                "players": player_results,
                "winner": results.get('winner', {}).get('id') if results.get('winner') else "tie",
                "benchmark_id": self.benchmark_config.get_benchmark_id()
            }

            # Append to the log file
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")

            logger.info(f"Logged result for session {self.sessions_run + 1}, winner: {log_entry['winner']}")
        except Exception as e:
            logger.error(f"Error logging session result: {str(e)}")