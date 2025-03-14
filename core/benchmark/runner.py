# core/benchmark/runner.py
import os
import yaml
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Set, Tuple, Any, Optional
import itertools

# Import from core modules
from core.benchmark.config import BenchmarkConfig
from core.game.engine import GameEngine
from core.game.config import ConfigLoader

logger = logging.getLogger("BenchmarkRunner")

class BenchmarkRunner:
    """
    Manages the execution of model benchmarks.

    This class handles tracking benchmark progress, determining
    which matchups need to be run, and executing game runs.
    """

    def __init__(self, benchmark_config: BenchmarkConfig):
        """
        Initialize the benchmark runner.

        Args:
            benchmark_config (BenchmarkConfig): The benchmark configuration
        """
        self.benchmark_config = benchmark_config
        self.output_dir = benchmark_config.get_output_dir()
        self.log_path = os.path.join(self.output_dir, "benchmark_log.jsonl")

        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Load the base game configuration
        self.base_game_config_path = benchmark_config.get_base_game_config_path()
        self.base_game_config = ConfigLoader.load(self.base_game_config_path)

        # Track benchmark stats
        self.completed_matchups = set()
        self.matchups_to_run = []
        self.games_run = 0

        logger.info(f"Initialized benchmark runner for {benchmark_config.get_benchmark_id()}")
        logger.info(f"Output directory: {self.output_dir}")

    def load_benchmark_log(self) -> None:
        """
        Load the existing benchmark log if it exists.

        This method reads the benchmark log JSONL file and tracks
        which matchups have already been completed.
        """
        if not os.path.exists(self.log_path):
            logger.info("No existing benchmark log found, starting fresh")
            return

        entries = 0
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        # Skip invalid entries
                        if not self._is_valid_log_entry(entry):
                            continue

                        # Check if the game config hash matches
                        if entry['game_config_hash'] != self.benchmark_config.get_base_game_config_hash():
                            logger.warning(
                                f"Game config hash mismatch in log entry. Expected {self.benchmark_config.get_base_game_config_hash()[:8]}..., "
                                f"got {entry['game_config_hash'][:8]}... (session: {entry.get('session_id', 'unknown')})"
                            )
                            continue

                        # Add to completed matchups
                        matchup_key = self._generate_matchup_key(
                            entry['player1']['model'],
                            entry['player2']['model'],
                            entry['game_number']
                        )
                        self.completed_matchups.add(matchup_key)
                        entries += 1
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse log entry: {str(e)}")
                        continue

            logger.info(f"Loaded benchmark log with {entries} completed matchups")
        except Exception as e:
            logger.error(f"Error loading benchmark log: {str(e)}")
            raise

    def _is_valid_log_entry(self, entry: Dict[str, Any]) -> bool:
        """
        Check if a log entry contains all required fields.

        Args:
            entry (Dict[str, Any]): The log entry to validate

        Returns:
            bool: True if the entry is valid, False otherwise
        """
        required_fields = ['timestamp', 'game_config_hash', 'session_id', 'player1', 'player2', 'game_number']
        for field in required_fields:
            if field not in entry:
                return False

        # Check player fields
        for player_field in ['player1', 'player2']:
            player = entry.get(player_field, {})
            if not isinstance(player, dict) or 'id' not in player or 'model' not in player:
                return False

        return True

    def generate_matchups(self) -> None:
        """
        Generate all possible matchups for the benchmark.

        This method creates a list of all model pairs that need to be tested,
        taking into account the number of games per pair and which matchups
        have already been completed.
        """
        models = self.benchmark_config.get_models()
        games_per_pair = self.benchmark_config.get_games_per_pair()
        logger.info(f"Generating matchups for {len(models)} models, {games_per_pair} games per pair")

        # Check if game is symmetric or asymmetric
        is_asymmetric = False
        if 'roles' in self.base_game_config.get('players', {}):
            is_asymmetric = self.base_game_config['players']['roles'] == 'asymmetric'

        # Generate all model pairs
        matchups = []
        for model1, model2 in itertools.combinations(models, 2):
            if is_asymmetric:
                # For asymmetric games, both orderings matter
                for game_num in range(1, games_per_pair + 1):
                    # model1 as player 1, model2 as player 2
                    matchup_key1 = self._generate_matchup_key(model1, model2, game_num)
                    if matchup_key1 not in self.completed_matchups:
                        matchups.append((model1, model2, game_num))

                    # model2 as player 1, model1 as player 2
                    matchup_key2 = self._generate_matchup_key(model2, model1, game_num)
                    if matchup_key2 not in self.completed_matchups:
                        matchups.append((model2, model1, game_num))
            else:
                # For symmetric games, the order doesn't matter
                for game_num in range(1, games_per_pair + 1):
                    matchup_key = self._generate_matchup_key(model1, model2, game_num)
                    if matchup_key not in self.completed_matchups:
                        matchups.append((model1, model2, game_num))

        self.matchups_to_run = matchups
        logger.info(f"Generated {len(matchups)} matchups to run")

    def _generate_matchup_key(self, model1: str, model2: str, game_num: int) -> str:
        """
        Generate a unique key for a matchup.

        Args:
            model1 (str): First model identifier
            model2 (str): Second model identifier
            game_num (int): Game number for this pair

        Returns:
            str: Unique matchup key
        """
        return f"{model1}_vs_{model2}_game{game_num}"

    def run_benchmark(self) -> None:
        """
        Run the benchmark for all remaining matchups.

        This method runs games for all matchups that haven't been
        completed yet and logs the results.
        """
        logger.info(f"Starting benchmark with {len(self.matchups_to_run)} matchups to run")
        start_time = time.time()

        # Create a copy since we'll be removing items as we go
        matchups = self.matchups_to_run.copy()
        total_matchups = len(matchups)

        for i, (model1, model2, game_num) in enumerate(matchups):
            logger.info(f"Running matchup {i+1}/{total_matchups}: {model1} vs {model2} (game {game_num})")

            try:
                # Run the game and get results
                session_id, session_dir = self._run_game(model1, model2, game_num)

                # Log the result
                self._log_matchup_result(model1, model2, game_num, session_id, session_dir)

                # Update stats
                self.games_run += 1
                matchup_key = self._generate_matchup_key(model1, model2, game_num)
                self.completed_matchups.add(matchup_key)

            except Exception as e:
                logger.error(f"Error running matchup {model1} vs {model2} (game {game_num}): {str(e)}")
                # Continue with the next matchup
                continue

        # Calculate benchmark stats
        elapsed_time = time.time() - start_time
        logger.info(f"Benchmark complete. Ran {self.games_run} games in {elapsed_time:.2f} seconds")
        logger.info(f"Total completed matchups: {len(self.completed_matchups)}")

    def _run_game(self, model1: str, model2: str, game_num: int) -> Tuple[str, str]:
        """
        Run a single game with the specified models.

        Args:
            model1 (str): First model identifier
            model2 (str): Second model identifier
            game_num (int): Game number for this pair

        Returns:
            tuple: (session_id, session_dir) of the completed game
        """
        # Create a modified game config with the specified models
        game_config = self.base_game_config.copy()

        # Ensure llm_integration section exists
        if 'llm_integration' not in game_config:
            game_config['llm_integration'] = {}

        # Set player models
        if 'player_models' not in game_config['llm_integration']:
            game_config['llm_integration']['player_models'] = {}

        game_config['llm_integration']['player_models']['player_1'] = model1
        game_config['llm_integration']['player_models']['player_2'] = model2

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

    def _log_matchup_result(self, model1: str, model2: str, game_num: int, session_id: str, session_dir: str) -> None:
        """
        Log the result of a matchup to the benchmark log.

        Args:
            model1 (str): First model identifier
            model2 (str): Second model identifier
            game_num (int): Game number for this pair
            session_id (str): Session ID of the completed game
            session_dir (str): Directory of the session
        """
        # Find the game results file directly using the session directory
        results_path = os.path.join(session_dir, "results.json")

        if not os.path.exists(results_path):
            logger.error(f"Results file not found: {results_path}")
            return

        try:
            # Load the game results
            with open(results_path, 'r') as f:
                results = json.load(f)

            # Create the log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "game_config_hash": self.benchmark_config.get_base_game_config_hash(),
                "session_id": session_id,
                "player1": {
                    "id": "player_1",
                    "model": model1,
                    "score": results.get('players', [])[0].get('final_state', {}).get('score')
                },
                "player2": {
                    "id": "player_2",
                    "model": model2,
                    "score": results.get('players', [])[1].get('final_state', {}).get('score')
                },
                "winner": results.get('winner', {}).get('id') if results.get('winner') else "tie",
                "rounds_played": results.get('rounds_played', 0),
                "game_number": game_num,
                "games_per_pair": self.benchmark_config.get_games_per_pair(),
                "benchmark_id": self.benchmark_config.get_benchmark_id()
            }

            # Append to the log file
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")

            logger.info(f"Logged result for {model1} vs {model2} (game {game_num})")
        except Exception as e:
            logger.error(f"Error logging matchup result: {str(e)}")