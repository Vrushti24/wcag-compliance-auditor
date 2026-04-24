"""
Pytest configuration — adds backend/ to sys.path so all imports resolve.
"""
import os
import sys

# Insert backend directory at front of path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
