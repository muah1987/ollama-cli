#!/bin/bash
set -euo pipefail
# One-line installer for ollama-cli
# Usage: curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash

REPO_URL="https://github.com/muah1987/ollama-cli.git"
INSTALL_DIR="${HOME}/.ollama-cli"

echo "Installing Ollama CLI..."

# Check for required tools
command -v git >/dev/null 2>&1 || { echo "Error: git is required but not installed."; exit 1; }

# Install uv if not present
if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR" && git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Install dependencies
uv sync

# Create .env from sample if not exists
[ ! -f .env ] && cp .env.sample .env 2>/dev/null || true

# Add alias suggestion
echo ""
echo "Installation complete!"
echo ""
echo "Add this to your shell profile (~/.bashrc or ~/.zshrc):"
echo "  alias ollama-cli='uv run $INSTALL_DIR/src/cli.py'"
echo ""
echo "Then start chatting: ollama-cli chat"
