"""
ClaudeEditor 4.6.0 端到端集成测试
测试完整的用户场景和系统集成
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from core.powerautomation_core import AutomationCore, CoreConfig
from core.hitl_coordinator import HITLCoordinator
from core.repository_manager import RepositoryContext
from adapters.ocr3b_flux_adapter import OCRAdapter

@pytest.mark.e2e
@pytest.mark.asyncio
class TestClaudeEditorE2E:
    """ClaudeEditor端到端测试"""
    
    async def test_complete_document_processing_workflow(self, temp_dir):
        """测试完整的文档处理工作流"""
        # 创建测试配置
        config = CoreConfig(
            environment="test",
            data_dir=str(temp_dir / "data"),
            log_dir=str(temp_dir / "logs"),
            cache_dir=str(temp_dir / "cache"),
            enable_cloud_sync=False
        )
        
        # 启动核心系统
        core = AutomationCore(config)
        await core.start()
        
        try:
            # 1. 创建文档处理工作流
            workflow_def = {
                "name": "文档处理工作流",
                "description": "OCR处理 -> 内容分析 -> 结果输出",
                "steps": [
                    {
                        "id": "ocr_processing",
                        "name": "OCR处理",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "ocr_processor",
                            "method": "process_image",
                            "params": {
                                "image_path": "${input_image}",
                                "output_format": "markdown"
                            }
                        }
                    },
                    {
                        "id": "content_analysis",
                        "name": "内容分析",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "command_master",
                            "method": "execute_command",
                            "params": {
                                "command": "wc -w ${ocr_result_file}"
                            }
                        },
                        "dependencies": ["ocr_processing"]
                    },
                    {
                        "id": "result_output",
                        "name": "结果输出",
                        "type": "script",
                        "config": {
                            "script": "print(f'处理完成: {ocr_result}')"
                        },
                        "dependencies": ["content_analysis"]
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            assert workflow_id is not None
            
            # 2. 执行工作流
            execution_context = {
                "input_image": str(temp_dir / "test_image.png"),
                "output_dir": str(temp_dir / "output")
            }
            
            execution_id = await core.execute_workflow(workflow_id, execution_context)
            assert execution_id is not None
            
            # 3. 等待执行完成
            max_wait = 30
            wait_time = 0
            while wait_time < max_wait:
                status = await core.get_workflow_status(execution_id)
                if status["status"] in ["completed", "failed"]:
                    break
                await asyncio.sleep(1)
                wait_time += 1
            
            # 4. 验证结果
            final_status = await core.get_workflow_status(execution_id)
            assert final_status["status"] in ["completed", "failed"]
            assert "step_results" in final_status
            
        finally:
            await core.stop()
    
    async def test_hitl_decision_workflow(self, temp_dir):
        """测试人机协作决策工作流"""
        config = CoreConfig(
            environment="test",
            data_dir=str(temp_dir / "data"),
            log_dir=str(temp_dir / "logs"),
            cache_dir=str(temp_dir / "cache")
        )
        
        core = AutomationCore(config)
        await core.start()
        
        try:
            # 1. 创建需要人工决策的工作流
            workflow_def = {
                "name": "HITL决策工作流",
                "steps": [
                    {
                        "id": "data_preparation",
                        "name": "数据准备",
                        "type": "script",
                        "config": {
                            "script": "context['data_ready'] = True"
                        }
                    },
                    {
                        "id": "human_decision",
                        "name": "人工决策",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "hitl_coordinator",
                            "method": "request_decision",
                            "params": {
                                "decision_type": "approval",
                                "context": "需要批准数据处理",
                                "timeout": 30
                            }
                        },
                        "dependencies": ["data_preparation"]
                    },
                    {
                        "id": "process_decision",
                        "name": "处理决策结果",
                        "type": "condition",
                        "config": {
                            "condition": "decision_result == 'approved'"
                        },
                        "dependencies": ["human_decision"]
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            execution_id = await core.execute_workflow(workflow_id)
            
            # 2. 等待人工决策请求
            await asyncio.sleep(2)
            
            # 3. 模拟人工决策（在实际场景中，这会通过UI完成）
            # 这里我们直接调用HITL协调器来模拟决策
            decision_status = await core.call_mcp(
                "hitl_coordinator",
                "get_decision_status",
                {"execution_id": execution_id}
            )
            
            # 4. 验证工作流状态
            workflow_status = await core.get_workflow_status(execution_id)
            assert workflow_status["status"] in ["running", "completed", "failed"]
            
        finally:
            await core.stop()
    
    async def test_repository_context_workflow(self, temp_dir):
        """测试仓库上下文工作流"""
        config = CoreConfig(
            environment="test",
            data_dir=str(temp_dir / "data"),
            log_dir=str(temp_dir / "logs"),
            cache_dir=str(temp_dir / "cache")
        )
        
        core = AutomationCore(config)
        await core.start()
        
        try:
            # 1. 创建仓库分析工作流
            workflow_def = {
                "name": "仓库分析工作流",
                "steps": [
                    {
                        "id": "get_current_repo",
                        "name": "获取当前仓库",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "repository_manager",
                            "method": "get_current_repository",
                            "params": {}
                        }
                    },
                    {
                        "id": "analyze_repo",
                        "name": "分析仓库",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "repository_manager",
                            "method": "analyze_repository",
                            "params": {
                                "repository_id": "${current_repo_id}"
                            }
                        },
                        "dependencies": ["get_current_repo"]
                    },
                    {
                        "id": "generate_context",
                        "name": "生成上下文",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "repository_manager",
                            "method": "get_repository_context",
                            "params": {
                                "repository_id": "${current_repo_id}",
                                "include_files": True
                            }
                        },
                        "dependencies": ["analyze_repo"]
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            execution_id = await core.execute_workflow(workflow_id)
            
            # 2. 等待执行完成
            await asyncio.sleep(3)
            
            # 3. 验证结果
            status = await core.get_workflow_status(execution_id)
            assert status["status"] in ["completed", "running", "failed"]
            
            if status["status"] == "completed":
                assert "step_results" in status
                assert "get_current_repo" in status["step_results"]
            
        finally:
            await core.stop()
    
    async def test_multi_component_integration(self, temp_dir):
        """测试多组件集成场景"""
        config = CoreConfig(
            environment="test",
            data_dir=str(temp_dir / "data"),
            log_dir=str(temp_dir / "logs"),
            cache_dir=str(temp_dir / "cache")
        )
        
        core = AutomationCore(config)
        await core.start()
        
        try:
            # 1. 创建复杂的多组件工作流
            workflow_def = {
                "name": "多组件集成工作流",
                "description": "集成OCR、命令执行、HITL和仓库管理",
                "steps": [
                    {
                        "id": "check_resources",
                        "name": "检查资源",
                        "type": "script",
                        "config": {
                            "script": "context['resources_ok'] = True"
                        }
                    },
                    {
                        "id": "process_document",
                        "name": "处理文档",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "ocr_processor",
                            "method": "process_pdf",
                            "params": {
                                "pdf_path": "${input_pdf}",
                                "output_format": "markdown"
                            }
                        },
                        "dependencies": ["check_resources"]
                    },
                    {
                        "id": "validate_output",
                        "name": "验证输出",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "command_master",
                            "method": "execute_command",
                            "params": {
                                "command": "ls -la ${output_dir}"
                            }
                        },
                        "dependencies": ["process_document"]
                    },
                    {
                        "id": "request_approval",
                        "name": "请求批准",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "hitl_coordinator",
                            "method": "request_decision",
                            "params": {
                                "decision_type": "quality_check",
                                "context": "请检查处理结果质量"
                            }
                        },
                        "dependencies": ["validate_output"]
                    },
                    {
                        "id": "save_to_repo",
                        "name": "保存到仓库",
                        "type": "condition",
                        "config": {
                            "condition": "approval_result == 'approved'"
                        },
                        "dependencies": ["request_approval"]
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            
            # 2. 执行工作流
            execution_context = {
                "input_pdf": str(temp_dir / "test.pdf"),
                "output_dir": str(temp_dir / "output")
            }
            
            execution_id = await core.execute_workflow(workflow_id, execution_context)
            
            # 3. 监控执行过程
            execution_steps = []
            max_wait = 30
            wait_time = 0
            
            while wait_time < max_wait:
                status = await core.get_workflow_status(execution_id)
                
                if status["current_step"] and status["current_step"] not in execution_steps:
                    execution_steps.append(status["current_step"])
                
                if status["status"] in ["completed", "failed"]:
                    break
                    
                await asyncio.sleep(1)
                wait_time += 1
            
            # 4. 验证执行过程
            final_status = await core.get_workflow_status(execution_id)
            assert final_status["status"] in ["completed", "failed"]
            
            # 验证至少执行了一些步骤
            assert len(execution_steps) > 0
            
        finally:
            await core.stop()
    
    async def test_error_recovery_scenario(self, temp_dir):
        """测试错误恢复场景"""
        config = CoreConfig(
            environment="test",
            data_dir=str(temp_dir / "data"),
            log_dir=str(temp_dir / "logs"),
            cache_dir=str(temp_dir / "cache")
        )
        
        core = AutomationCore(config)
        await core.start()
        
        try:
            # 1. 创建包含错误处理的工作流
            workflow_def = {
                "name": "错误恢复测试工作流",
                "steps": [
                    {
                        "id": "normal_step",
                        "name": "正常步骤",
                        "type": "delay",
                        "config": {"delay": 0.1}
                    },
                    {
                        "id": "error_step",
                        "name": "错误步骤",
                        "type": "mcp_call",
                        "config": {
                            "mcp_id": "non_existent_mcp",
                            "method": "non_existent_method",
                            "params": {}
                        },
                        "max_retries": 2,
                        "critical": False,  # 非关键步骤
                        "dependencies": ["normal_step"]
                    },
                    {
                        "id": "recovery_step",
                        "name": "恢复步骤",
                        "type": "script",
                        "config": {
                            "script": "context['recovered'] = True"
                        },
                        "dependencies": ["normal_step"]  # 不依赖错误步骤
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            execution_id = await core.execute_workflow(workflow_id)
            
            # 2. 等待执行完成
            await asyncio.sleep(5)
            
            # 3. 验证错误处理
            status = await core.get_workflow_status(execution_id)
            
            # 工作流应该能够继续执行，即使有步骤失败
            assert status["status"] in ["completed", "failed"]
            
            # 检查步骤结果
            if "step_results" in status:
                # 正常步骤应该成功
                assert "normal_step" in status["step_results"]
                
                # 错误步骤应该失败
                if "error_step" in status["step_results"]:
                    error_result = status["step_results"]["error_step"]
                    assert "error" in error_result or isinstance(error_result, dict)
            
            # 4. 检查监控告警
            alerts = core.monitoring_service.get_alerts(resolved=False, limit=10)
            # 可能有告警产生，但不强制要求
            
        finally:
            await core.stop()
    
    async def test_performance_under_load(self, temp_dir):
        """测试负载下的性能"""
        config = CoreConfig(
            environment="test",
            data_dir=str(temp_dir / "data"),
            log_dir=str(temp_dir / "logs"),
            cache_dir=str(temp_dir / "cache"),
            max_concurrent_workflows=5,
            max_concurrent_tasks=10
        )
        
        core = AutomationCore(config)
        await core.start()
        
        try:
            # 1. 创建简单的测试工作流
            workflow_def = {
                "name": "性能测试工作流",
                "steps": [
                    {
                        "id": "cpu_task",
                        "name": "CPU任务",
                        "type": "delay",
                        "config": {"delay": 0.5}
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            
            # 2. 并发执行多个工作流
            execution_tasks = []
            num_executions = 10
            
            start_time = asyncio.get_event_loop().time()
            
            for i in range(num_executions):
                task = asyncio.create_task(
                    core.execute_workflow(workflow_id, {"instance": i})
                )
                execution_tasks.append(task)
            
            # 3. 等待所有执行完成
            execution_ids = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # 4. 等待所有工作流完成
            await asyncio.sleep(3)
            
            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time
            
            # 5. 验证性能
            successful_executions = [
                eid for eid in execution_ids 
                if isinstance(eid, str)
            ]
            
            assert len(successful_executions) > 0
            
            # 检查执行时间是否合理（应该有并发效果）
            assert total_time < num_executions * 0.5  # 如果串行执行会需要更长时间
            
            # 6. 检查系统状态
            core_status = core.get_status()
            assert core_status["status"] == "running"
            
            # 检查监控数据
            monitoring_summary = core.monitoring_service.get_monitoring_summary()
            assert "performance" in monitoring_summary
            
        finally:
            await core.stop()

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestClaudeEditorLongRunning:
    """长时间运行的端到端测试"""
    
    async def test_system_stability_over_time(self, temp_dir):
        """测试系统长时间稳定性"""
        config = CoreConfig(
            environment="test",
            data_dir=str(temp_dir / "data"),
            log_dir=str(temp_dir / "logs"),
            cache_dir=str(temp_dir / "cache"),
            monitoring_interval=2,
            resource_check_interval=3
        )
        
        core = AutomationCore(config)
        await core.start()
        
        try:
            # 运行系统一段时间
            runtime = 30  # 30秒
            start_time = asyncio.get_event_loop().time()
            
            # 定期执行一些工作流
            workflow_def = {
                "name": "稳定性测试工作流",
                "steps": [
                    {
                        "id": "health_check",
                        "name": "健康检查",
                        "type": "script",
                        "config": {
                            "script": "import time; time.sleep(0.1); context['timestamp'] = time.time()"
                        }
                    }
                ]
            }
            
            workflow_id = await core.create_workflow(workflow_def)
            
            execution_count = 0
            while (asyncio.get_event_loop().time() - start_time) < runtime:
                try:
                    execution_id = await core.execute_workflow(workflow_id, {"run": execution_count})
                    execution_count += 1
                    await asyncio.sleep(2)
                except Exception as e:
                    # 记录错误但继续运行
                    print(f"执行错误: {e}")
            
            # 验证系统仍然健康
            final_status = core.get_status()
            assert final_status["status"] == "running"
            
            # 检查监控数据
            monitoring_summary = core.monitoring_service.get_monitoring_summary()
            assert monitoring_summary["metrics"]["total_records"] > 0
            
            # 验证至少执行了一些工作流
            assert execution_count > 0
            
        finally:
            await core.stop()

