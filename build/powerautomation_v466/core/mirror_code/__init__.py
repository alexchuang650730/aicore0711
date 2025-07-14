"""
PowerAutomation v4.6.2 Mirror Code System
完整的Mirror Code系統，提供端雲協同開發體驗

🪞 Mirror Code組件:
├── engine/                     # 核心引擎
├── command_execution/          # 命令執行
├── sync/                      # 同步管理
├── communication/             # 通信管理
└── launch_mirror.py           # 啟動腳本

Mirror Code系統整合了本地適配器、雲端集成、Claude Code服務等功能，
提供統一的開發體驗和實時的結果鏡像。
"""

from .engine.mirror_engine import MirrorEngine
from .command_execution.local_adapter_integration import LocalAdapterIntegration
from .command_execution.result_capture import ResultCapture
from .command_execution.claude_integration import ClaudeIntegration
from .sync.sync_manager import SyncManager
from .communication.comm_manager import CommunicationManager

__version__ = "4.6.2"
__all__ = [
    "MirrorEngine",
    "LocalAdapterIntegration", 
    "ResultCapture",
    "ClaudeIntegration",
    "SyncManager",
    "CommunicationManager"
]