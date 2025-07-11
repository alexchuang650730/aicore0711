"""
Terminal Selector UI Tests - 终端选择器UI测试
测试ClaudeEditor 4.6.0快速区域的终端连接功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ui.quick_actions.terminal_selector import TerminalSelector
from adapters.local_adapter_mcp import TerminalManager, ConnectionConfig

@pytest.mark.ui
@pytest.mark.asyncio
class TestTerminalSelectorUI:
    """终端选择器UI测试"""
    
    @pytest.fixture
    async def mock_terminal_manager(self):
        """模拟终端管理器"""
        manager = Mock()
        manager.create_connection = AsyncMock(return_value="test_connection_id")
        manager.connect = AsyncMock(return_value=True)
        manager.disconnect = AsyncMock(return_value=True)
        manager.remove_connection = AsyncMock(return_value=True)
        manager.execute_command = AsyncMock()
        manager.get_connection_status = Mock(return_value={
            "platform": "linux_ec2",
            "name": "Test Connection",
            "status": "connected",
            "session_id": "test_session"
        })
        manager.get_active_connections = Mock(return_value=["test_connection_id"])
        manager.health_check = AsyncMock(return_value={"test_connection_id": True})
        manager.get_system_info = AsyncMock(return_value={
            "hostname": "test-host",
            "os_release": "Ubuntu 20.04"
        })
        return manager
    
    @pytest.fixture
    def terminal_selector(self, mock_terminal_manager):
        """终端选择器实例"""
        return TerminalSelector(mock_terminal_manager)
    
    async def test_initialization(self, terminal_selector):
        """测试初始化"""
        assert terminal_selector.terminal_manager is not None
        assert terminal_selector.current_connection is None
        assert len(terminal_selector.connection_presets) > 0
        assert len(terminal_selector.custom_connections) == 0
    
    async def test_get_available_platforms(self, terminal_selector):
        """测试获取可用平台"""
        platforms = terminal_selector.get_available_platforms()
        
        assert "linux_ec2" in platforms
        assert "wsl" in platforms
        assert "mac_terminal" in platforms
        
        # 检查平台信息结构
        ec2_platform = platforms["linux_ec2"]
        assert "name" in ec2_platform
        assert "description" in ec2_platform
        assert "connector" in ec2_platform
        assert "protocols" in ec2_platform
        assert "auth_methods" in ec2_platform
    
    async def test_get_connection_presets(self, terminal_selector):
        """测试获取连接预设"""
        presets = terminal_selector.get_connection_presets()
        
        assert len(presets) > 0
        assert "dev_ec2" in presets or "local_wsl" in presets or "local_mac" in presets
        
        # 检查预设结构
        for preset_name, preset_config in presets.items():
            assert "platform" in preset_config
            assert "name" in preset_config
    
    async def test_add_custom_connection(self, terminal_selector):
        """测试添加自定义连接"""
        # 注册UI回调
        callback_called = False
        callback_data = None
        
        def ui_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data
        
        terminal_selector.register_ui_callback("connections_updated", ui_callback)
        
        # 添加自定义连接
        custom_config = {
            "platform": "linux_ec2",
            "name": "Custom EC2",
            "host": "custom.example.com",
            "user": "ubuntu"
        }
        
        terminal_selector.add_custom_connection("custom_ec2", custom_config)
        
        # 验证添加成功
        assert "custom_ec2" in terminal_selector.custom_connections
        assert terminal_selector.custom_connections["custom_ec2"] == custom_config
        
        # 等待回调执行
        await asyncio.sleep(0.1)
        
        # 验证UI回调
        assert callback_called is True
        assert callback_data["action"] == "added"
        assert callback_data["name"] == "custom_ec2"
    
    async def test_remove_custom_connection(self, terminal_selector):
        """测试移除自定义连接"""
        # 先添加一个自定义连接
        custom_config = {
            "platform": "wsl",
            "name": "Custom WSL"
        }
        terminal_selector.add_custom_connection("custom_wsl", custom_config)
        
        # 注册UI回调
        callback_called = False
        
        def ui_callback(data):
            nonlocal callback_called
            callback_called = True
        
        terminal_selector.register_ui_callback("connections_updated", ui_callback)
        
        # 移除连接
        result = terminal_selector.remove_custom_connection("custom_wsl")
        
        # 验证移除成功
        assert result is True
        assert "custom_wsl" not in terminal_selector.custom_connections
        
        # 等待回调执行
        await asyncio.sleep(0.1)
        assert callback_called is True
        
        # 测试移除不存在的连接
        result = terminal_selector.remove_custom_connection("non_existent")
        assert result is False
    
    async def test_quick_connect_success(self, terminal_selector):
        """测试快速连接成功"""
        # 注册UI回调
        connection_established = False
        
        async def ui_callback(data):
            nonlocal connection_established
            connection_established = True
        
        terminal_selector.register_ui_callback("connection_established", ui_callback)
        
        # 执行快速连接
        connection_id = await terminal_selector.quick_connect("dev_ec2")
        
        # 验证连接成功
        assert connection_id == "test_connection_id"
        assert terminal_selector.current_connection == connection_id
        
        # 验证管理器调用
        terminal_selector.terminal_manager.create_connection.assert_called_once()
        terminal_selector.terminal_manager.connect.assert_called_once_with(connection_id)
        
        # 等待回调执行
        await asyncio.sleep(0.1)
        assert connection_established is True
    
    async def test_quick_connect_failure(self, terminal_selector):
        """测试快速连接失败"""
        # 模拟连接失败
        terminal_selector.terminal_manager.connect = AsyncMock(return_value=False)
        
        # 执行快速连接应该抛出异常
        with pytest.raises(Exception, match="快速连接失败"):
            await terminal_selector.quick_connect("dev_ec2")
        
        # 验证清理调用
        terminal_selector.terminal_manager.remove_connection.assert_called_once()
    
    async def test_quick_connect_invalid_preset(self, terminal_selector):
        """测试连接不存在的预设"""
        with pytest.raises(ValueError, match="连接预设不存在"):
            await terminal_selector.quick_connect("non_existent_preset")
    
    async def test_connect_with_config(self, terminal_selector):
        """测试使用自定义配置连接"""
        config_dict = {
            "platform": "mac_terminal",
            "name": "Custom Mac Terminal",
            "extra_params": {
                "shell": "bash",
                "type": "local"
            }
        }
        
        connection_id = await terminal_selector.connect_with_config(config_dict)
        
        assert connection_id == "test_connection_id"
        assert terminal_selector.current_connection == connection_id
        
        # 验证管理器调用
        terminal_selector.terminal_manager.create_connection.assert_called_once()
        terminal_selector.terminal_manager.connect.assert_called_once()
    
    async def test_disconnect_current(self, terminal_selector):
        """测试断开当前连接"""
        # 先建立连接
        await terminal_selector.quick_connect("dev_ec2")
        
        # 注册UI回调
        disconnected = False
        
        async def ui_callback(data):
            nonlocal disconnected
            disconnected = True
        
        terminal_selector.register_ui_callback("connection_disconnected", ui_callback)
        
        # 断开连接
        result = await terminal_selector.disconnect_current()
        
        assert result is True
        assert terminal_selector.current_connection is None
        
        # 验证管理器调用
        terminal_selector.terminal_manager.disconnect.assert_called()
        
        # 等待回调执行
        await asyncio.sleep(0.1)
        assert disconnected is True
    
    async def test_disconnect_no_connection(self, terminal_selector):
        """测试没有连接时断开"""
        result = await terminal_selector.disconnect_current()
        assert result is True
    
    async def test_switch_connection(self, terminal_selector):
        """测试切换连接"""
        # 模拟已存在的连接
        terminal_selector.terminal_manager.get_connection_status = Mock(return_value={
            "status": "connected"
        })
        
        # 注册UI回调
        switched = False
        
        async def ui_callback(data):
            nonlocal switched
            switched = True
        
        terminal_selector.register_ui_callback("connection_switched", ui_callback)
        
        # 切换连接
        result = await terminal_selector.switch_connection("other_connection_id")
        
        assert result is True
        assert terminal_selector.current_connection == "other_connection_id"
        
        # 等待回调执行
        await asyncio.sleep(0.1)
        assert switched is True
    
    async def test_switch_connection_invalid(self, terminal_selector):
        """测试切换到无效连接"""
        # 模拟连接不存在或未连接
        terminal_selector.terminal_manager.get_connection_status = Mock(return_value={})
        
        result = await terminal_selector.switch_connection("invalid_connection")
        assert result is False
    
    async def test_execute_quick_command(self, terminal_selector):
        """测试执行快速命令"""
        # 先建立连接
        await terminal_selector.quick_connect("dev_ec2")
        
        # 模拟命令结果
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_result.execution_time = 1.5
        
        terminal_selector.terminal_manager.execute_command = AsyncMock(return_value=mock_result)
        
        # 注册UI回调
        command_executed = False
        
        async def ui_callback(data):
            nonlocal command_executed
            command_executed = True
        
        terminal_selector.register_ui_callback("command_executed", ui_callback)
        
        # 执行命令
        result = await terminal_selector.execute_quick_command("ls -la")
        
        assert result == mock_result
        
        # 验证管理器调用
        terminal_selector.terminal_manager.execute_command.assert_called_once_with(
            "test_connection_id", "ls -la", None
        )
        
        # 等待回调执行
        await asyncio.sleep(0.1)
        assert command_executed is True
    
    async def test_execute_quick_command_no_connection(self, terminal_selector):
        """测试没有连接时执行命令"""
        with pytest.raises(Exception, match="没有活跃的连接"):
            await terminal_selector.execute_quick_command("ls -la")
    
    async def test_get_current_connection_info(self, terminal_selector):
        """测试获取当前连接信息"""
        # 没有连接时
        info = terminal_selector.get_current_connection_info()
        assert info is None
        
        # 有连接时
        await terminal_selector.quick_connect("dev_ec2")
        info = terminal_selector.get_current_connection_info()
        
        assert info is not None
        assert info["platform"] == "linux_ec2"
        assert info["status"] == "connected"
    
    async def test_health_check_current(self, terminal_selector):
        """测试当前连接健康检查"""
        # 没有连接时
        healthy = await terminal_selector.health_check_current()
        assert healthy is False
        
        # 有连接时
        await terminal_selector.quick_connect("dev_ec2")
        healthy = await terminal_selector.health_check_current()
        assert healthy is True
    
    async def test_get_system_info_current(self, terminal_selector):
        """测试获取当前系统信息"""
        # 没有连接时
        info = await terminal_selector.get_system_info_current()
        assert info is None
        
        # 有连接时
        await terminal_selector.quick_connect("dev_ec2")
        info = await terminal_selector.get_system_info_current()
        
        assert info is not None
        assert "hostname" in info
        assert "os_release" in info
    
    async def test_get_quick_actions(self, terminal_selector):
        """测试获取快速操作"""
        actions = terminal_selector.get_quick_actions()
        
        assert len(actions) > 0
        
        # 检查操作结构
        for action in actions:
            assert "id" in action
            assert "name" in action
            assert "description" in action
            assert "action" in action
        
        # 检查特定操作
        action_ids = [action["id"] for action in actions]
        assert "connect_ec2" in action_ids
        assert "connect_wsl" in action_ids
        assert "connect_mac" in action_ids
        assert "system_info" in action_ids
        assert "health_check" in action_ids
    
    async def test_get_common_commands(self, terminal_selector):
        """测试获取常用命令"""
        commands = terminal_selector.get_common_commands()
        
        assert "system" in commands
        assert "files" in commands
        assert "network" in commands
        assert "development" in commands
        
        # 检查命令结构
        for category, cmd_list in commands.items():
            assert len(cmd_list) > 0
            for cmd in cmd_list:
                assert "name" in cmd
                assert "command" in cmd
                assert "description" in cmd
    
    async def test_execute_common_command(self, terminal_selector):
        """测试执行常用命令"""
        # 先建立连接
        await terminal_selector.quick_connect("dev_ec2")
        
        # 模拟命令结果
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.stdout = "test output"
        
        terminal_selector.terminal_manager.execute_command = AsyncMock(return_value=mock_result)
        
        # 执行常用命令
        result = await terminal_selector.execute_common_command("system", "系统信息")
        
        assert result == mock_result
        
        # 验证调用了正确的命令
        terminal_selector.terminal_manager.execute_command.assert_called_once()
        call_args = terminal_selector.terminal_manager.execute_command.call_args
        assert "uname -a" in call_args[0][1]  # 检查命令内容
    
    async def test_execute_common_command_invalid(self, terminal_selector):
        """测试执行无效的常用命令"""
        await terminal_selector.quick_connect("dev_ec2")
        
        # 无效分类
        with pytest.raises(ValueError, match="命令分类不存在"):
            await terminal_selector.execute_common_command("invalid_category", "test")
        
        # 无效命令
        with pytest.raises(ValueError, match="命令不存在"):
            await terminal_selector.execute_common_command("system", "invalid_command")
    
    async def test_get_selector_status(self, terminal_selector):
        """测试获取选择器状态"""
        # 初始状态
        status = terminal_selector.get_selector_status()
        
        assert status["current_connection"] is None
        assert status["current_connection_info"] is None
        assert "total_connections" in status
        assert "active_connections" in status
        assert "available_platforms" in status
        assert "connection_presets" in status
        assert "custom_connections" in status
        
        # 建立连接后的状态
        await terminal_selector.quick_connect("dev_ec2")
        status = terminal_selector.get_selector_status()
        
        assert status["current_connection"] == "test_connection_id"
        assert status["current_connection_info"] is not None
    
    async def test_ui_callback_registration(self, terminal_selector):
        """测试UI回调注册"""
        callback1_called = False
        callback2_called = False
        
        def callback1(data):
            nonlocal callback1_called
            callback1_called = True
        
        def callback2(data):
            nonlocal callback2_called
            callback2_called = True
        
        # 注册多个回调
        terminal_selector.register_ui_callback("test_event", callback1)
        terminal_selector.register_ui_callback("test_event", callback2)
        
        # 触发事件
        await terminal_selector._emit_ui_event("test_event", {"test": "data"})
        
        # 验证所有回调都被调用
        assert callback1_called is True
        assert callback2_called is True
    
    async def test_ui_callback_error_handling(self, terminal_selector):
        """测试UI回调错误处理"""
        def error_callback(data):
            raise Exception("Callback error")
        
        def normal_callback(data):
            pass
        
        # 注册回调
        terminal_selector.register_ui_callback("test_event", error_callback)
        terminal_selector.register_ui_callback("test_event", normal_callback)
        
        # 触发事件不应该抛出异常
        await terminal_selector._emit_ui_event("test_event", {"test": "data"})
        
        # 应该记录错误但继续执行

@pytest.mark.ui
class TestTerminalSelectorIntegration:
    """终端选择器集成测试"""
    
    @pytest.fixture
    def real_terminal_manager(self):
        """真实的终端管理器（用于集成测试）"""
        return TerminalManager()
    
    @pytest.fixture
    def terminal_selector_real(self, real_terminal_manager):
        """使用真实管理器的终端选择器"""
        return TerminalSelector(real_terminal_manager)
    
    def test_platform_config_creation(self, terminal_selector_real):
        """测试平台配置创建"""
        # 测试EC2配置
        ec2_preset = {
            "platform": "linux_ec2",
            "name": "Test EC2",
            "host": "test.example.com",
            "user": "ubuntu",
            "key_file": "~/.ssh/test.pem",
            "method": "ssh"
        }
        
        config = terminal_selector_real._create_connection_config(ec2_preset)
        
        assert config.platform == "linux_ec2"
        assert config.name == "Test EC2"
        assert config.host == "test.example.com"
        assert config.user == "ubuntu"
        assert config.key_file == "~/.ssh/test.pem"
        assert config.extra_params["method"] == "ssh"
        
        # 测试WSL配置
        wsl_preset = {
            "platform": "wsl",
            "name": "Test WSL",
            "distribution": "Ubuntu-20.04",
            "user": "ubuntu"
        }
        
        config = terminal_selector_real._create_connection_config(wsl_preset)
        
        assert config.platform == "wsl"
        assert config.name == "Test WSL"
        assert config.user == "ubuntu"
        assert config.extra_params["distribution"] == "Ubuntu-20.04"
        
        # 测试Mac配置
        mac_preset = {
            "platform": "mac_terminal",
            "name": "Test Mac",
            "shell": "zsh",
            "type": "local"
        }
        
        config = terminal_selector_real._create_connection_config(mac_preset)
        
        assert config.platform == "mac_terminal"
        assert config.name == "Test Mac"
        assert config.extra_params["shell"] == "zsh"
        assert config.extra_params["type"] == "local"

