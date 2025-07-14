#!/usr/bin/env python3
"""
PowerAutomation Core 學習集成器
統一管理所有學習組件與 MemoryOS MCP 的集成
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# 導入 MemoryOS MCP 組件
from .components.memoryos_mcp import MemoryEngine, ContextManager, LearningAdapter
from .components.memoryos_mcp import PersonalizationManager, MemoryOptimizer

# 導入 PowerAutomation Core 組件
from .components.intelligent_error_handler_mcp.error_handler import IntelligentErrorHandler
from .monitoring.intelligent_monitoring import IntelligentMonitoring
from .ai_assistants.orchestrator import AIAssistantOrchestrator
from .components.project_analyzer_mcp.project_analyzer import ProjectAnalyzer
from .components.deepgraph_mcp.deepgraph_engine import DeepGraphEngine
from .workflows.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)

@dataclass
class LearningIntegrationConfig:
    """學習集成配置"""
    enable_memoryos: bool = True
    enable_learning_adapter: bool = True
    enable_personalization: bool = True
    enable_memory_optimization: bool = True
    learning_update_interval: int = 300  # 5分鐘
    sync_interval: int = 60  # 1分鐘
    max_learning_records: int = 10000

class PowerAutomationLearningIntegration:
    """PowerAutomation Core 學習集成器"""
    
    def __init__(self, config: LearningIntegrationConfig = None):
        self.config = config or LearningIntegrationConfig()
        
        # MemoryOS MCP 組件
        self.memory_engine = None
        self.context_manager = None
        self.learning_adapter = None
        self.personalization_manager = None
        self.memory_optimizer = None
        
        # PowerAutomation Core 組件
        self.error_handler = None
        self.monitoring = None
        self.ai_orchestrator = None
        self.project_analyzer = None
        self.deepgraph_engine = None
        self.workflow_engine = None
        
        # 集成狀態
        self.is_initialized = False
        self.learning_tasks = []
        self.sync_tasks = []
        
        # 性能統計
        self.learning_stats = {
            "total_interactions": 0,
            "successful_fixes": 0,
            "learning_records": 0,
            "context_enhancements": 0,
            "performance_improvements": 0
        }
    
    async def initialize(self):
        """初始化學習集成器"""
        logger.info("🚀 初始化 PowerAutomation Core 學習集成器...")
        
        try:
            # 1. 初始化 MemoryOS MCP 組件
            if self.config.enable_memoryos:
                await self._initialize_memoryos_components()
            
            # 2. 初始化 PowerAutomation Core 組件
            await self._initialize_core_components()
            
            # 3. 建立組件間連接
            await self._establish_component_connections()
            
            # 4. 啟動學習任務
            await self._start_learning_tasks()
            
            self.is_initialized = True
            logger.info("✅ PowerAutomation Core 學習集成器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 學習集成器初始化失敗: {e}")
            raise
    
    async def _initialize_memoryos_components(self):
        """初始化 MemoryOS MCP 組件"""
        logger.info("🧠 初始化 MemoryOS MCP 組件...")
        
        # 初始化記憶引擎
        self.memory_engine = MemoryEngine()
        await self.memory_engine.initialize()
        
        # 初始化上下文管理器
        self.context_manager = ContextManager()
        await self.context_manager.initialize()
        
        # 初始化學習適配器
        if self.config.enable_learning_adapter:
            self.learning_adapter = LearningAdapter(self.memory_engine, self.context_manager)
            await self.learning_adapter.initialize()
        
        # 初始化個性化管理器
        if self.config.enable_personalization:
            self.personalization_manager = PersonalizationManager(self.memory_engine, self.context_manager)
            await self.personalization_manager.initialize()
        
        # 初始化記憶優化器
        if self.config.enable_memory_optimization:
            self.memory_optimizer = MemoryOptimizer(self.memory_engine, self.context_manager)
            await self.memory_optimizer.initialize()
        
        logger.info("✅ MemoryOS MCP 組件初始化完成")
    
    async def _initialize_core_components(self):
        """初始化 PowerAutomation Core 組件"""
        logger.info("⚙️ 初始化 PowerAutomation Core 組件...")
        
        # 初始化智能錯誤處理器
        self.error_handler = IntelligentErrorHandler()
        
        # 初始化智能監控
        self.monitoring = IntelligentMonitoring()
        await self.monitoring.initialize()
        
        # 初始化 AI 助手編排器
        self.ai_orchestrator = AIAssistantOrchestrator()
        await self.ai_orchestrator.initialize()
        
        # 初始化項目分析器
        self.project_analyzer = ProjectAnalyzer()
        
        # 初始化深度圖分析引擎
        self.deepgraph_engine = DeepGraphEngine()
        await self.deepgraph_engine.initialize()
        
        # 初始化工作流引擎
        self.workflow_engine = WorkflowEngine()
        await self.workflow_engine.initialize()
        
        logger.info("✅ PowerAutomation Core 組件初始化完成")
    
    async def _establish_component_connections(self):
        """建立組件間連接"""
        logger.info("🔗 建立組件間連接...")
        
        # 將 MemoryOS MCP 組件連接到 PowerAutomation Core 組件
        if self.memory_engine and self.learning_adapter:
            
            # 連接錯誤處理器
            if self.error_handler:
                self.error_handler.set_memoryos_components(
                    memory_engine=self.memory_engine,
                    learning_adapter=self.learning_adapter
                )
            
            # 連接監控系統
            if self.monitoring:
                self.monitoring.set_memoryos_components(
                    memory_engine=self.memory_engine,
                    learning_adapter=self.learning_adapter
                )
            
            # 連接 AI 助手編排器
            if self.ai_orchestrator:
                self.ai_orchestrator.set_memoryos_components(
                    memory_engine=self.memory_engine,
                    learning_adapter=self.learning_adapter
                )
            
            # 連接項目分析器
            if self.project_analyzer:
                self.project_analyzer.set_memoryos_components(
                    memory_engine=self.memory_engine,
                    learning_adapter=self.learning_adapter
                )
            
            # 連接深度圖引擎
            if self.deepgraph_engine:
                self.deepgraph_engine.set_memoryos_components(
                    memory_engine=self.memory_engine,
                    learning_adapter=self.learning_adapter
                )
            
            # 連接工作流引擎
            if self.workflow_engine:
                self.workflow_engine.set_memoryos_components(
                    memory_engine=self.memory_engine,
                    learning_adapter=self.learning_adapter
                )
        
        logger.info("✅ 組件間連接建立完成")
    
    async def _start_learning_tasks(self):
        """啟動學習任務"""
        logger.info("🎯 啟動學習任務...")
        
        # 啟動同步任務
        sync_task = asyncio.create_task(self._sync_learning_data())
        self.sync_tasks.append(sync_task)
        
        # 啟動學習更新任務
        learning_update_task = asyncio.create_task(self._update_learning_models())
        self.learning_tasks.append(learning_update_task)
        
        # 啟動性能監控任務
        performance_task = asyncio.create_task(self._monitor_learning_performance())
        self.learning_tasks.append(performance_task)
        
        logger.info("✅ 學習任務啟動完成")
    
    async def _sync_learning_data(self):
        """同步學習數據"""
        while True:
            try:
                if self.learning_adapter:
                    # 從各個組件收集學習數據
                    await self._collect_learning_data()
                
                # 等待下一次同步
                await asyncio.sleep(self.config.sync_interval)
                
            except Exception as e:
                logger.error(f"❌ 同步學習數據失敗: {e}")
                await asyncio.sleep(60)  # 錯誤時等待1分鐘
    
    async def _collect_learning_data(self):
        """收集學習數據"""
        try:
            # 從錯誤處理器收集數據
            if self.error_handler:
                error_stats = self.error_handler.get_status()
                await self._record_component_learning(
                    component="error_handler",
                    stats=error_stats,
                    learning_type="error_correction"
                )
            
            # 從監控系統收集數據
            if self.monitoring:
                monitoring_stats = await self.monitoring.get_monitoring_summary()
                await self._record_component_learning(
                    component="monitoring",
                    stats=monitoring_stats,
                    learning_type="performance_optimization"
                )
            
            # 從 AI 助手編排器收集數據
            if self.ai_orchestrator:
                orchestrator_stats = await self.ai_orchestrator.get_orchestration_statistics()
                await self._record_component_learning(
                    component="ai_orchestrator",
                    stats=orchestrator_stats,
                    learning_type="ai_optimization"
                )
            
            # 從項目分析器收集數據
            if self.project_analyzer:
                analyzer_stats = await self.project_analyzer.get_analyzer_statistics()
                await self._record_component_learning(
                    component="project_analyzer",
                    stats=analyzer_stats,
                    learning_type="project_analysis"
                )
            
            # 從深度圖引擎收集數據
            if self.deepgraph_engine:
                graph_stats = await self.deepgraph_engine.get_graph_statistics()
                await self._record_component_learning(
                    component="deepgraph_engine",
                    stats=graph_stats,
                    learning_type="graph_analysis"
                )
            
            # 從工作流引擎收集數據
            if self.workflow_engine:
                workflow_stats = await self.workflow_engine.get_workflow_statistics()
                await self._record_component_learning(
                    component="workflow_engine",
                    stats=workflow_stats,
                    learning_type="workflow_optimization"
                )
            
            logger.debug("📊 學習數據收集完成")
            
        except Exception as e:
            logger.error(f"❌ 收集學習數據失敗: {e}")
    
    async def _record_component_learning(self, 
                                       component: str, 
                                       stats: Dict[str, Any],
                                       learning_type: str):
        """記錄組件學習數據"""
        try:
            if self.learning_adapter:
                await self.learning_adapter.record_learning_data(
                    source=component,
                    data={
                        "component_stats": stats,
                        "timestamp": time.time(),
                        "component": component
                    },
                    learning_type=learning_type,
                    timestamp=time.time()
                )
            
            # 更新統計
            self.learning_stats["learning_records"] += 1
            
        except Exception as e:
            logger.error(f"❌ 記錄組件學習數據失敗 ({component}): {e}")
    
    async def _update_learning_models(self):
        """更新學習模型"""
        while True:
            try:
                if self.learning_adapter:
                    # 優化學習參數
                    await self.learning_adapter.optimize_learning_parameters()
                
                if self.memory_optimizer:
                    # 優化記憶性能
                    await self.memory_optimizer.optimize_learning_performance(
                        learning_data={"source": "periodic_update"},
                        source="learning_integration"
                    )
                
                # 等待下一次更新
                await asyncio.sleep(self.config.learning_update_interval)
                
            except Exception as e:
                logger.error(f"❌ 更新學習模型失敗: {e}")
                await asyncio.sleep(300)  # 錯誤時等待5分鐘
    
    async def _monitor_learning_performance(self):
        """監控學習性能"""
        while True:
            try:
                # 收集性能指標
                performance_metrics = await self._collect_performance_metrics()
                
                # 記錄性能數據
                if self.learning_adapter:
                    await self.learning_adapter.record_learning_data(
                        source="learning_integration",
                        data={
                            "performance_metrics": performance_metrics,
                            "learning_stats": self.learning_stats
                        },
                        learning_type="performance_monitoring",
                        timestamp=time.time()
                    )
                
                # 等待下一次監控
                await asyncio.sleep(120)  # 2分鐘監控一次
                
            except Exception as e:
                logger.error(f"❌ 監控學習性能失敗: {e}")
                await asyncio.sleep(300)
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """收集性能指標"""
        metrics = {
            "memory_usage": 0.0,
            "response_time": 0.0,
            "learning_efficiency": 0.0,
            "component_health": {}
        }
        
        try:
            # 收集記憶引擎指標
            if self.memory_engine:
                memory_stats = await self.memory_engine.get_memory_statistics()
                metrics["memory_usage"] = memory_stats.get("capacity_usage", 0.0)
            
            # 收集學習適配器指標
            if self.learning_adapter:
                learning_stats = await self.learning_adapter.get_learning_statistics()
                metrics["learning_efficiency"] = learning_stats.get("success_rate", 0.0)
            
            # 收集各組件健康狀態
            components = {
                "error_handler": self.error_handler,
                "monitoring": self.monitoring,
                "ai_orchestrator": self.ai_orchestrator,
                "project_analyzer": self.project_analyzer,
                "deepgraph_engine": self.deepgraph_engine,
                "workflow_engine": self.workflow_engine
            }
            
            for name, component in components.items():
                if component and hasattr(component, 'get_status'):
                    try:
                        status = component.get_status()
                        metrics["component_health"][name] = status.get("status", "unknown")
                    except Exception as e:
                        metrics["component_health"][name] = f"error: {e}"
            
        except Exception as e:
            logger.error(f"❌ 收集性能指標失敗: {e}")
        
        return metrics
    
    async def process_claude_interaction(self, interaction_data: Dict[str, Any]):
        """處理 Claude 交互數據"""
        try:
            # 更新統計
            self.learning_stats["total_interactions"] += 1
            
            # 記錄交互到學習適配器
            if self.learning_adapter:
                await self.learning_adapter.process_interaction(interaction_data)
            
            # 更新個性化模型
            if self.personalization_manager:
                await self.personalization_manager.update_user_model(
                    interaction_data=interaction_data,
                    source="claude_interaction"
                )
            
            # 創建上下文記錄
            if self.context_manager:
                context_id = await self.context_manager.create_claude_interaction_context(
                    user_input=interaction_data.get("user_input", ""),
                    claude_response=interaction_data.get("claude_response", ""),
                    metadata=interaction_data.get("metadata", {})
                )
            
            # 如果是成功的交互，更新成功統計
            if interaction_data.get("user_satisfaction", 0) > 0.7:
                self.learning_stats["successful_fixes"] += 1
            
            logger.debug(f"✅ 處理 Claude 交互: {interaction_data.get('user_input', '')[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ 處理 Claude 交互失敗: {e}")
    
    async def get_learning_statistics(self) -> Dict[str, Any]:
        """獲取學習統計"""
        try:
            stats = {
                "integration_stats": self.learning_stats.copy(),
                "component_stats": {},
                "memoryos_stats": {},
                "performance_metrics": await self._collect_performance_metrics()
            }
            
            # 收集 MemoryOS MCP 統計
            if self.memory_engine:
                stats["memoryos_stats"]["memory"] = await self.memory_engine.get_memory_statistics()
            
            if self.context_manager:
                stats["memoryos_stats"]["context"] = await self.context_manager.get_context_statistics()
            
            if self.learning_adapter:
                stats["memoryos_stats"]["learning"] = await self.learning_adapter.get_learning_statistics()
            
            if self.memory_optimizer:
                stats["memoryos_stats"]["optimization"] = await self.memory_optimizer.get_optimization_statistics()
            
            # 收集組件統計
            components = {
                "error_handler": self.error_handler,
                "monitoring": self.monitoring,
                "ai_orchestrator": self.ai_orchestrator,
                "project_analyzer": self.project_analyzer,
                "deepgraph_engine": self.deepgraph_engine,
                "workflow_engine": self.workflow_engine
            }
            
            for name, component in components.items():
                if component and hasattr(component, 'get_status'):
                    try:
                        stats["component_stats"][name] = component.get_status()
                    except Exception as e:
                        stats["component_stats"][name] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 獲取學習統計失敗: {e}")
            return {}
    
    async def cleanup(self):
        """清理資源"""
        logger.info("🧹 清理 PowerAutomation Core 學習集成器...")
        
        # 取消所有任務
        for task in self.sync_tasks + self.learning_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # 清理 MemoryOS MCP 組件
        if self.memory_engine:
            await self.memory_engine.cleanup()
        
        if self.learning_adapter:
            await self.learning_adapter.cleanup()
        
        if self.personalization_manager:
            await self.personalization_manager.cleanup()
        
        if self.memory_optimizer:
            await self.memory_optimizer.cleanup()
        
        # 清理 PowerAutomation Core 組件
        if self.monitoring:
            await self.monitoring.cleanup()
        
        if self.ai_orchestrator:
            await self.ai_orchestrator.cleanup()
        
        if self.deepgraph_engine:
            await self.deepgraph_engine.cleanup()
        
        if self.workflow_engine:
            await self.workflow_engine.cleanup()
        
        logger.info("✅ PowerAutomation Core 學習集成器清理完成")

# 創建全局學習集成器實例
learning_integration = None

async def initialize_learning_integration(config: LearningIntegrationConfig = None):
    """初始化學習集成器"""
    global learning_integration
    
    if learning_integration is None:
        learning_integration = PowerAutomationLearningIntegration(config)
        await learning_integration.initialize()
    
    return learning_integration

async def get_learning_integration():
    """獲取學習集成器實例"""
    global learning_integration
    
    if learning_integration is None:
        learning_integration = await initialize_learning_integration()
    
    return learning_integration

# 測試函數
async def main():
    """測試學習集成器"""
    print("🧪 測試 PowerAutomation Core 學習集成器...")
    
    # 創建測試配置
    config = LearningIntegrationConfig(
        enable_memoryos=True,
        enable_learning_adapter=True,
        enable_personalization=True,
        enable_memory_optimization=True,
        learning_update_interval=30,
        sync_interval=10
    )
    
    # 初始化集成器
    integration = await initialize_learning_integration(config)
    
    # 測試 Claude 交互處理
    test_interaction = {
        "user_input": "如何使用 Python 進行數據分析？",
        "claude_response": "Python 數據分析可以使用 pandas、numpy 等庫...",
        "user_satisfaction": 0.85,
        "response_time": 2500,
        "metadata": {
            "topic": "data_analysis",
            "difficulty": "intermediate"
        }
    }
    
    await integration.process_claude_interaction(test_interaction)
    
    # 測試統計
    stats = await integration.get_learning_statistics()
    print(f"📊 學習統計: {stats}")
    
    # 運行一段時間觀察
    await asyncio.sleep(5)
    
    # 清理
    await integration.cleanup()
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())