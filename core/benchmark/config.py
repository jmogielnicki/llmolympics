# core/benchmark/config.py
import os
import yaml
import hashlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger("BenchmarkConfig")

class BenchmarkConfig:
    """
    Loads and validates benchmark configurations from YAML files.

    This class handles loading benchmark configurations, validating
    their structure, and generating a hash of the base game config
    for consistency checking.
    """

    def __init__(self, config_path: str):
        """
        Initialize a benchmark configuration from a YAML file.

        Args:
            config_path (str): Path to the benchmark YAML configuration

        Raises:
            ValueError: If the configuration is invalid
            FileNotFoundError: If the configuration file doesn't exist
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Benchmark configuration file not found: {config_path}")

        # Load the benchmark configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Validate the configuration
        self._validate_config()

        # Load base game configuration and generate hash
        self.base_game_config_path = self.config['benchmark']['base_config']
        self.base_game_config_hash = self._generate_config_hash(self.base_game_config_path)

        logger.info(f"Loaded benchmark configuration: {self.get_benchmark_id()}")
        logger.info(f"Base game config: {self.base_game_config_path} (hash: {self.base_game_config_hash[:8]}...)")

    def _validate_config(self) -> None:
        """
        Validate that the configuration contains all required fields.

        Raises:
            ValueError: If any required fields are missing or invalid
        """
        # Check for required top-level sections
        required_sections = ['benchmark', 'models']
        missing_sections = [s for s in required_sections if s not in self.config]
        if missing_sections:
            raise ValueError(f"Missing required sections in benchmark config: {missing_sections}")

        # Validate benchmark section
        benchmark = self.config['benchmark']

        # Determine type of benchmark for validation
        benchmark_type = benchmark.get('type', 'pairwise')

        if benchmark_type == 'pairwise':
            # Validate pairwise benchmark fields
            required_benchmark_fields = ['id', 'base_config', 'games_per_pair', 'output_dir']
            missing_fields = [f for f in required_benchmark_fields if f not in benchmark]
            if missing_fields:
                raise ValueError(f"Missing required fields in pairwise benchmark section: {missing_fields}")
        elif benchmark_type == 'multi_player':
            # Validate multi-player benchmark fields
            required_benchmark_fields = ['id', 'base_config', 'output_dir', 'sessions', 'players_per_game']
            missing_fields = [f for f in required_benchmark_fields if f not in benchmark]
            if missing_fields:
                raise ValueError(f"Missing required fields in multi-player benchmark section: {missing_fields}")
        else:
            raise ValueError(f"Invalid benchmark type: {benchmark_type}. Must be 'pairwise' or 'multi_player'")

        # Check that base_config file exists
        base_config_path = benchmark['base_config']
        if not os.path.exists(base_config_path):
            raise ValueError(f"Base game configuration file not found: {base_config_path}")

        # Validate models list
        models = self.config['models']
        if not isinstance(models, list) or len(models) < 2:
            raise ValueError("At least two models must be specified in the models list")

        # Validate each model format (provider:model-name)
        for model in models:
            if ':' not in model:
                raise ValueError(f"Invalid model format: {model}. Expected 'provider:model-name'")

    def _generate_config_hash(self, config_path: str) -> str:
        """
        Generate a hash of the game configuration file.

        Args:
            config_path (str): Path to the configuration file

        Returns:
            str: SHA-256 hash of the file content
        """
        with open(config_path, 'rb') as f:
            file_content = f.read()
            return hashlib.sha256(file_content).hexdigest()

    def get_benchmark_id(self) -> str:
        """
        Get the benchmark ID.

        Returns:
            str: The benchmark ID
        """
        return self.config['benchmark']['id']

    def get_output_dir(self) -> str:
        """
        Get the output directory for benchmark results.

        Returns:
            str: Path to the output directory
        """
        return os.path.join(
            self.config['benchmark']['output_dir'],
            self.get_benchmark_id()
        )

    def get_games_per_pair(self) -> int:
        """
        Get the number of games per model pair (for pairwise benchmarks).

        Returns:
            int: Number of games per pair
        """
        return self.config['benchmark'].get('games_per_pair', 1)

    def get_models(self) -> List[str]:
        """
        Get the list of models to benchmark.

        Returns:
            List[str]: List of model identifiers
        """
        return self.config['models']

    def get_base_game_config_path(self) -> str:
        """
        Get the path to the base game configuration.

        Returns:
            str: Path to the base game configuration
        """
        return self.base_game_config_path

    def get_base_game_config_hash(self) -> str:
        """
        Get the hash of the base game configuration.

        Returns:
            str: SHA-256 hash of the base game configuration
        """
        return self.base_game_config_hash

    def get_benchmark_type(self) -> str:
        """
        Get the type of benchmark (pairwise or multi_player).

        Returns:
            str: The benchmark type
        """
        return self.config['benchmark'].get('type', 'pairwise')