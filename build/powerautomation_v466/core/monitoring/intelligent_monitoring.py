"""
PowerAutomation v4.6.1 智能監控和報告系統
Intelligent Monitoring and Reporting System

監控體系架構：
1. 實時指標收集 (Real-time Metrics Collection)
2. 智能異常檢測 (Intelligent Anomaly Detection)
3. 預測性分析 (Predictive Analytics)
4. 自動化報告生成 (Automated Report Generation)
5. 可視化儀表板 (Visualization Dashboard)
6. 告警和通知系統 (Alert and Notification System)

監控範圍：
- 系統性能監控 (CPU、Memory、Disk、Network)
- 應用程序監控 (API響應時間、錯誤率、吞吐量)
- 用戶行為監控 (使用模式、功能熱度、性能瓶頸)
- 業務指標監控 (代碼生成量、測試覆蓋率、部署成功率)
- 安全監控 (訪問異常、權限變更、安全事件)
"""

import asyncio
import logging
import json
import os
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque
import statistics
import uuid

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指標類型"""
    COUNTER = "counter"           # 計數器
    GAUGE = "gauge"              # 儀表盤
    HISTOGRAM = "histogram"       # 直方圖
    SUMMARY = "summary"          # 摘要
    TIMER = "timer"              # 計時器


class AlertSeverity(Enum):
    """告警嚴重程度"""
    CRITICAL = "critical"        # 嚴重
    HIGH = "high"               # 高
    MEDIUM = "medium"           # 中
    LOW = "low"                 # 低
    INFO = "info"               # 信息


class MonitoringScope(Enum):
    """監控範圍"""
    SYSTEM = "system"           # 系統監控
    APPLICATION = "application" # 應用監控
    USER = "user"              # 用戶監控
    BUSINESS = "business"       # 業務監控
    SECURITY = "security"       # 安全監控


@dataclass
class MetricPoint:
    """指標數據點"""
    name: str
    value: Union[int, float]
    timestamp: str
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class Alert:
    """告警信息"""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    scope: MonitoringScope
    metric_name: str
    threshold: Union[int, float]
    current_value: Union[int, float]
    triggered_at: str
    resolved_at: Optional[str] = None
    is_resolved: bool = False
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringReport:
    """監控報告"""
    id: str
    report_type: str
    scope: MonitoringScope
    period_start: str
    period_end: str
    summary: Dict[str, Any]
    metrics: List[MetricPoint]
    alerts: List[Alert]
    insights: List[str]
    recommendations: List[str]
    generated_at: str


@dataclass
class DashboardWidget:
    """儀表板組件"""
    id: str
    title: str
    widget_type: str  # "chart", "gauge", "table", "alert_list"
    metric_names: List[str]
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)


class MetricsCollector:
    """指標收集器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics_buffer = deque(maxlen=10000)
        self.collectors = {}
        self.collection_interval = 30  # 30秒
        self.is_collecting = False
        
    async def initialize(self):
        """初始化指標收集器"""
        self.logger.info("📊 初始化指標收集器")
        
        # 註冊系統指標收集器
        self.collectors["system"] = self._collect_system_metrics
        self.collectors["application"] = self._collect_application_metrics
        self.collectors["user"] = self._collect_user_metrics
        self.collectors["business"] = self._collect_business_metrics
        self.collectors["security"] = self._collect_security_metrics
        
        self.logger.info("✅ 指標收集器初始化完成")
    
    async def start_collection(self):
        """開始指標收集"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.logger.info("🔄 開始指標收集")
        
        # 在後台線程中運行收集
        collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        collection_thread.start()
    
    def stop_collection(self):
        """停止指標收集"""
        self.is_collecting = False
        self.logger.info("⏹️ 停止指標收集")
    
    def _collection_loop(self):
        """指標收集循環"""
        while self.is_collecting:
            try:
                # 收集所有類型的指標
                for scope, collector in self.collectors.items():
                    metrics = collector()
                    for metric in metrics:
                        self.metrics_buffer.append(metric)
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"指標收集錯誤: {e}")
                time.sleep(5)  # 錯誤後等待5秒重試
    
    def _collect_system_metrics(self) -> List[MetricPoint]:
        """收集系統指標"""
        timestamp = datetime.now().isoformat()
        metrics = []
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(MetricPoint(
            name="system.cpu.usage_percent",
            value=cpu_percent,
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "system"}
        ))
        
        # 內存使用率
        memory = psutil.virtual_memory()
        metrics.append(MetricPoint(
            name="system.memory.usage_percent",
            value=memory.percent,
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "system"}
        ))
        
        metrics.append(MetricPoint(
            name="system.memory.available_bytes",
            value=memory.available,
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "system"}
        ))
        
        # 磁盤使用率
        disk = psutil.disk_usage('/')
        metrics.append(MetricPoint(
            name="system.disk.usage_percent",
            value=(disk.used / disk.total) * 100,
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "system"}
        ))
        
        # 網絡IO
        net_io = psutil.net_io_counters()
        metrics.append(MetricPoint(
            name="system.network.bytes_sent",
            value=net_io.bytes_sent,
            timestamp=timestamp,
            metric_type=MetricType.COUNTER,
            labels={"scope": "system"}
        ))
        
        metrics.append(MetricPoint(
            name="system.network.bytes_recv",
            value=net_io.bytes_recv,
            timestamp=timestamp,
            metric_type=MetricType.COUNTER,
            labels={"scope": "system"}
        ))
        
        return metrics
    
    def _collect_application_metrics(self) -> List[MetricPoint]:
        """收集應用指標"""
        timestamp = datetime.now().isoformat()
        metrics = []
        
        # 模擬應用指標
        metrics.append(MetricPoint(
            name="app.api.response_time_ms",
            value=statistics.normalvariate(150, 50),  # 平均150ms，標準差50ms
            timestamp=timestamp,
            metric_type=MetricType.HISTOGRAM,
            labels={"scope": "application", "endpoint": "api"}
        ))
        
        metrics.append(MetricPoint(
            name="app.api.requests_per_second",
            value=statistics.normalvariate(10, 3),  # 平均10 RPS
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "application"}
        ))
        
        metrics.append(MetricPoint(
            name="app.errors.count",
            value=statistics.poisson(0.5),  # 平均0.5個錯誤
            timestamp=timestamp,
            metric_type=MetricType.COUNTER,
            labels={"scope": "application"}
        ))
        
        return metrics
    
    def _collect_user_metrics(self) -> List[MetricPoint]:
        """收集用戶指標"""
        timestamp = datetime.now().isoformat()
        metrics = []
        
        # 模擬用戶指標
        metrics.append(MetricPoint(
            name="user.active_sessions",
            value=statistics.randint(5, 50),
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "user"}
        ))
        
        metrics.append(MetricPoint(
            name="user.feature_usage.code_generation",
            value=statistics.randint(20, 100),
            timestamp=timestamp,
            metric_type=MetricType.COUNTER,
            labels={"scope": "user", "feature": "code_generation"}
        ))
        
        return metrics
    
    def _collect_business_metrics(self) -> List[MetricPoint]:
        """收集業務指標"""
        timestamp = datetime.now().isoformat()
        metrics = []
        
        # 模擬業務指標
        metrics.append(MetricPoint(
            name="business.code_lines_generated",
            value=statistics.randint(500, 2000),
            timestamp=timestamp,
            metric_type=MetricType.COUNTER,
            labels={"scope": "business"}
        ))
        
        metrics.append(MetricPoint(
            name="business.test_coverage_percent",
            value=statistics.normalvariate(85, 10),
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "business"}
        ))
        
        metrics.append(MetricPoint(
            name="business.deployment_success_rate",
            value=statistics.normalvariate(95, 5),
            timestamp=timestamp,
            metric_type=MetricType.GAUGE,
            labels={"scope": "business"}
        ))
        
        return metrics
    
    def _collect_security_metrics(self) -> List[MetricPoint]:
        """收集安全指標"""
        timestamp = datetime.now().isoformat()
        metrics = []
        
        # 模擬安全指標
        metrics.append(MetricPoint(
            name="security.failed_login_attempts",
            value=statistics.poisson(1),
            timestamp=timestamp,
            metric_type=MetricType.COUNTER,
            labels={"scope": "security"}
        ))
        
        metrics.append(MetricPoint(
            name="security.vulnerabilities_detected",
            value=statistics.poisson(0.1),
            timestamp=timestamp,
            metric_type=MetricType.COUNTER,
            labels={"scope": "security"}
        ))
        
        return metrics
    
    def get_recent_metrics(self, metric_name: str = None, duration_minutes: int = 60) -> List[MetricPoint]:
        """獲取最近的指標"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        recent_metrics = []
        for metric in self.metrics_buffer:
            metric_time = datetime.fromisoformat(metric.timestamp)
            if metric_time >= cutoff_time:
                if metric_name is None or metric.name == metric_name:
                    recent_metrics.append(metric)
        
        return recent_metrics


class AnomalyDetector:
    """異常檢測器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.thresholds = {}
        self.baseline_data = defaultdict(list)
        
    async def initialize(self):
        """初始化異常檢測器"""
        self.logger.info("🔍 初始化異常檢測器")
        
        # 設置默認閾值
        self.thresholds = {
            "system.cpu.usage_percent": {"high": 80, "critical": 95},
            "system.memory.usage_percent": {"high": 85, "critical": 95},
            "system.disk.usage_percent": {"high": 80, "critical": 90},
            "app.api.response_time_ms": {"high": 500, "critical": 1000},
            "app.errors.count": {"high": 10, "critical": 50},
            "security.failed_login_attempts": {"high": 5, "critical": 20}
        }
        
        self.logger.info("✅ 異常檢測器初始化完成")
    
    def detect_anomalies(self, metrics: List[MetricPoint]) -> List[Alert]:
        """檢測異常"""
        alerts = []
        
        for metric in metrics:
            # 閾值檢測
            threshold_alert = self._check_threshold_anomaly(metric)
            if threshold_alert:
                alerts.append(threshold_alert)
            
            # 統計異常檢測
            statistical_alert = self._check_statistical_anomaly(metric)
            if statistical_alert:
                alerts.append(statistical_alert)
        
        return alerts
    
    def _check_threshold_anomaly(self, metric: MetricPoint) -> Optional[Alert]:
        """檢查閾值異常"""
        if metric.name not in self.thresholds:
            return None
        
        thresholds = self.thresholds[metric.name]
        
        if "critical" in thresholds and metric.value >= thresholds["critical"]:
            return Alert(
                id=str(uuid.uuid4()),
                name=f"{metric.name} Critical Threshold",
                description=f"{metric.name} 超過嚴重閾值",
                severity=AlertSeverity.CRITICAL,
                scope=MonitoringScope(metric.labels.get("scope", "system")),
                metric_name=metric.name,
                threshold=thresholds["critical"],
                current_value=metric.value,
                triggered_at=metric.timestamp,
                labels=metric.labels
            )
        
        elif "high" in thresholds and metric.value >= thresholds["high"]:
            return Alert(
                id=str(uuid.uuid4()),
                name=f"{metric.name} High Threshold",
                description=f"{metric.name} 超過高閾值",
                severity=AlertSeverity.HIGH,
                scope=MonitoringScope(metric.labels.get("scope", "system")),
                metric_name=metric.name,
                threshold=thresholds["high"],
                current_value=metric.value,
                triggered_at=metric.timestamp,
                labels=metric.labels
            )
        
        return None
    
    def _check_statistical_anomaly(self, metric: MetricPoint) -> Optional[Alert]:
        """檢查統計異常"""
        # 收集基線數據
        self.baseline_data[metric.name].append(metric.value)
        
        # 保持最近100個數據點
        if len(self.baseline_data[metric.name]) > 100:
            self.baseline_data[metric.name] = self.baseline_data[metric.name][-100:]
        
        # 需要至少30個數據點才能進行統計分析
        if len(self.baseline_data[metric.name]) < 30:
            return None
        
        data = self.baseline_data[metric.name]
        mean = statistics.mean(data)
        stdev = statistics.stdev(data)
        
        # 3-sigma規則檢測異常
        if abs(metric.value - mean) > 3 * stdev:
            return Alert(
                id=str(uuid.uuid4()),
                name=f"{metric.name} Statistical Anomaly",
                description=f"{metric.name} 統計異常 (3-sigma)",
                severity=AlertSeverity.MEDIUM,
                scope=MonitoringScope(metric.labels.get("scope", "system")),
                metric_name=metric.name,
                threshold=mean + 3 * stdev,
                current_value=metric.value,
                triggered_at=metric.timestamp,
                labels=metric.labels
            )
        
        return None


class ReportGenerator:
    """報告生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.report_templates = {}
        
    async def initialize(self):
        """初始化報告生成器"""
        self.logger.info("📄 初始化報告生成器")
        
        # 設置報告模板
        self.report_templates = {
            "system_health": self._generate_system_health_report,
            "performance": self._generate_performance_report,
            "security": self._generate_security_report,
            "business": self._generate_business_report,
            "weekly_summary": self._generate_weekly_summary_report
        }
        
        self.logger.info("✅ 報告生成器初始化完成")
    
    async def generate_report(self, report_type: str, scope: MonitoringScope, 
                            period_hours: int = 24, metrics: List[MetricPoint] = None,
                            alerts: List[Alert] = None) -> MonitoringReport:
        """生成監控報告"""
        
        if report_type not in self.report_templates:
            raise ValueError(f"不支持的報告類型: {report_type}")
        
        period_end = datetime.now()
        period_start = period_end - timedelta(hours=period_hours)
        
        # 過濾指定時間範圍內的數據
        if metrics:
            filtered_metrics = [
                m for m in metrics 
                if period_start <= datetime.fromisoformat(m.timestamp) <= period_end
            ]
        else:
            filtered_metrics = []
        
        if alerts:
            filtered_alerts = [
                a for a in alerts
                if period_start <= datetime.fromisoformat(a.triggered_at) <= period_end
            ]
        else:
            filtered_alerts = []
        
        # 調用對應的報告生成器
        generator = self.report_templates[report_type]
        return await generator(scope, period_start, period_end, filtered_metrics, filtered_alerts)
    
    async def _generate_system_health_report(self, scope: MonitoringScope, 
                                           period_start: datetime, period_end: datetime,
                                           metrics: List[MetricPoint], alerts: List[Alert]) -> MonitoringReport:
        """生成系統健康報告"""
        
        # 計算關鍵指標
        cpu_metrics = [m for m in metrics if m.name == "system.cpu.usage_percent"]
        memory_metrics = [m for m in metrics if m.name == "system.memory.usage_percent"]
        disk_metrics = [m for m in metrics if m.name == "system.disk.usage_percent"]
        
        summary = {
            "avg_cpu_usage": statistics.mean([m.value for m in cpu_metrics]) if cpu_metrics else 0,
            "max_cpu_usage": max([m.value for m in cpu_metrics]) if cpu_metrics else 0,
            "avg_memory_usage": statistics.mean([m.value for m in memory_metrics]) if memory_metrics else 0,
            "max_memory_usage": max([m.value for m in memory_metrics]) if memory_metrics else 0,
            "avg_disk_usage": statistics.mean([m.value for m in disk_metrics]) if disk_metrics else 0,
            "total_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        }
        
        # 生成洞察
        insights = []
        if summary["avg_cpu_usage"] > 70:
            insights.append("CPU使用率較高，建議檢查資源密集型進程")
        if summary["avg_memory_usage"] > 80:
            insights.append("內存使用率較高，可能需要增加內存容量")
        if summary["critical_alerts"] > 0:
            insights.append(f"發現{summary['critical_alerts']}個嚴重告警，需要立即處理")
        
        # 生成建議
        recommendations = []
        if summary["max_cpu_usage"] > 90:
            recommendations.append("建議優化高CPU使用率的應用程序")
        if summary["max_memory_usage"] > 90:
            recommendations.append("建議監控內存洩漏並優化內存使用")
        if len(alerts) > 10:
            recommendations.append("建議調整告警閾值以減少噪音")
        
        return MonitoringReport(
            id=str(uuid.uuid4()),
            report_type="system_health",
            scope=scope,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            summary=summary,
            metrics=metrics,
            alerts=alerts,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
    
    async def _generate_performance_report(self, scope: MonitoringScope,
                                         period_start: datetime, period_end: datetime,
                                         metrics: List[MetricPoint], alerts: List[Alert]) -> MonitoringReport:
        """生成性能報告"""
        
        # 計算性能指標
        response_time_metrics = [m for m in metrics if m.name == "app.api.response_time_ms"]
        rps_metrics = [m for m in metrics if m.name == "app.api.requests_per_second"]
        error_metrics = [m for m in metrics if m.name == "app.errors.count"]
        
        summary = {
            "avg_response_time": statistics.mean([m.value for m in response_time_metrics]) if response_time_metrics else 0,
            "p95_response_time": statistics.quantiles([m.value for m in response_time_metrics], n=20)[18] if len(response_time_metrics) > 10 else 0,
            "avg_rps": statistics.mean([m.value for m in rps_metrics]) if rps_metrics else 0,
            "total_errors": sum([m.value for m in error_metrics]),
            "error_rate": (sum([m.value for m in error_metrics]) / len(response_time_metrics) * 100) if response_time_metrics else 0
        }
        
        insights = []
        if summary["avg_response_time"] > 300:
            insights.append("API響應時間較慢，建議性能優化")
        if summary["error_rate"] > 1:
            insights.append("錯誤率較高，需要檢查應用程序健康狀況")
        
        recommendations = []
        if summary["p95_response_time"] > 500:
            recommendations.append("建議優化慢查詢和數據庫性能")
        if summary["error_rate"] > 5:
            recommendations.append("建議加強錯誤處理和監控")
        
        return MonitoringReport(
            id=str(uuid.uuid4()),
            report_type="performance",
            scope=scope,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            summary=summary,
            metrics=metrics,
            alerts=alerts,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
    
    async def _generate_security_report(self, scope: MonitoringScope,
                                      period_start: datetime, period_end: datetime,
                                      metrics: List[MetricPoint], alerts: List[Alert]) -> MonitoringReport:
        """生成安全報告"""
        
        # 計算安全指標
        failed_login_metrics = [m for m in metrics if m.name == "security.failed_login_attempts"]
        vulnerability_metrics = [m for m in metrics if m.name == "security.vulnerabilities_detected"]
        security_alerts = [a for a in alerts if a.scope == MonitoringScope.SECURITY]
        
        summary = {
            "total_failed_logins": sum([m.value for m in failed_login_metrics]),
            "total_vulnerabilities": sum([m.value for m in vulnerability_metrics]),
            "security_alerts": len(security_alerts),
            "high_severity_security_alerts": len([a for a in security_alerts if a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]])
        }
        
        insights = []
        if summary["total_failed_logins"] > 50:
            insights.append("檢測到大量登錄失敗，可能存在暴力破解攻擊")
        if summary["total_vulnerabilities"] > 0:
            insights.append("發現安全漏洞，建議立即修復")
        
        recommendations = []
        if summary["total_failed_logins"] > 20:
            recommendations.append("建議啟用帳戶鎖定機制")
        if summary["total_vulnerabilities"] > 5:
            recommendations.append("建議增加安全掃描頻率")
        
        return MonitoringReport(
            id=str(uuid.uuid4()),
            report_type="security",
            scope=scope,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            summary=summary,
            metrics=metrics,
            alerts=alerts,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
    
    async def _generate_business_report(self, scope: MonitoringScope,
                                      period_start: datetime, period_end: datetime,
                                      metrics: List[MetricPoint], alerts: List[Alert]) -> MonitoringReport:
        """生成業務報告"""
        
        # 計算業務指標
        code_gen_metrics = [m for m in metrics if m.name == "business.code_lines_generated"]
        test_coverage_metrics = [m for m in metrics if m.name == "business.test_coverage_percent"]
        deployment_success_metrics = [m for m in metrics if m.name == "business.deployment_success_rate"]
        
        summary = {
            "total_code_generated": sum([m.value for m in code_gen_metrics]),
            "avg_test_coverage": statistics.mean([m.value for m in test_coverage_metrics]) if test_coverage_metrics else 0,
            "avg_deployment_success_rate": statistics.mean([m.value for m in deployment_success_metrics]) if deployment_success_metrics else 0,
            "productivity_trend": "上升" if len(code_gen_metrics) > 0 and code_gen_metrics[-1].value > statistics.mean([m.value for m in code_gen_metrics]) else "穩定"
        }
        
        insights = []
        if summary["avg_test_coverage"] < 70:
            insights.append("測試覆蓋率偏低，建議增加測試用例")
        if summary["avg_deployment_success_rate"] < 90:
            insights.append("部署成功率較低，需要優化部署流程")
        
        recommendations = []
        if summary["total_code_generated"] > 0:
            recommendations.append("代碼生成量良好，建議保持當前開發節奏")
        if summary["avg_test_coverage"] > 80:
            recommendations.append("測試覆蓋率良好，建議關注測試質量")
        
        return MonitoringReport(
            id=str(uuid.uuid4()),
            report_type="business",
            scope=scope,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            summary=summary,
            metrics=metrics,
            alerts=alerts,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
    
    async def _generate_weekly_summary_report(self, scope: MonitoringScope,
                                            period_start: datetime, period_end: datetime,
                                            metrics: List[MetricPoint], alerts: List[Alert]) -> MonitoringReport:
        """生成週總結報告"""
        
        # 綜合所有指標生成週總結
        summary = {
            "total_metrics_collected": len(metrics),
            "total_alerts_triggered": len(alerts),
            "system_health_score": self._calculate_health_score(metrics, alerts),
            "top_issues": self._identify_top_issues(alerts),
            "improvement_areas": self._identify_improvement_areas(metrics)
        }
        
        insights = [
            f"本週收集了{len(metrics)}個監控指標",
            f"觸發了{len(alerts)}個告警",
            f"系統健康分數為{summary['system_health_score']:.1f}/100"
        ]
        
        recommendations = [
            "建議定期檢查系統健康報告",
            "持續關注性能指標趨勢",
            "及時處理高優先級告警"
        ]
        
        return MonitoringReport(
            id=str(uuid.uuid4()),
            report_type="weekly_summary",
            scope=scope,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            summary=summary,
            metrics=metrics,
            alerts=alerts,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
    
    def _calculate_health_score(self, metrics: List[MetricPoint], alerts: List[Alert]) -> float:
        """計算健康分數"""
        base_score = 100.0
        
        # 根據告警數量扣分
        critical_alerts = len([a for a in alerts if a.severity == AlertSeverity.CRITICAL])
        high_alerts = len([a for a in alerts if a.severity == AlertSeverity.HIGH])
        
        base_score -= critical_alerts * 10
        base_score -= high_alerts * 5
        
        return max(0.0, base_score)
    
    def _identify_top_issues(self, alerts: List[Alert]) -> List[str]:
        """識別主要問題"""
        issue_counts = defaultdict(int)
        for alert in alerts:
            issue_counts[alert.metric_name] += 1
        
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return [f"{metric}: {count}次" for metric, count in top_issues]
    
    def _identify_improvement_areas(self, metrics: List[MetricPoint]) -> List[str]:
        """識別改進領域"""
        areas = []
        
        # 分析各類指標的表現
        cpu_metrics = [m for m in metrics if m.name == "system.cpu.usage_percent"]
        if cpu_metrics and statistics.mean([m.value for m in cpu_metrics]) > 70:
            areas.append("CPU性能優化")
        
        memory_metrics = [m for m in metrics if m.name == "system.memory.usage_percent"]
        if memory_metrics and statistics.mean([m.value for m in memory_metrics]) > 80:
            areas.append("內存管理優化")
        
        response_time_metrics = [m for m in metrics if m.name == "app.api.response_time_ms"]
        if response_time_metrics and statistics.mean([m.value for m in response_time_metrics]) > 300:
            areas.append("API響應時間優化")
        
        return areas


class IntelligentMonitoringSystem:
    """智能監控系統主管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics_collector = MetricsCollector()
        self.anomaly_detector = AnomalyDetector()
        self.report_generator = ReportGenerator()
        self.active_alerts = {}
        self.dashboard_widgets = []
        self.notification_handlers = []
        
    async def initialize(self):
        """初始化智能監控系統"""
        self.logger.info("📊 初始化Intelligent Monitoring System - 企業級監控平台")
        
        # 初始化各個組件
        await self.metrics_collector.initialize()
        await self.anomaly_detector.initialize()
        await self.report_generator.initialize()
        
        # 設置默認儀表板
        await self._setup_default_dashboard()
        
        self.logger.info("✅ Intelligent Monitoring System初始化完成")
    
    async def start_monitoring(self):
        """開始監控"""
        self.logger.info("🔄 開始智能監控")
        
        # 開始指標收集
        await self.metrics_collector.start_collection()
        
        # 開始異常檢測循環
        asyncio.create_task(self._anomaly_detection_loop())
        
        self.logger.info("✅ 智能監控已啟動")
    
    def stop_monitoring(self):
        """停止監控"""
        self.logger.info("⏹️ 停止智能監控")
        self.metrics_collector.stop_collection()
    
    async def _anomaly_detection_loop(self):
        """異常檢測循環"""
        while True:
            try:
                # 獲取最近的指標
                recent_metrics = self.metrics_collector.get_recent_metrics(duration_minutes=5)
                
                if recent_metrics:
                    # 檢測異常
                    new_alerts = self.anomaly_detector.detect_anomalies(recent_metrics)
                    
                    # 處理新告警
                    for alert in new_alerts:
                        await self._handle_new_alert(alert)
                
                # 等待下一次檢測
                await asyncio.sleep(60)  # 每分鐘檢測一次
                
            except Exception as e:
                self.logger.error(f"異常檢測循環錯誤: {e}")
                await asyncio.sleep(30)
    
    async def _handle_new_alert(self, alert: Alert):
        """處理新告警"""
        if alert.id not in self.active_alerts:
            self.active_alerts[alert.id] = alert
            self.logger.warning(f"新告警: {alert.name} - {alert.description}")
            
            # 發送通知
            await self._send_alert_notification(alert)
    
    async def _send_alert_notification(self, alert: Alert):
        """發送告警通知"""
        # 簡化的通知實現
        self.logger.info(f"發送告警通知: {alert.name} ({alert.severity.value})")
    
    async def generate_monitoring_report(self, report_type: str, scope: MonitoringScope = MonitoringScope.SYSTEM,
                                       period_hours: int = 24) -> MonitoringReport:
        """生成監控報告"""
        # 獲取指標和告警數據
        metrics = self.metrics_collector.get_recent_metrics(duration_minutes=period_hours * 60)
        alerts = list(self.active_alerts.values())
        
        # 生成報告
        report = await self.report_generator.generate_report(
            report_type, scope, period_hours, metrics, alerts
        )
        
        # 保存報告
        await self._save_report(report)
        
        return report
    
    async def _save_report(self, report: MonitoringReport):
        """保存報告"""
        reports_dir = Path("monitoring_reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"{report.report_type}_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"監控報告已保存: {report_file}")
    
    async def _setup_default_dashboard(self):
        """設置默認儀表板"""
        self.dashboard_widgets = [
            DashboardWidget(
                id="system_overview",
                title="系統概覽",
                widget_type="chart",
                metric_names=["system.cpu.usage_percent", "system.memory.usage_percent"],
                config={"chart_type": "line", "time_range": "1h"},
                position={"row": 0, "col": 0, "width": 6, "height": 4}
            ),
            DashboardWidget(
                id="api_performance",
                title="API性能",
                widget_type="chart",
                metric_names=["app.api.response_time_ms", "app.api.requests_per_second"],
                config={"chart_type": "line", "time_range": "1h"},
                position={"row": 0, "col": 6, "width": 6, "height": 4}
            ),
            DashboardWidget(
                id="active_alerts",
                title="活躍告警",
                widget_type="alert_list",
                metric_names=[],
                config={"max_alerts": 10},
                position={"row": 4, "col": 0, "width": 12, "height": 4}
            ),
            DashboardWidget(
                id="business_metrics",
                title="業務指標",
                widget_type="gauge",
                metric_names=["business.test_coverage_percent", "business.deployment_success_rate"],
                config={"gauge_type": "radial"},
                position={"row": 8, "col": 0, "width": 6, "height": 4}
            )
        ]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """獲取儀表板數據"""
        dashboard_data = {
            "widgets": [],
            "last_updated": datetime.now().isoformat()
        }
        
        for widget in self.dashboard_widgets:
            widget_data = {
                "id": widget.id,
                "title": widget.title,
                "type": widget.widget_type,
                "position": widget.position,
                "data": self._get_widget_data(widget)
            }
            dashboard_data["widgets"].append(widget_data)
        
        return dashboard_data
    
    def _get_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """獲取組件數據"""
        if widget.widget_type == "chart":
            # 獲取圖表數據
            chart_data = []
            for metric_name in widget.metric_names:
                metrics = self.metrics_collector.get_recent_metrics(metric_name, duration_minutes=60)
                chart_data.append({
                    "name": metric_name,
                    "data": [(m.timestamp, m.value) for m in metrics[-20:]]  # 最近20個點
                })
            return {"series": chart_data}
        
        elif widget.widget_type == "gauge":
            # 獲取儀表盤數據
            gauge_data = []
            for metric_name in widget.metric_names:
                metrics = self.metrics_collector.get_recent_metrics(metric_name, duration_minutes=5)
                current_value = metrics[-1].value if metrics else 0
                gauge_data.append({
                    "name": metric_name,
                    "value": current_value
                })
            return {"gauges": gauge_data}
        
        elif widget.widget_type == "alert_list":
            # 獲取告警列表數據
            alerts = list(self.active_alerts.values())
            alerts.sort(key=lambda x: x.triggered_at, reverse=True)
            max_alerts = widget.config.get("max_alerts", 10)
            return {
                "alerts": [asdict(alert) for alert in alerts[:max_alerts]]
            }
        
        return {}
    
    def get_system_metrics_summary(self) -> Dict[str, Any]:
        """獲取系統指標摘要"""
        recent_metrics = self.metrics_collector.get_recent_metrics(duration_minutes=30)
        
        # 按指標名稱分組
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.name].append(metric.value)
        
        summary = {}
        for metric_name, values in metrics_by_name.items():
            if values:
                summary[metric_name] = {
                    "current": values[-1],
                    "average": statistics.mean(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values)
                }
        
        return summary
    
    def get_status(self) -> Dict[str, Any]:
        """獲取監控系統狀態"""
        return {
            "component": "Intelligent Monitoring System",
            "version": "4.6.1",
            "monitoring_active": self.metrics_collector.is_collecting,
            "total_metrics_collected": len(self.metrics_collector.metrics_buffer),
            "active_alerts": len(self.active_alerts),
            "dashboard_widgets": len(self.dashboard_widgets),
            "supported_scopes": [scope.value for scope in MonitoringScope],
            "supported_report_types": list(self.report_generator.report_templates.keys()),
            "capabilities": [
                "real_time_metrics_collection",
                "intelligent_anomaly_detection",
                "automated_report_generation",
                "customizable_dashboards",
                "multi_scope_monitoring",
                "alert_management"
            ]
        }


# 單例實例
intelligent_monitoring_system = IntelligentMonitoringSystem()