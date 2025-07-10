"""
Trae Config Manager - Configuration Management for Trae Agent

This module provides comprehensive configuration management for Trae Agent,
including dynamic configuration optimization, model selection, and performance tuning.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum


class ModelType(Enum):
    """Available model types for Trae Agent"""
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    temperature: float
    max_tokens: int
    cost_per_token: float
    capabilities: List[str]
    performance_score: float
    availability: bool = True


@dataclass
class TaskProfile:
    """Profile for task-specific configuration"""
    task_type: str
    complexity: TaskComplexity
    estimated_tokens: int
    priority: str
    requires_accuracy: bool
    requires_speed: bool
    budget_limit: Optional[float] = None


@dataclass
class OptimalConfig:
    """Optimal configuration for a task"""
    model: str
    temperature: float
    max_tokens: int
    tools: List[str]
    timeout: int
    working_directory: str
    debug: bool
    confidence_score: float
    reasoning: str


class TraeConfigManager:
    """
    Trae Agent Configuration Manager
    
    Manages configuration optimization, model selection, and performance tuning
    for Trae Agent based on task characteristics and historical performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Trae Config Manager
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Configuration paths
        self.config_dir = self.config.get('config_dir', os.path.expanduser('~/.powerautomation/trae_config'))
        self.models_config_file = os.path.join(self.config_dir, 'models.json')
        self.performance_history_file = os.path.join(self.config_dir, 'performance_history.json')
        self.user_preferences_file = os.path.join(self.config_dir, 'user_preferences.json')
        
        # Default configurations
        self.default_models = self._initialize_default_models()
        self.default_tools = ['file_editor', 'sequential_thinking']
        self.default_timeout = 300
        
        # Performance tracking
        self.performance_history = {}
        self.user_preferences = {}
        
        # Manager state
        self.is_initialized = False
        
        self.logger.info("TraeConfigManager initialized")
    
    async def load_config(self) -> bool:
        """
        Load configuration from files
        
        Returns:
            bool: True if loading successful, False otherwise
        """
        try:
            self.logger.info("Loading Trae Agent configuration...")
            
            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)
            
            # Load models configuration
            await self._load_models_config()
            
            # Load performance history
            await self._load_performance_history()
            
            # Load user preferences
            await self._load_user_preferences()
            
            self.is_initialized = True
            self.logger.info("Trae Agent configuration loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load Trae Agent configuration: {str(e)}")
            self.is_initialized = False
            return False
    
    async def get_optimal_config(self, task: Any) -> OptimalConfig:
        """
        Get optimal configuration for a task
        
        Args:
            task: Task to get configuration for
            
        Returns:
            OptimalConfig: Optimal configuration for the task
        """
        try:
            self.logger.info(f"Getting optimal configuration for task")
            
            # Analyze task characteristics
            task_profile = await self._analyze_task_profile(task)
            
            # Select optimal model
            optimal_model = await self._select_optimal_model(task_profile)
            
            # Determine optimal parameters
            optimal_params = await self._determine_optimal_parameters(task_profile, optimal_model)
            
            # Select optimal tools
            optimal_tools = await self._select_optimal_tools(task_profile)
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(task_profile, optimal_model)
            
            # Generate reasoning
            reasoning = await self._generate_reasoning(task_profile, optimal_model, optimal_params)
            
            config = OptimalConfig(
                model=optimal_model.name,
                temperature=optimal_params['temperature'],
                max_tokens=optimal_params['max_tokens'],
                tools=optimal_tools,
                timeout=optimal_params['timeout'],
                working_directory=optimal_params['working_directory'],
                debug=optimal_params['debug'],
                confidence_score=confidence_score,
                reasoning=reasoning
            )
            
            # Record configuration decision for learning
            await self._record_configuration_decision(task_profile, config)
            
            self.logger.info(f"Optimal configuration determined with confidence: {confidence_score:.2f}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to get optimal configuration: {str(e)}")
            
            # Return fallback configuration
            return await self._get_fallback_config(task)
    
    async def _analyze_task_profile(self, task: Any) -> TaskProfile:
        """
        Analyze task to create a profile for configuration optimization
        
        Args:
            task: Task to analyze
            
        Returns:
            TaskProfile: Task profile
        """
        # Extract task characteristics
        description = getattr(task, 'description', '')
        context = getattr(task, 'context', {})
        files = getattr(task, 'files', [])
        priority = getattr(task, 'priority', 'normal')
        
        # Determine task type
        task_type = await self._determine_task_type(description, context, files)
        
        # Assess complexity
        complexity = await self._assess_task_complexity(description, context, files)
        
        # Estimate token requirements
        estimated_tokens = await self._estimate_token_requirements(description, context, files)
        
        # Determine requirements
        requires_accuracy = await self._requires_high_accuracy(description, context, priority)
        requires_speed = await self._requires_high_speed(description, context, priority)
        
        # Get budget limit from context
        budget_limit = context.get('budget_limit')
        
        return TaskProfile(
            task_type=task_type,
            complexity=complexity,
            estimated_tokens=estimated_tokens,
            priority=priority,
            requires_accuracy=requires_accuracy,
            requires_speed=requires_speed,
            budget_limit=budget_limit
        )
    
    async def _determine_task_type(self, description: str, context: Dict, files: List[str]) -> str:
        """
        Determine the type of task based on description, context, and files
        
        Args:
            description: Task description
            context: Task context
            files: Task files
            
        Returns:
            str: Task type
        """
        description_lower = description.lower()
        
        # Task type keywords mapping
        type_keywords = {
            'code_analysis': ['analyze', 'analysis', 'examine', 'inspect', 'understand', 'review'],
            'debugging': ['debug', 'bug', 'error', 'fix', 'issue', 'problem', 'troubleshoot'],
            'refactoring': ['refactor', 'improve', 'optimize', 'restructure', 'clean', 'reorganize'],
            'architecture_design': ['design', 'architecture', 'structure', 'pattern', 'framework', 'system'],
            'performance_optimization': ['performance', 'optimize', 'speed', 'efficiency', 'benchmark', 'profile'],
            'security_analysis': ['security', 'vulnerability', 'secure', 'safety', 'protection', 'audit'],
            'testing': ['test', 'testing', 'unit test', 'integration test', 'coverage', 'validation'],
            'documentation': ['document', 'documentation', 'comment', 'explain', 'describe', 'manual']
        }
        
        # Score each task type
        type_scores = {}
        for task_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                type_scores[task_type] = score
        
        # Check file extensions for additional hints
        if files:
            code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb']
            has_code_files = any(any(file.endswith(ext) for ext in code_extensions) for file in files)
            
            if has_code_files and not type_scores:
                return 'code_analysis'  # Default for code files
        
        # Return the highest scoring task type, default to 'code_analysis'
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'code_analysis'
    
    async def _assess_task_complexity(self, description: str, context: Dict, files: List[str]) -> TaskComplexity:
        """
        Assess the complexity of a task
        
        Args:
            description: Task description
            context: Task context
            files: Task files
            
        Returns:
            TaskComplexity: Assessed complexity level
        """
        complexity_score = 0
        
        # Description length and complexity indicators
        description_length = len(description.split())
        if description_length > 100:
            complexity_score += 2
        elif description_length > 50:
            complexity_score += 1
        
        # Complex keywords
        complex_keywords = [
            'complex', 'advanced', 'sophisticated', 'intricate', 'comprehensive',
            'multi-step', 'multi-file', 'large-scale', 'enterprise', 'distributed'
        ]
        complexity_score += sum(1 for keyword in complex_keywords if keyword in description.lower())
        
        # Number of files
        if files:
            file_count = len(files)
            if file_count > 10:
                complexity_score += 3
            elif file_count > 5:
                complexity_score += 2
            elif file_count > 1:
                complexity_score += 1
        
        # Context complexity
        if context:
            if len(context) > 10:
                complexity_score += 2
            elif len(context) > 5:
                complexity_score += 1
        
        # Priority indicators
        priority = context.get('priority', 'normal')
        if priority in ['critical', 'high']:
            complexity_score += 1
        
        # Map score to complexity level
        if complexity_score >= 6:
            return TaskComplexity.CRITICAL
        elif complexity_score >= 4:
            return TaskComplexity.COMPLEX
        elif complexity_score >= 2:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.SIMPLE
    
    async def _estimate_token_requirements(self, description: str, context: Dict, files: List[str]) -> int:
        """
        Estimate token requirements for a task
        
        Args:
            description: Task description
            context: Task context
            files: Task files
            
        Returns:
            int: Estimated token count
        """
        # Base tokens for description
        base_tokens = len(description.split()) * 1.3  # Rough token estimation
        
        # Add tokens for context
        context_tokens = len(str(context)) * 0.3
        
        # Add tokens for files (if they need to be processed)
        file_tokens = 0
        if files:
            # Estimate based on number of files (assuming average file size)
            file_tokens = len(files) * 500  # Average 500 tokens per file
        
        # Add buffer for response
        response_buffer = 1000
        
        total_estimated = int(base_tokens + context_tokens + file_tokens + response_buffer)
        
        # Ensure minimum and maximum bounds
        return max(1000, min(total_estimated, 8000))
    
    async def _requires_high_accuracy(self, description: str, context: Dict, priority: str) -> bool:
        """
        Determine if task requires high accuracy
        
        Args:
            description: Task description
            context: Task context
            priority: Task priority
            
        Returns:
            bool: True if high accuracy required
        """
        accuracy_keywords = [
            'critical', 'production', 'security', 'safety', 'precise', 'exact',
            'accurate', 'correct', 'validate', 'verify', 'audit', 'compliance'
        ]
        
        description_lower = description.lower()
        has_accuracy_keywords = any(keyword in description_lower for keyword in accuracy_keywords)
        
        is_high_priority = priority in ['critical', 'high']
        
        return has_accuracy_keywords or is_high_priority
    
    async def _requires_high_speed(self, description: str, context: Dict, priority: str) -> bool:
        """
        Determine if task requires high speed
        
        Args:
            description: Task description
            context: Task context
            priority: Task priority
            
        Returns:
            bool: True if high speed required
        """
        speed_keywords = [
            'urgent', 'fast', 'quick', 'immediate', 'asap', 'rush',
            'time-sensitive', 'deadline', 'real-time'
        ]
        
        description_lower = description.lower()
        has_speed_keywords = any(keyword in description_lower for keyword in speed_keywords)
        
        has_deadline = 'deadline' in context or 'timeout' in context
        
        return has_speed_keywords or has_deadline
    
    async def _select_optimal_model(self, task_profile: TaskProfile) -> ModelConfig:
        """
        Select the optimal model for a task profile
        
        Args:
            task_profile: Task profile
            
        Returns:
            ModelConfig: Optimal model configuration
        """
        # Get available models
        available_models = [model for model in self.default_models.values() if model.availability]
        
        if not available_models:
            raise Exception("No available models for task execution")
        
        # Score models based on task requirements
        model_scores = {}
        
        for model in available_models:
            score = 0
            
            # Capability matching
            if task_profile.task_type in model.capabilities:
                score += 3
            
            # Performance score
            score += model.performance_score
            
            # Complexity matching
            if task_profile.complexity == TaskComplexity.CRITICAL:
                if 'opus' in model.name.lower():
                    score += 3
                elif 'gpt-4' in model.name.lower():
                    score += 2
            elif task_profile.complexity == TaskComplexity.COMPLEX:
                if 'sonnet' in model.name.lower() or 'gpt-4' in model.name.lower():
                    score += 2
            elif task_profile.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MEDIUM]:
                if 'haiku' in model.name.lower() or 'gpt-3.5' in model.name.lower():
                    score += 2
            
            # Accuracy vs Speed trade-off
            if task_profile.requires_accuracy:
                if 'opus' in model.name.lower() or 'gpt-4' in model.name.lower():
                    score += 2
            
            if task_profile.requires_speed:
                if 'haiku' in model.name.lower() or 'gpt-3.5' in model.name.lower():
                    score += 2
            
            # Budget considerations
            if task_profile.budget_limit:
                estimated_cost = task_profile.estimated_tokens * model.cost_per_token
                if estimated_cost <= task_profile.budget_limit:
                    score += 1
                else:
                    score -= 2  # Penalize expensive models if budget is limited
            
            model_scores[model] = score
        
        # Select model with highest score
        optimal_model = max(model_scores.items(), key=lambda x: x[1])[0]
        
        self.logger.info(f"Selected optimal model: {optimal_model.name} (score: {model_scores[optimal_model]})")
        return optimal_model
    
    async def _determine_optimal_parameters(self, task_profile: TaskProfile, model: ModelConfig) -> Dict[str, Any]:
        """
        Determine optimal parameters for the task and model
        
        Args:
            task_profile: Task profile
            model: Selected model
            
        Returns:
            Dict: Optimal parameters
        """
        # Base parameters from model
        temperature = model.temperature
        max_tokens = min(task_profile.estimated_tokens, model.max_tokens)
        timeout = self.default_timeout
        
        # Adjust temperature based on task requirements
        if task_profile.requires_accuracy:
            temperature = max(0.0, temperature - 0.1)  # Lower temperature for accuracy
        
        if task_profile.task_type in ['debugging', 'security_analysis']:
            temperature = max(0.0, temperature - 0.1)  # Lower temperature for precise tasks
        
        if task_profile.task_type in ['architecture_design', 'documentation']:
            temperature = min(1.0, temperature + 0.1)  # Higher temperature for creative tasks
        
        # Adjust timeout based on complexity
        if task_profile.complexity == TaskComplexity.CRITICAL:
            timeout = int(timeout * 1.5)
        elif task_profile.complexity == TaskComplexity.COMPLEX:
            timeout = int(timeout * 1.2)
        elif task_profile.requires_speed:
            timeout = int(timeout * 0.8)
        
        # Working directory
        working_directory = self.config.get('working_directory', '/tmp/trae_tasks')
        
        # Debug mode
        debug = task_profile.complexity in [TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]
        
        return {
            'temperature': round(temperature, 2),
            'max_tokens': max_tokens,
            'timeout': timeout,
            'working_directory': working_directory,
            'debug': debug
        }
    
    async def _select_optimal_tools(self, task_profile: TaskProfile) -> List[str]:
        """
        Select optimal tools for the task
        
        Args:
            task_profile: Task profile
            
        Returns:
            List[str]: Optimal tools
        """
        # Base tools
        tools = ['sequential_thinking']
        
        # Task-specific tools
        task_tool_mapping = {
            'code_analysis': ['file_editor', 'sequential_thinking'],
            'debugging': ['file_editor', 'bash_executor', 'trajectory_recorder'],
            'refactoring': ['file_editor', 'sequential_thinking'],
            'architecture_design': ['sequential_thinking', 'file_editor'],
            'performance_optimization': ['file_editor', 'bash_executor', 'trajectory_recorder'],
            'security_analysis': ['file_editor', 'sequential_thinking'],
            'testing': ['file_editor', 'bash_executor'],
            'documentation': ['file_editor', 'sequential_thinking']
        }
        
        task_tools = task_tool_mapping.get(task_profile.task_type, ['file_editor', 'sequential_thinking'])
        tools.extend(task_tools)
        
        # Add tools based on complexity
        if task_profile.complexity in [TaskComplexity.COMPLEX, TaskComplexity.CRITICAL]:
            tools.append('trajectory_recorder')
        
        # Remove duplicates and return
        return list(set(tools))
    
    async def _calculate_confidence_score(self, task_profile: TaskProfile, model: ModelConfig) -> float:
        """
        Calculate confidence score for the configuration
        
        Args:
            task_profile: Task profile
            model: Selected model
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Model capability match
        if task_profile.task_type in model.capabilities:
            confidence += 0.2
        
        # Model performance score
        confidence += model.performance_score * 0.2
        
        # Complexity match
        if task_profile.complexity == TaskComplexity.SIMPLE:
            confidence += 0.1
        elif task_profile.complexity == TaskComplexity.CRITICAL and 'opus' in model.name.lower():
            confidence += 0.2
        
        # Historical performance (if available)
        historical_performance = await self._get_historical_performance(task_profile, model)
        if historical_performance:
            confidence += historical_performance * 0.2
        
        return min(1.0, max(0.0, confidence))
    
    async def _generate_reasoning(self, task_profile: TaskProfile, model: ModelConfig, params: Dict) -> str:
        """
        Generate reasoning for the configuration choice
        
        Args:
            task_profile: Task profile
            model: Selected model
            params: Selected parameters
            
        Returns:
            str: Reasoning explanation
        """
        reasoning_parts = []
        
        # Model selection reasoning
        reasoning_parts.append(f"Selected {model.name} for {task_profile.task_type} task")
        
        if task_profile.complexity == TaskComplexity.CRITICAL:
            reasoning_parts.append("using high-capability model for critical complexity")
        elif task_profile.requires_accuracy:
            reasoning_parts.append("prioritizing accuracy over speed")
        elif task_profile.requires_speed:
            reasoning_parts.append("optimizing for speed")
        
        # Parameter reasoning
        if params['temperature'] < 0.2:
            reasoning_parts.append("low temperature for precise output")
        elif params['temperature'] > 0.3:
            reasoning_parts.append("higher temperature for creative output")
        
        if params['debug']:
            reasoning_parts.append("debug mode enabled for complex task")
        
        return "; ".join(reasoning_parts)
    
    async def _get_historical_performance(self, task_profile: TaskProfile, model: ModelConfig) -> Optional[float]:
        """
        Get historical performance for similar tasks and model
        
        Args:
            task_profile: Task profile
            model: Model configuration
            
        Returns:
            Optional[float]: Historical performance score (0.0 to 1.0)
        """
        # Implementation would query performance history
        # For now, return None (no historical data)
        return None
    
    async def _record_configuration_decision(self, task_profile: TaskProfile, config: OptimalConfig):
        """
        Record configuration decision for future learning
        
        Args:
            task_profile: Task profile
            config: Configuration decision
        """
        try:
            # Record decision for learning (implementation depends on storage strategy)
            decision_record = {
                'timestamp': time.time(),
                'task_profile': asdict(task_profile),
                'config': asdict(config)
            }
            
            # This would be stored for machine learning purposes
            self.logger.debug(f"Recorded configuration decision: {decision_record}")
            
        except Exception as e:
            self.logger.error(f"Failed to record configuration decision: {str(e)}")
    
    async def _get_fallback_config(self, task: Any) -> OptimalConfig:
        """
        Get fallback configuration when optimization fails
        
        Args:
            task: Original task
            
        Returns:
            OptimalConfig: Fallback configuration
        """
        return OptimalConfig(
            model="claude-3-sonnet-20240229",
            temperature=0.1,
            max_tokens=4000,
            tools=self.default_tools,
            timeout=self.default_timeout,
            working_directory=self.config.get('working_directory', '/tmp/trae_tasks'),
            debug=False,
            confidence_score=0.5,
            reasoning="Fallback configuration due to optimization failure"
        )
    
    def _initialize_default_models(self) -> Dict[str, ModelConfig]:
        """
        Initialize default model configurations
        
        Returns:
            Dict[str, ModelConfig]: Default model configurations
        """
        return {
            'claude-3-opus': ModelConfig(
                name="claude-3-opus-20240229",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.000015,
                capabilities=['code_analysis', 'debugging', 'architecture_design', 'security_analysis'],
                performance_score=0.95,
                availability=True
            ),
            'claude-3-sonnet': ModelConfig(
                name="claude-3-sonnet-20240229",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.000003,
                capabilities=['code_analysis', 'refactoring', 'testing', 'documentation'],
                performance_score=0.85,
                availability=True
            ),
            'claude-3-haiku': ModelConfig(
                name="claude-3-haiku-20240307",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00000025,
                capabilities=['code_analysis', 'documentation', 'testing'],
                performance_score=0.75,
                availability=True
            ),
            'gpt-4': ModelConfig(
                name="gpt-4",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00003,
                capabilities=['code_analysis', 'debugging', 'architecture_design'],
                performance_score=0.90,
                availability=True
            ),
            'gpt-4-turbo': ModelConfig(
                name="gpt-4-turbo-preview",
                temperature=0.1,
                max_tokens=4000,
                cost_per_token=0.00001,
                capabilities=['code_analysis', 'refactoring', 'performance_optimization'],
                performance_score=0.88,
                availability=True
            )
        }
    
    async def _load_models_config(self):
        """Load models configuration from file"""
        try:
            if os.path.exists(self.models_config_file):
                with open(self.models_config_file, 'r') as f:
                    models_data = json.load(f)
                    # Update default models with loaded data
                    # Implementation depends on data format
            else:
                # Save default models configuration
                await self._save_models_config()
        except Exception as e:
            self.logger.error(f"Failed to load models config: {str(e)}")
    
    async def _load_performance_history(self):
        """Load performance history from file"""
        try:
            if os.path.exists(self.performance_history_file):
                with open(self.performance_history_file, 'r') as f:
                    self.performance_history = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load performance history: {str(e)}")
    
    async def _load_user_preferences(self):
        """Load user preferences from file"""
        try:
            if os.path.exists(self.user_preferences_file):
                with open(self.user_preferences_file, 'r') as f:
                    self.user_preferences = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load user preferences: {str(e)}")
    
    async def _save_models_config(self):
        """Save models configuration to file"""
        try:
            models_data = {name: asdict(config) for name, config in self.default_models.items()}
            with open(self.models_config_file, 'w') as f:
                json.dump(models_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save models config: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Perform health check on the config manager
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Check if initialized
            if not self.is_initialized:
                return False
            
            # Check if config directory exists
            if not os.path.exists(self.config_dir):
                return False
            
            # Check if default models are available
            if not self.default_models:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Config manager health check failed: {str(e)}")
            return False
    
    async def shutdown(self):
        """
        Gracefully shutdown the config manager
        """
        try:
            self.logger.info("Shutting down Trae Config Manager...")
            
            # Save current state if needed
            await self._save_models_config()
            
            self.is_initialized = False
            
            self.logger.info("Trae Config Manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during config manager shutdown: {str(e)}")

