# main.py
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core.game.engine import GameEngine
import core.game.handlers.common  # Import handlers to ensure they are registered
import core.game.handlers.creative_competition

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ParlourBench")

def main():
    """
    Main entry point for LLM Showdown.

    Parses command line arguments and runs the game engine.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py <game_config_file>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return

    # Ensure base session directory exists
    os.makedirs("data/sessions", exist_ok=True)

    # Initialize and run the game
    try:
        engine = GameEngine(config_path)

        # Print session information
        print(f"\nGame session started: {engine.game_session.session_id}")
        print(f"Session directory: {engine.game_session.session_dir}")

        engine.run_game()

        # Print results
        print("\nGame complete!")
        winner = engine.state.get_winner()
        if winner:
            if winner['id'] == 'tie':
                tied_players = ", ".join(winner.get('tied_players', []))
                print(f"Game ended in a tie between: {tied_players} with score {winner['state'].get('score', 'N/A')}")
            else:
                print(f"Winner: {winner['id']} with score {winner['state'].get('score', 'N/A')}")
        else:
            print("No winner determined")

        # Print session statistics
        print(f"\nSession statistics:")
        print(f"- Snapshots: {engine.game_session.snapshot_count}")
        print(f"- Events: {engine.game_session.event_count}")
        print(f"- Chat messages: {engine.game_session.chat_message_count}")
        print(f"- Session directory: {engine.game_session.session_dir}")
    except Exception as e:
        logger.error(f"Error running game: {str(e)}")
        raise

if __name__ == "__main__":
    main()