#!/usr/bin/env python3
"""
MemoryOS MCP - PowerAutomation Core 記憶管理系統
集成 Claude Code 和 PowerAutomation Core 的智能記憶和學習能力
"""

from .memory_engine import MemoryEngine, MemoryType
from .context_manager import ContextManager, ContextType
from .learning_adapter import LearningAdapter
from .personalization_manager import PersonalizationManager
from .memory_optimizer import MemoryOptimizer
from .memoryos_coordinator import MemoryOSCoordinator

__version__ = "4.6.9.4"
__all__ = [
    "MemoryEngine",
    "MemoryType", 
    "ContextManager",
    "ContextType",
    "LearningAdapter",
    "PersonalizationManager",
    "MemoryOptimizer",
    "MemoryOSCoordinator"
]