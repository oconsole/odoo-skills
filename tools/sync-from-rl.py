#!/usr/bin/env python3
"""sync-from-rl.py — sync graduated RL skills from skill_rl into odoo-skills.

Reads sync-config.json, walks the source skill folder, and for every mapped
skill copies SKILL.md and references/ into the configured tier directory.
Injects metadata.tier into frontmatter if missing. Updates marketplace.json
so each skill is registered under exactly one plugin. Runs the validator
at the end.

Usage:
    # Show what would change (default: dry run)
    python tools/sync-from-rl.py

    # Actually copy files
    python tools/sync-from-rl.py --apply

    # Copy + git stage + commit (does NOT push)
    python tools/sync-from-rl.py --apply --commit

    # Override the source repo path
    python tools/sync-from-rl.py --source-repo /path/to/skill_rl
"""

from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "sync-config.json"
SKILLS_DIR = REPO_ROOT / "skills"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
VALIDATOR_PATH = REPO_ROOT / "tools" / "validate-skills.sh"

VALID_TIERS = {"read", "write", "demo"}
PLUGIN_BY_TIER = {
    "read": "odoo-skills-read",
    "write": "odoo-skills-write",
    "demo": "odoo-skills-demo",
}


@dataclass
class SyncReport:
    new_in_source: list[str] = field(default_factory=list)        # found in source, no mapping
    missing_source: list[str] = field(default_factory=list)       # mapping points at nonexistent source
    files_added: list[str] = field(default_factory=list)
    files_updated: list[str] = field(default_factory=list)
    files_unchanged: list[str] = field(default_factory=list)
    marketplace_updated: bool = False
    errors: list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.files_added or self.files_updated or self.marketplace_updated)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"ERROR: {CONFIG_PATH} not found")
    with CONFIG_PATH.open() as f:
        return json.load(f)


def discover_source_skills(source_skills_dir: Path) -> list[str]:
    if not source_skills_dir.is_dir():
        sys.exit(f"ERROR: source skills dir {source_skills_dir} does not exist")
    return sorted(p.name for p in source_skills_dir.iterdir() if p.is_dir())


def inject_tier(content: str, tier: str) -> tuple[str, bool]:
    """Ensure frontmatter has metadata.tier set to the given value.

    Returns (new_content, changed).
    """
    fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not fm_match:
        # No frontmatter — leave content unchanged and surface the problem.
        return content, False

    frontmatter = fm_match.group(1)
    if re.search(r"^  tier:\s*\S+", frontmatter, re.MULTILINE):
        # Already has metadata.tier; replace if different.
        new_fm = re.sub(
            r"^  tier:.*$",
            f"  tier: {tier}",
            frontmatter,
            count=1,
            flags=re.MULTILINE,
        )
        if new_fm == frontmatter:
            return content, False
        return content.replace(frontmatter, new_fm, 1), True

    if re.search(r"^metadata:\s*$", frontmatter, re.MULTILINE):
        # Has metadata block but no tier key — append it.
        new_fm = re.sub(
            r"(^metadata:\s*$\n(?:  \w+:.*\n)*)",
            lambda m: m.group(1) + f"  tier: {tier}\n",
            frontmatter,
            count=1,
            flags=re.MULTILINE,
        )
        if new_fm == frontmatter:
            new_fm = frontmatter + f"\n  tier: {tier}"
        return content.replace(frontmatter, new_fm, 1), True

    # No metadata block at all — add one.
    new_fm = frontmatter.rstrip() + f"\nmetadata:\n  tier: {tier}\n"
    return content.replace(frontmatter, new_fm, 1), True


def sync_skill(
    source_dir: Path,
    target_dir: Path,
    tier: str,
    apply: bool,
    report: SyncReport,
) -> None:
    """Copy source_dir/SKILL.md and references/ → target_dir, injecting tier."""
    if not source_dir.is_dir():
        report.missing_source.append(str(source_dir))
        return

    target_dir.mkdir(parents=True, exist_ok=True)

    # SKILL.md
    src_md = source_dir / "SKILL.md"
    dst_md = target_dir / "SKILL.md"
    if not src_md.exists():
        report.errors.append(f"{source_dir} has no SKILL.md")
        return

    src_content = src_md.read_text()
    new_content, _ = inject_tier(src_content, tier)

    rel = dst_md.relative_to(REPO_ROOT)
    if dst_md.exists():
        if dst_md.read_text() == new_content:
            report.files_unchanged.append(str(rel))
        else:
            report.files_updated.append(str(rel))
            if apply:
                dst_md.write_text(new_content)
    else:
        report.files_added.append(str(rel))
        if apply:
            dst_md.write_text(new_content)

    # references/
    src_refs = source_dir / "references"
    dst_refs = target_dir / "references"
    if src_refs.is_dir():
        dst_refs.mkdir(exist_ok=True)
        for ref_file in sorted(src_refs.glob("*.md")):
            dst_file = dst_refs / ref_file.name
            rel_ref = dst_file.relative_to(REPO_ROOT)
            if dst_file.exists() and filecmp.cmp(ref_file, dst_file, shallow=False):
                report.files_unchanged.append(str(rel_ref))
                continue
            if dst_file.exists():
                report.files_updated.append(str(rel_ref))
            else:
                report.files_added.append(str(rel_ref))
            if apply:
                shutil.copy2(ref_file, dst_file)


def update_marketplace(config: dict, apply: bool, report: SyncReport) -> None:
    if not MARKETPLACE_PATH.exists():
        report.errors.append(f"{MARKETPLACE_PATH} not found")
        return

    with MARKETPLACE_PATH.open() as f:
        marketplace = json.load(f)

    plugins = {p["name"]: p for p in marketplace.get("plugins", [])}
    changed = False

    for source_name, mapping in config["mappings"].items():
        tier = mapping["tier"]
        target_name = mapping.get("target_name", source_name)
        plugin_name = PLUGIN_BY_TIER.get(tier)
        if plugin_name is None:
            report.errors.append(f"unknown tier '{tier}' for source '{source_name}'")
            continue
        if plugin_name not in plugins:
            report.errors.append(f"plugin '{plugin_name}' missing from marketplace.json")
            continue
        rel_skill_path = f"./skills/{tier}/{target_name}"
        skills_list = plugins[plugin_name].setdefault("skills", [])
        if rel_skill_path not in skills_list:
            skills_list.append(rel_skill_path)
            skills_list.sort()
            changed = True

    if changed:
        report.marketplace_updated = True
        if apply:
            with MARKETPLACE_PATH.open("w") as f:
                json.dump(marketplace, f, indent=2)
                f.write("\n")


def run_validator() -> int:
    if not VALIDATOR_PATH.exists():
        return 0
    result = subprocess.run(
        ["bash", str(VALIDATOR_PATH)],
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def git_commit(report: SyncReport) -> None:
    paths = sorted(set(report.files_added + report.files_updated))
    if report.marketplace_updated:
        paths.append(".claude-plugin/marketplace.json")
    if not paths:
        print("Nothing to commit.")
        return
    subprocess.run(["git", "add", "--"] + paths, cwd=REPO_ROOT, check=True)
    msg = (
        "chore: sync RL-graduated skills from skill_rl\n\n"
        "Auto-synced via tools/sync-from-rl.py.\n\n"
        f"Added: {len(report.files_added)} files\n"
        f"Updated: {len(report.files_updated)} files\n"
        f"Marketplace updated: {report.marketplace_updated}\n\n"
        "Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>\n"
    )
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=REPO_ROOT, check=True)


def print_report(report: SyncReport, apply: bool) -> None:
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'} sync report")
    print("-" * 60)

    def section(title: str, items: list[str]) -> None:
        if items:
            print(f"\n{title} ({len(items)}):")
            for item in items:
                print(f"  - {item}")

    section("Files added", report.files_added)
    section("Files updated", report.files_updated)
    section("Files unchanged", report.files_unchanged)
    section("New in source (need a mapping in sync-config.json)", report.new_in_source)
    section("Missing source paths", report.missing_source)
    section("Errors", report.errors)
    print(f"\nMarketplace updated: {report.marketplace_updated}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Actually copy files (default: dry run)")
    parser.add_argument("--commit", action="store_true", help="git add + commit changes (implies --apply)")
    parser.add_argument("--source-repo", help="Override source_repo from sync-config.json")
    args = parser.parse_args()

    if args.commit:
        args.apply = True

    config = load_config()
    source_repo = Path(args.source_repo or config["source_repo"])
    source_skills_dir = source_repo / config.get("source_skills_dir", "skills")

    report = SyncReport()

    found_sources = discover_source_skills(source_skills_dir)
    mappings = config.get("mappings", {})

    for src_name in found_sources:
        if src_name not in mappings:
            report.new_in_source.append(src_name)

    for src_name, mapping in mappings.items():
        tier = mapping["tier"]
        if tier not in VALID_TIERS:
            report.errors.append(f"{src_name}: invalid tier '{tier}'")
            continue
        target_name = mapping.get("target_name", src_name)
        target_dir = SKILLS_DIR / tier / target_name
        source_dir = source_skills_dir / src_name
        sync_skill(source_dir, target_dir, tier, args.apply, report)

    update_marketplace(config, args.apply, report)
    print_report(report, args.apply)

    if args.apply:
        rc = run_validator()
        if rc != 0:
            print("\nValidator FAILED — fix issues before committing.", file=sys.stderr)
            return rc

    if args.commit and report.has_changes():
        git_commit(report)
        print("\nCommitted. Run `git push` to publish.")
    elif args.commit:
        print("\nNo changes to commit.")

    if report.errors:
        return 1
    if report.new_in_source and not args.apply:
        # Surface unmapped skills as a warning, not an error, on dry runs.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
