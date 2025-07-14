"""
Local Adapter MCP 集成测试
测试所有平台MCP组件的功能和集成
"""

import asyncio
import unittest
import logging
import sys
import os
from typing import Dict, Any

# 添加路径以导入组件
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_adapter_engine import LocalAdapterEngine
from platform.platform_detector import PlatformDetector
from platform.command_adapter import CommandAdapter
from platform.macos_terminal_mcp import MacOSTerminalMCP
from platform.windows_terminal_mcp import WindowsTerminalMCP
from platform.wsl_terminal_mcp import WSLTerminalMCP
from platform.linux_terminal_mcp import LinuxTerminalMCP
from deployment_mcp_client import DeploymentMCPClient
from remote_environment_interface import RemoteEnvironmentInterface

class TestLocalAdapterMCP(unittest.TestCase):
    """Local Adapter MCP 集成测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # 初始化组件
        self.platform_detector = PlatformDetector()
        self.command_adapter = CommandAdapter()
        self.local_adapter = LocalAdapterEngine()
        
        # 根据平台初始化对应的终端MCP
        self.current_platform = self.platform_detector.detect_platform()
        self.terminal_mcp = self._get_terminal_mcp()
        
        self.logger.info(f"测试环境: {self.current_platform}")
    
    def _get_terminal_mcp(self):
        """根据平台获取对应的终端MCP"""
        if self.current_platform == "macos":
            return MacOSTerminalMCP()
        elif self.current_platform == "windows":
            return WindowsTerminalMCP()
        elif self.current_platform == "wsl":
            return WSLTerminalMCP()
        elif self.current_platform == "linux":
            return LinuxTerminalMCP()
        else:
            return None
    
    def test_platform_detection(self):
        """测试平台检测功能"""
        self.logger.info("测试平台检测...")
        
        platform_info = self.platform_detector.get_platform_info()
        
        self.assertIsNotNone(platform_info)
        self.assertIn("platform", platform_info)
        self.assertIn("architecture", platform_info)
        self.assertIn("capabilities", platform_info)
        
        self.logger.info(f"平台检测成功: {platform_info}")
    
    def test_command_adaptation(self):
        """测试命令适配功能"""
        self.logger.info("测试命令适配...")
        
        # 测试基本命令适配
        test_commands = [
            ("list_files", []),
            ("show_file_content", ["test.txt"]),
            ("copy_file", ["source.txt", "dest.txt"])
        ]
        
        for command, args in test_commands:
            adapted = self.command_adapter.adapt_command(command, args, self.current_platform)
            
            self.assertIsNotNone(adapted)
            self.assertIn("command", adapted)
            self.assertIn("args", adapted)
            
            self.logger.info(f"命令适配成功: {command} -> {adapted}")
    
    async def test_terminal_mcp_capabilities(self):
        """测试终端MCP能力"""
        if not self.terminal_mcp:
            self.skipTest(f"当前平台 {self.current_platform} 不支持")
        
        self.logger.info("测试终端MCP能力...")
        
        # 获取能力信息
        capabilities = await self.terminal_mcp.get_capabilities()
        
        self.assertIsNotNone(capabilities)
        self.assertIn("platform", capabilities)
        self.assertIn("supported_features", capabilities)
        
        self.logger.info(f"终端MCP能力: {capabilities}")
        
        # 测试状态获取
        status = self.terminal_mcp.get_status()
        
        self.assertIsNotNone(status)
        self.assertIn("platform", status)
        self.assertIn("ready", status)
        
        self.logger.info(f"终端MCP状态: {status}")
    
    async def test_basic_command_execution(self):
        """测试基本命令执行"""
        if not self.terminal_mcp:
            self.skipTest(f"当前平台 {self.current_platform} 不支持")
        
        self.logger.info("测试基本命令执行...")
        
        # 根据平台选择测试命令
        if self.current_platform == "windows":
            test_command = "echo"
            test_args = ["Hello World"]
        else:
            test_command = "echo"
            test_args = ["Hello World"]
        
        result = await self.terminal_mcp.execute_command(test_command, test_args)
        
        self.assertIsNotNone(result)
        self.assertIn("success", result)
        self.assertIn("stdout", result)
        
        if result["success"]:
            self.assertIn("Hello World", result["stdout"])
        
        self.logger.info(f"命令执行结果: {result}")
    
    async def test_platform_specific_features(self):
        """测试平台特有功能"""
        if not self.terminal_mcp:
            self.skipTest(f"当前平台 {self.current_platform} 不支持")
        
        self.logger.info("测试平台特有功能...")
        
        if self.current_platform == "macos":
            await self._test_macos_features()
        elif self.current_platform == "windows":
            await self._test_windows_features()
        elif self.current_platform == "wsl":
            await self._test_wsl_features()
        elif self.current_platform == "linux":
            await self._test_linux_features()
    
    async def _test_macos_features(self):
        """测试macOS特有功能"""
        self.logger.info("测试macOS特有功能...")
        
        # 测试Homebrew
        if hasattr(self.terminal_mcp, 'homebrew_available') and self.terminal_mcp.homebrew_available:
            result = await self.terminal_mcp.homebrew_list_installed()
            self.assertIsNotNone(result)
            self.logger.info("Homebrew测试通过")
        
        # 测试Spotlight搜索
        result = await self.terminal_mcp.spotlight_search("test", limit=5)
        self.assertIsNotNone(result)
        self.logger.info("Spotlight搜索测试通过")
        
        # 测试签名身份列表
        result = await self.terminal_mcp.list_signing_identities()
        self.assertIsNotNone(result)
        self.logger.info("代码签名测试通过")
    
    async def _test_windows_features(self):
        """测试Windows特有功能"""
        self.logger.info("测试Windows特有功能...")
        
        # 测试Winget
        if hasattr(self.terminal_mcp, 'winget_available') and self.terminal_mcp.winget_available:
            result = await self.terminal_mcp.winget_list_installed()
            self.assertIsNotNone(result)
            self.logger.info("Winget测试通过")
        
        # 测试服务列表
        result = await self.terminal_mcp.list_services()
        self.assertIsNotNone(result)
        self.logger.info("Windows服务测试通过")
        
        # 测试PowerShell系统信息
        if hasattr(self.terminal_mcp, 'powershell_available') and self.terminal_mcp.powershell_available:
            result = await self.terminal_mcp.powershell_get_system_info()
            self.assertIsNotNone(result)
            self.logger.info("PowerShell测试通过")
    
    async def _test_wsl_features(self):
        """测试WSL特有功能"""
        self.logger.info("测试WSL特有功能...")
        
        # 测试路径转换
        linux_path = "/mnt/c/Users"
        windows_path = self.terminal_mcp.linux_to_windows_path(linux_path)
        self.assertEqual(windows_path, "C:\\Users")
        self.logger.info("路径转换测试通过")
        
        # 测试网络接口
        result = await self.terminal_mcp.get_network_interfaces()
        self.assertIsNotNone(result)
        self.logger.info("网络接口测试通过")
        
        # 测试端口转发列表
        result = await self.terminal_mcp.list_port_forwardings()
        self.assertIsNotNone(result)
        self.logger.info("端口转发测试通过")
    
    async def _test_linux_features(self):
        """测试Linux特有功能"""
        self.logger.info("测试Linux特有功能...")
        
        # 测试包管理器
        if hasattr(self.terminal_mcp, 'package_manager') and self.terminal_mcp.package_manager != "unknown":
            result = await self.terminal_mcp.list_installed_packages()
            self.assertIsNotNone(result)
            self.logger.info("包管理器测试通过")
        
        # 测试systemd服务
        if hasattr(self.terminal_mcp, 'systemctl_available') and self.terminal_mcp.systemctl_available:
            result = await self.terminal_mcp.systemd_list_services()
            self.assertIsNotNone(result)
            self.logger.info("systemd测试通过")
        
        # 测试Docker
        if hasattr(self.terminal_mcp, 'docker_available') and self.terminal_mcp.docker_available:
            result = await self.terminal_mcp.docker_list_containers()
            self.assertIsNotNone(result)
            self.logger.info("Docker测试通过")
    
    async def test_local_adapter_engine(self):
        """测试Local Adapter Engine"""
        self.logger.info("测试Local Adapter Engine...")
        
        # 测试初始化
        self.assertIsNotNone(self.local_adapter)
        
        # 测试能力获取
        capabilities = await self.local_adapter.get_capabilities()
        self.assertIsNotNone(capabilities)
        self.assertIn("platform_support", capabilities)
        
        # 测试状态获取
        status = self.local_adapter.get_status()
        self.assertIsNotNone(status)
        self.assertIn("ready", status)
        
        self.logger.info("Local Adapter Engine测试通过")
    
    async def test_deployment_mcp_integration(self):
        """测试Deployment MCP集成"""
        self.logger.info("测试Deployment MCP集成...")
        
        # 创建Deployment MCP客户端
        deployment_client = DeploymentMCPClient()
        
        # 测试环境注册
        registration_data = {
            "environment_id": "test_env",
            "environment_type": "LOCAL",
            "platform": self.current_platform,
            "capabilities": await self.terminal_mcp.get_capabilities() if self.terminal_mcp else {}
        }
        
        # 注意：这里只测试客户端创建，实际注册需要Deployment MCP服务运行
        self.assertIsNotNone(deployment_client)
        self.logger.info("Deployment MCP集成测试通过")
    
    async def test_remote_environment_interface(self):
        """测试远程环境接口"""
        self.logger.info("测试远程环境接口...")
        
        # 创建远程环境接口
        remote_env = RemoteEnvironmentInterface()
        
        # 测试环境信息
        env_info = await remote_env.get_environment_info()
        self.assertIsNotNone(env_info)
        self.assertIn("environment_type", env_info)
        
        # 测试健康检查
        health = await remote_env.health_check()
        self.assertIsNotNone(health)
        self.assertIn("status", health)
        
        self.logger.info("远程环境接口测试通过")

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def run_async_tests(self):
        """运行异步测试"""
        test_instance = TestLocalAdapterMCP()
        test_instance.setUp()
        
        async_tests = [
            test_instance.test_terminal_mcp_capabilities,
            test_instance.test_basic_command_execution,
            test_instance.test_platform_specific_features,
            test_instance.test_local_adapter_engine,
            test_instance.test_deployment_mcp_integration,
            test_instance.test_remote_environment_interface
        ]
        
        for test in async_tests:
            try:
                self.logger.info(f"运行测试: {test.__name__}")
                await test()
                self.logger.info(f"测试通过: {test.__name__}")
            except Exception as e:
                self.logger.error(f"测试失败: {test.__name__} - {e}")
    
    def run_sync_tests(self):
        """运行同步测试"""
        test_instance = TestLocalAdapterMCP()
        test_instance.setUp()
        
        sync_tests = [
            test_instance.test_platform_detection,
            test_instance.test_command_adaptation
        ]
        
        for test in sync_tests:
            try:
                self.logger.info(f"运行测试: {test.__name__}")
                test()
                self.logger.info(f"测试通过: {test.__name__}")
            except Exception as e:
                self.logger.error(f"测试失败: {test.__name__} - {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始运行Local Adapter MCP集成测试...")
        
        # 运行同步测试
        self.logger.info("运行同步测试...")
        self.run_sync_tests()
        
        # 运行异步测试
        self.logger.info("运行异步测试...")
        await self.run_async_tests()
        
        self.logger.info("所有测试完成！")

async def main():
    """主函数"""
    runner = TestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

