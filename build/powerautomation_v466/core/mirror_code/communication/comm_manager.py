#!/usr/bin/env python3
"""
Communication Manager - 通信管理器
管理Mirror Code系統的通信和事件處理
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

class EventType(Enum):
    """事件類型"""
    COMMAND_EXECUTED = "command_executed"
    RESULT_CAPTURED = "result_captured"
    SYNC_COMPLETED = "sync_completed"
    CLAUDE_RESPONSE = "claude_response"
    ERROR_OCCURRED = "error_occurred"
    STATUS_UPDATE = "status_update"

@dataclass
class Event:
    """事件"""
    id: str
    type: EventType
    data: Any
    timestamp: float
    source: str

class CommunicationManager:
    """通信管理器"""
    
    def __init__(self):
        self.channels = {}
        self.event_handlers = {}
        self.subscribers = {}
        self.event_history = []
        self.is_initialized = False
        
    async def initialize(self):
        """初始化通信管理器"""
        print("📡 初始化通信管理器...")
        
        # 創建默認通道
        self.create_channel("events", "事件通道")
        self.create_channel("sync", "同步通道")
        self.create_channel("claude", "Claude通道")
        self.create_channel("status", "狀態通道")
        
        self.is_initialized = True
        print("✅ 通信管理器初始化完成")
    
    def create_channel(self, channel_id: str, description: str = ""):
        """創建通信通道"""
        self.channels[channel_id] = {
            "id": channel_id,
            "description": description,
            "created_at": time.time(),
            "message_count": 0,
            "subscribers": set()
        }
        
        print(f"📻 創建通道: {channel_id} - {description}")
    
    def subscribe_to_channel(self, channel_id: str, subscriber_id: str, callback: Callable = None):
        """訂閱通道"""
        if channel_id not in self.channels:
            logger.error(f"通道不存在: {channel_id}")
            return False
        
        self.channels[channel_id]["subscribers"].add(subscriber_id)
        
        if callback:
            if channel_id not in self.subscribers:
                self.subscribers[channel_id] = {}
            self.subscribers[channel_id][subscriber_id] = callback
        
        print(f"📨 {subscriber_id} 訂閱通道: {channel_id}")
        return True
    
    def unsubscribe_from_channel(self, channel_id: str, subscriber_id: str):
        """取消訂閱通道"""
        if channel_id in self.channels:
            self.channels[channel_id]["subscribers"].discard(subscriber_id)
        
        if channel_id in self.subscribers and subscriber_id in self.subscribers[channel_id]:
            del self.subscribers[channel_id][subscriber_id]
        
        print(f"📤 {subscriber_id} 取消訂閱通道: {channel_id}")
    
    def register_event_handler(self, event_type: EventType, handler: Callable):
        """註冊事件處理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        print(f"🎯 註冊事件處理器: {event_type.value}")
    
    async def emit_event(self, event_type: EventType, data: Any, source: str = "unknown"):
        """觸發事件"""
        event = Event(
            id=f"event_{uuid.uuid4().hex[:8]}",
            type=event_type,
            data=data,
            timestamp=time.time(),
            source=source
        )
        
        # 添加到事件歷史
        self.event_history.append(event)
        
        # 保持事件歷史在合理範圍內
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-500:]
        
        print(f"📢 觸發事件: {event_type.value} from {source}")
        
        # 調用事件處理器
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await self._call_handler(handler, event)
                except Exception as e:
                    logger.error(f"事件處理器錯誤: {e}")
        
        # 廣播到相關通道
        await self._broadcast_event_to_channels(event)
    
    async def _call_handler(self, handler: Callable, event: Event):
        """調用事件處理器"""
        if asyncio.iscoroutinefunction(handler):
            await handler(event)
        else:
            handler(event)
    
    async def _broadcast_event_to_channels(self, event: Event):
        """廣播事件到通道"""
        # 根據事件類型選擇通道
        target_channels = []
        
        if event.type == EventType.COMMAND_EXECUTED:
            target_channels = ["events"]
        elif event.type == EventType.RESULT_CAPTURED:
            target_channels = ["events"]
        elif event.type == EventType.SYNC_COMPLETED:
            target_channels = ["sync", "events"]
        elif event.type == EventType.CLAUDE_RESPONSE:
            target_channels = ["claude", "events"]
        elif event.type == EventType.STATUS_UPDATE:
            target_channels = ["status"]
        else:
            target_channels = ["events"]
        
        # 廣播到目標通道
        for channel_id in target_channels:
            await self.broadcast_to_channel(channel_id, {
                "type": "event",
                "event_type": event.type.value,
                "event_id": event.id,
                "data": event.data,
                "timestamp": event.timestamp,
                "source": event.source
            })
    
    async def broadcast_to_channel(self, channel_id: str, message: Dict[str, Any]):
        """廣播消息到通道"""
        if channel_id not in self.channels:
            logger.error(f"通道不存在: {channel_id}")
            return
        
        channel = self.channels[channel_id]
        channel["message_count"] += 1
        
        # 通知訂閱者
        if channel_id in self.subscribers:
            for subscriber_id, callback in self.subscribers[channel_id].items():
                try:
                    await self._call_subscriber_callback(callback, message)
                except Exception as e:
                    logger.error(f"訂閱者回調錯誤: {e}")
        
        print(f"📡 廣播到通道 {channel_id}: {len(channel['subscribers'])} 個訂閱者")
    
    async def _call_subscriber_callback(self, callback: Callable, message: Dict[str, Any]):
        """調用訂閱者回調"""
        if asyncio.iscoroutinefunction(callback):
            await callback(message)
        else:
            callback(message)
    
    async def send_message(self, channel_id: str, message: Dict[str, Any], sender_id: str = "system"):
        """發送消息到通道"""
        message_with_metadata = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "sender_id": sender_id,
            "timestamp": time.time(),
            "content": message
        }
        
        await self.broadcast_to_channel(channel_id, message_with_metadata)
    
    async def process_events(self):
        """處理事件 - 在主循環中調用"""
        # 這個方法可以用來處理任何待處理的事件
        # 目前事件是實時處理的，所以這裡不需要特別的處理
        pass
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """獲取通道信息"""
        if channel_id not in self.channels:
            return None
        
        channel = self.channels[channel_id]
        return {
            "id": channel["id"],
            "description": channel["description"],
            "created_at": channel["created_at"],
            "message_count": channel["message_count"],
            "subscriber_count": len(channel["subscribers"]),
            "subscribers": list(channel["subscribers"])
        }
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """獲取事件統計"""
        if not self.event_history:
            return {
                "total_events": 0,
                "event_types": {},
                "recent_events": 0
            }
        
        event_types = {}
        recent_events = 0
        current_time = time.time()
        
        for event in self.event_history:
            # 統計事件類型
            event_type = event.type.value
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
            
            # 統計最近事件（1小時內）
            if current_time - event.timestamp < 3600:
                recent_events += 1
        
        return {
            "total_events": len(self.event_history),
            "event_types": event_types,
            "recent_events": recent_events,
            "channels": len(self.channels)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        return {
            "initialized": self.is_initialized,
            "channels": len(self.channels),
            "event_handlers": sum(len(handlers) for handlers in self.event_handlers.values()),
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "event_history": len(self.event_history),
            "statistics": self.get_event_statistics()
        }