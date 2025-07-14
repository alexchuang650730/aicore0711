"""
PowerAutomation 4.0 安全模块

这个模块提供完整的企业级安全保障，包括认证、授权、安全管理和令牌管理。

主要组件：
- MCPAuthenticator: MCP认证管理器
- MCPAuthorizer: MCP授权控制器
- MCPSecurityManager: MCP安全管理器
- MCPTokenManager: MCP令牌管理器
- SecurityAuditor: 安全审计器
"""

from .authenticator import MCPAuthenticator
from .authorizer import MCPAuthorizer
from .security_manager import MCPSecurityManager
from .token_manager import MCPTokenManager
from .security_auditor import SecurityAuditor

__version__ = "4.0.0"
__author__ = "PowerAutomation Team"

__all__ = [
    "MCPAuthenticator",
    "MCPAuthorizer", 
    "MCPSecurityManager",
    "MCPTokenManager",
    "SecurityAuditor"
]

