"""
PowerAutomation 4.0 Stagewise MCP服务

基于Stagewise的可视化编程MCP服务，提供：
- 浏览器元素智能识别
- 可视化代码生成
- 所见即所得编程体验
- AI辅助代码优化

集成Stagewise的核心能力：
- 直接在浏览器中选择元素
- AI自动生成对应代码
- 实时预览和调试
- 智能代码建议
"""

__version__ = "4.0.0"
__author__ = "PowerAutomation Team"

from .stagewise_service import StagewiseService
from .visual_programming_engine import VisualProgrammingEngine
from .element_inspector import ElementInspector
from .code_generator import CodeGenerator

__all__ = [
    "StagewiseService",
    "VisualProgrammingEngine", 
    "ElementInspector",
    "CodeGenerator"
]

