#!/usr/bin/env python3
"""sync-from-rl.py — mirror skill_rl/skills/{read,write,demo}/* into odoo-skills.

Both repos use the same nested layout, so the sync is a straight 1:1 mirror —
no name-to-tier mapping is needed. Tier is implicit from the source path:

    skill_rl/skills/<tier>/<name>/    →    odoo-skills/skills/<tier>/<name>/

Skills that exist only in odoo-skills (not in skill_rl) are LEFT ALONE — that's
the channel for hand-authored skills that aren't RL-managed.

Skills that exist only in skill_rl are reported as new and copied across.
The validator runs at the end to enforce frontmatter and tier rules.

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


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "sync-config.json"
SKILLS_DIR = REPO_ROOT / "skills"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
VALIDATOR_PATH = REPO_ROOT / "tools" / "validate-skills.sh"

VALID_TIERS = ("read", "write", "demo")
PLUGIN_BY_TIER = {
    "read": "odoo-skills-read",
    "write": "odoo-skills-write",
    "demo": "odoo-skills-demo",
}


@dataclass
class SyncReport:
    new_skills: list[str] = field(default_factory=list)        # in source, never seen in dest before
    files_added: list[str] = field(default_factory=list)
    files_updated: list[str] = field(default_factory=list)
    files_unchanged: list[str] = field(default_factory=list)
    skipped_dest_only: list[str] = field(default_factory=list)  # in dest only — left alone
    marketplace_updated: bool = False
    errors: list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.files_added or self.files_updated or self.marketplace_updated)


def load_config() -> dict:
    """Load optional sync-config.json. Currently only used for `source_repo`
    default — the rest is path-driven."""
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open() as f:
            return json.load(f)
    return {"source_repo": "/home/ec2-user/skill_rl"}


def inject_tier(content: str, tier: str) -> tuple[str, bool]:
    """Ensure frontmatter has metadata.tier set to the given value.

    Returns (new_content, changed).
    """
    fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not fm_match:
        return content, False

    frontmatter = fm_match.group(1)
    if re.search(r"^  tier:\s*\S+", frontmatter, re.MULTILINE):
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

    new_fm = frontmatter.rstrip() + f"\nmetadata:\n  tier: {tier}\n"
    return content.replace(frontmatter, new_fm, 1), True


def sync_skill(
    source_dir: Path,
    target_dir: Path,
    tier: str,
    apply: bool,
    report: SyncReport,
) -> None:
    """Mirror source_dir → target_dir, injecting metadata.tier into SKILL.md."""
    is_new_skill = not target_dir.exists()
    if is_new_skill:
        report.new_skills.append(f"{tier}/{source_dir.name}")

    if apply:
        target_dir.mkdir(parents=True, exist_ok=True)

    # SKILL.md
    src_md = source_dir / "SKILL.md"
    if not src_md.exists():
        report.errors.append(f"{source_dir} has no SKILL.md")
        return

    dst_md = target_dir / "SKILL.md"
    src_content = src_md.read_text()
    new_content, _ = inject_tier(src_content, tier)
    rel = dst_md.relative_to(REPO_ROOT) if apply or dst_md.exists() else Path(f"skills/{tier}/{source_dir.name}/SKILL.md")

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
        if apply:
            dst_refs.mkdir(exist_ok=True)
        for ref_file in sorted(src_refs.glob("*.md")):
            dst_file = dst_refs / ref_file.name
            rel_ref = dst_file.relative_to(REPO_ROOT) if apply or dst_file.exists() else Path(f"skills/{tier}/{source_dir.name}/references/{ref_file.name}")
            if dst_file.exists() and filecmp.cmp(ref_file, dst_file, shallow=False):
                report.files_unchanged.append(str(rel_ref))
                continue
            if dst_file.exists():
                report.files_updated.append(str(rel_ref))
            else:
                report.files_added.append(str(rel_ref))
            if apply:
                shutil.copy2(ref_file, dst_file)


def update_marketplace(synced_skills: list[tuple[str, str]], apply: bool, report: SyncReport) -> None:
    """Ensure each (tier, name) pair is registered in the matching plugin."""
    if not MARKETPLACE_PATH.exists():
        report.errors.append(f"{MARKETPLACE_PATH} not found")
        return

    with MARKETPLACE_PATH.open() as f:
        marketplace = json.load(f)

    plugins = {p["name"]: p for p in marketplace.get("plugins", [])}
    changed = False

    for tier, name in synced_skills:
        plugin_name = PLUGIN_BY_TIER.get(tier)
        if plugin_name is None:
            report.errors.append(f"unknown tier '{tier}' for skill '{name}'")
            continue
        if plugin_name not in plugins:
            report.errors.append(f"plugin '{plugin_name}' missing from marketplace.json")
            continue
        rel_skill_path = f"./skills/{tier}/{name}"
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
        "chore: sync skills from skill_rl\n\n"
        "Auto-mirrored via tools/sync-from-rl.py.\n\n"
        f"Added: {len(report.files_added)} files\n"
        f"Updated: {len(report.files_updated)} files\n"
        f"New skills: {len(report.new_skills)}\n"
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

    section("New skills (created in registry)", report.new_skills)
    section("Files added", report.files_added)
    section("Files updated", report.files_updated)
    section("Files unchanged", report.files_unchanged)
    section("Skipped (dest-only — left alone)", report.skipped_dest_only)
    section("Errors", report.errors)
    print(f"\nMarketplace updated: {report.marketplace_updated}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--apply", action="store_true", help="Actually copy files (default: dry run)")
    parser.add_argument("--commit", action="store_true", help="git add + commit changes (implies --apply)")
    parser.add_argument("--source-repo", help="Override source repo path (default: from sync-config.json or /home/ec2-user/skill_rl)")
    args = parser.parse_args()

    if args.commit:
        args.apply = True

    config = load_config()
    source_repo = Path(args.source_repo or config.get("source_repo", "/home/ec2-user/skill_rl"))
    source_skills_dir = source_repo / "skills"

    if not source_skills_dir.is_dir():
        sys.exit(f"ERROR: source skills dir {source_skills_dir} does not exist")

    report = SyncReport()
    synced_skills: list[tuple[str, str]] = []

    # Walk source: skills/{read,write,demo}/<name>/
    for tier in VALID_TIERS:
        src_tier_dir = source_skills_dir / tier
        dst_tier_dir = SKILLS_DIR / tier

        if not src_tier_dir.is_dir():
            continue

        for source_dir in sorted(p for p in src_tier_dir.iterdir() if p.is_dir()):
            target_dir = dst_tier_dir / source_dir.name
            sync_skill(source_dir, target_dir, tier, args.apply, report)
            synced_skills.append((tier, source_dir.name))

    # Detect dest-only skills (hand-authored, leave them alone)
    for tier in VALID_TIERS:
        dst_tier_dir = SKILLS_DIR / tier
        src_tier_dir = source_skills_dir / tier
        if not dst_tier_dir.is_dir():
            continue
        for dst_skill in sorted(p for p in dst_tier_dir.iterdir() if p.is_dir()):
            src_equiv = src_tier_dir / dst_skill.name
            if not src_equiv.exists():
                report.skipped_dest_only.append(f"{tier}/{dst_skill.name}")

    update_marketplace(synced_skills, args.apply, report)
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
