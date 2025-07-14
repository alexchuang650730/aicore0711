"""
PowerAutomation 4.0 MCP中央协调器

这是PowerAutomation 4.0的核心组件，负责协调所有MCP服务的运行。
所有MCP服务必须通过这个协调器进行注册和通信。
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .service_registry import ServiceRegistry
from .message_router import MessageRouter
from .health_monitor import HealthMonitor
from .load_balancer import LoadBalancer


class MCPServiceStatus(Enum):
    """MCP服务状态枚举"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class MCPServiceInfo:
    """MCP服务信息"""
    service_id: str
    name: str
    version: str
    capabilities: List[str]
    endpoint: str
    status: MCPServiceStatus = MCPServiceStatus.STOPPED
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPMessage:
    """MCP消息格式"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_service: str = ""
    target_service: str = ""
    message_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


class MCPCoordinator:
    """
    PowerAutomation 4.0 MCP中央协调器
    
    负责：
    1. MCP服务的注册和发现
    2. 服务间消息路由
    3. 服务健康监控
    4. 负载均衡
    5. 错误处理和恢复
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化MCP协调器"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self.service_registry = ServiceRegistry()
        self.message_router = MessageRouter()
        self.health_monitor = HealthMonitor()
        self.load_balancer = LoadBalancer()
        
        # 运行状态
        self.is_running = False
        self.services: Dict[str, MCPServiceInfo] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        # 统计信息
        self.stats = {
            "messages_processed": 0,
            "services_registered": 0,
            "errors_count": 0,
            "uptime_start": None
        }
        
        self.logger.info("MCP协调器初始化完成")
    
    async def start(self) -> None:
        """启动MCP协调器"""
        if self.is_running:
            self.logger.warning("MCP协调器已经在运行")
            return
        
        try:
            self.logger.info("启动MCP协调器...")
            
            # 启动核心组件
            await self.service_registry.start()
            await self.message_router.start()
            await self.health_monitor.start()
            await self.load_balancer.start()
            
            # 设置消息处理器
            self._setup_message_handlers()
            
            # 启动后台任务
            asyncio.create_task(self._background_tasks())
            
            self.is_running = True
            self.stats["uptime_start"] = datetime.now()
            
            self.logger.info("MCP协调器启动成功")
            
        except Exception as e:
            self.logger.error(f"MCP协调器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止MCP协调器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止MCP协调器...")
            
            # 停止所有注册的服务
            for service_id in list(self.services.keys()):
                await self.unregister_service(service_id)
            
            # 停止核心组件
            await self.load_balancer.stop()
            await self.health_monitor.stop()
            await self.message_router.stop()
            await self.service_registry.stop()
            
            self.is_running = False
            
            self.logger.info("MCP协调器已停止")
            
        except Exception as e:
            self.logger.error(f"MCP协调器停止时出错: {e}")
            raise
    
    async def register_service(self, service_info: MCPServiceInfo) -> bool:
        """
        注册MCP服务
        
        Args:
            service_info: 服务信息
            
        Returns:
            bool: 注册是否成功
        """
        try:
            # 验证服务信息
            if not self._validate_service_info(service_info):
                return False
            
            # 检查服务是否已注册
            if service_info.service_id in self.services:
                self.logger.warning(f"服务 {service_info.service_id} 已经注册")
                return False
            
            # 注册到服务注册表
            await self.service_registry.register(service_info)
            
            # 添加到本地服务列表
            service_info.status = MCPServiceStatus.RUNNING
            service_info.last_heartbeat = datetime.now()
            self.services[service_info.service_id] = service_info
            
            # 添加到负载均衡器
            await self.load_balancer.add_service(service_info)
            
            # 开始健康监控
            await self.health_monitor.start_monitoring(service_info.service_id)
            
            self.stats["services_registered"] += 1
            
            self.logger.info(f"服务 {service_info.name} ({service_info.service_id}) 注册成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注册服务失败: {e}")
            self.stats["errors_count"] += 1
            return False
    
    async def unregister_service(self, service_id: str) -> bool:
        """
        注销MCP服务
        
        Args:
            service_id: 服务ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if service_id not in self.services:
                self.logger.warning(f"服务 {service_id} 未注册")
                return False
            
            service_info = self.services[service_id]
            
            # 停止健康监控
            await self.health_monitor.stop_monitoring(service_id)
            
            # 从负载均衡器移除
            await self.load_balancer.remove_service(service_id)
            
            # 从服务注册表移除
            await self.service_registry.unregister(service_id)
            
            # 更新服务状态
            service_info.status = MCPServiceStatus.STOPPED
            
            # 从本地服务列表移除
            del self.services[service_id]
            
            self.logger.info(f"服务 {service_info.name} ({service_id}) 注销成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注销服务失败: {e}")
            self.stats["errors_count"] += 1
            return False
    
    async def send_message(self, message: MCPMessage) -> bool:
        """
        发送消息到目标服务
        
        Args:
            message: MCP消息
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 验证消息
            if not self._validate_message(message):
                return False
            
            # 检查目标服务是否存在
            if message.target_service not in self.services:
                self.logger.error(f"目标服务 {message.target_service} 不存在")
                return False
            
            # 通过消息路由器发送
            success = await self.message_router.route_message(message)
            
            if success:
                self.stats["messages_processed"] += 1
                self.logger.debug(f"消息发送成功: {message.message_id}")
            else:
                self.stats["errors_count"] += 1
                self.logger.error(f"消息发送失败: {message.message_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"发送消息时出错: {e}")
            self.stats["errors_count"] += 1
            return False
    
    async def broadcast_message(self, message: MCPMessage, 
                              capability_filter: Optional[str] = None) -> int:
        """
        广播消息到所有服务或具有特定能力的服务
        
        Args:
            message: MCP消息
            capability_filter: 能力过滤器
            
        Returns:
            int: 成功发送的服务数量
        """
        try:
            target_services = []
            
            for service_id, service_info in self.services.items():
                # 跳过发送者自己
                if service_id == message.source_service:
                    continue
                
                # 应用能力过滤器
                if capability_filter and capability_filter not in service_info.capabilities:
                    continue
                
                target_services.append(service_id)
            
            success_count = 0
            for service_id in target_services:
                message_copy = MCPMessage(
                    source_service=message.source_service,
                    target_service=service_id,
                    message_type=message.message_type,
                    payload=message.payload.copy(),
                    correlation_id=message.correlation_id
                )
                
                if await self.send_message(message_copy):
                    success_count += 1
            
            self.logger.info(f"广播消息到 {success_count}/{len(target_services)} 个服务")
            return success_count
            
        except Exception as e:
            self.logger.error(f"广播消息时出错: {e}")
            return 0
    
    async def get_service_info(self, service_id: str) -> Optional[MCPServiceInfo]:
        """获取服务信息"""
        return self.services.get(service_id)
    
    async def list_services(self, capability_filter: Optional[str] = None) -> List[MCPServiceInfo]:
        """
        列出所有服务
        
        Args:
            capability_filter: 能力过滤器
            
        Returns:
            List[MCPServiceInfo]: 服务信息列表
        """
        services = list(self.services.values())
        
        if capability_filter:
            services = [s for s in services if capability_filter in s.capabilities]
        
        return services
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = None
        if self.stats["uptime_start"]:
            uptime = (datetime.now() - self.stats["uptime_start"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "active_services": len(self.services),
            "is_running": self.is_running
        }
    
    def _validate_service_info(self, service_info: MCPServiceInfo) -> bool:
        """验证服务信息"""
        if not service_info.service_id:
            self.logger.error("服务ID不能为空")
            return False
        
        if not service_info.name:
            self.logger.error("服务名称不能为空")
            return False
        
        if not service_info.endpoint:
            self.logger.error("服务端点不能为空")
            return False
        
        return True
    
    def _validate_message(self, message: MCPMessage) -> bool:
        """验证消息格式"""
        if not message.source_service:
            self.logger.error("消息源服务不能为空")
            return False
        
        if not message.target_service:
            self.logger.error("消息目标服务不能为空")
            return False
        
        if not message.message_type:
            self.logger.error("消息类型不能为空")
            return False
        
        return True
    
    def _setup_message_handlers(self) -> None:
        """设置消息处理器"""
        self.message_handlers = {
            "heartbeat": self._handle_heartbeat,
            "service_discovery": self._handle_service_discovery,
            "health_check": self._handle_health_check
        }
    
    async def _handle_heartbeat(self, message: MCPMessage) -> None:
        """处理心跳消息"""
        service_id = message.source_service
        if service_id in self.services:
            self.services[service_id].last_heartbeat = datetime.now()
            self.logger.debug(f"收到服务 {service_id} 的心跳")
    
    async def _handle_service_discovery(self, message: MCPMessage) -> None:
        """处理服务发现消息"""
        capability_filter = message.payload.get("capability_filter")
        services = await self.list_services(capability_filter)
        
        # 发送服务列表响应
        response = MCPMessage(
            source_service="mcp_coordinator",
            target_service=message.source_service,
            message_type="service_discovery_response",
            payload={"services": [s.__dict__ for s in services]},
            correlation_id=message.correlation_id
        )
        
        await self.send_message(response)
    
    async def _handle_health_check(self, message: MCPMessage) -> None:
        """处理健康检查消息"""
        stats = await self.get_stats()
        
        response = MCPMessage(
            source_service="mcp_coordinator",
            target_service=message.source_service,
            message_type="health_check_response",
            payload={"status": "healthy", "stats": stats},
            correlation_id=message.correlation_id
        )
        
        await self.send_message(response)
    
    async def _background_tasks(self) -> None:
        """后台任务"""
        while self.is_running:
            try:
                # 清理过期的服务
                await self._cleanup_expired_services()
                
                # 更新统计信息
                await self._update_stats()
                
                # 等待下一次执行
                await asyncio.sleep(30)  # 30秒执行一次
                
            except Exception as e:
                self.logger.error(f"后台任务执行出错: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_expired_services(self) -> None:
        """清理过期的服务"""
        current_time = datetime.now()
        expired_services = []
        
        for service_id, service_info in self.services.items():
            if service_info.last_heartbeat:
                time_diff = (current_time - service_info.last_heartbeat).total_seconds()
                if time_diff > 300:  # 5分钟无心跳认为服务过期
                    expired_services.append(service_id)
        
        for service_id in expired_services:
            self.logger.warning(f"服务 {service_id} 心跳超时，自动注销")
            await self.unregister_service(service_id)
    
    async def _update_stats(self) -> None:
        """更新统计信息"""
        # 这里可以添加更多的统计信息更新逻辑
        pass

