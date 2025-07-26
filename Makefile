.PHONY: help install lint test format type-check clean dev

help:  ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

lint:  ## Run linting
	ruff check .
	mypy .

format:  ## Format code
	black .
	isort .
	ruff format .

fix:  ## Fix code issues
	ruff check . --fix
	black .
	isort .

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=. --cov-report=term-missing --cov-report=html

type-check:  ## Run type checking
	mypy .

clean:  ## Clean cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

dev:  ## Start development server
	python main.py

all:  ## Run all quality checks
	make format
	make lint
	make type-check
	make test
