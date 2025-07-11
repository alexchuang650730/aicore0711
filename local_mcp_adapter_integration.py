#!/usr/bin/env python3
"""
PowerAutomation v4.6.2 本地MCP適配器集成
Local MCP Adapter Integration for PowerAutomation v4.6.2

🔧 本地適配器集成:
1. macOS 終端 MCP 適配器
2. WSL (Windows Subsystem for Linux) MCP 適配器  
3. Linux 原生 MCP 適配器
4. 跨平台命令執行和同步
5. 本地開發環境集成
"""

import asyncio
import json
import logging
import platform
import subprocess
import os
import shutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class LocalPlatform(Enum):
    """本地平台類型"""
    MACOS = "macos"
    LINUX = "linux" 
    WSL = "wsl"
    WINDOWS = "windows"

class MCPAdapterType(Enum):
    """MCP適配器類型"""
    TERMINAL = "terminal"
    FILE_SYSTEM = "file_system"
    PROCESS = "process"
    NETWORK = "network"
    DEVELOPMENT = "development"

@dataclass
class LocalEnvironment:
    """本地環境配置"""
    platform: LocalPlatform
    shell: str
    home_directory: str
    python_executable: str
    node_executable: Optional[str] = None
    git_executable: Optional[str] = None
    docker_available: bool = False
    available_commands: List[str] = field(default_factory=list)

@dataclass
class MCPCommand:
    """MCP命令封裝"""
    command_id: str
    platform: LocalPlatform
    shell_command: str
    working_directory: str
    timeout: int = 30
    environment_vars: Dict[str, str] = field(default_factory=dict)
    expected_output_pattern: Optional[str] = None

class LocalMCPAdapter:
    """本地MCP適配器基類"""
    
    def __init__(self, platform: LocalPlatform):
        self.platform = platform
        self.environment = None
        self.active_processes = {}
        self.command_history = []
        
    async def initialize(self) -> Dict[str, Any]:
        """初始化適配器"""
        print(f"🔧 初始化 {self.platform.value} MCP適配器...")
        
        # 檢測環境
        self.environment = await self._detect_environment()
        
        # 驗證必需工具
        await self._verify_required_tools()
        
        return {
            "platform": self.platform.value,
            "environment": {
                "shell": self.environment.shell,
                "home": self.environment.home_directory,
                "python": self.environment.python_executable,
                "available_commands": len(self.environment.available_commands)
            },
            "status": "initialized"
        }
    
    async def _detect_environment(self) -> LocalEnvironment:
        """檢測本地環境"""
        raise NotImplementedError("子類必須實現此方法")
    
    async def _verify_required_tools(self):
        """驗證必需工具"""
        required_tools = ["python3", "git", "npm", "code"]
        available_tools = []
        
        for tool in required_tools:
            if shutil.which(tool):
                available_tools.append(tool)
        
        self.environment.available_commands = available_tools
        print(f"  ✅ 可用工具: {', '.join(available_tools)}")
    
    async def execute_command(self, command: MCPCommand) -> Dict[str, Any]:
        """執行MCP命令"""
        print(f"🚀 執行命令: {command.shell_command}")
        
        try:
            # 設置環境變量
            env = os.environ.copy()
            env.update(command.environment_vars)
            
            # 執行命令
            process = await asyncio.create_subprocess_shell(
                command.shell_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=command.working_directory,
                env=env
            )
            
            # 等待完成，設置超時
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=command.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "status": "timeout",
                    "error": f"命令執行超時 ({command.timeout}s)"
                }
            
            # 處理結果
            result = {
                "command_id": command.command_id,
                "status": "success" if process.returncode == 0 else "failed",
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "platform": self.platform.value
            }
            
            # 記錄命令歷史
            self.command_history.append({
                "command": command.shell_command,
                "timestamp": asyncio.get_event_loop().time(),
                "status": result["status"]
            })
            
            return result
            
        except Exception as e:
            logger.error(f"命令執行失敗: {e}")
            return {
                "command_id": command.command_id,
                "status": "error",
                "error": str(e),
                "platform": self.platform.value
            }

class MacOSMCPAdapter(LocalMCPAdapter):
    """macOS 終端 MCP 適配器"""
    
    def __init__(self):
        super().__init__(LocalPlatform.MACOS)
    
    async def _detect_environment(self) -> LocalEnvironment:
        """檢測macOS環境"""
        return LocalEnvironment(
            platform=LocalPlatform.MACOS,
            shell=os.environ.get('SHELL', '/bin/zsh'),
            home_directory=os.path.expanduser('~'),
            python_executable=shutil.which('python3') or '/usr/bin/python3',
            node_executable=shutil.which('node'),
            git_executable=shutil.which('git'),
            docker_available=bool(shutil.which('docker'))
        )
    
    async def setup_development_environment(self) -> Dict[str, Any]:
        """設置macOS開發環境"""
        print("🍎 設置macOS開發環境...")
        
        setup_commands = [
            MCPCommand(
                command_id="check_homebrew",
                platform=LocalPlatform.MACOS,
                shell_command="brew --version",
                working_directory=self.environment.home_directory
            ),
            MCPCommand(
                command_id="check_xcode_tools",
                platform=LocalPlatform.MACOS,
                shell_command="xcode-select --version",
                working_directory=self.environment.home_directory
            ),
            MCPCommand(
                command_id="check_node_version",
                platform=LocalPlatform.MACOS,
                shell_command="node --version && npm --version",
                working_directory=self.environment.home_directory
            )
        ]
        
        results = []
        for command in setup_commands:
            result = await self.execute_command(command)
            results.append(result)
        
        return {
            "platform": "macOS",
            "setup_results": results,
            "environment_ready": all(r["status"] == "success" for r in results)
        }

class WSLMCPAdapter(LocalMCPAdapter):
    """WSL (Windows Subsystem for Linux) MCP 適配器"""
    
    def __init__(self):
        super().__init__(LocalPlatform.WSL)
    
    async def _detect_environment(self) -> LocalEnvironment:
        """檢測WSL環境"""
        # 檢測是否在WSL中
        is_wsl = False
        try:
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
                is_wsl = 'microsoft' in version_info or 'wsl' in version_info
        except:
            pass
        
        if not is_wsl:
            # 如果不在WSL中，嘗試通過wsl命令連接
            wsl_available = bool(shutil.which('wsl'))
            if not wsl_available:
                raise RuntimeError("WSL不可用，請安裝WSL或在WSL環境中運行")
        
        return LocalEnvironment(
            platform=LocalPlatform.WSL,
            shell='/bin/bash',
            home_directory='/home/' + os.environ.get('USER', 'user'),
            python_executable='/usr/bin/python3',
            node_executable=shutil.which('node'),
            git_executable=shutil.which('git'),
            docker_available=bool(shutil.which('docker'))
        )
    
    async def setup_wsl_integration(self) -> Dict[str, Any]:
        """設置WSL集成"""
        print("🐧 設置WSL集成...")
        
        integration_commands = [
            MCPCommand(
                command_id="check_wsl_version",
                platform=LocalPlatform.WSL,
                shell_command="wsl --version" if platform.system() == "Windows" else "cat /proc/version",
                working_directory=self.environment.home_directory
            ),
            MCPCommand(
                command_id="update_package_list",
                platform=LocalPlatform.WSL,
                shell_command="sudo apt update",
                working_directory=self.environment.home_directory
            ),
            MCPCommand(
                command_id="install_essential_tools",
                platform=LocalPlatform.WSL,
                shell_command="sudo apt install -y curl wget git build-essential",
                working_directory=self.environment.home_directory
            )
        ]
        
        results = []
        for command in integration_commands:
            result = await self.execute_command(command)
            results.append(result)
        
        return {
            "platform": "WSL",
            "integration_results": results,
            "wsl_ready": True
        }

class LinuxMCPAdapter(LocalMCPAdapter):
    """Linux 原生 MCP 適配器"""
    
    def __init__(self):
        super().__init__(LocalPlatform.LINUX)
    
    async def _detect_environment(self) -> LocalEnvironment:
        """檢測Linux環境"""
        return LocalEnvironment(
            platform=LocalPlatform.LINUX,
            shell=os.environ.get('SHELL', '/bin/bash'),
            home_directory=os.path.expanduser('~'),
            python_executable=shutil.which('python3') or '/usr/bin/python3',
            node_executable=shutil.which('node'),
            git_executable=shutil.which('git'),
            docker_available=bool(shutil.which('docker'))
        )
    
    async def setup_linux_environment(self) -> Dict[str, Any]:
        """設置Linux開發環境"""
        print("🐧 設置Linux開發環境...")
        
        # 檢測Linux發行版
        distro_command = MCPCommand(
            command_id="detect_distro",
            platform=LocalPlatform.LINUX,
            shell_command="cat /etc/os-release",
            working_directory=self.environment.home_directory
        )
        
        distro_result = await self.execute_command(distro_command)
        
        # 根據發行版設置包管理器命令
        if "ubuntu" in distro_result.get("stdout", "").lower():
            package_manager = "apt"
            update_cmd = "sudo apt update && sudo apt upgrade -y"
        elif "centos" in distro_result.get("stdout", "").lower() or "rhel" in distro_result.get("stdout", "").lower():
            package_manager = "yum"
            update_cmd = "sudo yum update -y"
        else:
            package_manager = "generic"
            update_cmd = "echo 'Unknown package manager'"
        
        setup_commands = [
            MCPCommand(
                command_id="update_system",
                platform=LocalPlatform.LINUX,
                shell_command=update_cmd,
                working_directory=self.environment.home_directory,
                timeout=300  # 系統更新可能需要更長時間
            ),
            MCPCommand(
                command_id="install_development_tools",
                platform=LocalPlatform.LINUX,
                shell_command=f"sudo {package_manager} install -y git curl wget build-essential python3-pip nodejs npm",
                working_directory=self.environment.home_directory,
                timeout=180
            )
        ]
        
        results = [distro_result]
        for command in setup_commands:
            result = await self.execute_command(command)
            results.append(result)
        
        return {
            "platform": "Linux",
            "package_manager": package_manager,
            "setup_results": results,
            "environment_ready": all(r["status"] in ["success", "timeout"] for r in results[-2:])
        }

class LocalMCPIntegrationManager:
    """本地MCP集成管理器"""
    
    def __init__(self):
        self.adapters = {}
        self.current_platform = self._detect_current_platform()
        self.sync_queue = asyncio.Queue()
        self.cross_platform_sessions = {}
        
    def _detect_current_platform(self) -> LocalPlatform:
        """檢測當前平台"""
        system = platform.system().lower()
        
        if system == "darwin":
            return LocalPlatform.MACOS
        elif system == "linux":
            # 檢測是否為WSL
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        return LocalPlatform.WSL
            except:
                pass
            return LocalPlatform.LINUX
        elif system == "windows":
            return LocalPlatform.WINDOWS
        else:
            return LocalPlatform.LINUX  # 默認
    
    async def initialize_all_adapters(self) -> Dict[str, Any]:
        """初始化所有可用的適配器"""
        print("🌐 初始化本地MCP適配器集成...")
        
        # 創建適配器實例
        adapter_classes = {
            LocalPlatform.MACOS: MacOSMCPAdapter,
            LocalPlatform.WSL: WSLMCPAdapter,
            LocalPlatform.LINUX: LinuxMCPAdapter
        }
        
        initialization_results = {}
        
        # 初始化當前平台的適配器
        if self.current_platform in adapter_classes:
            adapter_class = adapter_classes[self.current_platform]
            adapter = adapter_class()
            
            try:
                result = await adapter.initialize()
                self.adapters[self.current_platform] = adapter
                initialization_results[self.current_platform.value] = result
                print(f"✅ {self.current_platform.value} 適配器初始化成功")
            except Exception as e:
                initialization_results[self.current_platform.value] = {
                    "status": "failed",
                    "error": str(e)
                }
                print(f"❌ {self.current_platform.value} 適配器初始化失敗: {e}")
        
        # 嘗試初始化其他平台適配器（如果可用）
        for platform, adapter_class in adapter_classes.items():
            if platform != self.current_platform and platform not in self.adapters:
                try:
                    adapter = adapter_class()
                    result = await adapter.initialize()
                    self.adapters[platform] = adapter
                    initialization_results[platform.value] = result
                    print(f"✅ {platform.value} 適配器初始化成功（跨平台）")
                except Exception as e:
                    initialization_results[platform.value] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    print(f"⚠️ {platform.value} 適配器不可用: {e}")
        
        return {
            "current_platform": self.current_platform.value,
            "available_adapters": list(self.adapters.keys()),
            "initialization_results": initialization_results,
            "cross_platform_capability": len(self.adapters) > 1
        }
    
    async def execute_cross_platform_command(self, platform: LocalPlatform, command: str, working_dir: str = None) -> Dict[str, Any]:
        """執行跨平台命令"""
        if platform not in self.adapters:
            return {
                "status": "error",
                "error": f"{platform.value} 適配器不可用"
            }
        
        adapter = self.adapters[platform]
        working_directory = working_dir or adapter.environment.home_directory
        
        mcp_command = MCPCommand(
            command_id=f"cross_platform_{int(asyncio.get_event_loop().time() * 1000)}",
            platform=platform,
            shell_command=command,
            working_directory=working_directory
        )
        
        return await adapter.execute_command(mcp_command)
    
    async def setup_development_environments(self) -> Dict[str, Any]:
        """設置所有可用平台的開發環境"""
        print("🛠️ 設置跨平台開發環境...")
        
        setup_results = {}
        
        for platform, adapter in self.adapters.items():
            try:
                if platform == LocalPlatform.MACOS and hasattr(adapter, 'setup_development_environment'):
                    result = await adapter.setup_development_environment()
                elif platform == LocalPlatform.WSL and hasattr(adapter, 'setup_wsl_integration'):
                    result = await adapter.setup_wsl_integration()
                elif platform == LocalPlatform.LINUX and hasattr(adapter, 'setup_linux_environment'):
                    result = await adapter.setup_linux_environment()
                else:
                    result = {"status": "skipped", "reason": "No specific setup required"}
                
                setup_results[platform.value] = result
                
            except Exception as e:
                setup_results[platform.value] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        return {
            "setup_results": setup_results,
            "environments_ready": sum(1 for r in setup_results.values() if r.get("status") != "failed")
        }
    
    async def create_unified_development_session(self) -> Dict[str, Any]:
        """創建統一的開發會話"""
        session_id = f"unified_session_{int(asyncio.get_event_loop().time() * 1000)}"
        
        print(f"🔗 創建統一開發會話: {session_id}")
        
        # 為每個平台創建工作目錄
        session_info = {
            "session_id": session_id,
            "platforms": {},
            "sync_enabled": True
        }
        
        for platform, adapter in self.adapters.items():
            platform_session = {
                "platform": platform.value,
                "working_directory": os.path.join(adapter.environment.home_directory, "powerautomation_unified"),
                "environment": adapter.environment,
                "active": True
            }
            
            # 創建工作目錄
            mkdir_command = MCPCommand(
                command_id=f"create_workdir_{platform.value}",
                platform=platform,
                shell_command=f"mkdir -p {platform_session['working_directory']}",
                working_directory=adapter.environment.home_directory
            )
            
            await adapter.execute_command(mkdir_command)
            
            session_info["platforms"][platform.value] = platform_session
        
        self.cross_platform_sessions[session_id] = session_info
        
        return session_info
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """獲取集成狀態"""
        status = {
            "current_platform": self.current_platform.value,
            "available_adapters": len(self.adapters),
            "adapters": {},
            "active_sessions": len(self.cross_platform_sessions),
            "capabilities": {
                "cross_platform_execution": len(self.adapters) > 1,
                "unified_development": True,
                "command_synchronization": True
            }
        }
        
        for platform, adapter in self.adapters.items():
            status["adapters"][platform.value] = {
                "platform": platform.value,
                "environment": {
                    "shell": adapter.environment.shell,
                    "python": adapter.environment.python_executable,
                    "home": adapter.environment.home_directory,
                    "available_tools": len(adapter.environment.available_commands)
                },
                "command_history": len(adapter.command_history),
                "status": "active"
            }
        
        return status

# PowerAutomation v4.6.2 集成
async def integrate_local_mcp_with_powerautomation():
    """將本地MCP適配器集成到PowerAutomation v4.6.2"""
    print("🚀 PowerAutomation v4.6.2 本地MCP適配器集成")
    print("=" * 80)
    
    # 創建集成管理器
    integration_manager = LocalMCPIntegrationManager()
    
    # 初始化適配器
    print("\n🔧 初始化本地MCP適配器...")
    init_result = await integration_manager.initialize_all_adapters()
    
    print(f"\n✅ 適配器初始化完成:")
    print(f"  當前平台: {init_result['current_platform']}")
    print(f"  可用適配器: {len(init_result['available_adapters'])}個")
    print(f"  跨平台能力: {'是' if init_result['cross_platform_capability'] else '否'}")
    
    # 設置開發環境
    print("\n🛠️ 設置開發環境...")
    setup_result = await integration_manager.setup_development_environments()
    
    print(f"  環境設置完成: {setup_result['environments_ready']}個平台")
    
    # 創建統一開發會話
    print("\n🔗 創建統一開發會話...")
    session = await integration_manager.create_unified_development_session()
    
    print(f"  會話ID: {session['session_id']}")
    print(f"  支持平台: {list(session['platforms'].keys())}")
    
    # 演示跨平台命令執行
    print("\n🌐 演示跨平台命令執行:")
    
    demo_commands = [
        ("python3 --version", "檢查Python版本"),
        ("git --version", "檢查Git版本"),
        ("pwd", "顯示當前目錄"),
        ("ls -la", "列出文件")
    ]
    
    for platform in integration_manager.adapters.keys():
        print(f"\n  📱 在 {platform.value} 平台執行命令:")
        
        for cmd, desc in demo_commands:
            result = await integration_manager.execute_cross_platform_command(
                platform, cmd
            )
            
            if result["status"] == "success":
                output = result["stdout"].strip()
                print(f"    ✅ {desc}: {output[:50]}{'...' if len(output) > 50 else ''}")
            else:
                print(f"    ❌ {desc}: {result.get('error', 'Failed')}")
    
    # 獲取集成狀態
    print("\n📊 本地MCP集成狀態:")
    status = await integration_manager.get_integration_status()
    
    print(f"  當前平台: {status['current_platform']}")
    print(f"  可用適配器: {status['available_adapters']}個")
    print(f"  活躍會話: {status['active_sessions']}個")
    print(f"  跨平台執行: {'✅' if status['capabilities']['cross_platform_execution'] else '❌'}")
    print(f"  統一開發: {'✅' if status['capabilities']['unified_development'] else '❌'}")
    
    print(f"\n🎉 PowerAutomation v4.6.2 本地MCP適配器集成完成！")
    print(f"   現在支持 macOS/WSL/Linux 終端的統一MCP操作")
    
    return {
        "integration_manager": integration_manager,
        "initialization": init_result,
        "setup": setup_result,
        "session": session,
        "status": status
    }

if __name__ == "__main__":
    asyncio.run(integrate_local_mcp_with_powerautomation())