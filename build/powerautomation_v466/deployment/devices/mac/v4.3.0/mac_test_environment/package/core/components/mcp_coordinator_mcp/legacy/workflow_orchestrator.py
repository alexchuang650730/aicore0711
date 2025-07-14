"""
PowerAutomation 4.0 Workflow Orchestrator
工作流编排器 - 负责协调和编排复杂的多MCP工作流
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
from enum import Enum

from core.exceptions import WorkflowError, handle_exception
from core.logging_config import get_mcp_logger
from core.config import get_config


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StepStatus(Enum):
    """步骤状态枚举"""
    WAITING = "waiting"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionMode(Enum):
    """执行模式枚举"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    name: str
    mcp_id: str
    method: str
    params: Dict[str, Any]
    dependencies: List[str]
    timeout: int
    retry_count: int
    max_retries: int
    status: StepStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    execution_mode: ExecutionMode
    timeout: int
    max_retries: int
    metadata: Dict[str, Any]
    created_at: datetime
    created_by: str


@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    execution_id: str
    workflow_id: str
    definition: WorkflowDefinition
    status: WorkflowStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    context: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time: Optional[float]
    error: Optional[str]
    retry_count: int
    current_step: Optional[str]
    completed_steps: List[str]
    failed_steps: List[str]


class WorkflowOrchestrator:
    """工作流编排器"""
    
    def __init__(self):
        self.logger = get_mcp_logger()
        self.config = get_config()
        
        # 工作流存储
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []
        
        # 执行器
        self.step_executors: Dict[str, Callable] = {}
        self.condition_evaluators: Dict[str, Callable] = {}
        
        # 调度器
        self.scheduler_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        
        # 统计信息
        self.stats = {
            "total_workflows": 0,
            "active_executions": 0,
            "completed_workflows": 0,
            "failed_workflows": 0,
            "total_steps_executed": 0,
            "average_execution_time": 0.0
        }
        
        # 配置参数
        self.max_concurrent_executions = 10
        self.default_step_timeout = 300  # 5分钟
        self.default_workflow_timeout = 3600  # 1小时
        self.cleanup_interval = 300  # 5分钟
    
    async def initialize(self) -> bool:
        """初始化工作流编排器"""
        try:
            self.logger.info("初始化工作流编排器...")
            
            # 注册默认步骤执行器
            await self._register_default_executors()
            
            # 启动调度器
            self.is_running = True
            self.scheduler_tasks["main"] = asyncio.create_task(self._main_scheduler())
            self.scheduler_tasks["cleanup"] = asyncio.create_task(self._cleanup_scheduler())
            
            self.logger.info("工作流编排器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"工作流编排器初始化失败: {e}")
            return False
    
    async def register_workflow(self, definition: WorkflowDefinition) -> bool:
        """注册工作流定义"""
        try:
            # 验证工作流定义
            if not await self._validate_workflow_definition(definition):
                raise WorkflowError(f"工作流定义验证失败: {definition.workflow_id}")
            
            # 存储工作流定义
            self.workflow_definitions[definition.workflow_id] = definition
            self.stats["total_workflows"] += 1
            
            self.logger.info(f"工作流已注册: {definition.name} ({definition.workflow_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"注册工作流失败: {e}")
            return False
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> str:
        """执行工作流"""
        try:
            # 检查工作流定义是否存在
            if workflow_id not in self.workflow_definitions:
                raise WorkflowError(f"工作流定义不存在: {workflow_id}")
            
            # 检查并发执行限制
            if len(self.active_executions) >= self.max_concurrent_executions:
                raise WorkflowError("达到最大并发执行限制")
            
            # 创建执行实例
            execution_id = str(uuid.uuid4())
            definition = self.workflow_definitions[workflow_id]
            
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                definition=definition,
                status=WorkflowStatus.PENDING,
                input_data=input_data,
                output_data=None,
                context=context or {},
                started_at=None,
                completed_at=None,
                execution_time=None,
                error=None,
                retry_count=0,
                current_step=None,
                completed_steps=[],
                failed_steps=[]
            )
            
            # 添加到活跃执行列表
            self.active_executions[execution_id] = execution
            self.stats["active_executions"] += 1
            
            # 启动执行任务
            self.scheduler_tasks[execution_id] = asyncio.create_task(
                self._execute_workflow_instance(execution)
            )
            
            self.logger.info(f"工作流执行已启动: {definition.name} ({execution_id})")
            return execution_id
            
        except Exception as e:
            self.logger.error(f"启动工作流执行失败: {e}")
            raise WorkflowError(f"启动工作流执行失败: {str(e)}")
    
    async def _execute_workflow_instance(self, execution: WorkflowExecution):
        """执行工作流实例"""
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now()
            
            self.logger.info(f"开始执行工作流: {execution.workflow_id} ({execution.execution_id})")
            
            # 根据执行模式执行步骤
            if execution.definition.execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential_steps(execution)
            elif execution.definition.execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel_steps(execution)
            elif execution.definition.execution_mode == ExecutionMode.CONDITIONAL:
                await self._execute_conditional_steps(execution)
            elif execution.definition.execution_mode == ExecutionMode.LOOP:
                await self._execute_loop_steps(execution)
            
            # 完成执行
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
            
            # 收集输出数据
            execution.output_data = await self._collect_output_data(execution)
            
            self.logger.info(f"工作流执行完成: {execution.execution_id}, 耗时: {execution.execution_time:.2f}秒")
            
        except Exception as e:
            # 执行失败
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now()
            
            if execution.started_at:
                execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
            
            self.logger.error(f"工作流执行失败: {execution.execution_id}, 错误: {e}")
            
        finally:
            # 清理和统计
            await self._finalize_execution(execution)
    
    async def _execute_sequential_steps(self, execution: WorkflowExecution):
        """顺序执行步骤"""
        for step in execution.definition.steps:
            # 检查依赖
            if not await self._check_step_dependencies(step, execution):
                step.status = StepStatus.SKIPPED
                continue
            
            # 执行步骤
            await self._execute_step(step, execution)
            
            # 检查步骤执行结果
            if step.status == StepStatus.FAILED:
                if step.retry_count < step.max_retries:
                    # 重试
                    step.retry_count += 1
                    await self._execute_step(step, execution)
                
                if step.status == StepStatus.FAILED:
                    # 步骤失败，终止工作流
                    execution.failed_steps.append(step.step_id)
                    raise WorkflowError(f"步骤执行失败: {step.name}")
            
            execution.completed_steps.append(step.step_id)
            execution.current_step = step.step_id
    
    async def _execute_parallel_steps(self, execution: WorkflowExecution):
        """并行执行步骤"""
        # 创建步骤执行任务
        step_tasks = []
        for step in execution.definition.steps:
            if await self._check_step_dependencies(step, execution):
                task = asyncio.create_task(self._execute_step(step, execution))
                step_tasks.append((step, task))
            else:
                step.status = StepStatus.SKIPPED
        
        # 等待所有步骤完成
        for step, task in step_tasks:
            try:
                await task
                if step.status == StepStatus.COMPLETED:
                    execution.completed_steps.append(step.step_id)
                else:
                    execution.failed_steps.append(step.step_id)
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                execution.failed_steps.append(step.step_id)
        
        # 检查是否有失败的步骤
        if execution.failed_steps:
            raise WorkflowError(f"并行执行中有步骤失败: {execution.failed_steps}")
    
    async def _execute_conditional_steps(self, execution: WorkflowExecution):
        """条件执行步骤"""
        for step in execution.definition.steps:
            # 评估条件
            condition_result = await self._evaluate_step_condition(step, execution)
            
            if condition_result:
                await self._execute_step(step, execution)
                if step.status == StepStatus.COMPLETED:
                    execution.completed_steps.append(step.step_id)
                else:
                    execution.failed_steps.append(step.step_id)
            else:
                step.status = StepStatus.SKIPPED
    
    async def _execute_loop_steps(self, execution: WorkflowExecution):
        """循环执行步骤"""
        loop_condition = execution.definition.metadata.get("loop_condition", {})
        max_iterations = loop_condition.get("max_iterations", 10)
        
        for iteration in range(max_iterations):
            # 检查循环条件
            if not await self._evaluate_loop_condition(loop_condition, execution, iteration):
                break
            
            # 执行所有步骤
            for step in execution.definition.steps:
                await self._execute_step(step, execution)
                if step.status == StepStatus.FAILED:
                    execution.failed_steps.append(f"{step.step_id}_iter_{iteration}")
                else:
                    execution.completed_steps.append(f"{step.step_id}_iter_{iteration}")
    
    async def _execute_step(self, step: WorkflowStep, execution: WorkflowExecution):
        """执行单个步骤"""
        try:
            step.status = StepStatus.RUNNING
            step.started_at = datetime.now()
            execution.current_step = step.step_id
            
            self.logger.debug(f"执行步骤: {step.name} ({step.step_id})")
            
            # 准备步骤参数
            step_params = await self._prepare_step_params(step, execution)
            
            # 查找步骤执行器
            executor_key = f"{step.mcp_id}.{step.method}"
            if executor_key in self.step_executors:
                executor = self.step_executors[executor_key]
                step.result = await executor(step_params, execution.context)
            else:
                # 使用默认MCP调用
                step.result = await self._call_mcp_method(
                    step.mcp_id, step.method, step_params
                )
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            step.execution_time = (step.completed_at - step.started_at).total_seconds()
            
            self.stats["total_steps_executed"] += 1
            
            self.logger.debug(f"步骤执行完成: {step.name}, 耗时: {step.execution_time:.2f}秒")
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            
            if step.started_at:
                step.execution_time = (step.completed_at - step.started_at).total_seconds()
            
            self.logger.error(f"步骤执行失败: {step.name}, 错误: {e}")
    
    async def _check_step_dependencies(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """检查步骤依赖"""
        if not step.dependencies:
            return True
        
        # 检查所有依赖步骤是否已完成
        for dep_step_id in step.dependencies:
            if dep_step_id not in execution.completed_steps:
                return False
        
        return True
    
    async def _evaluate_step_condition(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """评估步骤条件"""
        condition = step.params.get("condition")
        if not condition:
            return True
        
        # 这里可以实现复杂的条件评估逻辑
        # 暂时返回True
        return True
    
    async def _evaluate_loop_condition(
        self, 
        loop_condition: Dict[str, Any], 
        execution: WorkflowExecution, 
        iteration: int
    ) -> bool:
        """评估循环条件"""
        # 检查最大迭代次数
        max_iterations = loop_condition.get("max_iterations", 10)
        if iteration >= max_iterations:
            return False
        
        # 这里可以实现复杂的循环条件评估逻辑
        return True
    
    async def _prepare_step_params(self, step: WorkflowStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """准备步骤参数"""
        params = step.params.copy()
        
        # 替换上下文变量
        params = await self._substitute_context_variables(params, execution)
        
        # 添加执行上下文
        params["_execution_context"] = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "step_id": step.step_id,
            "input_data": execution.input_data
        }
        
        return params
    
    async def _substitute_context_variables(
        self, 
        params: Dict[str, Any], 
        execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """替换上下文变量"""
        # 这里可以实现变量替换逻辑
        # 例如：${input.user_id} -> execution.input_data["user_id"]
        return params
    
    async def _call_mcp_method(self, mcp_id: str, method: str, params: Dict[str, Any]) -> Any:
        """调用MCP方法"""
        # 这里应该通过通信中心调用MCP方法
        # 暂时返回模拟结果
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return {"success": True, "data": f"Result from {mcp_id}.{method}"}
    
    async def _collect_output_data(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """收集输出数据"""
        output_data = {}
        
        for step in execution.definition.steps:
            if step.status == StepStatus.COMPLETED and step.result:
                output_data[step.step_id] = step.result
        
        return output_data
    
    async def _finalize_execution(self, execution: WorkflowExecution):
        """完成执行清理"""
        try:
            # 从活跃执行列表中移除
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
                self.stats["active_executions"] -= 1
            
            # 添加到历史记录
            self.execution_history.append(execution)
            
            # 保持历史记录在合理范围内
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-800:]
            
            # 更新统计
            if execution.status == WorkflowStatus.COMPLETED:
                self.stats["completed_workflows"] += 1
            elif execution.status == WorkflowStatus.FAILED:
                self.stats["failed_workflows"] += 1
            
            # 更新平均执行时间
            if execution.execution_time:
                total_completed = self.stats["completed_workflows"]
                if total_completed > 0:
                    current_avg = self.stats["average_execution_time"]
                    new_avg = (current_avg * (total_completed - 1) + execution.execution_time) / total_completed
                    self.stats["average_execution_time"] = new_avg
            
            # 清理调度任务
            if execution.execution_id in self.scheduler_tasks:
                del self.scheduler_tasks[execution.execution_id]
            
        except Exception as e:
            self.logger.error(f"完成执行清理失败: {e}")
    
    async def _validate_workflow_definition(self, definition: WorkflowDefinition) -> bool:
        """验证工作流定义"""
        try:
            # 基础验证
            if not definition.workflow_id or not definition.name:
                return False
            
            if not definition.steps:
                return False
            
            # 验证步骤依赖
            step_ids = {step.step_id for step in definition.steps}
            for step in definition.steps:
                for dep_id in step.dependencies:
                    if dep_id not in step_ids:
                        self.logger.error(f"步骤依赖不存在: {dep_id}")
                        return False
            
            # 检查循环依赖
            if await self._has_circular_dependencies(definition.steps):
                self.logger.error("检测到循环依赖")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证工作流定义失败: {e}")
            return False
    
    async def _has_circular_dependencies(self, steps: List[WorkflowStep]) -> bool:
        """检查循环依赖"""
        # 使用拓扑排序检查循环依赖
        # 这里简化实现
        return False
    
    async def _register_default_executors(self):
        """注册默认步骤执行器"""
        # 这里可以注册一些默认的步骤执行器
        pass
    
    async def _main_scheduler(self):
        """主调度器"""
        while self.is_running:
            try:
                # 检查超时的执行
                await self._check_execution_timeouts()
                
                # 短暂休眠
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"主调度器异常: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_scheduler(self):
        """清理调度器"""
        while self.is_running:
            try:
                # 清理过期的执行历史
                await self._cleanup_execution_history()
                
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理调度器异常: {e}")
                await asyncio.sleep(10)
    
    async def _check_execution_timeouts(self):
        """检查执行超时"""
        current_time = datetime.now()
        
        for execution in list(self.active_executions.values()):
            if execution.started_at:
                elapsed_time = (current_time - execution.started_at).total_seconds()
                if elapsed_time > execution.definition.timeout:
                    # 执行超时
                    execution.status = WorkflowStatus.TIMEOUT
                    execution.error = f"工作流执行超时: {elapsed_time}秒"
                    execution.completed_at = current_time
                    execution.execution_time = elapsed_time
                    
                    # 取消执行任务
                    if execution.execution_id in self.scheduler_tasks:
                        self.scheduler_tasks[execution.execution_id].cancel()
                    
                    await self._finalize_execution(execution)
                    
                    self.logger.warning(f"工作流执行超时: {execution.execution_id}")
    
    async def _cleanup_execution_history(self):
        """清理执行历史"""
        # 清理超过一定时间的执行历史
        cutoff_time = datetime.now() - timedelta(days=7)
        
        original_count = len(self.execution_history)
        self.execution_history = [
            execution for execution in self.execution_history
            if execution.completed_at and execution.completed_at > cutoff_time
        ]
        
        cleaned_count = original_count - len(self.execution_history)
        if cleaned_count > 0:
            self.logger.info(f"清理了 {cleaned_count} 个过期的执行历史记录")
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流执行状态"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
        else:
            # 在历史记录中查找
            execution = next(
                (ex for ex in self.execution_history if ex.execution_id == execution_id),
                None
            )
        
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "completed_steps": execution.completed_steps,
            "failed_steps": execution.failed_steps,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "execution_time": execution.execution_time,
            "error": execution.error
        }
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """获取编排器统计信息"""
        return {
            **self.stats,
            "registered_workflows": len(self.workflow_definitions),
            "active_executions": len(self.active_executions),
            "execution_history_count": len(self.execution_history),
            "is_running": self.is_running
        }
    
    async def shutdown(self):
        """关闭工作流编排器"""
        try:
            self.logger.info("关闭工作流编排器...")
            
            self.is_running = False
            
            # 取消所有调度任务
            for task in self.scheduler_tasks.values():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("工作流编排器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭工作流编排器失败: {e}")


# 全局工作流编排器实例
_workflow_orchestrator: Optional[WorkflowOrchestrator] = None


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """获取全局工作流编排器实例"""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = WorkflowOrchestrator()
    return _workflow_orchestrator

