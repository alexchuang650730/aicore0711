"""
工具性能监控器

监控MCP工具的性能指标，包括响应时间、成功率、资源使用等
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    tool_id: str
    response_time: float
    success_rate: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    throughput: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    tool_id: str
    metric_type: str
    threshold: float
    current_value: float
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

class PerformanceMonitor:
    """工具性能监控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化性能监控器"""
        self.config = config or {}
        
        # 性能数据存储
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.current_metrics: Dict[str, PerformanceMetrics] = {}
        self.alerts: List[PerformanceAlert] = []
        
        # 监控配置
        self.monitoring_interval = self.config.get('monitoring_interval', 30)  # 秒
        self.alert_thresholds = self.config.get('alert_thresholds', {
            'response_time': 5.0,  # 秒
            'error_rate': 0.1,     # 10%
            'cpu_usage': 80.0,     # 80%
            'memory_usage': 80.0   # 80%
        })
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        logger.info("PerformanceMonitor initialized")
    
    async def start_monitoring(self):
        """开始性能监控"""
        if self.is_monitoring:
            logger.warning("Performance monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                await self._collect_metrics()
                await self._check_alerts()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_metrics(self):
        """收集性能指标"""
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        
        # 为每个工具收集指标
        for tool_id in self.current_metrics.keys():
            try:
                metrics = await self._collect_tool_metrics(tool_id, cpu_percent, memory_info.percent)
                self.metrics_history[tool_id].append(metrics)
                self.current_metrics[tool_id] = metrics
            except Exception as e:
                logger.error(f"Error collecting metrics for tool {tool_id}: {e}")
    
    async def _collect_tool_metrics(self, tool_id: str, cpu_usage: float, memory_usage: float) -> PerformanceMetrics:
        """收集单个工具的性能指标"""
        # 计算响应时间（基于历史数据）
        history = list(self.metrics_history[tool_id])
        if history:
            recent_metrics = history[-10:]  # 最近10次
            avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        else:
            avg_response_time = 0.0
        
        # 计算成功率和错误率
        if history:
            recent_metrics = history[-100:]  # 最近100次
            success_count = sum(1 for m in recent_metrics if m.error_rate < 0.1)
            success_rate = success_count / len(recent_metrics)
            error_rate = 1 - success_rate
        else:
            success_rate = 1.0
            error_rate = 0.0
        
        # 计算吞吐量
        if len(history) >= 2:
            time_diff = (history[-1].timestamp - history[-2].timestamp).total_seconds()
            throughput = 1.0 / time_diff if time_diff > 0 else 0.0
        else:
            throughput = 0.0
        
        return PerformanceMetrics(
            tool_id=tool_id,
            response_time=avg_response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            throughput=throughput
        )
    
    async def _check_alerts(self):
        """检查性能告警"""
        for tool_id, metrics in self.current_metrics.items():
            # 检查响应时间告警
            if metrics.response_time > self.alert_thresholds['response_time']:
                await self._create_alert(
                    tool_id, 'response_time', 
                    self.alert_thresholds['response_time'],
                    metrics.response_time,
                    'high',
                    f"Tool {tool_id} response time ({metrics.response_time:.2f}s) exceeds threshold"
                )
            
            # 检查错误率告警
            if metrics.error_rate > self.alert_thresholds['error_rate']:
                await self._create_alert(
                    tool_id, 'error_rate',
                    self.alert_thresholds['error_rate'],
                    metrics.error_rate,
                    'medium',
                    f"Tool {tool_id} error rate ({metrics.error_rate:.2%}) exceeds threshold"
                )
            
            # 检查CPU使用率告警
            if metrics.cpu_usage > self.alert_thresholds['cpu_usage']:
                await self._create_alert(
                    tool_id, 'cpu_usage',
                    self.alert_thresholds['cpu_usage'],
                    metrics.cpu_usage,
                    'medium',
                    f"Tool {tool_id} CPU usage ({metrics.cpu_usage:.1f}%) exceeds threshold"
                )
            
            # 检查内存使用率告警
            if metrics.memory_usage > self.alert_thresholds['memory_usage']:
                await self._create_alert(
                    tool_id, 'memory_usage',
                    self.alert_thresholds['memory_usage'],
                    metrics.memory_usage,
                    'medium',
                    f"Tool {tool_id} memory usage ({metrics.memory_usage:.1f}%) exceeds threshold"
                )
    
    async def _create_alert(self, tool_id: str, metric_type: str, threshold: float, 
                          current_value: float, severity: str, message: str):
        """创建性能告警"""
        alert = PerformanceAlert(
            alert_id=f"alert_{tool_id}_{metric_type}_{int(time.time())}",
            tool_id=tool_id,
            metric_type=metric_type,
            threshold=threshold,
            current_value=current_value,
            severity=severity,
            message=message
        )
        
        self.alerts.append(alert)
        logger.warning(f"Performance alert: {message}")
        
        # 保持告警列表大小
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-500:]
    
    def record_tool_execution(self, tool_id: str, response_time: float, success: bool):
        """记录工具执行结果"""
        if tool_id not in self.current_metrics:
            self.current_metrics[tool_id] = PerformanceMetrics(
                tool_id=tool_id,
                response_time=response_time,
                success_rate=1.0 if success else 0.0,
                error_rate=0.0 if success else 1.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                throughput=0.0
            )
    
    def get_tool_metrics(self, tool_id: str) -> Optional[PerformanceMetrics]:
        """获取工具性能指标"""
        return self.current_metrics.get(tool_id)
    
    def get_tool_history(self, tool_id: str, limit: int = 100) -> List[PerformanceMetrics]:
        """获取工具历史性能数据"""
        history = list(self.metrics_history[tool_id])
        return history[-limit:] if limit else history
    
    def get_active_alerts(self, severity: str = None) -> List[PerformanceAlert]:
        """获取活跃告警"""
        if severity:
            return [alert for alert in self.alerts if alert.severity == severity]
        return self.alerts.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total_tools = len(self.current_metrics)
        if total_tools == 0:
            return {
                'total_tools': 0,
                'avg_response_time': 0.0,
                'avg_success_rate': 0.0,
                'total_alerts': len(self.alerts)
            }
        
        avg_response_time = sum(m.response_time for m in self.current_metrics.values()) / total_tools
        avg_success_rate = sum(m.success_rate for m in self.current_metrics.values()) / total_tools
        
        return {
            'total_tools': total_tools,
            'avg_response_time': avg_response_time,
            'avg_success_rate': avg_success_rate,
            'total_alerts': len(self.alerts),
            'monitoring_status': 'active' if self.is_monitoring else 'inactive'
        }

