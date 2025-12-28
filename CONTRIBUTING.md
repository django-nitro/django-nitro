# Contributing to Django Nitro

Thank you for your interest in contributing to Django Nitro! We welcome contributions from the community.

## Code of Conduct

Be respectful and constructive in all interactions. We're all here to learn and build something great together.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear title and description
- Steps to reproduce the bug
- Expected vs actual behavior
- Django, Python, and django-nitro versions
- Code samples or screenshots if applicable

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been requested
- Clearly describe the use case and benefits
- Provide examples of how it would work

### Pull Requests

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/my-awesome-feature
   ```

2. **Set up the development environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Run the example project** to test your changes:
   ```bash
   cd example
   python manage.py migrate
   python manage.py runserver
   ```

4. **Make your changes:**
   - Write clean, readable code
   - Follow PEP 8 style guidelines (we use `black` for formatting)
   - Add docstrings to classes and methods
   - Update documentation if needed

5. **Test your changes:**
   ```bash
   # Format code
   black nitro/
   isort nitro/

   # Type check
   mypy nitro/

   # Run tests
   pytest
   ```

6. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

   Use conventional commit prefixes:
   - `Add:` new features
   - `Fix:` bug fixes
   - `Update:` changes to existing features
   - `Docs:` documentation changes
   - `Refactor:` code refactoring
   - `Test:` test additions or changes

7. **Push and create a pull request:**
   ```bash
   git push origin feature/my-awesome-feature
   ```

   Then open a PR on GitHub with:
   - Clear description of what changed and why
   - Link to related issues
   - Screenshots/GIFs for UI changes

## Development Guidelines

### Code Style

- Follow PEP 8 (enforced by `black`)
- Use type hints where possible
- Keep functions small and focused
- Write descriptive variable names

### Documentation

- Add docstrings to all public classes and methods
- Update README.md if adding new features
- Add examples for new functionality
- Keep CHANGELOG.md updated

### Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage
- Test with multiple Python/Django versions if possible

### Project Structure

```
django-nitro/
├── nitro/              # Main package (DO modify)
│   ├── base.py        # Component base classes
│   ├── api.py         # Django Ninja API
│   ├── registry.py    # Component registration
│   └── static/        # JavaScript files
├── examples/           # Example projects (modify if improving examples)
├── tests/             # Test suite (DO add tests here)
└── docs/              # Documentation (DO update)
```

### What to Contribute

**Great contributions:**
- Bug fixes
- Performance improvements
- Better error messages
- Documentation improvements
- New examples
- Test coverage improvements

**Needs discussion first (open an issue):**
- Breaking changes to the API
- Major new features
- Architectural changes

## Questions?

- Open an issue for technical questions
- Use GitHub Discussions for general questions
- Check existing issues and PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Django Nitro!** 🚀
