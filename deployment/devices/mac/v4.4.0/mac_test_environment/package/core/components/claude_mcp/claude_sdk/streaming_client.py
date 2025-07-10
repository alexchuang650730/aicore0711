"""
PowerAutomation 4.0 Streaming Claude Client
流式Claude客户端，支持实时流式响应和WebSocket通信
"""

import asyncio
import logging
import json
import aiohttp
import websockets
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from dataclasses import dataclass
import time
import uuid

from .claude_client import ClaudeClient, ConversationContext, Message
from core.config import get_config


@dataclass
class StreamingSession:
    """流式会话"""
    session_id: str
    websocket: Optional[websockets.WebSocketServerProtocol]
    conversation_context: ConversationContext
    is_active: bool = True
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class StreamingClaudeClient:
    """流式Claude客户端"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.base_client = ClaudeClient()
        
        # WebSocket服务器
        self.websocket_server = None
        self.websocket_port = 8765
        
        # 活跃会话管理
        self.active_sessions: Dict[str, StreamingSession] = {}
        
        # 事件回调
        self.on_message_received: Optional[Callable] = None
        self.on_response_chunk: Optional[Callable] = None
        self.on_response_complete: Optional[Callable] = None
    
    async def initialize(self):
        """初始化流式客户端"""
        await self.base_client.initialize()
        await self.start_websocket_server()
        self.logger.info("流式Claude客户端初始化完成")
    
    async def start_websocket_server(self):
        """启动WebSocket服务器"""
        try:
            self.websocket_server = await websockets.serve(
                self.handle_websocket_connection,
                "0.0.0.0",
                self.websocket_port
            )
            self.logger.info(f"WebSocket服务器启动在端口 {self.websocket_port}")
        except Exception as e:
            self.logger.error(f"启动WebSocket服务器失败: {e}")
            raise
    
    async def handle_websocket_connection(self, websocket, path):
        """处理WebSocket连接"""
        session_id = str(uuid.uuid4())
        self.logger.info(f"新的WebSocket连接: {session_id}")
        
        # 创建会话
        conversation_context = ConversationContext(
            conversation_id=session_id,
            messages=[],
            system_prompt="你是一个专业的AI编程助手。"
        )
        
        session = StreamingSession(
            session_id=session_id,
            websocket=websocket,
            conversation_context=conversation_context
        )
        
        self.active_sessions[session_id] = session
        
        try:
            # 发送欢迎消息
            await self.send_to_client(session_id, {
                "type": "welcome",
                "session_id": session_id,
                "message": "连接成功，可以开始对话了！"
            })
            
            # 处理消息
            async for message in websocket:
                await self.handle_client_message(session_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"WebSocket连接关闭: {session_id}")
        except Exception as e:
            self.logger.error(f"WebSocket连接错误: {e}")
        finally:
            # 清理会话
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
    
    async def handle_client_message(self, session_id: str, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "chat":
                await self.handle_chat_message(session_id, data)
            elif message_type == "code_context":
                await self.handle_code_context(session_id, data)
            elif message_type == "system_prompt":
                await self.handle_system_prompt(session_id, data)
            else:
                await self.send_error(session_id, f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error(session_id, "无效的JSON格式")
        except Exception as e:
            self.logger.error(f"处理客户端消息失败: {e}")
            await self.send_error(session_id, f"处理消息失败: {str(e)}")
    
    async def handle_chat_message(self, session_id: str, data: Dict[str, Any]):
        """处理聊天消息"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        user_message = data.get("message", "")
        
        if not user_message.strip():
            await self.send_error(session_id, "消息不能为空")
            return
        
        # 添加用户消息到上下文
        session.conversation_context.messages.append(
            Message("user", user_message)
        )
        
        # 发送确认
        await self.send_to_client(session_id, {
            "type": "message_received",
            "message": user_message
        })
        
        # 调用回调
        if self.on_message_received:
            await self.on_message_received(session_id, user_message)
        
        # 开始流式响应
        await self.stream_ai_response(session_id, user_message)
    
    async def stream_ai_response(self, session_id: str, user_message: str):
        """流式AI响应"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        try:
            # 发送响应开始信号
            await self.send_to_client(session_id, {
                "type": "response_start"
            })
            
            # 流式获取AI响应
            response_chunks = []
            async for chunk in self.base_client.stream_message(
                message=user_message,
                conversation_context=session.conversation_context
            ):
                response_chunks.append(chunk)
                
                # 发送响应块
                await self.send_to_client(session_id, {
                    "type": "response_chunk",
                    "chunk": chunk
                })
                
                # 调用回调
                if self.on_response_chunk:
                    await self.on_response_chunk(session_id, chunk)
            
            # 组合完整响应
            full_response = "".join(response_chunks)
            
            # 添加AI响应到上下文
            session.conversation_context.messages.append(
                Message("assistant", full_response)
            )
            
            # 发送响应完成信号
            await self.send_to_client(session_id, {
                "type": "response_complete",
                "full_response": full_response
            })
            
            # 调用回调
            if self.on_response_complete:
                await self.on_response_complete(session_id, full_response)
                
        except Exception as e:
            self.logger.error(f"流式响应失败: {e}")
            await self.send_error(session_id, f"AI响应失败: {str(e)}")
    
    async def handle_code_context(self, session_id: str, data: Dict[str, Any]):
        """处理代码上下文"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        code_context = data.get("context", {})
        
        # 更新系统提示以包含代码上下文
        if code_context:
            context_prompt = f"""
当前代码上下文：
- 编程语言: {code_context.get('language', '未知')}
- 文件名: {code_context.get('filename', '未知')}
- 代码内容: {code_context.get('code', '无')}

请基于这个上下文提供帮助。
"""
            session.conversation_context.system_prompt += context_prompt
        
        await self.send_to_client(session_id, {
            "type": "context_updated",
            "message": "代码上下文已更新"
        })
    
    async def handle_system_prompt(self, session_id: str, data: Dict[str, Any]):
        """处理系统提示更新"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        new_prompt = data.get("prompt", "")
        
        if new_prompt:
            session.conversation_context.system_prompt = new_prompt
            
            await self.send_to_client(session_id, {
                "type": "system_prompt_updated",
                "message": "系统提示已更新"
            })
    
    async def send_to_client(self, session_id: str, data: Dict[str, Any]):
        """发送数据到客户端"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        if session.websocket and session.is_active:
            try:
                await session.websocket.send(json.dumps(data))
            except websockets.exceptions.ConnectionClosed:
                session.is_active = False
                self.logger.info(f"客户端连接已关闭: {session_id}")
            except Exception as e:
                self.logger.error(f"发送消息到客户端失败: {e}")
    
    async def send_error(self, session_id: str, error_message: str):
        """发送错误消息"""
        await self.send_to_client(session_id, {
            "type": "error",
            "message": error_message
        })
    
    async def broadcast_message(self, data: Dict[str, Any]):
        """广播消息给所有活跃会话"""
        for session_id in list(self.active_sessions.keys()):
            await self.send_to_client(session_id, data)
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "is_active": session.is_active,
            "created_at": session.created_at,
            "message_count": len(session.conversation_context.messages),
            "system_prompt": session.conversation_context.system_prompt
        }
    
    async def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_active = False
            
            if session.websocket:
                await session.websocket.close()
            
            del self.active_sessions[session_id]
            self.logger.info(f"会话已关闭: {session_id}")
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """获取所有活跃会话"""
        sessions = []
        for session_id, session in self.active_sessions.items():
            if session.is_active:
                sessions.append({
                    "session_id": session_id,
                    "created_at": session.created_at,
                    "message_count": len(session.conversation_context.messages)
                })
        return sessions
    
    async def cleanup_inactive_sessions(self):
        """清理非活跃会话"""
        current_time = time.time()
        inactive_sessions = []
        
        for session_id, session in self.active_sessions.items():
            # 如果会话超过1小时没有活动，标记为非活跃
            if current_time - session.created_at > 3600:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            await self.close_session(session_id)
    
    async def shutdown(self):
        """关闭流式客户端"""
        # 关闭所有会话
        for session_id in list(self.active_sessions.keys()):
            await self.close_session(session_id)
        
        # 关闭WebSocket服务器
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        self.logger.info("流式Claude客户端已关闭")


# 全局实例
_streaming_client = None

def get_streaming_client() -> StreamingClaudeClient:
    """获取流式客户端实例"""
    global _streaming_client
    if _streaming_client is None:
        _streaming_client = StreamingClaudeClient()
    return _streaming_client

