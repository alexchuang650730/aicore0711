"""
PowerAutomation 4.0 配置管理器

提供统一的配置管理功能，支持多种配置源、动态更新、配置验证等功能。
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .environment_manager import EnvironmentManager
from .secret_manager import SecretManager
from .config_validator import ConfigValidator


@dataclass
class ConfigSource:
    """配置源"""
    source_id: str
    source_type: str  # file, env, remote, database
    location: str
    priority: int = 100
    enabled: bool = True
    watch_changes: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigChange:
    """配置变更"""
    key: str
    old_value: Any
    new_value: Any
    source: str
    timestamp: datetime = field(default_factory=datetime.now)


class ConfigFileWatcher(FileSystemEventHandler):
    """配置文件监控器"""
    
    def __init__(self, config_manager, file_path: str):
        self.config_manager = config_manager
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.file_path:
            self.logger.info(f"配置文件变更: {self.file_path}")
            asyncio.create_task(self.config_manager._reload_file_config(self.file_path))


class ConfigManager:
    """
    PowerAutomation 4.0 配置管理器
    
    功能：
    1. 多配置源支持 (文件、环境变量、远程配置)
    2. 配置热重载
    3. 配置验证
    4. 配置变更通知
    5. 密钥管理集成
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录路径
        """
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path(config_dir or "config")
        self.is_running = False
        
        # 配置数据
        self.config_data: Dict[str, Any] = {}
        self.config_sources: Dict[str, ConfigSource] = {}
        
        # 组件
        self.env_manager = EnvironmentManager()
        self.secret_manager = SecretManager()
        self.validator = ConfigValidator()
        
        # 变更监听
        self.change_listeners: List[Callable[[ConfigChange], None]] = []
        self.file_watchers: Dict[str, Observer] = {}
        
        # 配置缓存
        self.config_cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        
        # 线程锁
        self.config_lock = threading.RLock()
        
        self.logger.info("配置管理器初始化完成")
    
    async def start(self) -> None:
        """启动配置管理器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动配置管理器...")
            
            # 启动子组件
            await self.env_manager.start()
            await self.secret_manager.start()
            await self.validator.start()
            
            # 加载默认配置源
            await self._load_default_sources()
            
            # 加载所有配置
            await self._load_all_configs()
            
            # 验证配置
            await self._validate_configs()
            
            self.is_running = True
            self.logger.info("配置管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"配置管理器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止配置管理器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止配置管理器...")
            
            self.is_running = False
            
            # 停止文件监控
            for observer in self.file_watchers.values():
                observer.stop()
                observer.join()
            self.file_watchers.clear()
            
            # 停止子组件
            await self.validator.stop()
            await self.secret_manager.stop()
            await self.env_manager.stop()
            
            self.logger.info("配置管理器已停止")
            
        except Exception as e:
            self.logger.error(f"配置管理器停止时出错: {e}")
    
    async def add_config_source(self, source: ConfigSource) -> bool:
        """
        添加配置源
        
        Args:
            source: 配置源
            
        Returns:
            bool: 添加是否成功
        """
        try:
            with self.config_lock:
                self.config_sources[source.source_id] = source
            
            # 加载配置源数据
            await self._load_source_config(source)
            
            # 启动文件监控
            if source.watch_changes and source.source_type == "file":
                await self._start_file_watching(source)
            
            self.logger.info(f"添加配置源: {source.source_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加配置源失败: {e}")
            return False
    
    async def remove_config_source(self, source_id: str) -> bool:
        """
        移除配置源
        
        Args:
            source_id: 配置源ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            with self.config_lock:
                if source_id not in self.config_sources:
                    self.logger.warning(f"配置源不存在: {source_id}")
                    return False
                
                source = self.config_sources[source_id]
                del self.config_sources[source_id]
            
            # 停止文件监控
            if source_id in self.file_watchers:
                self.file_watchers[source_id].stop()
                del self.file_watchers[source_id]
            
            # 重新加载配置
            await self._load_all_configs()
            
            self.logger.info(f"移除配置源: {source_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除配置源失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            with self.config_lock:
                # 检查缓存
                if key in self.config_cache:
                    cache_time = self.cache_ttl.get(key)
                    if cache_time and (datetime.now() - cache_time).total_seconds() < 300:  # 5分钟缓存
                        return self.config_cache[key]
                
                # 从配置数据中获取
                value = self._get_nested_value(self.config_data, key)
                
                # 处理密钥引用
                if isinstance(value, str) and value.startswith("${secret:"):
                    secret_key = value[9:-1]  # 移除 ${secret: 和 }
                    value = self.secret_manager.get_secret(secret_key)
                
                # 处理环境变量引用
                elif isinstance(value, str) and value.startswith("${env:"):
                    env_key = value[6:-1]  # 移除 ${env: 和 }
                    value = self.env_manager.get_env(env_key, default)
                
                # 缓存结果
                self.config_cache[key] = value
                self.cache_ttl[key] = datetime.now()
                
                return value if value is not None else default
                
        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            return default
    
    def set(self, key: str, value: Any, source: str = "runtime") -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            source: 配置源
            
        Returns:
            bool: 设置是否成功
        """
        try:
            with self.config_lock:
                old_value = self.get(key)
                
                # 设置新值
                self._set_nested_value(self.config_data, key, value)
                
                # 清除缓存
                if key in self.config_cache:
                    del self.config_cache[key]
                    del self.cache_ttl[key]
                
                # 触发变更事件
                change = ConfigChange(
                    key=key,
                    old_value=old_value,
                    new_value=value,
                    source=source
                )
                
                self._notify_change_listeners(change)
                
                self.logger.debug(f"设置配置: {key} = {value}")
                return True
                
        except Exception as e:
            self.logger.error(f"设置配置失败: {e}")
            return False
    
    def get_all(self, prefix: str = "") -> Dict[str, Any]:
        """
        获取所有配置或指定前缀的配置
        
        Args:
            prefix: 配置前缀
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        try:
            with self.config_lock:
                if not prefix:
                    return self.config_data.copy()
                
                # 获取指定前缀的配置
                result = {}
                for key, value in self._flatten_dict(self.config_data).items():
                    if key.startswith(prefix):
                        result[key] = value
                
                return result
                
        except Exception as e:
            self.logger.error(f"获取所有配置失败: {e}")
            return {}
    
    def add_change_listener(self, listener: Callable[[ConfigChange], None]) -> None:
        """
        添加配置变更监听器
        
        Args:
            listener: 监听器函数
        """
        self.change_listeners.append(listener)
        self.logger.info("添加配置变更监听器")
    
    def remove_change_listener(self, listener: Callable[[ConfigChange], None]) -> None:
        """
        移除配置变更监听器
        
        Args:
            listener: 监听器函数
        """
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
            self.logger.info("移除配置变更监听器")
    
    async def reload_config(self, source_id: Optional[str] = None) -> bool:
        """
        重新加载配置
        
        Args:
            source_id: 配置源ID，为None时重新加载所有配置
            
        Returns:
            bool: 重新加载是否成功
        """
        try:
            if source_id:
                if source_id in self.config_sources:
                    source = self.config_sources[source_id]
                    await self._load_source_config(source)
                    self.logger.info(f"重新加载配置源: {source_id}")
                else:
                    self.logger.error(f"配置源不存在: {source_id}")
                    return False
            else:
                await self._load_all_configs()
                self.logger.info("重新加载所有配置")
            
            # 清除缓存
            self.config_cache.clear()
            self.cache_ttl.clear()
            
            return True
            
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    async def validate_config(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        验证配置
        
        Args:
            config_data: 要验证的配置数据，为None时验证当前配置
            
        Returns:
            bool: 验证是否通过
        """
        try:
            data_to_validate = config_data or self.config_data
            return await self.validator.validate(data_to_validate)
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return False
    
    async def export_config(self, file_path: str, format: str = "yaml") -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 文件路径
            format: 文件格式 (yaml, json)
            
        Returns:
            bool: 导出是否成功
        """
        try:
            with self.config_lock:
                config_copy = self.config_data.copy()
            
            # 移除敏感信息
            config_copy = self._sanitize_config(config_copy)
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_copy, f, indent=2, ensure_ascii=False)
            else:  # yaml
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_copy, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"导出配置到: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            return False
    
    async def _load_default_sources(self) -> None:
        """加载默认配置源"""
        try:
            # 主配置文件
            main_config_file = self.config_dir / "config.yaml"
            if main_config_file.exists():
                source = ConfigSource(
                    source_id="main_config",
                    source_type="file",
                    location=str(main_config_file),
                    priority=100,
                    watch_changes=True
                )
                await self.add_config_source(source)
            
            # 环境特定配置
            env = os.getenv("POWERAUTOMATION_ENV", "development")
            env_config_file = self.config_dir / f"config.{env}.yaml"
            if env_config_file.exists():
                source = ConfigSource(
                    source_id=f"env_config_{env}",
                    source_type="file",
                    location=str(env_config_file),
                    priority=200,
                    watch_changes=True
                )
                await self.add_config_source(source)
            
            # 环境变量配置源
            env_source = ConfigSource(
                source_id="environment_variables",
                source_type="env",
                location="POWERAUTOMATION_",
                priority=300
            )
            await self.add_config_source(env_source)
            
        except Exception as e:
            self.logger.error(f"加载默认配置源失败: {e}")
    
    async def _load_all_configs(self) -> None:
        """加载所有配置"""
        try:
            # 按优先级排序配置源
            sorted_sources = sorted(
                self.config_sources.values(),
                key=lambda x: x.priority
            )
            
            # 清空当前配置
            with self.config_lock:
                self.config_data.clear()
            
            # 依次加载配置源
            for source in sorted_sources:
                if source.enabled:
                    await self._load_source_config(source)
            
        except Exception as e:
            self.logger.error(f"加载所有配置失败: {e}")
    
    async def _load_source_config(self, source: ConfigSource) -> None:
        """加载单个配置源"""
        try:
            config_data = {}
            
            if source.source_type == "file":
                config_data = await self._load_file_config(source.location)
            elif source.source_type == "env":
                config_data = await self._load_env_config(source.location)
            elif source.source_type == "remote":
                config_data = await self._load_remote_config(source.location)
            elif source.source_type == "database":
                config_data = await self._load_database_config(source.location)
            
            # 合并配置数据
            with self.config_lock:
                self._merge_config(self.config_data, config_data)
            
            self.logger.debug(f"加载配置源: {source.source_id}")
            
        except Exception as e:
            self.logger.error(f"加载配置源失败 {source.source_id}: {e}")
    
    async def _load_file_config(self, file_path: str) -> Dict[str, Any]:
        """加载文件配置"""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"配置文件不存在: {file_path}")
                return {}
            
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif path.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    self.logger.error(f"不支持的配置文件格式: {file_path}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"加载文件配置失败: {e}")
            return {}
    
    async def _load_env_config(self, prefix: str) -> Dict[str, Any]:
        """加载环境变量配置"""
        try:
            config_data = {}
            
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    # 移除前缀并转换为配置键
                    config_key = key[len(prefix):].lower().replace('_', '.')
                    
                    # 尝试解析值类型
                    parsed_value = self._parse_env_value(value)
                    
                    # 设置嵌套值
                    self._set_nested_value(config_data, config_key, parsed_value)
            
            return config_data
            
        except Exception as e:
            self.logger.error(f"加载环境变量配置失败: {e}")
            return {}
    
    async def _load_remote_config(self, url: str) -> Dict[str, Any]:
        """加载远程配置"""
        # 这里可以实现从远程服务器加载配置的逻辑
        # 例如从配置中心、API等获取配置
        self.logger.info(f"远程配置加载（待实现）: {url}")
        return {}
    
    async def _load_database_config(self, connection_string: str) -> Dict[str, Any]:
        """加载数据库配置"""
        # 这里可以实现从数据库加载配置的逻辑
        self.logger.info(f"数据库配置加载（待实现）: {connection_string}")
        return {}
    
    async def _reload_file_config(self, file_path: str) -> None:
        """重新加载文件配置"""
        try:
            # 找到对应的配置源
            source = None
            for s in self.config_sources.values():
                if s.source_type == "file" and s.location == file_path:
                    source = s
                    break
            
            if source:
                await self._load_source_config(source)
                self.logger.info(f"重新加载文件配置: {file_path}")
            
        except Exception as e:
            self.logger.error(f"重新加载文件配置失败: {e}")
    
    async def _start_file_watching(self, source: ConfigSource) -> None:
        """启动文件监控"""
        try:
            file_path = source.location
            directory = os.path.dirname(file_path)
            
            event_handler = ConfigFileWatcher(self, file_path)
            observer = Observer()
            observer.schedule(event_handler, directory, recursive=False)
            observer.start()
            
            self.file_watchers[source.source_id] = observer
            self.logger.info(f"启动文件监控: {file_path}")
            
        except Exception as e:
            self.logger.error(f"启动文件监控失败: {e}")
    
    async def _validate_configs(self) -> None:
        """验证配置"""
        try:
            is_valid = await self.validator.validate(self.config_data)
            if not is_valid:
                self.logger.warning("配置验证失败")
            else:
                self.logger.info("配置验证通过")
                
        except Exception as e:
            self.logger.error(f"配置验证出错: {e}")
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """获取嵌套值"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """设置嵌套值"""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """合并配置"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value
    
    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """扁平化字典"""
        result = {}
        
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_dict(value, new_key))
            else:
                result[new_key] = value
        
        return result
    
    def _parse_env_value(self, value: str) -> Any:
        """解析环境变量值"""
        # 尝试解析为布尔值
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # 尝试解析为数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 尝试解析为JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # 返回字符串
        return value
    
    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """清理配置中的敏感信息"""
        sanitized = {}
        
        for key, value in config.items():
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_config(value)
            elif isinstance(key, str) and any(sensitive in key.lower() for sensitive in ['password', 'secret', 'token', 'key']):
                sanitized[key] = "***HIDDEN***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _notify_change_listeners(self, change: ConfigChange) -> None:
        """通知配置变更监听器"""
        for listener in self.change_listeners:
            try:
                listener(change)
            except Exception as e:
                self.logger.error(f"配置变更监听器执行失败: {e}")

