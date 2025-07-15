#!/usr/bin/env python3
"""
Claude Code 客户端适配器
PowerAutomation v4.6.9.5 - Claude Code 端任务同步客户端

实现功能：
- 连接到任务同步服务器
- 发送任务创建、更新事件
- 处理来自 ClaudeEditor 的请求
- 文件操作和代码编辑集成
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import websockets
from websockets.client import WebSocketClientProtocol
import aiohttp
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class ClaudeCodeTaskClient:
    """Claude Code 任务客户端"""
    
    def __init__(self, server_url: str = "ws://localhost:5002/ws"):
        self.server_url = server_url
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.client_id: Optional[str] = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 3.0
        
        # 事件处理器
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # 请求处理器
        self.request_handlers = {
            "open_file": self.handle_open_file_request,
            "edit_code": self.handle_edit_code_request,
            "run_command": self.handle_run_command_request,
            "show_diff": self.handle_show_diff_request
        }
        
        # 当前工作目录和项目信息
        self.working_directory = os.getcwd()
        self.project_files: List[str] = []
        
    async def connect(self) -> bool:
        """连接到任务同步服务器"""
        try:
            logger.info(f"🔗 连接到任务同步服务器: {self.server_url}")
            
            self.websocket = await websockets.connect(self.server_url)
            
            # 注册为 Claude Code 客户端
            register_message = {
                "type": "register",
                "client": "claude_code",
                "capabilities": [
                    "task_creation",
                    "task_management", 
                    "file_operations",
                    "code_editing",
                    "command_execution",
                    "diff_generation"
                ]
            }
            
            await self.websocket.send(json.dumps(register_message))
            
            # 等待欢迎消息
            welcome_message = await self.websocket.recv()
            welcome_data = json.loads(welcome_message)
            
            if welcome_data.get("type") == "welcome":
                self.client_id = welcome_data.get("client_id")
                self.is_connected = True
                self.reconnect_attempts = 0
                
                logger.info(f"✅ 已连接到任务同步服务器 (客户端ID: {self.client_id})")
                
                # 同步现有任务
                existing_tasks = welcome_data.get("tasks", [])
                if existing_tasks:
                    logger.info(f"📋 同步了 {len(existing_tasks)} 个现有任务")
                    await self.trigger_event("tasks_synced", existing_tasks)
                
                return True
            else:
                logger.error("❌ 未收到预期的欢迎消息")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.is_connected = False
        logger.info("🔌 已断开与任务同步服务器的连接")
    
    async def listen_for_messages(self):
        """监听服务器消息"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_server_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析错误: {e}")
                except Exception as e:
                    logger.error(f"处理消息失败: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 WebSocket 连接已关闭")
            self.is_connected = False
            await self.attempt_reconnect()
        except Exception as e:
            logger.error(f"❌ 监听消息失败: {e}")
            self.is_connected = False
    
    async def handle_server_message(self, data: dict):
        """处理服务器消息"""
        message_type = data.get("type")
        message_data = data.get("data", {})
        
        logger.debug(f"📨 收到服务器消息: {message_type}")
        
        if message_type == "heartbeat":
            # 响应心跳
            await self.send_message({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })
        
        elif message_type == "task_created":
            await self.trigger_event("task_created", message_data)
        
        elif message_type == "task_updated":
            await self.trigger_event("task_updated", message_data)
        
        elif message_type == "task_message":
            await self.trigger_event("task_message", message_data)
        
        elif message_type.endswith("_request"):
            # 处理来自 ClaudeEditor 的请求
            request_type = message_type.replace("_request", "")
            await self.handle_claudeditor_request(request_type, message_data)
        
        else:
            logger.debug(f"未处理的消息类型: {message_type}")
    
    async def handle_claudeditor_request(self, request_type: str, request_data: dict):
        """处理来自 ClaudeEditor 的请求"""
        request_id = request_data.get("request_id")
        
        logger.info(f"🎯 处理 ClaudeEditor 请求: {request_type}")
        
        try:
            if request_type in self.request_handlers:
                handler = self.request_handlers[request_type]
                result = await handler(request_data)
                
                # 发送成功响应
                await self.send_request_response(request_id, "success", result)
            else:
                # 未知请求类型
                await self.send_request_response(
                    request_id, 
                    "error", 
                    {"message": f"不支持的请求类型: {request_type}"}
                )
                
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            await self.send_request_response(
                request_id,
                "error", 
                {"message": str(e)}
            )
    
    async def handle_open_file_request(self, request_data: dict) -> dict:
        """处理打开文件请求"""
        file_path = request_data.get("file_path")
        task_id = request_data.get("task_id")
        
        logger.info(f"📂 打开文件请求: {file_path}")
        
        if not file_path:
            raise ValueError("文件路径不能为空")
        
        # 检查文件是否存在
        full_path = Path(self.working_directory) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取文件内容
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(full_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        return {
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "task_id": task_id,
            "message": f"文件 {file_path} 已打开"
        }
    
    async def handle_edit_code_request(self, request_data: dict) -> dict:
        """处理代码编辑请求"""
        file_path = request_data.get("file_path")
        changes = request_data.get("changes", {})
        task_id = request_data.get("task_id")
        
        logger.info(f"✏️ 代码编辑请求: {file_path}")
        
        if not file_path:
            raise ValueError("文件路径不能为空")
        
        full_path = Path(self.working_directory) / file_path
        
        # 应用代码更改
        if "content" in changes:
            # 直接替换文件内容
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(changes["content"])
            
            return {
                "file_path": file_path,
                "changes_applied": True,
                "task_id": task_id,
                "message": f"文件 {file_path} 已更新"
            }
        
        elif "line_changes" in changes:
            # 按行更改
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_change in changes["line_changes"]:
                line_num = line_change.get("line", 0) - 1  # 转换为0索引
                new_content = line_change.get("content", "")
                
                if 0 <= line_num < len(lines):
                    lines[line_num] = new_content + "\n"
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return {
                "file_path": file_path,
                "changes_applied": True,
                "lines_modified": len(changes["line_changes"]),
                "task_id": task_id,
                "message": f"文件 {file_path} 已按行更新"
            }
        
        else:
            raise ValueError("无效的更改格式")
    
    async def handle_run_command_request(self, request_data: dict) -> dict:
        """处理命令执行请求"""
        command = request_data.get("command")
        task_id = request_data.get("task_id")
        working_dir = request_data.get("working_dir", self.working_directory)
        
        logger.info(f"⚡ 命令执行请求: {command}")
        
        if not command:
            raise ValueError("命令不能为空")
        
        # 执行命令
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "command": command,
            "return_code": process.returncode,
            "stdout": stdout.decode('utf-8', errors='ignore'),
            "stderr": stderr.decode('utf-8', errors='ignore'),
            "task_id": task_id,
            "message": f"命令执行完成 (返回码: {process.returncode})"
        }
    
    async def handle_show_diff_request(self, request_data: dict) -> dict:
        """处理显示差异请求"""
        before = request_data.get("before", "")
        after = request_data.get("after", "")
        task_id = request_data.get("task_id")
        
        logger.info(f"🔍 差异显示请求")
        
        # 生成简单的差异信息
        before_lines = before.split('\n')
        after_lines = after.split('\n')
        
        diff_info = {
            "before_lines": len(before_lines),
            "after_lines": len(after_lines),
            "lines_added": max(0, len(after_lines) - len(before_lines)),
            "lines_removed": max(0, len(before_lines) - len(after_lines)),
            "task_id": task_id,
            "message": "差异信息已生成"
        }
        
        return diff_info
    
    async def send_message(self, message: dict):
        """发送消息到服务器"""
        if not self.websocket or not self.is_connected:
            logger.warning("⚠️ WebSocket 未连接，无法发送消息")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    async def send_request_response(self, request_id: str, response: str, data: dict = None):
        """发送请求响应"""
        response_message = {
            "type": "request_response",
            "data": {
                "request_id": request_id,
                "response": response,
                "data": data or {},
                "client": "claude_code",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.send_message(response_message)
    
    async def create_task(self, title: str, description: str = "", **kwargs) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": kwargs.get("priority", "medium"),
            "status": "created",
            "source": "claude_code",
            "tags": kwargs.get("tags", ["Claude Code"]),
            "estimated_duration": kwargs.get("estimated_duration", "1小时"),
            "created_at": datetime.now().isoformat()
        }
        
        message = {
            "type": "task_created",
            "data": task_data
        }
        
        success = await self.send_message(message)
        if success:
            logger.info(f"📋 任务已创建: {title}")
            return task_id
        else:
            raise Exception("创建任务失败")
    
    async def update_task_status(self, task_id: str, status: str, message: str = None):
        """更新任务状态"""
        update_data = {
            "id": task_id,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if message:
            update_data["last_message"] = {
                "id": str(uuid.uuid4()),
                "task_id": task_id,
                "message": message,
                "sender": "claude_code",
                "timestamp": datetime.now().isoformat(),
                "type": "status_update"
            }
        
        message_obj = {
            "type": "task_updated",
            "data": update_data
        }
        
        success = await self.send_message(message_obj)
        if success:
            logger.info(f"📝 任务状态已更新: {task_id} -> {status}")
        else:
            raise Exception("更新任务状态失败")
    
    async def send_task_message(self, task_id: str, message: str, message_type: str = "comment"):
        """发送任务消息"""
        message_data = {
            "id": str(uuid.uuid4()),
            "task_id": task_id,
            "message": message,
            "sender": "claude_code",
            "timestamp": datetime.now().isoformat(),
            "type": message_type
        }
        
        message_obj = {
            "type": "task_message",
            "data": message_data
        }
        
        success = await self.send_message(message_obj)
        if success:
            logger.info(f"💬 任务消息已发送: {task_id}")
        else:
            raise Exception("发送任务消息失败")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """添加事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def trigger_event(self, event_type: str, data: Any):
        """触发事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"事件处理器错误: {e}")
    
    async def attempt_reconnect(self):
        """尝试重连"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("❌ 重连次数已达上限")
            return
        
        self.reconnect_attempts += 1
        logger.info(f"🔄 尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        await asyncio.sleep(self.reconnect_delay)
        
        if await self.connect():
            logger.info("✅ 重连成功")
            # 重新开始监听
            asyncio.create_task(self.listen_for_messages())
        else:
            await self.attempt_reconnect()
    
    async def start(self):
        """启动客户端"""
        logger.info("🚀 启动 Claude Code 任务客户端")
        
        if await self.connect():
            # 开始监听消息
            await self.listen_for_messages()
        else:
            logger.error("❌ 无法连接到任务同步服务器")


# 示例使用
async def demo_claude_code_client():
    """演示 Claude Code 客户端功能"""
    client = ClaudeCodeTaskClient()
    
    # 添加事件处理器
    def on_task_created(task_data):
        print(f"📋 收到新任务: {task_data['title']}")
    
    def on_task_updated(task_data):
        print(f"📝 任务更新: {task_data['title']} -> {task_data['status']}")
    
    client.add_event_handler("task_created", on_task_created)
    client.add_event_handler("task_updated", on_task_updated)
    
    try:
        # 连接到服务器
        if await client.connect():
            print("✅ 已连接到任务同步服务器")
            
            # 创建示例任务
            task_id = await client.create_task(
                "测试任务",
                "这是一个来自 Claude Code 的测试任务",
                priority="high",
                tags=["测试", "Claude Code"]
            )
            
            # 更新任务状态
            await asyncio.sleep(2)
            await client.update_task_status(task_id, "in_progress", "开始处理任务")
            
            # 发送任务消息
            await asyncio.sleep(2)
            await client.send_task_message(task_id, "任务进展顺利")
            
            # 监听消息
            await client.listen_for_messages()
        else:
            print("❌ 连接失败")
    
    except KeyboardInterrupt:
        print("\n🛑 收到中断信号")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(demo_claude_code_client())

