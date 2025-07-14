"""
ClaudEditor 4.1 AG-UI UI生成器包

提供完整的UI组件生成能力，包括：
- 组件生成器
- 布局生成器  
- 页面生成器
- 主题生成器
- 模板引擎
"""

from .base_generator import BaseGenerator
from .component_generator import ComponentGenerator
from .layout_generator import LayoutGenerator
from .page_generator import PageGenerator
from .theme_generator import ThemeGenerator
from .template_engine import TemplateEngine
from .ui_generator import UIGenerator

__version__ = "1.0.0"
__author__ = "ClaudEditor Team"

__all__ = [
    "BaseGenerator",
    "ComponentGenerator", 
    "LayoutGenerator",
    "PageGenerator",
    "ThemeGenerator",
    "TemplateEngine",
    "UIGenerator"
]

# 便捷函数
def get_ui_generator(**kwargs) -> UIGenerator:
    """获取UI生成器实例"""
    return UIGenerator(**kwargs)

def get_component_generator(**kwargs) -> ComponentGenerator:
    """获取组件生成器实例"""
    return ComponentGenerator(**kwargs)

def get_template_engine(**kwargs) -> TemplateEngine:
    """获取模板引擎实例"""
    return TemplateEngine(**kwargs)

