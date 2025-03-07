import os
import json
import random
from llm.client import LLMClient
from llm.prompts import PromptTemplates
from llm.parser import extract_vote
from game.state import PlayerStatus

class PlayerManager:
    def __init__(self, player_models_config="config/llm_models.json"):
        """Initialize the PlayerManager.

        Args:
            player_models_config: Path to the JSON file mapping player IDs to models.
        """
        self.players = {}
        # Create a single shared LLM client
        self.llm_client = LLMClient()
        self.load_player_models(player_models_config)

    def load_player_models(self, config_path):
        """Load player models from configuration."""
        try:
            with open(config_path, 'r') as f:
                player_models = json.load(f)

            # Store model info for each player
            for player_id, model_info in player_models.items():
                # Handle both string format and dict format for backward compatibility
                if isinstance(model_info, str):
                    # Legacy format - just model name, try to infer provider
                    model = model_info
                    provider = LLMClient.get_provider_for_model(model)
                else:
                    # New format with explicit provider
                    provider = model_info.get("provider")
                    model = model_info.get("model")

                    if not provider:
                        provider = LLMClient.get_provider_for_model(model)

                self.players[player_id] = {
                    "provider": provider,
                    "model": model
                }

            print(f"Loaded {len(self.players)} player models from {config_path}")

            # Print the models for confirmation
            for player_id, info in self.players.items():
                print(f"  {player_id}: {info['provider']}/{info['model']}")

        except FileNotFoundError:
            print(f"Warning: Player models config not found at {config_path}")
            print("No LLM players were configured.")

    def get_active_players(self, game_state):
        """Get lists of active and eliminated players from game state."""
        active_players = []
        eliminated_players = []

        for player_id, player in game_state.players.items():
            if player.status == PlayerStatus.ACTIVE:
                active_players.append(player_id)
            else:
                eliminated_players.append(player_id)

        return active_players, eliminated_players

    def format_previous_messages(self, game_state, max_messages=10):
        """Format previous messages for context."""
        # Get messages from the current round
        current_round = game_state.round
        round_messages = [
            msg for msg in game_state.messages
            if msg.round == current_round
        ]

        # Take the last max_messages
        recent_messages = round_messages[-max_messages:] if len(round_messages) > max_messages else round_messages

        # Format messages
        formatted_messages = ""
        for msg in recent_messages:
            formatted_messages += f"[{msg.player_id}]: {msg.content}\n"

        return formatted_messages

    def generate_player_message(self, player_id, game_state):
        """Generate a message from an LLM player during discussion phase."""
        if player_id not in self.players:
            raise ValueError(f"Unknown player: {player_id}")

        # Get active and eliminated players
        active_players, eliminated_players = self.get_active_players(game_state)

        # Format previous messages
        previous_messages = self.format_previous_messages(game_state)

        # Generate prompt
        prompt = PromptTemplates.get_discussion_prompt(
            player_id=player_id,
            active_players=active_players,
            eliminated_players=eliminated_players,
            round_num=game_state.round,
            previous_messages=previous_messages
        )

        # Get model info for this player
        provider = self.players[player_id]["provider"]
        model = self.players[player_id]["model"]

        # Generate response
        print(f"Generating message for {player_id} using {provider}/{model}...")
        response = self.llm_client.generate_response(
            prompt=prompt,
            provider=provider,
            model=model
        )

        return response

    def get_player_vote(self, player_id, game_state):
        """Get a vote from an LLM player during voting phase.

        Returns:
            (vote, raw_response) tuple, or (None, None) if no valid vote was found.
        """
        if player_id not in self.players:
            raise ValueError(f"Unknown player: {player_id}")

        # Get active and eliminated players
        active_players, eliminated_players = self.get_active_players(game_state)

        # Format previous messages
        previous_messages = self.format_previous_messages(game_state)

        # Generate prompt
        prompt = PromptTemplates.get_voting_prompt(
            player_id=player_id,
            active_players=active_players,
            eliminated_players=eliminated_players,
            round_num=game_state.round,
            previous_messages=previous_messages
        )

        # Get model info for this player
        provider = self.players[player_id]["provider"]
        model = self.players[player_id]["model"]

        # Generate response
        print(f"Getting vote from {player_id} using {provider}/{model}...")
        response = self.llm_client.generate_response(
            prompt=prompt,
            provider=provider,
            model=model
        )

        # Extract vote
        vote = extract_vote(response)

        # Validate vote
        if not vote:
            print(f"Warning: {player_id} did not provide a clear vote")
            return None, response

        if vote not in active_players:
            print(f"Warning: {player_id} voted for non-existent or eliminated player: {vote}")
            return None, response

        if vote == player_id:
            print(f"Warning: {player_id} tried to vote for themselves: {vote}")
            return None, response

        return vote, response

    def handle_invalid_vote(self, player_id, active_players):
        """Handle the case where a player gave an invalid vote."""
        # Choose a random player to vote for
        # TODO - consider giving a null vote instead
        valid_targets = [p for p in active_players if p != player_id]
        if valid_targets:
            random_vote = random.choice(valid_targets)
            print(f"[{player_id}] gave invalid vote, randomly voting for {random_vote}")
            return random_vote
        return None