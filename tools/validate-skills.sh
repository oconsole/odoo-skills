#!/usr/bin/env bash
# validate-skills.sh — lint every skills/*/SKILL.md for required frontmatter.
#
# Required fields: name, description
# Rules:
#   - SKILL.md must exist in each skills/* directory
#   - Frontmatter must be delimited by --- on its own lines
#   - name must match the parent directory name
#   - description must be present and non-empty
#
# Exit code: 0 if all skills pass, 1 if any fail.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "ERROR: $SKILLS_DIR does not exist"
  exit 1
fi

fail_count=0
pass_count=0

for skill_dir in "$SKILLS_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  skill_md="$skill_dir/SKILL.md"

  if [ ! -f "$skill_md" ]; then
    echo "FAIL  $skill_name — missing SKILL.md"
    fail_count=$((fail_count + 1))
    continue
  fi

  # Extract frontmatter (lines between first two --- delimiters)
  frontmatter="$(awk '/^---$/{c++; next} c==1' "$skill_md")"

  if [ -z "$frontmatter" ]; then
    echo "FAIL  $skill_name — no frontmatter block"
    fail_count=$((fail_count + 1))
    continue
  fi

  name_field="$(echo "$frontmatter" | awk -F': *' '/^name:/ {print $2; exit}' | tr -d '"' | tr -d "'")"
  desc_field="$(echo "$frontmatter" | awk -F': *' '/^description:/ {print $2; exit}')"

  errors=""

  if [ -z "$name_field" ]; then
    errors="$errors\n  - missing 'name' field"
  elif [ "$name_field" != "$skill_name" ]; then
    errors="$errors\n  - name '$name_field' does not match folder '$skill_name'"
  fi

  if [ -z "$desc_field" ]; then
    errors="$errors\n  - missing 'description' field"
  fi

  if [ -n "$errors" ]; then
    echo "FAIL  $skill_name"
    printf "$errors\n"
    fail_count=$((fail_count + 1))
  else
    echo "PASS  $skill_name"
    pass_count=$((pass_count + 1))
  fi
done

echo
echo "Results: $pass_count passed, $fail_count failed"

if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
