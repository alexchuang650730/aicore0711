#!/usr/bin/env python3
"""
Result Capture - 結果捕獲
捕獲命令執行結果並進行處理
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CapturedResult:
    """捕獲的結果"""
    id: str
    command: str
    result: Dict[str, Any]
    platform: str
    timestamp: float
    metadata: Dict[str, Any]

class ResultCapture:
    """結果捕獲組件"""
    
    def __init__(self):
        self.captured_results = []
        self.callbacks = []
        self.filters = []
        self.max_results = 1000
        self.is_initialized = False
        
    async def initialize(self):
        """初始化結果捕獲"""
        print("📸 初始化結果捕獲...")
        self.is_initialized = True
        print("✅ 結果捕獲初始化完成")
    
    def add_callback(self, callback: Callable):
        """添加結果回調"""
        self.callbacks.append(callback)
        print(f"📋 添加結果回調: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")
    
    def add_filter(self, filter_func: Callable[[str], bool]):
        """添加捕獲過濾器"""
        self.filters.append(filter_func)
        print(f"🔍 添加捕獲過濾器")
    
    async def capture_result(self, command: str, result: Dict[str, Any], platform: str = "unknown") -> CapturedResult:
        """捕獲命令結果"""
        # 檢查過濾器
        if self.filters:
            should_capture = any(filter_func(command) for filter_func in self.filters)
            if not should_capture:
                return None
        
        # 創建捕獲結果
        captured = CapturedResult(
            id=f"result_{uuid.uuid4().hex[:8]}",
            command=command,
            result=result,
            platform=platform,
            timestamp=time.time(),
            metadata={
                "capture_method": "direct",
                "result_size": len(str(result))
            }
        )
        
        # 添加到結果列表
        self.captured_results.append(captured)
        
        # 維護最大結果數量
        if len(self.captured_results) > self.max_results:
            self.captured_results = self.captured_results[-self.max_results:]
        
        print(f"📸 結果已捕獲: {command[:50]}... -> {platform}")
        
        # 調用回調
        for callback in self.callbacks:
            try:
                await self._call_callback(callback, captured)
            except Exception as e:
                logger.error(f"結果回調錯誤: {e}")
        
        return captured
    
    async def _call_callback(self, callback: Callable, captured: CapturedResult):
        """調用回調函數"""
        if asyncio.iscoroutinefunction(callback):
            await callback(captured.result)
        else:
            callback(captured.result)
    
    def get_recent_results(self, limit: int = 10) -> List[CapturedResult]:
        """獲取最近的結果"""
        return self.captured_results[-limit:]
    
    def search_results(self, query: str) -> List[CapturedResult]:
        """搜索結果"""
        results = []
        query_lower = query.lower()
        
        for captured in self.captured_results:
            if (query_lower in captured.command.lower() or
                query_lower in str(captured.result).lower()):
                results.append(captured)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        if not self.captured_results:
            return {
                "total_results": 0,
                "platforms": {},
                "success_rate": 0.0
            }
        
        platforms = {}
        success_count = 0
        
        for captured in self.captured_results:
            # 統計平台
            platform = captured.platform
            if platform not in platforms:
                platforms[platform] = 0
            platforms[platform] += 1
            
            # 統計成功率
            if captured.result.get("status") == "success":
                success_count += 1
        
        return {
            "total_results": len(self.captured_results),
            "platforms": platforms,
            "success_rate": success_count / len(self.captured_results),
            "recent_captures": len([r for r in self.captured_results 
                                 if time.time() - r.timestamp < 3600])  # 最近1小時
        }
    
    def clear_results(self):
        """清除所有結果"""
        count = len(self.captured_results)
        self.captured_results.clear()
        print(f"🗑️ 已清除 {count} 個捕獲結果")
    
    def export_results(self, format: str = "json") -> Any:
        """導出結果"""
        if format == "json":
            return [
                {
                    "id": captured.id,
                    "command": captured.command,
                    "result": captured.result,
                    "platform": captured.platform,
                    "timestamp": captured.timestamp,
                    "metadata": captured.metadata
                }
                for captured in self.captured_results
            ]
        else:
            raise ValueError(f"不支持的導出格式: {format}")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        return {
            "initialized": self.is_initialized,
            "total_results": len(self.captured_results),
            "callbacks": len(self.callbacks),
            "filters": len(self.filters),
            "max_results": self.max_results,
            "statistics": self.get_statistics()
        }