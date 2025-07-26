#!/bin/bash
# Comprehensive code quality fix script

echo "🔧 Running code quality fixes..."

echo "📝 Formatting with Black..."
black .

echo "📦 Sorting imports with isort..."
isort .

echo "🔍 Linting and fixing with Ruff..."
ruff check . --fix

echo "📋 Formatting with Ruff..."
ruff format .

echo "✅ Code quality fixes completed!"
