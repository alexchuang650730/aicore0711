"""
WorkflowEngine 单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.powerautomation_core.workflow_engine import (
    WorkflowEngine, WorkflowDefinition, WorkflowExecution, 
    WorkflowStep, WorkflowStatus, StepStatus
)

@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkflowEngine:
    """WorkflowEngine测试类"""
    
    async def test_initialization(self, test_config, mock_resource_manager, mock_mcp_coordinator):
        """测试初始化"""
        engine = WorkflowEngine(test_config, mock_resource_manager, mock_mcp_coordinator)
        
        assert engine.config == test_config
        assert engine.resource_manager == mock_resource_manager
        assert engine.mcp_coordinator == mock_mcp_coordinator
        assert len(engine.workflows) == 0
        assert len(engine.executions) == 0
        assert len(engine.running_executions) == 0
    
    async def test_create_workflow_success(self, workflow_engine, sample_workflow):
        """测试成功创建工作流"""
        workflow_id = await workflow_engine.create_workflow(sample_workflow)
        
        assert workflow_id is not None
        assert workflow_id in workflow_engine.workflows
        
        workflow = workflow_engine.workflows[workflow_id]
        assert workflow.name == sample_workflow["name"]
        assert workflow.description == sample_workflow["description"]
        assert len(workflow.steps) == len(sample_workflow["steps"])
    
    async def test_create_workflow_validation_error(self, workflow_engine):
        """测试工作流验证错误"""
        invalid_workflow = {
            "name": "Invalid Workflow",
            "steps": [
                {
                    "id": "step1",
                    "name": "Step 1",
                    "type": "command",
                    "config": {}
                },
                {
                    "id": "step1",  # 重复ID
                    "name": "Step 2", 
                    "type": "command",
                    "config": {}
                }
            ]
        }
        
        with pytest.raises(ValueError, match="步骤ID不唯一"):
            await workflow_engine.create_workflow(invalid_workflow)
    
    async def test_execute_workflow_success(self, workflow_engine, sample_workflow):
        """测试成功执行工作流"""
        # 创建工作流
        workflow_id = await workflow_engine.create_workflow(sample_workflow)
        
        # 模拟步骤执行
        with patch.object(workflow_engine, '_execute_workflow_task') as mock_execute:
            mock_execute.return_value = asyncio.Future()
            mock_execute.return_value.set_result(None)
            
            execution_id = await workflow_engine.execute_workflow(workflow_id)
            
            assert execution_id is not None
            assert execution_id in workflow_engine.executions
            assert execution_id in workflow_engine.running_executions
            
            execution = workflow_engine.executions[execution_id]
            assert execution.workflow_id == workflow_id
            assert execution.status == WorkflowStatus.PENDING
    
    async def test_execute_workflow_not_found(self, workflow_engine):
        """测试执行不存在的工作流"""
        with pytest.raises(ValueError, match="工作流不存在"):
            await workflow_engine.execute_workflow("non_existent_id")
    
    async def test_execute_workflow_concurrency_limit(self, workflow_engine, sample_workflow):
        """测试并发限制"""
        # 创建工作流
        workflow_id = await workflow_engine.create_workflow(sample_workflow)
        
        # 填满并发限制
        workflow_engine.max_concurrent_executions = 1
        workflow_engine.running_executions["dummy"] = Mock()
        
        with pytest.raises(RuntimeError, match="达到最大并发执行限制"):
            await workflow_engine.execute_workflow(workflow_id)
    
    async def test_get_execution_status(self, workflow_engine, sample_workflow):
        """测试获取执行状态"""
        # 创建工作流和执行
        workflow_id = await workflow_engine.create_workflow(sample_workflow)
        
        with patch.object(workflow_engine, '_execute_workflow_task'):
            execution_id = await workflow_engine.execute_workflow(workflow_id)
            
            status = await workflow_engine.get_execution_status(execution_id)
            
            assert status["id"] == execution_id
            assert status["workflow_id"] == workflow_id
            assert "status" in status
            assert "start_time" in status
    
    async def test_get_execution_status_not_found(self, workflow_engine):
        """测试获取不存在执行的状态"""
        with pytest.raises(ValueError, match="执行不存在"):
            await workflow_engine.get_execution_status("non_existent_id")
    
    async def test_health_check_success(self, workflow_engine):
        """测试健康检查成功"""
        # 模拟正常状态
        workflow_engine.running_executions = {}
        
        result = await workflow_engine.health_check()
        assert result is True
    
    async def test_health_check_failure(self, workflow_engine):
        """测试健康检查失败"""
        # 模拟超过并发限制
        workflow_engine.max_concurrent_executions = 1
        workflow_engine.running_executions = {"1": Mock(), "2": Mock()}
        
        result = await workflow_engine.health_check()
        assert result is False
    
    async def test_step_execution_command(self, workflow_engine):
        """测试命令步骤执行"""
        step = WorkflowStep(
            id="test_step",
            name="Test Command",
            type="command",
            config={"command": "echo 'test'"}
        )
        
        execution = WorkflowExecution(
            id="test_execution",
            workflow_id="test_workflow",
            status=WorkflowStatus.RUNNING,
            context={}
        )
        
        # 模拟MCP调用
        workflow_engine.mcp_coordinator.call_mcp.return_value = {"output": "test"}
        
        result = await workflow_engine._handle_command_step(execution, step)
        
        assert result["output"] == "test"
        workflow_engine.mcp_coordinator.call_mcp.assert_called_once()
    
    async def test_step_execution_mcp_call(self, workflow_engine):
        """测试MCP调用步骤执行"""
        step = WorkflowStep(
            id="test_step",
            name="Test MCP Call",
            type="mcp_call",
            config={
                "mcp_id": "test_mcp",
                "method": "test_method",
                "params": {"key": "value"}
            }
        )
        
        execution = WorkflowExecution(
            id="test_execution",
            workflow_id="test_workflow",
            status=WorkflowStatus.RUNNING,
            context={}
        )
        
        # 模拟MCP调用
        workflow_engine.mcp_coordinator.call_mcp.return_value = {"result": "success"}
        
        result = await workflow_engine._handle_mcp_call_step(execution, step)
        
        assert result["result"] == "success"
        workflow_engine.mcp_coordinator.call_mcp.assert_called_once_with(
            "test_mcp", "test_method", {"key": "value"}
        )
    
    async def test_step_execution_condition(self, workflow_engine):
        """测试条件步骤执行"""
        step = WorkflowStep(
            id="test_step",
            name="Test Condition",
            type="condition",
            config={"condition": "True"}
        )
        
        execution = WorkflowExecution(
            id="test_execution",
            workflow_id="test_workflow",
            status=WorkflowStatus.RUNNING,
            context={}
        )
        
        result = await workflow_engine._handle_condition_step(execution, step)
        
        assert result["condition_result"] is True
    
    async def test_step_execution_delay(self, workflow_engine):
        """测试延迟步骤执行"""
        step = WorkflowStep(
            id="test_step",
            name="Test Delay",
            type="delay",
            config={"delay": 0.1}
        )
        
        execution = WorkflowExecution(
            id="test_execution",
            workflow_id="test_workflow",
            status=WorkflowStatus.RUNNING,
            context={}
        )
        
        start_time = datetime.now()
        result = await workflow_engine._handle_delay_step(execution, step)
        end_time = datetime.now()
        
        assert result["delayed"] == 0.1
        assert (end_time - start_time).total_seconds() >= 0.1
    
    async def test_variable_replacement(self, workflow_engine):
        """测试变量替换"""
        context = {"name": "test", "value": 123}
        
        # 测试字符串替换
        text = "Hello ${name}, value is ${value}"
        result = workflow_engine._replace_variables(text, context)
        assert result == "Hello test, value is 123"
        
        # 测试字典替换
        data = {"message": "Hello ${name}", "count": "${value}"}
        result = workflow_engine._replace_variables(data, context)
        assert result["message"] == "Hello test"
        assert result["count"] == "123"
        
        # 测试列表替换
        data = ["${name}", "${value}"]
        result = workflow_engine._replace_variables(data, context)
        assert result == ["test", "123"]
    
    async def test_condition_evaluation(self, workflow_engine):
        """测试条件评估"""
        context = {"x": 10, "y": 5}
        
        # 测试简单条件
        assert workflow_engine._evaluate_condition("x > y", context) is True
        assert workflow_engine._evaluate_condition("x < y", context) is False
        assert workflow_engine._evaluate_condition("x == 10", context) is True
        
        # 测试复杂条件
        assert workflow_engine._evaluate_condition("x > 5 and y < 10", context) is True
        assert workflow_engine._evaluate_condition("x > 15 or y < 10", context) is True
    
    async def test_step_graph_building(self, workflow_engine):
        """测试步骤依赖图构建"""
        steps = [
            WorkflowStep("step1", "Step 1", "command", {}, []),
            WorkflowStep("step2", "Step 2", "command", {}, ["step1"]),
            WorkflowStep("step3", "Step 3", "command", {}, ["step1", "step2"])
        ]
        
        graph = workflow_engine._build_step_graph(steps)
        
        assert graph["step1"] == []
        assert graph["step2"] == ["step1"]
        assert graph["step3"] == ["step1", "step2"]
    
    async def test_event_system(self, workflow_engine):
        """测试事件系统"""
        events_received = []
        
        def event_handler(data):
            events_received.append(data)
        
        workflow_engine.on("test_event", event_handler)
        
        await workflow_engine._emit_event("test_event", {"message": "test"})
        
        assert len(events_received) == 1
        assert events_received[0]["message"] == "test"

@pytest.mark.unit
class TestWorkflowDefinition:
    """WorkflowDefinition测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        steps = [
            WorkflowStep("step1", "Step 1", "command", {})
        ]
        
        workflow = WorkflowDefinition(
            id="test_workflow",
            name="Test Workflow",
            description="Test Description",
            version="1.0",
            steps=steps
        )
        
        assert workflow.id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert workflow.description == "Test Description"
        assert workflow.version == "1.0"
        assert len(workflow.steps) == 1
        assert workflow.variables == {}
        assert workflow.timeout == 3600
        assert workflow.created_at is not None

@pytest.mark.unit
class TestWorkflowStep:
    """WorkflowStep测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        step = WorkflowStep(
            id="test_step",
            name="Test Step",
            type="command",
            config={"command": "echo test"}
        )
        
        assert step.id == "test_step"
        assert step.name == "Test Step"
        assert step.type == "command"
        assert step.config["command"] == "echo test"
        assert step.dependencies == []
        assert step.timeout == 300
        assert step.retry_count == 0
        assert step.max_retries == 3
    
    def test_with_dependencies(self):
        """测试带依赖的步骤"""
        step = WorkflowStep(
            id="test_step",
            name="Test Step",
            type="command",
            config={},
            dependencies=["step1", "step2"]
        )
        
        assert step.dependencies == ["step1", "step2"]

@pytest.mark.unit
class TestWorkflowExecution:
    """WorkflowExecution测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        execution = WorkflowExecution(
            id="test_execution",
            workflow_id="test_workflow",
            status=WorkflowStatus.PENDING,
            context={"key": "value"}
        )
        
        assert execution.id == "test_execution"
        assert execution.workflow_id == "test_workflow"
        assert execution.status == WorkflowStatus.PENDING
        assert execution.context["key"] == "value"
        assert execution.step_results == {}
        assert execution.current_step is None
        assert execution.start_time is not None
        assert execution.end_time is None
        assert execution.error_message is None

