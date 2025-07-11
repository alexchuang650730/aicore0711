#!/usr/bin/env python3
"""
Mirror Engine - Mirror Code系統核心引擎
負責協調所有Mirror Code組件並提供統一的管理接口
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class MirrorEngineStatus(Enum):
    """Mirror Engine狀態"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class MirrorConfig:
    """Mirror配置"""
    enabled: bool = True
    auto_sync: bool = True
    sync_interval: int = 5
    debug: bool = False
    websocket_port: int = 8765
    claude_integration: bool = True
    local_adapters: List[str] = None
    remote_endpoints: List[Dict[str, Any]] = None

class MirrorEngine:
    """Mirror Engine核心引擎"""
    
    def __init__(self, config: MirrorConfig = None):
        self.config = config or MirrorConfig()
        self.status = MirrorEngineStatus.STOPPED
        self.session_id = f"mirror_{uuid.uuid4().hex[:8]}"
        
        # 組件實例
        self.local_adapter_integration = None
        self.result_capture = None
        self.claude_integration = None
        self.sync_manager = None
        self.communication_manager = None
        self.websocket_server = None
        
        # 狀態管理
        self.sync_count = 0
        self.last_sync_time = None
        self.error_count = 0
        self.active_tasks = {}
        
        # 事件回調
        self.event_handlers = {}
        
        print(f"🪞 Mirror Engine 已創建: {self.session_id}")
    
    async def start(self) -> bool:
        """啟動Mirror Engine"""
        if self.status != MirrorEngineStatus.STOPPED:
            logger.warning("Mirror Engine 已經在運行中")
            return False
        
        print(f"🚀 啟動Mirror Engine...")
        self.status = MirrorEngineStatus.STARTING
        
        try:
            # 1. 初始化本地適配器
            await self._initialize_local_adapters()
            
            # 2. 初始化結果捕獲
            await self._initialize_result_capture()
            
            # 3. 初始化Claude集成
            await self._initialize_claude_integration()
            
            # 4. 初始化同步管理
            await self._initialize_sync_manager()
            
            # 5. 初始化通信管理
            await self._initialize_communication_manager()
            
            # 6. 啟動WebSocket服務
            await self._start_websocket_server()
            
            # 7. 啟動主循環
            asyncio.create_task(self._main_loop())
            
            self.status = MirrorEngineStatus.RUNNING
            print(f"✅ Mirror Engine 啟動成功")
            
            return True
            
        except Exception as e:
            logger.error(f"Mirror Engine 啟動失敗: {e}")
            self.status = MirrorEngineStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """停止Mirror Engine"""
        if self.status == MirrorEngineStatus.STOPPED:
            return True
            
        print(f"🛑 停止Mirror Engine...")
        self.status = MirrorEngineStatus.STOPPING
        
        try:
            # 停止所有活躍任務
            for task_id, task in self.active_tasks.items():
                task.cancel()
            
            # 停止WebSocket服務
            if self.websocket_server:
                await self.websocket_server.stop_server()
            
            # 清理資源
            self.active_tasks.clear()
            
            self.status = MirrorEngineStatus.STOPPED
            print(f"✅ Mirror Engine 已停止")
            
            return True
            
        except Exception as e:
            logger.error(f"停止Mirror Engine 失敗: {e}")
            self.status = MirrorEngineStatus.ERROR
            return False
    
    async def _initialize_local_adapters(self):
        """初始化本地適配器"""
        print("  🔧 初始化本地適配器...")
        
        from ..command_execution.local_adapter_integration import LocalAdapterIntegration
        
        self.local_adapter_integration = LocalAdapterIntegration()
        await self.local_adapter_integration.initialize(self.config.local_adapters or [])
    
    async def _initialize_result_capture(self):
        """初始化結果捕獲"""
        print("  📸 初始化結果捕獲...")
        
        from ..command_execution.result_capture import ResultCapture
        
        self.result_capture = ResultCapture()
        await self.result_capture.initialize()
        
        # 註冊結果捕獲回調
        self.result_capture.add_callback(self._on_result_captured)
    
    async def _initialize_claude_integration(self):
        """初始化Claude集成"""
        if not self.config.claude_integration:
            return
            
        print("  🤖 初始化Claude集成...")
        
        from ..command_execution.claude_integration import ClaudeIntegration
        
        self.claude_integration = ClaudeIntegration()
        await self.claude_integration.initialize()
    
    async def _initialize_sync_manager(self):
        """初始化同步管理"""
        print("  🔄 初始化同步管理...")
        
        from ..sync.sync_manager import SyncManager
        
        self.sync_manager = SyncManager(
            auto_sync=self.config.auto_sync,
            sync_interval=self.config.sync_interval
        )
        await self.sync_manager.initialize()
    
    async def _initialize_communication_manager(self):
        """初始化通信管理"""
        print("  📡 初始化通信管理...")
        
        from ..communication.comm_manager import CommunicationManager
        
        self.communication_manager = CommunicationManager()
        await self.communication_manager.initialize()
    
    async def _start_websocket_server(self):
        """啟動WebSocket服務"""
        print(f"  🌐 啟動WebSocket服務: {self.config.websocket_port}")
        
        # 從complete_mirror_code_system導入WebSocket服務
        from ...complete_mirror_code_system import WebSocketServer
        
        self.websocket_server = WebSocketServer("localhost", self.config.websocket_port)
        await self.websocket_server.start_server()
    
    async def _main_loop(self):
        """主循環"""
        while self.status == MirrorEngineStatus.RUNNING:
            try:
                # 處理定期任務
                await self._process_periodic_tasks()
                
                # 檢查同步
                if self.config.auto_sync:
                    await self._check_auto_sync()
                
                # 處理事件
                await self._process_events()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"主循環錯誤: {e}")
                self.error_count += 1
                
                if self.error_count > 10:
                    logger.error("錯誤過多，停止Mirror Engine")
                    await self.stop()
                    break
                    
                await asyncio.sleep(5)
    
    async def _process_periodic_tasks(self):
        """處理定期任務"""
        # 清理完成的任務
        completed_tasks = [
            task_id for task_id, task in self.active_tasks.items()
            if task.done()
        ]
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
    
    async def _check_auto_sync(self):
        """檢查自動同步"""
        if not self.last_sync_time:
            await self.sync_now()
            return
        
        time_since_sync = time.time() - self.last_sync_time
        if time_since_sync >= self.config.sync_interval:
            await self.sync_now()
    
    async def _process_events(self):
        """處理事件"""
        # 處理通信管理器的事件
        if self.communication_manager:
            await self.communication_manager.process_events()
    
    async def _on_result_captured(self, result):
        """結果捕獲回調"""
        print(f"📸 捕獲結果: {result.get('command', 'unknown')}")
        
        # 觸發同步
        if self.sync_manager:
            await self.sync_manager.sync_result(result)
        
        # 廣播事件
        if self.communication_manager:
            await self.communication_manager.broadcast_event("result_captured", result)
    
    async def sync_now(self) -> bool:
        """立即執行同步"""
        try:
            if self.sync_manager:
                success = await self.sync_manager.sync_now()
                
                if success:
                    self.sync_count += 1
                    self.last_sync_time = time.time()
                    print(f"🔄 同步完成 (第{self.sync_count}次)")
                
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"同步失敗: {e}")
            return False
    
    async def execute_command(self, command: str, platform: str = "auto") -> Dict[str, Any]:
        """執行命令"""
        if not self.local_adapter_integration:
            return {"error": "本地適配器未初始化"}
        
        try:
            result = await self.local_adapter_integration.execute_command(command, platform)
            
            # 捕獲結果
            if self.result_capture:
                await self.result_capture.capture_result(command, result)
            
            return result
            
        except Exception as e:
            logger.error(f"命令執行失敗: {e}")
            return {"error": str(e)}
    
    async def execute_claude_command(self, prompt: str) -> Dict[str, Any]:
        """執行Claude命令"""
        if not self.claude_integration:
            return {"error": "Claude集成未啟用"}
        
        try:
            result = await self.claude_integration.execute_command(prompt)
            return result
            
        except Exception as e:
            logger.error(f"Claude命令執行失敗: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """獲取Mirror Engine狀態"""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "sync_count": self.sync_count,
            "last_sync_time": self.last_sync_time,
            "error_count": self.error_count,
            "active_tasks": len(self.active_tasks),
            "config": {
                "enabled": self.config.enabled,
                "auto_sync": self.config.auto_sync,
                "sync_interval": self.config.sync_interval,
                "claude_integration": self.config.claude_integration
            },
            "components": {
                "local_adapter_integration": bool(self.local_adapter_integration),
                "result_capture": bool(self.result_capture),
                "claude_integration": bool(self.claude_integration),
                "sync_manager": bool(self.sync_manager),
                "communication_manager": bool(self.communication_manager),
                "websocket_server": bool(self.websocket_server)
            }
        }
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"🔧 更新配置: {key} = {value}")
    
    def register_event_handler(self, event_type: str, handler):
        """註冊事件處理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def emit_event(self, event_type: str, data: Any):
        """觸發事件"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data) if asyncio.iscoroutinefunction(handler) else handler(data)
                except Exception as e:
                    logger.error(f"事件處理器錯誤: {e}")