# Contributing to aiOla Python SDK

## Branch Strategy

This project follows a structured branching strategy with automated releases:

### Branch Types

- **`main`**: Production releases
  - Protected branch
  - All changes via Pull Requests
  - Triggers production releases to PyPI
  - Only stable, tested code

- **`rc`**: Release candidate branch  
  - Pre-production testing
  - Triggers pre-release versions (e.g., `1.0.0-rc.1`)
  - Used for final testing before main branch merge

- **`feature/*`**: Feature development branches
  - Created from `main` for new features
  - Merged back to `main` via Pull Request

- **`fix/*`**: Bug fix branches
  - Created from `main` for bug fixes
  - Merged back to `main` via Pull Request

## Commit Message Conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning:

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Types
- **feat**: New feature (triggers minor version bump)
- **fix**: Bug fix (triggers patch version bump)  
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **perf**: Performance improvements (triggers patch version bump)
- **test**: Adding/updating tests
- **build**: Build system changes
- **ci**: CI/CD changes
- **chore**: Maintenance tasks

### Examples
```bash
feat: add voice activity detection to STT streaming
fix: resolve audio buffer overflow in mic streaming
docs: update API documentation for TTS client
perf: optimize audio processing pipeline
```

### Breaking Changes
For breaking changes, add `!` after the type or add `BREAKING CHANGE:` in footer:
```bash
feat!: redesign client authentication API
# or
feat: add new authentication method

BREAKING CHANGE: The old authenticate() method is replaced with auth.login()
```

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following project conventions
   - Add tests for new functionality
   - Update documentation if needed

3. **Commit Changes**
   ```bash
   # Use conventional commit format
   git commit -m "feat: add your feature description"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request to main branch
   ```

5. **PR Validation**
   - Automated CI checks (linting, testing, build)
   - Commit message validation
   - Code review approval required

6. **Release Process**
   - Merge to `main` triggers automatic release
   - Version determined by commit types since last release
   - Changelog updated automatically
   - Package published to PyPI

## Release Candidate Testing

For major changes, use the `rc` branch for pre-release testing:

1. Create PR to `rc` branch first
2. Merge triggers pre-release (e.g., `1.0.0-rc.1`) published to **Test PyPI**
3. Test pre-release version from Test PyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ aiola==1.0.0-rc.1
   ```
4. When ready, merge `rc` to `main` for production release to **Production PyPI**

### Multi-Environment Support

The CD pipeline automatically selects the appropriate PyPI environment:

- **`rc` branch** → **Test PyPI** (https://test.pypi.org)
  - Pre-release versions with `-rc.X` suffix
  - Safe testing environment
  - Requires `TEST_PYPI_TOKEN` secret

- **`main` branch** → **Production PyPI** (https://pypi.org)  
  - Stable releases
  - Public package distribution
  - Requires `PYPI_TOKEN` secret

This approach ensures that experimental releases don't affect the production package while allowing thorough testing of release candidates.

## Local Development Setup

1. **Install Dependencies**
   ```bash
   uv sync --group dev
   ```

2. **Install Pre-commit Hooks**
   ```bash
   uv run pre-commit install
   uv run pre-commit install --hook-type commit-msg
   ```

3. **Run Tests**
   ```bash
   uv run pytest
   ```

4. **Check Linting**
   ```bash
   uv run ruff check .
   ```

5. **Test Commit Messages**
   ```bash
   uv run cz check --rev-range HEAD~1..HEAD
   ```

## Automated Release Process

The project uses [Python Semantic Release](https://python-semantic-release.readthedocs.io/) for automated releases:

- **Version Calculation**: Based on conventional commit messages
- **Changelog Generation**: Automatic based on commits since last release  
- **Tagging**: Automatic git tags in format `v{version}`
- **PyPI Publishing**: Automatic upload to PyPI
- **GitHub Releases**: Automatic GitHub release creation

### Version Bumping Rules
- `feat:` commits → Minor version bump (1.0.0 → 1.1.0)
- `fix:`, `perf:` commits → Patch version bump (1.0.0 → 1.0.1)
- `BREAKING CHANGE:` or `!` → Major version bump (1.0.0 → 2.0.0)
- Other types → No version bump

## Questions?

If you have questions about contributing, please:
1. Check existing issues and discussions
2. Create a new issue for bugs or feature requests
3. Join our community discussions