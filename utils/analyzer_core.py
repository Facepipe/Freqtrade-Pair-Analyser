"""
Analyzer Core - Redirect to Working Implementation
Version: 2.0.0 - Simplified to use data_handler implementation

This module now simply imports from the working data_handler implementation
to avoid code duplication and confusion.
"""

# Import the working implementation
from .data_handler import VersionedAnalyzer

# Re-export for compatibility
__all__ = ['VersionedAnalyzer']

# Version info
VERSION = "2.0.0"

# Note: The actual VersionedAnalyzer implementation is now in data_handler.py
# This file exists only for backward compatibility