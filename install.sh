#!/bin/bash
set -euo pipefail
# One-line installer for ollama-cli
# Usage: curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash

REPO_URL="https://github.com/muah1987/ollama-cli.git"
INSTALL_DIR="${HOME}/.ollama-cli"
OLLAMA_VERSION="0.3.5"

echo "=== Ollama CLI Installer ==="
echo ""

# Check for required tools
command -v git >/dev/null 2>&1 || { echo "Error: git is required but not installed."; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "Error: curl is required but not installed."; exit 1; }

# Detect platform
PLATFORM=$(uname -s)
echo "Detected platform: $PLATFORM"

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

# Install Python dependencies
echo "Installing Python dependencies..."
uv sync

# Create .env from sample if not exists
[ ! -f .env ] && cp .env.sample .env 2>/dev/null || true

# Install Ollama if not present
echo ""
echo "=== Ollama Installation Check ==="
if command -v ollama >/dev/null 2>&1; then
    OLLAMA_INSTALLED=$(ollama --version 2>/dev/null | head -1 || echo "unknown")
    echo "Ollama is already installed: $OLLAMA_INSTALLED"
else
    echo "Ollama not found. Installing Ollama..."
    case $PLATFORM in
        Linux)
            echo "Installing Ollama for Linux..."
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
        Darwin)
            echo "Installing Ollama for macOS..."
            # Use Homebrew if available
            if command -v brew >/dev/null 2>&1; then
                brew install ollama
            else
                # Download directly
                curl -L https://github.com/ollama/ollama/releases/download/v$OLLAMA_VERSION/ollama-darwin-amd64.tar.gz | tar xz -C /usr/local/bin
            fi
            ;;
        *)
            echo "Warning: Auto-installation not supported for this platform."
            echo "Please install Ollama manually from https://ollama.ai"
            ;;
    esac
fi

# Verify Ollama installation
echo ""
echo "=== Verification ==="
if command -v ollama >/dev/null 2>&1; then
    echo "Ollama: $(ollama --version 2>/dev/null | head -1)"
else
    echo "Warning: Ollama installation failed. Please install manually from https://ollama.ai"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Add this to your shell profile (~/.bashrc or ~/.zshrc):"
echo "  alias ollama-cli='uv run $INSTALL_DIR/src/cli.py'"
echo ""
echo "Start Ollama server:"
echo "  ollama serve"
echo ""
echo "Then start chatting:"
echo "  ollama-cli interactive"
echo ""
