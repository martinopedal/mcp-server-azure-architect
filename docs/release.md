# Release Process

Operator runbook for cutting a release of `mcp-server-azure-architect`.

## Overview

Releases are tag-triggered and automated via GitHub Actions. The `.github/workflows/release.yml` workflow handles:
- Version verification (tag must match `pyproject.toml`)
- Full test matrix execution
- Building sdist + wheel
- Publishing to PyPI via OIDC (no secrets)
- Creating a GitHub Release with CHANGELOG excerpt

## Prerequisites (One-Time Setup)

### PyPI Trusted Publishing

The first publish to PyPI for a new package name requires manual setup:

1. **Create PyPI account** (if not already done): https://pypi.org/account/register/
2. **Add "Pending Publisher"** in PyPI:
   - Go to https://pypi.org/manage/account/publishing/
   - Click "Add a new pending publisher"
   - Fill in:
     - **PyPI Project Name:** `mcp-server-azure-architect`
     - **Owner:** `martinopedal`
     - **Repository name:** `mcp-server-azure-architect`
     - **Workflow name:** `release.yml`
     - **Environment name:** `pypi`
   - Click "Add"

3. **Verify GitHub Actions environment** (if not already created):
   - Go to https://github.com/martinopedal/mcp-server-azure-architect/settings/environments
   - Create environment named `pypi` (if it doesn't exist)
   - No additional protection rules needed for OIDC, but you may add required reviewers if desired

Once the first release publishes successfully, the package name is claimed on PyPI and subsequent releases will publish automatically.

## Release Checklist

### 1. Update CHANGELOG.md

Move the `## [Unreleased]` section to a versioned section with today's date:

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
- New tool: `foo_bar`
...
```

Add the new version link at the bottom:

```markdown
[Unreleased]: https://github.com/martinopedal/mcp-server-azure-architect/compare/vX.Y.Z...HEAD
[X.Y.Z]: https://github.com/martinopedal/mcp-server-azure-architect/releases/tag/vX.Y.Z
```

### 2. Bump version in pyproject.toml

Edit `pyproject.toml`:

```toml
[project]
name = "mcp-server-azure-architect"
version = "X.Y.Z"  # Update this line
```

### 3. Commit and tag

```bash
git add CHANGELOG.md pyproject.toml
git commit -m "chore(release): vX.Y.Z

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git tag vX.Y.Z
git push origin main --follow-tags
```

**Important:** Use `--follow-tags` to push both the commit and the tag in one operation. The tag push triggers the release workflow.

### 4. Monitor the release workflow

1. Go to https://github.com/martinopedal/mcp-server-azure-architect/actions
2. Find the "Release" workflow run for your tag
3. Wait for all jobs to complete:
   - `verify-version` - Confirms tag matches pyproject.toml version
   - `test` - Runs full test matrix (ubuntu-latest, Python 3.11 + 3.12)
   - `build` - Builds sdist + wheel, uploads artifacts
   - `publish-pypi` - Publishes to PyPI via OIDC
   - `create-release` - Creates GitHub Release with CHANGELOG excerpt

If any job fails, investigate the logs. Common issues:
- **Tag mismatch:** Tag `vX.Y.Z` does not match `pyproject.toml` version. Fix: delete the tag locally and remotely, update pyproject.toml, re-tag and push.
- **Test failures:** A test broke between the last CI run and now. Fix: revert the tag, fix the test, re-release.
- **PyPI publish failure (first release only):** Trusted publishing not set up. Follow "Prerequisites" above.

### 5. Verify the release

1. **PyPI:** Visit https://pypi.org/project/mcp-server-azure-architect/ and confirm the new version appears.
2. **GitHub Release:** Visit https://github.com/martinopedal/mcp-server-azure-architect/releases and confirm the release was created with correct CHANGELOG body.
3. **Smoke test:** Install the new version locally and verify it works:
   ```bash
   uvx mcp-server-azure-architect@X.Y.Z
   ```

## SemVer Guidelines

See [ADR-005](adr/0005-semver-and-release-cadence.md) for detailed SemVer policy.

**Quick reference (pre-1.0):**
- **MINOR (`0.y.0`):** New tools. Breaking changes to tool signatures. ALZ query snapshot refreshes. `mcp-config.json` schema changes.
- **PATCH (`0.y.z`):** Bug fixes. Docs. Internal refactors. No user-visible behavior changes.

**Quick reference (post-1.0):**
- **MAJOR (`X.0.0`):** Breaking changes to tool names, parameters, or return shapes. Tool removals.
- **MINOR (`X.y.0`):** New tools. New optional parameters. Backward-compatible changes.
- **PATCH (`X.y.z`):** Bug fixes. Docs. Security patches.

## Rollback

If a release is broken:

1. **Yank the release on PyPI** (does not delete, just hides from default queries):
   ```bash
   # Requires PyPI API token with maintainer role
   pip install twine
   twine upload --repository pypi dist/*  # You'll need credentials
   # OR: use PyPI web UI to yank the release
   ```

2. **Delete the GitHub Release** (optional):
   - Go to https://github.com/martinopedal/mcp-server-azure-architect/releases
   - Click the release, then "Delete"

3. **Fix the issue and cut a new patch release** (e.g., if `0.1.0` is broken, cut `0.1.1`).

Do **not** delete the Git tag or force-push. Tags are immutable once published to PyPI.

## Troubleshooting

### "Trusted publishing configuration not found"

**Cause:** PyPI trusted publishing is not set up for the package name.

**Fix:** Follow "Prerequisites" above. For the first release, you must manually configure the pending publisher on PyPI.

### "Environment protection rules not satisfied"

**Cause:** The `pypi` environment in GitHub has required reviewers configured, and no approval was given.

**Fix:** Either approve the deployment in the Actions UI, or remove the protection rule if auto-deploy is desired.

### "Version already exists on PyPI"

**Cause:** You're trying to publish a version that already exists. PyPI does not allow overwriting releases.

**Fix:** Bump to a new version (e.g., `0.1.1` instead of `0.1.0`) and re-tag.

## Contact

For release process questions, ping @martinopedal or open an issue.
