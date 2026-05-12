#!/usr/bin/env python3
"""Verify SHA-256 integrity of vendored ALZ query files.

Computes SHA-256 hash of each query file and validates against manifest.json.
Supports both verification and hash regeneration modes.

Threat mitigation: T1 (compromised vendored query / KQL injection).

Usage:
    python scripts/verify_query_integrity.py          # Verify hashes
    python scripts/verify_query_integrity.py --update # Regenerate hashes
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load manifest.json."""
    if not manifest_path.exists():
        print(f"ERROR: manifest.json not found at {manifest_path}")
        sys.exit(1)
    with open(manifest_path) as f:
        data: dict[str, Any] = json.load(f)
        return data


def save_manifest(manifest: dict[str, Any], manifest_path: Path) -> None:
    """Save manifest.json with 2-space indent."""
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def generate_markdown_manifest(manifest: dict[str, Any], repo_root: Path) -> str:
    """Generate human-readable MANIFEST.md from manifest.json."""
    lines = ["# ALZ query snapshot manifest", ""]
    lines.append("Refreshed automatically; see .github/workflows/refresh-alz-snapshot.yml")
    lines.append("")

    # Get most recent vendored_at timestamp
    timestamps = [src["vendored_at"] for src in manifest.get("sources", [])]
    if timestamps:
        lines.append(f"Vendored at: {max(timestamps)}")
    lines.append("")
    lines.append("This snapshot is pinned to commit SHAs. No `main` or `latest` references are used for source content.")
    lines.append("")
    lines.append("## Sources")
    lines.append("")

    for source in manifest.get("sources", []):
        lines.append(f"### {source['repo']}")
        lines.append("")
        lines.append(f"- commit_sha: `{source['commit_sha']}`")
        lines.append(f"- ref: `{source['ref']}`")
        lines.append(f"- vendored_at: `{source['vendored_at']}`")
        lines.append(f"- source_file: `{source['subset']['source_file']}`")

        checklist_ids = ", ".join(source["subset"]["checklist_ids"])
        lines.append(f"- checklist_ids: `{checklist_ids}`")
        lines.append(f"- file_count: `{source['file_count']}`")
        lines.append("")

    return "\n".join(lines)


def verify_integrity(repo_root: Path) -> int:
    """Verify all query file hashes against manifest.json.

    Returns:
        0 if all hashes match, 1 otherwise.
    """
    manifest_path = repo_root / "data" / "alz-queries" / "manifest.json"
    manifest = load_manifest(manifest_path)

    all_pass = True
    total_files = 0

    for source in manifest.get("sources", []):
        for file_path_str in source["subset"]["files"]:
            total_files += 1
            file_path = repo_root / file_path_str

            if not file_path.exists():
                print(f"FAIL: {file_path_str} (file missing)")
                all_pass = False
                continue

            expected_hash = source["subset"].get("sha256", {}).get(file_path_str)
            if not expected_hash:
                print(f"FAIL: {file_path_str} (no hash in manifest)")
                all_pass = False
                continue

            actual_hash = compute_sha256(file_path)

            if actual_hash != expected_hash:
                print(f"FAIL: {file_path_str}")
                print(f"  Expected: {expected_hash}")
                print(f"  Actual:   {actual_hash}")
                all_pass = False
            else:
                print(f"PASS: {file_path_str}")

    print("")
    if all_pass:
        print(f"✓ All {total_files} query files passed integrity check")
        return 0
    else:
        print("✗ Integrity check failed")
        return 1


def update_hashes(repo_root: Path) -> int:
    """Recompute all query file hashes and update manifest.json + MANIFEST.md.

    Returns:
        0 on success, 1 on error.
    """
    manifest_path = repo_root / "data" / "alz-queries" / "manifest.json"
    manifest = load_manifest(manifest_path)

    total_files = 0

    for source in manifest.get("sources", []):
        # Initialize sha256 dict if not present
        if "sha256" not in source["subset"]:
            source["subset"]["sha256"] = {}

        for file_path_str in source["subset"]["files"]:
            file_path = repo_root / file_path_str

            if not file_path.exists():
                print(f"ERROR: {file_path_str} not found")
                return 1

            sha256_hash = compute_sha256(file_path)
            source["subset"]["sha256"][file_path_str] = sha256_hash
            print(f"Updated: {file_path_str} → {sha256_hash[:16]}...")
            total_files += 1

    # Save updated manifest.json
    save_manifest(manifest, manifest_path)
    print(f"✓ Wrote {manifest_path}")

    # Regenerate MANIFEST.md
    manifest_md_path = repo_root / "data" / "alz-queries" / "MANIFEST.md"
    markdown_content = generate_markdown_manifest(manifest, repo_root)
    manifest_md_path.write_text(markdown_content, encoding="utf-8")
    print(f"✓ Wrote {manifest_md_path}")

    print("")
    print(f"✓ Updated hashes for {total_files} query files")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify SHA-256 integrity of vendored ALZ queries"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Regenerate all hashes and update manifest (use after refresh)",
    )
    args = parser.parse_args()

    # Repo root is two levels up from scripts/
    repo_root = Path(__file__).parent.parent

    if args.update:
        return update_hashes(repo_root)
    else:
        return verify_integrity(repo_root)


if __name__ == "__main__":
    sys.exit(main())
