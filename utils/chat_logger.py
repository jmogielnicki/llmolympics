# utils/chat_logger.py
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("chat_logger")

class ChatLogger:
    """Logs chat history for all LLM interactions."""

    def __init__(self, game_session=None, log_dir: str = "data/logs"):
        """Initialize the chat logger.

        Args:
            game_session: GameSession object for unified logging
            log_dir: Directory to store log files (used only if no game_session)
        """
        self.game_session = game_session

        # If no game_session provided, use traditional logging approach
        if game_session is None:
            self.log_dir = log_dir
            os.makedirs(log_dir, exist_ok=True)

            # Set up file handler for consolidated log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Use a slightly different filename for test logs vs regular logs
            is_test = os.environ.get("PARLOURBENCH_USE_MOCK") == "1"
            prefix = "test_" if is_test else ""
            self.consolidated_log_path = os.path.join(log_dir, f"{prefix}chat_history_{timestamp}.jsonl")
        else:
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

        # Use game session if available
        if self.game_session:
            self.game_session.save_chat_log(log_entry)
        else:
            # Append to consolidated log file
            with open(self.consolidated_log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        logger.info(f"Logged interaction for player {player_id}")

    def get_consolidated_log_path(self) -> str:
        """Get the path to the consolidated log file.

        Returns:
            Path to the consolidated log file
        """
        return self.consolidated_log_path


# Singleton instance
_chat_logger = None

def get_chat_logger(game_session=None, log_dir: str = None) -> ChatLogger:
    """Get the singleton chat logger instance.

    Args:
        game_session: GameSession instance to use for logging
        log_dir: Directory to store log files. If None, determines based on environment.

    Returns:
        ChatLogger instance
    """
    global _chat_logger

    if log_dir is None:
        # Check if we're running tests
        if os.environ.get("PARLOURBENCH_USE_MOCK") == "1":
            # Setup test logs directory similar to how snapshots are handled
            project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            log_dir = os.path.join(project_root, "data", "test", "logs")
        else:
            log_dir = "data/logs"

    if _chat_logger is None:
        _chat_logger = ChatLogger(game_session=game_session, log_dir=log_dir)
    elif game_session is not None and _chat_logger.game_session is None:
        # Update the existing logger with the game session
        _chat_logger.game_session = game_session
        _chat_logger.consolidated_log_path = game_session.chat_logs_path

    return _chat_logger