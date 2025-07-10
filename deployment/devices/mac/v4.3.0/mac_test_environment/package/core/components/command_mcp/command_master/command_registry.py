"""
PowerAutomation 4.0 Command Registry
命令注册器，管理所有专业化命令
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import inspect


class CommandCategory(Enum):
    """命令分类枚举"""
    ARCHITECTURE = "architecture"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    UTILITY = "utility"


@dataclass
class CommandInfo:
    """命令信息数据类"""
    name: str
    category: CommandCategory
    description: str
    handler: Callable
    parameters: List[Dict[str, Any]]
    examples: List[str]
    is_async: bool
    requires_auth: bool = False
    min_args: int = 0
    max_args: Optional[int] = None


class CommandRegistry:
    """命令注册器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.commands: Dict[str, CommandInfo] = {}
        self.categories: Dict[CommandCategory, List[str]] = {}
        
        # 初始化分类
        for category in CommandCategory:
            self.categories[category] = []
    
    def register_command(
        self,
        name: str,
        category: CommandCategory,
        description: str,
        handler: Callable,
        parameters: List[Dict[str, Any]] = None,
        examples: List[str] = None,
        requires_auth: bool = False,
        min_args: int = 0,
        max_args: Optional[int] = None
    ):
        """注册命令"""
        # 检查处理器是否为异步函数
        is_async = asyncio.iscoroutinefunction(handler)
        
        # 自动分析参数（如果未提供）
        if parameters is None:
            parameters = self._analyze_parameters(handler)
        
        command_info = CommandInfo(
            name=name,
            category=category,
            description=description,
            handler=handler,
            parameters=parameters or [],
            examples=examples or [],
            is_async=is_async,
            requires_auth=requires_auth,
            min_args=min_args,
            max_args=max_args
        )
        
        self.commands[name] = command_info
        self.categories[category].append(name)
        
        self.logger.info(f"已注册命令: {name} ({category.value})")
    
    def get_command(self, name: str) -> Optional[CommandInfo]:
        """获取命令信息"""
        return self.commands.get(name)
    
    def get_commands_by_category(self, category: CommandCategory) -> List[CommandInfo]:
        """按分类获取命令"""
        command_names = self.categories.get(category, [])
        return [self.commands[name] for name in command_names]
    
    def get_all_commands(self) -> List[CommandInfo]:
        """获取所有命令"""
        return list(self.commands.values())
    
    def search_commands(self, query: str) -> List[CommandInfo]:
        """搜索命令"""
        query = query.lower()
        results = []
        
        for command in self.commands.values():
            if (query in command.name.lower() or 
                query in command.description.lower() or
                any(query in example.lower() for example in command.examples)):
                results.append(command)
        
        return results
    
    def validate_command_args(self, command_name: str, args: List[str]) -> bool:
        """验证命令参数"""
        command = self.get_command(command_name)
        if not command:
            return False
        
        arg_count = len(args)
        
        # 检查最小参数数量
        if arg_count < command.min_args:
            return False
        
        # 检查最大参数数量
        if command.max_args is not None and arg_count > command.max_args:
            return False
        
        return True
    
    def get_command_help(self, command_name: str) -> Optional[str]:
        """获取命令帮助信息"""
        command = self.get_command(command_name)
        if not command:
            return None
        
        help_text = f"命令: {command.name}\n"
        help_text += f"分类: {command.category.value}\n"
        help_text += f"描述: {command.description}\n"
        
        if command.parameters:
            help_text += "\n参数:\n"
            for param in command.parameters:
                help_text += f"  {param.get('name', '')}: {param.get('description', '')}\n"
        
        if command.examples:
            help_text += "\n示例:\n"
            for example in command.examples:
                help_text += f"  {example}\n"
        
        return help_text
    
    def _analyze_parameters(self, handler: Callable) -> List[Dict[str, Any]]:
        """分析函数参数"""
        try:
            sig = inspect.signature(handler)
            parameters = []
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'args', 'kwargs']:
                    continue
                
                param_info = {
                    "name": param_name,
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty,
                    "default": param.default if param.default != inspect.Parameter.empty else None
                }
                parameters.append(param_info)
            
            return parameters
        except Exception as e:
            self.logger.warning(f"无法分析函数参数: {e}")
            return []


# 全局命令注册器实例
_registry: Optional[CommandRegistry] = None


def get_command_registry() -> CommandRegistry:
    """获取全局命令注册器实例"""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry

