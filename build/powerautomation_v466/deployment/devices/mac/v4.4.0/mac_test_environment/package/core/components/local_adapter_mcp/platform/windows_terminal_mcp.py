"""
Windows Terminal MCP Adapter - Windows终端MCP适配器
支持Windows平台特有的终端功能和工具

特性：PowerShell、Winget、Visual Studio、WSL集成等
"""

import asyncio
import subprocess
import os
import json
import logging
import winreg
from typing import Dict, List, Optional, Any
from pathlib import Path

class WindowsTerminalMCP:
    """Windows终端MCP适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.platform = "windows"
        
        # 检查Windows特有工具
        self.powershell_available = self._check_powershell()
        self.winget_available = self._check_winget()
        self.chocolatey_available = self._check_chocolatey()
        self.wsl_available = self._check_wsl()
        self.windows_terminal_available = self._check_windows_terminal()
        
        self.logger.info(f"Windows终端MCP初始化完成 - PowerShell: {self.powershell_available}, Winget: {self.winget_available}, WSL: {self.wsl_available}")
    
    def _check_powershell(self) -> bool:
        """检查PowerShell是否可用"""
        try:
            # 检查PowerShell Core (pwsh) 或 Windows PowerShell (powershell)
            for cmd in ["pwsh", "powershell"]:
                result = subprocess.run([cmd, "-Command", "Get-Host"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_winget(self) -> bool:
        """检查Winget是否可用"""
        try:
            result = subprocess.run(["winget", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_chocolatey(self) -> bool:
        """检查Chocolatey是否可用"""
        try:
            result = subprocess.run(["choco", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_wsl(self) -> bool:
        """检查WSL是否可用"""
        try:
            result = subprocess.run(["wsl", "--list"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_windows_terminal(self) -> bool:
        """检查Windows Terminal是否可用"""
        try:
            result = subprocess.run(["wt", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def execute_command(self, command: str, args: List[str] = None, 
                            working_dir: str = None, env: Dict[str, str] = None,
                            shell: str = "cmd") -> Dict[str, Any]:
        """
        执行Windows命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            shell: 使用的shell (cmd, powershell, pwsh)
            
        Returns:
            Dict: 执行结果
        """
        args = args or []
        
        try:
            self.logger.info(f"执行Windows命令: {command} {' '.join(args)} (shell: {shell})")
            
            # 设置环境变量
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)
            
            # 根据shell类型构建命令
            if shell == "powershell" or shell == "pwsh":
                # PowerShell命令
                ps_command = f"{command} {' '.join(args)}"
                full_command = [shell, "-Command", ps_command]
            else:
                # CMD命令
                full_command = [command] + args
            
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
                "shell": shell
            }
            
            if process.returncode != 0:
                self.logger.warning(f"命令执行失败: {result['stderr']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": f"{command} {' '.join(args)}",
                "working_dir": working_dir,
                "shell": shell
            }
    
    # PowerShell相关方法
    async def execute_powershell_script(self, script: str, 
                                      execution_policy: str = "Bypass") -> Dict[str, Any]:
        """执行PowerShell脚本"""
        if not self.powershell_available:
            return {"success": False, "error": "PowerShell不可用"}
        
        ps_cmd = "pwsh" if subprocess.run(["pwsh", "-Command", "Get-Host"], 
                                        capture_output=True).returncode == 0 else "powershell"
        
        args = ["-ExecutionPolicy", execution_policy, "-Command", script]
        return await self.execute_command(ps_cmd, args)
    
    async def get_powershell_modules(self) -> Dict[str, Any]:
        """获取已安装的PowerShell模块"""
        script = "Get-Module -ListAvailable | Select-Object Name, Version | ConvertTo-Json"
        return await self.execute_powershell_script(script)
    
    async def install_powershell_module(self, module_name: str, scope: str = "CurrentUser") -> Dict[str, Any]:
        """安装PowerShell模块"""
        script = f"Install-Module -Name {module_name} -Scope {scope} -Force"
        return await self.execute_powershell_script(script)
    
    # Winget相关方法
    async def winget_install(self, package: str, source: str = None, 
                           accept_license: bool = True) -> Dict[str, Any]:
        """使用Winget安装包"""
        if not self.winget_available:
            return {"success": False, "error": "Winget不可用"}
        
        args = ["install", package]
        
        if source:
            args.extend(["--source", source])
        
        if accept_license:
            args.append("--accept-package-agreements")
            args.append("--accept-source-agreements")
        
        return await self.execute_command("winget", args)
    
    async def winget_uninstall(self, package: str) -> Dict[str, Any]:
        """使用Winget卸载包"""
        if not self.winget_available:
            return {"success": False, "error": "Winget不可用"}
        
        return await self.execute_command("winget", ["uninstall", package])
    
    async def winget_upgrade(self, package: str = None) -> Dict[str, Any]:
        """使用Winget升级包"""
        if not self.winget_available:
            return {"success": False, "error": "Winget不可用"}
        
        args = ["upgrade"]
        if package:
            args.append(package)
        else:
            args.append("--all")
        
        return await self.execute_command("winget", args)
    
    async def winget_search(self, query: str) -> Dict[str, Any]:
        """使用Winget搜索包"""
        if not self.winget_available:
            return {"success": False, "error": "Winget不可用"}
        
        return await self.execute_command("winget", ["search", query])
    
    async def winget_list(self) -> Dict[str, Any]:
        """列出已安装的包"""
        if not self.winget_available:
            return {"success": False, "error": "Winget不可用"}
        
        return await self.execute_command("winget", ["list"])
    
    # Chocolatey相关方法
    async def choco_install(self, package: str, force: bool = False) -> Dict[str, Any]:
        """使用Chocolatey安装包"""
        if not self.chocolatey_available:
            return {"success": False, "error": "Chocolatey不可用"}
        
        args = ["install", package, "-y"]
        if force:
            args.append("--force")
        
        return await self.execute_command("choco", args)
    
    async def choco_uninstall(self, package: str) -> Dict[str, Any]:
        """使用Chocolatey卸载包"""
        if not self.chocolatey_available:
            return {"success": False, "error": "Chocolatey不可用"}
        
        return await self.execute_command("choco", ["uninstall", package, "-y"])
    
    async def choco_upgrade(self, package: str = None) -> Dict[str, Any]:
        """使用Chocolatey升级包"""
        if not self.chocolatey_available:
            return {"success": False, "error": "Chocolatey不可用"}
        
        args = ["upgrade"]
        if package:
            args.append(package)
        else:
            args.append("all")
        args.append("-y")
        
        return await self.execute_command("choco", args)
    
    # WSL相关方法
    async def wsl_list_distributions(self) -> Dict[str, Any]:
        """列出WSL发行版"""
        if not self.wsl_available:
            return {"success": False, "error": "WSL不可用"}
        
        return await self.execute_command("wsl", ["--list", "--verbose"])
    
    async def wsl_execute_command(self, distribution: str, command: str) -> Dict[str, Any]:
        """在WSL中执行命令"""
        if not self.wsl_available:
            return {"success": False, "error": "WSL不可用"}
        
        args = ["--distribution", distribution, "--exec", command]
        return await self.execute_command("wsl", args)
    
    async def wsl_start_distribution(self, distribution: str) -> Dict[str, Any]:
        """启动WSL发行版"""
        if not self.wsl_available:
            return {"success": False, "error": "WSL不可用"}
        
        return await self.execute_command("wsl", ["--distribution", distribution])
    
    async def wsl_shutdown(self) -> Dict[str, Any]:
        """关闭WSL"""
        if not self.wsl_available:
            return {"success": False, "error": "WSL不可用"}
        
        return await self.execute_command("wsl", ["--shutdown"])
    
    # Visual Studio相关方法
    async def dotnet_build(self, project_path: str, configuration: str = "Release") -> Dict[str, Any]:
        """使用dotnet构建项目"""
        args = ["build", project_path, "--configuration", configuration]
        return await self.execute_command("dotnet", args)
    
    async def dotnet_run(self, project_path: str = None) -> Dict[str, Any]:
        """运行.NET项目"""
        args = ["run"]
        if project_path:
            args.extend(["--project", project_path])
        
        return await self.execute_command("dotnet", args)
    
    async def dotnet_test(self, project_path: str = None) -> Dict[str, Any]:
        """运行.NET测试"""
        args = ["test"]
        if project_path:
            args.append(project_path)
        
        return await self.execute_command("dotnet", args)
    
    async def dotnet_publish(self, project_path: str, output_dir: str, 
                           configuration: str = "Release") -> Dict[str, Any]:
        """发布.NET项目"""
        args = [
            "publish", project_path,
            "--configuration", configuration,
            "--output", output_dir
        ]
        return await self.execute_command("dotnet", args)
    
    # 系统信息方法
    async def get_system_info(self) -> Dict[str, Any]:
        """获取Windows系统信息"""
        try:
            # 使用PowerShell获取系统信息
            script = """
            $info = @{
                OS = (Get-WmiObject -Class Win32_OperatingSystem).Caption
                Version = (Get-WmiObject -Class Win32_OperatingSystem).Version
                Architecture = (Get-WmiObject -Class Win32_OperatingSystem).OSArchitecture
                Processor = (Get-WmiObject -Class Win32_Processor).Name
                Memory = [math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
                Computer = (Get-WmiObject -Class Win32_ComputerSystem).Name
            }
            $info | ConvertTo-Json
            """
            
            result = await self.execute_powershell_script(script)
            
            if result.get("success"):
                try:
                    system_data = json.loads(result["stdout"])
                    info = {
                        "platform": "windows",
                        "os": system_data.get("OS", "unknown"),
                        "version": system_data.get("Version", "unknown"),
                        "architecture": system_data.get("Architecture", "unknown"),
                        "processor": system_data.get("Processor", "unknown"),
                        "memory_gb": system_data.get("Memory", 0),
                        "computer_name": system_data.get("Computer", "unknown"),
                        "powershell_available": self.powershell_available,
                        "winget_available": self.winget_available,
                        "chocolatey_available": self.chocolatey_available,
                        "wsl_available": self.wsl_available,
                        "windows_terminal_available": self.windows_terminal_available
                    }
                    return {"success": True, "info": info}
                except json.JSONDecodeError:
                    pass
            
            # 如果PowerShell方法失败，使用基本方法
            basic_info = {
                "platform": "windows",
                "powershell_available": self.powershell_available,
                "winget_available": self.winget_available,
                "chocolatey_available": self.chocolatey_available,
                "wsl_available": self.wsl_available,
                "windows_terminal_available": self.windows_terminal_available
            }
            
            return {"success": True, "info": basic_info}
            
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {"success": False, "error": str(e)}
    
    # 注册表操作方法
    async def registry_read(self, key_path: str, value_name: str) -> Dict[str, Any]:
        """读取注册表值"""
        try:
            # 解析注册表路径
            parts = key_path.split("\\", 1)
            if len(parts) != 2:
                return {"success": False, "error": "无效的注册表路径"}
            
            root_key_name, sub_key = parts
            
            # 映射根键
            root_keys = {
                "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
                "HKEY_USERS": winreg.HKEY_USERS,
                "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
            }
            
            root_key = root_keys.get(root_key_name)
            if root_key is None:
                return {"success": False, "error": f"未知的根键: {root_key_name}"}
            
            # 读取注册表值
            with winreg.OpenKey(root_key, sub_key) as key:
                value, reg_type = winreg.QueryValueEx(key, value_name)
                
                return {
                    "success": True,
                    "value": value,
                    "type": reg_type,
                    "key_path": key_path,
                    "value_name": value_name
                }
                
        except FileNotFoundError:
            return {"success": False, "error": "注册表键或值不存在"}
        except Exception as e:
            self.logger.error(f"读取注册表失败: {e}")
            return {"success": False, "error": str(e)}
    
    # 服务管理方法
    async def get_services(self, status: str = None) -> Dict[str, Any]:
        """获取Windows服务列表"""
        script = "Get-Service"
        if status:
            script += f" | Where-Object {{$_.Status -eq '{status}'}}"
        script += " | Select-Object Name, Status, DisplayName | ConvertTo-Json"
        
        return await self.execute_powershell_script(script)
    
    async def start_service(self, service_name: str) -> Dict[str, Any]:
        """启动Windows服务"""
        script = f"Start-Service -Name '{service_name}'"
        return await self.execute_powershell_script(script)
    
    async def stop_service(self, service_name: str) -> Dict[str, Any]:
        """停止Windows服务"""
        script = f"Stop-Service -Name '{service_name}'"
        return await self.execute_powershell_script(script)
    
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启Windows服务"""
        script = f"Restart-Service -Name '{service_name}'"
        return await self.execute_powershell_script(script)
    
    # 开发环境方法
    async def setup_development_environment(self, tools: List[str]) -> Dict[str, Any]:
        """设置开发环境"""
        results = {}
        
        for tool in tools:
            if tool == "chocolatey" and not self.chocolatey_available:
                # 安装Chocolatey
                script = """
                Set-ExecutionPolicy Bypass -Scope Process -Force
                [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
                iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
                """
                result = await self.execute_powershell_script(script)
                results["chocolatey"] = result
                
            elif tool == "winget" and not self.winget_available:
                # Winget通常预装在Windows 10/11中
                results["winget"] = {"success": False, "error": "Winget需要手动安装或更新Windows"}
                
            elif tool in ["git", "node", "python", "docker", "vscode"]:
                # 优先使用Winget安装
                if self.winget_available:
                    result = await self.winget_install(tool)
                    results[tool] = result
                elif self.chocolatey_available:
                    result = await self.choco_install(tool)
                    results[tool] = result
                else:
                    results[tool] = {"success": False, "error": "没有可用的包管理器"}
        
        return {"success": True, "results": results}
    
    async def get_installed_programs(self) -> Dict[str, Any]:
        """获取已安装的程序列表"""
        script = """
        Get-WmiObject -Class Win32_Product | 
        Select-Object Name, Version, Vendor | 
        Sort-Object Name | 
        ConvertTo-Json
        """
        return await self.execute_powershell_script(script)
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取Windows平台能力"""
        return {
            "platform": "windows",
            "powershell_available": self.powershell_available,
            "winget_available": self.winget_available,
            "chocolatey_available": self.chocolatey_available,
            "wsl_available": self.wsl_available,
            "windows_terminal_available": self.windows_terminal_available,
            "supported_features": [
                "package_management",
                "powershell_scripting",
                "registry_access",
                "service_management",
                "wsl_integration",
                "dotnet_development",
                "windows_terminal"
            ],
            "development_tools": [
                "visual_studio",
                "dotnet",
                "powershell",
                "git",
                "node",
                "python",
                "docker",
                "wsl"
            ]
        }


            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_chocolatey(self) -> bool:
        """检查Chocolatey是否可用"""
        try:
            result = subprocess.run(["choco", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_wsl(self) -> bool:
        """检查WSL是否可用"""
        try:
            result = subprocess.run(["wsl", "--list"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_windows_terminal(self) -> bool:
        """检查Windows Terminal是否可用"""
        try:
            # 检查Windows Terminal是否安装
            result = subprocess.run(["wt", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def execute_command(self, command: str, args: List[str] = None, 
                            working_dir: str = None, env: Dict[str, str] = None,
                            use_powershell: bool = False) -> Dict[str, Any]:
        """
        执行Windows命令
        
        Args:
            command: 要执行的命令
            args: 命令参数
            working_dir: 工作目录
            env: 环境变量
            use_powershell: 是否使用PowerShell
            
        Returns:
            Dict: 执行结果
        """
        args = args or []
        
        try:
            if use_powershell:
                # 使用PowerShell执行
                ps_command = f"{command} {' '.join(args)}"
                full_command = ["powershell", "-Command", ps_command]
            else:
                # 使用cmd执行
                full_command = [command] + args
            
            self.logger.info(f"执行Windows命令: {' '.join(full_command)}")
            
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
                "use_powershell": use_powershell
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行Windows命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join([command] + args)
            }
    
    # ==================== Winget 包管理功能 ====================
    
    async def winget_search(self, query: str, source: str = None) -> Dict[str, Any]:
        """
        搜索包
        
        Args:
            query: 搜索查询
            source: 包源
            
        Returns:
            Dict: 搜索结果
        """
        try:
            if not self.winget_available:
                return {
                    "success": False,
                    "error": "Winget不可用"
                }
            
            args = ["search", query]
            if source:
                args.extend(["--source", source])
            
            result = await self.execute_command("winget", args)
            
            if result["success"]:
                packages = self._parse_winget_search(result["stdout"])
                return {
                    "success": True,
                    "packages": packages,
                    "count": len(packages),
                    "query": query
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _parse_winget_search(self, output: str) -> List[Dict[str, str]]:
        """解析Winget搜索输出"""
        packages = []
        lines = output.split('\n')
        
        # 跳过标题行
        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "Name" in line and "Id" in line:
                data_started = True
                continue
            
            if data_started and not line.startswith('-'):
                # 解析包信息
                parts = line.split()
                if len(parts) >= 2:
                    packages.append({
                        "name": parts[0],
                        "id": parts[1],
                        "version": parts[2] if len(parts) > 2 else "",
                        "source": parts[3] if len(parts) > 3 else ""
                    })
        
        return packages
    
    async def winget_install(self, package_id: str, version: str = None, 
                           source: str = None, silent: bool = True) -> Dict[str, Any]:
        """
        安装包
        
        Args:
            package_id: 包ID
            version: 指定版本
            source: 包源
            silent: 静默安装
            
        Returns:
            Dict: 安装结果
        """
        try:
            if not self.winget_available:
                return {
                    "success": False,
                    "error": "Winget不可用"
                }
            
            args = ["install", package_id]
            
            if version:
                args.extend(["--version", version])
            
            if source:
                args.extend(["--source", source])
            
            if silent:
                args.append("--silent")
            
            args.append("--accept-package-agreements")
            args.append("--accept-source-agreements")
            
            result = await self.execute_command("winget", args)
            
            if result["success"]:
                self.logger.info(f"Winget安装成功: {package_id}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package_id": package_id
            }
    
    async def winget_uninstall(self, package_id: str, silent: bool = True) -> Dict[str, Any]:
        """
        卸载包
        
        Args:
            package_id: 包ID
            silent: 静默卸载
            
        Returns:
            Dict: 卸载结果
        """
        try:
            if not self.winget_available:
                return {
                    "success": False,
                    "error": "Winget不可用"
                }
            
            args = ["uninstall", package_id]
            
            if silent:
                args.append("--silent")
            
            result = await self.execute_command("winget", args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package_id": package_id
            }
    
    async def winget_upgrade(self, package_id: str = None, all_packages: bool = False) -> Dict[str, Any]:
        """
        升级包
        
        Args:
            package_id: 包ID，如果为None且all_packages为True则升级所有
            all_packages: 是否升级所有包
            
        Returns:
            Dict: 升级结果
        """
        try:
            if not self.winget_available:
                return {
                    "success": False,
                    "error": "Winget不可用"
                }
            
            args = ["upgrade"]
            
            if all_packages:
                args.append("--all")
            elif package_id:
                args.append(package_id)
            
            args.append("--silent")
            args.append("--accept-package-agreements")
            args.append("--accept-source-agreements")
            
            result = await self.execute_command("winget", args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "package_id": package_id
            }
    
    async def winget_list_installed(self) -> Dict[str, Any]:
        """列出已安装的包"""
        try:
            if not self.winget_available:
                return {
                    "success": False,
                    "error": "Winget不可用"
                }
            
            result = await self.execute_command("winget", ["list"])
            
            if result["success"]:
                packages = self._parse_winget_list(result["stdout"])
                return {
                    "success": True,
                    "packages": packages,
                    "count": len(packages)
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_winget_list(self, output: str) -> List[Dict[str, str]]:
        """解析Winget列表输出"""
        packages = []
        lines = output.split('\n')
        
        # 跳过标题行
        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "Name" in line and "Id" in line:
                data_started = True
                continue
            
            if data_started and not line.startswith('-'):
                # 解析包信息
                parts = line.split()
                if len(parts) >= 2:
                    packages.append({
                        "name": parts[0],
                        "id": parts[1],
                        "version": parts[2] if len(parts) > 2 else "",
                        "available": parts[3] if len(parts) > 3 else ""
                    })
        
        return packages
    
    # ==================== Visual Studio 集成 ====================
    
    async def vs_build_solution(self, solution_path: str, configuration: str = "Release", 
                               platform: str = "Any CPU") -> Dict[str, Any]:
        """
        构建Visual Studio解决方案
        
        Args:
            solution_path: 解决方案文件路径
            configuration: 构建配置
            platform: 目标平台
            
        Returns:
            Dict: 构建结果
        """
        try:
            # 查找MSBuild
            msbuild_path = await self._find_msbuild()
            if not msbuild_path:
                return {
                    "success": False,
                    "error": "未找到MSBuild"
                }
            
            args = [
                solution_path,
                f"/p:Configuration={configuration}",
                f"/p:Platform={platform}",
                "/m",  # 多核构建
                "/v:minimal"  # 最小输出
            ]
            
            result = await self.execute_command(msbuild_path, args)
            
            if result["success"]:
                self.logger.info(f"Visual Studio构建成功: {solution_path}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "solution_path": solution_path
            }
    
    async def _find_msbuild(self) -> Optional[str]:
        """查找MSBuild路径"""
        try:
            # 常见的MSBuild路径
            possible_paths = [
                r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
                r"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
                r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
                r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
                r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe",
                r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            
            # 尝试从注册表查找
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                  r"SOFTWARE\Microsoft\MSBuild\ToolsVersions") as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        version = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, version) as version_key:
                                msbuild_path = winreg.QueryValueEx(version_key, "MSBuildToolsPath")[0]
                                full_path = os.path.join(msbuild_path, "MSBuild.exe")
                                if os.path.exists(full_path):
                                    return full_path
                        except:
                            continue
            except:
                pass
            
            return None
            
        except Exception as e:
            self.logger.debug(f"查找MSBuild失败: {e}")
            return None
    
    async def vs_clean_solution(self, solution_path: str, configuration: str = "Release") -> Dict[str, Any]:
        """
        清理Visual Studio解决方案
        
        Args:
            solution_path: 解决方案文件路径
            configuration: 构建配置
            
        Returns:
            Dict: 清理结果
        """
        try:
            msbuild_path = await self._find_msbuild()
            if not msbuild_path:
                return {
                    "success": False,
                    "error": "未找到MSBuild"
                }
            
            args = [
                solution_path,
                f"/p:Configuration={configuration}",
                "/t:Clean",
                "/v:minimal"
            ]
            
            result = await self.execute_command(msbuild_path, args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "solution_path": solution_path
            }
    
    async def vs_restore_packages(self, solution_path: str) -> Dict[str, Any]:
        """
        恢复NuGet包
        
        Args:
            solution_path: 解决方案文件路径
            
        Returns:
            Dict: 恢复结果
        """
        try:
            # 尝试使用dotnet restore
            result = await self.execute_command("dotnet", ["restore", solution_path])
            
            if result["success"]:
                return result
            
            # 如果dotnet不可用，尝试使用nuget
            nuget_result = await self.execute_command("nuget", ["restore", solution_path])
            
            return nuget_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "solution_path": solution_path
            }
    
    # ==================== Windows 服务管理 ====================
    
    async def service_start(self, service_name: str) -> Dict[str, Any]:
        """
        启动Windows服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 启动结果
        """
        try:
            result = await self.execute_command("sc", ["start", service_name])
            
            if result["success"]:
                self.logger.info(f"服务启动成功: {service_name}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def service_stop(self, service_name: str) -> Dict[str, Any]:
        """
        停止Windows服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 停止结果
        """
        try:
            result = await self.execute_command("sc", ["stop", service_name])
            
            if result["success"]:
                self.logger.info(f"服务停止成功: {service_name}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def service_restart(self, service_name: str) -> Dict[str, Any]:
        """
        重启Windows服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 重启结果
        """
        try:
            # 先停止服务
            stop_result = await self.service_stop(service_name)
            
            # 等待一下
            await asyncio.sleep(2)
            
            # 再启动服务
            start_result = await self.service_start(service_name)
            
            return {
                "success": stop_result["success"] and start_result["success"],
                "stop_result": stop_result,
                "start_result": start_result,
                "service_name": service_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def service_status(self, service_name: str) -> Dict[str, Any]:
        """
        获取Windows服务状态
        
        Args:
            service_name: 服务名称
            
        Returns:
            Dict: 服务状态
        """
        try:
            result = await self.execute_command("sc", ["query", service_name])
            
            if result["success"]:
                status_info = self._parse_service_status(result["stdout"])
                return {
                    "success": True,
                    "status_info": status_info,
                    "service_name": service_name
                }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    def _parse_service_status(self, output: str) -> Dict[str, str]:
        """解析服务状态输出"""
        status_info = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                status_info[key] = value
        
        return status_info
    
    async def list_services(self, state: str = None) -> Dict[str, Any]:
        """
        列出Windows服务
        
        Args:
            state: 服务状态过滤 (running, stopped, etc.)
            
        Returns:
            Dict: 服务列表
        """
        try:
            args = ["query"]
            if state:
                args.extend(["state=", state])
            
            result = await self.execute_command("sc", args)
            
            if result["success"]:
                services = self._parse_service_list(result["stdout"])
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
    
    def _parse_service_list(self, output: str) -> List[Dict[str, str]]:
        """解析服务列表输出"""
        services = []
        current_service = {}
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith("SERVICE_NAME:"):
                if current_service:
                    services.append(current_service)
                current_service = {"name": line.split(":", 1)[1].strip()}
            elif line.startswith("DISPLAY_NAME:"):
                current_service["display_name"] = line.split(":", 1)[1].strip()
            elif line.startswith("STATE:"):
                current_service["state"] = line.split(":", 1)[1].strip()
        
        if current_service:
            services.append(current_service)
        
        return services
    
    # ==================== PowerShell 增强功能 ====================
    
    async def powershell_execute_script(self, script_path: str, 
                                      parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行PowerShell脚本
        
        Args:
            script_path: 脚本文件路径
            parameters: 脚本参数
            
        Returns:
            Dict: 执行结果
        """
        try:
            if not self.powershell_available:
                return {
                    "success": False,
                    "error": "PowerShell不可用"
                }
            
            args = ["-ExecutionPolicy", "Bypass", "-File", script_path]
            
            if parameters:
                for key, value in parameters.items():
                    args.extend([f"-{key}", str(value)])
            
            result = await self.execute_command("powershell", args)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "script_path": script_path
            }
    
    async def powershell_get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            script = "Get-ComputerInfo | ConvertTo-Json"
            
            result = await self.execute_command("powershell", ["-Command", script])
            
            if result["success"]:
                try:
                    system_info = json.loads(result["stdout"])
                    return {
                        "success": True,
                        "system_info": system_info
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "raw_output": result["stdout"]
                    }
            else:
                return result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== 系统信息和能力 ====================
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取Windows平台能力"""
        return {
            "platform": self.platform,
            "powershell_available": self.powershell_available,
            "winget_available": self.winget_available,
            "chocolatey_available": self.chocolatey_available,
            "wsl_available": self.wsl_available,
            "windows_terminal_available": self.windows_terminal_available,
            "supported_features": {
                "package_management": self.winget_available or self.chocolatey_available,
                "visual_studio_integration": True,
                "service_management": True,
                "powershell_scripting": self.powershell_available,
                "wsl_integration": self.wsl_available
            },
            "winget_capabilities": {
                "search_packages": self.winget_available,
                "install_packages": self.winget_available,
                "uninstall_packages": self.winget_available,
                "upgrade_packages": self.winget_available,
                "list_installed": self.winget_available
            },
            "visual_studio_capabilities": {
                "build_solutions": True,
                "clean_solutions": True,
                "restore_packages": True
            },
            "service_capabilities": {
                "start_services": True,
                "stop_services": True,
                "restart_services": True,
                "query_status": True,
                "list_services": True
            },
            "powershell_capabilities": {
                "execute_scripts": self.powershell_available,
                "system_information": self.powershell_available,
                "advanced_commands": self.powershell_available
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "platform": self.platform,
            "powershell_available": self.powershell_available,
            "winget_available": self.winget_available,
            "chocolatey_available": self.chocolatey_available,
            "wsl_available": self.wsl_available,
            "windows_terminal_available": self.windows_terminal_available,
            "ready": True
        }

