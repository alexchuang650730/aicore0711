#!/usr/bin/env python3
"""
PowerAutomation 4.0 Stagewise Test Runner

Stagewise测试运行器，提供命令行接口和批量测试功能
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .enhanced_testing_framework import (
    EnhancedStagewiseTestingFramework,
    TestPriority,
    TestCategory,
    run_p0_tests,
    run_all_mcp_tests,
    run_comprehensive_tests
)

logger = logging.getLogger(__name__)


class StagewiseTestRunner:
    """Stagewise测试运行器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_config(config_file)
        self.framework = EnhancedStagewiseTestingFramework(self.config)
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "log_level": "INFO",
            "results_dir": "test_results",
            "timeout": 30,
            "retry_count": 0,
            "parallel": False,
            "max_workers": 4
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                default_config.update(file_config)
            except Exception as e:
                logger.warning(f"配置文件加载失败: {str(e)}")
        
        return default_config
    
    async def run_tests(self, args: argparse.Namespace) -> int:
        """运行测试"""
        try:
            if args.command == "p0":
                return await self._run_p0_tests(args)
            elif args.command == "mcp":
                return await self._run_mcp_tests(args)
            elif args.command == "ui":
                return await self._run_ui_tests(args)
            elif args.command == "performance":
                return await self._run_performance_tests(args)
            elif args.command == "all":
                return await self._run_all_tests(args)
            elif args.command == "suite":
                return await self._run_test_suite(args)
            elif args.command == "case":
                return await self._run_test_case(args)
            else:
                print(f"未知命令: {args.command}")
                return 1
        
        except Exception as e:
            logger.error(f"测试执行失败: {str(e)}")
            return 1
    
    async def _run_p0_tests(self, args: argparse.Namespace) -> int:
        """运行P0测试"""
        print("🚀 开始运行P0核心功能测试...")
        
        session = await run_p0_tests(self.config)
        
        # 生成报告
        report = self.framework.generate_test_report(session)
        print(report)
        
        # 保存报告
        if args.output:
            self._save_report(report, args.output)
        
        # 返回退出码
        return 0 if session.failed_tests == 0 and session.error_tests == 0 else 1
    
    async def _run_mcp_tests(self, args: argparse.Namespace) -> int:
        """运行MCP测试"""
        print("🔧 开始运行MCP组件测试...")
        
        session = await run_all_mcp_tests(self.config)
        
        # 生成报告
        report = self.framework.generate_test_report(session)
        print(report)
        
        # 保存报告
        if args.output:
            self._save_report(report, args.output)
        
        return 0 if session.failed_tests == 0 and session.error_tests == 0 else 1
    
    async def _run_ui_tests(self, args: argparse.Namespace) -> int:
        """运行UI测试"""
        print("🖥️ 开始运行UI功能测试...")
        
        session_id = await self.framework.start_test_session({"test_type": "UI功能测试"})
        
        try:
            results = await self.framework.run_test_suite("ui_functionality_tests")
            self.framework.current_session.test_results.extend(results)
            
            session = await self.framework.end_test_session()
            
            # 生成报告
            report = self.framework.generate_test_report(session)
            print(report)
            
            # 保存报告
            if args.output:
                self._save_report(report, args.output)
            
            return 0 if session.failed_tests == 0 and session.error_tests == 0 else 1
            
        except Exception as e:
            logger.error(f"UI测试执行失败: {str(e)}")
            if self.framework.current_session:
                await self.framework.end_test_session()
            return 1
    
    async def _run_performance_tests(self, args: argparse.Namespace) -> int:
        """运行性能测试"""
        print("⚡ 开始运行性能测试...")
        
        session_id = await self.framework.start_test_session({"test_type": "性能测试"})
        
        try:
            results = await self.framework.run_test_suite("performance_tests")
            self.framework.current_session.test_results.extend(results)
            
            session = await self.framework.end_test_session()
            
            # 生成报告
            report = self.framework.generate_test_report(session)
            print(report)
            
            # 保存报告
            if args.output:
                self._save_report(report, args.output)
            
            return 0 if session.failed_tests == 0 and session.error_tests == 0 else 1
            
        except Exception as e:
            logger.error(f"性能测试执行失败: {str(e)}")
            if self.framework.current_session:
                await self.framework.end_test_session()
            return 1
    
    async def _run_all_tests(self, args: argparse.Namespace) -> int:
        """运行所有测试"""
        print("🎯 开始运行全面测试...")
        
        sessions = await run_comprehensive_tests(self.config)
        
        # 生成综合报告
        total_tests = sum(s.total_tests for s in sessions)
        total_passed = sum(s.passed_tests for s in sessions)
        total_failed = sum(s.failed_tests for s in sessions)
        total_errors = sum(s.error_tests for s in sessions)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        comprehensive_report = f"""
# 综合测试报告

## 总体统计
- **总测试数**: {total_tests}
- **通过**: {total_passed}
- **失败**: {total_failed}
- **错误**: {total_errors}
- **成功率**: {success_rate:.1f}%

## 各测试套件结果
"""
        
        for session in sessions:
            suite_success_rate = (session.passed_tests / session.total_tests * 100) if session.total_tests > 0 else 0
            comprehensive_report += f"""
### {session.environment.get('test_type', '未知测试')}
- 测试数: {session.total_tests}
- 通过: {session.passed_tests}
- 失败: {session.failed_tests}
- 成功率: {suite_success_rate:.1f}%
"""
        
        print(comprehensive_report)
        
        # 保存报告
        if args.output:
            self._save_report(comprehensive_report, args.output)
        
        return 0 if total_failed == 0 and total_errors == 0 else 1
    
    async def _run_test_suite(self, args: argparse.Namespace) -> int:
        """运行指定测试套件"""
        suite_id = args.suite_id
        print(f"📋 开始运行测试套件: {suite_id}")
        
        if suite_id not in self.framework.test_suites:
            print(f"错误: 测试套件 {suite_id} 不存在")
            return 1
        
        session_id = await self.framework.start_test_session({"test_type": f"{suite_id}测试"})
        
        try:
            # 构建过滤器
            filters = {}
            if args.priority:
                filters['priority'] = args.priority
            if args.category:
                filters['category'] = args.category
            if args.component:
                filters['component'] = args.component
            
            results = await self.framework.run_test_suite(suite_id, filters)
            self.framework.current_session.test_results.extend(results)
            
            session = await self.framework.end_test_session()
            
            # 生成报告
            report = self.framework.generate_test_report(session)
            print(report)
            
            # 保存报告
            if args.output:
                self._save_report(report, args.output)
            
            return 0 if session.failed_tests == 0 and session.error_tests == 0 else 1
            
        except Exception as e:
            logger.error(f"测试套件执行失败: {str(e)}")
            if self.framework.current_session:
                await self.framework.end_test_session()
            return 1
    
    async def _run_test_case(self, args: argparse.Namespace) -> int:
        """运行指定测试用例"""
        test_id = args.test_id
        print(f"🧪 开始运行测试用例: {test_id}")
        
        if test_id not in self.framework.test_cases:
            print(f"错误: 测试用例 {test_id} 不存在")
            return 1
        
        session_id = await self.framework.start_test_session({"test_type": f"{test_id}测试"})
        
        try:
            test_case = self.framework.test_cases[test_id]
            result = await self.framework._run_test_case(test_case)
            
            self.framework.current_session.test_results.append(result)
            session = await self.framework.end_test_session()
            
            # 生成报告
            report = self.framework.generate_test_report(session)
            print(report)
            
            # 保存报告
            if args.output:
                self._save_report(report, args.output)
            
            return 0 if result.status.value in ['passed'] else 1
            
        except Exception as e:
            logger.error(f"测试用例执行失败: {str(e)}")
            if self.framework.current_session:
                await self.framework.end_test_session()
            return 1
    
    def _save_report(self, report: str, output_file: str):
        """保存报告到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存报告失败: {str(e)}")
    
    def list_test_suites(self):
        """列出所有测试套件"""
        print("📋 可用的测试套件:")
        for suite_id, suite in self.framework.test_suites.items():
            test_count = len(suite.test_cases)
            print(f"  - {suite_id}: {suite.name} ({test_count}个测试)")
    
    def list_test_cases(self, suite_id: Optional[str] = None):
        """列出测试用例"""
        if suite_id:
            if suite_id not in self.framework.test_suites:
                print(f"错误: 测试套件 {suite_id} 不存在")
                return
            
            suite = self.framework.test_suites[suite_id]
            print(f"📋 测试套件 {suite.name} 中的测试用例:")
            for test_case in suite.test_cases:
                print(f"  - {test_case.test_id}: {test_case.name} ({test_case.priority.value})")
        else:
            print("🧪 所有测试用例:")
            for test_id, test_case in self.framework.test_cases.items():
                print(f"  - {test_id}: {test_case.name} ({test_case.priority.value}, {test_case.component})")


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Stagewise测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行P0测试
  python test_runner.py p0
  
  # 运行MCP组件测试
  python test_runner.py mcp
  
  # 运行所有测试
  python test_runner.py all
  
  # 运行指定测试套件
  python test_runner.py suite p0_core_tests
  
  # 运行指定测试用例
  python test_runner.py case p0_001
  
  # 列出测试套件
  python test_runner.py list suites
  
  # 列出测试用例
  python test_runner.py list cases
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='报告输出文件路径'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # P0测试命令
    p0_parser = subparsers.add_parser('p0', help='运行P0核心功能测试')
    
    # MCP测试命令
    mcp_parser = subparsers.add_parser('mcp', help='运行MCP组件测试')
    
    # UI测试命令
    ui_parser = subparsers.add_parser('ui', help='运行UI功能测试')
    
    # 性能测试命令
    perf_parser = subparsers.add_parser('performance', help='运行性能测试')
    
    # 全部测试命令
    all_parser = subparsers.add_parser('all', help='运行所有测试')
    
    # 测试套件命令
    suite_parser = subparsers.add_parser('suite', help='运行指定测试套件')
    suite_parser.add_argument('suite_id', help='测试套件ID')
    suite_parser.add_argument('--priority', choices=['P0', 'P1', 'P2', 'P3'], help='按优先级过滤')
    suite_parser.add_argument('--category', choices=['unit', 'integration', 'e2e', 'performance', 'security', 'ui', 'api', 'mcp'], help='按分类过滤')
    suite_parser.add_argument('--component', help='按组件过滤')
    
    # 测试用例命令
    case_parser = subparsers.add_parser('case', help='运行指定测试用例')
    case_parser.add_argument('test_id', help='测试用例ID')
    
    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出测试套件或测试用例')
    list_subparsers = list_parser.add_subparsers(dest='list_type', help='列表类型')
    
    suites_parser = list_subparsers.add_parser('suites', help='列出测试套件')
    
    cases_parser = list_subparsers.add_parser('cases', help='列出测试用例')
    cases_parser.add_argument('--suite', help='指定测试套件')
    
    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 创建测试运行器
    runner = StagewiseTestRunner(args.config)
    
    # 处理列表命令
    if args.command == 'list':
        if args.list_type == 'suites':
            runner.list_test_suites()
        elif args.list_type == 'cases':
            runner.list_test_cases(getattr(args, 'suite', None))
        else:
            print("请指定要列出的类型: suites 或 cases")
            return 1
        return 0
    
    # 运行测试
    return await runner.run_tests(args)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

