# orcs2-salesagent Makefile
# Common development commands for muscle memory

.PHONY: help install dev test cov lint format clean check-env health

# Default target
help:
	@echo "orcs2-salesagent Development Commands"
	@echo "====================================="
	@echo "install     - Install Python dependencies"
	@echo "dev         - Start development server"
	@echo "test        - Run tests quickly"
	@echo "cov         - Run tests with coverage"
	@echo "lint        - Run linting checks"
	@echo "format      - Format code with ruff"
	@echo "clean       - Clean up temporary files"
	@echo "check-env   - Check environment setup"
	@echo "health      - Test health endpoint"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Start development server
dev:
	@echo "Starting development server..."
	bash scripts/dev_server.sh

# Run tests quickly
test:
	@echo "Running tests..."
	pytest -q --tb=short
	@echo "✅ Tests completed"

# Run tests with coverage
cov:
	@echo "Running tests with coverage..."
	pytest --maxfail=1 --disable-warnings --cov=. --cov-report=term-missing
	@echo "✅ Coverage report generated"

# Run linting
lint:
	@echo "Running linting checks..."
	ruff check .
	@echo "✅ Linting completed"

# Format code
format:
	@echo "Formatting code..."
	ruff format .
	@echo "✅ Code formatted"

# Clean up temporary files
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "✅ Cleanup completed"

# Check environment
check-env:
	@echo "Checking environment setup..."
	python scripts/check_env.py

# Test health endpoint
health:
	@echo "Testing health endpoint..."
	curl -s http://localhost:8000/health | python -m json.tool

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "✅ Virtual environment created"
	@echo "Activate with: source venv/bin/activate"

# Setup development environment
setup: venv
	@echo "Setting up development environment..."
	@echo "Please activate the virtual environment:"
	@echo "  source venv/bin/activate"
	@echo "Then run: make install"

# Run all checks
check: lint test
	@echo "✅ All checks passed"

# Quick start (assumes venv is active)
quick-start: install check-env
	@echo "✅ Environment ready for development"
	@echo "Run 'make dev' to start the server"
