"""
Predictive Resource Allocator - 预测性资源分配器
基于AI技术预测和优化资源分配，确保系统高效运行

功能：
- 基于历史数据预测资源需求
- 动态调整资源分配策略
- 预防性资源扩容和缩容
- 智能负载均衡
- 资源使用模式分析
- 成本优化建议
"""

import asyncio
import json
import logging
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
from enum import Enum

class ResourceType(Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"

class AllocationStrategy(Enum):
    """分配策略"""
    CONSERVATIVE = "conservative"  # 保守策略
    BALANCED = "balanced"         # 平衡策略
    AGGRESSIVE = "aggressive"     # 激进策略
    ADAPTIVE = "adaptive"         # 自适应策略

@dataclass
class ResourceUsage:
    """资源使用情况"""
    resource_type: ResourceType
    current_usage: float
    max_capacity: float
    timestamp: datetime
    platform: str
    task_id: Optional[str] = None
    
    @property
    def usage_percentage(self) -> float:
        """使用率百分比"""
        return (self.current_usage / self.max_capacity) * 100 if self.max_capacity > 0 else 0

@dataclass
class ResourcePrediction:
    """资源预测"""
    resource_type: ResourceType
    predicted_usage: float
    confidence: float
    time_horizon: int  # 预测时间范围（分钟）
    platform: str
    factors: List[str]  # 影响因素

@dataclass
class AllocationRecommendation:
    """分配建议"""
    resource_type: ResourceType
    platform: str
    current_allocation: float
    recommended_allocation: float
    reason: str
    priority: int  # 1-5，5最高
    estimated_impact: float
    implementation_cost: float

class PredictiveResourceAllocator:
    """预测性资源分配器"""
    
    def __init__(self, strategy: AllocationStrategy = AllocationStrategy.BALANCED):
        self.logger = logging.getLogger(__name__)
        self.strategy = strategy
        
        # 历史数据存储
        self.usage_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.prediction_history: Dict[str, List[ResourcePrediction]] = defaultdict(list)
        
        # 预测模型参数
        self.prediction_window = 60  # 预测窗口（分钟）
        self.learning_rate = 0.05
        self.confidence_threshold = 0.7
        
        # 资源阈值
        self.resource_thresholds = {
            ResourceType.CPU: {"warning": 70, "critical": 85, "target": 60},
            ResourceType.MEMORY: {"warning": 75, "critical": 90, "target": 65},
            ResourceType.DISK: {"warning": 80, "critical": 95, "target": 70},
            ResourceType.NETWORK: {"warning": 60, "critical": 80, "target": 50},
            ResourceType.GPU: {"warning": 75, "critical": 90, "target": 65}
        }
        
        # 平台权重
        self.platform_weights = {
            "macos": 1.0,
            "windows": 1.0,
            "linux": 1.0,
            "wsl": 0.8  # WSL相对权重较低
        }
        
        # 缓存
        self.prediction_cache: Dict[str, ResourcePrediction] = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        self.logger.info(f"预测性资源分配器初始化完成，策略: {strategy.value}")
    
    async def record_resource_usage(self, usage: ResourceUsage) -> None:
        """
        记录资源使用情况
        
        Args:
            usage: 资源使用数据
        """
        try:
            key = f"{usage.platform}_{usage.resource_type.value}"
            self.usage_history[key].append(usage)
            
            # 检查是否需要触发预测更新
            if len(self.usage_history[key]) % 10 == 0:  # 每10条记录触发一次
                await self._update_predictions(usage.platform, usage.resource_type)
            
            self.logger.debug(f"记录资源使用: {key} - {usage.usage_percentage:.1f}%")
            
        except Exception as e:
            self.logger.error(f"记录资源使用失败: {e}")
    
    async def predict_resource_demand(self, platform: str, resource_type: ResourceType,
                                    time_horizon: int = 60) -> ResourcePrediction:
        """
        预测资源需求
        
        Args:
            platform: 平台名称
            resource_type: 资源类型
            time_horizon: 预测时间范围（分钟）
            
        Returns:
            ResourcePrediction: 资源预测结果
        """
        try:
            cache_key = f"{platform}_{resource_type.value}_{time_horizon}"
            
            # 检查缓存
            if cache_key in self.prediction_cache:
                prediction = self.prediction_cache[cache_key]
                if (datetime.now() - prediction.time_horizon).seconds < self.cache_ttl:
                    return prediction
            
            # 获取历史数据
            key = f"{platform}_{resource_type.value}"
            historical_data = list(self.usage_history.get(key, []))
            
            if len(historical_data) < 5:
                # 数据不足，返回默认预测
                prediction = ResourcePrediction(
                    resource_type=resource_type,
                    predicted_usage=50.0,
                    confidence=0.3,
                    time_horizon=time_horizon,
                    platform=platform,
                    factors=["insufficient_data"]
                )
            else:
                # 基于历史数据进行预测
                prediction = await self._calculate_resource_prediction(
                    historical_data, platform, resource_type, time_horizon
                )
            
            # 缓存预测结果
            self.prediction_cache[cache_key] = prediction
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"预测资源需求失败: {e}")
            return ResourcePrediction(
                resource_type=resource_type,
                predicted_usage=50.0,
                confidence=0.1,
                time_horizon=time_horizon,
                platform=platform,
                factors=["prediction_error"]
            )
    
    async def _calculate_resource_prediction(self, historical_data: List[ResourceUsage],
                                           platform: str, resource_type: ResourceType,
                                           time_horizon: int) -> ResourcePrediction:
        """计算资源预测"""
        try:
            # 提取使用率数据
            usage_percentages = [usage.usage_percentage for usage in historical_data]
            timestamps = [usage.timestamp for usage in historical_data]
            
            # 时间序列分析
            trend = self._calculate_trend(usage_percentages)
            seasonality = self._detect_seasonality(usage_percentages, timestamps)
            volatility = self._calculate_volatility(usage_percentages)
            
            # 基础预测（移动平均）
            recent_data = usage_percentages[-20:]  # 最近20个数据点
            base_prediction = statistics.mean(recent_data)
            
            # 趋势调整
            trend_adjustment = trend * (time_horizon / 60.0)  # 按小时调整
            
            # 季节性调整
            seasonal_adjustment = seasonality * 0.1  # 季节性影响较小
            
            # 最终预测
            predicted_usage = base_prediction + trend_adjustment + seasonal_adjustment
            
            # 确保预测值在合理范围内
            predicted_usage = max(0, min(100, predicted_usage))
            
            # 计算置信度
            confidence = self._calculate_prediction_confidence(
                historical_data, volatility, len(recent_data)
            )
            
            # 识别影响因素
            factors = self._identify_factors(historical_data, trend, seasonality, volatility)
            
            return ResourcePrediction(
                resource_type=resource_type,
                predicted_usage=predicted_usage,
                confidence=confidence,
                time_horizon=time_horizon,
                platform=platform,
                factors=factors
            )
            
        except Exception as e:
            self.logger.error(f"计算资源预测失败: {e}")
            raise
    
    def _calculate_trend(self, data: List[float]) -> float:
        """计算趋势"""
        if len(data) < 2:
            return 0.0
        
        # 简单线性回归计算趋势
        n = len(data)
        x = list(range(n))
        y = data
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    def _detect_seasonality(self, data: List[float], timestamps: List[datetime]) -> float:
        """检测季节性模式"""
        if len(data) < 24:  # 需要至少24个数据点
            return 0.0
        
        try:
            # 按小时分组计算平均值
            hourly_averages = defaultdict(list)
            for i, timestamp in enumerate(timestamps):
                hour = timestamp.hour
                hourly_averages[hour].append(data[i])
            
            # 计算每小时的平均使用率
            hour_means = {}
            for hour, values in hourly_averages.items():
                hour_means[hour] = statistics.mean(values)
            
            if len(hour_means) < 3:
                return 0.0
            
            # 计算当前小时相对于全天平均的偏差
            current_hour = datetime.now().hour
            overall_mean = statistics.mean(hour_means.values())
            current_hour_mean = hour_means.get(current_hour, overall_mean)
            
            return current_hour_mean - overall_mean
            
        except Exception:
            return 0.0
    
    def _calculate_volatility(self, data: List[float]) -> float:
        """计算波动性"""
        if len(data) < 2:
            return 0.0
        
        return statistics.stdev(data) / statistics.mean(data) if statistics.mean(data) > 0 else 0.0
    
    def _calculate_prediction_confidence(self, historical_data: List[ResourceUsage],
                                       volatility: float, data_points: int) -> float:
        """计算预测置信度"""
        # 数据量因子
        data_factor = min(data_points / 50.0, 1.0)
        
        # 稳定性因子（波动性越低，置信度越高）
        stability_factor = max(0.1, 1.0 - volatility)
        
        # 时间因子（数据越新，置信度越高）
        if historical_data:
            latest_time = max(usage.timestamp for usage in historical_data)
            time_diff = (datetime.now() - latest_time).total_seconds() / 3600  # 小时
            time_factor = max(0.1, 1.0 - (time_diff / 24))  # 24小时内的数据权重较高
        else:
            time_factor = 0.1
        
        # 综合置信度
        confidence = (data_factor * 0.4 + stability_factor * 0.4 + time_factor * 0.2)
        
        return min(confidence, 0.95)  # 最大置信度95%
    
    def _identify_factors(self, historical_data: List[ResourceUsage], trend: float,
                         seasonality: float, volatility: float) -> List[str]:
        """识别影响因素"""
        factors = []
        
        if abs(trend) > 1.0:
            factors.append("strong_trend" if trend > 0 else "declining_trend")
        
        if abs(seasonality) > 5.0:
            factors.append("seasonal_pattern")
        
        if volatility > 0.3:
            factors.append("high_volatility")
        elif volatility < 0.1:
            factors.append("stable_usage")
        
        # 检查最近的使用模式
        if len(historical_data) >= 10:
            recent_usage = [usage.usage_percentage for usage in historical_data[-10:]]
            recent_avg = statistics.mean(recent_usage)
            
            if recent_avg > 80:
                factors.append("high_load")
            elif recent_avg < 20:
                factors.append("low_load")
        
        return factors if factors else ["normal_pattern"]
    
    async def generate_allocation_recommendations(self, platform: str = None) -> List[AllocationRecommendation]:
        """
        生成资源分配建议
        
        Args:
            platform: 目标平台，None表示所有平台
            
        Returns:
            List[AllocationRecommendation]: 分配建议列表
        """
        try:
            recommendations = []
            
            # 确定要分析的平台
            platforms_to_analyze = [platform] if platform else self._get_active_platforms()
            
            for plt in platforms_to_analyze:
                for resource_type in ResourceType:
                    recommendation = await self._generate_platform_resource_recommendation(
                        plt, resource_type
                    )
                    if recommendation:
                        recommendations.append(recommendation)
            
            # 按优先级排序
            recommendations.sort(key=lambda x: x.priority, reverse=True)
            
            self.logger.info(f"生成资源分配建议: {len(recommendations)} 条")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成分配建议失败: {e}")
            return []
    
    async def _generate_platform_resource_recommendation(self, platform: str,
                                                       resource_type: ResourceType) -> Optional[AllocationRecommendation]:
        """为特定平台和资源类型生成建议"""
        try:
            # 获取当前使用情况
            current_usage = await self._get_current_resource_usage(platform, resource_type)
            if current_usage is None:
                return None
            
            # 获取预测
            prediction = await self.predict_resource_demand(platform, resource_type)
            
            # 获取阈值
            thresholds = self.resource_thresholds[resource_type]
            
            # 计算建议分配
            recommended_allocation = await self._calculate_recommended_allocation(
                current_usage, prediction, thresholds
            )
            
            # 检查是否需要调整
            allocation_diff = abs(recommended_allocation - current_usage.max_capacity)
            if allocation_diff < current_usage.max_capacity * 0.05:  # 小于5%的变化忽略
                return None
            
            # 确定优先级和原因
            priority, reason = self._determine_priority_and_reason(
                current_usage, prediction, thresholds, recommended_allocation
            )
            
            # 估算影响和成本
            estimated_impact = self._estimate_impact(current_usage, recommended_allocation)
            implementation_cost = self._estimate_cost(platform, resource_type, allocation_diff)
            
            return AllocationRecommendation(
                resource_type=resource_type,
                platform=platform,
                current_allocation=current_usage.max_capacity,
                recommended_allocation=recommended_allocation,
                reason=reason,
                priority=priority,
                estimated_impact=estimated_impact,
                implementation_cost=implementation_cost
            )
            
        except Exception as e:
            self.logger.error(f"生成平台资源建议失败: {e}")
            return None
    
    async def _get_current_resource_usage(self, platform: str,
                                        resource_type: ResourceType) -> Optional[ResourceUsage]:
        """获取当前资源使用情况"""
        key = f"{platform}_{resource_type.value}"
        usage_data = self.usage_history.get(key, deque())
        
        if not usage_data:
            return None
        
        return usage_data[-1]  # 返回最新的使用数据
    
    async def _calculate_recommended_allocation(self, current_usage: ResourceUsage,
                                              prediction: ResourcePrediction,
                                              thresholds: Dict[str, float]) -> float:
        """计算建议分配"""
        # 基于预测使用率和目标阈值计算
        target_usage_rate = thresholds["target"] / 100.0
        predicted_usage_rate = prediction.predicted_usage / 100.0
        
        # 计算所需容量
        if predicted_usage_rate > 0:
            required_capacity = current_usage.current_usage / predicted_usage_rate
            recommended_allocation = required_capacity / target_usage_rate
        else:
            recommended_allocation = current_usage.max_capacity
        
        # 根据策略调整
        strategy_multiplier = self._get_strategy_multiplier()
        recommended_allocation *= strategy_multiplier
        
        # 确保最小值
        min_allocation = current_usage.max_capacity * 0.5  # 最少保留50%
        recommended_allocation = max(min_allocation, recommended_allocation)
        
        return recommended_allocation
    
    def _get_strategy_multiplier(self) -> float:
        """获取策略乘数"""
        multipliers = {
            AllocationStrategy.CONSERVATIVE: 1.3,
            AllocationStrategy.BALANCED: 1.1,
            AllocationStrategy.AGGRESSIVE: 0.9,
            AllocationStrategy.ADAPTIVE: 1.0
        }
        return multipliers.get(self.strategy, 1.0)
    
    def _determine_priority_and_reason(self, current_usage: ResourceUsage,
                                     prediction: ResourcePrediction,
                                     thresholds: Dict[str, float],
                                     recommended_allocation: float) -> Tuple[int, str]:
        """确定优先级和原因"""
        current_rate = current_usage.usage_percentage
        predicted_rate = prediction.predicted_usage
        
        # 高优先级情况
        if current_rate > thresholds["critical"]:
            return 5, f"当前{current_usage.resource_type.value}使用率已达到临界值({current_rate:.1f}%)"
        
        if predicted_rate > thresholds["critical"]:
            return 4, f"预测{current_usage.resource_type.value}使用率将达到临界值({predicted_rate:.1f}%)"
        
        # 中等优先级情况
        if current_rate > thresholds["warning"]:
            return 3, f"当前{current_usage.resource_type.value}使用率超过警告阈值({current_rate:.1f}%)"
        
        if predicted_rate > thresholds["warning"]:
            return 2, f"预测{current_usage.resource_type.value}使用率将超过警告阈值({predicted_rate:.1f}%)"
        
        # 优化建议
        if recommended_allocation < current_usage.max_capacity:
            return 1, f"可以减少{current_usage.resource_type.value}分配以节约成本"
        
        return 1, f"建议调整{current_usage.resource_type.value}分配以优化性能"
    
    def _estimate_impact(self, current_usage: ResourceUsage, recommended_allocation: float) -> float:
        """估算影响"""
        # 计算性能改善百分比
        if recommended_allocation > current_usage.max_capacity:
            # 扩容的性能改善
            improvement = (recommended_allocation - current_usage.max_capacity) / current_usage.max_capacity
            return min(improvement * 100, 50)  # 最大50%改善
        else:
            # 缩容的成本节约
            saving = (current_usage.max_capacity - recommended_allocation) / current_usage.max_capacity
            return min(saving * 100, 30)  # 最大30%节约
    
    def _estimate_cost(self, platform: str, resource_type: ResourceType, allocation_diff: float) -> float:
        """估算实施成本"""
        # 基础成本（相对值）
        base_costs = {
            ResourceType.CPU: 1.0,
            ResourceType.MEMORY: 0.8,
            ResourceType.DISK: 0.5,
            ResourceType.NETWORK: 0.3,
            ResourceType.GPU: 2.0
        }
        
        # 平台成本系数
        platform_cost = self.platform_weights.get(platform, 1.0)
        
        # 计算相对成本
        base_cost = base_costs.get(resource_type, 1.0)
        relative_cost = (allocation_diff / 1000) * base_cost * platform_cost
        
        return max(0.1, min(relative_cost, 10.0))  # 成本范围0.1-10.0
    
    def _get_active_platforms(self) -> List[str]:
        """获取活跃平台列表"""
        platforms = set()
        for key in self.usage_history.keys():
            platform = key.split('_')[0]
            platforms.add(platform)
        return list(platforms)
    
    async def _update_predictions(self, platform: str, resource_type: ResourceType) -> None:
        """更新预测"""
        try:
            # 生成新的预测
            prediction = await self.predict_resource_demand(platform, resource_type)
            
            # 存储预测历史
            key = f"{platform}_{resource_type.value}"
            self.prediction_history[key].append(prediction)
            
            # 限制历史记录大小
            if len(self.prediction_history[key]) > 100:
                self.prediction_history[key] = self.prediction_history[key][-80:]
            
        except Exception as e:
            self.logger.error(f"更新预测失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            total_platforms = len(self._get_active_platforms())
            total_resources = len(self.usage_history)
            
            # 计算平均预测准确性
            accuracy_scores = []
            for predictions in self.prediction_history.values():
                if len(predictions) > 1:
                    # 简单的准确性评估
                    recent_predictions = predictions[-10:]
                    avg_confidence = statistics.mean([p.confidence for p in recent_predictions])
                    accuracy_scores.append(avg_confidence)
            
            avg_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0.0
            
            # 资源使用统计
            resource_stats = {}
            for resource_type in ResourceType:
                type_usage = []
                for key, usage_data in self.usage_history.items():
                    if resource_type.value in key and usage_data:
                        latest_usage = usage_data[-1]
                        type_usage.append(latest_usage.usage_percentage)
                
                if type_usage:
                    resource_stats[resource_type.value] = {
                        "average_usage": statistics.mean(type_usage),
                        "max_usage": max(type_usage),
                        "min_usage": min(type_usage),
                        "platforms": len([k for k in self.usage_history.keys() if resource_type.value in k])
                    }
            
            return {
                "strategy": self.strategy.value,
                "total_platforms": total_platforms,
                "total_resources_monitored": total_resources,
                "prediction_accuracy": avg_accuracy,
                "resource_statistics": resource_stats,
                "cache_size": len(self.prediction_cache),
                "prediction_window_minutes": self.prediction_window,
                "confidence_threshold": self.confidence_threshold
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "status": "active",
            "strategy": self.strategy.value,
            "supported_resources": [rt.value for rt in ResourceType],
            "active_platforms": self._get_active_platforms(),
            "monitoring_enabled": True,
            "prediction_enabled": True,
            "statistics": self.get_statistics()
        }

