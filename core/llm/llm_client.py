import os
import logging

logger = logging.getLogger("LLMClient")

# Decide which implementation to use based on environment variable
print(os.environ.get("PARLOURBENCH_USE_MOCK", "false"))
use_mock = os.environ.get("PARLOURBENCH_USE_MOCK", "false").lower() in ["true", "1", "yes"]

if use_mock:
    logger.info("Using mock LLM implementation")
    from core.llm.mock_llm_client import MockLLMClient as LLMClient
else:
    logger.info("Using real LLM implementation")
    try:
        from core.llm.production_llm_client import ProductionLLMClient as LLMClient
    except ImportError as e:
        logger.warning(f"Failed to import real LLM client: {e}")
        logger.warning("Falling back to mock implementation")

# Export LLMClient only
__all__ = ["LLMClient"]