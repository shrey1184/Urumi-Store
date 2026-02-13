#!/bin/bash
# Setup script for Urumi-Ai local development environment
# This configures passwordless sudo for the hosts file updater

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Urumi-Ai Store Platform - Local Setup"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "Please run as normal user (not root)"
   echo "The script will ask for sudo password when needed"
   exit 1
fi

# Step 1: Configure sudoers for passwordless hosts file updates
echo "Step 1: Configuring passwordless sudo for hosts file management..."
echo ""
echo "This will allow the backend to automatically update /etc/hosts"
echo "when new stores are created."
echo ""

SUDOERS_FILE="$SCRIPT_DIR/urumi-ai-sudoers"
SUDOERS_DEST="/etc/sudoers.d/urumi-ai"

# Replace placeholder username with actual user
TEMP_SUDOERS="/tmp/urumi-ai-sudoers.$$"
sed "s|shrey|$USER|g; s|/home/shrey/Urumi-Ai|$PROJECT_ROOT|g" "$SUDOERS_FILE" > "$TEMP_SUDOERS"

echo "Installing sudoers configuration..."
sudo install -m 0440 "$TEMP_SUDOERS" "$SUDOERS_DEST"
rm "$TEMP_SUDOERS"

echo "✓ Sudoers configuration installed"
echo ""

# Step 2: Sync existing stores to /etc/hosts
echo "Step 2: Syncing existing store domains to /etc/hosts..."
"$SCRIPT_DIR/update-hosts.sh" sync
echo ""

# Step 3: Check if backend is running
echo "Step 3: Checking backend status..."
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "✓ Backend is running"
    echo ""
    echo "⚠ Note: You may need to restart the backend for changes to take effect:"
    echo "  Press Ctrl+C in the backend terminal and restart with:"
    echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
else
    echo "✓ Backend not running (no restart needed)"
fi
echo ""

# Step 4: Instructions
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "What's been configured:"
echo "  ✓ Passwordless sudo for hosts file updates"
echo "  ✓ Synced existing store domains to /etc/hosts"
echo ""
echo "Now when you create a new store:"
echo "  1. The backend will automatically add it to /etc/hosts"
echo "  2. You can immediately access the store in your browser"
echo ""
echo "Manual commands (if needed):"
echo "  - Sync all stores:   ./scripts/update-hosts.sh sync"
echo "  - Add a store:       ./scripts/update-hosts.sh add <name> <domain>"
echo "  - Remove a store:    ./scripts/update-hosts.sh remove <name>"
echo "  - Clean all entries: ./scripts/update-hosts.sh clean"
echo ""
