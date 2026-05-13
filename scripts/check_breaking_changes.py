#!/usr/bin/env python3
"""KQL breaking-change detector for ALZ snapshot refresh PRs.

Compares vendored .kql files between base-ref and head-ref. Flags breaking changes
when the first table reference token changes (schema surface altered).

Stdlib only. No external runtime dependencies.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ChangeType(Enum):
    """Change classification for a single .kql file."""

    UNCHANGED = "unchanged"
    FIRST_TOKEN_CHANGED = "first_token_changed"
    REMOVED = "removed"
    ADDED = "added"
    HEADER_ONLY_CHANGED = "header_only_changed"
    BODY_CHANGED_SAME_TOKEN = "body_changed_same_token"


@dataclass
class FileChange:
    """Change record for a single .kql file."""

    path: str
    change_type: ChangeType
    base_token: str | None
    head_token: str | None
    breaking: bool


def extract_first_token(content: str) -> str | None:
    """Extract the first identifier token from a .kql file.

    Args:
        content: Full .kql file content (headers + query)

    Returns:
        First identifier token on first non-comment line, or None if not found
    """
    for line in content.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("//"):
            continue
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", stripped)
        if match:
            return match.group(1)
    return None


def get_file_content(ref: str, path: str) -> str | None:
    """Retrieve file content at a specific git ref.

    Args:
        ref: Git ref (e.g., "origin/main", "HEAD")
        path: Relative file path from repo root

    Returns:
        File content as string, or None if file does not exist at ref
    """
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def strip_header(content: str) -> str:
    """Extract only the KQL query body (skip header comment lines).

    Args:
        content: Full .kql file content

    Returns:
        Query body (first non-comment line)
    """
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped and not stripped.startswith("//"):
            return stripped
    return ""


def classify_change(path: str, base_content: str | None, head_content: str | None) -> FileChange:
    """Classify change type for a single .kql file.

    Args:
        path: File path relative to repo root
        base_content: File content at base-ref (None if file did not exist)
        head_content: File content at head-ref (None if file removed)

    Returns:
        FileChange record with classification and breaking flag
    """
    if base_content is None and head_content is not None:
        head_token = extract_first_token(head_content)
        return FileChange(
            path=path,
            change_type=ChangeType.ADDED,
            base_token=None,
            head_token=head_token,
            breaking=False,
        )

    if base_content is not None and head_content is None:
        base_token = extract_first_token(base_content)
        return FileChange(
            path=path,
            change_type=ChangeType.REMOVED,
            base_token=base_token,
            head_token=None,
            breaking=True,
        )

    if base_content == head_content:
        base_token = extract_first_token(base_content)
        return FileChange(
            path=path,
            change_type=ChangeType.UNCHANGED,
            base_token=base_token,
            head_token=base_token,
            breaking=False,
        )

    base_token = extract_first_token(base_content)
    head_token = extract_first_token(head_content)

    base_body = strip_header(base_content)
    head_body = strip_header(head_content)

    if base_body == head_body:
        return FileChange(
            path=path,
            change_type=ChangeType.HEADER_ONLY_CHANGED,
            base_token=base_token,
            head_token=head_token,
            breaking=False,
        )

    if base_token != head_token:
        return FileChange(
            path=path,
            change_type=ChangeType.FIRST_TOKEN_CHANGED,
            base_token=base_token,
            head_token=head_token,
            breaking=True,
        )

    return FileChange(
        path=path,
        change_type=ChangeType.BODY_CHANGED_SAME_TOKEN,
        base_token=base_token,
        head_token=head_token,
        breaking=False,
    )


def collect_kql_files(data_dir: Path) -> list[str]:
    """Find all .kql files under data_dir.

    Args:
        data_dir: Root directory to scan (e.g., data/alz-queries)

    Returns:
        List of relative file paths (relative to repo root)
    """
    files = []
    for kql_file in data_dir.rglob("*.kql"):
        files.append(str(kql_file).replace("\\", "/"))
    return sorted(files)


def analyze_changes(
    base_ref: str, head_ref: str, data_dir: Path
) -> tuple[list[FileChange], dict[str, int]]:
    """Analyze all .kql files for breaking changes.

    Args:
        base_ref: Git ref for base (e.g., "origin/main")
        head_ref: Git ref for head (e.g., "HEAD")
        data_dir: Root directory for .kql files

    Returns:
        Tuple of (list of FileChange records, summary counts dict)
    """
    head_files = set(collect_kql_files(data_dir))

    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", base_ref],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        base_all_files = set(result.stdout.splitlines())
        base_files = {f for f in base_all_files if f.endswith(".kql") and data_dir.name in f}
    except subprocess.CalledProcessError:
        base_files = set()

    all_files = head_files | base_files
    changes = []

    for file_path in sorted(all_files):
        base_content = get_file_content(base_ref, file_path) if file_path in base_files else None
        head_content = get_file_content(head_ref, file_path) if file_path in head_files else None
        change = classify_change(file_path, base_content, head_content)
        changes.append(change)

    summary = {
        "total": len(changes),
        "breaking": sum(1 for c in changes if c.breaking),
        "unchanged": sum(1 for c in changes if c.change_type == ChangeType.UNCHANGED),
        "added": sum(1 for c in changes if c.change_type == ChangeType.ADDED),
        "removed": sum(1 for c in changes if c.change_type == ChangeType.REMOVED),
        "first_token_changed": sum(
            1 for c in changes if c.change_type == ChangeType.FIRST_TOKEN_CHANGED
        ),
        "header_only_changed": sum(
            1 for c in changes if c.change_type == ChangeType.HEADER_ONLY_CHANGED
        ),
        "body_changed_same_token": sum(
            1 for c in changes if c.change_type == ChangeType.BODY_CHANGED_SAME_TOKEN
        ),
    }

    return changes, summary


def format_markdown(changes: list[FileChange], summary: dict[str, int]) -> str:
    """Format breaking-change report as markdown.

    Args:
        changes: List of FileChange records
        summary: Summary counts dict

    Returns:
        Markdown-formatted report
    """
    lines = ["## ALZ Snapshot Breaking-Change Report", ""]

    if summary["breaking"] == 0:
        lines.append("**No breaking changes detected.**")
        lines.append("")
        lines.append(f"- Total files analyzed: {summary['total']}")
        lines.append(f"- Unchanged: {summary['unchanged']}")
        lines.append(f"- Added: {summary['added']}")
        lines.append(f"- Header-only changes: {summary['header_only_changed']}")
        lines.append(f"- Body changes (same token): {summary['body_changed_same_token']}")
        return "\n".join(lines)

    lines.append(f"**{summary['breaking']} breaking change(s) detected.**")
    lines.append("")
    lines.append("### Summary")
    lines.append("")
    lines.append(f"- **Breaking changes**: {summary['breaking']}")
    lines.append(f"  - First token changed: {summary['first_token_changed']}")
    lines.append(f"  - Files removed: {summary['removed']}")
    lines.append(f"- Total files analyzed: {summary['total']}")
    lines.append(f"- Unchanged: {summary['unchanged']}")
    lines.append(f"- Added: {summary['added']}")
    lines.append(f"- Header-only changes: {summary['header_only_changed']}")
    lines.append(f"- Body changes (same token): {summary['body_changed_same_token']}")
    lines.append("")

    breaking_changes = [c for c in changes if c.breaking]
    if breaking_changes:
        lines.append("### Breaking changes")
        lines.append("")
        lines.append("| File | Change Type | Base Token | Head Token |")
        lines.append("|------|-------------|------------|------------|")
        for change in breaking_changes:
            base_token_str = change.base_token or "(none)"
            head_token_str = change.head_token or "(none)"
            lines.append(
                f"| `{change.path}` | {change.change_type.value} | "
                f"`{base_token_str}` | `{head_token_str}` |"
            )
        lines.append("")

    non_breaking_changes = [
        c
        for c in changes
        if not c.breaking
        and c.change_type not in (ChangeType.UNCHANGED, ChangeType.HEADER_ONLY_CHANGED)
    ]
    if non_breaking_changes:
        lines.append("### Non-breaking changes for review")
        lines.append("")
        lines.append("| File | Change Type | Token |")
        lines.append("|------|-------------|-------|")
        for change in non_breaking_changes:
            token_str = change.head_token or "(none)"
            lines.append(f"| `{change.path}` | {change.change_type.value} | `{token_str}` |")
        lines.append("")

    lines.append(
        "**Action required**: Review the breaking changes above. "
        "If these are legitimate schema updates, apply the `breaking-change-approved` "
        "label to override this check."
    )

    return "\n".join(lines)


def format_json(changes: list[FileChange], summary: dict[str, int]) -> str:
    """Format breaking-change report as JSON.

    Args:
        changes: List of FileChange records
        summary: Summary counts dict

    Returns:
        JSON-formatted report
    """
    data: dict[str, Any] = {
        "summary": summary,
        "breaking": summary["breaking"] > 0,
        "changes": [
            {
                "path": c.path,
                "change_type": c.change_type.value,
                "base_token": c.base_token,
                "head_token": c.head_token,
                "breaking": c.breaking,
            }
            for c in changes
        ],
    }
    return json.dumps(data, indent=2)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="KQL breaking-change detector for ALZ snapshot refresh PRs"
    )
    parser.add_argument("--base-ref", required=True, help="Git ref for base (e.g., origin/main)")
    parser.add_argument("--head-ref", default="HEAD", help="Git ref for head (default: HEAD)")
    parser.add_argument(
        "--output",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/alz-queries"),
        help="Root directory for .kql files (default: data/alz-queries)",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Exit with code 0 even if breaking changes detected",
    )

    args = parser.parse_args()

    changes, summary = analyze_changes(args.base_ref, args.head_ref, args.data_dir)

    if args.output == "markdown":
        output = format_markdown(changes, summary)
    else:
        output = format_json(changes, summary)

    print(output)

    if summary["breaking"] > 0 and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
