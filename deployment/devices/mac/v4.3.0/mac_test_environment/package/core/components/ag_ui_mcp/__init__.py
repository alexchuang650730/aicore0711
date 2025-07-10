"""
PowerAutomation 4.0 AG-UI MCP服务

基于AG-UI协议的智能体交互标准化服务，提供生成式UI支持和统一的交互接口。

AG-UI (Agent-Generated User Interface) 是一个标准化的协议，用于定义智能体与用户界面之间的交互。
本模块实现了AG-UI协议的完整支持，包括：

1. 协议解析和验证
2. 智能体交互标准化
3. 生成式UI组件
4. 动态界面渲染
5. 事件处理和状态管理

主要组件：
- AGUIProtocolAdapter: AG-UI协议适配器
- AGUIInteractionManager: 智能体交互管理器
- AGUIComponentGenerator: UI组件生成器
- AGUIEventHandler: 事件处理器
- AGUIStateManager: 状态管理器
"""

from .ag_ui_protocol_adapter import AGUIProtocolAdapter
from .ag_ui_interaction_manager import AGUIInteractionManager
from .ag_ui_component_generator import AGUIComponentGenerator
from .ag_ui_event_handler import AGUIEventHandler
from .ag_ui_state_manager import AGUIStateManager

__version__ = "4.0.0"
__author__ = "PowerAutomation Team"

__all__ = [
    "AGUIProtocolAdapter",
    "AGUIInteractionManager", 
    "AGUIComponentGenerator",
    "AGUIEventHandler",
    "AGUIStateManager"
]

