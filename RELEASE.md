# Release Process

This document describes the process for releasing a new version of an individual skill.

Since guppi-skills is a multi-skill monorepo, each skill is versioned and tagged independently. There are no repo-wide releases.

## Prerequisites

- Clean working directory (`git status` shows no uncommitted changes)
- All tests passing for the skill (`cd <name>/ && uv run pytest`)
- On the `main` branch
- Push access to the repository

## Version Bumping

Skills follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes, incompatible CLI changes
- **MINOR** (0.X.0): New features, backward-compatible
- **PATCH** (0.0.X): Bug fixes, backward-compatible

If not specified, the agent should prompt for version bump type (major/minor/patch).

## Release Steps

### 1. Update Version

Update the version in all three locations:

- `<name>/pyproject.toml` — `version = "X.Y.Z"`
- `<name>/src/guppi_<name>/__init__.py` — `__version__ = "X.Y.Z"`
- `<name>/SKILL.md` — `version: "X.Y.Z"` (in YAML frontmatter)

### 2. Commit Version Bump

```bash
git add <name>/pyproject.toml <name>/src/guppi_<name>/__init__.py <name>/SKILL.md
git commit -m "Bump <name> to X.Y.Z"
git push
```

### 3. Create Git Tag

Tags are scoped to the skill using `<name>/vX.Y.Z` format:

```bash
git tag -a <name>/vX.Y.Z -m "<name> version X.Y.Z"
git push origin <name>/vX.Y.Z
```

### 4. Verify Installation

```bash
cd <name>/
uv tool install .
guppi-<name> --help
guppi-<name> skill show   # Verify SKILL.md version matches
```

## Example

Releasing spiker v0.2.0:

```bash
# 1. Update version in 3 files (pyproject.toml, __init__.py, SKILL.md)
# 2. Commit
git add spiker/pyproject.toml spiker/src/guppi_spiker/__init__.py spiker/SKILL.md
git commit -m "Bump spiker to 0.2.0"
git push

# 3. Tag
git tag -a spiker/v0.2.0 -m "spiker version 0.2.0"
git push origin spiker/v0.2.0

# 4. Verify
cd spiker/ && uv tool install . && guppi-spiker --help
```

## Rollback

If a release has issues:

1. Delete the git tag: `git tag -d <name>/vX.Y.Z && git push origin :refs/tags/<name>/vX.Y.Z`
2. Revert the version bump commit
3. Fix the issue and re-release
