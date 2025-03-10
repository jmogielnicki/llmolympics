# core/llm/parser.py
import logging
import re

logger = logging.getLogger("ResponseParser")

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


@ResponseParserRegistry.register("choice_parser")
class ChoiceParser:
    """
    Parser for choice responses.

    Parses responses from the LLM for choice-based actions,
    such as "cooperate" or "defect" in Prisoner's Dilemma.
    Prioritizes looking for choices in double brackets like [[COOPERATE]].
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

        # Get valid options from phase config
        options = []
        if 'actions' in phase_config and phase_config['actions']:
            action = phase_config['actions'][0]
            if 'options' in action:
                options = [opt.lower() for opt in action['options']]

        logger.debug(f"Valid options: {options}")

        # First, look for choices in double brackets [[CHOICE]]
        bracket_matches = re.findall(r'\[\[(.*?)\]\]', response, re.IGNORECASE)

        if bracket_matches:
            # Get the first bracketed choice
            bracketed_choice = bracket_matches[0].strip().lower()
            logger.debug(f"Found bracketed choice: {bracketed_choice}")

            # Check if the bracketed choice matches any valid option
            for option in options:
                if option in bracketed_choice:
                    logger.info(f"Matched bracketed choice to option: {option}")
                    return option

            # If brackets found but no valid option matched, try exact match
            if bracketed_choice in options:
                logger.info(f"Exact match for bracketed choice: {bracketed_choice}")
                return bracketed_choice

            logger.warning(f"Bracketed choice '{bracketed_choice}' didn't match any valid option")

        # Fail instead of using defaults
        if options:
            logger.error(f"No option matched in response. Valid options: {options}")
            raise ValueError(f"Failed to parse a valid choice from response. Options were: {options}")
        else:
            logger.error("No valid options found to choose from")
            raise ValueError("No valid options provided for choice parsing")


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


@ResponseParserRegistry.register("integer_parser")
class IntegerParser:
    """
    Parser for integer responses.

    Extracts an integer value from the LLM's response.
    Useful for things like Ultimatum Game offers.
    Also looks for responses in double brackets.
    """

    def parse(self, response, phase_config):
        """
        Parse an integer from the response.

        Args:
            response (str): The LLM's response
            phase_config (dict): The phase configuration

        Returns:
            int: The parsed integer, or a default value if none found
        """
        logger.debug(f"Parsing integer from response: {response[:50]}...")

        # Get constraints from phase config
        min_val = 0
        max_val = 100

        if 'actions' in phase_config and phase_config['actions']:
            action = phase_config['actions'][0]
            if 'parameters' in action:
                params = action['parameters']
                min_val = params.get('min', min_val)
                max_val = params.get('max', max_val)

        # First, check for integers in double brackets
        bracket_matches = re.findall(r'\[\[(\d+)\]\]', response)
        if bracket_matches:
            value = int(bracket_matches[0])
            if min_val <= value <= max_val:
                logger.info(f"Found valid integer in brackets: {value}")
                return value
            else:
                logger.error(f"Bracketed integer {value} out of range (min: {min_val}, max: {max_val})")
                raise ValueError(f"Integer {value} out of range (min: {min_val}, max: {max_val})")

        # If no bracketed integers, try to find any integer in the response
        matches = re.findall(r'\b(\d+)\b', response)

        if matches:
            # Get all integers and find the first one in range
            for match in matches:
                value = int(match)
                if min_val <= value <= max_val:
                    logger.info(f"Found valid integer in response: {value}")
                    return value

            # If no value in range, raise an exception
            value = int(matches[0])
            logger.error(f"Integer {value} out of range (min: {min_val}, max: {max_val})")
            raise ValueError(f"Integer {value} out of range (min: {min_val}, max: {max_val})")

        # Raise an exception if no integer found
        logger.error("No integer found in response")
        raise ValueError(f"Failed to parse an integer from response (min: {min_val}, max: {max_val})")


@ResponseParserRegistry.register("single_character_parser")
class SingleCharacterParser:
    """
    Parser for single character responses.

    Extracts a single character from the LLM's response.
    Useful for games like Ghost where players add single letters.
    Also checks for characters in double brackets.
    """

    def parse(self, response, phase_config):
        """
        Parse a single character from the response.

        Args:
            response (str): The LLM's response
            phase_config (dict): The phase configuration

        Returns:
            str: The parsed character, or a default if none found
        """
        logger.debug(f"Parsing single character from response: {response[:50]}...")

        # First, check for characters in double brackets
        bracket_matches = re.findall(r'\[\[([a-zA-Z])\]\]', response)
        if bracket_matches:
            logger.info(f"Found character in brackets: {bracket_matches[0]}")
            return bracket_matches[0].lower()

        # If no bracketed character, extract all alphabetic characters
        chars = re.findall(r'[a-zA-Z]', response)

        if chars:
            # Return the first character
            logger.info(f"Found character in response: {chars[0]}")
            return chars[0].lower()

        # Fail if no character found
        logger.error("No alphabetic character found in response")
        raise ValueError("Failed to parse any alphabetic character from response")