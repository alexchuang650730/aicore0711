"""
PowerAutomation 4.0 Configuration Management
配置管理模块，支持动态配置、环境变量和YAML配置文件
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import logging


class PowerAutomationConfig(BaseSettings):
    """PowerAutomation 4.0 配置类"""
    
    # 基础配置
    app_name: str = "PowerAutomation 4.0"
    version: str = "4.0.0"
    debug: bool = Field(default=False, env="PA_DEBUG")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", env="PA_HOST")
    port: int = Field(default=8000, env="PA_PORT")
    workers: int = Field(default=4, env="PA_WORKERS")
    
    # 并行处理配置
    max_concurrent_tasks: int = Field(default=10, env="PA_MAX_CONCURRENT_TASKS")
    task_timeout: int = Field(default=300, env="PA_TASK_TIMEOUT")  # 5分钟
    queue_size: int = Field(default=100, env="PA_QUEUE_SIZE")
    worker_threads: int = Field(default=4, env="PA_WORKER_THREADS")
    
    # Claude SDK配置
    claude_api_key: Optional[str] = Field(default=None, env="CLAUDE_API_KEY")
    claude_model: str = Field(default="claude-3-sonnet-20240229", env="CLAUDE_MODEL")
    claude_max_tokens: int = Field(default=4000, env="CLAUDE_MAX_TOKENS")
    claude_temperature: float = Field(default=0.7, env="CLAUDE_TEMPERATURE")
    
    # OpenAI配置（备用）
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    
    # Redis配置（用于任务队列）
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # 数据库配置
    database_url: str = Field(default="sqlite:///./powerautomation.db", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="PA_LOG_LEVEL")
    log_file: str = Field(default="logs/powerautomation.log", env="PA_LOG_FILE")
    log_max_size: str = Field(default="10MB", env="PA_LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, env="PA_LOG_BACKUP_COUNT")
    
    # MCP协议配置
    mcp_protocol_version: str = "1.0"
    mcp_coordinator_port: int = Field(default=8001, env="MCP_COORDINATOR_PORT")
    mcp_heartbeat_interval: int = Field(default=30, env="MCP_HEARTBEAT_INTERVAL")
    mcp_max_retries: int = Field(default=3, env="MCP_MAX_RETRIES")
    
    # 安全配置
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    max_login_attempts: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    
    # 监控配置
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8002, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # 智能路由配置
    semantic_analysis: bool = Field(default=True, env="SEMANTIC_ANALYSIS")
    confidence_threshold: float = Field(default=0.7, env="CONFIDENCE_THRESHOLD")
    max_routing_attempts: int = Field(default=3, env="MAX_ROUTING_ATTEMPTS")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('confidence_threshold')
    def validate_confidence_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence_threshold must be between 0.0 and 1.0')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ConfigManager:
    """配置管理器，支持多种配置源"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/config.yaml"
        self._config_data = {}
        self._pydantic_config = None
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置"""
        try:
            # 加载YAML配置文件
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or {}
                logging.info(f"已加载配置文件: {self.config_file}")
            else:
                logging.warning(f"配置文件不存在: {self.config_file}")
                self._config_data = {}
            
            # 创建Pydantic配置实例
            self._pydantic_config = PowerAutomationConfig()
            
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            self._config_data = {}
            self._pydantic_config = PowerAutomationConfig()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        try:
            # 首先尝试从Pydantic配置获取
            if hasattr(self._pydantic_config, key):
                return getattr(self._pydantic_config, key)
            
            # 然后从YAML配置获取
            keys = key.split('.')
            value = self._config_data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self._config_data
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置段"""
        return self.get(section, {})
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """保存配置到文件"""
        path = config_path or self.config_file
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            logging.info(f"配置已保存到: {path}")
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self.load_config()
    
    def get_pydantic_config(self) -> PowerAutomationConfig:
        """获取Pydantic配置实例"""
        return self._pydantic_config
    
    def validate_config(self) -> bool:
        """验证配置"""
        try:
            # 验证必需的配置项
            required_keys = [
                'app.name',
                'server.host',
                'server.port'
            ]
            
            for key in required_keys:
                if self.get(key) is None:
                    logging.error(f"缺少必需的配置项: {key}")
                    return False
            
            # 验证端口范围
            port = self.get('server.port')
            if not isinstance(port, int) or not 1 <= port <= 65535:
                logging.error(f"无效的端口号: {port}")
                return False
            
            logging.info("配置验证通过")
            return True
            
        except Exception as e:
            logging.error(f"配置验证失败: {e}")
            return False


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> PowerAutomationConfig:
    """获取全局配置实例"""
    return get_config_manager().get_pydantic_config()


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """从文件加载配置"""
    try:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        elif config_path.endswith('.json'):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logging.warning(f"不支持的配置文件格式: {config_path}")
            return {}
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        return {}


def save_config_to_file(config_data: Dict[str, Any], config_path: str) -> None:
    """保存配置到文件"""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        elif config_path.endswith('.json'):
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        else:
            logging.warning(f"不支持的配置文件格式: {config_path}")
            
    except Exception as e:
        logging.error(f"保存配置文件失败: {e}")


# 向后兼容
config = get_config()

