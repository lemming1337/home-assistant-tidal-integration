# Contributing to Tidal Home Assistant Integration

Thank you for your interest in contributing to the Tidal Home Assistant Integration! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with the following information:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**:
   - Home Assistant version
   - Integration version
   - Python version
6. **Logs**: Relevant log entries (enable debug logging if possible)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:

1. **Description**: Clear description of the enhancement
2. **Use Case**: Why this enhancement would be useful
3. **Proposed Solution**: Your ideas on how to implement it
4. **Alternatives**: Any alternative solutions you've considered

### Pull Requests

1. **Fork the Repository**: Create your own fork of the project
2. **Create a Branch**: Create a branch for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make Your Changes**: Implement your feature or bugfix
4. **Test Your Changes**: Ensure everything works as expected
5. **Commit Your Changes**: Use clear and descriptive commit messages
   ```bash
   git commit -m "Add feature: description of feature"
   ```
6. **Push to Your Fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**: Submit a PR to the main repository

## Development Setup

### Prerequisites

- Python 3.11 or newer
- Home Assistant development environment
- Tidal API credentials for testing

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/lemming1337/home-assistant-tidal-integration.git
   cd home-assistant-tidal-integration
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Link the integration to your Home Assistant installation:
   ```bash
   ln -s $(pwd)/custom_components/tidal /path/to/homeassistant/custom_components/tidal
   ```

### Testing

Before submitting a PR, ensure:

1. **Code Quality**: Run linters and formatters
   ```bash
   black custom_components/tidal
   pylint custom_components/tidal
   ```

2. **Functionality**: Test the integration in a Home Assistant instance
3. **Documentation**: Update documentation if needed

## Coding Guidelines

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://github.com/psf/black) for code formatting
- Maximum line length: 100 characters
- Use type hints where possible

### Code Structure

- Keep functions and methods focused on a single responsibility
- Use descriptive variable and function names
- Add docstrings to all public functions and classes
- Include type hints for function parameters and return values

### Example:

```python
async def get_user_playlists(self) -> list[dict[str, Any]]:
    """Get user's playlists.

    Returns:
        List of playlist data

    Raises:
        TidalAuthError: If authentication fails
        TidalConnectionError: If connection fails
    """
    response = await self._request("GET", f"userCollections/{self._user_id}/playlists")
    return response.get("data", [])
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Update translation files if adding new strings
- Include examples for new features

### Commit Messages

Use clear, descriptive commit messages:

- **Good**: "Add support for creating playlists"
- **Bad**: "Fix stuff"

Format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Project Structure

```
home-assistant-tidal-integration/
├── custom_components/
│   └── tidal/
│       ├── __init__.py           # Integration setup
│       ├── api.py                # Tidal API client
│       ├── config_flow.py        # Configuration flow
│       ├── const.py              # Constants
│       ├── coordinator.py        # Data update coordinator
│       ├── llm_tools.py          # LLM tools
│       ├── manifest.json         # Integration manifest
│       ├── media_player.py       # Media player entity
│       ├── sensor.py             # Sensor entities
│       ├── services.py           # Services
│       ├── services.yaml         # Service definitions
│       ├── strings.json          # Default strings
│       └── translations/         # Translation files
│           ├── en.json
│           └── de.json
├── .gitignore
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── hacs.json
└── requirements.txt
```

## Areas for Contribution

Here are some areas where contributions are especially welcome:

1. **Testing**: Add unit tests and integration tests
2. **Documentation**: Improve or translate documentation
3. **Features**: Implement new features from the issue tracker
4. **Bug Fixes**: Fix reported bugs
5. **Performance**: Optimize API calls and data processing
6. **UI/UX**: Improve configuration flow and user interface

## Questions?

If you have questions about contributing, feel free to:

- Open a discussion on GitHub
- Comment on relevant issues
- Reach out to maintainers

## Recognition

Contributors will be recognized in:

- The project's README
- Release notes
- GitHub contributors page

Thank you for contributing to making this integration better!
