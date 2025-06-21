<<<<<<< HEAD
.PHONY: setup test lint format clean build run docker-build docker-run

# Development setup
setup:
	./setup_project.sh && ./setup_dev.sh

# Testing
test:
	poetry run pytest -v --cov=src --cov-report=term-missing

# Linting and formatting
lint:
	poetry run flake8 src tests
	poetry run mypy src tests
	poetry run black --check src tests

format:
	poetry run black src tests

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/

# Building and running
build:
	poetry build

run:
	poetry run python -m src.secondbrain.main

# Docker commands
docker-build:
	docker-compose build

docker-run:
	docker-compose up

docker-test:
	docker-compose run --rm dev

# Install dependencies
install:
	poetry install

update-deps:
	poetry update

# Documentation
docs-build:
	poetry run sphinx-build -b html docs/source docs/build

docs-serve:
	python -m http.server --directory docs/build 8000 
=======
# Makefile for SecondBrainApp Docker automation

APP_NAME=secondbrainapp
DOCKERFILE=Dockerfile
TAG=$(APP_NAME):latest
PORT=8501

build:
	docker build -t $(TAG) -f $(DOCKERFILE) .

dev: build
	docker run -it --rm -p $(PORT):$(PORT) $(TAG)

shell:
	docker run -it --rm $(TAG) /bin/bash

logs:
	docker logs -f $(APP_NAME)

clean:
	docker container stop $$(docker ps -aq --filter ancestor=$(TAG)) || true
	docker container rm $$(docker ps -aq --filter ancestor=$(TAG)) || true
	docker image rm $(TAG) || true

gitpush:
	git add README.md
	git commit -m "Add project README with Docker and structure instructions" || echo "No changes to commit."
	git push origin main
>>>>>>> 46133858 (Initial auto-push with Visco: Docker, Compose, Makefile, README)
