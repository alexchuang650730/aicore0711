"""
Intelligent Task Router - Smart Task Routing for PowerAutomation 4.0

This module provides intelligent task routing capabilities, determining the optimal
processing engine (Trae Agent vs PowerAutomation native) for each task based on
task characteristics, performance metrics, and system state.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ProcessingEngine(Enum):
    """Available processing engines"""
    TRAE_AGENT = "trae_agent"
    POWERAUTOMATION_NATIVE = "powerautomation_native"
    HYBRID = "hybrid"
    AUTO = "auto"


class TaskCategory(Enum):
    """Task categories for routing decisions"""
    SOFTWARE_ENGINEERING = "software_engineering"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    AI_INTEGRATION = "ai_integration"
    SYSTEM_MANAGEMENT = "system_management"
    GENERAL = "general"


class RoutingDecision(Enum):
    """Routing decision types"""
    ROUTE_TO_TRAE = "route_to_trae"
    ROUTE_TO_NATIVE = "route_to_native"
    ROUTE_TO_HYBRID = "route_to_hybrid"
    ROUTE_TO_FALLBACK = "route_to_fallback"


@dataclass
class TaskProfile:
    """Comprehensive task profile for routing decisions"""
    task_id: str
    description: str
    category: TaskCategory
    complexity_score: float
    estimated_duration: float
    priority: str
    files: List[str]
    context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    historical_performance: Dict[str, Any]


@dataclass
class EngineCapability:
    """Engine capability assessment"""
    engine: ProcessingEngine
    suitability_score: float
    confidence_level: float
    estimated_performance: Dict[str, float]
    resource_requirements: Dict[str, Any]
    limitations: List[str]


@dataclass
class RoutingResult:
    """Result of routing decision"""
    decision: RoutingDecision
    primary_engine: ProcessingEngine
    secondary_engine: Optional[ProcessingEngine]
    confidence_score: float
    reasoning: str
    estimated_metrics: Dict[str, float]
    fallback_strategy: Optional[str]
    routing_metadata: Dict[str, Any]


class IntelligentTaskRouter:
    """
    Intelligent Task Router
    
    Provides smart task routing capabilities for PowerAutomation 4.0,
    determining the optimal processing engine for each task based on
    comprehensive analysis of task characteristics and system state.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Intelligent Task Router
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Routing configuration
        self.enable_hybrid_routing = self.config.get('enable_hybrid_routing', True)
        self.enable_learning = self.config.get('enable_learning', True)
        self.enable_performance_tracking = self.config.get('enable_performance_tracking', True)
        
        # Engine capabilities
        self.engine_capabilities = self._initialize_engine_capabilities()
        
        # Routing rules and weights
        self.routing_rules = self._initialize_routing_rules()
        self.decision_weights = self._initialize_decision_weights()
        
        # Performance tracking
        self.routing_history = []
        self.engine_performance = {}
        self.routing_stats = {
            'total_routes': 0,
            'routes_by_engine': {},
            'routes_by_category': {},
            'average_confidence': 0.0,
            'successful_routes': 0,
            'failed_routes': 0
        }
        
        # Learning system
        self.learning_data = {}
        self.pattern_recognition = {}
        
        self.logger.info("IntelligentTaskRouter initialized")
    
    async def route_task(self, task: Any) -> RoutingResult:
        """
        Route task to optimal processing engine
        
        Args:
            task: Task to route
            
        Returns:
            RoutingResult: Routing decision and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Routing task: {getattr(task, 'id', 'unknown')}")
            
            # Create task profile
            task_profile = await self._create_task_profile(task)
            
            # Assess engine capabilities for this task
            engine_assessments = await self._assess_engine_capabilities(task_profile)
            
            # Make routing decision
            routing_decision = await self._make_routing_decision(task_profile, engine_assessments)
            
            # Validate routing decision
            validated_decision = await self._validate_routing_decision(routing_decision, task_profile)
            
            # Record routing decision
            routing_time = time.time() - start_time
            await self._record_routing_decision(validated_decision, task_profile, routing_time)
            
            # Update statistics
            await self._update_routing_stats(validated_decision, task_profile)
            
            self.logger.info(f"Task routed to {validated_decision.primary_engine.value} in {routing_time:.2f}s")
            return validated_decision
            
        except Exception as e:
            routing_time = time.time() - start_time
            self.logger.error(f"Task routing failed: {str(e)}")
            
            # Return fallback routing decision
            return await self._create_fallback_routing_decision(task, str(e))
    
    async def _create_task_profile(self, task: Any) -> TaskProfile:
        """
        Create comprehensive task profile for routing analysis
        
        Args:
            task: Task to profile
            
        Returns:
            TaskProfile: Comprehensive task profile
        """
        # Extract basic task information
        task_id = getattr(task, 'id', f"task_{int(time.time())}")
        description = getattr(task, 'description', '')
        files = getattr(task, 'files', [])
        context = getattr(task, 'context', {})
        priority = getattr(task, 'priority', 'normal')
        
        # Determine task category
        category = await self._determine_task_category(description, files, context)
        
        # Calculate complexity score
        complexity_score = await self._calculate_complexity_score(description, files, context)
        
        # Estimate duration
        estimated_duration = await self._estimate_task_duration(description, files, context, complexity_score)
        
        # Get user preferences
        user_preferences = context.get('user_preferences', {})
        
        # Get historical performance data
        historical_performance = await self._get_historical_performance(task_id, category, description)
        
        return TaskProfile(
            task_id=task_id,
            description=description,
            category=category,
            complexity_score=complexity_score,
            estimated_duration=estimated_duration,
            priority=priority,
            files=files,
            context=context,
            user_preferences=user_preferences,
            historical_performance=historical_performance
        )
    
    async def _determine_task_category(self, description: str, files: List[str], context: Dict[str, Any]) -> TaskCategory:
        """
        Determine task category based on description, files, and context
        
        Args:
            description: Task description
            files: Task files
            context: Task context
            
        Returns:
            TaskCategory: Determined category
        """
        description_lower = description.lower()
        
        # Software engineering keywords
        se_keywords = [
            'code', 'programming', 'debug', 'refactor', 'analyze', 'architecture',
            'software', 'development', 'testing', 'review', 'implementation',
            'algorithm', 'function', 'class', 'method', 'variable', 'bug'
        ]
        
        # Data analysis keywords
        da_keywords = [
            'data', 'analysis', 'statistics', 'visualization', 'chart', 'graph',
            'dataset', 'csv', 'excel', 'database', 'query', 'report', 'metrics'
        ]
        
        # Automation keywords
        auto_keywords = [
            'automate', 'automation', 'workflow', 'process', 'batch', 'schedule',
            'trigger', 'action', 'integration', 'api', 'webhook', 'pipeline'
        ]
        
        # AI integration keywords
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 'model',
            'neural', 'training', 'prediction', 'classification', 'nlp', 'llm'
        ]
        
        # System management keywords
        sys_keywords = [
            'system', 'server', 'deployment', 'configuration', 'monitoring',
            'performance', 'security', 'backup', 'maintenance', 'infrastructure'
        ]
        
        # Score each category
        category_scores = {
            TaskCategory.SOFTWARE_ENGINEERING: sum(1 for kw in se_keywords if kw in description_lower),
            TaskCategory.DATA_ANALYSIS: sum(1 for kw in da_keywords if kw in description_lower),
            TaskCategory.AUTOMATION: sum(1 for kw in auto_keywords if kw in description_lower),
            TaskCategory.AI_INTEGRATION: sum(1 for kw in ai_keywords if kw in description_lower),
            TaskCategory.SYSTEM_MANAGEMENT: sum(1 for kw in sys_keywords if kw in description_lower)
        }
        
        # Check file extensions for additional hints
        if files:
            code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb']
            data_extensions = ['.csv', '.xlsx', '.json', '.xml', '.sql']
            config_extensions = ['.yaml', '.yml', '.toml', '.ini', '.conf']
            
            if any(any(file.endswith(ext) for ext in code_extensions) for file in files):
                category_scores[TaskCategory.SOFTWARE_ENGINEERING] += 3
            
            if any(any(file.endswith(ext) for ext in data_extensions) for file in files):
                category_scores[TaskCategory.DATA_ANALYSIS] += 3
            
            if any(any(file.endswith(ext) for ext in config_extensions) for file in files):
                category_scores[TaskCategory.SYSTEM_MANAGEMENT] += 2
        
        # Check context for category hints
        if 'automation' in context or 'workflow' in context:
            category_scores[TaskCategory.AUTOMATION] += 2
        
        if 'ai_model' in context or 'ml_task' in context:
            category_scores[TaskCategory.AI_INTEGRATION] += 2
        
        # Return highest scoring category, default to GENERAL
        if category_scores:
            max_score = max(category_scores.values())
            if max_score > 0:
                return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return TaskCategory.GENERAL
    
    async def _calculate_complexity_score(self, description: str, files: List[str], context: Dict[str, Any]) -> float:
        """
        Calculate task complexity score (0.0 to 1.0)
        
        Args:
            description: Task description
            files: Task files
            context: Task context
            
        Returns:
            float: Complexity score
        """
        complexity_score = 0.0
        
        # Description length and complexity
        word_count = len(description.split())
        if word_count > 100:
            complexity_score += 0.3
        elif word_count > 50:
            complexity_score += 0.2
        elif word_count > 20:
            complexity_score += 0.1
        
        # Complex keywords
        complex_keywords = [
            'complex', 'advanced', 'sophisticated', 'comprehensive', 'multi-step',
            'large-scale', 'enterprise', 'distributed', 'optimization', 'algorithm'
        ]
        complexity_score += min(0.3, len([kw for kw in complex_keywords if kw in description.lower()]) * 0.1)
        
        # File count and types
        if files:
            file_count = len(files)
            if file_count > 20:
                complexity_score += 0.3
            elif file_count > 10:
                complexity_score += 0.2
            elif file_count > 5:
                complexity_score += 0.1
            
            # Check for complex file types
            complex_extensions = ['.cpp', '.java', '.scala', '.hs', '.rs']
            if any(any(file.endswith(ext) for ext in complex_extensions) for file in files):
                complexity_score += 0.1
        
        # Context complexity
        if context:
            context_size = len(str(context))
            if context_size > 1000:
                complexity_score += 0.2
            elif context_size > 500:
                complexity_score += 0.1
            
            # Check for complex context indicators
            if any(key in context for key in ['dependencies', 'constraints', 'requirements']):
                complexity_score += 0.1
        
        return min(1.0, complexity_score)
    
    async def _estimate_task_duration(self, description: str, files: List[str], context: Dict[str, Any], complexity_score: float) -> float:
        """
        Estimate task duration in minutes
        
        Args:
            description: Task description
            files: Task files
            context: Task context
            complexity_score: Task complexity score
            
        Returns:
            float: Estimated duration in minutes
        """
        # Base duration based on description length
        word_count = len(description.split())
        base_duration = min(60, word_count * 0.5)  # 0.5 minutes per word, max 60 minutes
        
        # Adjust for complexity
        complexity_multiplier = 1 + (complexity_score * 2)  # 1x to 3x multiplier
        
        # Adjust for file count
        file_multiplier = 1 + (len(files) * 0.1) if files else 1
        
        # Adjust for context
        context_multiplier = 1 + (len(str(context)) / 10000) if context else 1
        
        estimated_duration = base_duration * complexity_multiplier * file_multiplier * context_multiplier
        
        # Apply reasonable bounds
        return max(1.0, min(480.0, estimated_duration))  # 1 minute to 8 hours
    
    async def _get_historical_performance(self, task_id: str, category: TaskCategory, description: str) -> Dict[str, Any]:
        """
        Get historical performance data for similar tasks
        
        Args:
            task_id: Task ID
            category: Task category
            description: Task description
            
        Returns:
            Dict: Historical performance data
        """
        # In a real implementation, this would query historical data
        # For now, return empty dict
        return {}
    
    async def _assess_engine_capabilities(self, task_profile: TaskProfile) -> List[EngineCapability]:
        """
        Assess capabilities of each engine for the given task
        
        Args:
            task_profile: Task profile
            
        Returns:
            List[EngineCapability]: Engine capability assessments
        """
        assessments = []
        
        # Assess Trae Agent capability
        trae_assessment = await self._assess_trae_agent_capability(task_profile)
        assessments.append(trae_assessment)
        
        # Assess PowerAutomation Native capability
        native_assessment = await self._assess_native_capability(task_profile)
        assessments.append(native_assessment)
        
        # Assess Hybrid capability if enabled
        if self.enable_hybrid_routing:
            hybrid_assessment = await self._assess_hybrid_capability(task_profile)
            assessments.append(hybrid_assessment)
        
        return assessments
    
    async def _assess_trae_agent_capability(self, task_profile: TaskProfile) -> EngineCapability:
        """
        Assess Trae Agent capability for the task
        
        Args:
            task_profile: Task profile
            
        Returns:
            EngineCapability: Trae Agent capability assessment
        """
        suitability_score = 0.0
        confidence_level = 0.5
        limitations = []
        
        # Category-based suitability
        if task_profile.category == TaskCategory.SOFTWARE_ENGINEERING:
            suitability_score += 0.9  # Trae Agent excels at software engineering
            confidence_level += 0.3
        elif task_profile.category == TaskCategory.AI_INTEGRATION:
            suitability_score += 0.7
            confidence_level += 0.2
        elif task_profile.category == TaskCategory.DATA_ANALYSIS:
            suitability_score += 0.6
            confidence_level += 0.1
        elif task_profile.category == TaskCategory.AUTOMATION:
            suitability_score += 0.4
            limitations.append("Limited automation workflow capabilities")
        elif task_profile.category == TaskCategory.SYSTEM_MANAGEMENT:
            suitability_score += 0.3
            limitations.append("Limited system management capabilities")
        else:  # GENERAL
            suitability_score += 0.5
        
        # Complexity adjustment
        if task_profile.complexity_score > 0.7:
            suitability_score += 0.2  # Trae Agent handles complex tasks well
            confidence_level += 0.1
        elif task_profile.complexity_score < 0.3:
            suitability_score -= 0.1  # Might be overkill for simple tasks
        
        # File type analysis
        if task_profile.files:
            code_files = [f for f in task_profile.files if any(f.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.cpp'])]
            if code_files:
                suitability_score += 0.2
                confidence_level += 0.1
        
        # Duration considerations
        if task_profile.estimated_duration > 60:  # > 1 hour
            suitability_score += 0.1  # Good for long-running tasks
        elif task_profile.estimated_duration < 5:  # < 5 minutes
            suitability_score -= 0.2  # Overhead might not be worth it
            limitations.append("High overhead for very short tasks")
        
        # Priority considerations
        if task_profile.priority in ['critical', 'high']:
            confidence_level += 0.1
        
        # Normalize scores
        suitability_score = max(0.0, min(1.0, suitability_score))
        confidence_level = max(0.0, min(1.0, confidence_level))
        
        return EngineCapability(
            engine=ProcessingEngine.TRAE_AGENT,
            suitability_score=suitability_score,
            confidence_level=confidence_level,
            estimated_performance={
                'accuracy': 0.85 + (task_profile.complexity_score * 0.1),
                'speed': 0.7 - (task_profile.complexity_score * 0.2),
                'resource_efficiency': 0.6,
                'reliability': 0.8
            },
            resource_requirements={
                'cpu_intensive': True,
                'memory_usage': 'high',
                'network_required': True,
                'estimated_cost': task_profile.estimated_duration * 0.05  # $0.05 per minute
            },
            limitations=limitations
        )
    
    async def _assess_native_capability(self, task_profile: TaskProfile) -> EngineCapability:
        """
        Assess PowerAutomation Native capability for the task
        
        Args:
            task_profile: Task profile
            
        Returns:
            EngineCapability: Native capability assessment
        """
        suitability_score = 0.0
        confidence_level = 0.7  # Generally high confidence in native capabilities
        limitations = []
        
        # Category-based suitability
        if task_profile.category == TaskCategory.AUTOMATION:
            suitability_score += 0.9  # Native excels at automation
            confidence_level += 0.2
        elif task_profile.category == TaskCategory.SYSTEM_MANAGEMENT:
            suitability_score += 0.8
            confidence_level += 0.2
        elif task_profile.category == TaskCategory.DATA_ANALYSIS:
            suitability_score += 0.7
            confidence_level += 0.1
        elif task_profile.category == TaskCategory.AI_INTEGRATION:
            suitability_score += 0.6
        elif task_profile.category == TaskCategory.SOFTWARE_ENGINEERING:
            suitability_score += 0.4
            limitations.append("Limited advanced code analysis capabilities")
        else:  # GENERAL
            suitability_score += 0.6
        
        # Complexity adjustment
        if task_profile.complexity_score < 0.5:
            suitability_score += 0.2  # Native good for simpler tasks
            confidence_level += 0.1
        elif task_profile.complexity_score > 0.8:
            suitability_score -= 0.2  # May struggle with very complex tasks
            limitations.append("May struggle with highly complex tasks")
        
        # Duration considerations
        if task_profile.estimated_duration < 30:  # < 30 minutes
            suitability_score += 0.2  # Good for quick tasks
        elif task_profile.estimated_duration > 120:  # > 2 hours
            suitability_score -= 0.1
        
        # File considerations
        if len(task_profile.files) > 50:
            limitations.append("May have performance issues with many files")
            suitability_score -= 0.1
        
        # Normalize scores
        suitability_score = max(0.0, min(1.0, suitability_score))
        confidence_level = max(0.0, min(1.0, confidence_level))
        
        return EngineCapability(
            engine=ProcessingEngine.POWERAUTOMATION_NATIVE,
            suitability_score=suitability_score,
            confidence_level=confidence_level,
            estimated_performance={
                'accuracy': 0.75 + (0.1 if task_profile.complexity_score < 0.5 else 0),
                'speed': 0.9 - (task_profile.complexity_score * 0.1),
                'resource_efficiency': 0.9,
                'reliability': 0.9
            },
            resource_requirements={
                'cpu_intensive': False,
                'memory_usage': 'medium',
                'network_required': False,
                'estimated_cost': task_profile.estimated_duration * 0.01  # $0.01 per minute
            },
            limitations=limitations
        )
    
    async def _assess_hybrid_capability(self, task_profile: TaskProfile) -> EngineCapability:
        """
        Assess Hybrid processing capability for the task
        
        Args:
            task_profile: Task profile
            
        Returns:
            EngineCapability: Hybrid capability assessment
        """
        suitability_score = 0.0
        confidence_level = 0.6
        limitations = []
        
        # Hybrid is good for complex, multi-faceted tasks
        if task_profile.complexity_score > 0.6:
            suitability_score += 0.7
            confidence_level += 0.2
        
        # Good for tasks that span multiple categories
        description_lower = task_profile.description.lower()
        category_indicators = 0
        
        if any(kw in description_lower for kw in ['code', 'programming', 'software']):
            category_indicators += 1
        if any(kw in description_lower for kw in ['data', 'analysis', 'report']):
            category_indicators += 1
        if any(kw in description_lower for kw in ['automate', 'workflow', 'process']):
            category_indicators += 1
        
        if category_indicators >= 2:
            suitability_score += 0.6
            confidence_level += 0.1
        
        # Duration considerations
        if task_profile.estimated_duration > 30:  # > 30 minutes
            suitability_score += 0.2  # Hybrid coordination overhead is worth it
        else:
            limitations.append("Coordination overhead may not be worth it for short tasks")
            suitability_score -= 0.3
        
        # File diversity
        if task_profile.files:
            file_types = set()
            for file in task_profile.files:
                if '.' in file:
                    file_types.add(file.split('.')[-1])
            
            if len(file_types) > 3:
                suitability_score += 0.2  # Good for diverse file types
        
        # Normalize scores
        suitability_score = max(0.0, min(1.0, suitability_score))
        confidence_level = max(0.0, min(1.0, confidence_level))
        
        return EngineCapability(
            engine=ProcessingEngine.HYBRID,
            suitability_score=suitability_score,
            confidence_level=confidence_level,
            estimated_performance={
                'accuracy': 0.9,  # Best of both engines
                'speed': 0.6,    # Slower due to coordination
                'resource_efficiency': 0.5,  # Higher resource usage
                'reliability': 0.85
            },
            resource_requirements={
                'cpu_intensive': True,
                'memory_usage': 'high',
                'network_required': True,
                'estimated_cost': task_profile.estimated_duration * 0.08  # $0.08 per minute
            },
            limitations=limitations + ["Higher complexity and resource usage", "Coordination overhead"]
        )
    
    async def _make_routing_decision(self, task_profile: TaskProfile, engine_assessments: List[EngineCapability]) -> RoutingResult:
        """
        Make routing decision based on task profile and engine assessments
        
        Args:
            task_profile: Task profile
            engine_assessments: Engine capability assessments
            
        Returns:
            RoutingResult: Routing decision
        """
        # Calculate weighted scores for each engine
        engine_scores = {}
        
        for assessment in engine_assessments:
            # Base score from suitability and confidence
            base_score = (assessment.suitability_score * 0.6) + (assessment.confidence_level * 0.4)
            
            # Apply decision weights
            weighted_score = base_score
            
            # Performance considerations
            performance = assessment.estimated_performance
            weighted_score += performance['accuracy'] * self.decision_weights['accuracy']
            weighted_score += performance['speed'] * self.decision_weights['speed']
            weighted_score += performance['resource_efficiency'] * self.decision_weights['resource_efficiency']
            weighted_score += performance['reliability'] * self.decision_weights['reliability']
            
            # Cost considerations
            cost_factor = 1.0 / (1.0 + assessment.resource_requirements['estimated_cost'])
            weighted_score += cost_factor * self.decision_weights['cost']
            
            # User preferences
            user_prefs = task_profile.user_preferences
            if 'preferred_engine' in user_prefs:
                if user_prefs['preferred_engine'] == assessment.engine.value:
                    weighted_score += 0.2
            
            if 'prefer_speed' in user_prefs and user_prefs['prefer_speed']:
                weighted_score += performance['speed'] * 0.2
            
            if 'prefer_accuracy' in user_prefs and user_prefs['prefer_accuracy']:
                weighted_score += performance['accuracy'] * 0.2
            
            engine_scores[assessment.engine] = {
                'score': weighted_score,
                'assessment': assessment
            }
        
        # Select best engine
        best_engine_data = max(engine_scores.items(), key=lambda x: x[1]['score'])
        best_engine = best_engine_data[0]
        best_assessment = best_engine_data[1]['assessment']
        
        # Determine routing decision type
        if best_engine == ProcessingEngine.TRAE_AGENT:
            decision = RoutingDecision.ROUTE_TO_TRAE
        elif best_engine == ProcessingEngine.POWERAUTOMATION_NATIVE:
            decision = RoutingDecision.ROUTE_TO_NATIVE
        elif best_engine == ProcessingEngine.HYBRID:
            decision = RoutingDecision.ROUTE_TO_HYBRID
        else:
            decision = RoutingDecision.ROUTE_TO_FALLBACK
        
        # Determine secondary engine for fallback
        remaining_engines = [data for engine, data in engine_scores.items() if engine != best_engine]
        secondary_engine = None
        if remaining_engines:
            secondary_engine_data = max(remaining_engines, key=lambda x: x['score'])
            secondary_engine = secondary_engine_data['assessment'].engine
        
        # Calculate confidence score
        confidence_score = best_assessment.confidence_level
        
        # Generate reasoning
        reasoning = await self._generate_routing_reasoning(
            task_profile, best_assessment, engine_scores
        )
        
        # Estimate metrics
        estimated_metrics = {
            'estimated_duration': task_profile.estimated_duration,
            'estimated_accuracy': best_assessment.estimated_performance['accuracy'],
            'estimated_cost': best_assessment.resource_requirements['estimated_cost'],
            'confidence': confidence_score
        }
        
        # Determine fallback strategy
        fallback_strategy = await self._determine_fallback_strategy(best_engine, secondary_engine)
        
        return RoutingResult(
            decision=decision,
            primary_engine=best_engine,
            secondary_engine=secondary_engine,
            confidence_score=confidence_score,
            reasoning=reasoning,
            estimated_metrics=estimated_metrics,
            fallback_strategy=fallback_strategy,
            routing_metadata={
                'task_category': task_profile.category.value,
                'complexity_score': task_profile.complexity_score,
                'engine_scores': {engine.value: data['score'] for engine, data in engine_scores.items()},
                'routing_timestamp': time.time()
            }
        )
    
    async def _generate_routing_reasoning(
        self, 
        task_profile: TaskProfile, 
        best_assessment: EngineCapability, 
        engine_scores: Dict[ProcessingEngine, Dict[str, Any]]
    ) -> str:
        """
        Generate human-readable reasoning for routing decision
        
        Args:
            task_profile: Task profile
            best_assessment: Best engine assessment
            engine_scores: All engine scores
            
        Returns:
            str: Routing reasoning
        """
        reasoning_parts = []
        
        # Primary reason
        reasoning_parts.append(f"Selected {best_assessment.engine.value} for {task_profile.category.value} task")
        
        # Suitability reason
        if best_assessment.suitability_score > 0.8:
            reasoning_parts.append("high suitability score")
        elif best_assessment.suitability_score > 0.6:
            reasoning_parts.append("good suitability score")
        
        # Complexity consideration
        if task_profile.complexity_score > 0.7:
            reasoning_parts.append("complex task requiring advanced capabilities")
        elif task_profile.complexity_score < 0.3:
            reasoning_parts.append("simple task suitable for efficient processing")
        
        # Performance consideration
        performance = best_assessment.estimated_performance
        if performance['accuracy'] > 0.8:
            reasoning_parts.append("high accuracy expected")
        if performance['speed'] > 0.8:
            reasoning_parts.append("fast processing expected")
        
        # Cost consideration
        cost = best_assessment.resource_requirements['estimated_cost']
        if cost < task_profile.estimated_duration * 0.02:
            reasoning_parts.append("cost-effective option")
        
        return "; ".join(reasoning_parts)
    
    async def _determine_fallback_strategy(
        self, 
        primary_engine: ProcessingEngine, 
        secondary_engine: Optional[ProcessingEngine]
    ) -> Optional[str]:
        """
        Determine fallback strategy
        
        Args:
            primary_engine: Primary engine
            secondary_engine: Secondary engine
            
        Returns:
            Optional[str]: Fallback strategy
        """
        if secondary_engine:
            return f"fallback_to_{secondary_engine.value}"
        elif primary_engine == ProcessingEngine.TRAE_AGENT:
            return "fallback_to_powerautomation_native"
        elif primary_engine == ProcessingEngine.POWERAUTOMATION_NATIVE:
            return "fallback_to_trae_agent"
        else:
            return "fallback_to_powerautomation_native"
    
    async def _validate_routing_decision(self, routing_result: RoutingResult, task_profile: TaskProfile) -> RoutingResult:
        """
        Validate and potentially adjust routing decision
        
        Args:
            routing_result: Initial routing result
            task_profile: Task profile
            
        Returns:
            RoutingResult: Validated routing result
        """
        # Check for system constraints
        if routing_result.primary_engine == ProcessingEngine.TRAE_AGENT:
            # Check if Trae Agent is available
            if not await self._is_trae_agent_available():
                self.logger.warning("Trae Agent not available, falling back to native")
                routing_result.primary_engine = ProcessingEngine.POWERAUTOMATION_NATIVE
                routing_result.decision = RoutingDecision.ROUTE_TO_NATIVE
                routing_result.reasoning += "; fallback due to Trae Agent unavailability"
        
        # Check resource constraints
        if routing_result.primary_engine == ProcessingEngine.HYBRID:
            # Check if system can handle hybrid processing
            if not await self._can_handle_hybrid_processing():
                self.logger.warning("System cannot handle hybrid processing, using primary engine")
                routing_result.primary_engine = ProcessingEngine.TRAE_AGENT
                routing_result.decision = RoutingDecision.ROUTE_TO_TRAE
                routing_result.reasoning += "; simplified to single engine due to resource constraints"
        
        # Check confidence threshold
        if routing_result.confidence_score < 0.5:
            self.logger.warning(f"Low confidence routing decision: {routing_result.confidence_score}")
            # Could implement additional validation or fallback logic here
        
        return routing_result
    
    async def _is_trae_agent_available(self) -> bool:
        """Check if Trae Agent is available"""
        # In real implementation, this would check Trae Agent health
        return True
    
    async def _can_handle_hybrid_processing(self) -> bool:
        """Check if system can handle hybrid processing"""
        # In real implementation, this would check system resources
        return True
    
    async def _create_fallback_routing_decision(self, task: Any, error_message: str) -> RoutingResult:
        """
        Create fallback routing decision when routing fails
        
        Args:
            task: Original task
            error_message: Error message
            
        Returns:
            RoutingResult: Fallback routing decision
        """
        return RoutingResult(
            decision=RoutingDecision.ROUTE_TO_FALLBACK,
            primary_engine=ProcessingEngine.POWERAUTOMATION_NATIVE,
            secondary_engine=None,
            confidence_score=0.3,
            reasoning=f"Fallback routing due to error: {error_message}",
            estimated_metrics={
                'estimated_duration': 30.0,
                'estimated_accuracy': 0.6,
                'estimated_cost': 0.5,
                'confidence': 0.3
            },
            fallback_strategy="emergency_fallback",
            routing_metadata={
                'error': error_message,
                'fallback_timestamp': time.time()
            }
        )
    
    async def _record_routing_decision(self, routing_result: RoutingResult, task_profile: TaskProfile, routing_time: float):
        """Record routing decision for learning and analysis"""
        record = {
            'timestamp': time.time(),
            'task_id': task_profile.task_id,
            'task_category': task_profile.category.value,
            'complexity_score': task_profile.complexity_score,
            'routing_decision': routing_result.decision.value,
            'primary_engine': routing_result.primary_engine.value,
            'confidence_score': routing_result.confidence_score,
            'routing_time': routing_time,
            'estimated_metrics': routing_result.estimated_metrics
        }
        
        # Add to routing history (keep last 1000 records)
        self.routing_history.append(record)
        if len(self.routing_history) > 1000:
            self.routing_history.pop(0)
        
        # Update learning data if enabled
        if self.enable_learning:
            await self._update_learning_data(record, task_profile, routing_result)
    
    async def _update_learning_data(self, record: Dict[str, Any], task_profile: TaskProfile, routing_result: RoutingResult):
        """Update learning data for future routing improvements"""
        # This would implement machine learning logic
        # For now, just track patterns
        pattern_key = f"{task_profile.category.value}_{int(task_profile.complexity_score * 10)}"
        
        if pattern_key not in self.learning_data:
            self.learning_data[pattern_key] = {
                'count': 0,
                'engine_choices': {},
                'average_confidence': 0.0
            }
        
        pattern = self.learning_data[pattern_key]
        pattern['count'] += 1
        
        engine = routing_result.primary_engine.value
        if engine not in pattern['engine_choices']:
            pattern['engine_choices'][engine] = 0
        pattern['engine_choices'][engine] += 1
        
        # Update average confidence
        pattern['average_confidence'] = (
            (pattern['average_confidence'] * (pattern['count'] - 1) + routing_result.confidence_score) / 
            pattern['count']
        )
    
    async def _update_routing_stats(self, routing_result: RoutingResult, task_profile: TaskProfile):
        """Update routing statistics"""
        self.routing_stats['total_routes'] += 1
        
        # Update routes by engine
        engine = routing_result.primary_engine.value
        if engine not in self.routing_stats['routes_by_engine']:
            self.routing_stats['routes_by_engine'][engine] = 0
        self.routing_stats['routes_by_engine'][engine] += 1
        
        # Update routes by category
        category = task_profile.category.value
        if category not in self.routing_stats['routes_by_category']:
            self.routing_stats['routes_by_category'][category] = 0
        self.routing_stats['routes_by_category'][category] += 1
        
        # Update average confidence
        total_routes = self.routing_stats['total_routes']
        current_avg = self.routing_stats['average_confidence']
        self.routing_stats['average_confidence'] = (
            (current_avg * (total_routes - 1) + routing_result.confidence_score) / total_routes
        )
    
    def _initialize_engine_capabilities(self) -> Dict[ProcessingEngine, Dict[str, Any]]:
        """Initialize engine capabilities configuration"""
        return {
            ProcessingEngine.TRAE_AGENT: {
                'strengths': ['software_engineering', 'complex_analysis', 'code_generation'],
                'weaknesses': ['simple_automation', 'system_management'],
                'resource_intensive': True,
                'cost_per_minute': 0.05
            },
            ProcessingEngine.POWERAUTOMATION_NATIVE: {
                'strengths': ['automation', 'system_management', 'data_processing'],
                'weaknesses': ['complex_code_analysis', 'advanced_ai_tasks'],
                'resource_intensive': False,
                'cost_per_minute': 0.01
            },
            ProcessingEngine.HYBRID: {
                'strengths': ['complex_multi_faceted_tasks', 'best_of_both'],
                'weaknesses': ['coordination_overhead', 'resource_intensive'],
                'resource_intensive': True,
                'cost_per_minute': 0.08
            }
        }
    
    def _initialize_routing_rules(self) -> Dict[str, Any]:
        """Initialize routing rules"""
        return {
            'software_engineering_to_trae': {
                'condition': 'category == SOFTWARE_ENGINEERING and complexity > 0.5',
                'action': 'route_to_trae',
                'weight': 0.8
            },
            'automation_to_native': {
                'condition': 'category == AUTOMATION',
                'action': 'route_to_native',
                'weight': 0.9
            },
            'complex_to_hybrid': {
                'condition': 'complexity > 0.8 and duration > 60',
                'action': 'route_to_hybrid',
                'weight': 0.7
            },
            'simple_to_native': {
                'condition': 'complexity < 0.3 and duration < 30',
                'action': 'route_to_native',
                'weight': 0.8
            }
        }
    
    def _initialize_decision_weights(self) -> Dict[str, float]:
        """Initialize decision weights for scoring"""
        return {
            'accuracy': 0.25,
            'speed': 0.20,
            'resource_efficiency': 0.20,
            'reliability': 0.20,
            'cost': 0.15
        }
    
    async def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        stats = self.routing_stats.copy()
        
        # Add success rate if available
        total_routes = stats['total_routes']
        if total_routes > 0:
            stats['success_rate'] = stats['successful_routes'] / total_routes if 'successful_routes' in stats else 0.0
        
        # Add learning data summary
        stats['learning_patterns'] = len(self.learning_data)
        stats['routing_history_size'] = len(self.routing_history)
        
        return stats
    
    async def get_routing_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent routing history"""
        return self.routing_history[-limit:] if self.routing_history else []

