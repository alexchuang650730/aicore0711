"""
PowerAutomation 4.0 MCP Coordinator
MCP协调器 - 统一的MCP通信和协调中心
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import time
from datetime import datetime
import uuid

# 导入核心模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.parallel_executor import get_executor
from core.event_bus import EventType, get_event_bus
from core.config import get_config

class MCPStatus(Enum):
    """MCP状态枚举"""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    REGISTRATION = "registration"
    DEREGISTRATION = "deregistration"

@dataclass
class MCPInfo:
    """MCP信息数据结构"""
    mcp_id: str
    name: str
    version: str
    capabilities: List[str]
    endpoints: Dict[str, str]
    status: MCPStatus
    load: float = 0.0
    last_heartbeat: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class MCPMessage:
    """MCP消息数据结构"""
    message_id: str
    message_type: MessageType
    source_mcp: str
    target_mcp: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 5
    timeout: int = 30
    correlation_id: Optional[str] = None

@dataclass
class WorkflowTask:
    """工作流任务数据结构"""
    task_id: str
    workflow_id: str
    task_type: str
    input_data: Dict[str, Any]
    assigned_mcp: str
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class MCPCoordinator:
    """MCP协调器 - 统一的MCP通信和协调中心"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.event_bus = get_event_bus()
        self.executor = get_executor()
        
        # MCP注册表
        self.registered_mcps: Dict[str, MCPInfo] = {}
        
        # 消息队列和路由
        self.message_queue = asyncio.Queue()
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # 工作流管理
        self.active_workflows: Dict[str, List[WorkflowTask]] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        
        # 性能监控
        self.performance_metrics = {
            "total_messages": 0,
            "successful_messages": 0,
            "failed_messages": 0,
            "average_response_time": 0.0,
            "active_mcps": 0,
            "workflow_success_rate": 0.0
        }
        
        # 负载均衡
        self.load_balancer = {}
        
        self.logger.info("MCPCoordinator 4.0 初始化完成")
    
    async def initialize(self):
        """初始化MCP协调器"""
        try:
            # 启动消息处理器
            await self._start_message_processor()
            
            # 启动心跳监控
            await self._start_heartbeat_monitor()
            
            # 加载工作流模板
            await self._load_workflow_templates()
            
            # 注册事件监听器
            await self._register_event_listeners()
            
            self.logger.info("MCPCoordinator 初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"MCPCoordinator 初始化失败: {e}")
            return False
    
    async def register_mcp(self, mcp_info: MCPInfo) -> bool:
        """
        注册MCP
        
        Args:
            mcp_info: MCP信息
            
        Returns:
            bool: 注册是否成功
        """
        try:
            mcp_id = mcp_info.mcp_id
            
            # 验证MCP信息
            if not await self._validate_mcp_info(mcp_info):
                self.logger.error(f"MCP信息验证失败: {mcp_id}")
                return False
            
            # 注册MCP
            mcp_info.status = MCPStatus.ACTIVE
            mcp_info.last_heartbeat = datetime.now()
            self.registered_mcps[mcp_id] = mcp_info
            
            # 更新性能指标
            self.performance_metrics["active_mcps"] = len(self.registered_mcps)
            
            # 发送注册成功通知
            await self._send_notification(mcp_id, {
                "type": "registration_success",
                "message": f"MCP {mcp_info.name} 注册成功"
            })
            
            self.logger.info(f"MCP注册成功: {mcp_info.name} ({mcp_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"MCP注册失败: {e}")
            return False
    
    async def deregister_mcp(self, mcp_id: str) -> bool:
        """
        注销MCP
        
        Args:
            mcp_id: MCP ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if mcp_id in self.registered_mcps:
                mcp_info = self.registered_mcps[mcp_id]
                
                # 清理相关资源
                await self._cleanup_mcp_resources(mcp_id)
                
                # 移除注册
                del self.registered_mcps[mcp_id]
                
                # 更新性能指标
                self.performance_metrics["active_mcps"] = len(self.registered_mcps)
                
                self.logger.info(f"MCP注销成功: {mcp_info.name} ({mcp_id})")
                return True
            else:
                self.logger.warning(f"尝试注销不存在的MCP: {mcp_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"MCP注销失败: {e}")
            return False
    
    async def send_message(self, message: MCPMessage) -> Optional[Dict[str, Any]]:
        """
        发送消息到指定MCP
        
        Args:
            message: MCP消息
            
        Returns:
            Optional[Dict[str, Any]]: 响应结果
        """
        try:
            # 验证目标MCP
            if message.target_mcp not in self.registered_mcps:
                raise ValueError(f"目标MCP不存在: {message.target_mcp}")
            
            target_mcp = self.registered_mcps[message.target_mcp]
            if target_mcp.status != MCPStatus.ACTIVE:
                raise ValueError(f"目标MCP不可用: {message.target_mcp} (状态: {target_mcp.status})")
            
            # 记录消息
            self.performance_metrics["total_messages"] += 1
            start_time = time.time()
            
            # 如果是请求消息，创建响应Future
            response_future = None
            if message.message_type == MessageType.REQUEST:
                response_future = asyncio.Future()
                self.pending_responses[message.message_id] = response_future
            
            # 将消息放入队列
            await self.message_queue.put(message)
            
            # 等待响应（如果是请求消息）
            if response_future:
                try:
                    response = await asyncio.wait_for(response_future, timeout=message.timeout)
                    
                    # 更新性能指标
                    response_time = time.time() - start_time
                    self._update_response_time(response_time)
                    self.performance_metrics["successful_messages"] += 1
                    
                    return response
                    
                except asyncio.TimeoutError:
                    self.logger.error(f"消息超时: {message.message_id}")
                    self.performance_metrics["failed_messages"] += 1
                    return None
                finally:
                    # 清理pending response
                    if message.message_id in self.pending_responses:
                        del self.pending_responses[message.message_id]
            
            return {"status": "sent"}
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            self.performance_metrics["failed_messages"] += 1
            return None
    
    async def create_workflow(self, workflow_id: str, tasks: List[Dict[str, Any]]) -> bool:
        """
        创建工作流
        
        Args:
            workflow_id: 工作流ID
            tasks: 任务列表
            
        Returns:
            bool: 创建是否成功
        """
        try:
            workflow_tasks = []
            
            for task_data in tasks:
                # 分配MCP
                assigned_mcp = await self._assign_mcp_for_task(task_data)
                if not assigned_mcp:
                    self.logger.error(f"无法为任务分配MCP: {task_data}")
                    return False
                
                # 创建工作流任务
                task = WorkflowTask(
                    task_id=str(uuid.uuid4()),
                    workflow_id=workflow_id,
                    task_type=task_data.get("type", "unknown"),
                    input_data=task_data.get("input", {}),
                    assigned_mcp=assigned_mcp,
                    created_at=datetime.now()
                )
                
                workflow_tasks.append(task)
            
            # 保存工作流
            self.active_workflows[workflow_id] = workflow_tasks
            
            self.logger.info(f"工作流创建成功: {workflow_id}, 任务数: {len(workflow_tasks)}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建工作流失败: {e}")
            return False
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"工作流不存在: {workflow_id}")
            
            tasks = self.active_workflows[workflow_id]
            results = []
            
            # 并行执行任务
            async def execute_task(task: WorkflowTask):
                try:
                    task.status = "running"
                    task.started_at = datetime.now()
                    
                    # 创建任务消息
                    message = MCPMessage(
                        message_id=str(uuid.uuid4()),
                        message_type=MessageType.REQUEST,
                        source_mcp="mcp_coordinator",
                        target_mcp=task.assigned_mcp,
                        content={
                            "task_id": task.task_id,
                            "task_type": task.task_type,
                            "input_data": task.input_data
                        },
                        timestamp=datetime.now()
                    )
                    
                    # 发送任务
                    result = await self.send_message(message)
                    
                    if result:
                        task.status = "completed"
                        task.result = result
                        task.completed_at = datetime.now()
                    else:
                        task.status = "failed"
                        task.result = {"error": "任务执行失败"}
                    
                    return task
                    
                except Exception as e:
                    task.status = "failed"
                    task.result = {"error": str(e)}
                    self.logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")
                    return task
            
            # 并行执行所有任务
            completed_tasks = await asyncio.gather(*[execute_task(task) for task in tasks])
            
            # 统计结果
            successful_tasks = sum(1 for task in completed_tasks if task.status == "completed")
            total_tasks = len(completed_tasks)
            
            workflow_result = {
                "workflow_id": workflow_id,
                "status": "completed" if successful_tasks == total_tasks else "partial_success",
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "failed_tasks": total_tasks - successful_tasks,
                "tasks": [asdict(task) for task in completed_tasks],
                "execution_time": (datetime.now() - tasks[0].created_at).total_seconds()
            }
            
            # 更新工作流成功率
            self._update_workflow_success_rate(successful_tasks / total_tasks)
            
            self.logger.info(f"工作流执行完成: {workflow_id}, 成功率: {successful_tasks}/{total_tasks}")
            return workflow_result
            
        except Exception as e:
            self.logger.error(f"执行工作流失败: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _start_message_processor(self):
        """启动消息处理器"""
        async def process_messages():
            while True:
                try:
                    message = await self.message_queue.get()
                    await self._process_message(message)
                except Exception as e:
                    self.logger.error(f"消息处理错误: {e}")
        
        # 启动消息处理任务
        asyncio.create_task(process_messages())
    
    async def _process_message(self, message: MCPMessage):
        """处理消息"""
        try:
            target_mcp_id = message.target_mcp
            
            # 模拟消息发送到目标MCP
            # 实际实现中这里应该调用目标MCP的API
            
            if message.message_type == MessageType.REQUEST:
                # 模拟处理请求并生成响应
                response_content = await self._simulate_mcp_response(message)
                
                # 发送响应
                if message.message_id in self.pending_responses:
                    future = self.pending_responses[message.message_id]
                    if not future.done():
                        future.set_result(response_content)
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            
            # 如果是请求消息，设置错误响应
            if message.message_type == MessageType.REQUEST and message.message_id in self.pending_responses:
                future = self.pending_responses[message.message_id]
                if not future.done():
                    future.set_result({"error": str(e)})
    
    async def _simulate_mcp_response(self, message: MCPMessage) -> Dict[str, Any]:
        """模拟MCP响应（用于测试）"""
        # 这里应该是实际的MCP调用逻辑
        await asyncio.sleep(0.1)  # 模拟处理时间
        
        return {
            "status": "success",
            "result": f"处理完成: {message.content}",
            "processed_by": message.target_mcp,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _start_heartbeat_monitor(self):
        """启动心跳监控"""
        async def monitor_heartbeats():
            while True:
                try:
                    await asyncio.sleep(30)  # 每30秒检查一次
                    await self._check_mcp_heartbeats()
                except Exception as e:
                    self.logger.error(f"心跳监控错误: {e}")
        
        # 启动心跳监控任务
        asyncio.create_task(monitor_heartbeats())
    
    async def _check_mcp_heartbeats(self):
        """检查MCP心跳"""
        current_time = datetime.now()
        timeout_threshold = 60  # 60秒超时
        
        for mcp_id, mcp_info in list(self.registered_mcps.items()):
            if mcp_info.last_heartbeat:
                time_since_heartbeat = (current_time - mcp_info.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > timeout_threshold:
                    self.logger.warning(f"MCP心跳超时: {mcp_info.name} ({mcp_id})")
                    mcp_info.status = MCPStatus.ERROR
    
    async def _validate_mcp_info(self, mcp_info: MCPInfo) -> bool:
        """验证MCP信息"""
        # 基本验证
        if not mcp_info.mcp_id or not mcp_info.name:
            return False
        
        if not mcp_info.capabilities:
            return False
        
        return True
    
    async def _cleanup_mcp_resources(self, mcp_id: str):
        """清理MCP相关资源"""
        # 清理pending responses
        to_remove = []
        for message_id, future in self.pending_responses.items():
            if not future.done():
                future.set_result({"error": f"MCP {mcp_id} 已注销"})
            to_remove.append(message_id)
        
        for message_id in to_remove:
            if message_id in self.pending_responses:
                del self.pending_responses[message_id]
    
    async def _assign_mcp_for_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """为任务分配MCP"""
        task_type = task_data.get("type", "unknown")
        
        # 简化的MCP分配逻辑
        mcp_mapping = {
            "architecture": "smart_router_mcp",
            "development": "command_master",
            "testing": "command_master",
            "deployment": "command_master",
            "monitoring": "command_master"
        }
        
        assigned_mcp = mcp_mapping.get(task_type, "command_master")
        
        # 检查MCP是否可用
        if assigned_mcp in self.registered_mcps:
            mcp_info = self.registered_mcps[assigned_mcp]
            if mcp_info.status == MCPStatus.ACTIVE:
                return assigned_mcp
        
        # 如果首选MCP不可用，选择任何可用的MCP
        for mcp_id, mcp_info in self.registered_mcps.items():
            if mcp_info.status == MCPStatus.ACTIVE:
                return mcp_id
        
        return None
    
    async def _send_notification(self, target_mcp: str, content: Dict[str, Any]):
        """发送通知"""
        notification = MCPMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.NOTIFICATION,
            source_mcp="mcp_coordinator",
            target_mcp=target_mcp,
            content=content,
            timestamp=datetime.now()
        )
        
        await self.message_queue.put(notification)
    
    def _update_response_time(self, response_time: float):
        """更新响应时间统计"""
        total_messages = self.performance_metrics["successful_messages"]
        current_avg = self.performance_metrics["average_response_time"]
        
        if total_messages == 1:
            self.performance_metrics["average_response_time"] = response_time
        else:
            new_avg = ((current_avg * (total_messages - 1)) + response_time) / total_messages
            self.performance_metrics["average_response_time"] = new_avg
    
    def _update_workflow_success_rate(self, success_rate: float):
        """更新工作流成功率"""
        # 简化的成功率更新逻辑
        current_rate = self.performance_metrics["workflow_success_rate"]
        self.performance_metrics["workflow_success_rate"] = (current_rate + success_rate) / 2
    
    async def _load_workflow_templates(self):
        """加载工作流模板"""
        # 加载工作流模板逻辑
        pass
    
    async def _register_event_listeners(self):
        """注册事件监听器"""
        # 注册事件监听器逻辑
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取协调器统计信息"""
        return {
            **self.performance_metrics,
            "registered_mcps": {mcp_id: {
                "name": info.name,
                "status": info.status.value,
                "load": info.load,
                "capabilities": info.capabilities
            } for mcp_id, info in self.registered_mcps.items()},
            "active_workflows": len(self.active_workflows),
            "pending_responses": len(self.pending_responses),
            "message_queue_size": self.message_queue.qsize()
        }
    
    async def update_mcp_heartbeat(self, mcp_id: str):
        """更新MCP心跳"""
        if mcp_id in self.registered_mcps:
            self.registered_mcps[mcp_id].last_heartbeat = datetime.now()
            if self.registered_mcps[mcp_id].status == MCPStatus.ERROR:
                self.registered_mcps[mcp_id].status = MCPStatus.ACTIVE
                self.logger.info(f"MCP恢复正常: {mcp_id}")
    
    async def update_mcp_load(self, mcp_id: str, load: float):
        """更新MCP负载"""
        if mcp_id in self.registered_mcps:
            self.registered_mcps[mcp_id].load = load

