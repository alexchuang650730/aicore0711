"""
Linux Terminal MCP Adapter - Linux终端MCP适配器
支持各种Linux发行版的终端功能和工具

特性：多发行版支持、包管理器适配、Docker、systemd等
"""

import asyncio
import subprocess
import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

class LinuxTerminalMCP:
    """Linux终端MCP适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.platform = "linux"
        
        # 检测Linux发行版和工具
        self.distribution = self._detect_distribution()
        self.distribution_version = self._get_distribution_version()
        self.package_manager = self._detect_package_manager()
        self.init_system = self._detect_init_system()
        
        # 检查常用工具
        self.docker_available = self._check_docker()
        self.systemctl_available = self._check_systemctl()
        self.snap_available = self._check_snap()
        self.flatpak_available = self._check_flatpak()
        
        self.logger.info(f"Linux终端MCP初始化完成 - 发行版: {self.distribution} {self.distribution_version}, 包管理器: {self.package_manager}")
    
    def _detect_distribution(self) -> str:
        """检测Linux发行版"""
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("ID="):
                            return line.split("=")[1].strip().strip('"')
            
            # 备用检测方法
            if os.path.exists("/etc/debian_version"):
                return "debian"
            elif os.path.exists("/etc/redhat-release"):
                return "rhel"
            elif os.path.exists("/etc/arch-release"):
                return "arch"
            elif os.path.exists("/etc/alpine-release"):
                return "alpine"
            
            return "unknown"
            
        except Exception as e:
            self.logger.debug(f"检测发行版失败: {e}")
            return "unknown"
    
    def _get_distribution_version(self) -> str:
        """获取发行版版本"""
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("VERSION_ID="):
                            return line.split("=")[1].strip().strip('"')
            
            return "unknown"
            
        except Exception as e:
            self.logger.debug(f"获取发行版版本失败: {e}")
            return "unknown"
    
    def _detect_package_manager(self) -> str:
        """检测包管理器"""
        managers = {
            "apt": ["apt", "apt-get"],
            "yum": ["yum"],
            "dnf": ["dnf"],
            "pacman": ["pacman"],
            "zypper": ["zypper"],
            "apk": ["apk"],
            "portage": ["emerge"],
            "xbps": ["xbps-install"]
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
    
    def _detect_init_system(self) -> str:
        """检测初始化系统"""
        try:
            if os.path.exists("/run/systemd/system"):
                return "systemd"
            elif os.path.exists("/sbin/openrc"):
                return "openrc"
            elif os.path.exists("/etc/init"):
                return "upstart"
            elif os.path.exists("/etc/inittab"):
                return "sysvinit"
            else:
                return "unknown"
        except Exception:
            return "unknown"
    
    def _check_docker(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_systemctl(self) -> bool:
        """检查systemctl是否可用"""
        try:
            result = subprocess.run(["systemctl", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_snap(self) -> bool:
        """检查Snap是否可用"""
        try:
            result = subprocess.run(["snap", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_flatpak(self) -> bool:
        """检查Flatpak是否可用"""
        try:
            result = subprocess.run(["flatpak", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def execute_command(self, command: str, args: List[str] = None, 
                            working_dir: str = None, env: Dict[str, str] = None,
                            use_sudo: bool = False) -> Dict[str, Any]:
        """
        执行Linux命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            use_sudo: 是否使用sudo
            
        Returns:
            Dict: 执行结果
        """
        args = args or []
        
        if use_sudo:
            full_command = ["sudo", command] + args
        else:
            full_command = [command] + args
        
        try:
            self.logger.info(f"执行Linux命令: {' '.join(full_command)}")
            
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
    
    # 包管理方法
    async def install_package(self, package: str, update_first: bool = True) -> Dict[str, Any]:
        """安装软件包"""
        if self.package_manager == "unknown":
            return {"success": False, "error": "未检测到包管理器"}
        
        results = {}
        
        # 先更新包列表
        if update_first:
            update_result = await self._update_package_list()
            results["update"] = update_result
        
        # 安装包
        install_result = await self._install_package_with_manager(package)
        results["install"] = install_result
        
        return {"success": install_result.get("success", False), "results": results}
    
    async def _update_package_list(self) -> Dict[str, Any]:
        """更新包列表"""
        if self.package_manager == "apt":
            return await self.execute_command("apt", ["update"], use_sudo=True)
        elif self.package_manager == "yum":
            return await self.execute_command("yum", ["check-update"], use_sudo=True)
        elif self.package_manager == "dnf":
            return await self.execute_command("dnf", ["check-update"], use_sudo=True)
        elif self.package_manager == "pacman":
            return await self.execute_command("pacman", ["-Sy"], use_sudo=True)
        elif self.package_manager == "zypper":
            return await self.execute_command("zypper", ["refresh"], use_sudo=True)
        elif self.package_manager == "apk":
            return await self.execute_command("apk", ["update"], use_sudo=True)
        else:
            return {"success": True, "message": "不需要更新包列表"}
    
    async def _install_package_with_manager(self, package: str) -> Dict[str, Any]:
        """使用包管理器安装包"""
        if self.package_manager == "apt":
            return await self.execute_command("apt", ["install", "-y", package], use_sudo=True)
        elif self.package_manager == "yum":
            return await self.execute_command("yum", ["install", "-y", package], use_sudo=True)
        elif self.package_manager == "dnf":
            return await self.execute_command("dnf", ["install", "-y", package], use_sudo=True)
        elif self.package_manager == "pacman":
            return await self.execute_command("pacman", ["-S", "--noconfirm", package], use_sudo=True)
        elif self.package_manager == "zypper":
            return await self.execute_command("zypper", ["install", "-y", package], use_sudo=True)
        elif self.package_manager == "apk":
            return await self.execute_command("apk", ["add", package], use_sudo=True)
        elif self.package_manager == "portage":
            return await self.execute_command("emerge", [package], use_sudo=True)
        elif self.package_manager == "xbps":
            return await self.execute_command("xbps-install", ["-y", package], use_sudo=True)
        else:
            return {"success": False, "error": f"不支持的包管理器: {self.package_manager}"}
    
    async def remove_package(self, package: str) -> Dict[str, Any]:
        """卸载软件包"""
        if self.package_manager == "apt":
            return await self.execute_command("apt", ["remove", "-y", package], use_sudo=True)
        elif self.package_manager == "yum":
            return await self.execute_command("yum", ["remove", "-y", package], use_sudo=True)
        elif self.package_manager == "dnf":
            return await self.execute_command("dnf", ["remove", "-y", package], use_sudo=True)
        elif self.package_manager == "pacman":
            return await self.execute_command("pacman", ["-R", "--noconfirm", package], use_sudo=True)
        elif self.package_manager == "zypper":
            return await self.execute_command("zypper", ["remove", "-y", package], use_sudo=True)
        elif self.package_manager == "apk":
            return await self.execute_command("apk", ["del", package], use_sudo=True)
        elif self.package_manager == "portage":
            return await self.execute_command("emerge", ["--unmerge", package], use_sudo=True)
        elif self.package_manager == "xbps":
            return await self.execute_command("xbps-remove", ["-y", package], use_sudo=True)
        else:
            return {"success": False, "error": f"不支持的包管理器: {self.package_manager}"}
    
    async def search_package(self, query: str) -> Dict[str, Any]:
        """搜索软件包"""
        if self.package_manager == "apt":
            return await self.execute_command("apt", ["search", query])
        elif self.package_manager == "yum":
            return await self.execute_command("yum", ["search", query])
        elif self.package_manager == "dnf":
            return await self.execute_command("dnf", ["search", query])
        elif self.package_manager == "pacman":
            return await self.execute_command("pacman", ["-Ss", query])
        elif self.package_manager == "zypper":
            return await self.execute_command("zypper", ["search", query])
        elif self.package_manager == "apk":
            return await self.execute_command("apk", ["search", query])
        elif self.package_manager == "portage":
            return await self.execute_command("emerge", ["--search", query])
        elif self.package_manager == "xbps":
            return await self.execute_command("xbps-query", ["-Rs", query])
        else:
            return {"success": False, "error": f"不支持的包管理器: {self.package_manager}"}
    
    async def upgrade_system(self) -> Dict[str, Any]:
        """升级系统"""
        if self.package_manager == "apt":
            update_result = await self.execute_command("apt", ["update"], use_sudo=True)
            if update_result.get("success"):
                return await self.execute_command("apt", ["upgrade", "-y"], use_sudo=True)
            return update_result
        elif self.package_manager == "yum":
            return await self.execute_command("yum", ["update", "-y"], use_sudo=True)
        elif self.package_manager == "dnf":
            return await self.execute_command("dnf", ["upgrade", "-y"], use_sudo=True)
        elif self.package_manager == "pacman":
            return await self.execute_command("pacman", ["-Syu", "--noconfirm"], use_sudo=True)
        elif self.package_manager == "zypper":
            return await self.execute_command("zypper", ["update", "-y"], use_sudo=True)
        elif self.package_manager == "apk":
            update_result = await self.execute_command("apk", ["update"], use_sudo=True)
            if update_result.get("success"):
                return await self.execute_command("apk", ["upgrade"], use_sudo=True)
            return update_result
        else:
            return {"success": False, "error": f"不支持的包管理器: {self.package_manager}"}
    
    # 服务管理方法
    async def start_service(self, service_name: str) -> Dict[str, Any]:
        """启动服务"""
        if self.init_system == "systemd" and self.systemctl_available:
            return await self.execute_command("systemctl", ["start", service_name], use_sudo=True)
        elif self.init_system == "openrc":
            return await self.execute_command("rc-service", [service_name, "start"], use_sudo=True)
        else:
            return await self.execute_command("service", [service_name, "start"], use_sudo=True)
    
    async def stop_service(self, service_name: str) -> Dict[str, Any]:
        """停止服务"""
        if self.init_system == "systemd" and self.systemctl_available:
            return await self.execute_command("systemctl", ["stop", service_name], use_sudo=True)
        elif self.init_system == "openrc":
            return await self.execute_command("rc-service", [service_name, "stop"], use_sudo=True)
        else:
            return await self.execute_command("service", [service_name, "stop"], use_sudo=True)
    
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启服务"""
        if self.init_system == "systemd" and self.systemctl_available:
            return await self.execute_command("systemctl", ["restart", service_name], use_sudo=True)
        elif self.init_system == "openrc":
            return await self.execute_command("rc-service", [service_name, "restart"], use_sudo=True)
        else:
            return await self.execute_command("service", [service_name, "restart"], use_sudo=True)
    
    async def enable_service(self, service_name: str) -> Dict[str, Any]:
        """启用服务（开机自启）"""
        if self.init_system == "systemd" and self.systemctl_available:
            return await self.execute_command("systemctl", ["enable", service_name], use_sudo=True)
        elif self.init_system == "openrc":
            return await self.execute_command("rc-update", ["add", service_name], use_sudo=True)
        else:
            return {"success": False, "error": "不支持的初始化系统"}
    
    async def disable_service(self, service_name: str) -> Dict[str, Any]:
        """禁用服务"""
        if self.init_system == "systemd" and self.systemctl_available:
            return await self.execute_command("systemctl", ["disable", service_name], use_sudo=True)
        elif self.init_system == "openrc":
            return await self.execute_command("rc-update", ["del", service_name], use_sudo=True)
        else:
            return {"success": False, "error": "不支持的初始化系统"}
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """获取服务状态"""
        if self.init_system == "systemd" and self.systemctl_available:
            return await self.execute_command("systemctl", ["status", service_name])
        elif self.init_system == "openrc":
            return await self.execute_command("rc-service", [service_name, "status"])
        else:
            return await self.execute_command("service", [service_name, "status"])
    
    # Docker方法
    async def docker_run(self, image: str, command: str = None, 
                        ports: List[str] = None, volumes: List[str] = None,
                        detach: bool = False, name: str = None) -> Dict[str, Any]:
        """运行Docker容器"""
        if not self.docker_available:
            return {"success": False, "error": "Docker不可用"}
        
        args = ["run"]
        
        if detach:
            args.append("-d")
        
        if name:
            args.extend(["--name", name])
        
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
    
    async def docker_images(self) -> Dict[str, Any]:
        """列出Docker镜像"""
        if not self.docker_available:
            return {"success": False, "error": "Docker不可用"}
        
        return await self.execute_command("docker", ["images"])
    
    # Snap方法
    async def snap_install(self, package: str, classic: bool = False) -> Dict[str, Any]:
        """使用Snap安装包"""
        if not self.snap_available:
            return {"success": False, "error": "Snap不可用"}
        
        args = ["install", package]
        if classic:
            args.append("--classic")
        
        return await self.execute_command("snap", args, use_sudo=True)
    
    async def snap_remove(self, package: str) -> Dict[str, Any]:
        """使用Snap卸载包"""
        if not self.snap_available:
            return {"success": False, "error": "Snap不可用"}
        
        return await self.execute_command("snap", ["remove", package], use_sudo=True)
    
    async def snap_list(self) -> Dict[str, Any]:
        """列出已安装的Snap包"""
        if not self.snap_available:
            return {"success": False, "error": "Snap不可用"}
        
        return await self.execute_command("snap", ["list"])
    
    # 系统信息方法
    async def get_system_info(self) -> Dict[str, Any]:
        """获取Linux系统信息"""
        try:
            info = {
                "platform": "linux",
                "distribution": self.distribution,
                "distribution_version": self.distribution_version,
                "package_manager": self.package_manager,
                "init_system": self.init_system,
                "docker_available": self.docker_available,
                "systemctl_available": self.systemctl_available,
                "snap_available": self.snap_available,
                "flatpak_available": self.flatpak_available
            }
            
            # 获取内核信息
            kernel_result = await self.execute_command("uname", ["-r"])
            if kernel_result.get("success"):
                info["kernel"] = kernel_result["stdout"].strip()
            
            # 获取架构信息
            arch_result = await self.execute_command("uname", ["-m"])
            if arch_result.get("success"):
                info["architecture"] = arch_result["stdout"].strip()
            
            # 获取内存信息
            memory_result = await self.execute_command("free", ["-h"])
            if memory_result.get("success"):
                info["memory_info"] = memory_result["stdout"]
            
            # 获取磁盘信息
            disk_result = await self.execute_command("df", ["-h"])
            if disk_result.get("success"):
                info["disk_info"] = disk_result["stdout"]
            
            # 获取CPU信息
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    info["cpu_info"] = cpuinfo
            
            return {"success": True, "info": info}
            
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {"success": False, "error": str(e)}
    
    # 开发环境方法
    async def setup_development_environment(self, tools: List[str]) -> Dict[str, Any]:
        """设置开发环境"""
        results = {}
        
        for tool in tools:
            if tool == "docker" and not self.docker_available:
                # 安装Docker
                result = await self._install_docker()
                results["docker"] = result
            
            elif tool in ["git", "curl", "wget", "vim", "nano", "htop", "tree"]:
                # 使用包管理器安装基础工具
                result = await self.install_package(tool, update_first=False)
                results[tool] = result
            
            elif tool == "node":
                # 安装Node.js
                if self.distribution in ["ubuntu", "debian"]:
                    # 使用NodeSource仓库
                    script = """
                    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                    sudo apt-get install -y nodejs
                    """
                    result = await self.execute_command("bash", ["-c", script])
                    results["node"] = result
                else:
                    result = await self.install_package("nodejs")
                    results["node"] = result
            
            elif tool == "python3":
                result = await self.install_package("python3")
                if result.get("success"):
                    pip_result = await self.install_package("python3-pip")
                    results["python3"] = {"install": result, "pip": pip_result}
                else:
                    results["python3"] = result
            
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
    
    async def _install_docker(self) -> Dict[str, Any]:
        """安装Docker"""
        if self.distribution in ["ubuntu", "debian"]:
            # Ubuntu/Debian Docker安装
            commands = [
                "sudo apt-get update",
                "sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release",
                "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg",
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
                "sudo apt-get update",
                "sudo apt-get install -y docker-ce docker-ce-cli containerd.io"
            ]
        elif self.distribution in ["centos", "rhel", "fedora"]:
            # CentOS/RHEL/Fedora Docker安装
            commands = [
                "sudo yum install -y yum-utils",
                "sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo",
                "sudo yum install -y docker-ce docker-ce-cli containerd.io"
            ]
        elif self.distribution == "arch":
            # Arch Linux Docker安装
            commands = [
                "sudo pacman -S --noconfirm docker"
            ]
        else:
            return {"success": False, "error": f"不支持在{self.distribution}上自动安装Docker"}
        
        docker_results = []
        for cmd in commands:
            result = await self.execute_command("bash", ["-c", cmd])
            docker_results.append(result)
            if not result.get("success"):
                break
        
        return {"success": True, "steps": docker_results}
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取Linux平台能力"""
        return {
            "platform": "linux",
            "distribution": self.distribution,
            "distribution_version": self.distribution_version,
            "package_manager": self.package_manager,
            "init_system": self.init_system,
            "docker_available": self.docker_available,
            "systemctl_available": self.systemctl_available,
            "snap_available": self.snap_available,
            "flatpak_available": self.flatpak_available,
            "supported_features": [
                "package_management",
                "service_management",
                "docker_containers",
                "system_administration",
                "development_tools",
                "snap_packages",
                "flatpak_packages"
            ],
            "development_tools": [
                "git",
                "gcc",
                "make",
                "cmake",
                "node",
                "python",
                "docker",
                "vim",
                "emacs",
                "vscode"
            ],
            "package_managers": [
                self.package_manager,
                "snap" if self.snap_available else None,
                "flatpak" if self.flatpak_available else None
            ]
        }


            elif os.path.exists("/etc/arch-release"):
                return "arch"
            elif os.path.exists("/etc/suse-release"):
                return "suse"
            
            return "unknown"
            
        except Exception as e:
            self.logger.debug(f"检测发行版失败: {e}")
            return "unknown"
    
    def _get_distribution_version(self) -> str:
        """获取发行版版本"""
        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("VERSION_ID="):
                            return line.split("=")[1].strip().strip('"')
            
            return "unknown"
            
        except Exception as e:
            self.logger.debug(f"获取发行版版本失败: {e}")
            return "unknown"
    
    def _detect_package_manager(self) -> str:
        """检测包管理器"""
        managers = {
            "apt": "/usr/bin/apt",
            "yum": "/usr/bin/yum",
            "dnf": "/usr/bin/dnf",
            "pacman": "/usr/bin/pacman",
            "zypper": "/usr/bin/zypper",
            "apk": "/sbin/apk",
            "portage": "/usr/bin/emerge"
        }
        
        for manager, path in managers.items():
            if os.path.exists(path):
                return manager
        
        return "unknown"
    
    def _detect_init_system(self) -> str:
        """检测初始化系统"""
        try:
            if os.path.exists("/run/systemd/system"):
                return "systemd"
            elif os.path.exists("/sbin/init") and os.path.islink("/sbin/init"):
                link_target = os.readlink("/sbin/init")
                if "systemd" in link_target:
                    return "systemd"
                elif "upstart" in link_target:
                    return "upstart"
            
            return "sysv"
            
        except Exception as e:
            self.logger.debug(f"检测初始化系统失败: {e}")
            return "unknown"
    
    def _check_docker(self) -> bool:
        """检查Docker是否可用"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_systemctl(self) -> bool:
        """检查systemctl是否可用"""
        try:
            result = subprocess.run(["systemctl", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_snap(self) -> bool:
        """检查Snap是否可用"""
        try:
            result = subprocess.run(["snap", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_flatpak(self) -> bool:
        """检查Flatpak是否可用"""
        try:
            result = subprocess.run(["flatpak", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def execute_command(self, command: str, args: List[str] = None, 
                            working_dir: str = None, env: Dict[str, str] = None,
                            use_sudo: bool = False) -> Dict[str, Any]:
        """
        执行Linux命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            use_sudo: 是否使用sudo
            
        Returns:
            Dict: 执行结果
        """
        args = args or []
        
        if use_sudo:
            full_command = ["sudo", command] + args
        else:
            full_command = [command] + args
        
        try:
            self.logger.info(f"执行Linux命令: {' '.join(full_command)}")
            
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
                "working_dir": working_dir,
                "use_sudo": use_sudo
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Linux命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(full_command)
            }
    
    # ==================== 多发行版包管理功能 ====================
    
    async def install_package(self, package: str, options: List[str] = None) -> Dict[str, Any]:
        """
        安装包（自动适配包管理器）
        
        Args:
            package: 包名
            options: 安装选项
            
        Returns:
            Dict: 安装结果
        """
        try:
            options = options or []
            
            if self.package_manager == "apt":
                args = ["install", "-y", package] + options
                result = await self.execute_command("apt", args, use_sudo=True)
            elif self.package_manager == "yum":
                args = ["install", "-y", package] + options
                result = await self.execute_command("yum", args, use_sudo=True)
            elif self.package_manager == "dnf":
                args = ["install", "-y", package] + options
                result = await self.execute_command("dnf", args, use_sudo=True)
            elif self.package_manager == "pacman":
                args = ["-S", "--noconfirm", package] + options
                result = await self.execute_command("pacman", args, use_sudo=True)
            elif self.package_manager == "zypper":
                args = ["install", "-y", package] + options
                result = await self.execute_command("zypper", args, use_sudo=True)
            elif self.package_manager == "apk":
                args = ["add", package] + options
                result = await self.execute_command("apk", args, use_sudo=True)
            elif self.package_manager == "portage":
                args = [package] + options
                result = await self.execute_command("emerge", args, use_sudo=True)
            else:
                return {
                    "success": False,
                    "error": f"不支持的包管理器: {self.package_manager}"
                }
            
            if result["success"]:
                self.logger.info(f"包安装成功: {package}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package": package
            }
    
    async def remove_package(self, package: str, options: List[str] = None) -> Dict[str, Any]:
        """
        卸载包
        
        Args:
            package: 包名
            options: 卸载选项
            
        Returns:
            Dict: 卸载结果
        """
        try:
            options = options or []
            
            if self.package_manager == "apt":
                args = ["remove", "-y", package] + options
                result = await self.execute_command("apt", args, use_sudo=True)
            elif self.package_manager == "yum":
                args = ["remove", "-y", package] + options
                result = await self.execute_command("yum", args, use_sudo=True)
            elif self.package_manager == "dnf":
                args = ["remove", "-y", package] + options
                result = await self.execute_command("dnf", args, use_sudo=True)
            elif self.package_manager == "pacman":
                args = ["-R", "--noconfirm", package] + options
                result = await self.execute_command("pacman", args, use_sudo=True)
            elif self.package_manager == "zypper":
                args = ["remove", "-y", package] + options
                result = await self.execute_command("zypper", args, use_sudo=True)
            elif self.package_manager == "apk":
                args = ["del", package] + options
                result = await self.execute_command("apk", args, use_sudo=True)
            elif self.package_manager == "portage":
                args = ["--unmerge", package] + options
                result = await self.execute_command("emerge", args, use_sudo=True)
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
    
    async def update_package_list(self) -> Dict[str, Any]:
        """更新包列表"""
        try:
            if self.package_manager == "apt":
                result = await self.execute_command("apt", ["update"], use_sudo=True)
            elif self.package_manager == "yum":
                result = await self.execute_command("yum", ["check-update"], use_sudo=True)
            elif self.package_manager == "dnf":
                result = await self.execute_command("dnf", ["check-update"], use_sudo=True)
            elif self.package_manager == "pacman":
                result = await self.execute_command("pacman", ["-Sy"], use_sudo=True)
            elif self.package_manager == "zypper":
                result = await self.execute_command("zypper", ["refresh"], use_sudo=True)
            elif self.package_manager == "apk":
                result = await self.execute_command("apk", ["update"], use_sudo=True)
            elif self.package_manager == "portage":
                result = await self.execute_command("emerge", ["--sync"], use_sudo=True)
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
    
    async def upgrade_packages(self, package: str = None) -> Dict[str, Any]:
        """
        升级包
        
        Args:
            package: 包名，如果为None则升级所有包
            
        Returns:
            Dict: 升级结果
        """
        try:
            if self.package_manager == "apt":
                if package:
                    args = ["install", "--only-upgrade", "-y", package]
                else:
                    args = ["upgrade", "-y"]
                result = await self.execute_command("apt", args, use_sudo=True)
            elif self.package_manager == "yum":
                if package:
                    args = ["update", "-y", package]
                else:
                    args = ["update", "-y"]
                result = await self.execute_command("yum", args, use_sudo=True)
            elif self.package_manager == "dnf":
                if package:
                    args = ["upgrade", "-y", package]
                else:
                    args = ["upgrade", "-y"]
                result = await self.execute_command("dnf", args, use_sudo=True)
            elif self.package_manager == "pacman":
                if package:
                    args = ["-S", "--noconfirm", package]
                else:
                    args = ["-Syu", "--noconfirm"]
                result = await self.execute_command("pacman", args, use_sudo=True)
            elif self.package_manager == "zypper":
                if package:
                    args = ["update", "-y", package]
                else:
                    args = ["update", "-y"]
                result = await self.execute_command("zypper", args, use_sudo=True)
            elif self.package_manager == "apk":
                if package:
                    args = ["upgrade", package]
                else:
                    args = ["upgrade"]
                result = await self.execute_command("apk", args, use_sudo=True)
            elif self.package_manager == "portage":
                if package:
                    args = ["--update", package]
                else:
                    args = ["--update", "@world"]
                result = await self.execute_command("emerge", args, use_sudo=True)
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
    
    async def search_package(self, query: str) -> Dict[str, Any]:
        """
        搜索包
        
        Args:
            query: 搜索查询
            
        Returns:
            Dict: 搜索结果
        """
        try:
            if self.package_manager == "apt":
                result = await self.execute_command("apt", ["search", query])
            elif self.package_manager == "yum":
                result = await self.execute_command("yum", ["search", query])
            elif self.package_manager == "dnf":
                result = await self.execute_command("dnf", ["search", query])
            elif self.package_manager == "pacman":
                result = await self.execute_command("pacman", ["-Ss", query])
            elif self.package_manager == "zypper":
                result = await self.execute_command("zypper", ["search", query])
            elif self.package_manager == "apk":
                result = await self.execute_command("apk", ["search", query])
            elif self.package_manager == "portage":
                result = await self.execute_command("emerge", ["--search", query])
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
                "query": query
            }
    
    async def list_installed_packages(self) -> Dict[str, Any]:
        """列出已安装的包"""
        try:
            if self.package_manager == "apt":
                result = await self.execute_command("apt", ["list", "--installed"])
            elif self.package_manager == "yum":
                result = await self.execute_command("yum", ["list", "installed"])
            elif self.package_manager == "dnf":
                result = await self.execute_command("dnf", ["list", "installed"])
            elif self.package_manager == "pacman":
                result = await self.execute_command("pacman", ["-Q"])
            elif self.package_manager == "zypper":
                result = await self.execute_command("zypper", ["search", "--installed-only"])
            elif self.package_manager == "apk":
                result = await self.execute_command("apk", ["info"])
            elif self.package_manager == "portage":
                result = await self.execute_command("qlist", ["-I"])
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
    
    # ==================== systemd 服务管理 ====================
    
    async def systemd_start_service(self, service_name: str) -> Dict[str, Any]:
        """
        启动systemd服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 启动结果
        """
        try:
            if not self.systemctl_available:
                return {
                    "success": False,
                    "error": "systemctl不可用"
                }
            
            result = await self.execute_command("systemctl", ["start", service_name], use_sudo=True)
            
            if result["success"]:
                self.logger.info(f"systemd服务启动成功: {service_name}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def systemd_stop_service(self, service_name: str) -> Dict[str, Any]:
        """
        停止systemd服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 停止结果
        """
        try:
            if not self.systemctl_available:
                return {
                    "success": False,
                    "error": "systemctl不可用"
                }
            
            result = await self.execute_command("systemctl", ["stop", service_name], use_sudo=True)
            
            if result["success"]:
                self.logger.info(f"systemd服务停止成功: {service_name}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def systemd_restart_service(self, service_name: str) -> Dict[str, Any]:
        """
        重启systemd服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 重启结果
        """
        try:
            if not self.systemctl_available:
                return {
                    "success": False,
                    "error": "systemctl不可用"
                }
            
            result = await self.execute_command("systemctl", ["restart", service_name], use_sudo=True)
            
            if result["success"]:
                self.logger.info(f"systemd服务重启成功: {service_name}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def systemd_enable_service(self, service_name: str) -> Dict[str, Any]:
        """
        启用systemd服务（开机自启）
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 启用结果
        """
        try:
            if not self.systemctl_available:
                return {
                    "success": False,
                    "error": "systemctl不可用"
                }
            
            result = await self.execute_command("systemctl", ["enable", service_name], use_sudo=True)
            
            if result["success"]:
                self.logger.info(f"systemd服务启用成功: {service_name}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def systemd_disable_service(self, service_name: str) -> Dict[str, Any]:
        """
        禁用systemd服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 禁用结果
        """
        try:
            if not self.systemctl_available:
                return {
                    "success": False,
                    "error": "systemctl不可用"
                }
            
            result = await self.execute_command("systemctl", ["disable", service_name], use_sudo=True)
            
            if result["success"]:
                self.logger.info(f"systemd服务禁用成功: {service_name}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def systemd_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        获取systemd服务状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 服务状态
        """
        try:
            if not self.systemctl_available:
                return {
                    "success": False,
                    "error": "systemctl不可用"
                }
            
            result = await self.execute_command("systemctl", ["status", service_name])
            
            if result["success"] or result["returncode"] == 3:  # 3表示服务未运行但正常
                status_info = self._parse_systemd_status(result["stdout"])
                return {
                    "success": True,
                    "status_info": status_info,
                    "service_name": service_name,
                    "raw_output": result["stdout"]
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    def _parse_systemd_status(self, output: str) -> Dict[str, str]:
        """解析systemd状态输出"""
        status_info = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == "Active":
                    status_info["active"] = value
                elif key == "Loaded":
                    status_info["loaded"] = value
                elif key == "Main PID":
                    status_info["main_pid"] = value
        
        return status_info
    
    async def systemd_list_services(self, state: str = None) -> Dict[str, Any]:
        """
        列出systemd服务
        
        Args:
            state: 服务状态过滤 (active, inactive, failed, etc.)
            
        Returns:
            Dict: 服务列表
        """
        try:
            if not self.systemctl_available:
                return {
                    "success": False,
                    "error": "systemctl不可用"
                }
            
            args = ["list-units", "--type=service"]
            if state:
                args.extend(["--state", state])
            
            result = await self.execute_command("systemctl", args)
            
            if result["success"]:
                services = self._parse_systemd_list(result["stdout"])
                return {
                    "success": True,
                    "services": services,
                    "count": len(services)
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_systemd_list(self, output: str) -> List[Dict[str, str]]:
        """解析systemd服务列表输出"""
        services = []
        lines = output.split('\n')
        
        # 跳过标题行
        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "UNIT" in line and "LOAD" in line:
                data_started = True
                continue
            
            if data_started and not line.startswith('●') and '.service' in line:
                parts = line.split()
                if len(parts) >= 4:
                    services.append({
                        "unit": parts[0],
                        "load": parts[1],
                        "active": parts[2],
                        "sub": parts[3],
                        "description": ' '.join(parts[4:]) if len(parts) > 4 else ""
                    })
        
        return services
    
    # ==================== Docker 集成 ====================
    
    async def docker_run(self, image: str, command: str = None, 
                        options: List[str] = None, 
                        volumes: List[str] = None,
                        ports: List[str] = None) -> Dict[str, Any]:
        """
        运行Docker容器
        
        Args:
            image: 镜像名
            command: 要执行的命令
            options: Docker选项
            volumes: 卷挂载
            ports: 端口映射
            
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
            
            if volumes:
                for volume in volumes:
                    args.extend(["-v", volume])
            
            if ports:
                for port in ports:
                    args.extend(["-p", port])
            
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
    
    async def docker_build(self, dockerfile_path: str, tag: str, 
                          build_args: Dict[str, str] = None) -> Dict[str, Any]:
        """
        构建Docker镜像
        
        Args:
            dockerfile_path: Dockerfile路径
            tag: 镜像标签
            build_args: 构建参数
            
        Returns:
            Dict: 构建结果
        """
        try:
            if not self.docker_available:
                return {
                    "success": False,
                    "error": "Docker不可用"
                }
            
            args = ["build", "-t", tag]
            
            if build_args:
                for key, value in build_args.items():
                    args.extend(["--build-arg", f"{key}={value}"])
            
            args.append(dockerfile_path)
            
            result = await self.execute_command("docker", args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "dockerfile_path": dockerfile_path,
                "tag": tag
            }
    
    async def docker_list_containers(self, all_containers: bool = False) -> Dict[str, Any]:
        """
        列出Docker容器
        
        Args:
            all_containers: 是否列出所有容器（包括停止的）
            
        Returns:
            Dict: 容器列表
        """
        try:
            if not self.docker_available:
                return {
                    "success": False,
                    "error": "Docker不可用"
                }
            
            args = ["ps"]
            if all_containers:
                args.append("-a")
            
            result = await self.execute_command("docker", args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 系统信息和能力 ====================
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取Linux平台能力"""
        return {
            "platform": self.platform,
            "distribution": self.distribution,
            "distribution_version": self.distribution_version,
            "package_manager": self.package_manager,
            "init_system": self.init_system,
            "docker_available": self.docker_available,
            "systemctl_available": self.systemctl_available,
            "snap_available": self.snap_available,
            "flatpak_available": self.flatpak_available,
            "supported_features": {
                "package_management": self.package_manager != "unknown",
                "service_management": self.systemctl_available,
                "docker_integration": self.docker_available,
                "snap_packages": self.snap_available,
                "flatpak_packages": self.flatpak_available
            },
            "package_capabilities": {
                "install_packages": self.package_manager != "unknown",
                "remove_packages": self.package_manager != "unknown",
                "update_package_list": self.package_manager != "unknown",
                "upgrade_packages": self.package_manager != "unknown",
                "search_packages": self.package_manager != "unknown",
                "list_installed": self.package_manager != "unknown"
            },
            "service_capabilities": {
                "start_services": self.systemctl_available,
                "stop_services": self.systemctl_available,
                "restart_services": self.systemctl_available,
                "enable_services": self.systemctl_available,
                "disable_services": self.systemctl_available,
                "service_status": self.systemctl_available,
                "list_services": self.systemctl_available
            },
            "docker_capabilities": {
                "run_containers": self.docker_available,
                "build_images": self.docker_available,
                "list_containers": self.docker_available
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "platform": self.platform,
            "distribution": self.distribution,
            "distribution_version": self.distribution_version,
            "package_manager": self.package_manager,
            "init_system": self.init_system,
            "docker_available": self.docker_available,
            "systemctl_available": self.systemctl_available,
            "snap_available": self.snap_available,
            "flatpak_available": self.flatpak_available,
            "ready": True
        }

