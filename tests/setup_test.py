#!/usr/bin/env python3
# setup_test.py
import os
import sys
import shutil
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Setup")

def create_directory_structure():
    """Create the directory structure needed for the project."""
    directories = [
        "config/games",
        "templates",
        "core",
        "handlers",
        "utils",
        "data/snapshots",
        "data/results",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def create_init_files():
    """Create __init__.py files for Python packages."""
    packages = [
        "core",
        "handlers",
        "utils",
    ]

    for package in packages:
        init_file = os.path.join(package, "__init__.py")
        with open(init_file, 'w') as f:
            f.write("# Package initialization\n")
        logger.info(f"Created init file: {init_file}")

def create_template_files():
    """Create template files for prompts."""
    templates = {
        "pd_decision.txt": """
You are playing the Prisoner's Dilemma game.

Current game state:
- Round: {current_round} of 5
- Your current score: {player_score}
- Your player ID: {player_id}

In this game, you must decide whether to cooperate with or defect against your opponent.
The payoffs are:
- If both players cooperate: 3 points each
- If both players defect: 1 point each
- If you defect and they cooperate: You get 5 points, they get 0
- If you cooperate and they defect: You get 0 points, they get 5

Please respond with your decision: COOPERATE or DEFECT
"""
    }

    for filename, content in templates.items():
        filepath = os.path.join("templates", filename)
        with open(filepath, 'w') as f:
            f.write(content.strip())
        logger.info(f"Created template file: {filepath}")

def create_config_files():
    """Create configuration files for games."""
    configs = {
        "prisoners_dilemma.yaml": """
game:
  name: "Prisoner's Dilemma"
  description: "A classic game of cooperation and betrayal"
  type: "simultaneous_choice"

players:
  min: 2
  max: 2
  roles: "symmetric"

setup:
  initial_state:
    resources: []
    assignments: []

phases:
  - id: "decision"
    type: "simultaneous_action"
    actions:
      - name: "choose"
        options: ["cooperate", "defect"]
    next_phase: "resolution"

  - id: "resolution"
    type: "automatic"
    handler: "calculate_pd_outcome"
    next_phase_condition: "rounds_remaining"
    next_phase_success: "decision"  # If more rounds remain
    next_phase_failure: "game_end"  # If all rounds complete

rounds:
  count: 5
  progression: "fixed"

state:
  player_state:
    - name: "score"
      initial: 0
      visible: true
  shared_state:
    - name: "current_round"
      initial: 1
      visible: true
  hidden_state: []
  history_state:
    - name: "decision_history"
      tracking: "decisions"

win_condition:
  type: "highest_score"
  score_field: "score"
  trigger: "rounds_complete"

scoring:
  rules:
    - condition: "both_cooperate"
      points: [3, 3]
    - condition: "both_defect"
      points: [1, 1]
    - condition: "p1_defect_p2_cooperate"
      points: [5, 0]
    - condition: "p1_cooperate_p2_defect"
      points: [0, 5]

llm_integration:
  model: "mock:default"  # Use mock implementation
  system_prompts:
    decision: "You are a player in a Prisoner's Dilemma game. Think strategically about cooperation and self-interest."
  prompts:
    decision: "pd_decision"
  parsers:
    decision: "choice_parser"
"""
    }

    for filename, content in configs.items():
        filepath = os.path.join("config/games", filename)
        with open(filepath, 'w') as f:
            f.write(content.strip())
        logger.info(f"Created config file: {filepath}")

def setup_handlers():
    """Create necessary handler files for testing."""
    # Import handler registration code if it already exists
    handlers_init = """# Package initialization
from handlers.registry import HandlerRegistry
from handlers.base import PhaseHandler, PhaseController

# Import handlers
from handlers.example_handlers import PDOutcomeHandler, SimultaneousActionHandler
"""

    with open("handlers/__init__.py", 'w') as f:
        f.write(handlers_init)

    # Create example handlers file
    example_handlers = """
import logging
import random
from handlers.base import PhaseHandler
from handlers.registry import HandlerRegistry

logger = logging.getLogger("ExampleHandlers")

@HandlerRegistry.register("calculate_pd_outcome")
class PDOutcomeHandler(PhaseHandler):
    \"\"\"
    Handler for the Prisoner's Dilemma outcome phase.

    Calculates scores based on players' decisions and
    updates the game state accordingly.
    \"\"\"

    def process(self, game_state):
        \"\"\"
        Process the Prisoner's Dilemma outcome.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: True if more rounds remain, False otherwise
        \"\"\"
        # Get decisions from state
        decisions = game_state.shared_state.get("decision_responses", {})

        logger.info(f"Processing PD outcomes with decisions: {decisions}")

        # For testing, if no real decisions exist, generate mock ones
        if not decisions or len(decisions) < 2:
            logger.warning("No real decisions found, generating mock decisions")
            decisions = {
                "player_1": "cooperate" if random.random() > 0.5 else "defect",
                "player_2": "cooperate" if random.random() > 0.5 else "defect"
            }
            game_state.shared_state["decision_responses"] = decisions

        # Apply scoring rules
        for player in game_state.get_active_players():
            player_id = player['id']
            player_decision = decisions.get(player_id)

            # Get opponent's decision
            opponent = None
            for p in game_state.get_active_players():
                if p['id'] != player_id:
                    opponent = p
                    break

            if opponent:
                opponent_id = opponent['id']
                opponent_decision = decisions.get(opponent_id)

                # Calculate points
                points = self._calculate_points(player_decision, opponent_decision)

                # Initialize score if not present
                if 'score' not in player['state']:
                    player['state']['score'] = 0

                # Update score
                player['state']['score'] += points

                logger.info(f"Player {player_id} ({player_decision}) vs {opponent_id} ({opponent_decision}): +{points} points")

        # Record in history
        if 'decision_history' in game_state.history_state:
            game_state.history_state['decision_history'].append({
                'round': game_state.shared_state['current_round'],
                'decisions': decisions,
            })

        # Increment round counter
        current_round = game_state.shared_state.get('current_round', 1)
        game_state.shared_state['current_round'] = current_round + 1

        max_rounds = game_state.config['rounds'].get('count', 5)
        logger.info(f"Completed round {current_round} of {max_rounds}")

        # Return condition result for phase transition - True if more rounds remain
        return game_state.shared_state['current_round'] <= max_rounds

    def _calculate_points(self, player_decision, opponent_decision):
        \"\"\"
        Calculate points based on decisions.

        Args:
            player_decision (str): The player's decision
            opponent_decision (str): The opponent's decision

        Returns:
            int: Points earned
        \"\"\"
        # Default values if decisions are not valid
        if not player_decision or not opponent_decision:
            return 0

        # Normalize decisions
        player_decision = player_decision.lower().strip()
        opponent_decision = opponent_decision.lower().strip()

        if player_decision == "cooperate" and opponent_decision == "cooperate":
            return 3
        elif player_decision == "defect" and opponent_decision == "cooperate":
            return 5
        elif player_decision == "cooperate" and opponent_decision == "defect":
            return 0
        else:  # Both defect
            return 1


@HandlerRegistry.register_default("simultaneous_action")
class SimultaneousActionHandler(PhaseHandler):
    \"\"\"
    Default handler for simultaneous action phases.

    Gets actions from all active players simultaneously
    and updates the game state with the responses.
    \"\"\"

    def process(self, game_state):
        \"\"\"
        Process a simultaneous action phase.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: Always returns True
        \"\"\"
        phase_config = self._get_phase_config(game_state)

        logger.info(f"Processing simultaneous action phase: {game_state.current_phase}")

        # Get LLM client
        from core.llm import LLMClient
        llm_client = LLMClient()

        # Get actions from all active players
        responses = {}
        for player in game_state.get_active_players():
            player_id = player['id']

            # Get action using LLM
            try:
                action = llm_client.get_action(game_state, player)
                responses[player_id] = action
                logger.info(f"Player {player_id} action: {action}")
            except Exception as e:
                logger.error(f"Error getting action for player {player_id}: {str(e)}")

                # Fallback to random action
                options = []
                if 'actions' in phase_config and phase_config['actions']:
                    action = phase_config['actions'][0]
                    if 'options' in action:
                        options = action['options']

                fallback_action = random.choice(options) if options else "default_action"
                responses[player_id] = fallback_action
                logger.warning(f"Using fallback action for player {player_id}: {fallback_action}")

        # Store responses in state
        game_state.set_action_responses(responses)

        # Always return True for this handler
        return True
"""

    with open("handlers/example_handlers.py", 'w') as f:
        f.write(example_handlers.strip())

    logger.info("Set up handler files")

def setup_parsers():
    """Create necessary parser files for testing."""
    parsers_file = """
import logging
from core.llm import ResponseParserRegistry

logger = logging.getLogger("Parsers")

@ResponseParserRegistry.register("choice_parser")
class ChoiceParser:
    \"\"\"
    Parser for choice responses.

    Parses responses from the LLM for choice-based actions,
    such as "cooperate" or "defect" in Prisoner's Dilemma.
    \"\"\"

    def parse(self, response, phase_config):
        \"\"\"
        Parse a choice response from the LLM.

        Args:
            response (str): The LLM's response
            phase_config (dict): The phase configuration

        Returns:
            str: The parsed choice
        \"\"\"
        logger.debug(f"Parsing choice response: {response[:50]}...")

        response = response.strip().lower()

        # Get valid options from phase config
        options = []
        if 'actions' in phase_config and phase_config['actions']:
            action = phase_config['actions'][0]
            if 'options' in action:
                options = [opt.lower() for opt in action['options']]

        logger.debug(f"Valid options: {options}")

        # Check if response contains any of the valid options
        for option in options:
            if option in response:
                logger.info(f"Found option in response: {option}")
                return option

        # If no match found, try to infer from context
        if options and len(options) >= 2:
            if "cooperate" in response or "collaboration" in response or "together" in response:
                logger.info("Inferred cooperation from context")
                for opt in options:
                    if "cooperate" in opt:
                        return opt

            if "defect" in response or "betray" in response or "self" in response:
                logger.info("Inferred defection from context")
                for opt in options:
                    if "defect" in opt:
                        return opt

        # Default to first option if nothing matches
        if options:
            logger.warning(f"No match found, defaulting to first option: {options[0]}")
            return options[0]

        logger.error("No valid options found and no fallback available")
        return None


@ResponseParserRegistry.register("default_parser")
class DefaultParser:
    \"\"\"
    Default parser for when no specific parser is specified.

    Simply returns the response as-is.
    \"\"\"

    def parse(self, response, phase_config):
        \"\"\"
        Parse a response from the LLM.

        Args:
            response (str): The LLM's response
            phase_config (dict): The phase configuration

        Returns:
            str: The raw response
        \"\"\"
        logger.info("Using default parser")
        return response.strip()
"""

    with open("utils/parsers.py", 'w') as f:
        f.write(parsers_file.strip())

    logger.info("Set up parser files")

def main():
    """Main entry point for the setup script."""
    logger.info("Setting up ParlourBench test environment")

    # Create directory structure
    create_directory_structure()

    # Create __init__.py files
    create_init_files()

    # Create template files
    create_template_files()

    # Create configuration files
    create_config_files()

    # Set up handlers
    setup_handlers()

    # Set up parsers
    setup_parsers()

    logger.info("Setup complete!")
    logger.info("You can now run the integration test with: python test_integration.py")

if __name__ == "__main__":
    main()