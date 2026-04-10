---
name: skill-name-in-kebab-case
description: "One sentence describing what this skill does. WHEN: list the user phrases or task patterns that should trigger it. DO NOT USE WHEN: list the cases where Claude should skip this skill and use something else. (For READ-tier skills, include the literal phrase READ-ONLY here.)"
license: MIT
metadata:
  author: your-name
  version: "1.0.0"
  tier: read   # or write, or demo — must match the parent skills/<tier>/ folder
---

# Skill Title

> One-paragraph summary of what this skill enables and the safety boundary it enforces.

## Triggers

Activate this skill when the user wants to:
- ...
- ...

> **Scope**: What this skill covers and what it explicitly does not cover.

## Rules

1. **Always start with discovery** — gather state before mutating
2. **Verify after every write** — re-read to confirm
3. **Confirm destructive changes** — ask before irreversible operations
4. ...

---

## Steps

| # | Action | Reference |
|---|--------|-----------|
| 1 | **Discover** — ... | [Discovery](references/discovery.md) |
| 2 | **Classify** — ... | — |
| 3 | **Execute** — ... | — |
| 4 | **Verify** — ... | — |
| 5 | **Report** — ... | — |

---

## Operation Guides

| Operation | Method | Reference |
|-----------|--------|-----------|
| ... | ... | ... |

---

## What This Skill Does Not Cover

| Operation | Why | What to suggest instead |
|-----------|-----|------------------------|
| ... | ... | ... |

## MCP Tools

| Tool | Purpose |
|------|---------|
| ... | ... |
