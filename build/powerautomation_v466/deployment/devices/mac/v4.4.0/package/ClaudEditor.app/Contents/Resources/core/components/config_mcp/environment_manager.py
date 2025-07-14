"""
PowerAutomation 4.0 环境管理器

负责管理不同环境的配置和环境变量，支持多环境部署和环境切换。
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class EnvironmentType(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class EnvironmentConfig:
    """环境配置"""
    env_name: str
    env_type: EnvironmentType
    description: str = ""
    variables: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnvironmentManager:
    """
    PowerAutomation 4.0 环境管理器
    
    功能：
    1. 环境变量管理
    2. 多环境配置支持
    3. 环境切换
    4. 环境变量验证
    5. 环境信息查询
    """
    
    def __init__(self):
        """初始化环境管理器"""
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # 环境配置
        self.environments: Dict[str, EnvironmentConfig] = {}
        self.current_environment: Optional[str] = None
        
        # 环境变量缓存
        self.env_cache: Dict[str, str] = {}
        
        # 必需的环境变量
        self.required_env_vars: List[str] = [
            "POWERAUTOMATION_ENV",
            "POWERAUTOMATION_LOG_LEVEL"
        ]
        
        # 敏感环境变量（不会被记录到日志）
        self.sensitive_env_vars: List[str] = [
            "PASSWORD", "SECRET", "TOKEN", "KEY", "API_KEY",
            "DATABASE_PASSWORD", "REDIS_PASSWORD"
        ]
        
        self.logger.info("环境管理器初始化完成")
    
    async def start(self) -> None:
        """启动环境管理器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动环境管理器...")
            
            # 检测当前环境
            await self._detect_current_environment()
            
            # 加载预定义环境
            await self._load_predefined_environments()
            
            # 验证必需的环境变量
            await self._validate_required_env_vars()
            
            # 缓存环境变量
            await self._cache_environment_variables()
            
            self.is_running = True
            self.logger.info(f"环境管理器启动成功，当前环境: {self.current_environment}")
            
        except Exception as e:
            self.logger.error(f"环境管理器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止环境管理器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止环境管理器...")
            
            self.is_running = False
            
            # 清理缓存
            self.env_cache.clear()
            
            self.logger.info("环境管理器已停止")
            
        except Exception as e:
            self.logger.error(f"环境管理器停止时出错: {e}")
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            Optional[str]: 环境变量值
        """
        try:
            # 先从缓存获取
            if key in self.env_cache:
                return self.env_cache[key]
            
            # 从系统环境变量获取
            value = os.getenv(key, default)
            
            # 缓存结果
            if value is not None:
                self.env_cache[key] = value
            
            return value
            
        except Exception as e:
            self.logger.error(f"获取环境变量失败: {e}")
            return default
    
    def set_env(self, key: str, value: str, persist: bool = False) -> bool:
        """
        设置环境变量
        
        Args:
            key: 环境变量名
            value: 环境变量值
            persist: 是否持久化到系统环境
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 设置到系统环境
            if persist:
                os.environ[key] = value
            
            # 更新缓存
            self.env_cache[key] = value
            
            # 记录日志（敏感变量不记录值）
            if any(sensitive in key.upper() for sensitive in self.sensitive_env_vars):
                self.logger.debug(f"设置环境变量: {key} = ***HIDDEN***")
            else:
                self.logger.debug(f"设置环境变量: {key} = {value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置环境变量失败: {e}")
            return False
    
    def get_current_environment(self) -> Optional[str]:
        """获取当前环境名称"""
        return self.current_environment
    
    def get_current_environment_type(self) -> Optional[EnvironmentType]:
        """获取当前环境类型"""
        if self.current_environment and self.current_environment in self.environments:
            return self.environments[self.current_environment].env_type
        return None
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        env_type = self.get_current_environment_type()
        return env_type == EnvironmentType.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        env_type = self.get_current_environment_type()
        return env_type == EnvironmentType.TESTING
    
    def is_staging(self) -> bool:
        """是否为预发布环境"""
        env_type = self.get_current_environment_type()
        return env_type == EnvironmentType.STAGING
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        env_type = self.get_current_environment_type()
        return env_type == EnvironmentType.PRODUCTION
    
    async def switch_environment(self, env_name: str) -> bool:
        """
        切换环境
        
        Args:
            env_name: 环境名称
            
        Returns:
            bool: 切换是否成功
        """
        try:
            if env_name not in self.environments:
                self.logger.error(f"环境不存在: {env_name}")
                return False
            
            env_config = self.environments[env_name]
            if not env_config.enabled:
                self.logger.error(f"环境已禁用: {env_name}")
                return False
            
            # 设置环境变量
            for key, value in env_config.variables.items():
                self.set_env(key, value, persist=True)
            
            # 更新当前环境
            old_env = self.current_environment
            self.current_environment = env_name
            
            # 设置环境标识
            self.set_env("POWERAUTOMATION_ENV", env_name, persist=True)
            
            self.logger.info(f"环境切换: {old_env} -> {env_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"环境切换失败: {e}")
            return False
    
    async def add_environment(self, env_config: EnvironmentConfig) -> bool:
        """
        添加环境配置
        
        Args:
            env_config: 环境配置
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.environments[env_config.env_name] = env_config
            self.logger.info(f"添加环境配置: {env_config.env_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加环境配置失败: {e}")
            return False
    
    async def remove_environment(self, env_name: str) -> bool:
        """
        移除环境配置
        
        Args:
            env_name: 环境名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if env_name not in self.environments:
                self.logger.warning(f"环境不存在: {env_name}")
                return False
            
            # 不能移除当前环境
            if env_name == self.current_environment:
                self.logger.error(f"不能移除当前环境: {env_name}")
                return False
            
            del self.environments[env_name]
            self.logger.info(f"移除环境配置: {env_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除环境配置失败: {e}")
            return False
    
    def get_environment_info(self, env_name: Optional[str] = None) -> Optional[EnvironmentConfig]:
        """
        获取环境信息
        
        Args:
            env_name: 环境名称，为None时返回当前环境信息
            
        Returns:
            Optional[EnvironmentConfig]: 环境配置
        """
        target_env = env_name or self.current_environment
        return self.environments.get(target_env) if target_env else None
    
    def list_environments(self) -> List[EnvironmentConfig]:
        """列出所有环境"""
        return list(self.environments.values())
    
    def get_all_env_vars(self, include_sensitive: bool = False) -> Dict[str, str]:
        """
        获取所有环境变量
        
        Args:
            include_sensitive: 是否包含敏感变量
            
        Returns:
            Dict[str, str]: 环境变量字典
        """
        try:
            env_vars = {}
            
            for key, value in os.environ.items():
                # 检查是否为敏感变量
                if not include_sensitive and any(sensitive in key.upper() for sensitive in self.sensitive_env_vars):
                    env_vars[key] = "***HIDDEN***"
                else:
                    env_vars[key] = value
            
            return env_vars
            
        except Exception as e:
            self.logger.error(f"获取所有环境变量失败: {e}")
            return {}
    
    async def validate_environment(self, env_name: Optional[str] = None) -> bool:
        """
        验证环境配置
        
        Args:
            env_name: 环境名称，为None时验证当前环境
            
        Returns:
            bool: 验证是否通过
        """
        try:
            target_env = env_name or self.current_environment
            if not target_env:
                self.logger.error("没有指定要验证的环境")
                return False
            
            env_config = self.environments.get(target_env)
            if not env_config:
                self.logger.error(f"环境配置不存在: {target_env}")
                return False
            
            # 验证必需的环境变量
            missing_vars = []
            for var in self.required_env_vars:
                if not self.get_env(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.logger.error(f"缺少必需的环境变量: {missing_vars}")
                return False
            
            # 验证环境特定的变量
            for key, expected_value in env_config.variables.items():
                actual_value = self.get_env(key)
                if actual_value != expected_value:
                    self.logger.warning(f"环境变量值不匹配: {key}")
            
            self.logger.info(f"环境验证通过: {target_env}")
            return True
            
        except Exception as e:
            self.logger.error(f"环境验证失败: {e}")
            return False
    
    async def _detect_current_environment(self) -> None:
        """检测当前环境"""
        try:
            # 从环境变量获取
            env_name = self.get_env("POWERAUTOMATION_ENV")
            
            if not env_name:
                # 根据其他环境变量推断
                if self.get_env("KUBERNETES_SERVICE_HOST"):
                    env_name = "production"
                elif self.get_env("CI"):
                    env_name = "testing"
                else:
                    env_name = "development"
                
                # 设置环境变量
                self.set_env("POWERAUTOMATION_ENV", env_name, persist=True)
            
            self.current_environment = env_name
            self.logger.info(f"检测到当前环境: {env_name}")
            
        except Exception as e:
            self.logger.error(f"检测当前环境失败: {e}")
            self.current_environment = "development"
    
    async def _load_predefined_environments(self) -> None:
        """加载预定义环境"""
        try:
            # 开发环境
            dev_env = EnvironmentConfig(
                env_name="development",
                env_type=EnvironmentType.DEVELOPMENT,
                description="开发环境",
                variables={
                    "POWERAUTOMATION_LOG_LEVEL": "DEBUG",
                    "POWERAUTOMATION_DEBUG": "true",
                    "POWERAUTOMATION_CACHE_TTL": "300"
                }
            )
            await self.add_environment(dev_env)
            
            # 测试环境
            test_env = EnvironmentConfig(
                env_name="testing",
                env_type=EnvironmentType.TESTING,
                description="测试环境",
                variables={
                    "POWERAUTOMATION_LOG_LEVEL": "INFO",
                    "POWERAUTOMATION_DEBUG": "false",
                    "POWERAUTOMATION_CACHE_TTL": "600"
                }
            )
            await self.add_environment(test_env)
            
            # 预发布环境
            staging_env = EnvironmentConfig(
                env_name="staging",
                env_type=EnvironmentType.STAGING,
                description="预发布环境",
                variables={
                    "POWERAUTOMATION_LOG_LEVEL": "INFO",
                    "POWERAUTOMATION_DEBUG": "false",
                    "POWERAUTOMATION_CACHE_TTL": "1800"
                }
            )
            await self.add_environment(staging_env)
            
            # 生产环境
            prod_env = EnvironmentConfig(
                env_name="production",
                env_type=EnvironmentType.PRODUCTION,
                description="生产环境",
                variables={
                    "POWERAUTOMATION_LOG_LEVEL": "WARNING",
                    "POWERAUTOMATION_DEBUG": "false",
                    "POWERAUTOMATION_CACHE_TTL": "3600"
                }
            )
            await self.add_environment(prod_env)
            
            self.logger.info("加载预定义环境完成")
            
        except Exception as e:
            self.logger.error(f"加载预定义环境失败: {e}")
    
    async def _validate_required_env_vars(self) -> None:
        """验证必需的环境变量"""
        try:
            missing_vars = []
            
            for var in self.required_env_vars:
                if not self.get_env(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.logger.warning(f"缺少必需的环境变量: {missing_vars}")
                
                # 设置默认值
                for var in missing_vars:
                    if var == "POWERAUTOMATION_ENV":
                        self.set_env(var, "development", persist=True)
                    elif var == "POWERAUTOMATION_LOG_LEVEL":
                        self.set_env(var, "INFO", persist=True)
            
        except Exception as e:
            self.logger.error(f"验证必需环境变量失败: {e}")
    
    async def _cache_environment_variables(self) -> None:
        """缓存环境变量"""
        try:
            # 缓存PowerAutomation相关的环境变量
            for key, value in os.environ.items():
                if key.startswith("POWERAUTOMATION_"):
                    self.env_cache[key] = value
            
            self.logger.debug(f"缓存了 {len(self.env_cache)} 个环境变量")
            
        except Exception as e:
            self.logger.error(f"缓存环境变量失败: {e}")

