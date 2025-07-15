#!/usr/bin/env python3
"""
任务同步服务器
PowerAutomation v4.6.9.5 - ClaudeEditor 和 Claude Code 双向通信

实现功能：
- WebSocket 双向通信
- 任务创建、更新、分配同步
- 文件操作请求转发
- 实时状态同步
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class ClientType(Enum):
    """客户端类型"""
    CLAUDE_EDITOR = "claudeditor"
    CLAUDE_CODE = "claude_code"
    UNKNOWN = "unknown"


class MessageType(Enum):
    """消息类型"""
    REGISTER = "register"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_MESSAGE = "task_message"
    CLAUDE_CODE_REQUEST = "claude_code_request"
    REQUEST_RESPONSE = "request_response"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"


@dataclass
class Task:
    """任务数据结构"""
    id: str
    title: str
    description: str = ""
    priority: str = "medium"  # high, medium, low
    status: str = "created"  # created, assigned, in_progress, completed, failed, cancelled
    assigned_to: Optional[str] = None
    estimated_duration: str = "1小时"
    tags: List[str] = None
    subtasks: List[Dict[str, Any]] = None
    created_at: str = None
    updated_at: str = None
    deadline: Optional[str] = None
    progress: int = 0
    source: str = "unknown"
    messages: List[Dict[str, Any]] = None
    last_message: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.subtasks is None:
            self.subtasks = []
        if self.messages is None:
            self.messages = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class Client:
    """客户端信息"""
    id: str
    type: ClientType
    websocket: WebSocket
    capabilities: List[str]
    connected_at: str
    last_heartbeat: str
    active_tasks: Set[str]
    
    def __post_init__(self):
        if isinstance(self.active_tasks, list):
            self.active_tasks = set(self.active_tasks)


class TaskSyncServer:
    """任务同步服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 5002):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Task Sync Server", version="4.6.9.5")
        
        # 添加 CORS 中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 数据存储
        self.tasks: Dict[str, Task] = {}
        self.clients: Dict[str, Client] = {}
        self.request_handlers: Dict[str, asyncio.Future] = {}
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "start_time": datetime.now().isoformat()
        }
        
        self._setup_routes()
        
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket_connection(websocket)
        
        @self.app.get("/api/tasks/sync")
        async def sync_tasks():
            """同步任务接口"""
            return {
                "tasks": [asdict(task) for task in self.tasks.values()],
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/api/tasks")
        async def create_task(task_data: dict):
            """创建任务接口"""
            task = Task(
                id=task_data.get("id", str(uuid.uuid4())),
                title=task_data["title"],
                description=task_data.get("description", ""),
                priority=task_data.get("priority", "medium"),
                status="created",
                source=task_data.get("source", "api")
            )
            
            self.tasks[task.id] = task
            self.stats["total_tasks"] += 1
            
            # 广播任务创建事件
            await self.broadcast_message({
                "type": MessageType.TASK_CREATED.value,
                "data": asdict(task)
            })
            
            return {"success": True, "task_id": task.id}
        
        @self.app.put("/api/tasks/{task_id}/status")
        async def update_task_status(task_id: str, update_data: dict):
            """更新任务状态接口"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[task_id]
            task.status = update_data["status"]
            task.updated_at = datetime.now().isoformat()
            
            if "message" in update_data:
                message = {
                    "id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "message": update_data["message"],
                    "sender": update_data.get("updated_by", "system"),
                    "timestamp": datetime.now().isoformat(),
                    "type": "status_update"
                }
                task.messages.append(message)
                task.last_message = message
            
            # 广播任务更新事件
            await self.broadcast_message({
                "type": MessageType.TASK_UPDATED.value,
                "data": asdict(task)
            })
            
            return {"success": True}
        
        @self.app.post("/api/tasks/{task_id}/messages")
        async def send_task_message(task_id: str, message_data: dict):
            """发送任务消息接口"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[task_id]
            message = {
                "id": str(uuid.uuid4()),
                "task_id": task_id,
                "message": message_data["message"],
                "sender": message_data["sender"],
                "timestamp": datetime.now().isoformat(),
                "type": message_data.get("type", "comment")
            }
            
            task.messages.append(message)
            task.last_message = message
            task.updated_at = datetime.now().isoformat()
            
            # 广播任务消息事件
            await self.broadcast_message({
                "type": MessageType.TASK_MESSAGE.value,
                "data": message
            })
            
            return {"success": True, "message_id": message["id"]}
        
        @self.app.get("/api/status")
        async def get_status():
            """获取服务器状态"""
            return {
                "status": "running",
                "stats": self.stats,
                "connected_clients": {
                    client_id: {
                        "type": client.type.value,
                        "capabilities": client.capabilities,
                        "connected_at": client.connected_at,
                        "active_tasks": list(client.active_tasks)
                    }
                    for client_id, client in self.clients.items()
                },
                "tasks_summary": {
                    "total": len(self.tasks),
                    "by_status": self._get_tasks_by_status(),
                    "by_source": self._get_tasks_by_source()
                }
            }
    
    async def handle_websocket_connection(self, websocket: WebSocket):
        """处理 WebSocket 连接"""
        await websocket.accept()
        client_id = str(uuid.uuid4())
        
        try:
            # 等待客户端注册
            register_message = await websocket.receive_json()
            
            if register_message.get("type") != "register":
                await websocket.close(code=4000, reason="Expected register message")
                return
            
            # 创建客户端
            client_type_str = register_message.get("client", "unknown")
            client_type = ClientType.CLAUDE_EDITOR if client_type_str == "claudeditor" else \
                         ClientType.CLAUDE_CODE if client_type_str == "claude_code" else \
                         ClientType.UNKNOWN
            
            client = Client(
                id=client_id,
                type=client_type,
                websocket=websocket,
                capabilities=register_message.get("capabilities", []),
                connected_at=datetime.now().isoformat(),
                last_heartbeat=datetime.now().isoformat(),
                active_tasks=set()
            )
            
            self.clients[client_id] = client
            self.stats["active_connections"] += 1
            
            logger.info(f"✅ 客户端已连接: {client_type.value} ({client_id})")
            
            # 发送欢迎消息和当前任务
            await websocket.send_json({
                "type": "welcome",
                "client_id": client_id,
                "server_time": datetime.now().isoformat(),
                "tasks": [asdict(task) for task in self.tasks.values()]
            })
            
            # 处理消息循环
            async for message in websocket.iter_json():
                await self.handle_client_message(client, message)
                
        except WebSocketDisconnect:
            logger.info(f"🔌 客户端断开连接: {client_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket 连接错误: {e}")
        finally:
            # 清理客户端
            if client_id in self.clients:
                del self.clients[client_id]
                self.stats["active_connections"] -= 1
    
    async def handle_client_message(self, client: Client, message: dict):
        """处理客户端消息"""
        message_type = message.get("type")
        self.stats["messages_received"] += 1
        
        logger.debug(f"📨 收到消息: {client.type.value} -> {message_type}")
        
        try:
            if message_type == MessageType.HEARTBEAT.value:
                client.last_heartbeat = datetime.now().isoformat()
                await client.websocket.send_json({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == MessageType.TASK_CREATED.value:
                await self.handle_task_created(client, message["data"])
            
            elif message_type == MessageType.TASK_UPDATED.value:
                await self.handle_task_updated(client, message["data"])
            
            elif message_type == MessageType.TASK_MESSAGE.value:
                await self.handle_task_message(client, message["data"])
            
            elif message_type == MessageType.CLAUDE_CODE_REQUEST.value:
                await self.handle_claude_code_request(client, message["data"])
            
            elif message_type == MessageType.REQUEST_RESPONSE.value:
                await self.handle_request_response(client, message["data"])
            
            elif message_type == MessageType.SYNC_REQUEST.value:
                await self.handle_sync_request(client)
            
            else:
                logger.warning(f"未知消息类型: {message_type}")
        
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await client.websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def handle_task_created(self, client: Client, task_data: dict):
        """处理任务创建"""
        task = Task(**task_data)
        task.source = client.type.value
        task.updated_at = datetime.now().isoformat()
        
        self.tasks[task.id] = task
        self.stats["total_tasks"] += 1
        client.active_tasks.add(task.id)
        
        # 广播给其他客户端
        await self.broadcast_message({
            "type": MessageType.TASK_CREATED.value,
            "data": asdict(task)
        }, exclude_client=client.id)
        
        logger.info(f"📋 任务已创建: {task.title} (来源: {client.type.value})")
    
    async def handle_task_updated(self, client: Client, task_data: dict):
        """处理任务更新"""
        task_id = task_data["id"]
        
        if task_id in self.tasks:
            # 更新现有任务
            task = self.tasks[task_id]
            for key, value in task_data.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now().isoformat()
        else:
            # 创建新任务
            task = Task(**task_data)
            self.tasks[task_id] = task
            self.stats["total_tasks"] += 1
        
        client.active_tasks.add(task_id)
        
        # 广播给其他客户端
        await self.broadcast_message({
            "type": MessageType.TASK_UPDATED.value,
            "data": asdict(task)
        }, exclude_client=client.id)
        
        logger.info(f"📝 任务已更新: {task.title} (状态: {task.status})")
    
    async def handle_task_message(self, client: Client, message_data: dict):
        """处理任务消息"""
        task_id = message_data["task_id"]
        
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.messages.append(message_data)
            task.last_message = message_data
            task.updated_at = datetime.now().isoformat()
            
            # 广播给其他客户端
            await self.broadcast_message({
                "type": MessageType.TASK_MESSAGE.value,
                "data": message_data
            }, exclude_client=client.id)
            
            logger.info(f"💬 任务消息: {task.title} <- {message_data['sender']}")
    
    async def handle_claude_code_request(self, client: Client, request_data: dict):
        """处理 Claude Code 请求"""
        request_id = request_data.get("request_id", str(uuid.uuid4()))
        
        # 转发给 ClaudeEditor 客户端
        claudeditor_clients = [
            c for c in self.clients.values() 
            if c.type == ClientType.CLAUDE_EDITOR
        ]
        
        if claudeditor_clients:
            for claudeditor_client in claudeditor_clients:
                await claudeditor_client.websocket.send_json({
                    "type": request_data["action"] + "_request",
                    "data": {
                        **request_data,
                        "request_id": request_id
                    }
                })
            
            logger.info(f"🚀 Claude Code 请求已转发: {request_data['action']}")
        else:
            # 没有 ClaudeEditor 客户端，返回错误
            await client.websocket.send_json({
                "type": "request_response",
                "data": {
                    "request_id": request_id,
                    "response": "error",
                    "message": "没有可用的 ClaudeEditor 客户端"
                }
            })
    
    async def handle_request_response(self, client: Client, response_data: dict):
        """处理请求响应"""
        request_id = response_data["request_id"]
        
        # 转发给 Claude Code 客户端
        claude_code_clients = [
            c for c in self.clients.values() 
            if c.type == ClientType.CLAUDE_CODE
        ]
        
        for claude_code_client in claude_code_clients:
            await claude_code_client.websocket.send_json({
                "type": "request_response",
                "data": response_data
            })
        
        logger.info(f"📤 请求响应已转发: {request_id}")
    
    async def handle_sync_request(self, client: Client):
        """处理同步请求"""
        await client.websocket.send_json({
            "type": MessageType.SYNC_RESPONSE.value,
            "data": {
                "tasks": [asdict(task) for task in self.tasks.values()],
                "timestamp": datetime.now().isoformat()
            }
        })
        
        logger.info(f"🔄 同步响应已发送: {len(self.tasks)} 个任务")
    
    async def broadcast_message(self, message: dict, exclude_client: str = None):
        """广播消息给所有客户端"""
        disconnected_clients = []
        
        for client_id, client in self.clients.items():
            if client_id == exclude_client:
                continue
            
            try:
                await client.websocket.send_json(message)
                self.stats["messages_sent"] += 1
            except Exception as e:
                logger.error(f"发送消息失败: {client_id} -> {e}")
                disconnected_clients.append(client_id)
        
        # 清理断开的客户端
        for client_id in disconnected_clients:
            if client_id in self.clients:
                del self.clients[client_id]
                self.stats["active_connections"] -= 1
    
    def _get_tasks_by_status(self) -> Dict[str, int]:
        """按状态统计任务"""
        status_count = {}
        for task in self.tasks.values():
            status_count[task.status] = status_count.get(task.status, 0) + 1
        return status_count
    
    def _get_tasks_by_source(self) -> Dict[str, int]:
        """按来源统计任务"""
        source_count = {}
        for task in self.tasks.values():
            source_count[task.source] = source_count.get(task.source, 0) + 1
        return source_count
    
    async def start_server(self):
        """启动服务器"""
        logger.info(f"🚀 启动任务同步服务器: {self.host}:{self.port}")
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()


# 示例使用
async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动服务器
    server = TaskSyncServer(host="0.0.0.0", port=5002)
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main())

