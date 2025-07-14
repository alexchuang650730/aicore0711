"""
Intelligent Error Handler MCP
智能錯誤處理系統 - PowerAutomation核心競爭優勢組件
"""

from .error_handler import (
    intelligent_error_handler_mcp,
    IntelligentErrorHandlerMCP,
    ErrorDetail,
    ErrorFix,
    ProjectHealthReport,
    ErrorSeverity,
    ErrorCategory,
    FixConfidence
)

__all__ = [
    'intelligent_error_handler_mcp',
    'IntelligentErrorHandlerMCP',
    'ErrorDetail',
    'ErrorFix', 
    'ProjectHealthReport',
    'ErrorSeverity',
    'ErrorCategory',
    'FixConfidence'
]

__version__ = "4.6.1"
__component__ = "Intelligent Error Handler MCP"