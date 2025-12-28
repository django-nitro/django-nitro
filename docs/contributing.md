# Contributing to Django Nitro

Thank you for your interest in contributing to Django Nitro! 🎉

## Quick Links

- [Full Contributing Guide](https://github.com/django-nitro/django-nitro/blob/main/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/django-nitro/django-nitro/blob/main/CODE_OF_CONDUCT.md)
- [Report Issues](https://github.com/django-nitro/django-nitro/issues)

## Development Setup

```bash
# Clone the repository
git clone https://github.com/django-nitro/django-nitro.git
cd django-nitro

# Create virtual environment
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black nitro/
isort nitro/
mypy nitro/
```

## How to Contribute

### 1. Report Bugs

[Open an issue](https://github.com/django-nitro/django-nitro/issues/new) with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Django Nitro version

### 2. Suggest Features

[Start a discussion](https://github.com/django-nitro/django-nitro/discussions) to propose new features.

### 3. Submit Pull Requests

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... code ...

# Run tests
pytest

# Commit with descriptive message
git commit -m "Add: Description of your changes"

# Push and create PR
git push origin feature/your-feature-name
```

## Contribution Guidelines

✅ **DO:**
- Add tests for new features
- Update documentation
- Follow existing code style
- Keep PRs focused and small

❌ **DON'T:**
- Submit large, unfocused PRs
- Break existing tests
- Ignore linter warnings
- Change unrelated code

## Code Style

- **Black** for formatting
- **isort** for imports
- **Type hints** required
- **Docstrings** for public APIs

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nitro

# Run specific test
pytest tests/test_base.py::test_component_render
```

## Documentation

Documentation lives in `docs/` and uses MkDocs Material.

```bash
# Install docs dependencies
pip install mkdocs-material

# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

## Questions?

- [GitHub Discussions](https://github.com/django-nitro/django-nitro/discussions)
- [Read the full guide](https://github.com/django-nitro/django-nitro/blob/main/CONTRIBUTING.md)

Thank you for contributing! 🙏
