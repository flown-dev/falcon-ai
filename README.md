# Falcon AI

AI tooling and automation for the Flown team.

## Setup

Install all AI development tools with a single command:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/flown-dev/falcon-ai/main/setup-ai-tools.sh)
```

Or if you've already cloned the repo:

```bash
./setup-ai-tools.sh
```

### What gets installed

| Tool | Purpose |
|------|---------|
| [Homebrew](https://brew.sh) | macOS package manager (needed for the rest) |
| [Node.js](https://nodejs.org) | JavaScript runtime |
| [Bun](https://bun.sh) | Fast JavaScript runtime & toolkit |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Anthropic's AI coding CLI |
| [Codex](https://github.com/openai/codex) | OpenAI's AI coding CLI |
| [Cursor](https://cursor.com) | AI-powered code editor |

### After setup

Set your API keys by adding these to your shell profile (`~/.zshrc`):

```bash
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
```

Then open a new terminal window and you're good to go.
