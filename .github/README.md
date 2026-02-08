# GitHub Actions Setup

This repository contains CI/CD workflows for automated testing, building, and releasing `ollama-cli`.

## Workflows

### 1. Build and Test (`build-test.yml`)
Runs on every push to `main` and on all pull requests to `main`.

**Steps:**
- Checks out code
- Sets up Python 3.11
- Installs `uv` dependency manager
- Caches dependencies for faster builds
- Runs tests with `pytest`
- Runs `ruff` linter
- Runs import sort check

### 2. Release (`release.yml`)
Runs when a tag matching `v*` is pushed.

**Steps:**
- Checks out code with full history
- Sets up Python 3.11
- Builds the package with `uv build`
- Creates a GitHub Release with all artifacts from `dist/`

### 3. Deploy to PyPI (`pypi-publish.yml`)
Runs when a release is published.

**Steps:**
- Checks out code
- Sets up Python 3.11
- Deploys the package to PyPI using `pypa/gh-action-pypi-publish`

### 4. Auto Release (`autorelease.yml`)
Runs on push to `main` when the commit message contains `release:`.

**Steps:**
- Checks out code with full history
- Sets up Python 3.11
- Runs `semantic-release` to automatically version and tag the release

## Required GitHub Secrets

### PYPI_API_TOKEN
**Required for:** `pypi-publish.yml` workflow

This token is used to publish the package to PyPI.

**How to add:**

1. Go to your PyPI account: https://pypi.org/account/
2. Navigate to "Account settings" → "API tokens"
3. Create a new API token with scope "Entire account" (recommended for publishing)
4. Copy the token
5. Go to your GitHub repository: https://github.com/muah1987/ollama-cli/settings/secrets/actions
6. Click "New repository secret"
7. Name: `PYPI_API_TOKEN`
8. Value: paste your PyPI API token
9. Click "Add secret"

**Getting a PyPI API token:**

```bash
# Create a token at https://pypi.org/manage/account/token/
# Use: pypa/gh-action-pypi-publish action will handle authentication automatically
```

## Automatic Versioning

This repository uses `python-semantic-release` for automated versioning. The version is determined by commit message prefixes:

- `feat:` - Minor version bump (e.g., 0.1.0 → 0.2.0)
- `fix:` - Patch version bump (e.g., 0.1.0 → 0.1.1)
- `BREAKING CHANGE:` or `!` - Major version bump (e.g., 0.1.0 → 1.0.0)

**Example commits:**

```bash
git commit -m "feat: add new command for model deletion"
git commit -m "fix: resolve issue with streaming responses"
git commit -m "feat!: change API response format (BREAKING CHANGE)"
```

**To release a new version:**

```bash
# Make your changes and commit with conventional commit message
git add .
git commit -m "feat: new feature"
git push origin main

# Trigger auto-release by including 'release:' in commit message
git commit --allow-empty -m "release: prepare next version"
git push origin main
```

## Manual Tagging

You can also manually create a tag to trigger a release:

```bash
# Create and push a version tag
git tag v0.1.0
git push origin v0.1.0
```

This will trigger both the `release.yml` and `pypi-publish.yml` workflows.

## Local Development

Run the same checks locally before pushing:

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest tests/

# Run linter
uv run ruff check .

# Run type/import checks
uv run ruff check --select I .

# Build package
uv build
```

## Troubleshooting

**Build fails in CI:**
- Check Python version (must be 3.11+)
- Verify `uv.lock` is committed
- Ensure all dependencies are in `pyproject.toml`

**PyPI publish fails:**
- Verify `PYPI_API_TOKEN` secret is set
- Check the token has publish permissions
- Ensure the version hasn't already been published

**Auto-release doesn't trigger:**
- Commit message must contain `release:`
- Branch must be `main`
- Changes must be in `cmd/`, `api/`, `model/`, `server/`, `runner/`, or `pyproject.toml`