# core/config.py
import yaml
import os

class ConfigLoader:
    """
    Loads and validates game configurations from YAML files.

    This class is responsible for parsing game configuration files,
    validating their structure, and providing sensible defaults for
    optional configuration fields.
    """

    @staticmethod
    def load(config_path):
        """
        Load a game configuration from a YAML file.

        Args:
            config_path (str): Path to the YAML configuration file

        Returns:
            dict: The parsed and validated configuration

        Raises:
            ValueError: If the configuration is invalid or missing required keys
            FileNotFoundError: If the configuration file doesn't exist
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Validate required configuration sections
        ConfigLoader._validate_required_keys(config)

        # Apply defaults for optional sections
        ConfigLoader._apply_defaults(config)

        return config

    @staticmethod
    def _validate_required_keys(config):
        """
        Validate that the configuration contains all required keys.

        Args:
            config (dict): The configuration to validate

        Raises:
            ValueError: If any required keys are missing
        """
        required_keys = ['game', 'players', 'phases']
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")

        # Validate game section
        if 'name' not in config['game']:
            raise ValueError("Missing 'name' in game configuration")

        # Validate players section
        if 'min' not in config['players'] or 'max' not in config['players']:
            raise ValueError("Players configuration must specify 'min' and 'max'")

        # Validate phases section
        if not config['phases'] or not isinstance(config['phases'], list):
            raise ValueError("Phases must be a non-empty list")

        for i, phase in enumerate(config['phases']):
            if 'id' not in phase:
                raise ValueError(f"Phase at index {i} missing required 'id' field")
            if 'type' not in phase:
                raise ValueError(f"Phase '{phase['id']}' missing required 'type' field")

    @staticmethod
    def _apply_defaults(config):
        """
        Apply default values for optional configuration sections.

        Args:
            config (dict): The configuration to update with defaults
        """
        # Apply defaults for state section
        if 'state' not in config:
            config['state'] = {
                'player_state': [],
                'shared_state': [],
                'hidden_state': [],
                'history_state': []
            }
        else:
            state = config['state']
            if 'player_state' not in state:
                state['player_state'] = []
            if 'shared_state' not in state:
                state['shared_state'] = []
            if 'hidden_state' not in state:
                state['hidden_state'] = []
            if 'history_state' not in state:
                state['history_state'] = []

        # Apply defaults for rounds section
        if 'rounds' not in config:
            config['rounds'] = {
                'count': 1,
                'progression': 'fixed'
            }

        # Apply defaults for setup section
        if 'setup' not in config:
            config['setup'] = {
                'initial_state': {
                    'resources': [],
                    'assignments': []
                }
            }

        # Apply defaults for win_condition
        if 'win_condition' not in config:
            config['win_condition'] = {
                'type': 'last_player_standing',
                'trigger': 'player_count_equals_one'
            }

        # Apply defaults for llm_integration
        if 'llm_integration' not in config:
            config['llm_integration'] = {}