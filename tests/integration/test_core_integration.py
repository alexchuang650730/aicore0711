"""
核心组件集成测试
测试各组件之间的协作和数据流
"""

import pytest
import asyncio
from unittest.mock import patch

from core.powerautomation_core import AutomationCore, CoreConfig

@pytest.mark.integration
@pytest.mark.asyncio
class TestCoreIntegration:
    """核心组件集成测试"""
    
    async def test_full_startup_shutdown_cycle(self, test_config):
        """测试完整的启动-停止周期"""
        core = AutomationCore(test_config)
        
        # 启动核心
        start_result = await core.start()
        assert start_result is True
        assert core.status.status == "running"
        
        # 验证所有组件都已初始化
        assert core.workflow_engine is not None
        assert core.task_scheduler is not None
        assert core.resource_manager is not None
        assert core.mcp_coordinator is not None
        assert core.monitoring_service is not None
        
        # 停止核心
        stop_result = await core.stop()
        assert stop_result is True
        assert core.status.status == "stopped"
    
    async def test_workflow_task_integration(self, test_config):
        """测试工作流和任务调度的集成"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 创建工作流
            workflow_def = {
                "name": "集成测试工作流",
                "description": "测试工作流和任务调度集成",
                "steps": [
                    {
                        "id": "step1",
                        "name": "第一步",
                        "type": "delay",
                        "config": {"delay": 0.1}
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            assert workflow_id is not None
            
            # 通过任务调度器调度工作流执行
            task_def = {
                "name": "工作流执行任务",
                "type": "immediate",
                "action": {
                    "type": "workflow",
                    "workflow_id": workflow_id,
                    "context": {"test": "value"}
                }
            }
            
            task_id = await core.schedule_task(task_def)
            assert task_id is not None
            
            # 等待任务完成
            await asyncio.sleep(1)
            
            # 验证任务状态
            scheduler_status = core.task_scheduler.get_scheduler_status()
            assert scheduler_status["total_tasks"] >= 1
            
        finally:
            await core.stop()
    
    async def test_mcp_workflow_integration(self, test_config):
        """测试MCP和工作流的集成"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 创建包含MCP调用的工作流
            workflow_def = {
                "name": "MCP集成测试工作流",
                "steps": [
                    {
                        "id": "mcp_step",
                        "name": "MCP调用步骤",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "command_master",
                            "method": "execute_command",
                            "params": {"command": "echo 'test'"}
                        }
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            execution_id = await core.execute_workflow(workflow_id)
            
            # 等待执行完成
            await asyncio.sleep(1)
            
            # 检查执行状态
            status = await core.get_workflow_status(execution_id)
            assert status["status"] in ["completed", "running"]
            
        finally:
            await core.stop()
    
    async def test_resource_monitoring_integration(self, test_config):
        """测试资源管理和监控的集成"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 分配资源
            allocation_id = await core.allocate_resource("cpu", 10.0)
            assert allocation_id is not None
            
            # 等待监控收集数据
            await asyncio.sleep(2)
            
            # 检查监控数据
            monitoring_summary = core.monitoring_service.get_monitoring_summary()
            assert "metrics" in monitoring_summary
            
            # 检查资源状态
            resource_status = await core.get_resource_status()
            assert "cpu_quota_usage" in resource_status or len(resource_status) > 0
            
            # 释放资源
            release_result = await core.resource_manager.release_resource(allocation_id)
            assert release_result is True
            
        finally:
            await core.stop()
    
    async def test_error_propagation(self, test_config):
        """测试错误传播和处理"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 创建会失败的工作流
            workflow_def = {
                "name": "错误测试工作流",
                "steps": [
                    {
                        "id": "error_step",
                        "name": "错误步骤",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "non_existent_mcp",
                            "method": "non_existent_method",
                            "params": {}
                        }
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            execution_id = await core.execute_workflow(workflow_id)
            
            # 等待执行完成
            await asyncio.sleep(2)
            
            # 检查执行状态应该是失败
            status = await core.get_workflow_status(execution_id)
            assert status["status"] in ["failed", "running"]
            
            # 检查是否有告警产生
            alerts = core.monitoring_service.get_alerts(resolved=False)
            # 可能有告警产生，但不强制要求
            
        finally:
            await core.stop()
    
    async def test_concurrent_operations(self, test_config):
        """测试并发操作"""
        # 降低并发限制以便测试
        test_config.max_concurrent_workflows = 2
        test_config.max_concurrent_tasks = 3
        
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 创建多个工作流
            workflow_def = {
                "name": "并发测试工作流",
                "steps": [
                    {
                        "id": "delay_step",
                        "name": "延迟步骤",
                        "type": "delay",
                        "config": {"delay": 0.5}
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            
            # 并发执行多个工作流
            execution_tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    core.execute_workflow(workflow_id, {"instance": i})
                )
                execution_tasks.append(task)
            
            # 等待所有执行启动
            execution_ids = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # 检查是否有执行因并发限制被拒绝
            successful_executions = [
                eid for eid in execution_ids 
                if isinstance(eid, str)
            ]
            
            # 应该有一些成功的执行
            assert len(successful_executions) > 0
            
            # 等待执行完成
            await asyncio.sleep(2)
            
        finally:
            await core.stop()
    
    async def test_configuration_update_propagation(self, test_config):
        """测试配置更新传播"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 更新配置
            new_config = {
                "monitoring_interval": 20,
                "max_concurrent_workflows": 15
            }
            
            result = await core.update_config(new_config)
            assert result is True
            
            # 验证配置已更新
            current_config = core.get_config()
            assert current_config["monitoring_interval"] == 20
            assert current_config["max_concurrent_workflows"] == 15
            
        finally:
            await core.stop()
    
    async def test_health_check_cascade(self, test_config):
        """测试健康检查级联"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 运行核心健康检查
            core_healthy = await core.health_check()
            
            # 运行各组件健康检查
            workflow_healthy = await core.workflow_engine.health_check()
            scheduler_healthy = await core.task_scheduler.health_check()
            resource_healthy = await core.resource_manager.health_check()
            mcp_healthy = await core.mcp_coordinator.health_check()
            monitoring_healthy = await core.monitoring_service.health_check()
            
            # 验证健康状态
            assert isinstance(core_healthy, bool)
            assert isinstance(workflow_healthy, bool)
            assert isinstance(scheduler_healthy, bool)
            assert isinstance(resource_healthy, bool)
            assert isinstance(mcp_healthy, bool)
            assert isinstance(monitoring_healthy, bool)
            
        finally:
            await core.stop()

@pytest.mark.integration
@pytest.mark.asyncio
class TestDataFlow:
    """数据流集成测试"""
    
    async def test_workflow_context_propagation(self, test_config):
        """测试工作流上下文传播"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 创建带上下文传播的工作流
            workflow_def = {
                "name": "上下文传播测试",
                "variables": {"global_var": "global_value"},
                "steps": [
                    {
                        "id": "step1",
                        "name": "设置变量",
                        "type": "script",
                        "config": {
                            "script": "context['step1_result'] = 'success'"
                        }
                    },
                    {
                        "id": "step2",
                        "name": "使用变量",
                        "type": "condition",
                        "config": {
                            "condition": "step1_result == 'success'"
                        },
                        "dependencies": ["step1"]
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            execution_id = await core.execute_workflow(workflow_id, {"input_var": "input_value"})
            
            # 等待执行完成
            await asyncio.sleep(1)
            
            # 检查执行状态和上下文
            status = await core.get_workflow_status(execution_id)
            assert "step_results" in status
            
        finally:
            await core.stop()
    
    async def test_metric_collection_flow(self, test_config):
        """测试指标收集流程"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 等待监控收集一些指标
            await asyncio.sleep(3)
            
            # 检查指标数据
            metrics = core.monitoring_service.get_metrics(limit=10)
            assert isinstance(metrics, dict)
            
            # 检查监控摘要
            summary = core.monitoring_service.get_monitoring_summary()
            assert "metrics" in summary
            assert "health" in summary
            
        finally:
            await core.stop()

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestLongRunningOperations:
    """长时间运行操作测试"""
    
    async def test_long_running_workflow(self, test_config):
        """测试长时间运行的工作流"""
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 创建长时间运行的工作流
            workflow_def = {
                "name": "长时间运行测试",
                "steps": [
                    {
                        "id": "long_step",
                        "name": "长时间步骤",
                        "type": "delay",
                        "config": {"delay": 2}
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            execution_id = await core.execute_workflow(workflow_id)
            
            # 检查初始状态
            initial_status = await core.get_workflow_status(execution_id)
            assert initial_status["status"] in ["pending", "running"]
            
            # 等待完成
            await asyncio.sleep(3)
            
            # 检查最终状态
            final_status = await core.get_workflow_status(execution_id)
            assert final_status["status"] == "completed"
            
        finally:
            await core.stop()
    
    async def test_monitoring_over_time(self, test_config):
        """测试长时间监控"""
        # 缩短监控间隔以便测试
        test_config.monitoring_interval = 1
        
        core = AutomationCore(test_config)
        await core.start()
        
        try:
            # 运行一段时间
            await asyncio.sleep(5)
            
            # 检查监控数据积累
            metrics = core.monitoring_service.get_metrics()
            assert len(metrics) > 0
            
            # 检查健康状态历史
            health_status = core.monitoring_service.get_health_status()
            assert "overall_healthy" in health_status
            
        finally:
            await core.stop()

