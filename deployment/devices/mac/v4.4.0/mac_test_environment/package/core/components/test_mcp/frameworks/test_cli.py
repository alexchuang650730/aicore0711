#!/usr/bin/env python3
"""
PowerAutomation 4.0 统一测试CLI

提供统一的命令行接口来管理和运行所有测试
"""

import asyncio
import click
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from test.test_manager import get_test_manager, TestType, TestPriority

@click.group()
@click.option('--config', '-c', help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def test(ctx, config: Optional[str], verbose: bool):
    """PowerAutomation 4.0 测试命令组"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

@test.command()
@click.option('--suite', '-s', help='指定测试套件名称')
@click.option('--type', '-t', type=click.Choice(['unit', 'integration', 'ui', 'e2e', 'performance', 'demo']), help='按类型运行测试')
@click.option('--priority', '-p', type=click.Choice(['p0', 'p1', 'p2', 'p3']), help='按优先级运行测试')
@click.option('--report', '-r', is_flag=True, help='生成测试报告')
@click.option('--format', '-f', type=click.Choice(['html', 'json']), default='html', help='报告格式')
@click.pass_context
def run(ctx, suite: Optional[str], type: Optional[str], priority: Optional[str], 
        report: bool, format: str):
    """运行测试"""
    try:
        manager = get_test_manager()
        
        if suite:
            # 运行指定测试套件
            click.echo(f"🧪 运行测试套件: {suite}")
            results = [asyncio.run(manager.run_test_suite(suite))]
            
        elif type:
            # 按类型运行测试
            test_type = TestType(type)
            click.echo(f"🧪 运行 {type} 类型测试")
            results = asyncio.run(manager.run_tests_by_type(test_type))
            
        elif priority:
            # 按优先级运行测试
            test_priority = TestPriority(priority)
            click.echo(f"🧪 运行 {priority} 优先级测试")
            results = asyncio.run(manager.run_tests_by_priority(test_priority))
            
        else:
            # 运行所有测试
            click.echo("🧪 运行所有测试")
            results = asyncio.run(manager.run_all_tests())
        
        # 显示结果摘要
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        total_failed = sum(r.failed_tests for r in results)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        click.echo(f"\\n📊 测试完成")
        click.echo(f"   总测试数: {total_tests}")
        click.echo(f"   通过: {total_passed}")
        click.echo(f"   失败: {total_failed}")
        click.echo(f"   成功率: {success_rate:.1f}%")
        
        # 生成报告
        if report:
            report_file = manager.generate_report(results, format)
            click.echo(f"   报告文件: {report_file}")
        
        # 如果有失败的测试，退出码为1
        if total_failed > 0:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 运行测试失败: {e}", err=True)
        sys.exit(1)

@test.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table', help='输出格式')
@click.pass_context
def list(ctx, format: str):
    """列出所有测试套件"""
    try:
        manager = get_test_manager()
        suites = manager.list_test_suites()
        
        if format == 'json':
            click.echo(json.dumps(suites, ensure_ascii=False, indent=2))
        else:
            if not suites:
                click.echo("📝 暂无测试套件")
                return
            
            click.echo("📝 测试套件列表:")
            click.echo()
            
            # 表格头
            click.echo(f"{'名称':<20} {'类型':<12} {'优先级':<8} {'描述':<40}")
            click.echo("-" * 85)
            
            # 表格内容
            for name, info in suites.items():
                click.echo(f"{name:<20} {info['type']:<12} {info['priority']:<8} {info['description']:<40}")
            
    except Exception as e:
        click.echo(f"❌ 获取测试套件列表失败: {e}", err=True)
        sys.exit(1)

@test.command()
@click.argument('suite_name')
@click.pass_context
def info(ctx, suite_name: str):
    """显示测试套件详细信息"""
    try:
        manager = get_test_manager()
        suites = manager.list_test_suites()
        
        if suite_name not in suites:
            click.echo(f"❌ 测试套件不存在: {suite_name}", err=True)
            sys.exit(1)
        
        suite_info = suites[suite_name]
        
        click.echo(f"📋 测试套件信息: {suite_name}")
        click.echo(f"   类型: {suite_info['type']}")
        click.echo(f"   优先级: {suite_info['priority']}")
        click.echo(f"   描述: {suite_info['description']}")
        
    except Exception as e:
        click.echo(f"❌ 获取测试套件信息失败: {e}", err=True)
        sys.exit(1)

@test.command()
@click.option('--days', '-d', type=int, default=30, help='清理多少天前的结果')
@click.option('--confirm', is_flag=True, help='确认清理')
@click.pass_context
def cleanup(ctx, days: int, confirm: bool):
    """清理旧的测试结果"""
    if not confirm:
        click.echo(f"⚠️ 将清理 {days} 天前的测试结果")
        click.echo("使用 --confirm 参数确认清理")
        return
    
    try:
        manager = get_test_manager()
        cleaned_count = manager.cleanup_old_results(days)
        
        click.echo(f"🧹 清理完成")
        click.echo(f"   清理了 {cleaned_count} 个测试结果文件")
        
    except Exception as e:
        click.echo(f"❌ 清理失败: {e}", err=True)
        sys.exit(1)

@test.command()
@click.pass_context
def status(ctx):
    """显示测试系统状态"""
    try:
        manager = get_test_manager()
        suites = manager.list_test_suites()
        
        click.echo("📊 测试系统状态")
        click.echo()
        click.echo(f"测试套件:")
        click.echo(f"  总数: {len(suites)}")
        
        # 按类型统计
        type_counts = {}
        priority_counts = {}
        
        for suite_info in suites.values():
            suite_type = suite_info['type']
            suite_priority = suite_info['priority']
            
            type_counts[suite_type] = type_counts.get(suite_type, 0) + 1
            priority_counts[suite_priority] = priority_counts.get(suite_priority, 0) + 1
        
        click.echo(f"  按类型:")
        for test_type, count in type_counts.items():
            click.echo(f"    {test_type}: {count}")
        
        click.echo(f"  按优先级:")
        for priority, count in priority_counts.items():
            click.echo(f"    {priority}: {count}")
        
        # 检查输出目录
        output_dir = Path(manager.config.get('output_dir', './test_results'))
        if output_dir.exists():
            report_files = list(output_dir.glob("test_report_*"))
            click.echo(f"\\n测试结果:")
            click.echo(f"  输出目录: {output_dir}")
            click.echo(f"  报告文件: {len(report_files)}")
        
    except Exception as e:
        click.echo(f"❌ 获取状态失败: {e}", err=True)
        sys.exit(1)

# P0测试快捷命令
@test.command()
@click.option('--headless', is_flag=True, help='无头模式运行')
@click.option('--report', '-r', is_flag=True, help='生成测试报告')
@click.pass_context
def p0(ctx, headless: bool, report: bool):
    """运行P0核心测试"""
    try:
        click.echo("🚀 运行P0核心测试")
        
        manager = get_test_manager()
        results = asyncio.run(manager.run_tests_by_priority(TestPriority.P0))
        
        # 显示结果
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        total_failed = sum(r.failed_tests for r in results)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        status_icon = "✅" if total_failed == 0 else "❌"
        click.echo(f"\\n{status_icon} P0测试完成")
        click.echo(f"   总测试数: {total_tests}")
        click.echo(f"   通过: {total_passed}")
        click.echo(f"   失败: {total_failed}")
        click.echo(f"   成功率: {success_rate:.1f}%")
        
        # 生成报告
        if report:
            report_file = manager.generate_report(results, 'html')
            click.echo(f"   报告文件: {report_file}")
        
        # 如果有失败的测试，退出码为1
        if total_failed > 0:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ P0测试失败: {e}", err=True)
        sys.exit(1)

# UI测试快捷命令
@test.command()
@click.option('--browser', type=click.Choice(['chrome', 'firefox', 'safari']), default='chrome', help='浏览器类型')
@click.option('--headless', is_flag=True, help='无头模式运行')
@click.option('--report', '-r', is_flag=True, help='生成测试报告')
@click.pass_context
def ui(ctx, browser: str, headless: bool, report: bool):
    """运行UI测试"""
    try:
        click.echo(f"🖥️ 运行UI测试 (浏览器: {browser})")
        
        manager = get_test_manager()
        results = asyncio.run(manager.run_tests_by_type(TestType.UI))
        
        # 显示结果
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        total_failed = sum(r.failed_tests for r in results)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        status_icon = "✅" if total_failed == 0 else "❌"
        click.echo(f"\\n{status_icon} UI测试完成")
        click.echo(f"   总测试数: {total_tests}")
        click.echo(f"   通过: {total_passed}")
        click.echo(f"   失败: {total_failed}")
        click.echo(f"   成功率: {success_rate:.1f}%")
        
        # 生成报告
        if report:
            report_file = manager.generate_report(results, 'html')
            click.echo(f"   报告文件: {report_file}")
        
        # 如果有失败的测试，退出码为1
        if total_failed > 0:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ UI测试失败: {e}", err=True)
        sys.exit(1)

# 演示测试快捷命令
@test.command()
@click.option('--demo', type=click.Choice(['tc_demo_001', 'tc_demo_002', 'tc_demo_003', 'tc_demo_004', 'all']), default='all', help='指定演示')
@click.option('--record', is_flag=True, help='录制演示过程')
@click.option('--report', '-r', is_flag=True, help='生成测试报告')
@click.pass_context
def demo(ctx, demo: str, record: bool, report: bool):
    """运行演示测试"""
    try:
        if demo == 'all':
            click.echo("🎬 运行所有演示测试")
        else:
            click.echo(f"🎬 运行演示测试: {demo}")
        
        manager = get_test_manager()
        results = asyncio.run(manager.run_tests_by_type(TestType.DEMO))
        
        # 显示结果
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        total_failed = sum(r.failed_tests for r in results)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        status_icon = "✅" if total_failed == 0 else "❌"
        click.echo(f"\\n{status_icon} 演示测试完成")
        click.echo(f"   总测试数: {total_tests}")
        click.echo(f"   通过: {total_passed}")
        click.echo(f"   失败: {total_failed}")
        click.echo(f"   成功率: {success_rate:.1f}%")
        
        # 生成报告
        if report:
            report_file = manager.generate_report(results, 'html')
            click.echo(f"   报告文件: {report_file}")
        
        # 如果有失败的测试，退出码为1
        if total_failed > 0:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 演示测试失败: {e}", err=True)
        sys.exit(1)

# 主入口点
if __name__ == '__main__':
    test()

