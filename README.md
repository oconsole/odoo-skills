# Odoo Skills

A registry of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) for working with Odoo, organized into **three install-isolated tiers** so the agent only has the capabilities you've explicitly granted.

These skills are produced by an RL pipeline ([SkillRL for OdooCLI](https://github.com/Mazzz-zzz/skill_rl)) that distills successful agent trajectories on real Odoo tasks into reusable skill bundles.

---

## The three tiers

| Tier | Plugin | What it can do | Where it's safe |
|---|---|---|---|
| **Read** | `odoo-skills-read` | Inspect models, query records, count, audit, run health checks. **No mutating tools loaded.** | Production, staging, demo — anywhere. The agent has no path to change state. |
| **Write** | `odoo-skills-write` | Set defaults, create custom fields, modify window actions, build automations. **Mutates state.** | Production only when you actually want changes. Treat as production tooling. |
| **Demo** | `odoo-skills-demo` | Same capabilities as write, but every artifact is tagged `[DEMO]` / `x_demo_` / `.demo.` for clean rollback. | Sandbox, demo, training Odoo instances. Tagging makes it findable and removable. |

**Why three plugins instead of one?** A user who installs only `odoo-skills-read` is structurally guaranteed that no skill in their Claude Code session knows how to mutate Odoo state. The dangerous capabilities are gated behind a separate install. This is the same model as Unix file permissions: capability separation enforced at install time, not just at runtime.

---

## Install

Add this repo as a Claude Code plugin marketplace once:

```bash
/plugin marketplace add oconsole/odoo-skills
```

Then install **only** the tier(s) you want:

```bash
# Read-only — safe on production
/plugin install odoo-skills-read@odoo-skills

# Write — only when you want real mutations on the connected Odoo
/plugin install odoo-skills-write@odoo-skills

# Demo — for sandbox / training instances
/plugin install odoo-skills-demo@odoo-skills
```

You can install **read** alongside **demo** for a safe prototyping setup. You can install **read** alongside **write** for full production tooling. Installing all three is supported but not recommended on production — pick read+write or read+demo per environment.

---

## Skills by tier

### `odoo-skills-read` (read-only)

| Skill | Purpose |
|---|---|
| [`odoo-model-inspect`](skills/read/odoo-model-inspect/) | Inspect models, query records, audit data quality, run diagnostics. Hard-locked to read-only tools. |

### `odoo-skills-write` (mutates production)

| Skill | Purpose |
|---|---|
| [`odoo-model-customize`](skills/write/odoo-model-customize/) | Runtime-safe model customization: defaults, sort order, custom fields, inherited views, automated actions. Knows the boundary between runtime-modifiable and module-required changes. |

### `odoo-skills-demo` (sandboxed mutations)

| Skill | Purpose |
|---|---|
| [`odoo-model-customize-demo`](skills/demo/odoo-model-customize-demo/) | Same as `odoo-model-customize` but every artifact is tagged for cleanup. Includes a cleanup recipe. |

---

## Compatibility

All skills are verified on **Odoo 18.0** and **Odoo 19.0**. Each skill's `SKILL.md` includes a per-version compatibility table calling out the small schema differences between the two versions and the fields the LLM commonly invents that exist in neither.

---

## Validated effectiveness

Each `SKILL.md` carries an auto-curated **Common Pitfalls** section maintained by the [SkillRL self-edit loop](https://github.com/oconsole/odoo-skills-rl). The bullets are produced from real failed agent episodes, verified against live Odoo (positive field-name claims must exist on the named model), and pruned by a cold-start validation harness.

A fresh agent loading only `SKILL.md` (no skill bank, no RL training) was measured against the same agent with no skill content on **18 held-out tasks** that the curation has never seen. Tasks were split across both tiers and probed specific bullet classes (`installed_version` vs `version`, `move_type` vs `type`, CRM-uninstalled fallback, MRP date-field naming, ir.default schema, etc.).

| Tier | Tasks | Mean Odoo errors (baseline → with SKILL.md) | Mean tool calls | Delta |
|---|---|---|---|---|
| **Read** | 12 | **0.92 → 0.25** | 2.75 → 2.50 | **−73% errors** |
| **Write** | 6 | **1.00 → 0.33** | 5.83 → 4.17 | **−67% errors, −29% tools** |
| **Combined** | 18 | **0.94 → 0.28** | 3.78 → 3.06 | **−70% errors** |

Completion rate stayed at 100% in both modes — the skill doesn't help the agent finish more tasks, it helps it finish them with fewer wrong tool calls. Reproduce locally:

```bash
git clone https://github.com/oconsole/odoo-skills-rl
cd odoo-skills-rl
python3 scripts/validate_cold_start.py            # both tiers, side-by-side report
python3 scripts/validate_cold_start.py --tier read --jsonl out.jsonl
```

The harness also actively prunes the curation: any bullet that the with-skill agent followed and made things *worse* gets retired. This is how we caught and removed the over-conservative `qty_available` and `stock.quant.qty_available` bullets — the validator proved they were misleading by running the agent both ways.

---

## Repo layout

```
odoo-skills/
├── .claude-plugin/marketplace.json  # 3 plugins: read, write, demo
├── skills/
│   ├── read/                         # safe — installs grant inspection only
│   │   └── odoo-model-inspect/
│   ├── write/                        # mutates production
│   │   └── odoo-model-customize/
│   └── demo/                         # mutates with [DEMO] tagging
│       └── odoo-model-customize-demo/
├── template/SKILL.md                 # starter for new skills
├── tools/validate-skills.sh          # tier-aware linter
├── CONTRIBUTING.md
└── LICENSE
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills must declare their tier and pass `tools/validate-skills.sh`.

## License

MIT — see [LICENSE](LICENSE).
