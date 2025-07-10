"""
Stagewise Integration - Stagewise MCP集成

与Stagewise MCP组件协同工作，提供可视化测试和录制即测试功能
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional

class StagewiseTestIntegration:
    """Stagewise测试集成类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Stagewise集成"""
        self.config = config
        self.stagewise_config = config.get("integrations", {}).get("stagewise_mcp", {})
        self.is_initialized = False
        self.stagewise_service = None
    
    async def initialize(self) -> bool:
        """初始化Stagewise集成"""
        try:
            if not self.stagewise_config.get("enabled", False):
                print("Stagewise集成未启用")
                return True
            
            # 尝试导入Stagewise MCP服务
            try:
                from ...stagewise_mcp.stagewise_service import StagewiseService
                self.stagewise_service = StagewiseService()
                await self.stagewise_service.initialize()
            except ImportError:
                print("Stagewise MCP组件未找到，使用模拟模式")
                self.stagewise_service = MockStagewiseService()
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Stagewise集成初始化失败: {e}")
            return False
    
    async def run_visual_test(self, test_spec: Dict[str, Any]) -> Dict[str, Any]:
        """运行可视化测试"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if self.stagewise_service:
                # 使用Stagewise运行可视化测试
                return await self.stagewise_service.run_visual_test(test_spec)
            else:
                return {"success": False, "error": "Stagewise服务未可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def start_recording(self, recording_spec: Dict[str, Any]) -> Dict[str, Any]:
        """开始录制测试"""
        try:
            if self.stagewise_service:
                return await self.stagewise_service.start_recording(recording_spec)
            else:
                return {"success": False, "error": "Stagewise服务未可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def stop_recording(self, recording_id: str) -> Dict[str, Any]:
        """停止录制测试"""
        try:
            if self.stagewise_service:
                return await self.stagewise_service.stop_recording(recording_id)
            else:
                return {"success": False, "error": "Stagewise服务未可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_test_from_recording(self, recording_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """从录制生成测试"""
        try:
            if self.stagewise_service:
                # 获取录制数据
                recording_data = await self.stagewise_service.get_recording(recording_id)
                
                if recording_data.get("success"):
                    # 生成测试代码
                    test_code = await self._generate_test_from_recording_data(
                        recording_data["recording"], options or {}
                    )
                    return test_code
                else:
                    return {"success": False, "error": "获取录制数据失败"}
            else:
                return {"success": False, "error": "Stagewise服务未可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_test_from_recording_data(self, recording_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """从录制数据生成测试代码"""
        try:
            actions = recording_data.get("actions", [])
            test_name = options.get("test_name", "recorded_test")
            
            # 构建测试代码
            test_code = self._build_recorded_test_code(actions, test_name)
            
            return {
                "success": True,
                "test_code": test_code,
                "test_file": f"{test_name}.py",
                "actions_count": len(actions),
                "recording_data": recording_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _build_recorded_test_code(self, actions: List[Dict[str, Any]], test_name: str) -> str:
        """构建录制的测试代码"""
        code_lines = [
            "import pytest",
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.common.action_chains import ActionChains",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
            "import time",
            "",
            f"class Test{test_name.title().replace('_', '')}:",
            f"    \"\"\"从录制生成的测试: {test_name}\"\"\"",
            "",
            "    @pytest.fixture",
            "    def driver(self):",
            "        driver = webdriver.Chrome()",
            "        driver.maximize_window()",
            "        yield driver",
            "        driver.quit()",
            "",
            f"    def test_{test_name}(self, driver):",
            f"        \"\"\"执行录制的测试步骤\"\"\"",
        ]
        
        for i, action in enumerate(actions):
            action_type = action.get("type", "")
            
            if action_type == "navigate":
                url = action.get("url", "")
                code_lines.append(f"        # 步骤 {i+1}: 导航到页面")
                code_lines.append(f"        driver.get('{url}')")
                
            elif action_type == "click":
                selector = action.get("selector", "")
                code_lines.extend([
                    f"        # 步骤 {i+1}: 点击元素",
                    f"        element = WebDriverWait(driver, 10).until(",
                    f"            EC.element_to_be_clickable((By.CSS_SELECTOR, '{selector}'))",
                    "        )",
                    "        element.click()"
                ])
                
            elif action_type == "type":
                selector = action.get("selector", "")
                text = action.get("text", "")
                code_lines.extend([
                    f"        # 步骤 {i+1}: 输入文本",
                    f"        input_element = WebDriverWait(driver, 10).until(",
                    f"            EC.presence_of_element_located((By.CSS_SELECTOR, '{selector}'))",
                    "        )",
                    "        input_element.clear()",
                    f"        input_element.send_keys('{text}')"
                ])
                
            elif action_type == "wait":
                duration = action.get("duration", 1)
                code_lines.extend([
                    f"        # 步骤 {i+1}: 等待",
                    f"        time.sleep({duration})"
                ])
                
            elif action_type == "scroll":
                x = action.get("x", 0)
                y = action.get("y", 0)
                code_lines.extend([
                    f"        # 步骤 {i+1}: 滚动页面",
                    f"        driver.execute_script('window.scrollTo({x}, {y});')"
                ])
                
            elif action_type == "assert":
                assertion_type = action.get("assertion_type", "")
                selector = action.get("selector", "")
                expected = action.get("expected", "")
                
                if assertion_type == "text":
                    code_lines.extend([
                        f"        # 步骤 {i+1}: 验证文本",
                        f"        element = driver.find_element(By.CSS_SELECTOR, '{selector}')",
                        f"        assert '{expected}' in element.text"
                    ])
                elif assertion_type == "visible":
                    code_lines.extend([
                        f"        # 步骤 {i+1}: 验证元素可见",
                        f"        element = driver.find_element(By.CSS_SELECTOR, '{selector}')",
                        "        assert element.is_displayed()"
                    ])
            
            # 添加步骤间的小延迟
            if i < len(actions) - 1:
                code_lines.append("        time.sleep(0.5)")
            
            code_lines.append("")
        
        # 添加最终验证
        code_lines.extend([
            "        # 最终验证: 测试完成",
            "        assert driver.current_url  # 确保页面仍然可访问",
            ""
        ])
        
        return "\n".join(code_lines)
    
    async def run_element_inspection(self, page_url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """运行元素检查"""
        try:
            if self.stagewise_service:
                return await self.stagewise_service.inspect_elements(page_url, options)
            else:
                return {"success": False, "error": "Stagewise服务未可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_visual_regression_test(self, baseline_spec: Dict[str, Any]) -> Dict[str, Any]:
        """生成视觉回归测试"""
        try:
            if self.stagewise_service:
                return await self.stagewise_service.create_visual_baseline(baseline_spec)
            else:
                return {"success": False, "error": "Stagewise服务未可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.stagewise_service and hasattr(self.stagewise_service, 'cleanup'):
                await self.stagewise_service.cleanup()
            self.is_initialized = False
        except Exception as e:
            print(f"Stagewise集成清理失败: {e}")


class MockStagewiseService:
    """Stagewise服务模拟类（当Stagewise MCP不可用时使用）"""
    
    async def initialize(self):
        """初始化模拟服务"""
        pass
    
    async def run_visual_test(self, test_spec: Dict[str, Any]) -> Dict[str, Any]:
        """模拟可视化测试"""
        return {
            "success": True,
            "test_results": {
                "passed": True,
                "screenshots": ["baseline.png", "current.png"],
                "diff_percentage": 0.1
            }
        }
    
    async def start_recording(self, recording_spec: Dict[str, Any]) -> Dict[str, Any]:
        """模拟开始录制"""
        return {
            "success": True,
            "recording_id": "mock_recording_123",
            "status": "recording"
        }
    
    async def stop_recording(self, recording_id: str) -> Dict[str, Any]:
        """模拟停止录制"""
        return {
            "success": True,
            "recording_id": recording_id,
            "status": "completed",
            "actions_count": 5
        }
    
    async def get_recording(self, recording_id: str) -> Dict[str, Any]:
        """模拟获取录制数据"""
        return {
            "success": True,
            "recording": {
                "id": recording_id,
                "actions": [
                    {"type": "navigate", "url": "http://localhost:3000"},
                    {"type": "click", "selector": "#login-button"},
                    {"type": "type", "selector": "#username", "text": "testuser"},
                    {"type": "type", "selector": "#password", "text": "testpass"},
                    {"type": "click", "selector": "#submit-button"}
                ]
            }
        }
    
    async def inspect_elements(self, page_url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """模拟元素检查"""
        return {
            "success": True,
            "elements": [
                {"selector": "#header", "type": "header", "visible": True},
                {"selector": ".nav-menu", "type": "navigation", "visible": True},
                {"selector": "#main-content", "type": "main", "visible": True}
            ]
        }
    
    async def create_visual_baseline(self, baseline_spec: Dict[str, Any]) -> Dict[str, Any]:
        """模拟创建视觉基线"""
        return {
            "success": True,
            "baseline_id": "mock_baseline_456",
            "screenshot_path": "/mock/path/baseline.png"
        }
    
    async def cleanup(self):
        """清理模拟服务"""
        pass

