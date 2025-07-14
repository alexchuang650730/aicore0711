"""
WSL Terminal MCP Adapter - WSL终端MCP适配器
支持Windows Subsystem for Linux的特殊功能

特性：双系统环境、文件桥接、网络共享、Windows集成等
"""

import asyncio
import subprocess
import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

class WSLTerminalMCP:
    """WSL终端MCP适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.platform = "wsl"
        
        # 检查WSL环境
        self.is_wsl = self._check_wsl_environment()
        self.wsl_version = self._get_wsl_version()
        self.distribution = self._get_distribution()
        self.windows_fs_accessible = self._check_windows_fs_access()
        self.windows_exe_accessible = self._check_windows_exe_access()
        
        # 检查Linux工具
        self.package_manager = self._detect_package_manager()
        self.docker_available = self._check_docker()
        
        self.logger.info(f"WSL终端MCP初始化完成 - 发行版: {self.distribution}, WSL版本: {self.wsl_version}, Windows文件系统: {self.windows_fs_accessible}")
    
    def _check_wsl_environment(self) -> bool:
        """检查是否在WSL环境中"""
        try:
            # 检查 /proc/version
            if os.path.exists("/proc/version"):
                with open("/proc/version", "r") as f:
                    version_info = f.read().lower()
                    if "microsoft" in version_info or "wsl" in version_info:
                        return True
            
            # 检查环境变量
            if "WSL_DISTRO_NAME" in os.environ:
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"WSL环境检测失败: {e}")
            return False
    
    def _get_wsl_version(self) -> str:
        """获取WSL版本"""
        try:
            if "WSL_INTEROP" in os.environ:
                return "2"
            elif self.is_wsl:
                return "1"
            else:
                return "unknown"
        except Exception:
            return "unknown"
    
    def _get_distribution(self) -> str:
        """获取WSL发行版名称"""
        try:
            # 从环境变量获取
            if "WSL_DISTRO_NAME" in os.environ:
                return os.environ["WSL_DISTRO_NAME"]
            
            # 从 /etc/os-release 获取
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("ID="):
                            return line.split("=")[1].strip().strip('"')
            
            return "unknown"
            
        except Exception as e:
            self.logger.debug(f"获取发行版信息失败: {e}")
            return "unknown"
    
    def _check_windows_fs_access(self) -> bool:
        """检查Windows文件系统访问"""
        return os.path.exists("/mnt/c")
    
    def _check_windows_exe_access(self) -> bool:
        """检查Windows可执行文件访问"""
        try:
            result = subprocess.run(["cmd.exe", "/c", "echo test"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _detect_package_manager(self) -> str:
        """检测包管理器"""
        managers = {
            "apt": ["apt", "apt-get"],
            "yum": ["yum"],
            "dnf": ["dnf"],
            "pacman": ["pacman"],
            "zypper": ["zypper"]
        }
        
        for manager, commands in managers.items():
            for cmd in commands:
                try:
                    result = subprocess.run(["which", cmd], 
                                          capture_output=True, timeout=2)
                    if result.returncode == 0:
                        return manager
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        
        return "unknown"
    
    def _check_docker(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def execute_command(self, command: str, args: List[str] = None, 
                            working_dir: str = None, env: Dict[str, str] = None) -> Dict[str, Any]:
        """
        执行WSL命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            
        Returns:
            Dict: 执行结果
        """
        args = args or []
        full_command = [command] + args
        
        try:
            self.logger.info(f"执行WSL命令: {' '.join(full_command)}")
            
            # 设置环境变量
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=exec_env
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": ' '.join(full_command),
                "working_dir": working_dir
            }
            
            if process.returncode != 0:
                self.logger.warning(f"命令执行失败: {result['stderr']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(full_command),
                "working_dir": working_dir
            }
    
    # Windows集成方法
    async def execute_windows_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """在WSL中执行Windows命令"""
        if not self.windows_exe_accessible:
            return {"success": False, "error": "Windows可执行文件不可访问"}
        
        args = args or []
        
        # 添加.exe后缀（如果需要）
        if not command.endswith(".exe"):
            command += ".exe"
        
        return await self.execute_command(command, args)
    
    async def access_windows_file(self, windows_path: str, operation: str = "read") -> Dict[str, Any]:
        """访问Windows文件系统"""
        if not self.windows_fs_accessible:
            return {"success": False, "error": "Windows文件系统不可访问"}
        
        try:
            # 转换Windows路径到WSL路径
            wsl_path = self._windows_to_wsl_path(windows_path)
            
            if operation == "read":
                return await self.execute_command("cat", [wsl_path])
            elif operation == "list":
                return await self.execute_command("ls", ["-la", wsl_path])
            elif operation == "exists":
                result = await self.execute_command("test", ["-e", wsl_path])
                return {
                    "success": True,
                    "exists": result["returncode"] == 0,
                    "path": wsl_path
                }
            else:
                return {"success": False, "error": f"不支持的操作: {operation}"}
                
        except Exception as e:
            self.logger.error(f"访问Windows文件失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _windows_to_wsl_path(self, windows_path: str) -> str:
        """将Windows路径转换为WSL路径"""
        # C:\path\to\file -> /mnt/c/path/to/file
        if windows_path.startswith("C:"):
            return windows_path.replace("C:", "/mnt/c").replace("\\", "/")
        elif windows_path.startswith("D:"):
            return windows_path.replace("D:", "/mnt/d").replace("\\", "/")
        elif len(windows_path) >= 2 and windows_path[1] == ":":
            drive = windows_path[0].lower()
            return windows_path.replace(f"{windows_path[0]}:", f"/mnt/{drive}").replace("\\", "/")
        else:
            return windows_path
    
    def _wsl_to_windows_path(self, wsl_path: str) -> str:
        """将WSL路径转换为Windows路径"""
        # /mnt/c/path/to/file -> C:\path\to\file
        if wsl_path.startswith("/mnt/"):
            parts = wsl_path.split("/")
            if len(parts) >= 3:
                drive = parts[2].upper()
                remaining = "/".join(parts[3:])
                return f"{drive}:\\{remaining.replace('/', '\\')}"
        return wsl_path
    
    # 包管理方法
    async def install_package(self, package: str, update_first: bool = True) -> Dict[str, Any]:
        """安装软件包"""
        if self.package_manager == "unknown":
            return {"success": False, "error": "未检测到包管理器"}
        
        results = {}
        
        # 先更新包列表
        if update_first:
            if self.package_manager == "apt":
                update_result = await self.execute_command("sudo", ["apt", "update"])
                results["update"] = update_result
        
        # 安装包
        if self.package_manager == "apt":
            install_result = await self.execute_command("sudo", ["apt", "install", "-y", package])
        elif self.package_manager == "yum":
            install_result = await self.execute_command("sudo", ["yum", "install", "-y", package])
        elif self.package_manager == "dnf":
            install_result = await self.execute_command("sudo", ["dnf", "install", "-y", package])
        elif self.package_manager == "pacman":
            install_result = await self.execute_command("sudo", ["pacman", "-S", "--noconfirm", package])
        else:
            install_result = {"success": False, "error": f"不支持的包管理器: {self.package_manager}"}
        
        results["install"] = install_result
        return {"success": install_result.get("success", False), "results": results}
    
    async def remove_package(self, package: str) -> Dict[str, Any]:
        """卸载软件包"""
        if self.package_manager == "unknown":
            return {"success": False, "error": "未检测到包管理器"}
        
        if self.package_manager == "apt":
            return await self.execute_command("sudo", ["apt", "remove", "-y", package])
        elif self.package_manager == "yum":
            return await self.execute_command("sudo", ["yum", "remove", "-y", package])
        elif self.package_manager == "dnf":
            return await self.execute_command("sudo", ["dnf", "remove", "-y", package])
        elif self.package_manager == "pacman":
            return await self.execute_command("sudo", ["pacman", "-R", "--noconfirm", package])
        else:
            return {"success": False, "error": f"不支持的包管理器: {self.package_manager}"}
    
    async def search_package(self, query: str) -> Dict[str, Any]:
        """搜索软件包"""
        if self.package_manager == "unknown":
            return {"success": False, "error": "未检测到包管理器"}
        
        if self.package_manager == "apt":
            return await self.execute_command("apt", ["search", query])
        elif self.package_manager == "yum":
            return await self.execute_command("yum", ["search", query])
        elif self.package_manager == "dnf":
            return await self.execute_command("dnf", ["search", query])
        elif self.package_manager == "pacman":
            return await self.execute_command("pacman", ["-Ss", query])
        else:
            return {"success": False, "error": f"不支持的包管理器: {self.package_manager}"}
    
    # Docker方法
    async def docker_run(self, image: str, command: str = None, 
                        ports: List[str] = None, volumes: List[str] = None,
                        detach: bool = False) -> Dict[str, Any]:
        """运行Docker容器"""
        if not self.docker_available:
            return {"success": False, "error": "Docker不可用"}
        
        args = ["run"]
        
        if detach:
            args.append("-d")
        
        if ports:
            for port in ports:
                args.extend(["-p", port])
        
        if volumes:
            for volume in volumes:
                args.extend(["-v", volume])
        
        args.append(image)
        
        if command:
            args.extend(command.split())
        
        return await self.execute_command("docker", args)
    
    async def docker_build(self, dockerfile_path: str, tag: str, 
                          context_path: str = ".") -> Dict[str, Any]:
        """构建Docker镜像"""
        if not self.docker_available:
            return {"success": False, "error": "Docker不可用"}
        
        args = ["build", "-f", dockerfile_path, "-t", tag, context_path]
        return await self.execute_command("docker", args)
    
    async def docker_ps(self, all_containers: bool = False) -> Dict[str, Any]:
        """列出Docker容器"""
        if not self.docker_available:
            return {"success": False, "error": "Docker不可用"}
        
        args = ["ps"]
        if all_containers:
            args.append("-a")
        
        return await self.execute_command("docker", args)
    
    # 开发环境方法
    async def setup_development_environment(self, tools: List[str]) -> Dict[str, Any]:
        """设置开发环境"""
        results = {}
        
        for tool in tools:
            if tool == "docker" and not self.docker_available:
                # 安装Docker
                if self.package_manager == "apt":
                    # Ubuntu/Debian Docker安装
                    commands = [
                        ["sudo", "apt", "update"],
                        ["sudo", "apt", "install", "-y", "apt-transport-https", "ca-certificates", "curl", "gnupg", "lsb-release"],
                        ["curl", "-fsSL", "https://download.docker.com/linux/ubuntu/gpg", "|", "sudo", "gpg", "--dearmor", "-o", "/usr/share/keyrings/docker-archive-keyring.gpg"],
                        ["sudo", "apt", "update"],
                        ["sudo", "apt", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io"]
                    ]
                    
                    docker_results = []
                    for cmd in commands:
                        result = await self.execute_command(cmd[0], cmd[1:])
                        docker_results.append(result)
                    
                    results["docker"] = {"success": True, "steps": docker_results}
                else:
                    results["docker"] = {"success": False, "error": f"不支持在{self.package_manager}上自动安装Docker"}
            
            elif tool in ["git", "node", "python3", "pip3", "curl", "wget", "vim", "nano"]:
                # 使用包管理器安装常用工具
                result = await self.install_package(tool, update_first=False)
                results[tool] = result
            
            elif tool == "nvm":
                # 安装Node Version Manager
                script = "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
                result = await self.execute_command("bash", ["-c", script])
                results["nvm"] = result
            
            elif tool == "pyenv":
                # 安装Python Version Manager
                script = "curl https://pyenv.run | bash"
                result = await self.execute_command("bash", ["-c", script])
                results["pyenv"] = result
        
        return {"success": True, "results": results}
    
    async def get_system_info(self) -> Dict[str, Any]:
        """获取WSL系统信息"""
        try:
            info = {
                "platform": "wsl",
                "is_wsl": self.is_wsl,
                "wsl_version": self.wsl_version,
                "distribution": self.distribution,
                "package_manager": self.package_manager,
                "windows_fs_accessible": self.windows_fs_accessible,
                "windows_exe_accessible": self.windows_exe_accessible,
                "docker_available": self.docker_available
            }
            
            # 获取Linux发行版信息
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            info["distribution_name"] = line.split("=")[1].strip().strip('"')
                        elif line.startswith("VERSION_ID="):
                            info["distribution_version"] = line.split("=")[1].strip().strip('"')
            
            # 获取内核信息
            kernel_result = await self.execute_command("uname", ["-r"])
            if kernel_result.get("success"):
                info["kernel"] = kernel_result["stdout"].strip()
            
            # 获取内存信息
            memory_result = await self.execute_command("free", ["-h"])
            if memory_result.get("success"):
                info["memory_info"] = memory_result["stdout"]
            
            return {"success": True, "info": info}
            
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_windows_integration_status(self) -> Dict[str, Any]:
        """获取Windows集成状态"""
        try:
            status = {
                "windows_fs_accessible": self.windows_fs_accessible,
                "windows_exe_accessible": self.windows_exe_accessible,
                "wsl_version": self.wsl_version
            }
            
            # 检查可访问的Windows驱动器
            if self.windows_fs_accessible:
                drives = []
                for drive in ["c", "d", "e", "f"]:
                    if os.path.exists(f"/mnt/{drive}"):
                        drives.append(drive.upper())
                status["accessible_drives"] = drives
            
            # 检查Windows PATH集成
            if self.windows_exe_accessible:
                path_result = await self.execute_command("cmd.exe", ["/c", "echo %PATH%"])
                if path_result.get("success"):
                    status["windows_path_available"] = True
                    status["windows_path"] = path_result["stdout"].strip()
                else:
                    status["windows_path_available"] = False
            
            return {"success": True, "status": status}
            
        except Exception as e:
            self.logger.error(f"获取Windows集成状态失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取WSL平台能力"""
        return {
            "platform": "wsl",
            "is_wsl": self.is_wsl,
            "wsl_version": self.wsl_version,
            "distribution": self.distribution,
            "package_manager": self.package_manager,
            "windows_fs_accessible": self.windows_fs_accessible,
            "windows_exe_accessible": self.windows_exe_accessible,
            "docker_available": self.docker_available,
            "supported_features": [
                "linux_commands",
                "package_management",
                "windows_integration",
                "file_bridge",
                "network_sharing",
                "docker_containers",
                "dual_system_access"
            ],
            "development_tools": [
                "git",
                "node",
                "python",
                "docker",
                "vim",
                "curl",
                "wget",
                "nvm",
                "pyenv"
            ],
            "windows_integration": [
                "file_system_access",
                "executable_access",
                "path_sharing",
                "network_sharing"
            ]
        }


    
    def _detect_package_manager(self) -> str:
        """检测包管理器"""
        managers = {
            "apt": "/usr/bin/apt",
            "yum": "/usr/bin/yum",
            "dnf": "/usr/bin/dnf",
            "pacman": "/usr/bin/pacman",
            "zypper": "/usr/bin/zypper"
        }
        
        for manager, path in managers.items():
            if os.path.exists(path):
                return manager
        
        return "unknown"
    
    def _check_docker(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def execute_command(self, command: str, args: List[str] = None, 
                            working_dir: str = None, env: Dict[str, str] = None) -> Dict[str, Any]:
        """
        执行WSL命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            
        Returns:
            Dict: 执行结果
        """
        args = args or []
        full_command = [command] + args
        
        try:
            self.logger.info(f"执行WSL命令: {' '.join(full_command)}")
            
            # 设置环境变量
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=exec_env
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": ' '.join(full_command),
                "working_dir": working_dir
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行WSL命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(full_command)
            }
    
    # ==================== 跨系统调用功能 ====================
    
    async def execute_windows_command(self, command: str, args: List[str] = None, 
                                    working_dir: str = None, 
                                    use_powershell: bool = False) -> Dict[str, Any]:
        """
        执行Windows命令
        
        Args:
            command: Windows命令
            args: 命令参数
            working_dir: Windows工作目录
            use_powershell: 是否使用PowerShell
            
        Returns:
            Dict: 执行结果
        """
        try:
            if not self.windows_exe_accessible:
                return {
                    "success": False,
                    "error": "Windows可执行文件不可访问"
                }
            
            args = args or []
            
            if use_powershell:
                # 使用PowerShell执行
                ps_command = f"{command} {' '.join(args)}"
                full_command = ["powershell.exe", "-Command", ps_command]
            else:
                # 使用cmd执行
                cmd_command = f"{command} {' '.join(args)}"
                full_command = ["cmd.exe", "/c", cmd_command]
            
            # 转换工作目录路径
            if working_dir:
                windows_working_dir = self.linux_to_windows_path(working_dir)
                if use_powershell:
                    full_command = ["powershell.exe", "-Command", 
                                  f"cd '{windows_working_dir}'; {command} {' '.join(args)}"]
                else:
                    full_command = ["cmd.exe", "/c", 
                                  f"cd /d \"{windows_working_dir}\" && {command} {' '.join(args)}"]
            
            self.logger.info(f"执行Windows命令: {' '.join(full_command)}")
            
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": command,
                "args": args,
                "use_powershell": use_powershell,
                "working_dir": working_dir
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Windows命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def execute_windows_executable(self, exe_path: str, args: List[str] = None, 
                                       working_dir: str = None) -> Dict[str, Any]:
        """
        执行Windows可执行文件
        
        Args:
            exe_path: 可执行文件路径（Windows路径）
            args: 参数
            working_dir: 工作目录
            
        Returns:
            Dict: 执行结果
        """
        try:
            if not self.windows_exe_accessible:
                return {
                    "success": False,
                    "error": "Windows可执行文件不可访问"
                }
            
            args = args or []
            
            # 构建完整命令
            full_command = [exe_path] + args
            
            self.logger.info(f"执行Windows可执行文件: {' '.join(full_command)}")
            
            # 设置工作目录
            cwd = None
            if working_dir:
                cwd = self.linux_to_windows_path(working_dir)
            
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "exe_path": exe_path,
                "args": args,
                "working_dir": working_dir
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Windows可执行文件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "exe_path": exe_path
            }
    
    def linux_to_windows_path(self, linux_path: str) -> str:
        """
        将Linux路径转换为Windows路径
        
        Args:
            linux_path: Linux路径
            
        Returns:
            str: Windows路径
        """
        try:
            # 处理 /mnt/c 格式的路径
            if linux_path.startswith("/mnt/"):
                # /mnt/c/Users/... -> C:\Users\...
                parts = linux_path.split("/")
                if len(parts) >= 3:
                    drive = parts[2].upper()
                    path_parts = parts[3:]
                    windows_path = f"{drive}:\\" + "\\".join(path_parts)
                    return windows_path
            
            # 处理相对路径
            if not linux_path.startswith("/"):
                return linux_path.replace("/", "\\")
            
            # 其他情况保持原样
            return linux_path
            
        except Exception as e:
            self.logger.debug(f"路径转换失败: {e}")
            return linux_path
    
    def windows_to_linux_path(self, windows_path: str) -> str:
        """
        将Windows路径转换为Linux路径
        
        Args:
            windows_path: Windows路径
            
        Returns:
            str: Linux路径
        """
        try:
            # 处理 C:\Users\... 格式的路径
            if ":" in windows_path:
                # C:\Users\... -> /mnt/c/Users/...
                drive = windows_path[0].lower()
                path_part = windows_path[2:].replace("\\", "/")
                linux_path = f"/mnt/{drive}{path_part}"
                return linux_path
            
            # 处理相对路径
            return windows_path.replace("\\", "/")
            
        except Exception as e:
            self.logger.debug(f"路径转换失败: {e}")
            return windows_path
    
    async def copy_file_to_windows(self, linux_path: str, windows_path: str) -> Dict[str, Any]:
        """
        将文件从Linux复制到Windows
        
        Args:
            linux_path: Linux文件路径
            windows_path: Windows目标路径
            
        Returns:
            Dict: 复制结果
        """
        try:
            # 转换Windows路径为Linux可访问路径
            target_linux_path = self.windows_to_linux_path(windows_path)
            
            result = await self.execute_command("cp", [linux_path, target_linux_path])
            
            if result["success"]:
                self.logger.info(f"文件复制成功: {linux_path} -> {windows_path}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "linux_path": linux_path,
                "windows_path": windows_path
            }
    
    async def copy_file_from_windows(self, windows_path: str, linux_path: str) -> Dict[str, Any]:
        """
        将文件从Windows复制到Linux
        
        Args:
            windows_path: Windows文件路径
            linux_path: Linux目标路径
            
        Returns:
            Dict: 复制结果
        """
        try:
            # 转换Windows路径为Linux可访问路径
            source_linux_path = self.windows_to_linux_path(windows_path)
            
            result = await self.execute_command("cp", [source_linux_path, linux_path])
            
            if result["success"]:
                self.logger.info(f"文件复制成功: {windows_path} -> {linux_path}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "windows_path": windows_path,
                "linux_path": linux_path
            }
    
    # ==================== 网络桥接功能 ====================
    
    async def setup_port_forwarding(self, linux_port: int, windows_port: int = None, 
                                   protocol: str = "tcp") -> Dict[str, Any]:
        """
        设置端口转发
        
        Args:
            linux_port: Linux端口
            windows_port: Windows端口，如果为None则使用相同端口
            protocol: 协议 (tcp/udp)
            
        Returns:
            Dict: 设置结果
        """
        try:
            if windows_port is None:
                windows_port = linux_port
            
            # 使用netsh设置端口转发
            command = f"netsh interface portproxy add v4tov4 listenport={windows_port} listenaddress=0.0.0.0 connectport={linux_port} connectaddress=127.0.0.1"
            
            result = await self.execute_windows_command("netsh", 
                                                       ["interface", "portproxy", "add", "v4tov4",
                                                        f"listenport={windows_port}",
                                                        "listenaddress=0.0.0.0",
                                                        f"connectport={linux_port}",
                                                        "connectaddress=127.0.0.1"])
            
            if result["success"]:
                self.logger.info(f"端口转发设置成功: {linux_port} -> {windows_port}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "linux_port": linux_port,
                "windows_port": windows_port
            }
    
    async def remove_port_forwarding(self, windows_port: int) -> Dict[str, Any]:
        """
        移除端口转发
        
        Args:
            windows_port: Windows端口
            
        Returns:
            Dict: 移除结果
        """
        try:
            result = await self.execute_windows_command("netsh", 
                                                       ["interface", "portproxy", "delete", "v4tov4",
                                                        f"listenport={windows_port}",
                                                        "listenaddress=0.0.0.0"])
            
            if result["success"]:
                self.logger.info(f"端口转发移除成功: {windows_port}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "windows_port": windows_port
            }
    
    async def list_port_forwardings(self) -> Dict[str, Any]:
        """
        列出端口转发规则
        
        Returns:
            Dict: 端口转发列表
        """
        try:
            result = await self.execute_windows_command("netsh", 
                                                       ["interface", "portproxy", "show", "all"])
            
            if result["success"]:
                forwardings = self._parse_port_forwardings(result["stdout"])
                return {
                    "success": True,
                    "forwardings": forwardings,
                    "count": len(forwardings)
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_port_forwardings(self, output: str) -> List[Dict[str, Any]]:
        """解析端口转发输出"""
        forwardings = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if 'listenport' in line.lower() and 'connectport' in line.lower():
                # 解析端口转发规则
                parts = line.split()
                forwarding = {}
                
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        forwarding[key.lower()] = value
                
                if forwarding:
                    forwardings.append(forwarding)
        
        return forwardings
    
    async def get_network_interfaces(self) -> Dict[str, Any]:
        """
        获取网络接口信息
        
        Returns:
            Dict: 网络接口信息
        """
        try:
            # 获取Linux网络接口
            linux_result = await self.execute_command("ip", ["addr", "show"])
            
            # 获取Windows网络接口
            windows_result = await self.execute_windows_command("ipconfig", ["/all"])
            
            return {
                "success": True,
                "linux_interfaces": linux_result.get("stdout", ""),
                "windows_interfaces": windows_result.get("stdout", ""),
                "linux_success": linux_result.get("success", False),
                "windows_success": windows_result.get("success", False)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_network_connectivity(self, target: str, 
                                      from_windows: bool = False) -> Dict[str, Any]:
        """
        测试网络连接
        
        Args:
            target: 目标地址
            from_windows: 是否从Windows测试
            
        Returns:
            Dict: 连接测试结果
        """
        try:
            if from_windows:
                result = await self.execute_windows_command("ping", ["-n", "4", target])
            else:
                result = await self.execute_command("ping", ["-c", "4", target])
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "target": target,
                "from_windows": from_windows
            }
    
    # ==================== 包管理功能 ====================
    
    async def install_package(self, package: str, options: List[str] = None) -> Dict[str, Any]:
        """
        安装包
        
        Args:
            package: 包名
            options: 安装选项
            
        Returns:
            Dict: 安装结果
        """
        try:
            if self.package_manager == "apt":
                args = ["install", "-y", package]
                if options:
                    args.extend(options)
                result = await self.execute_command("sudo", ["apt"] + args)
            elif self.package_manager == "yum":
                args = ["install", "-y", package]
                if options:
                    args.extend(options)
                result = await self.execute_command("sudo", ["yum"] + args)
            elif self.package_manager == "dnf":
                args = ["install", "-y", package]
                if options:
                    args.extend(options)
                result = await self.execute_command("sudo", ["dnf"] + args)
            else:
                return {
                    "success": False,
                    "error": f"不支持的包管理器: {self.package_manager}"
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package": package
            }
    
    async def update_packages(self) -> Dict[str, Any]:
        """更新包列表"""
        try:
            if self.package_manager == "apt":
                result = await self.execute_command("sudo", ["apt", "update"])
            elif self.package_manager == "yum":
                result = await self.execute_command("sudo", ["yum", "check-update"])
            elif self.package_manager == "dnf":
                result = await self.execute_command("sudo", ["dnf", "check-update"])
            else:
                return {
                    "success": False,
                    "error": f"不支持的包管理器: {self.package_manager}"
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upgrade_packages(self) -> Dict[str, Any]:
        """升级所有包"""
        try:
            if self.package_manager == "apt":
                result = await self.execute_command("sudo", ["apt", "upgrade", "-y"])
            elif self.package_manager == "yum":
                result = await self.execute_command("sudo", ["yum", "update", "-y"])
            elif self.package_manager == "dnf":
                result = await self.execute_command("sudo", ["dnf", "upgrade", "-y"])
            else:
                return {
                    "success": False,
                    "error": f"不支持的包管理器: {self.package_manager}"
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== Docker 集成 ====================
    
    async def docker_run(self, image: str, command: str = None, 
                        options: List[str] = None, 
                        mount_windows_path: str = None) -> Dict[str, Any]:
        """
        运行Docker容器
        
        Args:
            image: 镜像名
            command: 要执行的命令
            options: Docker选项
            mount_windows_path: 要挂载的Windows路径
            
        Returns:
            Dict: 运行结果
        """
        try:
            if not self.docker_available:
                return {
                    "success": False,
                    "error": "Docker不可用"
                }
            
            args = ["run"]
            
            if options:
                args.extend(options)
            
            # 挂载Windows路径
            if mount_windows_path:
                linux_path = self.windows_to_linux_path(mount_windows_path)
                args.extend(["-v", f"{linux_path}:/mnt/windows"])
            
            args.append(image)
            
            if command:
                args.extend(command.split())
            
            result = await self.execute_command("docker", args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "image": image
            }
    
    # ==================== 系统信息和能力 ====================
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取WSL平台能力"""
        return {
            "platform": self.platform,
            "is_wsl": self.is_wsl,
            "wsl_version": self.wsl_version,
            "distribution": self.distribution,
            "windows_fs_accessible": self.windows_fs_accessible,
            "windows_exe_accessible": self.windows_exe_accessible,
            "package_manager": self.package_manager,
            "docker_available": self.docker_available,
            "supported_features": {
                "cross_system_execution": self.windows_exe_accessible,
                "file_system_bridge": self.windows_fs_accessible,
                "network_bridge": True,
                "port_forwarding": True,
                "package_management": self.package_manager != "unknown",
                "docker_integration": self.docker_available
            },
            "cross_system_capabilities": {
                "execute_windows_commands": self.windows_exe_accessible,
                "execute_windows_executables": self.windows_exe_accessible,
                "path_conversion": True,
                "file_copy_bridge": self.windows_fs_accessible
            },
            "network_capabilities": {
                "port_forwarding": True,
                "network_interface_info": True,
                "connectivity_testing": True
            },
            "package_capabilities": {
                "install_packages": self.package_manager != "unknown",
                "update_packages": self.package_manager != "unknown",
                "upgrade_packages": self.package_manager != "unknown"
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "platform": self.platform,
            "is_wsl": self.is_wsl,
            "wsl_version": self.wsl_version,
            "distribution": self.distribution,
            "windows_fs_accessible": self.windows_fs_accessible,
            "windows_exe_accessible": self.windows_exe_accessible,
            "package_manager": self.package_manager,
            "docker_available": self.docker_available,
            "ready": self.is_wsl
        }

