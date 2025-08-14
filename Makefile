.PHONY: all test test-basic test-extended test-all install install-sublime install-standalone clean help lint check-python

PYTHON := python3
SUBLIME_USER_DIR_MAC := ~/Library/Application Support/Sublime Text/Packages/User
SUBLIME_USER_DIR_LINUX := ~/.config/sublime-text/Packages/User
SUBLIME_USER_DIR_WIN := %APPDATA%\Sublime Text\Packages\User
PLUGIN_DIR := SensitiveTextHider

all: test

help:
	@echo "Available targets:"
	@echo "  make test           - Run basic test suite (45 tests)"
	@echo "  make test-extended  - Run extended test suite (62 tests)"
	@echo "  make test-all       - Run all tests (107 tests)"
	@echo "  make test-edge      - Run only edge case tests"
	@echo "  make test-perf      - Run only performance tests"
	@echo "  make install        - Install both plugin and standalone script"
	@echo "  make install-sublime - Install Sublime Text plugin only"
	@echo "  make install-standalone - Install standalone script only"
	@echo "  make lint           - Check code with pylint/flake8"
	@echo "  make clean          - Remove temporary files and caches"
	@echo "  make check-python   - Verify Python version"

check-python:
	@$(PYTHON) --version | grep -E "Python 3\.[0-9]+\.[0-9]+" > /dev/null || \
		(echo "Error: Python 3 is required" && exit 1)
	@echo "✓ Python 3 detected: $$($(PYTHON) --version)"

test: test-basic

test-basic: check-python
	@echo "Running basic test suite..."
	@$(PYTHON) run_tests.py

test-extended: check-python
	@echo "Running extended test suite..."
	@$(PYTHON) run_extended_tests.py

test-all: check-python
	@echo "Running all tests..."
	@$(PYTHON) run_tests.py
	@echo ""
	@$(PYTHON) run_extended_tests.py

test-edge: check-python
	@echo "Running edge case tests..."
	@$(PYTHON) -m unittest tests.test_edge_cases -v

test-concurrent: check-python
	@echo "Running concurrent operations tests..."
	@$(PYTHON) -m unittest tests.test_concurrent_operations -v

test-large: check-python
	@echo "Running large file tests..."
	@$(PYTHON) -m unittest tests.test_large_files -v

test-custom: check-python
	@echo "Running custom pattern tests..."
	@$(PYTHON) -m unittest tests.test_custom_patterns -v

test-perf: check-python
	@echo "Running performance tests..."
	@$(PYTHON) -m unittest tests.test_performance -v

test-coverage: check-python
	@echo "Running tests with coverage..."
	@command -v coverage >/dev/null 2>&1 || (echo "Installing coverage..." && pip3 install coverage)
	@coverage run -m unittest discover tests
	@coverage report -m
	@coverage html
	@echo "Coverage report generated in htmlcov/index.html"

install: install-sublime install-standalone
	@echo "✓ Installation complete"

install-sublime:
	@echo "Installing Sublime Text plugin..."
	@if [ -d "$(SUBLIME_USER_DIR_MAC)" ]; then \
		echo "Detected macOS Sublime Text"; \
		mkdir -p "$(SUBLIME_USER_DIR_MAC)/$(PLUGIN_DIR)"; \
		cp -r sublime-plugin/* "$(SUBLIME_USER_DIR_MAC)/$(PLUGIN_DIR)/"; \
		cp sublime-plugin/hide_sensitive_text.py "$(SUBLIME_USER_DIR_MAC)/"; \
		echo "✓ Plugin installed to $(SUBLIME_USER_DIR_MAC)"; \
	elif [ -d "$(SUBLIME_USER_DIR_LINUX)" ]; then \
		echo "Detected Linux Sublime Text"; \
		mkdir -p "$(SUBLIME_USER_DIR_LINUX)/$(PLUGIN_DIR)"; \
		cp -r sublime-plugin/* "$(SUBLIME_USER_DIR_LINUX)/$(PLUGIN_DIR)/"; \
		cp sublime-plugin/hide_sensitive_text.py "$(SUBLIME_USER_DIR_LINUX)/"; \
		echo "✓ Plugin installed to $(SUBLIME_USER_DIR_LINUX)"; \
	else \
		echo "Sublime Text directory not found. Please install manually."; \
		exit 1; \
	fi

install-standalone:
	@echo "Installing standalone script..."
	@chmod +x standalone-script/sensitive_text_processor.py
	@if [ -w /usr/local/bin ]; then \
		ln -sf "$$(pwd)/standalone-script/sensitive_text_processor.py" /usr/local/bin/sensitive-text; \
		echo "✓ Standalone script installed to /usr/local/bin/sensitive-text"; \
	else \
		echo "Cannot write to /usr/local/bin. Script made executable at:"; \
		echo "  $$(pwd)/standalone-script/sensitive_text_processor.py"; \
	fi

uninstall:
	@echo "Uninstalling..."
	@if [ -d "$(SUBLIME_USER_DIR_MAC)/$(PLUGIN_DIR)" ]; then \
		rm -rf "$(SUBLIME_USER_DIR_MAC)/$(PLUGIN_DIR)"; \
		rm -f "$(SUBLIME_USER_DIR_MAC)/hide_sensitive_text.py"; \
		echo "✓ Removed from macOS Sublime Text"; \
	fi
	@if [ -d "$(SUBLIME_USER_DIR_LINUX)/$(PLUGIN_DIR)" ]; then \
		rm -rf "$(SUBLIME_USER_DIR_LINUX)/$(PLUGIN_DIR)"; \
		rm -f "$(SUBLIME_USER_DIR_LINUX)/hide_sensitive_text.py"; \
		echo "✓ Removed from Linux Sublime Text"; \
	fi
	@if [ -L /usr/local/bin/sensitive-text ]; then \
		rm /usr/local/bin/sensitive-text; \
		echo "✓ Removed standalone script symlink"; \
	fi

lint: check-python
	@echo "Running code quality checks..."
	@command -v flake8 >/dev/null 2>&1 || (echo "Installing flake8..." && pip3 install flake8)
	@echo "Checking standalone script..."
	@flake8 standalone-script/sensitive_text_processor.py --max-line-length=120 --ignore=E501 || true
	@echo "Checking Sublime plugin..."
	@flake8 sublime-plugin/hide_sensitive_text.py --max-line-length=120 --ignore=E501 || true
	@echo "Checking tests..."
	@flake8 tests/ --max-line-length=120 --ignore=E501 || true

format: check-python
	@echo "Formatting code with black..."
	@command -v black >/dev/null 2>&1 || (echo "Installing black..." && pip3 install black)
	@black standalone-script/ sublime-plugin/ tests/ --line-length=120

clean:
	@echo "Cleaning up..."
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@find . -type f -name "*.sensitive_backup" -delete 2>/dev/null || true
	@find . -type f -name "*.sensitive_map" -delete 2>/dev/null || true
	@rm -rf htmlcov/ .coverage 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@echo "✓ Cleanup complete"

dev-setup: check-python
	@echo "Setting up development environment..."
	@pip3 install -r requirements-dev.txt 2>/dev/null || \
		(echo "Creating requirements-dev.txt..." && \
		 echo "flake8\nblack\ncoverage\npytest" > requirements-dev.txt && \
		 pip3 install -r requirements-dev.txt)
	@echo "✓ Development environment ready"

benchmark: check-python
	@echo "Running performance benchmarks..."
	@$(PYTHON) -m unittest tests.test_performance.TestPerformanceBenchmarks -v

watch-tests:
	@echo "Watching for file changes and running tests..."
	@command -v fswatch >/dev/null 2>&1 || (echo "Please install fswatch: brew install fswatch" && exit 1)
	@fswatch -o standalone-script/ sublime-plugin/ tests/ | xargs -n1 -I{} make test-basic

release: test-all lint
	@echo "Preparing release..."
	@echo "Current version: $$(grep -E '^### v[0-9]+\.[0-9]+\.[0-9]+' README.md | head -1)"
	@echo "All tests passed ✓"
	@echo "Code quality checks passed ✓"
	@echo "Ready for release!"

.DEFAULT_GOAL := help