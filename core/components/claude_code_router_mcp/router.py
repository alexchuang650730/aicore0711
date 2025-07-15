"""
Claude Code Router MCP - 核心路由器
多AI模型智能路由系統的核心實現
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import asdict
import httpx
from datetime import datetime, timedelta
import random

from .models import (
    ModelProvider, RouterRequest, RouterResponse, RouterStats,
    ModelConfig, SupportedModel
)
from .config import RouterConfig, ModelConfigManager
from .utils import RouterUtils
from .cache import RouterCache
from .load_balancer import LoadBalancer


logger = logging.getLogger(__name__)


class ClaudeCodeRouterMCP:
    """Claude Code Router MCP - 多AI模型智能路由系統"""
    
    def __init__(self, config: RouterConfig = None):
        self.config = config or RouterConfig()
        self.model_manager = ModelConfigManager()
        self.cache = RouterCache(
            ttl=self.config.cache_ttl,
            max_size=self.config.cache_max_size
        )
        self.load_balancer = LoadBalancer(self.config.load_balancing_strategy)
        self.stats = RouterStats()
        self.utils = RouterUtils()
        
        # HTTP客戶端
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # 健康檢查
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        
        # 請求限制
        self.request_counts: Dict[str, List[float]] = {}
        
        logger.info("🚀 Claude Code Router MCP 初始化完成")
    
    async def initialize(self):
        """初始化路由器"""
        logger.info("🔧 初始化Claude Code Router MCP...")
        
        # 驗證配置
        config_errors = self.model_manager.validate_configs()
        if config_errors:
            logger.warning(f"配置警告: {config_errors}")
        
        # 啟動健康檢查
        if self.config.enable_failover:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        # 初始化負載均衡器
        enabled_models = self.model_manager.get_enabled_models()
        for model in enabled_models:
            self.load_balancer.add_endpoint(model.model_id, model.priority)
        
        logger.info("✅ Claude Code Router MCP 初始化完成")
    
    async def route_request(self, request: RouterRequest) -> RouterResponse:
        """路由請求到適當的AI模型"""
        start_time = time.time()
        
        try:
            # 檢查緩存
            if self.config.enable_cache and not request.stream:
                cached_response = await self._get_cached_response(request)
                if cached_response:
                    logger.info(f"🎯 緩存命中: {request.model}")
                    cached_response.cached = True
                    return cached_response
            
            # 選擇模型
            model_config = await self._select_model(request)
            if not model_config:
                raise Exception(f"無法找到可用的模型: {request.model}")
            
            # 檢查速率限制
            if not await self._check_rate_limit(model_config.model_id):
                raise Exception(f"速率限制: {model_config.model_id}")
            
            # 發送請求
            response = await self._send_request(request, model_config)
            
            # 計算成本
            cost = self._calculate_cost(response, model_config)
            response.cost = cost
            
            # 緩存響應
            if self.config.enable_cache and not request.stream:
                await self._cache_response(request, response)
            
            # 更新統計
            response_time = time.time() - start_time
            self.stats.add_request(
                model_config.model_id,
                model_config.provider,
                True,
                response_time,
                cost
            )
            
            # 更新模型性能指標
            await self._update_model_metrics(model_config.model_id, response_time, True)
            
            response.response_time = response_time
            
            logger.info(f"✅ 路由成功: {request.model} -> {model_config.model_id} ({response_time:.2f}s, ${cost:.4f})")
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"❌ 路由失敗: {request.model} -> {str(e)}")
            
            # 更新統計
            self.stats.add_request(
                request.model,
                ModelProvider.ANTHROPIC,  # 默認提供商
                False,
                response_time,
                0.0
            )
            
            raise e
    
    async def _select_model(self, request: RouterRequest) -> Optional[ModelConfig]:
        """選擇最佳模型"""
        # 首先檢查是否指定了具體模型
        model_config = self.model_manager.get_model_config(request.model)
        if model_config and model_config.enabled:
            return model_config
        
        # 根據模型名稱映射
        model_mapping = {
            "claude-3-opus": SupportedModel.CLAUDE_3_OPUS.value,
            "claude-3-sonnet": SupportedModel.CLAUDE_3_5_SONNET.value,
            "claude-3-haiku": SupportedModel.CLAUDE_3_HAIKU.value,
            "gpt-4": SupportedModel.GPT_4O.value,
            "gpt-4-turbo": SupportedModel.GPT_4_TURBO.value,
            "gpt-4o": SupportedModel.GPT_4O.value,
            "gpt-4o-mini": SupportedModel.GPT_4O_MINI.value,
            "gemini-pro": SupportedModel.GEMINI_1_5_PRO.value,
            "gemini-flash": SupportedModel.GEMINI_1_5_FLASH.value,
            "kimi-k2": SupportedModel.KIMI_K2_32K.value,
            "moonshot-v1-8k": SupportedModel.KIMI_K2_8K.value,
            "moonshot-v1-32k": SupportedModel.KIMI_K2_32K.value,
            "moonshot-v1-128k": SupportedModel.KIMI_K2_128K.value,
        }
        
        mapped_model = model_mapping.get(request.model)
        if mapped_model:
            model_config = self.model_manager.get_model_config(mapped_model)
            if model_config and model_config.enabled:
                return model_config
        
        # 智能選擇
        task_type = self._detect_task_type(request)
        max_cost = self.config.max_cost_per_request if self.config.cost_optimization else None
        
        return self.model_manager.get_best_model_for_task(task_type, max_cost)
    
    def _detect_task_type(self, request: RouterRequest) -> str:
        """檢測任務類型"""
        # 檢查是否包含圖像
        for message in request.messages:
            if isinstance(message.get("content"), list):
                for content in message["content"]:
                    if content.get("type") == "image":
                        return "vision"
        
        # 檢查是否需要函數調用
        if request.tools:
            return "function_calling"
        
        # 檢查上下文長度
        total_length = sum(len(str(msg.get("content", ""))) for msg in request.messages)
        if total_length > 50000:
            return "long_context"
        
        return "general"
    
    async def _send_request(self, request: RouterRequest, model_config: ModelConfig) -> RouterResponse:
        """發送請求到指定模型"""
        provider = model_config.provider
        
        if provider == ModelProvider.ANTHROPIC:
            return await self._send_anthropic_request(request, model_config)
        elif provider == ModelProvider.OPENAI:
            return await self._send_openai_request(request, model_config)
        elif provider == ModelProvider.GOOGLE:
            return await self._send_google_request(request, model_config)
        elif provider == ModelProvider.MOONSHOT:
            return await self._send_moonshot_request(request, model_config)
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    
    async def _send_anthropic_request(self, request: RouterRequest, model_config: ModelConfig) -> RouterResponse:
        """發送Anthropic請求"""
        url = f"{model_config.api_base}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": model_config.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = request.to_anthropic_format()
        payload["model"] = model_config.model_id
        
        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return RouterResponse.from_anthropic_response(result, model_config.model_id, ModelProvider.ANTHROPIC)
    
    async def _send_openai_request(self, request: RouterRequest, model_config: ModelConfig) -> RouterResponse:
        """發送OpenAI請求"""
        url = f"{model_config.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model_config.api_key}"
        }
        
        payload = request.to_openai_format()
        payload["model"] = model_config.model_id
        
        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return RouterResponse.from_openai_response(result, ModelProvider.OPENAI)
    
    async def _send_google_request(self, request: RouterRequest, model_config: ModelConfig) -> RouterResponse:
        """發送Google請求"""
        url = f"{model_config.api_base}/models/{model_config.model_id}:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {"key": model_config.api_key}
        payload = request.to_google_format()
        
        response = await self.http_client.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        
        result = response.json()
        return RouterResponse.from_google_response(result, model_config.model_id, ModelProvider.GOOGLE)
    
    async def _send_moonshot_request(self, request: RouterRequest, model_config: ModelConfig) -> RouterResponse:
        """發送Moonshot請求"""
        url = f"{model_config.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {model_config.api_key}"
        }
        
        payload = request.to_moonshot_format()
        payload["model"] = model_config.model_id
        
        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return RouterResponse.from_moonshot_response(result, ModelProvider.MOONSHOT)
    
    async def _get_cached_response(self, request: RouterRequest) -> Optional[RouterResponse]:
        """獲取緩存的響應"""
        cache_key = self._generate_cache_key(request)
        cached_data = await self.cache.get(cache_key)
        
        if cached_data:
            return RouterResponse(**cached_data)
        
        return None
    
    async def _cache_response(self, request: RouterRequest, response: RouterResponse):
        """緩存響應"""
        cache_key = self._generate_cache_key(request)
        await self.cache.set(cache_key, asdict(response))
    
    def _generate_cache_key(self, request: RouterRequest) -> str:
        """生成緩存鍵"""
        # 創建請求的唯一標識
        request_data = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p
        }
        
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _calculate_cost(self, response: RouterResponse, model_config: ModelConfig) -> float:
        """計算請求成本"""
        usage = response.usage
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        # 通常輸出token成本更高
        input_cost = (prompt_tokens / 1000) * model_config.cost_per_1k_tokens
        output_cost = (completion_tokens / 1000) * model_config.cost_per_1k_tokens * 3  # 輸出token通常3倍成本
        
        return input_cost + output_cost
    
    async def _check_rate_limit(self, model_id: str) -> bool:
        """檢查速率限制"""
        now = time.time()
        
        if model_id not in self.request_counts:
            self.request_counts[model_id] = []
        
        # 清理舊的記錄
        self.request_counts[model_id] = [
            timestamp for timestamp in self.request_counts[model_id]
            if now - timestamp < 60  # 保留最近1分鐘的記錄
        ]
        
        model_config = self.model_manager.get_model_config(model_id)
        if not model_config:
            return False
        
        # 檢查是否超過限制
        if len(self.request_counts[model_id]) >= model_config.rate_limit_per_minute:
            return False
        
        # 添加當前請求
        self.request_counts[model_id].append(now)
        return True
    
    async def _update_model_metrics(self, model_id: str, response_time: float, success: bool):
        """更新模型性能指標"""
        model_config = self.model_manager.get_model_config(model_id)
        if not model_config:
            return
        
        # 更新平均響應時間
        if model_config.avg_response_time == 0:
            model_config.avg_response_time = response_time
        else:
            model_config.avg_response_time = (model_config.avg_response_time * 0.9 + response_time * 0.1)
        
        # 更新成功率
        if success:
            model_config.success_rate = min(100.0, model_config.success_rate * 0.99 + 1.0)
        else:
            model_config.success_rate = max(0.0, model_config.success_rate * 0.99)
        
        model_config.last_used = time.time()
        
        # 保存更新的配置
        self.model_manager.save_config()
    
    async def _health_check_loop(self):
        """健康檢查循環"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"健康檢查失敗: {e}")
                await asyncio.sleep(30)  # 失敗時短暫等待
    
    async def _perform_health_checks(self):
        """執行健康檢查"""
        enabled_models = self.model_manager.get_enabled_models()
        
        for model_config in enabled_models:
            try:
                # 創建簡單的健康檢查請求
                health_request = RouterRequest(
                    model=model_config.model_id,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5
                )
                
                start_time = time.time()
                await self._send_request(health_request, model_config)
                response_time = time.time() - start_time
                
                self.health_status[model_config.model_id] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.health_status[model_config.model_id] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
                
                # 暫時禁用不健康的模型
                model_config.enabled = False
                logger.warning(f"模型 {model_config.model_id} 健康檢查失敗，已暫時禁用")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """獲取可用模型列表"""
        enabled_models = self.model_manager.get_enabled_models()
        
        return [
            {
                "model_id": model.model_id,
                "provider": model.provider.value,
                "supports_vision": model.supports_vision,
                "supports_function_calling": model.supports_function_calling,
                "context_window": model.context_window,
                "cost_per_1k_tokens": model.cost_per_1k_tokens,
                "priority": model.priority,
                "success_rate": model.success_rate,
                "avg_response_time": model.avg_response_time,
                "health_status": self.health_status.get(model.model_id, {"status": "unknown"})
            }
            for model in enabled_models
        ]
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "cached_requests": self.stats.cached_requests,
            "success_rate": self.stats.get_success_rate(),
            "cache_hit_rate": self.stats.get_cache_hit_rate(),
            "total_cost": self.stats.total_cost,
            "avg_response_time": self.stats.avg_response_time,
            "model_stats": self.stats.model_stats,
            "provider_stats": self.stats.provider_stats
        }
    
    async def switch_model(self, from_model: str, to_model: str) -> bool:
        """切換模型"""
        to_config = self.model_manager.get_model_config(to_model)
        if not to_config:
            logger.error(f"目標模型不存在: {to_model}")
            return False
        
        if not to_config.enabled:
            logger.error(f"目標模型未啟用: {to_model}")
            return False
        
        # 這裡可以添加更多的切換邏輯
        logger.info(f"模型切換: {from_model} -> {to_model}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """獲取組件狀態"""
        config_summary = self.model_manager.get_config_summary()
        
        return {
            "component": "Claude Code Router MCP",
            "version": "4.6.9.4",
            "status": "running",
            "uptime": time.time() - (getattr(self, '_start_time', time.time())),
            "configuration": {
                "total_models": config_summary["total_models"],
                "enabled_models": config_summary["enabled_models"],
                "cache_enabled": self.config.enable_cache,
                "load_balancing": self.config.load_balancing_strategy,
                "health_check_enabled": self.config.enable_failover
            },
            "statistics": {
                "total_requests": self.stats.total_requests,
                "success_rate": self.stats.get_success_rate(),
                "cache_hit_rate": self.stats.get_cache_hit_rate(),
                "total_cost": self.stats.total_cost
            },
            "health_status": self.health_status,
            "capabilities": [
                "multi_model_routing",
                "intelligent_load_balancing",
                "request_caching",
                "cost_optimization",
                "health_monitoring",
                "rate_limiting",
                "failover_support"
            ],
            "supported_providers": [
                "anthropic (Claude)",
                "openai (GPT)",
                "google (Gemini)",
                "moonshot (Kimi K2)"
            ]
        }
    
    async def cleanup(self):
        """清理資源"""
        if self.health_check_task:
            self.health_check_task.cancel()
        
        await self.http_client.aclose()
        await self.cache.close()
        
        logger.info("🧹 Claude Code Router MCP 清理完成")


# 單例實例
claude_code_router_mcp = ClaudeCodeRouterMCP()