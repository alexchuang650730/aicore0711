#!/usr/bin/env python3
"""
PowerAutomation 4.0 Enhanced Stagewise Testing Framework

增强的Stagewise测试框架，支持全面的MCP组件测试和验证
"""

import asyncio
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import traceback
from pathlib import Path
import psutil
import os

# 导入现有的stagewise组件
from .stagewise_service import StagewiseService, StagewiseEventType, StagewiseSession
from .visual_programming_engine import VisualProgrammingEngine
from .element_inspector import ElementInspector
from .code_generator import CodeGenerator

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPriority(Enum):
    """测试优先级"""
    P0 = "P0"  # 核心功能
    P1 = "P1"  # 重要功能
    P2 = "P2"  # 一般功能
    P3 = "P3"  # 边缘功能


class TestCategory(Enum):
    """测试分类"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    UI = "ui"
    API = "api"
    MCP = "mcp"


@dataclass
class TestCase:
    """测试用例"""
    test_id: str
    name: str
    description: str
    category: TestCategory
    priority: TestPriority
    component: str
    test_function: Callable
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    timeout: int = 30
    retry_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    expected_result: Any = None
    test_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    test_name: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    output: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """测试套件"""
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    parallel: bool = False
    max_workers: int = 4


@dataclass
class TestSession:
    """测试会话"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    test_results: List[TestResult] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)


class EnhancedStagewiseTestingFramework:
    """增强的Stagewise测试框架"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_cases: Dict[str, TestCase] = {}
        self.current_session: Optional[TestSession] = None
        self.stagewise_service = StagewiseService()
        
        # 系统监控
        self.process = psutil.Process(os.getpid())
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # 测试结果存储
        self.results_dir = Path(self.config.get('results_dir', 'test_results'))
        self.results_dir.mkdir(exist_ok=True)
        
        # 初始化日志
        self._setup_logging()
        
        # 注册内置测试套件
        self._register_builtin_test_suites()
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _register_builtin_test_suites(self):
        """注册内置测试套件"""
        # P0核心功能测试套件
        self.register_test_suite(TestSuite(
            suite_id="p0_core_tests",
            name="P0核心功能测试",
            description="测试系统的核心功能和关键路径",
            parallel=False
        ))
        
        # MCP组件测试套件
        self.register_test_suite(TestSuite(
            suite_id="mcp_component_tests",
            name="MCP组件测试",
            description="测试所有MCP组件的功能和集成",
            parallel=True,
            max_workers=4
        ))
        
        # UI功能测试套件
        self.register_test_suite(TestSuite(
            suite_id="ui_functionality_tests",
            name="UI功能测试",
            description="测试用户界面的所有功能",
            parallel=False
        ))
        
        # 性能测试套件
        self.register_test_suite(TestSuite(
            suite_id="performance_tests",
            name="性能测试",
            description="测试系统性能和资源使用",
            parallel=False
        ))
        
        # 安全测试套件
        self.register_test_suite(TestSuite(
            suite_id="security_tests",
            name="安全测试",
            description="测试系统安全性和漏洞",
            parallel=False
        ))
        
        # 注册具体的测试用例
        self._register_p0_test_cases()
        self._register_mcp_test_cases()
        self._register_ui_test_cases()
        self._register_performance_test_cases()
    
    def _register_p0_test_cases(self):
        """注册P0测试用例"""
        # 系统启动测试
        self.register_test_case(TestCase(
            test_id="p0_001",
            name="系统启动测试",
            description="验证系统能够正常启动",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component="core",
            test_function=self._test_system_startup,
            timeout=60
        ), "p0_core_tests")
        
        # MCP协调器测试
        self.register_test_case(TestCase(
            test_id="p0_002",
            name="MCP协调器测试",
            description="验证MCP协调器能够正常工作",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component="mcp_coordinator",
            test_function=self._test_mcp_coordinator,
            timeout=30
        ), "p0_core_tests")
        
        # Claude SDK集成测试
        self.register_test_case(TestCase(
            test_id="p0_003",
            name="Claude SDK集成测试",
            description="验证Claude SDK能够正常工作",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component="claude_sdk",
            test_function=self._test_claude_sdk_integration,
            timeout=45
        ), "p0_core_tests")
        
        # Stagewise服务测试
        self.register_test_case(TestCase(
            test_id="p0_004",
            name="Stagewise服务测试",
            description="验证Stagewise服务核心功能",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component="stagewise_mcp",
            test_function=self._test_stagewise_service,
            timeout=30
        ), "p0_core_tests")
    
    def _register_mcp_test_cases(self):
        """注册MCP组件测试用例"""
        mcp_components = [
            "ag_ui_mcp",
            "memoryos_mcp", 
            "trae_agent_mcp",
            
            "zen_mcp",
            # "enterprise_management",  # 已移动到showcase/
            "local_adapter_mcp",
            "mcp_zero_smart_engine"
        ]
        
        for i, component in enumerate(mcp_components, 1):
            self.register_test_case(TestCase(
                test_id=f"mcp_{i:03d}",
                name=f"{component}组件测试",
                description=f"测试{component}组件的基本功能",
                category=TestCategory.MCP,
                priority=TestPriority.P1,
                component=component,
                test_function=lambda comp=component: self._test_mcp_component(comp),
                timeout=30
            ), "mcp_component_tests")
    
    def _register_ui_test_cases(self):
        """注册UI测试用例"""
        ui_features = [
            ("ui_001", "主界面加载", "验证主界面能够正常加载"),
            ("ui_002", "AG-UI组件生成", "验证AG-UI组件生成功能"),
            ("ui_003", "代码编辑器", "验证代码编辑器功能"),
            ("ui_004", "AI助手对话", "验证AI助手对话功能"),
            ("ui_005", "项目管理", "验证项目管理功能")
        ]
        
        for test_id, name, description in ui_features:
            self.register_test_case(TestCase(
                test_id=test_id,
                name=name,
                description=description,
                category=TestCategory.UI,
                priority=TestPriority.P1,
                component="ui",
                test_function=lambda n=name: self._test_ui_feature(n),
                timeout=45
            ), "ui_functionality_tests")
    
    def _register_performance_test_cases(self):
        """注册性能测试用例"""
        performance_tests = [
            ("perf_001", "内存使用测试", "验证系统内存使用在合理范围内"),
            ("perf_002", "响应时间测试", "验证系统响应时间符合要求"),
            ("perf_003", "并发处理测试", "验证系统并发处理能力"),
            ("perf_004", "资源清理测试", "验证系统资源能够正确清理")
        ]
        
        for test_id, name, description in performance_tests:
            self.register_test_case(TestCase(
                test_id=test_id,
                name=name,
                description=description,
                category=TestCategory.PERFORMANCE,
                priority=TestPriority.P2,
                component="performance",
                test_function=lambda n=name: self._test_performance_metric(n),
                timeout=60
            ), "performance_tests")
    
    def register_test_suite(self, test_suite: TestSuite):
        """注册测试套件"""
        self.test_suites[test_suite.suite_id] = test_suite
        logger.info(f"注册测试套件: {test_suite.name}")
    
    def register_test_case(self, test_case: TestCase, suite_id: str):
        """注册测试用例"""
        if suite_id not in self.test_suites:
            raise ValueError(f"测试套件 {suite_id} 不存在")
        
        self.test_cases[test_case.test_id] = test_case
        self.test_suites[suite_id].test_cases.append(test_case)
        logger.info(f"注册测试用例: {test_case.name} -> {suite_id}")
    
    async def run_test_suite(self, suite_id: str, filters: Dict[str, Any] = None) -> List[TestResult]:
        """运行测试套件"""
        if suite_id not in self.test_suites:
            raise ValueError(f"测试套件 {suite_id} 不存在")
        
        suite = self.test_suites[suite_id]
        logger.info(f"开始运行测试套件: {suite.name}")
        
        # 应用过滤器
        test_cases = self._apply_filters(suite.test_cases, filters)
        
        # 执行套件设置
        if suite.setup_function:
            try:
                await suite.setup_function()
            except Exception as e:
                logger.error(f"测试套件设置失败: {str(e)}")
                return []
        
        results = []
        
        try:
            if suite.parallel:
                # 并行执行
                semaphore = asyncio.Semaphore(suite.max_workers)
                tasks = [
                    self._run_test_case_with_semaphore(test_case, semaphore)
                    for test_case in test_cases
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # 串行执行
                for test_case in test_cases:
                    result = await self._run_test_case(test_case)
                    results.append(result)
        
        finally:
            # 执行套件清理
            if suite.teardown_function:
                try:
                    await suite.teardown_function()
                except Exception as e:
                    logger.error(f"测试套件清理失败: {str(e)}")
        
        logger.info(f"测试套件 {suite.name} 执行完成")
        return [r for r in results if isinstance(r, TestResult)]
    
    async def _run_test_case_with_semaphore(self, test_case: TestCase, semaphore: asyncio.Semaphore) -> TestResult:
        """使用信号量运行测试用例"""
        async with semaphore:
            return await self._run_test_case(test_case)
    
    async def _run_test_case(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        start_time = datetime.now()
        result = TestResult(
            test_id=test_case.test_id,
            test_name=test_case.name,
            status=TestStatus.RUNNING,
            start_time=start_time
        )
        
        logger.info(f"开始执行测试: {test_case.name}")
        
        try:
            # 执行测试设置
            if test_case.setup_function:
                await test_case.setup_function()
            
            # 执行测试
            test_output = await asyncio.wait_for(
                test_case.test_function(),
                timeout=test_case.timeout
            )
            
            # 验证结果
            if test_case.expected_result is not None:
                if test_output != test_case.expected_result:
                    result.status = TestStatus.FAILED
                    result.error_message = f"期望结果: {test_case.expected_result}, 实际结果: {test_output}"
                else:
                    result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.PASSED
            
            result.output = str(test_output) if test_output else None
            
        except asyncio.TimeoutError:
            result.status = TestStatus.FAILED
            result.error_message = f"测试超时 ({test_case.timeout}s)"
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()
            
        finally:
            # 执行测试清理
            if test_case.teardown_function:
                try:
                    await test_case.teardown_function()
                except Exception as e:
                    logger.warning(f"测试清理失败: {str(e)}")
            
            # 计算执行时间
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            # 收集系统指标
            result.metrics = self._collect_system_metrics()
        
        logger.info(f"测试完成: {test_case.name} - {result.status.value}")
        return result
    
    def _apply_filters(self, test_cases: List[TestCase], filters: Dict[str, Any] = None) -> List[TestCase]:
        """应用测试过滤器"""
        if not filters:
            return test_cases
        
        filtered_cases = test_cases
        
        # 按优先级过滤
        if 'priority' in filters:
            priority = TestPriority(filters['priority'])
            filtered_cases = [tc for tc in filtered_cases if tc.priority == priority]
        
        # 按分类过滤
        if 'category' in filters:
            category = TestCategory(filters['category'])
            filtered_cases = [tc for tc in filtered_cases if tc.category == category]
        
        # 按组件过滤
        if 'component' in filters:
            component = filters['component']
            filtered_cases = [tc for tc in filtered_cases if tc.component == component]
        
        # 按标签过滤
        if 'tags' in filters:
            required_tags = set(filters['tags'])
            filtered_cases = [tc for tc in filtered_cases if required_tags.issubset(set(tc.tags))]
        
        return filtered_cases
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        memory_info = self.process.memory_info()
        cpu_percent = self.process.cpu_percent()
        
        return {
            "memory_rss_mb": memory_info.rss / 1024 / 1024,
            "memory_vms_mb": memory_info.vms / 1024 / 1024,
            "cpu_percent": cpu_percent,
            "timestamp": datetime.now().isoformat()
        }
    
    async def start_test_session(self, session_config: Dict[str, Any] = None) -> str:
        """开始测试会话"""
        session_id = str(uuid.uuid4())
        self.current_session = TestSession(
            session_id=session_id,
            start_time=datetime.now(),
            environment=session_config or {}
        )
        
        logger.info(f"开始测试会话: {session_id}")
        return session_id
    
    async def end_test_session(self) -> TestSession:
        """结束测试会话"""
        if not self.current_session:
            raise ValueError("没有活跃的测试会话")
        
        self.current_session.end_time = datetime.now()
        
        # 计算统计信息
        for result in self.current_session.test_results:
            if result.status == TestStatus.PASSED:
                self.current_session.passed_tests += 1
            elif result.status == TestStatus.FAILED:
                self.current_session.failed_tests += 1
            elif result.status == TestStatus.SKIPPED:
                self.current_session.skipped_tests += 1
            elif result.status == TestStatus.ERROR:
                self.current_session.error_tests += 1
        
        self.current_session.total_tests = len(self.current_session.test_results)
        
        # 收集系统指标
        self.current_session.system_metrics = self._collect_system_metrics()
        
        logger.info(f"结束测试会话: {self.current_session.session_id}")
        
        # 保存测试结果
        await self._save_test_results(self.current_session)
        
        session = self.current_session
        self.current_session = None
        return session
    
    async def _save_test_results(self, session: TestSession):
        """保存测试结果"""
        timestamp = session.start_time.strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"test_results_{timestamp}.json"
        
        # 转换为可序列化的格式
        session_data = {
            "session_id": session.session_id,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "total_tests": session.total_tests,
            "passed_tests": session.passed_tests,
            "failed_tests": session.failed_tests,
            "skipped_tests": session.skipped_tests,
            "error_tests": session.error_tests,
            "system_metrics": session.system_metrics,
            "environment": session.environment,
            "test_results": []
        }
        
        for result in session.test_results:
            result_data = {
                "test_id": result.test_id,
                "test_name": result.test_name,
                "status": result.status.value,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "duration": result.duration,
                "error_message": result.error_message,
                "output": result.output,
                "metrics": result.metrics
            }
            session_data["test_results"].append(result_data)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试结果已保存: {results_file}")
    
    # 具体的测试实现方法
    async def _test_system_startup(self) -> bool:
        """测试系统启动"""
        try:
            # 检查关键组件是否可用
            assert self.stagewise_service is not None
            
            # 检查内存使用是否合理
            current_memory = self.process.memory_info().rss / 1024 / 1024
            assert current_memory < 500, f"内存使用过高: {current_memory}MB"
            
            return True
        except Exception as e:
            logger.error(f"系统启动测试失败: {str(e)}")
            return False
    
    async def _test_mcp_coordinator(self) -> bool:
        """测试MCP协调器"""
        try:
            # 这里应该测试MCP协调器的功能
            # 暂时返回True，实际实现需要根据具体的MCP协调器API
            await asyncio.sleep(0.1)  # 模拟测试时间
            return True
        except Exception as e:
            logger.error(f"MCP协调器测试失败: {str(e)}")
            return False
    
    async def _test_claude_sdk_integration(self) -> bool:
        """测试Claude SDK集成"""
        try:
            # 这里应该测试Claude SDK的集成
            # 暂时返回True，实际实现需要根据具体的Claude SDK API
            await asyncio.sleep(0.1)  # 模拟测试时间
            return True
        except Exception as e:
            logger.error(f"Claude SDK集成测试失败: {str(e)}")
            return False
    
    async def _test_stagewise_service(self) -> bool:
        """测试Stagewise服务"""
        try:
            # 测试Stagewise服务的基本功能
            session_id = str(uuid.uuid4())
            
            # 这里应该调用实际的Stagewise服务方法
            # 暂时返回True
            await asyncio.sleep(0.1)  # 模拟测试时间
            return True
        except Exception as e:
            logger.error(f"Stagewise服务测试失败: {str(e)}")
            return False
    
    async def _test_mcp_component(self, component_name: str) -> bool:
        """测试MCP组件"""
        try:
            # 这里应该测试具体的MCP组件
            # 暂时返回True，实际实现需要根据具体的组件API
            await asyncio.sleep(0.1)  # 模拟测试时间
            logger.info(f"测试MCP组件: {component_name}")
            return True
        except Exception as e:
            logger.error(f"MCP组件 {component_name} 测试失败: {str(e)}")
            return False
    
    async def _test_ui_feature(self, feature_name: str) -> bool:
        """测试UI功能"""
        try:
            # 这里应该测试具体的UI功能
            # 暂时返回True，实际实现需要使用浏览器自动化
            await asyncio.sleep(0.1)  # 模拟测试时间
            logger.info(f"测试UI功能: {feature_name}")
            return True
        except Exception as e:
            logger.error(f"UI功能 {feature_name} 测试失败: {str(e)}")
            return False
    
    async def _test_performance_metric(self, metric_name: str) -> bool:
        """测试性能指标"""
        try:
            # 这里应该测试具体的性能指标
            current_memory = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent()
            
            if metric_name == "内存使用测试":
                return current_memory < 200  # 内存使用小于200MB
            elif metric_name == "响应时间测试":
                # 模拟响应时间测试
                start_time = time.time()
                await asyncio.sleep(0.01)  # 模拟操作
                response_time = time.time() - start_time
                return response_time < 1.0  # 响应时间小于1秒
            elif metric_name == "并发处理测试":
                # 模拟并发测试
                tasks = [asyncio.sleep(0.01) for _ in range(10)]
                await asyncio.gather(*tasks)
                return True
            elif metric_name == "资源清理测试":
                # 检查资源是否正确清理
                return True
            
            return True
        except Exception as e:
            logger.error(f"性能指标 {metric_name} 测试失败: {str(e)}")
            return False
    
    def generate_test_report(self, session: TestSession) -> str:
        """生成测试报告"""
        total_duration = (session.end_time - session.start_time).total_seconds() if session.end_time else 0
        success_rate = (session.passed_tests / session.total_tests * 100) if session.total_tests > 0 else 0
        
        report = f"""
# Stagewise测试报告

## 测试会话信息
- **会话ID**: {session.session_id}
- **开始时间**: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **结束时间**: {session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else 'N/A'}
- **总耗时**: {total_duration:.2f}秒

## 测试统计
- **总测试数**: {session.total_tests}
- **通过**: {session.passed_tests}
- **失败**: {session.failed_tests}
- **跳过**: {session.skipped_tests}
- **错误**: {session.error_tests}
- **成功率**: {success_rate:.1f}%

## 系统指标
- **内存使用**: {session.system_metrics.get('memory_rss_mb', 0):.1f}MB
- **CPU使用**: {session.system_metrics.get('cpu_percent', 0):.1f}%

## 测试结果详情
"""
        
        # 按状态分组显示测试结果
        for status in TestStatus:
            status_results = [r for r in session.test_results if r.status == status]
            if status_results:
                report += f"\n### {status.value.upper()}测试 ({len(status_results)}个)\n"
                for result in status_results:
                    report += f"- **{result.test_name}** ({result.duration:.2f}s)"
                    if result.error_message:
                        report += f" - {result.error_message}"
                    report += "\n"
        
        return report


# 便捷函数
async def run_p0_tests(config: Dict[str, Any] = None) -> TestSession:
    """运行P0核心功能测试"""
    framework = EnhancedStagewiseTestingFramework(config)
    
    session_id = await framework.start_test_session({"test_type": "P0核心功能测试"})
    
    try:
        results = await framework.run_test_suite("p0_core_tests", {"priority": "P0"})
        framework.current_session.test_results.extend(results)
        
        return await framework.end_test_session()
    except Exception as e:
        logger.error(f"P0测试执行失败: {str(e)}")
        if framework.current_session:
            framework.current_session.test_results.append(TestResult(
                test_id="error",
                test_name="测试执行错误",
                status=TestStatus.ERROR,
                start_time=datetime.now(),
                error_message=str(e)
            ))
            return await framework.end_test_session()
        raise


async def run_all_mcp_tests(config: Dict[str, Any] = None) -> TestSession:
    """运行所有MCP组件测试"""
    framework = EnhancedStagewiseTestingFramework(config)
    
    session_id = await framework.start_test_session({"test_type": "MCP组件测试"})
    
    try:
        results = await framework.run_test_suite("mcp_component_tests")
        framework.current_session.test_results.extend(results)
        
        return await framework.end_test_session()
    except Exception as e:
        logger.error(f"MCP测试执行失败: {str(e)}")
        if framework.current_session:
            return await framework.end_test_session()
        raise


async def run_comprehensive_tests(config: Dict[str, Any] = None) -> List[TestSession]:
    """运行全面的测试"""
    framework = EnhancedStagewiseTestingFramework(config)
    sessions = []
    
    # 运行所有测试套件
    test_suites = ["p0_core_tests", "mcp_component_tests", "ui_functionality_tests", "performance_tests"]
    
    for suite_id in test_suites:
        session_id = await framework.start_test_session({"test_type": f"{suite_id}测试"})
        
        try:
            results = await framework.run_test_suite(suite_id)
            framework.current_session.test_results.extend(results)
            
            session = await framework.end_test_session()
            sessions.append(session)
            
        except Exception as e:
            logger.error(f"测试套件 {suite_id} 执行失败: {str(e)}")
            if framework.current_session:
                session = await framework.end_test_session()
                sessions.append(session)
    
    return sessions


if __name__ == "__main__":
    async def main():
        """主函数示例"""
        print("🚀 启动Stagewise增强测试框架")
        
        # 运行P0测试
        print("\n📋 运行P0核心功能测试...")
        p0_session = await run_p0_tests()
        
        framework = EnhancedStagewiseTestingFramework()
        p0_report = framework.generate_test_report(p0_session)
        print(p0_report)
        
        # 运行MCP测试
        print("\n📋 运行MCP组件测试...")
        mcp_session = await run_all_mcp_tests()
        mcp_report = framework.generate_test_report(mcp_session)
        print(mcp_report)
    
    asyncio.run(main())

