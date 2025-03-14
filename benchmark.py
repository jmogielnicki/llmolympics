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
import core.game.handlers.common  # Import handlers to ensure they are registered

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ParlourBench-Benchmark")

def main():
    """
    Main entry point for ParlourBench benchmarking.

    Parses command line arguments and runs the benchmark.
    """
    parser = argparse.ArgumentParser(description="Run ParlourBench benchmarks")
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

    try:
        # Load benchmark configuration
        logger.info(f"Loading benchmark config: {config_path}")
        benchmark_config = BenchmarkConfig(config_path)

        # Create benchmark runner
        logger.info(f"Initializing benchmark runner")
        runner = BenchmarkRunner(benchmark_config)

        # Load existing benchmark log
        logger.info("Loading existing benchmark log (if any)")
        runner.load_benchmark_log()

        # Generate matchups to run
        logger.info("Generating matchups")
        runner.generate_matchups()

        if not runner.matchups_to_run:
            logger.info("No matchups to run. Benchmark is already complete.")
            return 0

        # Run the benchmark
        logger.info(f"Running benchmark with {len(runner.matchups_to_run)} matchups")
        runner.run_benchmark()

        logger.info(f"Benchmark complete! Results available in: {benchmark_config.get_output_dir()}")
        return 0

    except Exception as e:
        logger.error(f"Error running benchmark: {str(e)}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())