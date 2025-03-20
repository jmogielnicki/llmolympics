#!/bin/bash

function print_directory_structure() {
  local dir="$1"
  local indent="$2"

  if [[ -z "$indent" ]]; then
    indent="";
  fi

  echo "${indent}${dir##*/}/"

  local files=($(find "$dir" -maxdepth 1 -type f ! -name ".*" ! -name "__pycache__" | sort | head -n 5))

  for file in "${files[@]}"; do
    echo "${indent}  ${file##*/}"
  done

  local subdirs=($(find "$dir" -maxdepth 1 -type d ! -name ".*" ! -name "__pycache__" | sort))

  for subdir in "${subdirs[@]}"; do
    if [[ "$subdir" != "$dir" ]]; then
      print_directory_structure "$subdir" "${indent}  "
    fi
  done
}

# Check if subdirectories are provided as arguments
if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <subdir1> <subdir2> ..."
  exit 1
fi

# Iterate through the provided subdirectories
for subdir in "$@"; do
  if [[ -d "$subdir" ]]; then
    print_directory_structure "$subdir"
  else
    echo "Error: Directory '$subdir' not found."
  fi
done
