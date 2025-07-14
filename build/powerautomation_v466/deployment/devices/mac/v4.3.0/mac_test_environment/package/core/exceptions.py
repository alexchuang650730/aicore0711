"""
PowerAutomation 4.0 Exception Handling
统一异常处理模块，定义系统中的各种异常类型
"""

import traceback
import logging
from typing import Dict, Any, Optional, List
from enum import Enum


class ErrorCode(Enum):
    """错误代码枚举"""
    # 系统级错误 (1000-1999)
    SYSTEM_ERROR = 1000
    CONFIG_ERROR = 1001
    INITIALIZATION_ERROR = 1002
    SHUTDOWN_ERROR = 1003
    
    # 网络和通信错误 (2000-2999)
    NETWORK_ERROR = 2000
    CONNECTION_ERROR = 2001
    TIMEOUT_ERROR = 2002
    API_ERROR = 2003
    MCP_COMMUNICATION_ERROR = 2004
    
    # 认证和授权错误 (3000-3999)
    AUTHENTICATION_ERROR = 3000
    AUTHORIZATION_ERROR = 3001
    TOKEN_ERROR = 3002
    PERMISSION_ERROR = 3003
    
    # 数据和存储错误 (4000-4999)
    DATA_ERROR = 4000
    DATABASE_ERROR = 4001
    VALIDATION_ERROR = 4002
    SERIALIZATION_ERROR = 4003
    
    # 业务逻辑错误 (5000-5999)
    BUSINESS_ERROR = 5000
    COMMAND_ERROR = 5001
    ROUTING_ERROR = 5002
    AGENT_ERROR = 5003
    WORKFLOW_ERROR = 5004
    
    # 资源和限制错误 (6000-6999)
    RESOURCE_ERROR = 6000
    MEMORY_ERROR = 6001
    DISK_ERROR = 6002
    RATE_LIMIT_ERROR = 6003
    QUOTA_ERROR = 6004
    
    # 外部服务错误 (7000-7999)
    EXTERNAL_SERVICE_ERROR = 7000
    CLAUDE_API_ERROR = 7001
    OPENAI_API_ERROR = 7002
    REDIS_ERROR = 7003


class PowerAutomationException(Exception):
    """PowerAutomation基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.SYSTEM_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = self._get_timestamp()
        self.traceback_info = self._get_traceback()
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def _get_traceback(self) -> str:
        """获取堆栈跟踪信息"""
        return traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "cause": str(self.cause) if self.cause else None,
            "traceback": self.traceback_info
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code.name}] {self.message}"


class ConfigurationError(PowerAutomationException):
    """配置错误"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        super().__init__(
            message,
            error_code=ErrorCode.CONFIG_ERROR,
            details=details,
            **kwargs
        )


class NetworkError(PowerAutomationException):
    """网络错误"""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        details = kwargs.get('details', {})
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
        super().__init__(
            message,
            error_code=ErrorCode.NETWORK_ERROR,
            details=details,
            **kwargs
        )


class AuthenticationError(PowerAutomationException):
    """认证错误"""
    
    def __init__(self, message: str, user_id: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if user_id:
            details['user_id'] = user_id
        super().__init__(
            message,
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            details=details,
            **kwargs
        )


class ValidationError(PowerAutomationException):
    """数据验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        super().__init__(
            message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details,
            **kwargs
        )


class CommandError(PowerAutomationException):
    """命令执行错误"""
    
    def __init__(self, message: str, command: Optional[str] = None, exit_code: Optional[int] = None, **kwargs):
        details = kwargs.get('details', {})
        if command:
            details['command'] = command
        if exit_code is not None:
            details['exit_code'] = exit_code
        super().__init__(
            message,
            error_code=ErrorCode.COMMAND_ERROR,
            details=details,
            **kwargs
        )


class RoutingError(PowerAutomationException):
    """路由错误"""
    
    def __init__(self, message: str, intent: Optional[str] = None, confidence: Optional[float] = None, **kwargs):
        details = kwargs.get('details', {})
        if intent:
            details['intent'] = intent
        if confidence is not None:
            details['confidence'] = confidence
        super().__init__(
            message,
            error_code=ErrorCode.ROUTING_ERROR,
            details=details,
            **kwargs
        )


class AgentError(PowerAutomationException):
    """智能体错误"""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, agent_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if agent_id:
            details['agent_id'] = agent_id
        if agent_type:
            details['agent_type'] = agent_type
        super().__init__(
            message,
            error_code=ErrorCode.AGENT_ERROR,
            details=details,
            **kwargs
        )


class MCPCommunicationError(PowerAutomationException):
    """MCP通信错误"""
    
    def __init__(self, message: str, mcp_id: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if mcp_id:
            details['mcp_id'] = mcp_id
        if operation:
            details['operation'] = operation
        super().__init__(
            message,
            error_code=ErrorCode.MCP_COMMUNICATION_ERROR,
            details=details,
            **kwargs
        )


class ExternalServiceError(PowerAutomationException):
    """外部服务错误"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if service_name:
            details['service_name'] = service_name
        super().__init__(
            message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            details=details,
            **kwargs
        )


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_stats = {}
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = True
    ) -> Optional[PowerAutomationException]:
        """处理异常"""
        try:
            # 如果已经是PowerAutomation异常，直接处理
            if isinstance(exception, PowerAutomationException):
                pa_exception = exception
            else:
                # 转换为PowerAutomation异常
                pa_exception = self._convert_exception(exception, context)
            
            # 记录异常
            self._log_exception(pa_exception, context)
            
            # 更新统计
            self._update_error_stats(pa_exception)
            
            # 是否重新抛出异常
            if reraise:
                raise pa_exception
            
            return pa_exception
            
        except Exception as e:
            # 处理异常时发生错误
            self.logger.error(f"处理异常时发生错误: {e}")
            if reraise:
                raise exception
            return None
    
    def _convert_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> PowerAutomationException:
        """转换标准异常为PowerAutomation异常"""
        exception_type = type(exception).__name__
        message = str(exception)
        
        # 根据异常类型选择错误代码
        error_code_map = {
            'ConnectionError': ErrorCode.CONNECTION_ERROR,
            'TimeoutError': ErrorCode.TIMEOUT_ERROR,
            'ValueError': ErrorCode.VALIDATION_ERROR,
            'KeyError': ErrorCode.DATA_ERROR,
            'FileNotFoundError': ErrorCode.RESOURCE_ERROR,
            'PermissionError': ErrorCode.PERMISSION_ERROR,
            'MemoryError': ErrorCode.MEMORY_ERROR,
        }
        
        error_code = error_code_map.get(exception_type, ErrorCode.SYSTEM_ERROR)
        
        details = {
            'original_exception_type': exception_type,
            'original_message': message
        }
        
        if context:
            details.update(context)
        
        return PowerAutomationException(
            message=f"{exception_type}: {message}",
            error_code=error_code,
            details=details,
            cause=exception
        )
    
    def _log_exception(self, exception: PowerAutomationException, context: Optional[Dict[str, Any]] = None):
        """记录异常日志"""
        log_data = {
            'error_code': exception.error_code.name,
            'message': exception.message,
            'details': exception.details,
            'timestamp': exception.timestamp
        }
        
        if context:
            log_data['context'] = context
        
        # 根据错误级别选择日志级别
        if exception.error_code.value < 3000:
            self.logger.error(f"系统错误: {log_data}")
        elif exception.error_code.value < 5000:
            self.logger.warning(f"业务警告: {log_data}")
        else:
            self.logger.info(f"业务信息: {log_data}")
    
    def _update_error_stats(self, exception: PowerAutomationException):
        """更新错误统计"""
        error_name = exception.error_code.name
        if error_name not in self.error_stats:
            self.error_stats[error_name] = {
                'count': 0,
                'first_occurrence': exception.timestamp,
                'last_occurrence': exception.timestamp
            }
        
        self.error_stats[error_name]['count'] += 1
        self.error_stats[error_name]['last_occurrence'] = exception.timestamp
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return self.error_stats.copy()
    
    def reset_error_stats(self):
        """重置错误统计"""
        self.error_stats.clear()


# 全局错误处理器实例
_global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = True
) -> Optional[PowerAutomationException]:
    """处理异常的便捷函数"""
    return get_error_handler().handle_exception(exception, context, reraise)


def safe_execute(func, *args, default=None, context: Optional[Dict[str, Any]] = None, **kwargs):
    """安全执行函数，捕获异常并返回默认值"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        get_error_handler().handle_exception(e, context, reraise=False)
        return default


class ExceptionContext:
    """异常上下文管理器"""
    
    def __init__(self, context: Dict[str, Any], reraise: bool = True):
        self.context = context
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            handle_exception(exc_val, self.context, self.reraise)
        return not self.reraise  # 如果不重新抛出，则抑制异常



class AgentError(PowerAutomationException):
    """智能体错误"""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, agent_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if agent_id:
            details['agent_id'] = agent_id
        if agent_type:
            details['agent_type'] = agent_type
        super().__init__(
            message,
            error_code=ErrorCode.AGENT_ERROR,
            details=details,
            **kwargs
        )


class MCPCommunicationError(PowerAutomationException):
    """MCP通信错误"""
    
    def __init__(self, message: str, mcp_id: Optional[str] = None, endpoint: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if mcp_id:
            details['mcp_id'] = mcp_id
        if endpoint:
            details['endpoint'] = endpoint
        super().__init__(
            message,
            error_code=ErrorCode.MCP_COMMUNICATION_ERROR,
            details=details,
            **kwargs
        )


class MCPRegistrationError(PowerAutomationException):
    """MCP注册错误"""
    
    def __init__(self, message: str, mcp_name: Optional[str] = None, mcp_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if mcp_name:
            details['mcp_name'] = mcp_name
        if mcp_type:
            details['mcp_type'] = mcp_type
        super().__init__(
            message,
            error_code=ErrorCode.MCP_COMMUNICATION_ERROR,  # 使用MCP通信错误代码
            details=details,
            **kwargs
        )


class WorkflowError(PowerAutomationException):
    """工作流错误"""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, step: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if workflow_id:
            details['workflow_id'] = workflow_id
        if step:
            details['step'] = step
        super().__init__(
            message,
            error_code=ErrorCode.WORKFLOW_ERROR,
            details=details,
            **kwargs
        )


class ResourceError(PowerAutomationException):
    """资源错误"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        super().__init__(
            message,
            error_code=ErrorCode.RESOURCE_ERROR,
            details=details,
            **kwargs
        )


class ExternalServiceError(PowerAutomationException):
    """外部服务错误"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, service_url: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if service_name:
            details['service_name'] = service_name
        if service_url:
            details['service_url'] = service_url
        super().__init__(
            message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            details=details,
            **kwargs
        )


# 异常处理工具类
class ExceptionContext:
    """异常上下文管理器"""
    
    def __init__(self, context_data: Dict[str, Any], reraise: bool = True):
        self.context_data = context_data
        self.reraise = reraise
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # 记录异常信息
            self.logger.error(
                f"异常发生在上下文 {self.context_data}: {exc_type.__name__}: {exc_val}",
                extra={'context': self.context_data}
            )
            
            # 如果不是PowerAutomation异常，包装为PowerAutomation异常
            if not isinstance(exc_val, PowerAutomationException):
                wrapped_exception = PowerAutomationException(
                    f"未处理的异常: {str(exc_val)}",
                    details=self.context_data,
                    cause=exc_val
                )
                
                if self.reraise:
                    raise wrapped_exception from exc_val
                else:
                    self.logger.error(f"异常已被抑制: {wrapped_exception}")
                    return True  # 抑制异常
            
            return not self.reraise  # 如果reraise=False，抑制异常


class ErrorHandler:
    """全局错误处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_stats = {
            'total_errors': 0,
            'error_by_type': {},
            'error_by_code': {}
        }
    
    def handle_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> PowerAutomationException:
        """处理异常，转换为PowerAutomation异常"""
        context = context or {}
        
        # 更新统计
        self.error_stats['total_errors'] += 1
        
        if isinstance(exception, PowerAutomationException):
            # 已经是PowerAutomation异常
            pa_exception = exception
        else:
            # 转换为PowerAutomation异常
            pa_exception = PowerAutomationException(
                f"未处理的异常: {str(exception)}",
                details=context,
                cause=exception
            )
        
        # 更新统计
        error_type = type(pa_exception).__name__
        error_code = pa_exception.error_code.name
        
        self.error_stats['error_by_type'][error_type] = self.error_stats['error_by_type'].get(error_type, 0) + 1
        self.error_stats['error_by_code'][error_code] = self.error_stats['error_by_code'].get(error_code, 0) + 1
        
        # 记录日志
        self.logger.error(
            f"处理异常: {error_type} [{error_code}] {pa_exception.message}",
            extra={
                'error_code': pa_exception.error_code.value,
                'error_details': pa_exception.details,
                'context': context
            }
        )
        
        return pa_exception
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.error_stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.error_stats = {
            'total_errors': 0,
            'error_by_type': {},
            'error_by_code': {}
        }


# 全局错误处理器实例
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    return _error_handler


def handle_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> PowerAutomationException:
    """处理异常的便捷函数"""
    return _error_handler.handle_exception(exception, context)


def safe_execute(func, *args, default=None, context: Optional[Dict[str, Any]] = None, **kwargs):
    """安全执行函数，捕获异常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_exception(e, context)
        return default


async def safe_execute_async(func, *args, default=None, context: Optional[Dict[str, Any]] = None, **kwargs):
    """安全执行异步函数，捕获异常"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        handle_exception(e, context)
        return default



class TaskDispatchError(PowerAutomationException):
    """任务分发错误"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, dispatcher_id: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if task_id:
            details['task_id'] = task_id
        if dispatcher_id:
            details['dispatcher_id'] = dispatcher_id
        super().__init__(
            message,
            error_code=ErrorCode.TASK_ERROR,
            details=details,
            **kwargs
        )


class CollaborationError(PowerAutomationException):
    """协作错误"""
    
    def __init__(self, message: str, session_id: Optional[str] = None, collaboration_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if session_id:
            details['session_id'] = session_id
        if collaboration_type:
            details['collaboration_type'] = collaboration_type
        super().__init__(
            message,
            error_code=ErrorCode.AGENT_ERROR,
            details=details,
            **kwargs
        )


class CoordinationError(PowerAutomationException):
    """协调错误"""
    
    def __init__(self, message: str, coordinator_id: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if coordinator_id:
            details['coordinator_id'] = coordinator_id
        if operation:
            details['operation'] = operation
        super().__init__(
            message,
            error_code=ErrorCode.AGENT_ERROR,
            details=details,
            **kwargs
        )

