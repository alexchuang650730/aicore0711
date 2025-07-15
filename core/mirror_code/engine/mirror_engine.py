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
    claude_integration: bool = False  # 已禁用Claude
    k2_integration: bool = True  # 啟用K2
    local_adapters: List[str] = None
    remote_endpoints: List[Dict[str, Any]] = None
    # K2特定配置
    ai_integration: Dict[str, Any] = None
    routing_strategy: Dict[str, Any] = None
    migration_info: Dict[str, Any] = None

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
        
        # 加載K2配置
        self._load_k2_config()
        
        print(f"🪞 Mirror Engine 已創建: {self.session_id}")
        print(f"🤖 AI集成模式: {'K2' if self.config.k2_integration else 'Claude' if self.config.claude_integration else 'None'}")
    
    def _load_k2_config(self):
        """加載K2配置"""
        try:
            import json
            import os
            
            config_path = "mirror_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                # 更新配置
                if 'ai_integration' in config_data:
                    self.config.ai_integration = config_data['ai_integration']
                
                if 'routing_strategy' in config_data:
                    self.config.routing_strategy = config_data['routing_strategy']
                
                if 'migration_info' in config_data:
                    self.config.migration_info = config_data['migration_info']
                
                # 確保K2集成啟用，Claude集成禁用
                self.config.k2_integration = config_data.get('k2_integration', True)
                self.config.claude_integration = config_data.get('claude_integration', False)
                
                print(f"✅ K2配置已加載: {self.config.ai_integration.get('provider', 'unknown') if self.config.ai_integration else 'none'}")
                
        except Exception as e:
            logger.warning(f"加載K2配置失敗: {e}")
            # 使用默認K2配置
            self.config.ai_integration = {
                "provider": "kimi-k2",
                "service_type": "infini-ai-cloud",
                "model": "kimi-k2-instruct",
                "api_endpoint": "http://localhost:8765"
            }
    
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
            
            # 3. 初始化AI集成（K2或Claude）
            await self._initialize_ai_integration()
            
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
    
    async def _initialize_ai_integration(self):
        """初始化AI集成（優先K2）"""
        if self.config.k2_integration:
            print("  🤖 初始化K2集成...")
            await self._initialize_k2_integration()
        elif self.config.claude_integration:
            print("  🤖 初始化Claude集成（已棄用）...")
            await self._initialize_claude_integration()
        else:
            print("  ⚠️ 未啟用AI集成")
    
    async def _initialize_k2_integration(self):
        """初始化K2集成"""
        try:
            from ..command_execution.claude_integration import ClaudeIntegration
            
            # 重用ClaudeIntegration類但配置為使用K2
            self.k2_integration = ClaudeIntegration()
            
            # 確保使用K2配置
            if hasattr(self.k2_integration, 'config'):
                self.k2_integration.config = {
                    "provider": "kimi-k2",
                    "api_endpoint": self.config.ai_integration.get('api_endpoint', 'http://localhost:8765'),
                    "model": self.config.ai_integration.get('model', 'kimi-k2-instruct'),
                    "use_k2": True
                }
            
            await self.k2_integration.initialize()
            print(f"✅ K2集成初始化完成: {self.config.ai_integration.get('provider', 'kimi-k2')}")
            
        except Exception as e:
            logger.error(f"K2集成初始化失敗: {e}")
            # 創建基本K2集成
            self.k2_integration = type('K2Integration', (), {
                'execute_command': self._basic_k2_execute,
                'get_status': lambda: {"initialized": True, "provider": "kimi-k2"}
            })()
    
    async def _basic_k2_execute(self, prompt: str):
        """基本K2執行方法"""
        # 直接調用K2服務
        import aiohttp
        
        try:
            payload = {
                "model": "kimi-k2-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8765/v1/chat/completions",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {
                            "success": True,
                            "output": content,
                            "provider": "kimi-k2-via-mirror"
                        }
                    else:
                        return {"success": False, "error": f"K2服務錯誤: {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _initialize_claude_integration(self):
        """初始化Claude集成（已棄用）"""
        print("  ⚠️ Claude集成已棄用，請使用K2集成")
        
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
    
    async def execute_ai_command(self, prompt: str) -> Dict[str, Any]:
        """執行AI命令（優先K2）"""
        if self.config.k2_integration and hasattr(self, 'k2_integration'):
            try:
                result = await self.k2_integration.execute_command(prompt)
                # 添加K2標識
                if isinstance(result, dict):
                    result["ai_provider"] = "kimi-k2"
                    result["via_mirror"] = True
                return result
            except Exception as e:
                logger.error(f"K2命令執行失敗: {e}")
                return {"error": str(e), "ai_provider": "kimi-k2", "failed": True}
        
        elif self.config.claude_integration and hasattr(self, 'claude_integration'):
            logger.warning("⚠️ 使用已棄用的Claude集成")
            try:
                result = await self.claude_integration.execute_command(prompt)
                if isinstance(result, dict):
                    result["ai_provider"] = "claude"
                    result["deprecated_warning"] = True
                return result
            except Exception as e:
                logger.error(f"Claude命令執行失敗: {e}")
                return {"error": str(e), "ai_provider": "claude", "failed": True}
        
        else:
            return {"error": "AI集成未啟用或未初始化"}
    
    async def execute_claude_command(self, prompt: str) -> Dict[str, Any]:
        """執行Claude命令（已棄用，重定向到K2）"""
        logger.warning("⚠️ execute_claude_command已棄用，請使用execute_ai_command")
        return await self.execute_ai_command(prompt)
    
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
                "claude_integration": self.config.claude_integration,
                "k2_integration": self.config.k2_integration,
                "ai_provider": self.config.ai_integration.get('provider', 'none') if self.config.ai_integration else 'none'
            },
            "components": {
                "local_adapter_integration": bool(self.local_adapter_integration),
                "result_capture": bool(self.result_capture),
                "claude_integration": bool(getattr(self, 'claude_integration', None)),
                "k2_integration": bool(getattr(self, 'k2_integration', None)),
                "sync_manager": bool(self.sync_manager),
                "communication_manager": bool(self.communication_manager),
                "websocket_server": bool(self.websocket_server)
            },
            "ai_integration_status": {
                "primary_provider": "kimi-k2" if self.config.k2_integration else "claude" if self.config.claude_integration else "none",
                "migration_status": self.config.migration_info.get('migration_status', 'unknown') if self.config.migration_info else 'unknown',
                "k2_enabled": self.config.k2_integration,
                "claude_enabled": self.config.claude_integration,
                "routing_strategy": self.config.routing_strategy.get('primary', 'unknown') if self.config.routing_strategy else 'unknown'
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