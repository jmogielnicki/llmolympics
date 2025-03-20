# core/game/handlers/creative_competition.py
import logging
import random
from core.game.handlers.base import PhaseHandler
from core.game.handlers.registry import HandlerRegistry
from core.llm.production_llm_client import ProductionLLMClient

logger = logging.getLogger("CreativeCompetition")

class CreativeCompetitionBase:
    """Base class with shared methods for creative competition handlers."""

    def get_content_type(self, game_state):
        """Get the content type from the game configuration."""
        game_name = game_state.config['game']['name'].lower()
        if 'poetry' in game_name:
            return 'poem'
        elif 'story' in game_name:
            return 'story'
        else:
            return 'creative content'


@HandlerRegistry.register("creative_prompt_handler")
class CreativePromptHandler(PhaseHandler, CreativeCompetitionBase):
    """
    Handler for the prompt creation phase in creative competitions.

    Manages the process where one player creates a prompt for others.
    """

    def __init__(self):
        """Initialize the handler."""
        self.llm_client = None

    def process_player(self, game_state, player):
        """Process a single player's action (prompt creation)."""
        if self.llm_client is None:
            self.llm_client = ProductionLLMClient(chat_logger=game_state.chat_logger)

        # Check that this player is the prompter (check both roles list and legacy role field)
        has_prompter_role = ('roles' in player and 'prompter' in player['roles']) or player.get('role') == 'prompter'

        if not has_prompter_role:
            logger.warning(f"Player {player['id']} is not the prompter but was asked to create a prompt")
            return None

        # Add content type to context
        extra_context = {
            "content_type": self.get_content_type(game_state)
        }

        # Get prompt from the prompter
        prompt = self.llm_client.get_action(
            game_state,
            player,
            game_state.current_phase,
            extra_context=extra_context
        )

        logger.info(f"Received prompt from player {player['id']}: {prompt[:50]}...")

        # Store the prompt in shared state immediately
        game_state.shared_state['content_prompt'] = prompt

        return prompt


@HandlerRegistry.register("creative_content_handler")
class CreativeContentHandler(PhaseHandler, CreativeCompetitionBase):
    """
    Handler for the content creation phase in creative competitions.

    Manages the process where all players create content based on a prompt.
    """

    def __init__(self):
        """Initialize the handler."""
        self.llm_client = None

    def process_player(self, game_state, player):
        """Process a single player's content creation."""
        if self.llm_client is None:
            self.llm_client = ProductionLLMClient(chat_logger=game_state.chat_logger)

        # Get the prompt from shared state
        prompt = game_state.shared_state.get('content_prompt')
        if not prompt:
            logger.error("No prompt found in shared state")
            raise ValueError("No prompt found in shared state for content creation")

        # Add content type and prompt to context
        extra_context = {
            "content_type": self.get_content_type(game_state),
            "content_prompt": prompt
        }

        # Get content from this player
        content = self.llm_client.get_action(
            game_state,
            player,
            game_state.current_phase,
            extra_context=extra_context
        )

        # Store in player state for easy access
        player['state']['submission'] = content

        logger.info(f"Received content from player {player['id']}: {content[:50]}...")

        return content


@HandlerRegistry.register("content_voting_handler")
class ContentVotingHandler(PhaseHandler, CreativeCompetitionBase):
    """
    Handler for the voting phase in creative competitions.

    Manages the process where players vote on each other's content.
    """

    def __init__(self):
        """Initialize the handler."""
        self.llm_client = None

    def process_player(self, game_state, player):
        """Process a single player's vote."""
        if self.llm_client is None:
            self.llm_client = ProductionLLMClient(chat_logger=game_state.chat_logger)

        player_id = player['id']

        # Get all submissions
        submissions = {}
        for p in game_state.get_active_players():
            if p['id'] != player_id:  # Exclude self
                if 'submission' in p['state']:
                    submissions[p['id']] = p['state']['submission']

        if not submissions:
            logger.error(f"No submissions available for player {player_id} to vote on")
            raise ValueError("No valid submissions to vote on")

        # Format submissions for the prompt
        formatted_submissions = ""
        for pid, content in submissions.items():
            # Truncate long submissions for readability
            if len(content) > 500:
                content = content[:497] + "..."
            formatted_submissions += f"### SUBMISSION BY {pid}:\n{content}\n\n"

        # Add context for voting
        extra_context = {
            "content_type": self.get_content_type(game_state),
            "content_prompt": game_state.shared_state.get('content_prompt', 'Unknown prompt'),
            "submissions": formatted_submissions,
            "player_submission": player['state'].get('submission', '')
        }

        # Get vote from this player
        vote = self.llm_client.get_action(
            game_state,
            player,
            game_state.current_phase,
            extra_context=extra_context
        )

        # Validate vote - must be a player ID and not self
        if vote not in submissions:
            logger.warning(f"Invalid vote from player {player_id}: {vote}. Defaulting to random valid vote.")
            valid_votes = list(submissions.keys())
            if valid_votes:
                vote = random.choice(valid_votes)
            else:
                logger.error(f"No valid votes available for player {player_id}")
                return None

        logger.info(f"Player {player_id} voted for: {vote}")

        return vote


@HandlerRegistry.register("tally_votes_handler")
class TallyVotesHandler(PhaseHandler, CreativeCompetitionBase):
    """
    Handler for tallying votes in creative competitions.
    """

    def process(self, game_state):
        """
        Process the vote tallying phase.
        """
        # Get votes from shared state
        votes = game_state.shared_state.get('voting_responses', {})
        if not votes:
            logger.warning("No votes found, cannot determine winner")
            return True

        logger.info(f"Processing resolution with votes: {votes}")

        # Count votes for each player
        vote_counts = {}
        for player_id, voted_for in votes.items():
            vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1

        logger.info(f"Vote counts: {vote_counts}")

        # Find player(s) with the most votes
        max_votes = 0
        winners = []

        for player_id, count in vote_counts.items():
            if count > max_votes:
                max_votes = count
                winners = [player_id]
            elif count == max_votes:
                winners.append(player_id)

        # Store results in shared state
        game_state.shared_state['winners'] = winners
        game_state.shared_state['vote_counts'] = vote_counts

        # Update player scores
        for player in game_state.players:
            player_id = player['id']
            # Score is the number of votes received
            player['state']['score'] = vote_counts.get(player_id, 0)

        # Log the winner(s)
        if len(winners) == 1:
            logger.info(f"Winner: {winners[0]} with {max_votes} votes")
            game_state.game_session.save_event(
                "game_results",
                {
                    "winner": winners[0],
                    "votes": max_votes
                }
            )
        else:
            logger.info(f"Tie between players: {winners} with {max_votes} votes each")
            game_state.game_session.save_event(
                "game_results",
                {
                    "tied_winners": winners,
                    "votes": max_votes
                }
            )

        # Signal game end
        return True


# Register handlers for specific phases in Poetry Slam
@HandlerRegistry.register("prompt_creation")
class PromptCreationHandler(CreativePromptHandler):
    """Alias for CreativePromptHandler specifically for prompt_creation phase."""
    pass

@HandlerRegistry.register("content_creation")
class ContentCreationHandler(CreativeContentHandler):
    """Alias for CreativeContentHandler specifically for content_creation phase."""
    pass

@HandlerRegistry.register("voting")
class VotingHandler(ContentVotingHandler):
    """Alias for ContentVotingHandler specifically for voting phase."""
    pass

@HandlerRegistry.register("tally_votes")
class TallyVotesHandler(TallyVotesHandler):
    """Alias for TallyVotesHandler specifically for resolution phase."""
    pass