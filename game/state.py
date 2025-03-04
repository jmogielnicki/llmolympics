import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

class GameStatus(Enum):
    SETUP = "setup"
    ACTIVE = "active"
    COMPLETED = "completed"

class PlayerStatus(Enum):
    ACTIVE = "active"
    ELIMINATED = "eliminated"

class GamePhase(Enum):
    DISCUSSION = "discussion"
    VOTING = "voting"

@dataclass
class Player:
    id: str
    status: PlayerStatus = PlayerStatus.ACTIVE
    elimination_round: Optional[int] = None

@dataclass
class EliminationRecord:
    round: int
    eliminated: str
    votes: Dict[str, str]

@dataclass
class Message:
    round: int
    phase: GamePhase
    player_id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GameState:
    game_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: GameStatus = GameStatus.SETUP
    round: int = 0
    phase: GamePhase = GamePhase.DISCUSSION
    players: Dict[str, Player] = field(default_factory=dict)
    current_turn: Optional[str] = None
    elimination_history: List[EliminationRecord] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    votes: Dict[str, Optional[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert the game state to a dictionary for serialization"""
        return {
            "game_id": self.game_id,
            "status": self.status.value,
            "round": self.round,
            "phase": self.phase.value,
            "players": {
                player_id: {
                    "id": player.id,
                    "status": player.status.value,
                    "elimination_round": player.elimination_round
                } for player_id, player in self.players.items()
            },
            "current_turn": self.current_turn,
            "elimination_history": [
                {
                    "round": record.round,
                    "eliminated": record.eliminated,
                    "votes": record.votes
                } for record in self.elimination_history
            ],
            "messages": [
                {
                    "round": msg.round,
                    "phase": msg.phase.value,
                    "player_id": msg.player_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                } for msg in self.messages
            ],
            "votes": self.votes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """Create a game state from a dictionary"""
        game_state = cls(
            game_id=data.get("game_id", str(uuid.uuid4())),
            status=GameStatus(data.get("status", GameStatus.SETUP.value)),
            round=data.get("round", 0),
            phase=GamePhase(data.get("phase", GamePhase.DISCUSSION.value)),
            current_turn=data.get("current_turn")
        )

        # Restore players
        for player_id, player_data in data.get("players", {}).items():
            game_state.players[player_id] = Player(
                id=player_data["id"],
                status=PlayerStatus(player_data["status"]),
                elimination_round=player_data.get("elimination_round")
            )

        # Restore elimination history
        for record_data in data.get("elimination_history", []):
            game_state.elimination_history.append(
                EliminationRecord(
                    round=record_data["round"],
                    eliminated=record_data["eliminated"],
                    votes=record_data["votes"]
                )
            )

        # Restore messages
        for msg_data in data.get("messages", []):
            game_state.messages.append(
                Message(
                    round=msg_data["round"],
                    phase=GamePhase(msg_data["phase"]),
                    player_id=msg_data["player_id"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"])
                )
            )

        # Restore votes
        game_state.votes = data.get("votes", {})

        return game_state