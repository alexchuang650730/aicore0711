#!/usr/bin/env python3
"""
PowerAutomation 4.0 统一测试管理器

提供统一的测试管理接口，整合所有测试相关功能：
- 测试用例管理
- 测试运行器管理
- 演示系统管理
- 集成测试管理
"""

import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试组件
from .testcases.tc_demo_tests import TCDemoTestSuite
from .ui_tests.test_basic_ui_operations import BasicUITestSuite
from .ui_tests.test_complex_ui_workflows import ComplexUIWorkflowTestSuite
from .ui_tests.test_responsive_ui import ResponsiveUITestSuite

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestType(Enum):
    """测试类型枚举"""
    UNIT = "unit"
    INTEGRATION = "integration"
    UI = "ui"
    E2E = "e2e"
    PERFORMANCE = "performance"
    DEMO = "demo"

class TestPriority(Enum):
    """测试优先级枚举"""
    P0 = "p0"  # 核心功能
    P1 = "p1"  # 重要功能
    P2 = "p2"  # 一般功能
    P3 = "p3"  # 边缘功能

class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestResult:
    """测试结果数据结构"""
    test_id: str
    test_name: str
    test_type: TestType
    priority: TestPriority
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

@dataclass
class TestSuiteResult:
    """测试套件结果"""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    test_results: List[TestResult] = None
    
    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []
        
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

class TestManager:
    """统一测试管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化测试管理器"""
        self.config = self._load_config(config_path)
        self.test_suites = {}
        self.test_results = []
        self.current_session = None
        
        # 设置输出目录
        self.output_dir = Path(self.config.get('output_dir', './test_results'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 注册测试套件
        self._register_test_suites()
        
        logger.info("测试管理器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "test_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"无法加载配置文件: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'output_dir': './test_results',
            'parallel_execution': True,
            'max_workers': 4,
            'timeout': 300,
            'retry_failed': True,
            'retry_count': 3,
            'generate_reports': True,
            'report_formats': ['html', 'json'],
            'cleanup_old_results': True,
            'cleanup_days': 30
        }
    
    def _register_test_suites(self):
        """注册所有测试套件"""
        
        # 演示测试套件
        self.test_suites['tc_demo'] = {
            'class': TCDemoTestSuite,
            'type': TestType.DEMO,
            'priority': TestPriority.P0,
            'description': '四个核心演示用例测试'
        }
        
        # UI测试套件
        self.test_suites['basic_ui'] = {
            'class': BasicUITestSuite,
            'type': TestType.UI,
            'priority': TestPriority.P0,
            'description': '基础UI操作测试'
        }
        
        self.test_suites['complex_ui'] = {
            'class': ComplexUIWorkflowTestSuite,
            'type': TestType.UI,
            'priority': TestPriority.P1,
            'description': '复杂UI工作流测试'
        }
        
        self.test_suites['responsive_ui'] = {
            'class': ResponsiveUITestSuite,
            'type': TestType.UI,
            'priority': TestPriority.P1,
            'description': '响应式UI测试'
        }
        
        logger.info(f"已注册 {len(self.test_suites)} 个测试套件")
    
    async def run_test_suite(self, suite_name: str, **kwargs) -> TestSuiteResult:
        """运行指定测试套件"""
        if suite_name not in self.test_suites:
            raise ValueError(f"测试套件不存在: {suite_name}")
        
        suite_config = self.test_suites[suite_name]
        suite_class = suite_config['class']
        
        logger.info(f"开始运行测试套件: {suite_name}")
        start_time = datetime.now()
        
        try:
            # 创建测试套件实例
            suite_instance = suite_class()
            
            # 运行测试
            if hasattr(suite_instance, 'run_all_tests'):
                results = await suite_instance.run_all_tests(**kwargs)
            else:
                results = await self._run_suite_methods(suite_instance)
            
            # 统计结果
            suite_result = self._create_suite_result(
                suite_name, results, start_time, datetime.now()
            )
            
            logger.info(f"测试套件完成: {suite_name}, 成功率: {suite_result.success_rate:.1f}%")
            return suite_result
            
        except Exception as e:
            logger.error(f"运行测试套件失败: {suite_name}, 错误: {e}")
            raise
    
    async def run_tests_by_priority(self, priority: TestPriority, **kwargs) -> List[TestSuiteResult]:
        """按优先级运行测试"""
        target_suites = [
            name for name, config in self.test_suites.items()
            if config['priority'] == priority
        ]
        
        logger.info(f"运行 {priority.value} 优先级测试，共 {len(target_suites)} 个套件")
        
        results = []
        for suite_name in target_suites:
            try:
                result = await self.run_test_suite(suite_name, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"测试套件 {suite_name} 运行失败: {e}")
        
        return results
    
    async def run_tests_by_type(self, test_type: TestType, **kwargs) -> List[TestSuiteResult]:
        """按类型运行测试"""
        target_suites = [
            name for name, config in self.test_suites.items()
            if config['type'] == test_type
        ]
        
        logger.info(f"运行 {test_type.value} 类型测试，共 {len(target_suites)} 个套件")
        
        results = []
        for suite_name in target_suites:
            try:
                result = await self.run_test_suite(suite_name, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"测试套件 {suite_name} 运行失败: {e}")
        
        return results
    
    async def run_all_tests(self, **kwargs) -> List[TestSuiteResult]:
        """运行所有测试"""
        logger.info(f"运行所有测试，共 {len(self.test_suites)} 个套件")
        
        results = []
        for suite_name in self.test_suites.keys():
            try:
                result = await self.run_test_suite(suite_name, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"测试套件 {suite_name} 运行失败: {e}")
        
        return results
    
    async def _run_suite_methods(self, suite_instance) -> List[TestResult]:
        """运行测试套件的所有测试方法"""
        results = []
        
        # 获取所有测试方法
        test_methods = [
            method for method in dir(suite_instance)
            if method.startswith('test_') and callable(getattr(suite_instance, method))
        ]
        
        for method_name in test_methods:
            start_time = datetime.now()
            
            try:
                method = getattr(suite_instance, method_name)
                
                # 运行测试方法
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
                
                # 创建成功结果
                result = TestResult(
                    test_id=f"{suite_instance.__class__.__name__}.{method_name}",
                    test_name=method_name,
                    test_type=TestType.UNIT,
                    priority=TestPriority.P1,
                    status=TestStatus.PASSED,
                    start_time=start_time,
                    end_time=datetime.now()
                )
                
            except Exception as e:
                # 创建失败结果
                result = TestResult(
                    test_id=f"{suite_instance.__class__.__name__}.{method_name}",
                    test_name=method_name,
                    test_type=TestType.UNIT,
                    priority=TestPriority.P1,
                    status=TestStatus.FAILED,
                    start_time=start_time,
                    end_time=datetime.now(),
                    error_message=str(e)
                )
                
                logger.error(f"测试方法失败: {method_name}, 错误: {e}")
            
            results.append(result)
        
        return results
    
    def _create_suite_result(self, suite_name: str, test_results: List[TestResult], 
                           start_time: datetime, end_time: datetime) -> TestSuiteResult:
        """创建测试套件结果"""
        
        # 统计各种状态的测试数量
        passed_count = len([r for r in test_results if r.status == TestStatus.PASSED])
        failed_count = len([r for r in test_results if r.status == TestStatus.FAILED])
        skipped_count = len([r for r in test_results if r.status == TestStatus.SKIPPED])
        error_count = len([r for r in test_results if r.status == TestStatus.ERROR])
        
        return TestSuiteResult(
            suite_name=suite_name,
            total_tests=len(test_results),
            passed_tests=passed_count,
            failed_tests=failed_count,
            skipped_tests=skipped_count,
            error_tests=error_count,
            start_time=start_time,
            end_time=end_time,
            test_results=test_results
        )
    
    def generate_report(self, results: List[TestSuiteResult], format: str = 'html') -> str:
        """生成测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'html':
            return self._generate_html_report(results, timestamp)
        elif format == 'json':
            return self._generate_json_report(results, timestamp)
        else:
            raise ValueError(f"不支持的报告格式: {format}")
    
    def _generate_html_report(self, results: List[TestSuiteResult], timestamp: str) -> str:
        """生成HTML报告"""
        report_file = self.output_dir / f"test_report_{timestamp}.html"
        
        # 计算总体统计
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        total_failed = sum(r.failed_tests for r in results)
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PowerAutomation 4.0 测试报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .suite-header {{ background: #e9e9e9; padding: 10px; font-weight: bold; }}
        .test-result {{ padding: 5px 10px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        .error {{ color: purple; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PowerAutomation 4.0 测试报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>总体成功率: {overall_success_rate:.1f}%</p>
    </div>
    
    <div class="summary">
        <h2>测试总结</h2>
        <table>
            <tr><th>指标</th><th>数量</th></tr>
            <tr><td>总测试数</td><td>{total_tests}</td></tr>
            <tr><td class="passed">通过</td><td>{total_passed}</td></tr>
            <tr><td class="failed">失败</td><td>{total_failed}</td></tr>
            <tr><td>成功率</td><td>{overall_success_rate:.1f}%</td></tr>
        </table>
    </div>
"""
        
        # 添加每个测试套件的详细信息
        for result in results:
            html_content += f"""
    <div class="suite">
        <div class="suite-header">
            {result.suite_name} - 成功率: {result.success_rate:.1f}%
            (通过: {result.passed_tests}, 失败: {result.failed_tests})
        </div>
"""
            
            for test_result in result.test_results:
                status_class = test_result.status.value
                html_content += f"""
        <div class="test-result {status_class}">
            {test_result.test_name} - {test_result.status.value.upper()}
            {f" - {test_result.error_message}" if test_result.error_message else ""}
        </div>
"""
            
            html_content += "    </div>\\n"
        
        html_content += """
</body>
</html>
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已生成: {report_file}")
        return str(report_file)
    
    def _generate_json_report(self, results: List[TestSuiteResult], timestamp: str) -> str:
        """生成JSON报告"""
        report_file = self.output_dir / f"test_report_{timestamp}.json"
        
        # 转换为可序列化的格式
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_suites': len(results),
                'total_tests': sum(r.total_tests for r in results),
                'total_passed': sum(r.passed_tests for r in results),
                'total_failed': sum(r.failed_tests for r in results),
                'overall_success_rate': sum(r.success_rate for r in results) / len(results) if results else 0
            },
            'suites': []
        }
        
        for result in results:
            suite_data = {
                'name': result.suite_name,
                'total_tests': result.total_tests,
                'passed_tests': result.passed_tests,
                'failed_tests': result.failed_tests,
                'skipped_tests': result.skipped_tests,
                'error_tests': result.error_tests,
                'success_rate': result.success_rate,
                'duration': result.duration,
                'tests': []
            }
            
            for test_result in result.test_results:
                test_data = {
                    'id': test_result.test_id,
                    'name': test_result.test_name,
                    'type': test_result.test_type.value,
                    'priority': test_result.priority.value,
                    'status': test_result.status.value,
                    'duration': test_result.duration,
                    'error_message': test_result.error_message,
                    'details': test_result.details
                }
                suite_data['tests'].append(test_data)
            
            report_data['suites'].append(suite_data)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON报告已生成: {report_file}")
        return str(report_file)
    
    def list_test_suites(self) -> Dict[str, Dict]:
        """列出所有测试套件"""
        return {
            name: {
                'type': config['type'].value,
                'priority': config['priority'].value,
                'description': config['description']
            }
            for name, config in self.test_suites.items()
        }
    
    def cleanup_old_results(self, days: int = 30):
        """清理旧的测试结果"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for file_path in self.output_dir.glob("test_report_*"):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                file_path.unlink()
                cleaned_count += 1
        
        logger.info(f"清理了 {cleaned_count} 个旧测试报告")
        return cleaned_count

# 全局测试管理器实例
_test_manager_instance = None

def get_test_manager() -> TestManager:
    """获取测试管理器实例（单例模式）"""
    global _test_manager_instance
    if _test_manager_instance is None:
        _test_manager_instance = TestManager()
    return _test_manager_instance

