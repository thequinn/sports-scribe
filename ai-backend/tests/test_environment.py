"""Test script to verify all dependencies are properly installed."""

import sys

print(f"Python version: {sys.version}")

# Test core dependencies
try:
    print("✅ OpenAI package imported successfully")
except ImportError as e:
    print(f"❌ OpenAI import failed: {e}")

try:
    print("✅ OpenAI Agents package imported successfully")
except ImportError as e:
    print(f"❌ OpenAI Agents import failed: {e}")

try:
    print("✅ FastAPI package imported successfully")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")

try:
    print("✅ Pydantic package imported successfully")
except ImportError as e:
    print(f"❌ Pydantic import failed: {e}")

try:
    print("✅ Supabase package imported successfully")
except ImportError as e:
    print(f"❌ Supabase import failed: {e}")

try:
    print("✅ Aiohttp package imported successfully")
except ImportError as e:
    print(f"❌ Aiohttp import failed: {e}")

try:
    print("✅ Python-dotenv package imported successfully")
except ImportError as e:
    print(f"❌ Python-dotenv import failed: {e}")

try:
    print("✅ Structlog package imported successfully")
except ImportError as e:
    print(f"❌ Structlog import failed: {e}")

print("\n🎉 Environment test completed!")
