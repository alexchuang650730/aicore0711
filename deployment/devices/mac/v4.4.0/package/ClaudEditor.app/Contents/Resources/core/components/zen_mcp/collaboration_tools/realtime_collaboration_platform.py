"""
Zen MCP实时协作平台

提供实时协作功能，包括：
- 实时代码编辑
- 多人同步协作
- 冲突解决机制
- 协作历史追踪
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import websockets
from collections import defaultdict

logger = logging.getLogger(__name__)

class CollaborationType(Enum):
    """协作类型枚举"""
    CODE_EDITING = "code_editing"
    DOCUMENT_EDITING = "document_editing"
    DESIGN_REVIEW = "design_review"
    BRAINSTORMING = "brainstorming"
    DEBUGGING = "debugging"
    TESTING = "testing"

class UserRole(Enum):
    """用户角色枚举"""
    OWNER = "owner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
    GUEST = "guest"

class OperationType(Enum):
    """操作类型枚举"""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    MOVE = "move"
    FORMAT = "format"
    COMMENT = "comment"

@dataclass
class CollaborationUser:
    """协作用户数据结构"""
    id: str
    name: str
    email: str
    role: UserRole
    avatar_url: str
    is_online: bool
    last_active: datetime
    cursor_position: Dict[str, Any]
    selection_range: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CollaborationOperation:
    """协作操作数据结构"""
    id: str
    user_id: str
    operation_type: OperationType
    target_resource: str
    position: Dict[str, Any]
    content: str
    timestamp: datetime
    applied: bool = False
    conflicts: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CollaborationSession:
    """协作会话数据结构"""
    id: str
    name: str
    collaboration_type: CollaborationType
    owner_id: str
    participants: List[str]
    resources: List[str]
    created_at: datetime
    last_activity: datetime
    is_active: bool = True
    settings: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ConflictResolution:
    """冲突解决数据结构"""
    id: str
    session_id: str
    conflicting_operations: List[str]
    resolution_strategy: str
    resolved_operation: str
    resolver_id: str
    resolved_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class RealtimeCollaborationPlatform:
    """Zen MCP实时协作平台核心类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化实时协作平台
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.sessions: Dict[str, CollaborationSession] = {}
        self.users: Dict[str, CollaborationUser] = {}
        self.operations: Dict[str, List[CollaborationOperation]] = defaultdict(list)
        self.conflicts: Dict[str, ConflictResolution] = {}
        self.websocket_connections: Dict[str, Set[websockets.WebSocketServerProtocol]] = defaultdict(set)
        
        # 配置参数
        self.max_sessions = self.config.get('max_sessions', 100)
        self.max_participants_per_session = self.config.get('max_participants_per_session', 50)
        self.operation_history_limit = self.config.get('operation_history_limit', 1000)
        self.conflict_resolution_timeout = self.config.get('conflict_resolution_timeout', 30)
        self.auto_save_interval = self.config.get('auto_save_interval', 60)
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            'session_created': [],
            'user_joined': [],
            'user_left': [],
            'operation_applied': [],
            'conflict_detected': [],
            'conflict_resolved': []
        }
        
        # 启动自动保存任务
        asyncio.create_task(self._auto_save_loop())
        
        logger.info("Zen MCP实时协作平台初始化完成")
    
    async def create_collaboration_session(self,
                                         name: str,
                                         collaboration_type: CollaborationType,
                                         owner_id: str,
                                         resources: List[str] = None,
                                         settings: Dict[str, Any] = None) -> str:
        """
        创建协作会话
        
        Args:
            name: 会话名称
            collaboration_type: 协作类型
            owner_id: 所有者ID
            resources: 资源列表
            settings: 会话设置
            
        Returns:
            会话ID
        """
        try:
            if len(self.sessions) >= self.max_sessions:
                raise ValueError(f"会话数量已达上限: {self.max_sessions}")
            
            session_id = str(uuid.uuid4())
            
            session = CollaborationSession(
                id=session_id,
                name=name,
                collaboration_type=collaboration_type,
                owner_id=owner_id,
                participants=[owner_id],
                resources=resources or [],
                created_at=datetime.now(),
                last_activity=datetime.now(),
                settings=settings or {}
            )
            
            self.sessions[session_id] = session
            
            # 触发事件回调
            await self._trigger_event('session_created', session)
            
            logger.info(f"协作会话创建成功: {session_id} ({name})")
            return session_id
            
        except Exception as e:
            logger.error(f"创建协作会话失败: {e}")
            raise
    
    async def join_session(self,
                          session_id: str,
                          user_id: str,
                          websocket: websockets.WebSocketServerProtocol = None) -> bool:
        """
        加入协作会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            websocket: WebSocket连接
            
        Returns:
            是否成功加入
        """
        try:
            if session_id not in self.sessions:
                raise ValueError(f"会话不存在: {session_id}")
            
            session = self.sessions[session_id]
            
            if not session.is_active:
                raise ValueError(f"会话已关闭: {session_id}")
            
            if len(session.participants) >= self.max_participants_per_session:
                raise ValueError(f"会话参与者已达上限: {self.max_participants_per_session}")
            
            if user_id not in session.participants:
                session.participants.append(user_id)
            
            # 更新用户状态
            if user_id in self.users:
                self.users[user_id].is_online = True
                self.users[user_id].last_active = datetime.now()
            
            # 添加WebSocket连接
            if websocket:
                self.websocket_connections[session_id].add(websocket)
            
            session.last_activity = datetime.now()
            
            # 发送会话状态给新用户
            if websocket:
                await self._send_session_state(session_id, websocket)
            
            # 通知其他参与者
            await self._broadcast_to_session(session_id, {
                'type': 'user_joined',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }, exclude_user=user_id)
            
            # 触发事件回调
            await self._trigger_event('user_joined', {
                'session_id': session_id,
                'user_id': user_id
            })
            
            logger.info(f"用户加入会话成功: {user_id} -> {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"加入协作会话失败: {e}")
            return False
    
    async def leave_session(self,
                           session_id: str,
                           user_id: str,
                           websocket: websockets.WebSocketServerProtocol = None) -> bool:
        """
        离开协作会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            websocket: WebSocket连接
            
        Returns:
            是否成功离开
        """
        try:
            if session_id not in self.sessions:
                return True  # 会话不存在，视为已离开
            
            session = self.sessions[session_id]
            
            if user_id in session.participants:
                session.participants.remove(user_id)
            
            # 移除WebSocket连接
            if websocket and websocket in self.websocket_connections[session_id]:
                self.websocket_connections[session_id].remove(websocket)
            
            # 更新用户状态
            if user_id in self.users:
                self.users[user_id].is_online = False
                self.users[user_id].last_active = datetime.now()
            
            session.last_activity = datetime.now()
            
            # 通知其他参与者
            await self._broadcast_to_session(session_id, {
                'type': 'user_left',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
            
            # 如果没有参与者了，关闭会话
            if not session.participants:
                session.is_active = False
            
            # 触发事件回调
            await self._trigger_event('user_left', {
                'session_id': session_id,
                'user_id': user_id
            })
            
            logger.info(f"用户离开会话成功: {user_id} <- {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"离开协作会话失败: {e}")
            return False
    
    async def apply_operation(self,
                             session_id: str,
                             user_id: str,
                             operation_type: OperationType,
                             target_resource: str,
                             position: Dict[str, Any],
                             content: str,
                             metadata: Dict[str, Any] = None) -> str:
        """
        应用协作操作
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            operation_type: 操作类型
            target_resource: 目标资源
            position: 位置信息
            content: 内容
            metadata: 元数据
            
        Returns:
            操作ID
        """
        try:
            if session_id not in self.sessions:
                raise ValueError(f"会话不存在: {session_id}")
            
            session = self.sessions[session_id]
            
            if user_id not in session.participants:
                raise ValueError(f"用户不在会话中: {user_id}")
            
            operation_id = str(uuid.uuid4())
            
            operation = CollaborationOperation(
                id=operation_id,
                user_id=user_id,
                operation_type=operation_type,
                target_resource=target_resource,
                position=position,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # 检查冲突
            conflicts = await self._detect_conflicts(session_id, operation)
            
            if conflicts:
                operation.conflicts = conflicts
                # 启动冲突解决流程
                await self._resolve_conflicts(session_id, operation)
            else:
                # 直接应用操作
                operation.applied = True
                self.operations[session_id].append(operation)
                
                # 限制操作历史长度
                if len(self.operations[session_id]) > self.operation_history_limit:
                    self.operations[session_id] = self.operations[session_id][-self.operation_history_limit:]
                
                # 广播操作给其他参与者
                await self._broadcast_operation(session_id, operation, exclude_user=user_id)
                
                # 触发事件回调
                await self._trigger_event('operation_applied', operation)
            
            session.last_activity = datetime.now()
            
            logger.info(f"协作操作应用: {operation_id} ({operation_type.value})")
            return operation_id
            
        except Exception as e:
            logger.error(f"应用协作操作失败: {e}")
            raise
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话状态信息
        """
        try:
            if session_id not in self.sessions:
                raise ValueError(f"会话不存在: {session_id}")
            
            session = self.sessions[session_id]
            
            # 获取在线用户
            online_users = []
            for user_id in session.participants:
                if user_id in self.users and self.users[user_id].is_online:
                    user = self.users[user_id]
                    online_users.append({
                        'id': user.id,
                        'name': user.name,
                        'role': user.role.value,
                        'cursor_position': user.cursor_position,
                        'selection_range': user.selection_range
                    })
            
            # 获取最近操作
            recent_operations = []
            if session_id in self.operations:
                recent_ops = self.operations[session_id][-50:]  # 最近50个操作
                for op in recent_ops:
                    recent_operations.append({
                        'id': op.id,
                        'user_id': op.user_id,
                        'type': op.operation_type.value,
                        'target': op.target_resource,
                        'timestamp': op.timestamp.isoformat(),
                        'applied': op.applied
                    })
            
            state = {
                'session_info': {
                    'id': session.id,
                    'name': session.name,
                    'type': session.collaboration_type.value,
                    'owner_id': session.owner_id,
                    'created_at': session.created_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'is_active': session.is_active
                },
                'participants': {
                    'total': len(session.participants),
                    'online': len(online_users),
                    'users': online_users
                },
                'resources': session.resources,
                'recent_operations': recent_operations,
                'settings': session.settings
            }
            
            return state
            
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            return {}
    
    async def get_platform_statistics(self) -> Dict[str, Any]:
        """
        获取平台统计信息
        
        Returns:
            统计信息字典
        """
        try:
            total_sessions = len(self.sessions)
            active_sessions = len([s for s in self.sessions.values() if s.is_active])
            total_users = len(self.users)
            online_users = len([u for u in self.users.values() if u.is_online])
            
            # 协作类型分布
            type_distribution = {}
            for session in self.sessions.values():
                session_type = session.collaboration_type.value
                type_distribution[session_type] = type_distribution.get(session_type, 0) + 1
            
            # 操作统计
            total_operations = sum(len(ops) for ops in self.operations.values())
            total_conflicts = len(self.conflicts)
            
            # 计算平均会话时长
            session_durations = []
            for session in self.sessions.values():
                if not session.is_active:
                    duration = (session.last_activity - session.created_at).total_seconds()
                    session_durations.append(duration)
            
            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
            
            statistics = {
                'session_statistics': {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'session_type_distribution': type_distribution,
                    'average_session_duration_seconds': round(avg_session_duration, 2)
                },
                'user_statistics': {
                    'total_users': total_users,
                    'online_users': online_users,
                    'user_activity_rate': online_users / total_users if total_users > 0 else 0
                },
                'operation_statistics': {
                    'total_operations': total_operations,
                    'total_conflicts': total_conflicts,
                    'conflict_rate': total_conflicts / total_operations if total_operations > 0 else 0
                },
                'platform_health': {
                    'session_utilization': active_sessions / self.max_sessions,
                    'average_participants_per_session': sum(len(s.participants) for s in self.sessions.values()) / total_sessions if total_sessions > 0 else 0
                }
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取平台统计信息失败: {e}")
            return {}
    
    async def _detect_conflicts(self, session_id: str, operation: CollaborationOperation) -> List[str]:
        """检测操作冲突"""
        try:
            conflicts = []
            
            if session_id not in self.operations:
                return conflicts
            
            # 检查最近的操作是否有冲突
            recent_operations = self.operations[session_id][-10:]  # 检查最近10个操作
            
            for recent_op in recent_operations:
                if (recent_op.target_resource == operation.target_resource and
                    recent_op.user_id != operation.user_id and
                    abs((operation.timestamp - recent_op.timestamp).total_seconds()) < 5):  # 5秒内的操作
                    
                    # 检查位置冲突
                    if self._check_position_conflict(recent_op.position, operation.position):
                        conflicts.append(recent_op.id)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"检测操作冲突失败: {e}")
            return []
    
    def _check_position_conflict(self, pos1: Dict[str, Any], pos2: Dict[str, Any]) -> bool:
        """检查位置冲突"""
        try:
            # 简化的位置冲突检测
            if 'line' in pos1 and 'line' in pos2:
                return abs(pos1['line'] - pos2['line']) <= 1
            
            if 'start' in pos1 and 'end' in pos1 and 'start' in pos2 and 'end' in pos2:
                # 检查范围重叠
                return not (pos1['end'] < pos2['start'] or pos2['end'] < pos1['start'])
            
            return False
            
        except Exception:
            return False
    
    async def _resolve_conflicts(self, session_id: str, operation: CollaborationOperation):
        """解决冲突"""
        try:
            # 简化的冲突解决策略：最后写入获胜
            resolution_id = str(uuid.uuid4())
            
            resolution = ConflictResolution(
                id=resolution_id,
                session_id=session_id,
                conflicting_operations=operation.conflicts,
                resolution_strategy='last_write_wins',
                resolved_operation=operation.id,
                resolver_id='system',
                resolved_at=datetime.now()
            )
            
            self.conflicts[resolution_id] = resolution
            
            # 应用解决后的操作
            operation.applied = True
            operation.conflicts = []
            self.operations[session_id].append(operation)
            
            # 广播冲突解决结果
            await self._broadcast_to_session(session_id, {
                'type': 'conflict_resolved',
                'resolution_id': resolution_id,
                'operation_id': operation.id,
                'strategy': 'last_write_wins',
                'timestamp': datetime.now().isoformat()
            })
            
            # 触发事件回调
            await self._trigger_event('conflict_resolved', resolution)
            
            logger.info(f"冲突解决完成: {resolution_id}")
            
        except Exception as e:
            logger.error(f"解决冲突失败: {e}")
    
    async def _broadcast_operation(self, session_id: str, operation: CollaborationOperation, exclude_user: str = None):
        """广播操作给会话参与者"""
        try:
            message = {
                'type': 'operation',
                'operation': {
                    'id': operation.id,
                    'user_id': operation.user_id,
                    'operation_type': operation.operation_type.value,
                    'target_resource': operation.target_resource,
                    'position': operation.position,
                    'content': operation.content,
                    'timestamp': operation.timestamp.isoformat()
                }
            }
            
            await self._broadcast_to_session(session_id, message, exclude_user)
            
        except Exception as e:
            logger.error(f"广播操作失败: {e}")
    
    async def _broadcast_to_session(self, session_id: str, message: Dict[str, Any], exclude_user: str = None):
        """向会话广播消息"""
        try:
            if session_id not in self.websocket_connections:
                return
            
            message_json = json.dumps(message)
            
            # 发送给所有连接的WebSocket
            for websocket in self.websocket_connections[session_id].copy():
                try:
                    await websocket.send(message_json)
                except websockets.exceptions.ConnectionClosed:
                    # 移除已关闭的连接
                    self.websocket_connections[session_id].discard(websocket)
                except Exception as e:
                    logger.warning(f"发送消息失败: {e}")
            
        except Exception as e:
            logger.error(f"广播消息失败: {e}")
    
    async def _send_session_state(self, session_id: str, websocket: websockets.WebSocketServerProtocol):
        """发送会话状态给特定连接"""
        try:
            state = await self.get_session_state(session_id)
            message = {
                'type': 'session_state',
                'state': state
            }
            
            await websocket.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"发送会话状态失败: {e}")
    
    async def _auto_save_loop(self):
        """自动保存循环"""
        try:
            while True:
                await asyncio.sleep(self.auto_save_interval)
                await self._auto_save_sessions()
                
        except Exception as e:
            logger.error(f"自动保存循环失败: {e}")
    
    async def _auto_save_sessions(self):
        """自动保存会话数据"""
        try:
            # 这里可以实现将会话数据保存到持久化存储
            active_sessions = [s for s in self.sessions.values() if s.is_active]
            logger.debug(f"自动保存 {len(active_sessions)} 个活跃会话")
            
        except Exception as e:
            logger.error(f"自动保存会话失败: {e}")
    
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
    
    async def register_user(self,
                           user_id: str,
                           name: str,
                           email: str,
                           role: UserRole = UserRole.EDITOR,
                           avatar_url: str = "") -> bool:
        """
        注册用户
        
        Args:
            user_id: 用户ID
            name: 用户名
            email: 邮箱
            role: 角色
            avatar_url: 头像URL
            
        Returns:
            注册是否成功
        """
        try:
            user = CollaborationUser(
                id=user_id,
                name=name,
                email=email,
                role=role,
                avatar_url=avatar_url,
                is_online=False,
                last_active=datetime.now(),
                cursor_position={},
                selection_range={}
            )
            
            self.users[user_id] = user
            
            logger.info(f"用户注册成功: {user_id} ({name})")
            return True
            
        except Exception as e:
            logger.error(f"注册用户失败: {e}")
            return False
    
    async def update_user_cursor(self,
                                session_id: str,
                                user_id: str,
                                cursor_position: Dict[str, Any],
                                selection_range: Dict[str, Any] = None):
        """
        更新用户光标位置
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            cursor_position: 光标位置
            selection_range: 选择范围
        """
        try:
            if user_id in self.users:
                user = self.users[user_id]
                user.cursor_position = cursor_position
                user.selection_range = selection_range or {}
                user.last_active = datetime.now()
                
                # 广播光标更新
                await self._broadcast_to_session(session_id, {
                    'type': 'cursor_update',
                    'user_id': user_id,
                    'cursor_position': cursor_position,
                    'selection_range': selection_range,
                    'timestamp': datetime.now().isoformat()
                }, exclude_user=user_id)
            
        except Exception as e:
            logger.error(f"更新用户光标失败: {e}")
    
    async def close_session(self, session_id: str) -> bool:
        """
        关闭会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            关闭是否成功
        """
        try:
            if session_id not in self.sessions:
                return True
            
            session = self.sessions[session_id]
            session.is_active = False
            session.last_activity = datetime.now()
            
            # 通知所有参与者
            await self._broadcast_to_session(session_id, {
                'type': 'session_closed',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            # 关闭所有WebSocket连接
            for websocket in self.websocket_connections[session_id].copy():
                try:
                    await websocket.close()
                except Exception:
                    pass
            
            self.websocket_connections[session_id].clear()
            
            logger.info(f"会话关闭成功: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"关闭会话失败: {e}")
            return False
    
    async def shutdown(self):
        """关闭平台"""
        try:
            # 关闭所有会话
            for session_id in list(self.sessions.keys()):
                await self.close_session(session_id)
            
            # 清理资源
            self.sessions.clear()
            self.operations.clear()
            self.conflicts.clear()
            self.websocket_connections.clear()
            
            logger.info("实时协作平台已关闭")
            
        except Exception as e:
            logger.error(f"关闭平台失败: {e}")

