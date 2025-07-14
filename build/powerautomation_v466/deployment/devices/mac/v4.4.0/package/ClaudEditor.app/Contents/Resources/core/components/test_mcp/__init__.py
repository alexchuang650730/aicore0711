"""
PowerAutomation Test MCP Component

统一的测试管理组件，整合了所有测试框架、模板、结果和套件。
与SmartUI MCP、Stagewise MCP和AG-UI MCP协同工作，提供完整的AI驱动测试解决方案。

目录结构:
- frameworks/: 测试框架和核心测试功能
- templates/: 测试模板和页面模板
- results/: 测试结果和报告
- suites/: 测试套件和集成测试
- config/: 配置文件和设置

集成组件:
- SmartUI MCP: AI驱动的UI组件生成和测试
- Stagewise MCP: 可视化测试和录制即测试
- AG-UI MCP: 智能测试管理界面生成
"""

from .test_mcp_service import TestMCPService
from .test_orchestrator import TestOrchestrator
from .smartui_integration import SmartUITestIntegration
from .stagewise_integration import StagewiseTestIntegration
from .agui_integration import AGUITestIntegration

__version__ = "4.2.0"
__author__ = "PowerAutomation Team"

# 导出主要类
__all__ = [
    "TestMCPService",
    "TestOrchestrator", 
    "SmartUITestIntegration",
    "StagewiseTestIntegration",
    "AGUITestIntegration"
]

# 组件信息
COMPONENT_INFO = {
    "name": "test_mcp",
    "version": __version__,
    "description": "统一测试管理MCP组件",
    "dependencies": ["smartui_mcp", "stagewise_mcp", "ag_ui_mcp"],
    "capabilities": [
        "test_framework_management",
        "template_based_testing", 
        "result_analysis",
        "suite_orchestration",
        "cross_component_integration",
        "ai_driven_ui_generation",
        "visual_testing",
        "recording_based_testing",
        "intelligent_test_management"
    ],
    "integrations": {
        "smartui_mcp": {
            "description": "AI驱动的UI组件生成和测试",
            "features": ["component_generation", "automated_testing", "responsive_testing"]
        },
        "stagewise_mcp": {
            "description": "可视化测试和录制即测试",
            "features": ["visual_testing", "recording", "element_inspection", "regression_testing"]
        },
        "ag_ui_mcp": {
            "description": "智能测试管理界面生成",
            "features": ["dashboard_generation", "monitoring_ui", "results_visualization", "ai_suggestions"]
        }
    }
}

