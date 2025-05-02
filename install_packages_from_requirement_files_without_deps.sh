#!/bin/bash

# Path to your conflicting_deps.txt
DEPS_FILE="demo_input_requirements.txt"
DEPS_FILE="test_requirements.txt"
#DEPS_FILE="conflicting_deps.txt"
DEPS_FILE="python3_dev_requirements.txt"

# Ensure the file exists
if [[ ! -f "$DEPS_FILE" ]]; then
  echo "File '$DEPS_FILE' not found!"
  exit 1
fi

# Read and install each package with --no-deps option
while IFS= read -r package || [[ -n "$package" ]]; do
  if [[ ! -z "$package" ]]; then
    echo "Installing $package without dependencies..."
    pip3 install --no-deps "$package"
  fi
done < "$DEPS_FILE"
