"""
PowerAutomation 4.0 Event Bus
事件总线，支持异步事件发布和订阅
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
import uuid


class EventType(Enum):
    """事件类型枚举"""
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    COMMAND_EXECUTED = "command_executed"
    AGENT_MESSAGE = "agent_message"
    SYSTEM_STATUS = "system_status"


@dataclass
class Event:
    """事件数据类"""
    id: str
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str] = None


class EventBus:
    """事件总线类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history_size = 1000
        
    async def subscribe(self, event_type: EventType, handler: Callable[[Event], Any]):
        """订阅事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        self.logger.info(f"已订阅事件: {event_type.value}")
    
    async def unsubscribe(self, event_type: EventType, handler: Callable[[Event], Any]):
        """取消订阅事件"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
                self.logger.info(f"已取消订阅事件: {event_type.value}")
            except ValueError:
                pass
    
    async def publish(
        self, 
        event_type: EventType, 
        source: str, 
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """发布事件"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            data=data,
            timestamp=time.time(),
            correlation_id=correlation_id
        )
        
        # 添加到历史记录
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        
        # 通知订阅者
        if event_type in self.subscribers:
            tasks = []
            for handler in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(asyncio.create_task(handler(event)))
                    else:
                        # 同步处理器在线程池中执行
                        loop = asyncio.get_event_loop()
                        tasks.append(loop.run_in_executor(None, handler, event))
                except Exception as e:
                    self.logger.error(f"事件处理器错误: {e}")
            
            # 并行执行所有处理器
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.debug(f"已发布事件: {event_type.value} from {source}")
    
    async def get_events(
        self, 
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """获取事件历史"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if source:
            events = [e for e in events if e.source == source]
        
        return events[-limit:]


# 全局事件总线实例
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

