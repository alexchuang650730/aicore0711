"""
PowerAutomation Agents MCP Component

智能代理管理组件 - 提供完整的多代理协作和专业化代理服务

核心功能:
- 代理协调和管理
- 多代理通信
- 专业化代理服务
- 代理间协作

组件架构:
- agent_coordinator.py: 代理协调器
- communication/: 代理通信模块
- coordination/: 代理协调模块  
- shared/: 共享代理资源
- specialized/: 专业化代理集合

版本: 4.2.0
作者: PowerAutomation Team
"""

from .agent_coordinator import AgentCoordinator

__version__ = "4.2.0"
__all__ = ["AgentCoordinator"]

