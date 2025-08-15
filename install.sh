#!/bin/bash

echo "Sublime Sensitive Text Hider - Installation Script"
echo "=================================================="
echo ""

SUBLIME_PACKAGES=""
OS_TYPE=""
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
    SUBLIME_PACKAGES="$HOME/Library/Application Support/Sublime Text/Packages"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="Linux"
    SUBLIME_PACKAGES="$HOME/.config/sublime-text/Packages"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS_TYPE="Windows"
    SUBLIME_PACKAGES="$APPDATA/Sublime Text/Packages"
else
    echo "⚠️  Unknown operating system: $OSTYPE"
    echo "Please install manually following the README instructions."
    exit 1
fi

echo "Detected OS: $OS_TYPE"
echo ""

if [ ! -d "$SUBLIME_PACKAGES" ]; then
    echo "❌ Sublime Text packages directory not found at:"
    echo "   $SUBLIME_PACKAGES"
    echo ""
    echo "Please ensure Sublime Text is installed or specify the correct path."
    exit 1
fi

echo "✅ Found Sublime Text packages directory"
echo ""

PLUGIN_DIR="$SUBLIME_PACKAGES/SensitiveTextHider"

if [ -L "$PLUGIN_DIR" ] || [ -d "$PLUGIN_DIR" ]; then
    echo "⚠️  Plugin already exists at:"
    echo "   $PLUGIN_DIR"
    read -p "Do you want to reinstall it? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo "Removing existing plugin..."
    if [ -L "$PLUGIN_DIR" ]; then
        rm "$PLUGIN_DIR"
    else
        rm -rf "$PLUGIN_DIR"
    fi
fi

if [ -d "$CURRENT_DIR/sublime-plugin" ]; then
    echo "⚠️  Found duplicate sublime-plugin directory. Removing it to prevent conflicts..."
    rm -rf "$CURRENT_DIR/sublime-plugin"
    echo "✅ Duplicate directory removed"
fi

USER_DIR="$SUBLIME_PACKAGES/User"
if [ -d "$USER_DIR/SensitiveTextHider" ] || [ -f "$USER_DIR/hide_sensitive_text.py" ]; then
    echo "⚠️  Found old plugin files in User directory. Cleaning up..."
    [ -d "$USER_DIR/SensitiveTextHider" ] && rm -rf "$USER_DIR/SensitiveTextHider"
    [ -f "$USER_DIR/hide_sensitive_text.py" ] && rm "$USER_DIR/hide_sensitive_text.py"
    echo "✅ Old plugin files removed from User directory"
fi

echo "Creating symlink to plugin directory..."
ln -s "$CURRENT_DIR" "$PLUGIN_DIR"

if [ -L "$PLUGIN_DIR" ]; then
    echo "✅ Plugin installed successfully via symlink"
    echo "   Source: $CURRENT_DIR"
    echo "   Link: $PLUGIN_DIR"
else
    echo "❌ Failed to create symlink"
    exit 1
fi
echo ""

read -p "Do you want to install the standalone script to /usr/local/bin? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -w "/usr/local/bin" ]; then
        cp standalone-script/sensitive_text_processor.py /usr/local/bin/sensitive-text
        chmod +x /usr/local/bin/sensitive-text
        echo "✅ Standalone script installed to /usr/local/bin/sensitive-text"
    else
        echo "⚠️  Cannot write to /usr/local/bin. Trying with sudo..."
        sudo cp standalone-script/sensitive_text_processor.py /usr/local/bin/sensitive-text
        sudo chmod +x /usr/local/bin/sensitive-text
        echo "✅ Standalone script installed to /usr/local/bin/sensitive-text"
    fi
else
    echo "Skipping standalone script installation."
fi

echo ""
echo "=================================================="
echo "Installation Complete!"
echo "=================================================="
echo ""
echo "📝 Next steps:"
echo "1. Restart Sublime Text"
echo "2. Test the plugin with Cmd+Alt+H (Mac) or Ctrl+Alt+H (Win/Linux)"
echo ""
echo "📖 Usage:"
echo "   - Toggle: Cmd+Alt+H (Mac) / Ctrl+Alt+H (Win/Linux)"
echo "   - Menu: Tools → Sensitive Text"
echo "   - Command Palette: 'Hide Sensitive Text'"
echo ""
if [ -f "/usr/local/bin/sensitive-text" ]; then
    echo "🔧 Standalone script usage:"
    echo "   sensitive-text hide <file>"
    echo "   sensitive-text reveal <file>"
    echo ""
fi
echo "Thank you for installing Sublime Sensitive Text Hider!"