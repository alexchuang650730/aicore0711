"""
MCP-Zero + Smart Tool Engine 整合系统

业界首创的AI驱动MCP工具发现与选择系统
结合MCP-Zero的全面工具发现能力和Smart Tool Engine的智能选择优化

架构设计:
- MCP-Zero工具发现层 (底层) - 发现和注册工具
- Smart Tool Engine智能选择层 (上层) - AI驱动的智能选择和优化  
- 统一工具管理接口 (应用层) - 为ClaudEditor提供简化API

作者: PowerAutomation Team
版本: 1.0.0
创建时间: 2025-01-07
"""

from .discovery.mcp_zero_discovery_engine import MCPZeroDiscoveryEngine
from .selection.smart_tool_selection_engine import SmartToolSelectionEngine
from .interface.unified_tool_interface import UnifiedToolInterface
from .models.tool_models import (
    MCPTool,
    ToolCapability,
    TaskRequirement,
    ToolRecommendation,
    SelectedTool
)

__version__ = "1.0.0"
__author__ = "PowerAutomation Team"

# 导出主要类
__all__ = [
    'MCPZeroDiscoveryEngine',
    'SmartToolSelectionEngine', 
    'UnifiedToolInterface',
    'MCPTool',
    'ToolCapability',
    'TaskRequirement',
    'ToolRecommendation',
    'SelectedTool',
    'IntegratedToolSystem'
]

class IntegratedToolSystem:
    """
    MCP-Zero + Smart Tool Engine 整合系统主类
    
    提供完整的工具发现、智能选择和优化功能
    """
    
    def __init__(self, config=None):
        """
        初始化整合系统
        
        Args:
            config: 系统配置参数
        """
        self.config = config or {}
        
        # 初始化各个组件
        self.discovery_engine = MCPZeroDiscoveryEngine(self.config.get('discovery', {}))
        self.selection_engine = SmartToolSelectionEngine(self.config.get('selection', {}))
        self.unified_interface = UnifiedToolInterface(
            self.discovery_engine, 
            self.selection_engine,
            self.config.get('interface', {})
        )
    
    async def initialize(self):
        """异步初始化系统"""
        await self.discovery_engine.initialize()
        await self.selection_engine.initialize()
        await self.unified_interface.initialize()
    
    async def discover_and_select_tools(self, task_requirement):
        """
        发现并智能选择工具的一站式接口
        
        Args:
            task_requirement: 任务需求描述
            
        Returns:
            ToolRecommendation: 工具推荐结果
        """
        return await self.unified_interface.get_tools_for_task(task_requirement)
    
    async def get_available_tools(self):
        """获取所有可用工具"""
        return await self.discovery_engine.get_available_tools()
    
    async def refresh_tool_registry(self):
        """刷新工具注册表"""
        return await self.discovery_engine.refresh_registry()
    
    def get_system_stats(self):
        """获取系统统计信息"""
        return {
            'discovered_tools': self.discovery_engine.get_tool_count(),
            'selection_accuracy': self.selection_engine.get_accuracy_stats(),
            'total_recommendations': self.unified_interface.get_recommendation_count(),
            'system_version': __version__
        }

