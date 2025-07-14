"""
PowerAutomation 4.1 - SmartUI MCP组件

SmartUI MCP是PowerAutomation 4.1的智能UI生成和管理组件，提供：
- 模板驱动的UI组件生成
- AG-UI深度集成
- 多框架支持 (React, Vue, HTML)
- 智能主题系统
- 实时预览和热重载
- AI辅助UI设计

主要模块：
- templates: UI组件模板系统
- generators: UI生成器引擎
- services: SmartUI MCP服务
- cli: 命令行接口
- config: 配置管理
"""

__version__ = "4.1.0"
__author__ = "PowerAutomation 4.1 Team"

from .services.smartui_service import SmartUIService
from .generators.ui_generator import UIGenerator
from .cli.smartui_cli import SmartUICLI

__all__ = [
    "SmartUIService",
    "UIGenerator", 
    "SmartUICLI"
]

