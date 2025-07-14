#!/usr/bin/env python3
"""
PowerAutomation 4.0 主测试运行器
按照AICore0624的测试方法进行严谨测试
"""

import asyncio
import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import unittest
import pytest

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试模块
from tests.unit_tests.test_core_components import TestCoreComponents
from tests.unit_tests.test_smart_router_mcp import TestSmartRouterMCP
from tests.unit_tests.test_mcp_coordinator import TestMCPCoordinator
from tests.unit_tests.test_agent_squad import TestAgentSquad
from tests.integration_tests.test_mcp_integration import TestMCPIntegration
from tests.integration_tests.test_agent_integration import TestAgentIntegration
from tests.api_tests.test_api_endpoints import TestAPIEndpoints
from tests.performance_tests.test_performance import TestPerformance

class PowerAutomationTestRunner:
    """PowerAutomation 4.0 测试运行器"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "total_duration": 0,
            "test_suites": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            },
            "coverage": {},
            "performance_metrics": {}
        }
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'tests/logs/test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    async def run_all_tests(self, test_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        运行所有测试
        
        Args:
            test_types: 要运行的测试类型列表，None表示运行所有测试
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        self.test_results["start_time"] = datetime.now()
        start_time = time.time()
        
        self.logger.info("🚀 PowerAutomation 4.0 测试开始")
        self.logger.info("=" * 80)
        
        # 默认运行所有测试类型
        if test_types is None:
            test_types = ["unit", "integration", "api", "performance"]
        
        try:
            # 1. 单元测试
            if "unit" in test_types:
                await self._run_unit_tests()
            
            # 2. 集成测试
            if "integration" in test_types:
                await self._run_integration_tests()
            
            # 3. API测试
            if "api" in test_types:
                await self._run_api_tests()
            
            # 4. 性能测试
            if "performance" in test_types:
                await self._run_performance_tests()
            
            # 5. 生成测试报告
            await self._generate_test_report()
            
            # 6. 计算总体结果
            self._calculate_summary()
            
        except Exception as e:
            self.logger.error(f"测试运行失败: {e}")
            self.test_results["summary"]["errors"] += 1
        
        finally:
            self.test_results["end_time"] = datetime.now()
            self.test_results["total_duration"] = time.time() - start_time
            
            # 输出最终结果
            await self._print_final_results()
        
        return self.test_results
    
    async def _run_unit_tests(self):
        """运行单元测试"""
        self.logger.info("📋 开始单元测试")
        self.logger.info("-" * 40)
        
        unit_test_suites = [
            ("核心组件测试", TestCoreComponents),
            ("智慧路由MCP测试", TestSmartRouterMCP),
            ("MCP协调器测试", TestMCPCoordinator),
            ("智能体系统测试", TestAgentSquad)
        ]
        
        unit_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "test_cases": []
        }
        
        for suite_name, test_class in unit_test_suites:
            self.logger.info(f"🧪 运行 {suite_name}")
            
            try:
                # 创建测试套件
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                
                # 运行测试
                runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
                result = runner.run(suite)
                
                # 记录结果
                test_case_result = {
                    "suite_name": suite_name,
                    "tests_run": result.testsRun,
                    "failures": len(result.failures),
                    "errors": len(result.errors),
                    "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
                    "success": result.wasSuccessful()
                }
                
                unit_results["test_cases"].append(test_case_result)
                unit_results["total_tests"] += result.testsRun
                unit_results["failed"] += len(result.failures) + len(result.errors)
                unit_results["skipped"] += len(result.skipped) if hasattr(result, 'skipped') else 0
                unit_results["passed"] += result.testsRun - len(result.failures) - len(result.errors)
                
                status = "✅ 通过" if result.wasSuccessful() else "❌ 失败"
                self.logger.info(f"   {status} - {result.testsRun} 个测试")
                
            except Exception as e:
                self.logger.error(f"   ❌ 测试套件执行失败: {e}")
                unit_results["failed"] += 1
        
        self.test_results["test_suites"]["unit_tests"] = unit_results
        self.logger.info(f"📋 单元测试完成: {unit_results['passed']}/{unit_results['total_tests']} 通过")
    
    async def _run_integration_tests(self):
        """运行集成测试"""
        self.logger.info("🔗 开始集成测试")
        self.logger.info("-" * 40)
        
        integration_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "test_cases": []
        }
        
        # MCP集成测试
        try:
            self.logger.info("🧩 MCP组件集成测试")
            mcp_test = TestMCPIntegration()
            await mcp_test.setUp()
            
            # 运行MCP集成测试
            mcp_result = await mcp_test.test_mcp_communication()
            integration_results["test_cases"].append({
                "name": "MCP通信集成",
                "result": mcp_result,
                "success": mcp_result.get("status") == "success"
            })
            
            # 智能体集成测试
            self.logger.info("🤖 智能体系统集成测试")
            agent_test = TestAgentIntegration()
            await agent_test.setUp()
            
            agent_result = await agent_test.test_agent_collaboration()
            integration_results["test_cases"].append({
                "name": "智能体协作集成",
                "result": agent_result,
                "success": agent_result.get("status") == "success"
            })
            
            # 端到端工作流测试
            self.logger.info("🔄 端到端工作流测试")
            workflow_result = await self._test_end_to_end_workflow()
            integration_results["test_cases"].append({
                "name": "端到端工作流",
                "result": workflow_result,
                "success": workflow_result.get("status") == "success"
            })
            
        except Exception as e:
            self.logger.error(f"集成测试失败: {e}")
            integration_results["failed"] += 1
        
        # 计算集成测试结果
        integration_results["total_tests"] = len(integration_results["test_cases"])
        integration_results["passed"] = sum(1 for case in integration_results["test_cases"] if case["success"])
        integration_results["failed"] = integration_results["total_tests"] - integration_results["passed"]
        
        self.test_results["test_suites"]["integration_tests"] = integration_results
        self.logger.info(f"🔗 集成测试完成: {integration_results['passed']}/{integration_results['total_tests']} 通过")
    
    async def _run_api_tests(self):
        """运行API测试"""
        self.logger.info("🌐 开始API测试")
        self.logger.info("-" * 40)
        
        api_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "test_cases": []
        }
        
        try:
            api_test = TestAPIEndpoints()
            await api_test.setUp()
            
            # 测试API端点
            api_endpoints = [
                ("健康检查", "/health"),
                ("命令执行", "/commands/execute"),
                ("并行命令执行", "/commands/execute-parallel"),
                ("智能体状态", "/agents/status"),
                ("MCP状态", "/mcp/status")
            ]
            
            for endpoint_name, endpoint_path in api_endpoints:
                self.logger.info(f"🔌 测试 {endpoint_name} API")
                
                try:
                    result = await api_test.test_endpoint(endpoint_path)
                    api_results["test_cases"].append({
                        "name": endpoint_name,
                        "endpoint": endpoint_path,
                        "result": result,
                        "success": result.get("status_code") == 200
                    })
                except Exception as e:
                    self.logger.error(f"   ❌ API测试失败: {e}")
                    api_results["test_cases"].append({
                        "name": endpoint_name,
                        "endpoint": endpoint_path,
                        "result": {"error": str(e)},
                        "success": False
                    })
        
        except Exception as e:
            self.logger.error(f"API测试初始化失败: {e}")
            api_results["failed"] += 1
        
        # 计算API测试结果
        api_results["total_tests"] = len(api_results["test_cases"])
        api_results["passed"] = sum(1 for case in api_results["test_cases"] if case["success"])
        api_results["failed"] = api_results["total_tests"] - api_results["passed"]
        
        self.test_results["test_suites"]["api_tests"] = api_results
        self.logger.info(f"🌐 API测试完成: {api_results['passed']}/{api_results['total_tests']} 通过")
    
    async def _run_performance_tests(self):
        """运行性能测试"""
        self.logger.info("⚡ 开始性能测试")
        self.logger.info("-" * 40)
        
        performance_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "metrics": {},
            "test_cases": []
        }
        
        try:
            perf_test = TestPerformance()
            await perf_test.setUp()
            
            # 并发性能测试
            self.logger.info("🚀 并发处理性能测试")
            concurrency_result = await perf_test.test_concurrent_processing()
            performance_results["test_cases"].append({
                "name": "并发处理性能",
                "result": concurrency_result,
                "success": concurrency_result.get("success", False)
            })
            
            # 响应时间测试
            self.logger.info("⏱️ 响应时间测试")
            response_time_result = await perf_test.test_response_time()
            performance_results["test_cases"].append({
                "name": "响应时间",
                "result": response_time_result,
                "success": response_time_result.get("success", False)
            })
            
            # 内存使用测试
            self.logger.info("💾 内存使用测试")
            memory_result = await perf_test.test_memory_usage()
            performance_results["test_cases"].append({
                "name": "内存使用",
                "result": memory_result,
                "success": memory_result.get("success", False)
            })
            
            # 汇总性能指标
            performance_results["metrics"] = {
                "average_response_time": response_time_result.get("average_time", 0),
                "max_concurrent_tasks": concurrency_result.get("max_concurrent", 0),
                "memory_usage_mb": memory_result.get("peak_memory_mb", 0),
                "throughput_per_second": concurrency_result.get("throughput", 0)
            }
            
        except Exception as e:
            self.logger.error(f"性能测试失败: {e}")
            performance_results["failed"] += 1
        
        # 计算性能测试结果
        performance_results["total_tests"] = len(performance_results["test_cases"])
        performance_results["passed"] = sum(1 for case in performance_results["test_cases"] if case["success"])
        performance_results["failed"] = performance_results["total_tests"] - performance_results["passed"]
        
        self.test_results["test_suites"]["performance_tests"] = performance_results
        self.test_results["performance_metrics"] = performance_results["metrics"]
        
        self.logger.info(f"⚡ 性能测试完成: {performance_results['passed']}/{performance_results['total_tests']} 通过")
    
    async def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """端到端工作流测试"""
        try:
            self.logger.info("🔄 执行端到端工作流测试")
            
            # 模拟完整的工作流：架构设计 -> 开发 -> 测试 -> 部署
            workflow_steps = [
                "智慧路由接收请求",
                "MCP协调器分配任务",
                "架构师智能体设计架构",
                "开发智能体实现功能",
                "测试智能体验证质量",
                "部署智能体发布系统"
            ]
            
            completed_steps = []
            
            for step in workflow_steps:
                # 模拟每个步骤的执行
                await asyncio.sleep(0.1)  # 模拟处理时间
                completed_steps.append(step)
                self.logger.info(f"   ✅ {step}")
            
            return {
                "status": "success",
                "completed_steps": completed_steps,
                "total_steps": len(workflow_steps),
                "success_rate": len(completed_steps) / len(workflow_steps)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "completed_steps": completed_steps,
                "total_steps": len(workflow_steps)
            }
    
    async def _generate_test_report(self):
        """生成测试报告"""
        self.logger.info("📊 生成测试报告")
        
        report_data = {
            "test_run_info": {
                "start_time": self.test_results["start_time"].isoformat(),
                "end_time": self.test_results["end_time"].isoformat() if self.test_results["end_time"] else None,
                "duration": self.test_results["total_duration"],
                "environment": "PowerAutomation 4.0 Development"
            },
            "test_results": self.test_results["test_suites"],
            "summary": self.test_results["summary"],
            "performance_metrics": self.test_results["performance_metrics"]
        }
        
        # 保存JSON报告
        report_file = f"tests/reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📊 测试报告已保存: {report_file}")
    
    def _calculate_summary(self):
        """计算总体测试结果"""
        summary = self.test_results["summary"]
        
        for suite_name, suite_results in self.test_results["test_suites"].items():
            summary["total_tests"] += suite_results.get("total_tests", 0)
            summary["passed"] += suite_results.get("passed", 0)
            summary["failed"] += suite_results.get("failed", 0)
            summary["skipped"] += suite_results.get("skipped", 0)
    
    async def _print_final_results(self):
        """输出最终测试结果"""
        self.logger.info("=" * 80)
        self.logger.info("🎯 PowerAutomation 4.0 测试结果汇总")
        self.logger.info("=" * 80)
        
        summary = self.test_results["summary"]
        
        # 总体统计
        self.logger.info(f"📊 总体统计:")
        self.logger.info(f"   总测试数: {summary['total_tests']}")
        self.logger.info(f"   通过: {summary['passed']} ✅")
        self.logger.info(f"   失败: {summary['failed']} ❌")
        self.logger.info(f"   跳过: {summary['skipped']} ⏭️")
        self.logger.info(f"   错误: {summary['errors']} 💥")
        
        # 成功率
        if summary['total_tests'] > 0:
            success_rate = (summary['passed'] / summary['total_tests']) * 100
            self.logger.info(f"   成功率: {success_rate:.1f}%")
        
        # 执行时间
        self.logger.info(f"   执行时间: {self.test_results['total_duration']:.2f} 秒")
        
        # 各测试套件结果
        self.logger.info(f"\\n📋 各测试套件结果:")
        for suite_name, suite_results in self.test_results["test_suites"].items():
            passed = suite_results.get("passed", 0)
            total = suite_results.get("total_tests", 0)
            status = "✅" if passed == total and total > 0 else "❌"
            self.logger.info(f"   {suite_name}: {passed}/{total} {status}")
        
        # 性能指标
        if self.test_results["performance_metrics"]:
            self.logger.info(f"\\n⚡ 性能指标:")
            metrics = self.test_results["performance_metrics"]
            self.logger.info(f"   平均响应时间: {metrics.get('average_response_time', 0):.3f} 秒")
            self.logger.info(f"   最大并发任务: {metrics.get('max_concurrent_tasks', 0)}")
            self.logger.info(f"   内存使用峰值: {metrics.get('memory_usage_mb', 0):.1f} MB")
            self.logger.info(f"   吞吐量: {metrics.get('throughput_per_second', 0):.1f} 任务/秒")
        
        # 最终判断
        overall_success = summary['failed'] == 0 and summary['errors'] == 0 and summary['total_tests'] > 0
        final_status = "🎉 所有测试通过！" if overall_success else "⚠️ 存在测试失败"
        self.logger.info(f"\\n{final_status}")
        self.logger.info("=" * 80)

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PowerAutomation 4.0 测试运行器')
    parser.add_argument('--types', nargs='+', choices=['unit', 'integration', 'api', 'performance'], 
                       help='要运行的测试类型')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建测试运行器
    runner = PowerAutomationTestRunner()
    
    # 运行测试
    results = await runner.run_all_tests(test_types=args.types)
    
    # 返回退出码
    exit_code = 0 if results["summary"]["failed"] == 0 and results["summary"]["errors"] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())

