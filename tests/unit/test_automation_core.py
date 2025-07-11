"""
AutomationCore 单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.powerautomation_core import AutomationCore, CoreConfig, CoreStatus

@pytest.mark.unit
@pytest.mark.asyncio
class TestAutomationCore:
    """AutomationCore测试类"""
    
    async def test_initialization(self, test_config):
        """测试初始化"""
        core = AutomationCore(test_config)
        
        assert core.config == test_config
        assert core.status.status == "stopped"
        assert core.workflow_engine is None
        assert core.task_scheduler is None
        assert core.resource_manager is None
        assert core.mcp_coordinator is None
        assert core.monitoring_service is None
    
    async def test_start_success(self, test_config):
        """测试成功启动"""
        core = AutomationCore(test_config)
        
        # 模拟组件初始化和启动
        with patch.object(core, '_initialize_components') as mock_init, \
             patch.object(core, '_start_components') as mock_start, \
             patch.object(core, '_monitoring_loop') as mock_monitor:
            
            mock_init.return_value = asyncio.Future()
            mock_init.return_value.set_result(None)
            
            mock_start.return_value = asyncio.Future()
            mock_start.return_value.set_result(None)
            
            result = await core.start()
            
            assert result is True
            assert core.status.status == "running"
            assert core.running is True
            mock_init.assert_called_once()
            mock_start.assert_called_once()
    
    async def test_start_failure(self, test_config):
        """测试启动失败"""
        core = AutomationCore(test_config)
        
        # 模拟初始化失败
        with patch.object(core, '_initialize_components') as mock_init:
            mock_init.side_effect = Exception("初始化失败")
            
            result = await core.start()
            
            assert result is False
            assert core.status.status == "error"
            assert "初始化失败" in core.status.last_error
    
    async def test_stop_success(self, test_config):
        """测试成功停止"""
        core = AutomationCore(test_config)
        core.running = True
        core.status.status = "running"
        
        # 模拟组件停止
        with patch.object(core, '_stop_components') as mock_stop:
            mock_stop.return_value = asyncio.Future()
            mock_stop.return_value.set_result(None)
            
            result = await core.stop()
            
            assert result is True
            assert core.status.status == "stopped"
            assert core.running is False
            mock_stop.assert_called_once()
    
    async def test_get_status(self, test_config):
        """测试获取状态"""
        core = AutomationCore(test_config)
        
        status = core.get_status()
        
        assert "status" in status
        assert "version" in status
        assert "uptime" in status
        assert "components" in status
        assert status["version"] == test_config.version
    
    async def test_get_config(self, test_config):
        """测试获取配置"""
        core = AutomationCore(test_config)
        
        config = core.get_config()
        
        assert config["app_name"] == test_config.app_name
        assert config["version"] == test_config.version
        assert config["environment"] == test_config.environment
    
    async def test_update_config(self, test_config):
        """测试更新配置"""
        core = AutomationCore(test_config)
        
        new_config = {
            "max_concurrent_workflows": 20,
            "monitoring_interval": 15
        }
        
        with patch.object(core, '_emit_event') as mock_emit:
            mock_emit.return_value = asyncio.Future()
            mock_emit.return_value.set_result(None)
            
            result = await core.update_config(new_config)
            
            assert result is True
            assert core.config.max_concurrent_workflows == 20
            assert core.config.monitoring_interval == 15
            mock_emit.assert_called_once_with("config_updated", new_config)
    
    async def test_workflow_management(self, test_config):
        """测试工作流管理接口"""
        core = AutomationCore(test_config)
        
        # 模拟工作流引擎
        mock_engine = Mock()
        mock_engine.create_workflow = AsyncMock(return_value="workflow_id")
        mock_engine.execute_workflow = AsyncMock(return_value="execution_id")
        mock_engine.get_execution_status = AsyncMock(return_value={"status": "completed"})
        
        core.workflow_engine = mock_engine
        
        # 测试创建工作流
        workflow_def = {"name": "test", "steps": []}
        workflow_id = await core.create_workflow(workflow_def)
        assert workflow_id == "workflow_id"
        mock_engine.create_workflow.assert_called_once_with(workflow_def)
        
        # 测试执行工作流
        execution_id = await core.execute_workflow(workflow_id)
        assert execution_id == "execution_id"
        mock_engine.execute_workflow.assert_called_once_with(workflow_id, None)
        
        # 测试获取状态
        status = await core.get_workflow_status(execution_id)
        assert status["status"] == "completed"
        mock_engine.get_execution_status.assert_called_once_with(execution_id)
    
    async def test_workflow_management_without_engine(self, test_config):
        """测试没有工作流引擎时的错误处理"""
        core = AutomationCore(test_config)
        
        with pytest.raises(RuntimeError, match="工作流引擎未初始化"):
            await core.create_workflow({})
        
        with pytest.raises(RuntimeError, match="工作流引擎未初始化"):
            await core.execute_workflow("test_id")
        
        with pytest.raises(RuntimeError, match="工作流引擎未初始化"):
            await core.get_workflow_status("test_id")
    
    async def test_task_scheduling(self, test_config):
        """测试任务调度接口"""
        core = AutomationCore(test_config)
        
        # 模拟任务调度器
        mock_scheduler = Mock()
        mock_scheduler.schedule_task = AsyncMock(return_value="task_id")
        mock_scheduler.cancel_task = AsyncMock(return_value=True)
        
        core.task_scheduler = mock_scheduler
        
        # 测试调度任务
        task_def = {"name": "test", "type": "immediate"}
        task_id = await core.schedule_task(task_def)
        assert task_id == "task_id"
        mock_scheduler.schedule_task.assert_called_once_with(task_def)
        
        # 测试取消任务
        result = await core.cancel_task(task_id)
        assert result is True
        mock_scheduler.cancel_task.assert_called_once_with(task_id)
    
    async def test_mcp_coordination(self, test_config):
        """测试MCP协调接口"""
        core = AutomationCore(test_config)
        
        # 模拟MCP协调器
        mock_coordinator = Mock()
        mock_coordinator.register_mcp = AsyncMock(return_value=True)
        mock_coordinator.call_mcp = AsyncMock(return_value={"result": "success"})
        
        core.mcp_coordinator = mock_coordinator
        
        # 测试注册MCP
        mcp_info = {"id": "test_mcp", "name": "Test MCP"}
        result = await core.register_mcp(mcp_info)
        assert result is True
        mock_coordinator.register_mcp.assert_called_once_with(mcp_info)
        
        # 测试调用MCP
        result = await core.call_mcp("test_mcp", "test_method", {"param": "value"})
        assert result["result"] == "success"
        mock_coordinator.call_mcp.assert_called_once_with("test_mcp", "test_method", {"param": "value"})
    
    async def test_resource_management(self, test_config):
        """测试资源管理接口"""
        core = AutomationCore(test_config)
        
        # 模拟资源管理器
        mock_manager = Mock()
        mock_manager.get_status = AsyncMock(return_value={"cpu_usage": 50})
        mock_manager.allocate_resource = AsyncMock(return_value="allocation_id")
        
        core.resource_manager = mock_manager
        
        # 测试获取资源状态
        status = await core.get_resource_status()
        assert status["cpu_usage"] == 50
        mock_manager.get_status.assert_called_once()
        
        # 测试分配资源
        allocation_id = await core.allocate_resource("cpu", 10.0)
        assert allocation_id == "allocation_id"
        mock_manager.allocate_resource.assert_called_once_with("cpu", 10.0)
    
    async def test_event_system(self, test_config):
        """测试事件系统"""
        core = AutomationCore(test_config)
        
        # 注册事件处理器
        handler_called = False
        event_data = None
        
        def event_handler(data):
            nonlocal handler_called, event_data
            handler_called = True
            event_data = data
        
        core.on("test_event", event_handler)
        
        # 触发事件
        await core._emit_event("test_event", {"message": "test"})
        
        assert handler_called is True
        assert event_data["message"] == "test"
    
    async def test_async_event_handler(self, test_config):
        """测试异步事件处理器"""
        core = AutomationCore(test_config)
        
        # 注册异步事件处理器
        handler_called = False
        
        async def async_event_handler(data):
            nonlocal handler_called
            await asyncio.sleep(0.01)  # 模拟异步操作
            handler_called = True
        
        core.on("async_test_event", async_event_handler)
        
        # 触发事件
        await core._emit_event("async_test_event", {"message": "async_test"})
        
        assert handler_called is True
    
    async def test_monitoring_loop(self, test_config):
        """测试监控循环"""
        core = AutomationCore(test_config)
        core.running = True
        
        # 模拟状态更新和健康检查
        with patch.object(core, '_update_status') as mock_update, \
             patch.object(core, '_health_check') as mock_health:
            
            mock_update.return_value = asyncio.Future()
            mock_update.return_value.set_result(None)
            
            mock_health.return_value = asyncio.Future()
            mock_health.return_value.set_result(None)
            
            # 运行一次监控循环
            core.running = False  # 立即停止循环
            await core._monitoring_loop()
            
            # 验证方法被调用
            mock_update.assert_called()
            mock_health.assert_called()

@pytest.mark.unit
class TestCoreConfig:
    """CoreConfig测试类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = CoreConfig()
        
        assert config.app_name == "PowerAutomation Core 4.6.0"
        assert config.version == "4.6.0.0"
        assert config.environment == "edge"
        assert config.max_concurrent_workflows == 10
        assert config.max_concurrent_tasks == 50
    
    def test_custom_values(self):
        """测试自定义值"""
        config = CoreConfig(
            app_name="Custom App",
            version="1.0.0",
            environment="cloud",
            max_concurrent_workflows=20
        )
        
        assert config.app_name == "Custom App"
        assert config.version == "1.0.0"
        assert config.environment == "cloud"
        assert config.max_concurrent_workflows == 20

@pytest.mark.unit
class TestCoreStatus:
    """CoreStatus测试类"""
    
    def test_initialization(self):
        """测试初始化"""
        status = CoreStatus(
            status="running",
            start_time=datetime.now(),
            uptime=100.0,
            active_workflows=5,
            active_tasks=10,
            resource_usage={"cpu": 50.0}
        )
        
        assert status.status == "running"
        assert status.uptime == 100.0
        assert status.active_workflows == 5
        assert status.active_tasks == 10
        assert status.resource_usage["cpu"] == 50.0
        assert status.last_error is None

