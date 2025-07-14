"""
PowerAutomation 4.0 Conversation Manager
对话管理器，支持并行多对话管理和上下文保持
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
import time

from .claude_client import ClaudeClient, ConversationContext, get_claude_client
from core.parallel_executor import get_executor
from core.event_bus import EventType, get_event_bus


@dataclass
class ConversationSession:
    """对话会话数据类"""
    id: str
    context: ConversationContext
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """对话管理器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client: Optional[ClaudeClient] = None
        self.event_bus = get_event_bus()
        
        # 对话会话管理
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_sessions = 100
        self.session_timeout = 3600  # 1小时
        
        # 并行处理
        self.active_conversations: Dict[str, asyncio.Task] = {}
        self.max_concurrent_conversations = 10
        
        # 统计信息
        self.stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_messages": 0,
            "concurrent_conversations": 0
        }
    
    async def initialize(self):
        """初始化对话管理器"""
        self.client = await get_claude_client()
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_expired_sessions())
        
        self.logger.info("对话管理器已初始化")
    
    async def create_session(
        self,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """创建新的对话会话"""
        if not self.client:
            await self.initialize()
        
        # 生成会话ID
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 检查会话是否已存在
        if session_id in self.sessions:
            raise ValueError(f"会话已存在: {session_id}")
        
        # 检查会话数量限制
        if len(self.sessions) >= self.max_sessions:
            await self._cleanup_oldest_sessions()
        
        # 创建对话上下文
        context = await self.client.create_conversation_context(
            conversation_id=session_id,
            system_prompt=system_prompt,
            model=model,
            max_tokens=max_tokens
        )
        
        # 创建会话
        session = ConversationSession(
            id=session_id,
            context=context,
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        self.stats["total_sessions"] += 1
        self.stats["active_sessions"] += 1
        
        # 发布会话创建事件
        await self.event_bus.publish(
            EventType.AGENT_MESSAGE,
            "conversation_manager",
            {
                "action": "session_created",
                "session_id": session_id,
                "metadata": metadata
            }
        )
        
        self.logger.info(f"已创建对话会话: {session_id}")
        return session_id
    
    async def send_message(
        self,
        session_id: str,
        message: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """发送消息到指定会话"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        if not session.is_active:
            raise ValueError(f"会话已关闭: {session_id}")
        
        # 更新最后活动时间
        session.last_activity = time.time()
        
        try:
            # 发送消息
            if stream:
                return await self._send_streaming_message(session, message)
            else:
                return await self._send_regular_message(session, message)
                
        except Exception as e:
            self.logger.error(f"发送消息失败 (会话: {session_id}): {e}")
            raise
    
    async def send_parallel_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """并行发送多个消息到不同会话"""
        if len(messages) > self.max_concurrent_conversations:
            raise ValueError(f"并发对话数量超过限制: {self.max_concurrent_conversations}")
        
        tasks = []
        for msg_data in messages:
            session_id = msg_data.get("session_id")
            message = msg_data.get("message")
            stream = msg_data.get("stream", False)
            
            if not session_id or not message:
                continue
            
            task = asyncio.create_task(
                self.send_message(session_id, message, stream)
            )
            tasks.append(task)
        
        # 并行执行所有消息发送
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "session_id": messages[i].get("session_id")
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取会话历史"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")
        
        messages = session.context.messages
        if limit:
            messages = messages[-limit:]
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
    
    async def close_session(self, session_id: str) -> bool:
        """关闭会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        self.stats["active_sessions"] -= 1
        
        # 取消正在进行的对话
        if session_id in self.active_conversations:
            self.active_conversations[session_id].cancel()
            del self.active_conversations[session_id]
        
        # 发布会话关闭事件
        await self.event_bus.publish(
            EventType.AGENT_MESSAGE,
            "conversation_manager",
            {
                "action": "session_closed",
                "session_id": session_id
            }
        )
        
        self.logger.info(f"已关闭对话会话: {session_id}")
        return True
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """获取活跃会话列表"""
        active_sessions = []
        
        for session in self.sessions.values():
            if session.is_active:
                active_sessions.append({
                    "id": session.id,
                    "created_at": session.created_at,
                    "last_activity": session.last_activity,
                    "message_count": len(session.context.messages),
                    "metadata": session.metadata
                })
        
        return active_sessions
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        self.stats["concurrent_conversations"] = len(self.active_conversations)
        return self.stats.copy()
    
    async def _send_regular_message(
        self,
        session: ConversationSession,
        message: str
    ) -> Dict[str, Any]:
        """发送常规消息"""
        result = await self.client.send_message(
            message=message,
            context=session.context,
            stream=False
        )
        
        self.stats["total_messages"] += 1
        
        # 发布消息事件
        await self.event_bus.publish(
            EventType.AGENT_MESSAGE,
            "conversation_manager",
            {
                "action": "message_sent",
                "session_id": session.id,
                "message": message,
                "response": result.get("content", "")
            }
        )
        
        return result
    
    async def _send_streaming_message(
        self,
        session: ConversationSession,
        message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """发送流式消息"""
        async for chunk in self.client.send_message(
            message=message,
            context=session.context,
            stream=True
        ):
            yield chunk
        
        self.stats["total_messages"] += 1
    
    async def _cleanup_expired_sessions(self):
        """清理过期会话"""
        while True:
            try:
                current_time = time.time()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    if (current_time - session.last_activity) > self.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.close_session(session_id)
                    del self.sessions[session_id]
                    self.logger.info(f"已清理过期会话: {session_id}")
                
                # 每5分钟检查一次
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"清理过期会话时出错: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_oldest_sessions(self):
        """清理最旧的会话"""
        if len(self.sessions) < self.max_sessions:
            return
        
        # 按最后活动时间排序
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1].last_activity
        )
        
        # 删除最旧的会话
        sessions_to_remove = len(self.sessions) - self.max_sessions + 10
        for i in range(sessions_to_remove):
            session_id, session = sorted_sessions[i]
            await self.close_session(session_id)
            del self.sessions[session_id]
            self.logger.info(f"已清理旧会话: {session_id}")


# 全局对话管理器实例
_manager: Optional[ConversationManager] = None


async def get_conversation_manager() -> ConversationManager:
    """获取全局对话管理器实例"""
    global _manager
    if _manager is None:
        _manager = ConversationManager()
        await _manager.initialize()
    return _manager

