#!/bin/bash
# PreToolUse gate: forces skill evaluation before file-writing tools run.

INPUT=$(cat)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

if ! find "$PROJECT_DIR" -path '*/.claude/skills/*/SKILL.md' 2>/dev/null | grep -q .; then
  exit 0
fi

SESSION_ID=$(printf '%s' "$INPUT" | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/"session_id":"//; s/"$//')
if [ -z "$SESSION_ID" ]; then
  exit 0
fi

MARKER="/tmp/claude-skill-gate-$SESSION_ID"
if [ -f "$MARKER" ]; then
  exit 0
fi

cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"BLOCKED: skill evaluation required before file edits in this session.\n\nStep 1 — evaluate every available skill as ACTIVATE or SKIP with a one-line reason.\n\nStep 2 — you MUST take EXACTLY ONE of these tool actions to clear the gate. Listing skills in text is NOT enough; retrying the edit without doing one of these will be denied again:\n  (a) If any skill is ACTIVATE → call Skill(name) for it. This auto-clears the gate.\n  (b) If ALL skills are SKIP → run this Bash tool call: touch /tmp/claude-skill-gate-$SESSION_ID\n\nStep 3 — only after Step 2 completes, retry the file edit."}}
EOF
exit 0
