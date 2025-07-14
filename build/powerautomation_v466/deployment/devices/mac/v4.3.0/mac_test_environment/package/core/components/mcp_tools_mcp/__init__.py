"""
PowerAutomation 4.0 MCP工具框架

这个模块提供完整的MCP工具生态系统支持，包括工具注册、发现、代理和编排功能。

主要组件：
- MCPToolRegistry: MCP工具注册表
- MCPToolDiscovery: 工具自动发现机制
- MCPToolProxy: 工具代理和适配器
- MCPToolChain: 工具链编排系统
- MCPToolManager: 工具管理器
"""

from .tool_registry import MCPToolRegistry
from .tool_discovery import MCPToolDiscovery
from .tool_proxy import MCPToolProxy
from .tool_chain import MCPToolChain
from .tool_manager import MCPToolManager

__version__ = "4.0.0"
__author__ = "PowerAutomation Team"

__all__ = [
    "MCPToolRegistry",
    "MCPToolDiscovery", 
    "MCPToolProxy",
    "MCPToolChain",
    "MCPToolManager"
]

