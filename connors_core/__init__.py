"""
Connors Core - Foundational components for the Connors trading system

This package provides:
- Registry for strategies, screeners, and plugins
- Configuration management
- Technical indicators (TALipp-based)
- Performance metrics

- Utility functions
"""

__version__ = "0.1.0"
__author__ = "Connors Trading Team"

from connors_core.config.manager import ConfigManager
from connors_core.core.registry import registry

__all__ = ["registry", "ConfigManager", "__version__"]
