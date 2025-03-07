import time
from typing import Dict, List, Optional

from game.controller import GameController
from events.bus import EventBus, Event, EventType
from player.manager import PlayerManager
from game.state import GamePhase, PlayerStatus

class LLMGameController:
    def __init__(self, game_controller: GameController, player_manager: PlayerManager):
        """Initialize the LLM Game Controller.

        Args:
            game_controller: The game controller instance
            player_manager: The player manager for LLM interactions
        """
        self.game_controller = game_controller
        self.player_manager = player_manager

    def initialize_game(self, player_count: int):
        """Initialize a new game with the specified number of players."""
        self.game_controller.initialize_game(player_count)

    def start_game(self):
        """Start the game and run it automatically with LLM players."""
        self.game_controller.start_game()
        self._run_game_loop()

    def _run_game_loop(self):
        """Run the game loop until completion."""
        while self.game_controller.game_state.status.value == "active":
            # Handle current phase
            if self.game_controller.game_state.phase == GamePhase.DISCUSSION:
                self._run_discussion_phase()
            elif self.game_controller.game_state.phase == GamePhase.VOTING:
                self._run_voting_phase()

            # Add a small delay to make it easier to follow
            time.sleep(1)

    def _run_discussion_phase(self):
        """Run the discussion phase with LLM players."""
        game_state = self.game_controller.game_state

        # Process turns until the phase is complete
        while game_state.phase == GamePhase.DISCUSSION:
            current_player = game_state.current_turn
            print(f"\n========= Discussion Phase - {current_player}'s turn =========")

            # Generate a message from the current player
            try:
                message = self.player_manager.generate_player_message(current_player, game_state)
                print(f"[{current_player}]: {message}")

                # Process the message in the game controller
                self.game_controller.process_player_message(current_player, message)
            except Exception as e:
                print(f"Error generating message for {current_player}: {e}")
                # Force advance to next player
                self.game_controller._advance_to_next_player()

    def _run_voting_phase(self):
        """Run the voting phase with LLM players."""
        game_state = self.game_controller.game_state
        print("\n========= Voting Phase =========")

        # Get all active players
        active_players = [
            player_id for player_id, player in game_state.players.items()
            if player.status == PlayerStatus.ACTIVE
        ]

        # Collect votes from all active players
        for player_id in active_players:
            try:
                vote_result = self.player_manager.get_player_vote(player_id, game_state)

                if vote_result:
                    vote, reasoning = vote_result
                    print(f"[{player_id}] votes to eliminate: {vote}")
                    print(f"Reasoning: {reasoning[:150]}...")

                    # Submit the vote
                    self.game_controller.submit_vote(player_id, vote)
                else:
                    # Handle invalid vote
                    random_vote = self.player_manager.handle_invalid_vote(player_id, active_players)
                    if random_vote:
                        self.game_controller.submit_vote(player_id, random_vote)
            except Exception as e:
                print(f"Error getting vote from {player_id}: {e}")
                # Try to handle with random vote
                random_vote = self.player_manager.handle_invalid_vote(player_id, active_players)
                if random_vote:
                    self.game_controller.submit_vote(player_id, random_vote)