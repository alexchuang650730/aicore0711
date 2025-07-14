"""
Alert System - 智能告警系统
为ClaudEditor提供实时告警和通知功能

功能：
- 多级别告警管理
- 智能告警规则引擎
- 告警聚合和去重
- 多渠道通知支持
- 告警历史和统计
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """告警类型"""
    RESOURCE_THRESHOLD = "resource_threshold"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SYSTEM_ERROR = "system_error"
    AI_COMPONENT_FAILURE = "ai_component_failure"
    PREDICTION_RISK = "prediction_risk"
    CUSTOM = "custom"

class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    LOG = "log"
    DESKTOP = "desktop"

@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    alert_type: AlertType
    alert_level: AlertLevel
    metric_name: str
    condition: str  # "greater_than", "less_than", "equals", "not_equals"
    threshold: float
    duration: timedelta  # 持续时间
    enabled: bool
    notification_channels: List[NotificationChannel]
    cooldown_period: timedelta  # 冷却期
    tags: List[str]

@dataclass
class Alert:
    """告警"""
    alert_id: str
    rule_id: str
    alert_type: AlertType
    alert_level: AlertLevel
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold: float
    triggered_at: datetime
    resolved_at: Optional[datetime]
    status: str  # "active", "resolved", "suppressed"
    notification_sent: bool
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class NotificationConfig:
    """通知配置"""
    email_config: Optional[Dict[str, str]] = None
    webhook_config: Optional[Dict[str, str]] = None
    desktop_config: Optional[Dict[str, str]] = None

class AlertSystem:
    """智能告警系统"""
    
    def __init__(self, notification_config: Optional[NotificationConfig] = None):
        self.logger = logging.getLogger(__name__)
        
        # 告警规则和状态
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # 告警统计
        self.alert_stats = defaultdict(int)
        self.rule_trigger_count = defaultdict(int)
        
        # 通知配置
        self.notification_config = notification_config or NotificationConfig()
        
        # 告警聚合和去重
        self.alert_aggregation_window = timedelta(minutes=5)
        self.duplicate_alerts: Dict[str, datetime] = {}
        
        # 回调函数
        self.alert_callbacks: List[Callable] = []
        
        # WebSocket连接（用于实时通知）
        self.websocket_clients: Set = set()
        
        # 系统状态
        self.is_running = False
        self.monitoring_task = None
        
        # 默认规则
        self._create_default_rules()
        
        self.logger.info("告警系统初始化完成")
    
    def _create_default_rules(self):
        """创建默认告警规则"""
        default_rules = [
            AlertRule(
                rule_id="cpu_high",
                name="CPU使用率过高",
                description="CPU使用率超过80%",
                alert_type=AlertType.RESOURCE_THRESHOLD,
                alert_level=AlertLevel.WARNING,
                metric_name="cpu_percent",
                condition="greater_than",
                threshold=80.0,
                duration=timedelta(minutes=2),
                enabled=True,
                notification_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.LOG],
                cooldown_period=timedelta(minutes=10),
                tags=["system", "cpu"]
            ),
            AlertRule(
                rule_id="memory_critical",
                name="内存使用率严重",
                description="内存使用率超过90%",
                alert_type=AlertType.RESOURCE_THRESHOLD,
                alert_level=AlertLevel.CRITICAL,
                metric_name="memory_percent",
                condition="greater_than",
                threshold=90.0,
                duration=timedelta(minutes=1),
                enabled=True,
                notification_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL, NotificationChannel.LOG],
                cooldown_period=timedelta(minutes=15),
                tags=["system", "memory"]
            ),
            AlertRule(
                rule_id="disk_warning",
                name="磁盘空间不足",
                description="磁盘使用率超过85%",
                alert_type=AlertType.RESOURCE_THRESHOLD,
                alert_level=AlertLevel.WARNING,
                metric_name="disk_percent",
                condition="greater_than",
                threshold=85.0,
                duration=timedelta(minutes=5),
                enabled=True,
                notification_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.LOG],
                cooldown_period=timedelta(hours=1),
                tags=["system", "disk"]
            ),
            AlertRule(
                rule_id="ai_component_error",
                name="AI组件错误率过高",
                description="AI组件错误率超过5%",
                alert_type=AlertType.AI_COMPONENT_FAILURE,
                alert_level=AlertLevel.ERROR,
                metric_name="error_rate",
                condition="greater_than",
                threshold=5.0,
                duration=timedelta(minutes=3),
                enabled=True,
                notification_channels=[NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL, NotificationChannel.LOG],
                cooldown_period=timedelta(minutes=20),
                tags=["ai", "error"]
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    async def start_monitoring(self) -> bool:
        """启动告警监控"""
        try:
            if self.is_running:
                self.logger.warning("告警系统已在运行中")
                return True
            
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("告警系统启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动告警系统失败: {e}")
            self.is_running = False
            return False
    
    async def stop_monitoring(self):
        """停止告警监控"""
        try:
            self.is_running = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("告警系统已停止")
            
        except Exception as e:
            self.logger.error(f"停止告警系统失败: {e}")
    
    async def _monitoring_loop(self):
        """告警监控循环"""
        while self.is_running:
            try:
                # 检查告警状态
                await self._check_alert_resolution()
                
                # 清理过期的重复告警记录
                await self._cleanup_duplicate_alerts()
                
                await asyncio.sleep(30)  # 30秒检查一次
                
            except Exception as e:
                self.logger.error(f"告警监控循环错误: {e}")
                await asyncio.sleep(30)
    
    async def check_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """
        检查指标并触发告警
        
        Args:
            metrics: 当前指标数据
            
        Returns:
            List[Alert]: 触发的告警列表
        """
        try:
            triggered_alerts = []
            
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                if rule.metric_name not in metrics:
                    continue
                
                current_value = float(metrics[rule.metric_name])
                
                # 检查是否满足告警条件
                if self._evaluate_condition(current_value, rule.condition, rule.threshold):
                    alert = await self._trigger_alert(rule, current_value, metrics)
                    if alert:
                        triggered_alerts.append(alert)
            
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"检查指标告警失败: {e}")
            return []
    
    def _evaluate_condition(self, current_value: float, condition: str, threshold: float) -> bool:
        """评估告警条件"""
        if condition == "greater_than":
            return current_value > threshold
        elif condition == "less_than":
            return current_value < threshold
        elif condition == "equals":
            return abs(current_value - threshold) < 0.001
        elif condition == "not_equals":
            return abs(current_value - threshold) >= 0.001
        else:
            return False
    
    async def _trigger_alert(self, rule: AlertRule, current_value: float, metrics: Dict[str, Any]) -> Optional[Alert]:
        """触发告警"""
        try:
            # 检查冷却期
            if self._is_in_cooldown(rule.rule_id):
                return None
            
            # 检查是否为重复告警
            alert_key = f"{rule.rule_id}_{rule.metric_name}_{current_value:.2f}"
            if self._is_duplicate_alert(alert_key):
                return None
            
            # 创建告警
            alert_id = f"alert_{rule.rule_id}_{int(datetime.now().timestamp())}"
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                alert_type=rule.alert_type,
                alert_level=rule.alert_level,
                title=rule.name,
                message=self._generate_alert_message(rule, current_value),
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold=rule.threshold,
                triggered_at=datetime.now(),
                resolved_at=None,
                status="active",
                notification_sent=False,
                tags=rule.tags.copy(),
                metadata={
                    "rule_description": rule.description,
                    "condition": rule.condition,
                    "duration": rule.duration.total_seconds(),
                    "all_metrics": metrics.copy()
                }
            )
            
            # 存储告警
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # 更新统计
            self.alert_stats[rule.alert_level.value] += 1
            self.rule_trigger_count[rule.rule_id] += 1
            
            # 记录重复告警
            self.duplicate_alerts[alert_key] = datetime.now()
            
            # 发送通知
            await self._send_notifications(alert, rule.notification_channels)
            
            # 触发回调
            await self._trigger_alert_callbacks(alert)
            
            self.logger.info(f"触发告警: {alert.title} (ID: {alert_id})")
            return alert
            
        except Exception as e:
            self.logger.error(f"触发告警失败: {e}")
            return None
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """检查是否在冷却期内"""
        rule = self.alert_rules.get(rule_id)
        if not rule:
            return False
        
        # 查找最近的告警
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.rule_id == rule_id and 
            datetime.now() - alert.triggered_at < rule.cooldown_period
        ]
        
        return len(recent_alerts) > 0
    
    def _is_duplicate_alert(self, alert_key: str) -> bool:
        """检查是否为重复告警"""
        if alert_key in self.duplicate_alerts:
            last_time = self.duplicate_alerts[alert_key]
            if datetime.now() - last_time < self.alert_aggregation_window:
                return True
        return False
    
    def _generate_alert_message(self, rule: AlertRule, current_value: float) -> str:
        """生成告警消息"""
        return (
            f"{rule.description}\n"
            f"当前值: {current_value:.2f}\n"
            f"阈值: {rule.threshold:.2f}\n"
            f"触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    async def _send_notifications(self, alert: Alert, channels: List[NotificationChannel]):
        """发送通知"""
        try:
            for channel in channels:
                if channel == NotificationChannel.WEBSOCKET:
                    await self._send_websocket_notification(alert)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(alert)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook_notification(alert)
                elif channel == NotificationChannel.LOG:
                    self._send_log_notification(alert)
                elif channel == NotificationChannel.DESKTOP:
                    await self._send_desktop_notification(alert)
            
            # 标记通知已发送
            alert.notification_sent = True
            
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")
    
    async def _send_websocket_notification(self, alert: Alert):
        """发送WebSocket通知"""
        try:
            if not self.websocket_clients:
                return
            
            notification = {
                "type": "alert",
                "data": asdict(alert)
            }
            
            message = json.dumps(notification, default=str)
            disconnected_clients = set()
            
            for client in self.websocket_clients:
                try:
                    await client.send(message)
                except Exception:
                    disconnected_clients.add(client)
            
            # 清理断开的连接
            self.websocket_clients -= disconnected_clients
            
        except Exception as e:
            self.logger.error(f"WebSocket通知发送失败: {e}")
    
    async def _send_email_notification(self, alert: Alert):
        """发送邮件通知"""
        try:
            if not self.notification_config.email_config:
                return
            
            config = self.notification_config.email_config
            
            msg = MimeMultipart()
            msg['From'] = config['from_email']
            msg['To'] = config['to_email']
            msg['Subject'] = f"[{alert.alert_level.value.upper()}] {alert.title}"
            
            body = f"""
告警详情：

标题: {alert.title}
级别: {alert.alert_level.value.upper()}
类型: {alert.alert_type.value}
指标: {alert.metric_name}
当前值: {alert.current_value:.2f}
阈值: {alert.threshold:.2f}
触发时间: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}

消息: {alert.message}

标签: {', '.join(alert.tags)}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"邮件通知发送失败: {e}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """发送Webhook通知"""
        try:
            if not self.notification_config.webhook_config:
                return
            
            import aiohttp
            
            config = self.notification_config.webhook_config
            payload = {
                "alert": asdict(alert),
                "timestamp": datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config['url'],
                    json=payload,
                    headers=config.get('headers', {}),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        self.logger.warning(f"Webhook响应状态: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Webhook通知发送失败: {e}")
    
    def _send_log_notification(self, alert: Alert):
        """发送日志通知"""
        try:
            log_level = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.ERROR: logging.ERROR,
                AlertLevel.CRITICAL: logging.CRITICAL
            }.get(alert.alert_level, logging.INFO)
            
            self.logger.log(
                log_level,
                f"告警触发 - {alert.title}: {alert.message} "
                f"(当前值: {alert.current_value:.2f}, 阈值: {alert.threshold:.2f})"
            )
            
        except Exception as e:
            self.logger.error(f"日志通知发送失败: {e}")
    
    async def _send_desktop_notification(self, alert: Alert):
        """发送桌面通知"""
        try:
            # 这里可以集成桌面通知库，如plyer
            # 由于依赖问题，这里只记录日志
            self.logger.info(f"桌面通知: {alert.title}")
            
        except Exception as e:
            self.logger.error(f"桌面通知发送失败: {e}")
    
    async def _trigger_alert_callbacks(self, alert: Alert):
        """触发告警回调"""
        try:
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回调执行失败: {e}")
        except Exception as e:
            self.logger.error(f"触发告警回调失败: {e}")
    
    async def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """
        解决告警
        
        Args:
            alert_id: 告警ID
            resolution_note: 解决说明
            
        Returns:
            bool: 是否成功解决
        """
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now()
            alert.status = "resolved"
            
            if resolution_note:
                alert.metadata["resolution_note"] = resolution_note
            
            # 从活跃告警中移除
            del self.active_alerts[alert_id]
            
            # 发送解决通知
            await self._send_resolution_notification(alert)
            
            self.logger.info(f"告警已解决: {alert.title} (ID: {alert_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")
            return False
    
    async def _send_resolution_notification(self, alert: Alert):
        """发送告警解决通知"""
        try:
            if self.websocket_clients:
                notification = {
                    "type": "alert_resolved",
                    "data": asdict(alert)
                }
                
                message = json.dumps(notification, default=str)
                for client in self.websocket_clients:
                    try:
                        await client.send(message)
                    except Exception:
                        pass
            
        except Exception as e:
            self.logger.error(f"发送解决通知失败: {e}")
    
    async def _check_alert_resolution(self):
        """检查告警是否可以自动解决"""
        try:
            resolved_alerts = []
            
            for alert_id, alert in self.active_alerts.items():
                # 这里可以添加自动解决逻辑
                # 例如：如果指标恢复正常超过一定时间，自动解决告警
                pass
            
            for alert_id in resolved_alerts:
                await self.resolve_alert(alert_id, "自动解决")
            
        except Exception as e:
            self.logger.error(f"检查告警解决失败: {e}")
    
    async def _cleanup_duplicate_alerts(self):
        """清理过期的重复告警记录"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for alert_key, timestamp in self.duplicate_alerts.items():
                if current_time - timestamp > self.alert_aggregation_window * 2:
                    expired_keys.append(alert_key)
            
            for key in expired_keys:
                del self.duplicate_alerts[key]
            
        except Exception as e:
            self.logger.error(f"清理重复告警记录失败: {e}")
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """
        添加告警规则
        
        Args:
            rule: 告警规则
            
        Returns:
            bool: 是否成功添加
        """
        try:
            self.alert_rules[rule.rule_id] = rule
            self.logger.info(f"添加告警规则: {rule.name}")
            return True
        except Exception as e:
            self.logger.error(f"添加告警规则失败: {e}")
            return False
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """
        移除告警规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否成功移除
        """
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                self.logger.info(f"移除告警规则: {rule_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"移除告警规则失败: {e}")
            return False
    
    def register_alert_callback(self, callback: Callable):
        """
        注册告警回调函数
        
        Args:
            callback: 回调函数
        """
        self.alert_callbacks.append(callback)
        self.logger.info("注册告警回调函数")
    
    def add_websocket_client(self, client):
        """添加WebSocket客户端"""
        self.websocket_clients.add(client)
    
    def remove_websocket_client(self, client):
        """移除WebSocket客户端"""
        self.websocket_clients.discard(client)
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        return [asdict(alert) for alert in self.active_alerts.values()]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取告警历史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            asdict(alert) for alert in self.alert_history
            if alert.triggered_at > cutoff_time
        ]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        return {
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([r for r in self.alert_rules.values() if r.enabled]),
            "active_alerts": len(self.active_alerts),
            "alert_stats_by_level": dict(self.alert_stats),
            "rule_trigger_count": dict(self.rule_trigger_count),
            "websocket_clients": len(self.websocket_clients),
            "is_running": self.is_running
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取告警系统状态"""
        return {
            "status": "active" if self.is_running else "inactive",
            "active_alerts_count": len(self.active_alerts),
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([r for r in self.alert_rules.values() if r.enabled]),
            "notification_channels": [
                "websocket" if self.websocket_clients else None,
                "email" if self.notification_config.email_config else None,
                "webhook" if self.notification_config.webhook_config else None,
                "log"
            ],
            "statistics": self.get_alert_statistics()
        }

