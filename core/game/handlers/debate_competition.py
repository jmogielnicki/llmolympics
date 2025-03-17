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
        "topic": "Should tariffs be used to protect domestic industries?",
        "sides": [
            {"side_id": "pro-tariffs", "position": "Tariffs should be used to protect domestic industries"},
            {"side_id": "anti-tariffs", "position": "Tariffs should not be used to protect domestic industries"}
        ]
    },
    {
        "topic": "Is universal basic income a viable economic policy?",
        "sides": [
            {"side_id": "pro-ubi", "position": "Universal basic income is viable"},
            {"side_id": "anti-ubi", "position": "Universal basic income is not viable"}
        ]
    },
    {
        "topic": "Should social media platforms be regulated like public utilities?",
        "sides": [
            {"side_id": "pro-regulation", "position": "Social media should be regulated like utilities"},
            {"side_id": "anti-regulation", "position": "Social media should not be regulated like utilities"}
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
    },
    {
        "topic": "Should college education be free for all citizens?",
        "sides": [
            {"side_id": "pro-free-college", "position": "College education should be free for all citizens"},
            {"side_id": "anti-free-college", "position": "College education should not be free for all citizens"}
        ]
    },
    {
        "topic": "Should autonomous weapons systems be banned internationally?",
        "sides": [
            {"side_id": "pro-ban", "position": "Autonomous weapons systems should be banned internationally"},
            {"side_id": "anti-ban", "position": "Autonomous weapons systems should not be banned internationally"}
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

        # Store the argument in player state and shared state
        player['state']['current_argument'] = opening_argument

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
        """Process the rebuttal round in sequence based on first_rebutter."""
        # Determine player order based on first_rebutter_side_id
        first_rebutter_side_id = game_state.shared_state.get('first_rebutter_side_id', '')

        debaters = [p for p in game_state.get_active_players()
                   if 'roles' in p and 'debater' in p['roles']]

        if len(debaters) != 2:
            logger.error(f"Expected 2 debaters, found {len(debaters)}")
            raise ValueError(f"Expected 2 debaters, found {len(debaters)}")

        # Sort debaters so the first_rebutter is first
        debaters.sort(key=lambda p: 0 if p['state'].get('side_id') == first_rebutter_side_id else 1)

        # Process each debater in sequence
        for debater in debaters:
            self.process_player(game_state, debater)

        return True

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

        # Get current arguments from all debaters
        current_arguments = game_state.shared_state.get('current_arguments', {})

        # Format arguments for the prompt
        formatted_arguments = []
        for player_id, arg_data in current_arguments.items():
            side_id = arg_data.get('side_id', '')
            argument = arg_data.get('argument', '')

            # Find the position for this side_id
            position = ''
            for side in game_state.shared_state.get('sides', []):
                if side.get('side_id') == side_id:
                    position = side.get('position', '')
                    break

            formatted_arguments.append({
                "player_id": player_id,
                "side_id": side_id,
                "position": position,
                "argument": argument
            })

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

        # Add context for judging
        extra_context = {
            "debate_topic": game_state.shared_state.get('debate_topic', ''),
            "sides": game_state.shared_state.get('sides', []),
            "current_round": game_state.shared_state.get('current_round', 1),
            "arguments": formatted_arguments,
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

        # Get current arguments from all debaters
        current_arguments = game_state.shared_state.get('current_arguments', {})

        # Format arguments for the prompt
        formatted_arguments = []
        for player_id, arg_data in current_arguments.items():
            side_id = arg_data.get('side_id', '')
            argument = arg_data.get('argument', '')

            # Find the position for this side_id
            position = ''
            for side in game_state.shared_state.get('sides', []):
                if side.get('side_id') == side_id:
                    position = side.get('position', '')
                    break

            formatted_arguments.append({
                "player_id": player_id,
                "side_id": side_id,
                "position": position,
                "argument": argument
            })

        # Add context for final judging
        extra_context = {
            "debate_topic": game_state.shared_state.get('debate_topic', ''),
            "sides": game_state.shared_state.get('sides', []),
            "arguments": formatted_arguments,
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

        # Assign points to debaters based on their current side
        for debater in debaters:
            side_id = debater['state'].get('side_id', '')
            votes = side_votes.get(side_id, 0)

            # Store the votes for this debate in player state
            if game_state.shared_state.get('sides_swapped', False):
                debater['state']['second_debate_votes'] = votes
            else:
                debater['state']['first_debate_votes'] = votes

        # Store the results of this debate
        if not game_state.shared_state.get('sides_swapped', False):
            # First debate - store results in hidden state
            first_debate_results = {
                "votes": side_votes,
                "judge_opinions": copy.deepcopy(judge_opinions)
            }

            complete_history = game_state.hidden_state.get('complete_history', {})
            complete_history['first_debate'] = first_debate_results
            game_state.hidden_state['complete_history'] = complete_history

            logger.info(f"Stored first debate results: {side_votes}")

            # Return True to indicate we need to swap sides
            return True
        else:
            # Second debate - store results in hidden state
            second_debate_results = {
                "votes": side_votes,
                "judge_opinions": copy.deepcopy(judge_opinions)
            }

            complete_history = game_state.hidden_state.get('complete_history', {})
            complete_history['second_debate'] = second_debate_results
            game_state.hidden_state['complete_history'] = complete_history

            logger.info(f"Stored second debate results: {side_votes}")

            # Return False to indicate we're done with both debates
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
            first_debate_votes = debater['state'].get('first_debate_votes', 0)
            second_debate_votes = debater['state'].get('second_debate_votes', 0)
            total_votes = first_debate_votes + second_debate_votes

            # Set final score
            debater['state']['score'] = total_votes

            logger.info(f"Debater {debater['id']} final score: {total_votes} (first: {first_debate_votes}, second: {second_debate_votes})")

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