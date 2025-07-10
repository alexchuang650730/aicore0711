"""
PowerAutomation 4.0 Core Module
核心模块，提供并行任务管理和基础框架
"""

from .task_manager import TaskManager
from .parallel_executor import ParallelExecutor
from .event_bus import EventBus
from .config import PowerAutomationConfig as Config, get_config

__version__ = "4.0.0"
__all__ = ["TaskManager", "ParallelExecutor", "EventBus", "Config"]

