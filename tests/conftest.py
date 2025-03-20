import pytest
import os
import yaml
import glob
import uuid
import logging
from unittest.mock import patch
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import our mock utilities
from tests.mock.llm_client import MockLLMClient
from tests.mock.random_patch import DeterministicRandom
from tests.mock.time_patch import DeterministicTime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ParlourBenchTest")

def pytest_addoption(parser):
    """Add custom command line options for the test system"""
    parser.addoption(
        "--update-snapshots", 
        action="store_true", 
        default=False,
        help="Update expected output snapshots instead of comparing"
    )
    parser.addoption(
        "--benchmark", 
        action="store", 
        default=None,
        help="Run tests for a specific benchmark configuration"
    )
    parser.addoption(
        "--game", 
        action="store", 
        default=None,
        help="Run tests for a specific game configuration"
    )

@pytest.fixture
def update_snapshots(request):
    """Fixture that returns whether we should update snapshots"""
    return request.config.getoption("--update-snapshots")

@pytest.fixture
def benchmark_filter(request):
    """Fixture that returns the benchmark filter if specified"""
    return request.config.getoption("--benchmark")

@pytest.fixture
def game_filter(request):
    """Fixture that returns the game filter if specified"""
    return request.config.getoption("--game")

@pytest.fixture(scope="function")
def deterministic_environment():
    """
    Set up a fully deterministic environment for testing.
    
    This patches random functions, time functions, and UUID generation
    to ensure tests are completely reproducible.
    """
    # Create patchers
    det_random = DeterministicRandom()
    det_time = DeterministicTime()
    
    # Define deterministic UUID function
    def fixed_uuid4():
        return uuid.UUID('00000000-0000-0000-0000-000000000000')
    
    # Apply patches
    random_patches = det_random.apply_patches()
    time_patches = det_time.apply_patches()
    uuid_patch = patch('uuid.uuid4', fixed_uuid4)
    uuid_patch.start()
    
    # Store original directory for restoration
    original_dir = os.getcwd()
    
    # Ensure we're in the project root for consistent path resolution
    os.chdir(project_root)
    
    yield
    
    # Restore original directory
    os.chdir(original_dir)
    
    # Stop all patches
    uuid_patch.stop()
    # Use the custom stop method for time patches
    det_time.stop_patches(time_patches)
    for p in random_patches:
        p.stop()

@pytest.fixture
def mock_llm(request):
    """
    Create and inject a mock LLM client.
    
    The fixture is parameterized with the test configuration path.
    """
    # Get test config from parameter
    if isinstance(request.param, str):
        config_path = request.param
    else:
        # If we're passed a dict, it should be a loaded config
        config = request.param
        config_path = config.get('path', 'unknown_path')
    
    # Load the test configuration
    try:
        if isinstance(request.param, str):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = request.param
            
        mock_responses = config.get('mock_responses', [])
        logger.info(f"Configuring mock LLM with responses from: {mock_responses}")
        
        # Create the mock LLM client
        client = MockLLMClient(mock_responses)
        client.test_config_path = config_path
        
        # Apply patches - based on the actual module structure:
        
        # 1. Patch the ProductionLLMClient directly
        production_client_patch = patch('core.llm.production_llm_client.ProductionLLMClient', return_value=client)
        production_client_patch.start()
        
        # 3. Patch OpenAI for any direct usage
        openai_patch = patch('openai.OpenAI', return_value=client)
        openai_patch.start()
        
        # 4. Patch Anthropic for any direct usage
        anthropic_patch = patch('anthropic.Anthropic', return_value=client)
        anthropic_patch.start()
        
        yield client
        
        # Stop all patches
        production_client_patch.stop()
        openai_patch.stop()
        anthropic_patch.stop()
        
    except Exception as e:
        logger.error(f"Failed to set up mock LLM: {str(e)}")
        raise

def load_test_configs(directory_pattern):
    """
    Load all test configurations matching the pattern.
    
    Args:
        directory_pattern (str): Pattern to match test directories
        
    Returns:
        list: List of test configuration paths
    """
    # Get absolute path for pattern
    abs_pattern = os.path.join(project_root, directory_pattern)
    test_dirs = glob.glob(abs_pattern)
    
    configs = []
    for test_dir in test_dirs:
        config_path = os.path.join(test_dir, "test_config.yaml")
        if os.path.exists(config_path):
            configs.append(config_path)
    
    return configs

def pytest_generate_tests(metafunc):
    """
    Auto-discover and filter test configurations.
    
    This allows automatic parameterization of test functions
    that use the mock_llm fixture.
    """
    if 'mock_llm' in metafunc.fixturenames:
        # Get filters
        benchmark_filter = metafunc.config.getoption("--benchmark")
        game_filter = metafunc.config.getoption("--game")
        
        # Load benchmark configs
        benchmark_configs = load_test_configs("tests/test_data/benchmarks/*")
        
        # Load game configs
        game_configs = load_test_configs("tests/test_data/games/*")
        
        all_configs = []
        
        # Apply filters to benchmarks
        if benchmark_filter:
            filtered_benchmarks = [
                config for config in benchmark_configs 
                if benchmark_filter.lower() in config.lower()
            ]
            all_configs.extend(filtered_benchmarks)
        elif game_filter:
            filtered_games = [
                config for config in game_configs
                if game_filter.lower() in config.lower()
            ]
            all_configs.extend(filtered_games)
        else:
            # Use all configs if no filter
            all_configs = benchmark_configs + game_configs
            
        # If we have no configs even after filtering, use a sensible default
        if not all_configs and (benchmark_filter or game_filter):
            logger.warning(f"No configs found for filter: benchmark={benchmark_filter}, game={game_filter}")
            logger.warning("Using default test configuration")
            default_config = os.path.join(project_root, "tests/test_data/default_test_config.yaml")
            if os.path.exists(default_config):
                all_configs = [default_config]
        
        if not all_configs:
            logger.error("No test configurations found!")
        
        # Parameterize the test
        metafunc.parametrize("mock_llm", all_configs, indirect=True, 
                            ids=[os.path.basename(os.path.dirname(c)) for c in all_configs])