from typing import List, Optional, Dict
import argparse

class CommandParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="LLM Diplomacy Game")
        self._setup_commands()

    def _setup_commands(self) -> None:
        """Set up the command-line arguments"""
        subparsers = self.parser.add_subparsers(dest="command", help="Command to execute")

        # Initialize game command
        init_parser = subparsers.add_parser("init", help="Initialize a new game")
        init_parser.add_argument("--players", type=int, required=True, help="Number of players")

        # Start game command
        subparsers.add_parser("start", help="Start the game")

        # Show state command
        subparsers.add_parser("state", help="Show the current game state")

        # Force next phase command
        subparsers.add_parser("next-phase", help="Force transition to next phase")

        # Force next round command
        subparsers.add_parser("next-round", help="Force transition to next round")

        # Manual elimination command
        elim_parser = subparsers.add_parser("eliminate", help="Manually eliminate a player")
        elim_parser.add_argument("--player", type=str, required=True, help="Player ID to eliminate")

        # Export log command
        export_parser = subparsers.add_parser("export-log", help="Export event log to file")
        export_parser.add_argument("--file", type=str, help="File name for export")

    def parse_args(self, args: Optional[List[str]] = None) -> Dict:
        """Parse command-line arguments"""
        parsed = self.parser.parse_args(args)
        return vars(parsed)