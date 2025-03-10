# main.py
import sys
import os
import logging
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core.engine import GameEngine
from core.llm.production_llm_client import ProductionLLMClient
import handlers.common  # Import handlers to ensure they are registered

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ParlourBench")

def main():
    """
    Main entry point for ParlourBench.

    Parses command line arguments and runs the game engine.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py <game_config_file>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return

    # Ensure directories exist
    os.makedirs("data/snapshots", exist_ok=True)
    os.makedirs("data/results", exist_ok=True)

    # Initialize and run the game
    try:
        engine = GameEngine(config_path, ProductionLLMClient)
        engine.run_game()

        # Print results
        print("\nGame complete!")
        winner = engine.state.get_winner()
        if winner:
            print(f"Winner: {winner['id']} with score {winner['state'].get('score', 'N/A')}")
        else:
            print("No winner determined")
    except Exception as e:
        logger.error(f"Error running game: {str(e)}")
        raise

if __name__ == "__main__":
    main()
