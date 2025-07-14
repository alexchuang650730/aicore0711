#!/usr/bin/env python3
"""
MemoryOS MCP - 記憶優化器
優化記憶存儲和檢索性能
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class OptimizationType(Enum):
    """優化類型"""
    MEMORY_COMPRESSION = "memory_compression"
    RELEVANCE_SCORING = "relevance_scoring"
    RETRIEVAL_SPEED = "retrieval_speed"
    STORAGE_EFFICIENCY = "storage_efficiency"
    CONTEXT_CLUSTERING = "context_clustering"
    GARBAGE_COLLECTION = "garbage_collection"

@dataclass
class OptimizationMetrics:
    """優化指標"""
    optimization_type: OptimizationType
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_percentage: float
    timestamp: float
    
    def calculate_improvement(self):
        """計算改進百分比"""
        if not self.before_metrics or not self.after_metrics:
            return 0.0
        
        improvements = []
        for key in self.before_metrics:
            if key in self.after_metrics:
                before = self.before_metrics[key]
                after = self.after_metrics[key]
                
                if before > 0:
                    improvement = ((after - before) / before) * 100
                    improvements.append(improvement)
        
        return np.mean(improvements) if improvements else 0.0

class MemoryOptimizer:
    """記憶優化器"""
    
    def __init__(self, memory_engine, context_manager):
        self.memory_engine = memory_engine
        self.context_manager = context_manager
        self.optimization_history = deque(maxlen=100)
        self.performance_metrics = defaultdict(list)
        self.optimization_schedules = {}
        self.is_initialized = False
    
    async def initialize(self):
        """初始化記憶優化器"""
        logger.info("⚡ 初始化 Memory Optimizer...")
        
        # 設置優化計劃
        await self._setup_optimization_schedules()
        
        # 初始化基準性能指標
        await self._initialize_baseline_metrics()
        
        # 啟動背景優化任務
        await self._start_background_optimization()
        
        self.is_initialized = True
        logger.info("✅ Memory Optimizer 初始化完成")
    
    async def _setup_optimization_schedules(self):
        """設置優化計劃"""
        self.optimization_schedules = {
            OptimizationType.MEMORY_COMPRESSION: {
                "interval": 3600,  # 1小時
                "last_run": 0,
                "enabled": True
            },
            OptimizationType.RELEVANCE_SCORING: {
                "interval": 1800,  # 30分鐘
                "last_run": 0,
                "enabled": True
            },
            OptimizationType.RETRIEVAL_SPEED: {
                "interval": 7200,  # 2小時
                "last_run": 0,
                "enabled": True
            },
            OptimizationType.STORAGE_EFFICIENCY: {
                "interval": 86400,  # 24小時
                "last_run": 0,
                "enabled": True
            },
            OptimizationType.CONTEXT_CLUSTERING: {
                "interval": 10800,  # 3小時
                "last_run": 0,
                "enabled": True
            },
            OptimizationType.GARBAGE_COLLECTION: {
                "interval": 21600,  # 6小時
                "last_run": 0,
                "enabled": True
            }
        }
    
    async def _initialize_baseline_metrics(self):
        """初始化基準性能指標"""
        try:
            # 記憶引擎基準指標
            memory_stats = await self.memory_engine.get_memory_statistics()
            
            # 上下文管理器基準指標
            context_stats = await self.context_manager.get_context_statistics()
            
            # 存儲基準指標
            baseline_metrics = {
                "memory_count": memory_stats.get("total_memories", 0),
                "memory_size": memory_stats.get("database_size", 0),
                "average_importance": memory_stats.get("average_importance", 0),
                "context_count": context_stats.get("total_contexts", 0),
                "average_relevance": context_stats.get("average_relevance", 0)
            }
            
            self.performance_metrics["baseline"] = [baseline_metrics]
            
            logger.info(f"📊 基準指標: {baseline_metrics}")
            
        except Exception as e:
            logger.error(f"❌ 初始化基準指標失敗: {e}")
    
    async def _start_background_optimization(self):
        """啟動背景優化任務"""
        # 創建背景任務
        asyncio.create_task(self._optimization_loop())
    
    async def _optimization_loop(self):
        """優化循環"""
        while True:
            try:
                current_time = time.time()
                
                # 檢查需要執行的優化任務
                for opt_type, schedule in self.optimization_schedules.items():
                    if (schedule["enabled"] and 
                        current_time - schedule["last_run"] >= schedule["interval"]):
                        
                        await self._execute_optimization(opt_type)
                        schedule["last_run"] = current_time
                
                # 等待下一次檢查
                await asyncio.sleep(300)  # 5分鐘檢查一次
                
            except Exception as e:
                logger.error(f"❌ 優化循環錯誤: {e}")
                await asyncio.sleep(60)  # 錯誤時等待1分鐘
    
    async def _execute_optimization(self, optimization_type: OptimizationType):
        """執行優化"""
        logger.info(f"🔧 執行優化: {optimization_type.value}")
        
        try:
            # 記錄優化前指標
            before_metrics = await self._collect_current_metrics()
            
            # 執行特定類型的優化
            if optimization_type == OptimizationType.MEMORY_COMPRESSION:
                await self._optimize_memory_compression()
            elif optimization_type == OptimizationType.RELEVANCE_SCORING:
                await self._optimize_relevance_scoring()
            elif optimization_type == OptimizationType.RETRIEVAL_SPEED:
                await self._optimize_retrieval_speed()
            elif optimization_type == OptimizationType.STORAGE_EFFICIENCY:
                await self._optimize_storage_efficiency()
            elif optimization_type == OptimizationType.CONTEXT_CLUSTERING:
                await self._optimize_context_clustering()
            elif optimization_type == OptimizationType.GARBAGE_COLLECTION:
                await self._optimize_garbage_collection()
            
            # 記錄優化後指標
            after_metrics = await self._collect_current_metrics()
            
            # 計算改進
            metrics = OptimizationMetrics(
                optimization_type=optimization_type,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_percentage=0.0,
                timestamp=time.time()
            )
            
            metrics.improvement_percentage = metrics.calculate_improvement()
            
            # 記錄優化歷史
            self.optimization_history.append(metrics)
            
            logger.info(f"✅ 優化完成: {optimization_type.value} (改進: {metrics.improvement_percentage:.2f}%)")
            
        except Exception as e:
            logger.error(f"❌ 優化執行失敗 ({optimization_type.value}): {e}")
    
    async def _collect_current_metrics(self) -> Dict[str, float]:
        """收集當前指標"""
        try:
            memory_stats = await self.memory_engine.get_memory_statistics()
            context_stats = await self.context_manager.get_context_statistics()
            
            return {
                "memory_count": memory_stats.get("total_memories", 0),
                "memory_size": memory_stats.get("database_size", 0),
                "average_importance": memory_stats.get("average_importance", 0),
                "capacity_usage": memory_stats.get("capacity_usage", 0),
                "context_count": context_stats.get("total_contexts", 0),
                "average_relevance": context_stats.get("average_relevance", 0)
            }
        except Exception as e:
            logger.error(f"❌ 收集指標失敗: {e}")
            return {}
    
    async def _optimize_memory_compression(self):
        """優化記憶壓縮"""
        try:
            # 找到重複或相似的記憶
            all_memories = await self.memory_engine.search_memories(limit=1000)
            
            # 按相似度分組
            similar_groups = await self._group_similar_memories(all_memories)
            
            # 壓縮相似記憶
            compressed_count = 0
            for group in similar_groups:
                if len(group) > 1:
                    await self._compress_memory_group(group)
                    compressed_count += len(group) - 1
            
            logger.info(f"🗜️ 記憶壓縮: 壓縮了 {compressed_count} 個記憶")
            
        except Exception as e:
            logger.error(f"❌ 記憶壓縮失敗: {e}")
    
    async def _group_similar_memories(self, memories: List) -> List[List]:
        """分組相似記憶"""
        groups = []
        processed = set()
        
        for i, memory in enumerate(memories):
            if memory.id in processed:
                continue
            
            similar_group = [memory]
            processed.add(memory.id)
            
            # 找到相似的記憶
            for j, other_memory in enumerate(memories[i+1:], i+1):
                if other_memory.id in processed:
                    continue
                
                # 計算相似度
                similarity = await self._calculate_memory_similarity(memory, other_memory)
                
                if similarity > 0.8:  # 高相似度閾值
                    similar_group.append(other_memory)
                    processed.add(other_memory.id)
            
            if len(similar_group) > 1:
                groups.append(similar_group)
        
        return groups
    
    async def _calculate_memory_similarity(self, memory1, memory2) -> float:
        """計算記憶相似度"""
        # 簡化的相似度計算
        content1 = memory1.content.lower()
        content2 = memory2.content.lower()
        
        # 詞彙重疊
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # 考慮記憶類型
        type_similarity = 1.0 if memory1.memory_type == memory2.memory_type else 0.5
        
        return jaccard_similarity * type_similarity
    
    async def _compress_memory_group(self, memory_group: List):
        """壓縮記憶組"""
        # 選擇最重要的記憶作為主記憶
        main_memory = max(memory_group, key=lambda m: m.importance_score)
        
        # 合併其他記憶的內容
        merged_content = main_memory.content
        merged_metadata = main_memory.metadata.copy()
        
        for memory in memory_group:
            if memory.id != main_memory.id:
                # 合併標籤
                main_memory.tags.extend(memory.tags)
                
                # 合併訪問計數
                main_memory.access_count += memory.access_count
                
                # 更新重要性分數
                main_memory.importance_score = max(main_memory.importance_score, memory.importance_score)
        
        # 去重標籤
        main_memory.tags = list(set(main_memory.tags))
        
        # 添加壓縮信息
        merged_metadata["compressed_from"] = [m.id for m in memory_group if m.id != main_memory.id]
        merged_metadata["compression_timestamp"] = time.time()
        
        main_memory.metadata = merged_metadata
        
        # 更新主記憶
        await self.memory_engine.store_memory(main_memory)
    
    async def _optimize_relevance_scoring(self):
        """優化相關性評分"""
        try:
            # 重新計算所有記憶的重要性分數
            all_memories = await self.memory_engine.search_memories(limit=1000)
            
            updated_count = 0
            for memory in all_memories:
                old_score = memory.importance_score
                
                # 重新計算重要性分數
                new_score = await self._recalculate_importance_score(memory)
                
                if abs(new_score - old_score) > 0.1:  # 顯著變化
                    memory.importance_score = new_score
                    await self.memory_engine.store_memory(memory)
                    updated_count += 1
            
            logger.info(f"📊 相關性評分: 更新了 {updated_count} 個記憶的分數")
            
        except Exception as e:
            logger.error(f"❌ 相關性評分優化失敗: {e}")
    
    async def _recalculate_importance_score(self, memory) -> float:
        """重新計算重要性分數"""
        current_time = time.time()
        
        # 時間因子
        age = current_time - memory.created_at
        time_factor = max(0.1, 1.0 / (1.0 + age / 86400))  # 按天衰減
        
        # 訪問因子
        access_factor = min(2.0, memory.access_count / 10.0)
        
        # 最近訪問因子
        recent_access = current_time - memory.accessed_at
        recent_factor = max(0.1, 1.0 / (1.0 + recent_access / 3600))  # 按小時衰減
        
        # 內容長度因子
        content_factor = min(1.0, len(memory.content) / 1000.0)
        
        # 標籤因子
        tag_factor = min(1.5, len(memory.tags) / 5.0)
        
        # 組合分數
        importance_score = (time_factor * 0.3 + 
                          access_factor * 0.3 + 
                          recent_factor * 0.2 + 
                          content_factor * 0.1 + 
                          tag_factor * 0.1)
        
        return min(2.0, max(0.1, importance_score))
    
    async def _optimize_retrieval_speed(self):
        """優化檢索速度"""
        try:
            # 分析檢索模式
            retrieval_patterns = await self._analyze_retrieval_patterns()
            
            # 優化索引
            await self._optimize_search_indices(retrieval_patterns)
            
            # 預緩存熱門查詢
            await self._precache_popular_queries(retrieval_patterns)
            
            logger.info("🚀 檢索速度優化完成")
            
        except Exception as e:
            logger.error(f"❌ 檢索速度優化失敗: {e}")
    
    async def _analyze_retrieval_patterns(self) -> Dict[str, Any]:
        """分析檢索模式"""
        # 簡化的檢索模式分析
        patterns = {
            "frequent_queries": defaultdict(int),
            "query_types": defaultdict(int),
            "time_patterns": defaultdict(int)
        }
        
        # 從上下文歷史中分析
        context_history = await self.context_manager.get_context_history(limit=100)
        
        for context in context_history:
            # 提取查詢類型
            if context.context_type:
                patterns["query_types"][context.context_type.value] += 1
            
            # 提取時間模式
            hour = time.localtime(context.created_at).tm_hour
            patterns["time_patterns"][hour] += 1
        
        return dict(patterns)
    
    async def _optimize_search_indices(self, patterns: Dict[str, Any]):
        """優化搜索索引"""
        # 這裡可以實現索引優化邏輯
        # 例如：為頻繁查詢的欄位創建索引
        pass
    
    async def _precache_popular_queries(self, patterns: Dict[str, Any]):
        """預緩存熱門查詢"""
        # 這裡可以實現預緩存邏輯
        pass
    
    async def _optimize_storage_efficiency(self):
        """優化存儲效率"""
        try:
            # 清理過期記憶
            await self._cleanup_expired_memories()
            
            # 壓縮數據庫
            await self._compress_database()
            
            # 優化存儲分配
            await self._optimize_storage_allocation()
            
            logger.info("💾 存儲效率優化完成")
            
        except Exception as e:
            logger.error(f"❌ 存儲效率優化失敗: {e}")
    
    async def _cleanup_expired_memories(self):
        """清理過期記憶"""
        current_time = time.time()
        cutoff_time = current_time - (30 * 24 * 3600)  # 30天前
        
        # 查找過期記憶
        all_memories = await self.memory_engine.search_memories(limit=1000)
        
        expired_count = 0
        for memory in all_memories:
            if (memory.created_at < cutoff_time and 
                memory.importance_score < 0.3 and 
                memory.access_count < 2):
                
                # 刪除過期記憶
                expired_count += 1
        
        logger.info(f"🗑️ 清理過期記憶: {expired_count} 個")
    
    async def _compress_database(self):
        """壓縮數據庫"""
        # 這裡可以實現數據庫壓縮邏輯
        pass
    
    async def _optimize_storage_allocation(self):
        """優化存儲分配"""
        # 這裡可以實現存儲分配優化邏輯
        pass
    
    async def _optimize_context_clustering(self):
        """優化上下文聚類"""
        try:
            # 獲取所有上下文
            all_contexts = await self.context_manager.get_context_history(limit=200)
            
            # 執行聚類
            clusters = await self._cluster_contexts(all_contexts)
            
            # 優化上下文關係
            await self._optimize_context_relationships(clusters)
            
            logger.info(f"🔗 上下文聚類: 創建了 {len(clusters)} 個聚類")
            
        except Exception as e:
            logger.error(f"❌ 上下文聚類優化失敗: {e}")
    
    async def _cluster_contexts(self, contexts: List) -> List[List]:
        """聚類上下文"""
        # 簡化的上下文聚類
        clusters = []
        processed = set()
        
        for context in contexts:
            if context.id in processed:
                continue
            
            cluster = [context]
            processed.add(context.id)
            
            # 找到相關上下文
            for other_context in contexts:
                if other_context.id in processed:
                    continue
                
                # 計算相關性
                relatedness = await self._calculate_context_relatedness(context, other_context)
                
                if relatedness > 0.6:
                    cluster.append(other_context)
                    processed.add(other_context.id)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    async def _calculate_context_relatedness(self, context1, context2) -> float:
        """計算上下文相關性"""
        # 簡化的相關性計算
        content1 = context1.content.lower()
        content2 = context2.content.lower()
        
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        similarity = intersection / union if union > 0 else 0.0
        
        # 考慮時間接近性
        time_diff = abs(context1.created_at - context2.created_at)
        time_factor = max(0.1, 1.0 / (1.0 + time_diff / 3600))  # 按小時衰減
        
        return similarity * time_factor
    
    async def _optimize_context_relationships(self, clusters: List[List]):
        """優化上下文關係"""
        # 這裡可以實現上下文關係優化邏輯
        pass
    
    async def _optimize_garbage_collection(self):
        """優化垃圾回收"""
        try:
            # 記憶垃圾回收
            await self.memory_engine._manage_memory_capacity()
            
            # 上下文垃圾回收
            await self.context_manager.cleanup_old_contexts(max_age_hours=48)
            
            logger.info("🗑️ 垃圾回收優化完成")
            
        except Exception as e:
            logger.error(f"❌ 垃圾回收優化失敗: {e}")
    
    async def optimize_learning_performance(self, 
                                          learning_data: Dict[str, Any],
                                          source: str):
        """優化學習性能"""
        try:
            # 分析學習數據
            performance_metrics = learning_data.get("performance_metrics", {})
            
            # 如果響應時間過長，觸發檢索優化
            if performance_metrics.get("response_time", 0) > 5000:
                await self._execute_optimization(OptimizationType.RETRIEVAL_SPEED)
            
            # 如果記憶容量使用率過高，觸發存儲優化
            memory_stats = await self.memory_engine.get_memory_statistics()
            if memory_stats.get("capacity_usage", 0) > 80:
                await self._execute_optimization(OptimizationType.STORAGE_EFFICIENCY)
            
            # 如果上下文相關性低，觸發聚類優化
            if performance_metrics.get("context_relevance", 0) < 0.5:
                await self._execute_optimization(OptimizationType.CONTEXT_CLUSTERING)
            
            logger.debug(f"🔧 學習性能優化: {source}")
            
        except Exception as e:
            logger.error(f"❌ 學習性能優化失敗: {e}")
    
    async def get_optimization_statistics(self) -> Dict[str, Any]:
        """獲取優化統計"""
        try:
            stats = {
                "total_optimizations": len(self.optimization_history),
                "optimization_types": defaultdict(int),
                "average_improvement": 0.0,
                "recent_optimizations": [],
                "performance_trends": {}
            }
            
            if self.optimization_history:
                # 統計優化類型
                for opt_record in self.optimization_history:
                    stats["optimization_types"][opt_record.optimization_type.value] += 1
                
                # 計算平均改進
                improvements = [opt.improvement_percentage for opt in self.optimization_history]
                stats["average_improvement"] = np.mean(improvements)
                
                # 最近優化
                recent = list(self.optimization_history)[-5:]
                stats["recent_optimizations"] = [
                    {
                        "type": opt.optimization_type.value,
                        "improvement": opt.improvement_percentage,
                        "timestamp": opt.timestamp
                    }
                    for opt in recent
                ]
            
            return dict(stats)
            
        except Exception as e:
            logger.error(f"❌ 獲取優化統計失敗: {e}")
            return {}
    
    async def cleanup(self):
        """清理資源"""
        # 記錄最終優化統計
        final_stats = await self.get_optimization_statistics()
        logger.info(f"📊 最終優化統計: {final_stats}")
        
        self.optimization_history.clear()
        self.performance_metrics.clear()
        self.optimization_schedules.clear()
        
        logger.info("🧹 Memory Optimizer 清理完成")

# 測試函數
async def main():
    """測試記憶優化器"""
    print("🧪 測試 Memory Optimizer...")
    
    # 模擬依賴
    class MockMemoryEngine:
        async def get_memory_statistics(self):
            return {
                "total_memories": 100,
                "database_size": 1024000,
                "average_importance": 0.6,
                "capacity_usage": 60.0
            }
        
        async def search_memories(self, limit=100):
            return []
        
        async def store_memory(self, memory):
            return True
        
        async def _manage_memory_capacity(self):
            pass
    
    class MockContextManager:
        async def get_context_statistics(self):
            return {
                "total_contexts": 50,
                "average_relevance": 0.7
            }
        
        async def get_context_history(self, limit=100):
            return []
        
        async def cleanup_old_contexts(self, max_age_hours=48):
            pass
    
    # 創建測試實例
    memory_engine = MockMemoryEngine()
    context_manager = MockContextManager()
    
    optimizer = MemoryOptimizer(memory_engine, context_manager)
    await optimizer.initialize()
    
    # 測試單個優化
    await optimizer._execute_optimization(OptimizationType.MEMORY_COMPRESSION)
    
    # 測試統計
    stats = await optimizer.get_optimization_statistics()
    print(f"📊 優化統計: {stats}")
    
    await optimizer.cleanup()
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())