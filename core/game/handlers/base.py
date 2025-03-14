# handlers/base.py
class PhaseHandler:
    """
    Base class for phase handlers.

    Phase handlers implement the game logic for each phase of a game.
    They process the current state, apply game rules, and return a result
    that indicates whether a condition for phase transition is met.
    """

    def process(self, game_state):
        """
        Process the current phase.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: Result for conditional phase transitions
        """
        # Default implementation always returns True
        return True

    def process_player(self, game_state, player):
        """
        Process a single player's action in the current phase.

        This method should be implemented by handlers that need to
        process individual player actions.

        Args:
            game_state (GameState): The current game state
            player (dict): The player to process

        Returns:
            any: The player's action or response
        """
        # Default implementation returns None
        return None

    def _get_phase_config(self, game_state):
        """
        Get the configuration for the current phase.

        Args:
            game_state (GameState): The current game state

        Returns:
            dict: The phase configuration

        Raises:
            ValueError: If the phase configuration is not found
        """
        current_phase = game_state.current_phase

        for phase in game_state.config['phases']:
            if phase['id'] == current_phase:
                return phase

        raise ValueError(f"Phase configuration not found: {current_phase}")


class PhaseController:
    """
    Controls phase transitions based on game rules.

    Determines the next phase to transition to based on the current
    phase, phase configuration, and condition results.
    """

    def get_next_phase(self, game_state, current_phase, condition_result=None):
        """
        Determine the next phase based on configuration and condition result.

        Args:
            game_state (GameState): The current game state
            current_phase (str): The current phase ID
            condition_result (bool, optional): Result of condition check

        Returns:
            str: The next phase ID, or 'game_end' if game should end
        """
        phase_config = self._get_phase_config(game_state.config, current_phase)

        # Handle conditional transitions
        if 'next_phase_condition' in phase_config:
            if condition_result:
                return phase_config.get('next_phase_success', 'game_end')
            else:
                return phase_config.get('next_phase_failure', 'game_end')

        # Handle simple transitions
        return phase_config.get('next_phase', 'game_end')

    def _get_phase_config(self, config, phase_id):
        """
        Get the configuration for a specific phase.

        Args:
            config (dict): The game configuration
            phase_id (str): The phase ID to find

        Returns:
            dict: The phase configuration

        Raises:
            ValueError: If the phase configuration is not found
        """
        for phase in config['phases']:
            if phase['id'] == phase_id:
                return phase

        raise ValueError(f"Phase configuration not found: {phase_id}")
