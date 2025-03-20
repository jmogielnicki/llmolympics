# ParlourBench Integration Testing

This directory contains an integration testing system for ParlourBench that allows running benchmarks and games with mock LLM responses in a deterministic environment.

## Key Features

- Complete end-to-end testing of games and benchmarks
- Fully deterministic execution (random, time, UUID)
- Configurable mock LLM responses through YAML files
- Support for both snapshot-based and assertion-based validation
- Helper script for easy creation of new tests

## Directory Structure

```
tests/
├── mock/                       # Mock implementations
│   ├── llm_client.py           # Mock LLM client
│   ├── random_patch.py         # Deterministic random functions
│   └── time_patch.py           # Deterministic time functions
├── validation/                 # Validation utilities
│   ├── snapshot.py             # Snapshot comparison
│   └── assertions.py           # Assertion-based validation
├── test_benchmarks.py          # Benchmark tests
├── test_games.py               # Individual game tests
├── conftest.py                 # pytest fixtures and configuration
├── create_test.py              # Helper script for creating new tests
└── test_data/                  # Test configurations and mock responses
    ├── benchmarks/             # Benchmark test configurations
    │   └── prisoners_dilemma_benchmark/
    │       ├── test_config.yaml
    │       ├── benchmark_config.yaml
    │       ├── game_config.yaml
    │       └── expected/      # Expected output snapshots
    ├── games/                  # Game test configurations
    └── responses/              # Mock LLM responses
        └── pd_responses/
            ├── model1.yaml
            └── model2.yaml
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run a Specific Benchmark Test

```bash
pytest tests/test_benchmarks.py -v --benchmark=prisoners_dilemma_benchmark
```

### Run a Specific Game Test

```bash
pytest tests/test_games.py -v --game=prisoners_dilemma
```

### Update Snapshots

When you intentionally modify the code in a way that changes the expected output, update the snapshots:

```bash
pytest tests/test_benchmarks.py -v --benchmark=prisoners_dilemma_benchmark --update-snapshots
```

## Creating a New Test

The easiest way to create a new test is to use the helper script:

```bash
# For a benchmark test
python tests/create_test.py --benchmark werewolf_benchmark

# For a game test
python tests/create_test.py --game werewolf

# Specify models
python tests/create_test.py --game werewolf --models "openai:gpt-4o" "anthropic:claude-3-7-sonnet" "mistral:mistral-large"

# Use specific example template
python tests/create_test.py --game werewolf --example werewolf
```

This will create all necessary directories and files with appropriate templates.

For snapshot-based tests, you must then establish a baseline by running with the `--update-snapshots` flag:

```bash
# For a specific benchmark test
pytest tests/test_benchmarks.py -v --benchmark=prisoners_dilemma_benchmark --update-snapshots

# For a specific game test
pytest tests/test_games.py -v --game=prisoners_dilemma --update-snapshots
```

This creates the expected output directory and populates it with the current test results. After this initial setup, you can run tests normally to compare against this baseline.


## Test Configuration Format

Each test requires a `test_config.yaml` file:

```yaml
name: "Test Name"
description: "Description of what this test verifies"

# Configuration paths - use either benchmark_config or game_config depending on test type
benchmark_config: "path/to/benchmark_config.yaml"  # For benchmark tests
game_config: "path/to/game_config.yaml"           # For game tests

# Mock LLM responses
mock_responses:
  - "path/to/model1_responses.yaml"
  - "path/to/model2_responses.yaml"

# Validation configuration - use either snapshot or assertion validation
validation:
  type: "snapshot"
  snapshot_dir: "path/to/expected_output"

  # Or for assertion-based validation:
  # type: "assertion"
  # assertions:
  #   - "games_completed == 5"
  #   - "player_scores['player_1'] >= 8"
  #   - "winners.count('player_2') >= 3"
```

## Mock Response Format

Mock responses are defined in YAML files:

```yaml
model: "provider:model-name"  # e.g., "openai:gpt-4o"
responses:
  # Phase-specific responses with context matching
  - phase: "decision"
    round: 1
    content: "I'll [[COOPERATE]] in this first round to establish trust."

  - phase: "voting"
    role: "villager"
    content: "I vote to eliminate [[player_3]]."

  # Keywords for matching specific prompts
  - match_keywords: ["final decision", "urgent"]
    content: "My final decision is option C."

  # Default fallback response
  - default: true
    content: "I'll choose the first available option."
```

The mock LLM client will select the best matching response based on the context and prompt content.

## Adding Custom Validation

For specialized validation needs, you can create a custom validator:

1. Add your validator to `tests/validation/`
2. Use `validation.type: "custom"` in your test configuration
3. Import and use your validator in `test_benchmarks.py` or `test_games.py`

## Debugging Tests

For more verbose output:

```bash
pytest tests/test_benchmarks.py -v --benchmark=prisoners_dilemma_benchmark --log-cli-level=DEBUG
```

To debug interactively:

```bash
pytest tests/test_benchmarks.py -v --benchmark=prisoners_dilemma_benchmark --pdb
```

## Best Practices

1. **Always establish snapshots first** - Run new tests with `--update-snapshots` before running normal comparison tests.
2. **Keep mock responses minimal** - Define only the responses you need for the test case.
3. **Make tests deterministic** - Don't rely on random behavior; design tests with predictable outcomes.
4. **Validate key outcomes** - Focus validation on important aspects like winner determination, score distribution, etc.
5. **Use descriptive test names** - Name tests clearly based on what they verify.
6. **Group related tests** - Keep related test configurations and responses together.