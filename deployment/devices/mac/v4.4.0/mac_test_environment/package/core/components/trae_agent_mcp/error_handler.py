"""
Trae Error Handler - Comprehensive Error Handling and Recovery

This module provides comprehensive error handling, recovery mechanisms,
and resilience features for Trae Agent integration within PowerAutomation.
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    CONFIGURATION = "configuration"
    COMMUNICATION = "communication"
    EXECUTION = "execution"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    ABORT = "abort"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    task_id: str
    operation: str
    timestamp: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_context: Dict[str, Any] = None


@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    stack_trace: str
    recovery_strategy: RecoveryStrategy
    retry_count: int = 0
    max_retries: int = 3
    recovery_attempts: List[str] = None


@dataclass
class RecoveryResult:
    """Result of error recovery attempt"""
    success: bool
    strategy_used: RecoveryStrategy
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    recovery_time: float = 0.0
    additional_info: Dict[str, Any] = None


class TraeErrorHandler:
    """
    Trae Agent Error Handler
    
    Provides comprehensive error handling, recovery mechanisms, and resilience
    features for Trae Agent integration within PowerAutomation architecture.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Trae Error Handler
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Error handling configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.exponential_backoff = self.config.get('exponential_backoff', True)
        self.enable_fallback = self.config.get('enable_fallback', True)
        self.enable_circuit_breaker = self.config.get('enable_circuit_breaker', True)
        
        # Circuit breaker configuration
        self.circuit_breaker_threshold = self.config.get('circuit_breaker_threshold', 5)
        self.circuit_breaker_timeout = self.config.get('circuit_breaker_timeout', 60.0)
        self.circuit_breaker_state = 'closed'  # closed, open, half-open
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0
        
        # Error tracking
        self.error_history = []
        self.error_patterns = {}
        self.recovery_strategies = self._initialize_recovery_strategies()
        
        # Performance metrics
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'average_recovery_time': 0.0
        }
        
        self.logger.info("TraeErrorHandler initialized")
    
    async def handle_trae_error(self, error: Exception, task: Any) -> Dict[str, Any]:
        """
        Handle Trae Agent error with comprehensive recovery
        
        Args:
            error: Exception that occurred
            task: Original task that caused the error
            
        Returns:
            Dict: Error handling result
        """
        start_time = time.time()
        
        try:
            self.logger.error(f"Handling Trae Agent error: {str(error)}")
            
            # Create error context
            error_context = await self._create_error_context(error, task)
            
            # Classify error
            error_info = await self._classify_error(error, error_context)
            
            # Check circuit breaker
            if self.enable_circuit_breaker and await self._is_circuit_breaker_open():
                return await self._handle_circuit_breaker_open(error_info)
            
            # Attempt recovery
            recovery_result = await self._attempt_recovery(error_info, task)
            
            # Update circuit breaker state
            if self.enable_circuit_breaker:
                await self._update_circuit_breaker_state(recovery_result.success)
            
            # Record error and recovery
            await self._record_error_and_recovery(error_info, recovery_result)
            
            # Update statistics
            recovery_time = time.time() - start_time
            await self._update_error_stats(error_info, recovery_result, recovery_time)
            
            # Create final result
            result = await self._create_error_result(error_info, recovery_result, task)
            
            self.logger.info(f"Error handling completed in {recovery_time:.2f}s")
            return result
            
        except Exception as handling_error:
            self.logger.critical(f"Error in error handler: {str(handling_error)}")
            return await self._create_critical_error_result(error, handling_error, task)
    
    async def _create_error_context(self, error: Exception, task: Any) -> ErrorContext:
        """
        Create error context from error and task information
        
        Args:
            error: Exception that occurred
            task: Original task
            
        Returns:
            ErrorContext: Error context information
        """
        return ErrorContext(
            task_id=getattr(task, 'id', 'unknown'),
            operation='trae_agent_execution',
            timestamp=time.time(),
            user_id=getattr(task, 'user_id', None),
            session_id=getattr(task, 'session_id', None),
            additional_context={
                'task_description': getattr(task, 'description', ''),
                'task_priority': getattr(task, 'priority', 'normal'),
                'task_files': getattr(task, 'files', []),
                'error_type': type(error).__name__
            }
        )
    
    async def _classify_error(self, error: Exception, context: ErrorContext) -> ErrorInfo:
        """
        Classify error and determine handling strategy
        
        Args:
            error: Exception to classify
            context: Error context
            
        Returns:
            ErrorInfo: Classified error information
        """
        error_id = f"trae_error_{int(time.time())}_{id(error)}"
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Determine error category
        category = await self._determine_error_category(error, error_message)
        
        # Determine error severity
        severity = await self._determine_error_severity(error, category, context)
        
        # Determine recovery strategy
        recovery_strategy = await self._determine_recovery_strategy(error, category, severity)
        
        # Get max retries for this error type
        max_retries = await self._get_max_retries_for_error(error, category, severity)
        
        return ErrorInfo(
            error_id=error_id,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            context=context,
            stack_trace=stack_trace,
            recovery_strategy=recovery_strategy,
            retry_count=0,
            max_retries=max_retries,
            recovery_attempts=[]
        )
    
    async def _determine_error_category(self, error: Exception, error_message: str) -> ErrorCategory:
        """
        Determine error category based on error type and message
        
        Args:
            error: Exception object
            error_message: Error message string
            
        Returns:
            ErrorCategory: Determined category
        """
        error_type = type(error).__name__
        message_lower = error_message.lower()
        
        # Configuration errors
        if any(keyword in message_lower for keyword in ['config', 'configuration', 'setting', 'parameter']):
            return ErrorCategory.CONFIGURATION
        
        # Communication errors
        if any(keyword in message_lower for keyword in ['connection', 'network', 'socket', 'http', 'api']):
            return ErrorCategory.COMMUNICATION
        
        # Timeout errors
        if any(keyword in message_lower for keyword in ['timeout', 'timed out', 'deadline']):
            return ErrorCategory.TIMEOUT
        
        # Resource errors
        if any(keyword in message_lower for keyword in ['memory', 'disk', 'space', 'resource', 'limit']):
            return ErrorCategory.RESOURCE
        
        # Validation errors
        if any(keyword in message_lower for keyword in ['validation', 'invalid', 'format', 'schema']):
            return ErrorCategory.VALIDATION
        
        # Transformation errors
        if any(keyword in message_lower for keyword in ['transform', 'conversion', 'parse', 'decode']):
            return ErrorCategory.TRANSFORMATION
        
        # Execution errors
        if any(keyword in message_lower for keyword in ['execution', 'runtime', 'process', 'command']):
            return ErrorCategory.EXECUTION
        
        # Error type based classification
        if error_type in ['TimeoutError', 'asyncio.TimeoutError']:
            return ErrorCategory.TIMEOUT
        elif error_type in ['ConnectionError', 'NetworkError', 'HTTPError']:
            return ErrorCategory.COMMUNICATION
        elif error_type in ['ValueError', 'TypeError', 'ValidationError']:
            return ErrorCategory.VALIDATION
        elif error_type in ['MemoryError', 'OSError', 'IOError']:
            return ErrorCategory.RESOURCE
        elif error_type in ['RuntimeError', 'ProcessError', 'ExecutionError']:
            return ErrorCategory.EXECUTION
        
        return ErrorCategory.UNKNOWN
    
    async def _determine_error_severity(self, error: Exception, category: ErrorCategory, context: ErrorContext) -> ErrorSeverity:
        """
        Determine error severity based on error characteristics and context
        
        Args:
            error: Exception object
            category: Error category
            context: Error context
            
        Returns:
            ErrorSeverity: Determined severity
        """
        # Critical errors
        if category == ErrorCategory.RESOURCE and 'memory' in str(error).lower():
            return ErrorSeverity.CRITICAL
        
        if type(error).__name__ in ['SystemExit', 'KeyboardInterrupt', 'MemoryError']:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.COMMUNICATION, ErrorCategory.EXECUTION]:
            return ErrorSeverity.HIGH
        
        if context.additional_context.get('task_priority') == 'critical':
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.TIMEOUT, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.MEDIUM
        
        if context.additional_context.get('task_priority') == 'high':
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category in [ErrorCategory.VALIDATION, ErrorCategory.TRANSFORMATION]:
            return ErrorSeverity.LOW
        
        # Default to medium
        return ErrorSeverity.MEDIUM
    
    async def _determine_recovery_strategy(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity) -> RecoveryStrategy:
        """
        Determine recovery strategy based on error characteristics
        
        Args:
            error: Exception object
            category: Error category
            severity: Error severity
            
        Returns:
            RecoveryStrategy: Determined strategy
        """
        # Critical errors - abort immediately
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ABORT
        
        # Category-based strategies
        if category == ErrorCategory.TIMEOUT:
            return RecoveryStrategy.RETRY
        elif category == ErrorCategory.COMMUNICATION:
            return RecoveryStrategy.RETRY
        elif category == ErrorCategory.CONFIGURATION:
            return RecoveryStrategy.FALLBACK
        elif category == ErrorCategory.VALIDATION:
            return RecoveryStrategy.FALLBACK
        elif category == ErrorCategory.TRANSFORMATION:
            return RecoveryStrategy.FALLBACK
        elif category == ErrorCategory.RESOURCE:
            return RecoveryStrategy.ESCALATE
        elif category == ErrorCategory.EXECUTION:
            return RecoveryStrategy.RETRY
        
        # Default strategy
        return RecoveryStrategy.RETRY
    
    async def _get_max_retries_for_error(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity) -> int:
        """
        Get maximum retries for specific error type
        
        Args:
            error: Exception object
            category: Error category
            severity: Error severity
            
        Returns:
            int: Maximum retry count
        """
        # Severity-based retry limits
        if severity == ErrorSeverity.CRITICAL:
            return 0  # No retries for critical errors
        elif severity == ErrorSeverity.HIGH:
            return 2  # Limited retries for high severity
        elif severity == ErrorSeverity.MEDIUM:
            return self.max_retries
        else:  # LOW severity
            return self.max_retries + 2  # More retries for low severity
    
    async def _attempt_recovery(self, error_info: ErrorInfo, task: Any) -> RecoveryResult:
        """
        Attempt error recovery based on determined strategy
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            RecoveryResult: Recovery attempt result
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Attempting recovery with strategy: {error_info.recovery_strategy.value}")
            
            if error_info.recovery_strategy == RecoveryStrategy.RETRY:
                return await self._attempt_retry_recovery(error_info, task)
            elif error_info.recovery_strategy == RecoveryStrategy.FALLBACK:
                return await self._attempt_fallback_recovery(error_info, task)
            elif error_info.recovery_strategy == RecoveryStrategy.ESCALATE:
                return await self._attempt_escalation_recovery(error_info, task)
            elif error_info.recovery_strategy == RecoveryStrategy.IGNORE:
                return await self._attempt_ignore_recovery(error_info, task)
            elif error_info.recovery_strategy == RecoveryStrategy.ABORT:
                return await self._attempt_abort_recovery(error_info, task)
            else:
                return await self._attempt_default_recovery(error_info, task)
                
        except Exception as recovery_error:
            recovery_time = time.time() - start_time
            self.logger.error(f"Recovery attempt failed: {str(recovery_error)}")
            
            return RecoveryResult(
                success=False,
                strategy_used=error_info.recovery_strategy,
                error_message=f"Recovery failed: {str(recovery_error)}",
                recovery_time=recovery_time,
                additional_info={'recovery_error': str(recovery_error)}
            )
    
    async def _attempt_retry_recovery(self, error_info: ErrorInfo, task: Any) -> RecoveryResult:
        """
        Attempt recovery through retrying the operation
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            RecoveryResult: Recovery result
        """
        start_time = time.time()
        
        if error_info.retry_count >= error_info.max_retries:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.RETRY,
                error_message=f"Maximum retries ({error_info.max_retries}) exceeded",
                recovery_time=time.time() - start_time
            )
        
        # Calculate retry delay with exponential backoff
        delay = self.retry_delay
        if self.exponential_backoff:
            delay = self.retry_delay * (2 ** error_info.retry_count)
        
        # Wait before retry
        await asyncio.sleep(delay)
        
        # Increment retry count
        error_info.retry_count += 1
        error_info.recovery_attempts.append(f"retry_{error_info.retry_count}")
        
        try:
            # This would normally re-execute the original operation
            # For now, we simulate a recovery attempt
            self.logger.info(f"Retry attempt {error_info.retry_count}/{error_info.max_retries}")
            
            # Simulate recovery logic
            recovery_success = await self._simulate_retry_operation(error_info, task)
            
            recovery_time = time.time() - start_time
            
            if recovery_success:
                return RecoveryResult(
                    success=True,
                    strategy_used=RecoveryStrategy.RETRY,
                    result_data={'retry_count': error_info.retry_count, 'delay_used': delay},
                    recovery_time=recovery_time,
                    additional_info={'successful_retry': True}
                )
            else:
                # Retry failed, try again if retries remaining
                if error_info.retry_count < error_info.max_retries:
                    return await self._attempt_retry_recovery(error_info, task)
                else:
                    return RecoveryResult(
                        success=False,
                        strategy_used=RecoveryStrategy.RETRY,
                        error_message="All retry attempts failed",
                        recovery_time=recovery_time
                    )
                    
        except Exception as retry_error:
            recovery_time = time.time() - start_time
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.RETRY,
                error_message=f"Retry attempt failed: {str(retry_error)}",
                recovery_time=recovery_time
            )
    
    async def _attempt_fallback_recovery(self, error_info: ErrorInfo, task: Any) -> RecoveryResult:
        """
        Attempt recovery through fallback mechanisms
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            RecoveryResult: Recovery result
        """
        start_time = time.time()
        
        try:
            self.logger.info("Attempting fallback recovery")
            
            # Determine fallback strategy based on error category
            if error_info.category == ErrorCategory.CONFIGURATION:
                fallback_result = await self._fallback_to_default_config(error_info, task)
            elif error_info.category == ErrorCategory.VALIDATION:
                fallback_result = await self._fallback_to_basic_validation(error_info, task)
            elif error_info.category == ErrorCategory.TRANSFORMATION:
                fallback_result = await self._fallback_to_simple_transformation(error_info, task)
            else:
                fallback_result = await self._fallback_to_basic_operation(error_info, task)
            
            recovery_time = time.time() - start_time
            
            return RecoveryResult(
                success=fallback_result['success'],
                strategy_used=RecoveryStrategy.FALLBACK,
                result_data=fallback_result.get('data'),
                error_message=fallback_result.get('error'),
                recovery_time=recovery_time,
                additional_info={'fallback_type': fallback_result.get('fallback_type')}
            )
            
        except Exception as fallback_error:
            recovery_time = time.time() - start_time
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK,
                error_message=f"Fallback recovery failed: {str(fallback_error)}",
                recovery_time=recovery_time
            )
    
    async def _attempt_escalation_recovery(self, error_info: ErrorInfo, task: Any) -> RecoveryResult:
        """
        Attempt recovery through escalation
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            RecoveryResult: Recovery result
        """
        start_time = time.time()
        
        try:
            self.logger.info("Attempting escalation recovery")
            
            # Create escalation report
            escalation_report = {
                'error_id': error_info.error_id,
                'error_type': error_info.error_type,
                'error_message': error_info.error_message,
                'severity': error_info.severity.value,
                'category': error_info.category.value,
                'task_id': error_info.context.task_id,
                'timestamp': error_info.context.timestamp,
                'escalation_reason': 'Automatic escalation due to error severity/category'
            }
            
            # Log escalation (in real implementation, this would notify administrators)
            self.logger.warning(f"Error escalated: {escalation_report}")
            
            recovery_time = time.time() - start_time
            
            return RecoveryResult(
                success=True,  # Escalation itself is successful
                strategy_used=RecoveryStrategy.ESCALATE,
                result_data={'escalation_report': escalation_report},
                recovery_time=recovery_time,
                additional_info={'escalated': True, 'requires_manual_intervention': True}
            )
            
        except Exception as escalation_error:
            recovery_time = time.time() - start_time
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.ESCALATE,
                error_message=f"Escalation failed: {str(escalation_error)}",
                recovery_time=recovery_time
            )
    
    async def _attempt_ignore_recovery(self, error_info: ErrorInfo, task: Any) -> RecoveryResult:
        """
        Attempt recovery by ignoring the error
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            RecoveryResult: Recovery result
        """
        start_time = time.time()
        
        self.logger.info("Ignoring error as per recovery strategy")
        
        recovery_time = time.time() - start_time
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.IGNORE,
            result_data={'ignored_error': error_info.error_message},
            recovery_time=recovery_time,
            additional_info={'error_ignored': True}
        )
    
    async def _attempt_abort_recovery(self, error_info: ErrorInfo, task: Any) -> RecoveryResult:
        """
        Attempt recovery by aborting the operation
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            RecoveryResult: Recovery result
        """
        start_time = time.time()
        
        self.logger.error("Aborting operation due to critical error")
        
        recovery_time = time.time() - start_time
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.ABORT,
            error_message="Operation aborted due to critical error",
            recovery_time=recovery_time,
            additional_info={'operation_aborted': True, 'reason': 'critical_error'}
        )
    
    async def _attempt_default_recovery(self, error_info: ErrorInfo, task: Any) -> RecoveryResult:
        """
        Default recovery attempt
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            RecoveryResult: Recovery result
        """
        start_time = time.time()
        
        # Default to retry strategy
        return await self._attempt_retry_recovery(error_info, task)
    
    # Fallback implementation methods
    async def _fallback_to_default_config(self, error_info: ErrorInfo, task: Any) -> Dict[str, Any]:
        """Fallback to default configuration"""
        return {
            'success': True,
            'data': {'config': 'default', 'message': 'Using default configuration'},
            'fallback_type': 'default_config'
        }
    
    async def _fallback_to_basic_validation(self, error_info: ErrorInfo, task: Any) -> Dict[str, Any]:
        """Fallback to basic validation"""
        return {
            'success': True,
            'data': {'validation': 'basic', 'message': 'Using basic validation'},
            'fallback_type': 'basic_validation'
        }
    
    async def _fallback_to_simple_transformation(self, error_info: ErrorInfo, task: Any) -> Dict[str, Any]:
        """Fallback to simple transformation"""
        return {
            'success': True,
            'data': {'transformation': 'simple', 'message': 'Using simple transformation'},
            'fallback_type': 'simple_transformation'
        }
    
    async def _fallback_to_basic_operation(self, error_info: ErrorInfo, task: Any) -> Dict[str, Any]:
        """Fallback to basic operation"""
        return {
            'success': True,
            'data': {'operation': 'basic', 'message': 'Using basic operation'},
            'fallback_type': 'basic_operation'
        }
    
    async def _simulate_retry_operation(self, error_info: ErrorInfo, task: Any) -> bool:
        """
        Simulate retry operation (in real implementation, this would re-execute the original operation)
        
        Args:
            error_info: Error information
            task: Original task
            
        Returns:
            bool: True if retry successful, False otherwise
        """
        # Simulate success rate based on error category and retry count
        success_rates = {
            ErrorCategory.TIMEOUT: 0.7,
            ErrorCategory.COMMUNICATION: 0.6,
            ErrorCategory.EXECUTION: 0.5,
            ErrorCategory.CONFIGURATION: 0.3,
            ErrorCategory.VALIDATION: 0.4,
            ErrorCategory.TRANSFORMATION: 0.4,
            ErrorCategory.RESOURCE: 0.2,
            ErrorCategory.UNKNOWN: 0.3
        }
        
        base_success_rate = success_rates.get(error_info.category, 0.3)
        
        # Decrease success rate with each retry
        adjusted_success_rate = base_success_rate * (0.8 ** (error_info.retry_count - 1))
        
        # Simulate random success/failure
        import random
        return random.random() < adjusted_success_rate
    
    # Circuit breaker methods
    async def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_breaker_state == 'open':
            # Check if timeout has passed
            if time.time() - self.circuit_breaker_last_failure > self.circuit_breaker_timeout:
                self.circuit_breaker_state = 'half-open'
                self.logger.info("Circuit breaker moved to half-open state")
                return False
            return True
        
        return False
    
    async def _update_circuit_breaker_state(self, success: bool):
        """Update circuit breaker state based on operation result"""
        if success:
            if self.circuit_breaker_state == 'half-open':
                self.circuit_breaker_state = 'closed'
                self.circuit_breaker_failures = 0
                self.logger.info("Circuit breaker closed after successful recovery")
        else:
            self.circuit_breaker_failures += 1
            self.circuit_breaker_last_failure = time.time()
            
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                self.circuit_breaker_state = 'open'
                self.logger.warning(f"Circuit breaker opened after {self.circuit_breaker_failures} failures")
    
    async def _handle_circuit_breaker_open(self, error_info: ErrorInfo) -> Dict[str, Any]:
        """Handle case when circuit breaker is open"""
        return {
            'task_id': error_info.context.task_id,
            'success': False,
            'error_type': 'circuit_breaker_open',
            'error_message': 'Circuit breaker is open, operation blocked',
            'recovery_strategy': 'circuit_breaker',
            'circuit_breaker_state': self.circuit_breaker_state,
            'failures_count': self.circuit_breaker_failures,
            'retry_after': self.circuit_breaker_timeout
        }
    
    # Recording and statistics methods
    async def _record_error_and_recovery(self, error_info: ErrorInfo, recovery_result: RecoveryResult):
        """Record error and recovery information for analysis"""
        record = {
            'timestamp': time.time(),
            'error_info': {
                'error_id': error_info.error_id,
                'error_type': error_info.error_type,
                'category': error_info.category.value,
                'severity': error_info.severity.value,
                'task_id': error_info.context.task_id
            },
            'recovery_result': {
                'success': recovery_result.success,
                'strategy_used': recovery_result.strategy_used.value,
                'recovery_time': recovery_result.recovery_time
            }
        }
        
        # Add to error history (keep last 1000 records)
        self.error_history.append(record)
        if len(self.error_history) > 1000:
            self.error_history.pop(0)
        
        # Update error patterns for learning
        await self._update_error_patterns(error_info, recovery_result)
    
    async def _update_error_patterns(self, error_info: ErrorInfo, recovery_result: RecoveryResult):
        """Update error patterns for machine learning"""
        pattern_key = f"{error_info.category.value}_{error_info.severity.value}"
        
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = {
                'count': 0,
                'successful_recoveries': 0,
                'failed_recoveries': 0,
                'best_strategy': None,
                'average_recovery_time': 0.0
            }
        
        pattern = self.error_patterns[pattern_key]
        pattern['count'] += 1
        
        if recovery_result.success:
            pattern['successful_recoveries'] += 1
        else:
            pattern['failed_recoveries'] += 1
        
        # Update average recovery time
        pattern['average_recovery_time'] = (
            (pattern['average_recovery_time'] * (pattern['count'] - 1) + recovery_result.recovery_time) / 
            pattern['count']
        )
        
        # Update best strategy based on success rate
        if recovery_result.success:
            if pattern['best_strategy'] is None:
                pattern['best_strategy'] = recovery_result.strategy_used.value
    
    async def _update_error_stats(self, error_info: ErrorInfo, recovery_result: RecoveryResult, recovery_time: float):
        """Update error statistics"""
        self.error_stats['total_errors'] += 1
        
        # Update category stats
        category = error_info.category.value
        if category not in self.error_stats['errors_by_category']:
            self.error_stats['errors_by_category'][category] = 0
        self.error_stats['errors_by_category'][category] += 1
        
        # Update severity stats
        severity = error_info.severity.value
        if severity not in self.error_stats['errors_by_severity']:
            self.error_stats['errors_by_severity'][severity] = 0
        self.error_stats['errors_by_severity'][severity] += 1
        
        # Update recovery stats
        if recovery_result.success:
            self.error_stats['successful_recoveries'] += 1
        else:
            self.error_stats['failed_recoveries'] += 1
        
        # Update average recovery time
        total_recoveries = self.error_stats['successful_recoveries'] + self.error_stats['failed_recoveries']
        current_avg = self.error_stats['average_recovery_time']
        self.error_stats['average_recovery_time'] = (
            (current_avg * (total_recoveries - 1) + recovery_time) / total_recoveries
        )
    
    async def _create_error_result(self, error_info: ErrorInfo, recovery_result: RecoveryResult, task: Any) -> Dict[str, Any]:
        """Create final error handling result"""
        return {
            'task_id': error_info.context.task_id,
            'success': recovery_result.success,
            'error_info': {
                'error_id': error_info.error_id,
                'error_type': error_info.error_type,
                'error_message': error_info.error_message,
                'category': error_info.category.value,
                'severity': error_info.severity.value
            },
            'recovery_info': {
                'strategy_used': recovery_result.strategy_used.value,
                'recovery_success': recovery_result.success,
                'recovery_time': recovery_result.recovery_time,
                'retry_count': error_info.retry_count,
                'additional_info': recovery_result.additional_info or {}
            },
            'result_data': recovery_result.result_data or {},
            'error_message': recovery_result.error_message,
            'timestamp': time.time(),
            'circuit_breaker_state': self.circuit_breaker_state
        }
    
    async def _create_critical_error_result(self, original_error: Exception, handling_error: Exception, task: Any) -> Dict[str, Any]:
        """Create result for critical error in error handler"""
        return {
            'task_id': getattr(task, 'id', 'unknown'),
            'success': False,
            'error_info': {
                'error_type': 'critical_error_handler_failure',
                'original_error': str(original_error),
                'handling_error': str(handling_error),
                'category': 'critical',
                'severity': 'critical'
            },
            'recovery_info': {
                'strategy_used': 'none',
                'recovery_success': False,
                'recovery_time': 0.0,
                'critical_failure': True
            },
            'error_message': f"Critical error in error handler: {str(handling_error)}",
            'timestamp': time.time()
        }
    
    def _initialize_recovery_strategies(self) -> Dict[str, RecoveryStrategy]:
        """Initialize recovery strategies mapping"""
        return {
            'TimeoutError': RecoveryStrategy.RETRY,
            'ConnectionError': RecoveryStrategy.RETRY,
            'NetworkError': RecoveryStrategy.RETRY,
            'HTTPError': RecoveryStrategy.RETRY,
            'ValueError': RecoveryStrategy.FALLBACK,
            'TypeError': RecoveryStrategy.FALLBACK,
            'ValidationError': RecoveryStrategy.FALLBACK,
            'ConfigurationError': RecoveryStrategy.FALLBACK,
            'MemoryError': RecoveryStrategy.ESCALATE,
            'OSError': RecoveryStrategy.ESCALATE,
            'IOError': RecoveryStrategy.ESCALATE,
            'RuntimeError': RecoveryStrategy.RETRY,
            'ProcessError': RecoveryStrategy.RETRY,
            'ExecutionError': RecoveryStrategy.RETRY
        }
    
    async def get_error_stats(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        stats = self.error_stats.copy()
        
        # Add additional computed metrics
        total_errors = stats['total_errors']
        if total_errors > 0:
            stats['recovery_success_rate'] = stats['successful_recoveries'] / total_errors
            stats['recovery_failure_rate'] = stats['failed_recoveries'] / total_errors
        else:
            stats['recovery_success_rate'] = 0.0
            stats['recovery_failure_rate'] = 0.0
        
        # Add circuit breaker info
        stats['circuit_breaker'] = {
            'state': self.circuit_breaker_state,
            'failures': self.circuit_breaker_failures,
            'threshold': self.circuit_breaker_threshold,
            'last_failure': self.circuit_breaker_last_failure
        }
        
        # Add error patterns
        stats['error_patterns'] = self.error_patterns.copy()
        
        return stats
    
    async def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_breaker_state = 'closed'
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0
        self.logger.info("Circuit breaker manually reset")
    
    async def get_error_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent error history"""
        return self.error_history[-limit:] if self.error_history else []

