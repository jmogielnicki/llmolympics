# utils/game_session.py
import os
import time
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("GameSession")

class GameSession:
    """
    Manages logging and tracking for a single game run.

    Creates a unique session directory and provides methods
    for saving different types of game data.
    """

    def __init__(self, config, base_dir="data/sessions"):
        """
        Initialize a new game session.

        Args:
            config (dict): The game configuration
            base_dir (str): The base directory for all session data
        """
        # Generate unique session ID
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"{config['game']['name'].lower().replace(' ', '_')}_{self.timestamp}"

        # Set up directory structure
        self.base_dir = base_dir
        self.session_dir = os.path.join(base_dir, self.timestamp)

        # Create session directory
        os.makedirs(self.session_dir, exist_ok=True)

        # Save a copy of the game configuration
        self.config = config
        config_path = os.path.join(self.session_dir, "game_config.yaml")
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        logger.info(f"Created game session: {self.session_id} in {self.session_dir}")

        # Initialize paths for different log types
        self.snapshots_path = os.path.join(self.session_dir, "snapshots.jsonl")
        self.chat_logs_path = os.path.join(self.session_dir, "chat_logs.jsonl")
        self.results_path = os.path.join(self.session_dir, "results.json")

        # Track statistics
        self.snapshot_count = 0
        self.event_count = 0
        self.chat_message_count = 0

    def save_snapshot(self, snapshot_data):
        """
        Save a game state snapshot.

        Args:
            snapshot_data (dict): The snapshot data to save
        """
        # Add session metadata
        snapshot_data["session_id"] = self.session_id
        snapshot_data["snapshot_id"] = self.snapshot_count
        snapshot_data["record_type"] = "snapshot"

        # Append to snapshots file
        with open(self.snapshots_path, 'a') as f:
            f.write(json.dumps(snapshot_data) + "\n")

        self.snapshot_count += 1
        return self.snapshot_count - 1  # Return the snapshot ID

    def save_chat_log(self, chat_data):
        """
        Save a chat interaction log.

        Args:
            chat_data (dict): The chat data to save
        """
        # Add session metadata
        chat_data["session_id"] = self.session_id

        # Append to chat logs file
        with open(self.chat_logs_path, 'a') as f:
            f.write(json.dumps(chat_data) + "\n")

        self.chat_message_count += 1

    def save_event(self, event_type, event_data, phase_id=None, round_num=None):
        """
        Save a game event.

        Args:
            event_type (str): Type of event
            event_data (dict): Event-specific data
            phase_id (str, optional): The phase ID when event occurred
            round_num (int, optional): The round number when event occurred
        """
        event = {
            "session_id": self.session_id,
            "event_id": self.event_count,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "phase_id": phase_id,
            "round_num": round_num,
            "data": event_data,
            "record_type": "event"
        }

        # Append to snapshots file since it's the consolidated record
        with open(self.snapshots_path, 'a') as f:
            f.write(json.dumps(event) + "\n")

        self.event_count += 1
        return self.event_count - 1  # Return the event ID

    def save_results(self, results_data):
        """
        Save the final game results.

        Args:
            results_data (dict): The results data to save
        """
        # Add session metadata
        results_data["session_id"] = self.session_id
        results_data["timestamp"] = datetime.now().isoformat()
        results_data["stats"] = {
            "snapshot_count": self.snapshot_count,
            "event_count": self.event_count,
            "chat_message_count": self.chat_message_count
        }

        # Write to results file
        with open(self.results_path, 'w') as f:
            json.dump(results_data, f, indent=2)

        return self.results_path