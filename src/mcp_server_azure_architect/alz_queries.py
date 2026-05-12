# READ-ONLY: this module performs static lookups against vendored data; no
# Azure or filesystem writes. Per ADR-003, native tools backed by this loader
# expose the `_query_*` verb pattern and never construct an Azure SDK client.
"""Vendored ALZ checklist query loader.

Design notes (Forge, wave 4):

* **Pure stdlib.** Only `json` and `pathlib` are imported. No Azure SDK, no
  httpx, no Pydantic. This keeps cold-start overhead at near zero (the module
  loads in under a millisecond) and preserves the read-only invariant by
  construction.
* **Lazy parse.** The manifest is parsed on first call and cached in a
  module-level singleton. Importing this module does not touch the filesystem.
* **Source of truth.** Layout follows ADR-002 / PR #27. The vendored snapshot
  lives at `data/alz-queries/` with `manifest.json` indexing checklist IDs to
  `.kql` files. Atlas owns the data; this module is a read-only consumer.
* **Confused-deputy mitigation (per Sentinel threat model, S1/E1).** The only
  caller-supplied input is `checklist_id`, which is matched against the
  vendored allowlist. There is no `subscription_id` surface here, so no
  Azure-scoped authorization decision is delegated to the caller. Future tools
  that take a `subscription_id` MUST validate caller scope separately.
* **Install layouts.** The loader resolves the data root in two locations to
  cover both `pip install -e .` (data sits at the repo root) and a built wheel
  (force-included under the package as `_data/alz-queries`). See
  `[tool.hatch.build.targets.wheel.force-include]` in `pyproject.toml`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

_MANIFEST_NAME = "manifest.json"
_MAX_AVAILABLE_IDS_IN_ERROR = 10
_DATA_PREFIX = ("data", "alz-queries")


class QueryRecord(TypedDict):
    """Return shape for a single vendored ALZ query lookup."""

    checklist_id: str
    kql: str
    pillar: str
    source_repo: str
    source_commit: str
    source_ref: str
    source_file: str
    vendored_at: str
    vendored_path: str
    citation: str


def _resolve_data_root() -> Path:
    """Locate the vendored ALZ data directory.

    Tries the wheel-install location first (force-included under the package)
    then falls back to the editable / source-checkout layout (repo root).
    """
    package_dir = Path(__file__).resolve().parent

    wheel_path = package_dir / "_data" / "alz-queries"
    if (wheel_path / _MANIFEST_NAME).is_file():
        return wheel_path

    repo_path = package_dir.parent.parent / "data" / "alz-queries"
    if (repo_path / _MANIFEST_NAME).is_file():
        return repo_path

    raise FileNotFoundError(
        "ALZ query manifest not found. Looked in "
        f"{wheel_path} and {repo_path}."
    )


def _build_index(data_root: Path) -> dict[str, QueryRecord]:
    """Parse the manifest and build the checklist_id -> QueryRecord index."""
    manifest_path = data_root / _MANIFEST_NAME
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    index: dict[str, QueryRecord] = {}
    for source in raw.get("sources", []):
        repo = str(source["repo"])
        commit = str(source["commit_sha"])
        ref = str(source.get("ref", f"commit:{commit}"))
        vendored_at = str(source.get("vendored_at", ""))
        subset = source.get("subset", {})
        source_file = str(subset.get("source_file", ""))
        files = subset.get("files", [])

        for relative_path in files:
            parts = Path(relative_path).parts
            if parts[: len(_DATA_PREFIX)] == _DATA_PREFIX:
                inside = Path(*parts[len(_DATA_PREFIX) :])
            else:
                inside = Path(relative_path)
            kql_path = data_root / inside

            checklist_id = kql_path.stem
            pillar = kql_path.parent.name
            kql_text = kql_path.read_text(encoding="utf-8").strip()
            citation = (
                f"{repo}@{commit} ({source_file}) checklist_id={checklist_id}"
            )

            index[checklist_id] = QueryRecord(
                checklist_id=checklist_id,
                kql=kql_text,
                pillar=pillar,
                source_repo=repo,
                source_commit=commit,
                source_ref=ref,
                source_file=source_file,
                vendored_at=vendored_at,
                vendored_path=str(Path(relative_path).as_posix()),
                citation=citation,
            )

    return index


_INDEX: dict[str, QueryRecord] | None = None


def _get_index() -> dict[str, QueryRecord]:
    """Return the parsed manifest index, building it on first call."""
    global _INDEX
    if _INDEX is None:
        _INDEX = _build_index(_resolve_data_root())
    return _INDEX


def list_query_ids() -> list[str]:
    """Return the sorted list of vendored checklist IDs.

    Useful for diagnostics and for future tools that enumerate the catalog.
    """
    return sorted(_get_index().keys())


def get_query(checklist_id: str) -> QueryRecord:
    """Return the vendored query record for a checklist ID.

    Raises:
        LookupError: if the ID is not in the vendored allowlist. The error
            message includes a capped sample of available IDs to aid recovery
            without dumping the full catalog.
    """
    index = _get_index()
    record = index.get(checklist_id)
    if record is None:
        available = sorted(index.keys())
        sample = available[:_MAX_AVAILABLE_IDS_IN_ERROR]
        suffix = (
            f" (showing first {_MAX_AVAILABLE_IDS_IN_ERROR} of {len(available)})"
            if len(available) > _MAX_AVAILABLE_IDS_IN_ERROR
            else ""
        )
        raise LookupError(
            f"checklist_id {checklist_id!r} not found in vendored ALZ "
            f"snapshot. Available: {sample}{suffix}."
        )
    return record


def reset_cache() -> None:
    """Clear the cached manifest index. Intended for tests."""
    global _INDEX
    _INDEX = None
