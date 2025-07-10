"""
PowerAutomation 4.0 核心组件单元测试
"""

import unittest
import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.parallel_executor import ParallelExecutor
from core.event_bus import EventBus, EventType
from core.config import PowerAutomationConfig

class TestCoreComponents(unittest.TestCase):
    """核心组件测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """测试后置清理"""
        self.loop.close()
    
    def test_parallel_executor_initialization(self):
        """测试并行执行器初始化"""
        async def test():
            executor = ParallelExecutor()
            self.assertIsNotNone(executor)
            self.assertEqual(executor.max_workers, 10)
        
        self.loop.run_until_complete(test())
    
    def test_event_bus_publish_subscribe(self):
        """测试事件总线发布订阅"""
        async def test():
            event_bus = EventBus()
            received_events = []
            
            async def event_handler(event_data):
                received_events.append(event_data)
            
            # 订阅事件
            await event_bus.subscribe(EventType.TASK_COMPLETED, event_handler)
            
            # 发布事件
            test_data = {"task_id": "test_123", "result": "success"}
            await event_bus.publish(EventType.TASK_COMPLETED, test_data)
            
            # 等待事件处理
            await asyncio.sleep(0.1)
            
            # 验证事件接收
            self.assertEqual(len(received_events), 1)
            self.assertEqual(received_events[0], test_data)
        
        self.loop.run_until_complete(test())
    
    def test_config_loading(self):
        """测试配置加载"""
        config = PowerAutomationConfig()
        self.assertIsNotNone(config)
        self.assertIsInstance(config.max_concurrent_tasks, int)
        self.assertIsInstance(config.claude_api_key, str)

if __name__ == '__main__':
    unittest.main()

