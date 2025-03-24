# LLM Olympics

An open-source benchmark that evaluates AI models with gameplay.

## Overview

LLM Olympics is a platform for evaluating large language models (LLMs) by having them compete against each other in various parlour games. This benchmarking approach allows us to test strategic thinking, diplomatic prowess, creativity, persuasion, deceptive/cooperative behavior, and theory-of-mind capabilities.

Through these competitions, we develop comprehensive rankings across key dimensions and showcase them on our arena leaderboard. The benchmark continuously evolves as new models enter the competition, providing an ever-expanding view of the AI capability landscape.

## Why is this needed?

LLMs are quickly saturating traditional benchmarks - for example, they now achieve nearly 90% accuracy on MMLU. By pitting LLMs against one another in games we can continue to judge their relative performance even as they surpass us. We can also test their tendencies for various safety-related attributes, like deceptive behavior, strategic thinking, and persuasion.

## Features

- Modular architecture for easy extension to new games
- File-based configuration system using YAML
- Comprehensive state management and history tracking
- Detailed chat logs for all LLM interactions
- Integration with multiple LLM providers via `aisuite`
- Clean separation of game logic from LLM interaction
- Interactive web dashboard for visualizing results

## Supported Games

Currently, LLM Olympics has full implementation for:
- **Prisoner's Dilemma**: A classic game testing cooperation vs competition

Games with configuration but not fully implemented:
- **Diplomacy**: Tests alliance building and strategic elimination
- **Ghost**: Word game testing vocabulary and strategic planning
- **Ultimatum Game**: Tests fairness assessment and negotiation
- **Rock Paper Scissors**: Evaluates pattern prediction and deception

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

## Running the System

The complete workflow for running LLM Olympics involves several steps:

### 1. Running a Single Game

To run a single game with the specified configuration:

```bash
python main.py config/games/prisoners_dilemma.yaml
```

This will create a session directory in `data/sessions/` with logs, snapshots, and results.

### 2. Running a Benchmark

To run a benchmark that pits multiple models against each other:

```bash
python benchmark.py config/benchmarks/prisoners_dilemma_benchmark.yaml
```

This will run multiple games between different model combinations and store the results in `data/benchmark/[benchmark_id]/`.

### 3. Processing Data for Visualization

Process the benchmark data to generate visualization-friendly formats:

```bash
python scripts/process_data.py --all
```

Or for a specific benchmark:

```bash
python scripts/process_data.py --benchmark data/benchmark/prisoners_dilemma_benchmark_1
```

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

### Running Tests

To run integration tests:

```bash
python tests/integration_test.py --config config/games/prisoners_dilemma.yaml [--verbose] [--clean]
```

## Adding a New Game

To add a new game to LLM Olympics:

1. **Create a game configuration file** in `config/games/your_game.yaml`:

   ```yaml
   game:
     name: "Your Game Name"
     description: "A brief description of your game"
     type: "simultaneous_choice"  # or another game type

   players:
     min: 2
     max: 2
     roles: "symmetric"  # or "asymmetric"

   phases:
     - id: "phase_1"
       type: "simultaneous_action"
       actions:
         - name: "choose"
           options: ["option1", "option2"]
       next_phase: "resolution"

     - id: "resolution"
       type: "automatic"
       handler: "your_resolution_handler"
       next_phase_condition: "rounds_remaining"
       next_phase_success: "phase_1"
       next_phase_failure: "game_end"

   # Add other required sections: rounds, state, win_condition, etc.
   ```

2. **Create prompt templates** in `templates/your_game_prompt.txt` for LLM interactions.

3. **Implement custom handlers** if needed in `handlers/your_game.py`:

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
   python main.py config/games/your_game.yaml
   ```

5. **Add parsers** if needed for custom response formats in `core/llm/parser.py`.

## Adding a New Benchmark

To create a new benchmark configuration:

1. **Create a benchmark configuration file** in `config/benchmarks/your_benchmark.yaml`:

   ```yaml
   benchmark:
     id: "your_benchmark_id"
     base_config: "config/games/your_game.yaml"
     games_per_pair: 3
     output_dir: "data/benchmark"

   models:
     - openai:gpt-4o
     - anthropic:claude-3-5-sonnet-20240620
     - xai:grok-2-1212
     # Add more models as needed
   ```

2. **Run the benchmark**:

   ```bash
   python benchmark.py config/benchmarks/your_benchmark.yaml
   ```

3. **Process the benchmark data** for visualization:

   ```bash
   python scripts/process_data.py --benchmark data/benchmark/your_benchmark_id
   python scripts/process_game_detail.py --benchmark data/benchmark/your_benchmark_id --all
   ```

4. If you want to add visualization for a new game type, you'll need to update the web dashboard code in `web/src/components/ParlourBenchDashboard.jsx`.

## Adding a New Model to Existing Benchmarks

When a new model is released, you can add it to existing games and benchmarks:

1. **Add API Key** to your `.env` file for the model's provider:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   # Add new provider API key if needed
   NEW_PROVIDER_API_KEY=your_new_provider_api_key_here
   ```

2. **Update an existing benchmark** or create a new one with the new model:
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
   python benchmark.py config/benchmarks/your_updated_benchmark.yaml
   ```

4. **Process the new benchmark data**:
   ```bash
   python scripts/process_data.py --benchmark data/benchmark/your_benchmark_id
   python scripts/process_game_detail.py --benchmark data/benchmark/your_benchmark_id --all
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.