#!/bin/bash

# Make sure the script is executable: chmod +x run_llm_game.sh

# Default configuration
PLAYER_COUNT=6
CONFIG_FILE="config/llm_models.json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --experiment=*)
      EXPERIMENT="${1#*=}"
      CONFIG_FILE="config/experiments/${EXPERIMENT}.json"
      shift
      ;;
    --players=*)
      PLAYER_COUNT="${1#*=}"
      shift
      ;;
    --help)
      echo "Usage: $0 [--experiment=NAME] [--players=N]"
      echo ""
      echo "Options:"
      echo "  --experiment=NAME    Use experiment configuration from config/experiments/NAME.json"
      echo "  --players=N          Set number of players (default: 6)"
      echo ""
      echo "Examples:"
      echo "  $0                                  # Run with default config"
      echo "  $0 --experiment=mixed_models       # Run with mixed models experiment"
      echo "  $0 --experiment=openai_vs_anthropic # Compare OpenAI vs Anthropic models"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Verify Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: No .env file found. You may need to create one with API keys."
    echo "See .env.example for the required format."
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment and installing dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Ensure config directory exists
mkdir -p config
mkdir -p logs
mkdir -p config/experiments

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Model configuration not found at $CONFIG_FILE"
    exit 1
fi

echo "Starting LLM Diplomacy Game with $PLAYER_COUNT players"
echo "Using model configuration: $CONFIG_FILE"

# Automatically initialize and start an LLM game
python main.py --llm << EOF
init --players=$PLAYER_COUNT
init-llm --config=$CONFIG_FILE
start-llm
EOF