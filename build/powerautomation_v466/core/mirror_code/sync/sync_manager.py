#!/usr/bin/env python3
"""
Sync Manager - 同步管理器
管理Mirror Code系統的同步操作
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

class SyncStrategy(Enum):
    """同步策略"""
    REAL_TIME = "real_time"
    BATCH = "batch"
    ON_DEMAND = "on_demand"

class SyncDirection(Enum):
    """同步方向"""
    LOCAL_TO_REMOTE = "local_to_remote"
    REMOTE_TO_LOCAL = "remote_to_local"
    BIDIRECTIONAL = "bidirectional"

@dataclass
class SyncRule:
    """同步規則"""
    id: str
    pattern: str
    direction: SyncDirection
    strategy: SyncStrategy
    enabled: bool = True

class SyncManager:
    """同步管理器"""
    
    def __init__(self, auto_sync: bool = True, sync_interval: int = 5):
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval
        self.sync_rules = []
        self.sync_queue = asyncio.Queue()
        self.sync_history = []
        self.last_sync_time = None
        self.sync_count = 0
        self.is_running = False
        self.is_initialized = False
        
    async def initialize(self):
        """初始化同步管理器"""
        print("🔄 初始化同步管理器...")
        
        # 添加默認同步規則
        self.add_sync_rule("*", SyncDirection.BIDIRECTIONAL, SyncStrategy.REAL_TIME)
        
        # 啟動同步服務
        if self.auto_sync:
            await self.start_sync_service()
        
        self.is_initialized = True
        print("✅ 同步管理器初始化完成")
    
    def add_sync_rule(self, pattern: str, direction: SyncDirection, strategy: SyncStrategy) -> str:
        """添加同步規則"""
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        rule = SyncRule(
            id=rule_id,
            pattern=pattern,
            direction=direction,
            strategy=strategy
        )
        
        self.sync_rules.append(rule)
        print(f"📋 添加同步規則: {pattern} -> {direction.value} ({strategy.value})")
        
        return rule_id
    
    def remove_sync_rule(self, rule_id: str) -> bool:
        """移除同步規則"""
        for i, rule in enumerate(self.sync_rules):
            if rule.id == rule_id:
                removed_rule = self.sync_rules.pop(i)
                print(f"🗑️ 移除同步規則: {removed_rule.pattern}")
                return True
        return False
    
    async def start_sync_service(self):
        """啟動同步服務"""
        if self.is_running:
            return
        
        self.is_running = True
        asyncio.create_task(self._sync_service_loop())
        print("🔄 同步服務已啟動")
    
    async def stop_sync_service(self):
        """停止同步服務"""
        self.is_running = False
        print("🛑 同步服務已停止")
    
    async def _sync_service_loop(self):
        """同步服務循環"""
        while self.is_running:
            try:
                # 處理同步隊列
                await self._process_sync_queue()
                
                # 檢查自動同步
                if self.auto_sync:
                    await self._check_auto_sync()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"同步服務循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _process_sync_queue(self):
        """處理同步隊列"""
        try:
            while not self.sync_queue.empty():
                sync_task = await asyncio.wait_for(self.sync_queue.get(), timeout=0.1)
                await self._execute_sync_task(sync_task)
        except asyncio.TimeoutError:
            pass  # 隊列為空
    
    async def _check_auto_sync(self):
        """檢查自動同步"""
        if not self.last_sync_time:
            await self.sync_now()
            return
        
        time_since_sync = time.time() - self.last_sync_time
        if time_since_sync >= self.sync_interval:
            await self.sync_now()
    
    async def sync_now(self) -> bool:
        """立即執行同步"""
        try:
            sync_task = {
                "id": f"sync_{uuid.uuid4().hex[:8]}",
                "type": "manual_sync",
                "timestamp": time.time(),
                "data": {}
            }
            
            success = await self._execute_sync_task(sync_task)
            
            if success:
                self.sync_count += 1
                self.last_sync_time = time.time()
                print(f"🔄 同步完成 (第{self.sync_count}次)")
            
            return success
            
        except Exception as e:
            logger.error(f"立即同步失敗: {e}")
            return False
    
    async def sync_result(self, result: Any) -> bool:
        """同步結果"""
        try:
            sync_task = {
                "id": f"result_sync_{uuid.uuid4().hex[:8]}",
                "type": "result_sync",
                "timestamp": time.time(),
                "data": {"result": result}
            }
            
            await self.sync_queue.put(sync_task)
            return True
            
        except Exception as e:
            logger.error(f"結果同步失敗: {e}")
            return False
    
    async def _execute_sync_task(self, sync_task: Dict[str, Any]) -> bool:
        """執行同步任務"""
        try:
            task_id = sync_task["id"]
            task_type = sync_task["type"]
            
            print(f"🔄 執行同步任務: {task_id} ({task_type})")
            
            # 根據任務類型處理
            if task_type == "manual_sync":
                success = await self._execute_manual_sync(sync_task)
            elif task_type == "result_sync":
                success = await self._execute_result_sync(sync_task)
            else:
                logger.warning(f"未知的同步任務類型: {task_type}")
                success = False
            
            # 記錄同步歷史
            self.sync_history.append({
                "task_id": task_id,
                "type": task_type,
                "timestamp": sync_task["timestamp"],
                "success": success
            })
            
            # 保持歷史記錄在合理範圍內
            if len(self.sync_history) > 100:
                self.sync_history = self.sync_history[-50:]
            
            return success
            
        except Exception as e:
            logger.error(f"同步任務執行失敗: {e}")
            return False
    
    async def _execute_manual_sync(self, sync_task: Dict[str, Any]) -> bool:
        """執行手動同步"""
        # 模擬同步過程
        await asyncio.sleep(0.1)
        
        # 應用同步規則
        applied_rules = 0
        for rule in self.sync_rules:
            if rule.enabled:
                applied_rules += 1
        
        print(f"  📋 應用了 {applied_rules} 條同步規則")
        return True
    
    async def _execute_result_sync(self, sync_task: Dict[str, Any]) -> bool:
        """執行結果同步"""
        result = sync_task["data"]["result"]
        
        # 模擬結果同步
        await asyncio.sleep(0.05)
        
        print(f"  📸 同步結果: {str(result)[:50]}...")
        return True
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """獲取同步統計"""
        if not self.sync_history:
            return {
                "total_syncs": 0,
                "success_rate": 0.0,
                "recent_syncs": 0
            }
        
        successful_syncs = sum(1 for sync in self.sync_history if sync["success"])
        recent_syncs = sum(1 for sync in self.sync_history 
                          if time.time() - sync["timestamp"] < 3600)  # 最近1小時
        
        return {
            "total_syncs": len(self.sync_history),
            "successful_syncs": successful_syncs,
            "success_rate": successful_syncs / len(self.sync_history),
            "recent_syncs": recent_syncs,
            "last_sync_time": self.last_sync_time
        }
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        return {
            "initialized": self.is_initialized,
            "running": self.is_running,
            "auto_sync": self.auto_sync,
            "sync_interval": self.sync_interval,
            "sync_count": self.sync_count,
            "last_sync_time": self.last_sync_time,
            "sync_rules": len(self.sync_rules),
            "queue_size": self.sync_queue.qsize(),
            "statistics": self.get_sync_statistics()
        }