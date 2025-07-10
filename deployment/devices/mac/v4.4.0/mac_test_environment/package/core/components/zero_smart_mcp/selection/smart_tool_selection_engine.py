#!/usr/bin/env python3
"""
Smart Tool Engine智能选择层

基于AI驱动的智能工具选择引擎，能够根据任务需求自动推荐最适合的MCP工具。
支持多种选择策略、成本优化、性能预测和学习反馈机制。

主要功能：
- AI驱动的工具推荐
- 多维度工具评分
- 成本效益分析
- 性能预测
- 用户偏好学习
- 工具组合优化

作者: PowerAutomation Team
版本: 4.1.0
日期: 2025-01-07
"""

import asyncio
import json
import uuid
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import pickle
import hashlib
from pathlib import Path
import math

from ..models.tool_models import MCPTool, TaskRequirement, ToolRecommendation, ToolCapability, ToolStatus

logger = logging.getLogger(__name__)

class SelectionStrategy(Enum):
    """选择策略"""
    BEST_MATCH = "best_match"  # 最佳匹配
    COST_OPTIMIZED = "cost_optimized"  # 成本优化
    PERFORMANCE_FIRST = "performance_first"  # 性能优先
    BALANCED = "balanced"  # 平衡策略
    USER_PREFERENCE = "user_preference"  # 用户偏好
    ENSEMBLE = "ensemble"  # 集成策略

class RecommendationReason(Enum):
    """推荐原因"""
    CAPABILITY_MATCH = "capability_match"
    PERFORMANCE_SCORE = "performance_score"
    COST_EFFICIENCY = "cost_efficiency"
    USER_HISTORY = "user_history"
    POPULARITY = "popularity"
    COMPATIBILITY = "compatibility"
    NOVELTY = "novelty"

@dataclass
class ToolScore:
    """工具评分"""
    tool_id: str
    overall_score: float
    capability_score: float
    performance_score: float
    cost_score: float
    popularity_score: float
    compatibility_score: float
    user_preference_score: float
    confidence: float
    reasons: List[RecommendationReason] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    preferences: Dict[str, float] = field(default_factory=dict)
    usage_history: List[Dict[str, Any]] = field(default_factory=list)
    favorite_tools: Set[str] = field(default_factory=set)
    avoided_tools: Set[str] = field(default_factory=set)
    skill_level: str = "intermediate"  # beginner, intermediate, advanced
    domain_expertise: List[str] = field(default_factory=list)
    cost_sensitivity: float = 0.5  # 0-1, 越高越敏感
    performance_priority: float = 0.7  # 0-1, 越高越重视性能
    learning_rate: float = 0.1  # 学习速率
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class ToolPerformanceMetrics:
    """工具性能指标"""
    tool_id: str
    success_rate: float = 0.0
    average_execution_time: float = 0.0
    error_rate: float = 0.0
    user_satisfaction: float = 0.0
    usage_frequency: int = 0
    last_used: Optional[datetime] = None
    performance_trend: float = 0.0  # 性能趋势，正数表示改善
    reliability_score: float = 0.0

class SmartToolSelectionEngine:
    """Smart Tool Engine智能选择层"""
    
    def __init__(self, config_path: str = "./smart_tool_config.json"):
        """初始化智能选择引擎"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 核心组件
        self.available_tools: Dict[str, MCPTool] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.tool_metrics: Dict[str, ToolPerformanceMetrics] = {}
        self.recommendation_cache: Dict[str, List[ToolRecommendation]] = {}
        
        # AI模型和嵌入
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.similarity_threshold = self.config.get("similarity_threshold", 0.7)
        
        # 选择参数
        self.default_strategy = SelectionStrategy(self.config.get("default_strategy", "balanced"))
        self.max_recommendations = self.config.get("max_recommendations", 10)
        self.cache_ttl = self.config.get("cache_ttl", 3600)  # 1小时
        
        # 评分权重
        self.scoring_weights = self.config.get("scoring_weights", {
            "capability": 0.3,
            "performance": 0.25,
            "cost": 0.15,
            "popularity": 0.1,
            "compatibility": 0.1,
            "user_preference": 0.1
        })
        
        # 学习参数
        self.enable_learning = self.config.get("enable_learning", True)
        self.feedback_weight = self.config.get("feedback_weight", 0.2)
        
        # 存储路径
        self.data_dir = Path(self.config.get("data_dir", "./smart_tool_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载持久化数据
        self._load_persistent_data()
        
        logger.info("Smart Tool Engine智能选择层初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "similarity_threshold": 0.7,
            "default_strategy": "balanced",
            "max_recommendations": 10,
            "cache_ttl": 3600,
            "scoring_weights": {
                "capability": 0.3,
                "performance": 0.25,
                "cost": 0.15,
                "popularity": 0.1,
                "compatibility": 0.1,
                "user_preference": 0.1
            },
            "enable_learning": True,
            "feedback_weight": 0.2,
            "data_dir": "./smart_tool_data",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "enable_ensemble": True,
            "diversity_factor": 0.2
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _load_persistent_data(self):
        """加载持久化数据"""
        try:
            # 加载用户画像
            profiles_file = self.data_dir / "user_profiles.pkl"
            if profiles_file.exists():
                with open(profiles_file, 'rb') as f:
                    self.user_profiles = pickle.load(f)
            
            # 加载工具性能指标
            metrics_file = self.data_dir / "tool_metrics.pkl"
            if metrics_file.exists():
                with open(metrics_file, 'rb') as f:
                    self.tool_metrics = pickle.load(f)
            
            # 加载嵌入缓存
            embeddings_file = self.data_dir / "embeddings_cache.pkl"
            if embeddings_file.exists():
                with open(embeddings_file, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
            
            logger.info("持久化数据加载完成")
            
        except Exception as e:
            logger.warning(f"加载持久化数据失败: {e}")
    
    def _save_persistent_data(self):
        """保存持久化数据"""
        try:
            # 保存用户画像
            with open(self.data_dir / "user_profiles.pkl", 'wb') as f:
                pickle.dump(self.user_profiles, f)
            
            # 保存工具性能指标
            with open(self.data_dir / "tool_metrics.pkl", 'wb') as f:
                pickle.dump(self.tool_metrics, f)
            
            # 保存嵌入缓存
            with open(self.data_dir / "embeddings_cache.pkl", 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            
            logger.debug("持久化数据保存完成")
            
        except Exception as e:
            logger.error(f"保存持久化数据失败: {e}")
    
    async def register_tools(self, tools: List[MCPTool]):
        """注册工具"""
        for tool in tools:
            self.available_tools[tool.tool_id] = tool
            
            # 初始化工具性能指标
            if tool.tool_id not in self.tool_metrics:
                self.tool_metrics[tool.tool_id] = ToolPerformanceMetrics(
                    tool_id=tool.tool_id,
                    reliability_score=0.8  # 默认可靠性评分
                )
        
        logger.info(f"注册 {len(tools)} 个工具")
    
    async def recommend_tools(self, task_requirement: TaskRequirement, 
                            user_id: str = None,
                            strategy: SelectionStrategy = None,
                            max_results: int = None) -> List[ToolRecommendation]:
        """推荐工具"""
        if strategy is None:
            strategy = self.default_strategy
        
        if max_results is None:
            max_results = self.max_recommendations
        
        # 检查缓存
        cache_key = self._generate_cache_key(task_requirement, user_id, strategy)
        if cache_key in self.recommendation_cache:
            cached_recommendations = self.recommendation_cache[cache_key]
            if self._is_cache_valid(cached_recommendations):
                logger.debug(f"使用缓存的推荐结果: {cache_key}")
                return cached_recommendations[:max_results]
        
        # 获取用户画像
        user_profile = self._get_user_profile(user_id) if user_id else None
        
        # 计算工具评分
        tool_scores = await self._calculate_tool_scores(task_requirement, user_profile, strategy)
        
        # 生成推荐
        recommendations = await self._generate_recommendations(
            tool_scores, task_requirement, user_profile, strategy, max_results
        )
        
        # 缓存结果
        self.recommendation_cache[cache_key] = recommendations
        
        logger.info(f"为任务生成 {len(recommendations)} 个工具推荐")
        return recommendations
    
    def _generate_cache_key(self, task_requirement: TaskRequirement, 
                          user_id: str, strategy: SelectionStrategy) -> str:
        """生成缓存键"""
        content = f"{task_requirement.description}_{task_requirement.required_capabilities}_{user_id}_{strategy.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, recommendations: List[ToolRecommendation]) -> bool:
        """检查缓存是否有效"""
        if not recommendations:
            return False
        
        # 检查时间戳
        first_rec = recommendations[0]
        if hasattr(first_rec, 'timestamp'):
            age = (datetime.now() - first_rec.timestamp).total_seconds()
            return age < self.cache_ttl
        
        return False
    
    def _get_user_profile(self, user_id: str) -> UserProfile:
        """获取用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
        
        return self.user_profiles[user_id]
    
    async def _calculate_tool_scores(self, task_requirement: TaskRequirement,
                                   user_profile: Optional[UserProfile],
                                   strategy: SelectionStrategy) -> List[ToolScore]:
        """计算工具评分"""
        tool_scores = []
        
        for tool in self.available_tools.values():
            # 基础能力匹配评分
            capability_score = await self._calculate_capability_score(tool, task_requirement)
            
            # 性能评分
            performance_score = await self._calculate_performance_score(tool)
            
            # 成本评分
            cost_score = await self._calculate_cost_score(tool, task_requirement)
            
            # 流行度评分
            popularity_score = await self._calculate_popularity_score(tool)
            
            # 兼容性评分
            compatibility_score = await self._calculate_compatibility_score(tool, task_requirement)
            
            # 用户偏好评分
            user_preference_score = await self._calculate_user_preference_score(tool, user_profile)
            
            # 综合评分
            overall_score = self._calculate_overall_score(
                capability_score, performance_score, cost_score,
                popularity_score, compatibility_score, user_preference_score,
                strategy
            )
            
            # 置信度计算
            confidence = self._calculate_confidence(
                capability_score, performance_score, tool, task_requirement
            )
            
            # 推荐原因
            reasons = self._determine_recommendation_reasons(
                capability_score, performance_score, cost_score,
                popularity_score, user_preference_score
            )
            
            tool_score = ToolScore(
                tool_id=tool.tool_id,
                overall_score=overall_score,
                capability_score=capability_score,
                performance_score=performance_score,
                cost_score=cost_score,
                popularity_score=popularity_score,
                compatibility_score=compatibility_score,
                user_preference_score=user_preference_score,
                confidence=confidence,
                reasons=reasons,
                details={
                    "tool_name": tool.name,
                    "category": tool.category.value,
                    "capabilities": [cap.name for cap in tool.capabilities]
                }
            )
            
            tool_scores.append(tool_score)
        
        # 按综合评分排序
        tool_scores.sort(key=lambda x: x.overall_score, reverse=True)
        
        return tool_scores
    
    async def _calculate_capability_score(self, tool: MCPTool, 
                                        task_requirement: TaskRequirement) -> float:
        """计算能力匹配评分"""
        if not task_requirement.required_capabilities:
            return 0.5  # 默认评分
        
        tool_capabilities = {cap.name for cap in tool.capabilities}
        required_capabilities = set(task_requirement.required_capabilities)
        
        if not required_capabilities:
            return 0.5
        
        # 计算交集比例
        intersection = tool_capabilities.intersection(required_capabilities)
        capability_match_ratio = len(intersection) / len(required_capabilities)
        
        # 考虑能力的置信度
        confidence_bonus = 0.0
        for cap in tool.capabilities:
            if cap.name in required_capabilities:
                confidence_bonus += cap.confidence * 0.1
        
        # 语义相似性评分（如果有嵌入模型）
        semantic_score = await self._calculate_semantic_similarity(tool, task_requirement)
        
        # 综合评分
        final_score = (
            capability_match_ratio * 0.6 +
            min(confidence_bonus, 0.3) +
            semantic_score * 0.1
        )
        
        return min(final_score, 1.0)
    
    async def _calculate_semantic_similarity(self, tool: MCPTool, 
                                           task_requirement: TaskRequirement) -> float:
        """计算语义相似性"""
        try:
            # 获取工具描述嵌入
            tool_text = f"{tool.name} {tool.description} {' '.join([cap.name for cap in tool.capabilities])}"
            tool_embedding = await self._get_text_embedding(tool_text)
            
            # 获取任务需求嵌入
            task_text = f"{task_requirement.description} {' '.join(task_requirement.required_capabilities or [])}"
            task_embedding = await self._get_text_embedding(task_text)
            
            # 计算余弦相似性
            if tool_embedding is not None and task_embedding is not None:
                similarity = np.dot(tool_embedding, task_embedding) / (
                    np.linalg.norm(tool_embedding) * np.linalg.norm(task_embedding)
                )
                return max(0.0, similarity)
            
        except Exception as e:
            logger.debug(f"计算语义相似性失败: {e}")
        
        return 0.0
    
    async def _get_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """获取文本嵌入"""
        # 简化实现：使用缓存的随机嵌入
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash not in self.embeddings_cache:
            # 在实际应用中，这里应该调用真实的嵌入模型
            # 例如：sentence-transformers, OpenAI embeddings等
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.normal(0, 1, 384)  # 384维嵌入
            embedding = embedding / np.linalg.norm(embedding)  # 归一化
            self.embeddings_cache[text_hash] = embedding
        
        return self.embeddings_cache[text_hash]
    
    async def _calculate_performance_score(self, tool: MCPTool) -> float:
        """计算性能评分"""
        metrics = self.tool_metrics.get(tool.tool_id)
        if not metrics:
            return 0.6  # 默认评分
        
        # 成功率权重
        success_score = metrics.success_rate * 0.4
        
        # 可靠性权重
        reliability_score = metrics.reliability_score * 0.3
        
        # 用户满意度权重
        satisfaction_score = metrics.user_satisfaction * 0.2
        
        # 性能趋势权重
        trend_score = min(max(metrics.performance_trend + 0.5, 0), 1) * 0.1
        
        return success_score + reliability_score + satisfaction_score + trend_score
    
    async def _calculate_cost_score(self, tool: MCPTool, 
                                  task_requirement: TaskRequirement) -> float:
        """计算成本评分"""
        # 简化的成本模型
        base_cost = 0.5  # 基础成本
        
        # 根据工具复杂度调整成本
        complexity_factor = len(tool.capabilities) * 0.05
        
        # 根据任务复杂度调整成本
        task_complexity = task_requirement.complexity_level or "medium"
        complexity_multiplier = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.3
        }.get(task_complexity, 1.0)
        
        estimated_cost = (base_cost + complexity_factor) * complexity_multiplier
        
        # 成本评分（成本越低评分越高）
        cost_score = max(0, 1.0 - estimated_cost)
        
        return cost_score
    
    async def _calculate_popularity_score(self, tool: MCPTool) -> float:
        """计算流行度评分"""
        metrics = self.tool_metrics.get(tool.tool_id)
        if not metrics:
            return 0.5
        
        # 使用频率归一化
        max_usage = max([m.usage_frequency for m in self.tool_metrics.values()], default=1)
        usage_score = metrics.usage_frequency / max_usage if max_usage > 0 else 0
        
        # 最近使用时间
        recency_score = 0.5
        if metrics.last_used:
            days_since_use = (datetime.now() - metrics.last_used).days
            recency_score = max(0, 1.0 - days_since_use / 30)  # 30天内的使用
        
        return (usage_score * 0.7 + recency_score * 0.3)
    
    async def _calculate_compatibility_score(self, tool: MCPTool, 
                                           task_requirement: TaskRequirement) -> float:
        """计算兼容性评分"""
        score = 0.8  # 基础兼容性评分
        
        # 检查环境要求
        if hasattr(task_requirement, 'environment_constraints'):
            constraints = task_requirement.environment_constraints or {}
            
            # 操作系统兼容性
            if 'os' in constraints:
                required_os = constraints['os']
                if hasattr(tool, 'supported_os'):
                    if required_os in tool.supported_os:
                        score += 0.1
                    else:
                        score -= 0.2
            
            # 依赖兼容性
            if 'dependencies' in constraints:
                # 简化的依赖检查
                score += 0.1
        
        return min(max(score, 0), 1.0)
    
    async def _calculate_user_preference_score(self, tool: MCPTool, 
                                             user_profile: Optional[UserProfile]) -> float:
        """计算用户偏好评分"""
        if not user_profile:
            return 0.5
        
        score = 0.5
        
        # 收藏工具
        if tool.tool_id in user_profile.favorite_tools:
            score += 0.3
        
        # 避免的工具
        if tool.tool_id in user_profile.avoided_tools:
            score -= 0.4
        
        # 类别偏好
        category_pref = user_profile.preferences.get(tool.category.value, 0.5)
        score += (category_pref - 0.5) * 0.2
        
        # 使用历史
        for usage in user_profile.usage_history[-10:]:  # 最近10次使用
            if usage.get('tool_id') == tool.tool_id:
                rating = usage.get('rating', 0.5)
                score += (rating - 0.5) * 0.1
        
        return min(max(score, 0), 1.0)
    
    def _calculate_overall_score(self, capability_score: float, performance_score: float,
                               cost_score: float, popularity_score: float,
                               compatibility_score: float, user_preference_score: float,
                               strategy: SelectionStrategy) -> float:
        """计算综合评分"""
        weights = self.scoring_weights.copy()
        
        # 根据策略调整权重
        if strategy == SelectionStrategy.PERFORMANCE_FIRST:
            weights["performance"] *= 2.0
            weights["capability"] *= 1.5
        elif strategy == SelectionStrategy.COST_OPTIMIZED:
            weights["cost"] *= 2.5
            weights["performance"] *= 0.8
        elif strategy == SelectionStrategy.USER_PREFERENCE:
            weights["user_preference"] *= 3.0
            weights["popularity"] *= 1.5
        elif strategy == SelectionStrategy.BEST_MATCH:
            weights["capability"] *= 2.0
            weights["compatibility"] *= 1.5
        
        # 归一化权重
        total_weight = sum(weights.values())
        for key in weights:
            weights[key] /= total_weight
        
        # 计算加权评分
        overall_score = (
            capability_score * weights["capability"] +
            performance_score * weights["performance"] +
            cost_score * weights["cost"] +
            popularity_score * weights["popularity"] +
            compatibility_score * weights["compatibility"] +
            user_preference_score * weights["user_preference"]
        )
        
        return overall_score
    
    def _calculate_confidence(self, capability_score: float, performance_score: float,
                            tool: MCPTool, task_requirement: TaskRequirement) -> float:
        """计算置信度"""
        # 基于能力匹配和性能的置信度
        base_confidence = (capability_score + performance_score) / 2
        
        # 工具成熟度调整
        maturity_bonus = 0.0
        if hasattr(tool, 'version'):
            try:
                version_parts = tool.version.split('.')
                major_version = int(version_parts[0])
                if major_version >= 1:
                    maturity_bonus = 0.1
            except:
                pass
        
        # 文档完整性调整
        doc_bonus = 0.0
        if tool.documentation_url or tool.examples:
            doc_bonus = 0.05
        
        confidence = base_confidence + maturity_bonus + doc_bonus
        return min(confidence, 1.0)
    
    def _determine_recommendation_reasons(self, capability_score: float, performance_score: float,
                                        cost_score: float, popularity_score: float,
                                        user_preference_score: float) -> List[RecommendationReason]:
        """确定推荐原因"""
        reasons = []
        
        if capability_score > 0.8:
            reasons.append(RecommendationReason.CAPABILITY_MATCH)
        
        if performance_score > 0.8:
            reasons.append(RecommendationReason.PERFORMANCE_SCORE)
        
        if cost_score > 0.8:
            reasons.append(RecommendationReason.COST_EFFICIENCY)
        
        if popularity_score > 0.7:
            reasons.append(RecommendationReason.POPULARITY)
        
        if user_preference_score > 0.7:
            reasons.append(RecommendationReason.USER_HISTORY)
        
        return reasons
    
    async def _generate_recommendations(self, tool_scores: List[ToolScore],
                                      task_requirement: TaskRequirement,
                                      user_profile: Optional[UserProfile],
                                      strategy: SelectionStrategy,
                                      max_results: int) -> List[ToolRecommendation]:
        """生成推荐"""
        recommendations = []
        
        # 应用多样性过滤
        if self.config.get("enable_diversity", True):
            tool_scores = self._apply_diversity_filter(tool_scores)
        
        for i, score in enumerate(tool_scores[:max_results]):
            tool = self.available_tools[score.tool_id]
            
            recommendation = ToolRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                tool_id=tool.tool_id,
                task_id=task_requirement.task_id,
                user_id=user_profile.user_id if user_profile else None,
                score=score.overall_score,
                confidence=score.confidence,
                rank=i + 1,
                reasons=score.reasons,
                explanation=self._generate_explanation(tool, score, task_requirement),
                estimated_cost=self._estimate_tool_cost(tool, task_requirement),
                estimated_time=self._estimate_execution_time(tool, task_requirement),
                alternatives=[],  # 可以添加替代工具
                metadata={
                    "strategy": strategy.value,
                    "score_breakdown": {
                        "capability": score.capability_score,
                        "performance": score.performance_score,
                        "cost": score.cost_score,
                        "popularity": score.popularity_score,
                        "compatibility": score.compatibility_score,
                        "user_preference": score.user_preference_score
                    },
                    "tool_details": score.details
                },
                timestamp=datetime.now()
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _apply_diversity_filter(self, tool_scores: List[ToolScore]) -> List[ToolScore]:
        """应用多样性过滤"""
        if not tool_scores:
            return tool_scores
        
        diversity_factor = self.config.get("diversity_factor", 0.2)
        filtered_scores = [tool_scores[0]]  # 保留最高分的工具
        
        for score in tool_scores[1:]:
            tool = self.available_tools[score.tool_id]
            
            # 检查与已选工具的多样性
            is_diverse = True
            for selected_score in filtered_scores:
                selected_tool = self.available_tools[selected_score.tool_id]
                
                # 检查类别多样性
                if tool.category == selected_tool.category:
                    # 如果同类别，需要更高的评分才能入选
                    required_score = selected_score.overall_score + diversity_factor
                    if score.overall_score < required_score:
                        is_diverse = False
                        break
            
            if is_diverse:
                filtered_scores.append(score)
        
        return filtered_scores
    
    def _generate_explanation(self, tool: MCPTool, score: ToolScore, 
                            task_requirement: TaskRequirement) -> str:
        """生成推荐解释"""
        explanations = []
        
        # 基于推荐原因生成解释
        if RecommendationReason.CAPABILITY_MATCH in score.reasons:
            explanations.append(f"该工具的能力与任务需求高度匹配（匹配度：{score.capability_score:.1%}）")
        
        if RecommendationReason.PERFORMANCE_SCORE in score.reasons:
            explanations.append(f"该工具具有优秀的性能表现（性能评分：{score.performance_score:.1%}）")
        
        if RecommendationReason.COST_EFFICIENCY in score.reasons:
            explanations.append(f"该工具具有良好的成本效益（成本评分：{score.cost_score:.1%}）")
        
        if RecommendationReason.POPULARITY in score.reasons:
            explanations.append(f"该工具在社区中广受欢迎（流行度：{score.popularity_score:.1%}）")
        
        if RecommendationReason.USER_HISTORY in score.reasons:
            explanations.append(f"基于您的使用历史，您可能会喜欢这个工具")
        
        # 添加工具特色
        if tool.capabilities:
            top_capabilities = [cap.name for cap in tool.capabilities[:3]]
            explanations.append(f"主要能力：{', '.join(top_capabilities)}")
        
        return "；".join(explanations) if explanations else f"推荐使用 {tool.name} 来完成此任务"
    
    def _estimate_tool_cost(self, tool: MCPTool, task_requirement: TaskRequirement) -> float:
        """估算工具成本"""
        # 简化的成本估算模型
        base_cost = 0.1  # 基础成本
        
        # 根据工具复杂度调整
        complexity_cost = len(tool.capabilities) * 0.02
        
        # 根据任务复杂度调整
        task_complexity = task_requirement.complexity_level or "medium"
        complexity_multiplier = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.5
        }.get(task_complexity, 1.0)
        
        return (base_cost + complexity_cost) * complexity_multiplier
    
    def _estimate_execution_time(self, tool: MCPTool, task_requirement: TaskRequirement) -> float:
        """估算执行时间（秒）"""
        metrics = self.tool_metrics.get(tool.tool_id)
        if metrics and metrics.average_execution_time > 0:
            return metrics.average_execution_time
        
        # 基于工具复杂度的估算
        base_time = 5.0  # 基础时间（秒）
        complexity_time = len(tool.capabilities) * 2.0
        
        # 根据任务复杂度调整
        task_complexity = task_requirement.complexity_level or "medium"
        complexity_multiplier = {
            "low": 0.5,
            "medium": 1.0,
            "high": 2.0
        }.get(task_complexity, 1.0)
        
        return (base_time + complexity_time) * complexity_multiplier
    
    async def provide_feedback(self, recommendation_id: str, user_id: str, 
                             feedback: Dict[str, Any]):
        """提供反馈"""
        if not self.enable_learning:
            return
        
        try:
            # 更新用户画像
            user_profile = self._get_user_profile(user_id)
            
            # 记录使用历史
            usage_record = {
                "recommendation_id": recommendation_id,
                "timestamp": datetime.now().isoformat(),
                "rating": feedback.get("rating", 0.5),
                "success": feedback.get("success", True),
                "execution_time": feedback.get("execution_time"),
                "comments": feedback.get("comments", "")
            }
            
            user_profile.usage_history.append(usage_record)
            
            # 限制历史记录长度
            if len(user_profile.usage_history) > 100:
                user_profile.usage_history = user_profile.usage_history[-100:]
            
            # 更新工具性能指标
            tool_id = feedback.get("tool_id")
            if tool_id and tool_id in self.tool_metrics:
                metrics = self.tool_metrics[tool_id]
                
                # 更新成功率
                if "success" in feedback:
                    old_rate = metrics.success_rate
                    new_success = 1.0 if feedback["success"] else 0.0
                    metrics.success_rate = old_rate * 0.9 + new_success * 0.1
                
                # 更新用户满意度
                if "rating" in feedback:
                    old_satisfaction = metrics.user_satisfaction
                    new_rating = feedback["rating"]
                    metrics.user_satisfaction = old_satisfaction * 0.9 + new_rating * 0.1
                
                # 更新执行时间
                if "execution_time" in feedback:
                    old_time = metrics.average_execution_time
                    new_time = feedback["execution_time"]
                    if old_time > 0:
                        metrics.average_execution_time = old_time * 0.9 + new_time * 0.1
                    else:
                        metrics.average_execution_time = new_time
                
                # 更新使用频率
                metrics.usage_frequency += 1
                metrics.last_used = datetime.now()
            
            # 学习用户偏好
            await self._update_user_preferences(user_profile, feedback)
            
            # 保存数据
            self._save_persistent_data()
            
            logger.info(f"处理用户 {user_id} 的反馈：{recommendation_id}")
            
        except Exception as e:
            logger.error(f"处理反馈失败: {e}")
    
    async def _update_user_preferences(self, user_profile: UserProfile, 
                                     feedback: Dict[str, Any]):
        """更新用户偏好"""
        tool_id = feedback.get("tool_id")
        if not tool_id or tool_id not in self.available_tools:
            return
        
        tool = self.available_tools[tool_id]
        rating = feedback.get("rating", 0.5)
        learning_rate = user_profile.learning_rate
        
        # 更新类别偏好
        category = tool.category.value
        old_pref = user_profile.preferences.get(category, 0.5)
        new_pref = old_pref + learning_rate * (rating - old_pref)
        user_profile.preferences[category] = max(0, min(1, new_pref))
        
        # 更新收藏和避免列表
        if rating >= 0.8:
            user_profile.favorite_tools.add(tool_id)
            user_profile.avoided_tools.discard(tool_id)
        elif rating <= 0.2:
            user_profile.avoided_tools.add(tool_id)
            user_profile.favorite_tools.discard(tool_id)
        
        user_profile.last_updated = datetime.now()
    
    async def get_recommendation_analytics(self, user_id: str = None, 
                                         days: int = 30) -> Dict[str, Any]:
        """获取推荐分析"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_recommendations": 0,
            "successful_recommendations": 0,
            "average_rating": 0.0,
            "top_tools": [],
            "category_distribution": {},
            "strategy_performance": {},
            "user_satisfaction_trend": []
        }
        
        # 分析用户历史（如果指定用户）
        if user_id and user_id in self.user_profiles:
            user_profile = self.user_profiles[user_id]
            recent_usage = [
                usage for usage in user_profile.usage_history
                if datetime.fromisoformat(usage["timestamp"]) >= start_date
            ]
            
            analytics["total_recommendations"] = len(recent_usage)
            
            if recent_usage:
                successful_count = sum(1 for usage in recent_usage if usage.get("success", True))
                analytics["successful_recommendations"] = successful_count
                
                ratings = [usage.get("rating", 0.5) for usage in recent_usage]
                analytics["average_rating"] = sum(ratings) / len(ratings)
        
        # 分析工具性能
        tool_performance = []
        for tool_id, metrics in self.tool_metrics.items():
            if tool_id in self.available_tools:
                tool = self.available_tools[tool_id]
                tool_performance.append({
                    "tool_id": tool_id,
                    "tool_name": tool.name,
                    "usage_frequency": metrics.usage_frequency,
                    "success_rate": metrics.success_rate,
                    "user_satisfaction": metrics.user_satisfaction
                })
        
        # 排序并获取前10个工具
        tool_performance.sort(key=lambda x: x["usage_frequency"], reverse=True)
        analytics["top_tools"] = tool_performance[:10]
        
        # 类别分布
        for tool in self.available_tools.values():
            category = tool.category.value
            analytics["category_distribution"][category] = analytics["category_distribution"].get(category, 0) + 1
        
        return analytics
    
    async def optimize_selection_parameters(self):
        """优化选择参数"""
        if not self.enable_learning:
            return
        
        try:
            # 分析历史反馈数据
            all_feedback = []
            for user_profile in self.user_profiles.values():
                all_feedback.extend(user_profile.usage_history)
            
            if len(all_feedback) < 10:  # 数据不足
                return
            
            # 计算当前参数的性能
            current_performance = sum(feedback.get("rating", 0.5) for feedback in all_feedback) / len(all_feedback)
            
            # 简化的参数优化：调整评分权重
            best_weights = self.scoring_weights.copy()
            best_performance = current_performance
            
            # 尝试不同的权重组合
            weight_adjustments = [0.9, 1.1]  # ±10%调整
            
            for weight_name in self.scoring_weights:
                for adjustment in weight_adjustments:
                    test_weights = self.scoring_weights.copy()
                    test_weights[weight_name] *= adjustment
                    
                    # 归一化权重
                    total_weight = sum(test_weights.values())
                    for key in test_weights:
                        test_weights[key] /= total_weight
                    
                    # 评估性能（简化实现）
                    estimated_performance = current_performance + (adjustment - 1.0) * 0.1
                    
                    if estimated_performance > best_performance:
                        best_performance = estimated_performance
                        best_weights = test_weights
            
            # 更新权重
            if best_performance > current_performance:
                self.scoring_weights = best_weights
                logger.info(f"优化选择参数，性能提升：{best_performance - current_performance:.3f}")
            
        except Exception as e:
            logger.error(f"优化选择参数失败: {e}")

# 工厂函数
def get_smart_tool_selection_engine(config_path: str = "./smart_tool_config.json") -> SmartToolSelectionEngine:
    """获取Smart Tool Engine智能选择层实例"""
    return SmartToolSelectionEngine(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_selection_engine():
        """测试智能选择引擎"""
        engine = get_smart_tool_selection_engine()
        
        # 创建测试工具
        test_tools = [
            MCPTool(
                tool_id="file_manager",
                name="File Manager",
                description="Manage files and directories",
                capabilities=[
                    ToolCapability(name="file_operations", confidence=0.9),
                    ToolCapability(name="directory_management", confidence=0.8)
                ],
                category=ToolCategory.UTILITY
            ),
            MCPTool(
                tool_id="web_scraper",
                name="Web Scraper",
                description="Extract data from websites",
                capabilities=[
                    ToolCapability(name="web_scraping", confidence=0.95),
                    ToolCapability(name="data_extraction", confidence=0.8)
                ],
                category=ToolCategory.WEB_AUTOMATION
            )
        ]
        
        # 注册工具
        await engine.register_tools(test_tools)
        
        # 创建任务需求
        task_requirement = TaskRequirement(
            task_id="test_task",
            description="Extract data from a website and save to file",
            required_capabilities=["web_scraping", "file_operations"],
            complexity_level="medium"
        )
        
        # 获取推荐
        recommendations = await engine.recommend_tools(
            task_requirement=task_requirement,
            user_id="test_user",
            strategy=SelectionStrategy.BALANCED
        )
        
        print(f"🎯 获得 {len(recommendations)} 个工具推荐:")
        for rec in recommendations:
            tool = engine.available_tools[rec.tool_id]
            print(f"  {rec.rank}. {tool.name} (评分: {rec.score:.3f})")
            print(f"     {rec.explanation}")
            print(f"     预估成本: ${rec.estimated_cost:.2f}, 预估时间: {rec.estimated_time:.1f}秒")
            print()
        
        # 提供反馈
        if recommendations:
            await engine.provide_feedback(
                recommendation_id=recommendations[0].recommendation_id,
                user_id="test_user",
                feedback={
                    "tool_id": recommendations[0].tool_id,
                    "rating": 0.9,
                    "success": True,
                    "execution_time": 15.5,
                    "comments": "工具运行良好"
                }
            )
            print("✅ 反馈已提交")
        
        # 获取分析
        analytics = await engine.get_recommendation_analytics("test_user")
        print(f"📊 推荐分析:")
        print(f"  总推荐数: {analytics['total_recommendations']}")
        print(f"  成功推荐数: {analytics['successful_recommendations']}")
        print(f"  平均评分: {analytics['average_rating']:.2f}")
    
    # 运行测试
    asyncio.run(test_selection_engine())

