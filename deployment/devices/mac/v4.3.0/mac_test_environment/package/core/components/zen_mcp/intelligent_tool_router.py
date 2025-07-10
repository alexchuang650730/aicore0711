#!/usr/bin/env python3
"""
智能工具路由器
PowerAutomation 4.1 - 基于AI的智能工具选择和路由系统

功能特性:
- AI驱动的工具选择
- 多维度路由决策
- 实时性能优化
- 智能负载均衡
- 上下文感知路由
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import heapq

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoutingStrategy(Enum):
    """路由策略枚举"""
    PERFORMANCE_FIRST = "performance_first"
    COST_OPTIMIZED = "cost_optimized"
    LOAD_BALANCED = "load_balanced"
    QUALITY_FOCUSED = "quality_focused"
    ADAPTIVE = "adaptive"
    CONTEXT_AWARE = "context_aware"

class ToolCapability(Enum):
    """工具能力枚举"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"

@dataclass
class ToolMetrics:
    """工具性能指标"""
    tool_id: str
    success_rate: float = 0.0
    average_execution_time: float = 0.0
    resource_usage: float = 0.0
    quality_score: float = 0.0
    cost_per_execution: float = 0.0
    current_load: int = 0
    max_concurrent: int = 10
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class RoutingContext:
    """路由上下文"""
    task_type: str
    priority: int = 5  # 1-10, 10最高
    deadline: Optional[datetime] = None
    budget_limit: Optional[float] = None
    quality_requirement: float = 0.8  # 0-1
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    historical_context: Dict[str, Any] = field(default_factory=dict)
    resource_constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RoutingDecision:
    """路由决策结果"""
    selected_tool: str
    confidence: float
    reasoning: str
    alternative_tools: List[str]
    estimated_performance: Dict[str, float]
    routing_strategy: RoutingStrategy
    decision_time: datetime = field(default_factory=datetime.now)

class IntelligentToolRouter:
    """智能工具路由器"""
    
    def __init__(self):
        self.tool_metrics: Dict[str, ToolMetrics] = {}
        self.tool_capabilities: Dict[str, List[ToolCapability]] = {}
        self.routing_history: deque = deque(maxlen=1000)
        self.performance_cache: Dict[str, Dict] = {}
        self.user_preferences: Dict[str, Dict] = {}
        
        # AI模型权重（简化的决策权重）
        self.decision_weights = {
            "performance": 0.3,
            "cost": 0.2,
            "quality": 0.25,
            "load": 0.15,
            "context": 0.1
        }
        
        # 路由统计
        self.routing_stats = {
            "total_routes": 0,
            "successful_routes": 0,
            "average_decision_time": 0.0,
            "strategy_usage": defaultdict(int),
            "tool_usage": defaultdict(int)
        }
        
        logger.info("智能工具路由器初始化完成")
    
    async def register_tool(self, tool_id: str, capabilities: List[ToolCapability], 
                          initial_metrics: Optional[ToolMetrics] = None):
        """注册工具及其能力"""
        try:
            self.tool_capabilities[tool_id] = capabilities
            
            if initial_metrics:
                self.tool_metrics[tool_id] = initial_metrics
            else:
                self.tool_metrics[tool_id] = ToolMetrics(
                    tool_id=tool_id,
                    success_rate=0.8,  # 默认成功率
                    average_execution_time=1.0,  # 默认执行时间
                    quality_score=0.8,  # 默认质量分数
                    cost_per_execution=1.0  # 默认成本
                )
            
            logger.info(f"工具已注册: {tool_id} with capabilities: {[c.value for c in capabilities]}")
            
        except Exception as e:
            logger.error(f"注册工具失败: {e}")
            raise
    
    async def route_task(self, task_requirement: str, context: RoutingContext, 
                        strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE) -> RoutingDecision:
        """智能任务路由"""
        try:
            start_time = datetime.now()
            
            # 1. 分析任务需求
            required_capabilities = await self._analyze_task_requirements(task_requirement)
            
            # 2. 筛选候选工具
            candidate_tools = await self._filter_candidate_tools(required_capabilities, context)
            
            if not candidate_tools:
                raise ValueError("没有找到合适的工具")
            
            # 3. 根据策略选择最佳工具
            selected_tool, confidence, reasoning = await self._select_best_tool(
                candidate_tools, context, strategy
            )
            
            # 4. 生成路由决策
            decision = RoutingDecision(
                selected_tool=selected_tool,
                confidence=confidence,
                reasoning=reasoning,
                alternative_tools=[t for t in candidate_tools if t != selected_tool][:3],
                estimated_performance=await self._estimate_performance(selected_tool, context),
                routing_strategy=strategy
            )
            
            # 5. 更新统计和历史
            decision_time = (datetime.now() - start_time).total_seconds()
            await self._update_routing_stats(decision, decision_time)
            self.routing_history.append(decision)
            
            logger.info(f"路由决策完成: {selected_tool} (置信度: {confidence:.2f})")
            return decision
            
        except Exception as e:
            logger.error(f"任务路由失败: {e}")
            raise
    
    async def _analyze_task_requirements(self, task_requirement: str) -> List[ToolCapability]:
        """分析任务需求，识别所需能力"""
        # 简化的需求分析（实际应用中可使用NLP模型）
        capability_keywords = {
            ToolCapability.CODE_ANALYSIS: ["分析", "检查", "审查", "扫描"],
            ToolCapability.CODE_GENERATION: ["生成", "创建", "编写", "构建"],
            ToolCapability.DEBUGGING: ["调试", "修复", "错误", "bug"],
            ToolCapability.PERFORMANCE_OPTIMIZATION: ["优化", "性能", "加速", "效率"],
            ToolCapability.TESTING: ["测试", "验证", "检验"],
            ToolCapability.DEPLOYMENT: ["部署", "发布", "上线"],
            ToolCapability.MONITORING: ["监控", "观察", "跟踪"],
            ToolCapability.SECURITY: ["安全", "漏洞", "防护"],
            ToolCapability.DOCUMENTATION: ["文档", "注释", "说明"],
            ToolCapability.REFACTORING: ["重构", "重写", "改进"]
        }
        
        required_capabilities = []
        task_lower = task_requirement.lower()
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_capabilities.append(capability)
        
        # 如果没有匹配到特定能力，默认为代码分析
        if not required_capabilities:
            required_capabilities.append(ToolCapability.CODE_ANALYSIS)
        
        return required_capabilities
    
    async def _filter_candidate_tools(self, required_capabilities: List[ToolCapability], 
                                    context: RoutingContext) -> List[str]:
        """筛选候选工具"""
        candidate_tools = []
        
        for tool_id, tool_capabilities in self.tool_capabilities.items():
            # 检查能力匹配
            if any(cap in tool_capabilities for cap in required_capabilities):
                # 检查资源约束
                metrics = self.tool_metrics[tool_id]
                if metrics.current_load < metrics.max_concurrent:
                    # 检查质量要求
                    if metrics.quality_score >= context.quality_requirement:
                        candidate_tools.append(tool_id)
        
        return candidate_tools
    
    async def _select_best_tool(self, candidate_tools: List[str], context: RoutingContext, 
                              strategy: RoutingStrategy) -> Tuple[str, float, str]:
        """选择最佳工具"""
        if len(candidate_tools) == 1:
            return candidate_tools[0], 1.0, "唯一可用工具"
        
        # 计算每个工具的综合评分
        tool_scores = {}
        
        for tool_id in candidate_tools:
            score = await self._calculate_tool_score(tool_id, context, strategy)
            tool_scores[tool_id] = score
        
        # 选择最高分工具
        best_tool = max(tool_scores, key=tool_scores.get)
        best_score = tool_scores[best_tool]
        
        # 计算置信度
        scores = list(tool_scores.values())
        confidence = self._calculate_confidence(best_score, scores)
        
        # 生成推理说明
        reasoning = await self._generate_reasoning(best_tool, tool_scores, strategy)
        
        return best_tool, confidence, reasoning
    
    async def _calculate_tool_score(self, tool_id: str, context: RoutingContext, 
                                  strategy: RoutingStrategy) -> float:
        """计算工具综合评分"""
        metrics = self.tool_metrics[tool_id]
        
        # 基础评分组件
        performance_score = metrics.success_rate * (1 / max(metrics.average_execution_time, 0.1))
        cost_score = 1 / max(metrics.cost_per_execution, 0.1)
        quality_score = metrics.quality_score
        load_score = 1 - (metrics.current_load / max(metrics.max_concurrent, 1))
        
        # 上下文评分
        context_score = await self._calculate_context_score(tool_id, context)
        
        # 根据策略调整权重
        weights = self._get_strategy_weights(strategy)
        
        # 计算加权总分
        total_score = (
            performance_score * weights["performance"] +
            cost_score * weights["cost"] +
            quality_score * weights["quality"] +
            load_score * weights["load"] +
            context_score * weights["context"]
        )
        
        return total_score
    
    def _get_strategy_weights(self, strategy: RoutingStrategy) -> Dict[str, float]:
        """获取策略权重"""
        strategy_weights = {
            RoutingStrategy.PERFORMANCE_FIRST: {
                "performance": 0.5, "cost": 0.1, "quality": 0.2, "load": 0.1, "context": 0.1
            },
            RoutingStrategy.COST_OPTIMIZED: {
                "performance": 0.2, "cost": 0.4, "quality": 0.2, "load": 0.1, "context": 0.1
            },
            RoutingStrategy.LOAD_BALANCED: {
                "performance": 0.2, "cost": 0.2, "quality": 0.2, "load": 0.3, "context": 0.1
            },
            RoutingStrategy.QUALITY_FOCUSED: {
                "performance": 0.2, "cost": 0.1, "quality": 0.4, "load": 0.1, "context": 0.2
            },
            RoutingStrategy.ADAPTIVE: self.decision_weights,
            RoutingStrategy.CONTEXT_AWARE: {
                "performance": 0.2, "cost": 0.15, "quality": 0.25, "load": 0.1, "context": 0.3
            }
        }
        
        return strategy_weights.get(strategy, self.decision_weights)
    
    async def _calculate_context_score(self, tool_id: str, context: RoutingContext) -> float:
        """计算上下文评分"""
        score = 0.5  # 基础分数
        
        # 用户偏好
        user_prefs = context.user_preferences
        if "preferred_tools" in user_prefs and tool_id in user_prefs["preferred_tools"]:
            score += 0.2
        
        # 历史成功率
        if tool_id in context.historical_context:
            historical_success = context.historical_context[tool_id].get("success_rate", 0.5)
            score += historical_success * 0.3
        
        # 时间约束
        if context.deadline:
            metrics = self.tool_metrics[tool_id]
            time_remaining = (context.deadline - datetime.now()).total_seconds()
            if metrics.average_execution_time <= time_remaining:
                score += 0.2
            else:
                score -= 0.3
        
        return min(max(score, 0.0), 1.0)
    
    def _calculate_confidence(self, best_score: float, all_scores: List[float]) -> float:
        """计算决策置信度"""
        if len(all_scores) <= 1:
            return 1.0
        
        sorted_scores = sorted(all_scores, reverse=True)
        score_gap = sorted_scores[0] - sorted_scores[1]
        max_possible_gap = sorted_scores[0]
        
        # 基于分数差距和绝对分数计算置信度
        gap_confidence = score_gap / max(max_possible_gap, 0.1)
        absolute_confidence = best_score
        
        return min((gap_confidence + absolute_confidence) / 2, 1.0)
    
    async def _generate_reasoning(self, selected_tool: str, tool_scores: Dict[str, float], 
                                strategy: RoutingStrategy) -> str:
        """生成推理说明"""
        metrics = self.tool_metrics[selected_tool]
        score = tool_scores[selected_tool]
        
        reasoning_parts = [
            f"选择工具 {selected_tool}",
            f"综合评分: {score:.3f}",
            f"成功率: {metrics.success_rate:.2f}",
            f"平均执行时间: {metrics.average_execution_time:.2f}s",
            f"质量分数: {metrics.quality_score:.2f}",
            f"当前负载: {metrics.current_load}/{metrics.max_concurrent}",
            f"路由策略: {strategy.value}"
        ]
        
        return " | ".join(reasoning_parts)
    
    async def _estimate_performance(self, tool_id: str, context: RoutingContext) -> Dict[str, float]:
        """估算工具性能"""
        metrics = self.tool_metrics[tool_id]
        
        # 基于历史数据和当前负载估算
        load_factor = 1 + (metrics.current_load / max(metrics.max_concurrent, 1)) * 0.5
        
        estimated_performance = {
            "success_probability": metrics.success_rate,
            "estimated_time": metrics.average_execution_time * load_factor,
            "estimated_cost": metrics.cost_per_execution,
            "quality_expectation": metrics.quality_score,
            "resource_usage": metrics.resource_usage * load_factor
        }
        
        return estimated_performance
    
    async def _update_routing_stats(self, decision: RoutingDecision, decision_time: float):
        """更新路由统计"""
        self.routing_stats["total_routes"] += 1
        self.routing_stats["strategy_usage"][decision.routing_strategy.value] += 1
        self.routing_stats["tool_usage"][decision.selected_tool] += 1
        
        # 更新平均决策时间
        total_time = (self.routing_stats["average_decision_time"] * 
                     (self.routing_stats["total_routes"] - 1) + decision_time)
        self.routing_stats["average_decision_time"] = total_time / self.routing_stats["total_routes"]
    
    async def update_tool_metrics(self, tool_id: str, execution_result: Dict[str, Any]):
        """更新工具性能指标"""
        try:
            if tool_id not in self.tool_metrics:
                return
            
            metrics = self.tool_metrics[tool_id]
            
            # 更新成功率
            success = execution_result.get("success", False)
            total_executions = execution_result.get("total_executions", 1)
            
            new_success_rate = (
                (metrics.success_rate * (total_executions - 1) + (1 if success else 0)) / 
                total_executions
            )
            metrics.success_rate = new_success_rate
            
            # 更新执行时间
            execution_time = execution_result.get("execution_time", metrics.average_execution_time)
            metrics.average_execution_time = (
                (metrics.average_execution_time * (total_executions - 1) + execution_time) / 
                total_executions
            )
            
            # 更新质量分数
            if "quality_score" in execution_result:
                quality_score = execution_result["quality_score"]
                metrics.quality_score = (
                    (metrics.quality_score * (total_executions - 1) + quality_score) / 
                    total_executions
                )
            
            # 更新负载
            if "load_change" in execution_result:
                metrics.current_load += execution_result["load_change"]
                metrics.current_load = max(0, min(metrics.current_load, metrics.max_concurrent))
            
            metrics.last_updated = datetime.now()
            
            logger.info(f"工具指标已更新: {tool_id}")
            
        except Exception as e:
            logger.error(f"更新工具指标失败: {e}")
    
    async def get_routing_analytics(self) -> Dict[str, Any]:
        """获取路由分析数据"""
        return {
            "routing_stats": dict(self.routing_stats),
            "tool_performance": {
                tool_id: {
                    "success_rate": metrics.success_rate,
                    "average_execution_time": metrics.average_execution_time,
                    "quality_score": metrics.quality_score,
                    "current_load": metrics.current_load,
                    "usage_count": self.routing_stats["tool_usage"][tool_id]
                }
                for tool_id, metrics in self.tool_metrics.items()
            },
            "strategy_distribution": dict(self.routing_stats["strategy_usage"]),
            "recent_decisions": [
                {
                    "tool": decision.selected_tool,
                    "confidence": decision.confidence,
                    "strategy": decision.routing_strategy.value,
                    "time": decision.decision_time.isoformat()
                }
                for decision in list(self.routing_history)[-10:]
            ]
        }
    
    async def optimize_routing_weights(self):
        """优化路由权重"""
        try:
            # 基于历史路由结果优化决策权重
            if len(self.routing_history) < 10:
                return
            
            # 分析成功的路由决策
            successful_decisions = [
                d for d in self.routing_history 
                if d.confidence > 0.7  # 假设高置信度决策更可能成功
            ]
            
            if not successful_decisions:
                return
            
            # 简化的权重优化（实际应用中可使用机器学习）
            strategy_performance = defaultdict(list)
            
            for decision in successful_decisions:
                strategy_performance[decision.routing_strategy].append(decision.confidence)
            
            # 更新权重（简化版本）
            best_strategy = max(strategy_performance, key=lambda s: np.mean(strategy_performance[s]))
            self.decision_weights = self._get_strategy_weights(best_strategy)
            
            logger.info(f"路由权重已优化，最佳策略: {best_strategy.value}")
            
        except Exception as e:
            logger.error(f"优化路由权重失败: {e}")
    
    async def get_tool_recommendations(self, task_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """获取工具推荐"""
        try:
            # 创建简化的路由上下文
            context = RoutingContext(task_type=task_type)
            required_capabilities = await self._analyze_task_requirements(task_type)
            candidate_tools = await self._filter_candidate_tools(required_capabilities, context)
            
            # 计算推荐分数
            recommendations = []
            for tool_id in candidate_tools:
                score = await self._calculate_tool_score(tool_id, context, RoutingStrategy.ADAPTIVE)
                metrics = self.tool_metrics[tool_id]
                
                recommendations.append({
                    "tool_id": tool_id,
                    "score": score,
                    "success_rate": metrics.success_rate,
                    "average_time": metrics.average_execution_time,
                    "quality_score": metrics.quality_score,
                    "current_load": f"{metrics.current_load}/{metrics.max_concurrent}",
                    "capabilities": [cap.value for cap in self.tool_capabilities[tool_id]]
                })
            
            # 按分数排序
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"获取工具推荐失败: {e}")
            return []

# 示例使用
async def main():
    """示例主函数"""
    router = IntelligentToolRouter()
    
    # 注册工具
    await router.register_tool("code_analyzer", [ToolCapability.CODE_ANALYSIS])
    await router.register_tool("performance_optimizer", [ToolCapability.PERFORMANCE_OPTIMIZATION])
    await router.register_tool("test_generator", [ToolCapability.TESTING])
    
    # 创建路由上下文
    context = RoutingContext(
        task_type="代码性能优化",
        priority=8,
        quality_requirement=0.9
    )
    
    # 执行路由
    decision = await router.route_task("优化Python代码性能", context)
    print(f"路由决策: {decision.selected_tool} (置信度: {decision.confidence:.2f})")
    print(f"推理: {decision.reasoning}")
    
    # 获取分析数据
    analytics = await router.get_routing_analytics()
    print(f"路由统计: {analytics['routing_stats']}")

if __name__ == "__main__":
    asyncio.run(main())

