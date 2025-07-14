#!/usr/bin/env python3
"""
组件生成器

基于模板生成AG-UI组件，完全集成到ClaudEditor 4.1的AG-UI架构中
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_generator import BaseGenerator, GenerationConfig, GenerationResult
from .template_engine import TemplateEngine

# 导入AG-UI相关模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.components.ag_ui_mcp.ag_ui_component_generator import AGUIComponentGenerator
from core.components.ag_ui_mcp.ag_ui_protocol_adapter import AGUIProtocolAdapter

import logging
logger = logging.getLogger(__name__)

@dataclass
class AGUIComponentConfig:
    """AG-UI组件配置"""
    component_type: str
    props: Dict[str, Any]
    children: List[Any]
    events: Dict[str, str]
    styles: Dict[str, Any]
    theme: Optional[str] = None
    accessibility: Optional[Dict[str, Any]] = None

class ComponentGenerator(BaseGenerator):
    """组件生成器 - 集成AG-UI动态生成引擎"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 初始化模板引擎
        self.template_engine = TemplateEngine()
        
        # 初始化AG-UI组件生成器
        self.agui_generator = AGUIComponentGenerator()
        self.agui_adapter = AGUIProtocolAdapter()
        
        # 注册常用的部分模板
        self._register_common_partials()
        
        # 注册自定义辅助函数
        self._register_custom_helpers()
    
    def _register_common_partials(self):
        """注册常用的部分模板"""
        # 图标部分模板
        self.template_engine.register_partial('icon', '''
        {
            "component_type": "icon",
            "props": {
                "name": "{{name}}",
                "size": "{{size}}",
                "className": "{{className}}"
            }
        }
        ''')
        
        # 加载器部分模板
        self.template_engine.register_partial('spinner', '''
        {
            "component_type": "div",
            "props": {
                "className": "spinner spinner-{{size}}"
            },
            "children": [
                {
                    "component_type": "div",
                    "props": {
                        "className": "spinner-circle"
                    }
                }
            ]
        }
        ''')
    
    def _register_custom_helpers(self):
        """注册自定义辅助函数"""
        # 尺寸映射辅助函数
        def size_to_pixels(size: str) -> str:
            size_map = {
                'xs': '12',
                'sm': '14', 
                'md': '16',
                'lg': '18',
                'xl': '20'
            }
            return size_map.get(size, '16')
        
        self.template_engine.register_helper('sizeToPixels', size_to_pixels)
        
        # 类名组合辅助函数
        def combine_classes(*classes) -> str:
            return ' '.join(filter(None, classes))
        
        self.template_engine.register_helper('combineClasses', combine_classes)
    
    async def generate(self, config: GenerationConfig) -> GenerationResult:
        """生成AG-UI组件"""
        try:
            # 验证配置
            errors = self.validate_config(config)
            if errors:
                return GenerationResult(
                    success=False,
                    output_files=[],
                    errors=errors,
                    warnings=[],
                    metadata={}
                )
            
            # 查找模板
            template_path = self._find_template(config.template_name, "components")
            if not template_path:
                return GenerationResult(
                    success=False,
                    output_files=[],
                    errors=[f"Template '{config.template_name}' not found"],
                    warnings=[],
                    metadata={}
                )
            
            # 加载模板
            template = self._load_template(template_path)
            
            # 验证模板
            template_errors = self._validate_template(template)
            if template_errors:
                return GenerationResult(
                    success=False,
                    output_files=[],
                    errors=template_errors,
                    warnings=[],
                    metadata={}
                )
            
            # 渲染模板
            rendered_template = self.template_engine.render(template['template'], config.context)
            
            # 转换为AG-UI组件配置
            agui_config = self._convert_to_agui_config(rendered_template, template, config)
            
            # 生成AG-UI组件
            agui_component = await self.agui_generator.generate_component(agui_config)
            
            # 生成样式文件
            style_files = await self._generate_styles(template, config)
            
            # 生成组件文件
            component_files = await self._generate_component_files(agui_component, config)
            
            # 生成类型定义文件
            type_files = await self._generate_type_definitions(template, config)
            
            output_files = component_files + style_files + type_files
            
            return GenerationResult(
                success=True,
                output_files=output_files,
                errors=[],
                warnings=[],
                metadata={
                    'template_name': config.template_name,
                    'component_type': agui_config.component_type,
                    'theme': config.theme,
                    'dependencies': self._resolve_dependencies(template)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate component: {e}")
            return GenerationResult(
                success=False,
                output_files=[],
                errors=[str(e)],
                warnings=[],
                metadata={}
            )
    
    def _convert_to_agui_config(
        self, 
        rendered_template: Dict[str, Any], 
        original_template: Dict[str, Any],
        config: GenerationConfig
    ) -> AGUIComponentConfig:
        """转换为AG-UI组件配置"""
        
        # 基础组件配置
        agui_config = AGUIComponentConfig(
            component_type=rendered_template.get('component_type', 'div'),
            props=rendered_template.get('props', {}),
            children=rendered_template.get('children', []),
            events=rendered_template.get('events', {}),
            styles=original_template.get('styles', {}),
            theme=config.theme,
            accessibility=original_template.get('accessibility', {})
        )
        
        return agui_config
    
    async def _generate_styles(
        self, 
        template: Dict[str, Any], 
        config: GenerationConfig
    ) -> List[str]:
        """生成样式文件"""
        style_files = []
        
        if 'styles' not in template:
            return style_files
        
        styles = template['styles']
        
        # 生成CSS文件
        css_content = self._generate_css_from_styles(styles, config.context)
        
        # 输出路径
        css_file = f"{config.output_path}.css"
        
        # 写入CSS文件
        self._write_output_file(css_content, css_file, config.minify)
        style_files.append(css_file)
        
        # 如果需要，生成SCSS文件
        if self.config.get('generate_scss', False):
            scss_content = self._generate_scss_from_styles(styles, config.context)
            scss_file = f"{config.output_path}.scss"
            self._write_output_file(scss_content, scss_file)
            style_files.append(scss_file)
        
        return style_files
    
    def _generate_css_from_styles(self, styles: Dict[str, Any], context: Dict[str, Any]) -> str:
        """从样式定义生成CSS"""
        css_lines = []
        
        # 处理基础样式
        if 'base' in styles:
            css_lines.extend(self._convert_styles_to_css(styles['base']))
        
        # 处理变体样式
        if 'variants' in styles:
            for variant_name, variant_styles in styles['variants'].items():
                css_lines.extend(self._convert_styles_to_css(variant_styles))
        
        # 处理尺寸样式
        if 'sizes' in styles:
            for size_name, size_styles in styles['sizes'].items():
                css_lines.extend(self._convert_styles_to_css(size_styles))
        
        # 处理修饰符样式
        if 'modifiers' in styles:
            for modifier_name, modifier_styles in styles['modifiers'].items():
                css_lines.extend(self._convert_styles_to_css(modifier_styles))
        
        # 处理状态样式
        if 'states' in styles:
            for state_name, state_styles in styles['states'].items():
                css_lines.extend(self._convert_styles_to_css(state_styles))
        
        return '\n'.join(css_lines)
    
    def _convert_styles_to_css(self, styles: Dict[str, Any]) -> List[str]:
        """转换样式对象为CSS规则"""
        css_lines = []
        
        for selector, properties in styles.items():
            css_lines.append(f"{selector} {{")
            
            for prop, value in properties.items():
                css_lines.append(f"  {prop}: {value};")
            
            css_lines.append("}")
            css_lines.append("")  # 空行分隔
        
        return css_lines
    
    async def _generate_component_files(
        self, 
        agui_component: Any, 
        config: GenerationConfig
    ) -> List[str]:
        """生成组件文件"""
        component_files = []
        
        # 生成React组件文件
        if self.config.get('generate_react', True):
            react_content = await self._generate_react_component(agui_component, config)
            react_file = f"{config.output_path}.tsx"
            self._write_output_file(react_content, react_file, config.minify)
            component_files.append(react_file)
        
        # 生成Vue组件文件
        if self.config.get('generate_vue', False):
            vue_content = await self._generate_vue_component(agui_component, config)
            vue_file = f"{config.output_path}.vue"
            self._write_output_file(vue_content, vue_file, config.minify)
            component_files.append(vue_file)
        
        # 生成AG-UI组件定义文件
        agui_content = await self._generate_agui_definition(agui_component, config)
        agui_file = f"{config.output_path}.agui.json"
        self._write_output_file(agui_content, agui_file)
        component_files.append(agui_file)
        
        return component_files
    
    async def _generate_react_component(
        self, 
        agui_component: Any, 
        config: GenerationConfig
    ) -> str:
        """生成React组件代码"""
        # 这里应该调用AG-UI的React代码生成器
        # 暂时返回一个简单的模板
        component_name = config.context.get('name', 'Component')
        
        return f'''import React from 'react';
import {{ AGUIComponent }} from '@claudeditor/agui-react';
import './{component_name}.css';

interface {component_name}Props {{
  // Props will be generated based on template schema
}}

export const {component_name}: React.FC<{component_name}Props> = (props) => {{
  return (
    <AGUIComponent
      definition={{require('./{component_name}.agui.json')}}
      props={{props}}
    />
  );
}};

export default {component_name};
'''
    
    async def _generate_vue_component(
        self, 
        agui_component: Any, 
        config: GenerationConfig
    ) -> str:
        """生成Vue组件代码"""
        component_name = config.context.get('name', 'Component')
        
        return f'''<template>
  <AGUIComponent
    :definition="definition"
    :props="$props"
  />
</template>

<script setup lang="ts">
import {{ AGUIComponent }} from '@claudeditor/agui-vue';
import definition from './{component_name}.agui.json';

// Props will be generated based on template schema
</script>

<style scoped>
@import './{component_name}.css';
</style>
'''
    
    async def _generate_agui_definition(
        self, 
        agui_component: Any, 
        config: GenerationConfig
    ) -> str:
        """生成AG-UI组件定义"""
        definition = {
            "version": "1.0.0",
            "type": "component",
            "name": config.context.get('name', 'Component'),
            "component": agui_component,
            "metadata": {
                "generated_by": "ClaudEditor UI Generator",
                "template": config.template_name,
                "theme": config.theme,
                "timestamp": "2025-01-09T10:30:00Z"
            }
        }
        
        return json.dumps(definition, indent=2, ensure_ascii=False)
    
    async def _generate_type_definitions(
        self, 
        template: Dict[str, Any], 
        config: GenerationConfig
    ) -> List[str]:
        """生成TypeScript类型定义文件"""
        type_files = []
        
        if not self.config.get('generate_types', True):
            return type_files
        
        # 从模板schema生成TypeScript接口
        if 'schema' in template:
            ts_content = self._generate_typescript_interface(template['schema'], config)
            ts_file = f"{config.output_path}.types.ts"
            self._write_output_file(ts_content, ts_file)
            type_files.append(ts_file)
        
        return type_files
    
    def _generate_typescript_interface(
        self, 
        schema: Dict[str, Any], 
        config: GenerationConfig
    ) -> str:
        """从JSON Schema生成TypeScript接口"""
        component_name = config.context.get('name', 'Component')
        
        # 简单的类型映射
        type_mapping = {
            'string': 'string',
            'number': 'number',
            'integer': 'number',
            'boolean': 'boolean',
            'array': 'any[]',
            'object': 'any'
        }
        
        interface_lines = [f"export interface {component_name}Props {{"]
        
        if 'properties' in schema:
            for prop_name, prop_def in schema['properties'].items():
                prop_type = type_mapping.get(prop_def.get('type', 'any'), 'any')
                
                # 处理枚举类型
                if 'enum' in prop_def:
                    enum_values = [f"'{val}'" for val in prop_def['enum']]
                    prop_type = ' | '.join(enum_values)
                
                # 处理可选属性
                required = schema.get('required', [])
                optional = '' if prop_name in required else '?'
                
                # 添加注释
                description = prop_def.get('description', '')
                if description:
                    interface_lines.append(f"  /** {description} */")
                
                interface_lines.append(f"  {prop_name}{optional}: {prop_type};")
        
        interface_lines.append("}")
        
        return '\n'.join(interface_lines)
    
    def get_supported_templates(self) -> List[str]:
        """获取支持的组件模板列表"""
        templates = []
        
        for template_dir in self.template_dirs:
            components_dir = Path(template_dir) / "components"
            if components_dir.exists():
                for category_dir in components_dir.iterdir():
                    if category_dir.is_dir():
                        for template_file in category_dir.glob("*.json"):
                            templates.append(f"{category_dir.name}/{template_file.stem}")
        
        return templates
    
    async def generate_from_template_name(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: str,
        theme: Optional[str] = None
    ) -> GenerationResult:
        """便捷方法：从模板名称生成组件"""
        config = GenerationConfig(
            template_name=template_name,
            output_path=output_path,
            context=context,
            theme=theme
        )
        
        return await self.generate(config)

