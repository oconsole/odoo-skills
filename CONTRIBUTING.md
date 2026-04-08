# Contributing

## Adding a new skill

1. Copy `template/SKILL.md` into a new folder under `skills/<your-skill-name>/`.
2. Use kebab-case for the folder name. The folder name must match the `name` field in frontmatter.
3. Fill in the frontmatter — `name` and `description` are required. The `description` is what Claude reads to decide whether to load your skill, so be specific about *when* it should be used and *when not*.
4. Add deep-dive docs under `skills/<your-skill-name>/references/` if your skill has more than ~200 lines of guidance. Keep `SKILL.md` itself focused on triggers, rules, and a step table.
5. Run the validator:

   ```bash
   bash tools/validate-skills.sh
   ```

6. Open a PR. Include in the PR description:
   - What Odoo task the skill enables
   - Example user prompts that should trigger it
   - Whether the skill came from the SkillRL pipeline (and if so, which run / reward range)

## Skill quality bar

A skill belongs in this registry if it:

- **Solves a recurring Odoo task** — not a one-off recipe
- **Has a clear trigger boundary** — the description tells Claude when to load it AND when to skip it
- **Uses Odoo MCP tools where available** — prefer `odoo_set_default`, `odoo_modify_action`, etc. over raw `odoo_update`
- **Flags safety boundaries** — runtime-safe vs module-required, destructive vs reversible
- **Verifies its own work** — re-reads records after writes, reports before/after state

## Frontmatter spec

```yaml
---
name: kebab-case-skill-name           # required, must match folder name
description: "Use when ... DO NOT USE WHEN ..."  # required
license: MIT                          # optional, defaults to repo license
metadata:                             # optional
  author: your-name
  version: "1.0.0"
---
```
