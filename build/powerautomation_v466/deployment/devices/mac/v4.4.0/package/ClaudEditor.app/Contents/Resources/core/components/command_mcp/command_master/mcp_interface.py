"""
PowerAutomation 4.0 Command Master MCP Interface
命令系统MCP接口 - 提供命令执行、管理和智能体协作的MCP服务
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import uuid

from .command_executor import CommandExecutor, get_command_executor
from .command_registry import CommandRegistry, get_command_registry
from core.exceptions import CommandError, handle_exception
from core.logging_config import get_command_logger
from core.config import get_config


class CommandMasterMCP:
    """命令系统MCP接口"""
    
    def __init__(self):
        self.logger = get_command_logger()
        self.config = get_config()
        
        # 核心组件
        self.command_executor = get_command_executor()
        self.command_registry = get_command_registry()
        
        # MCP信息
        self.mcp_id = "command_master"
        self.mcp_name = "PowerAutomation Command Master"
        self.mcp_version = "4.0.0"
        self.mcp_description = "智能命令执行和管理系统，支持智能体协作"
        
        # 状态管理
        self.is_initialized = False
        self.active_collaborations: Dict[str, str] = {}  # task_id -> session_id
        
        # 统计信息
        self.mcp_stats = {
            "total_commands_executed": 0,
            "collaborative_commands": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "mcp_start_time": datetime.now()
        }
    
    async def initialize(self) -> bool:
        """初始化命令系统MCP"""
        try:
            self.logger.info("初始化命令系统MCP...")
            
            # 初始化核心组件
            await self.command_executor.initialize()
            await self.command_registry.initialize()
            
            self.is_initialized = True
            self.logger.info("命令系统MCP初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"命令系统MCP初始化失败: {e}")
            return False
    
    # MCP标准接口方法
    
    async def get_mcp_info(self) -> Dict[str, Any]:
        """获取MCP信息"""
        return {
            "mcp_id": self.mcp_id,
            "name": self.mcp_name,
            "version": self.mcp_version,
            "description": self.mcp_description,
            "capabilities": [
                "command_execution",
                "command_management", 
                "agent_collaboration",
                "task_distribution",
                "collaborative_execution",
                "command_suggestion",
                "execution_monitoring",
                "performance_analytics"
            ],
            "status": "active" if self.is_initialized else "inactive",
            "endpoints": [
                "execute_command",
                "execute_collaborative_command",
                "register_command",
                "list_commands",
                "get_command_suggestions",
                "create_collaboration_session",
                "join_collaboration",
                "get_execution_status",
                "get_command_history",
                "get_performance_metrics",
                "get_mcp_health",
                "shutdown_mcp"
            ]
        }
    
    async def get_mcp_health(self) -> Dict[str, Any]:
        """获取MCP健康状态"""
        try:
            # 检查核心组件状态
            executor_healthy = hasattr(self.command_executor, 'is_running') and self.command_executor.is_running
            registry_healthy = len(getattr(self.command_registry, 'commands', {})) > 0
            
            overall_health = executor_healthy and registry_healthy
            
            return {
                "status": "healthy" if overall_health else "unhealthy",
                "components": {
                    "command_executor": "healthy" if executor_healthy else "unhealthy",
                    "command_registry": "healthy" if registry_healthy else "unhealthy"
                },
                "metrics": self.mcp_stats,
                "uptime_seconds": (datetime.now() - self.mcp_stats["mcp_start_time"]).total_seconds(),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    # 命令执行接口
    
    async def execute_command(
        self,
        command: str,
        args: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        requester: str = "system",
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """执行单个命令"""
        try:
            start_time = datetime.now()
            
            # 执行命令
            result = await self.command_executor.execute_command(
                command=command,
                args=args or [],
                context=context or {},
                requester=requester
            )
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计
            self.mcp_stats["total_commands_executed"] += 1
            if result.get("status") == "success":
                self.mcp_stats["successful_executions"] += 1
            else:
                self.mcp_stats["failed_executions"] += 1
            
            self._update_average_execution_time(execution_time)
            
            # 添加执行信息
            result["execution_time"] = execution_time
            result["executed_at"] = start_time.isoformat()
            result["mcp_id"] = self.mcp_id
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            self.mcp_stats["failed_executions"] += 1
            return {
                "status": "error",
                "error": str(e),
                "command": command,
                "mcp_id": self.mcp_id
            }
    
    async def execute_collaborative_command(
        self,
        command: str,
        args: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        requester: str = "system",
        collaboration_type: str = "multi_agent",
        required_agents: Optional[List[str]] = None,
        max_agents: int = 3
    ) -> Dict[str, Any]:
        """执行协作命令"""
        try:
            start_time = datetime.now()
            task_id = str(uuid.uuid4())
            
            # 模拟协作命令执行
            # 在实际实现中，这里会与智能体协调器集成
            
            # 更新统计
            self.mcp_stats["collaborative_commands"] += 1
            
            return {
                "status": "started",
                "task_id": task_id,
                "command": command,
                "collaboration_type": collaboration_type,
                "started_at": start_time.isoformat(),
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            self.logger.error(f"执行协作命令失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "command": command,
                "mcp_id": self.mcp_id
            }
    
    async def get_execution_status(self, task_id: str) -> Dict[str, Any]:
        """获取命令执行状态"""
        try:
            # 检查是否是协作任务
            if task_id in self.active_collaborations:
                return {
                    "task_id": task_id,
                    "type": "collaborative",
                    "status": "running",
                    "mcp_id": self.mcp_id
                }
            else:
                # 检查单个命令执行状态
                return {
                    "task_id": task_id,
                    "type": "single",
                    "status": "completed",
                    "mcp_id": self.mcp_id
                }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "task_id": task_id,
                "mcp_id": self.mcp_id
            }
    
    # 命令管理接口
    
    async def register_command(
        self,
        command_name: str,
        command_info: Dict[str, Any],
        requester: str = "system"
    ) -> Dict[str, Any]:
        """注册新命令"""
        try:
            success = await self.command_registry.register_command(command_name, command_info)
            
            if success:
                return {
                    "status": "success",
                    "message": f"命令已注册: {command_name}",
                    "command_name": command_name,
                    "registered_by": requester,
                    "registered_at": datetime.now().isoformat(),
                    "mcp_id": self.mcp_id
                }
            else:
                return {
                    "status": "failed",
                    "error": "命令注册失败",
                    "command_name": command_name,
                    "mcp_id": self.mcp_id
                }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "command_name": command_name,
                "mcp_id": self.mcp_id
            }
    
    async def list_commands(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """列出可用命令"""
        try:
            commands = await self.command_registry.list_commands(category, search)
            
            return {
                "status": "success",
                "commands": commands,
                "total_count": len(commands),
                "category": category,
                "search": search,
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "mcp_id": self.mcp_id
            }
    
    async def get_command_suggestions(
        self,
        context: Dict[str, Any],
        user_input: Optional[str] = None,
        max_suggestions: int = 5
    ) -> Dict[str, Any]:
        """获取命令建议"""
        try:
            suggestions = await self.command_registry.get_command_suggestions(
                context, user_input, max_suggestions
            )
            
            return {
                "status": "success",
                "suggestions": suggestions,
                "context": context,
                "user_input": user_input,
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "mcp_id": self.mcp_id
            }
    
    # 协作管理接口
    
    async def create_collaboration_session(
        self,
        session_name: str,
        participants: List[str],
        objective: str,
        collaboration_type: str = "peer_to_peer",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建协作会话"""
        try:
            session_id = str(uuid.uuid4())
            
            return {
                "status": "success",
                "session_id": session_id,
                "session_name": session_name,
                "participants": participants,
                "collaboration_type": collaboration_type,
                "created_at": datetime.now().isoformat(),
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "mcp_id": self.mcp_id
            }
    
    async def join_collaboration(
        self,
        session_id: str,
        agent_id: str,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """加入协作会话"""
        try:
            return {
                "status": "success",
                "session_id": session_id,
                "agent_id": agent_id,
                "role": role,
                "joined_at": datetime.now().isoformat(),
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id,
                "agent_id": agent_id,
                "mcp_id": self.mcp_id
            }
    
    # 监控和分析接口
    
    async def get_command_history(
        self,
        limit: int = 100,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取命令执行历史"""
        try:
            # 模拟历史数据
            history = []
            
            return {
                "status": "success",
                "history": history,
                "total_count": len(history),
                "filters": {
                    "limit": limit,
                    "start_time": start_time,
                    "end_time": end_time,
                    "status_filter": status_filter
                },
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "mcp_id": self.mcp_id
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            return {
                "status": "success",
                "mcp_stats": self.mcp_stats,
                "collected_at": datetime.now().isoformat(),
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "mcp_id": self.mcp_id
            }
    
    # 工具方法
    
    def _update_average_execution_time(self, execution_time: float):
        """更新平均执行时间"""
        total_executions = self.mcp_stats["total_commands_executed"]
        if total_executions > 0:
            current_avg = self.mcp_stats["average_execution_time"]
            new_avg = (current_avg * (total_executions - 1) + execution_time) / total_executions
            self.mcp_stats["average_execution_time"] = new_avg
    
    async def shutdown_mcp(self) -> Dict[str, Any]:
        """关闭MCP"""
        try:
            self.logger.info("关闭命令系统MCP...")
            
            # 关闭核心组件
            if hasattr(self.command_executor, 'shutdown'):
                await self.command_executor.shutdown()
            
            # 结束所有活跃的协作会话
            for task_id, session_id in list(self.active_collaborations.items()):
                del self.active_collaborations[task_id]
            
            self.is_initialized = False
            
            return {
                "status": "success",
                "message": "命令系统MCP已关闭",
                "shutdown_at": datetime.now().isoformat(),
                "mcp_id": self.mcp_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "mcp_id": self.mcp_id
            }


# 全局命令系统MCP实例
_command_master_mcp: Optional[CommandMasterMCP] = None


def get_command_master_mcp() -> CommandMasterMCP:
    """获取全局命令系统MCP实例"""
    global _command_master_mcp
    if _command_master_mcp is None:
        _command_master_mcp = CommandMasterMCP()
    return _command_master_mcp

