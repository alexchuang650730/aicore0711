"""
PowerAutomation 4.0 AG-UI智能体交互管理器

管理智能体与用户界面之间的交互，提供标准化的交互接口和会话管理。
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from .ag_ui_protocol_adapter import AGUIMessage, AGUIInteraction, AGUIComponent, AGUIMessageType


class InteractionMode(Enum):
    """交互模式"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    STREAMING = "streaming"
    BATCH = "batch"


class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


@dataclass
class AgentProfile:
    """智能体配置文件"""
    agent_id: str
    name: str
    capabilities: List[str]
    supported_components: List[str]
    interaction_modes: List[str]
    max_concurrent_sessions: int = 10
    session_timeout: int = 3600  # 秒
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionSession:
    """交互会话"""
    session_id: str
    agent_id: str
    user_id: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    interaction_mode: InteractionMode
    context: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, AGUIComponent] = field(default_factory=dict)
    interaction_history: List[AGUIInteraction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionRule:
    """交互规则"""
    rule_id: str
    name: str
    condition: str  # 条件表达式
    action: str     # 动作表达式
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class AGUIInteractionManager:
    """AG-UI智能体交互管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 智能体注册表
        self.agent_registry: Dict[str, AgentProfile] = {}
        
        # 活跃会话
        self.active_sessions: Dict[str, InteractionSession] = {}
        
        # 交互规则
        self.interaction_rules: Dict[str, InteractionRule] = {}
        
        # 消息路由表
        self.message_routes: Dict[str, str] = {}  # agent_id -> endpoint
        
        # 事件监听器
        self.event_listeners: Dict[str, List[Callable]] = {}
        
        # 会话清理任务
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # 统计信息
        self.stats = {
            "total_agents": 0,
            "active_sessions": 0,
            "total_interactions": 0,
            "interactions_by_type": {},
            "session_duration_avg": 0.0,
            "error_count": 0
        }
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动交互管理器"""
        if self.is_running:
            return
        
        self.logger.info("启动AG-UI交互管理器...")
        
        # 启动会话清理任务
        self.cleanup_task = asyncio.create_task(self._session_cleanup_worker())
        
        # 注册默认交互规则
        await self._register_default_rules()
        
        self.is_running = True
        self.logger.info("AG-UI交互管理器启动完成")
    
    async def stop(self):
        """停止交互管理器"""
        if not self.is_running:
            return
        
        self.logger.info("停止AG-UI交互管理器...")
        
        # 停止清理任务
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 终止所有会话
        for session in self.active_sessions.values():
            session.status = SessionStatus.TERMINATED
        
        # 清理资源
        self.agent_registry.clear()
        self.active_sessions.clear()
        self.interaction_rules.clear()
        self.message_routes.clear()
        self.event_listeners.clear()
        
        self.is_running = False
        self.logger.info("AG-UI交互管理器已停止")
    
    async def register_agent(self, agent_profile: AgentProfile) -> bool:
        """注册智能体"""
        try:
            # 验证智能体配置
            if not agent_profile.agent_id or not agent_profile.name:
                raise ValueError("智能体ID和名称不能为空")
            
            # 检查是否已存在
            if agent_profile.agent_id in self.agent_registry:
                self.logger.warning(f"智能体已存在: {agent_profile.agent_id}")
                return False
            
            # 注册智能体
            self.agent_registry[agent_profile.agent_id] = agent_profile
            self.stats["total_agents"] += 1
            
            # 触发注册事件
            await self._emit_event("agent_registered", {
                "agent_id": agent_profile.agent_id,
                "agent_name": agent_profile.name
            })
            
            self.logger.info(f"智能体注册成功: {agent_profile.agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"智能体注册失败: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            if agent_id not in self.agent_registry:
                return False
            
            # 终止该智能体的所有会话
            sessions_to_terminate = [
                session for session in self.active_sessions.values()
                if session.agent_id == agent_id
            ]
            
            for session in sessions_to_terminate:
                await self.terminate_session(session.session_id)
            
            # 移除智能体
            del self.agent_registry[agent_id]
            self.stats["total_agents"] -= 1
            
            # 触发注销事件
            await self._emit_event("agent_unregistered", {
                "agent_id": agent_id
            })
            
            self.logger.info(f"智能体注销成功: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"智能体注销失败: {e}")
            return False
    
    async def create_session(
        self,
        agent_id: str,
        user_id: str,
        interaction_mode: str = "synchronous",
        context: Dict[str, Any] = None
    ) -> Optional[str]:
        """创建交互会话"""
        try:
            # 验证智能体
            if agent_id not in self.agent_registry:
                raise ValueError(f"智能体不存在: {agent_id}")
            
            agent_profile = self.agent_registry[agent_id]
            
            # 检查并发会话限制
            agent_sessions = [
                s for s in self.active_sessions.values()
                if s.agent_id == agent_id and s.status == SessionStatus.ACTIVE
            ]
            
            if len(agent_sessions) >= agent_profile.max_concurrent_sessions:
                raise ValueError(f"智能体并发会话数已达上限: {agent_profile.max_concurrent_sessions}")
            
            # 验证交互模式
            if interaction_mode not in agent_profile.interaction_modes:
                raise ValueError(f"智能体不支持交互模式: {interaction_mode}")
            
            # 创建会话
            session_id = str(uuid.uuid4())
            session = InteractionSession(
                session_id=session_id,
                agent_id=agent_id,
                user_id=user_id,
                status=SessionStatus.ACTIVE,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                interaction_mode=InteractionMode(interaction_mode),
                context=context or {}
            )
            
            self.active_sessions[session_id] = session
            self.stats["active_sessions"] += 1
            
            # 触发会话创建事件
            await self._emit_event("session_created", {
                "session_id": session_id,
                "agent_id": agent_id,
                "user_id": user_id
            })
            
            self.logger.info(f"创建交互会话: {session_id}")
            return session_id
            
        except Exception as e:
            self.logger.error(f"创建会话失败: {e}")
            self.stats["error_count"] += 1
            return None
    
    async def terminate_session(self, session_id: str) -> bool:
        """终止交互会话"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            session.status = SessionStatus.TERMINATED
            
            # 计算会话持续时间
            duration = (datetime.now() - session.created_at).total_seconds()
            
            # 更新平均会话时长
            current_avg = self.stats["session_duration_avg"]
            total_sessions = self.stats["active_sessions"]
            self.stats["session_duration_avg"] = (
                (current_avg * (total_sessions - 1) + duration) / total_sessions
                if total_sessions > 0 else duration
            )
            
            # 移除会话
            del self.active_sessions[session_id]
            self.stats["active_sessions"] -= 1
            
            # 触发会话终止事件
            await self._emit_event("session_terminated", {
                "session_id": session_id,
                "duration": duration
            })
            
            self.logger.info(f"终止交互会话: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"终止会话失败: {e}")
            return False
    
    async def handle_interaction(
        self,
        session_id: str,
        interaction: AGUIInteraction
    ) -> Optional[Dict[str, Any]]:
        """处理交互"""
        try:
            # 验证会话
            if session_id not in self.active_sessions:
                raise ValueError(f"会话不存在: {session_id}")
            
            session = self.active_sessions[session_id]
            
            if session.status != SessionStatus.ACTIVE:
                raise ValueError(f"会话状态无效: {session.status}")
            
            # 更新会话活动时间
            session.last_activity = datetime.now()
            
            # 验证交互
            if not await self._validate_interaction(session, interaction):
                raise ValueError("交互验证失败")
            
            # 应用交互规则
            rule_results = await self._apply_interaction_rules(session, interaction)
            
            # 记录交互历史
            session.interaction_history.append(interaction)
            self.stats["total_interactions"] += 1
            
            # 更新交互类型统计
            action_type = interaction.action_type
            if action_type not in self.stats["interactions_by_type"]:
                self.stats["interactions_by_type"][action_type] = 0
            self.stats["interactions_by_type"][action_type] += 1
            
            # 处理交互
            result = await self._process_interaction(session, interaction)
            
            # 合并规则结果
            if rule_results:
                result = {**(result or {}), "rule_results": rule_results}
            
            # 触发交互事件
            await self._emit_event("interaction_processed", {
                "session_id": session_id,
                "interaction_id": interaction.interaction_id,
                "action_type": interaction.action_type,
                "result": result
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理交互失败: {e}")
            self.stats["error_count"] += 1
            return {"error": str(e)}
    
    async def send_message_to_agent(
        self,
        agent_id: str,
        message: AGUIMessage
    ) -> bool:
        """发送消息到智能体"""
        try:
            # 检查智能体是否注册
            if agent_id not in self.agent_registry:
                raise ValueError(f"智能体不存在: {agent_id}")
            
            # 获取路由信息
            endpoint = self.message_routes.get(agent_id)
            if not endpoint:
                raise ValueError(f"智能体路由未配置: {agent_id}")
            
            # 这里应该实际发送消息到智能体
            # 简化实现，实际应该通过网络或消息队列发送
            self.logger.info(f"发送消息到智能体 {agent_id}: {message.id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            return False
    
    async def register_interaction_rule(self, rule: InteractionRule) -> bool:
        """注册交互规则"""
        try:
            self.interaction_rules[rule.rule_id] = rule
            self.logger.info(f"注册交互规则: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册交互规则失败: {e}")
            return False
    
    async def add_event_listener(
        self,
        event_type: str,
        listener: Callable[[Dict[str, Any]], None]
    ):
        """添加事件监听器"""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        
        self.event_listeners[event_type].append(listener)
        self.logger.info(f"添加事件监听器: {event_type}")
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "agent_id": session.agent_id,
            "user_id": session.user_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "interaction_mode": session.interaction_mode.value,
            "interaction_count": len(session.interaction_history),
            "component_count": len(session.components),
            "context": session.context,
            "metadata": session.metadata
        }
    
    async def get_agent_sessions(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取智能体的所有会话"""
        sessions = [
            session for session in self.active_sessions.values()
            if session.agent_id == agent_id
        ]
        
        return [
            await self.get_session_info(session.session_id)
            for session in sessions
        ]
    
    async def _validate_interaction(
        self,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> bool:
        """验证交互"""
        try:
            # 检查组件是否存在
            if interaction.component_id not in session.components:
                return False
            
            # 检查智能体能力
            agent_profile = self.agent_registry[session.agent_id]
            component = session.components[interaction.component_id]
            
            if component.type not in agent_profile.supported_components:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"交互验证失败: {e}")
            return False
    
    async def _apply_interaction_rules(
        self,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> List[Dict[str, Any]]:
        """应用交互规则"""
        results = []
        
        # 按优先级排序规则
        sorted_rules = sorted(
            self.interaction_rules.values(),
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            try:
                # 评估条件
                if await self._evaluate_rule_condition(rule, session, interaction):
                    # 执行动作
                    result = await self._execute_rule_action(rule, session, interaction)
                    results.append({
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "result": result
                    })
                    
            except Exception as e:
                self.logger.error(f"规则执行失败 {rule.rule_id}: {e}")
        
        return results
    
    async def _evaluate_rule_condition(
        self,
        rule: InteractionRule,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> bool:
        """评估规则条件"""
        # 简化实现，实际应该支持复杂的条件表达式
        condition = rule.condition
        
        # 替换变量
        context = {
            "session": session,
            "interaction": interaction,
            "agent_id": session.agent_id,
            "user_id": session.user_id,
            "action_type": interaction.action_type,
            "component_id": interaction.component_id
        }
        
        try:
            # 这里应该使用安全的表达式评估器
            # 简化实现
            if "action_type" in condition:
                return interaction.action_type in condition
            
            return True
            
        except Exception as e:
            self.logger.error(f"条件评估失败: {e}")
            return False
    
    async def _execute_rule_action(
        self,
        rule: InteractionRule,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> Any:
        """执行规则动作"""
        # 简化实现，实际应该支持复杂的动作表达式
        action = rule.action
        
        if action == "log_interaction":
            self.logger.info(f"规则日志: {rule.name} - {interaction.interaction_id}")
            return "logged"
        elif action == "update_context":
            session.context[f"rule_{rule.rule_id}"] = datetime.now().isoformat()
            return "context_updated"
        
        return "executed"
    
    async def _process_interaction(
        self,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> Dict[str, Any]:
        """处理交互"""
        # 根据交互类型处理
        action_type = interaction.action_type
        
        if action_type == "click":
            return await self._handle_click_interaction(session, interaction)
        elif action_type == "change":
            return await self._handle_change_interaction(session, interaction)
        elif action_type == "submit":
            return await self._handle_submit_interaction(session, interaction)
        else:
            return await self._handle_generic_interaction(session, interaction)
    
    async def _handle_click_interaction(
        self,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> Dict[str, Any]:
        """处理点击交互"""
        return {
            "action": "click",
            "component_id": interaction.component_id,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    
    async def _handle_change_interaction(
        self,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> Dict[str, Any]:
        """处理变更交互"""
        # 更新组件状态
        component = session.components.get(interaction.component_id)
        if component:
            component.properties.update(interaction.parameters)
        
        return {
            "action": "change",
            "component_id": interaction.component_id,
            "new_value": interaction.parameters.get("value"),
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    
    async def _handle_submit_interaction(
        self,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> Dict[str, Any]:
        """处理提交交互"""
        # 收集表单数据
        form_data = {}
        for component in session.components.values():
            if component.type in ["input", "select", "textarea", "checkbox"]:
                form_data[component.id] = component.properties.get("value")
        
        return {
            "action": "submit",
            "component_id": interaction.component_id,
            "form_data": form_data,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    
    async def _handle_generic_interaction(
        self,
        session: InteractionSession,
        interaction: AGUIInteraction
    ) -> Dict[str, Any]:
        """处理通用交互"""
        return {
            "action": interaction.action_type,
            "component_id": interaction.component_id,
            "parameters": interaction.parameters,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        listeners = self.event_listeners.get(event_type, [])
        
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(data)
                else:
                    listener(data)
            except Exception as e:
                self.logger.error(f"事件监听器执行失败: {e}")
    
    async def _session_cleanup_worker(self):
        """会话清理工作器"""
        while self.is_running:
            try:
                current_time = datetime.now()
                sessions_to_cleanup = []
                
                for session in self.active_sessions.values():
                    # 检查会话超时
                    agent_profile = self.agent_registry.get(session.agent_id)
                    if not agent_profile:
                        sessions_to_cleanup.append(session.session_id)
                        continue
                    
                    timeout_delta = timedelta(seconds=agent_profile.session_timeout)
                    if current_time - session.last_activity > timeout_delta:
                        sessions_to_cleanup.append(session.session_id)
                
                # 清理超时会话
                for session_id in sessions_to_cleanup:
                    await self.terminate_session(session_id)
                    self.logger.info(f"清理超时会话: {session_id}")
                
                # 等待下次清理
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                self.logger.error(f"会话清理失败: {e}")
                await asyncio.sleep(60)
    
    async def _register_default_rules(self):
        """注册默认交互规则"""
        default_rules = [
            InteractionRule(
                rule_id="log_all_interactions",
                name="记录所有交互",
                condition="True",
                action="log_interaction",
                priority=0
            ),
            InteractionRule(
                rule_id="update_activity_on_interaction",
                name="交互时更新活动时间",
                condition="True",
                action="update_context",
                priority=1
            )
        ]
        
        for rule in default_rules:
            await self.register_interaction_rule(rule)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "is_running": self.is_running,
            "registered_agents": len(self.agent_registry),
            "active_sessions": len(self.active_sessions),
            "interaction_rules": len(self.interaction_rules),
            "event_listeners": sum(len(listeners) for listeners in self.event_listeners.values()),
            "statistics": self.stats.copy()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "ag_ui_interaction_manager",
            "status": "healthy" if self.is_running else "unhealthy",
            "cleanup_task_running": self.cleanup_task and not self.cleanup_task.done(),
            "statistics": await self.get_statistics()
        }

