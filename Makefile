.PHONY: setup install install-dev format lint test clean run-tavern run-tavern-debug

# Environment setup
setup:
	pip install uv
	uv venv
	. .venv/bin/activate || . .venv/Scripts/activate

# Installation
install:
	uv pip install -r requirements.txt

install-dev: install
	uv pip install -r requirements-dev.txt

# Development tools
format:
	uv run black .
	uv run isort .

lint:
	uv run ruff check .

test:
	uv run pytest

# Cleanup
clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache

# Run examples
run-tavern:
	cd examples && uv run python tavern_adventure.py

run-tavern-debug:
	cd examples && uv run python tavern_adventure.py --debug

run-tavern-debug-verbose:
	cd examples && uv run python tavern_adventure.py --debug --debug-level DEBUG

# Help
help:
	@echo "Available commands:"
	@echo "  make setup              - Create virtual environment and install uv"
	@echo "  make install            - Install package dependencies"
	@echo "  make install-dev        - Install development dependencies"
	@echo "  make format             - Format code with black and isort"
	@echo "  make lint               - Run linting with ruff"
	@echo "  make test              - Run tests with pytest"
	@echo "  make clean             - Remove build artifacts and caches"
	@echo "  make run-tavern        - Run the tavern example"
	@echo "  make run-tavern-debug  - Run the tavern example with debug mode"
	@echo "  make run-tavern-debug-verbose - Run the tavern example with verbose debug output" 