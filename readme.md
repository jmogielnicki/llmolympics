# ParlourBench

An open-source benchmark that pits LLMs against one another in parlour games.

## Overview

ParlourBench is a platform for evaluating large language models (LLMs) by having them compete against each other in various parlour games. This benchmarking approach allows us to test strategic thinking, diplomatic prowess, creativity, persuasion, deceptive/cooperative behavior, and theory-of-mind capabilities.

## Features

- Modular architecture for easy extension to new games
- File-based configuration system using YAML
- Comprehensive state management and history tracking
- Detailed chat logs for all LLM interactions
- Integration with multiple LLM providers via `aisuite`
- Clean separation of game logic from LLM interaction

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jmogielnicki/parlourbench.git
   cd parlourbench
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running a Game

To run a game, use the `main.py` script with a game configuration file:

```bash
python main.py config/games/prisoners_dilemma.yaml
```

All LLM interactions are automatically logged in JSONL format:
- Regular runs: Logs stored in `data/logs/` directory
- Integration tests: Logs stored in `data/test/logs/` directory

Each run creates a timestamped log file that contains the complete chat history for all players.

### Creating a New Game

1. Create a YAML configuration file in `config/games/`
2. Create prompt templates in `templates/`
3. Implement any game-specific handlers in `handlers/`
4. Add custom parsers if needed in `utils/parsers.py`

### Configuration Format

Game configurations use a YAML format with the following key sections:

- `game`: Basic game information (name, description, type)
- `players`: Player configuration (min/max count, roles)
- `phases`: Game phases with actions and transitions
- `rounds`: Round configuration (count, progression type)
- `state`: State variables for players, shared state, and history
- `win_condition`: Rules for determining the winner
- `llm_integration`: Settings for LLM interaction

Example:
```yaml
game:
  name: "Prisoner's Dilemma"
  description: "A classic game of cooperation and betrayal"
  type: "simultaneous_choice"

players:
  min: 2
  max: 2
  roles: "symmetric"

phases:
  - id: "decision"
    type: "simultaneous_action"
    actions:
      - name: "choose"
        options: ["cooperate", "defect"]
    next_phase: "resolution"

  - id: "resolution"
    type: "automatic"
    handler: "calculate_pd_outcome"
    next_phase_condition: "rounds_remaining"
    next_phase_success: "decision"
    next_phase_failure: "game_end"

# ... more configuration sections
```

## Extending the Framework

### Adding a New Handler

Create a new handler by extending the `PhaseHandler` class and registering it:

```python
from handlers.base import PhaseHandler
from handlers.registry import HandlerRegistry

@HandlerRegistry.register("my_custom_handler")
class MyCustomHandler(PhaseHandler):
    def process(self, game_state):
        # Implement your handler logic here
        return True  # Return condition result
```

### Adding a New Parser

Create a new parser and register it:

```python
from core.llm import ResponseParserRegistry

@ResponseParserRegistry.register("my_custom_parser")
class MyCustomParser:
    def parse(self, response, phase_config):
        # Implement your parsing logic here
        return parsed_result
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.