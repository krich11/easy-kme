# Contributing to Easy-KME

Thank you for your interest in contributing to Easy-KME! This document provides guidelines and information for contributors.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

- Use the GitHub issue tracker
- Include detailed steps to reproduce the bug
- Provide system information and error messages
- Check if the bug has already been reported

### Suggesting Enhancements

- Use the GitHub issue tracker with the "enhancement" label
- Clearly describe the proposed feature
- Explain why this enhancement would be useful
- Include mockups or examples if applicable

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Git

### Local Development

1. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/easy-kme.git
   cd easy-kme
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Set up the database:
   ```bash
   # Database setup instructions will be provided
   ```

5. Run tests:
   ```bash
   pytest
   ```

## Coding Standards

### Python Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions and classes focused and small
- Write docstrings for all public functions and classes

### Security Considerations

- Never commit sensitive data (keys, passwords, etc.)
- Follow security best practices for cryptographic operations
- Validate all inputs
- Use parameterized queries for database operations

### Testing

- Write unit tests for new functionality
- Maintain test coverage above 80%
- Include integration tests for critical paths
- Test error conditions and edge cases

## Documentation

- Update README.md if adding new features
- Add docstrings to new functions and classes
- Update API documentation if changing endpoints
- Include usage examples

## Commit Messages

Use clear, descriptive commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

Example:
```
Add user authentication system

- Implement JWT token-based authentication
- Add login/logout endpoints
- Include password hashing with bcrypt
- Add user role management

Fixes #123
```

## Review Process

1. All pull requests require review
2. At least one maintainer must approve
3. All CI checks must pass
4. Code must follow project standards

## Getting Help

- Check existing issues and pull requests
- Join our community discussions
- Contact maintainers for guidance

## License

By contributing to Easy-KME, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Easy-KME! 
