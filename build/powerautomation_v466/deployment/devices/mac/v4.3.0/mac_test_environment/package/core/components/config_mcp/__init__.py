"""
PowerAutomation 4.0 配置管理模块

这个模块提供统一的配置管理功能，支持多种配置源和动态配置更新。

主要组件：
- ConfigManager: 配置管理器
- EnvironmentManager: 环境管理器
- SecretManager: 密钥管理器
- ConfigValidator: 配置验证器
"""

from .config_manager import ConfigManager
from .environment_manager import EnvironmentManager
from .secret_manager import SecretManager
from .config_validator import ConfigValidator

__version__ = "4.0.0"
__author__ = "PowerAutomation Team"

__all__ = [
    "ConfigManager",
    "EnvironmentManager",
    "SecretManager",
    "ConfigValidator"
]

