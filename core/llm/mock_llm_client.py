# core/llm/mock_llm_client.py
import logging
import re
import time
from core.prompt import PromptManager
from core.llm.parser import ResponseParserRegistry

logger = logging.getLogger("MockLLM")


class MockLLMClient():
    """
    A completely deterministic mock implementation of the LLM client for testing purposes.

    Returns predefined responses based on prompt content, player ID, and round number
    with no randomness for reliable test results.
    """

    def __init__(self, chat_logger, response_delay=0.1):
        """
        Initialize the mock LLM client.

        Args:
            chat_logger: ChatLogger instance for logging interactions
            response_delay (float): Simulated delay in seconds
        """
        if chat_logger is None:
            raise ValueError("ChatLogger is required for MockLLMClient")

        self.response_delay = response_delay
        self.prompt_manager = PromptManager()
        self.parser_registry = ResponseParserRegistry()
        self.chat_logger = chat_logger

        # Completely deterministic responses for Prisoner's Dilemma
        # Player 1: COOPERATE in rounds 1-3, DEFECT in rounds 4-5
        # Player 2: COOPERATE in rounds 1-2, DEFECT in rounds 3-5
        self.pd_responses = {
            "player_1": {
                1: "I choose to [[COOPERATE]].",
                2: "I choose to [[COOPERATE]].",
                3: "I choose to [[COOPERATE]].",
                4: "I choose to [[DEFECT]].",
                5: "I choose to [[DEFECT]]."
            },
            "player_2": {
                1: "I choose to [[COOPERATE]].",
                2: "I choose to [[COOPERATE]].",
                3: "I choose to [[DEFECT]].",
                4: "I choose to [[DEFECT]].",
                5: "I choose to [[DEFECT]]."
            }
        }

        # Deterministic responses for Diplomacy (if needed)
        self.diplomacy_responses = {
            "discussion": {
                "player_1": "I suggest an alliance against player_3, who seems to be the strongest.",
                "player_2": "I agree with player_1. Let's target player_3 this round.",
                "player_3": "I think player_1 is the biggest threat. We should eliminate them.",
                "player_4": "I propose we work together against player_2.",
                "player_5": "Player_4 is in the lead. We should vote against them.",
                "player_6": "I suggest we vote out player_5 as they're not contributing.",
            },
            "voting": {
                "player_1": "I vote to eliminate player_3",
                "player_2": "I vote to eliminate player_3",
                "player_3": "I vote to eliminate player_1",
                "player_4": "I vote to eliminate player_2",
                "player_5": "I vote to eliminate player_4",
                "player_6": "I vote to eliminate player_5",
            }
        }

        # Default responses for any other game or situation
        self.default_response = "I choose option A"

        logger.info("Initialized deterministic MockLLMClient")

    def get_completion(self, prompt, model="mock:default", system_prompt=None, player_id=None, phase_id=None, round_num=None):
        """
        Get a deterministic mock completion.

        Args:
            prompt (str): The user prompt
            model (str): Ignored in mock implementation
            system_prompt (str, optional): Ignored in mock implementation
            player_id (str, optional): Player ID for logging
            phase_id (str, optional): Current phase ID
            round_num (int, optional): Current round number

        Returns:
            str: A deterministic model response
        """
        logger.info(f"Mock LLM received prompt ({len(prompt)} chars)")

        # Simulate minimal processing delay
        time.sleep(self.response_delay)
        logger.info(f"Mock LLM response delay: {self.response_delay} seconds")

        # Extract player ID and round number from prompt if not provided
        extracted_player_id = self._extract_player_id(prompt)
        extracted_round_num = self._extract_round_number(prompt)

        # Use provided values if available, otherwise use extracted ones
        effective_player_id = player_id or extracted_player_id
        effective_round_num = round_num or extracted_round_num

        # Determine game type
        game_type = self._determine_game_type(prompt)
        logger.debug(f"Determined game type: {game_type}, player: {effective_player_id}, round: {effective_round_num}")

        # Get appropriate response based on game type, player, and round
        if game_type == "prisoner's dilemma" and effective_player_id and effective_round_num:
            response = self.pd_responses.get(effective_player_id, {}).get(effective_round_num, self.default_response)
            logger.info(f"Response for {effective_player_id}, round {effective_round_num} is {response}")
        elif game_type == "diplomacy":
            phase = "voting" if "voting" in prompt.lower() else "discussion"
            response = self.diplomacy_responses.get(phase, {}).get(effective_player_id, self.default_response)
        else:
            logger.error(f"No deterministic response found for game type: {game_type}")
            response = self.default_response

        # Log the interaction
        if effective_player_id:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            metadata = {
                "model": "mock:default",
                "game_type": game_type,
                "round": effective_round_num
            }

            self.chat_logger.log_interaction(
                player_id=effective_player_id,
                messages=messages,
                response=response,
                metadata=metadata,
                phase_id=phase_id,
                round_num=effective_round_num
            )

        logger.info(f"Mock LLM returning deterministic response for {effective_player_id}, round {effective_round_num}")
        return response

    def get_action(self, game_state, player, phase_id=None):
        """Get an action from a player in the current game state"""
        if phase_id is None:
            phase_id = game_state.current_phase

        # Get phase configuration
        phase_config = None
        for phase in game_state.config['phases']:
            if phase['id'] == phase_id:
                phase_config = phase
                break

        if phase_config is None:
            raise ValueError(f"Phase not found: {phase_id}")

        # Get prompt template
        prompt_template = game_state.config.get('llm_integration', {}).get('prompts', {}).get(phase_id)
        if not prompt_template:
            prompt_template = f"default_{phase_config['type']}"

        # Format prompt
        prompt = self.prompt_manager.format_prompt(prompt_template, game_state, player)

        # Get system prompt
        system_prompt = game_state.config.get('llm_integration', {}).get('system_prompts', {}).get(phase_id)

        # Get model
        player_models = game_state.config.get('llm_integration', {}).get('player_models', {})
        model = player_models.get(player['id'], game_state.config.get('llm_integration', {}).get('model', "openai:gpt-4o"))

        # Current round
        round_num = game_state.shared_state.get('current_round', 0)

        # Get response
        response = self.get_completion(
            prompt,
            model,
            system_prompt,
            player_id=player.get('id', 'unknown'),
            phase_id=phase_id,
            round_num=round_num
        )

        # Parse response
        parser_name = game_state.config.get('llm_integration', {}).get('parsers', {}).get(phase_id)
        if not parser_name:
            action_type = phase_config.get('actions', [{}])[0].get('name', 'default')
            parser_name = f"{action_type}_parser"

        parser = self.parser_registry.get_parser(parser_name)
        return parser.parse(response, phase_config)

    def _extract_player_id(self, prompt):
        """Extract player ID from prompt."""
        player_match = re.search(r'player[_\s]?(\d+)|player_id[:\s]+([a-zA-Z0-9_]+)', prompt, re.IGNORECASE)
        if player_match:
            # Get the first non-None group
            groups = player_match.groups()
            for group in groups:
                if group:
                    return f"player_{group}"
        return None

    def _extract_round_number(self, prompt):
        """Extract round number from prompt."""
        round_match = re.search(r'round[:\s]+(\d+)', prompt, re.IGNORECASE)
        if round_match:
            try:
                return int(round_match.group(1))
            except (ValueError, IndexError):
                pass
        return None

    def _determine_game_type(self, prompt):
        """
        Determine the game type from the prompt content.

        Args:
            prompt (str): The prompt to analyze

        Returns:
            str: The determined game type
        """
        prompt_lower = prompt.lower()

        if "prisoner's dilemma" in prompt_lower or "cooperate" in prompt_lower or "defect" in prompt_lower:
            return "prisoner's dilemma"
        elif "diplomacy" in prompt_lower or "alliance" in prompt_lower or "voting" in prompt_lower:
            return "diplomacy"
        elif "ghost" in prompt_lower or "word fragment" in prompt_lower or "add a letter" in prompt_lower:
            return "ghost"
        elif "ultimatum" in prompt_lower or "split" in prompt_lower or "proposer" in prompt_lower:
            return "ultimatum"

        return "default"