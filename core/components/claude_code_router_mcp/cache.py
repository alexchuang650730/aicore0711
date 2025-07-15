"""
Claude Code Router MCP - 緩存系統
高效的請求響應緩存實現
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """緩存條目"""
    key: str
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_access: float = 0
    
    def __post_init__(self):
        if self.last_access == 0:
            self.last_access = self.created_at
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """更新訪問統計"""
        self.access_count += 1
        self.last_access = time.time()


class RouterCache:
    """路由器緩存系統"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
        
        logger.info(f"📦 RouterCache 初始化完成 (TTL: {ttl}s, Max Size: {max_size})")
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        self.stats["total_requests"] += 1
        
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        
        # 檢查過期
        if entry.is_expired():
            del self.cache[key]
            self.stats["misses"] += 1
            return None
        
        # 更新訪問統計
        entry.update_access()
        self.stats["hits"] += 1
        
        logger.debug(f"🎯 緩存命中: {key}")
        return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """設置緩存值"""
        if ttl is None:
            ttl = self.ttl
        
        # 檢查容量
        if len(self.cache) >= self.max_size:
            await self._evict_entries()
        
        # 創建緩存條目
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl
        )
        
        self.cache[key] = entry
        
        logger.debug(f"💾 緩存設置: {key} (TTL: {ttl}s)")
        return True
    
    async def delete(self, key: str) -> bool:
        """刪除緩存值"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"🗑️ 緩存刪除: {key}")
            return True
        return False
    
    async def clear(self):
        """清空緩存"""
        self.cache.clear()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
        logger.info("🧹 緩存已清空")
    
    async def _evict_entries(self):
        """驅逐緩存條目"""
        if not self.cache:
            return
        
        # 移除過期條目
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats["evictions"] += 1
        
        # 如果還需要空間，使用LRU策略
        if len(self.cache) >= self.max_size:
            # 按最後訪問時間排序
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].last_access
            )
            
            # 驅逐最少使用的條目
            evict_count = max(1, len(self.cache) // 10)  # 驅逐10%
            for key, _ in sorted_entries[:evict_count]:
                del self.cache[key]
                self.stats["evictions"] += 1
        
        logger.debug(f"🧹 緩存驅逐完成: {len(expired_keys)} 過期")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        hit_rate = (self.stats["hits"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": f"{hit_rate:.2f}%",
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "total_requests": self.stats["total_requests"]
        }
    
    async def close(self):
        """關閉緩存系統"""
        await self.clear()
        logger.info("🔒 RouterCache 已關閉")