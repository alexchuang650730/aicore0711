"""
PowerAutomation v4.6.1 企業版本管理CLI
Enterprise Version Management CLI Commands
"""

import asyncio
import click
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from core.enterprise.version_strategy import (
    enterprise_version_strategy,
    EditionTier,
    VersionChannel,
    FeatureAccess
)

console = Console()


@click.group()
def enterprise():
    """PowerAutomation企業版本管理"""
    pass


@enterprise.command()
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json', 'yaml']),
              help='輸出格式')
def list_editions(format):
    """列出所有版本層級"""
    asyncio.run(_list_editions(format))


async def _list_editions(format):
    """列出版本層級實現"""
    await enterprise_version_strategy.initialize()
    
    comparison = enterprise_version_strategy.get_edition_comparison()
    
    if format == 'table':
        table = Table(title="PowerAutomation v4.6.1 版本對比")
        table.add_column("功能", style="cyan")
        table.add_column("個人版", style="green")
        table.add_column("專業版", style="yellow") 
        table.add_column("團隊版", style="blue")
        table.add_column("企業版", style="red")
        
        # 收集所有功能
        all_features = set()
        for edition_data in comparison.values():
            all_features.update(edition_data['features'].keys())
        
        for feature_id in sorted(all_features):
            row = [feature_id]
            for edition in ['personal', 'professional', 'team', 'enterprise']:
                edition_data = comparison[edition]
                feature_data = edition_data['features'].get(feature_id, {})
                access = feature_data.get('access', 'disabled')
                
                if access == 'enabled':
                    row.append("✅ 完全啟用")
                elif access == 'limited':
                    row.append("⚠️ 限制使用")
                elif access == 'trial':
                    row.append("🆓 試用模式")
                else:
                    row.append("❌ 不可用")
            
            table.add_row(*row)
        
        console.print(table)
        
        # 顯示定價信息
        pricing_table = Table(title="版本定價")
        pricing_table.add_column("版本", style="cyan")
        pricing_table.add_column("月費", style="green")
        pricing_table.add_column("年費", style="yellow")
        pricing_table.add_column("支持級別", style="blue")
        
        for edition in ['personal', 'professional', 'team', 'enterprise']:
            edition_data = comparison[edition]
            pricing = edition_data['pricing']
            
            pricing_table.add_row(
                edition.title(),
                f"${pricing.get('monthly', 0)}",
                f"${pricing.get('annual', 0)}",
                edition_data['support_level']
            )
        
        console.print(pricing_table)
        
    elif format == 'json':
        console.print(json.dumps(comparison, indent=2, ensure_ascii=False))
    
    elif format == 'yaml':
        console.print(yaml.dump(comparison, default_flow_style=False, allow_unicode=True))


@enterprise.command()
@click.option('--feature', '-f', help='檢查特定功能的訪問權限')
def check_access(feature):
    """檢查功能訪問權限"""
    asyncio.run(_check_access(feature))


async def _check_access(feature):
    """檢查功能訪問權限實現"""
    await enterprise_version_strategy.initialize()
    
    if feature:
        # 檢查特定功能
        access = enterprise_version_strategy.check_feature_access(feature)
        current_edition = enterprise_version_strategy.current_edition
        
        console.print(f"🔍 功能: {feature}")
        console.print(f"📦 當前版本: {current_edition.value}")
        console.print(f"🔑 訪問權限: {access.value}")
        
        if access == FeatureAccess.DISABLED:
            console.print("❌ 該功能在當前版本中不可用")
        elif access == FeatureAccess.LIMITED:
            console.print("⚠️ 該功能在當前版本中有限制")
        elif access == FeatureAccess.TRIAL:
            console.print("🆓 該功能為試用模式")
        else:
            console.print("✅ 該功能完全可用")
    
    else:
        # 顯示當前版本所有可用功能
        available_features = enterprise_version_strategy.get_available_features()
        current_edition = enterprise_version_strategy.current_edition
        
        console.print(f"📦 當前版本: {current_edition.value}")
        console.print(f"✅ 可用功能數量: {len(available_features)}")
        
        table = Table(title=f"{current_edition.value.title()} 版本可用功能")
        table.add_column("功能ID", style="cyan")
        table.add_column("功能名稱", style="green")
        table.add_column("訪問權限", style="yellow")
        table.add_column("類別", style="blue")
        
        for feature_id in available_features:
            feature = enterprise_version_strategy.features_registry[feature_id]
            access = enterprise_version_strategy.check_feature_access(feature_id)
            
            table.add_row(
                feature_id,
                feature.name,
                access.value,
                feature.category
            )
        
        console.print(table)


@enterprise.command()
@click.argument('edition', type=click.Choice(['personal', 'professional', 'team', 'enterprise']))
@click.option('--users', '-u', default=1, help='用戶數量')
@click.option('--organization', '-o', help='組織名稱')
@click.option('--days', '-d', default=365, help='授權天數')
def generate_license(edition, users, organization, days):
    """生成版本授權"""
    asyncio.run(_generate_license(edition, users, organization, days))


async def _generate_license(edition, users, organization, days):
    """生成版本授權實現"""
    await enterprise_version_strategy.initialize()
    
    edition_tier = EditionTier(edition)
    
    try:
        license_info = await enterprise_version_strategy.generate_license(
            edition=edition_tier,
            user_count=users,
            organization=organization,
            duration_days=days
        )
        
        console.print(Panel.fit(
            f"[green]✅ 授權生成成功[/green]\n\n"
            f"[cyan]授權密鑰:[/cyan] {license_info.license_key}\n"
            f"[cyan]版本:[/cyan] {license_info.edition.value}\n"
            f"[cyan]用戶數量:[/cyan] {license_info.user_count}\n"
            f"[cyan]有效期至:[/cyan] {license_info.valid_until}\n"
            f"[cyan]組織:[/cyan] {license_info.organization or 'N/A'}\n"
            f"[cyan]啟用功能:[/cyan] {len(license_info.features_enabled)} 個",
            title="PowerAutomation 授權信息"
        ))
        
    except Exception as e:
        console.print(f"[red]❌ 授權生成失敗: {e}[/red]")


@enterprise.command()
@click.option('--key', '-k', help='授權密鑰')
def validate_license(key):
    """驗證授權"""
    asyncio.run(_validate_license(key))


async def _validate_license(key):
    """驗證授權實現"""
    await enterprise_version_strategy.initialize()
    
    try:
        is_valid = await enterprise_version_strategy.validate_license(key)
        
        if is_valid:
            console.print("[green]✅ 授權驗證成功[/green]")
        else:
            console.print("[red]❌ 授權驗證失敗[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ 授權驗證出錯: {e}[/red]")


@enterprise.command()
@click.argument('target_edition', type=click.Choice(['professional', 'team', 'enterprise']))
def upgrade(target_edition):
    """升級版本"""
    asyncio.run(_upgrade(target_edition))


async def _upgrade(target_edition):
    """升級版本實現"""
    await enterprise_version_strategy.initialize()
    
    target_tier = EditionTier(target_edition)
    current_tier = enterprise_version_strategy.current_edition
    
    console.print(f"🔄 準備從 {current_tier.value} 升級到 {target_tier.value}")
    
    try:
        success = await enterprise_version_strategy.upgrade_edition(target_tier)
        
        if success:
            console.print(f"[green]✅ 成功升級到 {target_tier.value} 版本[/green]")
        else:
            console.print(f"[red]❌ 升級失敗[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ 升級出錯: {e}[/red]")


@enterprise.command()
def status():
    """顯示企業版本策略狀態"""
    asyncio.run(_status())


async def _status():
    """顯示狀態實現"""
    await enterprise_version_strategy.initialize()
    
    status = enterprise_version_strategy.get_status()
    
    console.print(Panel.fit(
        f"[green]組件:[/green] {status['component']}\n"
        f"[green]版本:[/green] {status['version']}\n"
        f"[green]當前版本:[/green] {status['current_edition']}\n"
        f"[green]總功能數:[/green] {status['total_features']}\n"
        f"[green]可用功能數:[/green] {status['available_features']}\n"
        f"[green]授權狀態:[/green] {status['license_status']}",
        title="Enterprise Version Strategy 狀態"
    ))


@enterprise.command()
@click.option('--output', '-o', default='enterprise_version_strategy.yaml', help='輸出文件路徑')
def export_config(output):
    """導出版本策略配置"""
    asyncio.run(_export_config(output))


async def _export_config(output):
    """導出配置實現"""
    await enterprise_version_strategy.initialize()
    
    try:
        await enterprise_version_strategy.save_version_strategy_config(output)
        console.print(f"[green]✅ 配置已導出到: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ 配置導出失敗: {e}[/red]")


if __name__ == '__main__':
    enterprise()