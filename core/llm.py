# core/llm.py
import os
import logging
import json
import time

logger = logging.getLogger("LLMClient")

class PromptManager:
    """
    Manages prompt templates and formatting.

    Loads prompt templates from files and formats them with
    game state information.
    """

    def __init__(self, templates_dir="templates"):
        """
        Initialize the prompt manager.

        Args:
            templates_dir (str): Directory containing prompt templates
        """
        self.templates_dir = templates_dir
        self.templates = {}
        logger.info(f"Initialized PromptManager with templates directory: {templates_dir}")

    def load_template(self, template_name):
        """
        Load a template from file if not already cached.

        Args:
            template_name (str): Name or path of the template

        Returns:
            str: The template content

        Raises:
            ValueError: If the template is not found
        """
        if template_name in self.templates:
            return self.templates[template_name]

        # Handle template paths from config
        if template_name.startswith("templates/"):
            path = template_name
        else:
            path = os.path.join(self.templates_dir, f"{template_name}.txt")

        logger.debug(f"Loading template from: {path}")

        try:
            with open(path, 'r') as f:
                template = f.read()

            self.templates[template_name] = template
            return template
        except FileNotFoundError:
            error_msg = f"Template not found: {path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def format_prompt(self, template_name, game_state, player=None, **extra_context):
        """
        Format a prompt with game state context.

        Args:
            template_name (str): Name or path of the template
            game_state (GameState): The current game state
            player (dict, optional): Player context
            **extra_context: Additional context variables

        Returns:
            str: The formatted prompt
        """
        template = self.load_template(template_name)

        # Build context from game state
        context = {
            "game_name": game_state.config['game']['name'],
            "game_description": game_state.config['game'].get('description', ''),
            "current_phase": game_state.current_phase,
            "current_round": game_state.shared_state.get('current_round', 1),
        }

        # Add all shared state variables that are marked as visible
        for state_item in game_state.config['state'].get('shared_state', []):
            if state_item.get('visible', True):
                context[state_item['name']] = game_state.shared_state.get(state_item['name'])

        # Add player context if provided
        if player:
            context["player_id"] = player['id']
            for key, value in player.get('state', {}).items():
                context[f"player_{key}"] = value

            # Add role if present
            if 'role' in player:
                context["player_role"] = player['role']

            # Add other players' info
            other_players = []
            for p in game_state.get_active_players():
                if p['id'] != player['id']:
                    other_player = {"id": p['id']}
                    for state_key in p.get('state', {}):
                        # Only include visible state
                        is_visible = True
                        for state_item in game_state.config['state'].get('player_state', []):
                            if state_item['name'] == state_key:
                                is_visible = state_item.get('visible', True)
                                break

                        if is_visible:
                            other_player[state_key] = p['state'][state_key]

                    other_players.append(other_player)

            context["other_players"] = other_players

        # Add any extra context
        context.update(extra_context)

        # Format the template with the context
        # Make sure all values are strings to avoid formatting errors
        safe_context = {k: str(v) if not isinstance(v, (dict, list)) else json.dumps(v)
                        for k, v in context.items()}

        try:
            return template.format(**safe_context)
        except KeyError as e:
            logger.warning(f"Missing key in template formatting: {str(e)}")
            # Try to repair by adding the missing key with a placeholder
            safe_context[str(e).strip("'")] = "[PLACEHOLDER]"
            return template.format(**safe_context)


class ResponseParserRegistry:
    """
    Registry for response parsers.

    Provides a way to register and retrieve parsers for
    different types of LLM responses.
    """

    _parsers = {}

    @classmethod
    def register(cls, name):
        """
        Register a response parser.

        Args:
            name (str): The name to register the parser under

        Returns:
            function: Decorator function
        """
        def decorator(parser_class):
            cls._parsers[name] = parser_class
            return parser_class
        return decorator

    @classmethod
    def get_parser(cls, name):
        """
        Get a parser by name.

        Args:
            name (str): The parser name

        Returns:
            object: An instance of the parser

        Raises:
            ValueError: If no parser is registered with the given name
        """
        if name not in cls._parsers:
            # Fall back to default parser if specific one not found
            if 'default_parser' in cls._parsers:
                logger.warning(f"Parser '{name}' not found, using default_parser")
                return cls._parsers['default_parser']()
            raise ValueError(f"No parser registered for '{name}'")
        return cls._parsers[name]()


class LLMClient:
    """
    Client for interacting with language models.

    Handles sending prompts to LLMs and parsing responses.
    Designed to work with the aisuite library for seamless
    access to multiple LLM providers.
    """

    def __init__(self):
        """
        Initialize the LLM client.
        """
        # We'll set this up with a mock implementation for now
        # In a real implementation, this would use the aisuite library
        self.prompt_manager = PromptManager()
        self.parser_registry = ResponseParserRegistry()
        logger.info("Initialized LLMClient")

    def get_completion(self, prompt, model="openai:gpt-4o", system_prompt=None):
        """
        Get a completion from the language model.

        Args:
            prompt (str): The user prompt
            model (str): Model identifier in format "provider:model-name"
            system_prompt (str, optional): System prompt to set context

        Returns:
            str: The model's response
        """
        # Mock implementation for testing
        # In a real implementation, this would call the aisuite library
        logger.info(f"Sending prompt to model: {model}")
        logger.debug(f"System prompt: {system_prompt}")
        logger.debug(f"Prompt: {prompt[:100]}...")

        # Simulate API call delay
        time.sleep(0.5)

        # Return a mock response
        response = f"This is a mock response from {model}"

        logger.info(f"Received response from model: {model}")
        logger.debug(f"Response: {response[:100]}...")

        return response

    def get_action(self, game_state, player, phase_id=None):
        """
        Get an action from the LLM for a specific player in the current phase.

        Args:
            game_state (GameState): Current game state
            player (dict): Player to get action for
            phase_id (str, optional): Phase ID (defaults to current phase)

        Returns:
            any: Parsed action appropriate for the phase
        """
        if phase_id is None:
            phase_id = game_state.current_phase

        # Get phase configuration
        phase_config = None
        for phase in game_state.config['phases']:
            if phase['id'] == phase_id:
                phase_config = phase
                break

        if phase_config is None:
            error_msg = f"Phase not found: {phase_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Get prompt template
        prompt_template = game_state.config.get('llm_integration', {}).get('prompts', {}).get(phase_id)
        if not prompt_template:
            # Use default template based on phase type
            prompt_template = f"default_{phase_config['type']}"
            logger.warning(f"No prompt template specified for phase '{phase_id}', using default: {prompt_template}")

        # Format prompt
        prompt = self.prompt_manager.format_prompt(prompt_template, game_state, player)

        # Get system prompt if defined
        system_prompt = game_state.config.get('llm_integration', {}).get('system_prompts', {}).get(phase_id)

        # Get model specification
        # First check if there's a model specified for this player
        player_models = game_state.config.get('llm_integration', {}).get('player_models', {})
        if player['id'] in player_models:
            model = player_models[player['id']]
        else:
            # Otherwise use the default model
            model = game_state.config.get('llm_integration', {}).get('model', "openai:gpt-4o")

        # Get LLM response
        response = self.get_completion(prompt, model, system_prompt)

        # Parse response
        parser_name = game_state.config.get('llm_integration', {}).get('parsers', {}).get(phase_id)
        if not parser_name:
            # Use default parser based on action type
            action_type = phase_config.get('actions', [{}])[0].get('name', 'default')
            parser_name = f"{action_type}_parser"
            logger.warning(f"No parser specified for phase '{phase_id}', using default: {parser_name}")

        parser = self.parser_registry.get_parser(parser_name)
        return parser.parse(response, phase_config)