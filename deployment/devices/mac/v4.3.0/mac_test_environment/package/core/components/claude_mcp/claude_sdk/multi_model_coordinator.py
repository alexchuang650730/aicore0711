"""
PowerAutomation 4.0 Multi-Model Coordinator
多模型协调器，支持Claude、Gemini、GPT等多个AI模型的协调使用
"""

import asyncio
import logging
import json
import aiohttp
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .claude_client import ClaudeClient, ConversationContext, Message
from core.config import get_config


class ModelProvider(Enum):
    """模型提供商"""
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"
    LOCAL = "local"


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    provider: ModelProvider
    api_key: str
    base_url: str
    max_tokens: int
    temperature: float = 0.7
    cost_per_token: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    rate_limit: int = 60  # 每分钟请求数


@dataclass
class ModelResponse:
    """模型响应"""
    model_name: str
    content: str
    tokens_used: int
    response_time: float
    cost: float
    success: bool
    error_message: Optional[str] = None


class MultiModelCoordinator:
    """多模型协调器"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # 模型配置
        self.models = self._initialize_models()
        
        # 客户端实例
        self.claude_client = ClaudeClient()
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # 性能监控
        self.performance_stats = {}
        self.rate_limiters = {}
        
        # 负载均衡
        self.model_usage_count = {model: 0 for model in self.models.keys()}
        self.model_error_count = {model: 0 for model in self.models.keys()}
    
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """初始化模型配置"""
        models = {}
        
        # Claude模型
        if hasattr(self.config, 'claude_api_key') and self.config.claude_api_key:
            models["claude-3-5-sonnet"] = ModelConfig(
                name="claude-3-5-sonnet-20241022",
                provider=ModelProvider.ANTHROPIC,
                api_key=self.config.claude_api_key,
                base_url="https://api.anthropic.com/v1",
                max_tokens=200000,
                temperature=0.7,
                cost_per_token=0.003,
                capabilities=["code", "analysis", "reasoning", "long_context"],
                rate_limit=50
            )
            
            models["claude-3-haiku"] = ModelConfig(
                name="claude-3-haiku-20240307",
                provider=ModelProvider.ANTHROPIC,
                api_key=self.config.claude_api_key,
                base_url="https://api.anthropic.com/v1",
                max_tokens=200000,
                temperature=0.7,
                cost_per_token=0.00025,
                capabilities=["fast_response", "simple_tasks"],
                rate_limit=100
            )
        
        # Gemini模型
        if hasattr(self.config, 'gemini_api_key') and self.config.gemini_api_key:
            models["gemini-1.5-flash"] = ModelConfig(
                name="gemini-1.5-flash",
                provider=ModelProvider.GOOGLE,
                api_key=self.config.gemini_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta",
                max_tokens=1000000,
                temperature=0.7,
                cost_per_token=0.0,
                capabilities=["multimodal", "fast_response", "free"],
                rate_limit=60
            )
        
        # GPT模型
        if hasattr(self.config, 'openai_api_key') and self.config.openai_api_key:
            models["gpt-4"] = ModelConfig(
                name="gpt-4",
                provider=ModelProvider.OPENAI,
                api_key=self.config.openai_api_key,
                base_url="https://api.openai.com/v1",
                max_tokens=128000,
                temperature=0.7,
                cost_per_token=0.03,
                capabilities=["general", "code", "analysis"],
                rate_limit=40
            )
        
        return models
    
    async def initialize(self):
        """初始化协调器"""
        self.http_session = aiohttp.ClientSession()
        await self.claude_client.initialize()
        
        # 初始化性能统计
        for model_name in self.models.keys():
            self.performance_stats[model_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_response_time": 0.0,
                "average_response_time": 0.0,
                "error_rate": 0.0
            }
        
        self.logger.info(f"多模型协调器初始化完成，支持 {len(self.models)} 个模型")
    
    async def send_message(self, 
                          message: str,
                          model_name: Optional[str] = None,
                          conversation_context: Optional[ConversationContext] = None,
                          **kwargs) -> ModelResponse:
        """发送消息到指定模型"""
        
        # 自动选择模型
        if model_name is None:
            model_name = await self.select_best_model(message, **kwargs)
        
        if model_name not in self.models:
            raise ValueError(f"不支持的模型: {model_name}")
        
        model_config = self.models[model_name]
        start_time = time.time()
        
        try:
            # 检查速率限制
            await self._check_rate_limit(model_name)
            
            # 发送请求
            if model_config.provider == ModelProvider.ANTHROPIC:
                response = await self._send_to_claude(
                    message, model_config, conversation_context
                )
            elif model_config.provider == ModelProvider.GOOGLE:
                response = await self._send_to_gemini(
                    message, model_config, conversation_context
                )
            elif model_config.provider == ModelProvider.OPENAI:
                response = await self._send_to_openai(
                    message, model_config, conversation_context
                )
            else:
                raise ValueError(f"不支持的提供商: {model_config.provider}")
            
            response_time = time.time() - start_time
            
            # 更新统计信息
            await self._update_stats(model_name, response_time, True)
            
            return ModelResponse(
                model_name=model_name,
                content=response,
                tokens_used=len(response.split()),  # 简化的token计算
                response_time=response_time,
                cost=len(response.split()) * model_config.cost_per_token,
                success=True
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            await self._update_stats(model_name, response_time, False)
            
            self.logger.error(f"模型 {model_name} 请求失败: {e}")
            
            return ModelResponse(
                model_name=model_name,
                content="",
                tokens_used=0,
                response_time=response_time,
                cost=0.0,
                success=False,
                error_message=str(e)
            )
    
    async def send_to_multiple_models(self, 
                                    message: str,
                                    model_names: List[str],
                                    conversation_context: Optional[ConversationContext] = None) -> List[ModelResponse]:
        """并行发送消息到多个模型"""
        tasks = []
        
        for model_name in model_names:
            if model_name in self.models:
                task = self.send_message(message, model_name, conversation_context)
                tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        valid_responses = []
        for response in responses:
            if isinstance(response, ModelResponse):
                valid_responses.append(response)
            else:
                self.logger.error(f"模型请求异常: {response}")
        
        return valid_responses
    
    async def select_best_model(self, 
                              message: str,
                              task_type: Optional[str] = None,
                              priority: str = "balanced",
                              **kwargs) -> str:
        """选择最佳模型"""
        
        # 分析消息特征
        message_features = self._analyze_message(message)
        
        # 计算每个模型的得分
        model_scores = {}
        
        for model_name, model_config in self.models.items():
            score = await self._calculate_model_score(
                model_name, model_config, message_features, task_type, priority
            )
            model_scores[model_name] = score
        
        # 选择得分最高的模型
        best_model = max(model_scores, key=model_scores.get)
        
        self.logger.debug(f"选择模型: {best_model}, 得分: {model_scores}")
        return best_model
    
    def _analyze_message(self, message: str) -> Dict[str, Any]:
        """分析消息特征"""
        features = {
            "length": len(message),
            "complexity": 0,
            "has_code": False,
            "language": "unknown",
            "urgency": "normal"
        }
        
        # 检测代码
        if "```" in message or "def " in message or "function " in message:
            features["has_code"] = True
            features["complexity"] += 1
        
        # 检测复杂度
        complex_keywords = ["分析", "详细", "复杂", "深入", "全面"]
        if any(keyword in message for keyword in complex_keywords):
            features["complexity"] += 1
        
        # 检测紧急程度
        urgent_keywords = ["紧急", "快速", "立即", "马上"]
        if any(keyword in message for keyword in urgent_keywords):
            features["urgency"] = "high"
        
        return features
    
    async def _calculate_model_score(self, 
                                   model_name: str,
                                   model_config: ModelConfig,
                                   message_features: Dict[str, Any],
                                   task_type: Optional[str],
                                   priority: str) -> float:
        """计算模型得分"""
        score = 0.0
        
        # 基础能力匹配
        if message_features["has_code"] and "code" in model_config.capabilities:
            score += 0.3
        
        if message_features["complexity"] > 0 and "reasoning" in model_config.capabilities:
            score += 0.2
        
        if message_features["urgency"] == "high" and "fast_response" in model_config.capabilities:
            score += 0.3
        
        # 优先级考虑
        if priority == "cost":
            score += (1.0 - model_config.cost_per_token / 0.03) * 0.3
        elif priority == "speed":
            if "fast_response" in model_config.capabilities:
                score += 0.4
        elif priority == "quality":
            if "reasoning" in model_config.capabilities:
                score += 0.4
        
        # 历史性能
        stats = self.performance_stats.get(model_name, {})
        error_rate = stats.get("error_rate", 0.0)
        score -= error_rate * 0.2
        
        # 负载均衡
        usage_count = self.model_usage_count.get(model_name, 0)
        max_usage = max(self.model_usage_count.values()) if self.model_usage_count.values() else 1
        if max_usage > 0:
            load_factor = usage_count / max_usage
            score -= load_factor * 0.1
        
        return score
    
    async def _send_to_claude(self, 
                            message: str,
                            model_config: ModelConfig,
                            conversation_context: Optional[ConversationContext]) -> str:
        """发送到Claude模型"""
        if conversation_context:
            return await self.claude_client.send_message(message, conversation_context)
        else:
            # 创建临时上下文
            temp_context = ConversationContext(
                conversation_id=str(uuid.uuid4()),
                messages=[],
                model=model_config.name
            )
            return await self.claude_client.send_message(message, temp_context)
    
    async def _send_to_gemini(self, 
                            message: str,
                            model_config: ModelConfig,
                            conversation_context: Optional[ConversationContext]) -> str:
        """发送到Gemini模型"""
        url = f"{model_config.base_url}/models/{model_config.name}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": message}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": model_config.temperature,
                "maxOutputTokens": min(model_config.max_tokens, 8192)
            }
        }
        
        params = {"key": model_config.api_key}
        
        async with self.http_session.post(url, json=data, headers=headers, params=params) as response:
            if response.status == 200:
                result = await response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                error_text = await response.text()
                raise Exception(f"Gemini API错误: {response.status}, {error_text}")
    
    async def _send_to_openai(self, 
                            message: str,
                            model_config: ModelConfig,
                            conversation_context: Optional[ConversationContext]) -> str:
        """发送到OpenAI模型"""
        url = f"{model_config.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model_config.api_key}"
        }
        
        messages = []
        if conversation_context and conversation_context.system_prompt:
            messages.append({"role": "system", "content": conversation_context.system_prompt})
        
        if conversation_context and conversation_context.messages:
            for msg in conversation_context.messages[-10:]:  # 最近10条消息
                messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": model_config.name,
            "messages": messages,
            "temperature": model_config.temperature,
            "max_tokens": min(model_config.max_tokens, 4096)
        }
        
        async with self.http_session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                raise Exception(f"OpenAI API错误: {response.status}, {error_text}")
    
    async def _check_rate_limit(self, model_name: str):
        """检查速率限制"""
        # 简化的速率限制实现
        # 实际应用中应该使用更复杂的令牌桶算法
        pass
    
    async def _update_stats(self, model_name: str, response_time: float, success: bool):
        """更新统计信息"""
        stats = self.performance_stats[model_name]
        
        stats["total_requests"] += 1
        if success:
            stats["successful_requests"] += 1
        
        stats["total_response_time"] += response_time
        stats["average_response_time"] = stats["total_response_time"] / stats["total_requests"]
        stats["error_rate"] = 1.0 - (stats["successful_requests"] / stats["total_requests"])
        
        # 更新使用计数
        self.model_usage_count[model_name] += 1
        if not success:
            self.model_error_count[model_name] += 1
    
    async def get_model_stats(self) -> Dict[str, Any]:
        """获取模型统计信息"""
        return {
            "performance_stats": self.performance_stats,
            "usage_count": self.model_usage_count,
            "error_count": self.model_error_count,
            "available_models": list(self.models.keys())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {}
        
        for model_name in self.models.keys():
            try:
                # 发送简单测试消息
                response = await self.send_message("Hello", model_name)
                health_status[model_name] = {
                    "status": "healthy" if response.success else "unhealthy",
                    "response_time": response.response_time,
                    "error": response.error_message
                }
            except Exception as e:
                health_status[model_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    async def shutdown(self):
        """关闭协调器"""
        if self.http_session:
            await self.http_session.close()
        
        self.logger.info("多模型协调器已关闭")


# 全局实例
_multi_model_coordinator = None

def get_multi_model_coordinator() -> MultiModelCoordinator:
    """获取多模型协调器实例"""
    global _multi_model_coordinator
    if _multi_model_coordinator is None:
        _multi_model_coordinator = MultiModelCoordinator()
    return _multi_model_coordinator

