#!/bin/bash

# Set variables
script_dir="$(cd "$(dirname "$0")" && pwd)"  # Absolute path of the directory containing the script
target_dir="/etc/uniVirt"

# Create the target directory
sudo mkdir -p "$target_dir"

# Copy the ansible directory from the script directory to the target directory, overwriting existing files and directories
sudo cp -Rf "$script_dir/scripts/ansible" "$target_dir"
sudo cp -Rf "$script_dir/scripts/yamls" "$target_dir"

echo "Setup completed"
echo "Target directory is $target_dir"
echo "Following steps please check https://github.com/kubesys/uniVirt"
