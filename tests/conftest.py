"""
pytest配置文件
定义测试夹具和全局配置
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# 导入被测试的组件
from core.powerautomation_core import (
    AutomationCore, CoreConfig,
    WorkflowEngine, TaskScheduler, 
    ResourceManager, MCPCoordinator, 
    MonitoringService
)

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """测试配置"""
    return CoreConfig(
        app_name="ClaudeEditor Test",
        version="4.6.0.0-test",
        environment="test",
        max_concurrent_workflows=5,
        max_concurrent_tasks=10,
        resource_check_interval=5,
        monitoring_interval=5,
        data_dir=tempfile.mkdtemp(),
        log_dir=tempfile.mkdtemp(),
        cache_dir=tempfile.mkdtemp(),
        enable_cloud_sync=False,
        enable_encryption=False,
        require_auth=False,
        audit_enabled=False
    )

@pytest.fixture
async def mock_resource_manager():
    """模拟资源管理器"""
    manager = Mock()
    manager.initialize = AsyncMock()
    manager.start = AsyncMock()
    manager.stop = AsyncMock()
    manager.health_check = AsyncMock(return_value=True)
    manager.get_status = AsyncMock(return_value={
        "cpu_usage": 50.0,
        "memory_usage": 60.0,
        "disk_usage": 30.0
    })
    manager.get_usage_stats = AsyncMock(return_value={
        "cpu_usage": 50.0,
        "memory_usage": 60.0,
        "disk_usage": 30.0
    })
    manager.allocate_resource = AsyncMock(return_value="test_allocation_id")
    manager.release_resource = AsyncMock(return_value=True)
    return manager

@pytest.fixture
async def mock_mcp_coordinator():
    """模拟MCP协调器"""
    coordinator = Mock()
    coordinator.initialize = AsyncMock()
    coordinator.start = AsyncMock()
    coordinator.stop = AsyncMock()
    coordinator.health_check = AsyncMock(return_value=True)
    coordinator.register_mcp = AsyncMock(return_value=True)
    coordinator.call_mcp = AsyncMock(return_value={"status": "success"})
    coordinator.get_mcp_list = AsyncMock(return_value=[])
    return coordinator

@pytest.fixture
async def resource_manager(test_config):
    """真实的资源管理器实例"""
    manager = ResourceManager(test_config)
    await manager.initialize()
    yield manager
    await manager.stop()

@pytest.fixture
async def mcp_coordinator(test_config):
    """真实的MCP协调器实例"""
    coordinator = MCPCoordinator(test_config)
    await coordinator.initialize()
    yield coordinator
    await coordinator.stop()

@pytest.fixture
async def workflow_engine(test_config, mock_resource_manager, mock_mcp_coordinator):
    """工作流引擎实例"""
    engine = WorkflowEngine(test_config, mock_resource_manager, mock_mcp_coordinator)
    await engine.initialize()
    yield engine
    await engine.stop()

@pytest.fixture
async def task_scheduler(test_config, workflow_engine, mock_resource_manager):
    """任务调度器实例"""
    scheduler = TaskScheduler(test_config, workflow_engine, mock_resource_manager)
    await scheduler.initialize()
    yield scheduler
    await scheduler.stop()

@pytest.fixture
async def monitoring_service(test_config, mock_resource_manager):
    """监控服务实例"""
    service = MonitoringService(test_config, mock_resource_manager)
    await service.initialize()
    yield service
    await service.stop()

@pytest.fixture
async def automation_core(test_config):
    """自动化核心实例"""
    core = AutomationCore(test_config)
    await core.start()
    yield core
    await core.stop()

@pytest.fixture
def sample_workflow():
    """示例工作流定义"""
    return {
        "name": "测试工作流",
        "description": "用于测试的简单工作流",
        "version": "1.0",
        "steps": [
            {
                "id": "step1",
                "name": "第一步",
                "type": "command",
                "config": {
                    "command": "echo 'Hello World'"
                }
            },
            {
                "id": "step2",
                "name": "第二步",
                "type": "delay",
                "config": {
                    "delay": 1
                },
                "dependencies": ["step1"]
            }
        ]
    }

@pytest.fixture
def sample_task():
    """示例任务定义"""
    return {
        "name": "测试任务",
        "type": "immediate",
        "action": {
            "type": "command",
            "command": "echo 'Test Task'"
        }
    }

@pytest.fixture
def temp_dir():
    """临时目录"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def mock_file_system(temp_dir):
    """模拟文件系统"""
    # 创建测试文件结构
    (temp_dir / "data").mkdir()
    (temp_dir / "logs").mkdir()
    (temp_dir / "cache").mkdir()
    
    # 创建测试文件
    (temp_dir / "data" / "test.txt").write_text("test data")
    (temp_dir / "logs" / "test.log").write_text("test log")
    
    return temp_dir

# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "e2e: 端到端测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "async_test: 异步测试"
    )

# 异步测试支持
@pytest.fixture
def async_test():
    """异步测试装饰器"""
    def decorator(func):
        return pytest.mark.asyncio(func)
    return decorator

