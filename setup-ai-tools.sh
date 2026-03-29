#!/bin/bash
set -euo pipefail

# ──────────────────────────────────────────────
# AI Dev Tools Setup Script
# Installs everything your team needs to develop with AI
# ──────────────────────────────────────────────

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Helpers
info()    { echo -e "${BLUE}ℹ${NC}  $1"; }
success() { echo -e "${GREEN}✔${NC}  $1"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $1"; }
fail()    { echo -e "${RED}✖${NC}  $1"; exit 1; }

trap 'echo ""; fail "Something went wrong. Check the output above for details."' ERR

# Parse flags
AUTO_APPROVE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) AUTO_APPROVE=true; shift ;;
    *) shift ;;
  esac
done

# ──────────────────────────────────────────────
# Welcome banner
# ──────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       AI Dev Tools — Team Setup Script       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "This script will install the following tools:"
echo ""
echo "  1. Homebrew     — macOS package manager"
echo "  2. Node.js      — JavaScript runtime"
echo "  3. Bun          — Fast JavaScript runtime & toolkit"
echo "  4. Claude Code  — Anthropic's AI coding CLI"
echo "  5. Codex        — OpenAI's AI coding CLI"
echo "  6. Cursor       — AI-powered code editor"
echo ""
echo -e "${YELLOW}Note:${NC} If Homebrew needs to install Xcode Command Line Tools,"
echo "      that step may take several minutes. This is normal."
echo ""

# ──────────────────────────────────────────────
# Confirm
# ──────────────────────────────────────────────
if [[ "$AUTO_APPROVE" != true ]]; then
  read -r -p "Continue with installation? [Y/n] " response
  response=${response:-Y}
  if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo ""
    info "Installation cancelled. No changes were made."
    exit 0
  fi
fi

echo ""

# ──────────────────────────────────────────────
# 1. Homebrew
# ──────────────────────────────────────────────
if command -v brew &>/dev/null; then
  success "Homebrew is already installed"
else
  info "Installing Homebrew..."
  NONINTERACTIVE=1 /bin/bash -c "$(curl --connect-timeout 10 --max-time 120 -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # Add Homebrew to PATH for the rest of this script
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -f /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi

  success "Homebrew installed"
fi

# ──────────────────────────────────────────────
# 2. Node.js
# ──────────────────────────────────────────────
if command -v node &>/dev/null; then
  success "Node.js is already installed ($(node --version))"
else
  info "Installing Node.js..."
  brew install node
  success "Node.js installed ($(node --version))"
fi

# ──────────────────────────────────────────────
# 3. Bun
# ──────────────────────────────────────────────
if command -v bun &>/dev/null; then
  success "Bun is already installed ($(bun --version))"
else
  info "Installing Bun..."
  brew install bun
  success "Bun installed ($(bun --version))"
fi

# ──────────────────────────────────────────────
# 4. Claude Code
# ──────────────────────────────────────────────
if command -v claude &>/dev/null; then
  success "Claude Code is already installed ($(claude --version 2>/dev/null || echo 'unknown'))"
else
  info "Installing Claude Code..."
  npm install -g @anthropic-ai/claude-code
  success "Claude Code installed"
fi

# ──────────────────────────────────────────────
# 5. Codex
# ──────────────────────────────────────────────
if command -v codex &>/dev/null; then
  success "Codex is already installed ($(codex --version 2>/dev/null || echo 'unknown'))"
else
  info "Installing Codex..."
  npm install -g @openai/codex
  success "Codex installed"
fi

# ──────────────────────────────────────────────
# 6. Cursor
# ──────────────────────────────────────────────
if [[ -d "/Applications/Cursor.app" ]] || command -v cursor &>/dev/null; then
  success "Cursor is already installed"
else
  info "Installing Cursor..."
  brew install --cask cursor
  success "Cursor installed"
fi

# ──────────────────────────────────────────────
# Done!
# ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  All tools installed successfully!${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo "  1. Set up your API keys:"
echo "     Create a file at ~/.config/ai-keys.env with:"
echo ""
echo "     ANTHROPIC_API_KEY=your-key-here"
echo "     OPENAI_API_KEY=your-key-here"
echo ""
echo "     Then add this to your shell profile (~/.zshrc or ~/.bashrc):"
echo "     source ~/.config/ai-keys.env"
echo "     Tip: run 'chmod 600 ~/.config/ai-keys.env' to restrict access."
echo ""
echo "  2. Try your new tools:"
echo "     claude        — Start Claude Code"
echo "     codex         — Start Codex"
echo "     cursor .      — Open current folder in Cursor"
echo ""
echo "  3. Open a new terminal tab/window for the tools to be available."
echo ""
