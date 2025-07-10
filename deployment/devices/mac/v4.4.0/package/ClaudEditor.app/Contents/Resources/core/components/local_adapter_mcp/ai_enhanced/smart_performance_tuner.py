"""
Smart Performance Tuner - 智能性能调优器
基于AI技术自动优化系统性能，提供智能调优建议

功能：
- 自动性能瓶颈检测
- 智能参数调优
- 性能基准测试
- 自适应优化策略
- 性能回归检测
- 实时性能监控
"""

import asyncio
import json
import logging
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
from enum import Enum

class PerformanceMetric(Enum):
    """性能指标类型"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_EFFICIENCY = "cpu_efficiency"
    MEMORY_EFFICIENCY = "memory_efficiency"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"

class TuningStrategy(Enum):
    """调优策略"""
    PERFORMANCE_FIRST = "performance_first"  # 性能优先
    EFFICIENCY_FIRST = "efficiency_first"    # 效率优先
    BALANCED = "balanced"                     # 平衡策略
    COST_OPTIMIZED = "cost_optimized"        # 成本优化

@dataclass
class PerformanceData:
    """性能数据"""
    metric_type: PerformanceMetric
    value: float
    timestamp: datetime
    platform: str
    task_type: str
    context: Dict[str, Any] = None

@dataclass
class PerformanceBenchmark:
    """性能基准"""
    metric_type: PerformanceMetric
    platform: str
    task_type: str
    baseline_value: float
    target_value: float
    current_value: float
    improvement_percentage: float

@dataclass
class TuningRecommendation:
    """调优建议"""
    parameter_name: str
    current_value: Any
    recommended_value: Any
    expected_improvement: float
    confidence: float
    risk_level: str  # low, medium, high
    description: str
    category: str

class SmartPerformanceTuner:
    """智能性能调优器"""
    
    def __init__(self, strategy: TuningStrategy = TuningStrategy.BALANCED):
        self.logger = logging.getLogger(__name__)
        self.strategy = strategy
        
        # 性能数据存储
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        
        # 调优参数
        self.tuning_parameters = {
            "cpu": {
                "max_workers": {"min": 1, "max": 16, "default": 4},
                "thread_pool_size": {"min": 2, "max": 32, "default": 8},
                "process_priority": {"min": -20, "max": 19, "default": 0}
            },
            "memory": {
                "cache_size": {"min": 64, "max": 2048, "default": 256},
                "buffer_size": {"min": 1024, "max": 65536, "default": 8192},
                "gc_threshold": {"min": 100, "max": 1000, "default": 700}
            },
            "io": {
                "batch_size": {"min": 1, "max": 1000, "default": 100},
                "timeout": {"min": 1, "max": 300, "default": 30},
                "retry_count": {"min": 0, "max": 10, "default": 3}
            },
            "network": {
                "connection_pool_size": {"min": 1, "max": 100, "default": 10},
                "keep_alive_timeout": {"min": 1, "max": 300, "default": 60},
                "request_timeout": {"min": 1, "max": 120, "default": 30}
            }
        }
        
        # 当前配置
        self.current_config = self._load_default_config()
        
        # 性能阈值
        self.performance_thresholds = {
            PerformanceMetric.RESPONSE_TIME: {"excellent": 100, "good": 500, "poor": 2000},
            PerformanceMetric.THROUGHPUT: {"excellent": 1000, "good": 500, "poor": 100},
            PerformanceMetric.ERROR_RATE: {"excellent": 0.1, "good": 1.0, "poor": 5.0},
            PerformanceMetric.CPU_EFFICIENCY: {"excellent": 90, "good": 70, "poor": 50},
            PerformanceMetric.MEMORY_EFFICIENCY: {"excellent": 85, "good": 65, "poor": 45}
        }
        
        # 学习参数
        self.learning_rate = 0.1
        self.exploration_rate = 0.2
        self.confidence_threshold = 0.7
        
        self.logger.info(f"智能性能调优器初始化完成，策略: {strategy.value}")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        config = {}
        for category, params in self.tuning_parameters.items():
            config[category] = {}
            for param_name, param_info in params.items():
                config[category][param_name] = param_info["default"]
        return config
    
    async def record_performance_data(self, data: PerformanceData) -> None:
        """
        记录性能数据
        
        Args:
            data: 性能数据
        """
        try:
            key = f"{data.platform}_{data.task_type}_{data.metric_type.value}"
            self.performance_history[key].append(data)
            
            # 检查是否需要触发调优
            if len(self.performance_history[key]) % 20 == 0:  # 每20条记录检查一次
                await self._check_performance_regression(key)
            
            self.logger.debug(f"记录性能数据: {key} - {data.value}")
            
        except Exception as e:
            self.logger.error(f"记录性能数据失败: {e}")
    
    async def analyze_performance_bottlenecks(self, platform: str = None,
                                            task_type: str = None) -> List[Dict[str, Any]]:
        """
        分析性能瓶颈
        
        Args:
            platform: 目标平台
            task_type: 任务类型
            
        Returns:
            List[Dict[str, Any]]: 瓶颈分析结果
        """
        try:
            bottlenecks = []
            
            # 筛选要分析的数据
            keys_to_analyze = self._filter_performance_keys(platform, task_type)
            
            for key in keys_to_analyze:
                performance_data = list(self.performance_history[key])
                if len(performance_data) < 10:
                    continue
                
                bottleneck = await self._analyze_single_metric_bottleneck(key, performance_data)
                if bottleneck:
                    bottlenecks.append(bottleneck)
            
            # 按严重程度排序
            bottlenecks.sort(key=lambda x: x.get("severity_score", 0), reverse=True)
            
            self.logger.info(f"检测到 {len(bottlenecks)} 个性能瓶颈")
            
            return bottlenecks
            
        except Exception as e:
            self.logger.error(f"分析性能瓶颈失败: {e}")
            return []
    
    async def _analyze_single_metric_bottleneck(self, key: str,
                                              performance_data: List[PerformanceData]) -> Optional[Dict[str, Any]]:
        """分析单个指标的瓶颈"""
        try:
            # 解析key
            parts = key.split('_')
            platform = parts[0]
            task_type = parts[1]
            metric_type = PerformanceMetric(parts[2])
            
            # 提取数值
            values = [data.value for data in performance_data]
            recent_values = values[-20:]  # 最近20个值
            
            # 计算统计指标
            current_avg = statistics.mean(recent_values)
            historical_avg = statistics.mean(values[:-20]) if len(values) > 20 else current_avg
            trend = self._calculate_trend(recent_values)
            volatility = statistics.stdev(recent_values) / current_avg if current_avg > 0 else 0
            
            # 获取阈值
            thresholds = self.performance_thresholds.get(metric_type, {})
            
            # 判断是否为瓶颈
            is_bottleneck = False
            severity_score = 0
            issues = []
            
            # 检查绝对值
            if metric_type in [PerformanceMetric.RESPONSE_TIME, PerformanceMetric.ERROR_RATE]:
                # 越小越好的指标
                if current_avg > thresholds.get("poor", float('inf')):
                    is_bottleneck = True
                    severity_score += 3
                    issues.append(f"{metric_type.value}过高")
                elif current_avg > thresholds.get("good", float('inf')):
                    severity_score += 1
                    issues.append(f"{metric_type.value}偏高")
            else:
                # 越大越好的指标
                if current_avg < thresholds.get("poor", 0):
                    is_bottleneck = True
                    severity_score += 3
                    issues.append(f"{metric_type.value}过低")
                elif current_avg < thresholds.get("good", 0):
                    severity_score += 1
                    issues.append(f"{metric_type.value}偏低")
            
            # 检查趋势
            if trend < -0.1:  # 性能下降趋势
                is_bottleneck = True
                severity_score += 2
                issues.append("性能下降趋势")
            
            # 检查波动性
            if volatility > 0.3:  # 高波动性
                severity_score += 1
                issues.append("性能不稳定")
            
            # 检查性能回归
            if len(values) > 20:
                regression_score = (current_avg - historical_avg) / historical_avg
                if metric_type in [PerformanceMetric.RESPONSE_TIME, PerformanceMetric.ERROR_RATE]:
                    if regression_score > 0.2:  # 恶化超过20%
                        is_bottleneck = True
                        severity_score += 2
                        issues.append("性能回归")
                else:
                    if regression_score < -0.2:  # 下降超过20%
                        is_bottleneck = True
                        severity_score += 2
                        issues.append("性能回归")
            
            if is_bottleneck or severity_score > 0:
                return {
                    "key": key,
                    "platform": platform,
                    "task_type": task_type,
                    "metric_type": metric_type.value,
                    "current_value": current_avg,
                    "historical_value": historical_avg,
                    "trend": trend,
                    "volatility": volatility,
                    "severity_score": severity_score,
                    "issues": issues,
                    "is_critical": severity_score >= 3
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"分析单个指标瓶颈失败: {e}")
            return None
    
    def _calculate_trend(self, data: List[float]) -> float:
        """计算趋势"""
        if len(data) < 2:
            return 0.0
        
        # 简单线性回归
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
        return slope / y_mean if y_mean != 0 else 0.0  # 归一化斜率
    
    async def generate_tuning_recommendations(self, platform: str = None,
                                            task_type: str = None) -> List[TuningRecommendation]:
        """
        生成调优建议
        
        Args:
            platform: 目标平台
            task_type: 任务类型
            
        Returns:
            List[TuningRecommendation]: 调优建议列表
        """
        try:
            recommendations = []
            
            # 分析性能瓶颈
            bottlenecks = await self.analyze_performance_bottlenecks(platform, task_type)
            
            # 为每个瓶颈生成调优建议
            for bottleneck in bottlenecks:
                bottleneck_recommendations = await self._generate_bottleneck_recommendations(bottleneck)
                recommendations.extend(bottleneck_recommendations)
            
            # 生成通用优化建议
            general_recommendations = await self._generate_general_recommendations(platform, task_type)
            recommendations.extend(general_recommendations)
            
            # 按预期改善排序
            recommendations.sort(key=lambda x: x.expected_improvement, reverse=True)
            
            self.logger.info(f"生成调优建议: {len(recommendations)} 条")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成调优建议失败: {e}")
            return []
    
    async def _generate_bottleneck_recommendations(self, bottleneck: Dict[str, Any]) -> List[TuningRecommendation]:
        """为特定瓶颈生成建议"""
        recommendations = []
        
        try:
            metric_type = bottleneck["metric_type"]
            platform = bottleneck["platform"]
            severity_score = bottleneck["severity_score"]
            
            # 根据指标类型生成特定建议
            if metric_type == PerformanceMetric.RESPONSE_TIME.value:
                recommendations.extend(self._generate_response_time_recommendations(bottleneck))
            elif metric_type == PerformanceMetric.THROUGHPUT.value:
                recommendations.extend(self._generate_throughput_recommendations(bottleneck))
            elif metric_type == PerformanceMetric.CPU_EFFICIENCY.value:
                recommendations.extend(self._generate_cpu_recommendations(bottleneck))
            elif metric_type == PerformanceMetric.MEMORY_EFFICIENCY.value:
                recommendations.extend(self._generate_memory_recommendations(bottleneck))
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成瓶颈建议失败: {e}")
            return []
    
    def _generate_response_time_recommendations(self, bottleneck: Dict[str, Any]) -> List[TuningRecommendation]:
        """生成响应时间优化建议"""
        recommendations = []
        current_config = self.current_config
        
        # 增加并发处理能力
        current_workers = current_config["cpu"]["max_workers"]
        if current_workers < 8:
            recommendations.append(TuningRecommendation(
                parameter_name="cpu.max_workers",
                current_value=current_workers,
                recommended_value=min(current_workers * 2, 8),
                expected_improvement=25.0,
                confidence=0.8,
                risk_level="low",
                description="增加并发工作线程数以提高处理能力",
                category="cpu"
            ))
        
        # 优化缓存大小
        current_cache = current_config["memory"]["cache_size"]
        if current_cache < 512:
            recommendations.append(TuningRecommendation(
                parameter_name="memory.cache_size",
                current_value=current_cache,
                recommended_value=min(current_cache * 2, 512),
                expected_improvement=15.0,
                confidence=0.7,
                risk_level="low",
                description="增加缓存大小以减少重复计算",
                category="memory"
            ))
        
        # 优化批处理大小
        current_batch = current_config["io"]["batch_size"]
        if current_batch < 200:
            recommendations.append(TuningRecommendation(
                parameter_name="io.batch_size",
                current_value=current_batch,
                recommended_value=min(current_batch * 2, 200),
                expected_improvement=20.0,
                confidence=0.75,
                risk_level="medium",
                description="增加批处理大小以提高I/O效率",
                category="io"
            ))
        
        return recommendations
    
    def _generate_throughput_recommendations(self, bottleneck: Dict[str, Any]) -> List[TuningRecommendation]:
        """生成吞吐量优化建议"""
        recommendations = []
        current_config = self.current_config
        
        # 增加线程池大小
        current_pool = current_config["cpu"]["thread_pool_size"]
        if current_pool < 16:
            recommendations.append(TuningRecommendation(
                parameter_name="cpu.thread_pool_size",
                current_value=current_pool,
                recommended_value=min(current_pool * 2, 16),
                expected_improvement=30.0,
                confidence=0.8,
                risk_level="low",
                description="增加线程池大小以提高并发处理能力",
                category="cpu"
            ))
        
        # 优化连接池
        current_conn_pool = current_config["network"]["connection_pool_size"]
        if current_conn_pool < 20:
            recommendations.append(TuningRecommendation(
                parameter_name="network.connection_pool_size",
                current_value=current_conn_pool,
                recommended_value=min(current_conn_pool * 2, 20),
                expected_improvement=25.0,
                confidence=0.75,
                risk_level="low",
                description="增加连接池大小以提高网络吞吐量",
                category="network"
            ))
        
        return recommendations
    
    def _generate_cpu_recommendations(self, bottleneck: Dict[str, Any]) -> List[TuningRecommendation]:
        """生成CPU效率优化建议"""
        recommendations = []
        current_config = self.current_config
        
        # 调整进程优先级
        current_priority = current_config["cpu"]["process_priority"]
        if current_priority > -5:
            recommendations.append(TuningRecommendation(
                parameter_name="cpu.process_priority",
                current_value=current_priority,
                recommended_value=max(current_priority - 5, -10),
                expected_improvement=10.0,
                confidence=0.6,
                risk_level="medium",
                description="提高进程优先级以获得更多CPU时间",
                category="cpu"
            ))
        
        return recommendations
    
    def _generate_memory_recommendations(self, bottleneck: Dict[str, Any]) -> List[TuningRecommendation]:
        """生成内存效率优化建议"""
        recommendations = []
        current_config = self.current_config
        
        # 调整垃圾回收阈值
        current_gc = current_config["memory"]["gc_threshold"]
        if current_gc > 500:
            recommendations.append(TuningRecommendation(
                parameter_name="memory.gc_threshold",
                current_value=current_gc,
                recommended_value=max(current_gc - 200, 300),
                expected_improvement=15.0,
                confidence=0.7,
                risk_level="low",
                description="降低垃圾回收阈值以减少内存占用",
                category="memory"
            ))
        
        # 优化缓冲区大小
        current_buffer = current_config["memory"]["buffer_size"]
        if current_buffer > 16384:
            recommendations.append(TuningRecommendation(
                parameter_name="memory.buffer_size",
                current_value=current_buffer,
                recommended_value=max(current_buffer // 2, 4096),
                expected_improvement=12.0,
                confidence=0.65,
                risk_level="low",
                description="减少缓冲区大小以节约内存",
                category="memory"
            ))
        
        return recommendations
    
    async def _generate_general_recommendations(self, platform: str = None,
                                              task_type: str = None) -> List[TuningRecommendation]:
        """生成通用优化建议"""
        recommendations = []
        
        try:
            # 基于策略生成建议
            if self.strategy == TuningStrategy.PERFORMANCE_FIRST:
                recommendations.extend(self._generate_performance_first_recommendations())
            elif self.strategy == TuningStrategy.EFFICIENCY_FIRST:
                recommendations.extend(self._generate_efficiency_first_recommendations())
            elif self.strategy == TuningStrategy.COST_OPTIMIZED:
                recommendations.extend(self._generate_cost_optimized_recommendations())
            else:  # BALANCED
                recommendations.extend(self._generate_balanced_recommendations())
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成通用建议失败: {e}")
            return []
    
    def _generate_performance_first_recommendations(self) -> List[TuningRecommendation]:
        """生成性能优先建议"""
        return [
            TuningRecommendation(
                parameter_name="cpu.max_workers",
                current_value=self.current_config["cpu"]["max_workers"],
                recommended_value=min(self.current_config["cpu"]["max_workers"] * 1.5, 12),
                expected_improvement=20.0,
                confidence=0.8,
                risk_level="low",
                description="性能优先策略：增加工作线程数",
                category="cpu"
            )
        ]
    
    def _generate_efficiency_first_recommendations(self) -> List[TuningRecommendation]:
        """生成效率优先建议"""
        return [
            TuningRecommendation(
                parameter_name="memory.cache_size",
                current_value=self.current_config["memory"]["cache_size"],
                recommended_value=min(self.current_config["memory"]["cache_size"] * 1.5, 1024),
                expected_improvement=15.0,
                confidence=0.75,
                risk_level="low",
                description="效率优先策略：优化缓存配置",
                category="memory"
            )
        ]
    
    def _generate_cost_optimized_recommendations(self) -> List[TuningRecommendation]:
        """生成成本优化建议"""
        return [
            TuningRecommendation(
                parameter_name="memory.cache_size",
                current_value=self.current_config["memory"]["cache_size"],
                recommended_value=max(self.current_config["memory"]["cache_size"] * 0.8, 128),
                expected_improvement=10.0,
                confidence=0.6,
                risk_level="low",
                description="成本优化策略：减少内存使用",
                category="memory"
            )
        ]
    
    def _generate_balanced_recommendations(self) -> List[TuningRecommendation]:
        """生成平衡策略建议"""
        return [
            TuningRecommendation(
                parameter_name="io.batch_size",
                current_value=self.current_config["io"]["batch_size"],
                recommended_value=min(self.current_config["io"]["batch_size"] * 1.2, 150),
                expected_improvement=12.0,
                confidence=0.7,
                risk_level="low",
                description="平衡策略：适度优化批处理",
                category="io"
            )
        ]
    
    async def apply_tuning_recommendation(self, recommendation: TuningRecommendation) -> bool:
        """
        应用调优建议
        
        Args:
            recommendation: 调优建议
            
        Returns:
            bool: 是否成功应用
        """
        try:
            # 解析参数路径
            param_path = recommendation.parameter_name.split('.')
            if len(param_path) != 2:
                self.logger.error(f"无效的参数路径: {recommendation.parameter_name}")
                return False
            
            category, param_name = param_path
            
            # 验证参数
            if category not in self.tuning_parameters:
                self.logger.error(f"未知的参数类别: {category}")
                return False
            
            if param_name not in self.tuning_parameters[category]:
                self.logger.error(f"未知的参数: {param_name}")
                return False
            
            # 验证值范围
            param_info = self.tuning_parameters[category][param_name]
            recommended_value = recommendation.recommended_value
            
            if not (param_info["min"] <= recommended_value <= param_info["max"]):
                self.logger.error(f"参数值超出范围: {recommended_value}")
                return False
            
            # 备份当前配置
            old_value = self.current_config[category][param_name]
            
            # 应用新配置
            self.current_config[category][param_name] = recommended_value
            
            self.logger.info(f"应用调优建议: {recommendation.parameter_name} "
                           f"{old_value} -> {recommended_value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"应用调优建议失败: {e}")
            return False
    
    async def _check_performance_regression(self, key: str) -> None:
        """检查性能回归"""
        try:
            performance_data = list(self.performance_history[key])
            if len(performance_data) < 40:  # 需要足够的数据
                return
            
            # 比较最近20个数据点和之前20个数据点
            recent_values = [data.value for data in performance_data[-20:]]
            previous_values = [data.value for data in performance_data[-40:-20]]
            
            recent_avg = statistics.mean(recent_values)
            previous_avg = statistics.mean(previous_values)
            
            # 计算变化百分比
            if previous_avg > 0:
                change_percentage = (recent_avg - previous_avg) / previous_avg
                
                # 检查是否有显著回归
                if abs(change_percentage) > 0.15:  # 15%的变化
                    self.logger.warning(f"检测到性能变化: {key} "
                                      f"变化 {change_percentage:.1%}")
            
        except Exception as e:
            self.logger.error(f"检查性能回归失败: {e}")
    
    def _filter_performance_keys(self, platform: str = None, task_type: str = None) -> List[str]:
        """筛选性能数据键"""
        keys = list(self.performance_history.keys())
        
        if platform:
            keys = [k for k in keys if k.startswith(f"{platform}_")]
        
        if task_type:
            keys = [k for k in keys if f"_{task_type}_" in k]
        
        return keys
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.current_config.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            total_metrics = len(self.performance_history)
            total_data_points = sum(len(data) for data in self.performance_history.values())
            
            # 计算平均性能
            avg_performance = {}
            for metric_type in PerformanceMetric:
                metric_values = []
                for key, data in self.performance_history.items():
                    if metric_type.value in key:
                        metric_values.extend([d.value for d in data])
                
                if metric_values:
                    avg_performance[metric_type.value] = {
                        "average": statistics.mean(metric_values),
                        "median": statistics.median(metric_values),
                        "std_dev": statistics.stdev(metric_values) if len(metric_values) > 1 else 0
                    }
            
            return {
                "strategy": self.strategy.value,
                "total_metrics_monitored": total_metrics,
                "total_data_points": total_data_points,
                "average_performance": avg_performance,
                "current_config": self.current_config,
                "learning_rate": self.learning_rate,
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
            "supported_metrics": [metric.value for metric in PerformanceMetric],
            "tuning_enabled": True,
            "auto_apply": False,  # 默认不自动应用建议
            "statistics": self.get_statistics()
        }

