#!/usr/bin/env python3
"""
ClaudEditor 简化版UI服务器
用于Stagewise测试的简化版本，避免复杂依赖问题
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudEditorSimpleUI:
    """ClaudEditor 简化版UI服务器"""
    
    def __init__(self):
        self.app = FastAPI(title="ClaudEditor v4.1 Simple UI", description="AI协作开发神器")
        self.setup_cors()
        self.setup_static_files()
        
        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []
        
        # 模拟数据
        self.mock_tools = [
            {"name": "code_analyzer", "description": "代码分析工具", "status": "active", "category": "development"},
            {"name": "web_scraper", "description": "网页抓取工具", "status": "active", "category": "web_automation"},
            {"name": "data_processor", "description": "数据处理工具", "status": "inactive", "category": "data_science"}
        ]
        
        self.mock_memories = [
            {"id": "1", "content": "JavaScript函数定义", "type": "short_term", "timestamp": datetime.now().isoformat()},
            {"id": "2", "content": "Python数据处理技巧", "type": "medium_term", "timestamp": datetime.now().isoformat()},
            {"id": "3", "content": "React组件设计模式", "type": "long_term", "timestamp": datetime.now().isoformat()}
        ]
        
        # 设置路由
        self.setup_routes()
        
    def setup_cors(self):
        """设置CORS"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_static_files(self):
        """设置静态文件服务"""
        # 确保静态文件目录存在
        if os.path.exists("claudeditor/static"):
            self.app.mount("/static", StaticFiles(directory="claudeditor/static"), name="static")
        if os.path.exists("claudeditor/templates"):
            self.templates = Jinja2Templates(directory="claudeditor/templates")
        else:
            self.templates = None
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """主页面"""
            if self.templates:
                return self.templates.TemplateResponse("index.html", {"request": request})
            else:
                return HTMLResponse(self.get_simple_html())
        
        @self.app.get("/api/status")
        async def get_status():
            """获取系统状态"""
            return {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "version": "4.1.0",
                "components": {
                    "ui_server": "active",
                    "mcp_discovery": "active",
                    "memory_engine": "active",
                    "ai_coordinator": "active"
                }
            }
        
        @self.app.get("/api/mcp/tools")
        async def get_mcp_tools():
            """获取MCP工具列表"""
            return {"tools": self.mock_tools, "count": len(self.mock_tools)}
        
        @self.app.post("/api/memory/store")
        async def store_memory(data: dict):
            """存储记忆"""
            memory_id = f"mem_{len(self.mock_memories) + 1}"
            new_memory = {
                "id": memory_id,
                "content": data.get("content", ""),
                "type": data.get("type", "short_term"),
                "timestamp": datetime.now().isoformat(),
                "metadata": data.get("metadata", {})
            }
            self.mock_memories.append(new_memory)
            return {"success": True, "memory_id": memory_id}
        
        @self.app.get("/api/memory/search")
        async def search_memory(query: str = "", limit: int = 10):
            """搜索记忆"""
            if query:
                filtered_memories = [
                    mem for mem in self.mock_memories 
                    if query.lower() in mem["content"].lower()
                ]
            else:
                filtered_memories = self.mock_memories
            
            return {
                "memories": filtered_memories[:limit], 
                "count": len(filtered_memories)
            }
        
        @self.app.post("/api/ai/chat")
        async def ai_chat(data: dict):
            """AI对话"""
            message = data.get("message", "")
            model = data.get("model", "claude")
            
            # 模拟AI响应
            response = f"[{model}] 我收到了您的消息：'{message}'。这是一个模拟响应，用于测试ClaudEditor的AI聊天功能。"
            
            return {"response": response, "model": model, "timestamp": datetime.now().isoformat()}
        
        @self.app.post("/api/stagewise/start")
        async def start_stagewise_session(data: dict):
            """启动Stagewise会话"""
            session_id = f"stagewise_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return {
                "session_id": session_id,
                "status": "started",
                "user_id": data.get("user_id", "default"),
                "project_id": data.get("project_id", "default")
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket连接"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                # 发送欢迎消息
                await websocket.send_text(json.dumps({
                    "type": "welcome",
                    "message": "WebSocket连接已建立",
                    "timestamp": datetime.now().isoformat()
                }))
                
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # 处理不同类型的消息
                    response = await self.handle_websocket_message(message)
                    await websocket.send_text(json.dumps(response))
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                logger.info("WebSocket连接断开")
    
    async def handle_websocket_message(self, message: dict) -> dict:
        """处理WebSocket消息"""
        message_type = message.get("type")
        
        if message_type == "ping":
            return {"type": "pong", "timestamp": datetime.now().isoformat()}
        
        elif message_type == "mcp_tool_execute":
            tool_name = message.get("tool_name")
            return {
                "type": "mcp_tool_result", 
                "tool_name": tool_name,
                "result": f"工具 {tool_name} 执行成功（模拟）",
                "timestamp": datetime.now().isoformat()
            }
        
        elif message_type == "memory_query":
            query = message.get("query")
            filtered_memories = [
                mem for mem in self.mock_memories 
                if query.lower() in mem["content"].lower()
            ] if query else self.mock_memories
            return {"type": "memory_results", "results": filtered_memories}
        
        elif message_type == "ai_stream_chat":
            message_content = message.get("message")
            model = message.get("model", "claude")
            response = f"[{model}] 流式响应：{message_content}"
            return {"type": "ai_response", "response": response}
        
        else:
            return {"type": "error", "message": f"未知消息类型: {message_type}"}
    
    def get_simple_html(self) -> str:
        """获取简单的HTML页面"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClaudEditor v4.1 - AI协作开发神器</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
        .header { background: #2d2d30; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .logo { color: #007acc; font-size: 24px; font-weight: bold; }
        .subtitle { color: #888; margin-top: 5px; }
        .status { background: #2d2d30; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .status-item { display: inline-block; margin-right: 20px; }
        .status-label { color: #888; }
        .status-value { color: #4caf50; font-weight: bold; }
        .section { background: #2d2d30; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section h2 { color: #cccccc; margin-top: 0; }
        .btn { background: #007acc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #005a9e; }
        .test-area { background: #252526; padding: 15px; border-radius: 4px; margin-top: 10px; }
        .test-result { margin-top: 10px; padding: 10px; border-radius: 4px; }
        .success { background: #1e5f1e; color: #4caf50; }
        .error { background: #5f1e1e; color: #f44336; }
        #chat-messages { height: 200px; overflow-y: auto; background: #1e1e1e; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .message { margin-bottom: 10px; }
        .user { color: #ff6b35; }
        .assistant { color: #007acc; }
        input, textarea { background: #3c3c3c; color: #cccccc; border: 1px solid #5a5a5a; padding: 8px; border-radius: 4px; width: 100%; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🧠 ClaudEditor v4.1</div>
        <div class="subtitle">AI协作开发神器 - Stagewise测试版</div>
    </div>
    
    <div class="status">
        <div class="status-item">
            <span class="status-label">系统状态:</span>
            <span class="status-value" id="system-status">运行中</span>
        </div>
        <div class="status-item">
            <span class="status-label">WebSocket:</span>
            <span class="status-value" id="ws-status">连接中...</span>
        </div>
        <div class="status-item">
            <span class="status-label">测试时间:</span>
            <span class="status-value" id="test-time">--</span>
        </div>
    </div>
    
    <div class="section">
        <h2>🔧 MCP工具管理</h2>
        <button class="btn" onclick="loadTools()">刷新工具列表</button>
        <div class="test-area">
            <div id="tools-list">点击"刷新工具列表"加载工具...</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🧠 记忆系统</h2>
        <input type="text" id="memory-query" placeholder="搜索记忆...">
        <button class="btn" onclick="searchMemory()">搜索</button>
        <button class="btn" onclick="storeTestMemory()">存储测试记忆</button>
        <div class="test-area">
            <div id="memory-results">输入搜索词或点击"存储测试记忆"...</div>
        </div>
    </div>
    
    <div class="section">
        <h2>🤖 AI助手</h2>
        <input type="text" id="ai-message" placeholder="输入消息...">
        <select id="ai-model">
            <option value="claude">Claude 3.5 Sonnet</option>
            <option value="gemini">Gemini 1.5 Flash</option>
        </select>
        <button class="btn" onclick="sendAIMessage()">发送</button>
        <div id="chat-messages"></div>
    </div>
    
    <div class="section">
        <h2>🎯 Stagewise可视化编程</h2>
        <button class="btn" onclick="startStagewise()">启动会话</button>
        <div class="test-area">
            <div id="stagewise-status">点击"启动会话"开始...</div>
        </div>
    </div>
    
    <script>
        let ws = null;
        
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('test-time').textContent = new Date().toLocaleString();
            initWebSocket();
            loadSystemStatus();
        });
        
        // WebSocket连接
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                document.getElementById('ws-status').textContent = '已连接';
                document.getElementById('ws-status').style.color = '#4caf50';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                console.log('WebSocket消息:', data);
            };
            
            ws.onclose = function() {
                document.getElementById('ws-status').textContent = '连接断开';
                document.getElementById('ws-status').style.color = '#f44336';
            };
        }
        
        // 加载系统状态
        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('system-status').textContent = data.status === 'running' ? '正常' : '异常';
            } catch (error) {
                document.getElementById('system-status').textContent = '错误';
                document.getElementById('system-status').style.color = '#f44336';
            }
        }
        
        // 加载工具列表
        async function loadTools() {
            try {
                const response = await fetch('/api/mcp/tools');
                const data = await response.json();
                
                let html = `<div class="test-result success">发现 ${data.count} 个工具:</div>`;
                data.tools.forEach(tool => {
                    html += `<div style="margin: 5px 0; padding: 5px; background: #3c3c3c; border-radius: 4px;">
                        <strong>${tool.name}</strong> - ${tool.description} 
                        <span style="color: ${tool.status === 'active' ? '#4caf50' : '#f44336'}">[${tool.status}]</span>
                    </div>`;
                });
                
                document.getElementById('tools-list').innerHTML = html;
            } catch (error) {
                document.getElementById('tools-list').innerHTML = '<div class="test-result error">加载工具失败: ' + error.message + '</div>';
            }
        }
        
        // 搜索记忆
        async function searchMemory() {
            const query = document.getElementById('memory-query').value;
            try {
                const response = await fetch(`/api/memory/search?query=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                let html = `<div class="test-result success">找到 ${data.count} 条记忆:</div>`;
                data.memories.forEach(memory => {
                    html += `<div style="margin: 5px 0; padding: 5px; background: #3c3c3c; border-radius: 4px;">
                        <strong>[${memory.type}]</strong> ${memory.content}
                        <div style="font-size: 12px; color: #888;">${memory.timestamp}</div>
                    </div>`;
                });
                
                document.getElementById('memory-results').innerHTML = html;
            } catch (error) {
                document.getElementById('memory-results').innerHTML = '<div class="test-result error">搜索失败: ' + error.message + '</div>';
            }
        }
        
        // 存储测试记忆
        async function storeTestMemory() {
            const testMemory = {
                content: `测试记忆 - ${new Date().toLocaleString()}`,
                type: 'short_term',
                metadata: { test: true }
            };
            
            try {
                const response = await fetch('/api/memory/store', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(testMemory)
                });
                const data = await response.json();
                
                document.getElementById('memory-results').innerHTML = 
                    `<div class="test-result success">记忆存储成功，ID: ${data.memory_id}</div>`;
            } catch (error) {
                document.getElementById('memory-results').innerHTML = 
                    '<div class="test-result error">存储失败: ' + error.message + '</div>';
            }
        }
        
        // 发送AI消息
        async function sendAIMessage() {
            const message = document.getElementById('ai-message').value;
            const model = document.getElementById('ai-model').value;
            
            if (!message.trim()) return;
            
            // 添加用户消息
            addChatMessage('user', message);
            document.getElementById('ai-message').value = '';
            
            try {
                const response = await fetch('/api/ai/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, model })
                });
                const data = await response.json();
                
                // 添加AI回复
                addChatMessage('assistant', data.response);
            } catch (error) {
                addChatMessage('assistant', '错误: ' + error.message);
            }
        }
        
        // 添加聊天消息
        function addChatMessage(role, content) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            messageDiv.innerHTML = `<strong>${role === 'user' ? '用户' : 'AI'}:</strong> ${content}`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 启动Stagewise会话
        async function startStagewise() {
            try {
                const response = await fetch('/api/stagewise/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: 'test_user', project_id: 'test_project' })
                });
                const data = await response.json();
                
                document.getElementById('stagewise-status').innerHTML = 
                    `<div class="test-result success">会话启动成功<br>会话ID: ${data.session_id}<br>状态: ${data.status}</div>`;
            } catch (error) {
                document.getElementById('stagewise-status').innerHTML = 
                    '<div class="test-result error">启动失败: ' + error.message + '</div>';
            }
        }
        
        // 键盘事件
        document.getElementById('ai-message').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendAIMessage();
            }
        });
        
        document.getElementById('memory-query').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchMemory();
            }
        });
    </script>
</body>
</html>
        """
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """启动服务器"""
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"ClaudEditor 简化版UI启动在 http://{host}:{port}")
        await server.serve()


async def main():
    """主函数"""
    claudeditor_ui = ClaudEditorSimpleUI()
    await claudeditor_ui.start_server()


if __name__ == "__main__":
    asyncio.run(main())

