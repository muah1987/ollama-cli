# Release Process

This document describes the automated release process for cli-ollama.

## Overview

The project uses an automated release workflow with three key components:

1. **Semantic Release** - Automatically determines version numbers and generates changelogs based on conventional commits
2. **GitHub Releases** - Creates releases with built artifacts
3. **PyPI Publishing** - Deploys packages to Python Package Index using trusted publishing

## Release Workflows

### 1. Auto Release (`autorelease.yml`)

**Trigger:** Push to `main` branch with commit message containing `release:`

**What it does:**
- Runs `semantic-release` to analyze commit history
- Determines the next version based on conventional commits
- Updates version in `pyproject.toml`
- Updates `CHANGELOG.md`
- Creates a git tag (format: `v{version}`)
- Pushes the tag to GitHub

**Requirements:**
- Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) format
- `GH_TOKEN` secret must be configured in repository settings

### 2. Release Workflow (`release.yml`)

**Trigger:** Push of a tag matching `v*` pattern (e.g., `v0.2.0`)

**What it does:**
- Builds the Python package (wheel and sdist)
- Creates a GitHub Release
- Attaches build artifacts to the release
- Marks the release as latest

**Artifacts:**
- `cli_ollama-{version}-py3-none-any.whl` - Python wheel package
- `cli_ollama-{version}.tar.gz` - Source distribution (if built)

### 3. PyPI Publish (`pypi-publish.yml`)

**Trigger:** When a GitHub Release is published

**What it does:**
- Builds the package
- Publishes to PyPI using trusted publishing (OIDC)
- No manual API tokens required

**Requirements:**
- PyPI trusted publisher must be configured for this repository
- Repository must have `id-token: write` permission (already configured)

## Version Management

Current version: `0.2.0` (defined in `pyproject.toml`)

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Major** (x.0.0) - Breaking changes
- **Minor** (0.x.0) - New features (backward compatible)
- **Patch** (0.0.x) - Bug fixes (backward compatible)

### Version Bumping

Version bumps are determined automatically from commit messages:

- `feat:` → Minor version bump
- `fix:` → Patch version bump
- `feat!:` or `BREAKING CHANGE:` → Major version bump
- `docs:`, `style:`, `refactor:`, `test:`, `chore:` → No version bump

## How to Create a Release

### Automatic Release (Recommended)

1. Ensure all changes are committed with conventional commit messages
2. Push a commit to `main` with message containing `release:`:
   ```bash
   git commit --allow-empty -m "chore: release: trigger automated release"
   git push origin main
   ```
3. The autorelease workflow will:
   - Analyze commits since last release
   - Determine version bump
   - Create tag and GitHub Release
   - Trigger PyPI publication

### Manual Tag Creation (For Testing)

If you need to create a tag manually:

```bash
# Create and push a tag
git tag v0.2.0
git push origin v0.2.0
```

This will:
1. Trigger the `release.yml` workflow
2. Create a GitHub Release
3. Trigger PyPI publication

**Note:** Manual tags should only be used for testing or emergency releases. The automated process is preferred.

## Release Checklist

Before creating a release:

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Linting passes (`ruff check .`)
- [ ] Code is formatted (`ruff format .`)
- [ ] Build succeeds (`uv build`)
- [ ] CHANGELOG.md is updated (automatic with semantic-release)
- [ ] Documentation is current
- [ ] Version number in `pyproject.toml` reflects intended release

## Troubleshooting

### Semantic Release Configuration

The semantic-release configuration is in `pyproject.toml` under `[tool.semantic_release]`.

Key settings:
- `version_toml = ["pyproject.toml:project.version"]` - Where to update version
- `commit_parser = "conventional"` - Uses conventional commit format
- `tag_format = "v{version}"` - Tag naming pattern
- `upload_to_pypi = false` - PyPI upload handled by separate workflow
- `upload_to_release = true` - Upload artifacts to GitHub Release

### Build Artifacts

To verify build artifacts locally:

```bash
# Build the package
uv build

# Check the dist/ directory
ls -la dist/

# Should contain:
# - cli_ollama-X.Y.Z-py3-none-any.whl
```

### PyPI Trusted Publishing

The repository uses [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) which eliminates the need for API tokens.

To configure (repository owner only):
1. Go to PyPI project settings
2. Add GitHub as a trusted publisher
3. Specify: `muah1987/cli-ollama` and workflow `pypi-publish.yml`

### Failed Workflows

If a workflow fails:

1. Check the Actions tab for error logs
2. Verify all secrets are configured (`GH_TOKEN`)
3. Ensure commit messages follow conventional format
4. Check that PyPI trusted publisher is configured
5. Verify version number doesn't already exist on PyPI

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for detailed version history.

## Related Documentation

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Python Semantic Release](https://python-semantic-release.readthedocs.io/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
