# Sublime Sensitive Text Hider

A powerful Sublime Text plugin and standalone Python script for hiding and revealing sensitive information in text files. Perfect for screenshots, documentation, and code sharing.

## Features

- 🔒 **Hide sensitive text** with customizable placeholders
- 🔓 **Reveal original text** with one click
- 🎯 **Smart pattern detection** for common sensitive data (emails, credit cards, SSNs, IP addresses, etc.)
- 💾 **Works with unsaved files** - no need to save first
- ⚡ **Toggle functionality** - quickly switch between hidden/revealed states
- 🛠️ **Standalone script** - use outside of Sublime Text
- ⚙️ **Customizable patterns** - add your own regex patterns

## Installation

### Quick Install with Make
```bash
# Clone the repository
git clone https://github.com/m-minasyan/sublime-sensitive-text-hider.git
cd sublime-sensitive-text-hider

# Install everything (plugin + standalone script)
make install

# Or install separately
make install-sublime      # Install Sublime Text plugin only
make install-standalone   # Install standalone script only
```

### Manual Installation

#### Sublime Text Plugin

##### Method 1: Installation Script
```bash
./install.sh
```

##### Method 2: Manual Copy
1. Copy the `sublime-plugin` folder contents to:
   - **macOS**: `~/Library/Application Support/Sublime Text/Packages/User/SensitiveTextHider/`
   - **Windows**: `%APPDATA%\Sublime Text\Packages\User\SensitiveTextHider\`
   - **Linux**: `~/.config/sublime-text/Packages/User/SensitiveTextHider/`

2. Copy `hide_sensitive_text.py` to the `User` folder (parent of `SensitiveTextHider`)

3. Restart Sublime Text

### Standalone Script
```bash
# Make the script executable
chmod +x standalone-script/sensitive_text_processor.py

# Optional: Add to PATH
ln -s $(pwd)/standalone-script/sensitive_text_processor.py /usr/local/bin/sensitive-text
```

## Usage

### Sublime Text

#### Keyboard Shortcuts
- `⌘+⌥+H` (Mac) / `Ctrl+Alt+H` (Win/Linux) - Toggle hide/reveal
- `⌘+Shift+⌥+H` - Force hide sensitive text
- `⌘+Shift+⌥+R` - Force reveal sensitive text
- `⌘+⌥+A` - Add custom pattern

#### Menu Access
- **Tools → Sensitive Text** - All functions
- **Edit → Sensitive Text** - Quick access
- **Right-click → Sensitive Text** - Context menu

#### Command Palette
Press `⌘+Shift+P` (Mac) / `Ctrl+Shift+P` (Win/Linux) and type:
- `Hide Sensitive Text`
- `Reveal Sensitive Text`
- `Toggle Sensitive Text`
- `Add Sensitive Pattern`

### Standalone Script

```bash
# Hide sensitive text in a file
python3 sensitive_text_processor.py hide document.txt

# Reveal sensitive text
python3 sensitive_text_processor.py reveal document.txt

# Use custom patterns
python3 sensitive_text_processor.py hide document.txt --patterns custom_patterns.json
```

## Default Patterns

The plugin comes with built-in patterns for common sensitive data:

| Pattern | Placeholder | Description |
|---------|------------|-------------|
| Email | `${EMAIL}` | Email addresses |
| Credit Card | `${CREDIT_CARD}` | Credit card numbers |
| SSN | `${SSN}` | Social Security Numbers |
| IP Address | `${IP_ADDRESS}` | IPv4 addresses |
| API Key | `${API_KEY}` | API keys and tokens |
| Password | `${PASSWORD}` | Password assignments |
| Phone | `${PHONE}` | Phone numbers |

## Custom Patterns

### Adding Patterns in Sublime Text
1. Use `⌘+⌥+A` or menu **Tools → Sensitive Text → Add Custom Pattern**
2. Enter your regex pattern
3. Enter the replacement placeholder

### Configuration File
Edit `SensitiveTextHider.sublime-settings`:

```json
{
    "patterns": [
        {
            "pattern": "\\bapi[_-]?key[_-]?[a-zA-Z0-9]{20,}\\b",
            "replacement": "${API_KEY}",
            "flags": "IGNORECASE"
        },
        {
            "pattern": "\\b[A-Za-z0-9._%+-]+@example\\.com\\b",
            "replacement": "${COMPANY_EMAIL}"
        }
    ]
}
```

### Custom Patterns File (Standalone)
Create a `patterns.json` file:

```json
[
    {
        "pattern": "\\bSECRET[_-]?[A-Z0-9]+\\b",
        "replacement": "${SECRET}",
        "flags": "IGNORECASE"
    }
]
```

## How It Works

1. **Hiding**: The plugin scans text using regex patterns and replaces matches with placeholders
2. **Backup**: Original content is saved to `.sensitive_backup` file (or memory for unsaved files)
3. **Mapping**: Replacement positions are stored in `.sensitive_map` file
4. **Revealing**: Original content is restored from backup

## File Structure

```
sublime-sensitive-text-hider/
├── sublime-plugin/           # Sublime Text plugin files
│   ├── hide_sensitive_text.py
│   ├── __init__.py
│   ├── Default.sublime-commands
│   ├── Default.sublime-keymap
│   ├── Main.sublime-menu
│   ├── Context.sublime-menu
│   └── SensitiveTextHider.sublime-settings
├── standalone-script/        # Standalone Python script
│   ├── sensitive_text_processor.py
│   └── custom_patterns.json
├── examples/                 # Example files
│   └── test_sensitive.txt
├── docs/                     # Documentation
├── install.sh               # Installation script
├── LICENSE
└── README.md
```

## Examples

### Before
```text
My email is john.doe@example.com and my API key is api_key_abc123xyz789.
Credit card: 1234-5678-9012-3456
Server IP: 192.168.1.100
```

### After Hiding
```text
My email is ${EMAIL} and my API key is ${API_KEY}.
Credit card: ${CREDIT_CARD}
Server IP: ${IP_ADDRESS}
```

## Testing

The project includes comprehensive test suites to ensure reliability and performance.

### Running Tests with Make

```bash
make test              # Run basic test suite (45 tests)
make test-extended     # Run extended test suite (62 tests)
make test-all          # Run all tests (107 tests)

# Run specific test categories
make test-edge         # Edge case tests
make test-concurrent   # Concurrent operations tests
make test-large        # Large file handling tests
make test-custom       # Custom pattern tests
make test-perf         # Performance benchmarks

# Additional testing tools
make test-coverage     # Run tests with coverage report
make lint             # Check code quality with flake8
make benchmark        # Run performance benchmarks
```

### Running Tests Manually

#### Basic Test Suite (45 tests)
```bash
python3 run_tests.py
```

#### Extended Test Suite (62 tests)
```bash
python3 run_extended_tests.py
```

### Test Coverage

The test suites cover:
- **Pattern Detection**: Email, credit cards, SSNs, IPs, API keys, passwords
- **Edge Cases**: Malformed inputs, Unicode, overlapping patterns
- **Concurrent Operations**: Thread-safe file operations
- **Large Files**: Performance with files up to 10MB
- **Custom Patterns**: Complex regex patterns and validation
- **Performance Benchmarks**: Speed and memory usage metrics

## Development

### Using Make Commands

```bash
# Development setup
make dev-setup         # Install development dependencies
make check-python      # Verify Python version

# Code quality
make lint             # Run code quality checks
make format           # Format code with black

# Testing
make test             # Run basic tests
make test-all         # Run all tests
make watch-tests      # Watch files and auto-run tests

# Maintenance
make clean            # Remove temporary files
make uninstall        # Uninstall plugin and script

# Release
make release          # Prepare for release (runs tests + lint)
```

### Available Make Targets

Run `make help` to see all available targets.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Run the test suite (`make test-all`)
4. Check code quality (`make lint`)
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created by [Mihran Minasyan](https://github.com/m-minasyan)

## Acknowledgments

- Built for Sublime Text
- Inspired by the need for privacy in documentation and screenshots
- Community feedback and contributions

## Support

If you encounter any issues or have suggestions:
- Open an issue on [GitHub](https://github.com/m-minasyan/sublime-sensitive-text-hider/issues)
- Check the [documentation](docs/)
- Contact the author

## Changelog

### v1.1.0 (2025-08-14)
- Added comprehensive test suite with 107 total tests
- Added edge case testing for pattern detection
- Added concurrent file operations testing
- Added large file handling tests (up to 10MB)
- Added custom pattern validation tests
- Added performance benchmarking suite
- Updated documentation with testing instructions

### v1.0.0 (2025-08-14)
- Initial release
- Sublime Text plugin with full functionality
- Standalone Python script
- Support for unsaved files
- Toggle functionality
- Custom pattern support
- Default patterns for common sensitive data