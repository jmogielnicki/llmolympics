# utils/mock_llm.py
import logging
import random
import re
import time

logger = logging.getLogger("MockLLM")

# Import the original LLMClient as a base class
try:
    from core.llm import LLMClient as BaseLLMClient
except ImportError:
    # Fallback for testing if the real LLMClient isn't available
    BaseLLMClient = object
    logger.warning("Could not import original LLMClient, using object as base class")

class MockLLMClient(BaseLLMClient):
    """
    A mock implementation of the LLM client for testing purposes.

    Returns predefined responses based on prompt content and patterns,
    simulating real LLM behavior without API calls.
    """

    def __init__(self, response_delay=0.2, randomness=0.3):
        """
        Initialize the mock LLM client.

        Args:
            response_delay (float): Simulated delay in seconds
            randomness (float): Level of randomness in responses (0-1)
        """
        # Only call super().__init__() if BaseLLMClient is not object
        if BaseLLMClient is not object:
            super().__init__()

        self.response_delay = response_delay
        self.randomness = randomness

        # Initialize prompt manager if needed
        if not hasattr(self, 'prompt_manager'):
            # Try to import from core.llm
            try:
                from core.llm import PromptManager
                self.prompt_manager = PromptManager()
            except ImportError:
                self.prompt_manager = None
                logger.warning("Could not import PromptManager")

        # Initialize parser registry if needed
        if not hasattr(self, 'parser_registry'):
            # Try to import from core.llm
            try:
                from core.llm import ResponseParserRegistry
                self.parser_registry = ResponseParserRegistry()
            except ImportError:
                self.parser_registry = None
                logger.warning("Could not import ResponseParserRegistry")

        self.response_patterns = {
            # Prisoner's Dilemma responses
            "prisoner's dilemma": [
                {
                    "pattern": r"round: 1",
                    "responses": [
                        "I choose to COOPERATE.",
                        "After analyzing the situation, I will COOPERATE for this round.",
                        "For the first round, cooperation seems optimal. I COOPERATE."
                    ]
                },
                {
                    "pattern": r"round: [2-3]",
                    "responses": [
                        "Based on previous interactions, I will COOPERATE again.",
                        "I think cooperation still makes sense. I COOPERATE.",
                        "I'll stick with cooperation. I COOPERATE."
                    ]
                },
                {
                    "pattern": r"round: [4-5]",
                    "responses": [
                        "For this later round, I will DEFECT to maximize my score.",
                        "I choose to DEFECT now that we're near the end.",
                        "DEFECT is my choice for this critical round."
                    ]
                },
                {
                    "pattern": r".*",  # Default fallback
                    "responses": [
                        "After consideration, I choose to COOPERATE.",
                        "I will DEFECT for this round.",
                        "My decision is to COOPERATE for now."
                    ]
                }
            ],

            # Diplomacy responses
            "diplomacy": [
                {
                    "pattern": r"discussion",
                    "responses": [
                        "I suggest we form an alliance against player_3, who seems to be in the strongest position.",
                        "I propose working together with player_2 and player_4 to eliminate player_1, who has been making aggressive moves.",
                        "I have been loyal so far and suggest we continue our alliance. Let's target player_5 this round."
                    ]
                },
                {
                    "pattern": r"voting",
                    "responses": [
                        "I vote to eliminate player_3",
                        "My vote is for player_1",
                        "player_5"
                    ]
                }
            ],

            # Default responses for any game
            "default": [
                {
                    "pattern": r".*",
                    "responses": [
                        "I choose option A",
                        "My decision is option B",
                        "After careful consideration, I select option C"
                    ]
                }
            ]
        }

        logger.info("Initialized MockLLMClient")

    def get_completion(self, prompt, model="mock:default", system_prompt=None):
        """
        Get a mock completion that simulates real LLM behavior.

        Args:
            prompt (str): The user prompt
            model (str): Ignored in mock implementation
            system_prompt (str, optional): Ignored in mock implementation

        Returns:
            str: A simulated model response
        """
        logger.info(f"Mock LLM received prompt ({len(prompt)} chars)")

        # Simulate processing delay
        time.sleep(self.response_delay)

        # Determine which game the prompt is for
        game_type = self._determine_game_type(prompt)
        logger.debug(f"Determined game type: {game_type}")

        # Get appropriate response patterns
        patterns = self.response_patterns.get(game_type, self.response_patterns["default"])

        # Find matching pattern
        response_options = []
        for pattern_obj in patterns:
            if re.search(pattern_obj["pattern"], prompt, re.IGNORECASE):
                response_options = pattern_obj["responses"]
                break

        if not response_options:
            # Fallback to default if no match
            response_options = self.response_patterns["default"][0]["responses"]

        # Select response (with some randomness)
        if random.random() < self.randomness:
            # Completely random selection
            response = random.choice(response_options)
        else:
            # Weighted towards first options (more predictable)
            weights = [0.5, 0.3, 0.2][:len(response_options)]

            # Normalize weights if needed
            if len(weights) < len(response_options):
                remaining = len(response_options) - len(weights)
                weights.extend([0.1 / remaining] * remaining)

            # Ensure weights sum to 1
            total = sum(weights)
            weights = [w / total for w in weights]

            # Make selection
            response = random.choices(response_options, weights=weights, k=1)[0]

        logger.info(f"Mock LLM returning response: {response[:50]}...")
        return response

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