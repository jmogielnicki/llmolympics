import json
import os
from typing import List
from datetime import datetime
from pathlib import Path

from events.bus import Event, EventBus

class EventLogger:
    def __init__(self, event_bus: EventBus, log_dir: str = "logs"):
        self.event_bus = event_bus
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Subscribe to all events
        for event_type in event_bus.subscribers.keys():
            event_bus.subscribe(event_type, self.log_event)

    def log_event(self, event: Event) -> None:
        """Log an event to the console (for now)"""
        print(f"[{event.timestamp.isoformat()}] {event.event_type.value}: {event.data}")

    def save_event_log(self, file_name: str = None) -> str:
        """Save the event log to a file"""
        if file_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"game_{timestamp}.json"

        file_path = self.log_dir / file_name

        with open(file_path, 'w') as f:
            json.dump(
                [event.to_dict() for event in self.event_bus.get_event_log()],
                f,
                indent=2
            )

        return str(file_path)

    def load_event_log(self, file_path: str) -> List[Event]:
        """Load an event log from a file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Event log file not found: {file_path}")

        with open(path, 'r') as f:
            event_data = json.load(f)

        return [Event.from_dict(data) for data in event_data]