# Odoo Skills

Companion agent skills for Odoo MCP clients, organized into read, write and demo tiers. Skills guide behavior; OAuth scopes and Odoo permissions enforce access.

Version 1.1 adds account connection selection and everyday record work. Domain recipes inherited from [SkillRL for OdooCLI](https://github.com/oconsole/odoo-skills-rl) remain available as optional references.

![Odoo Skills Overview](odoo-skills.gif)

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

## Account connections and efficient loading

For hosted OConsole, connect once at `https://mcp.odooconsole.com/mcp` and choose **Connect my account**. Skills use `get_context`, retain the active instance per connection, and require `context_version` for default-target writes. Explicit overrides and fixed-instance/local connectors remain supported. A stale version requires re-reading the target records, not just replacing the version.

Load the entrypoint for the current task; load only relevant references. Independent single-skill installs contain their own connection rules and references. Instance management is separate from everyday record work and from developer configuration. Recipes/examples in references inherit the entrypoint's current connection rules; trust live tool schemas over older examples.

The marketplace keeps `odoo-inspect` and `odoo-customize`, and adds `odoo-work` and `odoo-account`; their skill lists stay separate. Updating the hosted MCP server does not update a client's downloaded skills. Reinstall/update the package in that client to obtain v1.1.

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
| [`odoo-record-work`](odoo-record-work/) | Everyday contacts, sales and task queries and authorized record changes. |
| [`odoo-instance-manage`](odoo-instance-manage/) | Account selection, instance lifecycle, app presets and demo data. |
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

The inherited domain recipes contain Odoo 18/19 compatibility notes; they have not all been revalidated live for this release. Hosted instance creation currently offers Odoo 19. Use discovered capabilities for fixed-instance/local servers, which may not have account tools.

---

## Historical RL results

These are previously reported RL results, not measurements of v1.1 or of the new connection flow. The inherited pitfalls now live in optional guides. The training snapshots in the RL repository remain unchanged. Structure/token checks for v1.1 do not establish model task-success rates.

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
├── odoo-record-work/           # write — everyday operations
├── odoo-instance-manage/       # write — hosted account and lifecycle
├── odoo-model-customize/        # write — runtime customization
├── odoo-model-customize-demo/   # demo — sandboxed customization
├── template/SKILL.template.md            # starter for new skills
├── tools/validate-skills.sh     # linter
├── CONTRIBUTING.md
└── LICENSE
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
