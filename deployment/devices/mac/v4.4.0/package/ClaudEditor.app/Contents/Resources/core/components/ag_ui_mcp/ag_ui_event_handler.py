"""
PowerAutomation 4.0 AG-UI事件处理器

处理AG-UI组件的各种事件，提供事件路由、处理和响应机制。
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from .ag_ui_protocol_adapter import AGUIMessage, AGUIInteraction, AGUIComponent


class EventType(Enum):
    """事件类型"""
    CLICK = "click"
    CHANGE = "change"
    SUBMIT = "submit"
    FOCUS = "focus"
    BLUR = "blur"
    HOVER = "hover"
    SCROLL = "scroll"
    RESIZE = "resize"
    LOAD = "load"
    UNLOAD = "unload"
    KEYPRESS = "keypress"
    KEYDOWN = "keydown"
    KEYUP = "keyup"
    MOUSEDOWN = "mousedown"
    MOUSEUP = "mouseup"
    MOUSEMOVE = "mousemove"
    CUSTOM = "custom"


class EventPriority(Enum):
    """事件优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class EventContext:
    """事件上下文"""
    event_id: str
    session_id: str
    user_id: str
    agent_id: str
    component_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventHandler:
    """事件处理器"""
    handler_id: str
    name: str
    event_types: List[str]
    handler_func: Callable[[EventContext], Any]
    priority: EventPriority = EventPriority.NORMAL
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventRule:
    """事件规则"""
    rule_id: str
    name: str
    event_pattern: str
    condition: str
    action: str
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventSubscription:
    """事件订阅"""
    subscription_id: str
    subscriber_id: str
    event_types: List[str]
    filters: Dict[str, Any] = field(default_factory=dict)
    callback_url: Optional[str] = None
    callback_func: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AGUIEventHandler:
    """AG-UI事件处理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 事件处理器注册表
        self.event_handlers: Dict[str, EventHandler] = {}
        
        # 事件规则
        self.event_rules: Dict[str, EventRule] = {}
        
        # 事件订阅
        self.event_subscriptions: Dict[str, EventSubscription] = {}
        
        # 事件队列
        self.event_queue = asyncio.Queue()
        
        # 事件历史
        self.event_history: List[EventContext] = []
        self.max_history_size = self.config.get("max_history_size", 1000)
        
        # 事件处理器任务
        self.processor_tasks: List[asyncio.Task] = []
        self.num_processors = self.config.get("num_processors", 4)
        
        # 统计信息
        self.stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_priority": {},
            "processing_errors": 0,
            "avg_processing_time": 0.0,
            "handlers_executed": 0,
            "rules_applied": 0
        }
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动事件处理器"""
        if self.is_running:
            return
        
        self.logger.info("启动AG-UI事件处理器...")
        
        # 启动事件处理器任务
        for i in range(self.num_processors):
            task = asyncio.create_task(self._event_processor(f"processor_{i}"))
            self.processor_tasks.append(task)
        
        # 注册默认事件处理器
        await self._register_default_handlers()
        
        # 注册默认事件规则
        await self._register_default_rules()
        
        self.is_running = True
        self.logger.info(f"AG-UI事件处理器启动完成，{self.num_processors}个处理器运行中")
    
    async def stop(self):
        """停止事件处理器"""
        if not self.is_running:
            return
        
        self.logger.info("停止AG-UI事件处理器...")
        
        # 停止处理器任务
        for task in self.processor_tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self.processor_tasks, return_exceptions=True)
        self.processor_tasks.clear()
        
        # 清理资源
        self.event_handlers.clear()
        self.event_rules.clear()
        self.event_subscriptions.clear()
        self.event_history.clear()
        
        # 清空事件队列
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.is_running = False
        self.logger.info("AG-UI事件处理器已停止")
    
    async def handle_event(
        self,
        event_context: EventContext
    ) -> Dict[str, Any]:
        """处理事件"""
        try:
            # 添加到事件队列
            await self.event_queue.put(event_context)
            
            # 更新统计
            self.stats["total_events"] += 1
            event_type = event_context.event_type
            if event_type not in self.stats["events_by_type"]:
                self.stats["events_by_type"][event_type] = 0
            self.stats["events_by_type"][event_type] += 1
            
            self.logger.debug(f"事件已加入队列: {event_context.event_id}")
            
            return {
                "event_id": event_context.event_id,
                "status": "queued",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.stats["processing_errors"] += 1
            self.logger.error(f"事件处理失败: {e}")
            return {
                "event_id": event_context.event_id,
                "status": "error",
                "error": str(e)
            }
    
    async def register_handler(self, handler: EventHandler) -> bool:
        """注册事件处理器"""
        try:
            self.event_handlers[handler.handler_id] = handler
            self.logger.info(f"注册事件处理器: {handler.handler_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册事件处理器失败: {e}")
            return False
    
    async def unregister_handler(self, handler_id: str) -> bool:
        """注销事件处理器"""
        try:
            if handler_id in self.event_handlers:
                del self.event_handlers[handler_id]
                self.logger.info(f"注销事件处理器: {handler_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"注销事件处理器失败: {e}")
            return False
    
    async def register_rule(self, rule: EventRule) -> bool:
        """注册事件规则"""
        try:
            self.event_rules[rule.rule_id] = rule
            self.logger.info(f"注册事件规则: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册事件规则失败: {e}")
            return False
    
    async def subscribe_events(
        self,
        subscription: EventSubscription
    ) -> bool:
        """订阅事件"""
        try:
            self.event_subscriptions[subscription.subscription_id] = subscription
            self.logger.info(f"订阅事件: {subscription.subscription_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"订阅事件失败: {e}")
            return False
    
    async def unsubscribe_events(self, subscription_id: str) -> bool:
        """取消订阅事件"""
        try:
            if subscription_id in self.event_subscriptions:
                del self.event_subscriptions[subscription_id]
                self.logger.info(f"取消订阅事件: {subscription_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"取消订阅事件失败: {e}")
            return False
    
    async def emit_event(
        self,
        component_id: str,
        event_type: str,
        data: Dict[str, Any],
        session_id: str,
        user_id: str,
        agent_id: str
    ) -> str:
        """发出事件"""
        event_id = str(uuid.uuid4())
        
        event_context = EventContext(
            event_id=event_id,
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
            component_id=component_id,
            event_type=event_type,
            timestamp=datetime.now(),
            data=data
        )
        
        await self.handle_event(event_context)
        return event_id
    
    async def get_event_history(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取事件历史"""
        filtered_events = self.event_history
        
        # 按会话过滤
        if session_id:
            filtered_events = [
                event for event in filtered_events
                if event.session_id == session_id
            ]
        
        # 按事件类型过滤
        if event_type:
            filtered_events = [
                event for event in filtered_events
                if event.event_type == event_type
            ]
        
        # 限制数量
        filtered_events = filtered_events[-limit:]
        
        return [
            {
                "event_id": event.event_id,
                "session_id": event.session_id,
                "user_id": event.user_id,
                "agent_id": event.agent_id,
                "component_id": event.component_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "metadata": event.metadata
            }
            for event in filtered_events
        ]
    
    async def _event_processor(self, processor_name: str):
        """事件处理器协程"""
        self.logger.info(f"事件处理器启动: {processor_name}")
        
        while self.is_running:
            try:
                # 等待事件
                event_context = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                start_time = datetime.now()
                
                # 处理事件
                await self._process_event(event_context)
                
                # 更新处理时间统计
                processing_time = (datetime.now() - start_time).total_seconds()
                current_avg = self.stats["avg_processing_time"]
                total_events = self.stats["total_events"]
                self.stats["avg_processing_time"] = (
                    (current_avg * (total_events - 1) + processing_time) / total_events
                    if total_events > 0 else processing_time
                )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"事件处理器错误 {processor_name}: {e}")
                self.stats["processing_errors"] += 1
    
    async def _process_event(self, event_context: EventContext):
        """处理单个事件"""
        try:
            # 添加到历史记录
            self._add_to_history(event_context)
            
            # 应用事件规则
            await self._apply_event_rules(event_context)
            
            # 执行事件处理器
            await self._execute_event_handlers(event_context)
            
            # 通知订阅者
            await self._notify_subscribers(event_context)
            
            self.logger.debug(f"事件处理完成: {event_context.event_id}")
            
        except Exception as e:
            self.logger.error(f"事件处理失败 {event_context.event_id}: {e}")
            self.stats["processing_errors"] += 1
    
    async def _apply_event_rules(self, event_context: EventContext):
        """应用事件规则"""
        # 按优先级排序规则
        sorted_rules = sorted(
            self.event_rules.values(),
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            try:
                # 检查事件模式匹配
                if await self._match_event_pattern(rule, event_context):
                    # 评估条件
                    if await self._evaluate_rule_condition(rule, event_context):
                        # 执行动作
                        await self._execute_rule_action(rule, event_context)
                        self.stats["rules_applied"] += 1
                        
            except Exception as e:
                self.logger.error(f"规则执行失败 {rule.rule_id}: {e}")
    
    async def _execute_event_handlers(self, event_context: EventContext):
        """执行事件处理器"""
        # 查找匹配的处理器
        matching_handlers = []
        
        for handler in self.event_handlers.values():
            if not handler.enabled:
                continue
            
            # 检查事件类型匹配
            if event_context.event_type in handler.event_types or "*" in handler.event_types:
                # 检查条件
                if await self._check_handler_conditions(handler, event_context):
                    matching_handlers.append(handler)
        
        # 按优先级排序
        matching_handlers.sort(key=lambda h: h.priority.value, reverse=True)
        
        # 执行处理器
        for handler in matching_handlers:
            try:
                if asyncio.iscoroutinefunction(handler.handler_func):
                    await handler.handler_func(event_context)
                else:
                    handler.handler_func(event_context)
                
                self.stats["handlers_executed"] += 1
                self.logger.debug(f"执行事件处理器: {handler.handler_id}")
                
            except Exception as e:
                self.logger.error(f"事件处理器执行失败 {handler.handler_id}: {e}")
    
    async def _notify_subscribers(self, event_context: EventContext):
        """通知订阅者"""
        for subscription in self.event_subscriptions.values():
            try:
                # 检查事件类型匹配
                if event_context.event_type not in subscription.event_types:
                    continue
                
                # 检查过滤条件
                if not await self._check_subscription_filters(subscription, event_context):
                    continue
                
                # 发送通知
                if subscription.callback_func:
                    if asyncio.iscoroutinefunction(subscription.callback_func):
                        await subscription.callback_func(event_context)
                    else:
                        subscription.callback_func(event_context)
                elif subscription.callback_url:
                    # 这里应该发送HTTP回调
                    self.logger.info(f"发送HTTP回调: {subscription.callback_url}")
                
            except Exception as e:
                self.logger.error(f"订阅者通知失败 {subscription.subscription_id}: {e}")
    
    async def _match_event_pattern(
        self,
        rule: EventRule,
        event_context: EventContext
    ) -> bool:
        """匹配事件模式"""
        pattern = rule.event_pattern
        
        # 简化的模式匹配
        if pattern == "*":
            return True
        elif pattern == event_context.event_type:
            return True
        elif ":" in pattern:
            # 组件特定模式，如 "button:click"
            component_type, event_type = pattern.split(":", 1)
            return event_type == event_context.event_type
        
        return False
    
    async def _evaluate_rule_condition(
        self,
        rule: EventRule,
        event_context: EventContext
    ) -> bool:
        """评估规则条件"""
        condition = rule.condition
        
        # 简化的条件评估
        if condition == "true" or condition == "True":
            return True
        elif "component_id" in condition:
            return event_context.component_id in condition
        elif "user_id" in condition:
            return event_context.user_id in condition
        
        return True
    
    async def _execute_rule_action(
        self,
        rule: EventRule,
        event_context: EventContext
    ):
        """执行规则动作"""
        action = rule.action
        
        if action == "log_event":
            self.logger.info(f"规则日志: {rule.name} - {event_context.event_id}")
        elif action == "update_metadata":
            event_context.metadata[f"rule_{rule.rule_id}"] = datetime.now().isoformat()
        elif action.startswith("emit_"):
            # 发出新事件
            new_event_type = action[5:]  # 移除 "emit_" 前缀
            await self.emit_event(
                event_context.component_id,
                new_event_type,
                {"triggered_by": event_context.event_id},
                event_context.session_id,
                event_context.user_id,
                event_context.agent_id
            )
    
    async def _check_handler_conditions(
        self,
        handler: EventHandler,
        event_context: EventContext
    ) -> bool:
        """检查处理器条件"""
        conditions = handler.conditions
        
        if not conditions:
            return True
        
        # 检查组件ID条件
        if "component_ids" in conditions:
            if event_context.component_id not in conditions["component_ids"]:
                return False
        
        # 检查用户ID条件
        if "user_ids" in conditions:
            if event_context.user_id not in conditions["user_ids"]:
                return False
        
        # 检查会话ID条件
        if "session_ids" in conditions:
            if event_context.session_id not in conditions["session_ids"]:
                return False
        
        return True
    
    async def _check_subscription_filters(
        self,
        subscription: EventSubscription,
        event_context: EventContext
    ) -> bool:
        """检查订阅过滤条件"""
        filters = subscription.filters
        
        if not filters:
            return True
        
        # 检查组件ID过滤
        if "component_ids" in filters:
            if event_context.component_id not in filters["component_ids"]:
                return False
        
        # 检查用户ID过滤
        if "user_ids" in filters:
            if event_context.user_id not in filters["user_ids"]:
                return False
        
        return True
    
    def _add_to_history(self, event_context: EventContext):
        """添加到历史记录"""
        self.event_history.append(event_context)
        
        # 限制历史记录大小
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    async def _register_default_handlers(self):
        """注册默认事件处理器"""
        # 点击事件处理器
        click_handler = EventHandler(
            handler_id="default_click_handler",
            name="默认点击处理器",
            event_types=["click"],
            handler_func=self._handle_click_event,
            priority=EventPriority.NORMAL
        )
        await self.register_handler(click_handler)
        
        # 变更事件处理器
        change_handler = EventHandler(
            handler_id="default_change_handler",
            name="默认变更处理器",
            event_types=["change"],
            handler_func=self._handle_change_event,
            priority=EventPriority.NORMAL
        )
        await self.register_handler(change_handler)
        
        # 提交事件处理器
        submit_handler = EventHandler(
            handler_id="default_submit_handler",
            name="默认提交处理器",
            event_types=["submit"],
            handler_func=self._handle_submit_event,
            priority=EventPriority.HIGH
        )
        await self.register_handler(submit_handler)
    
    async def _register_default_rules(self):
        """注册默认事件规则"""
        # 记录所有事件的规则
        log_rule = EventRule(
            rule_id="log_all_events",
            name="记录所有事件",
            event_pattern="*",
            condition="true",
            action="log_event",
            priority=0
        )
        await self.register_rule(log_rule)
        
        # 按钮点击规则
        button_click_rule = EventRule(
            rule_id="button_click_rule",
            name="按钮点击规则",
            event_pattern="click",
            condition="true",
            action="update_metadata",
            priority=1
        )
        await self.register_rule(button_click_rule)
    
    async def _handle_click_event(self, event_context: EventContext):
        """处理点击事件"""
        self.logger.info(f"处理点击事件: {event_context.component_id}")
        
        # 更新事件数据
        event_context.data["processed_by"] = "default_click_handler"
        event_context.data["processed_at"] = datetime.now().isoformat()
    
    async def _handle_change_event(self, event_context: EventContext):
        """处理变更事件"""
        self.logger.info(f"处理变更事件: {event_context.component_id}")
        
        # 更新事件数据
        event_context.data["processed_by"] = "default_change_handler"
        event_context.data["processed_at"] = datetime.now().isoformat()
        
        # 记录变更值
        if "value" in event_context.data:
            self.logger.debug(f"组件值变更: {event_context.data['value']}")
    
    async def _handle_submit_event(self, event_context: EventContext):
        """处理提交事件"""
        self.logger.info(f"处理提交事件: {event_context.component_id}")
        
        # 更新事件数据
        event_context.data["processed_by"] = "default_submit_handler"
        event_context.data["processed_at"] = datetime.now().isoformat()
        
        # 验证表单数据
        if "form_data" in event_context.data:
            form_data = event_context.data["form_data"]
            self.logger.debug(f"表单数据: {json.dumps(form_data, ensure_ascii=False)}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "is_running": self.is_running,
            "event_handlers": len(self.event_handlers),
            "event_rules": len(self.event_rules),
            "event_subscriptions": len(self.event_subscriptions),
            "event_queue_size": self.event_queue.qsize(),
            "event_history_size": len(self.event_history),
            "processor_tasks": len(self.processor_tasks),
            "statistics": self.stats.copy()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "ag_ui_event_handler",
            "status": "healthy" if self.is_running else "unhealthy",
            "processors_running": sum(1 for task in self.processor_tasks if not task.done()),
            "statistics": await self.get_statistics()
        }

