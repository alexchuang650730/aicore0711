"""
PowerAutomation 4.0 Agent Coordinator
智能体协调器 - 负责智能体的注册、发现、任务分配和协作管理
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
from enum import Enum

from ..shared.agent_base import AgentBase, AgentStatus, AgentTask, TaskPriority, AgentCapability
from core.exceptions import AgentError, handle_exception
from core.logging_config import get_agent_logger
from core.config import get_config
from core.event_bus import EventType, get_event_bus


class CoordinationStrategy(Enum):
    """协调策略枚举"""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    CAPABILITY_BASED = "capability_based"
    PRIORITY_BASED = "priority_based"
    COLLABORATIVE = "collaborative"
    INTELLIGENT = "intelligent"


class TaskAssignmentMode(Enum):
    """任务分配模式枚举"""
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    PIPELINE = "pipeline"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"


@dataclass
class AgentRegistration:
    """智能体注册信息"""
    agent_id: str
    agent_name: str
    agent_type: str
    agent_instance: AgentBase
    capabilities: List[AgentCapability]
    status: AgentStatus
    registration_time: datetime
    last_heartbeat: datetime
    performance_metrics: Dict[str, Any]
    specializations: Set[str]
    collaboration_preferences: Dict[str, Any]
    load_factor: float = 0.0
    priority: int = 5


@dataclass
class TaskAssignment:
    """任务分配信息"""
    assignment_id: str
    task: AgentTask
    assigned_agents: List[str]
    assignment_strategy: CoordinationStrategy
    assignment_mode: TaskAssignmentMode
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]


@dataclass
class CollaborationSession:
    """协作会话信息"""
    session_id: str
    participants: List[str]
    session_type: str
    objective: str
    context: Dict[str, Any]
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    messages: List[Dict[str, Any]]
    shared_state: Dict[str, Any]


class AgentCoordinator:
    """智能体协调器"""
    
    def __init__(self):
        self.logger = get_agent_logger()
        self.config = get_config()
        self.event_bus = get_event_bus()
        
        # 智能体注册表
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.agent_capabilities_index: Dict[str, Set[str]] = {}
        self.agent_type_index: Dict[str, Set[str]] = {}
        self.agent_specialization_index: Dict[str, Set[str]] = {}
        
        # 任务管理
        self.active_assignments: Dict[str, TaskAssignment] = {}
        self.assignment_history: List[TaskAssignment] = []
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
        # 协作管理
        self.active_collaborations: Dict[str, CollaborationSession] = {}
        self.collaboration_history: List[CollaborationSession] = []
        
        # 协调策略
        self.default_strategy = CoordinationStrategy.INTELLIGENT
        self.strategy_handlers: Dict[CoordinationStrategy, Callable] = {}
        
        # 性能监控
        self.coordination_stats = {
            "total_agents": 0,
            "active_agents": 0,
            "total_tasks_assigned": 0,
            "successful_assignments": 0,
            "failed_assignments": 0,
            "average_assignment_time": 0.0,
            "collaboration_sessions": 0,
            "coordinator_start_time": datetime.now()
        }
        
        # 运行状态
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # 配置参数
        self.max_concurrent_assignments = 50
        self.heartbeat_timeout = 60  # 秒
        self.assignment_timeout = 300  # 秒
        self.collaboration_timeout = 1800  # 秒
    
    async def initialize(self) -> bool:
        """初始化智能体协调器"""
        try:
            self.logger.info("初始化智能体协调器...")
            
            # 注册策略处理器
            await self._register_strategy_handlers()
            
            # 注册事件处理器
            await self._register_event_handlers()
            
            # 启动工作线程
            self.is_running = True
            self.worker_tasks = [
                asyncio.create_task(self._task_assignment_worker()),
                asyncio.create_task(self._heartbeat_monitor()),
                asyncio.create_task(self._performance_monitor()),
                asyncio.create_task(self._cleanup_worker())
            ]
            
            self.logger.info("智能体协调器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"智能体协调器初始化失败: {e}")
            return False
    
    async def register_agent(self, agent: AgentBase) -> bool:
        """注册智能体"""
        try:
            agent_id = agent.agent_id
            
            # 检查是否已注册
            if agent_id in self.registered_agents:
                self.logger.warning(f"智能体已注册: {agent_id}")
                return True
            
            # 创建注册信息
            registration = AgentRegistration(
                agent_id=agent_id,
                agent_name=agent.agent_name,
                agent_type=agent.agent_type,
                agent_instance=agent,
                capabilities=agent.capabilities,
                status=agent.status,
                registration_time=datetime.now(),
                last_heartbeat=datetime.now(),
                performance_metrics=agent.performance_metrics,
                specializations=set(),  # 可以从agent.metadata中提取
                collaboration_preferences={}
            )
            
            # 存储注册信息
            self.registered_agents[agent_id] = registration
            
            # 更新索引
            await self._update_agent_indexes(agent_id, registration)
            
            # 更新统计
            self.coordination_stats["total_agents"] += 1
            if agent.status == AgentStatus.IDLE:
                self.coordination_stats["active_agents"] += 1
            
            # 发送注册事件
            await self.event_bus.emit(EventType.AGENT_REGISTERED, {
                "agent_id": agent_id,
                "agent_name": agent.agent_name,
                "agent_type": agent.agent_type,
                "capabilities": [asdict(cap) for cap in agent.capabilities]
            })
            
            self.logger.info(f"智能体注册成功: {agent.agent_name} ({agent_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"注册智能体失败: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            if agent_id not in self.registered_agents:
                self.logger.warning(f"智能体未注册: {agent_id}")
                return False
            
            registration = self.registered_agents[agent_id]
            
            # 取消该智能体的所有活跃任务
            await self._cancel_agent_assignments(agent_id)
            
            # 从索引中移除
            await self._remove_from_agent_indexes(agent_id, registration)
            
            # 从注册表中移除
            del self.registered_agents[agent_id]
            
            # 更新统计
            self.coordination_stats["total_agents"] -= 1
            if registration.status in [AgentStatus.IDLE, AgentStatus.BUSY]:
                self.coordination_stats["active_agents"] -= 1
            
            # 发送注销事件
            await self.event_bus.emit(EventType.AGENT_UNREGISTERED, {
                "agent_id": agent_id,
                "agent_name": registration.agent_name
            })
            
            self.logger.info(f"智能体注销成功: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注销智能体失败: {e}")
            return False
    
    async def assign_task(
        self,
        task: AgentTask,
        strategy: Optional[CoordinationStrategy] = None,
        preferred_agents: Optional[List[str]] = None,
        assignment_mode: TaskAssignmentMode = TaskAssignmentMode.SINGLE_AGENT
    ) -> str:
        """分配任务给智能体"""
        try:
            # 检查并发限制
            if len(self.active_assignments) >= self.max_concurrent_assignments:
                raise AgentError("达到最大并发任务分配限制")
            
            # 使用默认策略
            if strategy is None:
                strategy = self.default_strategy
            
            # 选择合适的智能体
            selected_agents = await self._select_agents_for_task(
                task, strategy, preferred_agents, assignment_mode
            )
            
            if not selected_agents:
                raise AgentError(f"没有找到合适的智能体执行任务: {task.task_type}")
            
            # 创建任务分配
            assignment_id = str(uuid.uuid4())
            assignment = TaskAssignment(
                assignment_id=assignment_id,
                task=task,
                assigned_agents=selected_agents,
                assignment_strategy=strategy,
                assignment_mode=assignment_mode,
                created_at=datetime.now(),
                started_at=None,
                completed_at=None,
                status="pending",
                result=None,
                error=None
            )
            
            # 存储分配信息
            self.active_assignments[assignment_id] = assignment
            
            # 将任务加入队列
            await self.task_queue.put(assignment)
            
            # 更新统计
            self.coordination_stats["total_tasks_assigned"] += 1
            
            self.logger.info(f"任务分配创建: {assignment_id}, 智能体: {selected_agents}")
            return assignment_id
            
        except Exception as e:
            self.logger.error(f"任务分配失败: {e}")
            raise AgentError(f"任务分配失败: {str(e)}")
    
    async def _select_agents_for_task(
        self,
        task: AgentTask,
        strategy: CoordinationStrategy,
        preferred_agents: Optional[List[str]],
        assignment_mode: TaskAssignmentMode
    ) -> List[str]:
        """为任务选择合适的智能体"""
        try:
            # 获取候选智能体
            candidates = await self._get_candidate_agents(task, preferred_agents)
            
            if not candidates:
                return []
            
            # 根据策略选择智能体
            if strategy in self.strategy_handlers:
                handler = self.strategy_handlers[strategy]
                selected = await handler(task, candidates, assignment_mode)
            else:
                # 默认使用能力匹配策略
                selected = await self._capability_based_selection(task, candidates, assignment_mode)
            
            return selected
            
        except Exception as e:
            self.logger.error(f"选择智能体失败: {e}")
            return []
    
    async def _get_candidate_agents(
        self,
        task: AgentTask,
        preferred_agents: Optional[List[str]]
    ) -> List[AgentRegistration]:
        """获取候选智能体"""
        candidates = []
        
        # 如果指定了首选智能体
        if preferred_agents:
            for agent_id in preferred_agents:
                if agent_id in self.registered_agents:
                    registration = self.registered_agents[agent_id]
                    if await self._is_agent_available(registration):
                        candidates.append(registration)
        else:
            # 获取所有可用的智能体
            for registration in self.registered_agents.values():
                if await self._is_agent_available(registration):
                    # 检查能力匹配
                    if await self._check_capability_match(task, registration):
                        candidates.append(registration)
        
        return candidates
    
    async def _is_agent_available(self, registration: AgentRegistration) -> bool:
        """检查智能体是否可用"""
        # 检查状态
        if registration.status not in [AgentStatus.IDLE, AgentStatus.BUSY]:
            return False
        
        # 检查心跳
        time_since_heartbeat = (datetime.now() - registration.last_heartbeat).total_seconds()
        if time_since_heartbeat > self.heartbeat_timeout:
            return False
        
        # 检查负载
        if registration.load_factor >= 1.0:
            return False
        
        # 检查智能体实例是否可以接受新任务
        if hasattr(registration.agent_instance, 'is_available_for_task'):
            return registration.agent_instance.is_available_for_task()
        
        return True
    
    async def _check_capability_match(self, task: AgentTask, registration: AgentRegistration) -> bool:
        """检查能力匹配"""
        required_capabilities = task.metadata.get("required_capabilities", [])
        
        if not required_capabilities:
            return True
        
        agent_capabilities = {cap.name for cap in registration.capabilities}
        
        # 检查是否所有必需能力都满足
        return all(cap in agent_capabilities for cap in required_capabilities)
    
    async def _capability_based_selection(
        self,
        task: AgentTask,
        candidates: List[AgentRegistration],
        assignment_mode: TaskAssignmentMode
    ) -> List[str]:
        """基于能力的智能体选择"""
        if not candidates:
            return []
        
        # 按能力匹配度和性能排序
        scored_candidates = []
        for candidate in candidates:
            score = await self._calculate_agent_score(task, candidate)
            scored_candidates.append((candidate, score))
        
        # 按分数排序
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 根据分配模式选择智能体
        if assignment_mode == TaskAssignmentMode.SINGLE_AGENT:
            return [scored_candidates[0][0].agent_id]
        elif assignment_mode == TaskAssignmentMode.MULTI_AGENT:
            # 选择前N个智能体
            max_agents = task.metadata.get("max_agents", 3)
            return [candidate.agent_id for candidate, _ in scored_candidates[:max_agents]]
        elif assignment_mode == TaskAssignmentMode.PARALLEL:
            # 选择所有合适的智能体
            return [candidate.agent_id for candidate, _ in scored_candidates]
        else:
            return [scored_candidates[0][0].agent_id]
    
    async def _calculate_agent_score(self, task: AgentTask, candidate: AgentRegistration) -> float:
        """计算智能体分数"""
        score = 0.0
        
        # 能力匹配分数 (40%)
        capability_score = await self._calculate_capability_score(task, candidate)
        score += capability_score * 0.4
        
        # 性能分数 (30%)
        performance_score = await self._calculate_performance_score(candidate)
        score += performance_score * 0.3
        
        # 负载分数 (20%)
        load_score = 1.0 - candidate.load_factor
        score += load_score * 0.2
        
        # 优先级分数 (10%)
        priority_score = candidate.priority / 10.0
        score += priority_score * 0.1
        
        return score
    
    async def _calculate_capability_score(self, task: AgentTask, candidate: AgentRegistration) -> float:
        """计算能力匹配分数"""
        required_capabilities = set(task.metadata.get("required_capabilities", []))
        agent_capabilities = {cap.name for cap in candidate.capabilities}
        
        if not required_capabilities:
            return 1.0
        
        # 计算匹配度
        matched = required_capabilities.intersection(agent_capabilities)
        match_ratio = len(matched) / len(required_capabilities)
        
        # 额外能力加分
        extra_capabilities = agent_capabilities - required_capabilities
        extra_bonus = min(len(extra_capabilities) * 0.1, 0.3)
        
        return min(match_ratio + extra_bonus, 1.0)
    
    async def _calculate_performance_score(self, candidate: AgentRegistration) -> float:
        """计算性能分数"""
        metrics = candidate.performance_metrics
        
        # 成功率 (50%)
        success_rate = metrics.get("success_rate", 0.0)
        
        # 平均完成时间 (30%) - 越短越好
        avg_time = metrics.get("average_completion_time", 60.0)
        time_score = max(0, 1.0 - (avg_time / 300.0))  # 5分钟为基准
        
        # 总任务数 (20%) - 经验加分
        total_tasks = metrics.get("total_tasks", 0)
        experience_score = min(total_tasks / 100.0, 1.0)
        
        return success_rate * 0.5 + time_score * 0.3 + experience_score * 0.2
    
    async def _task_assignment_worker(self):
        """任务分配工作线程"""
        while self.is_running:
            try:
                # 从队列获取任务分配
                assignment = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # 执行任务分配
                await self._execute_assignment(assignment)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"任务分配工作线程异常: {e}")
                await asyncio.sleep(1)
    
    async def _execute_assignment(self, assignment: TaskAssignment):
        """执行任务分配"""
        try:
            assignment.status = "running"
            assignment.started_at = datetime.now()
            
            self.logger.info(f"开始执行任务分配: {assignment.assignment_id}")
            
            # 根据分配模式执行任务
            if assignment.assignment_mode == TaskAssignmentMode.SINGLE_AGENT:
                result = await self._execute_single_agent_task(assignment)
            elif assignment.assignment_mode == TaskAssignmentMode.MULTI_AGENT:
                result = await self._execute_multi_agent_task(assignment)
            elif assignment.assignment_mode == TaskAssignmentMode.PARALLEL:
                result = await self._execute_parallel_task(assignment)
            elif assignment.assignment_mode == TaskAssignmentMode.PIPELINE:
                result = await self._execute_pipeline_task(assignment)
            else:
                result = await self._execute_single_agent_task(assignment)
            
            # 完成分配
            assignment.status = "completed"
            assignment.completed_at = datetime.now()
            assignment.result = result
            
            # 更新统计
            self.coordination_stats["successful_assignments"] += 1
            
            self.logger.info(f"任务分配完成: {assignment.assignment_id}")
            
        except Exception as e:
            # 分配失败
            assignment.status = "failed"
            assignment.error = str(e)
            assignment.completed_at = datetime.now()
            
            # 更新统计
            self.coordination_stats["failed_assignments"] += 1
            
            self.logger.error(f"任务分配失败: {assignment.assignment_id}, 错误: {e}")
            
        finally:
            # 清理分配
            await self._finalize_assignment(assignment)
    
    async def _execute_single_agent_task(self, assignment: TaskAssignment) -> Dict[str, Any]:
        """执行单智能体任务"""
        agent_id = assignment.assigned_agents[0]
        registration = self.registered_agents[agent_id]
        
        # 执行任务
        result = await registration.agent_instance.execute_task(assignment.task)
        
        return result
    
    async def _execute_multi_agent_task(self, assignment: TaskAssignment) -> Dict[str, Any]:
        """执行多智能体协作任务"""
        # 创建协作会话
        session = await self._create_collaboration_session(
            assignment.assigned_agents,
            "multi_agent_task",
            f"协作执行任务: {assignment.task.task_type}",
            {"assignment_id": assignment.assignment_id}
        )
        
        try:
            # 分解任务
            subtasks = await self._decompose_task(assignment.task, assignment.assigned_agents)
            
            # 分配子任务
            results = []
            for i, (agent_id, subtask) in enumerate(subtasks):
                registration = self.registered_agents[agent_id]
                result = await registration.agent_instance.execute_task(subtask)
                results.append(result)
            
            # 合并结果
            final_result = await self._merge_task_results(results, assignment.task)
            
            return final_result
            
        finally:
            # 结束协作会话
            await self._end_collaboration_session(session.session_id)
    
    async def _execute_parallel_task(self, assignment: TaskAssignment) -> Dict[str, Any]:
        """执行并行任务"""
        # 创建并行执行任务
        tasks = []
        for agent_id in assignment.assigned_agents:
            registration = self.registered_agents[agent_id]
            task = asyncio.create_task(
                registration.agent_instance.execute_task(assignment.task)
            )
            tasks.append((agent_id, task))
        
        # 等待所有任务完成
        results = []
        for agent_id, task in tasks:
            try:
                result = await task
                results.append({"agent_id": agent_id, "result": result})
            except Exception as e:
                results.append({"agent_id": agent_id, "error": str(e)})
        
        return {"parallel_results": results}
    
    async def _execute_pipeline_task(self, assignment: TaskAssignment) -> Dict[str, Any]:
        """执行流水线任务"""
        current_result = assignment.task.input_data
        
        # 按顺序执行
        for agent_id in assignment.assigned_agents:
            registration = self.registered_agents[agent_id]
            
            # 创建子任务
            subtask = AgentTask(
                task_id=f"{assignment.task.task_id}_pipeline_{agent_id}",
                task_type=assignment.task.task_type,
                priority=assignment.task.priority,
                input_data=current_result,
                context=assignment.task.context,
                requester=assignment.task.requester
            )
            
            # 执行子任务
            result = await registration.agent_instance.execute_task(subtask)
            
            # 更新结果作为下一个智能体的输入
            if result.get("status") == "success":
                current_result = result.get("result", current_result)
            else:
                raise AgentError(f"流水线任务失败在智能体 {agent_id}: {result.get('error')}")
        
        return {"pipeline_result": current_result}
    
    async def _decompose_task(self, task: AgentTask, agent_ids: List[str]) -> List[tuple]:
        """分解任务为子任务"""
        # 简单的任务分解逻辑
        subtasks = []
        
        for i, agent_id in enumerate(agent_ids):
            subtask = AgentTask(
                task_id=f"{task.task_id}_sub_{i}",
                task_type=task.task_type,
                priority=task.priority,
                input_data=task.input_data,
                context={**task.context, "subtask_index": i, "total_subtasks": len(agent_ids)},
                requester=task.requester
            )
            subtasks.append((agent_id, subtask))
        
        return subtasks
    
    async def _merge_task_results(self, results: List[Dict[str, Any]], original_task: AgentTask) -> Dict[str, Any]:
        """合并任务结果"""
        # 简单的结果合并逻辑
        successful_results = [r for r in results if r.get("status") == "success"]
        failed_results = [r for r in results if r.get("status") != "success"]
        
        if not successful_results:
            return {
                "status": "failed",
                "error": "所有子任务都失败了",
                "failed_results": failed_results
            }
        
        # 合并成功的结果
        merged_result = {
            "status": "success",
            "merged_data": [r.get("result") for r in successful_results],
            "successful_count": len(successful_results),
            "failed_count": len(failed_results)
        }
        
        if failed_results:
            merged_result["partial_failures"] = failed_results
        
        return merged_result
    
    async def _create_collaboration_session(
        self,
        participants: List[str],
        session_type: str,
        objective: str,
        context: Dict[str, Any]
    ) -> CollaborationSession:
        """创建协作会话"""
        session_id = str(uuid.uuid4())
        
        session = CollaborationSession(
            session_id=session_id,
            participants=participants,
            session_type=session_type,
            objective=objective,
            context=context,
            started_at=datetime.now(),
            ended_at=None,
            status="active",
            messages=[],
            shared_state={}
        )
        
        self.active_collaborations[session_id] = session
        self.coordination_stats["collaboration_sessions"] += 1
        
        self.logger.info(f"协作会话创建: {session_id}, 参与者: {participants}")
        return session
    
    async def _end_collaboration_session(self, session_id: str):
        """结束协作会话"""
        if session_id in self.active_collaborations:
            session = self.active_collaborations[session_id]
            session.status = "completed"
            session.ended_at = datetime.now()
            
            # 移动到历史记录
            self.collaboration_history.append(session)
            del self.active_collaborations[session_id]
            
            # 保持历史记录在合理范围内
            if len(self.collaboration_history) > 100:
                self.collaboration_history = self.collaboration_history[-80:]
            
            self.logger.info(f"协作会话结束: {session_id}")
    
    async def _finalize_assignment(self, assignment: TaskAssignment):
        """完成任务分配清理"""
        try:
            # 从活跃分配中移除
            if assignment.assignment_id in self.active_assignments:
                del self.active_assignments[assignment.assignment_id]
            
            # 添加到历史记录
            self.assignment_history.append(assignment)
            
            # 保持历史记录在合理范围内
            if len(self.assignment_history) > 1000:
                self.assignment_history = self.assignment_history[-800:]
            
            # 更新平均分配时间
            if assignment.started_at and assignment.completed_at:
                execution_time = (assignment.completed_at - assignment.started_at).total_seconds()
                
                total_successful = self.coordination_stats["successful_assignments"]
                if total_successful > 0:
                    current_avg = self.coordination_stats["average_assignment_time"]
                    new_avg = (current_avg * (total_successful - 1) + execution_time) / total_successful
                    self.coordination_stats["average_assignment_time"] = new_avg
            
        except Exception as e:
            self.logger.error(f"完成任务分配清理失败: {e}")
    
    async def _cancel_agent_assignments(self, agent_id: str):
        """取消智能体的所有活跃任务"""
        cancelled_assignments = []
        
        for assignment_id, assignment in list(self.active_assignments.items()):
            if agent_id in assignment.assigned_agents:
                assignment.status = "cancelled"
                assignment.error = f"智能体 {agent_id} 已注销"
                assignment.completed_at = datetime.now()
                
                cancelled_assignments.append(assignment_id)
                await self._finalize_assignment(assignment)
        
        if cancelled_assignments:
            self.logger.info(f"取消了智能体 {agent_id} 的 {len(cancelled_assignments)} 个任务分配")
    
    async def _update_agent_indexes(self, agent_id: str, registration: AgentRegistration):
        """更新智能体索引"""
        # 能力索引
        for capability in registration.capabilities:
            if capability.name not in self.agent_capabilities_index:
                self.agent_capabilities_index[capability.name] = set()
            self.agent_capabilities_index[capability.name].add(agent_id)
        
        # 类型索引
        if registration.agent_type not in self.agent_type_index:
            self.agent_type_index[registration.agent_type] = set()
        self.agent_type_index[registration.agent_type].add(agent_id)
        
        # 专业化索引
        for specialization in registration.specializations:
            if specialization not in self.agent_specialization_index:
                self.agent_specialization_index[specialization] = set()
            self.agent_specialization_index[specialization].add(agent_id)
    
    async def _remove_from_agent_indexes(self, agent_id: str, registration: AgentRegistration):
        """从智能体索引中移除"""
        # 能力索引
        for capability in registration.capabilities:
            if capability.name in self.agent_capabilities_index:
                self.agent_capabilities_index[capability.name].discard(agent_id)
                if not self.agent_capabilities_index[capability.name]:
                    del self.agent_capabilities_index[capability.name]
        
        # 类型索引
        if registration.agent_type in self.agent_type_index:
            self.agent_type_index[registration.agent_type].discard(agent_id)
            if not self.agent_type_index[registration.agent_type]:
                del self.agent_type_index[registration.agent_type]
        
        # 专业化索引
        for specialization in registration.specializations:
            if specialization in self.agent_specialization_index:
                self.agent_specialization_index[specialization].discard(agent_id)
                if not self.agent_specialization_index[specialization]:
                    del self.agent_specialization_index[specialization]
    
    async def _register_strategy_handlers(self):
        """注册策略处理器"""
        self.strategy_handlers = {
            CoordinationStrategy.ROUND_ROBIN: self._round_robin_selection,
            CoordinationStrategy.LOAD_BALANCED: self._load_balanced_selection,
            CoordinationStrategy.CAPABILITY_BASED: self._capability_based_selection,
            CoordinationStrategy.PRIORITY_BASED: self._priority_based_selection,
            CoordinationStrategy.COLLABORATIVE: self._collaborative_selection,
            CoordinationStrategy.INTELLIGENT: self._intelligent_selection
        }
    
    async def _register_event_handlers(self):
        """注册事件处理器"""
        # 注册智能体状态变更事件处理器
        await self.event_bus.subscribe(EventType.AGENT_STATUS_CHANGED, self._handle_agent_status_change)
    
    async def _handle_agent_status_change(self, event_data: Dict[str, Any]):
        """处理智能体状态变更事件"""
        agent_id = event_data.get("agent_id")
        new_status = event_data.get("new_status")
        
        if agent_id in self.registered_agents:
            registration = self.registered_agents[agent_id]
            old_status = registration.status
            registration.status = AgentStatus(new_status)
            
            # 更新活跃智能体统计
            if old_status in [AgentStatus.IDLE, AgentStatus.BUSY] and new_status not in ["idle", "busy"]:
                self.coordination_stats["active_agents"] -= 1
            elif old_status not in [AgentStatus.IDLE, AgentStatus.BUSY] and new_status in ["idle", "busy"]:
                self.coordination_stats["active_agents"] += 1
    
    async def _round_robin_selection(self, task: AgentTask, candidates: List[AgentRegistration], assignment_mode: TaskAssignmentMode) -> List[str]:
        """轮询选择策略"""
        if not candidates:
            return []
        
        # 简单的轮询实现
        selected_index = self.coordination_stats["total_tasks_assigned"] % len(candidates)
        
        if assignment_mode == TaskAssignmentMode.SINGLE_AGENT:
            return [candidates[selected_index].agent_id]
        else:
            return [candidate.agent_id for candidate in candidates]
    
    async def _load_balanced_selection(self, task: AgentTask, candidates: List[AgentRegistration], assignment_mode: TaskAssignmentMode) -> List[str]:
        """负载均衡选择策略"""
        if not candidates:
            return []
        
        # 按负载因子排序
        candidates.sort(key=lambda x: x.load_factor)
        
        if assignment_mode == TaskAssignmentMode.SINGLE_AGENT:
            return [candidates[0].agent_id]
        else:
            return [candidate.agent_id for candidate in candidates]
    
    async def _priority_based_selection(self, task: AgentTask, candidates: List[AgentRegistration], assignment_mode: TaskAssignmentMode) -> List[str]:
        """基于优先级的选择策略"""
        if not candidates:
            return []
        
        # 按优先级排序
        candidates.sort(key=lambda x: x.priority, reverse=True)
        
        if assignment_mode == TaskAssignmentMode.SINGLE_AGENT:
            return [candidates[0].agent_id]
        else:
            return [candidate.agent_id for candidate in candidates]
    
    async def _collaborative_selection(self, task: AgentTask, candidates: List[AgentRegistration], assignment_mode: TaskAssignmentMode) -> List[str]:
        """协作选择策略"""
        # 选择互补能力的智能体
        return await self._capability_based_selection(task, candidates, assignment_mode)
    
    async def _intelligent_selection(self, task: AgentTask, candidates: List[AgentRegistration], assignment_mode: TaskAssignmentMode) -> List[str]:
        """智能选择策略"""
        # 综合考虑多个因素
        return await self._capability_based_selection(task, candidates, assignment_mode)
    
    async def _heartbeat_monitor(self):
        """心跳监控工作线程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 检查所有注册智能体的心跳
                for agent_id, registration in list(self.registered_agents.items()):
                    time_since_heartbeat = (current_time - registration.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        # 心跳超时，标记为不可用
                        if registration.status in [AgentStatus.IDLE, AgentStatus.BUSY]:
                            registration.status = AgentStatus.INACTIVE
                            self.coordination_stats["active_agents"] -= 1
                            self.logger.warning(f"智能体心跳超时: {agent_id}")
                
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳监控异常: {e}")
                await asyncio.sleep(5)
    
    async def _performance_monitor(self):
        """性能监控工作线程"""
        while self.is_running:
            try:
                # 更新智能体性能指标
                for registration in self.registered_agents.values():
                    if hasattr(registration.agent_instance, 'performance_metrics'):
                        registration.performance_metrics = registration.agent_instance.performance_metrics
                    
                    # 更新负载因子
                    if hasattr(registration.agent_instance, 'current_tasks'):
                        max_tasks = getattr(registration.agent_instance.config, 'max_concurrent_tasks', 5)
                        current_tasks = len(registration.agent_instance.current_tasks)
                        registration.load_factor = current_tasks / max_tasks
                
                await asyncio.sleep(60)  # 每分钟更新一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"性能监控异常: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_worker(self):
        """清理工作线程"""
        while self.is_running:
            try:
                # 清理过期的分配历史
                cutoff_time = datetime.now() - timedelta(days=7)
                
                original_count = len(self.assignment_history)
                self.assignment_history = [
                    assignment for assignment in self.assignment_history
                    if assignment.completed_at and assignment.completed_at > cutoff_time
                ]
                
                cleaned_count = original_count - len(self.assignment_history)
                if cleaned_count > 0:
                    self.logger.info(f"清理了 {cleaned_count} 个过期的任务分配记录")
                
                # 清理过期的协作历史
                original_collab_count = len(self.collaboration_history)
                self.collaboration_history = [
                    session for session in self.collaboration_history
                    if session.ended_at and session.ended_at > cutoff_time
                ]
                
                cleaned_collab_count = original_collab_count - len(self.collaboration_history)
                if cleaned_collab_count > 0:
                    self.logger.info(f"清理了 {cleaned_collab_count} 个过期的协作会话记录")
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理工作异常: {e}")
                await asyncio.sleep(300)
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体状态"""
        if agent_id not in self.registered_agents:
            return None
        
        registration = self.registered_agents[agent_id]
        
        return {
            "agent_id": agent_id,
            "agent_name": registration.agent_name,
            "agent_type": registration.agent_type,
            "status": registration.status.value,
            "capabilities": [asdict(cap) for cap in registration.capabilities],
            "performance_metrics": registration.performance_metrics,
            "load_factor": registration.load_factor,
            "last_heartbeat": registration.last_heartbeat.isoformat(),
            "registration_time": registration.registration_time.isoformat()
        }
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """获取协调器统计信息"""
        uptime = datetime.now() - self.coordination_stats["coordinator_start_time"]
        
        return {
            **self.coordination_stats,
            "uptime_seconds": uptime.total_seconds(),
            "active_assignments": len(self.active_assignments),
            "active_collaborations": len(self.active_collaborations),
            "assignment_history_count": len(self.assignment_history),
            "collaboration_history_count": len(self.collaboration_history),
            "is_running": self.is_running
        }
    
    async def update_agent_heartbeat(self, agent_id: str) -> bool:
        """更新智能体心跳"""
        if agent_id in self.registered_agents:
            registration = self.registered_agents[agent_id]
            registration.last_heartbeat = datetime.now()
            
            # 如果之前是不活跃状态，恢复为空闲状态
            if registration.status == AgentStatus.INACTIVE:
                registration.status = AgentStatus.IDLE
                self.coordination_stats["active_agents"] += 1
                self.logger.info(f"智能体已恢复活跃: {agent_id}")
            
            return True
        
        return False
    
    async def shutdown(self):
        """关闭智能体协调器"""
        try:
            self.logger.info("关闭智能体协调器...")
            
            self.is_running = False
            
            # 取消所有工作任务
            for task in self.worker_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 取消所有活跃的任务分配
            for assignment in list(self.active_assignments.values()):
                assignment.status = "cancelled"
                assignment.error = "协调器关闭"
                assignment.completed_at = datetime.now()
                await self._finalize_assignment(assignment)
            
            # 结束所有活跃的协作会话
            for session_id in list(self.active_collaborations.keys()):
                await self._end_collaboration_session(session_id)
            
            self.logger.info("智能体协调器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭智能体协调器失败: {e}")


# 全局智能体协调器实例
_agent_coordinator: Optional[AgentCoordinator] = None


def get_agent_coordinator() -> AgentCoordinator:
    """获取全局智能体协调器实例"""
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator()
    return _agent_coordinator

