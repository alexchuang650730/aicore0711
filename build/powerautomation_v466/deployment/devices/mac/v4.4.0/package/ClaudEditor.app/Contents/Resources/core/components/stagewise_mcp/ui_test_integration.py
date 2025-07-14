#!/usr/bin/env python3
"""
Stagewise框架与UI测试集成模块

提供Stagewise测试框架与test/目录下UI测试用例的无缝集成，
支持自动发现、注册和执行UI测试。
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .enhanced_testing_framework import (
    EnhancedStagewiseTestingFramework,
    TestCase, TestResult, TestSuite, TestSession,
    TestStatus, TestPriority, TestCategory
)

logger = logging.getLogger(__name__)


class UITestIntegration:
    """UI测试集成器"""
    
    def __init__(self, framework: EnhancedStagewiseTestingFramework):
        self.framework = framework
        self.ui_test_registry = None
        self._initialize_ui_test_registry()
    
    def _initialize_ui_test_registry(self):
        """初始化UI测试注册器"""
        try:
            # 动态导入UI测试注册器 - 已迁移到test_mcp
            # from test.ui_test_registry import get_ui_test_registry
            # TODO: 更新为使用 core.components.test_mcp 的对应功能
            # self.ui_test_registry = get_ui_test_registry()
            self.ui_test_registry = None  # 临时禁用，等待test_mcp集成
            logger.info("UI测试注册器已禁用，等待test_mcp集成")
        except ImportError as e:
            logger.error(f"无法导入UI测试注册器: {str(e)}")
            self.ui_test_registry = None
        except Exception as e:
            logger.error(f"初始化UI测试注册器失败: {str(e)}")
            self.ui_test_registry = None
    
    def discover_and_register_ui_tests(self) -> Dict[str, Any]:
        """发现并注册UI测试"""
        if not self.ui_test_registry:
            logger.warning("UI测试注册器未初始化，跳过UI测试注册")
            return {"success": False, "error": "UI测试注册器未初始化"}
        
        try:
            # 发现和注册UI测试
            result = self.ui_test_registry.discover_and_register_tests()
            
            # 将UI测试用例添加到Stagewise框架
            ui_tests = self.ui_test_registry.get_registered_tests()
            for test_id, test_case in ui_tests.items():
                if test_id not in self.framework.test_cases:
                    self.framework.test_cases[test_id] = test_case
            
            # 将UI测试套件添加到Stagewise框架
            ui_suites = self.ui_test_registry.get_test_suites()
            for suite_id, test_suite in ui_suites.items():
                if suite_id not in self.framework.test_suites:
                    self.framework.test_suites[suite_id] = test_suite
            
            logger.info(f"成功集成 {len(ui_tests)} 个UI测试用例和 {len(ui_suites)} 个测试套件")
            
            return {
                "success": True,
                "ui_tests_count": len(ui_tests),
                "ui_suites_count": len(ui_suites),
                "total_tests": result.get("total_tests", 0),
                "modules": result.get("modules", []),
                "suites": result.get("suites", [])
            }
            
        except Exception as e:
            logger.error(f"发现和注册UI测试失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def run_ui_test_suite(self, suite_name: str) -> TestSession:
        """运行UI测试套件"""
        if not self.ui_test_registry:
            raise RuntimeError("UI测试注册器未初始化")
        
        # 确保UI测试已注册
        self.discover_and_register_ui_tests()
        
        # 检查测试套件是否存在
        if suite_name not in self.framework.test_suites:
            raise ValueError(f"UI测试套件不存在: {suite_name}")
        
        logger.info(f"开始运行UI测试套件: {suite_name}")
        
        # 启动测试会话
        session_id = await self.framework.start_test_session({
            "test_type": f"UI测试套件: {suite_name}",
            "suite_name": suite_name
        })
        
        try:
            # 运行测试套件
            results = await self.framework.run_test_suite(suite_name)
            
            # 更新会话结果
            if self.framework.current_session:
                self.framework.current_session.test_results.extend(results)
            
            # 结束测试会话
            session = await self.framework.end_test_session()
            
            logger.info(f"UI测试套件 {suite_name} 执行完成: "
                       f"{session.passed_tests}/{session.total_tests} 通过")
            
            return session
            
        except Exception as e:
            logger.error(f"运行UI测试套件失败: {str(e)}")
            if self.framework.current_session:
                await self.framework.end_test_session()
            raise
    
    async def run_ui_test_case(self, test_id: str) -> TestResult:
        """运行单个UI测试用例"""
        if not self.ui_test_registry:
            raise RuntimeError("UI测试注册器未初始化")
        
        # 确保UI测试已注册
        self.discover_and_register_ui_tests()
        
        # 检查测试用例是否存在
        if test_id not in self.framework.test_cases:
            raise ValueError(f"UI测试用例不存在: {test_id}")
        
        logger.info(f"开始运行UI测试用例: {test_id}")
        
        test_case = self.framework.test_cases[test_id]
        result = await self.framework.run_single_test(test_case)
        
        logger.info(f"UI测试用例 {test_id} 执行完成: {result.status.value}")
        
        return result
    
    def get_ui_test_summary(self) -> Dict[str, Any]:
        """获取UI测试摘要信息"""
        if not self.ui_test_registry:
            return {"error": "UI测试注册器未初始化"}
        
        try:
            ui_tests = self.ui_test_registry.get_registered_tests()
            ui_suites = self.ui_test_registry.get_test_suites()
            
            # 按优先级统计测试用例
            priority_stats = {}
            for test_case in ui_tests.values():
                priority = test_case.priority.value
                priority_stats[priority] = priority_stats.get(priority, 0) + 1
            
            # 按分类统计测试用例
            category_stats = {}
            for test_case in ui_tests.values():
                category = test_case.category.value
                category_stats[category] = category_stats.get(category, 0) + 1
            
            # 按组件统计测试用例
            component_stats = {}
            for test_case in ui_tests.values():
                component = test_case.component
                component_stats[component] = component_stats.get(component, 0) + 1
            
            return {
                "total_tests": len(ui_tests),
                "total_suites": len(ui_suites),
                "priority_distribution": priority_stats,
                "category_distribution": category_stats,
                "component_distribution": component_stats,
                "test_suites": {
                    suite_id: {
                        "name": suite.name,
                        "test_count": len(suite.test_cases),
                        "parallel": suite.parallel
                    }
                    for suite_id, suite in ui_suites.items()
                },
                "available_tests": list(ui_tests.keys())
            }
            
        except Exception as e:
            logger.error(f"获取UI测试摘要失败: {str(e)}")
            return {"error": str(e)}
    
    def is_ui_test_available(self) -> bool:
        """检查UI测试是否可用"""
        return self.ui_test_registry is not None
    
    def get_ui_test_config(self) -> Dict[str, Any]:
        """获取UI测试配置"""
        if not self.ui_test_registry:
            return {}
        
        return self.ui_test_registry.config


class StagewiseUITestRunner:
    """Stagewise UI测试运行器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.framework = EnhancedStagewiseTestingFramework(self.config)
        self.ui_integration = UITestIntegration(self.framework)
    
    async def initialize(self) -> bool:
        """初始化测试运行器"""
        try:
            # 发现和注册UI测试
            result = self.ui_integration.discover_and_register_ui_tests()
            
            if result.get("success", False):
                logger.info(f"测试运行器初始化成功: "
                           f"{result['ui_tests_count']} 个测试用例, "
                           f"{result['ui_suites_count']} 个测试套件")
                return True
            else:
                logger.error(f"测试运行器初始化失败: {result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            logger.error(f"初始化测试运行器异常: {str(e)}")
            return False
    
    async def run_all_ui_tests(self) -> Dict[str, TestSession]:
        """运行所有UI测试套件"""
        if not self.ui_integration.is_ui_test_available():
            raise RuntimeError("UI测试不可用")
        
        ui_suites = self.ui_integration.ui_test_registry.get_test_suites()
        results = {}
        
        for suite_name in ui_suites.keys():
            try:
                session = await self.ui_integration.run_ui_test_suite(suite_name)
                results[suite_name] = session
                logger.info(f"测试套件 {suite_name}: "
                           f"{session.passed_tests}/{session.total_tests} 通过")
            except Exception as e:
                logger.error(f"运行测试套件 {suite_name} 失败: {str(e)}")
        
        return results
    
    async def run_ui_test_by_priority(self, priority: TestPriority) -> List[TestResult]:
        """按优先级运行UI测试"""
        if not self.ui_integration.is_ui_test_available():
            raise RuntimeError("UI测试不可用")
        
        ui_tests = self.ui_integration.ui_test_registry.get_registered_tests()
        priority_tests = [
            test for test in ui_tests.values() 
            if test.priority == priority
        ]
        
        results = []
        for test_case in priority_tests:
            try:
                result = await self.ui_integration.run_ui_test_case(test_case.test_id)
                results.append(result)
            except Exception as e:
                logger.error(f"运行测试用例 {test_case.test_id} 失败: {str(e)}")
        
        return results
    
    def get_test_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        return self.ui_integration.get_ui_test_summary()
    
    def generate_test_report(self, session: TestSession) -> str:
        """生成测试报告"""
        return self.framework.generate_test_report(session)


# 便捷函数
async def run_ui_tests(suite_name: Optional[str] = None, 
                      test_id: Optional[str] = None,
                      config: Optional[Dict[str, Any]] = None) -> Any:
    """运行UI测试的便捷函数"""
    runner = StagewiseUITestRunner(config)
    
    # 初始化
    if not await runner.initialize():
        raise RuntimeError("UI测试运行器初始化失败")
    
    if test_id:
        # 运行单个测试用例
        return await runner.ui_integration.run_ui_test_case(test_id)
    elif suite_name:
        # 运行指定测试套件
        return await runner.ui_integration.run_ui_test_suite(suite_name)
    else:
        # 运行所有测试套件
        return await runner.run_all_ui_tests()


def get_ui_test_summary(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """获取UI测试摘要的便捷函数"""
    runner = StagewiseUITestRunner(config)
    return runner.get_test_summary()


if __name__ == "__main__":
    # 命令行测试接口
    import argparse
    
    parser = argparse.ArgumentParser(description="Stagewise UI测试集成工具")
    parser.add_argument("--suite", help="要运行的测试套件名称")
    parser.add_argument("--test", help="要运行的测试用例ID")
    parser.add_argument("--summary", action="store_true", help="显示测试摘要")
    parser.add_argument("--all", action="store_true", help="运行所有UI测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    async def main():
        try:
            if args.summary:
                summary = get_ui_test_summary()
                print("📊 UI测试摘要:")
                print(f"  总测试用例: {summary.get('total_tests', 0)}")
                print(f"  总测试套件: {summary.get('total_suites', 0)}")
                print(f"  优先级分布: {summary.get('priority_distribution', {})}")
                print(f"  分类分布: {summary.get('category_distribution', {})}")
                
            elif args.all:
                runner = StagewiseUITestRunner()
                if await runner.initialize():
                    results = await runner.run_all_ui_tests()
                    print(f"✅ 运行了 {len(results)} 个测试套件")
                    for suite_name, session in results.items():
                        print(f"  {suite_name}: {session.passed_tests}/{session.total_tests} 通过")
                
            elif args.suite or args.test:
                result = await run_ui_tests(suite_name=args.suite, test_id=args.test)
                if args.test:
                    print(f"✅ 测试用例 {args.test}: {result.status.value}")
                else:
                    print(f"✅ 测试套件 {args.suite}: {result.passed_tests}/{result.total_tests} 通过")
                    
            else:
                print("请指定要执行的操作 (--summary, --all, --suite, --test)")
                
        except Exception as e:
            logger.error(f"执行失败: {str(e)}")
            sys.exit(1)
    
    asyncio.run(main())

