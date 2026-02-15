# GitHub Repository Settings Setup Guide

This guide provides step-by-step instructions for configuring GitHub repository settings required for the qarin-cli project workflows.

## Table of Contents

1. [Required Secrets](#required-secrets)
2. [Repository Settings](#repository-settings)
3. [PyPI Trusted Publisher Setup](#pypi-trusted-publisher-setup)
4. [Workflow Permissions](#workflow-permissions)
5. [Verification Steps](#verification-steps)

---

## Required Secrets

Navigate to: **Settings → Secrets and variables → Actions → Repository secrets**

### Essential Secrets (Required for Release)

#### 1. GH_TOKEN
- **Description:** GitHub Personal Access Token for semantic-release
- **Required for:** Auto-release workflow, creating tags and releases
- **Permissions needed:**
  - `repo` (Full control of private repositories)
  - `write:packages` (if using GitHub Packages)
  - `workflow` (Update GitHub Action workflows)
- **How to create:**
  1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. Click "Generate new token (classic)"
  3. Name: `Qarin CLI Release Token`
  4. Select scopes: `repo`, `workflow`
  5. Generate token and copy the value
  6. Add to repository secrets as `GH_TOKEN`

**Note:** The built-in `GITHUB_TOKEN` has limited permissions and cannot trigger subsequent workflows. Use a Personal Access Token instead.

### Optional Secrets (For Testing)

These secrets are optional and only needed if you want to run tests with actual API providers:

#### 2. ANTHROPIC_API_KEY
- **Description:** Anthropic Claude API key
- **Required for:** Testing Claude provider integration
- **How to get:** https://console.anthropic.com/

#### 3. GEMINI_API_KEY
- **Description:** Google Gemini API key
- **Required for:** Testing Gemini provider integration
- **How to get:** https://makersuite.google.com/app/apikey

#### 4. OPENAI_API_KEY
- **Description:** OpenAI API key
- **Required for:** Testing OpenAI/Codex provider integration
- **How to get:** https://platform.openai.com/api-keys

#### 5. HF_TOKEN
- **Description:** Hugging Face API token
- **Required for:** Testing Hugging Face provider integration
- **How to get:** https://huggingface.co/settings/tokens

#### 6. CODECOV_TOKEN
- **Description:** Codecov upload token (optional)
- **Required for:** Code coverage reporting
- **How to get:** https://codecov.io/gh/muah1987/qarin-cli/settings

**Note:** Tests will skip provider-specific tests if these tokens are not configured. The test suite is designed to work without them.

---

## Repository Settings

### General Settings

Navigate to: **Settings → General**

#### Default branch
- Ensure `main` is set as the default branch

#### Pull Requests
- ✅ Allow merge commits
- ✅ Allow squash merging
- ✅ Allow rebase merging
- ✅ Always suggest updating pull request branches
- ✅ Allow auto-merge
- ✅ Automatically delete head branches

#### Tags
- ✅ No special configuration needed
- Tags are created automatically by semantic-release

### Actions Settings

Navigate to: **Settings → Actions → General**

#### Actions permissions
- ✅ Allow all actions and reusable workflows

#### Workflow permissions
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

**Important:** These permissions are required for:
- Auto-release workflow to create tags and releases
- Dependabot auto-merge workflow
- Build and test workflows to update status

---

## PyPI Trusted Publisher Setup

✅ **Already Configured** - PyPI Trusted Publishing is set up for this repository.

### Current Configuration

The repository is configured to use OIDC-based trusted publishing:

- **Publisher:** GitHub Actions
- **Repository:** muah1987/qarin-cli
- **Workflow:** pypi-publish.yml
- **Authentication:** OIDC (no API tokens required)

### How It Works

When a GitHub Release is published:
1. The `pypi-publish.yml` workflow runs
2. GitHub generates a short-lived OIDC token
3. PyPI verifies the token and allows the upload
4. Package is published to https://pypi.org/project/qarin-cli/

No manual API token management is needed.

---

## Workflow Permissions

The following workflows require specific permissions (already configured in workflow files):

### autorelease.yml
```yaml
permissions:
  contents: write  # Create tags and releases
```

### release.yml
```yaml
permissions:
  contents: write  # Create releases and upload artifacts
```

### pypi-publish.yml
```yaml
permissions:
  contents: read   # Read repository contents
  id-token: write  # OIDC token for PyPI trusted publishing
```

### build-test.yml
```yaml
permissions:
  contents: read  # Read repository contents for testing
```

---

## Verification Steps

After completing the setup, verify everything works:

### 1. Test Build Workflow

Push a commit to a branch and verify the build workflow runs successfully:

```bash
git checkout -b test-workflows
git commit --allow-empty -m "test: verify workflows"
git push origin test-workflows
```

Check: **Actions → Build and Test** should complete successfully

### 2. Test Auto-Release (Dry Run)

Check that semantic-release configuration is valid:

```bash
# Locally
uv run semantic-release version --print
```

Should output version information without errors.

### 3. Create First Release

To create your first release:

```bash
# On main branch
git commit --allow-empty -m "chore: release: trigger first automated release"
git push origin main
```

Check:
1. **Actions → Auto Release** - Should create tag and GitHub Release
2. **Actions → Release** - Should build and upload artifacts
3. **Actions → Deploy to PyPI** - Should publish to PyPI (if trusted publisher configured)

### 4. Verify Release Artifacts

After release workflow completes:

1. **GitHub Releases:** https://github.com/muah1987/qarin-cli/releases
   - Should show new release with `.whl` and `.tar.gz` files
   
2. **PyPI:** https://pypi.org/project/qarin-cli/
   - Should show new version
   
3. **Install Test:**
   ```bash
   pip install qarin-cli
   qarin-cli --version
   ```

---

## Troubleshooting

### GH_TOKEN Issues

**Error:** "Resource not accessible by integration"
- **Solution:** Ensure GH_TOKEN has `repo` and `workflow` scopes
- **Check:** Token permissions in GitHub settings

**Error:** "Bad credentials"
- **Solution:** GH_TOKEN might be expired or invalid
- **Action:** Regenerate the token and update the secret

### PyPI Publishing Issues

**Error:** "Invalid or non-existent authentication information"
- **Solution:** Verify trusted publisher is configured correctly
- **Check:** PyPI project settings match workflow configuration exactly

**Error:** "File already exists"
- **Solution:** Version already published to PyPI
- **Action:** Bump version number in pyproject.toml

### Workflow Permission Issues

**Error:** "Resource not accessible by integration"
- **Solution:** Check workflow permissions in Settings → Actions → General
- **Action:** Enable "Read and write permissions"

---

## Summary Checklist

Use this checklist to ensure all settings are configured:

- [ ] **GH_TOKEN secret** added with correct permissions
- [ ] **Workflow permissions** set to "Read and write"
- [ ] **Auto-merge enabled** for Dependabot PRs
- [ ] **PyPI trusted publisher** configured (if publishing)
- [ ] **Default branch** set to `main`
- [ ] **Auto-delete head branches** enabled
- [ ] **Build workflow** verified (run test)
- [ ] **Semantic-release** configuration tested locally
- [ ] **First release** created and verified
- [ ] **PyPI package** installable

---

## Additional Resources

- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [Semantic Release Documentation](https://python-semantic-release.readthedocs.io/)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

**Last Updated:** 2026-02-14  
**For:** qarin-cli v0.2.0+
