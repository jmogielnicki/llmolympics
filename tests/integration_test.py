#!/usr/bin/env python3
"""
Integration test for the LLM Diplomacy Game.
This script simulates a complete game flow to ensure all components work together correctly.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from events.bus import EventBus
from events.logger import EventLogger
from game.controller import GameController
from interface.commands import CommandParser
from interface.terminal import TerminalInterface
from game.state import GameStatus, PlayerStatus

class IntegrationTest:
    def __init__(self):
        # Initialize components
        self.event_bus = EventBus()
        self.game_controller = GameController(self.event_bus)
        self.event_logger = EventLogger(self.event_bus)
        self.terminal = TerminalInterface(self.game_controller, self.event_logger)
        self.parser = CommandParser()

        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "failures": []
        }

    def run_command(self, cmd_str):
        """Run a command string and return the result"""
        print(f"\nRunning command: {cmd_str}")
        import shlex
        args = shlex.split(cmd_str)
        parsed_cmd = self.parser.parse_args(args)
        return self.terminal.handle_command(parsed_cmd)

    def assert_condition(self, condition, description):
        """Assert a condition and track results"""
        self.test_results["total_tests"] += 1
        if condition:
            self.test_results["passed"] += 1
            print(f"✅ PASS: {description}")
            return True
        else:
            self.test_results["failed"] += 1
            self.test_results["failures"].append(description)
            print(f"❌ FAIL: {description}")
            return False

    def run_tests(self):
        """Run the integration tests"""
        print("Starting LLM Diplomacy Game Integration Tests")
        print("=" * 50)

        # Test 1: Initialize game with 4 players
        self.run_command("init --players=4")
        self.assert_condition(
            len(self.game_controller.game_state.players) == 4,
            "Game initialized with 4 players"
        )

        # Test 2: Check initial game state
        state = self.game_controller.get_game_state()
        self.assert_condition(
            state.status == GameStatus.SETUP,
            "Game status is SETUP after initialization"
        )

        # Test 3: Start the game
        self.run_command("start")
        self.assert_condition(
            self.game_controller.game_state.status == GameStatus.ACTIVE,
            "Game status is ACTIVE after starting"
        )
        self.assert_condition(
            self.game_controller.game_state.round == 1,
            "Game is in round 1 after starting"
        )

        # Test 4: Process player messages
        player1_msg = "Hello everyone, I suggest we form an alliance."
        self.run_command(f"message --player=player1 --content=\"{player1_msg}\"")
        self.assert_condition(
            self.game_controller.game_state.messages[-1].content == player1_msg,
            "Player1's message was recorded correctly"
        )
        self.assert_condition(
            self.game_controller.game_state.current_turn == "player2",
            "Turn advanced to player2 after player1's message"
        )

        # Process remaining player messages
        self.run_command("message --player=player2 --content=\"I agree with player1.\"")
        self.run_command("message --player=player3 --content=\"I'm suspicious of player4.\"")
        self.run_command("message --player=player4 --content=\"I think we should vote out player3.\"")

        # Test 5: Check if game transitioned to voting phase
        self.assert_condition(
            self.game_controller.game_state.phase.value == "voting",
            "Game transitioned to voting phase after all players sent messages"
        )

        # Test 6: Submit votes
        self.run_command("vote --voter=player1 --target=player3")
        self.run_command("vote --voter=player2 --target=player3")
        self.run_command("vote --voter=player3 --target=player4")

        # Last vote should trigger elimination and new round
        self.run_command("vote --voter=player4 --target=player3")

        # Test 7: Check elimination
        self.assert_condition(
            self.game_controller.game_state.players["player3"].status == PlayerStatus.ELIMINATED,
            "Player3 was eliminated after voting"
        )

        # Test 8: Check new round started
        self.assert_condition(
            self.game_controller.game_state.round == 2,
            "Game advanced to round 2"
        )

        # Test 9: Check active players in new round
        active_players = [p for p, data in self.game_controller.game_state.players.items()
                         if data.status == PlayerStatus.ACTIVE]
        self.assert_condition(
            len(active_players) == 3,
            "3 active players remain in round 2"
        )

        # Test 10: Check if player3 is not in active players
        self.assert_condition(
            "player3" not in active_players,
            "player3 is not in the active players list"
        )

        # Test 11: Export event log
        log_file = "test_game_log.json"
        self.run_command(f"export-log --file={log_file}")
        self.assert_condition(
            os.path.exists(os.path.join("logs", log_file)),
            "Event log was exported successfully"
        )

        # Print test summary
        print("\n" + "=" * 50)
        print("Test Summary:")
        print(f"Total tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed']}")
        print(f"Failed: {self.test_results['failed']}")

        if self.test_results["failures"]:
            print("\nFailures:")
            for i, failure in enumerate(self.test_results["failures"], 1):
                print(f"{i}. {failure}")

        return self.test_results["failed"] == 0

if __name__ == "__main__":
    test = IntegrationTest()
    success = test.run_tests()
    sys.exit(0 if success else 1)