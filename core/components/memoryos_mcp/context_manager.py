#!/usr/bin/env python3
"""
MemoryOS MCP - 上下文管理器
管理對話上下文和上下文關聯
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """上下文類型"""
    SESSION = "session"           # 會話上下文
    TASK = "task"                 # 任務上下文
    CONVERSATION = "conversation" # 對話上下文
    PROJECT = "project"           # 項目上下文
    CLAUDE_INTERACTION = "claude_interaction"  # Claude 互動上下文
    USER_WORKFLOW = "user_workflow"            # 用戶工作流上下文

@dataclass
class ContextItem:
    """上下文項目"""
    id: str
    context_type: ContextType
    content: str
    metadata: Dict[str, Any]
    created_at: float
    last_accessed: float
    relevance_score: float
    parent_context_id: Optional[str] = None
    child_context_ids: List[str] = None
    
    def __post_init__(self):
        if self.child_context_ids is None:
            self.child_context_ids = []

@dataclass
class ContextWindow:
    """上下文窗口"""
    id: str
    context_items: List[ContextItem]
    max_size: int
    current_focus: Optional[str] = None
    
    def add_item(self, item: ContextItem):
        """添加上下文項目"""
        self.context_items.append(item)
        if len(self.context_items) > self.max_size:
            # 移除最舊的項目
            self.context_items.pop(0)
    
    def get_relevant_items(self, query: str, limit: int = 5) -> List[ContextItem]:
        """獲取相關上下文項目"""
        relevant_items = []
        for item in self.context_items:
            if query.lower() in item.content.lower():
                relevant_items.append(item)
        
        # 按相關性排序
        relevant_items.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_items[:limit]

class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_context_window: int = 50):
        self.contexts: Dict[str, ContextItem] = {}
        self.context_windows: Dict[str, ContextWindow] = {}
        self.max_context_window = max_context_window
        self.current_session_id: Optional[str] = None
        self.context_relationships: Dict[str, List[str]] = defaultdict(list)
        self.context_transitions: Dict[str, Dict[str, int]] = defaultdict(dict)
        
    async def initialize(self):
        """初始化上下文管理器"""
        logger.info("🔄 初始化 ContextManager...")
        
        # 創建默認會話
        self.current_session_id = await self.create_session_context()
        
        logger.info("✅ ContextManager 初始化完成")
    
    async def create_context(self, 
                           context_type: ContextType,
                           content: str,
                           metadata: Optional[Dict[str, Any]] = None,
                           parent_context_id: Optional[str] = None) -> str:
        """創建新上下文"""
        context_id = f"{context_type.value}_{uuid.uuid4().hex[:8]}"
        
        context_item = ContextItem(
            id=context_id,
            context_type=context_type,
            content=content,
            metadata=metadata or {},
            created_at=time.time(),
            last_accessed=time.time(),
            relevance_score=1.0,
            parent_context_id=parent_context_id
        )
        
        self.contexts[context_id] = context_item
        
        # 建立父子關係
        if parent_context_id and parent_context_id in self.contexts:
            self.contexts[parent_context_id].child_context_ids.append(context_id)
            self.context_relationships[parent_context_id].append(context_id)
        
        # 添加到相應的上下文窗口
        await self._add_to_context_window(context_item)
        
        logger.debug(f"🆕 創建上下文: {context_id} ({context_type.value})")
        return context_id
    
    async def create_session_context(self) -> str:
        """創建會話上下文"""
        session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        context_id = await self.create_context(
            context_type=ContextType.SESSION,
            content=f"User session started at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            metadata={
                "session_id": session_id,
                "start_time": time.time(),
                "user_agent": "ClaudeEditor",
                "session_type": "interactive"
            }
        )
        
        # 創建對應的上下文窗口
        self.context_windows[session_id] = ContextWindow(
            id=session_id,
            context_items=[],
            max_size=self.max_context_window
        )
        
        return context_id
    
    async def create_claude_interaction_context(self,
                                              user_input: str,
                                              claude_response: str,
                                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """創建 Claude 互動上下文"""
        interaction_content = f"""
        User: {user_input}
        Claude: {claude_response}
        """
        
        interaction_metadata = {
            "interaction_type": "claude_code",
            "user_input": user_input,
            "claude_response": claude_response,
            "timestamp": time.time(),
            "response_quality": metadata.get("response_quality", 0.0) if metadata else 0.0,
            "user_satisfaction": metadata.get("user_satisfaction", 0.0) if metadata else 0.0,
            **(metadata or {})
        }
        
        context_id = await self.create_context(
            context_type=ContextType.CLAUDE_INTERACTION,
            content=interaction_content,
            metadata=interaction_metadata,
            parent_context_id=self.current_session_id
        )
        
        # 更新上下文相關性
        await self._update_context_relevance(context_id)
        
        return context_id
    
    async def get_context(self, context_id: str) -> Optional[ContextItem]:
        """獲取上下文"""
        if context_id in self.contexts:
            context = self.contexts[context_id]
            context.last_accessed = time.time()
            await self._update_context_relevance(context_id)
            return context
        return None
    
    async def get_context_history(self, 
                                context_type: Optional[ContextType] = None,
                                limit: int = 10) -> List[ContextItem]:
        """獲取上下文歷史"""
        contexts = list(self.contexts.values())
        
        if context_type:
            contexts = [ctx for ctx in contexts if ctx.context_type == context_type]
        
        # 按時間排序
        contexts.sort(key=lambda x: x.last_accessed, reverse=True)
        
        return contexts[:limit]
    
    async def get_related_contexts(self, 
                                 context_id: str,
                                 max_depth: int = 2) -> List[ContextItem]:
        """獲取相關上下文"""
        if context_id not in self.contexts:
            return []
        
        related_contexts = []
        visited = set()
        
        def _collect_related(ctx_id: str, depth: int):
            if depth > max_depth or ctx_id in visited:
                return
            
            visited.add(ctx_id)
            
            if ctx_id in self.contexts:
                context = self.contexts[ctx_id]
                related_contexts.append(context)
                
                # 獲取父上下文
                if context.parent_context_id:
                    _collect_related(context.parent_context_id, depth + 1)
                
                # 獲取子上下文
                for child_id in context.child_context_ids:
                    _collect_related(child_id, depth + 1)
        
        _collect_related(context_id, 0)
        
        # 按相關性排序
        related_contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return related_contexts
    
    async def get_context_recommendations(self,
                                        query: str,
                                        context_type: Optional[ContextType] = None,
                                        limit: int = 5) -> List[ContextItem]:
        """獲取上下文推薦"""
        candidates = []
        
        for context in self.contexts.values():
            if context_type and context.context_type != context_type:
                continue
            
            # 計算相關性分數
            relevance_score = await self._calculate_context_relevance(context, query)
            
            if relevance_score > 0.1:  # 最低相關性閾值
                candidates.append((context, relevance_score))
        
        # 按相關性排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [ctx for ctx, _ in candidates[:limit]]
    
    async def _calculate_context_relevance(self, 
                                         context: ContextItem,
                                         query: str) -> float:
        """計算上下文相關性"""
        base_score = 0.0
        
        # 內容相似度
        if query.lower() in context.content.lower():
            base_score += 0.5
        
        # 標籤匹配
        query_words = set(query.lower().split())
        content_words = set(context.content.lower().split())
        word_overlap = len(query_words & content_words)
        
        if word_overlap > 0:
            base_score += 0.3 * (word_overlap / len(query_words))
        
        # 時間因子
        current_time = time.time()
        age = current_time - context.created_at
        time_factor = max(0.1, 1.0 / (1.0 + age / 3600))  # 按小時衰減
        
        # 訪問頻率
        access_factor = min(1.0, context.last_accessed / current_time)
        
        # 上下文類型權重
        type_weights = {
            ContextType.CLAUDE_INTERACTION: 1.5,
            ContextType.TASK: 1.3,
            ContextType.PROJECT: 1.2,
            ContextType.CONVERSATION: 1.0,
            ContextType.USER_WORKFLOW: 0.9,
            ContextType.SESSION: 0.7
        }
        
        type_weight = type_weights.get(context.context_type, 1.0)
        
        return base_score * time_factor * access_factor * type_weight
    
    async def _add_to_context_window(self, context_item: ContextItem):
        """添加到上下文窗口"""
        if self.current_session_id:
            # 從會話ID提取窗口ID
            session_context = self.contexts.get(self.current_session_id)
            if session_context:
                session_id = session_context.metadata.get("session_id")
                if session_id and session_id in self.context_windows:
                    self.context_windows[session_id].add_item(context_item)
    
    async def _update_context_relevance(self, context_id: str):
        """更新上下文相關性"""
        if context_id not in self.contexts:
            return
        
        context = self.contexts[context_id]
        current_time = time.time()
        
        # 基於訪問時間更新相關性
        time_since_access = current_time - context.last_accessed
        decay_factor = max(0.1, 1.0 / (1.0 + time_since_access / 3600))
        
        # 基於上下文類型調整
        type_multipliers = {
            ContextType.CLAUDE_INTERACTION: 1.2,
            ContextType.TASK: 1.1,
            ContextType.PROJECT: 1.0,
            ContextType.CONVERSATION: 0.9,
            ContextType.USER_WORKFLOW: 0.8,
            ContextType.SESSION: 0.6
        }
        
        type_multiplier = type_multipliers.get(context.context_type, 1.0)
        
        context.relevance_score = min(2.0, context.relevance_score * decay_factor * type_multiplier)
    
    async def switch_context(self, context_id: str) -> bool:
        """切換上下文"""
        if context_id not in self.contexts:
            return False
        
        context = self.contexts[context_id]
        
        # 記錄上下文轉換
        if self.current_session_id:
            current_session = self.contexts.get(self.current_session_id)
            if current_session:
                prev_context = current_session.metadata.get("current_context")
                if prev_context:
                    # 更新轉換統計
                    if prev_context not in self.context_transitions:
                        self.context_transitions[prev_context] = {}
                    
                    self.context_transitions[prev_context][context_id] = \
                        self.context_transitions[prev_context].get(context_id, 0) + 1
        
        # 更新當前上下文
        if self.current_session_id and self.current_session_id in self.contexts:
            self.contexts[self.current_session_id].metadata["current_context"] = context_id
        
        context.last_accessed = time.time()
        await self._update_context_relevance(context_id)
        
        logger.debug(f"🔄 切換上下文: {context_id}")
        return True
    
    async def merge_contexts(self, 
                           context_ids: List[str],
                           new_context_type: ContextType,
                           merge_strategy: str = "concatenate") -> str:
        """合併上下文"""
        if not context_ids:
            return ""
        
        contexts = [self.contexts[cid] for cid in context_ids if cid in self.contexts]
        if not contexts:
            return ""
        
        # 合併內容
        if merge_strategy == "concatenate":
            merged_content = "\n---\n".join([ctx.content for ctx in contexts])
        elif merge_strategy == "summarize":
            # 簡化的摘要合併
            merged_content = f"Summary of {len(contexts)} contexts:\n"
            for ctx in contexts:
                merged_content += f"- {ctx.content[:100]}...\n"
        else:
            merged_content = contexts[0].content
        
        # 合併元數據
        merged_metadata = {
            "merged_from": context_ids,
            "merge_strategy": merge_strategy,
            "merge_time": time.time(),
            "original_contexts": len(contexts)
        }
        
        # 合併各個上下文的元數據
        for ctx in contexts:
            for key, value in ctx.metadata.items():
                if key not in merged_metadata:
                    merged_metadata[key] = value
        
        # 創建新的合併上下文
        merged_id = await self.create_context(
            context_type=new_context_type,
            content=merged_content,
            metadata=merged_metadata
        )
        
        logger.info(f"🔗 合併上下文: {len(contexts)} -> {merged_id}")
        return merged_id
    
    async def get_context_statistics(self) -> Dict[str, Any]:
        """獲取上下文統計"""
        total_contexts = len(self.contexts)
        
        # 按類型統計
        type_counts = {}
        for context in self.contexts.values():
            type_name = context.context_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # 平均相關性
        avg_relevance = sum(ctx.relevance_score for ctx in self.contexts.values()) / max(1, total_contexts)
        
        # 上下文窗口統計
        window_stats = {}
        for window_id, window in self.context_windows.items():
            window_stats[window_id] = {
                "size": len(window.context_items),
                "max_size": window.max_size,
                "current_focus": window.current_focus
            }
        
        return {
            "total_contexts": total_contexts,
            "type_distribution": type_counts,
            "average_relevance": avg_relevance,
            "context_windows": window_stats,
            "current_session": self.current_session_id,
            "context_relationships": len(self.context_relationships),
            "context_transitions": len(self.context_transitions)
        }
    
    async def cleanup_old_contexts(self, max_age_hours: int = 24):
        """清理舊上下文"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for context_id, context in self.contexts.items():
            if current_time - context.created_at > max_age_seconds:
                if context.context_type != ContextType.SESSION:  # 保留會話上下文
                    to_remove.append(context_id)
        
        for context_id in to_remove:
            del self.contexts[context_id]
            
            # 清理關係
            if context_id in self.context_relationships:
                del self.context_relationships[context_id]
            
            if context_id in self.context_transitions:
                del self.context_transitions[context_id]
        
        logger.info(f"🧹 清理舊上下文: 刪除 {len(to_remove)} 個上下文")
        return len(to_remove)

# 創建全局上下文管理器實例
context_manager = ContextManager()

async def main():
    """測試上下文管理器"""
    print("🧪 測試 ContextManager...")
    
    await context_manager.initialize()
    
    # 測試創建上下文
    task_context = await context_manager.create_context(
        context_type=ContextType.TASK,
        content="用戶要求實現一個 Python 爬蟲",
        metadata={"priority": "high", "estimated_time": 30}
    )
    print(f"✅ 創建任務上下文: {task_context}")
    
    # 測試 Claude 互動上下文
    claude_context = await context_manager.create_claude_interaction_context(
        user_input="如何使用 requests 庫進行網頁抓取？",
        claude_response="可以使用 requests.get() 方法來獲取網頁內容...",
        metadata={"response_quality": 0.9, "user_satisfaction": 0.8}
    )
    print(f"✅ 創建 Claude 互動上下文: {claude_context}")
    
    # 測試上下文推薦
    recommendations = await context_manager.get_context_recommendations(
        query="Python 爬蟲",
        limit=3
    )
    print(f"✅ 上下文推薦: 找到 {len(recommendations)} 個推薦")
    
    # 測試統計
    stats = await context_manager.get_context_statistics()
    print(f"📊 上下文統計: {stats['total_contexts']} 個上下文")
    
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())