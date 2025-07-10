"""
PowerAutomation 4.0 Task Dispatcher
任务分发器 - 负责智能任务分发、优先级管理和负载均衡
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
from enum import Enum
import heapq

from ..shared.agent_base import AgentTask, TaskPriority, AgentStatus
from core.exceptions import TaskDispatchError, handle_exception
from core.logging_config import get_task_logger
from core.config import get_config
from core.event_bus import EventType, get_event_bus


class DispatchStrategy(Enum):
    """分发策略枚举"""
    FIFO = "fifo"  # 先进先出
    PRIORITY = "priority"  # 优先级
    DEADLINE = "deadline"  # 截止时间
    LOAD_BALANCED = "load_balanced"  # 负载均衡
    INTELLIGENT = "intelligent"  # 智能分发


class TaskStatus(Enum):
    """任务状态枚举"""
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class QueuedTask:
    """队列中的任务"""
    task: AgentTask
    queue_time: datetime
    dispatch_time: Optional[datetime]
    deadline: Optional[datetime]
    retry_count: int
    max_retries: int
    status: TaskStatus
    assigned_agent: Optional[str]
    dispatch_attempts: List[Dict[str, Any]]
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        # 首先按优先级排序
        if self.task.priority != other.task.priority:
            return self.task.priority.value > other.task.priority.value
        
        # 然后按截止时间排序
        if self.deadline and other.deadline:
            return self.deadline < other.deadline
        elif self.deadline:
            return True
        elif other.deadline:
            return False
        
        # 最后按队列时间排序
        return self.queue_time < other.queue_time


@dataclass
class DispatchRule:
    """分发规则"""
    rule_id: str
    name: str
    condition: Callable[[AgentTask], bool]
    target_agents: List[str]
    priority_boost: int
    enabled: bool


class TaskDispatcher:
    """任务分发器"""
    
    def __init__(self):
        self.logger = get_task_logger()
        self.config = get_config()
        self.event_bus = get_event_bus()
        
        # 任务队列
        self.task_queues: Dict[TaskPriority, List[QueuedTask]] = {
            priority: [] for priority in TaskPriority
        }
        self.task_index: Dict[str, QueuedTask] = {}
        
        # 分发规则
        self.dispatch_rules: Dict[str, DispatchRule] = {}
        self.default_strategy = DispatchStrategy.INTELLIGENT
        
        # 智能体状态跟踪
        self.agent_workloads: Dict[str, int] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        
        # 分发统计
        self.dispatch_stats = {
            "total_tasks_received": 0,
            "total_tasks_dispatched": 0,
            "successful_dispatches": 0,
            "failed_dispatches": 0,
            "average_queue_time": 0.0,
            "average_dispatch_time": 0.0,
            "dispatcher_start_time": datetime.now()
        }
        
        # 运行状态
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # 配置参数
        self.max_queue_size = 1000
        self.dispatch_interval = 1.0  # 秒
        self.task_timeout = 300  # 秒
        self.max_retries = 3
        self.cleanup_interval = 300  # 秒
    
    async def initialize(self) -> bool:
        """初始化任务分发器"""
        try:
            self.logger.info("初始化任务分发器...")
            
            # 注册默认分发规则
            await self._register_default_rules()
            
            # 注册事件处理器
            await self._register_event_handlers()
            
            # 启动工作线程
            self.is_running = True
            self.worker_tasks = [
                asyncio.create_task(self._dispatch_worker()),
                asyncio.create_task(self._timeout_monitor()),
                asyncio.create_task(self._performance_monitor()),
                asyncio.create_task(self._cleanup_worker())
            ]
            
            self.logger.info("任务分发器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"任务分发器初始化失败: {e}")
            return False
    
    async def submit_task(self, task: AgentTask, deadline: Optional[datetime] = None) -> str:
        """提交任务到分发队列"""
        try:
            # 检查队列容量
            total_queued = sum(len(queue) for queue in self.task_queues.values())
            if total_queued >= self.max_queue_size:
                raise TaskDispatchError("任务队列已满")
            
            # 应用分发规则
            await self._apply_dispatch_rules(task)
            
            # 创建队列任务
            queued_task = QueuedTask(
                task=task,
                queue_time=datetime.now(),
                dispatch_time=None,
                deadline=deadline,
                retry_count=0,
                max_retries=self.max_retries,
                status=TaskStatus.QUEUED,
                assigned_agent=None,
                dispatch_attempts=[]
            )
            
            # 添加到队列
            priority_queue = self.task_queues[task.priority]
            heapq.heappush(priority_queue, queued_task)
            self.task_index[task.task_id] = queued_task
            
            # 更新统计
            self.dispatch_stats["total_tasks_received"] += 1
            
            # 发送事件
            await self.event_bus.emit(EventType.TASK_QUEUED, {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "priority": task.priority.value,
                "queue_time": queued_task.queue_time.isoformat()
            })
            
            self.logger.info(f"任务已提交到队列: {task.task_id} ({task.task_type})")
            return task.task_id
            
        except Exception as e:
            self.logger.error(f"提交任务失败: {e}")
            raise TaskDispatchError(f"提交任务失败: {str(e)}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id not in self.task_index:
                self.logger.warning(f"任务不存在: {task_id}")
                return False
            
            queued_task = self.task_index[task_id]
            
            if queued_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                self.logger.warning(f"任务已完成或取消: {task_id}")
                return False
            
            # 标记为取消
            queued_task.status = TaskStatus.CANCELLED
            
            # 从队列中移除
            priority_queue = self.task_queues[queued_task.task.priority]
            if queued_task in priority_queue:
                priority_queue.remove(queued_task)
                heapq.heapify(priority_queue)
            
            # 发送事件
            await self.event_bus.emit(EventType.TASK_CANCELLED, {
                "task_id": task_id,
                "cancelled_at": datetime.now().isoformat()
            })
            
            self.logger.info(f"任务已取消: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"取消任务失败: {e}")
            return False
    
    async def _dispatch_worker(self):
        """分发工作线程"""
        while self.is_running:
            try:
                # 获取下一个要分发的任务
                next_task = await self._get_next_task()
                
                if next_task:
                    # 分发任务
                    await self._dispatch_task(next_task)
                else:
                    # 没有任务，短暂休眠
                    await asyncio.sleep(self.dispatch_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"分发工作线程异常: {e}")
                await asyncio.sleep(1)
    
    async def _get_next_task(self) -> Optional[QueuedTask]:
        """获取下一个要分发的任务"""
        # 按优先级顺序检查队列
        for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
            queue = self.task_queues[priority]
            
            if queue:
                # 获取队列中的第一个任务
                next_task = queue[0]
                
                # 检查是否可以分发
                if await self._can_dispatch_task(next_task):
                    heapq.heappop(queue)
                    return next_task
        
        return None
    
    async def _can_dispatch_task(self, queued_task: QueuedTask) -> bool:
        """检查任务是否可以分发"""
        # 检查任务状态
        if queued_task.status != TaskStatus.QUEUED:
            return False
        
        # 检查截止时间
        if queued_task.deadline and datetime.now() > queued_task.deadline:
            queued_task.status = TaskStatus.TIMEOUT
            return False
        
        # 检查是否有可用的智能体
        available_agents = await self._get_available_agents(queued_task.task)
        return len(available_agents) > 0
    
    async def _dispatch_task(self, queued_task: QueuedTask):
        """分发任务"""
        try:
            queued_task.status = TaskStatus.DISPATCHED
            queued_task.dispatch_time = datetime.now()
            
            # 选择最佳智能体
            selected_agent = await self._select_best_agent(queued_task.task)
            
            if not selected_agent:
                raise TaskDispatchError("没有可用的智能体")
            
            queued_task.assigned_agent = selected_agent
            
            # 记录分发尝试
            dispatch_attempt = {
                "agent_id": selected_agent,
                "attempt_time": datetime.now().isoformat(),
                "attempt_number": len(queued_task.dispatch_attempts) + 1
            }
            queued_task.dispatch_attempts.append(dispatch_attempt)
            
            # 更新智能体工作负载
            self.agent_workloads[selected_agent] = self.agent_workloads.get(selected_agent, 0) + 1
            
            # 发送分发事件
            await self.event_bus.emit(EventType.TASK_DISPATCHED, {
                "task_id": queued_task.task.task_id,
                "agent_id": selected_agent,
                "dispatch_time": queued_task.dispatch_time.isoformat(),
                "queue_time": (queued_task.dispatch_time - queued_task.queue_time).total_seconds()
            })
            
            # 更新统计
            self.dispatch_stats["total_tasks_dispatched"] += 1
            queue_time = (queued_task.dispatch_time - queued_task.queue_time).total_seconds()
            self._update_average_queue_time(queue_time)
            
            self.logger.info(f"任务已分发: {queued_task.task.task_id} -> {selected_agent}")
            
        except Exception as e:
            # 分发失败
            queued_task.status = TaskStatus.FAILED
            queued_task.retry_count += 1
            
            # 检查是否可以重试
            if queued_task.retry_count < queued_task.max_retries:
                # 重新加入队列
                queued_task.status = TaskStatus.QUEUED
                priority_queue = self.task_queues[queued_task.task.priority]
                heapq.heappush(priority_queue, queued_task)
                
                self.logger.warning(f"任务分发失败，将重试: {queued_task.task.task_id}, 错误: {e}")
            else:
                # 达到最大重试次数
                self.dispatch_stats["failed_dispatches"] += 1
                
                await self.event_bus.emit(EventType.TASK_DISPATCH_FAILED, {
                    "task_id": queued_task.task.task_id,
                    "error": str(e),
                    "retry_count": queued_task.retry_count
                })
                
                self.logger.error(f"任务分发最终失败: {queued_task.task.task_id}, 错误: {e}")
    
    async def _get_available_agents(self, task: AgentTask) -> List[str]:
        """获取可用的智能体"""
        available_agents = []
        
        # 从智能体协调器获取可用智能体
        # 这里需要与智能体协调器集成
        # 暂时返回模拟数据
        
        return available_agents
    
    async def _select_best_agent(self, task: AgentTask) -> Optional[str]:
        """选择最佳智能体"""
        available_agents = await self._get_available_agents(task)
        
        if not available_agents:
            return None
        
        # 根据策略选择智能体
        if self.default_strategy == DispatchStrategy.LOAD_BALANCED:
            return await self._load_balanced_selection(available_agents)
        elif self.default_strategy == DispatchStrategy.INTELLIGENT:
            return await self._intelligent_selection(task, available_agents)
        else:
            # 默认选择第一个可用的智能体
            return available_agents[0]
    
    async def _load_balanced_selection(self, agents: List[str]) -> str:
        """负载均衡选择"""
        # 选择工作负载最低的智能体
        min_workload = float('inf')
        selected_agent = agents[0]
        
        for agent_id in agents:
            workload = self.agent_workloads.get(agent_id, 0)
            if workload < min_workload:
                min_workload = workload
                selected_agent = agent_id
        
        return selected_agent
    
    async def _intelligent_selection(self, task: AgentTask, agents: List[str]) -> str:
        """智能选择"""
        # 综合考虑能力匹配、性能和负载
        best_score = -1
        selected_agent = agents[0]
        
        for agent_id in agents:
            score = await self._calculate_agent_score(task, agent_id)
            if score > best_score:
                best_score = score
                selected_agent = agent_id
        
        return selected_agent
    
    async def _calculate_agent_score(self, task: AgentTask, agent_id: str) -> float:
        """计算智能体分数"""
        score = 0.0
        
        # 能力匹配分数 (40%)
        capabilities = self.agent_capabilities.get(agent_id, set())
        required_capabilities = set(task.metadata.get("required_capabilities", []))
        
        if required_capabilities:
            matched = required_capabilities.intersection(capabilities)
            capability_score = len(matched) / len(required_capabilities)
        else:
            capability_score = 1.0
        
        score += capability_score * 0.4
        
        # 性能分数 (40%)
        performance = self.agent_performance.get(agent_id, {})
        success_rate = performance.get("success_rate", 0.5)
        avg_time = performance.get("average_time", 60.0)
        
        # 成功率越高越好，时间越短越好
        performance_score = success_rate * 0.7 + max(0, 1.0 - avg_time / 300.0) * 0.3
        score += performance_score * 0.4
        
        # 负载分数 (20%)
        workload = self.agent_workloads.get(agent_id, 0)
        max_workload = 10  # 假设最大工作负载
        load_score = max(0, 1.0 - workload / max_workload)
        score += load_score * 0.2
        
        return score
    
    async def _apply_dispatch_rules(self, task: AgentTask):
        """应用分发规则"""
        for rule in self.dispatch_rules.values():
            if rule.enabled and rule.condition(task):
                # 应用规则
                if rule.priority_boost > 0:
                    # 提升优先级
                    current_priority = task.priority.value
                    new_priority = min(current_priority + rule.priority_boost, TaskPriority.CRITICAL.value)
                    task.priority = TaskPriority(new_priority)
                
                # 设置目标智能体
                if rule.target_agents:
                    task.metadata["preferred_agents"] = rule.target_agents
                
                self.logger.info(f"应用分发规则: {rule.name} -> 任务: {task.task_id}")
    
    async def _register_default_rules(self):
        """注册默认分发规则"""
        # 紧急任务规则
        urgent_rule = DispatchRule(
            rule_id="urgent_tasks",
            name="紧急任务优先处理",
            condition=lambda task: "urgent" in task.metadata.get("tags", []),
            target_agents=[],
            priority_boost=2,
            enabled=True
        )
        self.dispatch_rules[urgent_rule.rule_id] = urgent_rule
        
        # VIP用户规则
        vip_rule = DispatchRule(
            rule_id="vip_users",
            name="VIP用户优先处理",
            condition=lambda task: task.metadata.get("user_type") == "vip",
            target_agents=[],
            priority_boost=1,
            enabled=True
        )
        self.dispatch_rules[vip_rule.rule_id] = vip_rule
    
    async def _register_event_handlers(self):
        """注册事件处理器"""
        # 注册任务完成事件处理器
        await self.event_bus.subscribe(EventType.TASK_COMPLETED, self._handle_task_completed)
        await self.event_bus.subscribe(EventType.TASK_FAILED, self._handle_task_failed)
        await self.event_bus.subscribe(EventType.AGENT_STATUS_CHANGED, self._handle_agent_status_change)
    
    async def _handle_task_completed(self, event_data: Dict[str, Any]):
        """处理任务完成事件"""
        task_id = event_data.get("task_id")
        agent_id = event_data.get("agent_id")
        completion_time = event_data.get("completion_time", 0.0)
        
        if task_id in self.task_index:
            queued_task = self.task_index[task_id]
            queued_task.status = TaskStatus.COMPLETED
            
            # 更新智能体工作负载
            if agent_id and agent_id in self.agent_workloads:
                self.agent_workloads[agent_id] = max(0, self.agent_workloads[agent_id] - 1)
            
            # 更新智能体性能
            if agent_id:
                await self._update_agent_performance(agent_id, True, completion_time)
            
            # 更新统计
            self.dispatch_stats["successful_dispatches"] += 1
            if queued_task.dispatch_time:
                dispatch_time = (datetime.now() - queued_task.dispatch_time).total_seconds()
                self._update_average_dispatch_time(dispatch_time)
    
    async def _handle_task_failed(self, event_data: Dict[str, Any]):
        """处理任务失败事件"""
        task_id = event_data.get("task_id")
        agent_id = event_data.get("agent_id")
        error = event_data.get("error")
        
        if task_id in self.task_index:
            queued_task = self.task_index[task_id]
            queued_task.status = TaskStatus.FAILED
            
            # 更新智能体工作负载
            if agent_id and agent_id in self.agent_workloads:
                self.agent_workloads[agent_id] = max(0, self.agent_workloads[agent_id] - 1)
            
            # 更新智能体性能
            if agent_id:
                await self._update_agent_performance(agent_id, False, 0.0)
            
            # 检查是否需要重试
            if queued_task.retry_count < queued_task.max_retries:
                queued_task.status = TaskStatus.QUEUED
                queued_task.retry_count += 1
                
                # 重新加入队列
                priority_queue = self.task_queues[queued_task.task.priority]
                heapq.heappush(priority_queue, queued_task)
                
                self.logger.info(f"任务将重试: {task_id}, 重试次数: {queued_task.retry_count}")
    
    async def _handle_agent_status_change(self, event_data: Dict[str, Any]):
        """处理智能体状态变更事件"""
        agent_id = event_data.get("agent_id")
        new_status = event_data.get("new_status")
        
        # 如果智能体变为不可用，清理其工作负载
        if new_status not in ["idle", "busy"]:
            if agent_id in self.agent_workloads:
                self.agent_workloads[agent_id] = 0
    
    async def _update_agent_performance(self, agent_id: str, success: bool, completion_time: float):
        """更新智能体性能指标"""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = {
                "total_tasks": 0,
                "successful_tasks": 0,
                "success_rate": 0.0,
                "total_time": 0.0,
                "average_time": 0.0
            }
        
        performance = self.agent_performance[agent_id]
        performance["total_tasks"] += 1
        
        if success:
            performance["successful_tasks"] += 1
            performance["total_time"] += completion_time
            performance["average_time"] = performance["total_time"] / performance["successful_tasks"]
        
        performance["success_rate"] = performance["successful_tasks"] / performance["total_tasks"]
    
    def _update_average_queue_time(self, queue_time: float):
        """更新平均队列时间"""
        total_dispatched = self.dispatch_stats["total_tasks_dispatched"]
        if total_dispatched > 0:
            current_avg = self.dispatch_stats["average_queue_time"]
            new_avg = (current_avg * (total_dispatched - 1) + queue_time) / total_dispatched
            self.dispatch_stats["average_queue_time"] = new_avg
    
    def _update_average_dispatch_time(self, dispatch_time: float):
        """更新平均分发时间"""
        total_successful = self.dispatch_stats["successful_dispatches"]
        if total_successful > 0:
            current_avg = self.dispatch_stats["average_dispatch_time"]
            new_avg = (current_avg * (total_successful - 1) + dispatch_time) / total_successful
            self.dispatch_stats["average_dispatch_time"] = new_avg
    
    async def _timeout_monitor(self):
        """超时监控工作线程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 检查所有队列中的任务
                for priority_queue in self.task_queues.values():
                    for queued_task in list(priority_queue):
                        # 检查任务超时
                        if queued_task.status == TaskStatus.DISPATCHED:
                            if queued_task.dispatch_time:
                                elapsed = (current_time - queued_task.dispatch_time).total_seconds()
                                if elapsed > self.task_timeout:
                                    # 任务超时
                                    queued_task.status = TaskStatus.TIMEOUT
                                    
                                    # 清理智能体工作负载
                                    if queued_task.assigned_agent:
                                        agent_id = queued_task.assigned_agent
                                        if agent_id in self.agent_workloads:
                                            self.agent_workloads[agent_id] = max(0, self.agent_workloads[agent_id] - 1)
                                    
                                    self.logger.warning(f"任务执行超时: {queued_task.task.task_id}")
                        
                        # 检查截止时间
                        elif queued_task.deadline and current_time > queued_task.deadline:
                            if queued_task.status == TaskStatus.QUEUED:
                                queued_task.status = TaskStatus.TIMEOUT
                                priority_queue.remove(queued_task)
                                heapq.heapify(priority_queue)
                                
                                self.logger.warning(f"任务截止时间超时: {queued_task.task.task_id}")
                
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"超时监控异常: {e}")
                await asyncio.sleep(5)
    
    async def _performance_monitor(self):
        """性能监控工作线程"""
        while self.is_running:
            try:
                # 监控队列长度
                total_queued = sum(len(queue) for queue in self.task_queues.values())
                
                if total_queued > self.max_queue_size * 0.8:
                    self.logger.warning(f"任务队列接近满载: {total_queued}/{self.max_queue_size}")
                
                # 监控分发性能
                dispatch_rate = self.dispatch_stats["total_tasks_dispatched"] / max(1, 
                    (datetime.now() - self.dispatch_stats["dispatcher_start_time"]).total_seconds() / 60)
                
                self.logger.debug(f"分发速率: {dispatch_rate:.2f} 任务/分钟")
                
                await asyncio.sleep(60)  # 每分钟监控一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能监控异常: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_worker(self):
        """清理工作线程"""
        while self.is_running:
            try:
                # 清理已完成的任务
                cutoff_time = datetime.now() - timedelta(hours=1)
                
                for task_id, queued_task in list(self.task_index.items()):
                    if queued_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
                        if queued_task.dispatch_time and queued_task.dispatch_time < cutoff_time:
                            del self.task_index[task_id]
                
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理工作异常: {e}")
                await asyncio.sleep(60)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.task_index:
            return None
        
        queued_task = self.task_index[task_id]
        
        return {
            "task_id": task_id,
            "status": queued_task.status.value,
            "queue_time": queued_task.queue_time.isoformat(),
            "dispatch_time": queued_task.dispatch_time.isoformat() if queued_task.dispatch_time else None,
            "assigned_agent": queued_task.assigned_agent,
            "retry_count": queued_task.retry_count,
            "dispatch_attempts": queued_task.dispatch_attempts
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        queue_status = {}
        
        for priority in TaskPriority:
            queue = self.task_queues[priority]
            queue_status[priority.name] = {
                "count": len(queue),
                "oldest_task": queue[0].queue_time.isoformat() if queue else None
            }
        
        return queue_status
    
    def get_dispatcher_stats(self) -> Dict[str, Any]:
        """获取分发器统计信息"""
        uptime = datetime.now() - self.dispatch_stats["dispatcher_start_time"]
        total_queued = sum(len(queue) for queue in self.task_queues.values())
        
        return {
            **self.dispatch_stats,
            "uptime_seconds": uptime.total_seconds(),
            "current_queue_size": total_queued,
            "active_agents": len(self.agent_workloads),
            "total_agent_workload": sum(self.agent_workloads.values()),
            "dispatch_rules_count": len(self.dispatch_rules),
            "is_running": self.is_running
        }
    
    async def add_dispatch_rule(self, rule: DispatchRule) -> bool:
        """添加分发规则"""
        try:
            self.dispatch_rules[rule.rule_id] = rule
            self.logger.info(f"分发规则已添加: {rule.name}")
            return True
        except Exception as e:
            self.logger.error(f"添加分发规则失败: {e}")
            return False
    
    async def remove_dispatch_rule(self, rule_id: str) -> bool:
        """移除分发规则"""
        try:
            if rule_id in self.dispatch_rules:
                del self.dispatch_rules[rule_id]
                self.logger.info(f"分发规则已移除: {rule_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"移除分发规则失败: {e}")
            return False
    
    async def update_agent_capabilities(self, agent_id: str, capabilities: Set[str]):
        """更新智能体能力"""
        self.agent_capabilities[agent_id] = capabilities
        self.logger.debug(f"智能体能力已更新: {agent_id}")
    
    async def shutdown(self):
        """关闭任务分发器"""
        try:
            self.logger.info("关闭任务分发器...")
            
            self.is_running = False
            
            # 取消所有工作任务
            for task in self.worker_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 取消所有队列中的任务
            for priority_queue in self.task_queues.values():
                for queued_task in priority_queue:
                    if queued_task.status == TaskStatus.QUEUED:
                        queued_task.status = TaskStatus.CANCELLED
            
            self.logger.info("任务分发器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭任务分发器失败: {e}")


# 全局任务分发器实例
_task_dispatcher: Optional[TaskDispatcher] = None


def get_task_dispatcher() -> TaskDispatcher:
    """获取全局任务分发器实例"""
    global _task_dispatcher
    if _task_dispatcher is None:
        _task_dispatcher = TaskDispatcher()
    return _task_dispatcher

