#!/usr/bin/env python3
"""
UI测试注册器

负责将test/目录下的UI测试用例注册到Stagewise测试框架中，
使框架能够自动发现和执行这些测试。
"""

import os
import sys
import yaml
import importlib
import inspect
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.components.stagewise_mcp.enhanced_testing_framework import (
    EnhancedStagewiseTestingFramework,
    TestCase, TestSuite, TestPriority, TestCategory
)

logger = logging.getLogger(__name__)


class UITestRegistry:
    """UI测试注册器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "test/config/ui_test_config.yaml"
        self.config = self._load_config()
        self.framework = EnhancedStagewiseTestingFramework(self.config)
        self.registered_tests = {}
        self.test_modules = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """加载测试配置"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "test_environment": {
                "base_url": "http://localhost:3000",
                "timeout": 30
            },
            "stagewise_integration": {
                "enabled": True,
                "auto_discovery": True,
                "test_case_pattern": "test_*.py",
                "test_function_pattern": "test_*",
                "auto_register_tests": True
            },
            "test_suites": {
                "basic_ui_operations": {"enabled": True, "priority": "P0"},
                "complex_ui_workflows": {"enabled": True, "priority": "P1"},
                "responsive_ui": {"enabled": True, "priority": "P1"}
            }
        }
    
    def discover_and_register_tests(self) -> Dict[str, Any]:
        """发现并注册所有UI测试"""
        logger.info("开始发现和注册UI测试...")
        
        # 发现测试模块
        test_modules = self._discover_test_modules()
        
        # 注册测试用例
        registered_count = 0
        for module_name, module in test_modules.items():
            try:
                test_cases = self._extract_test_cases_from_module(module)
                for test_case in test_cases:
                    self._register_test_case(test_case)
                    registered_count += 1
                
                logger.info(f"从模块 {module_name} 注册了 {len(test_cases)} 个测试用例")
                
            except Exception as e:
                logger.error(f"注册模块 {module_name} 的测试用例失败: {str(e)}")
        
        # 创建测试套件
        self._create_test_suites()
        
        logger.info(f"测试发现和注册完成，共注册 {registered_count} 个测试用例")
        
        return {
            "total_tests": registered_count,
            "modules": list(test_modules.keys()),
            "suites": list(self.framework.test_suites.keys()),
            "config": self.config
        }
    
    def _discover_test_modules(self) -> Dict[str, Any]:
        """发现测试模块"""
        test_modules = {}
        test_dir = Path("test/ui_tests")
        
        if not test_dir.exists():
            logger.warning(f"测试目录不存在: {test_dir}")
            return test_modules
        
        # 查找所有测试文件
        pattern = self.config.get("stagewise_integration", {}).get("test_case_pattern", "test_*.py")
        test_files = list(test_dir.glob(pattern))
        
        for test_file in test_files:
            if test_file.name == "__init__.py":
                continue
                
            try:
                # 构建模块名
                module_name = f"test.ui_tests.{test_file.stem}"
                
                # 导入模块
                module = importlib.import_module(module_name)
                test_modules[module_name] = module
                
                logger.debug(f"发现测试模块: {module_name}")
                
            except Exception as e:
                logger.error(f"导入测试模块 {test_file} 失败: {str(e)}")
        
        return test_modules
    
    def _extract_test_cases_from_module(self, module) -> List[TestCase]:
        """从模块中提取测试用例"""
        test_cases = []
        
        # 查找模块中的测试用例创建函数
        for name, obj in inspect.getmembers(module):
            if name.startswith("create_") and name.endswith("_test_cases") and callable(obj):
                try:
                    # 调用函数获取测试用例列表
                    cases = obj()
                    if isinstance(cases, list):
                        test_cases.extend(cases)
                        logger.debug(f"从函数 {name} 提取了 {len(cases)} 个测试用例")
                except Exception as e:
                    logger.error(f"调用测试用例创建函数 {name} 失败: {str(e)}")
        
        return test_cases
    
    def _register_test_case(self, test_case: TestCase):
        """注册单个测试用例"""
        # 检查测试用例是否已注册
        if test_case.test_id in self.registered_tests:
            logger.warning(f"测试用例 {test_case.test_id} 已存在，跳过注册")
            return
        
        # 注册到框架
        self.framework.test_cases[test_case.test_id] = test_case
        self.registered_tests[test_case.test_id] = test_case
        
        logger.debug(f"注册测试用例: {test_case.test_id} - {test_case.name}")
    
    def _create_test_suites(self):
        """创建测试套件"""
        suite_configs = self.config.get("test_suites", {})
        
        for suite_name, suite_config in suite_configs.items():
            if not suite_config.get("enabled", True):
                continue
            
            # 根据组件或标签筛选测试用例
            suite_tests = self._filter_tests_for_suite(suite_name, suite_config)
            
            if suite_tests:
                test_suite = TestSuite(
                    suite_id=suite_name,
                    name=suite_config.get("name", suite_name.replace("_", " ").title()),
                    description=suite_config.get("description", f"{suite_name} 测试套件"),
                    test_cases=suite_tests,
                    parallel=suite_config.get("parallel", False),
                    max_workers=suite_config.get("max_workers", 4)
                )
                
                self.framework.register_test_suite(test_suite)
                logger.info(f"创建测试套件: {suite_name} ({len(suite_tests)} 个测试)")
    
    def _filter_tests_for_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> List[TestCase]:
        """为测试套件筛选测试用例"""
        filtered_tests = []
        
        # 根据套件名称匹配测试用例
        for test_case in self.registered_tests.values():
            should_include = False
            
            # 根据组件名匹配
            if suite_name == "basic_ui_operations" and test_case.component == "ui_operations":
                should_include = True
            elif suite_name == "complex_ui_workflows" and test_case.component in ["user_authentication", "form_handling", "ecommerce"]:
                should_include = True
            elif suite_name == "responsive_ui" and test_case.component in ["navigation", "layout", "forms", "media"]:
                should_include = True
            
            # 根据标签匹配
            if not should_include and "tags" in suite_config:
                required_tags = suite_config["tags"]
                if any(tag in test_case.tags for tag in required_tags):
                    should_include = True
            
            # 根据优先级匹配
            if not should_include and "priority" in suite_config:
                if test_case.priority.value == suite_config["priority"]:
                    should_include = True
            
            if should_include:
                filtered_tests.append(test_case)
        
        return filtered_tests
    
    def get_registered_tests(self) -> Dict[str, TestCase]:
        """获取已注册的测试用例"""
        return self.registered_tests.copy()
    
    def get_test_suites(self) -> Dict[str, TestSuite]:
        """获取测试套件"""
        return self.framework.test_suites.copy()
    
    def run_test_suite(self, suite_name: str) -> Any:
        """运行指定的测试套件"""
        if suite_name not in self.framework.test_suites:
            raise ValueError(f"测试套件不存在: {suite_name}")
        
        logger.info(f"开始运行测试套件: {suite_name}")
        return asyncio.run(self.framework.run_test_suite(suite_name))
    
    def run_test_case(self, test_id: str) -> Any:
        """运行指定的测试用例"""
        if test_id not in self.registered_tests:
            raise ValueError(f"测试用例不存在: {test_id}")
        
        logger.info(f"开始运行测试用例: {test_id}")
        test_case = self.registered_tests[test_id]
        return asyncio.run(self.framework.run_single_test(test_case))
    
    def generate_test_report(self) -> str:
        """生成测试报告"""
        if not self.framework.current_session:
            return "没有可用的测试会话数据"
        
        return self.framework.generate_test_report(self.framework.current_session)


# 全局注册器实例
_ui_test_registry = None


def get_ui_test_registry(config_path: Optional[str] = None) -> UITestRegistry:
    """获取UI测试注册器实例"""
    global _ui_test_registry
    if _ui_test_registry is None:
        _ui_test_registry = UITestRegistry(config_path)
    return _ui_test_registry


def register_ui_tests(config_path: Optional[str] = None) -> Dict[str, Any]:
    """注册所有UI测试（便捷函数）"""
    registry = get_ui_test_registry(config_path)
    return registry.discover_and_register_tests()


def run_ui_test_suite(suite_name: str, config_path: Optional[str] = None) -> Any:
    """运行UI测试套件（便捷函数）"""
    registry = get_ui_test_registry(config_path)
    return registry.run_test_suite(suite_name)


def run_ui_test_case(test_id: str, config_path: Optional[str] = None) -> Any:
    """运行UI测试用例（便捷函数）"""
    registry = get_ui_test_registry(config_path)
    return registry.run_test_case(test_id)


if __name__ == "__main__":
    # 命令行接口
    import argparse
    
    parser = argparse.ArgumentParser(description="UI测试注册和执行工具")
    parser.add_argument("action", choices=["register", "run-suite", "run-case", "list"], 
                       help="要执行的操作")
    parser.add_argument("--target", help="测试套件名称或测试用例ID")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        registry = get_ui_test_registry(args.config)
        
        if args.action == "register":
            result = registry.discover_and_register_tests()
            print(f"✅ 注册完成: {result['total_tests']} 个测试用例")
            print(f"📁 测试模块: {', '.join(result['modules'])}")
            print(f"📋 测试套件: {', '.join(result['suites'])}")
            
        elif args.action == "run-suite":
            if not args.target:
                print("❌ 请指定要运行的测试套件名称 (--target)")
                sys.exit(1)
            
            # 先注册测试
            registry.discover_and_register_tests()
            
            # 运行测试套件
            results = registry.run_test_suite(args.target)
            print(f"✅ 测试套件 {args.target} 执行完成")
            
        elif args.action == "run-case":
            if not args.target:
                print("❌ 请指定要运行的测试用例ID (--target)")
                sys.exit(1)
            
            # 先注册测试
            registry.discover_and_register_tests()
            
            # 运行测试用例
            result = registry.run_test_case(args.target)
            print(f"✅ 测试用例 {args.target} 执行完成")
            
        elif args.action == "list":
            # 先注册测试
            registry.discover_and_register_tests()
            
            # 列出所有测试
            tests = registry.get_registered_tests()
            suites = registry.get_test_suites()
            
            print(f"\n📋 已注册的测试套件 ({len(suites)} 个):")
            for suite_name, suite in suites.items():
                print(f"  - {suite_name}: {suite.name} ({len(suite.test_cases)} 个测试)")
            
            print(f"\n🧪 已注册的测试用例 ({len(tests)} 个):")
            for test_id, test_case in tests.items():
                print(f"  - {test_id}: {test_case.name} [{test_case.priority.value}]")
    
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)

