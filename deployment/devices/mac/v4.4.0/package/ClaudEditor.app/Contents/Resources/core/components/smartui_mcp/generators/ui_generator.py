#!/usr/bin/env python3
"""
统一UI生成器

整合所有UI生成功能，提供统一的接口和命令行工具
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import click
import logging

from .base_generator import GenerationConfig, GenerationResult
from .component_generator import ComponentGenerator
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)

@dataclass
class UIGenerationRequest:
    """UI生成请求"""
    type: str  # component, layout, page, theme
    template: str
    context: Dict[str, Any]
    output_dir: str
    theme: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class UIGenerator:
    """统一UI生成器"""
    
    def __init__(
        self,
        template_dirs: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        theme_dirs: Optional[List[str]] = None
    ):
        self.template_dirs = template_dirs or ["ui/templates"]
        self.output_dir = output_dir or "ui/components/generated"
        self.theme_dirs = theme_dirs or ["ui/themes"]
        
        # 初始化各种生成器
        self.component_generator = ComponentGenerator(
            template_dirs=self.template_dirs,
            output_dir=self.output_dir,
            theme_dirs=self.theme_dirs
        )
        
        # 配置
        self.config = self._load_config()
        
        # 统计信息
        self.stats = {
            "total_generated": 0,
            "components_generated": 0,
            "layouts_generated": 0,
            "pages_generated": 0,
            "errors": 0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载UI生成器配置"""
        config_path = Path("ui/config/ui_generator.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "default_theme": "default",
            "generate_react": True,
            "generate_vue": False,
            "generate_types": True,
            "generate_scss": False,
            "minify": False,
            "source_maps": False
        }
    
    async def generate(self, request: UIGenerationRequest) -> GenerationResult:
        """生成UI组件/布局/页面"""
        try:
            if request.type == "component":
                return await self._generate_component(request)
            elif request.type == "layout":
                return await self._generate_layout(request)
            elif request.type == "page":
                return await self._generate_page(request)
            elif request.type == "theme":
                return await self._generate_theme(request)
            else:
                return GenerationResult(
                    success=False,
                    output_files=[],
                    errors=[f"Unsupported generation type: {request.type}"],
                    warnings=[],
                    metadata={}
                )
        except Exception as e:
            logger.error(f"Failed to generate {request.type}: {e}")
            self.stats["errors"] += 1
            return GenerationResult(
                success=False,
                output_files=[],
                errors=[str(e)],
                warnings=[],
                metadata={}
            )
    
    async def _generate_component(self, request: UIGenerationRequest) -> GenerationResult:
        """生成组件"""
        config = GenerationConfig(
            template_name=request.template,
            output_path=f"{request.output_dir}/{request.context.get('name', 'Component')}",
            context=request.context,
            theme=request.theme or self.config.get("default_theme"),
            minify=self.config.get("minify", False)
        )
        
        result = await self.component_generator.generate(config)
        
        if result.success:
            self.stats["components_generated"] += 1
            self.stats["total_generated"] += 1
        
        return result
    
    async def _generate_layout(self, request: UIGenerationRequest) -> GenerationResult:
        """生成布局"""
        # 布局生成逻辑
        # 暂时返回一个占位结果
        return GenerationResult(
            success=True,
            output_files=[],
            errors=[],
            warnings=["Layout generation not implemented yet"],
            metadata={"type": "layout"}
        )
    
    async def _generate_page(self, request: UIGenerationRequest) -> GenerationResult:
        """生成页面"""
        # 页面生成逻辑
        # 暂时返回一个占位结果
        return GenerationResult(
            success=True,
            output_files=[],
            errors=[],
            warnings=["Page generation not implemented yet"],
            metadata={"type": "page"}
        )
    
    async def _generate_theme(self, request: UIGenerationRequest) -> GenerationResult:
        """生成主题"""
        # 主题生成逻辑
        # 暂时返回一个占位结果
        return GenerationResult(
            success=True,
            output_files=[],
            errors=[],
            warnings=["Theme generation not implemented yet"],
            metadata={"type": "theme"}
        )
    
    async def generate_multiple(self, requests: List[UIGenerationRequest]) -> List[GenerationResult]:
        """批量生成"""
        results = []
        
        for request in requests:
            result = await self.generate(request)
            results.append(result)
        
        return results
    
    def get_available_templates(self, type: str = None) -> Dict[str, List[str]]:
        """获取可用的模板列表"""
        templates = {}
        
        # 组件模板
        if not type or type == "component":
            templates["components"] = self.component_generator.get_supported_templates()
        
        # 其他类型的模板可以在这里添加
        
        return templates
    
    def get_template_info(self, template_name: str, category: str = "components") -> Optional[Dict[str, Any]]:
        """获取模板信息"""
        try:
            template_path = None
            
            for template_dir in self.template_dirs:
                possible_path = Path(template_dir) / category / f"{template_name}.json"
                if possible_path.exists():
                    template_path = possible_path
                    break
            
            if not template_path:
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            return {
                "meta": template.get("meta", {}),
                "schema": template.get("schema", {}),
                "examples": template.get("examples", []),
                "dependencies": template.get("dependencies", {})
            }
        
        except Exception as e:
            logger.error(f"Failed to get template info for {template_name}: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0

# CLI接口
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """ClaudEditor 4.1 AG-UI UI生成器"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

@cli.command()
@click.argument('template_name')
@click.argument('component_name')
@click.option('--output', '-o', default='ui/components/generated', help='Output directory')
@click.option('--theme', '-t', help='Theme to use')
@click.option('--context', '-c', help='Context JSON string or file path')
@click.pass_context
async def component(ctx, template_name, component_name, output, theme, context):
    """生成组件"""
    generator = UIGenerator()
    
    # 解析上下文
    context_data = {"name": component_name}
    if context:
        if context.startswith('{'):
            # JSON字符串
            context_data.update(json.loads(context))
        else:
            # 文件路径
            with open(context, 'r', encoding='utf-8') as f:
                context_data.update(json.load(f))
    
    request = UIGenerationRequest(
        type="component",
        template=template_name,
        context=context_data,
        output_dir=output,
        theme=theme
    )
    
    result = await generator.generate(request)
    
    if result.success:
        click.echo(f"✅ Component '{component_name}' generated successfully!")
        click.echo(f"📁 Output files: {', '.join(result.output_files)}")
    else:
        click.echo(f"❌ Failed to generate component '{component_name}'")
        for error in result.errors:
            click.echo(f"   Error: {error}")

@cli.command()
@click.option('--type', '-t', type=click.Choice(['component', 'layout', 'page', 'theme']), help='Template type filter')
def list_templates(type):
    """列出可用的模板"""
    generator = UIGenerator()
    templates = generator.get_available_templates(type)
    
    for category, template_list in templates.items():
        click.echo(f"\n📂 {category.title()}:")
        for template in template_list:
            click.echo(f"   • {template}")

@cli.command()
@click.argument('template_name')
@click.option('--category', '-c', default='components', help='Template category')
def template_info(template_name, category):
    """显示模板信息"""
    generator = UIGenerator()
    info = generator.get_template_info(template_name, category)
    
    if not info:
        click.echo(f"❌ Template '{template_name}' not found in category '{category}'")
        return
    
    click.echo(f"📋 Template: {template_name}")
    click.echo(f"📝 Description: {info['meta'].get('description', 'No description')}")
    click.echo(f"🏷️  Version: {info['meta'].get('version', 'Unknown')}")
    click.echo(f"👤 Author: {info['meta'].get('author', 'Unknown')}")
    
    if info['examples']:
        click.echo(f"\n💡 Examples:")
        for i, example in enumerate(info['examples'], 1):
            click.echo(f"   {i}. {example.get('name', 'Unnamed')}: {example.get('description', 'No description')}")

@cli.command()
def stats():
    """显示生成统计信息"""
    generator = UIGenerator()
    stats = generator.get_stats()
    
    click.echo("📊 Generation Statistics:")
    click.echo(f"   Total Generated: {stats['total_generated']}")
    click.echo(f"   Components: {stats['components_generated']}")
    click.echo(f"   Layouts: {stats['layouts_generated']}")
    click.echo(f"   Pages: {stats['pages_generated']}")
    click.echo(f"   Errors: {stats['errors']}")

if __name__ == '__main__':
    cli()

