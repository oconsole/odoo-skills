# Odoo Skills

Agent skills for working with Odoo via [Claude Code](https://docs.claude.com/en/docs/claude-code/skills), organized into **three tiers** so the agent only has the capabilities you've explicitly granted.

These skills are produced by an RL pipeline ([SkillRL for OdooCLI](https://github.com/oconsole/odoo-skills-rl)) that distills successful agent trajectories on real Odoo tasks into reusable skill bundles.

<video src="https://odoocli.com/odoo-skills.mp4" width="100%" controls poster="https://odoocli.com/odoo-skills-poster.jpg"></video>

---

## Install

```bash
npx skills add oconsole/odoo-skills
```

This installs all skills. To install a single skill:

```bash
npx skills add oconsole/odoo-skills/odoo-model-inspect
```

---

## Skills

### Read (inspect-only, safe on production)

| Skill | Purpose |
|---|---|
| [`odoo-model-inspect`](odoo-model-inspect/) | Inspect model structure, fields, views, record counts. General-purpose read-only queries. |
| [`odoo-accounting-inspect`](odoo-accounting-inspect/) | Query invoices, bills, payments, journal entries, aged receivables. |
| [`odoo-mrp-inspect`](odoo-mrp-inspect/) | Inspect manufacturing orders, BoMs, component availability, production KPIs. |
| [`odoo-stock-inspect`](odoo-stock-inspect/) | Analyze stock levels, moves, transfers, reordering rules, reservations. |
| [`odoo-system-inspect`](odoo-system-inspect/) | System health: modules, cron jobs, error logs, user activity, dependencies. |

### Write (mutates production)

| Skill | Purpose |
|---|---|
| [`odoo-model-customize`](odoo-model-customize/) | Runtime-safe customization: defaults, sort order, custom fields, inherited views, automated actions. Knows the boundary between runtime-modifiable and module-required changes. |

### Demo (sandboxed mutations)

| Skill | Purpose |
|---|---|
| [`odoo-model-customize-demo`](odoo-model-customize-demo/) | Same as `odoo-model-customize` but every artifact is tagged `[DEMO]` / `x_demo_` / `.demo.` for clean rollback. |

---

## Tier model

| Tier | What it can do | Where it's safe |
|---|---|---|
| **Read** | Inspect models, query records, count, audit, run health checks. Guides agent toward read-only operations. | Production, staging, demo — anywhere. |
| **Write** | Set defaults, create custom fields, modify window actions, build automations. **Mutates state.** | Production only when you want changes. |
| **Demo** | Same as write, but every artifact is tagged for clean rollback. | Sandbox, demo, training instances. |

*Skills guide the agent but do not enforce permissions at the tool level. For hard read-only enforcement, configure your MCP server in read-only mode.*

---

## Compatibility

All skills are verified on **Odoo 18.0** and **Odoo 19.0**. Each `SKILL.md` includes per-version compatibility tables for field name differences.

---

## Validated effectiveness

Each `SKILL.md` carries an auto-curated **Common Pitfalls** section maintained by the [SkillRL self-edit loop](https://github.com/oconsole/odoo-skills-rl). Bullets are produced from real failed agent episodes and verified against live Odoo.

| Tier | Tasks | Odoo errors (baseline → with skill) | Tool calls | Delta |
|---|---|---|---|---|
| **Read** | 12 | **0.92 → 0.25** | 2.75 → 2.50 | **-73% errors** |
| **Write** | 6 | **1.00 → 0.33** | 5.83 → 4.17 | **-67% errors, -29% tools** |
| **Combined** | 18 | **0.94 → 0.28** | 3.78 → 3.06 | **-70% errors** |

Reproduce locally:

```bash
git clone https://github.com/oconsole/odoo-skills-rl
cd odoo-skills-rl
python3 scripts/validate_cold_start.py
```

---

## Repo layout

```
odoo-skills/
├── odoo-model-inspect/          # read — general model inspection
├── odoo-accounting-inspect/     # read — invoices, payments, journals
├── odoo-mrp-inspect/            # read — manufacturing, BoMs
├── odoo-stock-inspect/          # read — inventory, stock levels
├── odoo-system-inspect/         # read — modules, cron, logs
├── odoo-model-customize/        # write — runtime customization
├── odoo-model-customize-demo/   # demo — sandboxed customization
├── template/SKILL.md            # starter for new skills
├── tools/validate-skills.sh     # linter
├── CONTRIBUTING.md
└── LICENSE
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
