import os
import yaml
import logging

logger = logging.getLogger("MockAISuiteClient")

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockCompletions:
    def __init__(self, response_dir):
        self.response_dir = response_dir
        self.model_responses = {}  # Maps model name to list of responses
        self.current_indices = {}  # Tracks which response index to use for each model

        # Load all model response files
        self._load_response_files()

    def _load_response_files(self):
        """Load all model response files from the response directory"""
        if not os.path.exists(self.response_dir):
            logger.warning(f"Response directory does not exist: {self.response_dir}")
            return

        for file_name in os.listdir(self.response_dir):
            if file_name.endswith('.yaml'):
                file_path = os.path.join(self.response_dir, file_name)
                self._load_response_file(file_path)

    def _load_response_file(self, file_path):
        """Load responses from a single YAML file"""
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)

            model = config.get('model')
            if not model:
                logger.warning(f"Response file {file_path} missing 'model' field")
                return

            responses = []
            for resp in config.get('responses', []):
                responses.append(resp)

            if responses:
                self.model_responses[model] = responses
                self.current_indices[model] = 0
                logger.info(f"Loaded {len(responses)} responses for model {model} from {file_path}")
            else:
                logger.warning(f"No valid responses found in {file_path}")

        except Exception as e:
            logger.error(f"Failed to load response file {file_path}: {str(e)}")

    def create(self, model, messages, temperature=0.7, **kwargs):
        """Mock the create method for getting completions"""
        # Check if we have responses for this model
        if model not in self.model_responses:
            logger.warning(f"No responses configured for model {model}, using default response")
            return MockResponse("No response configured for this model.")

        responses = self.model_responses[model]
        if not responses:
            logger.warning(f"Empty response list for model {model}")
            return MockResponse("Empty response list for this model.")

        # Get the next response
        current_index = self.current_indices[model]
        response = responses[current_index % len(responses)]

        # Increment index for next call
        self.current_indices[model] = current_index + 1

        logger.info(f"Returning response {current_index % len(responses)} for model {model}")
        return MockResponse(response)

class MockChat:
    def __init__(self, response_dir):
        self.completions = MockCompletions(response_dir)

class MockAISuiteClient:
    """Mock implementation of aisuite.Client"""
    def __init__(self, response_dir="tests/test_data/responses"):
        self.chat = MockChat(response_dir)