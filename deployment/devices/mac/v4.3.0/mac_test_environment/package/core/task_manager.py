"""
PowerAutomation 4.0 Task Manager
任务管理器，提供高级任务管理功能
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid

from .parallel_executor import ParallelExecutor, TaskStatus, get_executor
from .event_bus import EventBus, EventType, get_event_bus
from .config import get_config


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class TaskRequest:
    """任务请求数据类"""
    name: str
    command: Optional[str] = None
    function: Optional[Callable] = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskInfo:
    """任务信息数据类"""
    id: str
    request: TaskRequest
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies_resolved: bool = False


class TaskManager:
    """任务管理器类"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.executor: Optional[ParallelExecutor] = None
        self.event_bus: EventBus = get_event_bus()
        
        # 任务管理
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_dependencies: Dict[str, List[str]] = {}  # 任务ID -> 依赖它的任务ID列表
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0
        }
    
    async def initialize(self):
        """初始化任务管理器"""
        self.executor = await get_executor()
        
        # 订阅执行器事件
        await self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        await self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
        await self.event_bus.subscribe(EventType.TASK_CANCELLED, self._on_task_cancelled)
        
        self.logger.info("任务管理器已初始化")
    
    async def submit_task(self, request: TaskRequest) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        
        # 创建任务信息
        task_info = TaskInfo(
            id=task_id,
            request=request,
            status=TaskStatus.PENDING
        )
        
        self.tasks[task_id] = task_info
        self.stats["total_tasks"] += 1
        
        # 处理依赖关系
        if request.dependencies:
            for dep_id in request.dependencies:
                if dep_id not in self.task_dependencies:
                    self.task_dependencies[dep_id] = []
                self.task_dependencies[dep_id].append(task_id)
        else:
            task_info.dependencies_resolved = True
        
        # 发布任务创建事件
        await self.event_bus.publish(
            EventType.TASK_CREATED,
            "task_manager",
            {
                "task_id": task_id,
                "name": request.name,
                "priority": request.priority.value,
                "dependencies": request.dependencies
            }
        )
        
        # 如果依赖已解决，立即执行
        if task_info.dependencies_resolved:
            await self._execute_task(task_info)
        
        self.logger.info(f"已提交任务: {request.name} (ID: {task_id})")
        return task_id
    
    async def submit_command_task(
        self,
        command: str,
        args: List[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[int] = None,
        dependencies: List[str] = None
    ) -> str:
        """提交命令任务"""
        request = TaskRequest(
            name=f"command_{command}",
            command=command,
            args=args or [],
            priority=priority,
            timeout=timeout,
            dependencies=dependencies or []
        )
        return await self.submit_task(request)
    
    async def submit_function_task(
        self,
        function: Callable,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        name: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[int] = None,
        dependencies: List[str] = None
    ) -> str:
        """提交函数任务"""
        request = TaskRequest(
            name=name or function.__name__,
            function=function,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            timeout=timeout,
            dependencies=dependencies or []
        )
        return await self.submit_task(request)
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task_info = self.tasks.get(task_id)
        if not task_info:
            return None
        
        # 如果任务已提交给执行器，从执行器获取最新状态
        if task_info.status in [TaskStatus.RUNNING]:
            executor_status = await self.executor.get_task_status(task_id)
            if executor_status:
                task_info.status = executor_status
        
        return task_info.status
    
    async def get_task_result(self, task_id: str) -> Any:
        """获取任务结果"""
        task_info = self.tasks.get(task_id)
        if not task_info:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 如果任务已完成，返回结果
        if task_info.status == TaskStatus.COMPLETED:
            if task_info.result is None:
                # 从执行器获取结果
                try:
                    task_info.result = await self.executor.get_task_result(task_id)
                except Exception as e:
                    task_info.error = e
                    task_info.status = TaskStatus.FAILED
                    raise e
            return task_info.result
        
        elif task_info.status == TaskStatus.FAILED:
            raise task_info.error or Exception("任务执行失败")
        
        elif task_info.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise ValueError(f"任务尚未完成: {task_id}")
        
        else:
            raise ValueError(f"任务已取消: {task_id}")
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待任务完成并返回结果"""
        task_info = self.tasks.get(task_id)
        if not task_info:
            raise ValueError(f"任务不存在: {task_id}")
        
        # 如果任务已提交给执行器，使用执行器的等待方法
        if task_info.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED]:
            try:
                result = await self.executor.wait_for_task(task_id, timeout)
                task_info.result = result
                task_info.status = TaskStatus.COMPLETED
                return result
            except Exception as e:
                task_info.error = e
                task_info.status = TaskStatus.FAILED
                raise e
        
        # 否则等待任务状态变化
        start_time = time.time()
        while True:
            if task_info.status == TaskStatus.COMPLETED:
                return await self.get_task_result(task_id)
            elif task_info.status == TaskStatus.FAILED:
                raise task_info.error or Exception("任务执行失败")
            elif task_info.status == TaskStatus.CANCELLED:
                raise asyncio.CancelledError(f"任务已取消: {task_id}")
            
            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"等待任务超时: {task_id}")
            
            await asyncio.sleep(0.1)
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task_info = self.tasks.get(task_id)
        if not task_info:
            return False
        
        # 如果任务正在执行器中运行，取消执行器任务
        if task_info.status == TaskStatus.RUNNING:
            success = await self.executor.cancel_task(task_id)
            if success:
                task_info.status = TaskStatus.CANCELLED
                task_info.completed_at = time.time()
                self.stats["cancelled_tasks"] += 1
                
                # 发布取消事件
                await self.event_bus.publish(
                    EventType.TASK_CANCELLED,
                    "task_manager",
                    {"task_id": task_id, "name": task_info.request.name}
                )
            return success
        
        elif task_info.status == TaskStatus.PENDING:
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = time.time()
            self.stats["cancelled_tasks"] += 1
            
            # 发布取消事件
            await self.event_bus.publish(
                EventType.TASK_CANCELLED,
                "task_manager",
                {"task_id": task_id, "name": task_info.request.name}
            )
            return True
        
        return False
    
    async def get_task_list(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取任务列表"""
        tasks = []
        for task_info in self.tasks.values():
            if status is None or task_info.status == status:
                tasks.append({
                    "id": task_info.id,
                    "name": task_info.request.name,
                    "status": task_info.status.value,
                    "priority": task_info.request.priority.value,
                    "created_at": task_info.created_at,
                    "started_at": task_info.started_at,
                    "completed_at": task_info.completed_at,
                    "dependencies": task_info.request.dependencies,
                    "dependencies_resolved": task_info.dependencies_resolved
                })
        
        # 按创建时间排序
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return tasks[:limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        executor_stats = await self.executor.get_stats() if self.executor else {}
        
        return {
            **self.stats,
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "running_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            "executor_stats": executor_stats
        }
    
    async def _execute_task(self, task_info: TaskInfo):
        """执行任务"""
        if not task_info.dependencies_resolved:
            return
        
        request = task_info.request
        
        try:
            if request.command:
                # 执行命令任务
                executor_task_id = await self.executor.submit_command_task(
                    request.command,
                    request.args,
                    timeout=request.timeout,
                    priority=request.priority.value
                )
            elif request.function:
                # 执行函数任务
                if asyncio.iscoroutinefunction(request.function):
                    executor_task_id = await self.executor.submit_async_task(
                        request.function,
                        *request.args,
                        name=request.name,
                        timeout=request.timeout,
                        priority=request.priority.value,
                        **request.kwargs
                    )
                else:
                    executor_task_id = await self.executor.submit_sync_task(
                        request.function,
                        *request.args,
                        name=request.name,
                        timeout=request.timeout,
                        priority=request.priority.value,
                        **request.kwargs
                    )
            else:
                raise ValueError("任务必须指定命令或函数")
            
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = time.time()
            
            # 发布任务开始事件
            await self.event_bus.publish(
                EventType.TASK_STARTED,
                "task_manager",
                {
                    "task_id": task_info.id,
                    "name": request.name,
                    "executor_task_id": executor_task_id
                }
            )
            
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.error = e
            task_info.completed_at = time.time()
            self.stats["failed_tasks"] += 1
            
            # 发布任务失败事件
            await self.event_bus.publish(
                EventType.TASK_FAILED,
                "task_manager",
                {
                    "task_id": task_info.id,
                    "name": request.name,
                    "error": str(e)
                }
            )
    
    async def _check_dependencies(self, task_id: str):
        """检查并解决任务依赖"""
        task_info = self.tasks.get(task_id)
        if not task_info or task_info.dependencies_resolved:
            return
        
        # 检查所有依赖是否已完成
        all_resolved = True
        for dep_id in task_info.request.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                all_resolved = False
                break
        
        if all_resolved:
            task_info.dependencies_resolved = True
            await self._execute_task(task_info)
    
    async def _on_task_completed(self, event):
        """处理任务完成事件"""
        task_id = event.data.get("task_id")
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].completed_at = time.time()
            self.stats["completed_tasks"] += 1
            
            # 检查依赖此任务的其他任务
            if task_id in self.task_dependencies:
                for dependent_task_id in self.task_dependencies[task_id]:
                    await self._check_dependencies(dependent_task_id)
    
    async def _on_task_failed(self, event):
        """处理任务失败事件"""
        task_id = event.data.get("task_id")
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].completed_at = time.time()
            self.stats["failed_tasks"] += 1
    
    async def _on_task_cancelled(self, event):
        """处理任务取消事件"""
        task_id = event.data.get("task_id")
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.CANCELLED
            self.tasks[task_id].completed_at = time.time()
            self.stats["cancelled_tasks"] += 1


# 全局任务管理器实例
_task_manager: Optional[TaskManager] = None


async def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
        await _task_manager.initialize()
    return _task_manager

