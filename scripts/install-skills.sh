#!/usr/bin/env bash
# Install Claude-only skill + slash command wrappers for AgentSuite.
# Per `feedback_skills_always_get_slash_command.md`: paired install only.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
SKILLS_DIR="$CLAUDE_HOME/skills"
COMMANDS_DIR="$CLAUDE_HOME/commands"

mkdir -p "$SKILLS_DIR/founder-agent" "$SKILLS_DIR/design-agent" "$SKILLS_DIR/product-agent" "$COMMANDS_DIR"

cp "$REPO_ROOT/claude/skills/founder-agent/SKILL.md" "$SKILLS_DIR/founder-agent/SKILL.md"
cp "$REPO_ROOT/claude/skills/founder-agent/mcp-snippet.json" "$SKILLS_DIR/founder-agent/mcp-snippet.json"
cp "$REPO_ROOT/claude/commands/founder-agent.md" "$COMMANDS_DIR/founder-agent.md"

cp "$REPO_ROOT/claude/skills/design-agent/SKILL.md" "$SKILLS_DIR/design-agent/SKILL.md"
cp "$REPO_ROOT/claude/skills/design-agent/mcp-snippet.json" "$SKILLS_DIR/design-agent/mcp-snippet.json"
cp "$REPO_ROOT/claude/commands/design-agent.md" "$COMMANDS_DIR/design-agent.md"

cp "$REPO_ROOT/claude/skills/product-agent/SKILL.md" "$SKILLS_DIR/product-agent/SKILL.md"
cp "$REPO_ROOT/claude/skills/product-agent/mcp-snippet.json" "$SKILLS_DIR/product-agent/mcp-snippet.json"
echo "  [OK] product-agent skill installed"

echo "Installed:"
echo "  - $SKILLS_DIR/founder-agent/SKILL.md"
echo "  - $SKILLS_DIR/founder-agent/mcp-snippet.json"
echo "  - $COMMANDS_DIR/founder-agent.md"
echo "  - $SKILLS_DIR/design-agent/SKILL.md"
echo "  - $SKILLS_DIR/design-agent/mcp-snippet.json"
echo "  - $COMMANDS_DIR/design-agent.md"
echo "  - $SKILLS_DIR/product-agent/SKILL.md"
echo "  - $SKILLS_DIR/product-agent/mcp-snippet.json"
echo ""
echo "Restart Claude Code for the skill + slash command to be visible."
