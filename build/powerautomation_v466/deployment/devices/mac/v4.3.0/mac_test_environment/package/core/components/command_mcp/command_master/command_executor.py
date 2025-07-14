"""
PowerAutomation 4.0 Command Executor
命令执行器，支持并行命令执行和结果管理
"""

import asyncio
import logging
import shlex
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import time
import uuid

from .command_registry import CommandRegistry, get_command_registry
from core.parallel_executor import get_executor
from core.event_bus import EventType, get_event_bus
from core.config import get_config
from core.exceptions import (
    CommandError, ValidationError, PowerAutomationException,
    handle_exception, safe_execute, ExceptionContext
)
from core.logging_config import get_command_logger


@dataclass
class CommandResult:
    """命令执行结果数据类"""
    command: str
    args: List[str]
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    task_id: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0


class CommandExecutor:
    """命令执行器类"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_command_logger()
        self.registry: CommandRegistry = get_command_registry()
        self.event_bus = get_event_bus()
        
        # 执行历史
        self.execution_history: List[CommandResult] = []
        self.max_history_size = getattr(self.config, 'max_history', 1000)
        
        # 统计信息
        self.stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "retry_attempts": 0
        }
        
        # 重试配置
        self.max_retries = getattr(self.config, 'max_retries', 3)
        self.retry_delay = 1.0  # 秒
    
    async def execute_command(
        self, 
        command_line: str, 
        context: Dict[str, Any] = None
    ) -> CommandResult:
        """执行命令行"""
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        with ExceptionContext({'command_line': command_line, 'task_id': task_id}, reraise=False):
            try:
                # 解析命令行
                parts = shlex.split(command_line)
                if not parts:
                    raise ValidationError("空命令", field="command_line", value=command_line)
                
                command = parts[0]
                args = parts[1:] if len(parts) > 1 else []
                
                self.logger.info(f"开始执行命令: {command_line}", 
                               command=command, args=args, task_id=task_id)
                
                return await self.execute_command_with_args(command, args, context, task_id)
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = str(e)
                error_code = getattr(e, 'error_code', None)
                
                result = CommandResult(
                    command=command_line,
                    args=[],
                    success=False,
                    error=error_msg,
                    execution_time=execution_time,
                    task_id=task_id,
                    error_code=error_code.name if error_code else None
                )
                
                self._add_to_history(result)
                self.stats["failed_commands"] += 1
                self.stats["total_commands"] += 1
                
                self.logger.error(f"命令执行失败: {command_line}", 
                                error=error_msg, task_id=task_id, execution_time=execution_time)
                return result
    
    async def execute_command_with_args(
        self,
        command: str,
        args: List[str] = None,
        context: Dict[str, Any] = None,
        task_id: Optional[str] = None
    ) -> CommandResult:
        """执行指定命令和参数，支持重试机制"""
        start_time = time.time()
        args = args or []
        context = context or {}
        task_id = task_id or str(uuid.uuid4())
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # 获取命令信息
                command_info = self.registry.get_command(command)
                if not command_info:
                    raise CommandError(f"未知命令: {command}", command=command)
                
                # 验证参数
                if not self.registry.validate_command_args(command, args):
                    raise ValidationError(f"命令参数无效: {command} {' '.join(args)}", 
                                        field="args", value=args)
                
                # 执行命令
                self.logger.debug(f"执行命令函数: {command}", 
                                args=args, retry_count=retry_count, task_id=task_id)
                
                result = await self._execute_command_function(command_info, args, context)
                execution_time = time.time() - start_time
                
                # 创建成功结果
                command_result = CommandResult(
                    command=command,
                    args=args,
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    task_id=task_id,
                    retry_count=retry_count
                )
                
                self._add_to_history(command_result)
                self.stats["successful_commands"] += 1
                self.stats["total_commands"] += 1
                
                self.logger.info(f"命令执行成功: {command}", 
                               args=args, task_id=task_id, execution_time=execution_time)
                
                # 发送成功事件
                await self.event_bus.emit(EventType.COMMAND_COMPLETED, {
                    'command': command,
                    'args': args,
                    'result': result,
                    'task_id': task_id
                })
                
                return command_result
                
            except Exception as e:
                retry_count += 1
                self.stats["retry_attempts"] += 1
                
                if retry_count <= self.max_retries:
                    self.logger.warning(f"命令执行失败，准备重试 ({retry_count}/{self.max_retries}): {command}", 
                                      error=str(e), task_id=task_id)
                    await asyncio.sleep(self.retry_delay * retry_count)  # 指数退避
                    continue
                else:
                    # 最终失败
                    execution_time = time.time() - start_time
                    error_msg = str(e)
                    error_code = getattr(e, 'error_code', None)
                    
                    command_result = CommandResult(
                        command=command,
                        args=args,
                        success=False,
                        error=error_msg,
                        execution_time=execution_time,
                        task_id=task_id,
                        error_code=error_code.name if error_code else None,
                        retry_count=retry_count - 1
                    )
                    
                    self._add_to_history(command_result)
                    self.stats["failed_commands"] += 1
                    self.stats["total_commands"] += 1
                    
                    self.logger.error(f"命令执行最终失败: {command}", 
                                    error=error_msg, task_id=task_id, 
                                    retry_count=retry_count-1, execution_time=execution_time)
                    
                    # 发送失败事件
                    await self.event_bus.emit(EventType.COMMAND_FAILED, {
                        'command': command,
                        'args': args,
                        'error': error_msg,
                        'task_id': task_id
                    })
                    
                    return command_result
    
    async def _execute_command_function(self, command_info: Dict[str, Any], args: List[str], context: Dict[str, Any]) -> Any:
        """执行命令函数"""
        try:
            command_func = command_info['function']
            
            # 检查是否是异步函数
            if asyncio.iscoroutinefunction(command_func):
                return await command_func(*args, **context)
            else:
                # 在线程池中执行同步函数
                executor = await get_executor()
                return await asyncio.get_event_loop().run_in_executor(
                    executor, lambda: command_func(*args, **context)
                )
        except Exception as e:
            # 包装为CommandError
            if not isinstance(e, PowerAutomationException):
                raise CommandError(f"命令执行异常: {str(e)}", 
                                 command=command_info.get('name', 'unknown'), cause=e)
            raise
    
    async def execute_parallel_commands(
        self,
        commands: List[Union[str, Dict[str, Any]]],
        context: Dict[str, Any] = None
    ) -> List[CommandResult]:
        """并行执行多个命令"""
        tasks = []
        
        for cmd in commands:
            if isinstance(cmd, str):
                task = asyncio.create_task(self.execute_command(cmd, context))
            elif isinstance(cmd, dict):
                command = cmd.get("command", "")
                args = cmd.get("args", [])
                cmd_context = {**(context or {}), **cmd.get("context", {})}
                task = asyncio.create_task(
                    self.execute_command_with_args(command, args, cmd_context)
                )
            else:
                continue
            
            tasks.append(task)
        
        # 并行执行所有命令
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                cmd_str = commands[i] if isinstance(commands[i], str) else str(commands[i])
                error_result = CommandResult(
                    command=cmd_str,
                    args=[],
                    success=False,
                    error=str(result),
                    execution_time=0.0
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_command_suggestions(self, partial_command: str) -> List[str]:
        """获取命令建议"""
        suggestions = []
        partial_lower = partial_command.lower()
        
        for command_name in self.registry.commands.keys():
            if command_name.startswith(partial_lower):
                suggestions.append(command_name)
        
        return sorted(suggestions)
    
    async def get_execution_history(self, limit: int = 100) -> List[CommandResult]:
        """获取执行历史"""
        return self.execution_history[-limit:]
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        self.stats["total_commands"] = self.stats["successful_commands"] + self.stats["failed_commands"]
        return self.stats.copy()
    
    def _add_to_history(self, result: CommandResult):
        """添加到执行历史"""
        self.execution_history.append(result)
        if len(self.execution_history) > self.max_history_size:
            self.execution_history.pop(0)


# 全局命令执行器实例
_executor: Optional[CommandExecutor] = None


def get_command_executor() -> CommandExecutor:
    """获取全局命令执行器实例"""
    global _executor
    if _executor is None:
        _executor = CommandExecutor()
    return _executor

