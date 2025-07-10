"""
PowerAutomation 4.0 Parallel Executor
并行执行器，支持异步并行任务执行
"""

import asyncio
import uuid
import time
import logging
from typing import Dict, List, Any, Callable, Optional, Coroutine
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading

from .config import get_config


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务数据类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    timeout: Optional[int] = None
    priority: int = 0  # 优先级，数字越大优先级越高


class ParallelExecutor:
    """并行执行器类"""
    
    def __init__(self, max_concurrent_tasks: Optional[int] = None):
        self.config = get_config()
        self.max_concurrent_tasks = max_concurrent_tasks or self.config.max_concurrent_tasks
        self.logger = logging.getLogger(__name__)
        
        # 任务管理
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        # 线程池执行器（用于CPU密集型任务）
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_concurrent_tasks)
        
        # 事件循环和控制
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0
        }
    
    async def start(self):
        """启动并行执行器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())
        self.logger.info(f"并行执行器已启动，最大并发任务数: {self.max_concurrent_tasks}")
    
    async def stop(self):
        """停止并行执行器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 取消所有运行中的任务
        for task_id, task in self.running_tasks.items():
            task.cancel()
            self.tasks[task_id].status = TaskStatus.CANCELLED
            self.stats["cancelled_tasks"] += 1
        
        # 等待worker任务完成
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # 关闭线程池
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("并行执行器已停止")
    
    async def submit_async_task(
        self, 
        func: Callable, 
        *args, 
        name: str = "", 
        timeout: Optional[int] = None,
        priority: int = 0,
        **kwargs
    ) -> str:
        """提交异步任务"""
        task = Task(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            timeout=timeout or self.config.task_timeout,
            priority=priority
        )
        
        self.tasks[task.id] = task
        await self.task_queue.put(task)
        self.stats["total_tasks"] += 1
        
        self.logger.info(f"已提交异步任务: {task.name} (ID: {task.id})")
        return task.id
    
    async def submit_sync_task(
        self, 
        func: Callable, 
        *args, 
        name: str = "", 
        timeout: Optional[int] = None,
        priority: int = 0,
        **kwargs
    ) -> str:
        """提交同步任务（在线程池中执行）"""
        async def wrapper():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.thread_pool, func, *args)
        
        return await self.submit_async_task(
            wrapper, 
            name=name or f"sync_{func.__name__}",
            timeout=timeout,
            priority=priority
        )
    
    async def submit_command_task(
        self,
        command: str,
        args: List[str] = None,
        timeout: Optional[int] = None,
        priority: int = 0
    ) -> str:
        """提交命令任务"""
        async def execute_command():
            from ..command_master.command_executor import CommandExecutor
            executor = CommandExecutor()
            return await executor.execute_command(command, args or [])
        
        return await self.submit_async_task(
            execute_command,
            name=f"command_{command}",
            timeout=timeout,
            priority=priority
        )
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        return task.status if task else None
    
    async def get_task_result(self, task_id: str) -> Any:
        """获取任务结果"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        if task.status == TaskStatus.COMPLETED:
            return task.result
        elif task.status == TaskStatus.FAILED:
            raise task.error
        elif task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise ValueError(f"任务尚未完成: {task_id}")
        else:
            raise ValueError(f"任务已取消: {task_id}")
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待任务完成并返回结果"""
        start_time = time.time()
        
        while True:
            task = self.tasks.get(task_id)
            if not task:
                raise ValueError(f"任务不存在: {task_id}")
            
            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED:
                raise task.error
            elif task.status == TaskStatus.CANCELLED:
                raise asyncio.CancelledError(f"任务已取消: {task_id}")
            
            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"等待任务超时: {task_id}")
            
            await asyncio.sleep(0.1)
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        # 如果任务正在运行，取消asyncio任务
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = time.time()
        self.stats["cancelled_tasks"] += 1
        
        self.logger.info(f"已取消任务: {task.name} (ID: {task_id})")
        return True
    
    async def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取正在运行的任务列表"""
        running_tasks = []
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.RUNNING:
                running_tasks.append({
                    "id": task_id,
                    "name": task.name,
                    "started_at": task.started_at,
                    "duration": time.time() - (task.started_at or 0)
                })
        return running_tasks
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取执行器统计信息"""
        return {
            **self.stats,
            "running_tasks": len(self.running_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
    
    async def _worker(self):
        """工作线程，处理任务队列"""
        self.logger.info("并行执行器工作线程已启动")
        
        while self.is_running:
            try:
                # 获取任务（带超时，避免阻塞）
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 检查是否还在运行
                if not self.is_running:
                    break
                
                # 使用信号量控制并发数
                await self.semaphore.acquire()
                
                # 创建并启动任务
                asyncio_task = asyncio.create_task(self._execute_task(task))
                self.running_tasks[task.id] = asyncio_task
                
                # 不等待任务完成，继续处理下一个任务
                
            except Exception as e:
                self.logger.error(f"工作线程错误: {e}")
                await asyncio.sleep(1)
        
        self.logger.info("并行执行器工作线程已停止")
    
    async def _execute_task(self, task: Task):
        """执行单个任务"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            
            self.logger.info(f"开始执行任务: {task.name} (ID: {task.id})")
            
            # 执行任务（带超时）
            if asyncio.iscoroutinefunction(task.func):
                if task.timeout:
                    result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs), 
                        timeout=task.timeout
                    )
                else:
                    result = await task.func(*task.args, **task.kwargs)
            else:
                # 同步函数在线程池中执行
                loop = asyncio.get_event_loop()
                if task.timeout:
                    result = await asyncio.wait_for(
                        loop.run_in_executor(self.thread_pool, task.func, *task.args),
                        timeout=task.timeout
                    )
                else:
                    result = await loop.run_in_executor(self.thread_pool, task.func, *task.args)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            self.stats["completed_tasks"] += 1
            
            duration = task.completed_at - task.started_at
            self.logger.info(f"任务完成: {task.name} (ID: {task.id}), 耗时: {duration:.2f}秒")
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
            self.stats["cancelled_tasks"] += 1
            self.logger.info(f"任务已取消: {task.name} (ID: {task.id})")
            
        except Exception as e:
            task.error = e
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            self.stats["failed_tasks"] += 1
            self.logger.error(f"任务失败: {task.name} (ID: {task.id}), 错误: {e}")
            
        finally:
            # 清理
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            self.semaphore.release()


# 全局并行执行器实例
_executor: Optional[ParallelExecutor] = None


async def get_executor() -> ParallelExecutor:
    """获取全局并行执行器实例"""
    global _executor
    if _executor is None:
        _executor = ParallelExecutor()
        await _executor.start()
    return _executor


async def shutdown_executor():
    """关闭全局并行执行器"""
    global _executor
    if _executor:
        await _executor.stop()
        _executor = None

