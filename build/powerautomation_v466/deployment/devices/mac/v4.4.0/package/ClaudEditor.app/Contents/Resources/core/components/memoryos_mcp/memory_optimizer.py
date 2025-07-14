"""
Memory Optimizer - AI Memory Optimization and Performance System

This module provides comprehensive memory optimization capabilities for AI systems,
including intelligent memory cleanup, performance optimization, storage efficiency,
and adaptive memory management strategies.
"""

import asyncio
import json
import time
import uuid
import logging
import statistics
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
import sqlite3
import threading


class OptimizationStrategy(Enum):
    """Memory optimization strategies"""
    AGGRESSIVE = "aggressive"        # Maximum optimization, may lose some data
    BALANCED = "balanced"           # Balance between optimization and data retention
    CONSERVATIVE = "conservative"   # Minimal optimization, preserve most data
    ADAPTIVE = "adaptive"          # Dynamically adjust strategy based on usage
    CUSTOM = "custom"              # User-defined optimization rules


class OptimizationTarget(Enum):
    """Optimization targets"""
    STORAGE_SIZE = "storage_size"           # Minimize storage usage
    ACCESS_SPEED = "access_speed"           # Maximize access performance
    MEMORY_USAGE = "memory_usage"           # Minimize RAM usage
    RELEVANCE_QUALITY = "relevance_quality" # Maximize relevance of retained memories
    BALANCED_PERFORMANCE = "balanced_performance" # Balance all factors


class CleanupAction(Enum):
    """Types of cleanup actions"""
    DELETE = "delete"               # Permanently delete memory
    ARCHIVE = "archive"             # Move to archive storage
    COMPRESS = "compress"           # Compress memory content
    MERGE = "merge"                 # Merge with similar memories
    DOWNGRADE = "downgrade"         # Reduce priority/detail level
    SUMMARIZE = "summarize"         # Create summary and remove details


@dataclass
class OptimizationRule:
    """Memory optimization rule"""
    rule_id: str
    name: str
    description: str
    condition: Dict[str, Any]       # Conditions for applying rule
    action: CleanupAction
    parameters: Dict[str, Any]      # Action parameters
    priority: int                   # Rule priority (1 = highest)
    enabled: bool
    success_rate: float
    last_applied: Optional[float]
    application_count: int


@dataclass
class OptimizationTask:
    """Memory optimization task"""
    task_id: str
    strategy: OptimizationStrategy
    target: OptimizationTarget
    scope: Dict[str, Any]          # Scope of optimization (user, session, etc.)
    rules: List[str]               # Rule IDs to apply
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    status: str                    # pending, running, completed, failed
    progress: float                # 0.0 to 1.0
    results: Dict[str, Any]


@dataclass
class OptimizationResult:
    """Result of optimization operation"""
    task_id: str
    memories_processed: int
    memories_deleted: int
    memories_archived: int
    memories_compressed: int
    memories_merged: int
    storage_saved: int             # Bytes saved
    performance_improvement: float  # Percentage improvement
    execution_time: float
    errors: List[str]
    warnings: List[str]


@dataclass
class MemoryMetrics:
    """Memory system metrics"""
    total_memories: int
    active_memories: int
    archived_memories: int
    total_storage_bytes: int
    average_access_time: float
    cache_hit_rate: float
    memory_fragmentation: float
    optimization_score: float      # Overall optimization score (0-1)


class MemoryOptimizer:
    """
    Memory Optimizer - AI Memory Optimization and Performance System
    
    Provides comprehensive memory optimization capabilities including
    intelligent cleanup, performance tuning, storage optimization,
    and adaptive memory management strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Memory Optimizer
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Optimization configuration
        self.default_strategy = OptimizationStrategy(
            self.config.get('default_strategy', 'balanced')
        )
        self.optimization_interval = self.config.get('optimization_interval', 3600)  # 1 hour
        self.max_storage_mb = self.config.get('max_storage_mb', 1000)  # 1GB
        self.target_cache_hit_rate = self.config.get('target_cache_hit_rate', 0.8)
        self.enable_auto_optimization = self.config.get('enable_auto_optimization', True)
        
        # Optimization rules and tasks
        self.optimization_rules = {}
        self.active_tasks = {}
        self.completed_tasks = {}
        self.optimization_history = deque(maxlen=1000)
        
        # Performance monitoring
        self.metrics_history = deque(maxlen=100)
        self.performance_baselines = {}
        self.optimization_triggers = {}
        
        # Optimization statistics
        self.optimization_stats = {
            'total_optimizations': 0,
            'total_storage_saved': 0,
            'total_memories_processed': 0,
            'average_performance_improvement': 0.0,
            'last_optimization': None,
            'optimization_success_rate': 0.0
        }
        
        # Threading for background optimization
        self.optimization_thread = None
        self.stop_optimization = threading.Event()
        
        # Initialize optimizer
        self._initialize_default_rules()
        self._initialize_performance_baselines()
        
        # Start background optimization if enabled
        if self.enable_auto_optimization:
            self._start_background_optimization()
        
        self.logger.info("MemoryOptimizer initialized")
    
    async def optimize_memories(
        self,
        strategy: OptimizationStrategy = None,
        target: OptimizationTarget = OptimizationTarget.BALANCED_PERFORMANCE,
        scope: Optional[Dict[str, Any]] = None,
        custom_rules: Optional[List[str]] = None
    ) -> str:
        """
        Start memory optimization task
        
        Args:
            strategy: Optimization strategy to use
            target: Optimization target
            scope: Scope of optimization (user_id, session_id, etc.)
            custom_rules: Custom rule IDs to apply
            
        Returns:
            str: Task ID for tracking optimization progress
        """
        try:
            strategy = strategy or self.default_strategy
            scope = scope or {}
            
            # Create optimization task
            task_id = f"opt_{uuid.uuid4().hex[:8]}"
            
            # Determine rules to apply
            rules_to_apply = custom_rules or await self._select_optimization_rules(strategy, target)
            
            task = OptimizationTask(
                task_id=task_id,
                strategy=strategy,
                target=target,
                scope=scope,
                rules=rules_to_apply,
                created_at=time.time(),
                started_at=None,
                completed_at=None,
                status="pending",
                progress=0.0,
                results={}
            )
            
            self.active_tasks[task_id] = task
            
            # Start optimization in background
            asyncio.create_task(self._execute_optimization_task(task))
            
            self.logger.info(f"Started optimization task: {task_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Failed to start optimization: {str(e)}")
            raise
    
    async def get_optimization_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of optimization task
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Optional[Dict]: Task status information
        """
        try:
            # Check active tasks
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return {
                    'task_id': task_id,
                    'status': task.status,
                    'progress': task.progress,
                    'strategy': task.strategy.value,
                    'target': task.target.value,
                    'created_at': task.created_at,
                    'started_at': task.started_at,
                    'estimated_completion': self._estimate_completion_time(task),
                    'current_results': task.results
                }
            
            # Check completed tasks
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                return {
                    'task_id': task_id,
                    'status': task.status,
                    'progress': task.progress,
                    'strategy': task.strategy.value,
                    'target': task.target.value,
                    'created_at': task.created_at,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'execution_time': task.completed_at - task.started_at if task.started_at and task.completed_at else None,
                    'final_results': task.results
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get optimization status: {str(e)}")
            return None
    
    async def cancel_optimization(self, task_id: str) -> bool:
        """
        Cancel running optimization task
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = "cancelled"
                task.completed_at = time.time()
                
                # Move to completed tasks
                self.completed_tasks[task_id] = task
                del self.active_tasks[task_id]
                
                self.logger.info(f"Cancelled optimization task: {task_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel optimization: {str(e)}")
            return False
    
    async def get_memory_metrics(self) -> MemoryMetrics:
        """
        Get current memory system metrics
        
        Returns:
            MemoryMetrics: Current memory metrics
        """
        try:
            # This would integrate with the MemoryEngine to get actual metrics
            # For now, return simulated metrics
            
            metrics = MemoryMetrics(
                total_memories=1000,  # Would get from MemoryEngine
                active_memories=800,
                archived_memories=200,
                total_storage_bytes=50 * 1024 * 1024,  # 50MB
                average_access_time=0.05,  # 50ms
                cache_hit_rate=0.85,
                memory_fragmentation=0.15,
                optimization_score=0.75
            )
            
            # Store metrics for history
            self.metrics_history.append({
                'timestamp': time.time(),
                'metrics': metrics
            })
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get memory metrics: {str(e)}")
            # Return default metrics on error
            return MemoryMetrics(0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0)
    
    async def analyze_memory_usage(
        self,
        time_range_hours: float = 24.0
    ) -> Dict[str, Any]:
        """
        Analyze memory usage patterns and identify optimization opportunities
        
        Args:
            time_range_hours: Time range for analysis in hours
            
        Returns:
            Dict: Memory usage analysis results
        """
        try:
            current_time = time.time()
            start_time = current_time - (time_range_hours * 3600)
            
            # Filter metrics within time range
            relevant_metrics = [
                entry for entry in self.metrics_history
                if entry['timestamp'] >= start_time
            ]
            
            if not relevant_metrics:
                return {'error': 'Insufficient data for analysis'}
            
            # Analyze trends
            analysis = {
                'time_range_hours': time_range_hours,
                'data_points': len(relevant_metrics),
                'memory_growth_trend': await self._analyze_memory_growth(relevant_metrics),
                'performance_trend': await self._analyze_performance_trend(relevant_metrics),
                'optimization_opportunities': await self._identify_optimization_opportunities(relevant_metrics),
                'storage_efficiency': await self._analyze_storage_efficiency(relevant_metrics),
                'access_patterns': await self._analyze_access_patterns(relevant_metrics),
                'recommendations': await self._generate_optimization_recommendations(relevant_metrics)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze memory usage: {str(e)}")
            return {'error': str(e)}
    
    async def create_optimization_rule(
        self,
        name: str,
        description: str,
        condition: Dict[str, Any],
        action: CleanupAction,
        parameters: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """
        Create custom optimization rule
        
        Args:
            name: Rule name
            description: Rule description
            condition: Conditions for applying rule
            action: Action to take when conditions are met
            parameters: Action parameters
            priority: Rule priority (1 = highest)
            
        Returns:
            str: Rule ID
        """
        try:
            rule_id = f"rule_{uuid.uuid4().hex[:8]}"
            
            rule = OptimizationRule(
                rule_id=rule_id,
                name=name,
                description=description,
                condition=condition,
                action=action,
                parameters=parameters,
                priority=priority,
                enabled=True,
                success_rate=0.0,
                last_applied=None,
                application_count=0
            )
            
            self.optimization_rules[rule_id] = rule
            
            self.logger.info(f"Created optimization rule: {rule_id} ({name})")
            return rule_id
            
        except Exception as e:
            self.logger.error(f"Failed to create optimization rule: {str(e)}")
            raise
    
    async def update_optimization_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update existing optimization rule
        
        Args:
            rule_id: Rule ID to update
            updates: Updates to apply
            
        Returns:
            bool: True if successful
        """
        try:
            if rule_id not in self.optimization_rules:
                return False
            
            rule = self.optimization_rules[rule_id]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            self.logger.info(f"Updated optimization rule: {rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update optimization rule: {str(e)}")
            return False
    
    async def delete_optimization_rule(self, rule_id: str) -> bool:
        """
        Delete optimization rule
        
        Args:
            rule_id: Rule ID to delete
            
        Returns:
            bool: True if successful
        """
        try:
            if rule_id in self.optimization_rules:
                del self.optimization_rules[rule_id]
                self.logger.info(f"Deleted optimization rule: {rule_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete optimization rule: {str(e)}")
            return False
    
    async def get_optimization_recommendations(
        self,
        target: OptimizationTarget = OptimizationTarget.BALANCED_PERFORMANCE
    ) -> List[Dict[str, Any]]:
        """
        Get optimization recommendations based on current system state
        
        Args:
            target: Optimization target for recommendations
            
        Returns:
            List[Dict]: List of optimization recommendations
        """
        try:
            metrics = await self.get_memory_metrics()
            recommendations = []
            
            # Storage-based recommendations
            if target in [OptimizationTarget.STORAGE_SIZE, OptimizationTarget.BALANCED_PERFORMANCE]:
                storage_mb = metrics.total_storage_bytes / (1024 * 1024)
                if storage_mb > self.max_storage_mb * 0.8:  # 80% threshold
                    recommendations.append({
                        'type': 'storage_cleanup',
                        'priority': 'high',
                        'description': f'Storage usage is {storage_mb:.1f}MB, approaching limit of {self.max_storage_mb}MB',
                        'suggested_action': 'Run aggressive cleanup to free storage space',
                        'estimated_savings': f'{storage_mb * 0.3:.1f}MB',
                        'strategy': OptimizationStrategy.AGGRESSIVE.value
                    })
            
            # Performance-based recommendations
            if target in [OptimizationTarget.ACCESS_SPEED, OptimizationTarget.BALANCED_PERFORMANCE]:
                if metrics.cache_hit_rate < self.target_cache_hit_rate:
                    recommendations.append({
                        'type': 'cache_optimization',
                        'priority': 'medium',
                        'description': f'Cache hit rate is {metrics.cache_hit_rate:.2%}, below target of {self.target_cache_hit_rate:.2%}',
                        'suggested_action': 'Optimize cache by removing rarely accessed memories',
                        'estimated_improvement': f'{(self.target_cache_hit_rate - metrics.cache_hit_rate) * 100:.1f}% cache hit rate improvement',
                        'strategy': OptimizationStrategy.BALANCED.value
                    })
            
            # Memory fragmentation recommendations
            if metrics.memory_fragmentation > 0.3:  # 30% threshold
                recommendations.append({
                    'type': 'defragmentation',
                    'priority': 'medium',
                    'description': f'Memory fragmentation is {metrics.memory_fragmentation:.2%}',
                    'suggested_action': 'Run memory defragmentation to improve efficiency',
                    'estimated_improvement': 'Reduced memory fragmentation and improved access speed',
                    'strategy': OptimizationStrategy.CONSERVATIVE.value
                })
            
            # Overall optimization score recommendations
            if metrics.optimization_score < 0.6:  # 60% threshold
                recommendations.append({
                    'type': 'comprehensive_optimization',
                    'priority': 'high',
                    'description': f'Overall optimization score is {metrics.optimization_score:.2%}',
                    'suggested_action': 'Run comprehensive optimization to improve system performance',
                    'estimated_improvement': 'Significant improvement in all performance metrics',
                    'strategy': OptimizationStrategy.ADAPTIVE.value
                })
            
            # Sort by priority
            priority_order = {'high': 1, 'medium': 2, 'low': 3}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to get optimization recommendations: {str(e)}")
            return []
    
    async def get_optimization_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive optimization statistics
        
        Returns:
            Dict: Optimization statistics and performance data
        """
        try:
            stats = self.optimization_stats.copy()
            
            # Add current metrics
            current_metrics = await self.get_memory_metrics()
            stats['current_metrics'] = asdict(current_metrics)
            
            # Add rule statistics
            stats['optimization_rules'] = {
                'total_rules': len(self.optimization_rules),
                'enabled_rules': sum(1 for rule in self.optimization_rules.values() if rule.enabled),
                'most_successful_rule': await self._get_most_successful_rule(),
                'rule_success_rates': {
                    rule_id: rule.success_rate
                    for rule_id, rule in self.optimization_rules.items()
                }
            }
            
            # Add task statistics
            stats['task_statistics'] = {
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks),
                'recent_tasks': [
                    {
                        'task_id': task.task_id,
                        'strategy': task.strategy.value,
                        'status': task.status,
                        'completed_at': task.completed_at
                    }
                    for task in list(self.completed_tasks.values())[-10:]  # Last 10 tasks
                ]
            }
            
            # Add performance trends
            if len(self.metrics_history) > 1:
                stats['performance_trends'] = await self._calculate_performance_trends()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get optimization statistics: {str(e)}")
            return {}
    
    async def _execute_optimization_task(self, task: OptimizationTask):
        """Execute optimization task"""
        try:
            task.status = "running"
            task.started_at = time.time()
            task.progress = 0.0
            
            self.logger.info(f"Executing optimization task: {task.task_id}")
            
            # Initialize results
            result = OptimizationResult(
                task_id=task.task_id,
                memories_processed=0,
                memories_deleted=0,
                memories_archived=0,
                memories_compressed=0,
                memories_merged=0,
                storage_saved=0,
                performance_improvement=0.0,
                execution_time=0.0,
                errors=[],
                warnings=[]
            )
            
            # Get baseline metrics
            baseline_metrics = await self.get_memory_metrics()
            
            # Apply optimization rules
            total_rules = len(task.rules)
            for i, rule_id in enumerate(task.rules):
                if task.status == "cancelled":
                    break
                
                if rule_id in self.optimization_rules:
                    rule = self.optimization_rules[rule_id]
                    
                    try:
                        # Apply rule
                        rule_result = await self._apply_optimization_rule(rule, task.scope)
                        
                        # Update results
                        result.memories_processed += rule_result.get('memories_processed', 0)
                        result.memories_deleted += rule_result.get('memories_deleted', 0)
                        result.memories_archived += rule_result.get('memories_archived', 0)
                        result.memories_compressed += rule_result.get('memories_compressed', 0)
                        result.memories_merged += rule_result.get('memories_merged', 0)
                        result.storage_saved += rule_result.get('storage_saved', 0)
                        
                        # Update rule statistics
                        rule.last_applied = time.time()
                        rule.application_count += 1
                        
                        if rule_result.get('success', True):
                            rule.success_rate = (rule.success_rate * (rule.application_count - 1) + 1.0) / rule.application_count
                        else:
                            rule.success_rate = (rule.success_rate * (rule.application_count - 1)) / rule.application_count
                            result.errors.append(f"Rule {rule_id} failed: {rule_result.get('error', 'Unknown error')}")
                        
                    except Exception as e:
                        result.errors.append(f"Error applying rule {rule_id}: {str(e)}")
                        self.logger.error(f"Error applying optimization rule {rule_id}: {str(e)}")
                
                # Update progress
                task.progress = (i + 1) / total_rules
                
                # Small delay to allow cancellation
                await asyncio.sleep(0.1)
            
            # Calculate final metrics and performance improvement
            if task.status != "cancelled":
                final_metrics = await self.get_memory_metrics()
                result.performance_improvement = await self._calculate_performance_improvement(
                    baseline_metrics, final_metrics
                )
                
                task.status = "completed"
            
            task.completed_at = time.time()
            result.execution_time = task.completed_at - task.started_at
            task.results = asdict(result)
            
            # Move to completed tasks
            self.completed_tasks[task.task_id] = task
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            # Update global statistics
            self.optimization_stats['total_optimizations'] += 1
            self.optimization_stats['total_storage_saved'] += result.storage_saved
            self.optimization_stats['total_memories_processed'] += result.memories_processed
            self.optimization_stats['last_optimization'] = task.completed_at
            
            # Update success rate
            if task.status == "completed" and not result.errors:
                current_rate = self.optimization_stats['optimization_success_rate']
                total_opts = self.optimization_stats['total_optimizations']
                self.optimization_stats['optimization_success_rate'] = (
                    (current_rate * (total_opts - 1) + 1.0) / total_opts
                )
            
            # Update average performance improvement
            current_avg = self.optimization_stats['average_performance_improvement']
            total_opts = self.optimization_stats['total_optimizations']
            self.optimization_stats['average_performance_improvement'] = (
                (current_avg * (total_opts - 1) + result.performance_improvement) / total_opts
            )
            
            self.logger.info(f"Optimization task completed: {task.task_id}")
            
        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            task.results = {'error': str(e)}
            
            # Move to completed tasks
            self.completed_tasks[task.task_id] = task
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            self.logger.error(f"Optimization task failed: {task.task_id} - {str(e)}")
    
    async def _select_optimization_rules(
        self,
        strategy: OptimizationStrategy,
        target: OptimizationTarget
    ) -> List[str]:
        """Select optimization rules based on strategy and target"""
        selected_rules = []
        
        # Filter rules based on strategy and target
        for rule_id, rule in self.optimization_rules.items():
            if not rule.enabled:
                continue
            
            # Strategy-based selection
            if strategy == OptimizationStrategy.AGGRESSIVE:
                # Include all rules, prioritize high-impact actions
                if rule.action in [CleanupAction.DELETE, CleanupAction.COMPRESS, CleanupAction.MERGE]:
                    selected_rules.append(rule_id)
            
            elif strategy == OptimizationStrategy.CONSERVATIVE:
                # Only safe actions
                if rule.action in [CleanupAction.ARCHIVE, CleanupAction.DOWNGRADE]:
                    selected_rules.append(rule_id)
            
            elif strategy == OptimizationStrategy.BALANCED:
                # Balanced approach
                if rule.action in [CleanupAction.ARCHIVE, CleanupAction.COMPRESS, CleanupAction.MERGE, CleanupAction.SUMMARIZE]:
                    selected_rules.append(rule_id)
            
            elif strategy == OptimizationStrategy.ADAPTIVE:
                # Select based on current system state and rule success rate
                if rule.success_rate > 0.7:  # Only high-success rules
                    selected_rules.append(rule_id)
        
        # Sort by priority
        selected_rules.sort(key=lambda rule_id: self.optimization_rules[rule_id].priority)
        
        return selected_rules
    
    async def _apply_optimization_rule(
        self,
        rule: OptimizationRule,
        scope: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a specific optimization rule"""
        try:
            result = {
                'success': True,
                'memories_processed': 0,
                'memories_deleted': 0,
                'memories_archived': 0,
                'memories_compressed': 0,
                'memories_merged': 0,
                'storage_saved': 0
            }
            
            # This would integrate with MemoryEngine to actually apply the rule
            # For now, simulate the application
            
            if rule.action == CleanupAction.DELETE:
                # Simulate deletion of old, low-priority memories
                result['memories_processed'] = 50
                result['memories_deleted'] = 10
                result['storage_saved'] = 1024 * 1024  # 1MB
            
            elif rule.action == CleanupAction.ARCHIVE:
                # Simulate archiving of old memories
                result['memories_processed'] = 100
                result['memories_archived'] = 30
                result['storage_saved'] = 512 * 1024  # 512KB
            
            elif rule.action == CleanupAction.COMPRESS:
                # Simulate compression of large memories
                result['memories_processed'] = 75
                result['memories_compressed'] = 25
                result['storage_saved'] = 2 * 1024 * 1024  # 2MB
            
            elif rule.action == CleanupAction.MERGE:
                # Simulate merging of similar memories
                result['memories_processed'] = 60
                result['memories_merged'] = 20
                result['storage_saved'] = 800 * 1024  # 800KB
            
            # Add some randomness to simulate real-world variability
            import random
            for key in ['memories_processed', 'memories_deleted', 'memories_archived', 'memories_compressed', 'memories_merged']:
                if result[key] > 0:
                    result[key] = int(result[key] * (0.8 + random.random() * 0.4))  # ±20% variation
            
            result['storage_saved'] = int(result['storage_saved'] * (0.8 + random.random() * 0.4))
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'memories_processed': 0,
                'memories_deleted': 0,
                'memories_archived': 0,
                'memories_compressed': 0,
                'memories_merged': 0,
                'storage_saved': 0
            }
    
    async def _calculate_performance_improvement(
        self,
        baseline: MemoryMetrics,
        final: MemoryMetrics
    ) -> float:
        """Calculate performance improvement percentage"""
        try:
            # Calculate improvement in key metrics
            improvements = []
            
            # Storage efficiency improvement
            if baseline.total_storage_bytes > 0:
                storage_improvement = (baseline.total_storage_bytes - final.total_storage_bytes) / baseline.total_storage_bytes
                improvements.append(storage_improvement)
            
            # Access speed improvement
            if baseline.average_access_time > 0:
                speed_improvement = (baseline.average_access_time - final.average_access_time) / baseline.average_access_time
                improvements.append(speed_improvement)
            
            # Cache hit rate improvement
            cache_improvement = final.cache_hit_rate - baseline.cache_hit_rate
            improvements.append(cache_improvement)
            
            # Memory fragmentation improvement
            fragmentation_improvement = baseline.memory_fragmentation - final.memory_fragmentation
            improvements.append(fragmentation_improvement)
            
            # Overall optimization score improvement
            score_improvement = final.optimization_score - baseline.optimization_score
            improvements.append(score_improvement)
            
            # Calculate weighted average improvement
            if improvements:
                avg_improvement = sum(improvements) / len(improvements)
                return max(0.0, min(1.0, avg_improvement)) * 100  # Convert to percentage
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to calculate performance improvement: {str(e)}")
            return 0.0
    
    def _estimate_completion_time(self, task: OptimizationTask) -> Optional[float]:
        """Estimate completion time for optimization task"""
        if task.status != "running" or task.progress <= 0:
            return None
        
        elapsed_time = time.time() - task.started_at
        estimated_total_time = elapsed_time / task.progress
        estimated_completion = task.started_at + estimated_total_time
        
        return estimated_completion
    
    async def _analyze_memory_growth(self, metrics_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze memory growth trends"""
        if len(metrics_history) < 2:
            return {'trend': 'insufficient_data'}
        
        # Extract memory counts over time
        memory_counts = [entry['metrics'].total_memories for entry in metrics_history]
        storage_sizes = [entry['metrics'].total_storage_bytes for entry in metrics_history]
        
        # Calculate growth rates
        memory_growth_rate = (memory_counts[-1] - memory_counts[0]) / len(memory_counts)
        storage_growth_rate = (storage_sizes[-1] - storage_sizes[0]) / len(storage_sizes)
        
        # Determine trend
        if memory_growth_rate > 10:  # More than 10 memories per data point
            trend = 'rapid_growth'
        elif memory_growth_rate > 5:
            trend = 'moderate_growth'
        elif memory_growth_rate > 0:
            trend = 'slow_growth'
        else:
            trend = 'stable_or_declining'
        
        return {
            'trend': trend,
            'memory_growth_rate': memory_growth_rate,
            'storage_growth_rate': storage_growth_rate,
            'current_memory_count': memory_counts[-1],
            'current_storage_bytes': storage_sizes[-1]
        }
    
    async def _analyze_performance_trend(self, metrics_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends"""
        if len(metrics_history) < 2:
            return {'trend': 'insufficient_data'}
        
        # Extract performance metrics
        access_times = [entry['metrics'].average_access_time for entry in metrics_history]
        cache_hit_rates = [entry['metrics'].cache_hit_rate for entry in metrics_history]
        optimization_scores = [entry['metrics'].optimization_score for entry in metrics_history]
        
        # Calculate trends
        access_time_trend = 'improving' if access_times[-1] < access_times[0] else 'degrading'
        cache_trend = 'improving' if cache_hit_rates[-1] > cache_hit_rates[0] else 'degrading'
        optimization_trend = 'improving' if optimization_scores[-1] > optimization_scores[0] else 'degrading'
        
        return {
            'access_time_trend': access_time_trend,
            'cache_hit_rate_trend': cache_trend,
            'optimization_score_trend': optimization_trend,
            'current_access_time': access_times[-1],
            'current_cache_hit_rate': cache_hit_rates[-1],
            'current_optimization_score': optimization_scores[-1]
        }
    
    async def _identify_optimization_opportunities(self, metrics_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []
        
        if not metrics_history:
            return opportunities
        
        latest_metrics = metrics_history[-1]['metrics']
        
        # Storage optimization opportunities
        if latest_metrics.total_storage_bytes > self.max_storage_mb * 1024 * 1024 * 0.8:
            opportunities.append({
                'type': 'storage_cleanup',
                'severity': 'high',
                'description': 'Storage usage approaching limit',
                'recommended_action': 'aggressive_cleanup'
            })
        
        # Performance optimization opportunities
        if latest_metrics.cache_hit_rate < self.target_cache_hit_rate:
            opportunities.append({
                'type': 'cache_optimization',
                'severity': 'medium',
                'description': 'Cache hit rate below target',
                'recommended_action': 'cache_tuning'
            })
        
        # Memory fragmentation opportunities
        if latest_metrics.memory_fragmentation > 0.3:
            opportunities.append({
                'type': 'defragmentation',
                'severity': 'medium',
                'description': 'High memory fragmentation detected',
                'recommended_action': 'memory_defragmentation'
            })
        
        return opportunities
    
    async def _analyze_storage_efficiency(self, metrics_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze storage efficiency"""
        if not metrics_history:
            return {}
        
        latest_metrics = metrics_history[-1]['metrics']
        
        # Calculate storage efficiency metrics
        storage_per_memory = latest_metrics.total_storage_bytes / max(1, latest_metrics.total_memories)
        storage_utilization = latest_metrics.total_storage_bytes / (self.max_storage_mb * 1024 * 1024)
        
        efficiency_score = 1.0 - min(1.0, storage_utilization)  # Higher is better
        
        return {
            'storage_per_memory_bytes': storage_per_memory,
            'storage_utilization_percentage': storage_utilization * 100,
            'efficiency_score': efficiency_score,
            'fragmentation_level': latest_metrics.memory_fragmentation
        }
    
    async def _analyze_access_patterns(self, metrics_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze memory access patterns"""
        if len(metrics_history) < 2:
            return {}
        
        # Extract access-related metrics
        access_times = [entry['metrics'].average_access_time for entry in metrics_history]
        cache_hit_rates = [entry['metrics'].cache_hit_rate for entry in metrics_history]
        
        # Calculate statistics
        avg_access_time = statistics.mean(access_times)
        access_time_variance = statistics.variance(access_times) if len(access_times) > 1 else 0
        avg_cache_hit_rate = statistics.mean(cache_hit_rates)
        
        return {
            'average_access_time': avg_access_time,
            'access_time_variance': access_time_variance,
            'average_cache_hit_rate': avg_cache_hit_rate,
            'access_pattern_stability': 'stable' if access_time_variance < 0.01 else 'variable'
        }
    
    async def _generate_optimization_recommendations(self, metrics_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []
        
        if not metrics_history:
            return recommendations
        
        latest_metrics = metrics_history[-1]['metrics']
        
        # Storage recommendations
        storage_mb = latest_metrics.total_storage_bytes / (1024 * 1024)
        if storage_mb > self.max_storage_mb * 0.9:
            recommendations.append({
                'priority': 'high',
                'type': 'storage',
                'action': 'immediate_cleanup',
                'description': f'Storage at {storage_mb:.1f}MB, very close to {self.max_storage_mb}MB limit'
            })
        elif storage_mb > self.max_storage_mb * 0.7:
            recommendations.append({
                'priority': 'medium',
                'type': 'storage',
                'action': 'scheduled_cleanup',
                'description': f'Storage at {storage_mb:.1f}MB, consider proactive cleanup'
            })
        
        # Performance recommendations
        if latest_metrics.average_access_time > 0.1:  # 100ms threshold
            recommendations.append({
                'priority': 'medium',
                'type': 'performance',
                'action': 'cache_optimization',
                'description': f'Average access time is {latest_metrics.average_access_time:.3f}s, consider cache tuning'
            })
        
        # Optimization score recommendations
        if latest_metrics.optimization_score < 0.5:
            recommendations.append({
                'priority': 'high',
                'type': 'comprehensive',
                'action': 'full_optimization',
                'description': f'Optimization score is {latest_metrics.optimization_score:.2%}, comprehensive optimization needed'
            })
        
        return recommendations
    
    async def _get_most_successful_rule(self) -> Optional[Dict[str, Any]]:
        """Get the most successful optimization rule"""
        if not self.optimization_rules:
            return None
        
        best_rule = max(
            self.optimization_rules.values(),
            key=lambda rule: rule.success_rate if rule.application_count > 0 else 0
        )
        
        if best_rule.application_count > 0:
            return {
                'rule_id': best_rule.rule_id,
                'name': best_rule.name,
                'success_rate': best_rule.success_rate,
                'application_count': best_rule.application_count
            }
        
        return None
    
    async def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends from metrics history"""
        if len(self.metrics_history) < 2:
            return {}
        
        # Get recent metrics (last 10 data points)
        recent_metrics = list(self.metrics_history)[-10:]
        
        # Extract time series data
        timestamps = [entry['timestamp'] for entry in recent_metrics]
        access_times = [entry['metrics'].average_access_time for entry in recent_metrics]
        cache_hit_rates = [entry['metrics'].cache_hit_rate for entry in recent_metrics]
        optimization_scores = [entry['metrics'].optimization_score for entry in recent_metrics]
        
        # Calculate simple linear trends
        def calculate_trend(values):
            if len(values) < 2:
                return 0.0
            return (values[-1] - values[0]) / len(values)
        
        return {
            'access_time_trend': calculate_trend(access_times),
            'cache_hit_rate_trend': calculate_trend(cache_hit_rates),
            'optimization_score_trend': calculate_trend(optimization_scores),
            'data_points': len(recent_metrics),
            'time_span_hours': (timestamps[-1] - timestamps[0]) / 3600 if len(timestamps) > 1 else 0
        }
    
    def _initialize_default_rules(self):
        """Initialize default optimization rules"""
        # Rule 1: Delete very old, low-priority memories
        self.optimization_rules['delete_old_low_priority'] = OptimizationRule(
            rule_id='delete_old_low_priority',
            name='Delete Old Low Priority Memories',
            description='Delete memories older than 30 days with low priority and minimal access',
            condition={
                'age_days': {'min': 30},
                'priority': {'max': 4},
                'access_count': {'max': 2}
            },
            action=CleanupAction.DELETE,
            parameters={'batch_size': 100},
            priority=3,
            enabled=True,
            success_rate=0.0,
            last_applied=None,
            application_count=0
        )
        
        # Rule 2: Archive old memories
        self.optimization_rules['archive_old_memories'] = OptimizationRule(
            rule_id='archive_old_memories',
            name='Archive Old Memories',
            description='Archive memories older than 7 days that are rarely accessed',
            condition={
                'age_days': {'min': 7},
                'access_count': {'max': 5}
            },
            action=CleanupAction.ARCHIVE,
            parameters={'batch_size': 200},
            priority=5,
            enabled=True,
            success_rate=0.0,
            last_applied=None,
            application_count=0
        )
        
        # Rule 3: Compress large memories
        self.optimization_rules['compress_large_memories'] = OptimizationRule(
            rule_id='compress_large_memories',
            name='Compress Large Memories',
            description='Compress memories larger than 10KB to save storage space',
            condition={
                'content_size_bytes': {'min': 10240}  # 10KB
            },
            action=CleanupAction.COMPRESS,
            parameters={'compression_level': 6},
            priority=4,
            enabled=True,
            success_rate=0.0,
            last_applied=None,
            application_count=0
        )
        
        # Rule 4: Merge similar memories
        self.optimization_rules['merge_similar_memories'] = OptimizationRule(
            rule_id='merge_similar_memories',
            name='Merge Similar Memories',
            description='Merge memories with high content similarity to reduce redundancy',
            condition={
                'similarity_threshold': 0.8,
                'same_type': True
            },
            action=CleanupAction.MERGE,
            parameters={'max_merge_group_size': 5},
            priority=6,
            enabled=True,
            success_rate=0.0,
            last_applied=None,
            application_count=0
        )
    
    def _initialize_performance_baselines(self):
        """Initialize performance baselines"""
        self.performance_baselines = {
            'target_access_time': 0.05,  # 50ms
            'target_cache_hit_rate': 0.8,  # 80%
            'target_storage_efficiency': 0.7,  # 70%
            'target_optimization_score': 0.8  # 80%
        }
    
    def _start_background_optimization(self):
        """Start background optimization thread"""
        def background_optimization():
            while not self.stop_optimization.is_set():
                try:
                    # Check if optimization is needed
                    if self._should_run_auto_optimization():
                        # Run optimization asynchronously
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        task_id = loop.run_until_complete(
                            self.optimize_memories(
                                strategy=OptimizationStrategy.ADAPTIVE,
                                target=OptimizationTarget.BALANCED_PERFORMANCE
                            )
                        )
                        
                        self.logger.info(f"Auto-optimization started: {task_id}")
                        loop.close()
                    
                    # Wait for next check
                    self.stop_optimization.wait(self.optimization_interval)
                    
                except Exception as e:
                    self.logger.error(f"Background optimization error: {str(e)}")
                    self.stop_optimization.wait(60)  # Wait 1 minute on error
        
        self.optimization_thread = threading.Thread(target=background_optimization, daemon=True)
        self.optimization_thread.start()
    
    def _should_run_auto_optimization(self) -> bool:
        """Check if auto-optimization should run"""
        # Check if enough time has passed since last optimization
        last_opt = self.optimization_stats.get('last_optimization')
        if last_opt and time.time() - last_opt < self.optimization_interval:
            return False
        
        # Check if there are performance issues that warrant optimization
        # This would check current metrics against thresholds
        # For now, return True to enable regular optimization
        return True
    
    def stop_background_optimization(self):
        """Stop background optimization"""
        if self.optimization_thread:
            self.stop_optimization.set()
            self.optimization_thread.join(timeout=5)
            self.logger.info("Background optimization stopped")

