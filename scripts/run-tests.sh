#!/bin/bash
# Comprehensive testing script

echo "🧪 Running test suite..."

echo "🔬 Unit tests..."
pytest tests/ -v

echo "📊 Coverage report..."
pytest --cov=. --cov-report=term-missing

echo "✅ Testing completed!"
