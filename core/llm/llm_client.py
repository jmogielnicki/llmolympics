# core/llm/llm_client.py
import os
import logging

logger = logging.getLogger("LLMClient")

# Decide which implementation to use based on environment variable
use_mock = os.environ.get("PARLOURBENCH_USE_MOCK", "false").lower() in ["true", "1", "yes"]

if use_mock:
    logger.info("Using mock LLM implementation")
    from core.llm.mock_llm_client import MockLLMClient as LLMClient
else:
    logger.info("Using real LLM implementation")
    try:
        from core.llm.production_llm_client import ProductionLLMClient as LLMClient
    except ImportError as e:
        logger.error(f"Failed to import real LLM client: {e}")
        raise ImportError(f"Unable to load production LLM client: {e}. If you want to use mock implementation, set PARLOURBENCH_USE_MOCK=1")

# Export LLMClient only
__all__ = ["LLMClient"]