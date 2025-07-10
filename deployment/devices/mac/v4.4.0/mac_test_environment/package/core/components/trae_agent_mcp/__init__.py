"""
Trae Agent MCP Integration Module

This module integrates Trae Agent as a specialized software engineering engine
within the PowerAutomation 4.0 architecture, following Solution One approach.

Components:
- TraeAgentEngine: Core adapter for Trae Agent integration
- TraeClient: Client interface for Trae Agent communication
- ConfigManager: Configuration management for Trae Agent
- ResultTransformer: Result format transformation between systems
- ErrorHandler: Comprehensive error handling and recovery
"""

from .trae_agent_engine import TraeAgentEngine
from .trae_client import TraeClient
from .config_manager import TraeConfigManager
from .result_transformer import ResultTransformer
from .error_handler import TraeErrorHandler

__version__ = "1.0.0"
__author__ = "PowerAutomation 4.0 Team"

__all__ = [
    "TraeAgentEngine",
    "TraeClient", 
    "TraeConfigManager",
    "ResultTransformer",
    "TraeErrorHandler"
]

