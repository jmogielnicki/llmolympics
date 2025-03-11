# test_utils.py
import re
import logging

logger = logging.getLogger("MockAIClient")

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChatCompletions:
    def __init__(self):
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

    def create(self, model, messages, temperature=0.7):
        prompt = messages[-1]["content"]

        # Extract player ID and round number from prompt
        player_id = self._extract_player_id(prompt)
        round_num = self._extract_round_number(prompt)

        # Determine game type
        game_type = self._determine_game_type(prompt)
        logger.debug(f"Determined game type: {game_type}, player: {player_id}, round: {round_num}")

        # Get appropriate response based on game type, player, and round
        if game_type == "prisoner's dilemma" and player_id and round_num:
            response = self.pd_responses.get(player_id, {}).get(round_num, self.default_response)
            logger.info(f"Mock response for {player_id}, round {round_num} is {response}")
        elif game_type == "diplomacy":
            phase = "voting" if "voting" in prompt.lower() else "discussion"
            response = self.diplomacy_responses.get(phase, {}).get(player_id, self.default_response)
        else:
            logger.error(f"No deterministic response found for game type: {game_type}")
            response = self.default_response

        return MockResponse(response)

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


class MockAIClient:
    def __init__(self):
        self.chat = MockChatCompletions()