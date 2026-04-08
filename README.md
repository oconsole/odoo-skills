# Odoo Skills

A registry of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) for working with Odoo. Each skill bundles a focused capability — runtime model customization, ORM queries, view inheritance, deployment recipes — that Claude Code can load on demand.

These skills are produced by an RL pipeline ([SkillRL for OdooCLI](https://github.com/Mazzz-zzz/skill_rl)) that distills successful agent trajectories on real Odoo tasks into reusable skill bundles. New skills are added here once they graduate from the training loop.

## Install

Add this repo as a Claude Code plugin marketplace:

```bash
/plugin marketplace add oconsole/odoo-skills
/plugin install odoo-skills@odoo-skills
```

Or clone and symlink directly:

```bash
git clone https://github.com/oconsole/odoo-skills ~/odoo-skills
ln -s ~/odoo-skills/skills/odoo-model-customize ~/.claude/skills/odoo-model-customize
```

## Skills

### Model & Schema
- [`odoo-model-customize`](skills/odoo-model-customize/) — Runtime-safe model customization: defaults, sort order, custom fields, inherited views, automated actions. Knows the boundary between runtime-modifiable and module-required changes.

### ORM & Queries
*coming soon*

### Views & UX
*coming soon*

### Workflow & Actions
*coming soon*

### Security & Access
*coming soon*

### Deployment & Ops
*coming soon*

## Repo layout

```
odoo-skills/
├── .claude-plugin/marketplace.json  # plugin manifest
├── skills/                          # one folder per skill
│   └── <skill-name>/
│       ├── SKILL.md                 # required, with frontmatter
│       └── references/              # optional deep-dive docs
├── template/SKILL.md                # starter for new skills
├── tools/validate-skills.sh         # frontmatter linter
├── CONTRIBUTING.md
└── LICENSE
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New skills must pass `tools/validate-skills.sh`.

## License

MIT — see [LICENSE](LICENSE).
