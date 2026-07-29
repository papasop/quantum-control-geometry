# Contributing to Quantum Control Geometry

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Maintain scientific rigor and honesty

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/papasop/quantum-control-geometry/issues)
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs. actual behavior
   - Python version and dependencies
   - Minimal code example

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create an issue with:
   - Clear description of the enhancement
   - Use case and motivation
   - Proposed implementation (if applicable)

### Pull Requests

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Make your changes**:
   - Follow code style (see below)
   - Add tests for new functionality
   - Update documentation
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

## Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use type hints for all functions
- Write docstrings in [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html)

### Mathematical Notation

- Use clear variable names (e.g., `covariant_tensor` not `ct`)
- Document mathematical formulas in docstrings
- Reference papers/theorems where applicable

### Testing

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use descriptive test names

## Development Setup

```bash
# Clone repository
git clone https://github.com/papasop/quantum-control-geometry.git
cd quantum-control-geometry

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Type check
mypy src/
```

## Documentation

- Update documentation for any API changes
- Use clear examples in docstrings
- Keep theory documentation mathematically rigorous

## Review Process

1. All submissions require review
2. Reviewers will check:
   - Code quality and style
   - Test coverage
   - Documentation
   - Mathematical correctness
3. Address feedback and update your PR

## Questions?

- Open a [Discussion](https://github.com/papasop/quantum-control-geometry/discussions)
- Check existing documentation

Thank you for contributing! 🎉
