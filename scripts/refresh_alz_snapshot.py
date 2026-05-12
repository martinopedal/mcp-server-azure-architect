#!/usr/bin/env python3
"""Refresh vendored ALZ query snapshot from upstream sources.

Compares pinned commit SHAs in manifest.json against upstream HEAD,
fetches new queries if drift detected, and regenerates manifests.

Usage:
    python scripts/refresh_alz_snapshot.py [--dry-run]
"""

import argparse
import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict


class RepoConfig(TypedDict):
    """Configuration for a single upstream repo."""

    repo: str
    dest_subdir: str
    source_file: str
    extractor: Callable[[Path, Path], list[str]]


def run_git(args: list[str], cwd: str | Path) -> str:
    """Execute git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_upstream_commit(repo: str) -> str:
    """Fetch HEAD commit SHA from upstream GitHub repo via API."""
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits/main", "--jq", ".sha"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def clone_shallow(repo: str, dest: Path) -> None:
    """Clone repository shallow (depth=1) to destination."""
    url = f"https://github.com/{repo}.git"
    subprocess.run(
        ["git", "clone", "--depth=1", url, str(dest)],
        capture_output=True,
        check=True,
    )


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load manifest.json; return empty structure if missing."""
    if not manifest_path.exists():
        return {"sources": []}
    with manifest_path.open() as f:
        data: dict[str, Any] = json.load(f)
        return data


def save_manifest(manifest: dict[str, Any], manifest_path: Path) -> None:
    """Save manifest.json with 2-space indent."""
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def extract_queries_from_checklist_repo(clone_dir: Path, dest_dir: Path) -> list[str]:
    """Extract KQL queries from alz-checklist-queries repo.

    Returns list of checklist IDs extracted.
    """
    source_json = clone_dir / "queries" / "alz_all_queries.json"
    if not source_json.exists():
        print(f"Warning: {source_json} not found in clone, skipping")
        return []

    with open(source_json) as f:
        data = json.load(f)

    checklist_ids = []
    for item in data.get("items", []):
        checklist_id = item.get("id")
        kql_query = item.get("graph")
        if checklist_id and kql_query:
            checklist_ids.append(checklist_id)
            # Write KQL file with vendoring header
            kql_path = dest_dir / f"{checklist_id}.kql"
            with open(kql_path, "w") as f:
                f.write(
                    f"// Vendored from https://github.com/martinopedal/alz-checklist-queries/blob/{{sha}}/queries/alz_all_queries.json\n"
                    f"// Source checklist ID: {checklist_id}\n"
                    f"// Vendored at: {{timestamp}}\n"
                    f"{kql_query}\n"
                )
    return checklist_ids


def extract_queries_from_graph_repo(clone_dir: Path, dest_dir: Path) -> list[str]:
    """Extract KQL queries from alz-graph-queries repo.

    Returns list of query IDs extracted.
    """
    source_json = clone_dir / "queries" / "alz_additional_queries.json"
    if not source_json.exists():
        print(f"Warning: {source_json} not found in clone, skipping")
        return []

    with open(source_json) as f:
        data = json.load(f)

    query_ids = []
    for item in data.get("items", []):
        query_id = item.get("id")
        kql_query = item.get("graph")
        if query_id and kql_query:
            query_ids.append(query_id)
            kql_path = dest_dir / f"{query_id}.kql"
            with open(kql_path, "w") as f:
                f.write(
                    f"// Vendored from https://github.com/martinopedal/alz-graph-queries/blob/{{sha}}/queries/alz_additional_queries.json\n"
                    f"// Source query ID: {query_id}\n"
                    f"// Vendored at: {{timestamp}}\n"
                    f"{kql_query}\n"
                )
    return query_ids


def update_kql_headers(kql_dir: Path, repo: str, sha: str, timestamp: str) -> None:
    """Update placeholder {sha} and {timestamp} in all KQL files in directory."""
    for kql_file in kql_dir.glob("*.kql"):
        content = kql_file.read_text()
        content = content.replace("{sha}", sha)
        content = content.replace("{timestamp}", timestamp)
        kql_file.write_text(content)


def generate_manifest_md(manifest: dict[str, Any], manifest_md_path: Path) -> None:
    """Generate human-readable MANIFEST.md from manifest.json."""
    lines = [
        "# ALZ query snapshot manifest",
        "",
        "Refreshed automatically; see .github/workflows/refresh-alz-snapshot.yml",
        "",
        "This snapshot is pinned to commit SHAs. No `main` or `latest` references are used for source content.",
        "",
        "## Sources",
        "",
    ]

    for source in manifest.get("sources", []):
        repo = source["repo"]
        commit_sha = source["commit_sha"]
        ref = source["ref"]
        vendored_at = source["vendored_at"]
        source_file = source["subset"]["source_file"]
        checklist_ids = ", ".join(source["subset"]["checklist_ids"])
        file_count = source["file_count"]

        lines.append(f"### {repo}")
        lines.append("")
        lines.append(f"- commit_sha: `{commit_sha}`")
        lines.append(f"- ref: `{ref}`")
        lines.append(f"- vendored_at: `{vendored_at}`")
        lines.append(f"- source_file: `{source_file}`")
        lines.append(f"- checklist_ids: `{checklist_ids}`")
        lines.append(f"- file_count: `{file_count}`")
        lines.append("")

    manifest_md_path.write_text("\n".join(lines))


def refresh_snapshot(dry_run: bool = False) -> bool:
    """Refresh ALZ snapshot. Returns True if changes detected."""
    repo_root = Path(__file__).parent.parent
    data_dir = repo_root / "data" / "alz-queries"
    manifest_path = data_dir / "manifest.json"
    manifest_md_path = data_dir / "MANIFEST.md"

    manifest = load_manifest(manifest_path)

    # Source repo definitions
    repos = [
        {
            "repo": "martinopedal/alz-checklist-queries",
            "dest_subdir": "checklist",
            "source_file": "queries/alz_all_queries.json",
            "extractor": extract_queries_from_checklist_repo,
        },
        {
            "repo": "martinopedal/alz-graph-queries",
            "dest_subdir": "graph",
            "source_file": "queries/alz_additional_queries.json",
            "extractor": extract_queries_from_graph_repo,
        },
    ]

    changes_detected = False
    new_sources = []

    for repo_def in repos:
        repo = repo_def["repo"]
        print(f"Checking {repo}...")

        # Get upstream HEAD
        try:
            upstream_sha = get_upstream_commit(repo)
        except subprocess.CalledProcessError as e:
            print(f"Error fetching upstream SHA for {repo}: {e}")
            sys.exit(1)

        # Find existing source in manifest
        existing = next(
            (s for s in manifest.get("sources", []) if s["repo"] == repo),
            None,
        )

        pinned_sha = existing["commit_sha"] if existing else None

        if upstream_sha == pinned_sha:
            print(f"  No drift (pinned: {pinned_sha[:12]})")
            if existing:
                new_sources.append(existing)
            continue

        print(f"  Drift detected: {pinned_sha[:12] if pinned_sha else 'none'} -> {upstream_sha[:12]}")
        changes_detected = True

        if dry_run:
            print(f"  [DRY RUN] Would refresh {repo}")
            if existing:
                new_sources.append(existing)
            continue

        # Clone and extract
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_dir = Path(tmpdir) / "clone"
            print(f"  Cloning {repo}...")
            clone_shallow(repo, clone_dir)

            # Extract queries
            dest_dir = data_dir / repo_def["dest_subdir"]
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Clear existing queries in this subdir
            for old_kql in dest_dir.glob("*.kql"):
                old_kql.unlink()

            print(f"  Extracting queries to {dest_dir.name}/...")
            extractor = repo_def["extractor"]
            checklist_ids = extractor(clone_dir, dest_dir)

            if not checklist_ids:
                print(f"  Warning: No queries extracted from {repo}")
                continue

            # Update headers with actual SHA and timestamp
            timestamp = datetime.now(UTC).isoformat(timespec="seconds")
            update_kql_headers(dest_dir, repo, upstream_sha, timestamp)

            # Build new source entry
            files = [str(p.relative_to(repo_root)) for p in sorted(dest_dir.glob("*.kql"))]
            new_source = {
                "repo": repo,
                "commit_sha": upstream_sha,
                "ref": f"commit:{upstream_sha}",
                "vendored_at": timestamp,
                "subset": {
                    "source_file": repo_def["source_file"],
                    "checklist_ids": checklist_ids,
                    "files": files,
                },
                "file_count": len(checklist_ids),
            }
            new_sources.append(new_source)
            print(f"  Extracted {len(checklist_ids)} queries")

    if changes_detected and not dry_run:
        # Save updated manifest
        manifest["sources"] = new_sources
        save_manifest(manifest, manifest_path)
        generate_manifest_md(manifest, manifest_md_path)
        print("\nManifests updated.")

    if dry_run and changes_detected:
        print("\n[DRY RUN] Changes detected but not applied.")
    elif not changes_detected:
        print("\nNo changes needed.")

    return changes_detected


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh ALZ query snapshot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for drift without applying changes",
    )
    args = parser.parse_args()

    changes = refresh_snapshot(dry_run=args.dry_run)
    sys.exit(0 if not args.dry_run or not changes else 1)


if __name__ == "__main__":
    main()
