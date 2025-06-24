# Contributing to Nokia WebEM Generator

Thank you for your interest in contributing to Nokia WebEM Generator! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused

### Testing
- Write tests for new functionality
- Ensure all tests pass before submitting a pull request
- Run tests with: `python -m pytest` or `python test_basic.py`

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, etc.)
- Keep the first line under 50 characters

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add tests if applicable
4. Update documentation if needed
5. Ensure all tests pass
6. Submit a pull request with a clear description

## File Structure

When adding new files:
- Python modules go in the `modules/` directory
- HTML templates go in the `templates/` directory
- Static files (CSS, JS) go in a `static/` directory
- Tests go in the root directory with `test_` prefix

## Reporting Issues

When reporting issues:
- Use the issue template if available
- Provide clear steps to reproduce
- Include error messages and stack traces
- Specify your operating system and Python version

## Questions?

If you have questions about contributing, please open an issue or contact the maintainers. 