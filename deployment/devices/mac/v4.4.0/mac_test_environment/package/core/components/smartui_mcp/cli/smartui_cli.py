#!/usr/bin/env python3
"""
SmartUI MCP 命令行接口

PowerAutomation 4.1 SmartUI MCP的CLI工具
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import click
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from core.components.smartui_mcp.services.smartui_service import get_smartui_service
from core.components.smartui_mcp.generators.smartui_generator import SmartUIGenerator, SmartUIGenerationRequest

logger = logging.getLogger(__name__)

class SmartUICLI:
    """SmartUI MCP命令行接口"""
    
    def __init__(self):
        self.service = None
        self.generator = None
    
    async def initialize(self):
        """初始化CLI"""
        self.service = await get_smartui_service()
        self.generator = SmartUIGenerator(smartui_service=self.service)

# CLI命令组
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出')
@click.option('--config', '-c', help='配置文件路径')
@click.pass_context
def cli(ctx, verbose, config):
    """PowerAutomation 4.1 SmartUI MCP - 智能UI生成平台"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    
    # 配置日志
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

@cli.group()
def component():
    """组件管理命令"""
    pass

@component.command()
@click.argument('template_name')
@click.argument('component_name')
@click.option('--output', '-o', default='core/components/smartui_mcp/generated', help='输出目录')
@click.option('--theme', '-t', help='使用的主题')
@click.option('--framework', '-f', default='react', type=click.Choice(['react', 'vue', 'html']), help='目标框架')
@click.option('--context', help='上下文JSON字符串或文件路径')
@click.option('--agui/--no-agui', default=True, help='是否集成AG-UI')
@click.option('--ai/--no-ai', default=True, help='是否启用AI优化')
@click.pass_context
def generate(ctx, template_name, component_name, output, theme, framework, context, agui, ai):
    """生成UI组件"""
    async def _generate():
        try:
            cli_instance = SmartUICLI()
            await cli_instance.initialize()
            
            # 解析上下文
            context_data = {"name": component_name}
            if context:
                if context.startswith('{'):
                    # JSON字符串
                    context_data.update(json.loads(context))
                else:
                    # 文件路径
                    context_path = Path(context)
                    if context_path.exists():
                        with open(context_path, 'r', encoding='utf-8') as f:
                            context_data.update(json.load(f))
                    else:
                        click.echo(f"❌ 上下文文件不存在: {context}")
                        return
            
            # 创建生成请求
            request = SmartUIGenerationRequest(
                type="component",
                template=template_name,
                context=context_data,
                output_dir=output,
                theme=theme,
                framework=framework,
                agui_integration=agui,
                ai_optimization=ai
            )
            
            # 生成组件
            if ctx.obj['verbose']:
                click.echo(f"🚀 开始生成组件 '{component_name}'...")
                click.echo(f"   模板: {template_name}")
                click.echo(f"   框架: {framework}")
                click.echo(f"   主题: {theme or 'default'}")
                click.echo(f"   AG-UI集成: {'是' if agui else '否'}")
                click.echo(f"   AI优化: {'是' if ai else '否'}")
            
            result = await cli_instance.generator.generate_smart(request)
            
            if result.success:
                click.echo(f"✅ 组件 '{component_name}' 生成成功!")
                click.echo(f"📁 输出文件 ({len(result.output_files)} 个):")
                for file_path in result.output_files:
                    click.echo(f"   • {file_path}")
                
                if result.warnings:
                    click.echo(f"⚠️  警告 ({len(result.warnings)} 个):")
                    for warning in result.warnings:
                        click.echo(f"   • {warning}")
            else:
                click.echo(f"❌ 组件 '{component_name}' 生成失败!")
                for error in result.errors:
                    click.echo(f"   错误: {error}")
                
                if result.warnings:
                    for warning in result.warnings:
                        click.echo(f"   警告: {warning}")
        
        except Exception as e:
            click.echo(f"❌ 生成过程中发生错误: {e}")
            if ctx.obj['verbose']:
                import traceback
                click.echo(traceback.format_exc())
    
    asyncio.run(_generate())

@component.command()
@click.option('--category', '-c', help='组件分类过滤')
@click.pass_context
def list_templates(ctx, category):
    """列出可用的组件模板"""
    async def _list():
        try:
            cli_instance = SmartUICLI()
            await cli_instance.initialize()
            
            templates = await cli_instance.service.get_component_templates(category)
            
            if not templates:
                click.echo("❌ 没有找到组件模板")
                return
            
            # 按分类组织模板
            categories = {}
            for template in templates:
                cat = template.get('category', 'unknown')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(template)
            
            click.echo(f"📂 可用组件模板 ({len(templates)} 个):")
            
            for cat, cat_templates in categories.items():
                click.echo(f"\n📁 {cat.title()} ({len(cat_templates)} 个):")
                for template in cat_templates:
                    meta = template.get('meta', {})
                    name = meta.get('name', 'Unknown')
                    description = meta.get('description', 'No description')
                    version = meta.get('version', 'Unknown')
                    
                    click.echo(f"   • {name} (v{version})")
                    if ctx.obj['verbose']:
                        click.echo(f"     {description}")
        
        except Exception as e:
            click.echo(f"❌ 获取模板列表失败: {e}")
    
    asyncio.run(_list())

@component.command()
@click.argument('template_name')
@click.option('--category', '-c', default='basic', help='模板分类')
@click.pass_context
def template_info(ctx, template_name, category):
    """显示模板详细信息"""
    async def _info():
        try:
            cli_instance = SmartUICLI()
            await cli_instance.initialize()
            
            # 查找模板文件
            template_path = Path(f"core/components/smartui_mcp/templates/components/{category}/{template_name}.json")
            
            if not template_path.exists():
                click.echo(f"❌ 模板文件不存在: {template_path}")
                return
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            meta = template_data.get('meta', {})
            schema = template_data.get('schema', {})
            examples = template_data.get('examples', [])
            
            click.echo(f"📋 模板信息: {template_name}")
            click.echo(f"📝 名称: {meta.get('name', 'Unknown')}")
            click.echo(f"📄 描述: {meta.get('description', 'No description')}")
            click.echo(f"🏷️  版本: {meta.get('version', 'Unknown')}")
            click.echo(f"👤 作者: {meta.get('author', 'Unknown')}")
            click.echo(f"📂 分类: {meta.get('category', category)}")
            
            if meta.get('tags'):
                click.echo(f"🏷️  标签: {', '.join(meta['tags'])}")
            
            # 显示属性
            if schema.get('properties'):
                click.echo(f"\n⚙️  属性 ({len(schema['properties'])} 个):")
                for prop_name, prop_info in schema['properties'].items():
                    prop_type = prop_info.get('type', 'unknown')
                    prop_desc = prop_info.get('description', 'No description')
                    default_val = prop_info.get('default', 'None')
                    
                    click.echo(f"   • {prop_name} ({prop_type}): {prop_desc}")
                    if ctx.obj['verbose']:
                        click.echo(f"     默认值: {default_val}")
            
            # 显示示例
            if examples:
                click.echo(f"\n💡 示例 ({len(examples)} 个):")
                for i, example in enumerate(examples, 1):
                    example_name = example.get('name', f'示例 {i}')
                    example_desc = example.get('description', 'No description')
                    
                    click.echo(f"   {i}. {example_name}: {example_desc}")
                    
                    if ctx.obj['verbose'] and example.get('context'):
                        click.echo(f"      上下文: {json.dumps(example['context'], ensure_ascii=False, indent=6)}")
        
        except Exception as e:
            click.echo(f"❌ 获取模板信息失败: {e}")
    
    asyncio.run(_info())

@cli.group()
def theme():
    """主题管理命令"""
    pass

@theme.command()
@click.pass_context
def list(ctx):
    """列出可用主题"""
    async def _list():
        try:
            cli_instance = SmartUICLI()
            await cli_instance.initialize()
            
            themes = await cli_instance.service.get_available_themes()
            
            if not themes:
                click.echo("❌ 没有找到可用主题")
                return
            
            click.echo(f"🎨 可用主题 ({len(themes)} 个):")
            
            for theme in themes:
                name = theme.get('name', 'Unknown')
                description = theme.get('description', 'No description')
                version = theme.get('version', 'Unknown')
                
                click.echo(f"   • {name} (v{version})")
                if ctx.obj['verbose']:
                    click.echo(f"     {description}")
        
        except Exception as e:
            click.echo(f"❌ 获取主题列表失败: {e}")
    
    asyncio.run(_list())

@cli.group()
def service():
    """服务管理命令"""
    pass

@service.command()
@click.pass_context
def status(ctx):
    """显示服务状态"""
    async def _status():
        try:
            cli_instance = SmartUICLI()
            await cli_instance.initialize()
            
            status = cli_instance.service.get_service_status()
            
            click.echo("🔧 SmartUI MCP 服务状态:")
            click.echo(f"   服务ID: {status['service_id']}")
            click.echo(f"   版本: {status['version']}")
            click.echo(f"   运行状态: {'🟢 运行中' if status['is_running'] else '🔴 已停止'}")
            
            if status['uptime_seconds']:
                uptime_hours = status['uptime_seconds'] / 3600
                click.echo(f"   运行时间: {uptime_hours:.2f} 小时")
            
            # 显示统计信息
            stats = status['stats']
            click.echo(f"\n📊 统计信息:")
            click.echo(f"   处理请求: {stats['requests_processed']}")
            click.echo(f"   生成组件: {stats['components_generated']}")
            click.echo(f"   AI优化: {stats['ai_optimizations']}")
            click.echo(f"   主题应用: {stats['theme_applications']}")
            click.echo(f"   错误数量: {stats['errors']}")
            
            if stats['cache_hits'] + stats['cache_misses'] > 0:
                cache_hit_rate = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100
                click.echo(f"   缓存命中率: {cache_hit_rate:.1f}%")
            
            # 显示子服务状态
            services = status['services']
            click.echo(f"\n🔧 子服务状态:")
            click.echo(f"   AI优化服务: {'🟢 启用' if services['ai_optimization'] else '🔴 禁用'}")
            click.echo(f"   主题管理服务: {'🟢 启用' if services['theme_management'] else '🔴 禁用'}")
            click.echo(f"   组件注册服务: {'🟢 启用' if services['component_registry'] else '🔴 禁用'}")
        
        except Exception as e:
            click.echo(f"❌ 获取服务状态失败: {e}")
    
    asyncio.run(_status())

@service.command()
@click.pass_context
def health(ctx):
    """健康检查"""
    async def _health():
        try:
            cli_instance = SmartUICLI()
            await cli_instance.initialize()
            
            health = await cli_instance.service.health_check()
            
            status_emoji = "🟢" if health['status'] == 'healthy' else "🔴"
            click.echo(f"{status_emoji} SmartUI MCP 健康状态: {health['status']}")
            click.echo(f"   检查时间: {health['timestamp']}")
            
            if health.get('checks'):
                click.echo(f"\n🔍 详细检查:")
                for check_name, check_result in health['checks'].items():
                    if isinstance(check_result, dict):
                        if check_result.get('exists') or check_result.get('status') == 'healthy':
                            click.echo(f"   ✅ {check_name}")
                        else:
                            click.echo(f"   ❌ {check_name}")
                            if check_result.get('error'):
                                click.echo(f"      错误: {check_result['error']}")
                    else:
                        status_emoji = "✅" if check_result else "❌"
                        click.echo(f"   {status_emoji} {check_name}")
        
        except Exception as e:
            click.echo(f"❌ 健康检查失败: {e}")
    
    asyncio.run(_health())

@cli.command()
@click.pass_context
def version(ctx):
    """显示版本信息"""
    click.echo("PowerAutomation 4.1 SmartUI MCP")
    click.echo("版本: 4.1.0")
    click.echo("作者: PowerAutomation 4.1 Team")
    click.echo("描述: 智能UI生成和管理平台")

if __name__ == '__main__':
    cli()

