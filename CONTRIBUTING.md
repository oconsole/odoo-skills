# Contributing

## The three tiers

Skills are organized into three tiers so installs are isolated by capability:

- **Read** — read-only skills. NO mutating tools may appear in any allowed-tools list.
- **Write** — production write skills. Mutate state on the connected Odoo instance.
- **Demo** — sandboxed write skills. Same capabilities as write, but every artifact must carry a demo tag.

When in doubt, choose the **most restrictive tier** that still does the job.

## Adding a new skill

1. **Pick the tier.** Read, write, or demo.
2. **Create a folder at the repo root** using kebab-case: `<skill-name>/`
3. **Copy `template/SKILL.md`** as a starting point.
4. **Fill in the frontmatter.** Required: `name`, `description`. Required for this repo: `metadata.tier` set to `read`, `write`, or `demo`. The `name` field must match the folder name.
5. **Author SKILL.md per-tier rules** (see below).
6. **Add references** under `<your-skill>/references/` if your skill has more than ~200 lines of guidance.
7. **Run the validator:**

   ```bash
   bash tools/validate-skills.sh
   ```

8. **Update `README.md`** with a row in the right skills table.
9. **Open a PR.** Mention the tier in the PR title.

## Per-tier rules

### Read tier

- The `description` MUST contain "READ-ONLY" or "read-only" so the agent picks the right tier.
- The SKILL.md MUST list which Odoo MCP tools are allowed (only read tools: `odoo_search_read`, `odoo_search_count`, `odoo_get_fields`, `odoo_get_view`, `odoo_model_info`, `odoo_list_models`, `odoo_doctor`, plus `odoo_execute` constrained to read methods).
- The SKILL.md MUST list forbidden tools and what to do when the user asks for them (refer them to the write tier).
- Frontmatter: `metadata.tier: read`

### Write tier

- The SKILL.md MUST include a discovery step before any mutation.
- The SKILL.md MUST include a verify-after-write step.
- The SKILL.md MUST flag destructive operations (delete, type changes) as requiring explicit user confirmation.
- The SKILL.md MUST distinguish between what is runtime-safe and what requires a Python module (and refuse module-required ops).
- Frontmatter: `metadata.tier: write`

### Demo tier

- The SKILL.md MUST enforce demo tagging on every created or modified artifact:
  - Custom fields: `x_demo_<purpose>` (NOT plain `x_<purpose>`)
  - Views: `<model>.<viewtype>.demo.<purpose>`
  - Filters / automations / server actions: `[DEMO] <name>` prefix
- The SKILL.md MUST refuse to mutate untagged production records.
- The SKILL.md MUST include a cleanup recipe.
- Frontmatter: `metadata.tier: demo`

## Skill quality bar

A skill belongs in this registry if it:

- **Solves a recurring Odoo task** — not a one-off recipe.
- **Has a clear trigger boundary** — the description tells Claude when to load it AND when to skip it.
- **Uses Odoo MCP tools where available** — prefer `odoo_set_default`, `odoo_modify_action`, etc. over raw `odoo_update`.
- **Flags safety boundaries** — runtime-safe vs module-required, destructive vs reversible.
- **Verifies its own work** (write/demo tiers) — re-reads records after writes, reports before/after state.
- **Documents Odoo 18 vs 19 differences** in a Compatibility section if relevant.

## Frontmatter spec

```yaml
---
name: kebab-case-skill-name           # required, must match folder name
description: "Use when ... DO NOT USE WHEN ..."  # required
license: MIT                          # optional, defaults to repo license
metadata:                             # required for this repo
  author: your-name
  version: "1.0.0"
  tier: read                          # required: read | write | demo
---
```
