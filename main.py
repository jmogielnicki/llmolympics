import sys
import os
from dotenv import load_dotenv
from events.bus import EventBus
from events.logger import EventLogger
from game.controller import GameController
from interface.terminal import TerminalInterface

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Check for required API keys if running in non-interactive mode
    if "--llm" in sys.argv:
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: No API keys found in environment. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
            print("You can create a .env file based on the .env.example template.")
            sys.exit(1)

    # Initialize components
    event_bus = EventBus()
    game_controller = GameController(event_bus)
    event_logger = EventLogger(event_bus)
    terminal = TerminalInterface(game_controller, event_logger)

    # Auto-initialize LLM mode if requested
    if "--llm" in sys.argv:
        sys.argv.remove("--llm")
        print("Initializing LLM mode...")
        if not terminal.init_llm_mode():
            print("Failed to initialize LLM mode.")
            sys.exit(1)

    if len(sys.argv) > 1:
        # Command-line mode
        terminal.handle_command(terminal.command_parser.parse_args())
    else:
        # Interactive mode
        terminal.run_interactive()

if __name__ == "__main__":
    main()