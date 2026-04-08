#!/usr/bin/env bash
# validate-skills.sh — lint every skills/<tier>/<skill>/SKILL.md.
#
# Layout:
#   skills/read/<skill>/SKILL.md
#   skills/write/<skill>/SKILL.md
#   skills/demo/<skill>/SKILL.md
#
# Required frontmatter fields per skill:
#   - name        (must match folder name)
#   - description (must be non-empty)
#   - metadata.tier (must match parent tier folder: read | write | demo)
#
# Per-tier content rules:
#   - read tier: SKILL.md must contain a "READ-ONLY" / "read-only" marker
#   - demo tier: SKILL.md must contain "[DEMO]" tagging convention
#
# Marketplace cross-check:
#   - Each skill folder must be referenced by EXACTLY ONE plugin in
#     .claude-plugin/marketplace.json (no skill listed under multiple tiers)
#
# Exit code: 0 if all skills pass, 1 if any fail.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "ERROR: $SKILLS_DIR does not exist"
  exit 1
fi

fail_count=0
pass_count=0

validate_skill() {
  local tier="$1"
  local skill_dir="$2"
  local skill_name
  skill_name="$(basename "$skill_dir")"
  local skill_md="$skill_dir/SKILL.md"
  local label="$tier/$skill_name"

  if [ ! -f "$skill_md" ]; then
    echo "FAIL  $label — missing SKILL.md"
    fail_count=$((fail_count + 1))
    return
  fi

  local frontmatter
  frontmatter="$(awk '/^---$/{c++; next} c==1' "$skill_md")"

  if [ -z "$frontmatter" ]; then
    echo "FAIL  $label — no frontmatter block"
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
  elif [ "$tier_field" != "$tier" ]; then
    errors="$errors\n  - metadata.tier '$tier_field' does not match folder '$tier'"
  fi

  # Tier-specific content rules
  case "$tier" in
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

  # Marketplace cross-check
  if [ -f "$MARKETPLACE" ]; then
    local rel_path="./skills/$tier/$skill_name"
    local plugin_count
    plugin_count="$(grep -c "\"$rel_path\"" "$MARKETPLACE" || true)"
    if [ "$plugin_count" -eq 0 ]; then
      errors="$errors\n  - not registered in marketplace.json (expected '$rel_path')"
    elif [ "$plugin_count" -gt 1 ]; then
      errors="$errors\n  - registered in marketplace.json $plugin_count times — must be exactly one tier"
    fi
  fi

  if [ -n "$errors" ]; then
    echo "FAIL  $label"
    printf "$errors\n"
    fail_count=$((fail_count + 1))
  else
    echo "PASS  $label"
    pass_count=$((pass_count + 1))
  fi
}

for tier in read write demo; do
  tier_dir="$SKILLS_DIR/$tier"
  if [ ! -d "$tier_dir" ]; then
    continue
  fi
  for skill_dir in "$tier_dir"/*/; do
    [ -d "$skill_dir" ] || continue
    validate_skill "$tier" "$skill_dir"
  done
done

# Detect orphan skills directly under skills/ (legacy flat layout)
for legacy in "$SKILLS_DIR"/*/; do
  [ -d "$legacy" ] || continue
  base="$(basename "$legacy")"
  case "$base" in
    read|write|demo) continue ;;
    *)
      echo "FAIL  $base — found at skills/$base, must move under skills/{read,write,demo}/"
      fail_count=$((fail_count + 1))
      ;;
  esac
done

echo
echo "Results: $pass_count passed, $fail_count failed"

if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
