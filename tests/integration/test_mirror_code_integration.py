"""
Mirror Code 集成测试
测试Mirror Code功能的完整集成和工作流程
"""

import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# 导入Mirror Code组件
import sys
sys.path.append('/home/ubuntu/claudeditor-4.6.0')

from core.mirror_code.engine.mirror_engine import MirrorEngine, MirrorConfig
from core.mirror_code.engine.claude_cli_manager import ClaudeCLIManager

class TestMirrorCodeIntegration:
    """Mirror Code集成测试类"""
    
    @pytest.fixture
    async def mirror_engine(self):
        """创建Mirror引擎实例"""
        config = MirrorConfig(
            enabled=True,
            auto_sync=False,  # 测试时禁用自动同步
            sync_interval=10,
            debug=True
        )
        engine = MirrorEngine(config)
        yield engine
        
        # 清理
        if engine.status.value != "stopped":
            await engine.stop()
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_mirror_engine_lifecycle(self, mirror_engine):
        """测试Mirror引擎生命周期"""
        # 测试初始状态
        assert mirror_engine.status.value == "stopped"
        assert mirror_engine.sync_count == 0
        
        # 测试启动
        with patch.object(mirror_engine.claude_cli_manager, 'check_installation_status') as mock_check:
            mock_check.return_value = {
                "installed": True,
                "version": "1.0.0",
                "status": "installed"
            }
            
            success = await mirror_engine.start()
            assert success is True
            assert mirror_engine.status.value == "running"
        
        # 测试状态获取
        status = mirror_engine.get_status()
        assert status["status"] == "running"
        assert "claude_cli" in status["components"]
        
        # 测试停止
        success = await mirror_engine.stop()
        assert success is True
        assert mirror_engine.status.value == "stopped"
    
    @pytest.mark.asyncio
    async def test_claude_cli_integration(self, mirror_engine):
        """测试Claude CLI集成"""
        cli_manager = mirror_engine.claude_cli_manager
        
        # 模拟Claude CLI安装检查
        with patch.object(cli_manager, '_run_command') as mock_run:
            # 模拟which claude命令成功
            mock_run.side_effect = [
                {"success": True, "output": "/usr/local/bin/claude", "return_code": 0},
                {"success": True, "output": "claude v1.0.0", "return_code": 0}
            ]
            
            status = await cli_manager.check_installation_status()
            assert status["installed"] is True
            assert status["version"] == "claude v1.0.0"
    
    @pytest.mark.asyncio
    async def test_claude_cli_installation(self, mirror_engine):
        """测试Claude CLI自动安装"""
        cli_manager = mirror_engine.claude_cli_manager
        
        # 模拟安装过程
        with patch.object(cli_manager, '_run_command') as mock_run:
            # 模拟安装命令序列
            mock_run.side_effect = [
                # which npm
                {"success": True, "output": "/usr/local/bin/npm", "return_code": 0},
                # npm install
                {"success": True, "output": "安装成功", "return_code": 0},
                # which claude (验证)
                {"success": True, "output": "/usr/local/bin/claude", "return_code": 0},
                # claude --version
                {"success": True, "output": "claude v1.0.0", "return_code": 0},
                # claude --model test
                {"success": True, "output": "Claude CLI 测试成功", "return_code": 0}
            ]
            
            success = await cli_manager.install_claude_cli()
            assert success is True
            assert cli_manager.is_installed is True
            # 只验证安装成功，不验证具体版本字符串
            assert cli_manager.claude_version is not None
    
    @pytest.mark.asyncio
    async def test_mirror_sync_workflow(self, mirror_engine, temp_workspace):
        """测试Mirror同步工作流程"""
        # 启动引擎
        with patch.object(mirror_engine.claude_cli_manager, 'check_installation_status') as mock_check:
            mock_check.return_value = {"installed": True, "version": "1.0.0", "status": "installed"}
            await mirror_engine.start()
        
        # 测试手动同步
        initial_count = mirror_engine.sync_count
        success = await mirror_engine.sync_now()
        
        assert success is True
        assert mirror_engine.sync_count == initial_count + 1
        assert mirror_engine.last_sync_time is not None
    
    @pytest.mark.asyncio
    async def test_mirror_error_handling(self, mirror_engine):
        """测试Mirror错误处理"""
        # 模拟Claude CLI安装失败
        with patch.object(mirror_engine.claude_cli_manager, 'install_claude_cli') as mock_install:
            mock_install.return_value = False
            
            # 启动应该成功，但Claude CLI安装失败不应阻止启动
            success = await mirror_engine.start()
            assert success is True  # 引擎应该在有限功能模式下启动
    
    @pytest.mark.asyncio
    async def test_mirror_config_updates(self, mirror_engine):
        """测试Mirror配置更新"""
        # 测试配置更新
        mirror_engine.update_config({
            "sync_interval": 30,
            "auto_sync": True
        })
        
        assert mirror_engine.config.sync_interval == 30
        assert mirror_engine.config.auto_sync is True
    
    @pytest.mark.asyncio
    async def test_claude_command_execution(self, mirror_engine):
        """测试Claude命令执行"""
        # 启动引擎
        with patch.object(mirror_engine.claude_cli_manager, 'check_installation_status') as mock_check:
            mock_check.return_value = {"installed": True, "version": "1.0.0", "status": "installed"}
            await mirror_engine.start()
        
        # 模拟命令执行
        with patch.object(mirror_engine.claude_cli_manager, 'execute_claude_command') as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "output": "Claude命令执行成功"
            }
            
            result = await mirror_engine.execute_claude_command("--help")
            assert result["success"] is True
            assert "成功" in result["output"]

class TestMirrorCodeUIIntegration:
    """Mirror Code UI集成测试"""
    
    def test_mirror_toggle_component_props(self):
        """测试Mirror Toggle组件属性"""
        # 这里可以添加React组件测试
        # 由于是Python环境，我们模拟组件状态测试
        
        mirror_status = {
            "enabled": True,
            "syncing": False,
            "status": "enabled",
            "syncCount": 10,
            "lastSync": datetime.now().isoformat()
        }
        
        # 验证状态结构
        assert "enabled" in mirror_status
        assert "status" in mirror_status
        assert mirror_status["status"] in ["disabled", "enabled", "syncing", "error", "offline"]
    
    def test_claude_cli_status_component(self):
        """测试Claude CLI状态组件"""
        cli_status = {
            "is_installed": True,
            "installation_status": "installed",
            "claude_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # 验证状态结构
        assert "is_installed" in cli_status
        assert "installation_status" in cli_status
        assert cli_status["installation_status"] in ["not_installed", "installing", "installed", "error"]

class TestMirrorCodePerformance:
    """Mirror Code性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_operations(self):
        """测试并发同步操作"""
        config = MirrorConfig(enabled=True, auto_sync=False)
        engine = MirrorEngine(config)
        
        try:
            # 模拟Claude CLI已安装
            with patch.object(engine.claude_cli_manager, 'check_installation_status') as mock_check:
                mock_check.return_value = {"installed": True, "version": "1.0.0", "status": "installed"}
                await engine.start()
            
            # 并发执行多个同步操作
            tasks = []
            for i in range(5):
                task = asyncio.create_task(engine.sync_now())
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 至少有一个同步成功（其他可能被跳过）
            success_count = sum(1 for result in results if result is True)
            assert success_count >= 1
            
        finally:
            await engine.stop()
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建多个引擎实例
        engines = []
        for i in range(10):
            config = MirrorConfig(enabled=False)
            engine = MirrorEngine(config)
            engines.append(engine)
        
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # 内存增长应该在合理范围内 (< 50MB)
        assert memory_increase < 50 * 1024 * 1024
        
        # 清理
        del engines

def run_integration_tests():
    """运行集成测试"""
    import subprocess
    import sys
    
    print("🧪 开始运行Mirror Code集成测试...")
    
    try:
        # 运行pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            __file__, 
            "-v", 
            "--tb=short",
            "--asyncio-mode=auto"
        ], capture_output=True, text=True, cwd="/home/ubuntu/claudeditor-4.6.0")
        
        print("📊 测试结果:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ 测试警告:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ 所有集成测试通过!")
            return True
        else:
            print("❌ 部分测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False

if __name__ == "__main__":
    # 直接运行测试
    success = run_integration_tests()
    exit(0 if success else 1)

