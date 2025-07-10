"""
PowerAutomation 4.0 Agent Squad Coordination
智能体协调模块 - 负责智能体之间的协调、任务分配和协作管理
"""

from .agent_coordinator import AgentCoordinator, get_agent_coordinator
from .task_dispatcher import TaskDispatcher, get_task_dispatcher
from .collaboration_manager import CollaborationManager, get_collaboration_manager

__version__ = "4.0.0"
__all__ = [
    "AgentCoordinator",
    "TaskDispatcher", 
    "CollaborationManager",
    "get_agent_coordinator",
    "get_task_dispatcher",
    "get_collaboration_manager"
]

