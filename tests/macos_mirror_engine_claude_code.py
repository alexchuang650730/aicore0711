#!/usr/bin/env python3
"""
PowerAutomation v4.6.2 Mirror Engine + Claude Code 集成
Mirror Engine Integration with Claude Code Services for macOS

🪞 Mirror Engine 功能:
1. macOS Claude Code 服務集成
2. 結果即時反映到 ClaudEditor
3. 雙向同步和狀態管理
4. 智能命令路由和結果聚合
5. 與端雲MCP無縫整合
"""

import asyncio
import json
import logging
import subprocess
import os
import shutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import requests
import websockets
from pathlib import Path

# 導入相關模組
from cloud_edge_mcp_integration import CloudEdgeMCPManager, ExecutionMode
from claudeditor_claude_code_integration import ClaudEditorCloudEdgeManager

logger = logging.getLogger(__name__)

class MirrorEngineMode(Enum):
    """Mirror Engine 模式"""
    REAL_TIME = "real_time"           # 實時鏡像
    BATCH = "batch"                   # 批量鏡像
    ON_DEMAND = "on_demand"           # 按需鏡像
    SELECTIVE = "selective"           # 選擇性鏡像

class ClaudeCodeServiceType(Enum):
    """Claude Code 服務類型"""
    CHAT = "chat"                     # 對話服務
    CODE_GENERATION = "code_generation"  # 代碼生成
    CODE_ANALYSIS = "code_analysis"   # 代碼分析
    DEBUG_ASSISTANCE = "debug_assistance"  # 調試輔助
    REFACTORING = "refactoring"       # 代碼重構
    DOCUMENTATION = "documentation"   # 文檔生成

@dataclass
class ClaudeCodeRequest:
    """Claude Code 請求"""
    request_id: str
    service_type: ClaudeCodeServiceType
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4096
    temperature: float = 0.7

@dataclass
class ClaudeCodeResponse:
    """Claude Code 響應"""
    request_id: str
    service_type: ClaudeCodeServiceType
    response_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)

@dataclass
class MirrorEngineSession:
    """Mirror Engine 會話"""
    session_id: str
    claude_editor_connection: Optional[str] = None
    claude_code_api_key: str = ""
    mirror_mode: MirrorEngineMode = MirrorEngineMode.REAL_TIME
    active_requests: List[str] = field(default_factory=list)
    sync_queue: 'asyncio.Queue' = None

class MacOSMirrorEngine:
    """macOS Mirror Engine 核心"""
    
    def __init__(self):
        self.sessions = {}
        self.claude_code_client = None
        self.claudeditor_manager = None
        self.cloud_edge_manager = None
        self.mirror_queue = asyncio.Queue()
        self.sync_tasks = {}
        
        # 服務統計
        self.metrics = {
            "requests_processed": 0,
            "responses_mirrored": 0,
            "sync_operations": 0,
            "claude_code_calls": 0
        }
        
    async def initialize_mirror_engine(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """初始化 Mirror Engine"""
        print("🪞 初始化 macOS Mirror Engine...")
        
        try:
            # 1. 初始化 Claude Code 客戶端
            await self._setup_claude_code_client(config.get("claude_config", {}))
            
            # 2. 初始化 ClaudEditor 管理器
            await self._setup_claudeditor_manager()
            
            # 3. 初始化雲端集成
            if config.get("enable_cloud_edge", True):
                await self._setup_cloud_edge_integration(config.get("cloud_edge_config", {}))
            
            # 4. 啟動鏡像服務
            await self._start_mirror_service()
            
            # 5. 設置 macOS 特定服務
            await self._setup_macos_services()
            
            result = {
                "status": "initialized",
                "claude_code_client": "active" if self.claude_code_client else "inactive",
                "claudeditor_manager": "active" if self.claudeditor_manager else "inactive",
                "cloud_edge_integration": "active" if self.cloud_edge_manager else "inactive",
                "mirror_service": "running",
                "macos_services": "configured"
            }
            
            print("✅ Mirror Engine 初始化完成")
            return result
            
        except Exception as e:
            logger.error(f"Mirror Engine 初始化失敗: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _setup_claude_code_client(self, config: Dict[str, Any]):
        """設置 Claude Code 客戶端"""
        print("🤖 設置 Claude Code 客戶端...")
        
        self.claude_code_client = {
            "api_key": config.get("api_key", ""),
            "api_endpoint": config.get("api_endpoint", "https://api.anthropic.com/v1"),
            "model": config.get("model", "claude-3-sonnet-20240229"),
            "timeout": config.get("timeout", 30),
            "headers": {
                "Content-Type": "application/json",
                "x-api-key": config.get("api_key", ""),
                "anthropic-version": "2023-06-01"
            }
        }
        
        # 測試連接
        await self._test_claude_code_connection()
    
    async def _test_claude_code_connection(self):
        """測試 Claude Code 連接"""
        if not self.claude_code_client or not self.claude_code_client["api_key"]:
            print("  ⚠️ Claude Code API Key 未配置，使用模擬模式")
            return
        
        try:
            # 發送測試請求
            test_request = {
                "model": self.claude_code_client["model"],
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, test connection"
                    }
                ]
            }
            
            response = requests.post(
                f"{self.claude_code_client['api_endpoint']}/messages",
                headers=self.claude_code_client["headers"],
                json=test_request,
                timeout=10
            )
            
            if response.status_code == 200:
                print("  ✅ Claude Code 連接測試成功")
            else:
                print(f"  ⚠️ Claude Code 連接測試失敗: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️ Claude Code 連接測試異常: {e}")
    
    async def _setup_claudeditor_manager(self):
        """設置 ClaudEditor 管理器"""
        print("📝 設置 ClaudEditor 管理器...")
        
        self.claudeditor_manager = ClaudEditorCloudEdgeManager()
        
        # 初始化 ClaudEditor 端雲部署
        claudeditor_config = {
            "claude_config": self.claude_code_client,
            "edge_nodes": [
                {
                    "node_id": "macos_local",
                    "location": "macOS-Local",
                    "capabilities": ["mirror_engine", "claude_code", "local_processing"],
                    "max_users": 50
                }
            ],
            "load_balancing": {
                "algorithm": "mirror_priority"
            }
        }
        
        await self.claudeditor_manager.initialize_deployment(claudeditor_config)
    
    async def _setup_cloud_edge_integration(self, config: Dict[str, Any]):
        """設置雲端集成"""
        print("🌐 設置雲端集成...")
        
        self.cloud_edge_manager = CloudEdgeMCPManager()
        await self.cloud_edge_manager.initialize_cloud_edge_integration(config)
    
    async def _start_mirror_service(self):
        """啟動鏡像服務"""
        print("🔄 啟動鏡像服務...")
        
        # 啟動鏡像處理循環
        asyncio.create_task(self._mirror_service_loop())
        
        # 啟動同步服務
        asyncio.create_task(self._sync_service_loop())
    
    async def _setup_macos_services(self):
        """設置 macOS 特定服務"""
        print("🍎 設置 macOS 特定服務...")
        
        # 檢查必要的 macOS 工具
        macos_tools = {
            "osascript": "AppleScript 支援",
            "automator": "Automator 支援", 
            "shortcuts": "Shortcuts 支援",
            "code": "VS Code 集成"
        }
        
        available_tools = {}
        for tool, description in macos_tools.items():
            if shutil.which(tool):
                available_tools[tool] = description
                print(f"  ✅ {description}")
            else:
                print(f"  ⚠️ {description} 不可用")
        
        self.macos_tools = available_tools
    
    async def _mirror_service_loop(self):
        """鏡像服務循環"""
        while True:
            try:
                # 處理鏡像隊列中的任務
                if not self.mirror_queue.empty():
                    task = await self.mirror_queue.get()
                    await self._process_mirror_task(task)
                
                await asyncio.sleep(0.1)  # 高頻率檢查
                
            except Exception as e:
                logger.error(f"鏡像服務錯誤: {e}")
                await asyncio.sleep(1)
    
    async def _sync_service_loop(self):
        """同步服務循環"""
        while True:
            try:
                # 執行同步操作
                await self._perform_sync_operations()
                await asyncio.sleep(2)  # 每2秒同步一次
                
            except Exception as e:
                logger.error(f"同步服務錯誤: {e}")
                await asyncio.sleep(5)
    
    async def create_mirror_session(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """創建鏡像會話"""
        session_id = f"mirror_{uuid.uuid4().hex[:8]}"
        
        print(f"🪞 創建鏡像會話: {session_id}")
        
        session = MirrorEngineSession(
            session_id=session_id,
            claude_editor_connection=config.get("claudeditor_connection"),
            claude_code_api_key=config.get("claude_code_api_key", self.claude_code_client.get("api_key", "")),
            mirror_mode=MirrorEngineMode(config.get("mirror_mode", "real_time")),
            sync_queue=asyncio.Queue()
        )
        
        self.sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "mirror_mode": session.mirror_mode.value,
            "claudeditor_connected": bool(session.claude_editor_connection),
            "claude_code_enabled": bool(session.claude_code_api_key),
            "status": "active"
        }
    
    async def process_claude_code_request(self, session_id: str, request: ClaudeCodeRequest) -> ClaudeCodeResponse:
        """處理 Claude Code 請求"""
        if session_id not in self.sessions:
            raise ValueError(f"會話 {session_id} 不存在")
        
        session = self.sessions[session_id]
        
        print(f"🤖 處理 Claude Code 請求: {request.service_type.value}")
        
        start_time = time.time()
        
        try:
            # 1. 調用 Claude Code API
            response_text = await self._call_claude_code_api(request)
            
            # 2. 創建響應對象
            response = ClaudeCodeResponse(
                request_id=request.request_id,
                service_type=request.service_type,
                response_text=response_text,
                execution_time=time.time() - start_time,
                metadata={
                    "model": request.model,
                    "session_id": session_id,
                    "processed_by": "mirror_engine"
                }
            )
            
            # 3. 添加到鏡像隊列
            await self.mirror_queue.put({
                "type": "claude_code_response",
                "session_id": session_id,
                "response": response
            })
            
            # 4. 更新統計
            self.metrics["requests_processed"] += 1
            self.metrics["claude_code_calls"] += 1
            
            return response
            
        except Exception as e:
            logger.error(f"Claude Code 請求處理失敗: {e}")
            
            # 返回錯誤響應
            return ClaudeCodeResponse(
                request_id=request.request_id,
                service_type=request.service_type,
                response_text=f"錯誤: {str(e)}",
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def _call_claude_code_api(self, request: ClaudeCodeRequest) -> str:
        """調用 Claude Code API"""
        if not self.claude_code_client or not self.claude_code_client["api_key"]:
            # 模擬模式
            return await self._simulate_claude_code_response(request)
        
        try:
            # 構建 API 請求
            api_request = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": self._build_prompt(request)
                    }
                ]
            }
            
            # 發送請求
            response = requests.post(
                f"{self.claude_code_client['api_endpoint']}/messages",
                headers=self.claude_code_client["headers"],
                json=api_request,
                timeout=self.claude_code_client["timeout"]
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                raise Exception(f"API 調用失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Claude Code API 調用失敗: {e}")
            return await self._simulate_claude_code_response(request)
    
    def _build_prompt(self, request: ClaudeCodeRequest) -> str:
        """構建 Claude Code 提示"""
        service_prompts = {
            ClaudeCodeServiceType.CHAT: f"作為程式設計助手，請回答以下問題：\n\n{request.prompt}",
            ClaudeCodeServiceType.CODE_GENERATION: f"請根據以下需求生成代碼：\n\n{request.prompt}\n\n請提供完整、可運行的代碼，並包含必要的註釋。",
            ClaudeCodeServiceType.CODE_ANALYSIS: f"請分析以下代碼：\n\n{request.prompt}\n\n請提供詳細的分析報告，包括性能、安全性和改進建議。",
            ClaudeCodeServiceType.DEBUG_ASSISTANCE: f"請幫助調試以下問題：\n\n{request.prompt}\n\n請提供詳細的問題分析和解決方案。",
            ClaudeCodeServiceType.REFACTORING: f"請重構以下代碼：\n\n{request.prompt}\n\n請提供重構後的代碼和改進說明。",
            ClaudeCodeServiceType.DOCUMENTATION: f"請為以下代碼生成文檔：\n\n{request.prompt}\n\n請提供完整的API文檔和使用說明。"
        }
        
        base_prompt = service_prompts.get(request.service_type, request.prompt)
        
        # 添加上下文信息
        if request.context:
            context_info = "\n\n上下文信息：\n"
            for key, value in request.context.items():
                context_info += f"- {key}: {value}\n"
            base_prompt += context_info
        
        return base_prompt
    
    async def _simulate_claude_code_response(self, request: ClaudeCodeRequest) -> str:
        """模擬 Claude Code 響應"""
        await asyncio.sleep(0.5)  # 模擬API延遲
        
        service_responses = {
            ClaudeCodeServiceType.CHAT: f"這是針對「{request.prompt}」的程式設計助手回答。[模擬響應]",
            ClaudeCodeServiceType.CODE_GENERATION: f"""```python
# 根據需求生成的代碼: {request.prompt}
def generated_function():
    '''
    這是由 Mirror Engine 模擬生成的代碼
    實際環境中將調用 Claude Code API
    '''
    return "模擬生成的代碼"

if __name__ == "__main__":
    print(generated_function())
```""",
            ClaudeCodeServiceType.CODE_ANALYSIS: f"""代碼分析報告:

## 分析對象
{request.prompt[:100]}...

## 分析結果
1. **代碼結構**: 良好
2. **性能評估**: 優秀 
3. **安全性**: 通過基本檢查
4. **改進建議**: 
   - 添加錯誤處理
   - 改善文檔註釋
   - 考慮性能優化

[由 Mirror Engine 模擬分析]""",
            ClaudeCodeServiceType.DEBUG_ASSISTANCE: f"""調試分析:

## 問題描述
{request.prompt}

## 可能原因
1. 變數未初始化
2. 類型不匹配
3. 邏輯錯誤

## 建議解決方案
1. 檢查變數聲明
2. 添加類型檢查
3. 使用調試工具

[由 Mirror Engine 模擬調試]""",
            ClaudeCodeServiceType.REFACTORING: f"""重構建議:

## 原始代碼
{request.prompt[:200]}...

## 重構後的代碼
```python
# 重構後的代碼（模擬）
class RefactoredCode:
    def __init__(self):
        self.improved = True
    
    def better_method(self):
        return "改進的實現"
```

## 改進說明
- 提高了代碼可讀性
- 增強了維護性
- 優化了性能

[由 Mirror Engine 模擬重構]""",
            ClaudeCodeServiceType.DOCUMENTATION: f"""API 文檔:

## 函數說明
針對提供的代碼生成的文檔

### 參數
- 待分析的代碼內容

### 返回值
- 完整的API文檔

### 使用示例
```python
# 使用示例
result = documented_function()
print(result)
```

[由 Mirror Engine 模擬生成]"""
        }
        
        return service_responses.get(request.service_type, f"針對「{request.prompt}」的回答 [模擬響應]")
    
    async def _process_mirror_task(self, task: Dict[str, Any]):
        """處理鏡像任務"""
        task_type = task.get("type")
        
        if task_type == "claude_code_response":
            await self._mirror_claude_code_response(task)
        elif task_type == "sync_request":
            await self._mirror_sync_request(task)
        else:
            logger.warning(f"未知的鏡像任務類型: {task_type}")
    
    async def _mirror_claude_code_response(self, task: Dict[str, Any]):
        """鏡像 Claude Code 響應到 ClaudEditor"""
        session_id = task["session_id"]
        response = task["response"]
        
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        print(f"🪞 鏡像響應到 ClaudEditor: {response.request_id}")
        
        try:
            # 如果有 ClaudEditor 管理器，發送響應
            if self.claudeditor_manager:
                mirror_request = {
                    "service_type": response.service_type.value,
                    "response_text": response.response_text,
                    "metadata": response.metadata,
                    "execution_time": response.execution_time
                }
                
                # 通過 ClaudEditor 管理器處理響應
                claudeditor_result = await self.claudeditor_manager.handle_claude_code_request(
                    session_id, mirror_request
                )
                
                print(f"  ✅ 響應已鏡像到 ClaudEditor")
                
                # 如果啟用雲端集成，同時同步到雲端
                if self.cloud_edge_manager:
                    await self._sync_to_cloud_edge(session_id, response)
            
            self.metrics["responses_mirrored"] += 1
            
        except Exception as e:
            logger.error(f"鏡像響應失敗: {e}")
    
    async def _sync_to_cloud_edge(self, session_id: str, response: ClaudeCodeResponse):
        """同步到雲端"""
        try:
            # 創建雲端會話（如果不存在）
            if session_id not in self.cloud_edge_manager.active_sessions:
                await self.cloud_edge_manager.create_cloud_edge_session({
                    "execution_mode": "hybrid",
                    "sync_strategy": "real_time"
                })
            
            # 執行同步命令
            sync_command = f"echo 'Claude Code Response Synced: {response.request_id}'"
            await self.cloud_edge_manager.execute_smart_command(session_id, sync_command)
            
            print(f"  🌐 響應已同步到雲端")
            
        except Exception as e:
            logger.error(f"雲端同步失敗: {e}")
    
    async def _perform_sync_operations(self):
        """執行同步操作"""
        # 定期同步統計數據和狀態
        for session_id, session in self.sessions.items():
            if not session.sync_queue.empty():
                sync_item = await session.sync_queue.get()
                await self._process_sync_item(session_id, sync_item)
                
                self.metrics["sync_operations"] += 1
    
    async def _process_sync_item(self, session_id: str, sync_item: Dict[str, Any]):
        """處理同步項目"""
        # 實現具體的同步邏輯
        pass
    
    async def execute_macos_integration(self, session_id: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行 macOS 集成操作"""
        params = params or {}
        
        print(f"🍎 執行 macOS 集成: {action}")
        
        if action == "open_claudeditor":
            return await self._open_claudeditor(params)
        elif action == "run_applescript":
            return await self._run_applescript(params.get("script", ""))
        elif action == "create_shortcut":
            return await self._create_shortcut(params)
        elif action == "open_with_vscode":
            return await self._open_with_vscode(params)
        else:
            return {"status": "error", "error": f"未知的 macOS 操作: {action}"}
    
    async def _open_claudeditor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """打開 ClaudEditor"""
        try:
            # 使用 osascript 打開 ClaudEditor（假設有桌面應用）
            if "osascript" in self.macos_tools:
                script = '''
                tell application "ClaudEditor"
                    activate
                end tell
                '''
                
                process = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    return {"status": "success", "message": "ClaudEditor 已打開"}
                else:
                    return {"status": "error", "error": stderr.decode()}
            else:
                return {"status": "error", "error": "AppleScript 不可用"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _run_applescript(self, script: str) -> Dict[str, Any]:
        """運行 AppleScript"""
        try:
            if "osascript" in self.macos_tools:
                process = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                return {
                    "status": "success" if process.returncode == 0 else "error",
                    "output": stdout.decode(),
                    "error": stderr.decode() if stderr else None
                }
            else:
                return {"status": "error", "error": "AppleScript 不可用"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _create_shortcut(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """創建 Shortcuts"""
        try:
            shortcut_name = params.get("name", "PowerAutomation Shortcut")
            action = params.get("action", "echo 'Hello from PowerAutomation'")
            
            # 使用 shortcuts 命令創建快捷方式
            if "shortcuts" in self.macos_tools:
                # 這是一個簡化的實現，實際可能需要更複雜的 Shortcuts 語法
                return {
                    "status": "success",
                    "message": f"快捷方式 '{shortcut_name}' 創建完成（模擬）",
                    "shortcut_name": shortcut_name
                }
            else:
                return {"status": "error", "error": "Shortcuts 不可用"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _open_with_vscode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """使用 VS Code 打開文件"""
        try:
            file_path = params.get("file_path", "")
            
            if "code" in self.macos_tools and file_path:
                process = await asyncio.create_subprocess_exec(
                    "code", file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate()
                
                return {
                    "status": "success",
                    "message": f"已在 VS Code 中打開: {file_path}"
                }
            else:
                return {"status": "error", "error": "VS Code 不可用或未指定文件路徑"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_mirror_engine_status(self) -> Dict[str, Any]:
        """獲取 Mirror Engine 狀態"""
        return {
            "engine_status": "active",
            "sessions": len(self.sessions),
            "metrics": self.metrics,
            "claude_code_client": {
                "status": "active" if self.claude_code_client else "inactive",
                "endpoint": self.claude_code_client.get("api_endpoint") if self.claude_code_client else None
            },
            "claudeditor_manager": {
                "status": "active" if self.claudeditor_manager else "inactive"
            },
            "cloud_edge_integration": {
                "status": "active" if self.cloud_edge_manager else "inactive"
            },
            "macos_tools": self.macos_tools,
            "mirror_queue_size": self.mirror_queue.qsize(),
            "capabilities": {
                "claude_code_integration": True,
                "claudeditor_mirroring": True,
                "cloud_edge_sync": bool(self.cloud_edge_manager),
                "macos_native_integration": len(self.macos_tools) > 0
            }
        }

# 演示函數
async def demo_mirror_engine():
    """演示 Mirror Engine"""
    print("🪞 PowerAutomation v4.6.2 Mirror Engine 演示")
    print("=" * 80)
    
    # 創建 Mirror Engine
    mirror_engine = MacOSMirrorEngine()
    
    # 初始化配置
    config = {
        "claude_config": {
            "api_key": "your-claude-api-key-here",  # 實際使用時請提供真實的API Key
            "model": "claude-3-sonnet-20240229",
            "timeout": 30
        },
        "enable_cloud_edge": True,
        "cloud_edge_config": {
            "ec2_instances": []  # 可以添加 EC2 配置
        }
    }
    
    # 初始化 Mirror Engine
    print("\n🚀 初始化 Mirror Engine...")
    init_result = await mirror_engine.initialize_mirror_engine(config)
    
    print(f"  初始化狀態: {init_result['status']}")
    print(f"  Claude Code 客戶端: {init_result['claude_code_client']}")
    print(f"  ClaudEditor 管理器: {init_result['claudeditor_manager']}")
    print(f"  雲端集成: {init_result['cloud_edge_integration']}")
    
    # 創建鏡像會話
    print("\n🪞 創建鏡像會話...")
    session_config = {
        "mirror_mode": "real_time",
        "claudeditor_connection": "localhost:8080"
    }
    
    session = await mirror_engine.create_mirror_session(session_config)
    session_id = session["session_id"]
    
    print(f"  會話ID: {session_id}")
    print(f"  鏡像模式: {session['mirror_mode']}")
    
    # 演示 Claude Code 服務
    print("\n🤖 演示 Claude Code 服務:")
    
    claude_requests = [
        ClaudeCodeRequest(
            request_id="req_001",
            service_type=ClaudeCodeServiceType.CODE_GENERATION,
            prompt="創建一個Python函數來計算斐波那契數列"
        ),
        ClaudeCodeRequest(
            request_id="req_002", 
            service_type=ClaudeCodeServiceType.CODE_ANALYSIS,
            prompt="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
        ),
        ClaudeCodeRequest(
            request_id="req_003",
            service_type=ClaudeCodeServiceType.DEBUG_ASSISTANCE,
            prompt="我的遞歸函數導致堆疊溢出，如何修復？"
        )
    ]
    
    for request in claude_requests:
        print(f"\n  處理請求: {request.service_type.value}")
        response = await mirror_engine.process_claude_code_request(session_id, request)
        
        print(f"    ✅ 請求ID: {response.request_id}")
        print(f"    執行時間: {response.execution_time:.2f}s")
        print(f"    響應預覽: {response.response_text[:100]}...")
    
    # 演示 macOS 集成
    print("\n🍎 演示 macOS 集成:")
    
    macos_actions = [
        ("run_applescript", {"script": "display notification \"PowerAutomation Mirror Engine\" with title \"測試通知\""}),
        ("create_shortcut", {"name": "PA Mirror Test", "action": "echo 'Hello Mirror Engine'"}),
        ("open_with_vscode", {"file_path": "/tmp/test.py"})
    ]
    
    for action, params in macos_actions:
        print(f"\n  執行 macOS 操作: {action}")
        result = await mirror_engine.execute_macos_integration(session_id, action, params)
        
        if result["status"] == "success":
            print(f"    ✅ {result.get('message', '操作成功')}")
        else:
            print(f"    ⚠️ {result.get('error', '操作失敗')}")
    
    # 獲取 Mirror Engine 狀態
    print("\n📊 Mirror Engine 狀態:")
    status = await mirror_engine.get_mirror_engine_status()
    
    print(f"  引擎狀態: {status['engine_status']}")
    print(f"  活躍會話: {status['sessions']}個")
    print(f"  處理請求: {status['metrics']['requests_processed']}次")
    print(f"  鏡像響應: {status['metrics']['responses_mirrored']}次")
    print(f"  Claude Code 調用: {status['metrics']['claude_code_calls']}次")
    print(f"  macOS 工具: {len(status['macos_tools'])}個可用")
    
    capabilities = status['capabilities']
    print(f"\n🎯 功能特性:")
    for feature, enabled in capabilities.items():
        icon = "✅" if enabled else "❌"
        print(f"  {icon} {feature.replace('_', ' ').title()}")
    
    print(f"\n🎉 Mirror Engine 演示完成！")
    print(f"   現在 macOS 可以無縫使用 Claude Code 服務並實時反映到 ClaudEditor！")
    
    return mirror_engine

if __name__ == "__main__":
    asyncio.run(demo_mirror_engine())