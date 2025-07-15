#!/usr/bin/env python3
"""
MemoryOS MCP API 服務器
提供 RESTful API 接口供 ClaudeEditor 前端調用
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from contextlib import asynccontextmanager

from .memory_engine import MemoryEngine, Memory, MemoryType
from .context_manager import ContextManager, ContextType
from .rllm_integration import RLLMIntegration
from .learning_adapter import LearningAdapter
from .personalization_manager import PersonalizationManager
from .memory_optimizer import MemoryOptimizer

logger = logging.getLogger(__name__)

# Pydantic 模型
class MemoryOSInitRequest(BaseModel):
    config: Dict[str, Any] = Field(default_factory=dict)

class ContextEnhancementRequest(BaseModel):
    query: str
    context_type: str = "claude_interaction"
    limit: int = 5

class InteractionRecordRequest(BaseModel):
    user_input: str
    claude_response: str
    response_time: float
    user_satisfaction: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PowerAutomationLearningRequest(BaseModel):
    source: str
    data: Dict[str, Any]
    learning_type: str
    timestamp: float

class TrainingDataRequest(BaseModel):
    days_back: int = 7
    min_interactions: int = 100
    batch_size: int = 50

# 全局實例
memory_engine = None
context_manager = None
rllm_integration = None
learning_adapter = None
personalization_manager = None
memory_optimizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命周期管理"""
    # 啟動時初始化
    await initialize_memoryos_components()
    yield
    # 關閉時清理
    await cleanup_memoryos_components()

app = FastAPI(
    title="MemoryOS MCP API",
    description="PowerAutomation Core Memory Management API",
    version="4.6.9.4",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_memoryos_components():
    """初始化 MemoryOS MCP 組件"""
    global memory_engine, context_manager, rllm_integration
    global learning_adapter, personalization_manager, memory_optimizer
    
    logger.info("🚀 初始化 MemoryOS MCP 組件...")
    
    try:
        # 初始化核心組件
        memory_engine = MemoryEngine()
        await memory_engine.initialize()
        
        context_manager = ContextManager()
        await context_manager.initialize()
        
        # 初始化 RLLM 集成
        rllm_integration = RLLMIntegration(memory_engine, context_manager)
        await rllm_integration.initialize()
        
        # 初始化其他組件
        learning_adapter = LearningAdapter(memory_engine, context_manager)
        await learning_adapter.initialize()
        
        personalization_manager = PersonalizationManager(memory_engine, context_manager)
        await personalization_manager.initialize()
        
        memory_optimizer = MemoryOptimizer(memory_engine, context_manager)
        await memory_optimizer.initialize()
        
        logger.info("✅ MemoryOS MCP 組件初始化完成")
        
    except Exception as e:
        logger.error(f"❌ MemoryOS MCP 初始化失敗: {e}")
        raise

async def cleanup_memoryos_components():
    """清理 MemoryOS MCP 組件"""
    global memory_engine, context_manager, rllm_integration
    global learning_adapter, personalization_manager, memory_optimizer
    
    logger.info("🧹 清理 MemoryOS MCP 組件...")
    
    if memory_engine:
        await memory_engine.cleanup()
    if rllm_integration:
        await rllm_integration.cleanup()
    if learning_adapter:
        await learning_adapter.cleanup()
    if personalization_manager:
        await personalization_manager.cleanup()
    if memory_optimizer:
        await memory_optimizer.cleanup()
    
    logger.info("✅ MemoryOS MCP 組件清理完成")

@app.post("/api/memoryos/initialize")
async def initialize_memoryos(request: MemoryOSInitRequest):
    """初始化 MemoryOS MCP"""
    try:
        # 組件已經在應用啟動時初始化
        stats = await memory_engine.get_memory_statistics()
        
        return {
            "success": True,
            "message": "MemoryOS MCP 已初始化",
            "statistics": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"❌ MemoryOS 初始化失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memoryos/context-enhancement")
async def get_context_enhancement(request: ContextEnhancementRequest):
    """獲取上下文增強"""
    try:
        # 1. 獲取相關記憶
        similar_memories = await memory_engine.get_similar_memories(
            content=request.query,
            memory_type=MemoryType.CLAUDE_INTERACTION,
            limit=request.limit
        )
        
        # 2. 獲取上下文推薦
        context_recommendations = await context_manager.get_context_recommendations(
            query=request.query,
            context_type=ContextType.CLAUDE_INTERACTION,
            limit=request.limit
        )
        
        # 3. 獲取用戶偏好
        user_preferences = await personalization_manager.get_user_preferences(
            context=request.query
        )
        
        # 4. 獲取最佳實踐
        best_practices = await learning_adapter.get_best_practices(
            query=request.query,
            domain="software_engineering"
        )
        
        enhancement = {
            "relevant_contexts": [
                {
                    "id": ctx.id,
                    "content": ctx.content[:200],  # 限制內容長度
                    "relevance_score": ctx.relevance_score,
                    "context_type": ctx.context_type.value,
                    "timestamp": ctx.last_accessed
                }
                for ctx in context_recommendations
            ],
            "similar_interactions": [
                {
                    "id": mem.id,
                    "content": mem.content[:200],
                    "importance_score": mem.importance_score,
                    "access_count": mem.access_count,
                    "timestamp": mem.created_at
                }
                for mem in similar_memories
            ],
            "user_preferences": user_preferences,
            "best_practices": best_practices,
            "enhancement_quality": len(similar_memories) * 0.2 + len(context_recommendations) * 0.3
        }
        
        return {
            "success": True,
            "enhancement": enhancement,
            "query": request.query,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取上下文增強失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memoryos/record-interaction")
async def record_interaction(request: InteractionRecordRequest):
    """記錄交互數據"""
    try:
        # 1. 創建記憶
        memory_id = f"interaction_{int(time.time())}_{hash(request.user_input) % 10000}"
        
        interaction_content = f"""
        User: {request.user_input}
        Claude: {request.claude_response}
        """
        
        memory = Memory(
            id=memory_id,
            memory_type=MemoryType.CLAUDE_INTERACTION,
            content=interaction_content,
            metadata={
                "user_input": request.user_input,
                "claude_response": request.claude_response,
                "response_time": request.response_time,
                "user_satisfaction": request.user_satisfaction,
                "interaction_type": "claude_code",
                **request.metadata
            },
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            importance_score=request.user_satisfaction,
            tags=["claude_interaction", "software_engineering"]
        )
        
        # 2. 存儲記憶
        success = await memory_engine.store_memory(memory)
        
        if success:
            # 3. 創建上下文
            context_id = await context_manager.create_claude_interaction_context(
                user_input=request.user_input,
                claude_response=request.claude_response,
                metadata={
                    "response_time": request.response_time,
                    "user_satisfaction": request.user_satisfaction,
                    **request.metadata
                }
            )
            
            # 4. 學習適配
            await learning_adapter.process_interaction(
                interaction_data={
                    "memory_id": memory_id,
                    "context_id": context_id,
                    "user_input": request.user_input,
                    "claude_response": request.claude_response,
                    "user_satisfaction": request.user_satisfaction,
                    "response_time": request.response_time
                }
            )
            
            return {
                "success": True,
                "memory_id": memory_id,
                "context_id": context_id,
                "timestamp": time.time()
            }
        else:
            raise HTTPException(status_code=500, detail="記憶存儲失敗")
            
    except Exception as e:
        logger.error(f"❌ 記錄交互失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/powerautomation/learn")
async def powerautomation_learn(request: PowerAutomationLearningRequest):
    """PowerAutomation Core 學習接口"""
    try:
        # 1. 記錄學習數據
        await learning_adapter.record_learning_data(
            source=request.source,
            data=request.data,
            learning_type=request.learning_type,
            timestamp=request.timestamp
        )
        
        # 2. 觸發學習優化
        await memory_optimizer.optimize_learning_performance(
            learning_data=request.data,
            source=request.source
        )
        
        # 3. 更新個性化模型
        await personalization_manager.update_user_model(
            interaction_data=request.data,
            source=request.source
        )
        
        return {
            "success": True,
            "message": "學習數據已記錄",
            "source": request.source,
            "learning_type": request.learning_type,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ PowerAutomation 學習失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memoryos/learning-stats")
async def get_learning_stats():
    """獲取學習統計"""
    try:
        memory_stats = await memory_engine.get_memory_statistics()
        context_stats = await context_manager.get_context_statistics()
        learning_stats = await learning_adapter.get_learning_statistics()
        
        return {
            "success": True,
            "stats": {
                "totalInteractions": memory_stats.get("total_memories", 0),
                "successRate": learning_stats.get("success_rate", 0.0),
                "avgResponseTime": learning_stats.get("avg_response_time", 0.0),
                "contextEnhancementRate": learning_stats.get("context_enhancement_rate", 0.0),
                "userSatisfaction": learning_stats.get("avg_user_satisfaction", 0.0),
                "memoryUtilization": memory_stats.get("capacity_usage", 0.0),
                "contextCount": context_stats.get("total_contexts", 0)
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取學習統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memoryos/training/collect")
async def collect_training_data(request: TrainingDataRequest, background_tasks: BackgroundTasks):
    """收集訓練數據"""
    try:
        # 後台任務收集數據
        background_tasks.add_task(
            collect_training_data_background,
            request.days_back,
            request.min_interactions,
            request.batch_size
        )
        
        return {
            "success": True,
            "message": "訓練數據收集已開始",
            "parameters": {
                "days_back": request.days_back,
                "min_interactions": request.min_interactions,
                "batch_size": request.batch_size
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ 收集訓練數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def collect_training_data_background(days_back: int, min_interactions: int, batch_size: int):
    """後台收集訓練數據"""
    try:
        logger.info(f"📊 開始收集訓練數據 (days_back={days_back}, min_interactions={min_interactions})")
        
        # 收集數據
        collected_count = await rllm_integration.collect_training_data(
            days_back=days_back,
            min_interactions=min_interactions
        )
        
        if collected_count >= batch_size:
            # 創建訓練批次
            batch = await rllm_integration.create_training_batch(batch_size=batch_size)
            
            if batch:
                # 導出 DeepSeek 格式
                deepseek_file = await rllm_integration.export_for_deepseek_training(batch)
                
                # 創建訓練腳本
                script_file = await rllm_integration.create_rllm_training_script(batch)
                
                logger.info(f"✅ 訓練數據準備完成: {deepseek_file}")
                logger.info(f"📝 訓練腳本: {script_file}")
        
    except Exception as e:
        logger.error(f"❌ 後台收集訓練數據失敗: {e}")

@app.get("/api/memoryos/training/stats")
async def get_training_stats():
    """獲取訓練統計"""
    try:
        stats = await rllm_integration.get_training_statistics()
        return {
            "success": True,
            "training_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"❌ 獲取訓練統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memoryos/health")
async def health_check():
    """健康檢查"""
    try:
        memory_stats = await memory_engine.get_memory_statistics()
        context_stats = await context_manager.get_context_statistics()
        
        return {
            "status": "healthy",
            "components": {
                "memory_engine": memory_engine.is_initialized,
                "context_manager": True,
                "rllm_integration": True,
                "learning_adapter": True,
                "personalization_manager": True,
                "memory_optimizer": True
            },
            "statistics": {
                "memory": memory_stats,
                "context": context_stats
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 啟動服務器
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )