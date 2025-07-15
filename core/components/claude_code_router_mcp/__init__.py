"""
Claude Code Router MCP - 多AI模型智能路由系統
PowerAutomation v4.6.9.4 核心競爭優勢組件

支持的AI模型:
- Claude (Anthropic API)
- OpenAI GPT-4 (OpenAI API)
- Gemini (Google AI API)
- Kimi K2 (Moonshot AI API)

核心功能:
- 統一API接口
- 智能模型路由
- 負載均衡
- 請求緩存
- 成本優化
- 監控日誌
"""

from .router import ClaudeCodeRouterMCP
from .config import RouterConfig
from .models import SupportedModel, ModelProvider
from .utils import RouterUtils

__all__ = [
    'ClaudeCodeRouterMCP',
    'RouterConfig',
    'SupportedModel',
    'ModelProvider',
    'RouterUtils'
]

__version__ = "4.6.9.4"