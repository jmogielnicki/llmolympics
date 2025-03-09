# core/production_llm_client.py
import logging
from core.prompt import PromptManager
from core.llm.parser import ResponseParserRegistry
from utils.chat_logger import get_chat_logger

logger = logging.getLogger("ProductionLLMClient")

class ProductionLLMClient():
    """Production implementation using aisuite"""

    def __init__(self):
        """Initialize the client"""
        try:
            import aisuite as ai
            self.client = ai.Client()
            self.prompt_manager = PromptManager()
            self.parser_registry = ResponseParserRegistry()
            self.chat_logger = get_chat_logger()
            logger.info("Initialized production LLM client with aisuite")
        except ImportError:
            logger.error("Failed to import aisuite")
            raise ImportError("aisuite is required for ProductionLLMClient")

    def get_completion(self, prompt, model, system_prompt=None, player_id=None):
        """Get a completion from the model"""
        logger.info(f"Sending prompt to {model}")

        # throw an error if the model is not provided
        if not model:
            raise ValueError("Model is required")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7
        )

        response_content = response.choices[0].message.content

        # Log the interaction if player_id is provided
        if player_id:
            metadata = {
                "model": model,
                "temperature": 0.7
            }
            self.chat_logger.log_interaction(
                player_id=player_id,
                messages=messages,
                response=response_content,
                metadata=metadata
            )

        return response_content

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
        model = player_models.get(player['id'])

        if not model:
            # throw an error if the model is not provided
            raise ValueError(f"Model not found for player {player['id']}")

        # Get response
        response = self.get_completion(
            prompt, 
            model, 
            system_prompt, 
            player_id=player.get('id', 'unknown')
        )

        # Parse response
        parser_name = game_state.config.get('llm_integration', {}).get('parsers', {}).get(phase_id)
        if not parser_name:
            action_type = phase_config.get('actions', [{}])[0].get('name', 'default')
            parser_name = f"{action_type}_parser"

        parser = self.parser_registry.get_parser(parser_name)
        return parser.parse(response, phase_config)