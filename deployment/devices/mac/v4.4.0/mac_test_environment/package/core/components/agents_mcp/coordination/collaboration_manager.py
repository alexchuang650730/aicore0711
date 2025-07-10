"""
PowerAutomation 4.0 Collaboration Manager
协作管理器 - 负责智能体之间的协作、通信和知识共享
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
from enum import Enum

from ..shared.agent_base import AgentBase, AgentStatus, AgentTask
from core.exceptions import CollaborationError, handle_exception
from core.logging_config import get_collaboration_logger
from core.config import get_config
from core.event_bus import EventType, get_event_bus


class CollaborationType(Enum):
    """协作类型枚举"""
    PEER_TO_PEER = "peer_to_peer"
    HIERARCHICAL = "hierarchical"
    SWARM = "swarm"
    PIPELINE = "pipeline"
    CONSENSUS = "consensus"
    COMPETITIVE = "competitive"


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    QUERY = "query"
    ANSWER = "answer"
    PROPOSAL = "proposal"
    VOTE = "vote"
    KNOWLEDGE_SHARE = "knowledge_share"


class CollaborationStatus(Enum):
    """协作状态枚举"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CollaborationMessage:
    """协作消息"""
    message_id: str
    sender_id: str
    receiver_id: Optional[str]  # None表示广播
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str]  # 用于关联请求和响应
    priority: int = 5
    ttl: Optional[datetime] = None  # 消息生存时间


@dataclass
class KnowledgeItem:
    """知识项"""
    knowledge_id: str
    source_agent: str
    knowledge_type: str
    content: Dict[str, Any]
    confidence: float
    created_at: datetime
    updated_at: datetime
    access_count: int
    tags: Set[str]
    metadata: Dict[str, Any]


@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    session_name: str
    collaboration_type: CollaborationType
    participants: List[str]
    coordinator: Optional[str]
    objective: str
    context: Dict[str, Any]
    status: CollaborationStatus
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    messages: List[CollaborationMessage]
    shared_knowledge: Dict[str, KnowledgeItem]
    decisions: List[Dict[str, Any]]
    metrics: Dict[str, Any]


class CollaborationManager:
    """协作管理器"""
    
    def __init__(self):
        self.logger = get_collaboration_logger()
        self.config = get_config()
        self.event_bus = get_event_bus()
        
        # 协作会话管理
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.session_history: List[CollaborationSession] = []
        
        # 消息管理
        self.message_queues: Dict[str, asyncio.Queue] = {}  # agent_id -> queue
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # 知识管理
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.knowledge_index: Dict[str, Set[str]] = {}  # tag -> knowledge_ids
        
        # 协作策略
        self.collaboration_strategies: Dict[CollaborationType, Callable] = {}
        
        # 统计信息
        self.collaboration_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "completed_sessions": 0,
            "failed_sessions": 0,
            "total_messages": 0,
            "knowledge_items": 0,
            "manager_start_time": datetime.now()
        }
        
        # 运行状态
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # 配置参数
        self.max_session_duration = 3600  # 秒
        self.message_timeout = 30  # 秒
        self.max_message_queue_size = 1000
        self.knowledge_retention_days = 30
    
    async def initialize(self) -> bool:
        """初始化协作管理器"""
        try:
            self.logger.info("初始化协作管理器...")
            
            # 注册消息处理器
            await self._register_message_handlers()
            
            # 注册协作策略
            await self._register_collaboration_strategies()
            
            # 注册事件处理器
            await self._register_event_handlers()
            
            # 启动工作线程
            self.is_running = True
            self.worker_tasks = [
                asyncio.create_task(self._message_processor()),
                asyncio.create_task(self._session_monitor()),
                asyncio.create_task(self._knowledge_maintenance()),
                asyncio.create_task(self._cleanup_worker())
            ]
            
            self.logger.info("协作管理器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"协作管理器初始化失败: {e}")
            return False
    
    async def create_collaboration_session(
        self,
        session_name: str,
        collaboration_type: CollaborationType,
        participants: List[str],
        objective: str,
        coordinator: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建协作会话"""
        try:
            session_id = str(uuid.uuid4())
            
            # 验证参与者
            if len(participants) < 2:
                raise CollaborationError("协作会话至少需要2个参与者")
            
            # 创建会话
            session = CollaborationSession(
                session_id=session_id,
                session_name=session_name,
                collaboration_type=collaboration_type,
                participants=participants,
                coordinator=coordinator,
                objective=objective,
                context=context or {},
                status=CollaborationStatus.INITIALIZING,
                created_at=datetime.now(),
                started_at=None,
                ended_at=None,
                messages=[],
                shared_knowledge={},
                decisions=[],
                metrics={}
            )
            
            # 存储会话
            self.active_sessions[session_id] = session
            
            # 为参与者创建消息队列
            for participant in participants:
                if participant not in self.message_queues:
                    self.message_queues[participant] = asyncio.Queue(maxsize=self.max_message_queue_size)
            
            # 发送会话创建通知
            await self._notify_session_participants(session, "session_created")
            
            # 更新统计
            self.collaboration_stats["total_sessions"] += 1
            self.collaboration_stats["active_sessions"] += 1
            
            self.logger.info(f"协作会话已创建: {session_name} ({session_id})")
            return session_id
            
        except Exception as e:
            self.logger.error(f"创建协作会话失败: {e}")
            raise CollaborationError(f"创建协作会话失败: {str(e)}")
    
    async def start_collaboration_session(self, session_id: str) -> bool:
        """启动协作会话"""
        try:
            if session_id not in self.active_sessions:
                raise CollaborationError(f"协作会话不存在: {session_id}")
            
            session = self.active_sessions[session_id]
            
            if session.status != CollaborationStatus.INITIALIZING:
                raise CollaborationError(f"协作会话状态不正确: {session.status}")
            
            # 启动会话
            session.status = CollaborationStatus.ACTIVE
            session.started_at = datetime.now()
            
            # 根据协作类型执行启动策略
            if session.collaboration_type in self.collaboration_strategies:
                strategy = self.collaboration_strategies[session.collaboration_type]
                await strategy(session, "start")
            
            # 发送会话启动通知
            await self._notify_session_participants(session, "session_started")
            
            self.logger.info(f"协作会话已启动: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动协作会话失败: {e}")
            return False
    
    async def end_collaboration_session(self, session_id: str, reason: str = "completed") -> bool:
        """结束协作会话"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # 结束会话
            if reason == "completed":
                session.status = CollaborationStatus.COMPLETED
                self.collaboration_stats["completed_sessions"] += 1
            else:
                session.status = CollaborationStatus.FAILED
                self.collaboration_stats["failed_sessions"] += 1
            
            session.ended_at = datetime.now()
            
            # 计算会话指标
            await self._calculate_session_metrics(session)
            
            # 发送会话结束通知
            await self._notify_session_participants(session, "session_ended")
            
            # 移动到历史记录
            self.session_history.append(session)
            del self.active_sessions[session_id]
            
            # 更新统计
            self.collaboration_stats["active_sessions"] -= 1
            
            # 保持历史记录在合理范围内
            if len(self.session_history) > 100:
                self.session_history = self.session_history[-80:]
            
            self.logger.info(f"协作会话已结束: {session_id}, 原因: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"结束协作会话失败: {e}")
            return False
    
    async def send_message(
        self,
        sender_id: str,
        receiver_id: Optional[str],
        message_type: MessageType,
        content: Dict[str, Any],
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """发送消息"""
        try:
            message_id = str(uuid.uuid4())
            
            # 创建消息
            message = CollaborationMessage(
                message_id=message_id,
                sender_id=sender_id,
                receiver_id=receiver_id,
                message_type=message_type,
                content=content,
                timestamp=datetime.now(),
                correlation_id=correlation_id,
                priority=priority,
                ttl=datetime.now() + timedelta(seconds=self.message_timeout)
            )
            
            # 如果指定了会话，添加到会话消息历史
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.messages.append(message)
            
            # 分发消息
            await self._distribute_message(message)
            
            # 更新统计
            self.collaboration_stats["total_messages"] += 1
            
            self.logger.debug(f"消息已发送: {sender_id} -> {receiver_id or 'broadcast'} ({message_type.value})")
            return message_id
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            raise CollaborationError(f"发送消息失败: {str(e)}")
    
    async def send_request(
        self,
        sender_id: str,
        receiver_id: str,
        request_content: Dict[str, Any],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """发送请求并等待响应"""
        try:
            correlation_id = str(uuid.uuid4())
            
            # 创建响应Future
            response_future = asyncio.Future()
            self.pending_responses[correlation_id] = response_future
            
            # 发送请求
            await self.send_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message_type=MessageType.REQUEST,
                content=request_content,
                correlation_id=correlation_id
            )
            
            # 等待响应
            try:
                response = await asyncio.wait_for(response_future, timeout=timeout)
                return response
            except asyncio.TimeoutError:
                raise CollaborationError(f"请求超时: {sender_id} -> {receiver_id}")
            finally:
                # 清理
                if correlation_id in self.pending_responses:
                    del self.pending_responses[correlation_id]
            
        except Exception as e:
            self.logger.error(f"发送请求失败: {e}")
            raise CollaborationError(f"发送请求失败: {str(e)}")
    
    async def broadcast_message(
        self,
        sender_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        session_id: Optional[str] = None,
        exclude_sender: bool = True
    ) -> List[str]:
        """广播消息"""
        try:
            recipients = []
            
            if session_id and session_id in self.active_sessions:
                # 向会话参与者广播
                session = self.active_sessions[session_id]
                recipients = session.participants.copy()
                if exclude_sender and sender_id in recipients:
                    recipients.remove(sender_id)
            else:
                # 向所有注册的智能体广播
                recipients = list(self.message_queues.keys())
                if exclude_sender and sender_id in recipients:
                    recipients.remove(sender_id)
            
            # 发送消息给每个接收者
            message_ids = []
            for receiver_id in recipients:
                message_id = await self.send_message(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    message_type=message_type,
                    content=content,
                    session_id=session_id
                )
                message_ids.append(message_id)
            
            self.logger.info(f"广播消息已发送: {sender_id} -> {len(recipients)} 个接收者")
            return message_ids
            
        except Exception as e:
            self.logger.error(f"广播消息失败: {e}")
            raise CollaborationError(f"广播消息失败: {str(e)}")
    
    async def share_knowledge(
        self,
        source_agent: str,
        knowledge_type: str,
        content: Dict[str, Any],
        confidence: float = 1.0,
        tags: Optional[Set[str]] = None,
        session_id: Optional[str] = None
    ) -> str:
        """分享知识"""
        try:
            knowledge_id = str(uuid.uuid4())
            
            # 创建知识项
            knowledge_item = KnowledgeItem(
                knowledge_id=knowledge_id,
                source_agent=source_agent,
                knowledge_type=knowledge_type,
                content=content,
                confidence=confidence,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                access_count=0,
                tags=tags or set(),
                metadata={"session_id": session_id} if session_id else {}
            )
            
            # 存储知识
            self.knowledge_base[knowledge_id] = knowledge_item
            
            # 更新索引
            for tag in knowledge_item.tags:
                if tag not in self.knowledge_index:
                    self.knowledge_index[tag] = set()
                self.knowledge_index[tag].add(knowledge_id)
            
            # 如果在会话中，添加到会话共享知识
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.shared_knowledge[knowledge_id] = knowledge_item
                
                # 通知会话参与者
                await self.broadcast_message(
                    sender_id=source_agent,
                    message_type=MessageType.KNOWLEDGE_SHARE,
                    content={
                        "knowledge_id": knowledge_id,
                        "knowledge_type": knowledge_type,
                        "summary": content.get("summary", ""),
                        "confidence": confidence
                    },
                    session_id=session_id
                )
            
            # 更新统计
            self.collaboration_stats["knowledge_items"] += 1
            
            self.logger.info(f"知识已分享: {source_agent} -> {knowledge_type} ({knowledge_id})")
            return knowledge_id
            
        except Exception as e:
            self.logger.error(f"分享知识失败: {e}")
            raise CollaborationError(f"分享知识失败: {str(e)}")
    
    async def query_knowledge(
        self,
        requester_id: str,
        query: Dict[str, Any],
        tags: Optional[Set[str]] = None,
        min_confidence: float = 0.0
    ) -> List[KnowledgeItem]:
        """查询知识"""
        try:
            results = []
            
            # 根据标签筛选
            candidate_ids = set()
            if tags:
                for tag in tags:
                    if tag in self.knowledge_index:
                        candidate_ids.update(self.knowledge_index[tag])
            else:
                candidate_ids = set(self.knowledge_base.keys())
            
            # 筛选知识项
            for knowledge_id in candidate_ids:
                knowledge_item = self.knowledge_base[knowledge_id]
                
                # 检查置信度
                if knowledge_item.confidence < min_confidence:
                    continue
                
                # 检查查询匹配
                if await self._match_knowledge_query(knowledge_item, query):
                    # 更新访问计数
                    knowledge_item.access_count += 1
                    results.append(knowledge_item)
            
            # 按置信度和访问次数排序
            results.sort(key=lambda x: (x.confidence, x.access_count), reverse=True)
            
            self.logger.debug(f"知识查询完成: {requester_id}, 找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            self.logger.error(f"查询知识失败: {e}")
            return []
    
    async def _distribute_message(self, message: CollaborationMessage):
        """分发消息"""
        try:
            if message.receiver_id:
                # 单播消息
                if message.receiver_id in self.message_queues:
                    queue = self.message_queues[message.receiver_id]
                    try:
                        queue.put_nowait(message)
                    except asyncio.QueueFull:
                        self.logger.warning(f"消息队列已满: {message.receiver_id}")
                else:
                    self.logger.warning(f"接收者不存在: {message.receiver_id}")
            else:
                # 广播消息
                for agent_id, queue in self.message_queues.items():
                    if agent_id != message.sender_id:  # 不发送给发送者
                        try:
                            queue.put_nowait(message)
                        except asyncio.QueueFull:
                            self.logger.warning(f"消息队列已满: {agent_id}")
            
        except Exception as e:
            self.logger.error(f"分发消息失败: {e}")
    
    async def _message_processor(self):
        """消息处理工作线程"""
        while self.is_running:
            try:
                # 处理所有智能体的消息队列
                for agent_id, queue in self.message_queues.items():
                    try:
                        # 非阻塞获取消息
                        message = queue.get_nowait()
                        
                        # 检查消息是否过期
                        if message.ttl and datetime.now() > message.ttl:
                            self.logger.debug(f"消息已过期: {message.message_id}")
                            continue
                        
                        # 处理消息
                        await self._handle_message(message)
                        
                    except asyncio.QueueEmpty:
                        continue
                    except Exception as e:
                        self.logger.error(f"处理消息异常: {e}")
                
                await asyncio.sleep(0.1)  # 短暂休眠
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"消息处理工作线程异常: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: CollaborationMessage):
        """处理单个消息"""
        try:
            # 根据消息类型处理
            if message.message_type in self.message_handlers:
                handler = self.message_handlers[message.message_type]
                await handler(message)
            else:
                self.logger.warning(f"未知消息类型: {message.message_type}")
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {message.message_id}, 错误: {e}")
    
    async def _handle_request_message(self, message: CollaborationMessage):
        """处理请求消息"""
        # 这里可以实现请求处理逻辑
        # 暂时只记录日志
        self.logger.debug(f"收到请求: {message.sender_id} -> {message.receiver_id}")
    
    async def _handle_response_message(self, message: CollaborationMessage):
        """处理响应消息"""
        if message.correlation_id and message.correlation_id in self.pending_responses:
            future = self.pending_responses[message.correlation_id]
            if not future.done():
                future.set_result(message.content)
    
    async def _handle_notification_message(self, message: CollaborationMessage):
        """处理通知消息"""
        self.logger.debug(f"收到通知: {message.sender_id} -> {message.receiver_id}")
    
    async def _handle_broadcast_message(self, message: CollaborationMessage):
        """处理广播消息"""
        self.logger.debug(f"收到广播: {message.sender_id}")
    
    async def _handle_query_message(self, message: CollaborationMessage):
        """处理查询消息"""
        self.logger.debug(f"收到查询: {message.sender_id}")
    
    async def _handle_answer_message(self, message: CollaborationMessage):
        """处理回答消息"""
        self.logger.debug(f"收到回答: {message.sender_id}")
    
    async def _handle_proposal_message(self, message: CollaborationMessage):
        """处理提案消息"""
        self.logger.debug(f"收到提案: {message.sender_id}")
    
    async def _handle_vote_message(self, message: CollaborationMessage):
        """处理投票消息"""
        self.logger.debug(f"收到投票: {message.sender_id}")
    
    async def _handle_knowledge_share_message(self, message: CollaborationMessage):
        """处理知识分享消息"""
        self.logger.debug(f"收到知识分享: {message.sender_id}")
    
    async def _notify_session_participants(self, session: CollaborationSession, event_type: str):
        """通知会话参与者"""
        try:
            notification_content = {
                "event_type": event_type,
                "session_id": session.session_id,
                "session_name": session.session_name,
                "timestamp": datetime.now().isoformat()
            }
            
            for participant in session.participants:
                await self.send_message(
                    sender_id="collaboration_manager",
                    receiver_id=participant,
                    message_type=MessageType.NOTIFICATION,
                    content=notification_content
                )
            
        except Exception as e:
            self.logger.error(f"通知会话参与者失败: {e}")
    
    async def _calculate_session_metrics(self, session: CollaborationSession):
        """计算会话指标"""
        try:
            if session.started_at and session.ended_at:
                duration = (session.ended_at - session.started_at).total_seconds()
                session.metrics["duration_seconds"] = duration
            
            session.metrics["total_messages"] = len(session.messages)
            session.metrics["participants_count"] = len(session.participants)
            session.metrics["knowledge_items_shared"] = len(session.shared_knowledge)
            session.metrics["decisions_made"] = len(session.decisions)
            
            # 计算参与度
            participant_message_counts = {}
            for message in session.messages:
                sender = message.sender_id
                participant_message_counts[sender] = participant_message_counts.get(sender, 0) + 1
            
            session.metrics["participant_engagement"] = participant_message_counts
            
        except Exception as e:
            self.logger.error(f"计算会话指标失败: {e}")
    
    async def _match_knowledge_query(self, knowledge_item: KnowledgeItem, query: Dict[str, Any]) -> bool:
        """匹配知识查询"""
        # 简单的匹配逻辑
        query_type = query.get("type")
        if query_type and knowledge_item.knowledge_type != query_type:
            return False
        
        query_keywords = query.get("keywords", [])
        if query_keywords:
            content_text = json.dumps(knowledge_item.content).lower()
            for keyword in query_keywords:
                if keyword.lower() not in content_text:
                    return False
        
        return True
    
    async def _register_message_handlers(self):
        """注册消息处理器"""
        self.message_handlers = {
            MessageType.REQUEST: self._handle_request_message,
            MessageType.RESPONSE: self._handle_response_message,
            MessageType.NOTIFICATION: self._handle_notification_message,
            MessageType.BROADCAST: self._handle_broadcast_message,
            MessageType.QUERY: self._handle_query_message,
            MessageType.ANSWER: self._handle_answer_message,
            MessageType.PROPOSAL: self._handle_proposal_message,
            MessageType.VOTE: self._handle_vote_message,
            MessageType.KNOWLEDGE_SHARE: self._handle_knowledge_share_message
        }
    
    async def _register_collaboration_strategies(self):
        """注册协作策略"""
        self.collaboration_strategies = {
            CollaborationType.PEER_TO_PEER: self._peer_to_peer_strategy,
            CollaborationType.HIERARCHICAL: self._hierarchical_strategy,
            CollaborationType.SWARM: self._swarm_strategy,
            CollaborationType.PIPELINE: self._pipeline_strategy,
            CollaborationType.CONSENSUS: self._consensus_strategy,
            CollaborationType.COMPETITIVE: self._competitive_strategy
        }
    
    async def _register_event_handlers(self):
        """注册事件处理器"""
        await self.event_bus.subscribe(EventType.AGENT_REGISTERED, self._handle_agent_registered)
        await self.event_bus.subscribe(EventType.AGENT_UNREGISTERED, self._handle_agent_unregistered)
    
    async def _handle_agent_registered(self, event_data: Dict[str, Any]):
        """处理智


能体注册事件"""
        agent_id = event_data.get('agent_id')
        if agent_id and agent_id not in self.message_queues:
            self.message_queues[agent_id] = asyncio.Queue(maxsize=self.max_message_queue_size)
            self.logger.info(f"为新注册智能体创建消息队列: {agent_id}")
    
    async def _handle_agent_unregistered(self, event_data: Dict[str, Any]):
        """处理智能体注销事件"""
        agent_id = event_data.get('agent_id')
        if agent_id and agent_id in self.message_queues:
            del self.message_queues[agent_id]
            self.logger.info(f"删除已注销智能体的消息队列: {agent_id}")
    
    async def _session_monitor(self):
        """会话监控工作线程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 检查会话超时
                for session_id, session in list(self.active_sessions.items()):
                    if session.started_at:
                        duration = (current_time - session.started_at).total_seconds()
                        if duration > self.max_session_duration:
                            await self.end_collaboration_session(session_id, "timeout")
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"会话监控异常: {e}")
                await asyncio.sleep(10)
    
    async def _knowledge_maintenance(self):
        """知识维护工作线程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(days=self.knowledge_retention_days)
                
                # 清理过期知识
                expired_knowledge = []
                for knowledge_id, knowledge_item in self.knowledge_base.items():
                    if knowledge_item.created_at < cutoff_time:
                        expired_knowledge.append(knowledge_id)
                
                for knowledge_id in expired_knowledge:
                    knowledge_item = self.knowledge_base[knowledge_id]
                    # 从索引中移除
                    for tag in knowledge_item.tags:
                        if tag in self.knowledge_index:
                            self.knowledge_index[tag].discard(knowledge_id)
                            if not self.knowledge_index[tag]:
                                del self.knowledge_index[tag]
                    
                    del self.knowledge_base[knowledge_id]
                    self.collaboration_stats["knowledge_items"] -= 1
                
                if expired_knowledge:
                    self.logger.info(f"清理了 {len(expired_knowledge)} 个过期知识项")
                
                await asyncio.sleep(3600)  # 每小时检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"知识维护异常: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_worker(self):
        """清理工作线程"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 清理过期的待响应请求
                expired_requests = []
                for correlation_id, future in self.pending_responses.items():
                    if future.done() or (current_time - datetime.now()).total_seconds() > self.message_timeout:
                        expired_requests.append(correlation_id)
                
                for correlation_id in expired_requests:
                    future = self.pending_responses.pop(correlation_id, None)
                    if future and not future.done():
                        future.cancel()
                
                await asyncio.sleep(30)  # 每30秒清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理工作异常: {e}")
                await asyncio.sleep(10)
    
    # 协作策略实现
    
    async def _peer_to_peer_strategy(self, session: CollaborationSession, action: str):
        """点对点协作策略"""
        if action == "start":
            # 通知所有参与者开始协作
            await self.broadcast_message(
                sender_id="collaboration_manager",
                message_type=MessageType.NOTIFICATION,
                content={
                    "action": "start_peer_collaboration",
                    "session_id": session.session_id,
                    "participants": session.participants
                },
                session_id=session.session_id
            )
    
    async def _hierarchical_strategy(self, session: CollaborationSession, action: str):
        """分层协作策略"""
        if action == "start" and session.coordinator:
            # 通知协调者开始分层协作
            await self.send_message(
                sender_id="collaboration_manager",
                receiver_id=session.coordinator,
                message_type=MessageType.NOTIFICATION,
                content={
                    "action": "start_hierarchical_collaboration",
                    "session_id": session.session_id,
                    "subordinates": [p for p in session.participants if p != session.coordinator]
                },
                session_id=session.session_id
            )
    
    async def _swarm_strategy(self, session: CollaborationSession, action: str):
        """群体协作策略"""
        if action == "start":
            # 启动群体协作
            await self.broadcast_message(
                sender_id="collaboration_manager",
                message_type=MessageType.NOTIFICATION,
                content={
                    "action": "start_swarm_collaboration",
                    "session_id": session.session_id,
                    "swarm_size": len(session.participants)
                },
                session_id=session.session_id
            )
    
    async def _pipeline_strategy(self, session: CollaborationSession, action: str):
        """流水线协作策略"""
        if action == "start":
            # 设置流水线顺序
            pipeline_order = session.participants.copy()
            for i, agent_id in enumerate(pipeline_order):
                next_agent = pipeline_order[(i + 1) % len(pipeline_order)] if len(pipeline_order) > 1 else None
                
                await self.send_message(
                    sender_id="collaboration_manager",
                    receiver_id=agent_id,
                    message_type=MessageType.NOTIFICATION,
                    content={
                        "action": "start_pipeline_collaboration",
                        "session_id": session.session_id,
                        "position": i,
                        "next_agent": next_agent,
                        "is_first": i == 0,
                        "is_last": i == len(pipeline_order) - 1
                    },
                    session_id=session.session_id
                )
    
    async def _consensus_strategy(self, session: CollaborationSession, action: str):
        """共识协作策略"""
        if action == "start":
            # 启动共识协作
            await self.broadcast_message(
                sender_id="collaboration_manager",
                message_type=MessageType.NOTIFICATION,
                content={
                    "action": "start_consensus_collaboration",
                    "session_id": session.session_id,
                    "required_consensus": len(session.participants) // 2 + 1
                },
                session_id=session.session_id
            )
    
    async def _competitive_strategy(self, session: CollaborationSession, action: str):
        """竞争协作策略"""
        if action == "start":
            # 启动竞争协作
            await self.broadcast_message(
                sender_id="collaboration_manager",
                message_type=MessageType.NOTIFICATION,
                content={
                    "action": "start_competitive_collaboration",
                    "session_id": session.session_id,
                    "competitors": session.participants
                },
                session_id=session.session_id
            )
    
    def get_collaboration_stats(self) -> Dict[str, Any]:
        """获取协作统计信息"""
        return self.collaboration_stats.copy()
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "status": session.status.value,
                "participants": session.participants,
                "message_count": len(session.messages),
                "knowledge_count": len(session.shared_knowledge),
                "created_at": session.created_at.isoformat(),
                "started_at": session.started_at.isoformat() if session.started_at else None
            }
        return None
    
    async def shutdown(self):
        """关闭协作管理器"""
        try:
            self.logger.info("关闭协作管理器...")
            
            # 停止运行
            self.is_running = False
            
            # 取消工作任务
            for task in self.worker_tasks:
                task.cancel()
            
            # 等待任务完成
            if self.worker_tasks:
                await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
            # 结束所有活跃会话
            for session_id in list(self.active_sessions.keys()):
                await self.end_collaboration_session(session_id, "manager_shutdown")
            
            self.logger.info("协作管理器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭协作管理器失败: {e}")


# 全局协作管理器实例
_collaboration_manager: Optional[CollaborationManager] = None


def get_collaboration_manager() -> CollaborationManager:
    """获取全局协作管理器实例"""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = CollaborationManager()
    return _collaboration_manager

