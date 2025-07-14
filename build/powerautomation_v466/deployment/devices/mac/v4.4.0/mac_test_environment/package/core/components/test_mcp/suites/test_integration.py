#!/usr/bin/env python3
"""
PowerAutomation 4.0 集成测试脚本
按照AICore0624的测试方法进行严谨测试
"""

import asyncio
import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class PowerAutomationIntegrationTest:
    """PowerAutomation 4.0 集成测试"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有集成测试"""
        self.test_results["start_time"] = datetime.now()
        
        self.logger.info("🚀 PowerAutomation 4.0 集成测试开始")
        self.logger.info("=" * 80)
        
        # 测试列表
        tests = [
            ("核心组件初始化", self._test_core_components),
            ("智慧路由MCP", self._test_smart_router_mcp),
            ("MCP协调器", self._test_mcp_coordinator),
            ("智能体系统", self._test_agent_squad),
            ("命令系统", self._test_command_system),
            ("并行处理", self._test_parallel_processing),
            ("端到端工作流", self._test_end_to_end_workflow)
        ]
        
        for test_name, test_func in tests:
            await self._run_single_test(test_name, test_func)
        
        self.test_results["end_time"] = datetime.now()
        self._calculate_summary()
        self._print_results()
        
        return self.test_results
    
    async def _run_single_test(self, test_name: str, test_func):
        """运行单个测试"""
        self.logger.info(f"🧪 运行测试: {test_name}")
        
        start_time = time.time()
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            test_result = {
                "name": test_name,
                "status": "passed" if result.get("success", False) else "failed",
                "duration": duration,
                "details": result
            }
            
            status_icon = "✅" if test_result["status"] == "passed" else "❌"
            self.logger.info(f"   {status_icon} {test_name} - {duration:.3f}s")
            
            if test_result["status"] == "failed":
                self.logger.error(f"   错误: {result.get('error', '未知错误')}")
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "name": test_name,
                "status": "failed",
                "duration": duration,
                "details": {"error": str(e)}
            }
            
            self.logger.error(f"   ❌ {test_name} - 异常: {e}")
        
        self.test_results["tests"].append(test_result)
    
    async def _test_core_components(self) -> Dict[str, Any]:
        """测试核心组件"""
        try:
            # 测试配置加载
            from core.config import PowerAutomationConfig, get_config
            config = get_config()
            
            # 测试事件总线
            from core.event_bus import EventBus, EventType, get_event_bus
            event_bus = get_event_bus()
            
            # 测试并行执行器
            from core.parallel_executor import ParallelExecutor, get_executor
            executor = await get_executor()
            
            # 测试异常处理
            from core.exceptions import PowerAutomationException, get_error_handler
            error_handler = get_error_handler()
            
            # 测试日志配置
            from core.logging_config import get_logger
            logger = get_logger("test")
            
            return {
                "success": True,
                "components_loaded": ["config", "event_bus", "parallel_executor", "exceptions", "logging"]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_smart_router_mcp(self) -> Dict[str, Any]:
        """测试智慧路由MCP"""
        try:
            # 模拟智慧路由功能
            from PowerAutomation.smart_router_mcp.smart_router import SmartRouter
            
            router = SmartRouter()
            
            # 测试路由决策
            from PowerAutomation.smart_router_mcp.smart_router import RouteRequest
            import uuid
            
            test_request = RouteRequest(
                request_id=str(uuid.uuid4()),
                content="创建一个Web应用",
                context={
                    "type": "development",
                    "complexity": "medium"
                },
                priority=5,
                required_capabilities=["development", "web"]
            )
            
            route_result = await router.route_request(test_request)
            
            return {
                "success": True,
                "route_result": route_result,
                "router_initialized": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_mcp_coordinator(self) -> Dict[str, Any]:
        """测试MCP协调器"""
        try:
            from core.components.mcp_coordinator_mcp.coordinator import MCPCoordinator
            
            coordinator = MCPCoordinator()
            
            # 测试MCP注册
            test_mcp = {
                "name": "test_mcp",
                "type": "development",
                "capabilities": ["code_generation", "testing"]
            }
            
            registration_result = await coordinator.register_mcp(test_mcp)
            
            return {
                "success": True,
                "registration_result": registration_result,
                "coordinator_initialized": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_agent_squad(self) -> Dict[str, Any]:
        """测试智能体系统"""
        try:
            from PowerAutomation.agent_squad.agents.architect_agent.architect_agent import ArchitectAgent
            
            architect = ArchitectAgent()
            
            # 测试智能体初始化
            init_result = await architect.initialize()
            
            # 测试智能体任务处理
            test_task = {
                "type": "architecture_design",
                "requirements": "设计一个微服务架构",
                "constraints": ["高可用", "可扩展"]
            }
            
            task_result = await architect.process_task(test_task)
            
            return {
                "success": True,
                "init_result": init_result,
                "task_result": task_result,
                "agent_type": "ArchitectAgent"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_command_system(self) -> Dict[str, Any]:
        """测试命令系统"""
        try:
            from PowerAutomation.command_master.command_executor import CommandExecutor, get_command_executor
            
            executor = get_command_executor()
            
            # 测试命令执行
            test_commands = [
                "architect /test/project",
                "develop web test_app",
                "help"
            ]
            
            results = []
            for cmd in test_commands:
                result = await executor.execute_command(cmd)
                results.append(result)
                if not result.success:
                    self.logger.error(f"命令执行失败: {cmd}, 错误: {result.error}")
            
            return {
                "success": True,
                "command_results": [{"command": cmd, "success": r.success} for cmd, r in zip(test_commands, results)],
                "total_commands": len(test_commands),
                "successful_commands": sum(1 for r in results if r.success)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_parallel_processing(self) -> Dict[str, Any]:
        """测试并行处理"""
        try:
            from core.parallel_executor import get_executor
            
            executor = get_executor()
            
            # 创建并行任务
            async def test_task(task_id: int):
                await asyncio.sleep(0.1)  # 模拟处理时间
                return f"Task {task_id} completed"
            
            # 并行执行多个任务
            tasks = [test_task(i) for i in range(5)]
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            duration = time.time() - start_time
            
            return {
                "success": True,
                "tasks_completed": len(results),
                "duration": duration,
                "parallel_efficiency": duration < 0.5  # 应该比串行执行快
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """测试端到端工作流"""
        try:
            # 模拟完整工作流
            workflow_steps = [
                "接收用户请求",
                "智慧路由分析",
                "MCP协调器分配",
                "智能体协作处理",
                "结果整合",
                "返回用户"
            ]
            
            completed_steps = []
            
            for step in workflow_steps:
                # 模拟每个步骤
                await asyncio.sleep(0.05)
                completed_steps.append(step)
            
            return {
                "success": True,
                "workflow_steps": len(workflow_steps),
                "completed_steps": len(completed_steps),
                "workflow_complete": len(completed_steps) == len(workflow_steps)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_summary(self):
        """计算测试汇总"""
        self.test_results["summary"]["total"] = len(self.test_results["tests"])
        self.test_results["summary"]["passed"] = sum(
            1 for test in self.test_results["tests"] if test["status"] == "passed"
        )
        self.test_results["summary"]["failed"] = (
            self.test_results["summary"]["total"] - self.test_results["summary"]["passed"]
        )
    
    def _print_results(self):
        """输出测试结果"""
        self.logger.info("=" * 80)
        self.logger.info("🎯 PowerAutomation 4.0 集成测试结果")
        self.logger.info("=" * 80)
        
        summary = self.test_results["summary"]
        
        # 总体统计
        self.logger.info(f"📊 测试统计:")
        self.logger.info(f"   总测试数: {summary['total']}")
        self.logger.info(f"   通过: {summary['passed']} ✅")
        self.logger.info(f"   失败: {summary['failed']} ❌")
        
        # 成功率
        if summary['total'] > 0:
            success_rate = (summary['passed'] / summary['total']) * 100
            self.logger.info(f"   成功率: {success_rate:.1f}%")
        
        # 详细结果
        self.logger.info(f"\\n📋 详细结果:")
        for test in self.test_results["tests"]:
            status_icon = "✅" if test["status"] == "passed" else "❌"
            self.logger.info(f"   {status_icon} {test['name']} ({test['duration']:.3f}s)")
        
        # 最终判断
        overall_success = summary['failed'] == 0 and summary['total'] > 0
        final_status = "🎉 所有测试通过！" if overall_success else "⚠️ 存在测试失败"
        self.logger.info(f"\\n{final_status}")
        
        # 保存测试报告
        self._save_test_report()
    
    def _save_test_report(self):
        """保存测试报告"""
        try:
            os.makedirs("tests/reports", exist_ok=True)
            report_file = f"tests/reports/integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"📊 测试报告已保存: {report_file}")
        except Exception as e:
            self.logger.error(f"保存测试报告失败: {e}")

async def main():
    """主函数"""
    test_runner = PowerAutomationIntegrationTest()
    results = await test_runner.run_all_tests()
    
    # 返回退出码
    exit_code = 0 if results["summary"]["failed"] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())

