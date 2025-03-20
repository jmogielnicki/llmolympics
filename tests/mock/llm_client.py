import yaml
import re
import logging
import json

logger = logging.getLogger("MockLLMClient")

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockLLMClient:
    """
    Mock LLM client that returns preconfigured responses based on context
    matching rules and prompt content.

    This allows deterministic testing of LLM interactions.
    """

    def __init__(self, response_files=None):
        """
        Initialize the mock client with response configuration files.

        Args:
            response_files (list): List of paths to YAML files containing response configurations
        """
        self.responses = {}
        self.fallbacks = {}
        self.test_config_path = None  # Will be set when used through the fixture

        if response_files:
            self.load_responses(response_files)

        logger.info(f"Initialized MockLLMClient with {len(self.responses)} model configurations")

    def load_responses(self, response_files):
        """
        Load response configurations from YAML files.

        Args:
            response_files (list): List of paths to YAML files
        """
        for file_path in response_files:
            try:
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)

                model = config.get('model')
                if not model:
                    logger.warning(f"Response file {file_path} missing 'model' field")
                    continue

                responses = config.get('responses', [])

                # Store responses by model
                self.responses[model] = responses

                # Find default fallback responses
                for resp in responses:
                    if resp.get('default', False):
                        self.fallbacks[model] = resp.get('content', "Default response")
                        break

                logger.info(f"Loaded {len(responses)} responses for model {model} from {file_path}")

            except Exception as e:
                logger.error(f"Failed to load response file {file_path}: {str(e)}")

    def find_matching_response(self, model, prompt, context=None):
        """
        Find the best matching response for the given prompt and context.

        Args:
            model (str): The model identifier
            prompt (str): The prompt text
            context (dict): Additional context like phase, round, player_id

        Returns:
            str: The matching response content
        """
        if model not in self.responses:
            logger.warning(f"No responses configured for model {model}, using generic fallback")
            return "No response configured for this model. Please add a response definition."

        model_responses = self.responses[model]
        if not model_responses:
            logger.warning(f"Empty response list for model {model}")
            return "Empty response list for this model."

        # Default context
        if context is None:
            context = {}

        # Extract key matching criteria
        phase = context.get('phase', '')
        round_num = context.get('round_num')
        player_id = context.get('player_id', '')
        role = context.get('role', '')

        # Try to extract these from prompt if not in context
        if not phase:
            phase_match = re.search(r'phase[:\s]+([a-zA-Z_]+)', prompt, re.IGNORECASE)
            if phase_match:
                phase = phase_match.group(1).lower()

        if not round_num:
            round_match = re.search(r'round[:\s]+(\d+)', prompt, re.IGNORECASE)
            if round_match:
                try:
                    round_num = int(round_match.group(1))
                except (ValueError, IndexError):
                    pass

        if not player_id:
            player_match = re.search(r'player[_\s]?(\d+)|player_id[:\s]+([a-zA-Z0-9_]+)', prompt, re.IGNORECASE)
            if player_match:
                # Get the first non-None group
                groups = player_match.groups()
                for group in groups:
                    if group:
                        player_id = f"player_{group}"
                        break

        if not role:
            for role_type in ['werewolf', 'villager', 'seer', 'prompter', 'judge', 'debater', 'detective']:
                if role_type in prompt.lower():
                    role = role_type
                    break

        logger.debug(f"Matching response for model={model}, phase={phase}, round={round_num}, "
                    f"player={player_id}, role={role}")

        # Scoring function for matching
        def score_response(response):
            score = 0

            # Phase match - most important
            if 'phase' in response and response['phase'] == phase:
                score += 100

            # Round match
            if 'round' in response and response['round'] == round_num:
                score += 50

            # Player match
            if 'player_id' in response and response['player_id'] == player_id:
                score += 30

            # Role match
            if 'role' in response and response['role'] == role:
                score += 40

            # Content match - look for specific keywords
            if 'match_keywords' in response:
                keywords = response['match_keywords']
                if isinstance(keywords, list):
                    for keyword in keywords:
                        if keyword.lower() in prompt.lower():
                            score += 10
                elif isinstance(keywords, str) and keywords.lower() in prompt.lower():
                    score += 10

            return score

        # Score all responses and find the best match
        scored_responses = [(resp, score_response(resp)) for resp in model_responses
                            if 'default' not in resp or not resp['default']]

        # Sort by score, highest first
        scored_responses.sort(key=lambda x: x[1], reverse=True)

        # If we have a good match, use it
        if scored_responses and scored_responses[0][1] > 0:
            best_match = scored_responses[0][0]
            logger.info(f"Found matching response with score {scored_responses[0][1]}: "
                       f"{best_match.get('content', '')[:50]}...")
            return best_match.get('content', '')

        # Fallback to default response for this model
        if model in self.fallbacks:
            logger.info(f"Using fallback response for {model}")
            return self.fallbacks[model]

        # Ultimate fallback
        logger.warning(f"No matching response found for {model} with phase={phase}, round={round_num}")
        return "No matching response found. Please add a response definition."

    def get_completion(self, model, messages, **kwargs):
        """
        Mock the OpenAI create function for chat completions.

        Args:
            model (str): The model identifier
            messages (list): The conversation history
            **kwargs: Additional arguments

        Returns:
            MockResponse: Response object with content field
        """
        # Extract the prompt from the last message
        if not messages or 'content' not in messages[-1]:
            return MockResponse("No valid prompt provided")

        prompt = messages[-1]['content']

        # Extract context from messages
        context = self._extract_context_from_messages(messages)

        # Find matching response
        response_content = self.find_matching_response(model, prompt, context)

        # Create mock response
        return MockResponse(response_content)

    def create(self, model, messages, **kwargs):
        """Alias for get_completion for OpenAI client compatibility"""
        return self.get_completion(model, messages, **kwargs)

    def get_action(self, game_state, player, phase_id, extra_context=None):
        """
        Mock the LLM client's get_action method to bridge with the game engine.

        Args:
            game_state: The current game state
            player: The player object
            phase_id: The current phase ID
            extra_context: Any additional context

        Returns:
            str: Action string as expected by the game engine
        """
        # Get model for this player
        model = self._get_player_model(game_state, player)

        # Build context
        context = {
            'phase': phase_id,
            'round_num': game_state.shared_state.get('current_round', 1),
            'player_id': player['id'],
            'role': player.get('role', '')
        }

        # Add roles from player object
        if 'roles' in player:
            context['roles'] = player['roles']

        # Add any extra context
        if extra_context:
            context.update(extra_context)

        # Generate a prompt (similar to how the real LLM client would)
        prompt = self._generate_mock_prompt(game_state, player, phase_id, context)

        # Get response
        response = self.find_matching_response(model, prompt, context)

        logger.info(f"Mock LLM response for {player['id']} ({model}): {response[:50]}...")

        # Parse the action from the response
        action = self._parse_action(response, phase_id)

        return action

    def _get_player_model(self, game_state, player):
        """Extract the model identifier for a player from the game config"""
        player_id = player['id']

        # Look in llm_integration section of config
        if 'llm_integration' in game_state.config:
            if 'player_models' in game_state.config['llm_integration']:
                return game_state.config['llm_integration']['player_models'].get(player_id, "default-model")

        return "default-model"

    def _generate_mock_prompt(self, game_state, player, phase_id, context):
        """Generate a fake prompt that contains enough info for matching"""
        prompt_parts = [
            f"You are {player['id']} in phase {phase_id}.",
            f"Current round: {context.get('round_num', 1)}.",
        ]

        # Add role info
        if 'role' in context and context['role']:
            prompt_parts.append(f"Your role is {context['role']}.")
        elif 'roles' in context and context['roles']:
            roles_str = ', '.join(context['roles'])
            prompt_parts.append(f"Your roles are: {roles_str}.")

        # Add game specific context
        game_name = game_state.config['game']['name']
        prompt_parts.append(f"This is a {game_name} game.")

        # Add phase specific instructions
        if phase_id == 'decision':
            prompt_parts.append("Please choose to [[COOPERATE]] or [[DEFECT]].")
        elif phase_id == 'voting':
            prompt_parts.append("Please vote to eliminate one player using [[player_X]] format.")
        elif phase_id == 'night_action':
            prompt_parts.append("Choose a player to target tonight.")

        return "\n".join(prompt_parts)

    def _parse_action(self, response, phase_id):
        """Extract structured action from the response string"""
        # For decisions in double brackets like [[COOPERATE]]
        bracket_match = re.search(r'\[\[(.*?)\]\]', response)
        if bracket_match:
            return bracket_match.group(1).strip().lower()

        # For Prisoner's Dilemma
        if phase_id == 'decision':
            if 'cooperate' in response.lower():
                return 'cooperate'
            elif 'defect' in response.lower():
                return 'defect'

        # For voting
        if phase_id in ['voting', 'vote']:
            # Try to find player_X pattern
            player_match = re.search(r'player_\d+', response.lower())
            if player_match:
                return player_match.group(0)

        # For letter additions in Ghost
        if phase_id == 'add_letter':
            # Find the first letter
            letter_match = re.search(r'[a-zA-Z]', response)
            if letter_match:
                return letter_match.group(0).lower()

        # Default - return the full response
        # The game engine will need to handle parsing this appropriately
        return response

    def _extract_context_from_messages(self, messages):
        """Extract context information from message history"""
        context = {}

        # Look for relevant info in system message
        system_msg = next((msg for msg in messages if msg.get('role') == 'system'), None)
        if system_msg and 'content' in system_msg:
            system_content = system_msg['content']

            # Extract phase
            phase_match = re.search(r'phase[:\s]+([a-zA-Z_]+)', system_content, re.IGNORECASE)
            if phase_match:
                context['phase'] = phase_match.group(1).lower()

            # Extract round
            round_match = re.search(r'round[:\s]+(\d+)', system_content, re.IGNORECASE)
            if round_match:
                try:
                    context['round_num'] = int(round_match.group(1))
                except (ValueError, IndexError):
                    pass

            # Extract roles
            for role_type in ['werewolf', 'villager', 'seer', 'prompter', 'judge', 'debater']:
                if role_type in system_content.lower():
                    context['role'] = role_type
                    break

        return context