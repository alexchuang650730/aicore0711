"""
Intelligent Task Optimizer - 智能任务优化器
使用AI技术优化任务执行策略和资源分配

功能：
- 基于历史数据的任务性能预测
- 智能任务调度和优先级排序
- 动态资源分配优化
- 任务执行路径智能选择
- 性能瓶颈自动识别和优化
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import statistics
import numpy as np
from collections import defaultdict, deque

@dataclass
class TaskMetrics:
    """任务性能指标"""
    task_id: str
    task_type: str
    platform: str
    execution_time: float
    cpu_usage: float
    memory_usage: float
    success: bool
    error_type: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class OptimizationRecommendation:
    """优化建议"""
    task_id: str
    recommendation_type: str
    description: str
    expected_improvement: float
    confidence: float
    implementation_priority: int

@dataclass
class ResourcePrediction:
    """资源需求预测"""
    task_type: str
    platform: str
    predicted_cpu: float
    predicted_memory: float
    predicted_duration: float
    confidence: float

class IntelligentTaskOptimizer:
    """智能任务优化器"""
    
    def __init__(self, max_history_size: int = 10000):
        self.logger = logging.getLogger(__name__)
        self.max_history_size = max_history_size
        
        # 历史数据存储
        self.task_history: deque = deque(maxlen=max_history_size)
        self.performance_metrics: Dict[str, List[TaskMetrics]] = defaultdict(list)
        self.platform_performance: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        # 优化模型参数
        self.learning_rate = 0.01
        self.optimization_threshold = 0.1
        self.confidence_threshold = 0.7
        
        # 缓存
        self.prediction_cache: Dict[str, ResourcePrediction] = {}
        self.cache_ttl = 300  # 5分钟缓存
        self.cache_timestamps: Dict[str, datetime] = {}
        
        self.logger.info("智能任务优化器初始化完成")
    
    async def record_task_execution(self, task_metrics: TaskMetrics) -> None:
        """
        记录任务执行数据
        
        Args:
            task_metrics: 任务性能指标
        """
        try:
            # 添加到历史记录
            self.task_history.append(task_metrics)
            
            # 按任务类型分类存储
            task_key = f"{task_metrics.task_type}_{task_metrics.platform}"
            self.performance_metrics[task_key].append(task_metrics)
            
            # 更新平台性能数据
            platform_data = self.platform_performance[task_metrics.platform]
            platform_data['execution_time'].append(task_metrics.execution_time)
            platform_data['cpu_usage'].append(task_metrics.cpu_usage)
            platform_data['memory_usage'].append(task_metrics.memory_usage)
            
            # 限制历史数据大小
            if len(self.performance_metrics[task_key]) > 1000:
                self.performance_metrics[task_key] = self.performance_metrics[task_key][-800:]
            
            # 清理过期缓存
            await self._cleanup_cache()
            
            self.logger.debug(f"记录任务执行数据: {task_metrics.task_id}")
            
        except Exception as e:
            self.logger.error(f"记录任务执行数据失败: {e}")
    
    async def predict_task_performance(self, task_type: str, platform: str) -> ResourcePrediction:
        """
        预测任务性能需求
        
        Args:
            task_type: 任务类型
            platform: 执行平台
            
        Returns:
            ResourcePrediction: 资源需求预测
        """
        try:
            cache_key = f"{task_type}_{platform}"
            
            # 检查缓存
            if cache_key in self.prediction_cache:
                cache_time = self.cache_timestamps.get(cache_key)
                if cache_time and (datetime.now() - cache_time).seconds < self.cache_ttl:
                    return self.prediction_cache[cache_key]
            
            # 获取历史数据
            task_key = f"{task_type}_{platform}"
            historical_data = self.performance_metrics.get(task_key, [])
            
            if len(historical_data) < 3:
                # 数据不足，使用默认预测
                prediction = ResourcePrediction(
                    task_type=task_type,
                    platform=platform,
                    predicted_cpu=50.0,
                    predicted_memory=1024.0,
                    predicted_duration=30.0,
                    confidence=0.3
                )
            else:
                # 基于历史数据预测
                prediction = await self._calculate_prediction(historical_data, task_type, platform)
            
            # 更新缓存
            self.prediction_cache[cache_key] = prediction
            self.cache_timestamps[cache_key] = datetime.now()
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"预测任务性能失败: {e}")
            # 返回默认预测
            return ResourcePrediction(
                task_type=task_type,
                platform=platform,
                predicted_cpu=50.0,
                predicted_memory=1024.0,
                predicted_duration=30.0,
                confidence=0.1
            )
    
    async def _calculate_prediction(self, historical_data: List[TaskMetrics], 
                                  task_type: str, platform: str) -> ResourcePrediction:
        """计算性能预测"""
        try:
            # 只使用成功的任务数据
            successful_tasks = [task for task in historical_data if task.success]
            
            if not successful_tasks:
                successful_tasks = historical_data  # 如果没有成功的任务，使用所有数据
            
            # 计算统计指标
            execution_times = [task.execution_time for task in successful_tasks]
            cpu_usages = [task.cpu_usage for task in successful_tasks]
            memory_usages = [task.memory_usage for task in successful_tasks]
            
            # 使用加权平均，最近的数据权重更高
            weights = self._calculate_weights(len(successful_tasks))
            
            predicted_duration = np.average(execution_times, weights=weights)
            predicted_cpu = np.average(cpu_usages, weights=weights)
            predicted_memory = np.average(memory_usages, weights=weights)
            
            # 计算置信度
            confidence = self._calculate_confidence(successful_tasks)
            
            # 添加安全边际
            safety_margin = 1.2
            predicted_cpu *= safety_margin
            predicted_memory *= safety_margin
            predicted_duration *= safety_margin
            
            return ResourcePrediction(
                task_type=task_type,
                platform=platform,
                predicted_cpu=predicted_cpu,
                predicted_memory=predicted_memory,
                predicted_duration=predicted_duration,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"计算性能预测失败: {e}")
            raise
    
    def _calculate_weights(self, data_size: int) -> List[float]:
        """计算时间衰减权重"""
        weights = []
        for i in range(data_size):
            # 最新的数据权重最高
            weight = np.exp(-0.1 * (data_size - i - 1))
            weights.append(weight)
        
        # 归一化权重
        total_weight = sum(weights)
        return [w / total_weight for w in weights]
    
    def _calculate_confidence(self, tasks: List[TaskMetrics]) -> float:
        """计算预测置信度"""
        if len(tasks) < 3:
            return 0.3
        
        # 基于数据量和一致性计算置信度
        data_size_factor = min(len(tasks) / 50.0, 1.0)  # 数据量因子
        
        # 计算执行时间的变异系数
        execution_times = [task.execution_time for task in tasks]
        if len(execution_times) > 1:
            cv = statistics.stdev(execution_times) / statistics.mean(execution_times)
            consistency_factor = max(0.1, 1.0 - cv)  # 一致性因子
        else:
            consistency_factor = 0.5
        
        # 成功率因子
        success_rate = sum(1 for task in tasks if task.success) / len(tasks)
        
        # 综合置信度
        confidence = (data_size_factor * 0.4 + consistency_factor * 0.4 + success_rate * 0.2)
        
        return min(confidence, 0.95)  # 最大置信度95%
    
    async def optimize_task_scheduling(self, pending_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        优化任务调度顺序
        
        Args:
            pending_tasks: 待执行任务列表
            
        Returns:
            List[Dict[str, Any]]: 优化后的任务列表
        """
        try:
            if not pending_tasks:
                return []
            
            # 为每个任务计算优先级分数
            scored_tasks = []
            for task in pending_tasks:
                score = await self._calculate_task_priority(task)
                scored_tasks.append((task, score))
            
            # 按分数排序（分数越高优先级越高）
            scored_tasks.sort(key=lambda x: x[1], reverse=True)
            
            optimized_tasks = [task for task, score in scored_tasks]
            
            self.logger.info(f"优化任务调度: {len(pending_tasks)} -> {len(optimized_tasks)}")
            
            return optimized_tasks
            
        except Exception as e:
            self.logger.error(f"优化任务调度失败: {e}")
            return pending_tasks
    
    async def _calculate_task_priority(self, task: Dict[str, Any]) -> float:
        """计算任务优先级分数"""
        try:
            task_type = task.get('type', 'unknown')
            platform = task.get('platform', 'unknown')
            urgency = task.get('urgency', 5)  # 1-10，10最紧急
            
            # 基础优先级分数
            base_score = urgency * 10
            
            # 预测性能影响
            prediction = await self.predict_task_performance(task_type, platform)
            
            # 执行时间影响（时间越短优先级越高）
            time_factor = max(0.1, 1.0 / (prediction.predicted_duration / 60.0))
            
            # 成功率影响
            success_rate = await self._get_task_success_rate(task_type, platform)
            success_factor = success_rate
            
            # 资源利用率影响
            resource_factor = await self._calculate_resource_efficiency(task_type, platform)
            
            # 综合分数
            total_score = (
                base_score * 0.4 +
                time_factor * 20 * 0.3 +
                success_factor * 100 * 0.2 +
                resource_factor * 50 * 0.1
            )
            
            return total_score
            
        except Exception as e:
            self.logger.error(f"计算任务优先级失败: {e}")
            return 50.0  # 默认分数
    
    async def _get_task_success_rate(self, task_type: str, platform: str) -> float:
        """获取任务成功率"""
        task_key = f"{task_type}_{platform}"
        historical_data = self.performance_metrics.get(task_key, [])
        
        if not historical_data:
            return 0.8  # 默认成功率
        
        # 计算最近的成功率
        recent_data = historical_data[-50:]  # 最近50次执行
        success_count = sum(1 for task in recent_data if task.success)
        
        return success_count / len(recent_data)
    
    async def _calculate_resource_efficiency(self, task_type: str, platform: str) -> float:
        """计算资源利用效率"""
        task_key = f"{task_type}_{platform}"
        historical_data = self.performance_metrics.get(task_key, [])
        
        if not historical_data:
            return 0.5  # 默认效率
        
        # 计算资源利用效率
        recent_data = historical_data[-20:]
        
        if not recent_data:
            return 0.5
        
        # 效率 = 成功率 / (CPU使用率 * 内存使用率 * 执行时间)
        total_efficiency = 0
        for task in recent_data:
            if task.success:
                efficiency = 1.0 / (
                    (task.cpu_usage / 100.0) * 
                    (task.memory_usage / 1000.0) * 
                    (task.execution_time / 60.0)
                )
                total_efficiency += efficiency
        
        return total_efficiency / len(recent_data) if recent_data else 0.5
    
    async def generate_optimization_recommendations(self, 
                                                 platform: str = None) -> List[OptimizationRecommendation]:
        """
        生成优化建议
        
        Args:
            platform: 目标平台，None表示所有平台
            
        Returns:
            List[OptimizationRecommendation]: 优化建议列表
        """
        try:
            recommendations = []
            
            # 分析性能瓶颈
            bottlenecks = await self._identify_performance_bottlenecks(platform)
            
            for bottleneck in bottlenecks:
                recommendation = await self._create_recommendation_for_bottleneck(bottleneck)
                if recommendation:
                    recommendations.append(recommendation)
            
            # 分析资源浪费
            waste_issues = await self._identify_resource_waste(platform)
            
            for issue in waste_issues:
                recommendation = await self._create_recommendation_for_waste(issue)
                if recommendation:
                    recommendations.append(recommendation)
            
            # 按优先级排序
            recommendations.sort(key=lambda x: x.implementation_priority)
            
            self.logger.info(f"生成优化建议: {len(recommendations)} 条")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成优化建议失败: {e}")
            return []
    
    async def _identify_performance_bottlenecks(self, platform: str = None) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        try:
            # 分析各平台的性能数据
            platforms_to_analyze = [platform] if platform else self.platform_performance.keys()
            
            for plt in platforms_to_analyze:
                platform_data = self.platform_performance.get(plt, {})
                
                if not platform_data:
                    continue
                
                # 分析执行时间
                execution_times = platform_data.get('execution_time', [])
                if execution_times:
                    avg_time = statistics.mean(execution_times)
                    if avg_time > 300:  # 超过5分钟
                        bottlenecks.append({
                            'type': 'slow_execution',
                            'platform': plt,
                            'metric': 'execution_time',
                            'value': avg_time,
                            'severity': 'high' if avg_time > 600 else 'medium'
                        })
                
                # 分析CPU使用率
                cpu_usages = platform_data.get('cpu_usage', [])
                if cpu_usages:
                    avg_cpu = statistics.mean(cpu_usages)
                    if avg_cpu > 80:
                        bottlenecks.append({
                            'type': 'high_cpu_usage',
                            'platform': plt,
                            'metric': 'cpu_usage',
                            'value': avg_cpu,
                            'severity': 'high' if avg_cpu > 90 else 'medium'
                        })
                
                # 分析内存使用率
                memory_usages = platform_data.get('memory_usage', [])
                if memory_usages:
                    avg_memory = statistics.mean(memory_usages)
                    if avg_memory > 4000:  # 超过4GB
                        bottlenecks.append({
                            'type': 'high_memory_usage',
                            'platform': plt,
                            'metric': 'memory_usage',
                            'value': avg_memory,
                            'severity': 'high' if avg_memory > 8000 else 'medium'
                        })
            
            return bottlenecks
            
        except Exception as e:
            self.logger.error(f"识别性能瓶颈失败: {e}")
            return []
    
    async def _identify_resource_waste(self, platform: str = None) -> List[Dict[str, Any]]:
        """识别资源浪费"""
        waste_issues = []
        
        try:
            # 分析任务失败率
            for task_key, metrics in self.performance_metrics.items():
                if platform and not task_key.endswith(f"_{platform}"):
                    continue
                
                if len(metrics) < 10:
                    continue
                
                recent_metrics = metrics[-50:]  # 最近50次执行
                failure_rate = 1 - (sum(1 for m in recent_metrics if m.success) / len(recent_metrics))
                
                if failure_rate > 0.2:  # 失败率超过20%
                    waste_issues.append({
                        'type': 'high_failure_rate',
                        'task_key': task_key,
                        'metric': 'failure_rate',
                        'value': failure_rate,
                        'severity': 'high' if failure_rate > 0.5 else 'medium'
                    })
            
            return waste_issues
            
        except Exception as e:
            self.logger.error(f"识别资源浪费失败: {e}")
            return []
    
    async def _create_recommendation_for_bottleneck(self, bottleneck: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """为性能瓶颈创建优化建议"""
        try:
            bottleneck_type = bottleneck['type']
            platform = bottleneck['platform']
            value = bottleneck['value']
            severity = bottleneck['severity']
            
            if bottleneck_type == 'slow_execution':
                return OptimizationRecommendation(
                    task_id=f"bottleneck_{bottleneck_type}_{platform}",
                    recommendation_type="performance_optimization",
                    description=f"平台 {platform} 执行时间过长 ({value:.1f}秒)，建议优化任务并行度或迁移到更强的平台",
                    expected_improvement=0.3,
                    confidence=0.8,
                    implementation_priority=1 if severity == 'high' else 2
                )
            elif bottleneck_type == 'high_cpu_usage':
                return OptimizationRecommendation(
                    task_id=f"bottleneck_{bottleneck_type}_{platform}",
                    recommendation_type="resource_optimization",
                    description=f"平台 {platform} CPU使用率过高 ({value:.1f}%)，建议限制并发任务数或升级硬件",
                    expected_improvement=0.25,
                    confidence=0.7,
                    implementation_priority=1 if severity == 'high' else 3
                )
            elif bottleneck_type == 'high_memory_usage':
                return OptimizationRecommendation(
                    task_id=f"bottleneck_{bottleneck_type}_{platform}",
                    recommendation_type="memory_optimization",
                    description=f"平台 {platform} 内存使用过高 ({value:.1f}MB)，建议优化内存使用或增加内存",
                    expected_improvement=0.2,
                    confidence=0.75,
                    implementation_priority=2 if severity == 'high' else 4
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"创建瓶颈优化建议失败: {e}")
            return None
    
    async def _create_recommendation_for_waste(self, waste: Dict[str, Any]) -> Optional[OptimizationRecommendation]:
        """为资源浪费创建优化建议"""
        try:
            waste_type = waste['type']
            task_key = waste['task_key']
            value = waste['value']
            severity = waste['severity']
            
            if waste_type == 'high_failure_rate':
                return OptimizationRecommendation(
                    task_id=f"waste_{waste_type}_{task_key}",
                    recommendation_type="reliability_improvement",
                    description=f"任务 {task_key} 失败率过高 ({value:.1%})，建议检查任务配置或增加重试机制",
                    expected_improvement=0.4,
                    confidence=0.85,
                    implementation_priority=1 if severity == 'high' else 2
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"创建浪费优化建议失败: {e}")
            return None
    
    async def _cleanup_cache(self) -> None:
        """清理过期缓存"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, timestamp in self.cache_timestamps.items():
                if (current_time - timestamp).seconds > self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.prediction_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
                
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")
    
    async def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        try:
            total_tasks = len(self.task_history)
            
            if total_tasks == 0:
                return {
                    "total_tasks": 0,
                    "platforms": {},
                    "task_types": {},
                    "overall_success_rate": 0.0,
                    "average_execution_time": 0.0
                }
            
            # 平台统计
            platform_stats = {}
            for platform, data in self.platform_performance.items():
                execution_times = data.get('execution_time', [])
                platform_stats[platform] = {
                    "task_count": len(execution_times),
                    "average_execution_time": statistics.mean(execution_times) if execution_times else 0,
                    "average_cpu_usage": statistics.mean(data.get('cpu_usage', [0])),
                    "average_memory_usage": statistics.mean(data.get('memory_usage', [0]))
                }
            
            # 任务类型统计
            task_type_stats = {}
            for task_key, metrics in self.performance_metrics.items():
                task_type = task_key.split('_')[0]
                if task_type not in task_type_stats:
                    task_type_stats[task_type] = {
                        "task_count": 0,
                        "success_count": 0,
                        "total_execution_time": 0
                    }
                
                task_type_stats[task_type]["task_count"] += len(metrics)
                task_type_stats[task_type]["success_count"] += sum(1 for m in metrics if m.success)
                task_type_stats[task_type]["total_execution_time"] += sum(m.execution_time for m in metrics)
            
            # 计算成功率和平均执行时间
            for task_type, stats in task_type_stats.items():
                stats["success_rate"] = stats["success_count"] / stats["task_count"] if stats["task_count"] > 0 else 0
                stats["average_execution_time"] = stats["total_execution_time"] / stats["task_count"] if stats["task_count"] > 0 else 0
            
            # 总体统计
            overall_success_rate = sum(1 for task in self.task_history if task.success) / total_tasks
            average_execution_time = statistics.mean([task.execution_time for task in self.task_history])
            
            return {
                "total_tasks": total_tasks,
                "platforms": platform_stats,
                "task_types": task_type_stats,
                "overall_success_rate": overall_success_rate,
                "average_execution_time": average_execution_time,
                "cache_size": len(self.prediction_cache),
                "optimization_recommendations_count": len(await self.generate_optimization_recommendations())
            }
            
        except Exception as e:
            self.logger.error(f"获取优化统计信息失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取优化器状态"""
        return {
            "status": "active",
            "total_tasks_recorded": len(self.task_history),
            "platforms_monitored": len(self.platform_performance),
            "task_types_tracked": len(self.performance_metrics),
            "cache_entries": len(self.prediction_cache),
            "learning_rate": self.learning_rate,
            "optimization_threshold": self.optimization_threshold,
            "confidence_threshold": self.confidence_threshold
        }

