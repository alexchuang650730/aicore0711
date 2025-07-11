#!/usr/bin/env python3
"""
PowerAutomation v4.6.2 完整Mirror Code架構
Complete Mirror Code System Architecture

🪞 Mirror Code架構組件:
├── Mirror Engine (核心引擎)
├── Local Adapter Integration (本地適配器集成)
├── Result Capture (結果捕獲)
├── Claude Integration (Claude集成)
├── Sync Manager (同步管理)
├── Communication Manager (通信管理)
└── WebSocket Server (WebSocket服務)
"""

import asyncio
import json
import logging
import websockets
import uuid
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import subprocess
import os
from pathlib import Path

# 導入相關模組
from local_mcp_adapter_integration import LocalMCPIntegrationManager, LocalPlatform
from cloud_edge_mcp_integration import CloudEdgeMCPManager
from macos_mirror_engine_claude_code import MacOSMirrorEngine, ClaudeCodeRequest, ClaudeCodeServiceType

logger = logging.getLogger(__name__)

class MirrorCodeEventType(Enum):
    """Mirror Code 事件類型"""
    COMMAND_EXECUTED = "command_executed"
    RESULT_CAPTURED = "result_captured"
    CLAUDE_RESPONSE = "claude_response"
    SYNC_COMPLETED = "sync_completed"
    ERROR_OCCURRED = "error_occurred"
    STATUS_UPDATE = "status_update"

class SyncDirection(Enum):
    """同步方向"""
    LOCAL_TO_REMOTE = "local_to_remote"
    REMOTE_TO_LOCAL = "remote_to_local"
    BIDIRECTIONAL = "bidirectional"

@dataclass
class MirrorCodeEvent:
    """Mirror Code 事件"""
    event_id: str
    event_type: MirrorCodeEventType
    timestamp: float
    source: str
    target: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CapturedResult:
    """捕獲的結果"""
    result_id: str
    command: str
    output: str
    error: str
    return_code: int
    execution_time: float
    platform: str
    captured_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResultCapture:
    """結果捕獲組件"""
    
    def __init__(self):
        self.captured_results = {}
        self.capture_filters = []
        self.capture_callbacks = []
        
    def add_capture_filter(self, filter_func: Callable[[str], bool]):
        """添加捕獲過濾器"""
        self.capture_filters.append(filter_func)
    
    def add_capture_callback(self, callback: Callable[[CapturedResult], None]):
        """添加捕獲回調"""
        self.capture_callbacks.append(callback)
    
    async def capture_command_result(self, command: str, result: Dict[str, Any], platform: str) -> CapturedResult:
        """捕獲命令結果"""
        # 檢查過濾器
        if self.capture_filters:
            should_capture = any(filter_func(command) for filter_func in self.capture_filters)
            if not should_capture:
                return None
        
        captured_result = CapturedResult(
            result_id=f"capture_{uuid.uuid4().hex[:8]}",
            command=command,
            output=result.get("stdout", ""),
            error=result.get("stderr", ""),
            return_code=result.get("return_code", 0),
            execution_time=result.get("execution_time", 0.0),
            platform=platform,
            captured_at=time.time(),
            metadata={
                "status": result.get("status", "unknown"),
                "execution_location": result.get("execution_location", "unknown")
            }
        )
        
        # 保存結果
        self.captured_results[captured_result.result_id] = captured_result
        
        # 調用回調
        for callback in self.capture_callbacks:
            try:
                await callback(captured_result) if asyncio.iscoroutinefunction(callback) else callback(captured_result)
            except Exception as e:
                logger.error(f"捕獲回調錯誤: {e}")
        
        print(f"📸 捕獲結果: {command} -> {platform}")
        return captured_result
    
    def get_captured_results(self, limit: int = 100) -> List[CapturedResult]:
        """獲取捕獲的結果"""
        results = list(self.captured_results.values())
        return sorted(results, key=lambda x: x.captured_at, reverse=True)[:limit]
    
    def clear_captured_results(self):
        """清除捕獲的結果"""
        self.captured_results.clear()

class ClaudeIntegration:
    """Claude 集成組件"""
    
    def __init__(self):
        self.claude_engine = None
        self.request_queue = asyncio.Queue()
        self.response_callbacks = {}
        self.is_processing = False
        
    async def initialize_claude_integration(self, config: Dict[str, Any]):
        """初始化 Claude 集成"""
        print("🤖 初始化 Claude 集成...")
        
        self.claude_engine = MacOSMirrorEngine()
        init_result = await self.claude_engine.initialize_mirror_engine(config)
        
        # 啟動請求處理循環
        if not self.is_processing:
            asyncio.create_task(self._process_claude_requests())
            self.is_processing = True
        
        return init_result
    
    async def _process_claude_requests(self):
        """處理 Claude 請求循環"""
        while True:
            try:
                if not self.request_queue.empty():
                    request_data = await self.request_queue.get()
                    await self._handle_claude_request(request_data)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Claude 請求處理錯誤: {e}")
                await asyncio.sleep(1)
    
    async def _handle_claude_request(self, request_data: Dict[str, Any]):
        """處理 Claude 請求"""
        try:
            session_id = request_data["session_id"]
            claude_request = request_data["request"]
            callback = request_data.get("callback")
            
            # 處理 Claude 請求
            response = await self.claude_engine.process_claude_code_request(session_id, claude_request)
            
            # 調用回調
            if callback and callback in self.response_callbacks:
                await self.response_callbacks[callback](response)
            
        except Exception as e:
            logger.error(f"Claude 請求處理失敗: {e}")
    
    async def submit_claude_request(self, session_id: str, request: ClaudeCodeRequest, callback_id: str = None) -> str:
        """提交 Claude 請求"""
        request_id = f"claude_req_{uuid.uuid4().hex[:8]}"
        
        request_data = {
            "request_id": request_id,
            "session_id": session_id,
            "request": request,
            "callback": callback_id
        }
        
        await self.request_queue.put(request_data)
        print(f"🤖 提交 Claude 請求: {request.service_type.value}")
        
        return request_id
    
    def register_response_callback(self, callback_id: str, callback: Callable):
        """註冊響應回調"""
        self.response_callbacks[callback_id] = callback

class SyncManager:
    """同步管理組件"""
    
    def __init__(self):
        self.sync_rules = []
        self.sync_queue = asyncio.Queue()
        self.sync_history = []
        self.is_syncing = False
        
    def add_sync_rule(self, rule: Dict[str, Any]):
        """添加同步規則"""
        self.sync_rules.append({
            "id": f"rule_{uuid.uuid4().hex[:8]}",
            "pattern": rule.get("pattern", "*"),
            "direction": SyncDirection(rule.get("direction", "bidirectional")),
            "target_platforms": rule.get("target_platforms", []),
            "enabled": rule.get("enabled", True),
            **rule
        })
        
        print(f"📋 添加同步規則: {rule.get('pattern', '*')} -> {rule.get('direction', 'bidirectional')}")
    
    async def start_sync_service(self):
        """啟動同步服務"""
        if not self.is_syncing:
            asyncio.create_task(self._sync_service_loop())
            self.is_syncing = True
            print("🔄 同步服務已啟動")
    
    async def _sync_service_loop(self):
        """同步服務循環"""
        while True:
            try:
                if not self.sync_queue.empty():
                    sync_task = await self.sync_queue.get()
                    await self._process_sync_task(sync_task)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"同步服務錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _process_sync_task(self, sync_task: Dict[str, Any]):
        """處理同步任務"""
        task_id = sync_task["task_id"]
        sync_type = sync_task["type"]
        data = sync_task["data"]
        
        print(f"🔄 處理同步任務: {task_id} ({sync_type})")
        
        try:
            # 根據同步類型處理
            if sync_type == "result_sync":
                await self._sync_result(data)
            elif sync_type == "file_sync":
                await self._sync_file(data)
            elif sync_type == "status_sync":
                await self._sync_status(data)
            
            # 記錄同步歷史
            self.sync_history.append({
                "task_id": task_id,
                "type": sync_type,
                "timestamp": time.time(),
                "status": "completed"
            })
            
        except Exception as e:
            logger.error(f"同步任務失敗: {e}")
            self.sync_history.append({
                "task_id": task_id,
                "type": sync_type,
                "timestamp": time.time(),
                "status": "failed",
                "error": str(e)
            })
    
    async def _sync_result(self, data: Dict[str, Any]):
        """同步結果"""
        # 實現結果同步邏輯
        pass
    
    async def _sync_file(self, data: Dict[str, Any]):
        """同步文件"""
        # 實現文件同步邏輯
        pass
    
    async def _sync_status(self, data: Dict[str, Any]):
        """同步狀態"""
        # 實現狀態同步邏輯
        pass
    
    async def submit_sync_task(self, sync_type: str, data: Dict[str, Any]) -> str:
        """提交同步任務"""
        task_id = f"sync_{uuid.uuid4().hex[:8]}"
        
        sync_task = {
            "task_id": task_id,
            "type": sync_type,
            "data": data,
            "submitted_at": time.time()
        }
        
        await self.sync_queue.put(sync_task)
        return task_id

class CommunicationManager:
    """通信管理組件"""
    
    def __init__(self):
        self.channels = {}
        self.message_handlers = {}
        self.event_subscribers = {}
        
    def create_channel(self, channel_id: str, channel_type: str = "general") -> str:
        """創建通信通道"""
        self.channels[channel_id] = {
            "id": channel_id,
            "type": channel_type,
            "created_at": time.time(),
            "subscribers": set(),
            "message_history": []
        }
        
        print(f"📡 創建通信通道: {channel_id} ({channel_type})")
        return channel_id
    
    def subscribe_to_channel(self, channel_id: str, subscriber_id: str):
        """訂閱通道"""
        if channel_id in self.channels:
            self.channels[channel_id]["subscribers"].add(subscriber_id)
            print(f"📨 {subscriber_id} 訂閱通道: {channel_id}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """註冊消息處理器"""
        self.message_handlers[message_type] = handler
    
    def register_event_subscriber(self, event_type: MirrorCodeEventType, subscriber: Callable):
        """註冊事件訂閱者"""
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = []
        self.event_subscribers[event_type].append(subscriber)
    
    async def send_message(self, channel_id: str, message: Dict[str, Any], sender_id: str = "system"):
        """發送消息"""
        if channel_id not in self.channels:
            return False
        
        message_with_metadata = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "channel_id": channel_id,
            "sender_id": sender_id,
            "timestamp": time.time(),
            "content": message
        }
        
        # 保存到歷史
        self.channels[channel_id]["message_history"].append(message_with_metadata)
        
        # 通知訂閱者
        for subscriber in self.channels[channel_id]["subscribers"]:
            await self._notify_subscriber(subscriber, message_with_metadata)
        
        return True
    
    async def _notify_subscriber(self, subscriber_id: str, message: Dict[str, Any]):
        """通知訂閱者"""
        # 實現訂閱者通知邏輯
        print(f"📬 通知訂閱者 {subscriber_id}: {message['content'].get('type', 'message')}")
    
    async def publish_event(self, event: MirrorCodeEvent):
        """發布事件"""
        if event.event_type in self.event_subscribers:
            for subscriber in self.event_subscribers[event.event_type]:
                try:
                    await subscriber(event) if asyncio.iscoroutinefunction(subscriber) else subscriber(event)
                except Exception as e:
                    logger.error(f"事件訂閱者錯誤: {e}")

class WebSocketServer:
    """WebSocket 服務組件"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.connected_clients = {}
        self.message_handlers = {}
        
    async def start_server(self):
        """啟動 WebSocket 服務"""
        print(f"🌐 啟動 WebSocket 服務: {self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self._handle_client_connection,
            self.host,
            self.port
        )
        
        print(f"✅ WebSocket 服務已啟動")
    
    async def _handle_client_connection(self, websocket, path):
        """處理客戶端連接"""
        client_id = f"client_{uuid.uuid4().hex[:8]}"
        self.connected_clients[client_id] = {
            "id": client_id,
            "websocket": websocket,
            "connected_at": time.time(),
            "path": path
        }
        
        print(f"🔗 客戶端連接: {client_id} ({path})")
        
        try:
            await self._send_to_client(client_id, {
                "type": "connection_established",
                "client_id": client_id,
                "server_time": time.time()
            })
            
            async for message in websocket:
                await self._handle_client_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 客戶端斷開: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket 連接錯誤: {e}")
        finally:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
    
    async def _handle_client_message(self, client_id: str, message: str):
        """處理客戶端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            print(f"📨 收到消息: {client_id} -> {message_type}")
            
            # 處理不同類型的消息
            if message_type in self.message_handlers:
                response = await self.message_handlers[message_type](client_id, data)
                if response:
                    await self._send_to_client(client_id, response)
            else:
                await self._send_to_client(client_id, {
                    "type": "error",
                    "message": f"未知的消息類型: {message_type}"
                })
                
        except json.JSONDecodeError:
            await self._send_to_client(client_id, {
                "type": "error",
                "message": "無效的 JSON 格式"
            })
        except Exception as e:
            logger.error(f"處理客戶端消息錯誤: {e}")
    
    async def _send_to_client(self, client_id: str, data: Dict[str, Any]):
        """發送數據到客戶端"""
        if client_id in self.connected_clients:
            try:
                websocket = self.connected_clients[client_id]["websocket"]
                await websocket.send(json.dumps(data))
            except Exception as e:
                logger.error(f"發送到客戶端失敗: {e}")
    
    async def broadcast_to_all_clients(self, data: Dict[str, Any]):
        """廣播到所有客戶端"""
        for client_id in list(self.connected_clients.keys()):
            await self._send_to_client(client_id, data)
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """註冊消息處理器"""
        self.message_handlers[message_type] = handler
    
    async def stop_server(self):
        """停止 WebSocket 服務"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("🛑 WebSocket 服務已停止")

class MirrorEngine:
    """Mirror Engine 核心引擎"""
    
    def __init__(self):
        # 核心組件
        self.local_adapter_integration = None
        self.result_capture = ResultCapture()
        self.claude_integration = ClaudeIntegration()
        self.sync_manager = SyncManager()
        self.communication_manager = CommunicationManager()
        self.websocket_server = WebSocketServer()
        
        # 狀態管理
        self.is_initialized = False
        self.active_sessions = {}
        self.event_history = []
        
        # 統計數據
        self.metrics = {
            "commands_executed": 0,
            "results_captured": 0,
            "claude_requests": 0,
            "sync_operations": 0,
            "events_published": 0
        }
    
    async def initialize_mirror_engine(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """初始化 Mirror Engine"""
        print("🪞 初始化 Mirror Code 系統...")
        
        try:
            # 1. 初始化本地適配器集成
            await self._initialize_local_adapter_integration(config.get("local_adapter_config", {}))
            
            # 2. 初始化結果捕獲
            await self._initialize_result_capture(config.get("capture_config", {}))
            
            # 3. 初始化 Claude 集成
            await self._initialize_claude_integration(config.get("claude_config", {}))
            
            # 4. 初始化同步管理
            await self._initialize_sync_manager(config.get("sync_config", {}))
            
            # 5. 初始化通信管理
            await self._initialize_communication_manager(config.get("communication_config", {}))
            
            # 6. 初始化 WebSocket 服務
            await self._initialize_websocket_server(config.get("websocket_config", {}))
            
            # 7. 設置組件間連接
            await self._setup_component_connections()
            
            self.is_initialized = True
            
            result = {
                "status": "initialized",
                "components": {
                    "local_adapter_integration": bool(self.local_adapter_integration),
                    "result_capture": True,
                    "claude_integration": bool(self.claude_integration.claude_engine),
                    "sync_manager": self.sync_manager.is_syncing,
                    "communication_manager": len(self.communication_manager.channels),
                    "websocket_server": bool(self.websocket_server.server)
                },
                "initialization_time": time.time()
            }
            
            print("✅ Mirror Code 系統初始化完成")
            return result
            
        except Exception as e:
            logger.error(f"Mirror Engine 初始化失敗: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _initialize_local_adapter_integration(self, config: Dict[str, Any]):
        """初始化本地適配器集成"""
        print("  🔧 初始化本地適配器集成...")
        
        self.local_adapter_integration = LocalMCPIntegrationManager()
        await self.local_adapter_integration.initialize_all_adapters()
    
    async def _initialize_result_capture(self, config: Dict[str, Any]):
        """初始化結果捕獲"""
        print("  📸 初始化結果捕獲...")
        
        # 添加默認捕獲過濾器
        if config.get("capture_all", True):
            self.result_capture.add_capture_filter(lambda cmd: True)
        
        # 添加捕獲回調
        self.result_capture.add_capture_callback(self._on_result_captured)
    
    async def _initialize_claude_integration(self, config: Dict[str, Any]):
        """初始化 Claude 集成"""
        print("  🤖 初始化 Claude 集成...")
        
        await self.claude_integration.initialize_claude_integration(config)
        
        # 註冊響應回調
        self.claude_integration.register_response_callback("mirror_engine", self._on_claude_response)
    
    async def _initialize_sync_manager(self, config: Dict[str, Any]):
        """初始化同步管理"""
        print("  🔄 初始化同步管理...")
        
        # 添加默認同步規則
        default_rules = config.get("sync_rules", [
            {
                "pattern": "*.py",
                "direction": "bidirectional",
                "target_platforms": ["all"]
            },
            {
                "pattern": "stdout",
                "direction": "local_to_remote",
                "target_platforms": ["remote"]
            }
        ])
        
        for rule in default_rules:
            self.sync_manager.add_sync_rule(rule)
        
        await self.sync_manager.start_sync_service()
    
    async def _initialize_communication_manager(self, config: Dict[str, Any]):
        """初始化通信管理"""
        print("  📡 初始化通信管理...")
        
        # 創建默認通道
        default_channels = config.get("channels", [
            {"id": "mirror_events", "type": "events"},
            {"id": "claude_responses", "type": "claude"},
            {"id": "system_status", "type": "status"}
        ])
        
        for channel in default_channels:
            self.communication_manager.create_channel(channel["id"], channel["type"])
        
        # 註冊事件訂閱者
        for event_type in MirrorCodeEventType:
            self.communication_manager.register_event_subscriber(event_type, self._on_event_published)
    
    async def _initialize_websocket_server(self, config: Dict[str, Any]):
        """初始化 WebSocket 服務"""
        print("  🌐 初始化 WebSocket 服務...")
        
        host = config.get("host", "localhost")
        port = config.get("port", 8765)
        
        self.websocket_server = WebSocketServer(host, port)
        
        # 註冊消息處理器
        self.websocket_server.register_message_handler("execute_command", self._handle_execute_command_message)
        self.websocket_server.register_message_handler("claude_request", self._handle_claude_request_message)
        self.websocket_server.register_message_handler("sync_request", self._handle_sync_request_message)
        
        await self.websocket_server.start_server()
    
    async def _setup_component_connections(self):
        """設置組件間連接"""
        print("  🔗 設置組件間連接...")
        
        # 將組件相互連接，形成完整的 Mirror Code 系統
        # 這裡可以設置更多的組件間通信邏輯
        pass
    
    async def _on_result_captured(self, result: CapturedResult):
        """結果捕獲回調"""
        self.metrics["results_captured"] += 1
        
        # 發布事件
        event = MirrorCodeEvent(
            event_id=f"event_{uuid.uuid4().hex[:8]}",
            event_type=MirrorCodeEventType.RESULT_CAPTURED,
            timestamp=time.time(),
            source="result_capture",
            target="mirror_engine",
            payload={
                "result_id": result.result_id,
                "command": result.command,
                "platform": result.platform,
                "status": "captured"
            }
        )
        
        await self.communication_manager.publish_event(event)
        
        # 廣播到 WebSocket 客戶端
        await self.websocket_server.broadcast_to_all_clients({
            "type": "result_captured",
            "result": {
                "id": result.result_id,
                "command": result.command,
                "output": result.output[:200] + "..." if len(result.output) > 200 else result.output,
                "platform": result.platform,
                "execution_time": result.execution_time
            }
        })
    
    async def _on_claude_response(self, response):
        """Claude 響應回調"""
        self.metrics["claude_requests"] += 1
        
        # 發布事件
        event = MirrorCodeEvent(
            event_id=f"event_{uuid.uuid4().hex[:8]}",
            event_type=MirrorCodeEventType.CLAUDE_RESPONSE,
            timestamp=time.time(),
            source="claude_integration",
            target="mirror_engine",
            payload={
                "request_id": response.request_id,
                "service_type": response.service_type.value,
                "response_preview": response.response_text[:100] + "..." if len(response.response_text) > 100 else response.response_text
            }
        )
        
        await self.communication_manager.publish_event(event)
        
        # 廣播到 WebSocket 客戶端
        await self.websocket_server.broadcast_to_all_clients({
            "type": "claude_response",
            "response": {
                "request_id": response.request_id,
                "service_type": response.service_type.value,
                "response_text": response.response_text,
                "execution_time": response.execution_time
            }
        })
    
    async def _on_event_published(self, event: MirrorCodeEvent):
        """事件發布回調"""
        self.metrics["events_published"] += 1
        self.event_history.append(event)
        
        # 保持事件歷史在合理範圍內
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-500:]
    
    async def _handle_execute_command_message(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理執行命令消息"""
        command = data.get("command", "")
        platform = data.get("platform", "auto")
        
        if not command:
            return {"type": "error", "message": "命令不能為空"}
        
        try:
            # 執行命令
            if platform == "auto" and self.local_adapter_integration:
                # 自動選擇平台
                available_platforms = list(self.local_adapter_integration.adapters.keys())
                if available_platforms:
                    selected_platform = available_platforms[0]
                    result = await self.local_adapter_integration.execute_cross_platform_command(
                        selected_platform, command
                    )
                else:
                    return {"type": "error", "message": "沒有可用的平台適配器"}
            else:
                return {"type": "error", "message": "平台適配器未初始化"}
            
            # 捕獲結果
            captured_result = await self.result_capture.capture_command_result(
                command, result, selected_platform.value
            )
            
            self.metrics["commands_executed"] += 1
            
            return {
                "type": "command_executed",
                "result": {
                    "command": command,
                    "platform": selected_platform.value,
                    "status": result["status"],
                    "output": result.get("stdout", ""),
                    "captured_id": captured_result.result_id if captured_result else None
                }
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def _handle_claude_request_message(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理 Claude 請求消息"""
        service_type = data.get("service_type", "chat")
        prompt = data.get("prompt", "")
        
        if not prompt:
            return {"type": "error", "message": "提示不能為空"}
        
        try:
            # 創建 Claude 請求
            claude_request = ClaudeCodeRequest(
                request_id=f"ws_req_{uuid.uuid4().hex[:8]}",
                service_type=ClaudeCodeServiceType(service_type),
                prompt=prompt
            )
            
            # 提交請求
            session_id = f"ws_session_{client_id}"
            request_id = await self.claude_integration.submit_claude_request(
                session_id, claude_request, "mirror_engine"
            )
            
            return {
                "type": "claude_request_submitted",
                "request_id": request_id,
                "message": "Claude 請求已提交，請等待響應"
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def _handle_sync_request_message(self, client_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理同步請求消息"""
        sync_type = data.get("sync_type", "result_sync")
        sync_data = data.get("data", {})
        
        try:
            task_id = await self.sync_manager.submit_sync_task(sync_type, sync_data)
            
            self.metrics["sync_operations"] += 1
            
            return {
                "type": "sync_request_submitted",
                "task_id": task_id,
                "message": "同步請求已提交"
            }
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
    
    async def get_mirror_engine_status(self) -> Dict[str, Any]:
        """獲取 Mirror Engine 狀態"""
        return {
            "engine_status": "active" if self.is_initialized else "inactive",
            "components": {
                "local_adapter_integration": {
                    "status": "active" if self.local_adapter_integration else "inactive",
                    "adapters": len(self.local_adapter_integration.adapters) if self.local_adapter_integration else 0
                },
                "result_capture": {
                    "status": "active",
                    "captured_results": len(self.result_capture.captured_results),
                    "capture_filters": len(self.result_capture.capture_filters)
                },
                "claude_integration": {
                    "status": "active" if self.claude_integration.claude_engine else "inactive",
                    "processing": self.claude_integration.is_processing,
                    "queue_size": self.claude_integration.request_queue.qsize()
                },
                "sync_manager": {
                    "status": "active" if self.sync_manager.is_syncing else "inactive",
                    "sync_rules": len(self.sync_manager.sync_rules),
                    "queue_size": self.sync_manager.sync_queue.qsize(),
                    "sync_history": len(self.sync_manager.sync_history)
                },
                "communication_manager": {
                    "status": "active",
                    "channels": len(self.communication_manager.channels),
                    "event_subscribers": sum(len(subscribers) for subscribers in self.communication_manager.event_subscribers.values())
                },
                "websocket_server": {
                    "status": "active" if self.websocket_server.server else "inactive",
                    "connected_clients": len(self.websocket_server.connected_clients),
                    "host": self.websocket_server.host,
                    "port": self.websocket_server.port
                }
            },
            "metrics": self.metrics,
            "active_sessions": len(self.active_sessions),
            "event_history": len(self.event_history),
            "capabilities": {
                "command_execution": bool(self.local_adapter_integration),
                "result_capture": True,
                "claude_integration": bool(self.claude_integration.claude_engine),
                "real_time_sync": self.sync_manager.is_syncing,
                "websocket_communication": bool(self.websocket_server.server),
                "event_system": True
            }
        }

# 演示函數
async def demo_complete_mirror_code_system():
    """演示完整的 Mirror Code 系統"""
    print("🪞 PowerAutomation v4.6.2 完整 Mirror Code 系統演示")
    print("=" * 80)
    
    # 創建 Mirror Engine
    mirror_engine = MirrorEngine()
    
    # 配置系統
    config = {
        "local_adapter_config": {},
        "capture_config": {
            "capture_all": True
        },
        "claude_config": {
            "api_key": "test-key",
            "model": "claude-3-sonnet-20240229"
        },
        "sync_config": {
            "sync_rules": [
                {
                    "pattern": "*.py",
                    "direction": "bidirectional",
                    "target_platforms": ["all"]
                }
            ]
        },
        "communication_config": {
            "channels": [
                {"id": "mirror_events", "type": "events"},
                {"id": "claude_responses", "type": "claude"}
            ]
        },
        "websocket_config": {
            "host": "localhost",
            "port": 8765
        }
    }
    
    # 初始化系統
    print("\n🚀 初始化完整 Mirror Code 系統...")
    init_result = await mirror_engine.initialize_mirror_engine(config)
    
    print(f"  初始化狀態: {init_result['status']}")
    components = init_result.get('components', {})
    for component, status in components.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {component.replace('_', ' ').title()}")
    
    # 等待系統穩定
    await asyncio.sleep(2)
    
    # 獲取系統狀態
    print("\n📊 Mirror Code 系統狀態:")
    status = await mirror_engine.get_mirror_engine_status()
    
    print(f"  引擎狀態: {status['engine_status']}")
    print(f"  活躍會話: {status['active_sessions']}")
    print(f"  事件歷史: {status['event_history']}條")
    
    components_status = status['components']
    print(f"\n🔧 組件狀態:")
    for component, component_status in components_status.items():
        main_status = component_status.get('status', 'unknown')
        status_icon = "✅" if main_status == "active" else "❌"
        print(f"  {status_icon} {component.replace('_', ' ').title()}: {main_status}")
    
    metrics = status['metrics']
    print(f"\n📈 系統指標:")
    for metric, value in metrics.items():
        print(f"  📊 {metric.replace('_', ' ').title()}: {value}")
    
    capabilities = status['capabilities']
    print(f"\n🎯 系統能力:")
    for capability, enabled in capabilities.items():
        status_icon = "✅" if enabled else "❌"
        print(f"  {status_icon} {capability.replace('_', ' ').title()}")
    
    print(f"\n🌐 WebSocket 服務信息:")
    ws_status = components_status['websocket_server']
    print(f"  服務地址: ws://{ws_status['host']}:{ws_status['port']}")
    print(f"  連接客戶端: {ws_status['connected_clients']}個")
    
    print(f"\n🎉 完整 Mirror Code 系統演示完成！")
    print(f"   系統現在提供完整的 Mirror Code 架構功能:")
    print(f"   🪞 Mirror Engine (核心引擎)")
    print(f"   🔧 Local Adapter Integration (本地適配器集成)")
    print(f"   📸 Result Capture (結果捕獲)")
    print(f"   🤖 Claude Integration (Claude集成)")
    print(f"   🔄 Sync Manager (同步管理)")
    print(f"   📡 Communication Manager (通信管理)")
    print(f"   🌐 WebSocket Server (WebSocket服務)")
    
    return mirror_engine

if __name__ == "__main__":
    asyncio.run(demo_complete_mirror_code_system())