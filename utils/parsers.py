# utils/parsers.py
import logging
from core.llm import ResponseParserRegistry

logger = logging.getLogger("Parsers")

@ResponseParserRegistry.register("choice_parser")
class ChoiceParser:
    """
    Parser for choice responses.

    Parses responses from the LLM for choice-based actions,
    such as "cooperate" or "defect" in Prisoner's Dilemma.
    """

    def parse(self, response, phase_config):
        """
        Parse a choice response from the LLM.

        Args:
            response (str): The LLM's response
            phase_config (dict): The phase configuration

        Returns:
            str: The parsed choice
        """
        logger.debug(f"Parsing choice response: {response[:50]}...")

        response = response.strip().lower()

        # Get valid options from phase config
        options = []
        if 'actions' in phase_config and phase_config['actions']:
            action = phase_config['actions'][0]
            if 'options' in action:
                options = [opt.lower() for opt in action['options']]

        logger.debug(f"Valid options: {options}")

        # Check if response contains any of the valid options
        for option in options:
            if option in response:
                logger.info(f"Found option in response: {option}")
                return option

        # If no match found, try to infer from context
        if options and len(options) >= 2:
            if "cooperate" in response or "collaboration" in response or "together" in response:
                logger.info("Inferred cooperation from context")
                for opt in options:
                    if "cooperate" in opt:
                        return opt

            if "defect" in response or "betray" in response or "self" in response:
                logger.info("Inferred defection from context")
                for opt in options:
                    if "defect" in opt:
                        return opt

        # Default to first option if nothing matches
        if options:
            logger.warning(f"No match found, defaulting to first option: {options[0]}")
            return options[0]

        logger.error("No valid options found and no fallback available")
        return None


@ResponseParserRegistry.register("default_parser")
class DefaultParser:
    """
    Default parser for when no specific parser is specified.

    Simply returns the response as-is.
    """

    def parse(self, response, phase_config):
        """
        Parse a response from the LLM.

        Args:
            response (str): The LLM's response
            phase_config (dict): The phase configuration

        Returns:
            str: The raw response
        """
        logger.info("Using default parser")
        return response.strip()