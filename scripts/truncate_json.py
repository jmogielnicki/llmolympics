#!/usr/bin/env python3
import json
import sys
from typing import Any, Dict, List, Union

def truncate_strings(obj: Any, max_length: int = 100) -> Any:
    """
    Recursively truncate all string values in a JSON object to the specified maximum length.

    Args:
        obj: The JSON object (dict, list, str, int, float, bool, None)
        max_length: Maximum length to truncate strings to (default: 100)

    Returns:
        The object with all string values truncated
    """
    if isinstance(obj, dict):
        return {k: truncate_strings(v, max_length) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [truncate_strings(item, max_length) for item in obj]
    elif isinstance(obj, str) and len(obj) > max_length:
        return obj[:max_length]
    else:
        # Return non-string values unchanged
        return obj

def process_jsonl_file(input_file: str, output_file: str, max_length: int = 100) -> None:
    """
    Process a JSONL file, truncating all string values to the specified length.

    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSONL file
        max_length: Maximum length for string values (default: 100)
    """
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line_num, line in enumerate(infile, 1):
            try:
                # Parse JSON object from line
                obj = json.loads(line.strip())

                # Truncate all string values
                truncated_obj = truncate_strings(obj, max_length)

                # Write truncated object as JSON line
                outfile.write(json.dumps(truncated_obj) + '\n')

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_num}: {e}", file=sys.stderr)
                # Skip invalid lines or handle differently as needed

    print(f"Processing complete. Truncated strings saved to {output_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Truncate all string values in a JSONL file to a maximum length")
    parser.add_argument("input_file", help="Path to input JSONL file")
    parser.add_argument("output_file", help="Path to output JSONL file")
    parser.add_argument("--max-length", type=int, default=100,
                        help="Maximum length for string values (default: 100)")

    args = parser.parse_args()

    process_jsonl_file(args.input_file, args.output_file, args.max_length)