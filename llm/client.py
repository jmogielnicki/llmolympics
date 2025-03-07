import os
import json
from aisuite import AIClient

class LLMClient:
    """A client for interacting with multiple LLM providers using AISuite."""

    def __init__(self):
        """Initialize the LLM client with AISuite."""
        self.client = AIClient()

        # Supported providers mapping for reference
        self.supported_providers = {
            "openai": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "claude-2.1"],
            "google": ["gemini-pro"],
            "mistral": ["mistral-tiny", "mistral-small", "mistral-medium", "mistral-large"],
            "cohere": ["command", "command-light", "command-r", "command-r-plus"],
            "ollama": ["llama3", "llama2", "mistral", "mixtral", "phi3"]
            # Add more providers as they become available in AISuite
        }

    def generate_response(self, prompt, provider, model, max_tokens=1000):
        """Generate a response from the specified LLM provider and model.

        Args:
            prompt (str): The prompt to send to the model
            provider (str): The provider name (e.g., "openai", "anthropic")
            model (str): The model name (e.g., "gpt-4o", "claude-3-haiku")
            max_tokens (int): Maximum tokens in the response

        Returns:
            str: The generated response
        """
        try:
            # Provider-specific parameters
            params = {
                "max_tokens": max_tokens,
            }

            # Add provider-specific API keys from environment
            self._set_api_key(provider)

            # Generate the response
            response = self.client.generate(
                prompt=prompt,
                provider=provider,
                model=model,
                **params
            )

            return response

        except Exception as e:
            print(f"Error generating response from {provider}/{model}: {e}")
            # Return a simple error message as fallback
            return f"[Error generating response: {str(e)}]"

    def _set_api_key(self, provider):
        """Set the appropriate API key for the provider from environment variables."""
        env_var_name = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(env_var_name)

        if not api_key:
            raise ValueError(f"No API key found for {provider}. Set {env_var_name} environment variable.")

        # AISuite will use these environment variables automatically
        # This just validates they exist

    @staticmethod
    def get_provider_for_model(model_name):
        """Determine the likely provider for a given model name.

        This is a fallback in case the provider isn't explicitly specified.
        """
        model_prefixes = {
            "gpt": "openai",
            "claude": "anthropic",
            "gemini": "google",
            "mistral": "mistral",
            "command": "cohere",
            "llama": "ollama",
            "mixtral": "ollama",
            "phi": "ollama"
        }

        for prefix, provider in model_prefixes.items():
            if model_name.lower().startswith(prefix):
                return provider

        raise ValueError(f"Could not determine provider for model: {model_name}")