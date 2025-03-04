import sys
from events.bus import EventBus
from events.logger import EventLogger
from game.controller import GameController
from interface.terminal import TerminalInterface

def main():
    # Initialize components
    event_bus = EventBus()
    game_controller = GameController(event_bus)
    event_logger = EventLogger(event_bus)
    terminal = TerminalInterface(game_controller, event_logger)

    if len(sys.argv) > 1:
        # Command-line mode
        terminal.handle_command(terminal.command_parser.parse_args())
    else:
        # Interactive mode
        terminal.run_interactive()

if __name__ == "__main__":
    main()