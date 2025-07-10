"""
PowerAutomation 4.0 Communication Hub
通信中心 - 负责MCP之间的消息传递和通信协调
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
from enum import Enum

from core.exceptions import MCPCommunicationError, handle_exception
from core.logging_config import get_mcp_logger
from core.config import get_config


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class MessagePriority(Enum):
    """消息优先级枚举"""
    LOW = 1
    NORMAL = 3
    HIGH = 5
    URGENT = 7
    CRITICAL = 9


@dataclass
class Message:
    """消息数据结构"""
    id: str
    type: MessageType
    sender: str
    receiver: str
    method: Optional[str]
    params: Optional[Dict[str, Any]]
    result: Optional[Any]
    error: Optional[Dict[str, Any]]
    priority: MessagePriority
    timestamp: datetime
    correlation_id: Optional[str] = None
    timeout: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class MessageRoute:
    """消息路由信息"""
    sender: str
    receiver: str
    message_type: MessageType
    handler: Callable
    is_active: bool = True


class CommunicationHub:
    """通信中心 - 负责MCP之间的消息传递"""
    
    def __init__(self):
        self.logger = get_mcp_logger()
        self.config = get_config()
        
        # 消息队列
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.priority_queues: Dict[str, Dict[MessagePriority, asyncio.Queue]] = {}
        
        # 路由表
        self.routes: List[MessageRoute] = []
        self.subscribers: Dict[str, Set[str]] = {}  # 事件订阅者
        
        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
        
        # 连接管理
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.connection_status: Dict[str, bool] = {}
        
        # 统计信息
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "active_connections": 0,
            "total_connections": 0
        }
        
        # 运行状态
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # 配置参数
        self.max_queue_size = 1000
        self.default_timeout = 30
        self.heartbeat_interval = 10
        self.cleanup_interval = 60
    
    async def initialize(self) -> bool:
        """初始化通信中心"""
        try:
            self.logger.info("初始化通信中心...")
            
            # 启动消息处理工作线程
            self.is_running = True
            self.worker_tasks = [
                asyncio.create_task(self._message_processor()),
                asyncio.create_task(self._heartbeat_monitor()),
                asyncio.create_task(self._cleanup_worker())
            ]
            
            self.logger.info("通信中心初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"通信中心初始化失败: {e}")
            return False
    
    async def register_mcp(self, mcp_id: str, connection_info: Dict[str, Any]) -> bool:
        """注册MCP到通信中心"""
        try:
            # 创建消息队列
            self.message_queues[mcp_id] = asyncio.Queue(maxsize=self.max_queue_size)
            
            # 创建优先级队列
            self.priority_queues[mcp_id] = {
                priority: asyncio.Queue(maxsize=self.max_queue_size)
                for priority in MessagePriority
            }
            
            # 保存连接信息
            self.connections[mcp_id] = {
                **connection_info,
                "registered_at": datetime.now(),
                "last_heartbeat": datetime.now()
            }
            
            self.connection_status[mcp_id] = True
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
            self.logger.info(f"MCP已注册到通信中心: {mcp_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册MCP失败: {mcp_id}, 错误: {e}")
            return False
    
    async def unregister_mcp(self, mcp_id: str) -> bool:
        """从通信中心注销MCP"""
        try:
            # 清理队列
            if mcp_id in self.message_queues:
                del self.message_queues[mcp_id]
            
            if mcp_id in self.priority_queues:
                del self.priority_queues[mcp_id]
            
            # 清理连接信息
            if mcp_id in self.connections:
                del self.connections[mcp_id]
            
            if mcp_id in self.connection_status:
                del self.connection_status[mcp_id]
                self.stats["active_connections"] -= 1
            
            # 清理路由
            self.routes = [route for route in self.routes 
                          if route.sender != mcp_id and route.receiver != mcp_id]
            
            # 清理订阅
            for event_type in list(self.subscribers.keys()):
                self.subscribers[event_type].discard(mcp_id)
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
            
            self.logger.info(f"MCP已从通信中心注销: {mcp_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注销MCP失败: {mcp_id}, 错误: {e}")
            return False
    
    async def send_message(
        self,
        sender: str,
        receiver: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        timeout: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """发送消息"""
        try:
            # 创建消息
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                sender=sender,
                receiver=receiver,
                method=method,
                params=params,
                result=None,
                error=None,
                priority=priority,
                timestamp=datetime.now(),
                correlation_id=correlation_id,
                timeout=timeout or self.default_timeout
            )
            
            # 验证接收者
            if receiver not in self.connection_status or not self.connection_status[receiver]:
                raise MCPCommunicationError(f"接收者不可用: {receiver}")
            
            # 应用中间件
            for middleware in self.middleware:
                message = await middleware(message)
            
            # 路由消息
            await self._route_message(message)
            
            self.stats["messages_sent"] += 1
            self.logger.debug(f"消息已发送: {message.id} from {sender} to {receiver}")
            
            return message.id
            
        except Exception as e:
            self.stats["messages_failed"] += 1
            self.logger.error(f"发送消息失败: {e}")
            raise MCPCommunicationError(f"发送消息失败: {str(e)}")
    
    async def send_response(
        self,
        original_message: Message,
        result: Optional[Any] = None,
        error: Optional[Dict[str, Any]] = None
    ) -> str:
        """发送响应消息"""
        try:
            response = Message(
                id=str(uuid.uuid4()),
                type=MessageType.RESPONSE,
                sender=original_message.receiver,
                receiver=original_message.sender,
                method=original_message.method,
                params=None,
                result=result,
                error=error,
                priority=original_message.priority,
                timestamp=datetime.now(),
                correlation_id=original_message.id
            )
            
            await self._route_message(response)
            
            self.stats["messages_sent"] += 1
            return response.id
            
        except Exception as e:
            self.stats["messages_failed"] += 1
            self.logger.error(f"发送响应失败: {e}")
            raise MCPCommunicationError(f"发送响应失败: {str(e)}")
    
    async def broadcast_message(
        self,
        sender: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        exclude: Optional[Set[str]] = None
    ) -> List[str]:
        """广播消息"""
        try:
            exclude = exclude or set()
            message_ids = []
            
            # 向所有活跃的MCP发送消息
            for mcp_id in self.connection_status:
                if self.connection_status[mcp_id] and mcp_id != sender and mcp_id not in exclude:
                    message_id = await self.send_message(
                        sender=sender,
                        receiver=mcp_id,
                        method=method,
                        params=params,
                        priority=priority
                    )
                    message_ids.append(message_id)
            
            self.logger.info(f"广播消息已发送: {len(message_ids)} 个接收者")
            return message_ids
            
        except Exception as e:
            self.logger.error(f"广播消息失败: {e}")
            raise MCPCommunicationError(f"广播消息失败: {str(e)}")
    
    async def subscribe_event(self, mcp_id: str, event_type: str) -> bool:
        """订阅事件"""
        try:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = set()
            
            self.subscribers[event_type].add(mcp_id)
            self.logger.info(f"MCP {mcp_id} 已订阅事件: {event_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"订阅事件失败: {e}")
            return False
    
    async def unsubscribe_event(self, mcp_id: str, event_type: str) -> bool:
        """取消订阅事件"""
        try:
            if event_type in self.subscribers:
                self.subscribers[event_type].discard(mcp_id)
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
            
            self.logger.info(f"MCP {mcp_id} 已取消订阅事件: {event_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"取消订阅事件失败: {e}")
            return False
    
    async def publish_event(
        self,
        publisher: str,
        event_type: str,
        event_data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> int:
        """发布事件"""
        try:
            if event_type not in self.subscribers:
                return 0
            
            sent_count = 0
            for subscriber in self.subscribers[event_type]:
                if subscriber != publisher:
                    await self.send_message(
                        sender=publisher,
                        receiver=subscriber,
                        method=f"event.{event_type}",
                        params=event_data,
                        priority=priority
                    )
                    sent_count += 1
            
            self.logger.info(f"事件已发布: {event_type}, 发送给 {sent_count} 个订阅者")
            return sent_count
            
        except Exception as e:
            self.logger.error(f"发布事件失败: {e}")
            raise MCPCommunicationError(f"发布事件失败: {str(e)}")
    
    async def add_route(
        self,
        sender: str,
        receiver: str,
        message_type: MessageType,
        handler: Callable
    ) -> bool:
        """添加消息路由"""
        try:
            route = MessageRoute(
                sender=sender,
                receiver=receiver,
                message_type=message_type,
                handler=handler
            )
            
            self.routes.append(route)
            self.logger.info(f"路由已添加: {sender} -> {receiver} ({message_type.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"添加路由失败: {e}")
            return False
    
    async def _route_message(self, message: Message):
        """路由消息到目标队列"""
        try:
            receiver = message.receiver
            
            # 检查接收者是否存在
            if receiver not in self.message_queues:
                raise MCPCommunicationError(f"接收者不存在: {receiver}")
            
            # 根据优先级选择队列
            if message.priority in self.priority_queues[receiver]:
                queue = self.priority_queues[receiver][message.priority]
            else:
                queue = self.message_queues[receiver]
            
            # 将消息放入队列
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # 队列满了，丢弃低优先级消息或报错
                if message.priority.value >= MessagePriority.HIGH.value:
                    # 高优先级消息，尝试清理低优先级消息
                    await self._cleanup_low_priority_messages(receiver)
                    queue.put_nowait(message)
                else:
                    raise MCPCommunicationError(f"消息队列已满: {receiver}")
            
        except Exception as e:
            self.logger.error(f"路由消息失败: {e}")
            raise
    
    async def _cleanup_low_priority_messages(self, mcp_id: str):
        """清理低优先级消息"""
        try:
            low_priority_queue = self.priority_queues[mcp_id][MessagePriority.LOW]
            discarded_count = 0
            
            while not low_priority_queue.empty():
                try:
                    low_priority_queue.get_nowait()
                    discarded_count += 1
                except asyncio.QueueEmpty:
                    break
            
            if discarded_count > 0:
                self.logger.warning(f"丢弃了 {discarded_count} 个低优先级消息: {mcp_id}")
                
        except Exception as e:
            self.logger.error(f"清理低优先级消息失败: {e}")
    
    async def _message_processor(self):
        """消息处理工作线程"""
        while self.is_running:
            try:
                # 处理所有MCP的消息
                for mcp_id in list(self.message_queues.keys()):
                    await self._process_mcp_messages(mcp_id)
                
                # 短暂休眠
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"消息处理器异常: {e}")
                await asyncio.sleep(1)
    
    async def _process_mcp_messages(self, mcp_id: str):
        """处理特定MCP的消息"""
        try:
            # 按优先级处理消息
            for priority in sorted(MessagePriority, key=lambda x: x.value, reverse=True):
                if mcp_id in self.priority_queues and priority in self.priority_queues[mcp_id]:
                    queue = self.priority_queues[mcp_id][priority]
                    
                    while not queue.empty():
                        try:
                            message = queue.get_nowait()
                            await self._handle_message(message)
                            self.stats["messages_received"] += 1
                        except asyncio.QueueEmpty:
                            break
                        except Exception as e:
                            self.logger.error(f"处理消息失败: {e}")
                            self.stats["messages_failed"] += 1
            
        except Exception as e:
            self.logger.error(f"处理MCP消息失败 {mcp_id}: {e}")
    
    async def _handle_message(self, message: Message):
        """处理单个消息"""
        try:
            # 查找匹配的路由
            matching_routes = [
                route for route in self.routes
                if (route.sender == message.sender or route.sender == "*") and
                   (route.receiver == message.receiver or route.receiver == "*") and
                   route.message_type == message.type and
                   route.is_active
            ]
            
            if matching_routes:
                # 使用第一个匹配的路由
                route = matching_routes[0]
                await route.handler(message)
            else:
                # 没有匹配的路由，使用默认处理器
                if message.method in self.message_handlers:
                    handler = self.message_handlers[message.method]
                    await handler(message)
                else:
                    self.logger.warning(f"没有找到消息处理器: {message.method}")
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            
            # 发送错误响应
            if message.type == MessageType.REQUEST:
                await self.send_response(
                    message,
                    error={
                        "code": -32603,
                        "message": f"内部错误: {str(e)}"
                    }
                )
    
    async def _heartbeat_monitor(self):
        """心跳监控工作线程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 检查所有连接的心跳
                for mcp_id, connection_info in list(self.connections.items()):
                    last_heartbeat = connection_info.get("last_heartbeat")
                    if last_heartbeat:
                        time_diff = (current_time - last_heartbeat).total_seconds()
                        
                        # 如果超过心跳间隔的3倍没有收到心跳，标记为不活跃
                        if time_diff > self.heartbeat_interval * 3:
                            if self.connection_status.get(mcp_id, False):
                                self.connection_status[mcp_id] = False
                                self.stats["active_connections"] -= 1
                                self.logger.warning(f"MCP连接超时: {mcp_id}")
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳监控异常: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_worker(self):
        """清理工作线程"""
        while self.is_running:
            try:
                # 清理过期消息、统计信息等
                await self._cleanup_expired_messages()
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理工作异常: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_expired_messages(self):
        """清理过期消息"""
        # 这里可以实现消息过期清理逻辑
        pass
    
    async def update_heartbeat(self, mcp_id: str) -> bool:
        """更新MCP心跳"""
        try:
            if mcp_id in self.connections:
                self.connections[mcp_id]["last_heartbeat"] = datetime.now()
                
                # 如果之前是不活跃状态，恢复为活跃
                if not self.connection_status.get(mcp_id, False):
                    self.connection_status[mcp_id] = True
                    self.stats["active_connections"] += 1
                    self.logger.info(f"MCP连接已恢复: {mcp_id}")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"更新心跳失败: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "active_connections": self.stats["active_connections"],
            "total_connections": self.stats["total_connections"],
            "connection_details": {
                mcp_id: {
                    "is_active": self.connection_status.get(mcp_id, False),
                    "last_heartbeat": conn_info.get("last_heartbeat"),
                    "registered_at": conn_info.get("registered_at")
                }
                for mcp_id, conn_info in self.connections.items()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "queue_sizes": {
                mcp_id: queue.qsize()
                for mcp_id, queue in self.message_queues.items()
            },
            "routes_count": len(self.routes),
            "subscribers_count": sum(len(subs) for subs in self.subscribers.values()),
            "is_running": self.is_running
        }
    
    async def shutdown(self):
        """关闭通信中心"""
        try:
            self.logger.info("关闭通信中心...")
            
            self.is_running = False
            
            # 取消所有工作任务
            for task in self.worker_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 清理资源
            self.message_queues.clear()
            self.priority_queues.clear()
            self.connections.clear()
            self.connection_status.clear()
            
            self.logger.info("通信中心已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭通信中心失败: {e}")


# 全局通信中心实例
_communication_hub: Optional[CommunicationHub] = None


def get_communication_hub() -> CommunicationHub:
    """获取全局通信中心实例"""
    global _communication_hub
    if _communication_hub is None:
        _communication_hub = CommunicationHub()
    return _communication_hub

