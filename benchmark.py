#!/usr/bin/env python
# benchmark.py
import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core.benchmark.config import BenchmarkConfig
from core.benchmark.runner import BenchmarkRunner
from core.benchmark.multi_player_runner import MultiPlayerBenchmarkRunner
import core.game.handlers.common  # Import handlers to ensure they are registered
import core.game.handlers.creative_competition
import core.game.handlers.debate_competition

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ParlourBench-Benchmark")

def main():
    """
    Main entry point for LLM Showdown benchmarking.

    Parses command line arguments and runs the benchmark.
    """
    parser = argparse.ArgumentParser(description="Run LLM Showdown benchmarks")
    parser.add_argument("config", help="Path to the benchmark configuration file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if the config file exists
    config_path = args.config
    if not os.path.exists(config_path):
        print(f"Benchmark config file not found: {config_path}")
        if not config_path.startswith("config/benchmarks/"):
            suggested_path = os.path.join("config/benchmarks", os.path.basename(config_path))
            print(f"Try: {suggested_path}")
        return 1

    # Load benchmark configuration
    logger.info(f"Loading benchmark config: {config_path}")
    benchmark_config = BenchmarkConfig(config_path)

    # Determine benchmark type
    benchmark_type = benchmark_config.config['benchmark'].get('type', 'pairwise')
    logger.info(f"Benchmark type: {benchmark_type}")
    runner = None

    if benchmark_type == 'multi_player':
        # Create multi-player benchmark runner
        logger.info(f"Initializing multi-player benchmark runner")
        runner = MultiPlayerBenchmarkRunner(benchmark_config)

    else:
        # Create standard pairwise benchmark runner
        logger.info(f"Initializing pairwise benchmark runner")
        runner = BenchmarkRunner(benchmark_config)

    runner.run_benchmark()

    logger.info(f"Benchmark complete! Results available in: {benchmark_config.get_output_dir()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())