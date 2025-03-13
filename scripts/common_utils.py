def extract_model_name(full_model_name):
    """
    Extract a readable model name from provider:model format,
    mapping only the model portion to a friendly name.

    Args:
        full_model_name (str): The model identifier in format "provider:model"

    Returns:
        str: A human-readable model name in format "Provider FriendlyModelName"
    """
    # Only process if in provider:model format
    if ":" not in full_model_name:
        return full_model_name

    provider, model_id = full_model_name.split(":", 1)

    # Provider name mapping
    provider_map = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "xai": "xAI",
        "google": "Google",
        "deepseek": "DeepSeek",
        "mistral": "Mistral"
    }
    provider_clean = provider_map.get(provider.lower(), provider.capitalize())

    # Model name mapping (only for the model portion)
    model_name_map = {
        # DeepSeek models
        "deepseek-chat": "Chat",
        "deepseek-reasoner": "Reasoner",

        # OpenAI models
        "gpt-4o": "GPT-4o",
        "o3-mini": "O3 Mini",
        "gpt-4.5-preview": "GPT-4.5",
        "o1": "O1",

        # Anthropic models
        "claude-3-5-sonnet-20240620": "Claude 3.5",
        "claude-3-7-sonnet-20250219": "Claude 3.7",

        # xAI models
        "grok-2-1212": "Grok-2",

        # Google models
        "gemini-2.0-flash": "Gemini 2.0",
        "gemini-2.0-flash-exp": "Gemini 2.0 (Experimental)",
        "gemini-2.0-flash-thinking-exp-01-21": "Gemini 2.0 Thinking",

        # Mistral models
        "mistral-large-latest": "Mistral Large"
    }

    # Get the friendly model name, or use the original if not in our map
    friendly_model = model_name_map.get(model_id, model_id)

    return f"{provider_clean} {friendly_model}"

def get_session_directory(benchmark_dir, session_id):
    """
    Extract the directory name from a session ID.
    From 'prisoner's_dilemma_20250311_144154' extracts '20250311_144154'

    Args:
        session_id (str): Full session ID with game name and timestamp

    Returns:
        str: Directory name (timestamp portion only)
    """
    parts = session_id.split('_')
    # Check if we have enough parts for a timestamp (needs at least 2 parts)
    if len(parts) >= 2:
        # Get the last two parts which make up the timestamp
        timestamp = '_'.join(parts[-2:])
        return '/'.join([benchmark_dir, timestamp])
    # Fallback if format doesn't match expected
    return '/'.join([benchmark_dir, session_id])