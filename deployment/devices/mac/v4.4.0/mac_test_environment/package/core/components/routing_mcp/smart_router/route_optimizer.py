"""
PowerAutomation 4.0 Route Optimizer
路由优化器，用于优化智能路由决策和性能
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .semantic_analyzer import SemanticResult, IntentType


class OptimizationStrategy(Enum):
    """优化策略枚举"""
    PERFORMANCE = "performance"  # 性能优先
    ACCURACY = "accuracy"       # 准确性优先
    BALANCED = "balanced"       # 平衡策略
    COST_EFFECTIVE = "cost_effective"  # 成本效益优先


@dataclass
class RouteMetrics:
    """路由指标"""
    response_time: float
    accuracy_score: float
    resource_usage: float
    success_rate: float
    cost_score: float


@dataclass
class OptimizationResult:
    """优化结果"""
    original_route: Dict[str, Any]
    optimized_route: Dict[str, Any]
    improvement_score: float
    metrics_before: RouteMetrics
    metrics_after: RouteMetrics
    optimization_time: float


class RouteOptimizer:
    """路由优化器"""
    
    def __init__(self, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        
        # 历史数据
        self.route_history: List[Dict[str, Any]] = []
        self.performance_cache: Dict[str, RouteMetrics] = {}
        
        # 优化参数
        self.optimization_weights = self._get_optimization_weights()
        
        # 统计信息
        self.stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "average_improvement": 0.0,
            "total_time_saved": 0.0
        }
    
    def _get_optimization_weights(self) -> Dict[str, float]:
        """获取优化权重"""
        weight_configs = {
            OptimizationStrategy.PERFORMANCE: {
                "response_time": 0.5,
                "accuracy_score": 0.2,
                "resource_usage": 0.2,
                "success_rate": 0.1,
                "cost_score": 0.0
            },
            OptimizationStrategy.ACCURACY: {
                "response_time": 0.1,
                "accuracy_score": 0.6,
                "resource_usage": 0.1,
                "success_rate": 0.2,
                "cost_score": 0.0
            },
            OptimizationStrategy.BALANCED: {
                "response_time": 0.25,
                "accuracy_score": 0.25,
                "resource_usage": 0.2,
                "success_rate": 0.2,
                "cost_score": 0.1
            },
            OptimizationStrategy.COST_EFFECTIVE: {
                "response_time": 0.2,
                "accuracy_score": 0.2,
                "resource_usage": 0.1,
                "success_rate": 0.1,
                "cost_score": 0.4
            }
        }
        return weight_configs.get(self.strategy, weight_configs[OptimizationStrategy.BALANCED])
    
    async def optimize_route(
        self,
        route_request: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        semantic_result: Optional[SemanticResult] = None
    ) -> OptimizationResult:
        """优化路由"""
        start_time = time.time()
        
        try:
            # 生成原始路由
            original_route = await self._generate_original_route(
                route_request, available_agents, semantic_result
            )
            
            # 计算原始指标
            metrics_before = await self._calculate_route_metrics(original_route)
            
            # 执行优化
            optimized_route = await self._apply_optimizations(
                original_route, available_agents, semantic_result
            )
            
            # 计算优化后指标
            metrics_after = await self._calculate_route_metrics(optimized_route)
            
            # 计算改进分数
            improvement_score = self._calculate_improvement_score(
                metrics_before, metrics_after
            )
            
            optimization_time = time.time() - start_time
            
            # 创建优化结果
            result = OptimizationResult(
                original_route=original_route,
                optimized_route=optimized_route,
                improvement_score=improvement_score,
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                optimization_time=optimization_time
            )
            
            # 更新统计信息
            self._update_stats(result)
            
            # 缓存结果
            self._cache_optimization_result(result)
            
            self.logger.info(f"路由优化完成，改进分数: {improvement_score:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"路由优化失败: {e}")
            raise
    
    async def _generate_original_route(
        self,
        route_request: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        semantic_result: Optional[SemanticResult] = None
    ) -> Dict[str, Any]:
        """生成原始路由"""
        # 简单的路由生成逻辑
        intent = semantic_result.intent if semantic_result else IntentType.UNKNOWN
        
        # 根据意图选择合适的智能体
        suitable_agents = []
        for agent in available_agents:
            agent_capabilities = agent.get('capabilities', [])
            if self._is_agent_suitable(intent, agent_capabilities):
                suitable_agents.append(agent)
        
        # 如果没有合适的智能体，选择通用智能体
        if not suitable_agents:
            suitable_agents = [agent for agent in available_agents 
                             if 'general' in agent.get('capabilities', [])]
        
        # 选择第一个合适的智能体
        selected_agent = suitable_agents[0] if suitable_agents else available_agents[0]
        
        return {
            "request": route_request,
            "selected_agent": selected_agent,
            "routing_strategy": "simple",
            "confidence": semantic_result.confidence if semantic_result else 0.5,
            "estimated_time": self._estimate_execution_time(route_request, selected_agent),
            "resource_requirements": self._estimate_resource_requirements(route_request)
        }
    
    async def _apply_optimizations(
        self,
        original_route: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        semantic_result: Optional[SemanticResult] = None
    ) -> Dict[str, Any]:
        """应用优化策略"""
        optimized_route = original_route.copy()
        
        # 优化1: 智能体选择优化
        optimized_route = await self._optimize_agent_selection(
            optimized_route, available_agents, semantic_result
        )
        
        # 优化2: 并行处理优化
        optimized_route = await self._optimize_parallel_processing(optimized_route)
        
        # 优化3: 缓存优化
        optimized_route = await self._optimize_caching(optimized_route)
        
        # 优化4: 资源分配优化
        optimized_route = await self._optimize_resource_allocation(optimized_route)
        
        return optimized_route
    
    async def _optimize_agent_selection(
        self,
        route: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        semantic_result: Optional[SemanticResult] = None
    ) -> Dict[str, Any]:
        """优化智能体选择"""
        if not semantic_result:
            return route
        
        # 计算每个智能体的适配分数
        agent_scores = []
        for agent in available_agents:
            score = self._calculate_agent_score(agent, semantic_result, route['request'])
            agent_scores.append((agent, score))
        
        # 选择最高分的智能体
        if agent_scores:
            best_agent, best_score = max(agent_scores, key=lambda x: x[1])
            route['selected_agent'] = best_agent
            route['agent_selection_score'] = best_score
            route['routing_strategy'] = "optimized"
        
        return route
    
    async def _optimize_parallel_processing(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """优化并行处理"""
        request = route['request']
        
        # 检查是否可以并行处理
        if self._can_parallelize(request):
            route['parallel_enabled'] = True
            route['parallel_tasks'] = self._identify_parallel_tasks(request)
            route['estimated_time'] *= 0.6  # 并行处理可以减少40%的时间
        
        return route
    
    async def _optimize_caching(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """优化缓存策略"""
        request = route['request']
        
        # 检查缓存
        cache_key = self._generate_cache_key(request)
        if cache_key in self.performance_cache:
            route['cache_hit'] = True
            route['cached_metrics'] = self.performance_cache[cache_key]
            route['estimated_time'] *= 0.1  # 缓存命中可以大幅减少时间
        else:
            route['cache_hit'] = False
            route['cache_key'] = cache_key
        
        return route
    
    async def _optimize_resource_allocation(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """优化资源分配"""
        # 根据任务复杂度调整资源分配
        complexity = route['request'].get('complexity', 'medium')
        
        resource_multipliers = {
            'low': 0.7,
            'medium': 1.0,
            'high': 1.5,
            'critical': 2.0
        }
        
        multiplier = resource_multipliers.get(complexity, 1.0)
        route['resource_multiplier'] = multiplier
        route['resource_requirements'] = {
            k: v * multiplier for k, v in route.get('resource_requirements', {}).items()
        }
        
        return route
    
    async def _calculate_route_metrics(self, route: Dict[str, Any]) -> RouteMetrics:
        """计算路由指标"""
        # 模拟指标计算
        base_time = route.get('estimated_time', 10.0)
        confidence = route.get('confidence', 0.5)
        
        return RouteMetrics(
            response_time=base_time,
            accuracy_score=confidence,
            resource_usage=route.get('resource_multiplier', 1.0),
            success_rate=min(confidence + 0.2, 1.0),
            cost_score=1.0 / (base_time + 1.0)  # 时间越短，成本效益越高
        )
    
    def _calculate_improvement_score(
        self,
        metrics_before: RouteMetrics,
        metrics_after: RouteMetrics
    ) -> float:
        """计算改进分数"""
        improvements = {}
        
        # 计算各项指标的改进
        improvements['response_time'] = (metrics_before.response_time - metrics_after.response_time) / metrics_before.response_time
        improvements['accuracy_score'] = (metrics_after.accuracy_score - metrics_before.accuracy_score) / max(metrics_before.accuracy_score, 0.1)
        improvements['resource_usage'] = (metrics_before.resource_usage - metrics_after.resource_usage) / metrics_before.resource_usage
        improvements['success_rate'] = (metrics_after.success_rate - metrics_before.success_rate) / max(metrics_before.success_rate, 0.1)
        improvements['cost_score'] = (metrics_after.cost_score - metrics_before.cost_score) / max(metrics_before.cost_score, 0.1)
        
        # 加权计算总改进分数
        total_score = 0.0
        for metric, improvement in improvements.items():
            weight = self.optimization_weights.get(metric, 0.0)
            total_score += weight * improvement
        
        return total_score
    
    def _calculate_agent_score(
        self,
        agent: Dict[str, Any],
        semantic_result: SemanticResult,
        request: Dict[str, Any]
    ) -> float:
        """计算智能体适配分数"""
        score = 0.0
        
        # 能力匹配分数
        agent_capabilities = set(agent.get('capabilities', []))
        required_capabilities = set(self._get_required_capabilities(semantic_result.intent))
        
        if required_capabilities:
            capability_match = len(agent_capabilities & required_capabilities) / len(required_capabilities)
            score += capability_match * 0.4
        
        # 历史性能分数
        agent_id = agent.get('id', 'unknown')
        if agent_id in self.performance_cache:
            historical_metrics = self.performance_cache[agent_id]
            score += historical_metrics.success_rate * 0.3
            score += (1.0 - historical_metrics.response_time / 100.0) * 0.2  # 假设100秒为最大响应时间
        
        # 当前负载分数
        current_load = agent.get('current_load', 0.5)
        score += (1.0 - current_load) * 0.1
        
        return min(score, 1.0)
    
    def _get_required_capabilities(self, intent: IntentType) -> List[str]:
        """获取意图所需的能力"""
        capability_map = {
            IntentType.ARCHITECT: ["design", "planning", "architecture"],
            IntentType.DEVELOP: ["coding", "implementation", "debugging"],
            IntentType.TEST: ["testing", "validation", "quality_assurance"],
            IntentType.DEPLOY: ["deployment", "devops", "infrastructure"],
            IntentType.MONITOR: ["monitoring", "observability", "analytics"],
            IntentType.SECURITY: ["security", "compliance", "vulnerability_assessment"],
            IntentType.UTILITY: ["utility", "helper", "information"]
        }
        return capability_map.get(intent, ["general"])
    
    def _is_agent_suitable(self, intent: IntentType, agent_capabilities: List[str]) -> bool:
        """检查智能体是否适合处理特定意图"""
        required_capabilities = self._get_required_capabilities(intent)
        return any(cap in agent_capabilities for cap in required_capabilities)
    
    def _estimate_execution_time(self, request: Dict[str, Any], agent: Dict[str, Any]) -> float:
        """估算执行时间"""
        base_time = 10.0  # 基础时间
        
        # 根据复杂度调整
        complexity_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 2.0,
            'critical': 3.0
        }
        
        complexity = request.get('complexity', 'medium')
        multiplier = complexity_multipliers.get(complexity, 1.0)
        
        # 根据智能体性能调整
        agent_performance = agent.get('performance_rating', 1.0)
        
        return base_time * multiplier / agent_performance
    
    def _estimate_resource_requirements(self, request: Dict[str, Any]) -> Dict[str, float]:
        """估算资源需求"""
        base_requirements = {
            'cpu': 1.0,
            'memory': 1.0,
            'network': 0.5
        }
        
        complexity = request.get('complexity', 'medium')
        complexity_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 2.0,
            'critical': 3.0
        }
        
        multiplier = complexity_multipliers.get(complexity, 1.0)
        
        return {k: v * multiplier for k, v in base_requirements.items()}
    
    def _can_parallelize(self, request: Dict[str, Any]) -> bool:
        """检查是否可以并行处理"""
        # 简单的并行化检查逻辑
        task_type = request.get('type', '')
        parallelizable_types = ['development', 'testing', 'analysis']
        return task_type in parallelizable_types
    
    def _identify_parallel_tasks(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别可并行的任务"""
        # 简单的任务分解逻辑
        task_type = request.get('type', '')
        
        if task_type == 'development':
            return [
                {'name': 'frontend', 'estimated_time': 5.0},
                {'name': 'backend', 'estimated_time': 7.0},
                {'name': 'database', 'estimated_time': 3.0}
            ]
        elif task_type == 'testing':
            return [
                {'name': 'unit_tests', 'estimated_time': 3.0},
                {'name': 'integration_tests', 'estimated_time': 5.0},
                {'name': 'performance_tests', 'estimated_time': 4.0}
            ]
        
        return []
    
    def _generate_cache_key(self, request: Dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        # 创建请求的标准化表示
        normalized_request = {
            'type': request.get('type', ''),
            'complexity': request.get('complexity', 'medium'),
            'description_hash': hashlib.md5(
                request.get('description', '').encode()
            ).hexdigest()[:8]
        }
        
        cache_string = json.dumps(normalized_request, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _update_stats(self, result: OptimizationResult):
        """更新统计信息"""
        self.stats["total_optimizations"] += 1
        
        if result.improvement_score > 0:
            self.stats["successful_optimizations"] += 1
        
        # 更新平均改进
        total_improvement = (
            self.stats["average_improvement"] * (self.stats["total_optimizations"] - 1) +
            result.improvement_score
        )
        self.stats["average_improvement"] = total_improvement / self.stats["total_optimizations"]
        
        # 计算时间节省
        time_saved = max(0, result.metrics_before.response_time - result.metrics_after.response_time)
        self.stats["total_time_saved"] += time_saved
    
    def _cache_optimization_result(self, result: OptimizationResult):
        """缓存优化结果"""
        # 缓存路由性能数据
        cache_key = result.optimized_route.get('cache_key')
        if cache_key:
            self.performance_cache[cache_key] = result.metrics_after
        
        # 保存到历史记录
        self.route_history.append({
            'timestamp': time.time(),
            'optimization_result': result,
            'improvement_score': result.improvement_score
        })
        
        # 限制历史记录大小
        if len(self.route_history) > 1000:
            self.route_history = self.route_history[-1000:]
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return self.stats.copy()
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """获取性能洞察"""
        if not self.route_history:
            return {"message": "暂无优化历史数据"}
        
        recent_optimizations = self.route_history[-100:]  # 最近100次优化
        
        improvements = [opt['improvement_score'] for opt in recent_optimizations]
        
        return {
            "recent_optimizations": len(recent_optimizations),
            "average_improvement": sum(improvements) / len(improvements) if improvements else 0,
            "best_improvement": max(improvements) if improvements else 0,
            "optimization_trend": "improving" if len(improvements) > 1 and improvements[-1] > improvements[0] else "stable",
            "cache_hit_rate": len(self.performance_cache) / max(len(self.route_history), 1)
        }


# 全局路由优化器实例
_route_optimizer = None


def get_route_optimizer(strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> RouteOptimizer:
    """获取全局路由优化器实例"""
    global _route_optimizer
    if _route_optimizer is None:
        _route_optimizer = RouteOptimizer(strategy)
    return _route_optimizer

