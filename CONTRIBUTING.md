# Contributing to MCP Telegram

Thank you for your interest in contributing to MCP Telegram! This document provides guidelines and instructions for contributing to this project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/dryeab/mcp-telegram.git
   cd mcp-telegram
   ```

2. **Set up Python environment**
   - This project requires Python 3.10 or higher
   - We use `uv` as our package manager. If you haven't installed it yet:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Create and activate a virtual environment:
     ```bash
     uv venv
     source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
     ```

3. **Install dependencies**
   ```bash
   uv pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

1. **Create a new branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**
   - Write clear, concise commit messages
   - Follow the existing code style
   - Update documentation as needed

3. **Run checks**
   - Run pre-commit hooks on your changes
   - Fix any linting issues reported by ruff

4. **Submit a Pull Request**
   - Push your changes to your fork
   - Create a Pull Request with a clear description of the changes
   - Link any related issues

## Code Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions, classes, and modules
- Keep functions focused and single-purpose
- Use meaningful variable and function names

## Commit Guidelines

- Use clear and descriptive commit messages
- Start with a verb in the present tense (e.g., "Add", "Fix", "Update")
- Reference issue numbers when applicable
- Keep commits focused and atomic

## Documentation

- Update the README.md for any user-facing changes
- Add docstrings for new functions and classes
- Include examples for new features

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. The PR may be merged once you have the sign-off of at least one maintainer

## Questions or Need Help?

- Open an issue for any questions
- Tag maintainers for urgent matters
- Be respectful and constructive in discussions

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

Thank you for contributing to MCP Telegram! 