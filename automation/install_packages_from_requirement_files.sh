#!/bin/bash

# install_packages_from_requirement_files.sh
#
# This script installs Python packages from a requirements file using parallel installation.
# It skips dependencies to avoid conflicts and uses multiple cores for faster installation.
#
# Usage: ./install_packages_from_requirement_files.sh <requirements.txt>
#
# Arguments:
#   $1 - Path to the requirements file
#
# Exit codes:
#   0 - Success
#   1 - Error (file not found or invalid arguments)
#
# Notes:
#   - Uses pip3 to install packages
#   - Installs packages with --no-deps to avoid dependency conflicts
#   - Uses parallel installation for better performance
#   - Skips comments and empty lines in the requirements file

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <requirements.txt>"
    exit 1
fi

# Store the requirements file path
DEPS_FILE="$1"

# Check if the file exists
if [[ ! -f "$DEPS_FILE" ]]; then
  echo "File '$DEPS_FILE' not found!"
  exit 1
fi

# Determine the number of CPU cores for parallel processing
# Try different methods depending on the OS
NUM_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# Set the number of parallel jobs to twice the number of cores
# This is a common heuristic for I/O bound tasks
PARALLEL_JOBS=$((NUM_CORES * 2))

echo "Installing packages from $DEPS_FILE using $PARALLEL_JOBS parallel jobs..."

# Process the requirements file:
# 1. Remove comment lines (starting with #)
# 2. Remove empty lines
# 3. Pass each package to xargs for parallel installation
# 4. Install each package with pip3 using --no-deps flag
grep -vE '^\s*#' "$DEPS_FILE" | grep -vE '^\s*$' | \
  xargs -n1 -P"$PARALLEL_JOBS" pip3 install --no-deps

echo "All packages installed."
