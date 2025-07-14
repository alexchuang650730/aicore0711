#!/usr/bin/env python3
"""
Zen MCP工作流引擎
PowerAutomation 4.1 - 智能工作流编排和执行引擎

功能特性:
- 智能工作流编排
- 多工具协作执行
- 动态工作流优化
- 实时执行监控
- 错误恢复机制
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from concurrent.futures import ThreadPoolExecutor
import networkx as nx

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    """任务状态枚举"""
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class ExecutionStrategy(Enum):
    """执行策略枚举"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ADAPTIVE = "adaptive"

@dataclass
class WorkflowTask:
    """工作流任务定义"""
    task_id: str
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300
    retry_count: int = 3
    status: TaskStatus = TaskStatus.WAITING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: float = 0.0

@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    timeout: int = 3600
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowExecution:
    """工作流执行实例"""
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
    """Zen MCP工作流引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.task_registry: Dict[str, Callable] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running_workflows: Dict[str, asyncio.Task] = {}
        
        # 性能监控
        self.execution_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0,
            "total_tasks_executed": 0
        }
        
        logger.info("Zen工作流引擎初始化完成")
    
    async def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """注册工作流定义"""
        try:
            # 验证工作流定义
            if not await self._validate_workflow(workflow):
                return False
            
            self.workflows[workflow.workflow_id] = workflow
            logger.info(f"工作流已注册: {workflow.name} ({workflow.workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"注册工作流失败: {e}")
            return False
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """执行工作流"""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"工作流不存在: {workflow_id}")
            
            workflow = self.workflows[workflow_id]
            execution_id = str(uuid.uuid4())
            
            # 创建执行实例
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                total_tasks=len(workflow.tasks),
                start_time=datetime.now()
            )
            
            self.executions[execution_id] = execution
            
            # 启动异步执行
            task = asyncio.create_task(
                self._execute_workflow_async(workflow, execution, context or {})
            )
            self.running_workflows[execution_id] = task
            
            logger.info(f"工作流执行已启动: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"启动工作流执行失败: {e}")
            raise
    
    async def _execute_workflow_async(self, workflow: WorkflowDefinition, 
                                    execution: WorkflowExecution, context: Dict[str, Any]):
        """异步执行工作流"""
        try:
            execution.status = WorkflowStatus.RUNNING
            
            # 根据策略执行任务
            if workflow.strategy == ExecutionStrategy.SEQUENTIAL:
                await self._execute_sequential(workflow, execution, context)
            elif workflow.strategy == ExecutionStrategy.PARALLEL:
                await self._execute_parallel(workflow, execution, context)
            elif workflow.strategy == ExecutionStrategy.CONDITIONAL:
                await self._execute_conditional(workflow, execution, context)
            elif workflow.strategy == ExecutionStrategy.ADAPTIVE:
                await self._execute_adaptive(workflow, execution, context)
            
            # 完成执行
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.progress = 100.0
            
            # 更新统计
            self._update_stats(execution, True)
            
            logger.info(f"工作流执行完成: {execution.execution_id}")
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            
            self._update_stats(execution, False)
            logger.error(f"工作流执行失败: {e}")
        
        finally:
            # 清理运行中的工作流
            if execution.execution_id in self.running_workflows:
                del self.running_workflows[execution.execution_id]
    
    async def _execute_sequential(self, workflow: WorkflowDefinition, 
                                execution: WorkflowExecution, context: Dict[str, Any]):
        """顺序执行策略"""
        for task in workflow.tasks:
            if execution.status == WorkflowStatus.CANCELLED:
                break
            
            await self._execute_task(task, execution, context)
            execution.completed_tasks += 1
            execution.progress = (execution.completed_tasks / execution.total_tasks) * 100
    
    async def _execute_parallel(self, workflow: WorkflowDefinition, 
                              execution: WorkflowExecution, context: Dict[str, Any]):
        """并行执行策略"""
        # 构建依赖图
        dependency_graph = self._build_dependency_graph(workflow.tasks)
        
        # 按依赖层级执行
        levels = list(nx.topological_generations(dependency_graph))
        
        for level_tasks in levels:
            if execution.status == WorkflowStatus.CANCELLED:
                break
            
            # 并行执行同一层级的任务
            tasks_to_execute = [task for task in workflow.tasks if task.task_id in level_tasks]
            await asyncio.gather(*[
                self._execute_task(task, execution, context) 
                for task in tasks_to_execute
            ])
            
            execution.completed_tasks += len(tasks_to_execute)
            execution.progress = (execution.completed_tasks / execution.total_tasks) * 100
    
    async def _execute_conditional(self, workflow: WorkflowDefinition, 
                                 execution: WorkflowExecution, context: Dict[str, Any]):
        """条件执行策略"""
        for task in workflow.tasks:
            if execution.status == WorkflowStatus.CANCELLED:
                break
            
            # 检查条件
            if await self._check_task_condition(task, context):
                await self._execute_task(task, execution, context)
                execution.completed_tasks += 1
            else:
                task.status = TaskStatus.SKIPPED
                execution.completed_tasks += 1
            
            execution.progress = (execution.completed_tasks / execution.total_tasks) * 100
    
    async def _execute_adaptive(self, workflow: WorkflowDefinition, 
                              execution: WorkflowExecution, context: Dict[str, Any]):
        """自适应执行策略"""
        # 动态选择最优执行策略
        if len(workflow.tasks) <= 3:
            await self._execute_sequential(workflow, execution, context)
        elif self._has_complex_dependencies(workflow.tasks):
            await self._execute_parallel(workflow, execution, context)
        else:
            await self._execute_conditional(workflow, execution, context)
    
    async def _execute_task(self, task: WorkflowTask, execution: WorkflowExecution, 
                          context: Dict[str, Any]):
        """执行单个任务"""
        try:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            
            # 检查依赖
            if not await self._check_dependencies(task, execution):
                task.status = TaskStatus.FAILED
                task.error = "依赖检查失败"
                return
            
            # 执行任务
            if task.tool_name in self.task_registry:
                tool_func = self.task_registry[task.tool_name]
                task.result = await self._execute_with_timeout(
                    tool_func, task.parameters, task.timeout
                )
            else:
                # 模拟工具执行
                await asyncio.sleep(0.1)
                task.result = {"status": "completed", "tool": task.tool_name}
            
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            task.execution_time = (task.end_time - task.start_time).total_seconds()
            
            logger.info(f"任务执行完成: {task.task_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            if task.start_time:
                task.execution_time = (task.end_time - task.start_time).total_seconds()
            
            logger.error(f"任务执行失败: {task.task_id} - {e}")
            
            # 重试机制
            if task.retry_count > 0:
                task.retry_count -= 1
                await asyncio.sleep(1)  # 等待1秒后重试
                await self._execute_task(task, execution, context)
    
    async def _execute_with_timeout(self, func: Callable, params: Dict[str, Any], 
                                  timeout: int) -> Any:
        """带超时的任务执行"""
        try:
            return await asyncio.wait_for(func(**params), timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"任务执行超时 ({timeout}秒)")
    
    def _build_dependency_graph(self, tasks: List[WorkflowTask]) -> nx.DiGraph:
        """构建任务依赖图"""
        graph = nx.DiGraph()
        
        # 添加节点
        for task in tasks:
            graph.add_node(task.task_id)
        
        # 添加边（依赖关系）
        for task in tasks:
            for dep in task.dependencies:
                graph.add_edge(dep, task.task_id)
        
        return graph
    
    async def _check_dependencies(self, task: WorkflowTask, execution: WorkflowExecution) -> bool:
        """检查任务依赖"""
        workflow = self.workflows[execution.workflow_id]
        
        for dep_id in task.dependencies:
            dep_task = next((t for t in workflow.tasks if t.task_id == dep_id), None)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _check_task_condition(self, task: WorkflowTask, context: Dict[str, Any]) -> bool:
        """检查任务执行条件"""
        # 简化的条件检查逻辑
        condition = task.parameters.get("condition")
        if not condition:
            return True
        
        # 评估条件表达式
        try:
            return eval(condition, {"context": context})
        except:
            return True
    
    def _has_complex_dependencies(self, tasks: List[WorkflowTask]) -> bool:
        """检查是否有复杂依赖关系"""
        total_deps = sum(len(task.dependencies) for task in tasks)
        return total_deps > len(tasks) * 0.5
    
    async def _validate_workflow(self, workflow: WorkflowDefinition) -> bool:
        """验证工作流定义"""
        try:
            # 检查任务ID唯一性
            task_ids = [task.task_id for task in workflow.tasks]
            if len(task_ids) != len(set(task_ids)):
                logger.error("任务ID不唯一")
                return False
            
            # 检查依赖关系
            for task in workflow.tasks:
                for dep in task.dependencies:
                    if dep not in task_ids:
                        logger.error(f"依赖任务不存在: {dep}")
                        return False
            
            # 检查循环依赖
            graph = self._build_dependency_graph(workflow.tasks)
            if not nx.is_directed_acyclic_graph(graph):
                logger.error("存在循环依赖")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"工作流验证失败: {e}")
            return False
    
    def _update_stats(self, execution: WorkflowExecution, success: bool):
        """更新执行统计"""
        self.execution_stats["total_workflows"] += 1
        if success:
            self.execution_stats["successful_workflows"] += 1
        else:
            self.execution_stats["failed_workflows"] += 1
        
        # 更新平均执行时间
        total_time = (self.execution_stats["average_execution_time"] * 
                     (self.execution_stats["total_workflows"] - 1) + 
                     execution.execution_time)
        self.execution_stats["average_execution_time"] = total_time / self.execution_stats["total_workflows"]
        
        self.execution_stats["total_tasks_executed"] += execution.completed_tasks
    
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行状态"""
        return self.executions.get(execution_id)
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """取消工作流执行"""
        try:
            if execution_id in self.executions:
                execution = self.executions[execution_id]
                execution.status = WorkflowStatus.CANCELLED
                
                if execution_id in self.running_workflows:
                    self.running_workflows[execution_id].cancel()
                
                logger.info(f"工作流已取消: {execution_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"取消工作流失败: {e}")
            return False
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """暂停工作流执行"""
        try:
            if execution_id in self.executions:
                execution = self.executions[execution_id]
                execution.status = WorkflowStatus.PAUSED
                logger.info(f"工作流已暂停: {execution_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"暂停工作流失败: {e}")
            return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """恢复工作流执行"""
        try:
            if execution_id in self.executions:
                execution = self.executions[execution_id]
                if execution.status == WorkflowStatus.PAUSED:
                    execution.status = WorkflowStatus.RUNNING
                    logger.info(f"工作流已恢复: {execution_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"恢复工作流失败: {e}")
            return False
    
    async def get_workflow_list(self) -> List[Dict[str, Any]]:
        """获取工作流列表"""
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
    
    async def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取执行历史"""
        executions = sorted(
            self.executions.values(),
            key=lambda x: x.start_time or datetime.min,
            reverse=True
        )[:limit]
        
        return [
            {
                "execution_id": ex.execution_id,
                "workflow_id": ex.workflow_id,
                "status": ex.status.value,
                "start_time": ex.start_time.isoformat() if ex.start_time else None,
                "end_time": ex.end_time.isoformat() if ex.end_time else None,
                "execution_time": ex.execution_time,
                "progress": ex.progress,
                "completed_tasks": ex.completed_tasks,
                "total_tasks": ex.total_tasks
            }
            for ex in executions
        ]
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            **self.execution_stats,
            "success_rate": (
                self.execution_stats["successful_workflows"] / 
                max(self.execution_stats["total_workflows"], 1) * 100
            ),
            "active_workflows": len(self.running_workflows),
            "registered_workflows": len(self.workflows)
        }
    
    async def register_tool(self, tool_name: str, tool_func: Callable):
        """注册工具函数"""
        self.task_registry[tool_name] = tool_func
        logger.info(f"工具已注册: {tool_name}")
    
    async def cleanup_old_executions(self, days: int = 7):
        """清理旧的执行记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            exec_id for exec_id, execution in self.executions.items()
            if (execution.end_time and execution.end_time < cutoff_date)
        ]
        
        for exec_id in to_remove:
            del self.executions[exec_id]
        
        logger.info(f"清理了 {len(to_remove)} 个旧执行记录")

# 示例使用
async def main():
    """示例主函数"""
    engine = ZenWorkflowEngine()
    
    # 创建示例工作流
    workflow = WorkflowDefinition(
        workflow_id="example_workflow",
        name="示例开发工作流",
        description="完整的代码开发工作流",
        tasks=[
            WorkflowTask(
                task_id="analyze",
                tool_name="code_analyzer",
                parameters={"source_code": "def hello(): pass"}
            ),
            WorkflowTask(
                task_id="generate",
                tool_name="code_generator",
                parameters={"requirements": "生成测试函数"},
                dependencies=["analyze"]
            ),
            WorkflowTask(
                task_id="test",
                tool_name="test_runner",
                parameters={"test_files": ["test_*.py"]},
                dependencies=["generate"]
            )
        ],
        strategy=ExecutionStrategy.SEQUENTIAL
    )
    
    # 注册工作流
    await engine.register_workflow(workflow)
    
    # 执行工作流
    execution_id = await engine.execute_workflow("example_workflow")
    
    # 监控执行
    while True:
        status = await engine.get_execution_status(execution_id)
        if status and status.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
            break
        await asyncio.sleep(1)
    
    # 获取结果
    final_status = await engine.get_execution_status(execution_id)
    print(f"工作流执行完成: {final_status.status.value}")
    
    # 获取性能统计
    stats = await engine.get_performance_stats()
    print(f"性能统计: {stats}")

if __name__ == "__main__":
    asyncio.run(main())

