# core/llm/client_factory.py
import os
import logging

logger = logging.getLogger("client_factory")

def create_llm_client(chat_logger):
    """
    Create an appropriate LLM client based on environment settings.

    Args:
        chat_logger: ChatLogger instance for logging interactions

    Returns:
        An instance of ProductionLLMClient with the appropriate API client
    """
    from core.llm.production_llm_client import ProductionLLMClient

    # Check if we're in test mode
    use_mock = os.environ.get("PARLOURBENCH_USE_MOCK", "false").lower() in ["true", "1", "yes"]

    if use_mock:
        logger.info("Using mock API client")
        from tests.test_utils import MockAIClient
        api_client = MockAIClient()
    else:
        logger.info("Using real API client")
        api_client = None  # Will use real client

    # Always use ProductionLLMClient with the appropriate API client
    return ProductionLLMClient(chat_logger=chat_logger, api_client=api_client)