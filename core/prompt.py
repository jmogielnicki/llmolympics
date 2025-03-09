# core/prompt.py
import os
import json
import logging

logger = logging.getLogger("PromptManager")

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

    def _format_decision_history(self, history, player_id):
        """
        Format the decision history for inclusion in prompts.
        
        Args:
            history (list): List of history entries
            player_id (str): ID of the current player
            
        Returns:
            str: Formatted history string
        """
        if not history:
            return "No previous rounds"
            
        # Find all other players
        other_players = set()
        for entry in history:
            for pid in entry.get('decisions', {}).keys():
                if pid != player_id:
                    other_players.add(pid)
                    
        other_player_id = next(iter(other_players)) if other_players else "opponent"
        
        # Format history entries
        lines = []
        for entry in history:
            round_num = entry.get('round', 0)
            decisions = entry.get('decisions', {})
            
            your_decision = decisions.get(player_id, "unknown").upper()
            their_decision = decisions.get(other_player_id, "unknown").upper()
            
            lines.append(f"Round {round_num}: You chose {your_decision}, {other_player_id} chose {their_decision}")
            
        return "\n".join(lines)
    
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

        # Format decision history if present (for Prisoner's Dilemma)
        if 'decision_history' in game_state.history_state and player:
            decision_history = self._format_decision_history(game_state.history_state['decision_history'], player['id'])
            context["decision_history"] = decision_history
            logger.info(f"Added decision history for {player['id']}: {decision_history}")
        else:
            context["decision_history"] = "No previous rounds"
            logger.info("No decision history available")

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