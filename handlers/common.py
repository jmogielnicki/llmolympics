# handlers/common.py
import logging
from handlers.base import PhaseHandler
from handlers.registry import HandlerRegistry
from core.llm.llm_client import LLMClient

logger = logging.getLogger("ProductionHandlers")

@HandlerRegistry.register("player_action_handler")
class PlayerActionHandler(PhaseHandler):
    """
    Handler for processing a single player's action.

    This simplified handler focuses solely on getting an action from a single player,
    with the game engine handling all sequencing logic.
    """

    def __init__(self):
        """Initialize the handler with an LLM client."""
        self.llm_client = LLMClient()

    def process_player(self, game_state, player):
        """
        Process an action for a single player.

        Args:
            game_state (GameState): The current game state
            player (dict): The player to process

        Returns:
            any: The player's action
        """
        phase_id = game_state.current_phase
        phase_config = self._get_phase_config(game_state)
        player_id = player['id']

        logger.info(f"Getting action for player {player_id} in phase {phase_id}")

        try:
            # Call the LLM client to get the player's action
            action = self.llm_client.get_action(game_state, player, phase_id)

            if action is None:
                logger.error(f"Received None action for player {player_id}, using default")
                ValueError("Received None action from LLM client")

            logger.info(f"Player {player_id} chose: {action}")
            return action

        except Exception as e:
            logger.error(f"Error getting action for player {player_id}: {str(e)}")
            ValueError("Error getting action from LLM client")

    def process(self, game_state):
        """
        Legacy method for compatibility with existing code.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: Always returns True
        """
        logger.warning("Legacy process method called, should use process_player instead")
        return True


# Communication handler will be implemented when needed


# Automatic phase handlers (not player-focused)

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
            logger.info(f"Added to decision history: round {game_state.shared_state['current_round']}, decisions: {decisions}")

        # Check if this is the final round
        is_final_round = game_state.shared_state['current_round'] >= game_state.config['rounds']['count']

        # Only increment if not the final round
        if not is_final_round:
            game_state.shared_state['current_round'] += 1
            return True  # More rounds to go
        else:
            return False  # No more rounds, end game


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


@HandlerRegistry.register("eliminate_most_voted")
class EliminateMostVotedHandler(PhaseHandler):
    """
    Handler for eliminating the player with the most votes in Diplomacy.
    """

    def process(self, game_state):
        """
        Process the elimination based on votes.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: True if only one player remains, False otherwise
        """
        # Get votes from shared state
        votes = game_state.get_votes()
        logger.info(f"Processing elimination with votes: {votes}")

        if not votes:
            logger.warning("No votes found, cannot eliminate any player")
            return False

        # Count votes for each player
        vote_counts = {}
        for player_id, voted_for in votes.items():
            vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1

        logger.info(f"Vote counts: {vote_counts}")

        # Find the player with the most votes
        most_votes = 0
        most_voted = None

        for player_id, count in vote_counts.items():
            if count > most_votes:
                most_votes = count
                most_voted = player_id

        # Handle ties using tiebreaker rules
        if most_voted is None:
            logger.warning("No player received any votes")
            return False

        # Find all players with the highest vote count
        tied_players = [p for p, c in vote_counts.items() if c == most_votes]

        if len(tied_players) > 1:
            logger.info(f"Tie detected between players: {tied_players}")

            # Get tiebreaker rule
            tiebreakers = game_state.config.get('tiebreakers', ['random_selection'])
            tiebreaker = tiebreakers[0] if tiebreakers else 'random_selection'

            logger.info(f"Using tiebreaker: {tiebreaker}")

            if tiebreaker == 'random_selection':
                # Randomly select one of the tied players
                import random
                most_voted = random.choice(tied_players)
                logger.info(f"Randomly selected {most_voted} from tied players")

        # Eliminate the player with the most votes
        if most_voted:
            logger.info(f"Eliminating player {most_voted} with {most_votes} votes")
            game_state.eliminate_player(most_voted)

            # Record elimination in shared state if tracking exists
            if 'eliminated_players' not in game_state.shared_state:
                game_state.shared_state['eliminated_players'] = []

            game_state.shared_state['eliminated_players'].append({
                'player': most_voted,
                'votes': most_votes,
                'round': game_state.shared_state.get('current_round', 0)
            })

            # Increment round counter
            current_round = game_state.shared_state.get('current_round', 1)
            game_state.shared_state['current_round'] = current_round + 1

        # Check if only one player remains
        active_players = game_state.get_active_players()
        logger.info(f"Active players remaining: {len(active_players)}")

        return len(active_players) <= 1


@HandlerRegistry.register("check_last_player_standing")
class CheckLastPlayerStandingHandler(PhaseHandler):
    """
    Handler for checking if there is only one player remaining in elimination games.
    """

    def process(self, game_state):
        """
        Check if there is only one player remaining.

        Args:
            game_state (GameState): The current game state

        Returns:
            bool: True if only one player remains, False otherwise
        """
        active_players = game_state.get_active_players()
        logger.info(f"Checking win condition: {len(active_players)} active players")

        # Return True if only one player remains
        return len(active_players) <= 1


# Additional handlers for Ghost game
@HandlerRegistry.register("validate_letter_addition")
class ValidateLetterAdditionHandler(PhaseHandler):
    """Handler for validating letter additions in Ghost."""

    def process(self, game_state):
        """Validate the letter addition."""
        # Get the current word fragment
        word_fragment = game_state.shared_state.get('word_fragment', '')

        # Get the added letter from responses
        responses = game_state.shared_state.get('letter_addition_responses', {})
        current_player_index = game_state.shared_state.get('current_player_index', 0)
        active_players = game_state.get_active_players()

        player_id = active_players[current_player_index]['id'] if active_players and current_player_index < len(active_players) else None
        letter = responses.get(player_id, '')

        if not letter:
            logger.warning(f"No letter provided by player {player_id}")
            return False

        # Take just the first character if multiple were provided
        letter = letter[0].lower()

        # Update the word fragment
        new_fragment = word_fragment + letter
        game_state.shared_state['word_fragment'] = new_fragment

        logger.info(f"Player {player_id} added letter '{letter}', new fragment: '{new_fragment}'")

        # In a real implementation, we would check against a dictionary here
        # For simplicity, we'll just return True for testing
        return True