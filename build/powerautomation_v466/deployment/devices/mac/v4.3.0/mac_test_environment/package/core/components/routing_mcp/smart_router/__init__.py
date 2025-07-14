"""
PowerAutomation 4.0 Smart Router MCP
智慧路由MCP - 负责智能路由、语义分析和任务分发
"""

from .smart_router import SmartRouter
from .semantic_analyzer import SemanticAnalyzer
from .route_optimizer import RouteOptimizer
from .mcp_interface import SmartRouterMCPInterface

__version__ = "4.0.0"
__all__ = [
    "SmartRouter",
    "SemanticAnalyzer", 
    "RouteOptimizer",
    "SmartRouterMCPInterface"
]

