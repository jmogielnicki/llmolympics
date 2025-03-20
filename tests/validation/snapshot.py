import os
import glob
import json
import shutil
import logging
import difflib
from pathlib import Path

logger = logging.getLogger("SnapshotValidation")

def normalize_json(json_obj):
    """
    Normalize timestamps and other variable data in JSON objects.

    Args:
        json_obj: JSON object (dict, list, etc.)

    Returns:
        JSON object with normalized values
    """
    if isinstance(json_obj, dict):
        normalized = {}
        for key, value in json_obj.items():
            # Normalize timestamp fields
            if key in ('timestamp', 'created_at', 'modified_at'):
                normalized[key] = "NORMALIZED_TIMESTAMP"
            # Skip session_id which contains timestamps
            elif key == 'session_id':
                normalized[key] = "NORMALIZED_SESSION_ID"
            # UUID fields
            elif key.endswith('_id') and isinstance(value, str) and '-' in value and len(value) > 30:
                normalized[key] = "NORMALIZED_UUID"
            # Directories with timestamps
            elif key in ('session_dir', 'output_dir') and isinstance(value, str):
                normalized[key] = "NORMALIZED_DIRECTORY"
            else:
                normalized[key] = normalize_json(value)
        return normalized
    elif isinstance(json_obj, list):
        return [normalize_json(item) for item in json_obj]
    else:
        return json_obj

def compare_json_files(actual_file, expected_file):
    """
    Compare two JSON files, normalizing variable data.

    Args:
        actual_file (str): Path to actual JSON file
        expected_file (str): Path to expected JSON file

    Returns:
        tuple: (bool, str) - Is match, difference description
    """
    if not os.path.exists(actual_file):
        return False, f"Actual file does not exist: {actual_file}"

    if not os.path.exists(expected_file):
        return False, f"Expected file does not exist: {expected_file}"

    try:
        with open(actual_file, 'r') as f1, open(expected_file, 'r') as f2:
            actual_json = json.load(f1)
            expected_json = json.load(f2)

            # Normalize variable data
            actual_normalized = normalize_json(actual_json)
            expected_normalized = normalize_json(expected_json)

            # Convert to string with consistent formatting
            actual_str = json.dumps(actual_normalized, sort_keys=True, indent=2)
            expected_str = json.dumps(expected_normalized, sort_keys=True, indent=2)

            # Check for exact match
            if actual_str == expected_str:
                return True, "Files match exactly"

            # Generate diff for reporting
            diff = difflib.unified_diff(
                expected_str.splitlines(),
                actual_str.splitlines(),
                fromfile="expected",
                tofile="actual",
                lineterm=""
            )
            diff_str = "\n".join(list(diff)[:20])  # Limit diff size
            if len(list(diff)) > 20:
                diff_str += "\n... (diff truncated) ..."

            return False, diff_str

    except json.JSONDecodeError as e:
        return False, f"JSON parsing error: {str(e)}"
    except Exception as e:
        return False, f"Comparison failed: {str(e)}"

def compare_jsonl_files(actual_file, expected_file):
    """
    Compare two JSONL files, normalizing variable data.

    Args:
        actual_file (str): Path to actual JSONL file
        expected_file (str): Path to expected JSONL file

    Returns:
        tuple: (bool, str) - Is match, difference description
    """
    if not os.path.exists(actual_file):
        return False, f"Actual file does not exist: {actual_file}"

    if not os.path.exists(expected_file):
        return False, f"Expected file does not exist: {expected_file}"

    try:
        # Load both files into lists of normalized JSON objects
        actual_lines = []
        with open(actual_file, 'r') as f:
            for line in f:
                try:
                    actual_lines.append(normalize_json(json.loads(line)))
                except json.JSONDecodeError:
                    actual_lines.append(line.strip())

        expected_lines = []
        with open(expected_file, 'r') as f:
            for line in f:
                try:
                    expected_lines.append(normalize_json(json.loads(line)))
                except json.JSONDecodeError:
                    expected_lines.append(line.strip())

        # Check line count first
        if len(actual_lines) != len(expected_lines):
            return False, f"Line count mismatch: actual={len(actual_lines)}, expected={len(expected_lines)}"

        # Compare each line
        for i, (actual, expected) in enumerate(zip(actual_lines, expected_lines)):
            if actual != expected:
                # Convert to string for detailed diff
                actual_str = json.dumps(actual, sort_keys=True)
                expected_str = json.dumps(expected, sort_keys=True)

                diff = difflib.unified_diff(
                    expected_str.splitlines(),
                    actual_str.splitlines(),
                    fromfile=f"expected line {i+1}",
                    tofile=f"actual line {i+1}",
                    lineterm=""
                )

                return False, f"Difference at line {i+1}:\n" + "\n".join(list(diff))

        # All lines match
        return True, "Files match exactly"

    except Exception as e:
        return False, f"Comparison failed: {str(e)}"

def compare_with_snapshot(actual_dir, expected_dir, update=False):
    """
    Compare actual benchmark results with expected snapshot.

    Args:
        actual_dir (str): Directory containing actual results
        expected_dir (str): Directory containing expected snapshots
        update (bool): Whether to update snapshots instead of comparing

    Returns:
        tuple: (bool, str) - Success flag and detailed message
    """
    logger.info(f"SNAPSHOT DEBUG - actual_dir: {actual_dir}, expected_dir: {expected_dir}, update: {update}")
    
    if not os.path.exists(actual_dir):
        logger.error(f"Actual directory does not exist: {actual_dir}")
        return False, f"Actual directory does not exist: {actual_dir}"

    # If updating, copy the actual results to the expected directory
    if update:
        logger.info(f"SNAPSHOT DEBUG - Attempting to update snapshots")
        # Ensure parent directory exists
        try:
            os.makedirs(os.path.dirname(expected_dir), exist_ok=True)
            logger.info(f"SNAPSHOT DEBUG - Created parent directory: {os.path.dirname(expected_dir)}")
        except Exception as e:
            logger.error(f"SNAPSHOT DEBUG - Failed to create parent directory: {str(e)}")
        
        # Remove existing directory if it exists
        if os.path.exists(expected_dir):
            shutil.rmtree(expected_dir)

        # Copy all contents
        shutil.copytree(actual_dir, expected_dir)
        logger.info(f"Updated snapshot at {expected_dir}")
        return True, f"Snapshot updated at {expected_dir}"

    # If expected directory doesn't exist, fail
    if not os.path.exists(expected_dir):
        return False, f"Expected output directory not found: {expected_dir}"

    # Compare benchmark log
    bench_log = os.path.join(actual_dir, "benchmark_log.jsonl")
    expected_bench_log = os.path.join(expected_dir, "benchmark_log.jsonl")

    if os.path.exists(bench_log) and os.path.exists(expected_bench_log):
        log_match, log_diff = compare_jsonl_files(bench_log, expected_bench_log)
        if not log_match:
            return False, f"Benchmark log mismatch:\n{log_diff}"

    # Compare benchmark state
    bench_state = os.path.join(actual_dir, "benchmark_state.json")
    expected_bench_state = os.path.join(expected_dir, "benchmark_state.json")

    if os.path.exists(bench_state) and os.path.exists(expected_bench_state):
        state_match, state_diff = compare_json_files(bench_state, expected_bench_state)
        if not state_match:
            return False, f"Benchmark state mismatch:\n{state_diff}"

    # Get session directories
    actual_sessions = [d for d in glob.glob(f"{actual_dir}/*")
                      if os.path.isdir(d) and not d.endswith("expected")]
    expected_sessions = [d for d in glob.glob(f"{expected_dir}/*")
                        if os.path.isdir(d) and not d.endswith("expected")]

    # We don't care about matching session IDs, but we want to match counts
    if len(actual_sessions) != len(expected_sessions):
        return False, f"Session count mismatch: actual={len(actual_sessions)}, expected={len(expected_sessions)}"

    # Sort sessions to ensure consistent comparison
    actual_sessions.sort()
    expected_sessions.sort()

    # Compare each session's results
    for i, (actual_session, expected_session) in enumerate(zip(actual_sessions, expected_sessions)):
        # Compare results.json
        actual_results = os.path.join(actual_session, "results.json")
        expected_results = os.path.join(expected_session, "results.json")

        if os.path.exists(actual_results) and os.path.exists(expected_results):
            results_match, results_diff = compare_json_files(actual_results, expected_results)
            if not results_match:
                return False, f"Results mismatch in session {i+1}:\n{results_diff}"

        # Compare snapshots.jsonl (if present)
        actual_snapshots = os.path.join(actual_session, "snapshots.jsonl")
        expected_snapshots = os.path.join(expected_session, "snapshots.jsonl")

        if os.path.exists(actual_snapshots) and os.path.exists(expected_snapshots):
            snapshots_match, snapshots_diff = compare_jsonl_files(actual_snapshots, expected_snapshots)
            if not snapshots_match:
                return False, f"Snapshots mismatch in session {i+1}:\n{snapshots_diff}"

    # All comparisons passed
    return True, "All results match expected snapshot"

def update_snapshot(actual_dir, expected_dir):
    """
    Update the expected snapshot with actual results.

    Args:
        actual_dir (str): Directory containing actual results
        expected_dir (str): Directory where expected snapshots should be stored

    Returns:
        bool: Success flag
    """
    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(expected_dir), exist_ok=True)

        # Remove existing directory if it exists
        if os.path.exists(expected_dir):
            shutil.rmtree(expected_dir)

        # Copy all contents
        shutil.copytree(actual_dir, expected_dir)
        logger.info(f"Updated snapshot at {expected_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to update snapshot: {str(e)}")
        return False