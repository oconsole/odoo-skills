#!/usr/bin/env bash
# validate-skills.sh — lint every <skill>/SKILL.md at the repo root.
#
# Layout:
#   <skill-name>/SKILL.md
#
# Required frontmatter fields per skill:
#   - name        (must match folder name)
#   - description (must be non-empty)
#   - metadata.tier (must be: read | write | demo)
#
# Per-tier content rules:
#   - read tier: SKILL.md must contain a "READ-ONLY" / "read-only" marker
#   - demo tier: SKILL.md must contain "[DEMO]" tagging convention
#
# Exit code: 0 if all skills pass, 1 if any fail.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Directories to skip (not skills)
SKIP_DIRS="template tools"

fail_count=0
pass_count=0

validate_skill() {
  local skill_dir="$1"
  local skill_name
  skill_name="$(basename "$skill_dir")"
  local skill_md="$skill_dir/SKILL.md"

  if [ ! -f "$skill_md" ]; then
    echo "FAIL  $skill_name — missing SKILL.md"
    fail_count=$((fail_count + 1))
    return
  fi

  local frontmatter
  frontmatter="$(awk '/^---$/{c++; next} c==1' "$skill_md")"

  if [ -z "$frontmatter" ]; then
    echo "FAIL  $skill_name — no frontmatter block"
    fail_count=$((fail_count + 1))
    return
  fi

  local name_field desc_field tier_field
  name_field="$(echo "$frontmatter" | awk -F': *' '/^name:/ {print $2; exit}' | tr -d '"' | tr -d "'")"
  desc_field="$(echo "$frontmatter" | awk -F': *' '/^description:/ {print $2; exit}')"
  tier_field="$(echo "$frontmatter" | awk -F': *' '/^  tier:/ {print $2; exit}' | tr -d '"' | tr -d "'")"

  local errors=""

  if [ -z "$name_field" ]; then
    errors="$errors\n  - missing 'name' field"
  elif [ "$name_field" != "$skill_name" ]; then
    errors="$errors\n  - name '$name_field' does not match folder '$skill_name'"
  fi

  if [ -z "$desc_field" ]; then
    errors="$errors\n  - missing 'description' field"
  fi

  if [ -z "$tier_field" ]; then
    errors="$errors\n  - missing 'metadata.tier' field"
  elif [ "$tier_field" != "read" ] && [ "$tier_field" != "write" ] && [ "$tier_field" != "demo" ]; then
    errors="$errors\n  - metadata.tier '$tier_field' must be read, write, or demo"
  fi

  # Tier-specific content rules
  case "$tier_field" in
    read)
      if ! grep -qiE "(READ-ONLY|read-only)" "$skill_md"; then
        errors="$errors\n  - read-tier skill must contain READ-ONLY marker in SKILL.md"
      fi
      ;;
    demo)
      if ! grep -qE "\[DEMO\]" "$skill_md"; then
        errors="$errors\n  - demo-tier skill must reference [DEMO] tagging convention"
      fi
      if ! grep -qE "x_demo_" "$skill_md"; then
        errors="$errors\n  - demo-tier skill must reference x_demo_ field prefix"
      fi
      ;;
  esac

  if [ -n "$errors" ]; then
    echo "FAIL  $skill_name"
    printf "$errors\n"
    fail_count=$((fail_count + 1))
  else
    echo "PASS  $skill_name"
    pass_count=$((pass_count + 1))
  fi
}

for skill_dir in "$REPO_ROOT"/odoo-*/; do
  [ -d "$skill_dir" ] || continue
  validate_skill "$skill_dir"
done

echo
echo "Results: $pass_count passed, $fail_count failed"

if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
