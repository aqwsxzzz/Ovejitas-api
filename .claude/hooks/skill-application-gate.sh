#!/bin/bash
# PreToolUse application gate: blocks file edits until each loaded skill
# has been explicitly applied (acked) for this session.

INPUT=$(cat)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

SESSION_ID=$(printf '%s' "$INPUT" | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/"session_id":"//; s/"$//')
if [ -z "$SESSION_ID" ]; then
  exit 0
fi

# Defer to the loading gate until it's been satisfied this session.
if [ ! -f "/tmp/claude-skill-gate-$SESSION_ID" ]; then
  exit 0
fi

# Find the first loaded-but-unacked skill (handle one at a time; the next
# blocked write will surface the next skill).
UNACKED=""
for marker in /tmp/claude-skill-loaded-$SESSION_ID-*; do
  [ ! -f "$marker" ] && continue
  skill_name="${marker##/tmp/claude-skill-loaded-$SESSION_ID-}"
  if [ ! -f "/tmp/claude-skill-acked-$SESSION_ID-$skill_name" ]; then
    UNACKED="$skill_name"
    break
  fi
done

if [ -z "$UNACKED" ]; then
  exit 0
fi

SKILL_MD="$PROJECT_DIR/.claude/skills/$UNACKED/SKILL.md"
RULES=""
if [ -f "$SKILL_MD" ]; then
  RULES=$(awk '/^## Rules/{flag=1} /^## /{if(flag && !/^## Rules/)exit} flag' "$SKILL_MD")
fi
if [ -z "$RULES" ]; then
  RULES="(Rules section not found in $SKILL_MD — refer to the loaded skill content already in context.)"
fi

MSG="BLOCKED: skill '$UNACKED' was loaded but not yet applied to your work.

Before this Write/Edit, you must:

1. State the specific rules from '$UNACKED' that apply to the file you're about to write.
2. State how your next write respects each rule.
3. Then ack the application by running this Bash tool call:
     touch /tmp/claude-skill-acked-$SESSION_ID-$UNACKED

One ack per skill per session. After acking, retry the Write/Edit.

Rules from $UNACKED/SKILL.md:

$RULES"

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '"%s"' "$s"
}

REASON=$(json_escape "$MSG")
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' "$REASON"
exit 0
