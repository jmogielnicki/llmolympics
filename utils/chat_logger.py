"""Chat history logging for LLM interactions."""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class ChatLogger:
    """Logs chat history for all LLM interactions."""
    
    def __init__(self, log_dir: str = "data/logs"):
        """Initialize the chat logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up file handler for consolidated log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use a slightly different filename for test logs vs regular logs
        is_test = os.environ.get("PARLOURBENCH_USE_MOCK") == "1"
        prefix = "test_" if is_test else ""
        self.consolidated_log_path = os.path.join(log_dir, f"{prefix}chat_history_{timestamp}.jsonl")
        
        # Set up logging
        self.logger = logging.getLogger("chat_logger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
    
    def log_interaction(self, 
                       player_id: str, 
                       messages: List[Dict[str, Any]], 
                       response: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a single LLM interaction.
        
        Args:
            player_id: Identifier for the player/agent
            messages: List of message objects sent to the LLM
            response: Response from the LLM (if available)
            metadata: Additional information about the interaction
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "player_id": player_id,
            "messages": messages,
            "response": response,
            "metadata": metadata or {}
        }
        
        # Append to consolidated log file
        with open(self.consolidated_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        self.logger.info(f"Logged interaction for player {player_id}")
        
    def get_consolidated_log_path(self) -> str:
        """Get the path to the consolidated log file.
        
        Returns:
            Path to the consolidated log file
        """
        return self.consolidated_log_path


# Singleton instance
_chat_logger = None

def get_chat_logger(log_dir: str = None) -> ChatLogger:
    """Get the singleton chat logger instance.
    
    Args:
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
        _chat_logger = ChatLogger(log_dir)
    
    return _chat_logger