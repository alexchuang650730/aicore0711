#!/usr/bin/env python3
"""
ClaudEditor v4.1 主界面程序
使用AG-UI组件生成器创建完整的ClaudEditor界面，整合所有MCP组件

基于aicore0707现有架构，提供统一的Web界面访问所有v4.1功能：
- MCP-Zero Smart Engine (智能工具发现)
- MemoryOS (三层记忆系统)
- Trae Agent (多模型协作)
- ClaudEditor Deep Integration (深度集成)
- Stagewise (可视化编程)
- Claude SDK (AI对话)
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

# 导入AG-UI组件
from core.components.ag_ui_mcp.ag_ui_component_generator import AGUIComponentGenerator
from core.components.ag_ui_mcp.ag_ui_interaction_manager import AGUIInteractionManager
from core.components.ag_ui_mcp.ag_ui_event_handler import AGUIEventHandler
from core.components.ag_ui_mcp.ag_ui_protocol_adapter import AGUIProtocolAdapter

# 导入MCP组件
from core.components.mcp_zero_smart_engine.discovery.mcp_zero_discovery_engine import MCPZeroDiscoveryEngine
from core.components.memoryos_mcp.memory_engine import MemoryOSEngine
from core.components.trae_agent_mcp.trae_agent_coordinator import TraeAgentCoordinator
from core.components.ai_ecosystem_integration.claudeditor.claudeditor_deep_integration import ClaudEditorDeepIntegration
from core.components.stagewise_mcp.stagewise_service import StagewiseService

# 导入Claude SDK
from core.components.claude_integration_mcp.claude_sdk.claude_client import ClaudeClient
from core.components.claude_integration_mcp.claude_sdk.conversation_manager import ConversationManager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudEditorMainUI:
    """ClaudEditor v4.1 主界面管理器"""
    
    def __init__(self):
        self.app = FastAPI(title="ClaudEditor v4.1", description="AI协作开发神器")
        self.setup_cors()
        self.setup_static_files()
        
        # 初始化AG-UI组件
        self.component_generator = AGUIComponentGenerator()
        self.interaction_manager = AGUIInteractionManager()
        self.event_handler = AGUIEventHandler()
        self.protocol_adapter = AGUIProtocolAdapter()
        
        # 初始化MCP组件
        self.mcp_discovery = MCPZeroDiscoveryEngine()
        self.memory_engine = MemoryOSEngine()
        self.trae_coordinator = TraeAgentCoordinator()
        self.claudeditor_integration = ClaudEditorDeepIntegration()
        self.stagewise_service = StagewiseService()
        
        # 初始化Claude SDK
        self.claude_client = ClaudeClient()
        self.conversation_manager = ConversationManager()
        
        # WebSocket连接管理
        self.active_connections: List[WebSocket] = []
        
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
        # 创建静态文件目录
        os.makedirs("claudeditor/static", exist_ok=True)
        os.makedirs("claudeditor/templates", exist_ok=True)
        
        self.app.mount("/static", StaticFiles(directory="claudeditor/static"), name="static")
        self.templates = Jinja2Templates(directory="claudeditor/templates")
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """主页面"""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.get("/api/status")
        async def get_status():
            """获取系统状态"""
            return {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "mcp_discovery": await self.mcp_discovery.get_status(),
                    "memory_engine": await self.memory_engine.get_status(),
                    "trae_coordinator": await self.trae_coordinator.get_status(),
                    "claudeditor_integration": await self.claudeditor_integration.get_status(),
                    "stagewise_service": await self.stagewise_service.get_status()
                }
            }
        
        @self.app.get("/api/mcp/tools")
        async def get_mcp_tools():
            """获取MCP工具列表"""
            try:
                tools = await self.mcp_discovery.discover_tools()
                return {"tools": tools, "count": len(tools)}
            except Exception as e:
                logger.error(f"获取MCP工具失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/memory/store")
        async def store_memory(data: dict):
            """存储记忆"""
            try:
                result = await self.memory_engine.store_memory(
                    content=data.get("content"),
                    memory_type=data.get("type", "short_term"),
                    metadata=data.get("metadata", {})
                )
                return {"success": True, "memory_id": result}
            except Exception as e:
                logger.error(f"存储记忆失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/memory/search")
        async def search_memory(query: str, limit: int = 10):
            """搜索记忆"""
            try:
                results = await self.memory_engine.search_memories(query, limit)
                return {"memories": results, "count": len(results)}
            except Exception as e:
                logger.error(f"搜索记忆失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/ai/chat")
        async def ai_chat(data: dict):
            """AI对话"""
            try:
                message = data.get("message")
                model = data.get("model", "claude")
                
                if model == "claude":
                    response = await self.claude_client.send_message(message)
                else:
                    # 通过Trae Agent协调其他模型
                    response = await self.trae_coordinator.process_message(message, model)
                
                return {"response": response, "model": model}
            except Exception as e:
                logger.error(f"AI对话失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/stagewise/start")
        async def start_stagewise_session(data: dict):
            """启动Stagewise会话"""
            try:
                session_id = await self.stagewise_service.start_session(
                    user_id=data.get("user_id"),
                    project_id=data.get("project_id", "default")
                )
                return {"session_id": session_id}
            except Exception as e:
                logger.error(f"启动Stagewise会话失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket连接"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
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
        
        if message_type == "mcp_tool_execute":
            # 执行MCP工具
            tool_name = message.get("tool_name")
            parameters = message.get("parameters", {})
            result = await self.mcp_discovery.execute_tool(tool_name, parameters)
            return {"type": "mcp_tool_result", "result": result}
        
        elif message_type == "memory_query":
            # 记忆查询
            query = message.get("query")
            results = await self.memory_engine.search_memories(query)
            return {"type": "memory_results", "results": results}
        
        elif message_type == "ai_stream_chat":
            # 流式AI对话
            message_content = message.get("message")
            model = message.get("model", "claude")
            
            # 这里应该实现流式响应，简化处理
            response = await self.claude_client.send_message(message_content)
            return {"type": "ai_response", "response": response}
        
        else:
            return {"type": "error", "message": f"未知消息类型: {message_type}"}
    
    async def broadcast_message(self, message: dict):
        """广播消息给所有连接的客户端"""
        if self.active_connections:
            message_str = json.dumps(message)
            for connection in self.active_connections.copy():
                try:
                    await connection.send_text(message_str)
                except:
                    self.active_connections.remove(connection)
    
    async def initialize_components(self):
        """初始化所有组件"""
        logger.info("初始化ClaudEditor v4.1组件...")
        
        try:
            # 初始化MCP组件
            await self.mcp_discovery.initialize()
            await self.memory_engine.initialize()
            await self.trae_coordinator.initialize()
            await self.claudeditor_integration.initialize()
            await self.stagewise_service.initialize()
            
            # 初始化Claude SDK
            await self.claude_client.initialize()
            await self.conversation_manager.initialize()
            
            logger.info("所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """启动服务器"""
        await self.initialize_components()
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"ClaudEditor v4.1 启动在 http://{host}:{port}")
        await server.serve()


async def main():
    """主函数"""
    claudeditor_ui = ClaudEditorMainUI()
    await claudeditor_ui.start_server()


if __name__ == "__main__":
    asyncio.run(main())

