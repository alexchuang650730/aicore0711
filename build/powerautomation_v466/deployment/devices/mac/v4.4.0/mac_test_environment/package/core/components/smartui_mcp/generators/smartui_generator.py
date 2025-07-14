#!/usr/bin/env python3
"""
SmartUI MCP 专用生成器

集成PowerAutomation 4.1特性的智能UI生成器
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import logging

from .base_generator import BaseGenerator, GenerationConfig, GenerationResult
from .ui_generator import UIGenerator, UIGenerationRequest
from ..services.smartui_service import SmartUIService

logger = logging.getLogger(__name__)

@dataclass
class SmartUIGenerationRequest:
    """SmartUI生成请求"""
    type: str  # component, layout, page, theme, suite
    template: str
    context: Dict[str, Any]
    output_dir: str
    theme: Optional[str] = None
    framework: str = "react"  # react, vue, html
    agui_integration: bool = True
    ai_optimization: bool = True
    options: Optional[Dict[str, Any]] = None

class SmartUIGenerator(UIGenerator):
    """SmartUI MCP专用生成器"""
    
    def __init__(
        self,
        template_dirs: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        theme_dirs: Optional[List[str]] = None,
        smartui_service: Optional[SmartUIService] = None
    ):
        # 使用SmartUI MCP的路径
        default_template_dirs = [
            "core/components/smartui_mcp/templates",
            "core/components/smartui_mcp/templates/components",
            "core/components/smartui_mcp/templates/layouts",
            "core/components/smartui_mcp/templates/pages"
        ]
        
        default_output_dir = "core/components/smartui_mcp/generated"
        default_theme_dirs = ["core/components/smartui_mcp/templates/themes"]
        
        super().__init__(
            template_dirs=template_dirs or default_template_dirs,
            output_dir=output_dir or default_output_dir,
            theme_dirs=theme_dirs or default_theme_dirs
        )
        
        self.smartui_service = smartui_service
        
        # SmartUI特有配置
        self.smartui_config = self._load_smartui_config()
        
        # 统计信息扩展
        self.stats.update({
            "agui_components_generated": 0,
            "ai_optimizations": 0,
            "theme_variations": 0,
            "framework_outputs": {
                "react": 0,
                "vue": 0,
                "html": 0
            }
        })
    
    def _load_smartui_config(self) -> Dict[str, Any]:
        """加载SmartUI配置"""
        config_path = Path("core/components/smartui_mcp/config/smartui_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "agui_integration": True,
            "ai_optimization": True,
            "default_framework": "react",
            "auto_theme_generation": True,
            "performance_optimization": True,
            "accessibility_enhancement": True
        }
    
    async def generate_smart(self, request: SmartUIGenerationRequest) -> GenerationResult:
        """智能生成UI组件"""
        try:
            # 1. AI优化请求
            if request.ai_optimization and self.smartui_service:
                request = await self._ai_optimize_request(request)
            
            # 2. 转换为标准请求
            standard_request = self._convert_to_standard_request(request)
            
            # 3. 生成组件
            result = await self.generate(standard_request)
            
            # 4. AG-UI集成
            if request.agui_integration and result.success:
                result = await self._integrate_agui(result, request)
            
            # 5. 多框架输出
            if result.success:
                result = await self._generate_multi_framework(result, request)
            
            # 6. 更新统计
            self._update_smartui_stats(request, result)
            
            return result
            
        except Exception as e:
            logger.error(f"SmartUI generation failed: {e}")
            return GenerationResult(
                success=False,
                output_files=[],
                errors=[str(e)],
                warnings=[],
                metadata={"smartui_error": True}
            )
    
    async def _ai_optimize_request(self, request: SmartUIGenerationRequest) -> SmartUIGenerationRequest:
        """AI优化生成请求"""
        if not self.smartui_service:
            return request
        
        try:
            # 使用AI服务优化请求
            optimized_context = await self.smartui_service.optimize_component_context(
                request.context,
                request.template,
                request.framework
            )
            
            request.context.update(optimized_context)
            self.stats["ai_optimizations"] += 1
            
        except Exception as e:
            logger.warning(f"AI optimization failed: {e}")
        
        return request
    
    def _convert_to_standard_request(self, request: SmartUIGenerationRequest) -> UIGenerationRequest:
        """转换为标准UI生成请求"""
        return UIGenerationRequest(
            type=request.type,
            template=request.template,
            context=request.context,
            output_dir=request.output_dir,
            theme=request.theme,
            options=request.options
        )
    
    async def _integrate_agui(self, result: GenerationResult, request: SmartUIGenerationRequest) -> GenerationResult:
        """集成AG-UI"""
        try:
            # 生成AG-UI组件定义
            agui_definition = await self._generate_agui_definition(result, request)
            
            # 保存AG-UI定义文件
            agui_file = f"{request.output_dir}/{request.context.get('name', 'Component')}.agui.json"
            
            with open(agui_file, 'w', encoding='utf-8') as f:
                json.dump(agui_definition, f, indent=2, ensure_ascii=False)
            
            result.output_files.append(agui_file)
            result.metadata["agui_integrated"] = True
            self.stats["agui_components_generated"] += 1
            
        except Exception as e:
            logger.warning(f"AG-UI integration failed: {e}")
            result.warnings.append(f"AG-UI integration failed: {e}")
        
        return result
    
    async def _generate_agui_definition(self, result: GenerationResult, request: SmartUIGenerationRequest) -> Dict[str, Any]:
        """生成AG-UI组件定义"""
        return {
            "meta": {
                "name": request.context.get("name", "Component"),
                "version": "1.0.0",
                "framework": request.framework,
                "generated_by": "SmartUI MCP",
                "created": "2025-07-09"
            },
            "component": {
                "type": request.template,
                "props": self._extract_props_from_context(request.context),
                "events": self._extract_events_from_context(request.context),
                "styles": self._extract_styles_from_context(request.context)
            },
            "agui_protocol": {
                "version": "4.1.0",
                "compatible": True,
                "features": ["reactive", "themeable", "accessible"]
            }
        }
    
    def _extract_props_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文提取属性"""
        props = {}
        
        # 基础属性
        for key in ["variant", "size", "color", "disabled", "loading"]:
            if key in context:
                props[key] = context[key]
        
        # 文本属性
        for key in ["text", "label", "placeholder", "helper"]:
            if key in context:
                props[key] = context[key]
        
        # 布尔属性
        for key in ["required", "clearable", "block", "rounded"]:
            if key in context:
                props[key] = context[key]
        
        return props
    
    def _extract_events_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文提取事件"""
        events = {}
        
        # 常见事件
        for key in ["onClick", "onChange", "onFocus", "onBlur", "onSubmit"]:
            if key in context:
                events[key] = context[key]
        
        return events
    
    def _extract_styles_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """从上下文提取样式"""
        styles = {}
        
        # 样式属性
        for key in ["className", "style", "width", "height"]:
            if key in context:
                styles[key] = context[key]
        
        return styles
    
    async def _generate_multi_framework(self, result: GenerationResult, request: SmartUIGenerationRequest) -> GenerationResult:
        """生成多框架输出"""
        if request.framework == "react":
            self.stats["framework_outputs"]["react"] += 1
        elif request.framework == "vue":
            # 生成Vue版本
            await self._generate_vue_version(result, request)
            self.stats["framework_outputs"]["vue"] += 1
        elif request.framework == "html":
            # 生成HTML版本
            await self._generate_html_version(result, request)
            self.stats["framework_outputs"]["html"] += 1
        
        return result
    
    async def _generate_vue_version(self, result: GenerationResult, request: SmartUIGenerationRequest):
        """生成Vue版本"""
        # Vue组件生成逻辑
        pass
    
    async def _generate_html_version(self, result: GenerationResult, request: SmartUIGenerationRequest):
        """生成HTML版本"""
        # HTML组件生成逻辑
        pass
    
    def _update_smartui_stats(self, request: SmartUIGenerationRequest, result: GenerationResult):
        """更新SmartUI统计信息"""
        if result.success:
            self.stats["total_generated"] += 1
            
            if request.type == "component":
                self.stats["components_generated"] += 1
            elif request.type == "layout":
                self.stats["layouts_generated"] += 1
            elif request.type == "page":
                self.stats["pages_generated"] += 1
        else:
            self.stats["errors"] += 1
    
    async def generate_component_suite(self, suite_name: str, components: List[SmartUIGenerationRequest]) -> List[GenerationResult]:
        """生成组件套件"""
        results = []
        
        for component_request in components:
            # 设置套件输出目录
            component_request.output_dir = f"{component_request.output_dir}/{suite_name}"
            
            result = await self.generate_smart(component_request)
            results.append(result)
        
        return results
    
    async def generate_theme_variations(self, base_request: SmartUIGenerationRequest, themes: List[str]) -> List[GenerationResult]:
        """生成主题变体"""
        results = []
        
        for theme in themes:
            theme_request = SmartUIGenerationRequest(
                type=base_request.type,
                template=base_request.template,
                context=base_request.context.copy(),
                output_dir=f"{base_request.output_dir}/themes/{theme}",
                theme=theme,
                framework=base_request.framework,
                agui_integration=base_request.agui_integration,
                ai_optimization=base_request.ai_optimization,
                options=base_request.options
            )
            
            result = await self.generate_smart(theme_request)
            results.append(result)
            
            if result.success:
                self.stats["theme_variations"] += 1
        
        return results
    
    def get_smartui_stats(self) -> Dict[str, Any]:
        """获取SmartUI统计信息"""
        stats = self.get_stats()
        stats.update({
            "smartui_version": "4.1.0",
            "agui_integration_rate": (
                self.stats["agui_components_generated"] / max(self.stats["total_generated"], 1) * 100
            ),
            "ai_optimization_rate": (
                self.stats["ai_optimizations"] / max(self.stats["total_generated"], 1) * 100
            )
        })
        return stats

# 工厂函数
def get_smartui_generator(smartui_service: Optional[SmartUIService] = None) -> SmartUIGenerator:
    """获取SmartUI生成器实例"""
    return SmartUIGenerator(smartui_service=smartui_service)

