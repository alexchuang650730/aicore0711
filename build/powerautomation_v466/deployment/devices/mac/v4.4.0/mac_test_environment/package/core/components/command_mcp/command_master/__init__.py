"""
PowerAutomation 4.0 Command Master
命令系统 - 负责命令注册、执行和管理
"""

from .command_registry import CommandRegistry, get_command_registry
from .command_executor import CommandExecutor, CommandResult, get_command_executor
from .mcp_interface import CommandMasterMCP, get_command_master_mcp

__version__ = "4.0.0"
__all__ = [
    "CommandRegistry",
    "CommandExecutor", 
    "CommandResult",
    "CommandMasterMCP",
    "get_command_registry",
    "get_command_executor",
    "get_command_master_mcp"
]

