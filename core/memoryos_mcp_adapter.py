#!/usr/bin/env python3
"""
MemoryOS MCP 適配器
v4.6.9.4 - 提供統一的 MemoryOS MCP 接口和集成
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import uuid
import sqlite3
from datetime import datetime, timedelta

# 導入 MemoryOS MCP 組件
from .components.memoryos_mcp import MemoryEngine, ContextManager, LearningAdapter
from .components.memoryos_mcp import PersonalizationManager, MemoryOptimizer
from .components.memoryos_mcp import Memory, MemoryType, Context, ContextType

# 導入學習集成
from .learning_integration import PowerAutomationLearningIntegration
from .data_collection_system import DataCollectionSystem, DataType, DataPriority

logger = logging.getLogger(__name__)

class AdapterStatus(Enum):
    """適配器狀態"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class IntegrationMode(Enum):
    """集成模式"""
    FULL_INTEGRATION = "full_integration"
    MEMORY_ONLY = "memory_only"
    CONTEXT_ONLY = "context_only"
    LEARNING_ONLY = "learning_only"
    OPTIMIZATION_ONLY = "optimization_only"

@dataclass
class AdapterConfig:
    """適配器配置"""
    integration_mode: IntegrationMode = IntegrationMode.FULL_INTEGRATION
    enable_memory_engine: bool = True
    enable_context_manager: bool = True
    enable_learning_adapter: bool = True
    enable_personalization: bool = True
    enable_memory_optimizer: bool = True
    enable_data_collection: bool = True
    auto_sync_interval: int = 60  # 秒
    health_check_interval: int = 300  # 5分鐘
    max_concurrent_operations: int = 10
    memory_capacity_limit: int = 100000
    context_retention_days: int = 30
    learning_batch_size: int = 100

@dataclass
class OperationResult:
    """操作結果"""
    success: bool
    operation_id: str
    operation_type: str
    data: Any = None
    error_message: str = None
    execution_time: float = 0.0
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class MemoryOSMCPAdapter:
    """MemoryOS MCP 適配器"""
    
    def __init__(self, config: AdapterConfig = None):
        self.config = config or AdapterConfig()
        self.status = AdapterStatus.INITIALIZING
        self.adapter_id = str(uuid.uuid4())
        
        # 核心組件
        self.memory_engine = None
        self.context_manager = None
        self.learning_adapter = None
        self.personalization_manager = None
        self.memory_optimizer = None
        
        # 集成組件
        self.learning_integration = None
        self.data_collection = None
        
        # 運行時狀態
        self.active_operations = {}
        self.operation_history = []
        self.health_metrics = {}
        self.sync_tasks = []
        
        # 統計信息
        self.adapter_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_response_time": 0.0,
            "memory_operations": 0,
            "context_operations": 0,
            "learning_operations": 0,
            "uptime": 0.0,
            "last_sync": 0.0
        }
        
        self.start_time = time.time()
    
    async def initialize(self):
        """初始化適配器"""
        logger.info("🚀 初始化 MemoryOS MCP 適配器...")
        
        try:
            self.status = AdapterStatus.INITIALIZING
            
            # 1. 初始化核心組件
            await self._initialize_core_components()
            
            # 2. 初始化集成組件
            await self._initialize_integration_components()
            
            # 3. 建立組件連接
            await self._establish_component_connections()
            
            # 4. 啟動後台任務
            await self._start_background_tasks()
            
            # 5. 執行健康檢查
            await self._perform_health_check()
            
            self.status = AdapterStatus.READY
            logger.info("✅ MemoryOS MCP 適配器初始化完成")
            
        except Exception as e:
            self.status = AdapterStatus.ERROR
            logger.error(f"❌ 適配器初始化失敗: {e}")
            raise
    
    async def _initialize_core_components(self):
        """初始化核心組件"""
        logger.info("🧠 初始化核心組件...")
        
        # 初始化記憶引擎
        if self.config.enable_memory_engine:
            self.memory_engine = MemoryEngine()
            await self.memory_engine.initialize()
            logger.info("✅ Memory Engine 初始化完成")
        
        # 初始化上下文管理器
        if self.config.enable_context_manager:
            self.context_manager = ContextManager()
            await self.context_manager.initialize()
            logger.info("✅ Context Manager 初始化完成")
        
        # 初始化學習適配器
        if self.config.enable_learning_adapter and self.memory_engine and self.context_manager:
            self.learning_adapter = LearningAdapter(self.memory_engine, self.context_manager)
            await self.learning_adapter.initialize()
            logger.info("✅ Learning Adapter 初始化完成")
        
        # 初始化個性化管理器
        if self.config.enable_personalization and self.memory_engine and self.context_manager:
            self.personalization_manager = PersonalizationManager(
                self.memory_engine, 
                self.context_manager
            )
            await self.personalization_manager.initialize()
            logger.info("✅ Personalization Manager 初始化完成")
        
        # 初始化記憶優化器
        if self.config.enable_memory_optimizer and self.memory_engine and self.context_manager:
            self.memory_optimizer = MemoryOptimizer(
                self.memory_engine,
                self.context_manager
            )
            await self.memory_optimizer.initialize()
            logger.info("✅ Memory Optimizer 初始化完成")
    
    async def _initialize_integration_components(self):
        """初始化集成組件"""
        logger.info("🔗 初始化集成組件...")
        
        # 初始化學習集成
        if self.config.integration_mode == IntegrationMode.FULL_INTEGRATION:
            self.learning_integration = PowerAutomationLearningIntegration()
            await self.learning_integration.initialize()
            logger.info("✅ Learning Integration 初始化完成")
        
        # 初始化數據收集
        if self.config.enable_data_collection:
            self.data_collection = DataCollectionSystem()
            await self.data_collection.initialize()
            logger.info("✅ Data Collection 初始化完成")
    
    async def _establish_component_connections(self):
        """建立組件連接"""
        logger.info("🔗 建立組件連接...")
        
        # 連接學習集成和核心組件
        if self.learning_integration:
            # 設置 MemoryOS MCP 組件到學習集成
            if hasattr(self.learning_integration, 'memory_engine') and self.memory_engine:
                self.learning_integration.memory_engine = self.memory_engine
            
            if hasattr(self.learning_integration, 'context_manager') and self.context_manager:
                self.learning_integration.context_manager = self.context_manager
            
            if hasattr(self.learning_integration, 'learning_adapter') and self.learning_adapter:
                self.learning_integration.learning_adapter = self.learning_adapter
            
            if hasattr(self.learning_integration, 'personalization_manager') and self.personalization_manager:
                self.learning_integration.personalization_manager = self.personalization_manager
            
            if hasattr(self.learning_integration, 'memory_optimizer') and self.memory_optimizer:
                self.learning_integration.memory_optimizer = self.memory_optimizer
        
        logger.info("✅ 組件連接建立完成")
    
    async def _start_background_tasks(self):
        """啟動後台任務"""
        logger.info("🎯 啟動後台任務...")
        
        # 自動同步任務
        if self.config.auto_sync_interval > 0:
            sync_task = asyncio.create_task(self._auto_sync_loop())
            self.sync_tasks.append(sync_task)
        
        # 健康檢查任務
        if self.config.health_check_interval > 0:
            health_task = asyncio.create_task(self._health_check_loop())
            self.sync_tasks.append(health_task)
        
        # 統計更新任務
        stats_task = asyncio.create_task(self._stats_update_loop())
        self.sync_tasks.append(stats_task)
        
        logger.info("✅ 後台任務啟動完成")
    
    async def _auto_sync_loop(self):
        """自動同步循環"""
        while True:
            try:
                await self._perform_auto_sync()
                await asyncio.sleep(self.config.auto_sync_interval)
            except Exception as e:
                logger.error(f"❌ 自動同步錯誤: {e}")
                await asyncio.sleep(60)  # 錯誤時等待1分鐘
    
    async def _health_check_loop(self):
        """健康檢查循環"""
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"❌ 健康檢查錯誤: {e}")
                await asyncio.sleep(300)  # 錯誤時等待5分鐘
    
    async def _stats_update_loop(self):
        """統計更新循環"""
        while True:
            try:
                await self._update_adapter_stats()
                await asyncio.sleep(60)  # 每分鐘更新一次統計
            except Exception as e:
                logger.error(f"❌ 統計更新錯誤: {e}")
                await asyncio.sleep(60)
    
    async def _perform_auto_sync(self):
        """執行自動同步"""
        try:
            # 同步記憶和上下文
            if self.memory_engine and self.context_manager:
                await self._sync_memory_and_context()
            
            # 同步學習數據
            if self.learning_adapter:
                await self._sync_learning_data()
            
            # 觸發優化
            if self.memory_optimizer:
                await self._trigger_optimization()
            
            self.adapter_stats["last_sync"] = time.time()
            
        except Exception as e:
            logger.error(f"❌ 自動同步失敗: {e}")
    
    async def _perform_health_check(self):
        """執行健康檢查"""
        try:
            health_status = {
                "adapter_status": self.status.value,
                "components": {},
                "memory_usage": 0.0,
                "response_time": 0.0,
                "error_rate": 0.0,
                "timestamp": time.time()
            }
            
            # 檢查各個組件
            if self.memory_engine:
                health_status["components"]["memory_engine"] = "healthy"
            
            if self.context_manager:
                health_status["components"]["context_manager"] = "healthy"
            
            if self.learning_adapter:
                health_status["components"]["learning_adapter"] = "healthy"
            
            if self.personalization_manager:
                health_status["components"]["personalization_manager"] = "healthy"
            
            if self.memory_optimizer:
                health_status["components"]["memory_optimizer"] = "healthy"
            
            # 計算錯誤率
            if self.adapter_stats["total_operations"] > 0:
                health_status["error_rate"] = (
                    self.adapter_stats["failed_operations"] / 
                    self.adapter_stats["total_operations"]
                ) * 100
            
            # 計算響應時間
            health_status["response_time"] = self.adapter_stats["average_response_time"]
            
            self.health_metrics = health_status
            
        except Exception as e:
            logger.error(f"❌ 健康檢查失敗: {e}")
            self.health_metrics = {
                "adapter_status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _update_adapter_stats(self):
        """更新適配器統計"""
        try:
            current_time = time.time()
            self.adapter_stats["uptime"] = current_time - self.start_time
            
            # 計算平均響應時間
            if self.operation_history:
                response_times = [op.execution_time for op in self.operation_history[-100:]]
                self.adapter_stats["average_response_time"] = sum(response_times) / len(response_times)
            
        except Exception as e:
            logger.error(f"❌ 統計更新失敗: {e}")
    
    async def store_memory(self, 
                          content: str, 
                          memory_type: MemoryType = MemoryType.EPISODIC,
                          importance: float = 0.5,
                          tags: List[str] = None,
                          metadata: Dict[str, Any] = None) -> OperationResult:
        """存儲記憶"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.status = AdapterStatus.BUSY
            
            if not self.memory_engine:
                raise ValueError("Memory Engine 未初始化")
            
            # 創建記憶對象
            memory = Memory(
                id=str(uuid.uuid4()),
                content=content,
                memory_type=memory_type,
                importance_score=importance,
                tags=tags or [],
                metadata=metadata or {},
                created_at=time.time()
            )
            
            # 存儲記憶
            success = await self.memory_engine.store_memory(memory)
            
            # 記錄操作
            execution_time = time.time() - start_time
            result = OperationResult(
                success=success,
                operation_id=operation_id,
                operation_type="store_memory",
                data={"memory_id": memory.id},
                execution_time=execution_time
            )
            
            # 更新統計
            await self._record_operation_result(result)
            
            # 數據收集
            if self.data_collection:
                await self.data_collection.collect_data(
                    data_type=DataType.COMPONENT_METRICS,
                    priority=DataPriority.NORMAL,
                    source="memoryos_adapter",
                    data={
                        "operation": "store_memory",
                        "memory_type": memory_type.value,
                        "importance": importance,
                        "execution_time": execution_time,
                        "success": success
                    }
                )
            
            self.status = AdapterStatus.READY
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = OperationResult(
                success=False,
                operation_id=operation_id,
                operation_type="store_memory",
                error_message=str(e),
                execution_time=execution_time
            )
            
            await self._record_operation_result(result)
            self.status = AdapterStatus.ERROR
            return result
    
    async def retrieve_memories(self, 
                               query: str = None,
                               memory_type: MemoryType = None,
                               limit: int = 10,
                               min_importance: float = 0.0) -> OperationResult:
        """檢索記憶"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.status = AdapterStatus.BUSY
            
            if not self.memory_engine:
                raise ValueError("Memory Engine 未初始化")
            
            # 檢索記憶
            memories = await self.memory_engine.search_memories(
                query=query,
                memory_type=memory_type,
                limit=limit,
                min_importance=min_importance
            )
            
            # 記錄操作
            execution_time = time.time() - start_time
            result = OperationResult(
                success=True,
                operation_id=operation_id,
                operation_type="retrieve_memories",
                data={
                    "memories": [memory.to_dict() for memory in memories],
                    "count": len(memories)
                },
                execution_time=execution_time
            )
            
            # 更新統計
            await self._record_operation_result(result)
            
            self.status = AdapterStatus.READY
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = OperationResult(
                success=False,
                operation_id=operation_id,
                operation_type="retrieve_memories",
                error_message=str(e),
                execution_time=execution_time
            )
            
            await self._record_operation_result(result)
            self.status = AdapterStatus.ERROR
            return result
    
    async def create_context(self, 
                           user_input: str,
                           system_response: str = None,
                           context_type: ContextType = ContextType.CONVERSATION,
                           metadata: Dict[str, Any] = None) -> OperationResult:
        """創建上下文"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.status = AdapterStatus.BUSY
            
            if not self.context_manager:
                raise ValueError("Context Manager 未初始化")
            
            # 創建上下文
            context_id = await self.context_manager.create_context(
                user_input=user_input,
                system_response=system_response,
                context_type=context_type,
                metadata=metadata or {}
            )
            
            # 記錄操作
            execution_time = time.time() - start_time
            result = OperationResult(
                success=True,
                operation_id=operation_id,
                operation_type="create_context",
                data={"context_id": context_id},
                execution_time=execution_time
            )
            
            # 更新統計
            await self._record_operation_result(result)
            
            self.status = AdapterStatus.READY
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = OperationResult(
                success=False,
                operation_id=operation_id,
                operation_type="create_context",
                error_message=str(e),
                execution_time=execution_time
            )
            
            await self._record_operation_result(result)
            self.status = AdapterStatus.ERROR
            return result
    
    async def process_learning_interaction(self, 
                                         interaction_data: Dict[str, Any]) -> OperationResult:
        """處理學習交互"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.status = AdapterStatus.BUSY
            
            if not self.learning_adapter:
                raise ValueError("Learning Adapter 未初始化")
            
            # 處理交互
            await self.learning_adapter.process_interaction(interaction_data)
            
            # 同時處理學習集成
            if self.learning_integration:
                await self.learning_integration.process_claude_interaction(interaction_data)
            
            # 記錄操作
            execution_time = time.time() - start_time
            result = OperationResult(
                success=True,
                operation_id=operation_id,
                operation_type="process_learning_interaction",
                data={"interaction_processed": True},
                execution_time=execution_time
            )
            
            # 更新統計
            await self._record_operation_result(result)
            
            self.status = AdapterStatus.READY
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = OperationResult(
                success=False,
                operation_id=operation_id,
                operation_type="process_learning_interaction",
                error_message=str(e),
                execution_time=execution_time
            )
            
            await self._record_operation_result(result)
            self.status = AdapterStatus.ERROR
            return result
    
    async def get_personalized_recommendations(self, 
                                             user_id: str,
                                             context: str = None,
                                             limit: int = 5) -> OperationResult:
        """獲取個性化推薦"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.status = AdapterStatus.BUSY
            
            if not self.personalization_manager:
                raise ValueError("Personalization Manager 未初始化")
            
            # 獲取推薦
            recommendations = await self.personalization_manager.get_personalized_recommendations(
                user_id=user_id,
                context=context,
                limit=limit
            )
            
            # 記錄操作
            execution_time = time.time() - start_time
            result = OperationResult(
                success=True,
                operation_id=operation_id,
                operation_type="get_personalized_recommendations",
                data={
                    "recommendations": recommendations,
                    "count": len(recommendations)
                },
                execution_time=execution_time
            )
            
            # 更新統計
            await self._record_operation_result(result)
            
            self.status = AdapterStatus.READY
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = OperationResult(
                success=False,
                operation_id=operation_id,
                operation_type="get_personalized_recommendations",
                error_message=str(e),
                execution_time=execution_time
            )
            
            await self._record_operation_result(result)
            self.status = AdapterStatus.ERROR
            return result
    
    async def _record_operation_result(self, result: OperationResult):
        """記錄操作結果"""
        try:
            # 添加到操作歷史
            self.operation_history.append(result)
            
            # 限制歷史記錄數量
            if len(self.operation_history) > 1000:
                self.operation_history = self.operation_history[-500:]
            
            # 更新統計
            self.adapter_stats["total_operations"] += 1
            
            if result.success:
                self.adapter_stats["successful_operations"] += 1
            else:
                self.adapter_stats["failed_operations"] += 1
            
            # 更新特定操作統計
            if result.operation_type in ["store_memory", "retrieve_memories"]:
                self.adapter_stats["memory_operations"] += 1
            elif result.operation_type == "create_context":
                self.adapter_stats["context_operations"] += 1
            elif result.operation_type in ["process_learning_interaction", "get_personalized_recommendations"]:
                self.adapter_stats["learning_operations"] += 1
            
        except Exception as e:
            logger.error(f"❌ 記錄操作結果失敗: {e}")
    
    async def _sync_memory_and_context(self):
        """同步記憶和上下文"""
        # 實現記憶和上下文的同步邏輯
        pass
    
    async def _sync_learning_data(self):
        """同步學習數據"""
        # 實現學習數據同步邏輯
        pass
    
    async def _trigger_optimization(self):
        """觸發優化"""
        if self.memory_optimizer:
            await self.memory_optimizer.optimize_learning_performance(
                learning_data={"source": "auto_trigger"},
                source="memoryos_adapter"
            )
    
    async def get_adapter_status(self) -> Dict[str, Any]:
        """獲取適配器狀態"""
        return {
            "adapter_id": self.adapter_id,
            "status": self.status.value,
            "config": asdict(self.config),
            "stats": self.adapter_stats.copy(),
            "health_metrics": self.health_metrics.copy(),
            "components": {
                "memory_engine": self.memory_engine is not None,
                "context_manager": self.context_manager is not None,
                "learning_adapter": self.learning_adapter is not None,
                "personalization_manager": self.personalization_manager is not None,
                "memory_optimizer": self.memory_optimizer is not None,
                "learning_integration": self.learning_integration is not None,
                "data_collection": self.data_collection is not None
            },
            "active_operations": len(self.active_operations),
            "operation_history_count": len(self.operation_history),
            "uptime": time.time() - self.start_time
        }
    
    async def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """獲取全面統計信息"""
        try:
            stats = {
                "adapter_stats": self.adapter_stats.copy(),
                "component_stats": {},
                "health_metrics": self.health_metrics.copy(),
                "operation_history": []
            }
            
            # 收集組件統計
            if self.memory_engine:
                stats["component_stats"]["memory"] = await self.memory_engine.get_memory_statistics()
            
            if self.context_manager:
                stats["component_stats"]["context"] = await self.context_manager.get_context_statistics()
            
            if self.learning_adapter:
                stats["component_stats"]["learning"] = await self.learning_adapter.get_learning_statistics()
            
            if self.personalization_manager:
                stats["component_stats"]["personalization"] = await self.personalization_manager.get_personalization_statistics()
            
            if self.memory_optimizer:
                stats["component_stats"]["optimization"] = await self.memory_optimizer.get_optimization_statistics()
            
            if self.learning_integration:
                stats["component_stats"]["learning_integration"] = await self.learning_integration.get_learning_statistics()
            
            # 最近操作歷史
            stats["operation_history"] = [
                {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type,
                    "success": op.success,
                    "execution_time": op.execution_time,
                    "timestamp": op.timestamp,
                    "error_message": op.error_message
                }
                for op in self.operation_history[-20:]  # 最近20次操作
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 獲取統計信息失敗: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """清理資源"""
        logger.info("🧹 清理 MemoryOS MCP 適配器...")
        
        # 取消所有後台任務
        for task in self.sync_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # 清理組件
        if self.memory_engine:
            await self.memory_engine.cleanup()
        
        if self.context_manager:
            await self.context_manager.cleanup()
        
        if self.learning_adapter:
            await self.learning_adapter.cleanup()
        
        if self.personalization_manager:
            await self.personalization_manager.cleanup()
        
        if self.memory_optimizer:
            await self.memory_optimizer.cleanup()
        
        if self.learning_integration:
            await self.learning_integration.cleanup()
        
        if self.data_collection:
            await self.data_collection.cleanup()
        
        # 清理狀態
        self.active_operations.clear()
        self.operation_history.clear()
        self.health_metrics.clear()
        self.sync_tasks.clear()
        
        self.status = AdapterStatus.INITIALIZING
        logger.info("✅ MemoryOS MCP 適配器清理完成")

# 全局適配器實例
memoryos_adapter = None

async def get_memoryos_adapter(config: AdapterConfig = None) -> MemoryOSMCPAdapter:
    """獲取 MemoryOS MCP 適配器實例"""
    global memoryos_adapter
    
    if memoryos_adapter is None:
        memoryos_adapter = MemoryOSMCPAdapter(config)
        await memoryos_adapter.initialize()
    
    return memoryos_adapter

async def initialize_memoryos_adapter(config: AdapterConfig = None) -> MemoryOSMCPAdapter:
    """初始化 MemoryOS MCP 適配器"""
    global memoryos_adapter
    
    if memoryos_adapter is not None:
        await memoryos_adapter.cleanup()
    
    memoryos_adapter = MemoryOSMCPAdapter(config)
    await memoryos_adapter.initialize()
    
    return memoryos_adapter

# 測試函數
async def main():
    """測試 MemoryOS MCP 適配器"""
    print("🧪 測試 MemoryOS MCP 適配器...")
    
    # 創建測試配置
    config = AdapterConfig(
        integration_mode=IntegrationMode.FULL_INTEGRATION,
        auto_sync_interval=10,
        health_check_interval=30
    )
    
    # 初始化適配器
    adapter = await initialize_memoryos_adapter(config)
    
    # 測試記憶存儲
    memory_result = await adapter.store_memory(
        content="這是一個測試記憶",
        memory_type=MemoryType.EPISODIC,
        importance=0.8,
        tags=["測試", "記憶"]
    )
    print(f"記憶存儲結果: {memory_result.success}")
    
    # 測試記憶檢索
    retrieve_result = await adapter.retrieve_memories(
        query="測試",
        limit=5
    )
    print(f"記憶檢索結果: {retrieve_result.success}, 數量: {len(retrieve_result.data['memories'])}")
    
    # 測試上下文創建
    context_result = await adapter.create_context(
        user_input="這是用戶輸入",
        system_response="這是系統回應",
        context_type=ContextType.CONVERSATION
    )
    print(f"上下文創建結果: {context_result.success}")
    
    # 測試學習交互
    learning_result = await adapter.process_learning_interaction({
        "user_input": "如何使用 Python？",
        "system_response": "Python 是一種編程語言...",
        "user_satisfaction": 0.9
    })
    print(f"學習交互結果: {learning_result.success}")
    
    # 測試狀態
    status = await adapter.get_adapter_status()
    print(f"適配器狀態: {status['status']}")
    
    # 測試統計
    stats = await adapter.get_comprehensive_statistics()
    print(f"總操作數: {stats['adapter_stats']['total_operations']}")
    
    # 運行一段時間觀察
    await asyncio.sleep(5)
    
    # 清理
    await adapter.cleanup()
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())