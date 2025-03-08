# core/engine.py
import os
import time
import logging

from core.config import ConfigLoader
from core.state import GameState
from handlers.base import PhaseController
from handlers.registry import HandlerRegistry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GameEngine")

class GameEngine:
    """
    Manages the game flow and coordinates components.

    The game engine is responsible for initializing the game,
    running the game loop, managing phase transitions, and
    coordinating interactions between components.
    """

    def __init__(self, config_path):
        """
        Initialize the game engine.

        Args:
            config_path (str): Path to the game configuration file
        """
        logger.info(f"Initializing game from config: {config_path}")
        self.config = ConfigLoader.load(config_path)
        self.state = GameState(self.config)
        self.phase_controller = PhaseController()

        # Extract key info for logging
        self.game_name = self.config['game']['name']
        self.player_count = len(self.state.players)

        logger.info(f"Initialized {self.game_name} with {self.player_count} players")

    def run_game(self):
        """
        Run the game from start to finish.

        Executes the main game loop, processing phases until
        the game is complete. Saves state snapshots after each
        phase for analysis.
        """
        logger.info(f"Starting game: {self.game_name}")

        # Save initial state snapshot
        self.state.save_snapshot()

        # Main game loop
        while not self.state.is_game_over():
            current_phase = self.state.current_phase
            phase_config = self._get_phase_config(current_phase)

            logger.info(f"Processing phase: {current_phase}")

            # Get the appropriate handler for this phase
            handler_name = phase_config.get('handler')
            if handler_name:
                logger.debug(f"Using named handler: {handler_name}")
                handler = HandlerRegistry.get_handler(handler_name)
            else:
                phase_type = phase_config['type']
                logger.debug(f"Using default handler for phase type: {phase_type}")
                handler = HandlerRegistry.get_default_handler(phase_type)

            # Process the phase
            start_time = time.time()
            try:
                result = handler.process(self.state)
                elapsed = time.time() - start_time
                logger.debug(f"Phase processed in {elapsed:.2f} seconds with result: {result}")
            except Exception as e:
                logger.error(f"Error processing phase: {str(e)}")
                raise

            # Determine next phase
            next_phase = self.phase_controller.get_next_phase(
                self.state, current_phase, result
            )

            logger.info(f"Transitioning from {current_phase} to {next_phase}")

            if next_phase == "game_end":
                logger.info("Game end condition met")
                self.state.game_over = True
            else:
                self.state.current_phase = next_phase

            # Save state snapshot after each phase
            self.state.save_snapshot()

        logger.info(f"Game completed: {self.game_name}")

        # Save final results
        results_file = self.state.save_results()
        logger.info(f"Game results saved to: {results_file}")

    def _get_phase_config(self, phase_id):
        """
        Get the configuration for a specific phase.

        Args:
            phase_id (str): The phase ID to find

        Returns:
            dict: The phase configuration

        Raises:
            ValueError: If the phase configuration is not found
        """
        for phase in self.config['phases']:
            if phase['id'] == phase_id:
                return phase
        raise ValueError(f"Phase configuration not found: {phase_id}")