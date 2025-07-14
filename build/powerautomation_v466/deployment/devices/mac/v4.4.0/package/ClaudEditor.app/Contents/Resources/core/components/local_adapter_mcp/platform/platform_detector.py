"""
Platform Detector - 平台检测器
检测和识别不同操作系统平台，提供平台特定的能力信息

支持平台：macOS、Windows、Linux、WSL
"""

import os
import sys
import platform
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
import logging

class PlatformDetector:
    """平台检测器 - 检测和识别操作系统平台"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._platform_cache = None
        self._capabilities_cache = None
    
    def detect_platform(self) -> str:
        """
        检测当前平台
        
        Returns:
            str: 平台名称 ('macos', 'windows', 'linux', 'wsl')
        """
        if self._platform_cache:
            return self._platform_cache
        
        system = platform.system().lower()
        
        if system == "darwin":
            self._platform_cache = "macos"
        elif system == "windows":
            self._platform_cache = "windows"
        elif system == "linux":
            # 检查是否是WSL
            if self._is_wsl():
                self._platform_cache = "wsl"
            else:
                self._platform_cache = "linux"
        else:
            self.logger.warning(f"未知平台: {system}，默认为linux")
            self._platform_cache = "linux"
        
        self.logger.info(f"检测到平台: {self._platform_cache}")
        return self._platform_cache
    
    def _is_wsl(self) -> bool:
        """检查是否运行在WSL环境中"""
        try:
            # 方法1: 检查 /proc/version
            if os.path.exists("/proc/version"):
                with open("/proc/version", "r") as f:
                    version_info = f.read().lower()
                    if "microsoft" in version_info or "wsl" in version_info:
                        return True
            
            # 方法2: 检查环境变量
            if "WSL_DISTRO_NAME" in os.environ:
                return True
            
            # 方法3: 检查 /proc/sys/kernel/osrelease
            if os.path.exists("/proc/sys/kernel/osrelease"):
                with open("/proc/sys/kernel/osrelease", "r") as f:
                    release_info = f.read().lower()
                    if "microsoft" in release_info or "wsl" in release_info:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"WSL检测失败: {e}")
            return False
    
    def get_platform_info(self) -> Dict[str, str]:
        """
        获取详细的平台信息
        
        Returns:
            Dict: 包含平台详细信息的字典
        """
        current_platform = self.detect_platform()
        
        info = {
            "platform": current_platform,
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version()
        }
        
        # 添加平台特定信息
        if current_platform == "macos":
            info.update(self._get_macos_info())
        elif current_platform == "windows":
            info.update(self._get_windows_info())
        elif current_platform == "linux":
            info.update(self._get_linux_info())
        elif current_platform == "wsl":
            info.update(self._get_wsl_info())
        
        return info
    
    def _get_macos_info(self) -> Dict[str, str]:
        """获取macOS特定信息"""
        info = {}
        
        try:
            # macOS版本
            result = subprocess.run(["sw_vers", "-productVersion"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info["macos_version"] = result.stdout.strip()
            
            # 检查Apple Silicon
            if platform.machine() == "arm64":
                info["apple_silicon"] = "true"
                info["chip_type"] = "Apple Silicon (M1/M2/M3)"
            else:
                info["apple_silicon"] = "false"
                info["chip_type"] = "Intel"
            
            # 检查Xcode
            if shutil.which("xcode-select"):
                result = subprocess.run(["xcode-select", "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info["xcode_tools"] = "installed"
                else:
                    info["xcode_tools"] = "not_installed"
            
            # 检查Homebrew
            if shutil.which("brew"):
                info["homebrew"] = "installed"
            else:
                info["homebrew"] = "not_installed"
                
        except Exception as e:
            self.logger.debug(f"获取macOS信息失败: {e}")
        
        return info
    
    def _get_windows_info(self) -> Dict[str, str]:
        """获取Windows特定信息"""
        info = {}
        
        try:
            # Windows版本
            info["windows_version"] = platform.win32_ver()[0]
            info["windows_edition"] = platform.win32_edition()
            
            # 检查PowerShell
            if shutil.which("powershell") or shutil.which("pwsh"):
                info["powershell"] = "installed"
            else:
                info["powershell"] = "not_installed"
            
            # 检查Windows Terminal
            try:
                result = subprocess.run(["wt", "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info["windows_terminal"] = "installed"
                else:
                    info["windows_terminal"] = "not_installed"
            except:
                info["windows_terminal"] = "not_installed"
            
            # 检查包管理器
            if shutil.which("winget"):
                info["winget"] = "installed"
            else:
                info["winget"] = "not_installed"
            
            if shutil.which("choco"):
                info["chocolatey"] = "installed"
            else:
                info["chocolatey"] = "not_installed"
            
            # 检查WSL
            try:
                result = subprocess.run(["wsl", "--list"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info["wsl_available"] = "true"
                else:
                    info["wsl_available"] = "false"
            except:
                info["wsl_available"] = "false"
                
        except Exception as e:
            self.logger.debug(f"获取Windows信息失败: {e}")
        
        return info
    
    def _get_linux_info(self) -> Dict[str, str]:
        """获取Linux特定信息"""
        info = {}
        
        try:
            # 发行版信息
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("ID="):
                            info["distribution"] = line.split("=")[1].strip().strip('"')
                        elif line.startswith("VERSION_ID="):
                            info["distribution_version"] = line.split("=")[1].strip().strip('"')
                        elif line.startswith("PRETTY_NAME="):
                            info["distribution_name"] = line.split("=")[1].strip().strip('"')
            
            # 包管理器检测
            package_managers = {
                "apt": ["apt", "apt-get"],
                "yum": ["yum"],
                "dnf": ["dnf"],
                "pacman": ["pacman"],
                "zypper": ["zypper"],
                "apk": ["apk"]
            }
            
            detected_managers = []
            for manager, commands in package_managers.items():
                for cmd in commands:
                    if shutil.which(cmd):
                        detected_managers.append(manager)
                        break
            
            info["package_managers"] = ",".join(detected_managers)
            
            # 检查Docker
            if shutil.which("docker"):
                info["docker"] = "installed"
            else:
                info["docker"] = "not_installed"
            
            # 检查systemd
            if os.path.exists("/run/systemd/system"):
                info["init_system"] = "systemd"
            else:
                info["init_system"] = "other"
                
        except Exception as e:
            self.logger.debug(f"获取Linux信息失败: {e}")
        
        return info
    
    def _get_wsl_info(self) -> Dict[str, str]:
        """获取WSL特定信息"""
        info = self._get_linux_info()  # 继承Linux信息
        
        try:
            # WSL版本
            if "WSL_DISTRO_NAME" in os.environ:
                info["wsl_distro"] = os.environ["WSL_DISTRO_NAME"]
            
            # 检查Windows文件系统访问
            if os.path.exists("/mnt/c"):
                info["windows_fs_access"] = "true"
                info["windows_drive_mount"] = "/mnt/c"
            else:
                info["windows_fs_access"] = "false"
            
            # 检查WSL版本
            try:
                result = subprocess.run(["wsl.exe", "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info["wsl_version"] = "2"
                else:
                    info["wsl_version"] = "1"
            except:
                info["wsl_version"] = "unknown"
            
            # 检查Windows可执行文件访问
            if shutil.which("cmd.exe") or shutil.which("powershell.exe"):
                info["windows_exe_access"] = "true"
            else:
                info["windows_exe_access"] = "false"
                
        except Exception as e:
            self.logger.debug(f"获取WSL信息失败: {e}")
        
        return info
    
    def get_terminal_capabilities(self, platform: Optional[str] = None) -> Dict[str, List[str]]:
        """
        获取平台特定的终端能力
        
        Args:
            platform: 指定平台，如果为None则使用当前平台
            
        Returns:
            Dict: 包含各种能力的字典
        """
        if self._capabilities_cache and platform is None:
            return self._capabilities_cache
        
        target_platform = platform or self.detect_platform()
        
        capabilities = {
            "shells": [],
            "package_managers": [],
            "development_tools": [],
            "terminal_apps": [],
            "special_features": []
        }
        
        if target_platform == "macos":
            capabilities.update({
                "shells": ["zsh", "bash", "fish"],
                "package_managers": ["brew", "macports"],
                "development_tools": ["xcode", "xcode-select", "git", "node", "python"],
                "terminal_apps": ["Terminal", "iTerm2", "Hyper", "Alacritty"],
                "special_features": ["codesign", "spotlight", "apple_silicon", "universal_binaries"]
            })
        
        elif target_platform == "windows":
            capabilities.update({
                "shells": ["powershell", "cmd", "bash", "zsh"],
                "package_managers": ["winget", "chocolatey", "scoop"],
                "development_tools": ["visual_studio", "dotnet", "git", "node", "python"],
                "terminal_apps": ["Windows Terminal", "PowerShell", "Command Prompt", "Git Bash"],
                "special_features": ["wsl_integration", "windows_subsystem", "registry_access", "com_objects"]
            })
        
        elif target_platform == "linux":
            capabilities.update({
                "shells": ["bash", "zsh", "fish", "dash"],
                "package_managers": ["apt", "yum", "dnf", "pacman", "zypper", "apk"],
                "development_tools": ["gcc", "make", "git", "docker", "node", "python"],
                "terminal_apps": ["gnome-terminal", "konsole", "xterm", "alacritty"],
                "special_features": ["systemd", "containers", "package_managers", "kernel_modules"]
            })
        
        elif target_platform == "wsl":
            capabilities.update({
                "shells": ["bash", "zsh", "fish"],
                "package_managers": ["apt", "snap"],  # 通常是Ubuntu
                "development_tools": ["gcc", "make", "git", "node", "python", "docker"],
                "terminal_apps": ["Windows Terminal", "WSL Terminal"],
                "special_features": ["windows_integration", "file_bridge", "network_sharing", "dual_system"]
            })
        
        # 检查实际可用的工具
        capabilities = self._verify_capabilities(capabilities)
        
        if platform is None:
            self._capabilities_cache = capabilities
        
        return capabilities
    
    def _verify_capabilities(self, capabilities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """验证能力是否实际可用"""
        verified = {}
        
        for category, items in capabilities.items():
            verified[category] = []
            for item in items:
                if self._is_capability_available(item, category):
                    verified[category].append(item)
        
        return verified
    
    def _is_capability_available(self, capability: str, category: str) -> bool:
        """检查特定能力是否可用"""
        try:
            if category == "shells":
                return shutil.which(capability) is not None
            elif category == "package_managers":
                return shutil.which(capability) is not None
            elif category == "development_tools":
                return shutil.which(capability) is not None
            elif category == "terminal_apps":
                # 终端应用检查比较复杂，这里简化处理
                return True
            elif category == "special_features":
                return self._check_special_feature(capability)
            else:
                return True
                
        except Exception:
            return False
    
    def _check_special_feature(self, feature: str) -> bool:
        """检查特殊功能是否可用"""
        try:
            if feature == "codesign":
                return shutil.which("codesign") is not None
            elif feature == "spotlight":
                return shutil.which("mdfind") is not None
            elif feature == "apple_silicon":
                return platform.machine() == "arm64" and self.detect_platform() == "macos"
            elif feature == "wsl_integration":
                return self.detect_platform() == "windows" and shutil.which("wsl") is not None
            elif feature == "systemd":
                return os.path.exists("/run/systemd/system")
            elif feature == "docker":
                return shutil.which("docker") is not None
            elif feature == "windows_integration":
                return self.detect_platform() == "wsl" and os.path.exists("/mnt/c")
            elif feature == "file_bridge":
                return self.detect_platform() == "wsl" and os.path.exists("/mnt/c")
            else:
                return True
                
        except Exception:
            return False
    
    def get_recommended_tools(self, platform: Optional[str] = None) -> Dict[str, str]:
        """
        获取推荐的工具
        
        Args:
            platform: 指定平台，如果为None则使用当前平台
            
        Returns:
            Dict: 推荐工具的字典
        """
        target_platform = platform or self.detect_platform()
        
        recommendations = {}
        
        if target_platform == "macos":
            recommendations = {
                "package_manager": "brew",
                "shell": "zsh",
                "terminal": "iTerm2",
                "editor": "vim",
                "git": "git",
                "node_manager": "nvm",
                "python_manager": "pyenv"
            }
        
        elif target_platform == "windows":
            recommendations = {
                "package_manager": "winget",
                "shell": "powershell",
                "terminal": "Windows Terminal",
                "editor": "notepad++",
                "git": "git",
                "node_manager": "nvm-windows",
                "python_manager": "pyenv-win"
            }
        
        elif target_platform == "linux":
            recommendations = {
                "package_manager": "apt",  # 根据发行版可能不同
                "shell": "bash",
                "terminal": "gnome-terminal",
                "editor": "vim",
                "git": "git",
                "node_manager": "nvm",
                "python_manager": "pyenv"
            }
        
        elif target_platform == "wsl":
            recommendations = {
                "package_manager": "apt",
                "shell": "bash",
                "terminal": "Windows Terminal",
                "editor": "vim",
                "git": "git",
                "node_manager": "nvm",
                "python_manager": "pyenv"
            }
        
        return recommendations
    
    def is_platform_supported(self, platform: str) -> bool:
        """检查平台是否受支持"""
        supported_platforms = ["macos", "windows", "linux", "wsl"]
        return platform.lower() in supported_platforms
    
    def get_platform_limitations(self, platform: Optional[str] = None) -> List[str]:
        """
        获取平台限制
        
        Args:
            platform: 指定平台，如果为None则使用当前平台
            
        Returns:
            List: 平台限制列表
        """
        target_platform = platform or self.detect_platform()
        
        limitations = []
        
        if target_platform == "macos":
            limitations = [
                "需要Apple开发者账户进行代码签名",
                "某些Linux工具可能不可用",
                "Docker需要虚拟化支持"
            ]
        
        elif target_platform == "windows":
            limitations = [
                "路径分隔符差异可能导致脚本问题",
                "某些Unix工具需要额外安装",
                "权限模型与Unix系统不同"
            ]
        
        elif target_platform == "linux":
            limitations = [
                "发行版差异可能导致包管理器不同",
                "某些专有软件可能不可用",
                "GUI应用需要X11或Wayland"
            ]
        
        elif target_platform == "wsl":
            limitations = [
                "性能可能略低于原生Linux",
                "某些系统调用可能不支持",
                "GUI应用需要额外配置"
            ]
        
        return limitations

