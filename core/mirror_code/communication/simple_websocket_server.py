#!/usr/bin/env python3
"""
Simple WebSocket Server - 不依賴外部庫的 WebSocket 服務器實現
使用標準庫實現 WebSocket 協議
"""

import socket
import threading
import time
import json
import hashlib
import base64
import struct
import logging
from typing import Dict, Set, Any, Optional, Callable
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

@dataclass
class WebSocketClient:
    """WebSocket 客戶端"""
    id: str
    socket: socket.socket
    address: tuple
    connected_at: float
    last_ping: float = 0
    subscriptions: Set[str] = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()

class SimpleWebSocketServer:
    """簡單 WebSocket 服務器"""
    
    WEBSOCKET_MAGIC_STRING = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, WebSocketClient] = {}
        self.is_running = False
        self.server_socket = None
        self.accept_thread = None
        self.heartbeat_thread = None
        
    def start_server(self):
        """啟動 WebSocket 服務器"""
        try:
            print(f"🌐 啟動 WebSocket 服務器: ws://{self.host}:{self.port}")
            
            # 創建服務器 socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 綁定和監聽
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            print(f"✅ WebSocket 服務器已啟動: ws://{self.host}:{self.port}")
            
            # 啟動接受連接線程
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.accept_thread.start()
            
            # 啟動心跳線程
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"WebSocket 服務器啟動失敗: {e}")
            return False
    
    def stop_server(self):
        """停止 WebSocket 服務器"""
        self.is_running = False
        
        # 斷開所有客戶端
        for client in list(self.clients.values()):
            self._disconnect_client(client)
        
        # 關閉服務器 socket
        if self.server_socket:
            self.server_socket.close()
        
        print("🛑 WebSocket 服務器已停止")
    
    def _accept_connections(self):
        """接受客戶端連接"""
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"📞 新連接來自: {address}")
                
                # 處理 WebSocket 握手
                if self._handle_handshake(client_socket):
                    # 創建客戶端對象
                    client_id = f"client_{uuid.uuid4().hex[:8]}"
                    client = WebSocketClient(
                        id=client_id,
                        socket=client_socket,
                        address=address,
                        connected_at=time.time()
                    )
                    
                    self.clients[client_id] = client
                    print(f"✅ WebSocket 客戶端已連接: {client_id}")
                    
                    # 啟動客戶端處理線程
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,),
                        daemon=True
                    )
                    client_thread.start()
                    
                    # 發送歡迎消息
                    self._send_message(client, {
                        "type": "welcome",
                        "client_id": client_id,
                        "server_time": time.time()
                    })
                else:
                    client_socket.close()
                    
            except Exception as e:
                if self.is_running:
                    logger.error(f"接受連接錯誤: {e}")
    
    def _handle_handshake(self, client_socket: socket.socket) -> bool:
        """處理 WebSocket 握手"""
        try:
            # 接收 HTTP 請求
            request = client_socket.recv(1024).decode('utf-8')
            
            # 解析請求頭
            lines = request.split('\r\n')
            headers = {}
            
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            # 檢查是否為 WebSocket 請求
            if (headers.get('upgrade', '').lower() != 'websocket' or
                headers.get('connection', '').lower() != 'upgrade'):
                return False
            
            # 獲取 WebSocket Key
            websocket_key = headers.get('sec-websocket-key')
            if not websocket_key:
                return False
            
            # 生成響應 key
            accept_key = self._generate_accept_key(websocket_key)
            
            # 發送握手響應
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n"
                "\r\n"
            )
            
            client_socket.send(response.encode('utf-8'))
            return True
            
        except Exception as e:
            logger.error(f"WebSocket 握手失敗: {e}")
            return False
    
    def _generate_accept_key(self, websocket_key: str) -> str:
        """生成 WebSocket Accept Key"""
        combined = websocket_key + self.WEBSOCKET_MAGIC_STRING
        sha1_hash = hashlib.sha1(combined.encode('utf-8')).digest()
        return base64.b64encode(sha1_hash).decode('utf-8')
    
    def _handle_client(self, client: WebSocketClient):
        """處理客戶端消息"""
        try:
            while self.is_running and client.id in self.clients:
                # 接收 WebSocket 幀
                frame_data = self._receive_frame(client.socket)
                
                if frame_data is None:
                    break
                
                # 解析消息
                try:
                    message = json.loads(frame_data)
                    self._process_message(client, message)
                except json.JSONDecodeError:
                    logger.error("無效的 JSON 消息")
                except Exception as e:
                    logger.error(f"消息處理錯誤: {e}")
                    
        except Exception as e:
            logger.error(f"客戶端處理錯誤: {e}")
        finally:
            self._disconnect_client(client)
    
    def _receive_frame(self, client_socket: socket.socket) -> Optional[str]:
        """接收 WebSocket 幀"""
        try:
            # 讀取前兩個字節
            first_bytes = client_socket.recv(2)
            if len(first_bytes) != 2:
                return None
            
            # 解析幀頭
            first_byte, second_byte = first_bytes
            
            # 檢查 FIN 位
            fin = (first_byte >> 7) & 1
            
            # 檢查操作碼
            opcode = first_byte & 0x0f
            
            # 檢查 MASK 位
            masked = (second_byte >> 7) & 1
            
            # 獲取載荷長度
            payload_length = second_byte & 0x7f
            
            # 處理擴展載荷長度
            if payload_length == 126:
                length_bytes = client_socket.recv(2)
                payload_length = struct.unpack('!H', length_bytes)[0]
            elif payload_length == 127:
                length_bytes = client_socket.recv(8)
                payload_length = struct.unpack('!Q', length_bytes)[0]
            
            # 讀取掩碼 (如果有)
            mask = None
            if masked:
                mask = client_socket.recv(4)
            
            # 讀取載荷數據
            payload = client_socket.recv(payload_length)
            
            # 解碼數據 (如果有掩碼)
            if masked and mask:
                payload = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
            
            # 處理不同的操作碼
            if opcode == 1:  # 文本幀
                return payload.decode('utf-8')
            elif opcode == 8:  # 關閉幀
                return None
            elif opcode == 9:  # Ping 幀
                self._send_pong(client_socket, payload)
                return ""
            elif opcode == 10:  # Pong 幀
                return ""
            
            return payload.decode('utf-8')
            
        except Exception as e:
            logger.error(f"接收幀錯誤: {e}")
            return None
    
    def _send_frame(self, client_socket: socket.socket, data: str, opcode: int = 1):
        """發送 WebSocket 幀"""
        try:
            payload = data.encode('utf-8')
            payload_length = len(payload)
            
            # 構建幀頭
            frame = bytearray()
            
            # 第一個字節: FIN=1, RSV=000, OPCODE
            frame.append(0x80 | opcode)
            
            # 第二個字節和長度
            if payload_length < 126:
                frame.append(payload_length)
            elif payload_length < 65536:
                frame.append(126)
                frame.extend(struct.pack('!H', payload_length))
            else:
                frame.append(127)
                frame.extend(struct.pack('!Q', payload_length))
            
            # 添加載荷
            frame.extend(payload)
            
            client_socket.send(frame)
            
        except Exception as e:
            logger.error(f"發送幀錯誤: {e}")
    
    def _send_pong(self, client_socket: socket.socket, ping_data: bytes):
        """發送 Pong 幀"""
        try:
            frame = bytearray()
            frame.append(0x8A)  # FIN=1, OPCODE=10 (Pong)
            frame.append(len(ping_data))
            frame.extend(ping_data)
            client_socket.send(frame)
        except Exception as e:
            logger.error(f"發送 Pong 錯誤: {e}")
    
    def _process_message(self, client: WebSocketClient, message: Dict[str, Any]):
        """處理客戶端消息"""
        message_type = message.get("type")
        
        if message_type == "ping":
            self._handle_ping(client)
        elif message_type == "subscribe":
            self._handle_subscribe(client, message)
        elif message_type == "unsubscribe":
            self._handle_unsubscribe(client, message)
        elif message_type == "command":
            self._handle_command(client, message)
        else:
            logger.warning(f"未知消息類型: {message_type}")
    
    def _handle_ping(self, client: WebSocketClient):
        """處理 ping 消息"""
        client.last_ping = time.time()
        self._send_message(client, {
            "type": "pong",
            "timestamp": time.time()
        })
    
    def _handle_subscribe(self, client: WebSocketClient, message: Dict[str, Any]):
        """處理訂閱請求"""
        channels = message.get("channels", [])
        
        for channel in channels:
            client.subscriptions.add(channel)
        
        self._send_message(client, {
            "type": "subscribed",
            "channels": list(client.subscriptions)
        })
        
        logger.info(f"客戶端 {client.id} 訂閱頻道: {channels}")
    
    def _handle_unsubscribe(self, client: WebSocketClient, message: Dict[str, Any]):
        """處理取消訂閱請求"""
        channels = message.get("channels", [])
        
        for channel in channels:
            client.subscriptions.discard(channel)
        
        self._send_message(client, {
            "type": "unsubscribed",
            "channels": channels
        })
        
        logger.info(f"客戶端 {client.id} 取消訂閱頻道: {channels}")
    
    def _handle_command(self, client: WebSocketClient, message: Dict[str, Any]):
        """處理命令請求"""
        command = message.get("command")
        params = message.get("params", {})
        
        # 這裡可以集成 Mirror Code 的命令執行
        result = {
            "type": "command_result",
            "command": command,
            "success": True,
            "result": f"執行命令: {command}",
            "timestamp": time.time()
        }
        
        self._send_message(client, result)
    
    def _send_message(self, client: WebSocketClient, message: Dict[str, Any]):
        """發送消息給客戶端"""
        try:
            message_json = json.dumps(message)
            self._send_frame(client.socket, message_json)
        except Exception as e:
            logger.error(f"發送消息失敗: {e}")
            self._disconnect_client(client)
    
    def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """廣播消息到頻道"""
        if not self.is_running:
            return
        
        subscribers = [
            client for client in self.clients.values()
            if channel in client.subscriptions
        ]
        
        if subscribers:
            logger.info(f"廣播到頻道 {channel}: {len(subscribers)} 個客戶端")
            
            broadcast_message = {
                "type": "broadcast",
                "channel": channel,
                "data": message,
                "timestamp": time.time()
            }
            
            for client in subscribers:
                self._send_message(client, broadcast_message)
    
    def _disconnect_client(self, client: WebSocketClient):
        """斷開客戶端連接"""
        try:
            client.socket.close()
        except:
            pass
        
        if client.id in self.clients:
            del self.clients[client.id]
        
        logger.info(f"客戶端已斷開: {client.id}")
    
    def _heartbeat_loop(self):
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
                self._disconnect_client(client)
            
            # 發送服務器狀態
            if self.clients:
                status_message = {
                    "type": "server_status",
                    "connected_clients": len(self.clients),
                    "uptime": current_time - getattr(self, 'start_time', current_time),
                    "timestamp": current_time
                }
                
                self.broadcast_to_channel("status", status_message)
            
            time.sleep(10)  # 每10秒檢查一次
    
    def get_server_stats(self) -> Dict[str, Any]:
        """獲取服務器統計信息"""
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "connected_clients": len(self.clients),
            "implementation": "simple_websocket_server",
            "clients": [
                {
                    "id": client.id,
                    "address": client.address,
                    "connected_at": client.connected_at,
                    "last_ping": client.last_ping,
                    "subscriptions": list(client.subscriptions)
                }
                for client in self.clients.values()
            ]
        }

# 測試函數
def test_simple_websocket_server():
    """測試簡單 WebSocket 服務器"""
    server = SimpleWebSocketServer("localhost", 8765)
    
    try:
        print("啟動 WebSocket 服務器測試...")
        success = server.start_server()
        
        if success:
            print("✅ 服務器啟動成功")
            
            # 運行10秒
            time.sleep(10)
            
            stats = server.get_server_stats()
            print(f"📊 服務器統計: {stats['connected_clients']} 個客戶端")
            
        else:
            print("❌ 服務器啟動失敗")
            
    except KeyboardInterrupt:
        print("\n收到中斷信號")
    finally:
        server.stop_server()
        print("✅ 測試完成")

if __name__ == "__main__":
    test_simple_websocket_server()