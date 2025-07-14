"""
Platform Support Module - 跨平台终端MCP支持
支持 macOS、Windows、Linux、WSL 等多种平台

Author: Manus AI
Version: 1.0.0
Date: 2025-07-07
"""

from .platform_detector import PlatformDetector
from .command_adapter import CrossPlatformCommandAdapter
from .macos_terminal_mcp import MacOSTerminalMCP
from .windows_terminal_mcp import WindowsTerminalMCP
from .wsl_terminal_mcp import WSLTerminalMCP
from .linux_terminal_mcp import LinuxTerminalMCP

__version__ = "1.0.0"
__author__ = "Manus AI"

__all__ = [
    "PlatformDetector",
    "CrossPlatformCommandAdapter",
    "MacOSTerminalMCP",
    "WindowsTerminalMCP", 
    "WSLTerminalMCP",
    "LinuxTerminalMCP"
]

# 支持的平台列表
SUPPORTED_PLATFORMS = [
    "macos",
    "windows", 
    "linux",
    "wsl"
]

# 平台特定配置
PLATFORM_CONFIGS = {
    "macos": {
        "default_shell": "/bin/zsh",
        "package_manager": "brew",
        "terminal_apps": ["Terminal", "iTerm2", "Hyper", "Alacritty"],
        "capabilities": ["xcode", "codesign", "spotlight", "apple_silicon"]
    },
    "windows": {
        "default_shell": "powershell",
        "package_manager": "winget",
        "terminal_apps": ["Windows Terminal", "PowerShell", "Command Prompt", "Git Bash"],
        "capabilities": ["powershell", "dotnet", "visual_studio", "wsl_integration"]
    },
    "linux": {
        "default_shell": "/bin/bash",
        "package_manager": "auto_detect",  # 根据发行版自动检测
        "terminal_apps": ["gnome-terminal", "konsole", "xterm", "alacritty"],
        "capabilities": ["docker", "systemd", "package_managers", "containers"]
    },
    "wsl": {
        "default_shell": "/bin/bash",
        "package_manager": "apt",  # 通常是Ubuntu
        "terminal_apps": ["Windows Terminal", "WSL Terminal"],
        "capabilities": ["windows_integration", "file_bridge", "network_sharing", "dual_system"]
    }
}

