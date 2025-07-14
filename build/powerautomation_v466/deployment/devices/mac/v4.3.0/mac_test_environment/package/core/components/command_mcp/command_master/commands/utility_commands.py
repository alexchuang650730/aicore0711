"""
PowerAutomation 4.0 Utility Commands
工具相关的专业化命令
"""

import asyncio
from typing import List, Dict, Any
from ..command_registry import CommandRegistry, CommandCategory

async def help_command(args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
    """显示帮助信息"""
    command = args[0] if args else None
    
    if command:
        from ..command_registry import get_command_registry
        registry = get_command_registry()
        help_text = registry.get_command_help(command)
        return {"command": command, "help": help_text or "命令不存在"}
    
    return {
        "available_commands": [
            "architect - 架构分析和设计",
            "develop - 项目开发和代码生成", 
            "test - 测试执行和管理",
            "deploy - 应用部署",
            "monitor - 系统监控",
            "scan - 安全扫描",
            "help - 显示帮助信息"
        ]
    }

def register_utility_commands(registry: CommandRegistry):
    registry.register_command("help", CommandCategory.UTILITY, "显示帮助信息", help_command)

