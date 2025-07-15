#!/usr/bin/env python3
"""
MemoryOS MCP - 記憶引擎
核心記憶存儲和檢索系統
"""

import sqlite3
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """記憶類型"""
    EPISODIC = "episodic"        # 特定事件記憶
    SEMANTIC = "semantic"        # 事實和知識記憶
    PROCEDURAL = "procedural"    # 技能和流程記憶
    WORKING = "working"          # 工作記憶
    CLAUDE_INTERACTION = "claude_interaction"  # Claude Code 互動記憶
    USER_PREFERENCE = "user_preference"       # 用戶偏好記憶

@dataclass
class Memory:
    """記憶項目"""
    id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any]
    created_at: float
    accessed_at: float
    access_count: int
    importance_score: float
    tags: List[str]
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """從字典創建"""
        if 'memory_type' in data:
            data['memory_type'] = MemoryType(data['memory_type'])
        return cls(**data)

class MemoryEngine:
    """記憶引擎基類"""
    pass


class MemoryOSEngine(MemoryEngine):
    """記憶引擎核心類"""
    
    def __init__(self, db_path: str = "memoryos.db", max_memories: int = 10000):
        self.db_path = Path(db_path)
        self.max_memories = max_memories
        self.working_memory: Dict[str, Memory] = {}
        self.max_working_memory = 100
        self.connection = None
        self.is_initialized = False
        
    async def initialize(self):
        """初始化記憶引擎"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.execute('PRAGMA journal_mode=WAL')
            self.connection.execute('PRAGMA synchronous=NORMAL')
            
            # 創建表結構
            await self._create_tables()
            
            # 載入工作記憶
            await self._load_working_memory()
            
            self.is_initialized = True
            logger.info(f"✅ MemoryEngine 初始化完成 (DB: {self.db_path})")
            
        except Exception as e:
            logger.error(f"❌ MemoryEngine 初始化失敗: {e}")
            raise
    
    async def _create_tables(self):
        """創建數據庫表"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at REAL NOT NULL,
            accessed_at REAL NOT NULL,
            access_count INTEGER DEFAULT 0,
            importance_score REAL DEFAULT 0.0,
            tags TEXT,
            embedding BLOB
        );
        
        CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type);
        CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at);
        CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance_score);
        CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags);
        """
        
        self.connection.executescript(create_sql)
        self.connection.commit()
    
    async def _load_working_memory(self):
        """載入工作記憶"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM memories 
            WHERE memory_type = ? 
            ORDER BY accessed_at DESC 
            LIMIT ?
        """, (MemoryType.WORKING.value, self.max_working_memory))
        
        rows = cursor.fetchall()
        for row in rows:
            memory = self._row_to_memory(row)
            self.working_memory[memory.id] = memory
    
    def _row_to_memory(self, row) -> Memory:
        """將數據庫行轉換為記憶對象"""
        return Memory(
            id=row[0],
            memory_type=MemoryType(row[1]),
            content=row[2],
            metadata=json.loads(row[3]) if row[3] else {},
            created_at=row[4],
            accessed_at=row[5],
            access_count=row[6],
            importance_score=row[7],
            tags=json.loads(row[8]) if row[8] else [],
            embedding=np.frombuffer(row[9]) if row[9] else None
        )
    
    async def store_memory(self, memory: Memory) -> bool:
        """存儲記憶"""
        try:
            # 生成嵌入向量
            if memory.embedding is None:
                memory.embedding = self._generate_embedding(memory.content)
            
            # 插入到數據庫
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO memories 
                (id, memory_type, content, metadata, created_at, accessed_at, 
                 access_count, importance_score, tags, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.memory_type.value,
                memory.content,
                json.dumps(memory.metadata),
                memory.created_at,
                memory.accessed_at,
                memory.access_count,
                memory.importance_score,
                json.dumps(memory.tags),
                memory.embedding.tobytes() if memory.embedding is not None else None
            ))
            
            self.connection.commit()
            
            # 更新工作記憶
            if memory.memory_type == MemoryType.WORKING:
                await self._update_working_memory(memory)
            
            # 檢查記憶容量
            await self._manage_memory_capacity()
            
            logger.debug(f"✅ 存儲記憶: {memory.id} ({memory.memory_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 存儲記憶失敗: {e}")
            return False
    
    async def _update_working_memory(self, memory: Memory):
        """更新工作記憶"""
        self.working_memory[memory.id] = memory
        
        # 限制工作記憶大小
        if len(self.working_memory) > self.max_working_memory:
            # 移除最舊的記憶
            oldest_id = min(self.working_memory.keys(), 
                          key=lambda x: self.working_memory[x].accessed_at)
            del self.working_memory[oldest_id]
    
    async def retrieve_memory(self, memory_id: str) -> Optional[Memory]:
        """檢索單個記憶"""
        try:
            # 先檢查工作記憶
            if memory_id in self.working_memory:
                memory = self.working_memory[memory_id]
                await self._update_memory_access(memory)
                return memory
            
            # 從數據庫檢索
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if row:
                memory = self._row_to_memory(row)
                await self._update_memory_access(memory)
                return memory
                
            return None
            
        except Exception as e:
            logger.error(f"❌ 檢索記憶失敗: {e}")
            return None
    
    async def search_memories(self, 
                            query: str = "",
                            memory_type: Optional[MemoryType] = None,
                            tags: Optional[List[str]] = None,
                            limit: int = 10,
                            min_importance: float = 0.0) -> List[Memory]:
        """搜索記憶"""
        try:
            conditions = []
            params = []
            
            if memory_type:
                conditions.append("memory_type = ?")
                params.append(memory_type.value)
            
            if tags:
                for tag in tags:
                    conditions.append("tags LIKE ?")
                    params.append(f"%{tag}%")
            
            if min_importance > 0:
                conditions.append("importance_score >= ?")
                params.append(min_importance)
            
            if query:
                conditions.append("content LIKE ?")
                params.append(f"%{query}%")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT * FROM memories 
                WHERE {where_clause}
                ORDER BY importance_score DESC, accessed_at DESC
                LIMIT ?
            """, params + [limit])
            
            rows = cursor.fetchall()
            memories = [self._row_to_memory(row) for row in rows]
            
            # 更新訪問統計
            for memory in memories:
                await self._update_memory_access(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ 搜索記憶失敗: {e}")
            return []
    
    async def get_similar_memories(self, 
                                 content: str, 
                                 memory_type: Optional[MemoryType] = None,
                                 limit: int = 5) -> List[Memory]:
        """獲取相似記憶"""
        try:
            query_embedding = self._generate_embedding(content)
            
            # 簡化的相似度計算（在實際實現中應該使用向量數據庫）
            cursor = self.connection.cursor()
            conditions = []
            params = []
            
            if memory_type:
                conditions.append("memory_type = ?")
                params.append(memory_type.value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor.execute(f"""
                SELECT * FROM memories 
                WHERE {where_clause} AND embedding IS NOT NULL
                ORDER BY importance_score DESC
                LIMIT ?
            """, params + [limit * 2])  # 獲取更多候選
            
            rows = cursor.fetchall()
            memories = [self._row_to_memory(row) for row in rows]
            
            # 計算相似度並排序
            similarities = []
            for memory in memories:
                if memory.embedding is not None:
                    similarity = self._cosine_similarity(query_embedding, memory.embedding)
                    similarities.append((memory, similarity))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return [mem for mem, _ in similarities[:limit]]
            
        except Exception as e:
            logger.error(f"❌ 獲取相似記憶失敗: {e}")
            return []
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成嵌入向量（簡化版）"""
        # 這裡使用簡化的嵌入生成，實際應該使用專業的嵌入模型
        words = text.lower().split()
        embedding = np.random.random(128)  # 128維向量
        
        # 簡單的詞頻統計影響
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # 根據詞頻調整嵌入
        for i, word in enumerate(words[:128]):
            if i < len(embedding):
                embedding[i] *= word_counts.get(word, 1)
        
        return embedding / np.linalg.norm(embedding)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算餘弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    async def _update_memory_access(self, memory: Memory):
        """更新記憶訪問統計"""
        memory.accessed_at = time.time()
        memory.access_count += 1
        memory.importance_score = self._calculate_importance(memory)
        
        # 更新數據庫
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE memories 
            SET accessed_at = ?, access_count = ?, importance_score = ?
            WHERE id = ?
        """, (memory.accessed_at, memory.access_count, memory.importance_score, memory.id))
        self.connection.commit()
    
    def _calculate_importance(self, memory: Memory) -> float:
        """計算記憶重要性分數"""
        current_time = time.time()
        age = current_time - memory.created_at
        
        # 基礎分數
        base_score = 1.0
        
        # 訪問頻率影響
        frequency_score = min(memory.access_count / 10.0, 2.0)
        
        # 時間衰減影響
        time_decay = max(0.1, 1.0 / (1.0 + age / 86400))  # 按天衰減
        
        # 記憶類型權重
        type_weights = {
            MemoryType.CLAUDE_INTERACTION: 1.5,
            MemoryType.USER_PREFERENCE: 1.3,
            MemoryType.PROCEDURAL: 1.2,
            MemoryType.SEMANTIC: 1.0,
            MemoryType.EPISODIC: 0.8,
            MemoryType.WORKING: 0.5
        }
        
        type_weight = type_weights.get(memory.memory_type, 1.0)
        
        return base_score * frequency_score * time_decay * type_weight
    
    async def _manage_memory_capacity(self):
        """管理記憶容量"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        count = cursor.fetchone()[0]
        
        if count > self.max_memories:
            # 刪除最不重要的記憶
            to_delete = count - self.max_memories + 100  # 多刪除一些
            
            cursor.execute("""
                DELETE FROM memories 
                WHERE id IN (
                    SELECT id FROM memories 
                    ORDER BY importance_score ASC, accessed_at ASC
                    LIMIT ?
                )
            """, (to_delete,))
            
            self.connection.commit()
            logger.info(f"🗑️ 清理記憶: 刪除 {to_delete} 個低重要性記憶")
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """獲取記憶統計信息"""
        cursor = self.connection.cursor()
        
        # 總記憶數
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        
        # 按類型統計
        cursor.execute("""
            SELECT memory_type, COUNT(*) 
            FROM memories 
            GROUP BY memory_type
        """)
        type_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 平均重要性
        cursor.execute("SELECT AVG(importance_score) FROM memories")
        avg_importance = cursor.fetchone()[0] or 0.0
        
        # 工作記憶統計
        working_memory_count = len(self.working_memory)
        
        return {
            "total_memories": total_memories,
            "working_memory_count": working_memory_count,
            "type_distribution": type_counts,
            "average_importance": avg_importance,
            "database_size": self.db_path.stat().st_size if self.db_path.exists() else 0,
            "max_capacity": self.max_memories,
            "capacity_usage": (total_memories / self.max_memories) * 100
        }
    
    async def cleanup(self):
        """清理資源"""
        if self.connection:
            self.connection.close()
            self.connection = None
        
        self.working_memory.clear()
        logger.info("🧹 MemoryEngine 清理完成")

# 創建全局記憶引擎實例
memory_engine = MemoryEngine()

async def main():
    """測試記憶引擎"""
    print("🧪 測試 MemoryEngine...")
    
    await memory_engine.initialize()
    
    # 測試存儲記憶
    test_memory = Memory(
        id="test_001",
        memory_type=MemoryType.CLAUDE_INTERACTION,
        content="用戶問了如何使用 Python 進行數據分析",
        metadata={"user_id": "user123", "topic": "data_analysis"},
        created_at=time.time(),
        accessed_at=time.time(),
        access_count=1,
        importance_score=1.0,
        tags=["python", "data_analysis", "question"]
    )
    
    success = await memory_engine.store_memory(test_memory)
    print(f"✅ 存儲測試: {'成功' if success else '失敗'}")
    
    # 測試檢索
    retrieved = await memory_engine.retrieve_memory("test_001")
    print(f"✅ 檢索測試: {'成功' if retrieved else '失敗'}")
    
    # 測試搜索
    results = await memory_engine.search_memories(
        query="Python",
        memory_type=MemoryType.CLAUDE_INTERACTION,
        limit=5
    )
    print(f"✅ 搜索測試: 找到 {len(results)} 個結果")
    
    # 獲取統計信息
    stats = await memory_engine.get_memory_statistics()
    print(f"📊 記憶統計: {stats['total_memories']} 個記憶")
    
    await memory_engine.cleanup()
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())