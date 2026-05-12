# Contributing to ALZ Query Vendoring

This document explains how to work with vendored ALZ queries, including adding new queries, refreshing from upstream, and maintaining SHA-256 integrity checks.

## Why Integrity Checks

Vendored queries are subject to threat T1 (compromised vendored query / KQL injection). To mitigate this:

- Each query file has a SHA-256 hash recorded in `manifest.json`
- CI validates hashes on every build before tests run
- Any tampered or modified query file triggers build failure
- Hash regeneration is explicit and auditable

See: `.squad/decisions/threat-model.md` for full threat analysis.

## Adding a New Query

When vendoring a new ALZ checklist query:

1. **Extract the query file** to the appropriate subdirectory:
   - `data/alz-queries/checklist/` for queries from `alz-checklist-queries`
   - `data/alz-queries/graph/` for queries from `alz-graph-queries`

2. **Update manifest.json** with the new file path in the `subset.files` array for the relevant source.

3. **Regenerate hashes**:
   ```bash
   python scripts/verify_query_integrity.py --update
   ```
   This computes SHA-256 for all query files and updates both `manifest.json` and `MANIFEST.md`.

4. **Commit the changes**:
   ```bash
   git add data/alz-queries/
   git commit -m "chore(alz-queries): add query <checklist-id>"
   ```

5. **Open a PR** with labels `squad`, `squad:atlas`, `vendoring`.

## Refreshing from Upstream

The weekly refresh workflow (`.github/workflows/refresh-alz-snapshot.yml`) automates upstream sync. For manual refresh:

1. **Run the refresh script**:
   ```bash
   python scripts/refresh_alz_snapshot.py
   ```
   This fetches latest commits, extracts queries, updates manifests, and regenerates hashes automatically.

2. **Review the diff** to identify new/changed/removed queries.

3. **Open a PR** with the refresh commit. The refresh workflow does this automatically.

## What CI Does on Tamper

If any query file is modified without updating its hash:

1. `python scripts/verify_query_integrity.py` runs in the CI `test` job
2. The script prints `FAIL: <file>` with expected vs actual hash
3. CI job exits with code 1, failing the build
4. PR cannot merge until hash is regenerated or file is restored

This protects against accidental edits or supply-chain compromise.

## Verification Command Reference

- **Verify integrity** (CI uses this):
  ```bash
  python scripts/verify_query_integrity.py
  ```
  Exit code 0 = all hashes match. Exit code 1 = integrity failure.

- **Regenerate hashes** (use after adding/modifying queries):
  ```bash
  python scripts/verify_query_integrity.py --update
  ```
  Rewrites `manifest.json` with new hashes and regenerates `MANIFEST.md`.

## Manifest Schema

`manifest.json` is the machine-readable source of truth. Each source entry contains:

```json
{
  "repo": "martinopedal/alz-checklist-queries",
  "commit_sha": "e7641beeda0126cc78825f8b77764c379552f3e1",
  "ref": "commit:e7641beeda0126cc78825f8b77764c379552f3e1",
  "vendored_at": "2026-04-22T12:35:39Z",
  "subset": {
    "source_file": "queries/alz_all_queries.json",
    "checklist_ids": ["54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a"],
    "files": ["data/alz-queries/checklist/54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a.kql"],
    "sha256": {
      "data/alz-queries/checklist/54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a.kql": "35c9f61e21f4aa19..."
    }
  },
  "file_count": 1
}
```

The `sha256` dictionary maps each file path to its SHA-256 hash (64-character hex string).

`MANIFEST.md` is the human-readable mirror, auto-generated from `manifest.json`.
