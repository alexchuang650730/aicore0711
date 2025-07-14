"""
PowerAutomation 4.0 Logging Configuration
统一日志配置模块，提供结构化日志和多种输出格式
"""

import os
import sys
import logging
import logging.handlers
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .config import get_config


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """结构化格式化器"""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为结构化文本"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        base_format = (
            f"{timestamp} | {record.levelname:8} | "
            f"{record.name:20} | {record.module}:{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}"
        )
        
        # 添加异常信息
        if record.exc_info:
            base_format += f"\n{self.formatException(record.exc_info)}"
        
        # 添加额外字段
        if self.include_extra and hasattr(record, 'extra_fields'):
            extra_str = " | ".join([f"{k}={v}" for k, v in record.extra_fields.items()])
            base_format += f" | {extra_str}"
        
        return base_format


class PowerAutomationLogger:
    """PowerAutomation日志器"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        app_config = get_config()
        return {
            'level': app_config.log_level,
            'file': app_config.log_file,
            'max_size': app_config.log_max_size,
            'backup_count': app_config.log_backup_count,
            'format': 'structured',  # 'structured', 'json', 'simple'
            'console': True,
            'file_enabled': True
        }
    
    def _setup_logger(self):
        """设置日志器"""
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 设置日志级别
        level = getattr(logging, self.config['level'].upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 防止重复日志
        self.logger.propagate = False
        
        # 添加控制台处理器
        if self.config.get('console', True):
            self._add_console_handler()
        
        # 添加文件处理器
        if self.config.get('file_enabled', True):
            self._add_file_handler()
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 选择格式化器
        if self.config['format'] == 'json':
            formatter = JSONFormatter()
        elif self.config['format'] == 'structured':
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """添加文件处理器"""
        log_file = self.config['file']
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # 解析文件大小
        max_bytes = self._parse_size(self.config.get('max_size', '10MB'))
        backup_count = self.config.get('backup_count', 5)
        
        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 文件使用JSON格式
        formatter = JSONFormatter()
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def log_with_context(self, level: int, message: str, **context):
        """带上下文的日志记录"""
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        record.extra_fields = context
        self.logger.handle(record)
    
    def debug(self, message: str, **context):
        """调试日志"""
        self.log_with_context(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        """信息日志"""
        self.log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context):
        """警告日志"""
        self.log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, **context):
        """错误日志"""
        self.log_with_context(logging.ERROR, message, **context)
    
    def critical(self, message: str, **context):
        """严重错误日志"""
        self.log_with_context(logging.CRITICAL, message, **context)
    
    def exception(self, message: str, **context):
        """异常日志"""
        self.logger.exception(message, extra={'extra_fields': context})


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self._loggers: Dict[str, PowerAutomationLogger] = {}
        self._default_config = None
        self._setup_default_config()
    
    def _setup_default_config(self):
        """设置默认配置"""
        try:
            app_config = get_config()
            self._default_config = {
                'level': app_config.log_level,
                'file': app_config.log_file,
                'max_size': app_config.log_max_size,
                'backup_count': app_config.log_backup_count,
                'format': 'structured',
                'console': True,
                'file_enabled': True
            }
        except Exception:
            # 如果配置加载失败，使用硬编码默认值
            self._default_config = {
                'level': 'INFO',
                'file': 'logs/powerautomation.log',
                'max_size': '10MB',
                'backup_count': 5,
                'format': 'structured',
                'console': True,
                'file_enabled': True
            }
    
    def get_logger(self, name: str, config: Optional[Dict[str, Any]] = None) -> PowerAutomationLogger:
        """获取日志器"""
        if name not in self._loggers:
            logger_config = config or self._default_config
            self._loggers[name] = PowerAutomationLogger(name, logger_config)
        return self._loggers[name]
    
    def configure_logger(self, name: str, config: Dict[str, Any]):
        """配置特定日志器"""
        if name in self._loggers:
            # 重新配置现有日志器
            self._loggers[name].config.update(config)
            self._loggers[name]._setup_logger()
        else:
            # 创建新的日志器
            merged_config = self._default_config.copy()
            merged_config.update(config)
            self._loggers[name] = PowerAutomationLogger(name, merged_config)
    
    def set_global_level(self, level: str):
        """设置全局日志级别"""
        for logger in self._loggers.values():
            logger.config['level'] = level
            logger._setup_logger()
    
    def get_all_loggers(self) -> List[str]:
        """获取所有日志器名称"""
        return list(self._loggers.keys())


# 全局日志管理器实例
_logger_manager = None


def get_logger_manager() -> LoggerManager:
    """获取全局日志管理器"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager


def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> PowerAutomationLogger:
    """获取日志器的便捷函数"""
    return get_logger_manager().get_logger(name, config)


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """设置全局日志配置"""
    if config:
        manager = get_logger_manager()
        manager._default_config.update(config)
        
        # 重新配置所有现有日志器
        for name in manager.get_all_loggers():
            manager.configure_logger(name, config)


# 预定义的日志器
def get_system_logger() -> PowerAutomationLogger:
    """获取系统日志器"""
    return get_logger('powerautomation.system')


def get_api_logger() -> PowerAutomationLogger:
    """获取API日志器"""
    return get_logger('powerautomation.api')


def get_agent_logger() -> PowerAutomationLogger:
    """获取智能体日志器"""
    return get_logger('powerautomation.agent')


def get_mcp_logger() -> PowerAutomationLogger:
    """获取MCP日志器"""
    return get_logger('powerautomation.mcp')


def get_command_logger() -> PowerAutomationLogger:
    """获取命令日志器"""
    return get_logger('powerautomation.command')


# 初始化默认日志配置
try:
    setup_logging()
except Exception:
    # 如果初始化失败，使用基本配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )



def get_task_logger() -> PowerAutomationLogger:
    """获取任务日志器"""
    return _logger_manager.get_logger("task")


def get_coordination_logger() -> PowerAutomationLogger:
    """获取协调日志器"""
    return _logger_manager.get_logger("coordination")


def get_collaboration_logger() -> PowerAutomationLogger:
    """获取协作日志器"""
    return _logger_manager.get_logger("collaboration")


def get_dispatcher_logger() -> PowerAutomationLogger:
    """获取分发器日志器"""
    return _logger_manager.get_logger("dispatcher")


def get_workflow_logger() -> PowerAutomationLogger:
    """获取工作流日志器"""
    return _logger_manager.get_logger("workflow")


def get_router_logger() -> PowerAutomationLogger:
    """获取路由器日志器"""
    return _logger_manager.get_logger("router")

