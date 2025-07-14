"""
PowerAutomation 4.0 Enhanced Conversation Manager
增强版对话管理器，支持多模型协作、流式响应和智能上下文管理
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
import time
from datetime import datetime, timedelta

from .claude_client import ClaudeClient, ConversationContext, Message
from .message_processor import MessageProcessor, ProcessedMessage
from core.parallel_executor import get_executor
from core.event_bus import EventType, get_event_bus


@dataclass
class EnhancedConversationSession:
    """增强版对话会话"""
    id: str
    context: ConversationContext
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 增强功能
    model_preferences: Dict[str, float] = field(default_factory=dict)  # 模型偏好
    context_summary: str = ""  # 上下文摘要
    code_context: Dict[str, Any] = field(default_factory=dict)  # 代码上下文
    memory_references: List[str] = field(default_factory=list)  # 记忆引用
    performance_metrics: Dict[str, float] = field(default_factory=dict)  # 性能指标


class ModelType(Enum):
    """AI模型类型"""
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    GEMINI_FLASH = "gemini-1.5-flash"
    GPT4 = "gpt-4"


@dataclass
class ModelCapability:
    """模型能力定义"""
    name: str
    strengths: List[str]
    weaknesses: List[str]
    cost_per_token: float
    max_tokens: int
    response_time_avg: float


class EnhancedConversationManager:
    """增强版对话管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.claude_client = ClaudeClient()
        self.message_processor = MessageProcessor()
        self.event_bus = get_event_bus()
        
        # 会话管理
        self.sessions: Dict[str, EnhancedConversationSession] = {}
        self.max_sessions = 100
        self.session_timeout = 3600  # 1小时
        
        # 模型管理
        self.models = self._initialize_models()
        self.model_selector = ModelSelector(self.models)
        
        # 并行处理
        self.active_conversations: Dict[str, asyncio.Task] = {}
        self.max_concurrent_conversations = 10
        
        # 性能监控
        self.performance_tracker = PerformanceTracker()
        
        # 统计信息
        self.stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_messages": 0,
            "model_usage": defaultdict(int),
            "average_response_time": 0.0,
            "error_rate": 0.0
        }
    
    def _initialize_models(self) -> Dict[ModelType, ModelCapability]:
        """初始化模型能力定义"""
        return {
            ModelType.CLAUDE_SONNET: ModelCapability(
                name="Claude 3.5 Sonnet",
                strengths=["代码生成", "复杂推理", "长文本处理"],
                weaknesses=["成本较高", "响应时间较长"],
                cost_per_token=0.003,
                max_tokens=200000,
                response_time_avg=2.5
            ),
            ModelType.CLAUDE_HAIKU: ModelCapability(
                name="Claude 3 Haiku",
                strengths=["快速响应", "成本低", "简单任务"],
                weaknesses=["复杂推理能力有限"],
                cost_per_token=0.00025,
                max_tokens=200000,
                response_time_avg=0.8
            ),
            ModelType.GEMINI_FLASH: ModelCapability(
                name="Gemini 1.5 Flash",
                strengths=["多模态", "快速响应", "免费使用"],
                weaknesses=["API稳定性"],
                cost_per_token=0.0,
                max_tokens=1000000,
                response_time_avg=1.2
            ),
            ModelType.GPT4: ModelCapability(
                name="GPT-4",
                strengths=["通用能力强", "生态完善"],
                weaknesses=["成本高", "上下文限制"],
                cost_per_token=0.03,
                max_tokens=128000,
                response_time_avg=3.0
            )
        }
    
    async def initialize(self):
        """初始化管理器"""
        try:
            await self.claude_client.initialize()
            self.logger.info("增强版对话管理器初始化完成")
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            raise
    
    async def create_session(self, 
                           user_id: str,
                           system_prompt: Optional[str] = None,
                           model_preference: Optional[ModelType] = None) -> str:
        """创建新的对话会话"""
        session_id = str(uuid.uuid4())
        
        context = ConversationContext(
            conversation_id=session_id,
            messages=[],
            system_prompt=system_prompt or "你是一个专业的AI编程助手。",
            model=model_preference.value if model_preference else ModelType.CLAUDE_SONNET.value
        )
        
        session = EnhancedConversationSession(
            id=session_id,
            context=context,
            metadata={"user_id": user_id}
        )
        
        # 设置模型偏好
        if model_preference:
            session.model_preferences[model_preference.value] = 1.0
        
        self.sessions[session_id] = session
        self.stats["total_sessions"] += 1
        self.stats["active_sessions"] += 1
        
        self.logger.info(f"创建新会话: {session_id}")
        return session_id
    
    async def send_message(self, 
                          session_id: str, 
                          message: str,
                          context_data: Optional[Dict[str, Any]] = None) -> str:
        """发送消息并获取回复"""
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        session.last_activity = time.time()
        
        # 处理消息
        processed_msg = await self.message_processor.process_message(message)
        
        # 选择最佳模型
        best_model = await self.model_selector.select_model(
            processed_msg, session, context_data
        )
        
        # 更新上下文
        if context_data:
            session.code_context.update(context_data)
        
        # 记录性能开始时间
        start_time = time.time()
        
        try:
            # 发送到Claude API
            response = await self.claude_client.send_message(
                message=processed_msg.processed,
                conversation_context=session.context
            )
            
            # 记录性能指标
            response_time = time.time() - start_time
            await self.performance_tracker.record_response(
                session_id, best_model, response_time, True
            )
            
            # 更新统计
            self.stats["total_messages"] += 1
            self.stats["model_usage"][best_model.value] += 1
            
            # 更新会话上下文
            session.context.messages.append(Message("user", message))
            session.context.messages.append(Message("assistant", response))
            
            # 更新性能指标
            session.performance_metrics["last_response_time"] = response_time
            session.performance_metrics["total_messages"] = len(session.context.messages)
            
            return response
            
        except Exception as e:
            # 记录错误
            await self.performance_tracker.record_response(
                session_id, best_model, time.time() - start_time, False
            )
            self.logger.error(f"发送消息失败: {e}")
            raise
    
    async def stream_message(self, 
                           session_id: str, 
                           message: str) -> AsyncGenerator[str, None]:
        """流式发送消息"""
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        session.last_activity = time.time()
        
        # 处理消息
        processed_msg = await self.message_processor.process_message(message)
        
        # 选择最佳模型
        best_model = await self.model_selector.select_model(processed_msg, session)
        
        # 流式响应
        response_chunks = []
        async for chunk in self.claude_client.stream_message(
            message=processed_msg.processed,
            conversation_context=session.context
        ):
            response_chunks.append(chunk)
            yield chunk
        
        # 保存完整响应
        full_response = "".join(response_chunks)
        session.context.messages.append(Message("user", message))
        session.context.messages.append(Message("assistant", full_response))
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        return {
            "id": session.id,
            "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
            "last_activity": datetime.fromtimestamp(session.last_activity).isoformat(),
            "message_count": len(session.context.messages),
            "model_preferences": session.model_preferences,
            "performance_metrics": session.performance_metrics,
            "code_context": session.code_context,
            "memory_references": session.memory_references
        }
    
    async def update_code_context(self, 
                                session_id: str, 
                                code_context: Dict[str, Any]):
        """更新代码上下文"""
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        session.code_context.update(code_context)
        session.last_activity = time.time()
    
    async def add_memory_reference(self, 
                                 session_id: str, 
                                 memory_id: str):
        """添加记忆引用"""
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        if memory_id not in session.memory_references:
            session.memory_references.append(memory_id)
    
    async def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            self.stats["active_sessions"] -= 1
            self.logger.info(f"清理过期会话: {session_id}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        await self.cleanup_expired_sessions()
        
        # 计算平均响应时间
        total_response_time = sum(
            session.performance_metrics.get("last_response_time", 0)
            for session in self.sessions.values()
        )
        active_sessions = len(self.sessions)
        avg_response_time = total_response_time / active_sessions if active_sessions > 0 else 0
        
        self.stats["average_response_time"] = avg_response_time
        self.stats["active_sessions"] = active_sessions
        
        return self.stats.copy()


class ModelSelector:
    """模型选择器"""
    
    def __init__(self, models: Dict[ModelType, ModelCapability]):
        self.models = models
        self.logger = logging.getLogger(__name__)
    
    async def select_model(self, 
                         processed_msg: ProcessedMessage,
                         session: EnhancedConversationSession,
                         context_data: Optional[Dict[str, Any]] = None) -> ModelType:
        """选择最佳模型"""
        
        # 分析消息特征
        features = self._analyze_message_features(processed_msg, context_data)
        
        # 计算每个模型的得分
        scores = {}
        for model_type, capability in self.models.items():
            score = self._calculate_model_score(
                model_type, capability, features, session
            )
            scores[model_type] = score
        
        # 选择得分最高的模型
        best_model = max(scores, key=scores.get)
        
        self.logger.debug(f"模型选择结果: {best_model.value}, 得分: {scores}")
        return best_model
    
    def _analyze_message_features(self, 
                                processed_msg: ProcessedMessage,
                                context_data: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """分析消息特征"""
        features = {
            "complexity": 0.0,      # 复杂度
            "code_heavy": 0.0,      # 代码密集度
            "urgency": 0.0,         # 紧急程度
            "cost_sensitivity": 0.0, # 成本敏感度
            "length": len(processed_msg.processed) / 1000.0  # 长度（KB）
        }
        
        # 分析复杂度
        if len(processed_msg.code_blocks) > 0:
            features["code_heavy"] = 1.0
            features["complexity"] = min(len(processed_msg.code_blocks) / 5.0, 1.0)
        
        # 分析命令
        if processed_msg.commands:
            features["urgency"] = 0.8
        
        # 分析关键词
        text_lower = processed_msg.processed.lower()
        if any(word in text_lower for word in ["复杂", "详细", "深入", "分析"]):
            features["complexity"] += 0.3
        
        if any(word in text_lower for word in ["快速", "简单", "快点", "急"]):
            features["urgency"] += 0.5
        
        return features
    
    def _calculate_model_score(self, 
                             model_type: ModelType,
                             capability: ModelCapability,
                             features: Dict[str, float],
                             session: EnhancedConversationSession) -> float:
        """计算模型得分"""
        score = 0.0
        
        # 基础能力得分
        if features["complexity"] > 0.5 and "复杂推理" in capability.strengths:
            score += 0.4
        
        if features["code_heavy"] > 0.5 and "代码生成" in capability.strengths:
            score += 0.3
        
        if features["urgency"] > 0.5 and "快速响应" in capability.strengths:
            score += 0.3
        
        # 成本考虑
        if capability.cost_per_token < 0.001:  # 低成本模型
            score += 0.2
        
        # 用户偏好
        if model_type.value in session.model_preferences:
            score += session.model_preferences[model_type.value] * 0.2
        
        # 历史性能
        if "last_response_time" in session.performance_metrics:
            expected_time = capability.response_time_avg
            actual_time = session.performance_metrics["last_response_time"]
            if actual_time < expected_time:
                score += 0.1
        
        return score


class PerformanceTracker:
    """性能跟踪器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.response_history = deque(maxlen=1000)
    
    async def record_response(self, 
                            session_id: str,
                            model: ModelType,
                            response_time: float,
                            success: bool):
        """记录响应性能"""
        record = {
            "session_id": session_id,
            "model": model.value,
            "response_time": response_time,
            "success": success,
            "timestamp": time.time()
        }
        
        self.response_history.append(record)
        
        if not success:
            self.logger.warning(f"响应失败: {session_id}, 模型: {model.value}")


# 全局实例
_enhanced_conversation_manager = None

def get_enhanced_conversation_manager() -> EnhancedConversationManager:
    """获取增强版对话管理器实例"""
    global _enhanced_conversation_manager
    if _enhanced_conversation_manager is None:
        _enhanced_conversation_manager = EnhancedConversationManager()
    return _enhanced_conversation_manager

