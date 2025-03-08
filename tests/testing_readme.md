# ParlourBench Testing

This document explains how to run the integration tests for ParlourBench without requiring actual LLM API calls.

## Prerequisites

- Python 3.9+
- PyYAML

## Setup

1. First, run the setup script to create the necessary directory structure and files:

```bash
python setup_test.py
```

This will:
- Create the project directory structure
- Set up template files
- Create configuration files
- Install mock handlers and parsers

2. Ensure you have the required Python packages:

```bash
pip install pyyaml
```

## Running the Integration Test

Run the integration test with:

```bash
python test_integration.py
```

This will:
1. Set up the test environment
2. Install the mock LLM client
3. Run a full game of Prisoner's Dilemma
4. Verify that state snapshots are created
5. Check that a results file is generated
6. Output the winner and final scores

### Options

- `--config`: Specify a different game configuration file
- `--verbose`: Enable more detailed logging

Example:
```bash
python test_integration.py --verbose
```

## Understanding the Test Process

The integration test uses a `MockLLMClient` that simulates real LLM responses without making API calls. This allows testing the full flow of the system, including:

1. Game initialization
2. Phase transitions
3. State management
4. History tracking
5. Game completion logic

The mock client is designed to provide somewhat realistic and contextually appropriate responses based on the game type and the content of the prompt.

## Extending the Tests

To test additional game types:

1. Add new configuration files in `config/games/`
2. Add corresponding templates in `templates/`
3. Add appropriate response patterns to the `MockLLMClient`
4. Implement any required custom handlers

## Troubleshooting

If you encounter errors:

1. Check the log output for details
2. Verify that all required files were created by the setup script
3. Ensure the directory structure matches what's expected
4. Make sure the `MockLLMClient` is properly installed

## Files Used in Testing

- `setup_test.py`: Sets up the test environment
- `test_integration.py`: Main test script
- `utils/mock_llm.py`: Mock LLM implementation
- `config/games/prisoners_dilemma.yaml`: Game configuration
- `templates/pd_decision.txt`: Prompt template