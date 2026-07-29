#!/bin/bash
# PostToolUse on Skill: marks gate satisfied + records loaded skill.

INPUT=$(cat)

SESSION_ID=$(printf '%s' "$INPUT" | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/"session_id":"//; s/"$//')
if [ -z "$SESSION_ID" ]; then
  exit 0
fi

touch "/tmp/claude-skill-gate-$SESSION_ID"

SKILL_NAME=$(printf '%s' "$INPUT" | grep -o '"skill":"[^"]*"' | head -1 | sed 's/"skill":"//; s/"$//')
if [ -n "$SKILL_NAME" ]; then
  # Sanitize: only allow [A-Za-z0-9_-] in the marker filename.
  SAFE_NAME=$(printf '%s' "$SKILL_NAME" | tr -cd 'A-Za-z0-9_-')
  if [ -n "$SAFE_NAME" ]; then
    touch "/tmp/claude-skill-loaded-$SESSION_ID-$SAFE_NAME"
  fi
fi

exit 0
