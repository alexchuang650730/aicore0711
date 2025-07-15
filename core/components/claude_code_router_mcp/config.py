"""
Claude Code Router MCP - 配置管理
多AI模型路由系統的配置管理
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from .models import ModelConfig, ModelProvider, SupportedModel


@dataclass
class RouterConfig:
    """路由器配置"""
    # 服務配置
    host: str = "0.0.0.0"
    port: int = 8765
    workers: int = 4
    debug: bool = False
    
    # 緩存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1小時
    cache_max_size: int = 1000
    
    # 日誌配置
    log_level: str = "INFO"
    log_file: str = "router.log"
    
    # 安全配置
    require_auth: bool = True
    auth_token: Optional[str] = None
    rate_limit_per_minute: int = 100
    
    # 負載均衡配置
    load_balancing_strategy: str = "round_robin"  # round_robin, least_connections, weighted
    enable_failover: bool = True
    health_check_interval: int = 60
    
    # 成本優化配置
    cost_optimization: bool = True
    max_cost_per_request: float = 1.0
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.auth_token:
            self.auth_token = os.environ.get("ROUTER_AUTH_TOKEN", "default-token")


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path.home() / ".claude_code_router" / "models.json"
        self.models: Dict[str, ModelConfig] = {}
        self._load_default_configs()
        self._load_config()
    
    def _load_default_configs(self):
        """載入默認配置"""
        # Anthropic Claude配置
        self.models[SupportedModel.CLAUDE_3_OPUS.value] = ModelConfig(
            model_id=SupportedModel.CLAUDE_3_OPUS.value,
            provider=ModelProvider.ANTHROPIC,
            api_base="https://api.anthropic.com",
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.015,
            rate_limit_per_minute=50,
            supports_vision=True,
            supports_function_calling=True,
            context_window=200000,
            priority=1
        )
        
        self.models[SupportedModel.CLAUDE_3_5_SONNET.value] = ModelConfig(
            model_id=SupportedModel.CLAUDE_3_5_SONNET.value,
            provider=ModelProvider.ANTHROPIC,
            api_base="https://api.anthropic.com",
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.003,
            rate_limit_per_minute=50,
            supports_vision=True,
            supports_function_calling=True,
            context_window=200000,
            priority=1
        )
        
        # OpenAI GPT配置
        self.models[SupportedModel.GPT_4O.value] = ModelConfig(
            model_id=SupportedModel.GPT_4O.value,
            provider=ModelProvider.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.005,
            rate_limit_per_minute=60,
            supports_vision=True,
            supports_function_calling=True,
            context_window=128000,
            priority=2
        )
        
        self.models[SupportedModel.GPT_4O_MINI.value] = ModelConfig(
            model_id=SupportedModel.GPT_4O_MINI.value,
            provider=ModelProvider.OPENAI,
            api_base="https://api.openai.com/v1",
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.00015,
            rate_limit_per_minute=60,
            supports_vision=True,
            supports_function_calling=True,
            context_window=128000,
            priority=1
        )
        
        # Google Gemini配置
        self.models[SupportedModel.GEMINI_1_5_PRO.value] = ModelConfig(
            model_id=SupportedModel.GEMINI_1_5_PRO.value,
            provider=ModelProvider.GOOGLE,
            api_base="https://generativelanguage.googleapis.com/v1beta",
            api_key=os.environ.get("GOOGLE_AI_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.0025,
            rate_limit_per_minute=60,
            supports_vision=True,
            supports_function_calling=True,
            context_window=2000000,
            priority=2
        )
        
        self.models[SupportedModel.GEMINI_1_5_FLASH.value] = ModelConfig(
            model_id=SupportedModel.GEMINI_1_5_FLASH.value,
            provider=ModelProvider.GOOGLE,
            api_base="https://generativelanguage.googleapis.com/v1beta",
            api_key=os.environ.get("GOOGLE_AI_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.000075,
            rate_limit_per_minute=60,
            supports_vision=True,
            supports_function_calling=True,
            context_window=1000000,
            priority=1
        )
        
        # Moonshot Kimi配置 - 官方API
        self.models[SupportedModel.KIMI_K2_8K.value] = ModelConfig(
            model_id=SupportedModel.KIMI_K2_8K.value,
            provider=ModelProvider.MOONSHOT,
            api_base="https://api.moonshot.cn/v1",
            api_key=os.environ.get("MOONSHOT_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.0012,
            rate_limit_per_minute=60,
            supports_vision=False,
            supports_function_calling=True,
            context_window=8000,
            priority=1
        )
        
        # Infini-AI Kimi配置 - 第三方代理 (高QPS優化)
        self.models["kimi-k2-instruct-infini"] = ModelConfig(
            model_id="kimi-k2-instruct",
            provider=ModelProvider.MOONSHOT,  # 使用相同的provider類型
            api_base="https://cloud.infini-ai.com/maas/v1",
            api_key=os.environ.get("INFINI_AI_API_KEY", "sk-kqbgz7fvqdutvns7"),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.0005,  # 💰 成本優先：比官方便宜60%
            rate_limit_per_minute=500,  # 🚀 高QPS：500/分鐘
            supports_vision=False,
            supports_function_calling=True,
            context_window=8000,
            priority=1  # 🏆 高QPS優先作為主選
        )
        
        self.models[SupportedModel.KIMI_K2_32K.value] = ModelConfig(
            model_id=SupportedModel.KIMI_K2_32K.value,
            provider=ModelProvider.MOONSHOT,
            api_base="https://api.moonshot.cn/v1",
            api_key=os.environ.get("MOONSHOT_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.0024,
            rate_limit_per_minute=60,
            supports_vision=False,
            supports_function_calling=True,
            context_window=32000,
            priority=2
        )
        
        self.models[SupportedModel.KIMI_K2_128K.value] = ModelConfig(
            model_id=SupportedModel.KIMI_K2_128K.value,
            provider=ModelProvider.MOONSHOT,
            api_base="https://api.moonshot.cn/v1",
            api_key=os.environ.get("MOONSHOT_API_KEY", ""),
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.0096,
            rate_limit_per_minute=60,
            supports_vision=False,
            supports_function_calling=True,
            context_window=128000,
            priority=3
        )
    
    def _load_config(self):
        """從文件載入配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for model_id, config_data in data.items():
                    if model_id in self.models:
                        # 更新現有配置
                        config = self.models[model_id]
                        for key, value in config_data.items():
                            if hasattr(config, key):
                                setattr(config, key, value)
                    else:
                        # 創建新配置
                        config_data['provider'] = ModelProvider(config_data['provider'])
                        self.models[model_id] = ModelConfig(**config_data)
                        
            except Exception as e:
                print(f"載入配置失敗: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for model_id, config in self.models.items():
            config_dict = asdict(config)
            config_dict['provider'] = config.provider.value
            data[model_id] = config_dict
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """獲取模型配置"""
        return self.models.get(model_id)
    
    def get_enabled_models(self) -> List[ModelConfig]:
        """獲取啟用的模型"""
        return [config for config in self.models.values() if config.enabled]
    
    def get_models_by_provider(self, provider: ModelProvider) -> List[ModelConfig]:
        """按提供商獲取模型"""
        return [config for config in self.models.values() if config.provider == provider]
    
    def update_model_config(self, model_id: str, **kwargs):
        """更新模型配置"""
        if model_id in self.models:
            config = self.models[model_id]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            self.save_config()
    
    def add_model_config(self, config: ModelConfig):
        """添加模型配置"""
        self.models[config.model_id] = config
        self.save_config()
    
    def remove_model_config(self, model_id: str):
        """移除模型配置"""
        if model_id in self.models:
            del self.models[model_id]
            self.save_config()
    
    def get_best_model_for_task(self, task_type: str = "general", 
                               max_cost: float = None) -> Optional[ModelConfig]:
        """根據任務類型獲取最佳模型"""
        enabled_models = self.get_enabled_models()
        
        if not enabled_models:
            return None
        
        # 按成本過濾
        if max_cost:
            enabled_models = [m for m in enabled_models if m.cost_per_1k_tokens <= max_cost]
        
        if not enabled_models:
            return None
        
        # 根據任務類型和優先級排序
        if task_type == "vision":
            enabled_models = [m for m in enabled_models if m.supports_vision]
        elif task_type == "function_calling":
            enabled_models = [m for m in enabled_models if m.supports_function_calling]
        elif task_type == "long_context":
            enabled_models = sorted(enabled_models, key=lambda m: m.context_window, reverse=True)
        elif task_type == "cost_efficient":
            enabled_models = sorted(enabled_models, key=lambda m: m.cost_per_1k_tokens)
        
        if not enabled_models:
            return None
        
        # 按優先級和成功率排序
        enabled_models.sort(key=lambda m: (m.priority, -m.success_rate))
        
        return enabled_models[0]
    
    def validate_configs(self) -> Dict[str, List[str]]:
        """驗證配置"""
        errors = {}
        
        for model_id, config in self.models.items():
            model_errors = []
            
            # 檢查API Key
            if not config.api_key:
                model_errors.append("API Key未設置")
            
            # 檢查API Base
            if not config.api_base:
                model_errors.append("API Base未設置")
            
            # 檢查參數範圍
            if not 0 <= config.temperature <= 2:
                model_errors.append("temperature必須在0-2之間")
            
            if not 0 <= config.top_p <= 1:
                model_errors.append("top_p必須在0-1之間")
            
            if config.max_tokens <= 0:
                model_errors.append("max_tokens必須大於0")
            
            if model_errors:
                errors[model_id] = model_errors
        
        return errors
    
    def get_config_summary(self) -> Dict[str, any]:
        """獲取配置摘要"""
        enabled_count = len(self.get_enabled_models())
        total_count = len(self.models)
        
        provider_count = {}
        for config in self.models.values():
            provider = config.provider.value
            provider_count[provider] = provider_count.get(provider, 0) + 1
        
        return {
            "total_models": total_count,
            "enabled_models": enabled_count,
            "disabled_models": total_count - enabled_count,
            "provider_distribution": provider_count,
            "models": {
                model_id: {
                    "provider": config.provider.value,
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "cost_per_1k": config.cost_per_1k_tokens,
                    "context_window": config.context_window
                } for model_id, config in self.models.items()
            }
        }