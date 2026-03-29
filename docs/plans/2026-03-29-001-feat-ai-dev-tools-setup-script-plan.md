---
title: "feat: AI dev tools setup script for team onboarding"
type: feat
status: completed
date: 2026-03-29
---

# AI Dev Tools Setup Script

## Overview

Create a single shell script that installs all necessary AI development tools on macOS so any team member — including non-technical ones — can get set up with minimal effort and no prior terminal knowledge.

## Problem Frame

The team needs to use AI coding tools (Claude Code, Codex) and run MCPs, but setting up Node.js, Bun, and CLI tools manually is error-prone and intimidating for non-developers. A one-command setup script removes this barrier.

## Requirements Trace

- R1. Single script installs: Homebrew (if missing), Node.js, Bun, Claude Code, Codex, Cursor IDE
- R2. Idempotent — safe to re-run; skips tools already installed
- R3. Non-techie friendly — clear colored output, progress messages, no jargon
- R4. Minimal user interaction — only confirm at the start, then hands-off
- R5. macOS only (Intel and Apple Silicon)
- R6. Runnable with a single copy-paste command from a README

## Scope Boundaries

- No Linux or Windows/WSL support
- No version pinning or version manager (nvm/fnm) — Homebrew's latest Node LTS is sufficient
- No project-specific setup (Python venv, repo cloning, etc.) — just the shared AI tooling
- No automatic API key configuration — the script tells users what to do next

## Key Technical Decisions

- **Homebrew as foundation**: The standard macOS package manager. Most team members may already have it. Installing it first unlocks Node and Bun via simple `brew install` commands.
- **Node via Homebrew (`brew install node`)**: Simplest path for non-techies. No version manager complexity. LTS is fine for running CLI tools.
- **Bun via Homebrew (`brew install oven-sh/bun/bun`)**: Consistent with the Homebrew-first approach. Alternative is the official curl installer, but Homebrew keeps everything in one ecosystem.
- **Claude Code via npm (`npm install -g @anthropic-ai/claude-code`)**: Official installation method.
- **Codex via npm (`npm install -g @openai/codex`)**: Official installation method.
- **Cursor via Homebrew Cask (`brew install --cask cursor`)**: Installs the desktop app cleanly. Homebrew Cask handles the `.dmg` download, extraction, and placement in `/Applications` — no manual drag-and-drop needed.
- **Bash script (not zsh)**: `#!/bin/bash` is more portable and conventional for install scripts, even on macOS where zsh is the default shell. Bash is always available on macOS.
- **Single confirmation prompt at start**: Show what will be installed, ask for a single "Continue? [Y/n]" confirmation, then run everything without further interaction.

## Open Questions

### Resolved During Planning

- **Node version manager vs Homebrew?** Homebrew direct — simpler for non-techies, no shell config modification needed. Version managers add complexity with no benefit when the goal is just running CLI tools.
- **How should users run the script?** `curl | bash` one-liner from the README for maximum simplicity, with the script also available to run locally from the repo.

### Deferred to Implementation

- **Exact Homebrew tap path for Bun**: Verify whether `brew install bun` works directly now or still needs `oven-sh/bun/bun` tap.
- **npm global install permissions**: May need to check if `npm install -g` works without sudo on Homebrew-installed Node (it should, but verify).

## Implementation Units

- [ ] **Unit 1: Create the setup script**

  **Goal:** A single `setup-ai-tools.sh` script that installs all tools with clear, friendly output.

  **Requirements:** R1, R2, R3, R4, R5

  **Dependencies:** None

  **Files:**
  - Create: `setup-ai-tools.sh`

  **Approach:**
  - Start with a banner and summary of what will be installed
  - Single "Continue? [Y/n]" prompt
  - For each tool: check if already installed (`command -v`), skip with a success message if present, install if missing
  - Installation order: Homebrew -> Node -> Bun -> Claude Code -> Codex -> Cursor (Homebrew must be first; Node before npm-based tools; Cursor last as it's independent)
  - Use colored output (green checkmarks for success, yellow for skipping, red for errors)
  - End with a "Next steps" section telling users to set up their API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)
  - Make script executable (`chmod +x`)

  **Patterns to follow:**
  - Homebrew's own install script pattern (friendly, minimal interaction)
  - Use `set -e` for fail-fast behavior
  - Trap errors to show a friendly message instead of raw shell errors

  **Test scenarios:**
  - Fresh macOS with nothing installed — all tools install in order
  - macOS with Homebrew and Node already present — those are skipped, Bun/Claude/Codex install
  - All tools already installed — script completes instantly with all "already installed" messages
  - No internet connection — script fails with clear error message
  - User declines the confirmation prompt — script exits cleanly

  **Verification:**
  - Running `./setup-ai-tools.sh` on a clean macOS installs all 6 tools
  - Running it again skips everything and shows success
  - `claude --version`, `codex --version`, `node --version`, `bun --version` all work after the script completes
  - Cursor appears in `/Applications` and can be launched

- [ ] **Unit 2: Add README instructions**

  **Goal:** Document the one-liner command to run the script and what it does.

  **Requirements:** R6

  **Dependencies:** Unit 1

  **Files:**
  - Create or modify: `README.md` (root level)

  **Approach:**
  - Add a "Getting Started" or "Setup" section
  - Include the copy-paste one-liner: `curl -fsSL <raw-github-url> | bash` (or `bash <(curl -fsSL <url>)`)
  - Also document the local alternative: `./setup-ai-tools.sh`
  - List what gets installed and the "Next steps" for API key setup
  - Keep it short — the script itself provides detailed output

  **Test scenarios:**
  - A non-technical team member can follow the README and get set up

  **Verification:**
  - README contains clear, copy-pasteable instructions
  - The curl one-liner URL points to the correct raw GitHub file

## Risks & Dependencies

- **Xcode Command Line Tools**: Homebrew installation triggers Xcode CLT install if missing, which can take a while. The script should warn about this upfront.
- **Corporate proxy/VPN**: Some team members may be behind a proxy that blocks Homebrew or npm. Out of scope for the script, but the error message should suggest checking network access.
- **npm global permissions**: Homebrew-installed Node should allow `npm install -g` without sudo, but if something goes wrong, the error should be clear.

## Sources & References

- Homebrew install: `https://brew.sh`
- Claude Code npm: `@anthropic-ai/claude-code`
- Codex npm: `@openai/codex`
- Bun install: `https://bun.sh`
- Cursor: `https://cursor.com` (Homebrew cask: `cursor`)
