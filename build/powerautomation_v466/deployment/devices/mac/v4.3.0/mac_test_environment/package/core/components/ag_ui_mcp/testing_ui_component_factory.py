#!/usr/bin/env python3
"""
测试UI组件工厂

基于AG-UI组件生成器的测试UI组件工厂，负责根据JSON定义生成具体的UI组件实例。
"""

import json
import logging
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from .ag_ui_protocol_adapter import AGUIComponent, AGUIComponentType
from .ag_ui_component_generator import AGUIComponentGenerator

logger = logging.getLogger(__name__)

class TestingUIComponentType(Enum):
    """测试UI组件类型枚举"""
    TEST_DASHBOARD = "test_dashboard"
    RECORDING_CONTROL_PANEL = "recording_control_panel"
    TEST_RESULTS_VIEWER = "test_results_viewer"
    AI_SUGGESTIONS_PANEL = "ai_suggestions_panel"
    TEST_CONFIG_PANEL = "test_config_panel"
    LIVE_PREVIEW_PANEL = "live_preview_panel"
    TEST_SUITE_MANAGER = "test_suite_manager"

class TestingUITheme(Enum):
    """测试UI主题枚举"""
    CLAUDEDITOR_DARK = "claudeditor_dark"
    CLAUDEDITOR_LIGHT = "claudeditor_light"
    TESTING_FOCUSED = "testing_focused"

@dataclass
class TestingComponentConfig:
    """测试组件配置"""
    component_type: TestingUIComponentType
    theme: TestingUITheme = TestingUITheme.CLAUDEDITOR_DARK
    layout: str = "default"
    features: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    real_time: bool = True
    ai_enabled: bool = True
    custom_props: Dict[str, Any] = field(default_factory=dict)

class TestingUIComponentFactory:
    """测试UI组件工厂"""
    
    def __init__(self):
        self.component_generator = AGUIComponentGenerator()
        self.component_definitions = self._load_component_definitions()
        self.theme_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("测试UI组件工厂初始化完成")
    
    def _load_component_definitions(self) -> Dict[str, Any]:
        """加载组件定义"""
        definitions_path = Path(__file__).parent / "testing_component_definitions.json"
        
        try:
            with open(definitions_path, 'r', encoding='utf-8') as f:
                definitions = json.load(f)
            
            logger.info(f"成功加载 {len(definitions['testing_ui_component_definitions']['components'])} 个组件定义")
            return definitions['testing_ui_component_definitions']
            
        except Exception as e:
            logger.error(f"加载组件定义失败: {e}")
            return {"components": {}, "shared_styles": {}}
    
    async def create_component(
        self,
        component_type: TestingUIComponentType,
        config: TestingComponentConfig,
        data: Dict[str, Any]
    ) -> AGUIComponent:
        """创建测试UI组件"""
        
        # 获取组件定义
        component_def = self.component_definitions["components"].get(component_type.value)
        if not component_def:
            raise ValueError(f"未找到组件类型 {component_type.value} 的定义")
        
        # 合并配置和定义
        merged_config = self._merge_config_with_definition(config, component_def)
        
        # 应用主题
        themed_config = self._apply_theme(merged_config, config.theme)
        
        # 验证数据
        validated_data = self._validate_component_data(data, component_def.get("schema", {}))
        
        # 生成组件
        component = await self.component_generator.generate_component(
            component_type=AGUIComponentType.CUSTOM,
            config=themed_config,
            data=validated_data
        )
        
        # 设置组件特定属性
        component.component_id = f"{component_type.value}_{id(component)}"
        component.component_category = "testing"
        component.real_time_enabled = config.real_time
        component.ai_enabled = config.ai_enabled
        
        logger.info(f"成功创建测试组件: {component_type.value}")
        return component
    
    def _merge_config_with_definition(
        self,
        config: TestingComponentConfig,
        definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并配置和定义"""
        
        merged = {
            "type": definition["type"],
            "category": definition["category"],
            "complexity": definition["complexity"],
            "layout": config.layout,
            "features": config.features,
            "data_sources": config.data_sources,
            "real_time": config.real_time,
            "ai_enabled": config.ai_enabled,
            "events": definition.get("events", {}),
            "styling": definition.get("styling", {}),
            **config.custom_props
        }
        
        return merged
    
    def _apply_theme(
        self,
        config: Dict[str, Any],
        theme: TestingUITheme
    ) -> Dict[str, Any]:
        """应用主题"""
        
        # 获取主题配置
        theme_config = self._get_theme_config(theme)
        
        # 应用主题到样式
        if "styling" in config:
            config["styling"]["theme"] = theme.value
            config["styling"]["theme_variables"] = theme_config
        
        return config
    
    def _get_theme_config(self, theme: TestingUITheme) -> Dict[str, Any]:
        """获取主题配置"""
        
        if theme.value in self.theme_cache:
            return self.theme_cache[theme.value]
        
        themes = self.component_definitions.get("shared_styles", {}).get("themes", {})
        theme_config = themes.get(theme.value, themes.get("claudeditor_dark", {}))
        
        # 缓存主题配置
        self.theme_cache[theme.value] = theme_config
        
        return theme_config
    
    def _validate_component_data(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证组件数据"""
        
        # 简单的数据验证
        # 在实际实现中，可以使用 jsonschema 库进行更严格的验证
        
        validated_data = data.copy()
        
        # 确保必需的数据字段存在
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in validated_data:
                logger.warning(f"缺少必需字段: {field}")
                validated_data[field] = None
        
        return validated_data
    
    async def create_dashboard(
        self,
        config: Optional[TestingComponentConfig] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AGUIComponent:
        """创建测试仪表板"""
        
        if config is None:
            config = TestingComponentConfig(
                component_type=TestingUIComponentType.TEST_DASHBOARD,
                layout="responsive_grid",
                features=["real_time_updates", "interactive_charts", "quick_actions"],
                data_sources=["test_manager", "ui_registry", "results_db"]
            )
        
        if data is None:
            data = {
                "stats": {"total_tests": 0, "success_rate": 0},
                "test_suites": [],
                "recent_results": [],
                "quick_actions": []
            }
        
        return await self.create_component(
            TestingUIComponentType.TEST_DASHBOARD,
            config,
            data
        )
    
    async def create_recording_panel(
        self,
        config: Optional[TestingComponentConfig] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AGUIComponent:
        """创建录制控制面板"""
        
        if config is None:
            config = TestingComponentConfig(
                component_type=TestingUIComponentType.RECORDING_CONTROL_PANEL,
                layout="vertical_stack",
                features=["real_time_recording", "live_preview", "ai_suggestions"],
                data_sources=["recording_engine", "browser_controller"]
            )
        
        if data is None:
            data = {
                "recording_status": {"state": "idle", "duration": 0},
                "recording_options": {"capture_screenshots": True},
                "live_actions": [],
                "browser_info": {"browser": "chrome", "version": "120.0"}
            }
        
        return await self.create_component(
            TestingUIComponentType.RECORDING_CONTROL_PANEL,
            config,
            data
        )
    
    async def create_results_viewer(
        self,
        config: Optional[TestingComponentConfig] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AGUIComponent:
        """创建测试结果查看器"""
        
        if config is None:
            config = TestingComponentConfig(
                component_type=TestingUIComponentType.TEST_RESULTS_VIEWER,
                layout="master_detail",
                features=["result_filtering", "result_comparison", "export_reports"],
                data_sources=["results_db", "media_storage"]
            )
        
        if data is None:
            data = {
                "results": [],
                "charts": {},
                "filters": [],
                "comparison_data": {}
            }
        
        return await self.create_component(
            TestingUIComponentType.TEST_RESULTS_VIEWER,
            config,
            data
        )
    
    async def create_ai_suggestions_panel(
        self,
        config: Optional[TestingComponentConfig] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AGUIComponent:
        """创建AI建议面板"""
        
        if config is None:
            config = TestingComponentConfig(
                component_type=TestingUIComponentType.AI_SUGGESTIONS_PANEL,
                layout="feed_layout",
                features=["real_time_suggestions", "batch_apply", "learning_feedback"],
                data_sources=["claude_ai", "test_analyzer"]
            )
        
        if data is None:
            data = {
                "suggestions": [],
                "suggestion_history": [],
                "user_feedback": {},
                "learning_stats": {}
            }
        
        return await self.create_component(
            TestingUIComponentType.AI_SUGGESTIONS_PANEL,
            config,
            data
        )
    
    async def create_config_panel(
        self,
        config: Optional[TestingComponentConfig] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AGUIComponent:
        """创建测试配置面板"""
        
        if config is None:
            config = TestingComponentConfig(
                component_type=TestingUIComponentType.TEST_CONFIG_PANEL,
                layout="tabbed_form",
                features=["live_validation", "config_templates", "import_export"],
                data_sources=["config_manager", "template_library"]
            )
        
        if data is None:
            data = {
                "current_config": {},
                "config_templates": [],
                "validation_rules": {},
                "environment_configs": {}
            }
        
        return await self.create_component(
            TestingUIComponentType.TEST_CONFIG_PANEL,
            config,
            data
        )
    
    async def create_live_preview_panel(
        self,
        config: Optional[TestingComponentConfig] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> AGUIComponent:
        """创建实时预览面板"""
        
        if config is None:
            config = TestingComponentConfig(
                component_type=TestingUIComponentType.LIVE_PREVIEW_PANEL,
                layout="split_preview",
                features=["real_time_updates", "multi_viewport", "interaction_overlay"],
                data_sources=["browser_engine", "recording_engine"]
            )
        
        if data is None:
            data = {
                "preview_frames": [],
                "interaction_steps": [],
                "performance_data": {},
                "viewport_configs": []
            }
        
        return await self.create_component(
            TestingUIComponentType.LIVE_PREVIEW_PANEL,
            config,
            data
        )
    
    def get_available_components(self) -> List[str]:
        """获取可用的组件类型列表"""
        return list(self.component_definitions["components"].keys())
    
    def get_component_definition(self, component_type: str) -> Optional[Dict[str, Any]]:
        """获取组件定义"""
        return self.component_definitions["components"].get(component_type)
    
    def get_available_themes(self) -> List[str]:
        """获取可用的主题列表"""
        return list(self.component_definitions.get("shared_styles", {}).get("themes", {}).keys())


# 全局工厂实例
_testing_ui_factory = None

def get_testing_ui_factory() -> TestingUIComponentFactory:
    """获取测试UI组件工厂实例"""
    global _testing_ui_factory
    if _testing_ui_factory is None:
        _testing_ui_factory = TestingUIComponentFactory()
    return _testing_ui_factory


# 导出
__all__ = [
    'TestingUIComponentFactory',
    'TestingUIComponentType',
    'TestingUITheme',
    'TestingComponentConfig',
    'get_testing_ui_factory'
]

