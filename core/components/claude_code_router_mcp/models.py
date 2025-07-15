"""
Claude Code Router MCP - 模型定義
多AI模型統一接口的數據結構定義
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time


class ModelProvider(Enum):
    """AI模型提供商"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    MOONSHOT = "moonshot"


class SupportedModel(Enum):
    """支持的AI模型"""
    # Anthropic Claude
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    
    # OpenAI GPT
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    
    # Google Gemini
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    
    # Moonshot Kimi
    KIMI_K2_8K = "moonshot-v1-8k"
    KIMI_K2_32K = "moonshot-v1-32k"
    KIMI_K2_128K = "moonshot-v1-128k"


@dataclass
class ModelConfig:
    """AI模型配置"""
    model_id: str
    provider: ModelProvider
    api_base: str
    api_key: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    retry_count: int = 3
    cost_per_1k_tokens: float = 0.0
    rate_limit_per_minute: int = 60
    enabled: bool = True
    priority: int = 1  # 1=highest, 10=lowest
    
    # 模型特性
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = True
    context_window: int = 128000
    
    # 性能指標
    avg_response_time: float = 0.0
    success_rate: float = 100.0
    last_used: float = field(default_factory=time.time)


@dataclass
class RouterRequest:
    """路由請求數據結構"""
    model: str
    messages: List[Dict[str, Any]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """轉換為Anthropic API格式"""
        return {
            "model": self.model,
            "messages": self.messages,
            "max_tokens": self.max_tokens or 4096,
            "temperature": self.temperature or 0.7,
            "top_p": self.top_p or 1.0,
            "stream": self.stream,
            "tools": self.tools,
            "tool_choice": self.tool_choice
        }
    
    def to_openai_format(self) -> Dict[str, Any]:
        """轉換為OpenAI API格式"""
        return {
            "model": self.model,
            "messages": self.messages,
            "max_tokens": self.max_tokens or 4096,
            "temperature": self.temperature or 0.7,
            "top_p": self.top_p or 1.0,
            "frequency_penalty": self.frequency_penalty or 0.0,
            "presence_penalty": self.presence_penalty or 0.0,
            "stream": self.stream,
            "tools": self.tools,
            "tool_choice": self.tool_choice
        }
    
    def to_google_format(self) -> Dict[str, Any]:
        """轉換為Google AI API格式"""
        # 轉換消息格式
        contents = []
        for msg in self.messages:
            if msg["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "system":
                # Google使用instruction代替system message
                contents.insert(0, {"role": "user", "parts": [{"text": f"System: {msg['content']}"}]})
        
        return {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": self.max_tokens or 4096,
                "temperature": self.temperature or 0.7,
                "topP": self.top_p or 1.0,
            }
        }
    
    def to_moonshot_format(self) -> Dict[str, Any]:
        """轉換為Moonshot API格式"""
        return {
            "model": self.model,
            "messages": self.messages,
            "max_tokens": self.max_tokens or 4096,
            "temperature": self.temperature or 0.7,
            "top_p": self.top_p or 1.0,
            "stream": self.stream
        }


@dataclass
class RouterResponse:
    """路由響應數據結構"""
    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]
    created: int
    object: str = "chat.completion"
    
    # 路由相關信息
    provider: ModelProvider = None
    response_time: float = 0.0
    cached: bool = False
    cost: float = 0.0
    
    @classmethod
    def from_anthropic_response(cls, response: Dict[str, Any], model: str, provider: ModelProvider) -> 'RouterResponse':
        """從Anthropic響應創建RouterResponse"""
        return cls(
            id=response.get("id", ""),
            model=model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.get("content", [{}])[0].get("text", "")
                },
                "finish_reason": response.get("stop_reason", "stop")
            }],
            usage={
                "prompt_tokens": response.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": response.get("usage", {}).get("input_tokens", 0) + response.get("usage", {}).get("output_tokens", 0)
            },
            created=int(time.time()),
            provider=provider
        )
    
    @classmethod
    def from_openai_response(cls, response: Dict[str, Any], provider: ModelProvider) -> 'RouterResponse':
        """從OpenAI響應創建RouterResponse"""
        return cls(
            id=response.get("id", ""),
            model=response.get("model", ""),
            choices=response.get("choices", []),
            usage=response.get("usage", {}),
            created=response.get("created", int(time.time())),
            provider=provider
        )
    
    @classmethod
    def from_google_response(cls, response: Dict[str, Any], model: str, provider: ModelProvider) -> 'RouterResponse':
        """從Google AI響應創建RouterResponse"""
        candidates = response.get("candidates", [])
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                content = parts[0].get("text", "")
        
        return cls(
            id=f"google_{int(time.time())}",
            model=model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": response.get("usageMetadata", {}).get("promptTokenCount", 0),
                "completion_tokens": response.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                "total_tokens": response.get("usageMetadata", {}).get("totalTokenCount", 0)
            },
            created=int(time.time()),
            provider=provider
        )
    
    @classmethod
    def from_moonshot_response(cls, response: Dict[str, Any], provider: ModelProvider) -> 'RouterResponse':
        """從Moonshot響應創建RouterResponse"""
        return cls(
            id=response.get("id", ""),
            model=response.get("model", ""),
            choices=response.get("choices", []),
            usage=response.get("usage", {}),
            created=response.get("created", int(time.time())),
            provider=provider
        )


@dataclass
class RouterStats:
    """路由統計信息"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_requests: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0
    
    # 按模型統計
    model_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 按提供商統計
    provider_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def add_request(self, model: str, provider: ModelProvider, success: bool, 
                   response_time: float, cost: float, cached: bool = False):
        """添加請求統計"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        if cached:
            self.cached_requests += 1
        
        self.total_cost += cost
        self.avg_response_time = (self.avg_response_time * (self.total_requests - 1) + response_time) / self.total_requests
        
        # 更新模型統計
        if model not in self.model_stats:
            self.model_stats[model] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "cost": 0.0,
                "avg_response_time": 0.0
            }
        
        model_stat = self.model_stats[model]
        model_stat["requests"] += 1
        if success:
            model_stat["successes"] += 1
        else:
            model_stat["failures"] += 1
        model_stat["cost"] += cost
        model_stat["avg_response_time"] = (model_stat["avg_response_time"] * (model_stat["requests"] - 1) + response_time) / model_stat["requests"]
        
        # 更新提供商統計
        provider_name = provider.value
        if provider_name not in self.provider_stats:
            self.provider_stats[provider_name] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "cost": 0.0,
                "avg_response_time": 0.0
            }
        
        provider_stat = self.provider_stats[provider_name]
        provider_stat["requests"] += 1
        if success:
            provider_stat["successes"] += 1
        else:
            provider_stat["failures"] += 1
        provider_stat["cost"] += cost
        provider_stat["avg_response_time"] = (provider_stat["avg_response_time"] * (provider_stat["requests"] - 1) + response_time) / provider_stat["requests"]
    
    def get_success_rate(self) -> float:
        """獲取成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_cache_hit_rate(self) -> float:
        """獲取緩存命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cached_requests / self.total_requests) * 100