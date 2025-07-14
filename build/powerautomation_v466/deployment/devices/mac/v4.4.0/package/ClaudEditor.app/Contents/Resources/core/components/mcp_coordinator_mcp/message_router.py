"""
PowerAutomation 4.0 消息路由器

负责在MCP服务之间高效路由和转发消息，支持多种路由策略和消息模式。
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from .coordinator import MCPMessage, MCPServiceInfo


class RoutingStrategy(Enum):
    """路由策略枚举"""
    DIRECT = "direct"           # 直接路由
    ROUND_ROBIN = "round_robin" # 轮询
    RANDOM = "random"           # 随机
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    WEIGHTED = "weighted"       # 加权


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RoutingRule:
    """路由规则"""
    rule_id: str
    source_pattern: str = "*"
    target_pattern: str = "*"
    message_type_pattern: str = "*"
    strategy: RoutingStrategy = RoutingStrategy.DIRECT
    priority: MessagePriority = MessagePriority.NORMAL
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageMetrics:
    """消息指标"""
    total_messages: int = 0
    successful_routes: int = 0
    failed_routes: int = 0
    average_latency: float = 0.0
    last_message_time: Optional[datetime] = None


class MessageRouter:
    """
    PowerAutomation 4.0 消息路由器
    
    功能：
    1. 高效的消息路由和转发
    2. 多种路由策略支持
    3. 消息优先级处理
    4. 路由规则管理
    5. 性能监控和统计
    """
    
    def __init__(self, max_queue_size: int = 10000):
        """
        初始化消息路由器
        
        Args:
            max_queue_size: 最大队列大小
        """
        self.logger = logging.getLogger(__name__)
        self.max_queue_size = max_queue_size
        self.is_running = False
        
        # 消息队列 - 按优先级分组
        self.message_queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size)
            for priority in MessagePriority
        }
        
        # 路由规则
        self.routing_rules: Dict[str, RoutingRule] = {}
        
        # 服务连接池
        self.service_connections: Dict[str, Any] = {}
        self.connection_counts: Dict[str, int] = {}
        
        # 路由策略状态
        self.round_robin_counters: Dict[str, int] = {}
        
        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {}
        
        # 性能指标
        self.metrics = MessageMetrics()
        self.service_metrics: Dict[str, MessageMetrics] = {}
        
        # 工作任务
        self.worker_tasks: List[asyncio.Task] = []
        
        self.logger.info("消息路由器初始化完成")
    
    async def start(self) -> None:
        """启动消息路由器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动消息路由器...")
            
            # 启动消息处理工作器
            self.worker_tasks = [
                asyncio.create_task(self._message_worker(priority))
                for priority in MessagePriority
            ]
            
            # 启动性能监控任务
            self.worker_tasks.append(
                asyncio.create_task(self._metrics_collector())
            )
            
            self.is_running = True
            self.logger.info("消息路由器启动成功")
            
        except Exception as e:
            self.logger.error(f"消息路由器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止消息路由器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止消息路由器...")
            
            self.is_running = False
            
            # 取消所有工作任务
            for task in self.worker_tasks:
                task.cancel()
            
            # 等待任务完成
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
            # 关闭所有连接
            await self._close_all_connections()
            
            self.logger.info("消息路由器已停止")
            
        except Exception as e:
            self.logger.error(f"消息路由器停止时出错: {e}")
    
    async def route_message(self, message: MCPMessage) -> bool:
        """
        路由消息
        
        Args:
            message: 要路由的消息
            
        Returns:
            bool: 路由是否成功
        """
        try:
            start_time = time.time()
            
            # 确定消息优先级
            priority = self._determine_priority(message)
            
            # 将消息加入相应优先级队列
            try:
                await self.message_queues[priority].put(message)
                self.logger.debug(f"消息 {message.message_id} 已加入 {priority.name} 优先级队列")
                return True
                
            except asyncio.QueueFull:
                self.logger.error(f"消息队列已满，丢弃消息 {message.message_id}")
                self.metrics.failed_routes += 1
                return False
            
        except Exception as e:
            self.logger.error(f"路由消息失败: {e}")
            self.metrics.failed_routes += 1
            return False
    
    async def add_routing_rule(self, rule: RoutingRule) -> bool:
        """
        添加路由规则
        
        Args:
            rule: 路由规则
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.routing_rules[rule.rule_id] = rule
            self.logger.info(f"添加路由规则: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加路由规则失败: {e}")
            return False
    
    async def remove_routing_rule(self, rule_id: str) -> bool:
        """
        移除路由规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if rule_id in self.routing_rules:
                del self.routing_rules[rule_id]
                self.logger.info(f"移除路由规则: {rule_id}")
                return True
            else:
                self.logger.warning(f"路由规则不存在: {rule_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"移除路由规则失败: {e}")
            return False
    
    async def get_routing_rules(self) -> List[RoutingRule]:
        """获取所有路由规则"""
        return list(self.routing_rules.values())
    
    async def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理器函数
        """
        self.message_handlers[message_type] = handler
        self.logger.info(f"注册消息处理器: {message_type}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取路由器指标"""
        return {
            "total_messages": self.metrics.total_messages,
            "successful_routes": self.metrics.successful_routes,
            "failed_routes": self.metrics.failed_routes,
            "average_latency": self.metrics.average_latency,
            "success_rate": (
                self.metrics.successful_routes / max(self.metrics.total_messages, 1) * 100
            ),
            "queue_sizes": {
                priority.name: queue.qsize()
                for priority, queue in self.message_queues.items()
            },
            "service_metrics": self.service_metrics,
            "active_connections": len(self.service_connections)
        }
    
    def _determine_priority(self, message: MCPMessage) -> MessagePriority:
        """确定消息优先级"""
        # 检查消息类型
        if message.message_type in ["heartbeat", "health_check"]:
            return MessagePriority.LOW
        elif message.message_type in ["error", "alert", "emergency"]:
            return MessagePriority.CRITICAL
        elif message.message_type in ["command", "request"]:
            return MessagePriority.HIGH
        else:
            return MessagePriority.NORMAL
    
    async def _message_worker(self, priority: MessagePriority) -> None:
        """消息处理工作器"""
        queue = self.message_queues[priority]
        
        while self.is_running:
            try:
                # 等待消息
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                
                # 处理消息
                await self._process_message(message)
                
                # 标记任务完成
                queue.task_done()
                
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except Exception as e:
                self.logger.error(f"消息工作器 {priority.name} 出错: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, message: MCPMessage) -> None:
        """处理单个消息"""
        start_time = time.time()
        
        try:
            self.metrics.total_messages += 1
            
            # 查找匹配的路由规则
            rule = self._find_matching_rule(message)
            
            if rule:
                # 根据路由策略处理消息
                success = await self._route_by_strategy(message, rule)
            else:
                # 使用默认直接路由
                success = await self._direct_route(message)
            
            # 更新指标
            processing_time = time.time() - start_time
            self._update_metrics(message, success, processing_time)
            
            if success:
                self.metrics.successful_routes += 1
                self.logger.debug(f"消息 {message.message_id} 路由成功")
            else:
                self.metrics.failed_routes += 1
                self.logger.error(f"消息 {message.message_id} 路由失败")
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            self.metrics.failed_routes += 1
    
    def _find_matching_rule(self, message: MCPMessage) -> Optional[RoutingRule]:
        """查找匹配的路由规则"""
        for rule in self.routing_rules.values():
            if not rule.enabled:
                continue
            
            # 检查源服务模式
            if not self._match_pattern(message.source_service, rule.source_pattern):
                continue
            
            # 检查目标服务模式
            if not self._match_pattern(message.target_service, rule.target_pattern):
                continue
            
            # 检查消息类型模式
            if not self._match_pattern(message.message_type, rule.message_type_pattern):
                continue
            
            return rule
        
        return None
    
    def _match_pattern(self, value: str, pattern: str) -> bool:
        """模式匹配"""
        if pattern == "*":
            return True
        
        # 简单的通配符匹配
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return value.startswith(prefix) and value.endswith(suffix)
        
        return value == pattern
    
    async def _route_by_strategy(self, message: MCPMessage, rule: RoutingRule) -> bool:
        """根据路由策略路由消息"""
        try:
            if rule.strategy == RoutingStrategy.DIRECT:
                return await self._direct_route(message)
            elif rule.strategy == RoutingStrategy.ROUND_ROBIN:
                return await self._round_robin_route(message)
            elif rule.strategy == RoutingStrategy.RANDOM:
                return await self._random_route(message)
            elif rule.strategy == RoutingStrategy.LEAST_CONNECTIONS:
                return await self._least_connections_route(message)
            elif rule.strategy == RoutingStrategy.WEIGHTED:
                return await self._weighted_route(message)
            else:
                return await self._direct_route(message)
                
        except Exception as e:
            self.logger.error(f"路由策略执行失败: {e}")
            return False
    
    async def _direct_route(self, message: MCPMessage) -> bool:
        """直接路由"""
        try:
            # 检查是否有注册的消息处理器
            if message.message_type in self.message_handlers:
                handler = self.message_handlers[message.message_type]
                await handler(message)
                return True
            
            # 发送到目标服务
            return await self._send_to_service(message.target_service, message)
            
        except Exception as e:
            self.logger.error(f"直接路由失败: {e}")
            return False
    
    async def _round_robin_route(self, message: MCPMessage) -> bool:
        """轮询路由"""
        # 这里可以实现轮询逻辑
        # 暂时使用直接路由
        return await self._direct_route(message)
    
    async def _random_route(self, message: MCPMessage) -> bool:
        """随机路由"""
        # 这里可以实现随机路由逻辑
        # 暂时使用直接路由
        return await self._direct_route(message)
    
    async def _least_connections_route(self, message: MCPMessage) -> bool:
        """最少连接路由"""
        # 这里可以实现最少连接路由逻辑
        # 暂时使用直接路由
        return await self._direct_route(message)
    
    async def _weighted_route(self, message: MCPMessage) -> bool:
        """加权路由"""
        # 这里可以实现加权路由逻辑
        # 暂时使用直接路由
        return await self._direct_route(message)
    
    async def _send_to_service(self, service_id: str, message: MCPMessage) -> bool:
        """发送消息到指定服务"""
        try:
            # 这里应该实现实际的消息发送逻辑
            # 可以通过HTTP、WebSocket、gRPC等协议
            
            # 模拟发送成功
            self.logger.debug(f"发送消息 {message.message_id} 到服务 {service_id}")
            
            # 更新连接计数
            self.connection_counts[service_id] = self.connection_counts.get(service_id, 0) + 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"发送消息到服务失败: {e}")
            return False
    
    def _update_metrics(self, message: MCPMessage, success: bool, processing_time: float) -> None:
        """更新指标"""
        # 更新全局指标
        self.metrics.last_message_time = datetime.now()
        
        # 更新平均延迟
        if self.metrics.total_messages > 0:
            self.metrics.average_latency = (
                (self.metrics.average_latency * (self.metrics.total_messages - 1) + processing_time)
                / self.metrics.total_messages
            )
        else:
            self.metrics.average_latency = processing_time
        
        # 更新服务级指标
        service_id = message.target_service
        if service_id not in self.service_metrics:
            self.service_metrics[service_id] = MessageMetrics()
        
        service_metrics = self.service_metrics[service_id]
        service_metrics.total_messages += 1
        service_metrics.last_message_time = datetime.now()
        
        if success:
            service_metrics.successful_routes += 1
        else:
            service_metrics.failed_routes += 1
        
        # 更新服务平均延迟
        if service_metrics.total_messages > 0:
            service_metrics.average_latency = (
                (service_metrics.average_latency * (service_metrics.total_messages - 1) + processing_time)
                / service_metrics.total_messages
            )
        else:
            service_metrics.average_latency = processing_time
    
    async def _metrics_collector(self) -> None:
        """指标收集器"""
        while self.is_running:
            try:
                # 定期清理过期的服务指标
                await self._cleanup_expired_metrics()
                
                # 等待下次收集
                await asyncio.sleep(60)  # 每分钟执行一次
                
            except Exception as e:
                self.logger.error(f"指标收集器出错: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_expired_metrics(self) -> None:
        """清理过期的指标"""
        current_time = datetime.now()
        expired_services = []
        
        for service_id, metrics in self.service_metrics.items():
            if metrics.last_message_time:
                time_diff = (current_time - metrics.last_message_time).total_seconds()
                if time_diff > 3600:  # 1小时无消息则清理
                    expired_services.append(service_id)
        
        for service_id in expired_services:
            del self.service_metrics[service_id]
            self.logger.debug(f"清理过期服务指标: {service_id}")
    
    async def _close_all_connections(self) -> None:
        """关闭所有连接"""
        try:
            for service_id, connection in self.service_connections.items():
                # 这里应该实现实际的连接关闭逻辑
                self.logger.debug(f"关闭服务连接: {service_id}")
            
            self.service_connections.clear()
            self.connection_counts.clear()
            
        except Exception as e:
            self.logger.error(f"关闭连接时出错: {e}")

