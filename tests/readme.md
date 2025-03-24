# LLM Olympics Integration Testing

This directory contains an integration testing system for LLM Olympics that allows running benchmarks and games with mock LLM responses in a deterministic environment.

## Key Features

- Complete end-to-end testing of games and benchmarks
- Fully deterministic execution (random, time, UUID)
- Configurable mock LLM responses through YAML files
- Support for both snapshot-based and assertion-based validation

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
Note: See [this commit](https://github.com/jmogielnicki/llmolympics/commit/ab88ebdcfaa6cb7ce5c0338711f2fa07446ce574) for an example of adding new config files and [this commit](https://github.com/jmogielnicki/llmolympics/commit/6b6c23f164a7b603830331758bcdf692f430b2fa) to see the saved snapshots.

__________________

To create a new test, you will need to create a new directory like tests/test_data/benchmarks/<benchmark_name>.

Then add the required configuration files:
- benchmark_config.py
- game_config.py
- test_config.py
- responses (directory)
  - model1.yaml
  - model2.yaml
  - etc

Once these files have been added you should be able to run the test like this:

```bash
# For a specific benchmark test
pytest tests/test_benchmarks.py -v --benchmark=prisoners_dilemma_benchmark
```

The integration test should output the benchmark json files into the directory you specify in test_config.py.  You can then go and inspect these results to see if they match your expectations of what should happen given your configuration - game/benchmark setup and deterministic model responses.

Once you've determined that the results match expectations, you can update the snapshot with

```bash
# For a specific benchmark test
pytest tests/test_benchmarks.py -v --benchmark=prisoners_dilemma_benchmark --update-snapshots
```

This creates the expected output directory and populates it with the current test results. After this initial setup, you can run tests normally to compare against this baseline.

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