# Simple Makefile for common tasks

.PHONY: test test-fast install clean test-os reset-vm test-cycle

# Run all tests (fast, local, no VM) - ULTRA SIMPLE
test:
	@./scripts/test-simple.sh

# Run tests in parallel (even faster)
test-fast:
	@echo "Running tests in parallel..."
	.venv/bin/python -m pytest tests/ -v -n auto

# Install dependencies
install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov

# Watch mode (requires pytest-watch: pip install pytest-watch)
watch:
	.venv/bin/pytest-watch tests/

# OS testing (requires VM with snapshot)
test-os:
	./scripts/test-os-fast.sh

# Reset VM to clean state
reset-vm:
	./scripts/test-os-fast.sh

# Complete cycle: local tests + VM reset
test-cycle:
	./scripts/quick-test-cycle.sh

# Visual testing: code tests + start VM
test-visual:
	./scripts/test-visual.sh

# Start VM for visual/interactive testing
start-vm:
	./scripts/start-vm-visual.sh

# Fully automated OS setup (creates VM, configures, starts)
setup-os:
	./scripts/auto-setup-os.sh

# Setup Buildroot
setup-buildroot:
	./scripts/setup-buildroot.sh

# Custom Buildroot OS targets
build-custom-os: setup-buildroot
	./scripts/build-custom-os.sh

test-custom-os:
	./scripts/test-custom-os.sh

# Quick rebuild (incremental - only changed files)
rebuild-custom-os:
	cd buildroot && make

# Check build status
check-build:
	./scripts/check-build-status.sh

