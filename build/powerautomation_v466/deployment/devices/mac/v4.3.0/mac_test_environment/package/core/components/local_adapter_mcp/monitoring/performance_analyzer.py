"""
Performance Analyzer - 性能分析器
为ClaudEditor提供深度性能分析和趋势预测

功能：
- 性能趋势分析
- 瓶颈识别和诊断
- 性能回归检测
- 优化建议生成
- 预测性分析
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import statistics
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

class AnalysisType(Enum):
    """分析类型"""
    TREND_ANALYSIS = "trend_analysis"
    BOTTLENECK_DETECTION = "bottleneck_detection"
    REGRESSION_DETECTION = "regression_detection"
    PREDICTION = "prediction"
    OPTIMIZATION = "optimization"

class PerformanceLevel(Enum):
    """性能等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class PerformanceTrend:
    """性能趋势"""
    metric_name: str
    time_period: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    correlation_coefficient: float
    p_value: float
    confidence_level: float
    data_points: int
    start_value: float
    end_value: float
    change_percentage: float

@dataclass
class BottleneckInfo:
    """瓶颈信息"""
    component: str
    metric: str
    severity: str  # "high", "medium", "low"
    current_value: float
    threshold: float
    impact_score: float
    duration: timedelta
    first_detected: datetime
    last_detected: datetime
    frequency: int
    recommendations: List[str]

@dataclass
class PerformanceRegression:
    """性能回归"""
    metric_name: str
    regression_type: str  # "sudden", "gradual"
    severity: PerformanceLevel
    detected_at: datetime
    baseline_period: Tuple[datetime, datetime]
    regression_period: Tuple[datetime, datetime]
    baseline_average: float
    current_average: float
    degradation_percentage: float
    confidence_score: float
    potential_causes: List[str]

@dataclass
class PerformancePrediction:
    """性能预测"""
    metric_name: str
    prediction_horizon: timedelta
    predicted_values: List[float]
    confidence_intervals: List[Tuple[float, float]]
    trend_forecast: str
    risk_assessment: str
    recommended_actions: List[str]
    model_accuracy: float

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 分析配置
        self.analysis_window = timedelta(hours=24)
        self.trend_min_points = 10
        self.bottleneck_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time": 5.0,
            "error_rate": 5.0
        }
        
        # 缓存
        self.analysis_cache = {}
        self.cache_ttl = timedelta(minutes=15)
        
        # 历史分析结果
        self.trend_history = defaultdict(list)
        self.bottleneck_history = defaultdict(list)
        self.regression_history = []
        
        self.logger.info("性能分析器初始化完成")
    
    async def analyze_performance_trends(self, 
                                       metrics_data: List[Dict[str, Any]], 
                                       metric_names: List[str]) -> List[PerformanceTrend]:
        """
        分析性能趋势
        
        Args:
            metrics_data: 指标数据列表
            metric_names: 要分析的指标名称
            
        Returns:
            List[PerformanceTrend]: 趋势分析结果
        """
        try:
            trends = []
            
            for metric_name in metric_names:
                trend = await self._analyze_single_metric_trend(metrics_data, metric_name)
                if trend:
                    trends.append(trend)
                    self.trend_history[metric_name].append(trend)
            
            self.logger.info(f"完成趋势分析，分析了 {len(metric_names)} 个指标")
            return trends
            
        except Exception as e:
            self.logger.error(f"趋势分析失败: {e}")
            return []
    
    async def _analyze_single_metric_trend(self, 
                                         metrics_data: List[Dict[str, Any]], 
                                         metric_name: str) -> Optional[PerformanceTrend]:
        """分析单个指标的趋势"""
        try:
            # 提取指标值和时间戳
            values = []
            timestamps = []
            
            for data in metrics_data:
                if metric_name in data:
                    values.append(float(data[metric_name]))
                    timestamps.append(data.get('timestamp', datetime.now()))
            
            if len(values) < self.trend_min_points:
                return None
            
            # 转换为数值数组
            x = np.arange(len(values))
            y = np.array(values)
            
            # 线性回归分析
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # 确定趋势方向
            if abs(slope) < 0.01:
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"
            
            # 计算趋势强度
            trend_strength = min(abs(r_value), 1.0)
            
            # 计算变化百分比
            start_value = values[0]
            end_value = values[-1]
            change_percentage = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0
            
            # 计算置信度
            confidence_level = 1 - p_value if p_value < 1 else 0
            
            return PerformanceTrend(
                metric_name=metric_name,
                time_period=f"{len(values)} data points",
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                correlation_coefficient=r_value,
                p_value=p_value,
                confidence_level=confidence_level,
                data_points=len(values),
                start_value=start_value,
                end_value=end_value,
                change_percentage=change_percentage
            )
            
        except Exception as e:
            self.logger.error(f"分析指标 {metric_name} 趋势失败: {e}")
            return None
    
    async def detect_bottlenecks(self, 
                               current_metrics: Dict[str, Any],
                               historical_data: List[Dict[str, Any]]) -> List[BottleneckInfo]:
        """
        检测性能瓶颈
        
        Args:
            current_metrics: 当前指标
            historical_data: 历史数据
            
        Returns:
            List[BottleneckInfo]: 瓶颈信息列表
        """
        try:
            bottlenecks = []
            
            for metric_name, threshold in self.bottleneck_thresholds.items():
                if metric_name in current_metrics:
                    bottleneck = await self._detect_metric_bottleneck(
                        metric_name, 
                        current_metrics[metric_name],
                        threshold,
                        historical_data
                    )
                    if bottleneck:
                        bottlenecks.append(bottleneck)
                        self.bottleneck_history[metric_name].append(bottleneck)
            
            self.logger.info(f"检测到 {len(bottlenecks)} 个性能瓶颈")
            return bottlenecks
            
        except Exception as e:
            self.logger.error(f"瓶颈检测失败: {e}")
            return []
    
    async def _detect_metric_bottleneck(self,
                                      metric_name: str,
                                      current_value: float,
                                      threshold: float,
                                      historical_data: List[Dict[str, Any]]) -> Optional[BottleneckInfo]:
        """检测单个指标的瓶颈"""
        try:
            if current_value <= threshold:
                return None
            
            # 计算严重程度
            severity_ratio = current_value / threshold
            if severity_ratio >= 1.5:
                severity = "high"
            elif severity_ratio >= 1.2:
                severity = "medium"
            else:
                severity = "low"
            
            # 计算影响分数
            impact_score = min((severity_ratio - 1) * 100, 100)
            
            # 分析历史数据中的瓶颈频率
            frequency = 0
            first_detected = datetime.now()
            last_detected = datetime.now()
            
            for data in historical_data:
                if metric_name in data and data[metric_name] > threshold:
                    frequency += 1
                    timestamp = data.get('timestamp', datetime.now())
                    if timestamp < first_detected:
                        first_detected = timestamp
                    if timestamp > last_detected:
                        last_detected = timestamp
            
            duration = last_detected - first_detected
            
            # 生成优化建议
            recommendations = self._generate_bottleneck_recommendations(metric_name, current_value, severity)
            
            return BottleneckInfo(
                component=self._get_component_name(metric_name),
                metric=metric_name,
                severity=severity,
                current_value=current_value,
                threshold=threshold,
                impact_score=impact_score,
                duration=duration,
                first_detected=first_detected,
                last_detected=last_detected,
                frequency=frequency,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"检测指标 {metric_name} 瓶颈失败: {e}")
            return None
    
    def _generate_bottleneck_recommendations(self, 
                                           metric_name: str, 
                                           current_value: float, 
                                           severity: str) -> List[str]:
        """生成瓶颈优化建议"""
        recommendations = []
        
        if metric_name == "cpu_percent":
            recommendations.extend([
                "检查CPU密集型进程并考虑优化",
                "增加CPU核心数或升级处理器",
                "优化算法以减少计算复杂度",
                "考虑将部分任务迁移到云端执行"
            ])
        elif metric_name == "memory_percent":
            recommendations.extend([
                "检查内存泄漏问题",
                "增加系统内存容量",
                "优化数据结构以减少内存使用",
                "实施内存缓存清理策略"
            ])
        elif metric_name == "disk_percent":
            recommendations.extend([
                "清理临时文件和日志",
                "增加存储容量",
                "实施数据归档策略",
                "优化数据存储格式"
            ])
        elif metric_name == "response_time":
            recommendations.extend([
                "优化数据库查询",
                "实施缓存策略",
                "优化网络连接",
                "考虑异步处理"
            ])
        
        if severity == "high":
            recommendations.insert(0, "立即采取行动，系统性能严重受影响")
        
        return recommendations
    
    def _get_component_name(self, metric_name: str) -> str:
        """根据指标名称获取组件名称"""
        component_mapping = {
            "cpu_percent": "CPU",
            "memory_percent": "Memory",
            "disk_percent": "Storage",
            "response_time": "Network",
            "error_rate": "Application"
        }
        return component_mapping.get(metric_name, "System")
    
    async def detect_performance_regression(self,
                                          current_data: List[Dict[str, Any]],
                                          baseline_data: List[Dict[str, Any]],
                                          metric_names: List[str]) -> List[PerformanceRegression]:
        """
        检测性能回归
        
        Args:
            current_data: 当前时期数据
            baseline_data: 基线时期数据
            metric_names: 要检查的指标名称
            
        Returns:
            List[PerformanceRegression]: 性能回归列表
        """
        try:
            regressions = []
            
            for metric_name in metric_names:
                regression = await self._detect_metric_regression(
                    metric_name, current_data, baseline_data
                )
                if regression:
                    regressions.append(regression)
                    self.regression_history.append(regression)
            
            self.logger.info(f"检测到 {len(regressions)} 个性能回归")
            return regressions
            
        except Exception as e:
            self.logger.error(f"性能回归检测失败: {e}")
            return []
    
    async def _detect_metric_regression(self,
                                      metric_name: str,
                                      current_data: List[Dict[str, Any]],
                                      baseline_data: List[Dict[str, Any]]) -> Optional[PerformanceRegression]:
        """检测单个指标的性能回归"""
        try:
            # 提取指标值
            current_values = [d[metric_name] for d in current_data if metric_name in d]
            baseline_values = [d[metric_name] for d in baseline_data if metric_name in d]
            
            if len(current_values) < 5 or len(baseline_values) < 5:
                return None
            
            # 计算平均值
            current_avg = statistics.mean(current_values)
            baseline_avg = statistics.mean(baseline_values)
            
            # 计算退化百分比
            degradation_percentage = ((current_avg - baseline_avg) / baseline_avg) * 100
            
            # 判断是否为回归（性能下降）
            if degradation_percentage <= 5:  # 5%阈值
                return None
            
            # 统计显著性检验
            t_stat, p_value = stats.ttest_ind(current_values, baseline_values)
            confidence_score = 1 - p_value if p_value < 1 else 0
            
            # 确定严重程度
            if degradation_percentage >= 50:
                severity = PerformanceLevel.CRITICAL
            elif degradation_percentage >= 30:
                severity = PerformanceLevel.POOR
            elif degradation_percentage >= 15:
                severity = PerformanceLevel.AVERAGE
            else:
                severity = PerformanceLevel.GOOD
            
            # 确定回归类型
            regression_type = self._determine_regression_type(current_values)
            
            # 生成潜在原因
            potential_causes = self._generate_regression_causes(metric_name, degradation_percentage)
            
            return PerformanceRegression(
                metric_name=metric_name,
                regression_type=regression_type,
                severity=severity,
                detected_at=datetime.now(),
                baseline_period=(
                    baseline_data[0].get('timestamp', datetime.now()),
                    baseline_data[-1].get('timestamp', datetime.now())
                ),
                regression_period=(
                    current_data[0].get('timestamp', datetime.now()),
                    current_data[-1].get('timestamp', datetime.now())
                ),
                baseline_average=baseline_avg,
                current_average=current_avg,
                degradation_percentage=degradation_percentage,
                confidence_score=confidence_score,
                potential_causes=potential_causes
            )
            
        except Exception as e:
            self.logger.error(f"检测指标 {metric_name} 回归失败: {e}")
            return None
    
    def _determine_regression_type(self, values: List[float]) -> str:
        """确定回归类型"""
        if len(values) < 3:
            return "unknown"
        
        # 计算变化率
        changes = [values[i] - values[i-1] for i in range(1, len(values))]
        avg_change = statistics.mean(changes)
        
        # 检查是否为突然变化
        max_change = max(abs(c) for c in changes)
        if max_change > abs(avg_change) * 3:
            return "sudden"
        else:
            return "gradual"
    
    def _generate_regression_causes(self, metric_name: str, degradation_percentage: float) -> List[str]:
        """生成性能回归的潜在原因"""
        causes = []
        
        common_causes = [
            "系统负载增加",
            "软件更新或配置变更",
            "硬件老化或故障",
            "网络环境变化"
        ]
        
        if metric_name == "cpu_percent":
            causes.extend([
                "新增CPU密集型任务",
                "算法效率下降",
                "并发处理增加"
            ])
        elif metric_name == "memory_percent":
            causes.extend([
                "内存泄漏",
                "数据集大小增加",
                "缓存策略变更"
            ])
        elif metric_name == "response_time":
            causes.extend([
                "网络延迟增加",
                "数据库性能下降",
                "第三方服务响应慢"
            ])
        
        causes.extend(common_causes)
        return causes[:5]  # 返回前5个最可能的原因
    
    async def predict_performance(self,
                                historical_data: List[Dict[str, Any]],
                                metric_name: str,
                                prediction_horizon: timedelta) -> Optional[PerformancePrediction]:
        """
        预测性能趋势
        
        Args:
            historical_data: 历史数据
            metric_name: 指标名称
            prediction_horizon: 预测时间范围
            
        Returns:
            Optional[PerformancePrediction]: 预测结果
        """
        try:
            # 提取时间序列数据
            values = []
            timestamps = []
            
            for data in historical_data:
                if metric_name in data:
                    values.append(float(data[metric_name]))
                    timestamps.append(data.get('timestamp', datetime.now()))
            
            if len(values) < 10:
                return None
            
            # 准备训练数据
            X = np.arange(len(values)).reshape(-1, 1)
            y = np.array(values)
            
            # 标准化
            scaler_X = StandardScaler()
            scaler_y = StandardScaler()
            X_scaled = scaler_X.fit_transform(X)
            y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()
            
            # 训练线性回归模型
            model = LinearRegression()
            model.fit(X_scaled, y_scaled)
            
            # 计算模型准确性
            y_pred_scaled = model.predict(X_scaled)
            y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
            model_accuracy = 1 - np.mean(np.abs(y - y_pred) / y)
            
            # 预测未来值
            prediction_points = int(prediction_horizon.total_seconds() / 300)  # 5分钟间隔
            future_X = np.arange(len(values), len(values) + prediction_points).reshape(-1, 1)
            future_X_scaled = scaler_X.transform(future_X)
            future_y_scaled = model.predict(future_X_scaled)
            predicted_values = scaler_y.inverse_transform(future_y_scaled.reshape(-1, 1)).ravel()
            
            # 计算置信区间（简化版本）
            std_error = np.std(y - y_pred)
            confidence_intervals = [
                (val - 1.96 * std_error, val + 1.96 * std_error)
                for val in predicted_values
            ]
            
            # 趋势预测
            if model.coef_[0] > 0.01:
                trend_forecast = "increasing"
            elif model.coef_[0] < -0.01:
                trend_forecast = "decreasing"
            else:
                trend_forecast = "stable"
            
            # 风险评估
            max_predicted = max(predicted_values)
            risk_assessment = self._assess_prediction_risk(metric_name, max_predicted)
            
            # 推荐行动
            recommended_actions = self._generate_prediction_recommendations(
                metric_name, trend_forecast, max_predicted
            )
            
            return PerformancePrediction(
                metric_name=metric_name,
                prediction_horizon=prediction_horizon,
                predicted_values=predicted_values.tolist(),
                confidence_intervals=confidence_intervals,
                trend_forecast=trend_forecast,
                risk_assessment=risk_assessment,
                recommended_actions=recommended_actions,
                model_accuracy=model_accuracy
            )
            
        except Exception as e:
            self.logger.error(f"性能预测失败: {e}")
            return None
    
    def _assess_prediction_risk(self, metric_name: str, max_predicted: float) -> str:
        """评估预测风险"""
        thresholds = self.bottleneck_thresholds.get(metric_name, 100)
        
        if max_predicted >= thresholds * 1.2:
            return "high"
        elif max_predicted >= thresholds:
            return "medium"
        elif max_predicted >= thresholds * 0.8:
            return "low"
        else:
            return "minimal"
    
    def _generate_prediction_recommendations(self,
                                           metric_name: str,
                                           trend_forecast: str,
                                           max_predicted: float) -> List[str]:
        """生成预测建议"""
        recommendations = []
        
        if trend_forecast == "increasing":
            recommendations.append("监控资源使用趋势，准备扩容计划")
            
            if metric_name == "cpu_percent":
                recommendations.extend([
                    "考虑优化CPU密集型任务",
                    "准备增加计算资源"
                ])
            elif metric_name == "memory_percent":
                recommendations.extend([
                    "检查内存使用模式",
                    "准备内存扩容"
                ])
        
        elif trend_forecast == "decreasing":
            recommendations.append("性能趋势良好，继续监控")
        
        else:
            recommendations.append("性能稳定，保持当前配置")
        
        return recommendations
    
    async def generate_performance_report(self,
                                        trends: List[PerformanceTrend],
                                        bottlenecks: List[BottleneckInfo],
                                        regressions: List[PerformanceRegression],
                                        predictions: List[PerformancePrediction]) -> Dict[str, Any]:
        """
        生成性能分析报告
        
        Args:
            trends: 趋势分析结果
            bottlenecks: 瓶颈信息
            regressions: 性能回归
            predictions: 性能预测
            
        Returns:
            Dict[str, Any]: 完整的性能报告
        """
        try:
            # 计算总体性能评分
            overall_score = self._calculate_overall_performance_score(
                trends, bottlenecks, regressions
            )
            
            # 生成执行摘要
            executive_summary = self._generate_executive_summary(
                overall_score, trends, bottlenecks, regressions
            )
            
            # 优先级建议
            priority_recommendations = self._generate_priority_recommendations(
                bottlenecks, regressions, predictions
            )
            
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "analysis_period": self.analysis_window.total_seconds() / 3600,  # 小时
                "overall_performance_score": overall_score,
                "executive_summary": executive_summary,
                "trends_analysis": {
                    "total_metrics_analyzed": len(trends),
                    "trends": [asdict(trend) for trend in trends]
                },
                "bottlenecks_detection": {
                    "total_bottlenecks": len(bottlenecks),
                    "high_severity": len([b for b in bottlenecks if b.severity == "high"]),
                    "medium_severity": len([b for b in bottlenecks if b.severity == "medium"]),
                    "low_severity": len([b for b in bottlenecks if b.severity == "low"]),
                    "bottlenecks": [asdict(bottleneck) for bottleneck in bottlenecks]
                },
                "regression_analysis": {
                    "total_regressions": len(regressions),
                    "critical_regressions": len([r for r in regressions if r.severity == PerformanceLevel.CRITICAL]),
                    "regressions": [asdict(regression) for regression in regressions]
                },
                "performance_predictions": {
                    "total_predictions": len(predictions),
                    "predictions": [asdict(prediction) for prediction in predictions]
                },
                "priority_recommendations": priority_recommendations,
                "next_analysis_scheduled": (datetime.now() + self.cache_ttl).isoformat()
            }
            
            self.logger.info("性能分析报告生成完成")
            return report
            
        except Exception as e:
            self.logger.error(f"生成性能报告失败: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_performance_score(self,
                                           trends: List[PerformanceTrend],
                                           bottlenecks: List[BottleneckInfo],
                                           regressions: List[PerformanceRegression]) -> float:
        """计算总体性能评分（0-100）"""
        base_score = 100.0
        
        # 瓶颈扣分
        for bottleneck in bottlenecks:
            if bottleneck.severity == "high":
                base_score -= 20
            elif bottleneck.severity == "medium":
                base_score -= 10
            else:
                base_score -= 5
        
        # 回归扣分
        for regression in regressions:
            if regression.severity == PerformanceLevel.CRITICAL:
                base_score -= 25
            elif regression.severity == PerformanceLevel.POOR:
                base_score -= 15
            else:
                base_score -= 8
        
        # 趋势调整
        negative_trends = len([t for t in trends if t.trend_direction == "decreasing"])
        if negative_trends > 0:
            base_score -= negative_trends * 3
        
        return max(0.0, min(100.0, base_score))
    
    def _generate_executive_summary(self,
                                  overall_score: float,
                                  trends: List[PerformanceTrend],
                                  bottlenecks: List[BottleneckInfo],
                                  regressions: List[PerformanceRegression]) -> str:
        """生成执行摘要"""
        if overall_score >= 90:
            status = "优秀"
        elif overall_score >= 75:
            status = "良好"
        elif overall_score >= 60:
            status = "一般"
        elif overall_score >= 40:
            status = "较差"
        else:
            status = "严重"
        
        summary = f"系统整体性能状态：{status}（评分：{overall_score:.1f}/100）。"
        
        if bottlenecks:
            high_severity = len([b for b in bottlenecks if b.severity == "high"])
            if high_severity > 0:
                summary += f" 检测到 {high_severity} 个高严重性瓶颈，需要立即关注。"
        
        if regressions:
            critical_regressions = len([r for r in regressions if r.severity == PerformanceLevel.CRITICAL])
            if critical_regressions > 0:
                summary += f" 发现 {critical_regressions} 个严重性能回归，建议立即调查。"
        
        negative_trends = len([t for t in trends if t.trend_direction == "decreasing"])
        if negative_trends > 0:
            summary += f" {negative_trends} 个指标呈下降趋势，需要持续监控。"
        
        return summary
    
    def _generate_priority_recommendations(self,
                                         bottlenecks: List[BottleneckInfo],
                                         regressions: List[PerformanceRegression],
                                         predictions: List[PerformancePrediction]) -> List[Dict[str, Any]]:
        """生成优先级建议"""
        recommendations = []
        
        # 高优先级：严重瓶颈
        high_bottlenecks = [b for b in bottlenecks if b.severity == "high"]
        for bottleneck in high_bottlenecks:
            recommendations.append({
                "priority": "high",
                "type": "bottleneck",
                "title": f"解决 {bottleneck.component} 性能瓶颈",
                "description": f"{bottleneck.metric} 当前值 {bottleneck.current_value:.1f}，超过阈值 {bottleneck.threshold:.1f}",
                "actions": bottleneck.recommendations[:3],
                "estimated_impact": "high"
            })
        
        # 高优先级：严重回归
        critical_regressions = [r for r in regressions if r.severity == PerformanceLevel.CRITICAL]
        for regression in critical_regressions:
            recommendations.append({
                "priority": "high",
                "type": "regression",
                "title": f"修复 {regression.metric_name} 性能回归",
                "description": f"性能下降 {regression.degradation_percentage:.1f}%",
                "actions": regression.potential_causes[:3],
                "estimated_impact": "high"
            })
        
        # 中优先级：高风险预测
        high_risk_predictions = [p for p in predictions if p.risk_assessment == "high"]
        for prediction in high_risk_predictions:
            recommendations.append({
                "priority": "medium",
                "type": "prediction",
                "title": f"预防 {prediction.metric_name} 性能问题",
                "description": f"预测趋势：{prediction.trend_forecast}，风险等级：{prediction.risk_assessment}",
                "actions": prediction.recommended_actions[:3],
                "estimated_impact": "medium"
            })
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations[:10]  # 返回前10个建议
    
    def get_status(self) -> Dict[str, Any]:
        """获取分析器状态"""
        return {
            "status": "active",
            "analysis_window_hours": self.analysis_window.total_seconds() / 3600,
            "cache_ttl_minutes": self.cache_ttl.total_seconds() / 60,
            "bottleneck_thresholds": self.bottleneck_thresholds,
            "trend_history_count": sum(len(trends) for trends in self.trend_history.values()),
            "bottleneck_history_count": sum(len(bottlenecks) for bottlenecks in self.bottleneck_history.values()),
            "regression_history_count": len(self.regression_history)
        }

