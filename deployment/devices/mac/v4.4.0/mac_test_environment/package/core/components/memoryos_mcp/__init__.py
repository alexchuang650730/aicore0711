"""
MemoryOS MCP - AI Memory and Personalization System

This module provides comprehensive AI memory capabilities including:
- Persistent memory storage and retrieval
- Personalized learning and adaptation
- Context-aware memory management
- Cross-session memory continuity
- Intelligent memory optimization
"""

from .memory_engine import MemoryEngine
from .personalization_manager import PersonalizationManager
from .context_manager import ContextManager
from .memory_optimizer import MemoryOptimizer
from .learning_adapter import LearningAdapter

__version__ = "1.0.0"
__author__ = "PowerAutomation 4.0 Team"

__all__ = [
    "MemoryEngine",
    "PersonalizationManager", 
    "ContextManager",
    "MemoryOptimizer",
    "LearningAdapter"
]

