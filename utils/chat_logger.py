# utils/chat_logger.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("chat_logger")

class ChatLogger:
    """Logs chat history for all LLM interactions."""

    def __init__(self, game_session):
        """Initialize the chat logger.

        Args:
            game_session: GameSession object for logging
        """
        if game_session is None:
            raise ValueError("GameSession is required for ChatLogger")

        self.game_session = game_session
        self.consolidated_log_path = game_session.chat_logs_path

        # Set up logging
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)

    def log_interaction(self,
                       player_id: str,
                       messages: List[Dict[str, Any]],
                       response: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None,
                       phase_id: Optional[str] = None,
                       round_num: Optional[int] = None,
                       action_id: Optional[str] = None) -> None:
        """Log a single LLM interaction.

        Args:
            player_id: Identifier for the player/agent
            messages: List of message objects sent to the LLM
            response: Response from the LLM (if available)
            metadata: Additional information about the interaction
            phase_id: Current game phase ID
            round_num: Current round number
            action_id: ID to link with game state changes
        """
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "player_id": player_id,
            "messages": messages,
            "response": response,
            "metadata": metadata or {},
            "phase_id": phase_id,
            "round_num": round_num,
            "action_id": action_id
        }

        # Save to the game session
        self.game_session.save_chat_log(log_entry)
        logger.info(f"Logged interaction for player {player_id}")

    def get_consolidated_log_path(self) -> str:
        """Get the path to the consolidated log file.

        Returns:
            Path to the consolidated log file
        """
        return self.consolidated_log_path