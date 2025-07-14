#!/usr/bin/env python3
"""
Zen MCP - 智能工作流程編排和執行引擎
PowerAutomation v4.6.1 - 禪式工作流管理平台

基於aicore0707的Zen MCP實現，提供：
- 智能工作流編排
- 多工具協作執行
- 動態工作流優化
- 實時執行監控
"""

import asyncio
import logging
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """任務狀態枚舉"""
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStrategy(Enum):
    """執行策略枚舉"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ADAPTIVE = "adaptive"


@dataclass
class WorkflowTask:
    """工作流任務定義"""
    task_id: str
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    timeout: int = 300
    retry_count: int = 3
    status: TaskStatus = TaskStatus.WAITING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: float = 0.0

    def __post_init__(self):
        if not self.dependencies:
            self.dependencies = []


@dataclass
class WorkflowDefinition:
    """工作流定義"""
    workflow_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    timeout: int = 3600
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkflowExecution:
    """工作流執行實例"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    completed_tasks: int = 0
    total_tasks: int = 0
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ZenWorkflowEngine:
    """Zen工作流引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.workflows = {}
        self.executions = {}
        self.task_registry = {}
        self.running_workflows = {}
        
        # 性能監控
        self.execution_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0,
            "total_tasks_executed": 0
        }
    
    async def initialize(self):
        """初始化Zen工作流引擎"""
        self.logger.info("🧘 初始化Zen MCP - 智能工作流編排引擎")
        
        # 註冊默認工具
        await self._register_default_tools()
        
        # 載入預定義工作流
        await self._load_predefined_workflows()
        
        self.logger.info("✅ Zen MCP初始化完成")
    
    async def _register_default_tools(self):
        """註冊默認工具"""
        default_tools = {
            "test_runner": self._execute_test_tool,
            "code_generator": self._execute_code_generator,
            "file_processor": self._execute_file_processor,
            "api_caller": self._execute_api_caller,
            "data_transformer": self._execute_data_transformer
        }
        
        for tool_name, tool_func in default_tools.items():
            self.task_registry[tool_name] = tool_func
            
        self.logger.info(f"註冊 {len(default_tools)} 個默認工具")
    
    async def _load_predefined_workflows(self):
        """載入預定義工作流"""
        # PowerAutomation標準工作流
        standard_workflows = [
            await self._create_testing_workflow(),
            await self._create_deployment_workflow(),
            await self._create_code_review_workflow()
        ]
        
        for workflow in standard_workflows:
            await self.register_workflow(workflow)
    
    async def _create_testing_workflow(self) -> WorkflowDefinition:
        """創建測試工作流"""
        return WorkflowDefinition(
            workflow_id="powerautomation_testing",
            name="PowerAutomation測試工作流",
            description="完整的自動化測試執行流程",
            tasks=[
                WorkflowTask(
                    task_id="setup_test_env",
                    tool_name="test_runner",
                    parameters={"action": "setup", "environment": "test"},
                    dependencies=[]
                ),
                WorkflowTask(
                    task_id="run_unit_tests",
                    tool_name="test_runner",
                    parameters={"action": "run", "type": "unit"},
                    dependencies=["setup_test_env"]
                ),
                WorkflowTask(
                    task_id="run_integration_tests",
                    tool_name="test_runner",
                    parameters={"action": "run", "type": "integration"},
                    dependencies=["run_unit_tests"]
                ),
                WorkflowTask(
                    task_id="generate_test_report",
                    tool_name="file_processor",
                    parameters={"action": "generate_report", "format": "html"},
                    dependencies=["run_integration_tests"]
                )
            ],
            strategy=ExecutionStrategy.SEQUENTIAL
        )
    
    async def _create_deployment_workflow(self) -> WorkflowDefinition:
        """創建部署工作流"""
        return WorkflowDefinition(
            workflow_id="powerautomation_deployment",
            name="PowerAutomation部署工作流",
            description="自動化部署到各個環境",
            tasks=[
                WorkflowTask(
                    task_id="build_application",
                    tool_name="code_generator",
                    parameters={"action": "build", "target": "production"},
                    dependencies=[]
                ),
                WorkflowTask(
                    task_id="run_security_scan",
                    tool_name="test_runner",
                    parameters={"action": "security_scan"},
                    dependencies=["build_application"]
                ),
                WorkflowTask(
                    task_id="deploy_to_staging",
                    tool_name="api_caller",
                    parameters={"action": "deploy", "environment": "staging"},
                    dependencies=["run_security_scan"]
                ),
                WorkflowTask(
                    task_id="run_smoke_tests",
                    tool_name="test_runner",
                    parameters={"action": "smoke_test", "environment": "staging"},
                    dependencies=["deploy_to_staging"]
                )
            ],
            strategy=ExecutionStrategy.SEQUENTIAL
        )
    
    async def _create_code_review_workflow(self) -> WorkflowDefinition:
        """創建代碼審查工作流"""
        return WorkflowDefinition(
            workflow_id="powerautomation_code_review",
            name="PowerAutomation代碼審查工作流",
            description="AI驅動的代碼質量審查",
            tasks=[
                WorkflowTask(
                    task_id="analyze_code_quality",
                    tool_name="code_generator",
                    parameters={"action": "analyze", "scope": "quality"},
                    dependencies=[]
                ),
                WorkflowTask(
                    task_id="check_security_issues",
                    tool_name="test_runner",
                    parameters={"action": "security_check"},
                    dependencies=[]
                ),
                WorkflowTask(
                    task_id="generate_review_report",
                    tool_name="file_processor",
                    parameters={"action": "review_report"},
                    dependencies=["analyze_code_quality", "check_security_issues"]
                )
            ],
            strategy=ExecutionStrategy.PARALLEL
        )
    
    async def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """註冊工作流定義"""
        try:
            # 驗證工作流
            if not await self._validate_workflow(workflow):
                return False
            
            self.workflows[workflow.workflow_id] = workflow
            self.logger.info(f"註冊工作流: {workflow.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"註冊工作流失敗: {e}")
            return False
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """執行工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        execution_id = str(uuid.uuid4())
        
        # 創建執行實例
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            total_tasks=len(workflow.tasks),
            start_time=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        # 啟動異步執行
        task = asyncio.create_task(
            self._execute_workflow_async(workflow, execution, context or {})
        )
        self.running_workflows[execution_id] = task
        
        self.logger.info(f"啟動工作流執行: {workflow.name} ({execution_id[:8]}...)")
        return execution_id
    
    async def _execute_workflow_async(self, workflow: WorkflowDefinition,
                                    execution: WorkflowExecution, context: Dict[str, Any]):
        """異步執行工作流"""
        try:
            execution.status = WorkflowStatus.RUNNING
            
            # 根據策略執行任務
            if workflow.strategy == ExecutionStrategy.SEQUENTIAL:
                await self._execute_sequential(workflow, execution, context)
            elif workflow.strategy == ExecutionStrategy.PARALLEL:
                await self._execute_parallel(workflow, execution, context)
            elif workflow.strategy == ExecutionStrategy.CONDITIONAL:
                await self._execute_conditional(workflow, execution, context)
            elif workflow.strategy == ExecutionStrategy.ADAPTIVE:
                await self._execute_adaptive(workflow, execution, context)
            
            # 完成執行
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.progress = 100.0
            
            # 更新統計
            self._update_stats(execution, True)
            
            self.logger.info(f"工作流執行完成: {execution.execution_id[:8]}...")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            
            self._update_stats(execution, False)
            self.logger.error(f"工作流執行失敗: {e}")
        
        finally:
            # 清理運行中的工作流
            if execution.execution_id in self.running_workflows:
                del self.running_workflows[execution.execution_id]
    
    async def _execute_sequential(self, workflow: WorkflowDefinition,
                                execution: WorkflowExecution, context: Dict[str, Any]):
        """順序執行策略"""
        for task in workflow.tasks:
            if execution.status == WorkflowStatus.CANCELLED:
                break
            
            await self._execute_task(task, execution, context)
            execution.completed_tasks += 1
            execution.progress = (execution.completed_tasks / execution.total_tasks) * 100
    
    async def _execute_parallel(self, workflow: WorkflowDefinition,
                              execution: WorkflowExecution, context: Dict[str, Any]):
        """並行執行策略"""
        # 處理依賴關係，分批並行執行
        remaining_tasks = workflow.tasks.copy()
        
        while remaining_tasks and execution.status != WorkflowStatus.CANCELLED:
            # 找出可以執行的任務（沒有未完成的依賴）
            ready_tasks = []
            for task in remaining_tasks:
                if self._task_dependencies_satisfied(task, workflow.tasks):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                break
            
            # 並行執行準備好的任務
            await asyncio.gather(*[
                self._execute_task(task, execution, context)
                for task in ready_tasks
            ])
            
            # 更新進度
            execution.completed_tasks += len(ready_tasks)
            execution.progress = (execution.completed_tasks / execution.total_tasks) * 100
            
            # 移除已完成的任務
            for task in ready_tasks:
                remaining_tasks.remove(task)
    
    async def _execute_conditional(self, workflow: WorkflowDefinition,
                                 execution: WorkflowExecution, context: Dict[str, Any]):
        """條件執行策略"""
        for task in workflow.tasks:
            if execution.status == WorkflowStatus.CANCELLED:
                break
            
            # 檢查條件
            if await self._check_task_condition(task, context):
                await self._execute_task(task, execution, context)
                execution.completed_tasks += 1
            else:
                task.status = TaskStatus.SKIPPED
                execution.completed_tasks += 1
            
            execution.progress = (execution.completed_tasks / execution.total_tasks) * 100
    
    async def _execute_adaptive(self, workflow: WorkflowDefinition,
                              execution: WorkflowExecution, context: Dict[str, Any]):
        """自適應執行策略"""
        # 動態選擇最優執行策略
        if len(workflow.tasks) <= 3:
            await self._execute_sequential(workflow, execution, context)
        elif self._has_complex_dependencies(workflow.tasks):
            await self._execute_parallel(workflow, execution, context)
        else:
            await self._execute_conditional(workflow, execution, context)
    
    async def _execute_task(self, task: WorkflowTask, execution: WorkflowExecution,
                          context: Dict[str, Any]):
        """執行單個任務"""
        try:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            
            # 檢查依賴
            if not self._task_dependencies_satisfied(task, self.workflows[execution.workflow_id].tasks):
                task.status = TaskStatus.FAILED
                task.error = "依賴檢查失敗"
                return
            
            # 執行任務
            if task.tool_name in self.task_registry:
                tool_func = self.task_registry[task.tool_name]
                task.result = await self._execute_with_timeout(
                    tool_func, task.parameters, task.timeout
                )
            else:
                # 模擬工具執行
                await asyncio.sleep(0.1)
                task.result = {"status": "completed", "tool": task.tool_name}
            
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            task.execution_time = (task.end_time - task.start_time).total_seconds()
            
            self.logger.info(f"任務執行完成: {task.task_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            if task.start_time:
                task.execution_time = (task.end_time - task.start_time).total_seconds()
            
            self.logger.error(f"任務執行失敗: {task.task_id} - {e}")
            
            # 重試機制
            if task.retry_count > 0:
                task.retry_count -= 1
                await asyncio.sleep(1)
                await self._execute_task(task, execution, context)
    
    async def _execute_with_timeout(self, func: Callable, params: Dict[str, Any],
                                  timeout: int) -> Any:
        """帶超時的任務執行"""
        try:
            return await asyncio.wait_for(func(**params), timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"任務執行超時 ({timeout}秒)")
    
    def _task_dependencies_satisfied(self, task: WorkflowTask, all_tasks: List[WorkflowTask]) -> bool:
        """檢查任務依賴是否滿足"""
        for dep_id in task.dependencies:
            dep_task = next((t for t in all_tasks if t.task_id == dep_id), None)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    async def _check_task_condition(self, task: WorkflowTask, context: Dict[str, Any]) -> bool:
        """檢查任務執行條件"""
        condition = task.parameters.get("condition")
        if not condition:
            return True
        
        # 簡化的條件評估
        try:
            return eval(condition, {"context": context})
        except:
            return True
    
    def _has_complex_dependencies(self, tasks: List[WorkflowTask]) -> bool:
        """檢查是否有複雜依賴關係"""
        total_deps = sum(len(task.dependencies) for task in tasks)
        return total_deps > len(tasks) * 0.5
    
    async def _validate_workflow(self, workflow: WorkflowDefinition) -> bool:
        """驗證工作流定義"""
        try:
            # 檢查任務ID唯一性
            task_ids = [task.task_id for task in workflow.tasks]
            if len(task_ids) != len(set(task_ids)):
                self.logger.error("任務ID不唯一")
                return False
            
            # 檢查依賴關係
            for task in workflow.tasks:
                for dep in task.dependencies:
                    if dep not in task_ids:
                        self.logger.error(f"依賴任務不存在: {dep}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"工作流驗證失敗: {e}")
            return False
    
    def _update_stats(self, execution: WorkflowExecution, success: bool):
        """更新執行統計"""
        self.execution_stats["total_workflows"] += 1
        if success:
            self.execution_stats["successful_workflows"] += 1
        else:
            self.execution_stats["failed_workflows"] += 1
        
        # 更新平均執行時間
        total_time = (self.execution_stats["average_execution_time"] * 
                     (self.execution_stats["total_workflows"] - 1) + 
                     execution.execution_time)
        self.execution_stats["average_execution_time"] = total_time / self.execution_stats["total_workflows"]
        
        self.execution_stats["total_tasks_executed"] += execution.completed_tasks
    
    # 默認工具實現
    async def _execute_test_tool(self, **params) -> Dict[str, Any]:
        """執行測試工具"""
        action = params.get("action", "run")
        await asyncio.sleep(0.2)
        return {"action": action, "result": "success", "tests_run": 10, "passed": 9}
    
    async def _execute_code_generator(self, **params) -> Dict[str, Any]:
        """執行代碼生成工具"""
        action = params.get("action", "generate")
        await asyncio.sleep(0.3)
        return {"action": action, "result": "success", "files_generated": 5}
    
    async def _execute_file_processor(self, **params) -> Dict[str, Any]:
        """執行文件處理工具"""
        action = params.get("action", "process")
        await asyncio.sleep(0.1)
        return {"action": action, "result": "success", "files_processed": 3}
    
    async def _execute_api_caller(self, **params) -> Dict[str, Any]:
        """執行API調用工具"""
        action = params.get("action", "call")
        await asyncio.sleep(0.2)
        return {"action": action, "result": "success", "status_code": 200}
    
    async def _execute_data_transformer(self, **params) -> Dict[str, Any]:
        """執行數據轉換工具"""
        action = params.get("action", "transform")
        await asyncio.sleep(0.1)
        return {"action": action, "result": "success", "records_processed": 100}
    
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """獲取執行狀態"""
        return self.executions.get(execution_id)
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有工作流"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "task_count": len(wf.tasks),
                "strategy": wf.strategy.value
            }
            for wf in self.workflows.values()
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """獲取Zen MCP狀態"""
        return {
            "component": "Zen MCP",
            "version": "4.6.1",
            "status": "running",
            "registered_workflows": len(self.workflows),
            "active_executions": len(self.running_workflows),
            "total_executions": len(self.executions),
            "execution_stats": self.execution_stats,
            "capabilities": [
                "workflow_orchestration",
                "parallel_execution",
                "dependency_management",
                "conditional_logic",
                "adaptive_strategy",
                "real_time_monitoring"
            ]
        }


# 單例實例
zen_mcp = ZenWorkflowEngine()