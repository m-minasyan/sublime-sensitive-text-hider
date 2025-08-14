# Contributing to Sublime Sensitive Text Hider

First off, thank you for considering contributing to Sublime Sensitive Text Hider! It's people like you that make this tool better for everyone.

## Code of Conduct

By participating in this project, you are expected to uphold our principles of respect and collaboration.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Sublime Text version, Python version)
- Any relevant error messages or screenshots

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Why this enhancement would be useful
- Possible implementation approach (if you have ideas)

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests if applicable
3. Ensure your code follows the existing style
4. Update the documentation if needed
5. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/sublime-sensitive-text-hider.git
cd sublime-sensitive-text-hider

# Create a branch
git checkout -b feature/your-feature-name

# Make your changes and test them
# For Sublime Text plugin testing, symlink the plugin folder to your Packages directory

# Commit your changes
git commit -m "Add your meaningful commit message"

# Push to your fork
git push origin feature/your-feature-name
```

## Style Guidelines

### Python Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and small

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Pattern Contributions

When adding new default patterns:

1. Ensure the pattern is commonly needed
2. Test the regex thoroughly
3. Use descriptive placeholder names
4. Document the pattern in the README

## Testing

### Manual Testing

1. Test with various file types
2. Test with saved and unsaved files
3. Test all keyboard shortcuts
4. Test menu items
5. Verify backup files are created/removed correctly

### Test Cases to Consider

- Empty files
- Large files (>10MB)
- Files with mixed encodings
- Files with no sensitive data
- Files with overlapping patterns

## Documentation

- Update README.md if you change functionality
- Update inline comments for complex logic
- Add examples if introducing new features

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉