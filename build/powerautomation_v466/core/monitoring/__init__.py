"""
PowerAutomation v4.6.1 智能監控和報告系統
Intelligent Monitoring and Reporting System Package
"""

from .intelligent_monitoring import (
    intelligent_monitoring_system,
    IntelligentMonitoringSystem,
    MetricsCollector,
    AnomalyDetector,
    ReportGenerator,
    MetricType,
    AlertSeverity,
    MonitoringScope,
    MetricPoint,
    Alert,
    MonitoringReport,
    DashboardWidget
)

__all__ = [
    'intelligent_monitoring_system',
    'IntelligentMonitoringSystem',
    'MetricsCollector',
    'AnomalyDetector', 
    'ReportGenerator',
    'MetricType',
    'AlertSeverity',
    'MonitoringScope',
    'MetricPoint',
    'Alert',
    'MonitoringReport',
    'DashboardWidget'
]

__version__ = "4.6.1"
__component__ = "Intelligent Monitoring and Reporting System"