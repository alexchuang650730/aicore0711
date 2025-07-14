#!/usr/bin/env python3
"""
MemoryOS MCP - RLLM/DeepSeek-R1 SWE 訓練集成
整合 MemoryOS MCP 數據進行強化學習訓練
"""

import asyncio
import json
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """訓練樣例"""
    id: str
    input_text: str
    output_text: str
    reward_score: float
    context_data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    
    def to_rllm_format(self) -> Dict[str, Any]:
        """轉換為 RLLM 訓練格式"""
        return {
            "id": self.id,
            "prompt": self.input_text,
            "response": self.output_text,
            "reward": self.reward_score,
            "context": self.context_data,
            "metadata": {
                **self.metadata,
                "timestamp": self.timestamp,
                "source": "memoryos_mcp"
            }
        }

@dataclass
class TrainingBatch:
    """訓練批次"""
    batch_id: str
    examples: List[TrainingExample]
    batch_size: int
    created_at: float
    quality_score: float
    
    def to_deepseek_format(self) -> Dict[str, Any]:
        """轉換為 DeepSeek-R1 SWE 格式"""
        return {
            "batch_id": self.batch_id,
            "examples": [ex.to_rllm_format() for ex in self.examples],
            "batch_size": self.batch_size,
            "quality_score": self.quality_score,
            "created_at": self.created_at,
            "training_config": {
                "domain": "software_engineering",
                "model_type": "deepseek-r1-swe",
                "context_length": 24000,
                "reward_model": "user_satisfaction"
            }
        }

class RLLMIntegration:
    """RLLM 訓練集成器"""
    
    def __init__(self, memory_engine, context_manager):
        self.memory_engine = memory_engine
        self.context_manager = context_manager
        self.training_data_path = Path("training_data")
        self.training_data_path.mkdir(exist_ok=True)
        
        # 訓練配置
        self.min_reward_threshold = 0.5
        self.max_examples_per_batch = 100
        self.context_window_size = 8192
        self.reward_weights = {
            "user_satisfaction": 0.4,
            "response_quality": 0.3,
            "context_relevance": 0.2,
            "processing_efficiency": 0.1
        }
        
    async def initialize(self):
        """初始化 RLLM 集成器"""
        logger.info("🚀 初始化 RLLM Integration...")
        
        # 創建訓練數據庫
        self.training_db = sqlite3.connect(self.training_data_path / "training_data.db")
        await self._create_training_tables()
        
        logger.info("✅ RLLM Integration 初始化完成")
    
    async def _create_training_tables(self):
        """創建訓練數據表"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS training_examples (
            id TEXT PRIMARY KEY,
            input_text TEXT NOT NULL,
            output_text TEXT NOT NULL,
            reward_score REAL NOT NULL,
            context_data TEXT,
            metadata TEXT,
            timestamp REAL NOT NULL,
            used_in_training BOOLEAN DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS training_batches (
            batch_id TEXT PRIMARY KEY,
            examples_count INTEGER NOT NULL,
            quality_score REAL NOT NULL,
            created_at REAL NOT NULL,
            training_status TEXT DEFAULT 'pending'
        );
        
        CREATE INDEX IF NOT EXISTS idx_reward_score ON training_examples(reward_score);
        CREATE INDEX IF NOT EXISTS idx_timestamp ON training_examples(timestamp);
        CREATE INDEX IF NOT EXISTS idx_used_in_training ON training_examples(used_in_training);
        """
        
        self.training_db.executescript(create_sql)
        self.training_db.commit()
    
    async def collect_training_data(self, 
                                  days_back: int = 7,
                                  min_interactions: int = 100) -> int:
        """收集訓練數據"""
        logger.info(f"📊 收集最近 {days_back} 天的訓練數據...")
        
        # 從 MemoryOS MCP 獲取交互數據
        cutoff_time = time.time() - (days_back * 24 * 3600)
        
        claude_interactions = await self.memory_engine.search_memories(
            memory_type=self.memory_engine.MemoryType.CLAUDE_INTERACTION,
            limit=min_interactions * 2
        )
        
        training_examples = []
        
        for memory in claude_interactions:
            if memory.created_at < cutoff_time:
                continue
                
            # 提取交互數據
            metadata = memory.metadata
            if not all(key in metadata for key in ['user_input', 'claude_response']):
                continue
            
            # 計算獎勵分數
            reward_score = await self._calculate_reward_score(memory)
            
            if reward_score < self.min_reward_threshold:
                continue
            
            # 獲取上下文數據
            context_data = await self._extract_context_data(memory)
            
            # 創建訓練樣例
            example = TrainingExample(
                id=memory.id,
                input_text=metadata['user_input'],
                output_text=metadata['claude_response'],
                reward_score=reward_score,
                context_data=context_data,
                metadata={
                    "interaction_type": metadata.get('interaction_type', 'unknown'),
                    "response_time": metadata.get('response_time', 0),
                    "user_satisfaction": metadata.get('user_satisfaction', 0),
                    "context_enhanced": metadata.get('context_enhanced', False)
                },
                timestamp=memory.created_at
            )
            
            training_examples.append(example)
        
        # 存儲訓練樣例
        stored_count = await self._store_training_examples(training_examples)
        
        logger.info(f"✅ 收集到 {stored_count} 個訓練樣例")
        return stored_count
    
    async def _calculate_reward_score(self, memory) -> float:
        """計算獎勵分數"""
        metadata = memory.metadata
        
        # 基礎分數組件
        user_satisfaction = metadata.get('user_satisfaction', 0.5)
        response_quality = metadata.get('response_quality', 0.5)
        
        # 上下文相關性
        context_relevance = 0.5
        if metadata.get('context_enhanced', False):
            context_relevance = 0.8
        
        # 處理效率
        response_time = metadata.get('response_time', 5000)  # 毫秒
        processing_efficiency = max(0.1, min(1.0, 3000 / response_time))
        
        # 加權計算
        reward_score = (
            user_satisfaction * self.reward_weights['user_satisfaction'] +
            response_quality * self.reward_weights['response_quality'] +
            context_relevance * self.reward_weights['context_relevance'] +
            processing_efficiency * self.reward_weights['processing_efficiency']
        )
        
        return min(1.0, max(0.0, reward_score))
    
    async def _extract_context_data(self, memory) -> Dict[str, Any]:
        """提取上下文數據"""
        context_data = {
            "session_context": [],
            "related_interactions": [],
            "user_preferences": {},
            "project_context": {}
        }
        
        # 獲取相關上下文
        related_contexts = await self.context_manager.get_related_contexts(
            memory.id, 
            max_depth=2
        )
        
        for ctx in related_contexts:
            if ctx.context_type.value == "session":
                context_data["session_context"].append({
                    "content": ctx.content[:500],  # 限制長度
                    "timestamp": ctx.created_at
                })
            elif ctx.context_type.value == "claude_interaction":
                context_data["related_interactions"].append({
                    "content": ctx.content[:300],
                    "relevance": ctx.relevance_score
                })
        
        return context_data
    
    async def _store_training_examples(self, examples: List[TrainingExample]) -> int:
        """存儲訓練樣例"""
        cursor = self.training_db.cursor()
        stored_count = 0
        
        for example in examples:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO training_examples
                    (id, input_text, output_text, reward_score, context_data, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    example.id,
                    example.input_text,
                    example.output_text,
                    example.reward_score,
                    json.dumps(example.context_data),
                    json.dumps(example.metadata),
                    example.timestamp
                ))
                stored_count += 1
            except Exception as e:
                logger.error(f"❌ 存儲訓練樣例失敗: {e}")
        
        self.training_db.commit()
        return stored_count
    
    async def create_training_batch(self, batch_size: int = 50) -> Optional[TrainingBatch]:
        """創建訓練批次"""
        logger.info(f"📦 創建訓練批次 (size: {batch_size})...")
        
        # 獲取高質量的訓練樣例
        cursor = self.training_db.cursor()
        cursor.execute("""
            SELECT * FROM training_examples 
            WHERE used_in_training = 0 AND reward_score >= ?
            ORDER BY reward_score DESC, timestamp DESC
            LIMIT ?
        """, (self.min_reward_threshold, batch_size))
        
        rows = cursor.fetchall()
        if len(rows) < batch_size // 2:  # 至少要有一半的數據
            logger.warning("⚠️ 訓練數據不足，無法創建批次")
            return None
        
        # 創建訓練樣例
        examples = []
        for row in rows:
            example = TrainingExample(
                id=row[0],
                input_text=row[1],
                output_text=row[2],
                reward_score=row[3],
                context_data=json.loads(row[4]) if row[4] else {},
                metadata=json.loads(row[5]) if row[5] else {},
                timestamp=row[6]
            )
            examples.append(example)
        
        # 計算批次質量分數
        quality_score = np.mean([ex.reward_score for ex in examples])
        
        # 創建批次
        batch_id = f"batch_{int(time.time())}_{len(examples)}"
        batch = TrainingBatch(
            batch_id=batch_id,
            examples=examples,
            batch_size=len(examples),
            created_at=time.time(),
            quality_score=quality_score
        )
        
        # 存儲批次信息
        cursor.execute("""
            INSERT INTO training_batches
            (batch_id, examples_count, quality_score, created_at)
            VALUES (?, ?, ?, ?)
        """, (batch_id, len(examples), quality_score, batch.created_at))
        
        # 標記樣例已使用
        example_ids = [ex.id for ex in examples]
        cursor.execute(f"""
            UPDATE training_examples 
            SET used_in_training = 1 
            WHERE id IN ({','.join(['?' for _ in example_ids])})
        """, example_ids)
        
        self.training_db.commit()
        
        logger.info(f"✅ 創建訓練批次: {batch_id} (質量分數: {quality_score:.3f})")
        return batch
    
    async def export_for_deepseek_training(self, batch: TrainingBatch) -> str:
        """導出為 DeepSeek-R1 SWE 訓練格式"""
        logger.info(f"📤 導出 DeepSeek-R1 SWE 訓練數據: {batch.batch_id}")
        
        # 轉換為 DeepSeek 格式
        deepseek_data = batch.to_deepseek_format()
        
        # 添加 DeepSeek-R1 特定配置
        deepseek_data["training_config"].update({
            "model_base": "deepseek-r1-distill-qwen-32b",
            "rl_algorithm": "ppo",
            "learning_rate": 1e-6,
            "batch_size": batch.batch_size,
            "max_seq_length": 24000,
            "gradient_accumulation_steps": 4,
            "num_train_epochs": 3,
            "warmup_steps": 100,
            "reward_model_path": "memoryos_reward_model",
            "domain_specific_prompts": True,
            "context_enhancement": True
        })
        
        # 保存到文件
        output_file = self.training_data_path / f"deepseek_training_{batch.batch_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(deepseek_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ 導出完成: {output_file}")
        return str(output_file)
    
    async def create_rllm_training_script(self, batch: TrainingBatch) -> str:
        """創建 RLLM 訓練腳本"""
        training_script = f"""#!/bin/bash
# RLLM Training Script for MemoryOS MCP Data
# Generated: {datetime.now().isoformat()}
# Batch: {batch.batch_id}

set -e

# 配置
MODEL_BASE="deepseek-r1-distill-qwen-32b"
TRAINING_DATA="deepseek_training_{batch.batch_id}.json"
OUTPUT_DIR="./models/memoryos_enhanced_model"
REWARD_MODEL="./models/memoryos_reward_model"

# 確保目錄存在
mkdir -p $OUTPUT_DIR
mkdir -p ./logs

# 開始訓練
echo "🚀 開始 MemoryOS MCP 增強訓練..."
echo "📊 批次: {batch.batch_id}"
echo "📈 質量分數: {batch.quality_score:.3f}"
echo "🔢 樣例數量: {batch.batch_size}"

# 使用 RLLM 框架進行訓練
python -m rllm.train \\
    --model_name_or_path $MODEL_BASE \\
    --training_data $TRAINING_DATA \\
    --output_dir $OUTPUT_DIR \\
    --reward_model_path $REWARD_MODEL \\
    --learning_rate 1e-6 \\
    --batch_size {min(batch.batch_size, 8)} \\
    --gradient_accumulation_steps 4 \\
    --num_train_epochs 3 \\
    --max_seq_length 24000 \\
    --warmup_steps 100 \\
    --logging_steps 10 \\
    --save_steps 500 \\
    --evaluation_strategy steps \\
    --eval_steps 250 \\
    --load_best_model_at_end true \\
    --metric_for_best_model reward \\
    --greater_is_better true \\
    --logging_dir ./logs/{batch.batch_id} \\
    --report_to tensorboard \\
    --domain software_engineering \\
    --context_enhancement true \\
    --memoryos_integration true

echo "✅ 訓練完成！"
echo "📁 模型保存在: $OUTPUT_DIR"
echo "📊 訓練日誌: ./logs/{batch.batch_id}"

# 評估模型
echo "🧪 開始模型評估..."
python -m rllm.evaluate \\
    --model_path $OUTPUT_DIR \\
    --test_data validation_data.json \\
    --output_file evaluation_results_{batch.batch_id}.json

echo "🎉 MemoryOS MCP 增強訓練完成！"
"""
        
        script_file = self.training_data_path / f"train_{batch.batch_id}.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(training_script)
        
        # 設置執行權限
        script_file.chmod(0o755)
        
        logger.info(f"📝 創建訓練腳本: {script_file}")
        return str(script_file)
    
    async def get_training_statistics(self) -> Dict[str, Any]:
        """獲取訓練統計信息"""
        cursor = self.training_db.cursor()
        
        # 總訓練樣例
        cursor.execute("SELECT COUNT(*) FROM training_examples")
        total_examples = cursor.fetchone()[0]
        
        # 已使用的樣例
        cursor.execute("SELECT COUNT(*) FROM training_examples WHERE used_in_training = 1")
        used_examples = cursor.fetchone()[0]
        
        # 平均獎勵分數
        cursor.execute("SELECT AVG(reward_score) FROM training_examples")
        avg_reward = cursor.fetchone()[0] or 0.0
        
        # 訓練批次統計
        cursor.execute("SELECT COUNT(*) FROM training_batches")
        total_batches = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(quality_score) FROM training_batches")
        avg_batch_quality = cursor.fetchone()[0] or 0.0
        
        return {
            "total_examples": total_examples,
            "used_examples": used_examples,
            "available_examples": total_examples - used_examples,
            "average_reward": avg_reward,
            "total_batches": total_batches,
            "average_batch_quality": avg_batch_quality,
            "training_data_size": sum(f.stat().st_size for f in self.training_data_path.glob("*.json")),
            "last_collection": time.time()
        }
    
    async def cleanup(self):
        """清理資源"""
        if hasattr(self, 'training_db'):
            self.training_db.close()
        logger.info("🧹 RLLM Integration 清理完成")

# 創建全局 RLLM 集成實例
rllm_integration = None

async def create_rllm_integration(memory_engine, context_manager):
    """創建 RLLM 集成實例"""
    global rllm_integration
    rllm_integration = RLLMIntegration(memory_engine, context_manager)
    await rllm_integration.initialize()
    return rllm_integration

async def main():
    """測試 RLLM 集成"""
    print("🧪 測試 RLLM Integration...")
    
    # 模擬依賴
    class MockMemoryEngine:
        class MemoryType:
            CLAUDE_INTERACTION = "claude_interaction"
        
        async def search_memories(self, memory_type, limit):
            return []
    
    class MockContextManager:
        async def get_related_contexts(self, memory_id, max_depth):
            return []
    
    # 創建測試實例
    memory_engine = MockMemoryEngine()
    context_manager = MockContextManager()
    
    integration = await create_rllm_integration(memory_engine, context_manager)
    
    # 測試統計
    stats = await integration.get_training_statistics()
    print(f"📊 訓練統計: {stats}")
    
    await integration.cleanup()
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())