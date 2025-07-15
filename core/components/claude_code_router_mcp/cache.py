"""
Claude Code Router MCP - 緩存系統
高效的請求響應緩存實現
"""

import asyncio
import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
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
        
        # 啟動清理任務
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
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
        
        logger.debug(f"🧹 緩存驅逐完成: {len(expired_keys)} 過期, {self.stats['evictions']} 總驅逐")
    
    async def _cleanup_loop(self):
        """清理循環"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分鐘清理一次
                await self._evict_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"緩存清理失敗: {e}")
    
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
            "total_requests": self.stats["total_requests"],
            "memory_usage": self._calculate_memory_usage()
        }
    
    def _calculate_memory_usage(self) -> str:
        """計算記憶體使用量"""
        total_size = 0
        for entry in self.cache.values():
            try:
                # 粗略估算
                total_size += len(json.dumps(entry.value, default=str))
            except:
                total_size += 1000  # 默認大小
        
        if total_size < 1024:
            return f"{total_size} B"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.1f} KB"
        else:
            return f"{total_size / (1024 * 1024):.1f} MB"
    
    def get_cache_keys(self) -> List[str]:
        """獲取所有緩存鍵"""
        return list(self.cache.keys())
    
    def get_cache_info(self, key: str) -> Optional[Dict[str, Any]]:
        """獲取緩存條目信息"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        return {
            "key": key,
            "created_at": datetime.fromtimestamp(entry.created_at).isoformat(),
            "ttl": entry.ttl,
            "access_count": entry.access_count,
            "last_access": datetime.fromtimestamp(entry.last_access).isoformat(),
            "is_expired": entry.is_expired(),
            "size": len(json.dumps(entry.value, default=str))
        }
    
    async def extend_ttl(self, key: str, additional_ttl: int) -> bool:
        """延長TTL"""
        if key not in self.cache:
            return False
        
        entry = self.cache[key]
        entry.ttl += additional_ttl
        
        logger.debug(f"⏰ TTL延長: {key} (+{additional_ttl}s)")
        return True
    
    async def refresh_entry(self, key: str) -> bool:
        """刷新緩存條目（重置創建時間）"""
        if key not in self.cache:
            return False
        
        entry = self.cache[key]
        entry.created_at = time.time()
        entry.update_access()
        
        logger.debug(f"🔄 緩存刷新: {key}")
        return True
    
    async def get_popular_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取最受歡迎的緩存鍵"""
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].access_count,
            reverse=True
        )
        
        return [
            {
                "key": key,
                "access_count": entry.access_count,
                "last_access": datetime.fromtimestamp(entry.last_access).isoformat()
            }
            for key, entry in sorted_entries[:limit]
        ]
    
    async def close(self):
        """關閉緩存系統"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.clear()
        logger.info("🔒 RouterCache 已關閉")


class SmartCache(RouterCache):
    """智能緩存系統"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        super().__init__(ttl, max_size)
        self.model_cache_stats: Dict[str, Dict[str, Any]] = {}
        self.request_patterns: Dict[str, List[float]] = {}
    
    async def set_with_model_context(self, key: str, value: Any, 
                                   model_id: str, response_time: float,
                                   ttl: Optional[int] = None) -> bool:
        """帶模型上下文的緩存設置"""
        # 更新模型緩存統計
        if model_id not in self.model_cache_stats:
            self.model_cache_stats[model_id] = {
                "cache_count": 0,
                "avg_response_time": 0,
                "total_response_time": 0
            }
        
        stats = self.model_cache_stats[model_id]
        stats["cache_count"] += 1
        stats["total_response_time"] += response_time
        stats["avg_response_time"] = stats["total_response_time"] / stats["cache_count"]
        
        # 根據響應時間動態調整TTL
        if ttl is None:
            if response_time > 5.0:  # 慢響應緩存更久
                ttl = self.ttl * 2
            elif response_time < 1.0:  # 快響應緩存時間短
                ttl = self.ttl // 2
            else:
                ttl = self.ttl
        
        return await self.set(key, value, ttl)
    
    async def get_with_pattern_learning(self, key: str) -> Optional[Any]:
        """帶模式學習的緩存獲取"""
        # 記錄請求模式
        if key not in self.request_patterns:
            self.request_patterns[key] = []
        
        self.request_patterns[key].append(time.time())
        
        # 只保留最近的請求記錄
        cutoff_time = time.time() - 3600  # 1小時
        self.request_patterns[key] = [
            t for t in self.request_patterns[key] if t > cutoff_time
        ]
        
        result = await self.get(key)
        
        # 如果是頻繁請求的項目，自動延長TTL
        if result is not None and len(self.request_patterns[key]) > 5:
            await self.extend_ttl(key, 1800)  # 延長30分鐘
        
        return result
    
    def get_model_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """獲取模型緩存統計"""
        return self.model_cache_stats
    
    def get_request_patterns(self) -> Dict[str, Any]:
        """獲取請求模式分析"""
        patterns = {}
        
        for key, timestamps in self.request_patterns.items():
            if len(timestamps) > 1:
                intervals = [
                    timestamps[i] - timestamps[i-1]
                    for i in range(1, len(timestamps))
                ]
                
                patterns[key] = {
                    "request_count": len(timestamps),
                    "avg_interval": sum(intervals) / len(intervals) if intervals else 0,
                    "frequency": len(timestamps) / 3600,  # 每小時請求次數
                    "last_request": datetime.fromtimestamp(timestamps[-1]).isoformat()
                }
        
        return patterns
    
    async def preload_popular_responses(self, popular_requests: List[Dict[str, Any]]):
        """預載入流行響應"""
        for request_data in popular_requests:
            # 這裡可以實現預載入邏輯
            # 例如：提前計算常見請求的響應並緩存
            pass
    
    def get_cache_efficiency(self) -> Dict[str, Any]:
        """獲取緩存效率分析"""
        base_stats = self.get_stats()
        
        # 計算平均訪問次數
        total_access = sum(entry.access_count for entry in self.cache.values())
        avg_access = total_access / len(self.cache) if self.cache else 0
        
        # 計算熱點數據比例
        hot_entries = sum(1 for entry in self.cache.values() if entry.access_count > avg_access)
        hot_ratio = hot_entries / len(self.cache) if self.cache else 0
        
        return {
            **base_stats,
            "avg_access_count": avg_access,
            "hot_data_ratio": f"{hot_ratio * 100:.1f}%",
            "model_stats": self.model_cache_stats,
            "active_patterns": len(self.request_patterns)
        }