#!/usr/bin/env python3
"""
任务双向通信演示脚本
PowerAutomation v4.6.9.5 - ClaudeEditor 和 Claude Code 双向通信演示

演示功能：
- 启动任务同步服务器
- 模拟 Claude Code 客户端
- 模拟 ClaudeEditor 客户端
- 展示完整的任务协作流程
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.components.task_management.task_sync_server import TaskSyncServer
from core.components.task_management.claude_code_client import ClaudeCodeTaskClient


class MockClaudeEditorClient:
    """模拟 ClaudeEditor 客户端"""
    
    def __init__(self, server_url: str = "ws://localhost:5002/ws"):
        self.server_url = server_url
        self.websocket = None
        self.client_id = None
        self.is_connected = False
        
    async def connect(self):
        """连接到服务器"""
        import websockets
        
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # 注册为 ClaudeEditor 客户端
            register_message = {
                "type": "register",
                "client": "claudeditor",
                "capabilities": [
                    "task_management",
                    "code_editing", 
                    "ui_interaction",
                    "file_operations"
                ]
            }
            
            await self.websocket.send(json.dumps(register_message))
            
            # 等待欢迎消息
            welcome_message = await self.websocket.recv()
            welcome_data = json.loads(welcome_message)
            
            if welcome_data.get("type") == "welcome":
                self.client_id = welcome_data.get("client_id")
                self.is_connected = True
                print(f"✅ ClaudeEditor 客户端已连接 (ID: {self.client_id})")
                return True
            
        except Exception as e:
            print(f"❌ ClaudeEditor 客户端连接失败: {e}")
            return False
    
    async def listen_for_messages(self):
        """监听消息"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except Exception as e:
            print(f"❌ ClaudeEditor 客户端监听失败: {e}")
    
    async def handle_message(self, data: dict):
        """处理消息"""
        message_type = data.get("type")
        message_data = data.get("data", {})
        
        if message_type == "task_created":
            print(f"📋 ClaudeEditor 收到新任务: {message_data.get('title')}")
        
        elif message_type == "task_updated":
            print(f"📝 ClaudeEditor 收到任务更新: {message_data.get('title')} -> {message_data.get('status')}")
        
        elif message_type == "task_message":
            print(f"💬 ClaudeEditor 收到任务消息: {message_data.get('message')}")
        
        elif message_type == "open_file_request":
            # 模拟处理文件打开请求
            await self.handle_file_request(message_data)
        
        elif message_type == "edit_code_request":
            # 模拟处理代码编辑请求
            await self.handle_edit_request(message_data)
    
    async def handle_file_request(self, request_data: dict):
        """处理文件请求"""
        request_id = request_data.get("request_id")
        file_path = request_data.get("file_path")
        
        print(f"📂 ClaudeEditor 处理文件打开请求: {file_path}")
        
        # 模拟处理延迟
        await asyncio.sleep(1)
        
        # 发送响应
        response = {
            "type": "request_response",
            "data": {
                "request_id": request_id,
                "response": "success",
                "data": {
                    "message": f"文件 {file_path} 已在 ClaudeEditor 中打开",
                    "editor_status": "file_opened"
                },
                "client": "claudeditor",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.websocket.send(json.dumps(response))
        print(f"✅ ClaudeEditor 已响应文件请求: {file_path}")
    
    async def handle_edit_request(self, request_data: dict):
        """处理编辑请求"""
        request_id = request_data.get("request_id")
        file_path = request_data.get("file_path")
        
        print(f"✏️ ClaudeEditor 处理代码编辑请求: {file_path}")
        
        # 模拟处理延迟
        await asyncio.sleep(2)
        
        # 发送响应
        response = {
            "type": "request_response",
            "data": {
                "request_id": request_id,
                "response": "success",
                "data": {
                    "message": f"代码编辑已应用到 {file_path}",
                    "changes_applied": True,
                    "editor_status": "code_updated"
                },
                "client": "claudeditor",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.websocket.send(json.dumps(response))
        print(f"✅ ClaudeEditor 已响应编辑请求: {file_path}")
    
    async def create_task(self, title: str, description: str = ""):
        """创建任务"""
        task_data = {
            "id": f"ce_{int(time.time())}",
            "title": title,
            "description": description,
            "priority": "medium",
            "status": "created",
            "source": "claudeditor",
            "tags": ["ClaudeEditor"],
            "created_at": datetime.now().isoformat()
        }
        
        message = {
            "type": "task_created",
            "data": task_data
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"📋 ClaudeEditor 创建任务: {title}")
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False


async def run_demo():
    """运行演示"""
    print("🚀 PowerAutomation v4.6.9.5 - 任务双向通信演示")
    print("=" * 60)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 1. 启动任务同步服务器
    print("\n🔧 步骤 1: 启动任务同步服务器")
    server = TaskSyncServer(host="localhost", port=5002)
    server_task = asyncio.create_task(server.start_server())
    
    # 等待服务器启动
    await asyncio.sleep(2)
    print("✅ 任务同步服务器已启动")
    
    try:
        # 2. 连接 Claude Code 客户端
        print("\n🔧 步骤 2: 连接 Claude Code 客户端")
        claude_code_client = ClaudeCodeTaskClient()
        
        if await claude_code_client.connect():
            print("✅ Claude Code 客户端已连接")
            
            # 启动 Claude Code 消息监听
            claude_code_task = asyncio.create_task(claude_code_client.listen_for_messages())
            
            # 3. 连接 ClaudeEditor 客户端
            print("\n🔧 步骤 3: 连接 ClaudeEditor 客户端")
            claudeditor_client = MockClaudeEditorClient()
            
            if await claudeditor_client.connect():
                print("✅ ClaudeEditor 客户端已连接")
                
                # 启动 ClaudeEditor 消息监听
                claudeditor_task = asyncio.create_task(claudeditor_client.listen_for_messages())
                
                # 4. 演示任务协作流程
                print("\n🎯 步骤 4: 演示任务协作流程")
                await demo_task_workflow(claude_code_client, claudeditor_client)
                
                # 5. 演示文件操作请求
                print("\n📂 步骤 5: 演示文件操作请求")
                await demo_file_operations(claude_code_client)
                
                # 6. 显示统计信息
                print("\n📊 步骤 6: 显示统计信息")
                await show_statistics()
                
                print("\n✅ 演示完成！")
                print("🔍 您可以访问 http://localhost:5002/api/status 查看详细状态")
                
                # 等待一段时间让用户观察
                print("\n⏳ 演示将在 10 秒后结束...")
                await asyncio.sleep(10)
                
                # 清理
                claudeditor_task.cancel()
                await claudeditor_client.disconnect()
            
            claude_code_task.cancel()
            await claude_code_client.disconnect()
        
    except KeyboardInterrupt:
        print("\n🛑 收到中断信号，正在关闭...")
    finally:
        server_task.cancel()
        print("👋 演示结束")


async def demo_task_workflow(claude_code_client, claudeditor_client):
    """演示任务协作流程"""
    print("\n📋 任务协作流程演示:")
    
    # Claude Code 创建任务
    print("  1. Claude Code 创建新任务...")
    task_id = await claude_code_client.create_task(
        "实现用户登录功能",
        "需要创建用户登录页面和后端验证逻辑",
        priority="high",
        tags=["前端", "后端", "安全"]
    )
    
    await asyncio.sleep(1)
    
    # ClaudeEditor 创建任务
    print("  2. ClaudeEditor 创建新任务...")
    await claudeditor_client.create_task(
        "优化页面加载速度",
        "分析并优化前端资源加载性能"
    )
    
    await asyncio.sleep(1)
    
    # Claude Code 更新任务状态
    print("  3. Claude Code 更新任务状态...")
    await claude_code_client.update_task_status(
        task_id, 
        "in_progress", 
        "开始实现登录功能，已创建基础文件结构"
    )
    
    await asyncio.sleep(1)
    
    # Claude Code 发送任务消息
    print("  4. Claude Code 发送任务消息...")
    await claude_code_client.send_task_message(
        task_id,
        "登录页面 UI 设计已完成，正在实现后端 API"
    )
    
    await asyncio.sleep(1)
    
    # Claude Code 完成任务
    print("  5. Claude Code 完成任务...")
    await claude_code_client.update_task_status(
        task_id,
        "completed",
        "用户登录功能已完成，包括前端页面和后端验证"
    )
    
    print("✅ 任务协作流程演示完成")


async def demo_file_operations(claude_code_client):
    """演示文件操作请求"""
    print("\n📂 文件操作请求演示:")
    
    # 模拟 Claude Code 发送文件操作请求
    print("  1. Claude Code 请求打开文件...")
    
    # 这里我们直接调用处理器来模拟请求
    file_request = {
        "request_id": "req_001",
        "action": "open_file",
        "file_path": "src/login.js",
        "task_id": "task_001"
    }
    
    # 发送请求到服务器（这会转发给 ClaudeEditor）
    await claude_code_client.send_message({
        "type": "claude_code_request",
        "data": file_request
    })
    
    await asyncio.sleep(2)
    
    print("  2. Claude Code 请求编辑代码...")
    
    edit_request = {
        "request_id": "req_002", 
        "action": "edit_code",
        "file_path": "src/login.js",
        "changes": {
            "content": "// 更新的登录逻辑\nfunction login(username, password) {\n  // 实现登录验证\n}"
        },
        "task_id": "task_001"
    }
    
    await claude_code_client.send_message({
        "type": "claude_code_request",
        "data": edit_request
    })
    
    await asyncio.sleep(2)
    
    print("✅ 文件操作请求演示完成")


async def show_statistics():
    """显示统计信息"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:5002/api/status") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print("\n📊 服务器统计信息:")
                    print(f"  • 服务状态: {data['status']}")
                    print(f"  • 连接的客户端: {len(data['connected_clients'])}")
                    print(f"  • 总任务数: {data['tasks_summary']['total']}")
                    print(f"  • 消息统计: 发送 {data['stats']['messages_sent']}, 接收 {data['stats']['messages_received']}")
                    
                    print("\n🔗 连接的客户端:")
                    for client_id, client_info in data['connected_clients'].items():
                        print(f"  • {client_info['type']}: {client_id[:8]}...")
                    
                    print("\n📋 任务状态分布:")
                    for status, count in data['tasks_summary']['by_status'].items():
                        print(f"  • {status}: {count}")
                
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n👋 演示已中断")
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        sys.exit(1)

