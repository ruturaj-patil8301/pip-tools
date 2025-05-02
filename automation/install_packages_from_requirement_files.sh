#!/bin/bash

# Check provided arguments first
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <requirements.txt>"
    exit 1
fi

DEPS_FILE="$1"

# Ensure the provided requirements.txt file exists clearly
if [[ ! -f "$DEPS_FILE" ]]; then
  echo "File '$DEPS_FILE' not found!"
  exit 1
fi

# Install packages from the provided requirements.txt file explicitly without dependencies
while IFS= read -r package || [[ -n "$package" ]]; do
  # Skip empty lines and comments (#)
  if [[ ! -z "$package" && ! "$package" =~ ^# ]]; then
    echo "Installing $package without dependencies..."
    pip3 install "$package"
  fi
done < "$DEPS_FILE"
