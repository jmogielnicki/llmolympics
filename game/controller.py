import random
from typing import Dict, List, Optional, Tuple
import hashlib
import json

from game.state import GameState, Player, GameStatus, PlayerStatus, GamePhase, Message, EliminationRecord
from events.bus import EventBus, Event, EventType

class GameController:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.game_state = GameState()

    def _calculate_state_hash(self) -> str:
        """Calculate a hash of the current game state for event logging"""
        state_dict = self.game_state.to_dict()
        state_json = json.dumps(state_dict, sort_keys=True)
        return hashlib.md5(state_json.encode()).hexdigest()

    def initialize_game(self, player_count: int) -> None:
        """Initialize a new game with the specified number of players"""
        self.game_state = GameState()

        # Create players
        for i in range(1, player_count + 1):
            player_id = f"player{i}"
            self.game_state.players[player_id] = Player(id=player_id)
            self.game_state.votes[player_id] = None

        self.game_state.status = GameStatus.SETUP

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.GAME_INITIALIZED,
            data={
                "player_count": player_count,
                "player_ids": list(self.game_state.players.keys())
            },
            game_state_hash=self._calculate_state_hash()
        ))

    def start_game(self) -> None:
        """Start the game and transition to the first round"""
        if self.game_state.status != GameStatus.SETUP:
            raise ValueError("Game is already started")

        self.game_state.status = GameStatus.ACTIVE
        self.start_round(1)

    def start_round(self, round_number: int) -> None:
        """Start a new round"""
        self.game_state.round = round_number
        self.game_state.phase = GamePhase.DISCUSSION

        # Reset votes
        for player_id in self.game_state.votes:
            self.game_state.votes[player_id] = None

        active_players = self._get_active_players()
        if not active_players:
            raise ValueError("No active players available")

        # Set the first player's turn
        self.game_state.current_turn = active_players[0]

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.ROUND_STARTED,
            data={
                "round": round_number,
                "active_players": active_players
            },
            game_state_hash=self._calculate_state_hash()
        ))

        # Start the first player's turn
        self._start_player_turn(self.game_state.current_turn)

    def _get_active_players(self) -> List[str]:
        """Get a list of active player IDs"""
        return [
            player_id for player_id, player in self.game_state.players.items()
            if player.status == PlayerStatus.ACTIVE
        ]

    def _start_player_turn(self, player_id: str) -> None:
        """Start a player's turn in the discussion phase"""
        if self.game_state.phase != GamePhase.DISCUSSION:
            raise ValueError("Player turns only apply in discussion phase")

        self.game_state.current_turn = player_id

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.PLAYER_TURN_STARTED,
            data={
                "player_id": player_id,
                "round": self.game_state.round,
                "phase": self.game_state.phase.value
            },
            game_state_hash=self._calculate_state_hash()
        ))

    def process_player_message(self, player_id: str, content: str) -> bool:
        """Process a message from a player during the discussion phase"""
        if self.game_state.phase != GamePhase.DISCUSSION:
            return False

        if player_id != self.game_state.current_turn:
            return False

        # Add message to history
        message = Message(
            round=self.game_state.round,
            phase=self.game_state.phase,
            player_id=player_id,
            content=content
        )
        self.game_state.messages.append(message)

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.PLAYER_MESSAGE_RECEIVED,
            data={
                "player_id": player_id,
                "content": content,
                "round": self.game_state.round,
                "phase": self.game_state.phase.value,
                "timestamp": message.timestamp.isoformat()
            },
            game_state_hash=self._calculate_state_hash()
        ))

        # Move to next player's turn
        return self._advance_to_next_player()

    def _advance_to_next_player(self) -> bool:
        """Advance to the next player's turn or transition to voting phase if all players have had their turn"""
        active_players = self._get_active_players()

        # Find the index of the current player
        current_index = active_players.index(self.game_state.current_turn)

        # If this is the last player, transition to voting phase
        if current_index == len(active_players) - 1:
            self.transition_to_voting_phase()
            return True

        # Otherwise, move to the next player
        next_player = active_players[current_index + 1]
        self._start_player_turn(next_player)
        return True

    def transition_to_voting_phase(self) -> None:
        """Transition from discussion to voting phase"""
        if self.game_state.phase != GamePhase.DISCUSSION:
            raise ValueError("Can only transition to voting phase from discussion phase")

        self.game_state.phase = GamePhase.VOTING
        self.game_state.current_turn = None

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.PHASE_CHANGED,
            data={
                "round": self.game_state.round,
                "phase": self.game_state.phase.value,
                "active_players": self._get_active_players()
            },
            game_state_hash=self._calculate_state_hash()
        ))

    def submit_vote(self, voter_id: str, target_id: str) -> bool:
        """Submit a vote during the voting phase"""
        if self.game_state.phase != GamePhase.VOTING:
            return False

        if voter_id not in self._get_active_players():
            return False

        if target_id not in self._get_active_players():
            return False

        if voter_id == target_id:
            return False

        # Record the vote
        self.game_state.votes[voter_id] = target_id

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.VOTE_SUBMITTED,
            data={
                "voter_id": voter_id,
                "target_id": target_id,
                "round": self.game_state.round
            },
            game_state_hash=self._calculate_state_hash()
        ))

        # Check if all active players have voted
        active_players = self._get_active_players()
        all_voted = all(self.game_state.votes.get(player_id) is not None for player_id in active_players)

        if all_voted:
            self._process_votes()

        return True

    def _process_votes(self) -> None:
        """Process votes and eliminate the player with the most votes"""
        vote_counts: Dict[str, int] = {}

        # Count votes
        for voter_id, target_id in self.game_state.votes.items():
            if voter_id in self._get_active_players() and target_id is not None:
                vote_counts[target_id] = vote_counts.get(target_id, 0) + 1

        if not vote_counts:
            return

        # Find player(s) with the most votes
        max_votes = max(vote_counts.values())
        most_voted = [player_id for player_id, count in vote_counts.items() if count == max_votes]

        # In case of a tie, randomly select one
        eliminated_id = random.choice(most_voted)

        # Create elimination record
        elimination_record = EliminationRecord(
            round=self.game_state.round,
            eliminated=eliminated_id,
            votes={k: v for k, v in self.game_state.votes.items() if k in self._get_active_players()}
        )
        self.game_state.elimination_history.append(elimination_record)

        # Eliminate the player
        self._eliminate_player(eliminated_id)

        # Check if game has ended
        if self._check_game_end_condition():
            self._end_game()
        else:
            # Start the next round
            self.start_round(self.game_state.round + 1)

    def _eliminate_player(self, player_id: str) -> None:
        """Eliminate a player from the game"""
        player = self.game_state.players.get(player_id)
        if not player:
            return

        player.status = PlayerStatus.ELIMINATED
        player.elimination_round = self.game_state.round

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.PLAYER_ELIMINATED,
            data={
                "player_id": player_id,
                "round": self.game_state.round,
                "vote_tally": {
                    player_id: sum(1 for target in self.game_state.votes.values() if target == player_id)
                    for player_id in self._get_active_players() + [player_id]
                }
            },
            game_state_hash=self._calculate_state_hash()
        ))

    def _check_game_end_condition(self) -> bool:
        """Check if the game has ended (only one player remains)"""
        active_players = self._get_active_players()
        return len(active_players) <= 1

    def _end_game(self) -> None:
        """End the game"""
        self.game_state.status = GameStatus.COMPLETED
        winner = self._get_active_players()[0] if self._get_active_players() else None

        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.GAME_ENDED,
            data={
                "winner": winner,
                "rounds_played": self.game_state.round,
                "elimination_order": [
                    record.eliminated for record in sorted(
                        self.game_state.elimination_history,
                        key=lambda r: r.round
                    )
                ]
            },
            game_state_hash=self._calculate_state_hash()
        ))

    def get_game_state(self) -> GameState:
        """Get the current game state"""
        return self.game_state

    def get_game_state_dict(self) -> dict:
        """Get the current game state as a dictionary"""
        return self.game_state.to_dict()