"""
Agent Zero有机智能体框架深度集成核心模块

提供与Agent Zero有机智能体框架的深度集成功能，实现有机智能体管理和自适应学习。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """智能体类型枚举"""
    REACTIVE = "reactive"
    PROACTIVE = "proactive"
    HYBRID = "hybrid"
    LEARNING = "learning"
    COLLABORATIVE = "collaborative"

class AgentState(Enum):
    """智能体状态枚举"""
    IDLE = "idle"
    ACTIVE = "active"
    LEARNING = "learning"
    COLLABORATING = "collaborating"
    SUSPENDED = "suspended"
    ERROR = "error"

class LearningMode(Enum):
    """学习模式枚举"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    FEDERATED = "federated"

@dataclass
class AgentCapability:
    """智能体能力数据结构"""
    name: str
    description: str
    proficiency_level: float  # 0.0 - 1.0
    learning_rate: float
    last_updated: datetime
    usage_count: int = 0

@dataclass
class OrganicAgent:
    """有机智能体数据结构"""
    id: str
    name: str
    agent_type: AgentType
    state: AgentState
    capabilities: List[AgentCapability]
    learning_mode: LearningMode
    memory_capacity: int
    collaboration_score: float
    adaptation_rate: float
    created_at: datetime
    last_active: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LearningTask:
    """学习任务数据结构"""
    id: str
    agent_id: str
    task_type: str
    input_data: Any
    expected_output: Any
    learning_mode: LearningMode
    priority: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    success_rate: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CollaborationRequest:
    """协作请求数据结构"""
    id: str
    requester_id: str
    target_agents: List[str]
    task_description: str
    required_capabilities: List[str]
    priority: int
    deadline: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class AgentZeroDeepIntegration:
    """Agent Zero有机智能体框架深度集成核心类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化Agent Zero深度集成
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.agents: Dict[str, OrganicAgent] = {}
        self.learning_tasks: Dict[str, LearningTask] = {}
        self.collaboration_requests: Dict[str, CollaborationRequest] = {}
        self.agent_networks: Dict[str, List[str]] = {}
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        
        # 配置参数
        self.max_agents = self.config.get('max_agents', 100)
        self.default_memory_capacity = self.config.get('default_memory_capacity', 1000)
        self.learning_rate_decay = self.config.get('learning_rate_decay', 0.99)
        self.collaboration_threshold = self.config.get('collaboration_threshold', 0.7)
        self.adaptation_speed = self.config.get('adaptation_speed', 0.1)
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            'agent_created': [],
            'agent_learned': [],
            'collaboration_started': [],
            'collaboration_completed': [],
            'adaptation_occurred': []
        }
        
        logger.info("Agent Zero深度集成初始化完成")
    
    async def create_organic_agent(self,
                                  name: str,
                                  agent_type: AgentType,
                                  capabilities: List[Dict[str, Any]],
                                  learning_mode: LearningMode = LearningMode.SUPERVISED,
                                  memory_capacity: int = None) -> str:
        """
        创建有机智能体
        
        Args:
            name: 智能体名称
            agent_type: 智能体类型
            capabilities: 能力列表
            learning_mode: 学习模式
            memory_capacity: 记忆容量
            
        Returns:
            智能体ID
        """
        try:
            if len(self.agents) >= self.max_agents:
                raise ValueError(f"智能体数量已达上限: {self.max_agents}")
            
            agent_id = str(uuid.uuid4())
            
            # 创建能力对象
            agent_capabilities = []
            for cap_data in capabilities:
                capability = AgentCapability(
                    name=cap_data['name'],
                    description=cap_data.get('description', ''),
                    proficiency_level=cap_data.get('proficiency_level', 0.5),
                    learning_rate=cap_data.get('learning_rate', 0.01),
                    last_updated=datetime.now()
                )
                agent_capabilities.append(capability)
            
            # 创建智能体
            agent = OrganicAgent(
                id=agent_id,
                name=name,
                agent_type=agent_type,
                state=AgentState.IDLE,
                capabilities=agent_capabilities,
                learning_mode=learning_mode,
                memory_capacity=memory_capacity or self.default_memory_capacity,
                collaboration_score=0.5,
                adaptation_rate=self.adaptation_speed,
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            
            self.agents[agent_id] = agent
            self.performance_metrics[agent_id] = {
                'tasks_completed': 0,
                'learning_efficiency': 0.5,
                'collaboration_success': 0.5,
                'adaptation_speed': 0.5
            }
            
            # 触发事件回调
            await self._trigger_event('agent_created', agent)
            
            logger.info(f"有机智能体创建成功: {agent_id} ({name})")
            return agent_id
            
        except Exception as e:
            logger.error(f"创建有机智能体失败: {e}")
            raise
    
    async def assign_learning_task(self,
                                  agent_id: str,
                                  task_type: str,
                                  input_data: Any,
                                  expected_output: Any = None,
                                  priority: int = 1) -> str:
        """
        分配学习任务
        
        Args:
            agent_id: 智能体ID
            task_type: 任务类型
            input_data: 输入数据
            expected_output: 期望输出
            priority: 优先级
            
        Returns:
            任务ID
        """
        try:
            if agent_id not in self.agents:
                raise ValueError(f"智能体不存在: {agent_id}")
            
            agent = self.agents[agent_id]
            task_id = str(uuid.uuid4())
            
            learning_task = LearningTask(
                id=task_id,
                agent_id=agent_id,
                task_type=task_type,
                input_data=input_data,
                expected_output=expected_output,
                learning_mode=agent.learning_mode,
                priority=priority,
                created_at=datetime.now()
            )
            
            self.learning_tasks[task_id] = learning_task
            
            # 更新智能体状态
            agent.state = AgentState.LEARNING
            agent.last_active = datetime.now()
            
            # 异步执行学习任务
            asyncio.create_task(self._execute_learning_task(task_id))
            
            logger.info(f"学习任务分配成功: {task_id} -> {agent_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"分配学习任务失败: {e}")
            raise
    
    async def request_collaboration(self,
                                   requester_id: str,
                                   task_description: str,
                                   required_capabilities: List[str],
                                   priority: int = 1,
                                   deadline: datetime = None) -> str:
        """
        请求协作
        
        Args:
            requester_id: 请求者ID
            task_description: 任务描述
            required_capabilities: 所需能力
            priority: 优先级
            deadline: 截止时间
            
        Returns:
            协作请求ID
        """
        try:
            if requester_id not in self.agents:
                raise ValueError(f"请求者智能体不存在: {requester_id}")
            
            # 查找合适的协作伙伴
            suitable_agents = await self._find_collaboration_partners(
                required_capabilities, requester_id
            )
            
            if not suitable_agents:
                raise ValueError("未找到合适的协作伙伴")
            
            request_id = str(uuid.uuid4())
            
            collaboration_request = CollaborationRequest(
                id=request_id,
                requester_id=requester_id,
                target_agents=suitable_agents,
                task_description=task_description,
                required_capabilities=required_capabilities,
                priority=priority,
                deadline=deadline
            )
            
            self.collaboration_requests[request_id] = collaboration_request
            
            # 更新智能体状态
            for agent_id in [requester_id] + suitable_agents:
                if agent_id in self.agents:
                    self.agents[agent_id].state = AgentState.COLLABORATING
                    self.agents[agent_id].last_active = datetime.now()
            
            # 异步执行协作任务
            asyncio.create_task(self._execute_collaboration(request_id))
            
            # 触发事件回调
            await self._trigger_event('collaboration_started', collaboration_request)
            
            logger.info(f"协作请求创建成功: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"请求协作失败: {e}")
            raise
    
    async def adapt_agent_behavior(self,
                                  agent_id: str,
                                  performance_feedback: Dict[str, float],
                                  environmental_changes: Dict[str, Any] = None) -> bool:
        """
        适应智能体行为
        
        Args:
            agent_id: 智能体ID
            performance_feedback: 性能反馈
            environmental_changes: 环境变化
            
        Returns:
            适应是否成功
        """
        try:
            if agent_id not in self.agents:
                raise ValueError(f"智能体不存在: {agent_id}")
            
            agent = self.agents[agent_id]
            
            # 更新性能指标
            if agent_id in self.performance_metrics:
                metrics = self.performance_metrics[agent_id]
                for key, value in performance_feedback.items():
                    if key in metrics:
                        # 使用指数移动平均更新指标
                        alpha = agent.adaptation_rate
                        metrics[key] = alpha * value + (1 - alpha) * metrics[key]
            
            # 适应能力水平
            for capability in agent.capabilities:
                if capability.name in performance_feedback:
                    feedback = performance_feedback[capability.name]
                    
                    # 根据反馈调整熟练度
                    if feedback > 0.7:  # 表现良好
                        capability.proficiency_level = min(1.0, 
                            capability.proficiency_level + capability.learning_rate)
                    elif feedback < 0.3:  # 表现不佳
                        capability.proficiency_level = max(0.0,
                            capability.proficiency_level - capability.learning_rate * 0.5)
                    
                    capability.last_updated = datetime.now()
                    capability.usage_count += 1
            
            # 适应学习率
            overall_performance = sum(performance_feedback.values()) / len(performance_feedback)
            if overall_performance > 0.8:
                # 表现优秀，降低学习率以稳定性能
                for capability in agent.capabilities:
                    capability.learning_rate *= self.learning_rate_decay
            elif overall_performance < 0.4:
                # 表现不佳，提高学习率以加速改进
                for capability in agent.capabilities:
                    capability.learning_rate = min(0.1, capability.learning_rate * 1.1)
            
            # 更新协作分数
            if 'collaboration_success' in performance_feedback:
                collab_feedback = performance_feedback['collaboration_success']
                agent.collaboration_score = (agent.collaboration_score * 0.8 + 
                                            collab_feedback * 0.2)
            
            agent.last_active = datetime.now()
            
            # 触发事件回调
            await self._trigger_event('adaptation_occurred', {
                'agent_id': agent_id,
                'performance_feedback': performance_feedback,
                'environmental_changes': environmental_changes
            })
            
            logger.info(f"智能体行为适应完成: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"适应智能体行为失败: {e}")
            return False
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        获取智能体状态
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            智能体状态信息
        """
        try:
            if agent_id not in self.agents:
                raise ValueError(f"智能体不存在: {agent_id}")
            
            agent = self.agents[agent_id]
            metrics = self.performance_metrics.get(agent_id, {})
            
            # 计算能力统计
            capability_stats = {
                'total_capabilities': len(agent.capabilities),
                'average_proficiency': sum(cap.proficiency_level for cap in agent.capabilities) / 
                                     len(agent.capabilities) if agent.capabilities else 0,
                'most_proficient': max(agent.capabilities, 
                                     key=lambda x: x.proficiency_level).name 
                                     if agent.capabilities else None,
                'least_proficient': min(agent.capabilities,
                                      key=lambda x: x.proficiency_level).name
                                      if agent.capabilities else None
            }
            
            # 计算活跃度
            time_since_active = datetime.now() - agent.last_active
            activity_score = max(0, 1 - (time_since_active.total_seconds() / 3600))  # 1小时内为满分
            
            status = {
                'agent_info': {
                    'id': agent.id,
                    'name': agent.name,
                    'type': agent.agent_type.value,
                    'state': agent.state.value,
                    'learning_mode': agent.learning_mode.value
                },
                'capabilities': capability_stats,
                'performance_metrics': metrics,
                'collaboration_score': agent.collaboration_score,
                'adaptation_rate': agent.adaptation_rate,
                'activity_score': activity_score,
                'memory_usage': len(agent.metadata.get('memory', [])) if 'memory' in agent.metadata else 0,
                'memory_capacity': agent.memory_capacity,
                'created_at': agent.created_at.isoformat(),
                'last_active': agent.last_active.isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"获取智能体状态失败: {e}")
            return {}
    
    async def get_ecosystem_overview(self) -> Dict[str, Any]:
        """
        获取生态系统概览
        
        Returns:
            生态系统概览信息
        """
        try:
            total_agents = len(self.agents)
            active_agents = len([a for a in self.agents.values() if a.state == AgentState.ACTIVE])
            learning_agents = len([a for a in self.agents.values() if a.state == AgentState.LEARNING])
            collaborating_agents = len([a for a in self.agents.values() if a.state == AgentState.COLLABORATING])
            
            # 统计智能体类型分布
            type_distribution = {}
            for agent in self.agents.values():
                agent_type = agent.agent_type.value
                type_distribution[agent_type] = type_distribution.get(agent_type, 0) + 1
            
            # 统计学习模式分布
            learning_mode_distribution = {}
            for agent in self.agents.values():
                learning_mode = agent.learning_mode.value
                learning_mode_distribution[learning_mode] = learning_mode_distribution.get(learning_mode, 0) + 1
            
            # 计算平均性能指标
            avg_metrics = {}
            if self.performance_metrics:
                all_metrics = list(self.performance_metrics.values())
                for key in all_metrics[0].keys():
                    avg_metrics[key] = sum(metrics[key] for metrics in all_metrics) / len(all_metrics)
            
            # 协作统计
            active_collaborations = len([r for r in self.collaboration_requests.values() 
                                       if not hasattr(r, 'completed_at') or r.completed_at is None])
            
            overview = {
                'agent_statistics': {
                    'total_agents': total_agents,
                    'active_agents': active_agents,
                    'learning_agents': learning_agents,
                    'collaborating_agents': collaborating_agents,
                    'type_distribution': type_distribution,
                    'learning_mode_distribution': learning_mode_distribution
                },
                'performance_overview': {
                    'average_metrics': avg_metrics,
                    'ecosystem_health': self._calculate_ecosystem_health()
                },
                'collaboration_statistics': {
                    'active_collaborations': active_collaborations,
                    'total_collaboration_requests': len(self.collaboration_requests),
                    'network_density': self._calculate_network_density()
                },
                'learning_statistics': {
                    'active_learning_tasks': len([t for t in self.learning_tasks.values() 
                                                if t.completed_at is None]),
                    'total_learning_tasks': len(self.learning_tasks),
                    'average_success_rate': sum(t.success_rate for t in self.learning_tasks.values()) / 
                                          len(self.learning_tasks) if self.learning_tasks else 0
                }
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"获取生态系统概览失败: {e}")
            return {}
    
    async def _execute_learning_task(self, task_id: str):
        """执行学习任务"""
        try:
            if task_id not in self.learning_tasks:
                return
            
            task = self.learning_tasks[task_id]
            agent = self.agents.get(task.agent_id)
            
            if not agent:
                return
            
            # 模拟学习过程
            await asyncio.sleep(1)  # 模拟学习时间
            
            # 计算学习成功率
            relevant_capabilities = [cap for cap in agent.capabilities 
                                   if cap.name in task.task_type]
            
            if relevant_capabilities:
                avg_proficiency = sum(cap.proficiency_level for cap in relevant_capabilities) / len(relevant_capabilities)
                success_rate = min(1.0, avg_proficiency + 0.1)  # 学习有助于提高成功率
            else:
                success_rate = 0.5  # 默认成功率
            
            # 更新任务状态
            task.completed_at = datetime.now()
            task.success_rate = success_rate
            
            # 更新智能体状态
            agent.state = AgentState.ACTIVE
            
            # 更新性能指标
            if agent.id in self.performance_metrics:
                metrics = self.performance_metrics[agent.id]
                metrics['tasks_completed'] += 1
                metrics['learning_efficiency'] = (metrics['learning_efficiency'] * 0.9 + 
                                                success_rate * 0.1)
            
            # 触发事件回调
            await self._trigger_event('agent_learned', {
                'agent_id': agent.id,
                'task_id': task_id,
                'success_rate': success_rate
            })
            
            logger.info(f"学习任务完成: {task_id}, 成功率: {success_rate:.2f}")
            
        except Exception as e:
            logger.error(f"执行学习任务失败: {e}")
    
    async def _execute_collaboration(self, request_id: str):
        """执行协作任务"""
        try:
            if request_id not in self.collaboration_requests:
                return
            
            request = self.collaboration_requests[request_id]
            
            # 模拟协作过程
            await asyncio.sleep(2)  # 模拟协作时间
            
            # 计算协作成功率
            participating_agents = [self.agents[agent_id] for agent_id in request.target_agents 
                                  if agent_id in self.agents]
            participating_agents.append(self.agents[request.requester_id])
            
            avg_collaboration_score = sum(agent.collaboration_score for agent in participating_agents) / len(participating_agents)
            collaboration_success = min(1.0, avg_collaboration_score + 0.1)
            
            # 更新智能体状态
            for agent in participating_agents:
                agent.state = AgentState.ACTIVE
                agent.collaboration_score = (agent.collaboration_score * 0.8 + 
                                           collaboration_success * 0.2)
                
                # 更新性能指标
                if agent.id in self.performance_metrics:
                    metrics = self.performance_metrics[agent.id]
                    metrics['collaboration_success'] = (metrics['collaboration_success'] * 0.8 + 
                                                       collaboration_success * 0.2)
            
            # 标记协作完成
            request.metadata = request.metadata or {}
            request.metadata['completed_at'] = datetime.now().isoformat()
            request.metadata['success_rate'] = collaboration_success
            
            # 触发事件回调
            await self._trigger_event('collaboration_completed', {
                'request_id': request_id,
                'success_rate': collaboration_success,
                'participants': [agent.id for agent in participating_agents]
            })
            
            logger.info(f"协作任务完成: {request_id}, 成功率: {collaboration_success:.2f}")
            
        except Exception as e:
            logger.error(f"执行协作任务失败: {e}")
    
    async def _find_collaboration_partners(self, 
                                         required_capabilities: List[str], 
                                         requester_id: str) -> List[str]:
        """查找协作伙伴"""
        try:
            suitable_agents = []
            
            for agent_id, agent in self.agents.items():
                if agent_id == requester_id:
                    continue
                
                if agent.state not in [AgentState.IDLE, AgentState.ACTIVE]:
                    continue
                
                # 检查能力匹配
                agent_capabilities = [cap.name for cap in agent.capabilities]
                capability_match = len(set(required_capabilities) & set(agent_capabilities))
                
                if capability_match > 0 and agent.collaboration_score >= self.collaboration_threshold:
                    suitable_agents.append(agent_id)
            
            # 按协作分数排序
            suitable_agents.sort(key=lambda x: self.agents[x].collaboration_score, reverse=True)
            
            return suitable_agents[:3]  # 最多返回3个协作伙伴
            
        except Exception as e:
            logger.error(f"查找协作伙伴失败: {e}")
            return []
    
    def _calculate_ecosystem_health(self) -> float:
        """计算生态系统健康度"""
        try:
            if not self.agents:
                return 0.0
            
            # 活跃度权重
            active_ratio = len([a for a in self.agents.values() 
                              if a.state in [AgentState.ACTIVE, AgentState.LEARNING, AgentState.COLLABORATING]]) / len(self.agents)
            
            # 平均性能权重
            if self.performance_metrics:
                avg_performance = sum(
                    sum(metrics.values()) / len(metrics) 
                    for metrics in self.performance_metrics.values()
                ) / len(self.performance_metrics)
            else:
                avg_performance = 0.5
            
            # 协作活跃度权重
            collaboration_ratio = len([a for a in self.agents.values() 
                                     if a.collaboration_score > 0.6]) / len(self.agents)
            
            health_score = (active_ratio * 0.4 + avg_performance * 0.4 + collaboration_ratio * 0.2)
            return min(1.0, health_score)
            
        except Exception:
            return 0.0
    
    def _calculate_network_density(self) -> float:
        """计算网络密度"""
        try:
            if len(self.agents) < 2:
                return 0.0
            
            total_possible_connections = len(self.agents) * (len(self.agents) - 1) / 2
            actual_connections = sum(len(connections) for connections in self.agent_networks.values()) / 2
            
            return actual_connections / total_possible_connections if total_possible_connections > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def _trigger_event(self, event_type: str, data: Any):
        """触发事件回调"""
        try:
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
        except Exception as e:
            logger.error(f"触发事件回调失败: {e}")
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            logger.warning(f"未知事件类型: {event_type}")
    
    async def shutdown(self):
        """关闭生态系统"""
        try:
            # 停止所有智能体
            for agent in self.agents.values():
                agent.state = AgentState.SUSPENDED
            
            # 清理资源
            self.learning_tasks.clear()
            self.collaboration_requests.clear()
            self.agent_networks.clear()
            
            logger.info("Agent Zero生态系统已关闭")
            
        except Exception as e:
            logger.error(f"关闭生态系统失败: {e}")

