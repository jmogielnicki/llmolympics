# LLM Olympics Agent Guidelines

## Commands
- Run game: `python main.py config/games/prisoners_dilemma.yaml`
- Run integration test: `python tests/integration_test.py --config config/games/prisoners_dilemma.yaml [--verbose] [--clean]`
- View logs: 
  - Game logs: Stored in `data/logs/` directory in JSONL format with timestamp prefixes
  - Test logs: Stored in `data/test/logs/` directory when running integration tests

## Code Style
- PEP 8 conventions with 4-space indentation
- Google docstring format with complete param/return documentation
- Type hints for function parameters and return values
- Module-level loggers for consistent logging
- Component registration via decorators in registry patterns
- Explicit error handling with informative error messages
- Use snake_case for variables/functions, PascalCase for classes

## Architecture
- Clean separation of concerns (game logic, LLM interaction, state)
- Phase-based game flow with typed handlers for different phases
- Configuration-driven game definition using YAML
- Snapshot-based state management for game replay and analysis
- Comprehensive chat logging for debugging and analysis
- Singleton chat logger instance accessible throughout the application