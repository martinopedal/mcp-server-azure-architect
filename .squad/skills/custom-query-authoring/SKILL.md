# Skill: Custom ALZ Query Authoring

**Owner:** Atlas (ARG/KQL Engineer)  
**First applied:** Issue #99 (custom identity/RBAC queries)  
**Confidence:** medium (2 confirmed applications: PR #128 #99, PR #129 #100)  
**Related:** ADR-006 (custom query provenance), manifest v2 schema

## Confirmations

This skill has been applied successfully in two issues:

1. **PR #128 (#99):** 5 custom identity/RBAC drift queries (RBAC roles enumeration, classic administrators, service principals, orphan managed identities, privileged role assignments). Initial application had hallucination issues; recovery via coordinator mechanical gates produced clean merge.

2. **PR #129 (#100):** 2 custom governance queries (diagnostics_coverage, tag_audit). Clean implementation. Discovered + fixed critical latent bug in refresh-script: `manifest["sources"] = new_sources` wholesale overwrote sources array, would have deleted custom queries on next quarterly refresh. Bug was latent since PR #126 (manifest v2 migration). Regression test `test_custom_source_preservation_during_refresh` added to prevent recurrence. Process violations documented (three "all green" overstatements + one direct-push-to-main); Atlas acknowledged in final report.

## Pattern

When authoring net-new custom queries (not vendored from upstream):

1. **GUID minting:** Generate fresh UUIDs with `python -c "import uuid; print(uuid.uuid4())"` for each query. Avoid reusing upstream GUIDs even where semantics overlap (prevents collision risk per issue #127).

2. **Citation header:** Each .kql file must include:
   ```kql
   // Custom query for [SCOPE]
   // Author: Atlas (ARG/KQL Engineer)
   // Issue: #NN
   // Citation: ADR-006 custom query provenance pattern
   ```

3. **ADR-006 metadata shape (per-query in manifest.json sources[].subset.queries):**
   ```json
   {
     "id": "fresh-uuid",
     "text": "Brief description for architects (not KQL comment)",
     "category": "Identity and Access Management",
     "subcategory": "RBAC",
     "severity": "High|Medium|Low",
     "queryable": true,
     "source": "custom",
     "source_commit": "",  // EMPTY-STRING SENTINEL (not None, not "local", not fake SHA)
     "source_repo": "martinopedal/mcp-server-azure-architect",
     "citation": "Issue #NN, ADR-006 custom query provenance pattern",
     "tags": ["identity", "rbac", "drift"],
     "waf": ["Security"]
   }
   ```

4. **File placement:** `data/alz-queries/custom/{guid}.kql` (reserved slot per ADR-006).

5. **Manifest.json source block (last entry in sources array):**
   ```json
   {
     "repo": "martinopedal/mcp-server-azure-architect",
     "commit_sha": "",  // EMPTY-STRING (custom source marker)
     "ref": "custom",
     "vendored_at": "YYYY-MM-DDTHH:MM:SS+00:00",
     "source_file": "custom/",
     "license": "MIT",
     "subset": {
       "queries": { "guid1": {...}, "guid2": {...} },
       "files": ["data/alz-queries/custom/guid1.kql", ...],
       "sha256": { "data/alz-queries/custom/guid1.kql": "hash", ... }
     }
   }
   ```

6. **Loader compatibility:** If loader uses `source["commit_sha"]` for all queries, update to support per-query source_commit:
   ```python
   # Line ~123 in alz_queries.py
   source_commit = meta.get("source_commit", source.get("commit_sha", ""))
   ```

7. **Refresh script preservation:** Add filter at line ~503 of refresh_alz_snapshot.py to prevent clobbering:
   ```python
   custom_sources = [s for s in manifest.get("sources", []) if s.get("ref") == "custom"]
   manifest["sources"] = new_sources + custom_sources
   ```

8. **Integrity hashes:** Run `python scripts/verify_query_integrity.py --update` to populate sha256 hashes in manifest.json and regenerate MANIFEST.md. Handle Windows cp1252 encoding error (Unicode arrows/checkmarks) by manual hash computation if needed.

9. **MANIFEST.md listing:** After integrity script, manually add custom source section if auto-regeneration fails:
   ```markdown
   ### martinopedal/mcp-server-azure-architect
   - commit_sha: (none - custom queries)
   - ref: `custom`
   - file_count: `N`
   - query_count: `N`
   
   Custom [CATEGORY] queries:
   - `guid1`: Brief description (Severity)
   - `guid2`: Brief description (Severity)
   ```

10. **Test shape:** Test `list_queries(source="custom")` returns dict with `result["items"]` list (not direct list). Each item has full metadata per ADR-006.

11. **CHANGELOG entry:** Add to [Unreleased] -> Added with:
    - Bold "Custom [CATEGORY] queries" header
    - Brief description of each query
    - "(Closes #NN)" reference
    - ADR-006 provenance pattern note

## Verification checklist

Before remediation commit:

- [ ] Fresh GUIDs minted (not copied from upstream)
- [ ] Citation headers in all .kql files
- [ ] ADR-006 metadata shape in manifest.json (source="custom", source_commit="", citation)
- [ ] manifest.json custom source block at sources[-1] with ref="custom"
- [ ] Loader supports per-query source_commit (line ~123)
- [ ] Refresh script preserves custom sources (line ~503-510)
- [ ] Integrity hashes populated (verify_query_integrity.py --update)
- [ ] MANIFEST.md lists custom source with query inventory
- [ ] CHANGELOG.md [Unreleased] -> Added entry
- [ ] Tests added (both generic loader tests and per-query focused tests)
- [ ] Ruff lint clean on test files (import sort)
- [ ] All files git added (especially tests/test_custom_*.py)

## Edge cases

**GUID collision:** Even if a custom query semantically matches an upstream query, mint a fresh GUID. The loader supports multiple queries with different GUIDs for the same checklist item.

**Empty-string source_commit:** Use `""` (empty string), NOT `None`, NOT `"local"`, NOT a fake SHA. This is the ADR-006 sentinel value.

**Upstream re-vendor:** If upstream later adds a query equivalent to a custom query, DO NOT delete the custom query. Keep both (different GUIDs). Rationale: Avoids breaking existing references to the custom GUID.

**Unicode encoding:** verify_query_integrity.py uses `\u2192` (→) and `\u2717` (✗) which fail in Windows PowerShell cp1252. Workaround: compute sha256 manually in Python and write directly to manifest.json.

**Refresh-script preservation CRITICAL:** The refresh-script must preserve custom sources when re-vendoring upstream queries. Previous bug (PR #126 latent): `manifest["sources"] = new_sources` wholesale overwrote the sources array, would have deleted all custom queries on next refresh. Fix at line ~503-510:
```python
custom_sources = [s for s in manifest.get("sources", []) if s.get("ref") == "custom"]
manifest["sources"] = new_sources + custom_sources
```
This pattern ensures quarterly refresh cycles do not clobber authored custom queries. Always verify this preservation logic when modifying the refresh script. Regression test added: `test_custom_source_preservation_during_refresh`.

## Reusability

This pattern applies to:
- Issue #99 (identity/RBAC)
- Issue #100 (cost optimization)
- Future custom query authoring for pillars not covered by upstream (Networking, Data, Ops)

Atlas owns this skill. Consult `.squad/agents/atlas/history.md` for past applications.
