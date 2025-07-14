"""
PowerAutomation 4.0 MCP协调器模块

这个模块是PowerAutomation 4.0的核心，负责管理所有MCP服务的注册、发现、
路由和协调。所有MCP之间的通信都必须通过这个协调器进行。

主要组件：
- MCPCoordinator: 中央协调器
- ServiceRegistry: 服务注册表
- MessageRouter: 消息路由器
- HealthMonitor: 健康监控
- LoadBalancer: 负载均衡器
"""

from .coordinator import MCPCoordinator
from .service_registry import ServiceRegistry
from .message_router import MessageRouter
from .health_monitor import HealthMonitor
from .load_balancer import LoadBalancer

__version__ = "4.0.0"
__author__ = "PowerAutomation Team"

__all__ = [
    "MCPCoordinator",
    "ServiceRegistry", 
    "MessageRouter",
    "HealthMonitor",
    "LoadBalancer"
]


# 新增集成层导入
from .integration_layer import *
