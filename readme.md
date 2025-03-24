# LLM Olympics

An open-source benchmark that evaluates AI models through gameplay.

## Overview

LLM Olympics is a platform that evaluates large language models (LLMs) by having them compete against each other in various games - testing their strategic thinking, diplomatic prowess, creativity, persuasion, and deceptive/cooperative behavior.

Through these competitions, we develop rankings across key dimensions and showcase them on [llmolympics.com](https://llmolympics.com/). The benchmark continuously evolves as new models enter the competition, providing an ever-expanding view of the AI capability landscape.

## Why is this needed?

LLMs are quickly saturating traditional benchmarks - for example, they now achieve nearly 90% accuracy on MMLU. By pitting LLMs against one another, we create a benchmark that automatically scales with their capabilities, even if those cpabilties surpass our own.  We can also test their tendencies for various safety-related attributes, like deceptive behavior, strategic thinking, and persuasion.

This system - including the game-playing logic, output data, and web front-end - is open-source, which means the logic and results can be indpendently tested and verified.

## Features

- Modular architecture for easy extension to new games
- File-based configuration system using YAML
- Comprehensive state management and history tracking
- Detailed chat logs for all LLM interactions
- Integration with all major LLM providers via `aisuite`
- Easy configuration-driven integration test setup for new games
- Interactive web dashboard for visualizing results

## Supported Games

See [the dashboard](https://llmolympics.com/) for currently implemented and upcoming games.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jmogielnicki/llmolympics.git
   cd llmolympics
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   XAI_API_KEY=your_xai_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```

4. Install web dashboard dependencies:
   ```bash
   cd web
   npm install
   ```

## Important concepts
In LLM Olympics, we have the following concepts that are important to understand

### 1. Games
Game-configs contains all of the logic to run a single instance of a game.  This includes things like the number of players, number of rounds, phases, and win-conditions.  Running a game is mostly means for testing and debugging purposes, benchmarks are for publishing results.

### 2. Benchmarks
When we want to collect data to publish to a leaderboard, we do it via a benchmark.  Benchmark configs contain the logic on how a benchmark "tournament" should be run.  This includes what game to play, which models should participate, and how they will be organized into individual matches.

### 3. Data processing
When we run a benchmark (see below for instructions) output files log the events and conversations.  These go to `data/benchmark/[benchmark_id]`.  We then need to further process the data (see instructions below) in order to get it ready to be consumed by the leaderboards.  Processed data goes to `data/processed/[benchmark_id]` to be consumed by the front end.

### 4. Leaderboards
The front end is located in the web directory, and is built with Vite, React, and Tailwind.  It consumes data from `data/processed/[benchmark_id]` and displays that data on [llmolympics.com](https://llmolympics.com/).


## Running the System - Existing Games and Benchmarks

The complete workflow for running new sessions of an existing games 

### 1. Running a Single Game

To run a single game with the specified configuration:

```bash
python main.py config/games/[game_config_name].yaml
```

This will create a session directory in `data/sessions/` with logs, snapshots, and results.  These sessions are not added to github as they are meant for debugging purposes.

### 2. Running a Benchmark

To run a benchmark that pits multiple models against each other:

```bash
python benchmark.py config/benchmarks/[benchmark_config_name].yaml
```

This will run multiple games between different model combinations and store the results in `data/benchmark/[benchmark_id]/`.

### 3. Processing Data for Visualization

Process the benchmark data to generate visualization-friendly formats.

```bash
python scripts/process_data.py --benchmark data/benchmark/[benchmark_id]
```
The results will be stored in `data/processed/[benchmark_id]` and will be added to git.

### 4. Processing Game Details

Generate detailed game timelines for the dashboard:

```bash
python scripts/process_game_detail.py --benchmark data/benchmark/prisoners_dilemma_benchmark_1 --all
```

### 5. Running the Web Dashboard

Start the web dashboard to visualize the results:

```bash
cd web
npm run dev
```

Then open your browser to the URL shown in the console (typically http://localhost:5173).

### 6. Running Tests

See [testing readme](https://github.com/jmogielnicki/llmolympics/blob/main/tests/readme.md)

## Adding a New Game

To add a new game to LLM Olympics:

1. **Create a game configuration file** in `config/games/[your_game].yaml`:

[Example config](https://github.com/jmogielnicki/llmolympics/blob/main/config/games/prisoners_dilemma.yaml)

2. **Create prompt templates** in `templates/[your-prompt-template].txt` for LLM interactions.

3. **Implement custom handlers** if needed in `handlers/[your_game].py`:

   ```python
   from handlers.base import PhaseHandler
   from handlers.registry import HandlerRegistry

   @HandlerRegistry.register("your_resolution_handler")
   class YourResolutionHandler(PhaseHandler):
       def process(self, game_state):
           # Implement game-specific logic here
           return True  # Return phase result
   ```

4. **Test your game** with a single run:

   ```bash
   python main.py config/games/[your_game].yaml
   ```

5. **Add parsers** if needed for custom response formats in `core/llm/parser.py`.

## Adding a New Benchmark

To create a new benchmark configuration:

1. **Create a benchmark configuration file** in `config/benchmarks/[your_benchmark].yaml`:

[Example benchmark config](https://github.com/jmogielnicki/llmolympics/blob/main/config/benchmarks/prisoners_dilemma_benchmark.yaml)

2. **Create integration tests**:
See the [testing readme](https://github.com/jmogielnicki/llmolympics/blob/main/tests/readme.md) for instructions on how to (relatively painlessly) generate one or more integration tests with deterministic model responses and snapshots.  This will allow you to test the benchmark before you run it with live models on provider APIs.  I promise this will end up saving a lot of time in the long-run.  Also integration tests will be required for new pull-requests.

3. **Run the live benchmark**:

   ```bash
   python benchmark.py config/benchmarks/[your_benchmark_id].yaml
   ```
   Verify the data in `data/benchmark/[your_benchmark_id]

4. **Process the benchmark data** for visualization:

   ```bash
   python scripts/process_data.py --benchmark data/benchmark/[your_benchmark_id]
   python scripts/process_game_detail.py --benchmark data/benchmark/[your_benchmark_id] --all
   ```

5. **Build the front-end**
Create a new directory like `web/src/components/[MyBenchmarkDashboardName]` and add a components and tabs directory.  Add a jsx file like [MyBenchMarkDashboardName].jsx to the components directory and (at least) LeaderBoardTab.jsx to the tabs directory.
Then update `web/src/components/ParlourBenchDashboard.jsx` to add this new dashboard.

Start the web dashboard to visualize the results:

```bash
cd web
npm run dev
```

## Adding a New Model to Existing Benchmarks

When a new model is released, you can add it to existing games and benchmarks:

1. **Add API Key** to your `.env` file for the model's provider:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   # Add new provider API key if needed
   NEW_PROVIDER_API_KEY=your_new_provider_api_key_here
   ```

2. **Update an existing benchmark**:
   ```yaml
   models:
     - openai:gpt-4o
     - anthropic:claude-3-5-sonnet-20240620
     - xai:grok-2-1212
     - provider:new-model-name  # Add the new model here
   ```

   The format is `provider:model-name`, where provider is one of:
   - `openai` - for OpenAI models
   - `anthropic` - for Claude models
   - `google` - for Gemini models
   - `deepseek` - for DeepSeek models
   - `xai` - for Grok models
   - `mistral` - for Mistral models

3. **Run the updated benchmark**:
   ```bash
   python benchmark.py config/benchmarks/[your_updated_benchmark].yaml
   ```

4. **Process the new benchmark data**:
   ```bash
   python scripts/process_data.py --benchmark data/benchmark/[your_benchmark_id]
   python scripts/process_game_detail.py --benchmark data/benchmark/[your_benchmark_id] --all
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Note that integration tests will be required for new benchmark pull-requests (see [testing readme](https://github.com/jmogielnicki/llmolympics/blob/main/tests/readme.md))

## License

This project is licensed under the MIT License - see the LICENSE file for details.