"""
Cross-Platform Command Adapter - 跨平台命令适配器
处理不同操作系统间的命令差异和转换

支持命令适配、路径转换、环境变量处理等
"""

import os
import re
import shlex
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path

class CrossPlatformCommandAdapter:
    """跨平台命令适配器"""
    
    def __init__(self, source_platform: str, target_platform: str):
        """
        初始化命令适配器
        
        Args:
            source_platform: 源平台 ('macos', 'windows', 'linux', 'wsl')
            target_platform: 目标平台 ('macos', 'windows', 'linux', 'wsl')
        """
        self.source_platform = source_platform.lower()
        self.target_platform = target_platform.lower()
        self.logger = logging.getLogger(__name__)
        
        # 命令映射表
        self.command_mappings = self._build_command_mappings()
        
        # 路径分隔符
        self.path_separators = {
            "windows": "\\",
            "macos": "/",
            "linux": "/",
            "wsl": "/"
        }
        
        self.logger.info(f"命令适配器初始化: {source_platform} -> {target_platform}")
    
    def _build_command_mappings(self) -> Dict[str, Dict[str, str]]:
        """构建命令映射表"""
        return {
            # 文件操作命令
            "file_operations": {
                "ls": {
                    "windows": "dir",
                    "macos": "ls",
                    "linux": "ls",
                    "wsl": "ls"
                },
                "cat": {
                    "windows": "type",
                    "macos": "cat",
                    "linux": "cat",
                    "wsl": "cat"
                },
                "cp": {
                    "windows": "copy",
                    "macos": "cp",
                    "linux": "cp",
                    "wsl": "cp"
                },
                "mv": {
                    "windows": "move",
                    "macos": "mv",
                    "linux": "mv",
                    "wsl": "mv"
                },
                "rm": {
                    "windows": "del",
                    "macos": "rm",
                    "linux": "rm",
                    "wsl": "rm"
                },
                "mkdir": {
                    "windows": "mkdir",
                    "macos": "mkdir",
                    "linux": "mkdir",
                    "wsl": "mkdir"
                },
                "rmdir": {
                    "windows": "rmdir",
                    "macos": "rmdir",
                    "linux": "rmdir",
                    "wsl": "rmdir"
                },
                "find": {
                    "windows": "where",
                    "macos": "find",
                    "linux": "find",
                    "wsl": "find"
                },
                "grep": {
                    "windows": "findstr",
                    "macos": "grep",
                    "linux": "grep",
                    "wsl": "grep"
                }
            },
            
            # 系统信息命令
            "system_info": {
                "ps": {
                    "windows": "tasklist",
                    "macos": "ps",
                    "linux": "ps",
                    "wsl": "ps"
                },
                "kill": {
                    "windows": "taskkill",
                    "macos": "kill",
                    "linux": "kill",
                    "wsl": "kill"
                },
                "top": {
                    "windows": "taskmgr",
                    "macos": "top",
                    "linux": "top",
                    "wsl": "top"
                },
                "df": {
                    "windows": "wmic logicaldisk get size,freespace,caption",
                    "macos": "df",
                    "linux": "df",
                    "wsl": "df"
                },
                "free": {
                    "windows": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory",
                    "macos": "vm_stat",
                    "linux": "free",
                    "wsl": "free"
                }
            },
            
            # 网络命令
            "network": {
                "ping": {
                    "windows": "ping",
                    "macos": "ping",
                    "linux": "ping",
                    "wsl": "ping"
                },
                "curl": {
                    "windows": "curl",
                    "macos": "curl",
                    "linux": "curl",
                    "wsl": "curl"
                },
                "wget": {
                    "windows": "curl -O",
                    "macos": "wget",
                    "linux": "wget",
                    "wsl": "wget"
                }
            },
            
            # 包管理命令
            "package_management": {
                "install": {
                    "windows": "winget install",
                    "macos": "brew install",
                    "linux": "apt install",  # 默认Ubuntu/Debian
                    "wsl": "apt install"
                },
                "uninstall": {
                    "windows": "winget uninstall",
                    "macos": "brew uninstall",
                    "linux": "apt remove",
                    "wsl": "apt remove"
                },
                "update": {
                    "windows": "winget upgrade",
                    "macos": "brew update && brew upgrade",
                    "linux": "apt update && apt upgrade",
                    "wsl": "apt update && apt upgrade"
                },
                "search": {
                    "windows": "winget search",
                    "macos": "brew search",
                    "linux": "apt search",
                    "wsl": "apt search"
                }
            },
            
            # 开发工具命令
            "development": {
                "git": {
                    "windows": "git",
                    "macos": "git",
                    "linux": "git",
                    "wsl": "git"
                },
                "node": {
                    "windows": "node",
                    "macos": "node",
                    "linux": "node",
                    "wsl": "node"
                },
                "npm": {
                    "windows": "npm",
                    "macos": "npm",
                    "linux": "npm",
                    "wsl": "npm"
                },
                "python": {
                    "windows": "python",
                    "macos": "python3",
                    "linux": "python3",
                    "wsl": "python3"
                },
                "pip": {
                    "windows": "pip",
                    "macos": "pip3",
                    "linux": "pip3",
                    "wsl": "pip3"
                }
            }
        }
    
    def adapt_command(self, command: str, args: Optional[List[str]] = None) -> Tuple[str, List[str]]:
        """
        适配命令到目标平台
        
        Args:
            command: 源命令
            args: 命令参数
            
        Returns:
            Tuple[str, List[str]]: (适配后的命令, 适配后的参数)
        """
        args = args or []
        
        # 查找命令映射
        adapted_command = self._find_command_mapping(command)
        adapted_args = self._adapt_arguments(command, args)
        
        self.logger.debug(f"命令适配: {command} {' '.join(args)} -> {adapted_command} {' '.join(adapted_args)}")
        
        return adapted_command, adapted_args
    
    def _find_command_mapping(self, command: str) -> str:
        """查找命令映射"""
        for category, mappings in self.command_mappings.items():
            if command in mappings:
                target_command = mappings[command].get(self.target_platform)
                if target_command:
                    return target_command
        
        # 如果没有找到映射，返回原命令
        return command
    
    def _adapt_arguments(self, command: str, args: List[str]) -> List[str]:
        """适配命令参数"""
        adapted_args = []
        
        for arg in args:
            # 适配路径
            if self._is_path_argument(arg):
                adapted_args.append(self._adapt_path(arg))
            # 适配参数格式
            elif self._is_option_argument(arg):
                adapted_args.append(self._adapt_option(command, arg))
            else:
                adapted_args.append(arg)
        
        return adapted_args
    
    def _is_path_argument(self, arg: str) -> bool:
        """判断参数是否是路径"""
        # 简单的路径判断逻辑
        return (
            "/" in arg or "\\" in arg or
            arg.startswith("./") or arg.startswith(".\\") or
            arg.startswith("~/") or arg.startswith("~\\") or
            ":" in arg  # Windows驱动器路径
        )
    
    def _is_option_argument(self, arg: str) -> bool:
        """判断参数是否是选项"""
        return arg.startswith("-") or arg.startswith("/")
    
    def _adapt_path(self, path: str) -> str:
        """适配路径格式"""
        # WSL特殊处理
        if self.source_platform == "wsl" and self.target_platform == "windows":
            return self._wsl_to_windows_path(path)
        elif self.source_platform == "windows" and self.target_platform == "wsl":
            return self._windows_to_wsl_path(path)
        
        # 一般路径分隔符转换
        source_sep = self.path_separators.get(self.source_platform, "/")
        target_sep = self.path_separators.get(self.target_platform, "/")
        
        if source_sep != target_sep:
            path = path.replace(source_sep, target_sep)
        
        return path
    
    def _wsl_to_windows_path(self, path: str) -> str:
        """WSL路径转Windows路径"""
        # /mnt/c/... -> C:\...
        if path.startswith("/mnt/"):
            parts = path.split("/")
            if len(parts) >= 3:
                drive = parts[2].upper()
                remaining = "/".join(parts[3:])
                return f"{drive}:\\{remaining.replace('/', '\\')}"
        
        # 其他情况保持不变
        return path
    
    def _windows_to_wsl_path(self, path: str) -> str:
        """Windows路径转WSL路径"""
        # C:\... -> /mnt/c/...
        if re.match(r"^[A-Za-z]:", path):
            drive = path[0].lower()
            remaining = path[2:].replace("\\", "/")
            return f"/mnt/{drive}{remaining}"
        
        # 其他情况保持不变
        return path
    
    def _adapt_option(self, command: str, option: str) -> str:
        """适配选项格式"""
        # Windows命令通常使用 /option 格式
        if self.target_platform == "windows":
            if option.startswith("-") and not option.startswith("--"):
                # 某些命令需要转换为 /option 格式
                if command in ["dir", "copy", "move", "del"]:
                    return "/" + option[1:]
        
        # Unix系统通常使用 -option 格式
        elif self.source_platform == "windows" and option.startswith("/"):
            return "-" + option[1:]
        
        return option
    
    def adapt_full_command_line(self, command_line: str) -> str:
        """
        适配完整的命令行
        
        Args:
            command_line: 完整的命令行字符串
            
        Returns:
            str: 适配后的命令行
        """
        # 解析命令行
        try:
            parts = shlex.split(command_line)
        except ValueError:
            # 如果解析失败，尝试简单分割
            parts = command_line.split()
        
        if not parts:
            return command_line
        
        command = parts[0]
        args = parts[1:]
        
        # 适配命令和参数
        adapted_command, adapted_args = self.adapt_command(command, args)
        
        # 重新组合命令行
        adapted_command_line = adapted_command
        if adapted_args:
            adapted_command_line += " " + " ".join(adapted_args)
        
        return adapted_command_line
    
    def get_environment_variables(self) -> Dict[str, str]:
        """获取目标平台的环境变量设置"""
        env_vars = {}
        
        if self.target_platform == "windows":
            env_vars.update({
                "PATH_SEPARATOR": ";",
                "LINE_ENDING": "\\r\\n",
                "SHELL": "cmd.exe",
                "HOME_VAR": "USERPROFILE"
            })
        else:  # Unix-like systems
            env_vars.update({
                "PATH_SEPARATOR": ":",
                "LINE_ENDING": "\\n",
                "SHELL": "/bin/bash",
                "HOME_VAR": "HOME"
            })
        
        return env_vars
    
    def adapt_script(self, script_content: str, script_type: str = "shell") -> str:
        """
        适配脚本内容
        
        Args:
            script_content: 脚本内容
            script_type: 脚本类型 ('shell', 'batch', 'powershell')
            
        Returns:
            str: 适配后的脚本内容
        """
        if script_type == "shell" and self.target_platform == "windows":
            # Shell脚本转换为批处理或PowerShell
            return self._shell_to_batch(script_content)
        elif script_type == "batch" and self.target_platform != "windows":
            # 批处理转换为Shell脚本
            return self._batch_to_shell(script_content)
        elif script_type == "powershell" and self.target_platform != "windows":
            # PowerShell转换为Shell脚本
            return self._powershell_to_shell(script_content)
        
        return script_content
    
    def _shell_to_batch(self, shell_script: str) -> str:
        """Shell脚本转批处理"""
        # 简单的转换逻辑
        lines = shell_script.split("\n")
        batch_lines = ["@echo off"]
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # 适配常见命令
            if line.startswith("ls"):
                batch_lines.append(line.replace("ls", "dir"))
            elif line.startswith("cat"):
                batch_lines.append(line.replace("cat", "type"))
            elif line.startswith("cp"):
                batch_lines.append(line.replace("cp", "copy"))
            elif line.startswith("mv"):
                batch_lines.append(line.replace("mv", "move"))
            elif line.startswith("rm"):
                batch_lines.append(line.replace("rm", "del"))
            else:
                batch_lines.append(line)
        
        return "\n".join(batch_lines)
    
    def _batch_to_shell(self, batch_script: str) -> str:
        """批处理转Shell脚本"""
        lines = batch_script.split("\n")
        shell_lines = ["#!/bin/bash"]
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("@") or line.startswith("rem"):
                continue
            
            # 适配常见命令
            if line.startswith("dir"):
                shell_lines.append(line.replace("dir", "ls"))
            elif line.startswith("type"):
                shell_lines.append(line.replace("type", "cat"))
            elif line.startswith("copy"):
                shell_lines.append(line.replace("copy", "cp"))
            elif line.startswith("move"):
                shell_lines.append(line.replace("move", "mv"))
            elif line.startswith("del"):
                shell_lines.append(line.replace("del", "rm"))
            else:
                shell_lines.append(line)
        
        return "\n".join(shell_lines)
    
    def _powershell_to_shell(self, powershell_script: str) -> str:
        """PowerShell转Shell脚本"""
        # 这是一个复杂的转换，这里只做简单处理
        lines = powershell_script.split("\n")
        shell_lines = ["#!/bin/bash"]
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # 适配一些基本的PowerShell命令
            if "Get-ChildItem" in line:
                shell_lines.append(line.replace("Get-ChildItem", "ls"))
            elif "Get-Content" in line:
                shell_lines.append(line.replace("Get-Content", "cat"))
            elif "Copy-Item" in line:
                shell_lines.append(line.replace("Copy-Item", "cp"))
            elif "Move-Item" in line:
                shell_lines.append(line.replace("Move-Item", "mv"))
            elif "Remove-Item" in line:
                shell_lines.append(line.replace("Remove-Item", "rm"))
            else:
                shell_lines.append(line)
        
        return "\n".join(shell_lines)
    
    def get_platform_specific_commands(self, category: str) -> Dict[str, str]:
        """
        获取平台特定的命令
        
        Args:
            category: 命令类别
            
        Returns:
            Dict: 平台特定命令字典
        """
        if category in self.command_mappings:
            result = {}
            for cmd, platforms in self.command_mappings[category].items():
                if self.target_platform in platforms:
                    result[cmd] = platforms[self.target_platform]
            return result
        
        return {}
    
    def is_command_available(self, command: str) -> bool:
        """检查命令在目标平台是否可用"""
        adapted_command, _ = self.adapt_command(command)
        
        # 这里可以添加更复杂的检查逻辑
        # 例如检查命令是否在PATH中
        import shutil
        return shutil.which(adapted_command) is not None
    
    def get_adaptation_summary(self) -> Dict[str, any]:
        """获取适配摘要信息"""
        return {
            "source_platform": self.source_platform,
            "target_platform": self.target_platform,
            "supported_categories": list(self.command_mappings.keys()),
            "path_separator_change": (
                self.path_separators.get(self.source_platform) != 
                self.path_separators.get(self.target_platform)
            ),
            "requires_script_adaptation": (
                (self.source_platform == "windows") != (self.target_platform == "windows")
            )
        }

