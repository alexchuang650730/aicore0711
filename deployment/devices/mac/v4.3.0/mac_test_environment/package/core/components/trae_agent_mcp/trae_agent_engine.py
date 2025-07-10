"""
Trae Agent Engine - Core Adapter

This module provides the main adapter for integrating Trae Agent as a specialized
software engineering engine within PowerAutomation 4.0 architecture.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from .trae_client import TraeClient
from .config_manager import TraeConfigManager
from .result_transformer import ResultTransformer
from .error_handler import TraeErrorHandler


class TaskType(Enum):
    """Task types that can be processed by Trae Agent"""
    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    CODE_REVIEW = "code_review"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_ANALYSIS = "security_analysis"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


@dataclass
class Task:
    """PowerAutomation task representation"""
    id: str
    description: str
    context: Dict[str, Any]
    files: List[str] = None
    priority: str = "normal"
    timeout: int = 300
    metadata: Dict[str, Any] = None


@dataclass
class Result:
    """PowerAutomation result representation"""
    task_id: str
    success: bool
    data: Dict[str, Any]
    execution_time: float
    engine_used: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class TraeAgentEngine:
    """
    Trae Agent Engine Adapter
    
    Main adapter class that integrates Trae Agent as a specialized software
    engineering engine within PowerAutomation 4.0 architecture.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Trae Agent Engine
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize components
        self.trae_client = TraeClient(self.config.get('trae_client', {}))
        self.config_manager = TraeConfigManager(self.config.get('config_manager', {}))
        self.result_transformer = ResultTransformer(self.config.get('result_transformer', {}))
        self.error_handler = TraeErrorHandler(self.config.get('error_handler', {}))
        
        # Performance tracking
        self.performance_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_execution_time': 0.0,
            'last_execution_time': 0.0
        }
        
        # Engine status
        self.is_initialized = False
        self.is_healthy = True
        
        self.logger.info("TraeAgentEngine initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the Trae Agent Engine
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing Trae Agent Engine...")
            
            # Initialize Trae client
            await self.trae_client.initialize()
            
            # Load configuration
            await self.config_manager.load_config()
            
            # Verify Trae Agent availability
            health_check = await self.trae_client.health_check()
            if not health_check:
                raise Exception("Trae Agent health check failed")
            
            self.is_initialized = True
            self.is_healthy = True
            
            self.logger.info("Trae Agent Engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Trae Agent Engine: {str(e)}")
            self.is_initialized = False
            self.is_healthy = False
            return False
    
    async def process_software_task(self, task: Task) -> Result:
        """
        Process a software engineering task using Trae Agent
        
        Args:
            task: PowerAutomation task to process
            
        Returns:
            Result: Processed result in PowerAutomation format
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing software task: {task.id}")
            
            # Validate engine status
            if not self.is_initialized or not self.is_healthy:
                raise Exception("Trae Agent Engine not properly initialized or unhealthy")
            
            # Analyze task and determine if suitable for Trae Agent
            if not await self._is_suitable_for_trae(task):
                raise Exception(f"Task {task.id} not suitable for Trae Agent processing")
            
            # Transform task to Trae Agent format
            trae_task = await self._transform_task_to_trae_format(task)
            
            # Get optimal configuration for this task
            config = await self.config_manager.get_optimal_config(task)
            
            # Configure Trae Agent for this task
            await self.trae_client.configure(config)
            
            # Execute task using Trae Agent
            trae_result = await self.trae_client.execute_task(trae_task)
            
            # Transform result back to PowerAutomation format
            pa_result = await self.result_transformer.transform_to_pa_format(
                trae_result, task
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Update performance statistics
            await self._update_performance_stats(execution_time, True)
            
            # Create final result
            result = Result(
                task_id=task.id,
                success=True,
                data=pa_result,
                execution_time=execution_time,
                engine_used="trae_agent",
                metadata={
                    'trae_config': config,
                    'task_type': await self._identify_task_type(task),
                    'tools_used': trae_result.get('tools_used', []),
                    'model_used': trae_result.get('model_used', 'unknown')
                }
            )
            
            self.logger.info(f"Successfully processed task {task.id} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Handle error
            error_result = await self.error_handler.handle_trae_error(e, task)
            
            # Update performance statistics
            await self._update_performance_stats(execution_time, False)
            
            # Create error result
            result = Result(
                task_id=task.id,
                success=False,
                data=error_result,
                execution_time=execution_time,
                engine_used="trae_agent",
                error_message=str(e),
                metadata={
                    'error_type': type(e).__name__,
                    'error_details': error_result
                }
            )
            
            self.logger.error(f"Failed to process task {task.id}: {str(e)}")
            return result
    
    async def _is_suitable_for_trae(self, task: Task) -> bool:
        """
        Determine if a task is suitable for Trae Agent processing
        
        Args:
            task: Task to analyze
            
        Returns:
            bool: True if suitable for Trae Agent, False otherwise
        """
        # Keywords that indicate software engineering tasks
        software_engineering_keywords = [
            'code', 'debug', 'refactor', 'analyze', 'architecture',
            'review', 'optimize', 'test', 'security', 'performance',
            'bug', 'function', 'class', 'module', 'api', 'database',
            'algorithm', 'data structure', 'design pattern'
        ]
        
        # Check task description for software engineering keywords
        description_lower = task.description.lower()
        keyword_matches = sum(1 for keyword in software_engineering_keywords 
                            if keyword in description_lower)
        
        # Check if files are provided (indicates code-related task)
        has_code_files = bool(task.files and any(
            file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb'))
            for file in task.files
        ))
        
        # Check task context for software engineering indicators
        context_indicators = task.context.get('task_type', '').lower() in [
            'software_engineering', 'code_analysis', 'debugging', 'refactoring'
        ]
        
        # Task is suitable if it has multiple indicators
        suitability_score = (
            (keyword_matches >= 2) +
            has_code_files +
            context_indicators +
            (task.priority in ['high', 'critical'])  # High priority tasks benefit from specialized handling
        )
        
        return suitability_score >= 2
    
    async def _transform_task_to_trae_format(self, task: Task) -> Dict[str, Any]:
        """
        Transform PowerAutomation task to Trae Agent format
        
        Args:
            task: PowerAutomation task
            
        Returns:
            Dict: Task in Trae Agent format
        """
        task_type = await self._identify_task_type(task)
        tools = await self._select_trae_tools(task, task_type)
        
        trae_task = {
            'instruction': task.description,
            'context': task.context,
            'files': task.files or [],
            'tools': tools,
            'model_preferences': await self._get_model_preferences(task),
            'timeout': task.timeout,
            'metadata': {
                'original_task_id': task.id,
                'task_type': task_type.value,
                'priority': task.priority
            }
        }
        
        return trae_task
    
    async def _identify_task_type(self, task: Task) -> TaskType:
        """
        Identify the type of software engineering task
        
        Args:
            task: Task to analyze
            
        Returns:
            TaskType: Identified task type
        """
        description_lower = task.description.lower()
        
        # Task type mapping based on keywords
        type_keywords = {
            TaskType.CODE_ANALYSIS: ['analyze', 'analysis', 'examine', 'inspect', 'understand'],
            TaskType.DEBUGGING: ['debug', 'bug', 'error', 'fix', 'issue', 'problem'],
            TaskType.REFACTORING: ['refactor', 'improve', 'optimize', 'restructure', 'clean'],
            TaskType.CODE_REVIEW: ['review', 'check', 'validate', 'assess', 'evaluate'],
            TaskType.ARCHITECTURE_DESIGN: ['design', 'architecture', 'structure', 'pattern', 'framework'],
            TaskType.PERFORMANCE_OPTIMIZATION: ['performance', 'optimize', 'speed', 'efficiency', 'benchmark'],
            TaskType.SECURITY_ANALYSIS: ['security', 'vulnerability', 'secure', 'safety', 'protection'],
            TaskType.TESTING: ['test', 'testing', 'unit test', 'integration test', 'coverage'],
            TaskType.DOCUMENTATION: ['document', 'documentation', 'comment', 'explain', 'describe']
        }
        
        # Score each task type based on keyword matches
        type_scores = {}
        for task_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                type_scores[task_type] = score
        
        # Return the task type with highest score, default to CODE_ANALYSIS
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return TaskType.CODE_ANALYSIS
    
    async def _select_trae_tools(self, task: Task, task_type: TaskType) -> List[str]:
        """
        Select appropriate Trae Agent tools for the task
        
        Args:
            task: Task to process
            task_type: Identified task type
            
        Returns:
            List[str]: List of tool names to use
        """
        # Tool mapping for different task types
        tool_mapping = {
            TaskType.CODE_ANALYSIS: ['file_editor', 'sequential_thinking'],
            TaskType.DEBUGGING: ['file_editor', 'bash_executor', 'trajectory_recorder'],
            TaskType.REFACTORING: ['file_editor', 'sequential_thinking'],
            TaskType.CODE_REVIEW: ['file_editor', 'sequential_thinking'],
            TaskType.ARCHITECTURE_DESIGN: ['sequential_thinking', 'file_editor'],
            TaskType.PERFORMANCE_OPTIMIZATION: ['file_editor', 'bash_executor', 'trajectory_recorder'],
            TaskType.SECURITY_ANALYSIS: ['file_editor', 'sequential_thinking'],
            TaskType.TESTING: ['file_editor', 'bash_executor'],
            TaskType.DOCUMENTATION: ['file_editor', 'sequential_thinking']
        }
        
        base_tools = tool_mapping.get(task_type, ['file_editor', 'sequential_thinking'])
        
        # Add additional tools based on task characteristics
        if task.files:
            base_tools.append('file_editor')
        
        if any(keyword in task.description.lower() for keyword in ['run', 'execute', 'compile', 'build']):
            base_tools.append('bash_executor')
        
        if task.priority in ['high', 'critical']:
            base_tools.append('trajectory_recorder')
        
        # Remove duplicates and return
        return list(set(base_tools))
    
    async def _get_model_preferences(self, task: Task) -> Dict[str, Any]:
        """
        Get model preferences for the task
        
        Args:
            task: Task to process
            
        Returns:
            Dict: Model preferences
        """
        # Default model preferences
        preferences = {
            'primary_model': 'claude-3-sonnet',
            'fallback_models': ['gpt-4', 'claude-3-haiku'],
            'temperature': 0.1,  # Low temperature for code tasks
            'max_tokens': 4000
        }
        
        # Adjust based on task characteristics
        if task.priority == 'critical':
            preferences['primary_model'] = 'claude-3-opus'  # Use most capable model
            preferences['max_tokens'] = 8000
        
        if 'creative' in task.description.lower() or 'design' in task.description.lower():
            preferences['temperature'] = 0.3  # Higher temperature for creative tasks
        
        return preferences
    
    async def _update_performance_stats(self, execution_time: float, success: bool):
        """
        Update performance statistics
        
        Args:
            execution_time: Time taken to execute the task
            success: Whether the task was successful
        """
        self.performance_stats['total_tasks'] += 1
        self.performance_stats['last_execution_time'] = execution_time
        
        if success:
            self.performance_stats['successful_tasks'] += 1
        else:
            self.performance_stats['failed_tasks'] += 1
        
        # Update average execution time
        total_tasks = self.performance_stats['total_tasks']
        current_avg = self.performance_stats['average_execution_time']
        self.performance_stats['average_execution_time'] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get current performance statistics
        
        Returns:
            Dict: Performance statistics
        """
        return self.performance_stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the engine
        
        Returns:
            Dict: Health status information
        """
        try:
            # Check Trae client health
            trae_health = await self.trae_client.health_check()
            
            # Check configuration manager
            config_health = await self.config_manager.health_check()
            
            # Overall health status
            overall_health = (
                self.is_initialized and 
                self.is_healthy and 
                trae_health and 
                config_health
            )
            
            return {
                'status': 'healthy' if overall_health else 'unhealthy',
                'initialized': self.is_initialized,
                'engine_healthy': self.is_healthy,
                'trae_client_healthy': trae_health,
                'config_manager_healthy': config_health,
                'performance_stats': await self.get_performance_stats(),
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def shutdown(self):
        """
        Gracefully shutdown the engine
        """
        try:
            self.logger.info("Shutting down Trae Agent Engine...")
            
            # Shutdown components
            await self.trae_client.shutdown()
            await self.config_manager.shutdown()
            
            self.is_initialized = False
            self.is_healthy = False
            
            self.logger.info("Trae Agent Engine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")

