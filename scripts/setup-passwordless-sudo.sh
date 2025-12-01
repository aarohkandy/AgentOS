#!/bin/bash
# Script to configure passwordless sudo for the current user
# WARNING: This reduces security - only use on development machines

USER=$(whoami)
SUDOERS_LINE="$USER ALL=(ALL:ALL) NOPASSWD: ALL"

echo "Setting up passwordless sudo for user: $USER"
echo "This will allow you to run sudo commands without entering a password."
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Check if the line already exists
if sudo grep -q "^$USER.*NOPASSWD" /etc/sudoers 2>/dev/null; then
    echo "Passwordless sudo is already configured for $USER"
    exit 0
fi

# Use visudo to safely edit sudoers
echo "$SUDOERS_LINE" | sudo EDITOR='tee -a' visudo

if [ $? -eq 0 ]; then
    echo "✓ Passwordless sudo configured successfully!"
    echo "You can now run sudo commands without a password."
else
    echo "✗ Failed to configure passwordless sudo"
    exit 1
fi

