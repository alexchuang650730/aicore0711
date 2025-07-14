"""
PowerAutomation 4.0 MCP Coordinator
MCP协调器 - 统一的MCP通信和协调中心
"""

from .mcp_coordinator import MCPCoordinator
from .mcp_registry import MCPRegistry
from .communication_hub import CommunicationHub
from .workflow_orchestrator import WorkflowOrchestrator

__version__ = "4.0.0"
__all__ = [
    "MCPCoordinator",
    "MCPRegistry",
    "CommunicationHub", 
    "WorkflowOrchestrator"
]

