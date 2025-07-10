"""
Local Adapter MCP - 端云一键部署本地适配器
基于PowerAutomation_local v3.1.1核心功能

Author: Manus AI
Version: 1.0.0
Date: 2025-07-07
"""

from .local_adapter_engine import LocalAdapterEngine
from .edge_cloud_coordinator import EdgeCloudCoordinator
from .local_resource_manager import LocalResourceManager
from .deployment_bridge import DeploymentBridge
from .config_manager import LocalAdapterConfigManager
from .security_manager import LocalAdapterSecurityManager

__version__ = "1.0.0"
__author__ = "Manus AI"

__all__ = [
    "LocalAdapterEngine",
    "EdgeCloudCoordinator", 
    "LocalResourceManager",
    "DeploymentBridge",
    "LocalAdapterConfigManager",
    "LocalAdapterSecurityManager"
]

# 模块级配置
DEFAULT_CONFIG = {
    "mcp_server": {
        "host": "0.0.0.0",
        "port": 5000,
        "websocket_port": 5001
    },
    "edge_cloud": {
        "coordination_mode": "intelligent",  # intelligent, local_first, cloud_first
        "failover_enabled": True,
        "load_balancing": True,
        "sync_interval": 30
    },
    "local_resources": {
        "max_cpu_usage": 80,
        "max_memory_usage": 80,
        "storage_path": "./local_storage",
        "temp_path": "./temp"
    },
    "deployment": {
        "auto_switch": True,
        "rollback_enabled": True,
        "health_check_interval": 10
    },
    "security": {
        "role_system_enabled": True,
        "api_key_required": True,
        "audit_logging": True
    }
}

