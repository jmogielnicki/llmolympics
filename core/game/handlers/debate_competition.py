# core/game/handlers/debate_competition.py
import logging
import random
import copy
from core.game.handlers.base import PhaseHandler
from core.game.handlers.registry import HandlerRegistry

logger = logging.getLogger("DebateCompetition")

# List of debate topics with neutral side identifiers
DEBATE_TOPICS = [
    {
        "topic": "Is universal basic income a viable economic policy?",
        "sides": [
            {"side_id": "pro-ubi", "position": "Universal basic income is viable"},
            {"side_id": "anti-ubi", "position": "Universal basic income is not viable"}
        ]
    },
    {
        "topic": "Is cryptocurrency a legitimate alternative to traditional banking?",
        "sides": [
            {"side_id": "pro-crypto", "position": "Cryptocurrency is a legitimate alternative to traditional banking"},
            {"side_id": "anti-crypto", "position": "Cryptocurrency is not a legitimate alternative to traditional banking"}
        ]
    },
    {
        "topic": "Should genetic modification of human embryos be permitted?",
        "sides": [
            {"side_id": "pro-genetic-mod", "position": "Genetic modification of human embryos should be permitted"},
            {"side_id": "anti-genetic-mod", "position": "Genetic modification of human embryos should not be permitted"}
        ]
    },
    {
        "topic": "Is nuclear energy the best solution for climate change?",
        "sides": [
            {"side_id": "pro-nuclear", "position": "Nuclear energy is the best solution for climate change"},
            {"side_id": "anti-nuclear", "position": "Nuclear energy is not the best solution for climate change"}
        ]
    }
]

@HandlerRegistry.register("debate_topic_selection")
class DebateTopicSelectionHandler(PhaseHandler):
    """Handler for selecting a debate topic."""

    def process(self, game_state):
        """Select a debate topic and store in shared state."""
        # Randomly select a topic from the predefined list
        selected_topic = random.choice(DEBATE_TOPICS)

        # Store the topic and sides in shared state
        game_state.shared_state['debate_topic'] = selected_topic['topic']
        game_state.shared_state['sides'] = selected_topic['sides']

        logger.info(f"Selected debate topic: {selected_topic['topic']}")

        # Log the event
        game_state.game_session.save_event(
            "topic_selection",
            {
                "topic": selected_topic['topic'],
                "sides": selected_topic['sides']
            }
        )

        return True


@HandlerRegistry.register("debate_side_assignment")
class DebateSideAssignmentHandler(PhaseHandler):
    """Handler for assigning debate sides to players."""

    def process(self, game_state):
        """Assign sides to debaters and initialize state."""
        # Get all players with 'debater' role (roles are already assigned by GameState initialization)
        debaters = [p for p in game_state.get_active_players()
                    if ('roles' in p and 'debater' in p['roles']) or p.get('role') == 'debater']

        logger.info(f"Found {len(debaters)} active debaters")

        # For standard debate, we need exactly 2 debaters
        if len(debaters) != 2:
            logger.error(f"Expected 2 debaters, found {len(debaters)}")
            raise ValueError(f"Expected 2 debaters, found {len(debaters)}")

        # Get sides from shared state
        sides = game_state.shared_state.get('sides', [])
        if len(sides) != 2:
            logger.error(f"Expected 2 sides, found {len(sides)}")
            raise ValueError(f"Expected 2 sides, found {len(sides)}")

        # Assign sides to debaters (randomly for the first debate)
        debater1, debater2 = debaters

        # Assign first side to first debater
        debater1['state']['side_id'] = sides[0]['side_id']
        debater1['state']['position'] = sides[0]['position']

        # Assign second side to second debater
        debater2['state']['side_id'] = sides[1]['side_id']
        debater2['state']['position'] = sides[1]['position']

        # Randomly select which side goes first in rebuttals
        first_rebutter_side_id = random.choice([sides[0]['side_id'], sides[1]['side_id']])
        game_state.shared_state['first_rebutter_side_id'] = first_rebutter_side_id

        logger.info(f"Assigned sides: {debater1['id']} -> {sides[0]['side_id']}, {debater2['id']} -> {sides[1]['side_id']}")
        logger.info(f"First rebutter side: {first_rebutter_side_id}")

        # Log the event
        game_state.game_session.save_event(
            "side_assignment",
            {
                "assignments": [
                    {"player_id": debater1['id'], "side_id": sides[0]['side_id']},
                    {"player_id": debater2['id'], "side_id": sides[1]['side_id']}
                ],
                "first_rebutter": first_rebutter_side_id
            }
        )

        # Reorder debaters so the one with first_rebutter_side_id comes first
        reordered_debaters = sorted(debaters, key=lambda p: 0 if p['state'].get('side_id') == first_rebutter_side_id else 1)

        # Rebuild players array preserving non-debaters at their positions
        new_players = []
        debater_idx = 0

        for p in game_state.players:
            if p in debaters:
                new_players.append(reordered_debaters[debater_idx])
                debater_idx += 1
            else:
                new_players.append(p)

        game_state.players = new_players

        logger.info(f"Reordered players array with first rebutter {first_rebutter_side_id} first among debaters")

        return True


@HandlerRegistry.register("debate_argument_handler")
class DebateArgumentHandler(PhaseHandler):
    """Handler for opening arguments in the debate."""

    def __init__(self):
        """Initialize the handler."""
        self.llm_client = None

    def process_player(self, game_state, player):
        """Process a player's opening argument."""
        from core.llm.client_factory import create_llm_client

        if self.llm_client is None:
            self.llm_client = create_llm_client(chat_logger=game_state.chat_logger)

        # Get player's assigned side
        side_id = player['state'].get('side_id')
        position = player['state'].get('position')

        if not side_id or not position:
            logger.error(f"Player {player['id']} does not have an assigned debate side")
            raise ValueError(f"Player {player['id']} does not have an assigned debate side")

        # Add context for the opening argument
        extra_context = {
            "debate_topic": game_state.shared_state.get('debate_topic', ''),
            "side_id": side_id,
            "position": position,
            "sides": game_state.shared_state.get('sides', []),
            "sides_swapped": game_state.shared_state.get('sides_swapped', False)
        }

        # Get opening argument from player
        opening_argument = self.llm_client.get_action(
            game_state,
            player,
            game_state.current_phase,
            extra_context=extra_context
        )

        logger.info(f"Received opening argument from {player['id']} for side {side_id}")

        # Store in shared state for access by other players
        current_arguments = game_state.shared_state.get('current_arguments', {})
        current_arguments[player['id']] = {
            "side_id": side_id,
            "argument": opening_argument
        }
        game_state.shared_state['current_arguments'] = current_arguments

        return opening_argument


@HandlerRegistry.register("debate_rebuttal_handler")
class DebateRebuttalHandler(PhaseHandler):
    """Handler for rebuttal rounds in the debate."""

    def __init__(self):
        """Initialize the handler."""
        self.llm_client = None

    def process(self, game_state):
        # Check if we're in the final round
        current_round = game_state.shared_state.get('current_round', 1)
        max_rounds = game_state.shared_state.get('max_rounds', 3)

        logger.info(f"DebateRebuttalHandler - Round {current_round}/{max_rounds}")

        # Return True ONLY if we're in the final round
        is_final_round = (current_round >= max_rounds)

        logger.info(f"DebateRebuttalHandler - Is final round? {is_final_round}")
        return is_final_round


    def process_player(self, game_state, player):
        """Process a player's rebuttal."""
        from core.llm.client_factory import create_llm_client

        if self.llm_client is None:
            self.llm_client = create_llm_client(chat_logger=game_state.chat_logger)

        # Get player's assigned side
        side_id = player['state'].get('side_id')
        position = player['state'].get('position')

        if not side_id or not position:
            logger.error(f"Player {player['id']} does not have an assigned debate side")
            raise ValueError(f"Player {player['id']} does not have an assigned debate side")

        # Get all current arguments
        current_arguments = game_state.shared_state.get('current_arguments', {})

        # Find opponent's argument and ID
        opponent_argument = None
        opponent_id = None

        for pid, arg_data in current_arguments.items():
            if pid != player['id']:
                opponent_argument = arg_data.get('argument', '')
                opponent_id = pid
                break

        # Get debate history (all rounds so far in this debate)
        debate_history = []

        # First add opening arguments if they exist
        if 'argument_history' in game_state.history_state:
            for entry in game_state.history_state['argument_history']:
                if entry.get('responses'):
                    for pid, response in entry.get('responses').items():
                        player_side_id = None
                        for p in game_state.players:
                            if p['id'] == pid:
                                player_side_id = p['state'].get('side_id', '')
                                break

                        if pid == player['id']:
                            debate_history.append({
                                "round": entry.get('round', 0),
                                "speaker": "You",
                                "side_id": player_side_id,
                                "argument": response
                            })
                        elif pid == opponent_id:
                            debate_history.append({
                                "round": entry.get('round', 0),
                                "speaker": "Opponent",
                                "side_id": player_side_id,
                                "argument": response
                            })

        # Sort by round number
        debate_history.sort(key=lambda x: x.get('round', 0))

        # Format debate history as text
        formatted_history = ""
        for entry in debate_history:
            round_label = "Opening Arguments" if entry.get('round', 0) == 0 else f"Round {entry.get('round', 0)}"
            formatted_history += f"{round_label} - {entry['speaker']} ({entry['side_id']}):\n{entry['argument']}\n\n"

        # Add context for the rebuttal
        extra_context = {
            "debate_topic": game_state.shared_state.get('debate_topic', ''),
            "side_id": side_id,
            "position": position,
            "sides": game_state.shared_state.get('sides', []),
            "current_round": game_state.shared_state.get('current_round', 1),
            "sides_swapped": game_state.shared_state.get('sides_swapped', False),
            "opponent_argument": opponent_argument,
            "is_first_rebutter": side_id == game_state.shared_state.get('first_rebutter_side_id', ''),
            "debate_history": formatted_history
        }

        # Get rebuttal from player
        rebuttal = self.llm_client.get_action(
            game_state,
            player,
            game_state.current_phase,
            extra_context=extra_context
        )

        logger.info(f"Received rebuttal from {player['id']} for side {side_id} in round {game_state.shared_state.get('current_round', 1)}")

        # Update the player's current argument in player state and shared state
        player['state']['current_argument'] = rebuttal

        # Update in shared state
        current_arguments = game_state.shared_state.get('current_arguments', {})
        current_arguments[player['id']] = {
            "side_id": side_id,
            "argument": rebuttal
        }
        game_state.shared_state['current_arguments'] = current_arguments

        return rebuttal

def get_formatted_history(game_state):

    # Get debate history (all rounds so far in this debate)
    debate_history = []
    debater_ids = {}

    # Map side_ids to player_ids for both debaters
    for p in game_state.get_active_players():
        if 'roles' in p and 'debater' in p['roles']:
            side_id = p['state'].get('side_id', '')
            debater_ids[side_id] = p['id']

    # Get history from argument_history
    if 'argument_history' in game_state.history_state:
        for entry in game_state.history_state['argument_history']:
            if entry.get('responses'):
                for pid, response in entry.get('responses').items():
                    player_side_id = None
                    for p in game_state.players:
                        if p['id'] == pid:
                            player_side_id = p['state'].get('side_id', '')
                            break

                    if player_side_id:
                        debate_history.append({
                            "round": entry.get('round', 0),
                            "player_id": pid,
                            "side_id": player_side_id,
                            "argument": response
                        })

    # Sort by round number
    debate_history.sort(key=lambda x: x.get('round', 0))

    # Format debate history as text
    formatted_history = ""
    for entry in debate_history:
        round_label = "Opening Arguments" if entry.get('round', 0) == 0 else f"Round {entry.get('round', 0)}"

        # Find the position for this side_id
        position = ""
        for side in game_state.shared_state.get('sides', []):
            if side.get('side_id') == entry.get('side_id', ''):
                position = side.get('position', '')
                break

        formatted_history += f"{round_label} - {entry['side_id']} ({position}):\n{entry['argument']}\n\n"
    return formatted_history

@HandlerRegistry.register("debate_judging_handler")
class DebateJudgingHandler(PhaseHandler):
    """Handler for judging after each round of debate."""

    def __init__(self):
        """Initialize the handler."""
        self.llm_client = None

    def process_player(self, game_state, player):
        """Process a judge's opinion after a round."""
        from core.llm.client_factory import create_llm_client

        if self.llm_client is None:
            self.llm_client = create_llm_client(chat_logger=game_state.chat_logger)

        # Ensure this is a judge
        if 'roles' not in player or 'judge' not in player['roles']:
            logger.error(f"Player {player['id']} is not a judge")
            raise ValueError(f"Player {player['id']} is not a judge")

        formatted_history = get_formatted_history(game_state)

        # sides array
        game_state.shared_state.get('sides', [])

        # sides ids concated string
        sides_ids = " vs ".join([side.get('side_id') for side in game_state.shared_state.get('sides', [])])

        # Add context for judging
        extra_context = {
            "debate_topic": game_state.shared_state.get('debate_topic', ''),
            "sides": game_state.shared_state.get('sides', []),
            "sides_ids": sides_ids,
            "current_round": game_state.shared_state.get('current_round', 1),
            "sides_swapped": game_state.shared_state.get('sides_swapped', False),
            "is_final": False,
            "debate_history": formatted_history
        }

        # Get opinion from judge
        opinion = self.llm_client.get_action(
            game_state,
            player,
            game_state.current_phase,
            extra_context=extra_context
        )

        logger.info(f"Received opinion from judge {player['id']} in round {game_state.shared_state.get('current_round', 1)}: {opinion}")

        # Store judge's opinion
        judge_opinions = game_state.shared_state.get('judge_opinions', {})

        if 'rounds' not in judge_opinions:
            judge_opinions['rounds'] = {}

        current_round = game_state.shared_state.get('current_round', 1)

        if str(current_round) not in judge_opinions['rounds']:
            judge_opinions['rounds'][str(current_round)] = {}

        judge_opinions['rounds'][str(current_round)][player['id']] = opinion
        game_state.shared_state['judge_opinions'] = judge_opinions

        return opinion

    def process(self, game_state):
        """Process after all judges have given opinions."""
        # Check if we need to move to the next round or end this phase
        current_round = game_state.shared_state.get('current_round', 1)
        max_rounds = game_state.shared_state.get('max_rounds', 3)

        # Increment round counter
        game_state.shared_state['current_round'] = current_round + 1

        # Determine if we continue to next round or end
        return current_round < max_rounds


@HandlerRegistry.register("debate_final_judging_handler")
class DebateFinalJudgingHandler(PhaseHandler):
    """Handler for final judging at the end of a debate."""

    def __init__(self):
        """Initialize the handler."""
        self.llm_client = None

    def process_player(self, game_state, player):
        """Process a judge's final opinion."""
        from core.llm.client_factory import create_llm_client

        if self.llm_client is None:
            self.llm_client = create_llm_client(chat_logger=game_state.chat_logger)

        # Ensure this is a judge
        if 'roles' not in player or 'judge' not in player['roles']:
            logger.error(f"Player {player['id']} is not a judge")
            raise ValueError(f"Player {player['id']} is not a judge")

        formatted_history = get_formatted_history(game_state)

        # sides array
        game_state.shared_state.get('sides', [])

        # sides ids concated string
        sides_ids = " vs ".join([side.get('side_id') for side in game_state.shared_state.get('sides', [])])

        # Add context for judging
        extra_context = {
            "debate_topic": game_state.shared_state.get('debate_topic', ''),
            "sides": game_state.shared_state.get('sides', []),
            "sides_ids": sides_ids,
            "current_round": game_state.shared_state.get('current_round', 1),
            "debate_history": formatted_history,
            "sides_swapped": game_state.shared_state.get('sides_swapped', False),
            "is_final": True
        }

        # Get final opinion from judge
        final_opinion = self.llm_client.get_action(
            game_state,
            player,
            game_state.current_phase,
            extra_context=extra_context
        )

        logger.info(f"Received final opinion from judge {player['id']}: {final_opinion}")

        # Store judge's final opinion
        judge_opinions = game_state.shared_state.get('judge_opinions', {})

        if 'final' not in judge_opinions:
            judge_opinions['final'] = {}

        judge_opinions['final'][player['id']] = final_opinion
        game_state.shared_state['judge_opinions'] = judge_opinions

        return final_opinion

    def process(self, game_state):
        """Process after all judges have given final opinions."""
        # Update scores based on final opinions
        judge_opinions = game_state.shared_state.get('judge_opinions', {})
        final_opinions = judge_opinions.get('final', {})

        # Get all debaters
        debaters = [p for p in game_state.get_active_players()
                   if 'roles' in p and 'debater' in p['roles']]

        # Count votes for each side
        side_votes = {}
        for side in game_state.shared_state.get('sides', []):
            side_id = side.get('side_id', '')
            side_votes[side_id] = 0

        for judge_id, opinion in final_opinions.items():
            if opinion in side_votes:
                side_votes[opinion] += 1

        # Store the results of this debate
        if not game_state.shared_state.get('sides_swapped', False):
            # First debate - use pre_swap
            for debater in debaters:
                side_id = debater['state'].get('side_id', '')
                position = debater['state'].get('position', '')
                votes = side_votes.get(side_id, 0)

                # Initialize pre_swap object
                if 'pre_swap' not in debater['state']:
                    debater['state']['pre_swap'] = {}

                # Store data in pre_swap
                debater['state']['pre_swap']['side_id'] = side_id
                debater['state']['pre_swap']['position'] = position
                debater['state']['pre_swap']['score'] = votes

            # Store results in hidden state
            first_debate_results = {
                "votes": side_votes,
                "judge_opinions": copy.deepcopy(judge_opinions)
            }
            complete_history = game_state.hidden_state.get('complete_history', {})
            complete_history['first_debate'] = first_debate_results
            game_state.hidden_state['complete_history'] = complete_history

            logger.info(f"Stored first debate results in pre_swap: {side_votes}")
            return True

        else:
            # Second debate - use post_swap
            for debater in debaters:
                side_id = debater['state'].get('side_id', '')
                position = debater['state'].get('position', '')
                votes = side_votes.get(side_id, 0)

                # Initialize post_swap object
                if 'post_swap' not in debater['state']:
                    debater['state']['post_swap'] = {}

                # Store data in post_swap
                debater['state']['post_swap']['side_id'] = side_id
                debater['state']['post_swap']['position'] = position
                debater['state']['post_swap']['score'] = votes

            # Store results in hidden state
            second_debate_results = {
                "votes": side_votes,
                "judge_opinions": copy.deepcopy(judge_opinions)
            }
            complete_history = game_state.hidden_state.get('complete_history', {})
            complete_history['second_debate'] = second_debate_results
            game_state.hidden_state['complete_history'] = complete_history

            logger.info(f"Stored second debate results in post_swap: {side_votes}")
            return False


@HandlerRegistry.register("debate_side_swap_handler")
class DebateSideSwapHandler(PhaseHandler):
    """Handler for swapping debate sides between players."""

    def process(self, game_state):
        """Swap the sides between debaters and reset for second debate."""
        # Get all debaters
        debaters = [p for p in game_state.get_active_players()
                   if 'roles' in p and 'debater' in p['roles']]

        if len(debaters) != 2:
            logger.error(f"Expected 2 debaters, found {len(debaters)}")
            raise ValueError(f"Expected 2 debaters, found {len(debaters)}")

        # Swap sides between debaters
        debater1, debater2 = debaters

        # Swap side_id and position
        temp_side_id = debater1['state']['side_id']
        temp_position = debater1['state']['position']

        debater1['state']['side_id'] = debater2['state']['side_id']
        debater1['state']['position'] = debater2['state']['position']

        debater2['state']['side_id'] = temp_side_id
        debater2['state']['position'] = temp_position

        # Reset round counter and other debate-specific state
        game_state.shared_state['current_round'] = 1
        game_state.shared_state['sides_swapped'] = True
        game_state.shared_state['current_arguments'] = {}

        # Keep the same first rebutter side_id (so the other debater goes first now)
        first_rebutter_side_id = game_state.shared_state.get('first_rebutter_side_id', '')

        logger.info(f"Swapped sides: {debater1['id']} -> {debater1['state']['side_id']}, {debater2['id']} -> {debater2['state']['side_id']}")
        logger.info(f"First rebutter side remains: {first_rebutter_side_id}")

        # Reset judge opinions for the new debate
        game_state.shared_state['judge_opinions'] = {}

        # Save first debate history to hidden state but clear for the second debate
        if 'complete_history' not in game_state.hidden_state:
            game_state.hidden_state['complete_history'] = {}

        # Save the argument and judging history
        game_state.hidden_state['complete_history']['first_debate_arguments'] = copy.deepcopy(game_state.history_state.get('argument_history', []))
        game_state.hidden_state['complete_history']['first_debate_judging'] = copy.deepcopy(game_state.history_state.get('judging_history', []))

        # Clear history state for the new debate
        for key in game_state.history_state:
            game_state.history_state[key] = []

        logger.info("Saved first debate history to hidden state and cleared history state for second debate")

        # Log the event
        game_state.game_session.save_event(
            "side_swap",
            {
                "new_assignments": [
                    {"player_id": debater1['id'], "side_id": debater1['state']['side_id']},
                    {"player_id": debater2['id'], "side_id": debater2['state']['side_id']}
                ],
                "first_rebutter": first_rebutter_side_id
            }
        )

        # Reorder debaters so the one with first_rebutter_side_id comes first
        reordered_debaters = sorted(debaters, key=lambda p: 0 if p['state'].get('side_id') == first_rebutter_side_id else 1)

        # Rebuild players array preserving non-debaters at their positions
        new_players = []
        debater_idx = 0

        for p in game_state.players:
            if p in debaters:
                new_players.append(reordered_debaters[debater_idx])
                debater_idx += 1
            else:
                new_players.append(p)

        game_state.players = new_players

        logger.info(f"Reordered players array with first rebutter {first_rebutter_side_id} first among debaters")


        return True


@HandlerRegistry.register("debate_resolution_handler")
class DebateResolutionHandler(PhaseHandler):
    """Handler for resolving the final outcome of both debates."""

    def process(self, game_state):
        """Calculate final scores and determine the winner."""
        # Get all debaters
        debaters = [p for p in game_state.players
                   if 'roles' in p and 'debater' in p['roles']]

        if len(debaters) != 2:
            logger.error(f"Expected 2 debaters, found {len(debaters)}")
            raise ValueError(f"Expected 2 debaters, found {len(debaters)}")

        # Calculate total votes across both debates
        for debater in debaters:
            pre_swap_score = debater['state'].get('pre_swap', {}).get('score', 0)
            post_swap_score = debater['state'].get('post_swap', {}).get('score', 0)
            total_score = pre_swap_score + post_swap_score

            # Set final score
            debater['state']['score'] = total_score

            # Clean up - remove current_argument
            if 'current_argument' in debater['state']:
                del debater['state']['current_argument']

            logger.info(f"Debater {debater['id']} final score: {total_score} " +
                       f"(pre-swap: {pre_swap_score}, post-swap: {post_swap_score})")

        # Determine winner
        debater1, debater2 = debaters

        if debater1['state']['score'] > debater2['state']['score']:
            winner = debater1
        elif debater2['state']['score'] > debater1['state']['score']:
            winner = debater2
        else:
            # Tie - no clear winner
            winner = None

        # Log the final result
        if winner:
            logger.info(f"Winner: {winner['id']} with {winner['state']['score']} total votes")
            game_state.game_session.save_event(
                "game_results",
                {
                    "winner": winner['id'],
                    "scores": {
                        debater1['id']: debater1['state']['score'],
                        debater2['id']: debater2['state']['score']
                    }
                }
            )
        else:
            logger.info(f"Tie between {debater1['id']} and {debater2['id']} with {debater1['state']['score']} votes each")
            game_state.game_session.save_event(
                "game_results",
                {
                    "winner": "tie",
                    "scores": {
                        debater1['id']: debater1['state']['score'],
                        debater2['id']: debater2['state']['score']
                    }
                }
            )

        # Signal end of game
        game_state.game_over = True
        return True