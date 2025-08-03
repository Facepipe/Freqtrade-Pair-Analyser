"""
Utils Package - Centralized Imports
Version: 1.0.0

This module ensures all utilities are properly importable
"""

# Import all main classes for easy access
from .data_handler import VersionedAnalyzer
from .data_manager import DataManager
from .analysis_engine import AnalysisEngine
from .config_handler import load_config, check_directory_permissions, get_project_root

# Version information
__version__ = "1.0.0"
__all__ = [
    'VersionedAnalyzer',
    'DataManager', 
    'AnalysisEngine',
    'load_config',
    'check_directory_permissions',
    'get_project_root'
]

# Package metadata
PACKAGE_INFO = {
    'name': 'freqtrade-pair-analyzer-utils',
    'version': __version__,
    'description': 'Utility modules for Freqtrade Pair Analyzer',
    'components': {
        'data_handler': 'Main analyzer class with versioning',
        'data_manager': 'Data downloading and management',
        'analysis_engine': 'Technical analysis calculations',
        'config_handler': 'Configuration loading and validation'
    }
}