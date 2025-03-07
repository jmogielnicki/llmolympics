import json
import os
from typing import Dict, Any, Optional, List

from game.controller import GameController
from events.bus import EventBus
from events.logger import EventLogger
from interface.commands import CommandParser
from game.state import GamePhase

# For LLM mode
from player.manager import PlayerManager
from game.llm_controller import LLMGameController

class TerminalInterface:
    def __init__(self, game_controller: GameController, event_logger: EventLogger):
        self.game_controller = game_controller
        self.event_logger = event_logger
        self.command_parser = CommandParser()

        # Initialize player manager (will be used if LLM mode is enabled)
        self.player_manager = None
        self.llm_controller = None

    def print_game_state(self) -> None:
        """Print the current game state to the terminal"""
        state = self.game_controller.get_game_state_dict()
        print("\n=== GAME STATE ===")
        print(f"Game ID: {state['game_id']}")
        print(f"Status: {state['status']}")
        print(f"Round: {state['round']}")
        print(f"Phase: {state['phase']}")

        print("\nPlayers:")
        for player_id, player in state['players'].items():
            status = player['status']
            elim_info = f" (eliminated in round {player['elimination_round']})" if status == "eliminated" else ""
            print(f"  {player_id}: {status}{elim_info}")

        if state['current_turn']:
            print(f"\nCurrent Turn: {state['current_turn']}")

        print("\nVotes:")
        for player_id, vote in state['votes'].items():
            if state['players'][player_id]['status'] == "active":
                vote_info = vote if vote else "none"
                print(f"  {player_id} -> {vote_info}")

        print("\nMessages:")
        # Only show the last 5 messages for brevity
        for msg in state['messages'][-5:]:
            print(f"  [{msg['round']}][{msg['phase']}] {msg['player_id']}: {msg['content'][:100]}...")

        print("\nElimination History:")
        for record in state['elimination_history']:
            print(f"  Round {record['round']}: {record['eliminated']} eliminated")

    def init_llm_mode(self, models_config="config/llm_models.json") -> bool:
        """Initialize LLM mode with the specified models configuration."""
        # Check if the config file exists
        if not os.path.exists(models_config):
            print(f"Error: LLM models config file not found: {models_config}")
            return False

        try:
            # Initialize player manager
            self.player_manager = PlayerManager(models_config)

            # Initialize LLM controller
            self.llm_controller = LLMGameController(
                self.game_controller,
                self.player_manager
            )

            print(f"LLM mode initialized with models from {models_config}")
            return True
        except Exception as e:
            print(f"Error initializing LLM mode: {e}")
            return False

    def handle_command(self, command: Dict[str, Any]) -> bool:
        """Handle a CLI command"""
        cmd = command.get("command")

        if cmd == "init":
            self.game_controller.initialize_game(command["players"])
            print(f"Game initialized with {command['players']} players")
            return True

        elif cmd == "start":
            self.game_controller.start_game()
            print("Game started")
            return True

        elif cmd == "init-llm":
            models_config = command.get("config", "config/llm_models.json")
            return self.init_llm_mode(models_config)

        elif cmd == "start-llm":
            if not self.llm_controller:
                print("Error: LLM mode not initialized. Use 'init-llm' first.")
                return False

            # Make sure game is initialized
            if self.game_controller.game_state.status.value == "setup":
                print("Starting LLM game...")
                self.llm_controller.start_game()
                return True
            else:
                print("Error: Game already started or completed")
                return False

        elif cmd == "state":
            self.print_game_state()
            return True

        elif cmd == "next-phase":
            if self.game_controller.game_state.phase == GamePhase.DISCUSSION:
                self.game_controller.transition_to_voting_phase()
                print("Transitioned to voting phase")
            else:
                print("Cannot transition from current phase")
            return True

        elif cmd == "next-round":
            self.game_controller.start_round(self.game_controller.game_state.round + 1)
            print(f"Started round {self.game_controller.game_state.round}")
            return True

        elif cmd == "eliminate":
            player_id = command["player"]
            self.game_controller._eliminate_player(player_id)
            print(f"Player {player_id} eliminated")
            return True

        elif cmd == "export-log":
            file_name = command.get("file")
            path = self.event_logger.save_event_log(file_name)
            print(f"Event log exported to: {path}")
            return True

        elif cmd == "message":
            player_id = command["player"]
            content = command["content"]
            success = self.game_controller.process_player_message(player_id, content)
            if success:
                print(f"Message from {player_id} processed successfully")
            else:
                print(f"Failed to process message. Make sure it's {player_id}'s turn and the game is in discussion phase.")
            return True

        elif cmd == "vote":
            voter_id = command["voter"]
            target_id = command["target"]
            success = self.game_controller.submit_vote(voter_id, target_id)
            if success:
                print(f"Vote from {voter_id} for {target_id} recorded")
            else:
                print(f"Failed to record vote. Make sure the game is in voting phase.")
            return True

        return False

    def run_interactive(self) -> None:
        """Run the interface in interactive mode"""
        # Enable readline support for arrow keys and command history
        try:
            import readline
            # Set history file
            import os
            history_file = os.path.join(os.path.expanduser("~"), ".llm_diplomacy_history")
            try:
                readline.read_history_file(history_file)
                # Default history length is -1 (infinite), which may grow unruly
                readline.set_history_length(1000)
            except FileNotFoundError:
                pass

            # Enable tab completion for commands
            def completer(text, state):
                commands = ["init", "start", "state", "next-phase", "next-round",
                           "eliminate", "message", "vote", "export-log", "help", "exit", "quit",
                           "init-llm", "start-llm"]
                matches = [cmd for cmd in commands if cmd.startswith(text)]
                if state < len(matches):
                    return matches[state]
                else:
                    return None

            readline.parse_and_bind("tab: complete")
            readline.set_completer(completer)

            # Save history on exit
            import atexit
            atexit.register(readline.write_history_file, history_file)
        except ImportError:
            print("Warning: readline module not available. Arrow keys and command history will not work.")
            pass

        print("LLM Diplomacy Game - Interactive CLI")
        print("Type 'help' for available commands")

        while True:
            cmd = input("\n> ").strip()

            if cmd == "exit" or cmd == "quit":
                break

            if cmd == "help":
                print("Available commands:")
                print("  init --players=N     Initialize a new game with N players")
                print("  start                Start the game")
                print("  init-llm [--config=path] Initialize LLM mode with optional config path")
                print("  start-llm            Start game with LLM players")
                print("  state                Show the current game state")
                print("  next-phase           Force transition to next phase")
                print("  next-round           Force transition to next round")
                print("  eliminate --player=X Manually eliminate a player")
                print("  message --player=X --content=\"Message content\" Submit a player message")
                print("  vote --voter=X --target=Y Submit a vote")
                print("  export-log [--file=name] Export event log to file")
                print("  exit, quit           Exit the program")
                continue

            try:
                # Use shlex to properly handle quoted arguments
                import shlex
                args = shlex.split(cmd)
                parsed_cmd = self.command_parser.parse_args(args)
                self.handle_command(parsed_cmd)
            except Exception as e:
                print(f"Error: {e}")