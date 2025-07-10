"""
Test MCP Service - 统一测试管理服务

提供完整的测试管理功能，整合所有测试相关组件
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .test_orchestrator import TestOrchestrator
from .smartui_integration import SmartUITestIntegration
from .stagewise_integration import StagewiseTestIntegration
from .agui_integration import AGUITestIntegration

class TestMCPService:
    """Test MCP主服务类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化Test MCP服务"""
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "config", "test_mcp_config.json"
        )
        self.config = self._load_config()
        
        # 初始化组件
        self.orchestrator = TestOrchestrator(self.config)
        self.smartui_integration = SmartUITestIntegration(self.config)
        self.stagewise_integration = StagewiseTestIntegration(self.config)
        self.agui_integration = AGUITestIntegration(self.config)
        
        # 设置日志
        self.logger = self._setup_logging()
        
        # 服务状态
        self.is_running = False
        self.active_tests = {}
        self.generated_ui_components = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"配置加载失败: {e}")
        
        # 默认配置
        return {
            "test_frameworks": {
                "ui_tests": {"enabled": True, "parallel": True},
                "api_tests": {"enabled": True, "timeout": 30},
                "e2e_tests": {"enabled": True, "browser": "chromium"},
                "integration_tests": {"enabled": True, "cleanup": True}
            },
            "integrations": {
                "smartui_mcp": {"enabled": True, "auto_generate": True},
                "stagewise_mcp": {"enabled": True, "visual_testing": True},
                "ag_ui_mcp": {"enabled": True, "auto_generate_ui": True}
            },
            "results": {
                "formats": ["json", "html", "xml"],
                "retention_days": 30,
                "auto_cleanup": True
            },
            "templates": {
                "auto_discovery": True,
                "custom_templates": True,
                "template_validation": True
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger("test_mcp")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def start_service(self) -> bool:
        """启动Test MCP服务"""
        try:
            self.logger.info("启动Test MCP服务...")
            
            # 启动各个组件
            await self.orchestrator.initialize()
            await self.smartui_integration.initialize()
            await self.stagewise_integration.initialize()
            await self.agui_integration.initialize()
            
            # 如果启用了自动UI生成，生成默认界面
            if self.config.get("ui_generation", {}).get("auto_generate_on_startup", True):
                await self._generate_default_ui()
            
            self.is_running = True
            self.logger.info("Test MCP服务启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"服务启动失败: {e}")
            return False
    
    async def _generate_default_ui(self):
        """生成默认测试管理界面"""
        try:
            self.logger.info("生成默认测试管理界面...")
            
            # 生成完整的测试界面
            interface_spec = {
                "theme": self.config.get("integrations", {}).get("ag_ui_mcp", {}).get("default_theme", "claudeditor_dark"),
                "layout_type": "tabbed",
                "responsive": True,
                "dashboard": {
                    "features": ["test_suite_overview", "execution_status", "results_summary", "performance_metrics"]
                },
                "monitor": {
                    "real_time": True,
                    "features": ["live_progress", "test_logs", "error_tracking"]
                },
                "viewer": {
                    "view_modes": ["summary", "detailed", "timeline"],
                    "features": ["filtering", "sorting", "export"]
                },
                "recording": {
                    "features": ["start_stop_recording", "settings_panel", "preview_window"]
                },
                "ai_suggestions": {
                    "ai_features": ["test_optimization", "coverage_analysis", "failure_prediction"]
                },
                "code_generation": {
                    "languages": ["python", "javascript"],
                    "features": ["syntax_highlighting", "live_preview"]
                }
            }
            
            result = await self.agui_integration.generate_complete_testing_interface(interface_spec)
            
            if result.get("success"):
                self.generated_ui_components["default_interface"] = result
                self.logger.info("默认测试界面生成成功")
            else:
                self.logger.warning(f"默认界面生成失败: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"生成默认界面失败: {e}")
    
    async def stop_service(self) -> bool:
        """停止Test MCP服务"""
        try:
            self.logger.info("停止Test MCP服务...")
            
            # 停止所有活动测试
            for test_id in list(self.active_tests.keys()):
                await self.stop_test(test_id)
            
            # 停止各个组件
            await self.orchestrator.cleanup()
            await self.smartui_integration.cleanup()
            await self.stagewise_integration.cleanup()
            await self.agui_integration.cleanup()
            
            self.is_running = False
            self.logger.info("Test MCP服务已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"服务停止失败: {e}")
            return False
    
    async def run_test_suite(self, suite_name: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """运行测试套件"""
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info(f"开始运行测试套件: {suite_name}")
            
            # 记录活动测试
            self.active_tests[test_id] = {
                "suite_name": suite_name,
                "start_time": datetime.now(),
                "status": "running",
                "options": options or {}
            }
            
            # 通过编排器运行测试
            result = await self.orchestrator.run_suite(suite_name, options)
            
            # 更新测试状态
            self.active_tests[test_id]["status"] = "completed"
            self.active_tests[test_id]["end_time"] = datetime.now()
            self.active_tests[test_id]["result"] = result
            
            self.logger.info(f"测试套件 {suite_name} 运行完成")
            return result
            
        except Exception as e:
            self.logger.error(f"测试套件运行失败: {e}")
            if test_id in self.active_tests:
                self.active_tests[test_id]["status"] = "failed"
                self.active_tests[test_id]["error"] = str(e)
            
            return {
                "success": False,
                "error": str(e),
                "test_id": test_id
            }
    
    async def generate_ui_test(self, component_spec: Dict[str, Any]) -> Dict[str, Any]:
        """使用SmartUI生成UI测试"""
        try:
            self.logger.info("生成SmartUI测试...")
            return await self.smartui_integration.generate_test(component_spec)
        except Exception as e:
            self.logger.error(f"SmartUI测试生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_visual_test(self, test_spec: Dict[str, Any]) -> Dict[str, Any]:
        """使用Stagewise运行可视化测试"""
        try:
            self.logger.info("运行Stagewise可视化测试...")
            return await self.stagewise_integration.run_visual_test(test_spec)
        except Exception as e:
            self.logger.error(f"可视化测试运行失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_test_ui(self, ui_spec: Dict[str, Any]) -> Dict[str, Any]:
        """使用AG-UI生成测试管理界面"""
        try:
            self.logger.info("生成测试管理界面...")
            
            ui_type = ui_spec.get("type", "dashboard")
            
            if ui_type == "dashboard":
                result = await self.agui_integration.generate_test_dashboard(ui_spec)
            elif ui_type == "monitor":
                result = await self.agui_integration.generate_test_execution_monitor(ui_spec)
            elif ui_type == "viewer":
                result = await self.agui_integration.generate_test_results_viewer(ui_spec)
            elif ui_type == "recording":
                result = await self.agui_integration.generate_recording_control_panel(ui_spec)
            elif ui_type == "ai_suggestions":
                result = await self.agui_integration.generate_ai_suggestions_panel(ui_spec)
            elif ui_type == "code_generation":
                result = await self.agui_integration.generate_code_generation_panel(ui_spec)
            elif ui_type == "complete":
                result = await self.agui_integration.generate_complete_testing_interface(ui_spec)
            else:
                return {"success": False, "error": f"不支持的UI类型: {ui_type}"}
            
            # 保存生成的UI组件
            if result.get("success"):
                component_id = f"ui_{ui_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.generated_ui_components[component_id] = result
                result["component_id"] = component_id
            
            return result
            
        except Exception as e:
            self.logger.error(f"测试UI生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_recording(self, recording_spec: Dict[str, Any]) -> Dict[str, Any]:
        """开始录制测试"""
        try:
            self.logger.info("开始录制测试...")
            return await self.stagewise_integration.start_recording(recording_spec)
        except Exception as e:
            self.logger.error(f"开始录制失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_recording(self, recording_id: str) -> Dict[str, Any]:
        """停止录制测试"""
        try:
            self.logger.info(f"停止录制: {recording_id}")
            return await self.stagewise_integration.stop_recording(recording_id)
        except Exception as e:
            self.logger.error(f"停止录制失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_test_from_recording(self, recording_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """从录制生成测试"""
        try:
            self.logger.info(f"从录制生成测试: {recording_id}")
            return await self.stagewise_integration.generate_test_from_recording(recording_id, options)
        except Exception as e:
            self.logger.error(f"从录制生成测试失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_test_results(self, test_id: Optional[str] = None) -> Dict[str, Any]:
        """获取测试结果"""
        if test_id:
            return self.active_tests.get(test_id, {})
        else:
            return {
                "active_tests": len(self.active_tests),
                "tests": list(self.active_tests.values())
            }
    
    async def get_generated_ui_components(self, component_id: Optional[str] = None) -> Dict[str, Any]:
        """获取生成的UI组件"""
        if component_id:
            return self.generated_ui_components.get(component_id, {})
        else:
            return {
                "components": self.generated_ui_components,
                "count": len(self.generated_ui_components)
            }
    
    async def stop_test(self, test_id: str) -> bool:
        """停止指定测试"""
        try:
            if test_id in self.active_tests:
                self.active_tests[test_id]["status"] = "stopped"
                self.active_tests[test_id]["end_time"] = datetime.now()
                self.logger.info(f"测试 {test_id} 已停止")
                return True
            return False
        except Exception as e:
            self.logger.error(f"停止测试失败: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "service_running": self.is_running,
            "active_tests": len(self.active_tests),
            "generated_ui_components": len(self.generated_ui_components),
            "components": {
                "orchestrator": getattr(self.orchestrator, 'is_initialized', False),
                "smartui_integration": getattr(self.smartui_integration, 'is_initialized', False),
                "stagewise_integration": getattr(self.stagewise_integration, 'is_initialized', False),
                "agui_integration": getattr(self.agui_integration, 'is_initialized', False)
            },
            "integrations": {
                "smartui_mcp": self.config.get("integrations", {}).get("smartui_mcp", {}).get("enabled", False),
                "stagewise_mcp": self.config.get("integrations", {}).get("stagewise_mcp", {}).get("enabled", False),
                "ag_ui_mcp": self.config.get("integrations", {}).get("ag_ui_mcp", {}).get("enabled", False)
            },
            "config": self.config
        }
    
    async def get_available_themes(self) -> List[str]:
        """获取可用主题"""
        try:
            return await self.agui_integration.get_available_themes()
        except Exception as e:
            self.logger.error(f"获取主题失败: {e}")
            return ["claudeditor_dark", "claudeditor_light"]
    
    async def get_available_ui_components(self) -> List[str]:
        """获取可用UI组件类型"""
        try:
            return await self.agui_integration.get_available_component_types()
        except Exception as e:
            self.logger.error(f"获取UI组件类型失败: {e}")
            return ["dashboard", "monitor", "viewer"]

# 全局服务实例
test_mcp_service = None

def get_test_mcp_service() -> TestMCPService:
    """获取Test MCP服务实例"""
    global test_mcp_service
    if test_mcp_service is None:
        test_mcp_service = TestMCPService()
    return test_mcp_service

