#!/usr/bin/env python3
"""Refresh vendored ALZ query snapshot from upstream sources.

Compares pinned commit SHAs in manifest.json against upstream HEAD,
fetches new queries if drift detected, and regenerates manifests.

Usage:
    python scripts/refresh_alz_snapshot.py [--dry-run]
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict


class RepoConfig(TypedDict):
    """Configuration for a single upstream repo."""

    repo: str
    dest_subdir: str
    source_file: str
    extractor: Callable[[Path, Path], tuple[list[str], dict[str, dict[str, Any]]]]


def compute_content_hash(kql_path: Path, metadata: dict[str, Any]) -> str:
    """Compute a content hash for deduplication (KQL + metadata bytes)."""
    sha256 = hashlib.sha256()
    # Hash KQL file content
    with open(kql_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    # Hash metadata JSON (sorted keys for determinism)
    metadata_json = json.dumps(metadata, sort_keys=True).encode("utf-8")
    sha256.update(metadata_json)
    return sha256.hexdigest()


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


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


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


def extract_queries_from_checklist_repo(
    clone_dir: Path, dest_dir: Path
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Extract KQL queries from alz-checklist-queries repo.

    Returns tuple of (checklist IDs extracted, metadata dict by guid).
    """
    source_json = clone_dir / "queries" / "alz_all_queries.json"
    if not source_json.exists():
        print(f"Warning: {source_json} not found in clone, skipping")
        return ([], {})

    with open(source_json) as f:
        data = json.load(f)

    # Check for merged-catalogue marker
    metadata = data.get("metadata", {})
    if metadata.get("merged", False):
        print(
            f"  Detected merged catalogue (total_items: {metadata.get('total_items', 'unknown')})"
        )

    # Schema-shape: accept both {items: [...]} and {queries: [...]}
    queries = data.get("queries", data.get("items", []))
    if not queries:
        raise ValueError(
            f"Upstream schema mismatch in alz_all_queries.json: "
            f"expected top-level key 'queries' or 'items', got: {list(data.keys())}"
        )

    checklist_ids = []
    metadata_dict = {}
    skipped_count = 0

    for item in queries:
        # Accept both 'guid' and 'id' keys
        checklist_id = item.get("guid") or item.get("id")
        kql_query = item.get("graph")

        # Validate required fields
        if not checklist_id or not kql_query:
            print(
                f"Warning: skipping item missing 'guid'/'id' or 'graph': {checklist_id or 'unknown'}"
            )
            continue

        # Filter: skip non-queryable items
        if not item.get("queryable", True):
            skipped_count += 1
            continue

        checklist_ids.append(checklist_id)

        # Store metadata for manifest v2
        metadata_dict[checklist_id] = {
            "text": item.get("text", ""),
            "category": item.get("category", ""),
            "subcategory": item.get("subcategory", ""),
            "severity": item.get("severity", ""),
            "queryable": item.get("queryable", True),
            "upstream_reason": item.get("reason"),
            "waf": item.get("waf"),
        }

        # Write KQL file with vendoring header
        kql_path = dest_dir / f"{checklist_id}.kql"
        with open(kql_path, "w") as f:
            f.write(
                f"// Vendored from https://github.com/martinopedal/alz-checklist-queries/blob/{{sha}}/queries/alz_all_queries.json\n"
                f"// Source checklist ID: {checklist_id}\n"
                f"// Vendored at: {{timestamp}}\n"
                f"{kql_query}\n"
            )

    if skipped_count > 0:
        print(f"  Skipped {skipped_count} non-queryable items")

    return (checklist_ids, metadata_dict)


def extract_queries_from_graph_repo(
    clone_dir: Path, dest_dir: Path
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Extract KQL queries from alz-graph-queries repo.

    Returns tuple of (query IDs extracted, metadata dict by guid).
    """
    source_json = clone_dir / "queries" / "alz_additional_queries.json"
    if not source_json.exists():
        print(f"Warning: {source_json} not found in clone, skipping")
        return ([], {})

    with open(source_json) as f:
        data = json.load(f)

    # Check for merged-catalogue marker
    metadata = data.get("metadata", {})
    if metadata.get("merged", False):
        print(
            f"  Detected merged catalogue (total_items: {metadata.get('total_items', 'unknown')})"
        )
        print("  Skipping secondary fetch (merged upstream)")
        return ([], {})

    # Schema-shape: expect {queries: [...]}
    if "queries" not in data:
        raise ValueError(
            f"Upstream schema mismatch in alz_additional_queries.json: "
            f"expected top-level key 'queries', got: {list(data.keys())}"
        )

    query_ids = []
    metadata_dict = {}
    skipped_count = 0

    for item in data["queries"]:
        # Validate each item has required fields
        query_id = item.get("guid")
        kql_query = item.get("graph")

        if not query_id or not kql_query:
            print(f"Warning: skipping item missing 'guid' or 'graph': {query_id or 'unknown'}")
            continue

        # Filter: skip non-queryable items
        if not item.get("queryable", False):
            skipped_count += 1
            continue

        query_ids.append(query_id)

        # Store metadata for manifest v2
        metadata_dict[query_id] = {
            "text": item.get("text", ""),
            "category": item.get("category", ""),
            "subcategory": item.get("subcategory", ""),
            "severity": item.get("severity", ""),
            "queryable": item.get("queryable", True),
            "upstream_reason": item.get("reason"),
            "waf": item.get("waf"),
        }

        kql_path = dest_dir / f"{query_id}.kql"
        with open(kql_path, "w") as f:
            f.write(
                f"// Vendored from https://github.com/martinopedal/alz-graph-queries/blob/{{sha}}/queries/alz_additional_queries.json\n"
                f"// Source query ID: {query_id}\n"
                f"// Vendored at: {{timestamp}}\n"
                f"{kql_query}\n"
            )

    if skipped_count > 0:
        print(f"  Skipped {skipped_count} non-queryable items")

    return (query_ids, metadata_dict)


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
    # NOTE: Temporarily vendoring from checklist repo ONLY to avoid guid collision
    # per Decision 10/11 (issue #96). The checklist repo is marked as merged=true
    # and contains 173 queryable items. The graph repo causes guid collision for
    # one item (see PR #127 body for the specific guid).
    repos: list[RepoConfig] = [
        {
            "repo": "martinopedal/alz-checklist-queries",
            "dest_subdir": "checklist",
            "source_file": "queries/alz_all_queries.json",
            "extractor": extract_queries_from_checklist_repo,
        },
        # Temporarily commented out due to guid collision:
        # {
        #     "repo": "martinopedal/alz-graph-queries",
        #     "dest_subdir": "graph",
        #     "source_file": "queries/alz_additional_queries.json",
        #     "extractor": extract_queries_from_graph_repo,
        # },
    ]

    changes_detected = False
    new_sources = []

    # Track guids across sources for deduplication
    guid_registry: dict[
        str, tuple[str, str, dict[str, Any]]
    ] = {}  # guid -> (source_path, content_hash, metadata)

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

        print(
            f"  Drift detected: {pinned_sha[:12] if pinned_sha else 'none'} -> {upstream_sha[:12]}"
        )
        changes_detected = True

        if dry_run:
            print(f"  [DRY RUN] Would refresh {repo}")
            if existing:
                new_sources.append(existing)
            continue

        # Extract to tempdir for atomic replace
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_dir = Path(tmpdir) / "clone"
            temp_dest_dir = Path(tmpdir) / "extracted"
            temp_dest_dir.mkdir()

            print(f"  Cloning {repo}...")
            clone_shallow(repo, clone_dir)

            # Extract queries and metadata
            print("  Extracting queries...")
            extractor = repo_def["extractor"]
            checklist_ids, metadata_dict = extractor(clone_dir, temp_dest_dir)

            if not checklist_ids:
                print(f"  Warning: No queries extracted from {repo}")
                continue

            # Update headers with actual SHA and timestamp
            timestamp = datetime.now(UTC).isoformat(timespec="seconds")
            update_kql_headers(temp_dest_dir, repo, upstream_sha, timestamp)

            # Validate mandatory metadata present for all queries
            for guid in checklist_ids:
                meta = metadata_dict.get(guid, {})
                missing = [
                    f for f in ["text", "category", "subcategory", "severity"] if not meta.get(f)
                ]
                if missing:
                    raise ValueError(f"Mandatory metadata missing for {guid} in {repo}: {missing}")

            # Deduplication: check for guid collisions across sources
            source_name = "vendored-checklist" if "checklist" in repo else "vendored-graph"
            for guid in checklist_ids:
                kql_path = temp_dest_dir / f"{guid}.kql"
                meta = metadata_dict[guid]
                content_hash = compute_content_hash(kql_path, meta)

                if guid in guid_registry:
                    existing_path, existing_hash, existing_meta = guid_registry[guid]
                    if content_hash == existing_hash:
                        # Identical duplicate, accept silently
                        print(f"  DEBUG: guid {guid} duplicated but identical content, accepting")
                    else:
                        # Different content, hard error
                        raise ValueError(
                            f"Duplicate guid collision: {guid} appears in both {existing_path} "
                            f"and {repo}/{repo_def['dest_subdir']}/{guid}.kql with different content. "
                            f"Remediation: investigate upstream merge, or manually deduplicate."
                        )
                else:
                    # Register this guid
                    guid_registry[guid] = (
                        f"{repo}/{repo_def['dest_subdir']}/{guid}.kql",
                        content_hash,
                        meta,
                    )

            # Atomic replace: move tempdir to final destination
            dest_dir = data_dir / repo_def["dest_subdir"]
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Clear existing queries in this subdir
            for old_kql in dest_dir.glob("*.kql"):
                old_kql.unlink()

            # Copy extracted queries atomically
            for kql_file in temp_dest_dir.glob("*.kql"):
                target = dest_dir / kql_file.name
                target.write_bytes(kql_file.read_bytes())

            # Build manifest v2 source entry with queries metadata
            files = [p.relative_to(repo_root).as_posix() for p in sorted(dest_dir.glob("*.kql"))]
            queries_metadata = {}
            for guid in checklist_ids:
                meta = metadata_dict[guid]
                vendored_path = f"data/alz-queries/{repo_def['dest_subdir']}/{guid}.kql"
                queries_metadata[guid] = {
                    "id": guid,
                    "text": meta.get("text", ""),
                    "category": meta["category"],
                    "subcategory": meta["subcategory"],
                    "severity": meta["severity"],
                    "source": source_name,
                    "source_repo": repo,
                    "source_ref": f"commit:{upstream_sha}",
                    "source_file": repo_def["source_file"],
                    "vendored_at": timestamp,
                    "vendored_path": vendored_path,
                    "citation": f"{repo}@{upstream_sha} ({repo_def['source_file']}) checklist_id={guid}",
                    "queryable": meta.get("queryable", True),
                }
                # Optional fields
                if meta.get("upstream_reason"):
                    queries_metadata[guid]["upstream_reason"] = meta["upstream_reason"]
                if meta.get("waf"):
                    queries_metadata[guid]["waf"] = meta["waf"]

            # Preserve existing license info if present
            license_info = (
                existing.get("license")
                if existing
                else {
                    "spdx": "MIT",
                    "upstream_license_url": f"https://github.com/{repo}/blob/{upstream_sha}/LICENSE",
                }
            )

            new_source = {
                "repo": repo,
                "commit_sha": upstream_sha,
                "ref": f"commit:{upstream_sha}",
                "vendored_at": timestamp,
                "license": license_info,
                "subset": {
                    "source_file": repo_def["source_file"],
                    "checklist_ids": checklist_ids,
                    "files": files,
                    "queries": queries_metadata,
                },
                "file_count": len(checklist_ids),
            }
            new_sources.append(new_source)
            print(f"  Extracted {len(checklist_ids)} queries")

    if changes_detected and not dry_run:
        # Preserve custom sources before overwriting
        custom_sources = [
            s for s in manifest.get("sources", [])
            if s.get("ref") == "custom" or s.get("source_ref") == "custom"
        ]
        
        # Save updated manifest with schema_version: 2
        manifest["schema_version"] = 2
        manifest["sources"] = new_sources + custom_sources  # Append preserved custom sources

        # Regenerate SHA-256 hashes for all query files
        print("Regenerating SHA-256 hashes...")
        for source in new_sources:
            if "sha256" not in source["subset"]:
                source["subset"]["sha256"] = {}

            for file_path_str in source["subset"]["files"]:
                file_path = repo_root / file_path_str
                if file_path.exists():
                    sha256_hash = compute_sha256(file_path)
                    source["subset"]["sha256"][file_path_str] = sha256_hash

        save_manifest(manifest, manifest_path)
        generate_manifest_md(manifest, manifest_md_path)
        print("\nManifests updated with SHA-256 hashes.")

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
