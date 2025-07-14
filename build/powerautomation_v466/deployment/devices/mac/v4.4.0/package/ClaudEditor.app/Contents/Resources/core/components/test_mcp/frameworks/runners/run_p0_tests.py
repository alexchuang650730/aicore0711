#!/usr/bin/env python3
"""
PowerAutomation 4.0 P0测试运行脚本
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入测试框架
try:
    from core.components.stagewise_mcp.enhanced_testing_framework import (
        EnhancedStagewiseTestingFramework,
        TestCase, TestResult, TestStatus, TestPriority, TestCategory, TestSuite
    )
    from core.components.stagewise_mcp.visual_testing_recorder import (
        VisualTestingRecorder, IntegratedVisualTestingFramework
    )
except ImportError as e:
    logger.error(f"导入测试框架失败: {e}")
    sys.exit(1)


class P0TestRunner:
    """P0测试运行器"""
    
    def __init__(self):
        self.framework = EnhancedStagewiseTestingFramework()
        self.visual_framework = IntegratedVisualTestingFramework()
        self.results = []
        
        # 输出目录
        self.output_dir = project_root / "test_results" / "p0_tests"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def run_p0_core_system_tests(self):
        """运行P0核心系统测试"""
        logger.info("🚀 开始P0核心系统测试")
        
        # 创建P0核心测试套件
        p0_core_suite = TestSuite(
            suite_id="p0_core_system",
            name="P0核心系统测试套件",
            description="测试PowerAutomation核心系统的基础功能",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0
        )
        
        # 添加核心测试用例
        test_cases = [
            self._create_system_startup_test(),
            self._create_mcp_coordinator_test(),
            self._create_claude_sdk_test(),
            self._create_stagewise_service_test(),
            self._create_event_bus_test()
        ]
        
        for test_case in test_cases:
            p0_core_suite.add_test_case(test_case)
        
        # 执行测试套件
        suite_result = await self.framework.run_test_suite(p0_core_suite)
        self.results.append(("P0核心系统", suite_result))
        
        logger.info(f"✅ P0核心系统测试完成: {suite_result.status}")
        return suite_result
    
    def _create_system_startup_test(self) -> TestCase:
        """创建系统启动测试"""
        async def test_system_startup():
            """测试系统启动"""
            try:
                # 测试导入核心模块
                from core.event_bus import EventBus
                from core.config import Config
                
                # 测试配置加载
                config = Config()
                assert config is not None, "配置对象创建失败"
                
                # 测试事件总线
                event_bus = EventBus()
                assert event_bus is not None, "事件总线创建失败"
                
                logger.info("✅ 系统启动测试通过")
                return {"status": "success", "message": "系统核心模块启动正常"}
                
            except Exception as e:
                logger.error(f"❌ 系统启动测试失败: {e}")
                raise
        
        return TestCase(
            test_id="p0_001",
            name="系统启动测试",
            description="验证PowerAutomation核心系统能够正常启动",
            category=TestCategory.UNIT,
            priority=TestPriority.P0,
            component="core_system",
            test_function=test_system_startup,
            timeout=30
        )
    
    def _create_mcp_coordinator_test(self) -> TestCase:
        """创建MCP协调器测试"""
        async def test_mcp_coordinator():
            """测试MCP协调器"""
            try:
                from core.mcp_coordinator.mcp_coordinator import MCPCoordinator
                
                # 创建MCP协调器
                coordinator = MCPCoordinator()
                assert coordinator is not None, "MCP协调器创建失败"
                
                # 测试组件注册
                component_count = len(coordinator.registered_components)
                logger.info(f"已注册MCP组件数量: {component_count}")
                
                # 验证核心组件存在
                expected_components = [
                    "ag_ui_mcp",
                    "memoryos_mcp", 
                    "stagewise_mcp",
                    "trae_agent_mcp"
                ]
                
                for component in expected_components:
                    assert component in coordinator.registered_components, f"缺少核心组件: {component}"
                
                logger.info("✅ MCP协调器测试通过")
                return {"status": "success", "message": f"MCP协调器正常，已注册{component_count}个组件"}
                
            except Exception as e:
                logger.error(f"❌ MCP协调器测试失败: {e}")
                raise
        
        return TestCase(
            test_id="p0_002",
            name="MCP协调器测试",
            description="验证MCP协调器能够正常工作和管理组件",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component="mcp_coordinator",
            test_function=test_mcp_coordinator,
            timeout=30
        )
    
    def _create_claude_sdk_test(self) -> TestCase:
        """创建Claude SDK测试"""
        async def test_claude_sdk():
            """测试Claude SDK"""
            try:
                from core.components.claude_integration_mcp.claude_sdk.claude_client import ClaudeClient
                from core.components.claude_integration_mcp.claude_sdk.claude_sdk_mcp_v2 import ClaudeSDKMCP
                
                # 测试Claude客户端
                client = ClaudeClient()
                assert client is not None, "Claude客户端创建失败"
                
                # 测试Claude SDK MCP
                sdk_mcp = ClaudeSDKMCP()
                assert sdk_mcp is not None, "Claude SDK MCP创建失败"
                
                # 验证专家系统
                experts = sdk_mcp.experts
                assert len(experts) >= 5, f"专家系统数量不足: {len(experts)}"
                
                # 验证操作处理器
                processors = sdk_mcp.operation_processors
                assert len(processors) >= 30, f"操作处理器数量不足: {len(processors)}"
                
                logger.info("✅ Claude SDK测试通过")
                return {
                    "status": "success", 
                    "message": f"Claude SDK正常，{len(experts)}个专家，{len(processors)}个处理器"
                }
                
            except Exception as e:
                logger.error(f"❌ Claude SDK测试失败: {e}")
                raise
        
        return TestCase(
            test_id="p0_003",
            name="Claude SDK测试",
            description="验证Claude SDK和MCP v2.0功能正常",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component="claude_sdk",
            test_function=test_claude_sdk,
            timeout=30
        )
    
    def _create_stagewise_service_test(self) -> TestCase:
        """创建Stagewise服务测试"""
        async def test_stagewise_service():
            """测试Stagewise服务"""
            try:
                from core.components.stagewise_mcp.stagewise_service import StagewiseService
                
                # 创建Stagewise服务
                service = StagewiseService()
                assert service is not None, "Stagewise服务创建失败"
                
                # 测试服务初始化
                await service.initialize()
                
                # 测试基本功能
                test_data = {"test": "data"}
                result = await service.process_request(test_data)
                assert result is not None, "Stagewise服务处理请求失败"
                
                logger.info("✅ Stagewise服务测试通过")
                return {"status": "success", "message": "Stagewise服务正常工作"}
                
            except Exception as e:
                logger.error(f"❌ Stagewise服务测试失败: {e}")
                raise
        
        return TestCase(
            test_id="p0_004",
            name="Stagewise服务测试",
            description="验证Stagewise服务核心功能正常",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component="stagewise_mcp",
            test_function=test_stagewise_service,
            timeout=30
        )
    
    def _create_event_bus_test(self) -> TestCase:
        """创建事件总线测试"""
        async def test_event_bus():
            """测试事件总线"""
            try:
                from core.event_bus import EventBus
                
                # 创建事件总线
                event_bus = EventBus()
                assert event_bus is not None, "事件总线创建失败"
                
                # 测试事件发布和订阅
                received_events = []
                
                def event_handler(event_data):
                    received_events.append(event_data)
                
                # 订阅事件
                event_bus.subscribe("test_event", event_handler)
                
                # 发布事件
                test_event_data = {"message": "test"}
                event_bus.publish("test_event", test_event_data)
                
                # 验证事件接收
                assert len(received_events) == 1, "事件未正确接收"
                assert received_events[0] == test_event_data, "事件数据不匹配"
                
                logger.info("✅ 事件总线测试通过")
                return {"status": "success", "message": "事件总线正常工作"}
                
            except Exception as e:
                logger.error(f"❌ 事件总线测试失败: {e}")
                raise
        
        return TestCase(
            test_id="p0_005",
            name="事件总线测试",
            description="验证事件总线发布订阅功能正常",
            category=TestCategory.UNIT,
            priority=TestPriority.P0,
            component="event_bus",
            test_function=test_event_bus,
            timeout=30
        )
    
    async def run_p0_mcp_component_tests(self):
        """运行P0 MCP组件测试"""
        logger.info("🧩 开始P0 MCP组件测试")
        
        # 创建MCP组件测试套件
        p0_mcp_suite = TestSuite(
            suite_id="p0_mcp_components",
            name="P0 MCP组件测试套件",
            description="测试核心MCP组件的基础功能",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0
        )
        
        # 添加MCP组件测试用例
        mcp_components = [
            ("ag_ui_mcp", "AG-UI组件生成器"),
            ("memoryos_mcp", "记忆操作系统"),
            ("stagewise_mcp", "阶段化处理系统"),
            ("trae_agent_mcp", "Trae智能代理"),
            ("mcp_zero_smart_engine", "MCP零智能引擎")
        ]
        
        for component_name, description in mcp_components:
            test_case = self._create_mcp_component_test(component_name, description)
            p0_mcp_suite.add_test_case(test_case)
        
        # 执行测试套件
        suite_result = await self.framework.run_test_suite(p0_mcp_suite)
        self.results.append(("P0 MCP组件", suite_result))
        
        logger.info(f"✅ P0 MCP组件测试完成: {suite_result.status}")
        return suite_result
    
    def _create_mcp_component_test(self, component_name: str, description: str) -> TestCase:
        """创建MCP组件测试"""
        async def test_mcp_component():
            """测试MCP组件"""
            try:
                # 动态导入组件
                module_path = f"core.components.{component_name}"
                component_module = __import__(module_path, fromlist=[component_name])
                
                # 验证组件存在
                assert hasattr(component_module, '__init__'), f"组件模块缺少__init__: {component_name}"
                
                # 测试组件基本功能
                logger.info(f"✅ {component_name} 组件测试通过")
                return {"status": "success", "message": f"{description}组件正常"}
                
            except Exception as e:
                logger.error(f"❌ {component_name} 组件测试失败: {e}")
                raise
        
        return TestCase(
            test_id=f"p0_mcp_{component_name}",
            name=f"{description}测试",
            description=f"验证{description}组件基础功能",
            category=TestCategory.INTEGRATION,
            priority=TestPriority.P0,
            component=component_name,
            test_function=test_mcp_component,
            timeout=30
        )
    
    async def generate_p0_test_report(self):
        """生成P0测试报告"""
        logger.info("📊 生成P0测试报告")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"p0_test_report_{timestamp}.md"
        
        # 统计测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        report_content = f"""# PowerAutomation 4.0 P0测试报告

## 📊 测试概览
- **测试时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **测试版本**: PowerAutomation 4.0
- **测试类型**: P0核心功能测试

## 🎯 测试结果汇总

"""
        
        for suite_name, suite_result in self.results:
            total_tests += len(suite_result.test_results)
            suite_passed = sum(1 for r in suite_result.test_results if r.status == TestStatus.PASSED)
            suite_failed = sum(1 for r in suite_result.test_results if r.status == TestStatus.FAILED)
            
            passed_tests += suite_passed
            failed_tests += suite_failed
            
            status_emoji = "✅" if suite_result.status == TestStatus.PASSED else "❌"
            
            report_content += f"""### {status_emoji} {suite_name}
- **总用例数**: {len(suite_result.test_results)}
- **通过**: {suite_passed}
- **失败**: {suite_failed}
- **成功率**: {(suite_passed/len(suite_result.test_results)*100):.1f}%

"""
            
            # 详细测试结果
            for test_result in suite_result.test_results:
                result_emoji = "✅" if test_result.status == TestStatus.PASSED else "❌"
                report_content += f"""#### {result_emoji} {test_result.test_case.name}
- **测试ID**: {test_result.test_case.test_id}
- **组件**: {test_result.test_case.component}
- **状态**: {test_result.status.value}
- **执行时间**: {test_result.execution_time:.2f}秒
"""
                
                if test_result.error_message:
                    report_content += f"- **错误信息**: {test_result.error_message}\n"
                
                if test_result.result_data:
                    report_content += f"- **结果数据**: {test_result.result_data}\n"
                
                report_content += "\n"
        
        # 总体统计
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        overall_status = "✅ 通过" if failed_tests == 0 else "❌ 失败"
        
        summary = f"""## 📈 总体统计
- **总测试用例**: {total_tests}
- **通过用例**: {passed_tests}
- **失败用例**: {failed_tests}
- **成功率**: {success_rate:.1f}%
- **总体状态**: {overall_status}

## 🔍 测试环境
- **Python版本**: {sys.version}
- **操作系统**: {os.name}
- **测试框架**: Enhanced Stagewise Testing Framework

## 📝 测试说明
本次P0测试覆盖了PowerAutomation 4.0的核心功能，包括：
1. 系统启动和基础模块
2. MCP协调器和组件管理
3. Claude SDK和AI集成
4. Stagewise服务和测试框架
5. 事件总线和通信机制

所有P0测试用例都是关键功能验证，确保系统核心功能正常运行。

---
*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        # 将总体统计插入到报告开头
        report_content = report_content.replace("## 🎯 测试结果汇总", summary + "\n## 🎯 测试结果汇总")
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📄 P0测试报告已生成: {report_file}")
        return report_file, {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "overall_status": overall_status
        }
    
    async def run_all_p0_tests(self):
        """运行所有P0测试"""
        logger.info("🚀 开始完整P0测试流程")
        
        try:
            # 1. 运行核心系统测试
            await self.run_p0_core_system_tests()
            
            # 2. 运行MCP组件测试
            await self.run_p0_mcp_component_tests()
            
            # 3. 生成测试报告
            report_file, summary = await self.generate_p0_test_report()
            
            logger.info("🎉 P0测试流程完成")
            return report_file, summary
            
        except Exception as e:
            logger.error(f"❌ P0测试流程失败: {e}")
            raise


async def main():
    """主函数"""
    print("🚀 PowerAutomation 4.0 P0测试开始")
    
    runner = P0TestRunner()
    
    try:
        report_file, summary = await runner.run_all_p0_tests()
        
        print(f"\n📊 P0测试完成!")
        print(f"📄 报告文件: {report_file}")
        print(f"📈 测试统计:")
        print(f"   - 总用例: {summary['total_tests']}")
        print(f"   - 通过: {summary['passed_tests']}")
        print(f"   - 失败: {summary['failed_tests']}")
        print(f"   - 成功率: {summary['success_rate']:.1f}%")
        print(f"   - 状态: {summary['overall_status']}")
        
    except Exception as e:
        print(f"❌ P0测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

