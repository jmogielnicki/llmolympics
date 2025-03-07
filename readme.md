# LLM Diplomacy Arena

A framework for running diplomacy-style games using large language models (LLMs) as players.

## Overview

This project implements a game system where LLM instances participate in a diplomacy-style elimination game. Players communicate with each other, form alliances, and vote to eliminate other players, with the goal of being the last player standing.

## System Architecture

The system is built around these core components:

- **Game Controller**: Manages game state, controls round progression, and enforces game rules
- **Event System**: Provides event broadcasting and comprehensive logging of all game actions
- **Terminal Interface**: Enables game control and monitoring through a command-line interface
- **Player Manager**: (Coming in Phase 2) Will handle LLM interactions and response parsing

## Features Implemented (Phase 1)

- Complete game state management
- Round structure with discussion and voting phases
- Turn management during discussion phase
- Vote collection and processing
- Player elimination logic
- Game end detection
- Comprehensive event logging
- Terminal-based user interface
- Command-line game control
- Game state serialization and persistence

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/jmogielnicki/llm_diplomacy_arena.git
   cd llm-diplomacy
   ```

2. No additional dependencies are required for Phase 1, as it only uses Python's standard library.

## Usage

### Interactive Mode

Run the game in interactive mode:

```
python main.py
```

This opens a command-line interface where you can control the game using commands.

### Available Commands

- `init --players=N`: Initialize a new game with N players
- `start`: Start the game
- `state`: Show the current game state
- `message --player=X --content="Message"`: Submit a player message
- `vote --voter=X --target=Y`: Submit a vote
- `next-phase`: Force transition to next phase
- `next-round`: Force transition to next round
- `eliminate --player=X`: Manually eliminate a player
- `export-log --file=name`: Export event log to file

### Example Workflow

1. Initialize a game with 6 players:
   ```
   init --players=6
   ```

2. Start the game:
   ```
   start
   ```

3. Submit messages for each player during discussion phase:
   ```
   message --player=player1 --content="Hello everyone, I suggest we form an alliance."
   message --player=player2 --content="I agree with player1."
   ...
   ```

4. Submit votes during voting phase:
   ```
   vote --voter=player1 --target=player3
   vote --voter=player2 --target=player3
   ...
   ```

5. After all votes, the game automatically processes them, eliminates a player, and starts the next round.

6. Export the event log:
   ```
   export-log --file=game1.json
   ```

## Testing

Run the integration test to verify core functionality:

```
python tests/integration_test.py
```

The test runs through a complete game simulation, checking that each component works correctly.
