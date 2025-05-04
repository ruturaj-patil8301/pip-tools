#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <requirements.txt>"
    exit 1
fi

DEPS_FILE="$1"

if [[ ! -f "$DEPS_FILE" ]]; then
  echo "File '$DEPS_FILE' not found!"
  exit 1
fi

NUM_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
PARALLEL_JOBS=$((NUM_CORES * 2))

echo "Installing packages from $DEPS_FILE using $PARALLEL_JOBS parallel jobs..."

grep -vE '^\s*#' "$DEPS_FILE" | grep -vE '^\s*$' | \
  xargs -n1 -P"$PARALLEL_JOBS" pip3 install --no-deps

echo "All packages installed."
