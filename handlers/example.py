import logging
import random
from handlers.base import PhaseHandler
from handlers.registry import HandlerRegistry

logger = logging.getLogger("ExampleHandlers")

@HandlerRegistry.register("calculate_pd_outcome")
class PDOutcomeHandler(PhaseHandler):
    """
    Handler for the Prisoner's Dilemma outcome phase.

    Calculates scores based on players' decisions and
    updates the game state accordingly.
    """

    def process(self, game_state):
        """
        Process the Prisoner's Dilemma outcome.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: True if more rounds remain, False otherwise
        """
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
        """
        Calculate points based on decisions.

        Args:
            player_decision (str): The player's decision
            opponent_decision (str): The opponent's decision

        Returns:
            int: Points earned
        """
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
    """
    Default handler for simultaneous action phases.

    Gets actions from all active players simultaneously
    and updates the game state with the responses.
    """

    def process(self, game_state):
        """
        Process a simultaneous action phase.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: Always returns True
        """
        phase_config = self._get_phase_config(game_state)

        logger.info(f"Processing simultaneous action phase: {game_state.current_phase}")

        # For testing purposes, generate mock responses
        # In a real implementation, this would call the LLM client
        responses = {}
        for player in game_state.get_active_players():
            player_id = player['id']

            # Get available options from phase config
            options = []
            if 'actions' in phase_config and phase_config['actions']:
                action = phase_config['actions'][0]
                if 'options' in action:
                    options = action['options']

            # Generate a mock response
            if options:
                response = random.choice(options)
            else:
                response = "default_action"

            responses[player_id] = response
            logger.info(f"Player {player_id} chose: {response}")

        # Store responses in state
        game_state.set_action_responses(responses)

        # Always return True for this handler
        return True