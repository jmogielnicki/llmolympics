from enum import Enum
from typing import Dict, List, Callable, Any
import uuid
from datetime import datetime

class EventType(Enum):
    GAME_INITIALIZED = "GameInitialized"
    ROUND_STARTED = "RoundStarted"
    PHASE_CHANGED = "PhaseChanged"
    PLAYER_TURN_STARTED = "PlayerTurnStarted"
    PLAYER_MESSAGE_RECEIVED = "PlayerMessageReceived"
    VOTE_SUBMITTED = "VoteSubmitted"
    PLAYER_ELIMINATED = "PlayerEliminated"
    GAME_ENDED = "GameEnded"

class Event:
    def __init__(self, event_type: EventType, data: dict, game_state_hash: str = None):
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.data = data
        self.game_state_hash = game_state_hash

    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "data": self.data,
            "game_state_hash": self.game_state_hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        """Create event from dictionary"""
        event = cls(
            event_type=EventType(data["event_type"]),
            data=data["data"],
            game_state_hash=data.get("game_state_hash")
        )
        event.event_id = data["event_id"]
        event.timestamp = datetime.fromisoformat(data["timestamp"])
        return event

class EventBus:
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable[[Event], None]]] = {
            event_type: [] for event_type in EventType
        }
        self.event_log: List[Event] = []

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type"""
        self.subscribers[event_type].append(callback)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers"""
        self.event_log.append(event)
        for callback in self.subscribers[event.event_type]:
            callback(event)

    def get_event_log(self) -> List[Event]:
        """Get the event log"""
        return self.event_log