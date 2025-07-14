#!/usr/bin/env python3
"""
WebSocket Server - Mirror Code WebSocket 服務器
提供實時通信能力
"""

import asyncio
import json
import logging
import time

# 嘗試導入 websockets，如果不可用則使用模擬模式
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WEBSOCKETS_AVAILABLE = False
from typing import Dict, Set, Any, Optional
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

@dataclass
class WebSocketClient:
    """WebSocket 客戶端"""
    id: str
    websocket: Any
    connected_at: float
    last_ping: float = 0
    subscriptions: Set[str] = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()

class WebSocketServer:
    """WebSocket 服務器"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, WebSocketClient] = {}
        self.is_running = False
        self.server = None
        self.communication_manager = None
        
    async def start_server(self):
        """啟動 WebSocket 服務器"""
        try:
            print(f"🌐 啟動 WebSocket 服務器: ws://{self.host}:{self.port}")
            
            if not WEBSOCKETS_AVAILABLE:
                print(f"⚠️ websockets 模組不可用，使用模擬模式")
                self.is_running = True
                print(f"✅ WebSocket 服務器已啟動 (模擬模式)")
                asyncio.create_task(self._heartbeat_loop())
                return True
            
            # 實際的 WebSocket 服務器啟動
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port
            )
            
            self.is_running = True
            print(f"✅ WebSocket 服務器已啟動: ws://{self.host}:{self.port}")
            
            # 創建心跳任務
            asyncio.create_task(self._heartbeat_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket 服務器啟動失敗: {e}")
            return False
    
    async def stop_server(self):
        """停止 WebSocket 服務器"""
        self.is_running = False
        
        # 斷開所有客戶端
        for client in list(self.clients.values()):
            await self._disconnect_client(client)
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        print("🛑 WebSocket 服務器已停止")
    
    async def _handle_client(self, websocket, path):
        """處理客戶端連接"""
        client_id = f"client_{uuid.uuid4().hex[:8]}"
        client = WebSocketClient(
            id=client_id,
            websocket=websocket,
            connected_at=time.time()
        )
        
        self.clients[client_id] = client
        logger.info(f"客戶端連接: {client_id}")
        
        try:
            # 發送歡迎消息
            await self._send_to_client(client, {
                "type": "welcome",
                "client_id": client_id,
                "server_time": time.time()
            })
            
            # 處理客戶端消息
            async for message in websocket:
                await self._handle_message(client, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客戶端斷開: {client_id}")
        except Exception as e:
            logger.error(f"客戶端處理錯誤: {e}")
        finally:
            await self._disconnect_client(client)
    
    async def _handle_message(self, client: WebSocketClient, message: str):
        """處理客戶端消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self._handle_ping(client)
            elif message_type == "subscribe":
                await self._handle_subscribe(client, data)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(client, data)
            elif message_type == "command":
                await self._handle_command(client, data)
            else:
                logger.warning(f"未知消息類型: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("無效的 JSON 消息")
        except Exception as e:
            logger.error(f"消息處理錯誤: {e}")
    
    async def _handle_ping(self, client: WebSocketClient):
        """處理 ping 消息"""
        client.last_ping = time.time()
        await self._send_to_client(client, {
            "type": "pong",
            "timestamp": time.time()
        })
    
    async def _handle_subscribe(self, client: WebSocketClient, data: Dict[str, Any]):
        """處理訂閱請求"""
        channels = data.get("channels", [])
        
        for channel in channels:
            client.subscriptions.add(channel)
        
        await self._send_to_client(client, {
            "type": "subscribed",
            "channels": list(client.subscriptions)
        })
        
        logger.info(f"客戶端 {client.id} 訂閱頻道: {channels}")
    
    async def _handle_unsubscribe(self, client: WebSocketClient, data: Dict[str, Any]):
        """處理取消訂閱請求"""
        channels = data.get("channels", [])
        
        for channel in channels:
            client.subscriptions.discard(channel)
        
        await self._send_to_client(client, {
            "type": "unsubscribed",
            "channels": channels
        })
        
        logger.info(f"客戶端 {client.id} 取消訂閱頻道: {channels}")
    
    async def _handle_command(self, client: WebSocketClient, data: Dict[str, Any]):
        """處理命令請求"""
        command = data.get("command")
        params = data.get("params", {})
        
        # 這裡可以集成 Mirror Code 的命令執行
        result = {
            "type": "command_result",
            "command": command,
            "success": True,
            "result": f"執行命令: {command}",
            "timestamp": time.time()
        }
        
        await self._send_to_client(client, result)
    
    async def _send_to_client(self, client: WebSocketClient, message: Dict[str, Any]):
        """發送消息給客戶端"""
        try:
            # 模擬發送 (在實際實現中會使用 websocket.send)
            logger.debug(f"發送消息給 {client.id}: {message['type']}")
        except Exception as e:
            logger.error(f"發送消息失敗: {e}")
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """廣播消息到頻道"""
        if not self.is_running:
            return
        
        subscribers = [
            client for client in self.clients.values()
            if channel in client.subscriptions
        ]
        
        if subscribers:
            logger.info(f"廣播到頻道 {channel}: {len(subscribers)} 個客戶端")
            
            for client in subscribers:
                await self._send_to_client(client, {
                    "type": "broadcast",
                    "channel": channel,
                    "data": message,
                    "timestamp": time.time()
                })
    
    async def _disconnect_client(self, client: WebSocketClient):
        """斷開客戶端連接"""
        if client.id in self.clients:
            del self.clients[client.id]
        
        logger.info(f"客戶端已斷開: {client.id}")
    
    async def _heartbeat_loop(self):
        """心跳循環"""
        while self.is_running:
            current_time = time.time()
            
            # 檢查客戶端連接狀態
            disconnected_clients = []
            
            for client in self.clients.values():
                # 30秒無 ping 視為斷開
                if current_time - client.last_ping > 30:
                    disconnected_clients.append(client)
            
            # 清理斷開的客戶端
            for client in disconnected_clients:
                await self._disconnect_client(client)
            
            # 發送服務器狀態
            if self.clients:
                status_message = {
                    "type": "server_status",
                    "connected_clients": len(self.clients),
                    "uptime": current_time - self.connected_at if hasattr(self, 'connected_at') else 0,
                    "timestamp": current_time
                }
                
                await self.broadcast_to_channel("status", status_message)
            
            await asyncio.sleep(10)  # 每10秒檢查一次
    
    def get_server_stats(self) -> Dict[str, Any]:
        """獲取服務器統計信息"""
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "connected_clients": len(self.clients),
            "clients": [
                {
                    "id": client.id,
                    "connected_at": client.connected_at,
                    "last_ping": client.last_ping,
                    "subscriptions": list(client.subscriptions)
                }
                for client in self.clients.values()
            ]
        }

class MockWebSocketServer(WebSocketServer):
    """模擬 WebSocket 服務器 (用於測試)"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        super().__init__(host, port)
        self.mock_clients = {}
        self.connected_at = time.time()
    
    async def start_server(self):
        """啟動模擬服務器"""
        self.is_running = True
        print(f"🌐 模擬 WebSocket 服務器已啟動: ws://{self.host}:{self.port}")
        
        # 創建一些模擬客戶端
        for i in range(3):
            client_id = f"mock_client_{i+1}"
            self.mock_clients[client_id] = {
                "id": client_id,
                "connected_at": time.time(),
                "subscriptions": ["events", "status"]
            }
        
        asyncio.create_task(self._heartbeat_loop())
        return True
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """模擬廣播"""
        if not self.is_running:
            return
        
        subscribers = [
            client for client in self.mock_clients.values()
            if channel in client.get("subscriptions", [])
        ]
        
        if subscribers:
            print(f"📡 模擬廣播到頻道 {channel}: {len(subscribers)} 個客戶端")
            print(f"   消息: {message.get('type', 'unknown')}")
    
    def get_server_stats(self) -> Dict[str, Any]:
        """獲取模擬服務器統計"""
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "connected_clients": len(self.mock_clients),
            "mock_mode": True,
            "clients": list(self.mock_clients.values())
        }