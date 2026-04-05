"""
Root conftest.py — shared pytest fixtures and collection configuration.

This file is auto-discovered by pytest.  Fixtures and hooks defined here are
available to every test module without an explicit import.
"""
import sys
import os

# Ensure the project root is on sys.path so that ``from src.X import Y``
# style imports work correctly when running pytest from the repo root.
sys.path.insert(0, os.path.dirname(__file__))

# Exclude DeepEval tests from the default run — they require live API keys.
# Run them explicitly with:  pytest tests/deepeval_tests/ -v
collect_ignore_glob = ["tests/deepeval_tests/*.py"]

