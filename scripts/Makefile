.PHONY: install test lint format clean backup deploy monitor

# Python version
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy
BANDIT := $(VENV)/bin/bandit
RADON := $(VENV)/bin/radon
ISORT := $(VENV)/bin/isort

# Default target
all: install test lint

# Create virtual environment
$(VENV)/bin/activate: requirements.txt requirements-dev.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

# Install dependencies
install: $(VENV)/bin/activate

# Run tests
test: install
	$(PYTEST) tests/ -v --cov=scripts --cov-report=term-missing

# Run linters
lint: install
	$(FLAKE8) scripts/ tests/
	$(MYPY) scripts/ tests/
	$(BANDIT) -r scripts/ -c pyproject.toml
	$(RADON) mi scripts/ -a
	$(RADON) cc scripts/ -a

# Format code
format: install
	$(BLACK) scripts/ tests/
	$(ISORT) scripts/ tests/

# Clean up
clean:
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Run backup script
backup: install
	$(PYTHON) backup.py

# Run deployment script
deploy: install
	$(PYTHON) deploy.py

# Run monitoring script
monitor: install
	$(PYTHON) monitor.py

# Run automation script
automate: install
	$(PYTHON) advanced_automation.py

# Help
help:
	@echo "Available targets:"
	@echo "  install   - Install dependencies"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linters"
	@echo "  format    - Format code"
	@echo "  clean     - Clean up"
	@echo "  backup    - Run backup script"
	@echo "  deploy    - Run deployment script"
	@echo "  monitor   - Run monitoring script"
	@echo "  automate  - Run automation script" 