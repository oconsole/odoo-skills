# Contributing

## The three-tier model

This repo is organized into three tiers so installs are isolated by capability:

- **`skills/read/`** — read-only skills. NO mutating tools may appear in any allowed-tools list, and the SKILL.md must explicitly forbid them.
- **`skills/write/`** — production write skills. Mutate state on the connected Odoo instance.
- **`skills/demo/`** — sandboxed write skills. Same capabilities as write, but every created/modified artifact must carry a demo tag (`[DEMO]` prefix on names, `x_demo_` prefix on custom field names, `.demo.` infix on view names).

When in doubt, choose the **most restrictive tier** that still does the job. A `read` tier skill is always preferable to a `write` tier skill if both can answer the user's question.

## Where skills come from

This registry is fed by two channels:

1. **Hand-authored skills** — written directly under `skills/<tier>/<name>/`. The read tier (`odoo-model-inspect`) and demo tier (`odoo-model-customize-demo`) skills currently come from this channel.
2. **RL-graduated skills** — produced by [SkillRL for OdooCLI](https://github.com/Mazzz-zzz/skill_rl). These live in `skill_rl/skills/<name>/` and are promoted into this registry via `tools/sync-from-rl.py`. Each promoted skill needs an entry in `sync-config.json` mapping its source folder to a target tier.

### Promoting an RL skill into this registry

```bash
# 1. Add an entry to sync-config.json mapping the source folder to a tier
#    e.g. {"odoo-new-skill": {"tier": "write", "target_name": "odoo-new-skill"}}

# 2. Dry-run the sync to see what would change
python3 tools/sync-from-rl.py

# 3. Apply
python3 tools/sync-from-rl.py --apply

# 4. Validate, commit, push
bash tools/validate-skills.sh
git add -A && git commit -m "feat: promote odoo-new-skill from RL"
git push
```

The sync script:
- Copies `SKILL.md` and `references/*.md` from skill_rl into the target tier folder
- Injects `metadata.tier: <tier>` into the frontmatter if missing
- Adds the skill path to the matching plugin's `skills` array in `marketplace.json`
- Runs `validate-skills.sh` after applying

The RL pipeline can also call the sync automatically after each generation by passing `--sync-after-evolve` to `skill_rl/run.py`. This makes the registry self-updating during long training runs.

## Adding a new skill (hand-authored)

1. **Pick the tier.** Read, write, or demo.
2. **Create the folder.** Use kebab-case under the right tier:
   - Read: `skills/read/<name>/`
   - Write: `skills/write/<name>/`
   - Demo: `skills/demo/<name>-demo/` (suffix the name with `-demo` to keep it visually distinct)
3. **Copy `template/SKILL.md`** as a starting point.
4. **Fill in the frontmatter.** Required: `name`, `description`. Required for this repo: `metadata.tier` set to `read`, `write`, or `demo`. The `name` field must match the folder name.
5. **Author SKILL.md per-tier rules** (see below).
6. **Add references** under `<your-skill>/references/` if your skill has more than ~200 lines of guidance.
7. **Run the validator:**

   ```bash
   bash tools/validate-skills.sh
   ```

8. **Register in `marketplace.json`.** Add the skill path to the matching plugin's `skills` array — `odoo-skills-read`, `odoo-skills-write`, or `odoo-skills-demo`. **Never list a skill under multiple plugins.**
9. **Update `README.md`** with a row in the right "Skills by tier" table.
10. **Open a PR.** Mention the tier in the PR title.

## Per-tier rules

### Read tier (`skills/read/`)

- The `description` MUST contain "READ-ONLY" or "read-only" so the agent picks the right tier.
- The SKILL.md MUST list which Odoo MCP tools are allowed (only read tools: `odoo_search_read`, `odoo_search_count`, `odoo_get_fields`, `odoo_get_view`, `odoo_model_info`, `odoo_list_models`, `odoo_doctor`, plus `odoo_execute` constrained to read methods).
- The SKILL.md MUST list forbidden tools and what to do when the user asks for them (refer them to the write tier).
- Frontmatter: `metadata.tier: read`

### Write tier (`skills/write/`)

- The SKILL.md MUST include a discovery step before any mutation.
- The SKILL.md MUST include a verify-after-write step.
- The SKILL.md MUST flag destructive operations (delete, type changes) as requiring explicit user confirmation.
- The SKILL.md MUST distinguish between what is runtime-safe and what requires a Python module (and refuse module-required ops).
- Frontmatter: `metadata.tier: write`

### Demo tier (`skills/demo/`)

- The SKILL.md MUST enforce demo tagging on every created or modified artifact:
  - Custom fields: `x_demo_<purpose>` (NOT plain `x_<purpose>`)
  - Views: `<model>.<viewtype>.demo.<purpose>`
  - Filters / automations / server actions: `[DEMO] <name>` prefix
- The SKILL.md MUST refuse to mutate untagged production records.
- The SKILL.md MUST refuse to modify shared `ir.actions.act_window` records (they leak into production).
- The SKILL.md MUST include a cleanup recipe at the end that finds all demo artifacts and (with confirmation) removes them in dependency order.
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
