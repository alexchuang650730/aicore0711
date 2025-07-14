"""
PowerAutomation 4.0 MCP安全管理器

负责统一管理系统安全策略、威胁检测、安全事件监控和合规性检查。
"""

import logging
import asyncio
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import re
import ipaddress
from collections import defaultdict, deque


class ThreatLevel(Enum):
    """威胁级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """安全事件类型枚举"""
    LOGIN_FAILURE = "login_failure"
    BRUTE_FORCE = "brute_force"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH = "data_breach"
    MALWARE_DETECTED = "malware_detected"
    POLICY_VIOLATION = "policy_violation"
    ANOMALY_DETECTED = "anomaly_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"


class SecurityAction(Enum):
    """安全动作枚举"""
    BLOCK = "block"
    ALERT = "alert"
    LOG = "log"
    QUARANTINE = "quarantine"
    TERMINATE = "terminate"
    NOTIFY = "notify"
    ESCALATE = "escalate"


@dataclass
class SecurityEvent:
    """安全事件"""
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    resource: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    actions_taken: List[str] = field(default_factory=list)


@dataclass
class SecurityRule:
    """安全规则"""
    rule_id: str
    name: str
    description: str
    event_types: List[SecurityEventType]
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[SecurityAction] = field(default_factory=list)
    threshold: int = 1
    time_window: int = 300  # 5分钟
    is_active: bool = True
    priority: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPolicy:
    """安全策略"""
    policy_id: str
    name: str
    description: str
    rules: List[str] = field(default_factory=list)  # rule_ids
    compliance_standards: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatIntelligence:
    """威胁情报"""
    intel_id: str
    threat_type: str
    indicators: List[str] = field(default_factory=list)  # IP、域名、哈希等
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    description: str = ""
    source: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class ComplianceCheck:
    """合规检查"""
    check_id: str
    name: str
    description: str
    standard: str  # GDPR, SOX, HIPAA等
    check_function: str  # 检查函数名
    severity: ThreatLevel = ThreatLevel.MEDIUM
    is_active: bool = True
    last_check: Optional[datetime] = None
    last_result: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPSecurityManager:
    """
    PowerAutomation 4.0 MCP安全管理器
    
    功能：
    1. 安全策略统一管理
    2. 威胁检测和防护
    3. 安全事件监控和告警
    4. 合规性检查和报告
    5. 威胁情报集成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化安全管理器
        
        Args:
            config: 配置参数
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.is_running = False
        
        # 安全事件存储
        self.security_events: Dict[str, SecurityEvent] = {}
        self.event_queue: deque = deque(maxlen=10000)
        
        # 安全规则存储
        self.security_rules: Dict[str, SecurityRule] = {}
        
        # 安全策略存储
        self.security_policies: Dict[str, SecurityPolicy] = {}
        
        # 威胁情报存储
        self.threat_intelligence: Dict[str, ThreatIntelligence] = {}
        
        # 合规检查存储
        self.compliance_checks: Dict[str, ComplianceCheck] = {}
        
        # 实时监控数据
        self.ip_activity: Dict[str, List[datetime]] = defaultdict(list)
        self.user_activity: Dict[str, List[datetime]] = defaultdict(list)
        self.failed_logins: Dict[str, List[datetime]] = defaultdict(list)
        self.blocked_ips: Set[str] = set()
        self.quarantined_users: Set[str] = set()
        
        # 异常检测
        self.baseline_metrics: Dict[str, Any] = {}
        self.anomaly_threshold = self.config.get("anomaly_threshold", 2.0)  # 标准差倍数
        
        # 配置参数
        self.max_failed_logins = self.config.get("max_failed_logins", 5)
        self.brute_force_window = self.config.get("brute_force_window", 300)  # 5分钟
        self.ip_block_duration = self.config.get("ip_block_duration", 3600)  # 1小时
        self.event_retention_days = self.config.get("event_retention_days", 90)
        
        # 事件回调
        self.event_callbacks: Dict[str, List[callable]] = {
            "security_event": [],
            "threat_detected": [],
            "compliance_violation": [],
            "policy_updated": [],
            "action_taken": []
        }
        
        self.logger.info("MCP安全管理器初始化完成")
    
    async def start(self) -> None:
        """启动安全管理器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动MCP安全管理器...")
            
            # 加载默认安全规则
            await self._load_default_rules()
            
            # 加载默认安全策略
            await self._load_default_policies()
            
            # 加载默认合规检查
            await self._load_default_compliance_checks()
            
            # 初始化威胁情报
            await self._init_threat_intelligence()
            
            # 启动后台任务
            asyncio.create_task(self._background_tasks())
            
            self.is_running = True
            self.logger.info("MCP安全管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"MCP安全管理器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止安全管理器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止MCP安全管理器...")
            
            self.is_running = False
            
            # 保存安全事件
            await self._save_security_events()
            
            # 保存安全规则
            await self._save_security_rules()
            
            # 保存安全策略
            await self._save_security_policies()
            
            self.logger.info("MCP安全管理器已停止")
            
        except Exception as e:
            self.logger.error(f"MCP安全管理器停止时出错: {e}")
    
    async def report_security_event(self, event_type: SecurityEventType,
                                   threat_level: ThreatLevel,
                                   source_ip: Optional[str] = None,
                                   user_id: Optional[str] = None,
                                   resource: Optional[str] = None,
                                   description: str = "",
                                   details: Optional[Dict[str, Any]] = None) -> str:
        """
        报告安全事件
        
        Args:
            event_type: 事件类型
            threat_level: 威胁级别
            source_ip: 源IP地址
            user_id: 用户ID
            resource: 相关资源
            description: 事件描述
            details: 事件详情
            
        Returns:
            str: 事件ID
        """
        try:
            # 生成事件ID
            event_id = self._generate_event_id()
            
            # 创建安全事件
            event = SecurityEvent(
                event_id=event_id,
                event_type=event_type,
                threat_level=threat_level,
                source_ip=source_ip,
                user_id=user_id,
                resource=resource,
                description=description,
                details=details or {}
            )
            
            # 存储事件
            self.security_events[event_id] = event
            self.event_queue.append(event)
            
            # 更新活动统计
            await self._update_activity_stats(event)
            
            # 检查安全规则
            await self._check_security_rules(event)
            
            # 威胁检测
            await self._detect_threats(event)
            
            # 触发事件回调
            await self._trigger_event("security_event", event)
            
            self.logger.info(f"安全事件已报告: {event_id} - {event_type.value}")
            return event_id
            
        except Exception as e:
            self.logger.error(f"报告安全事件失败: {e}")
            return ""
    
    async def check_ip_blocked(self, ip_address: str) -> bool:
        """
        检查IP是否被阻止
        
        Args:
            ip_address: IP地址
            
        Returns:
            bool: 是否被阻止
        """
        try:
            # 检查是否在阻止列表中
            if ip_address in self.blocked_ips:
                return True
            
            # 检查威胁情报
            for intel in self.threat_intelligence.values():
                if intel.is_active and ip_address in intel.indicators:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查IP阻止状态失败: {e}")
            return False
    
    async def check_user_quarantined(self, user_id: str) -> bool:
        """
        检查用户是否被隔离
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否被隔离
        """
        return user_id in self.quarantined_users
    
    async def block_ip(self, ip_address: str, duration: Optional[int] = None,
                      reason: str = "") -> bool:
        """
        阻止IP地址
        
        Args:
            ip_address: IP地址
            duration: 阻止持续时间（秒）
            reason: 阻止原因
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.blocked_ips.add(ip_address)
            
            # 记录安全事件
            await self.report_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                threat_level=ThreatLevel.HIGH,
                source_ip=ip_address,
                description=f"IP地址已被阻止: {reason}",
                details={"action": "block_ip", "duration": duration, "reason": reason}
            )
            
            # 如果指定了持续时间，设置自动解除阻止
            if duration:
                asyncio.create_task(self._auto_unblock_ip(ip_address, duration))
            
            self.logger.warning(f"IP地址已被阻止: {ip_address} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"阻止IP地址失败: {e}")
            return False
    
    async def unblock_ip(self, ip_address: str) -> bool:
        """
        解除IP地址阻止
        
        Args:
            ip_address: IP地址
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.blocked_ips.discard(ip_address)
            
            self.logger.info(f"IP地址阻止已解除: {ip_address}")
            return True
            
        except Exception as e:
            self.logger.error(f"解除IP地址阻止失败: {e}")
            return False
    
    async def quarantine_user(self, user_id: str, reason: str = "") -> bool:
        """
        隔离用户
        
        Args:
            user_id: 用户ID
            reason: 隔离原因
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.quarantined_users.add(user_id)
            
            # 记录安全事件
            await self.report_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                threat_level=ThreatLevel.HIGH,
                user_id=user_id,
                description=f"用户已被隔离: {reason}",
                details={"action": "quarantine_user", "reason": reason}
            )
            
            self.logger.warning(f"用户已被隔离: {user_id} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"隔离用户失败: {e}")
            return False
    
    async def release_user(self, user_id: str) -> bool:
        """
        释放隔离用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.quarantined_users.discard(user_id)
            
            self.logger.info(f"用户隔离已解除: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"释放隔离用户失败: {e}")
            return False
    
    async def add_security_rule(self, rule: SecurityRule) -> bool:
        """
        添加安全规则
        
        Args:
            rule: 安全规则
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.security_rules[rule.rule_id] = rule
            
            self.logger.info(f"安全规则添加成功: {rule.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加安全规则失败: {e}")
            return False
    
    async def add_security_policy(self, policy: SecurityPolicy) -> bool:
        """
        添加安全策略
        
        Args:
            policy: 安全策略
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.security_policies[policy.policy_id] = policy
            
            # 触发事件
            await self._trigger_event("policy_updated", policy)
            
            self.logger.info(f"安全策略添加成功: {policy.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加安全策略失败: {e}")
            return False
    
    async def add_threat_intelligence(self, intel: ThreatIntelligence) -> bool:
        """
        添加威胁情报
        
        Args:
            intel: 威胁情报
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.threat_intelligence[intel.intel_id] = intel
            
            # 触发事件
            await self._trigger_event("threat_detected", intel)
            
            self.logger.info(f"威胁情报添加成功: {intel.threat_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加威胁情报失败: {e}")
            return False
    
    async def run_compliance_check(self, check_id: str) -> bool:
        """
        运行合规检查
        
        Args:
            check_id: 检查ID
            
        Returns:
            bool: 检查结果
        """
        try:
            if check_id not in self.compliance_checks:
                self.logger.error(f"合规检查不存在: {check_id}")
                return False
            
            check = self.compliance_checks[check_id]
            
            # 执行检查函数
            result = await self._execute_compliance_check(check)
            
            # 更新检查结果
            check.last_check = datetime.now()
            check.last_result = result
            
            # 如果检查失败，报告合规违规事件
            if not result:
                await self.report_security_event(
                    event_type=SecurityEventType.COMPLIANCE_VIOLATION,
                    threat_level=check.severity,
                    description=f"合规检查失败: {check.name}",
                    details={"check_id": check_id, "standard": check.standard}
                )
                
                # 触发事件
                await self._trigger_event("compliance_violation", {
                    "check_id": check_id,
                    "check_name": check.name,
                    "standard": check.standard,
                    "result": result
                })
            
            self.logger.info(f"合规检查完成: {check.name} - {'通过' if result else '失败'}")
            return result
            
        except Exception as e:
            self.logger.error(f"运行合规检查失败: {e}")
            return False
    
    async def get_security_events(self, limit: int = 100,
                                 event_type: Optional[SecurityEventType] = None,
                                 threat_level: Optional[ThreatLevel] = None,
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None) -> List[SecurityEvent]:
        """
        获取安全事件
        
        Args:
            limit: 返回数量限制
            event_type: 事件类型过滤
            threat_level: 威胁级别过滤
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[SecurityEvent]: 安全事件列表
        """
        try:
            events = []
            
            for event in reversed(list(self.event_queue)):
                # 应用过滤条件
                if event_type and event.event_type != event_type:
                    continue
                
                if threat_level and event.threat_level != threat_level:
                    continue
                
                if start_time and event.timestamp < start_time:
                    continue
                
                if end_time and event.timestamp > end_time:
                    continue
                
                events.append(event)
                
                if len(events) >= limit:
                    break
            
            return events
            
        except Exception as e:
            self.logger.error(f"获取安全事件失败: {e}")
            return []
    
    async def get_security_statistics(self) -> Dict[str, Any]:
        """
        获取安全统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            now = datetime.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # 统计最近24小时的事件
            events_24h = [e for e in self.event_queue if e.timestamp >= last_24h]
            events_7d = [e for e in self.event_queue if e.timestamp >= last_7d]
            
            # 按类型统计
            event_types_24h = defaultdict(int)
            threat_levels_24h = defaultdict(int)
            
            for event in events_24h:
                event_types_24h[event.event_type.value] += 1
                threat_levels_24h[event.threat_level.value] += 1
            
            statistics = {
                "total_events": len(self.security_events),
                "events_24h": len(events_24h),
                "events_7d": len(events_7d),
                "event_types_24h": dict(event_types_24h),
                "threat_levels_24h": dict(threat_levels_24h),
                "blocked_ips": len(self.blocked_ips),
                "quarantined_users": len(self.quarantined_users),
                "active_rules": len([r for r in self.security_rules.values() if r.is_active]),
                "active_policies": len([p for p in self.security_policies.values() if p.is_active]),
                "threat_intelligence": len([t for t in self.threat_intelligence.values() if t.is_active]),
                "compliance_checks": len(self.compliance_checks),
                "last_updated": now.isoformat()
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"获取安全统计信息失败: {e}")
            return {}
    
    def add_event_callback(self, event_type: str, callback: callable) -> None:
        """
        添加事件回调
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            self.logger.info(f"添加事件回调: {event_type}")
    
    async def _update_activity_stats(self, event: SecurityEvent) -> None:
        """更新活动统计"""
        try:
            current_time = datetime.now()
            
            # 更新IP活动统计
            if event.source_ip:
                self.ip_activity[event.source_ip].append(current_time)
                # 保留最近1小时的记录
                cutoff_time = current_time - timedelta(hours=1)
                self.ip_activity[event.source_ip] = [
                    t for t in self.ip_activity[event.source_ip] if t >= cutoff_time
                ]
            
            # 更新用户活动统计
            if event.user_id:
                self.user_activity[event.user_id].append(current_time)
                # 保留最近1小时的记录
                cutoff_time = current_time - timedelta(hours=1)
                self.user_activity[event.user_id] = [
                    t for t in self.user_activity[event.user_id] if t >= cutoff_time
                ]
            
            # 更新登录失败统计
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                key = event.source_ip or event.user_id or "unknown"
                self.failed_logins[key].append(current_time)
                # 保留最近的记录
                cutoff_time = current_time - timedelta(seconds=self.brute_force_window)
                self.failed_logins[key] = [
                    t for t in self.failed_logins[key] if t >= cutoff_time
                ]
                
        except Exception as e:
            self.logger.error(f"更新活动统计失败: {e}")
    
    async def _check_security_rules(self, event: SecurityEvent) -> None:
        """检查安全规则"""
        try:
            for rule in self.security_rules.values():
                if not rule.is_active:
                    continue
                
                # 检查事件类型匹配
                if event.event_type not in rule.event_types:
                    continue
                
                # 检查条件匹配
                if not await self._match_rule_conditions(rule, event):
                    continue
                
                # 检查阈值
                if await self._check_rule_threshold(rule, event):
                    # 执行安全动作
                    await self._execute_security_actions(rule, event)
                    
        except Exception as e:
            self.logger.error(f"检查安全规则失败: {e}")
    
    async def _match_rule_conditions(self, rule: SecurityRule, event: SecurityEvent) -> bool:
        """匹配规则条件"""
        try:
            conditions = rule.conditions
            
            # 检查威胁级别
            if "threat_level" in conditions:
                required_levels = conditions["threat_level"]
                if isinstance(required_levels, list):
                    if event.threat_level.value not in required_levels:
                        return False
                elif event.threat_level.value != required_levels:
                    return False
            
            # 检查源IP
            if "source_ip" in conditions and event.source_ip:
                ip_patterns = conditions["source_ip"]
                if not self._match_ip_patterns(event.source_ip, ip_patterns):
                    return False
            
            # 检查用户ID
            if "user_id" in conditions and event.user_id:
                user_patterns = conditions["user_id"]
                if not self._match_patterns(event.user_id, user_patterns):
                    return False
            
            # 检查资源
            if "resource" in conditions and event.resource:
                resource_patterns = conditions["resource"]
                if not self._match_patterns(event.resource, resource_patterns):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"匹配规则条件失败: {e}")
            return False
    
    async def _check_rule_threshold(self, rule: SecurityRule, event: SecurityEvent) -> bool:
        """检查规则阈值"""
        try:
            if rule.threshold <= 1:
                return True
            
            # 统计时间窗口内的相同事件数量
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(seconds=rule.time_window)
            
            count = 0
            for e in reversed(list(self.event_queue)):
                if e.timestamp < cutoff_time:
                    break
                
                if (e.event_type == event.event_type and
                    e.source_ip == event.source_ip and
                    e.user_id == event.user_id):
                    count += 1
            
            return count >= rule.threshold
            
        except Exception as e:
            self.logger.error(f"检查规则阈值失败: {e}")
            return False
    
    async def _execute_security_actions(self, rule: SecurityRule, event: SecurityEvent) -> None:
        """执行安全动作"""
        try:
            for action in rule.actions:
                if action == SecurityAction.BLOCK and event.source_ip:
                    await self.block_ip(event.source_ip, self.ip_block_duration, f"规则触发: {rule.name}")
                
                elif action == SecurityAction.QUARANTINE and event.user_id:
                    await self.quarantine_user(event.user_id, f"规则触发: {rule.name}")
                
                elif action == SecurityAction.ALERT:
                    await self._send_security_alert(rule, event)
                
                elif action == SecurityAction.LOG:
                    self.logger.warning(f"安全规则触发: {rule.name} - 事件: {event.event_id}")
                
                elif action == SecurityAction.ESCALATE:
                    await self._escalate_security_incident(rule, event)
                
                # 记录执行的动作
                event.actions_taken.append(f"{action.value}:{rule.rule_id}")
            
            # 触发事件
            await self._trigger_event("action_taken", {
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "event_id": event.event_id,
                "actions": [a.value for a in rule.actions]
            })
            
        except Exception as e:
            self.logger.error(f"执行安全动作失败: {e}")
    
    async def _detect_threats(self, event: SecurityEvent) -> None:
        """威胁检测"""
        try:
            # 检测暴力破解攻击
            if event.event_type == SecurityEventType.LOGIN_FAILURE:
                await self._detect_brute_force(event)
            
            # 检测异常活动
            await self._detect_anomalies(event)
            
            # 检测威胁情报匹配
            await self._check_threat_intelligence(event)
            
        except Exception as e:
            self.logger.error(f"威胁检测失败: {e}")
    
    async def _detect_brute_force(self, event: SecurityEvent) -> None:
        """检测暴力破解攻击"""
        try:
            key = event.source_ip or event.user_id or "unknown"
            failed_attempts = len(self.failed_logins.get(key, []))
            
            if failed_attempts >= self.max_failed_logins:
                # 报告暴力破解事件
                await self.report_security_event(
                    event_type=SecurityEventType.BRUTE_FORCE,
                    threat_level=ThreatLevel.HIGH,
                    source_ip=event.source_ip,
                    user_id=event.user_id,
                    description=f"检测到暴力破解攻击: {failed_attempts} 次失败尝试",
                    details={"failed_attempts": failed_attempts, "time_window": self.brute_force_window}
                )
                
        except Exception as e:
            self.logger.error(f"检测暴力破解攻击失败: {e}")
    
    async def _detect_anomalies(self, event: SecurityEvent) -> None:
        """检测异常活动"""
        try:
            # 检测IP活动异常
            if event.source_ip:
                ip_activity_count = len(self.ip_activity.get(event.source_ip, []))
                if ip_activity_count > 100:  # 1小时内超过100次活动
                    await self.report_security_event(
                        event_type=SecurityEventType.ANOMALY_DETECTED,
                        threat_level=ThreatLevel.MEDIUM,
                        source_ip=event.source_ip,
                        description=f"检测到IP活动异常: {ip_activity_count} 次/小时",
                        details={"activity_count": ip_activity_count}
                    )
            
            # 检测用户活动异常
            if event.user_id:
                user_activity_count = len(self.user_activity.get(event.user_id, []))
                if user_activity_count > 200:  # 1小时内超过200次活动
                    await self.report_security_event(
                        event_type=SecurityEventType.ANOMALY_DETECTED,
                        threat_level=ThreatLevel.MEDIUM,
                        user_id=event.user_id,
                        description=f"检测到用户活动异常: {user_activity_count} 次/小时",
                        details={"activity_count": user_activity_count}
                    )
                    
        except Exception as e:
            self.logger.error(f"检测异常活动失败: {e}")
    
    async def _check_threat_intelligence(self, event: SecurityEvent) -> None:
        """检查威胁情报匹配"""
        try:
            for intel in self.threat_intelligence.values():
                if not intel.is_active:
                    continue
                
                # 检查IP地址匹配
                if event.source_ip and event.source_ip in intel.indicators:
                    await self.report_security_event(
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        threat_level=intel.threat_level,
                        source_ip=event.source_ip,
                        description=f"威胁情报匹配: {intel.threat_type}",
                        details={"intel_id": intel.intel_id, "source": intel.source}
                    )
                    
        except Exception as e:
            self.logger.error(f"检查威胁情报失败: {e}")
    
    def _match_ip_patterns(self, ip: str, patterns: List[str]) -> bool:
        """匹配IP模式"""
        try:
            for pattern in patterns:
                if pattern == "*":
                    return True
                
                if "/" in pattern:
                    # CIDR格式
                    try:
                        network = ipaddress.ip_network(pattern, strict=False)
                        if ipaddress.ip_address(ip) in network:
                            return True
                    except:
                        continue
                else:
                    # 直接匹配
                    if ip == pattern:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"匹配IP模式失败: {e}")
            return False
    
    def _match_patterns(self, value: str, patterns: List[str]) -> bool:
        """匹配模式"""
        try:
            for pattern in patterns:
                if pattern == "*":
                    return True
                
                # 支持通配符匹配
                import fnmatch
                if fnmatch.fnmatch(value, pattern):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"匹配模式失败: {e}")
            return False
    
    def _generate_event_id(self) -> str:
        """生成事件ID"""
        import uuid
        return f"event_{uuid.uuid4().hex[:16]}"
    
    async def _auto_unblock_ip(self, ip_address: str, duration: int) -> None:
        """自动解除IP阻止"""
        try:
            await asyncio.sleep(duration)
            await self.unblock_ip(ip_address)
        except Exception as e:
            self.logger.error(f"自动解除IP阻止失败: {e}")
    
    async def _send_security_alert(self, rule: SecurityRule, event: SecurityEvent) -> None:
        """发送安全告警"""
        try:
            alert_message = f"安全告警: {rule.name}\n"
            alert_message += f"事件类型: {event.event_type.value}\n"
            alert_message += f"威胁级别: {event.threat_level.value}\n"
            alert_message += f"描述: {event.description}\n"
            alert_message += f"时间: {event.timestamp}\n"
            
            if event.source_ip:
                alert_message += f"源IP: {event.source_ip}\n"
            if event.user_id:
                alert_message += f"用户: {event.user_id}\n"
            if event.resource:
                alert_message += f"资源: {event.resource}\n"
            
            # 这里可以集成邮件、短信、Slack等告警渠道
            self.logger.warning(f"安全告警: {alert_message}")
            
        except Exception as e:
            self.logger.error(f"发送安全告警失败: {e}")
    
    async def _escalate_security_incident(self, rule: SecurityRule, event: SecurityEvent) -> None:
        """升级安全事件"""
        try:
            # 创建高级别安全事件
            await self.report_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                threat_level=ThreatLevel.CRITICAL,
                source_ip=event.source_ip,
                user_id=event.user_id,
                resource=event.resource,
                description=f"安全事件升级: {rule.name} - {event.description}",
                details={
                    "original_event_id": event.event_id,
                    "escalation_rule": rule.rule_id,
                    "escalation_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"升级安全事件失败: {e}")
    
    async def _execute_compliance_check(self, check: ComplianceCheck) -> bool:
        """执行合规检查"""
        try:
            # 这里可以实现具体的合规检查逻辑
            # 例如检查密码策略、数据加密、访问日志等
            
            if check.check_function == "check_password_policy":
                return await self._check_password_policy()
            elif check.check_function == "check_data_encryption":
                return await self._check_data_encryption()
            elif check.check_function == "check_access_logs":
                return await self._check_access_logs()
            else:
                self.logger.warning(f"未知的合规检查函数: {check.check_function}")
                return True
                
        except Exception as e:
            self.logger.error(f"执行合规检查失败: {e}")
            return False
    
    async def _check_password_policy(self) -> bool:
        """检查密码策略合规性"""
        # 示例实现
        return True
    
    async def _check_data_encryption(self) -> bool:
        """检查数据加密合规性"""
        # 示例实现
        return True
    
    async def _check_access_logs(self) -> bool:
        """检查访问日志合规性"""
        # 示例实现
        return True
    
    async def _trigger_event(self, event_type: str, data: Any) -> None:
        """触发事件"""
        try:
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        self.logger.error(f"事件回调执行失败: {e}")
        except Exception as e:
            self.logger.error(f"触发事件失败: {e}")
    
    async def _load_default_rules(self) -> None:
        """加载默认安全规则"""
        try:
            default_rules = [
                # 暴力破解检测规则
                SecurityRule(
                    rule_id="brute_force_detection",
                    name="暴力破解检测",
                    description="检测暴力破解攻击",
                    event_types=[SecurityEventType.LOGIN_FAILURE],
                    threshold=5,
                    time_window=300,
                    actions=[SecurityAction.BLOCK, SecurityAction.ALERT]
                ),
                
                # 权限提升检测规则
                SecurityRule(
                    rule_id="privilege_escalation_detection",
                    name="权限提升检测",
                    description="检测权限提升攻击",
                    event_types=[SecurityEventType.PRIVILEGE_ESCALATION],
                    threshold=1,
                    actions=[SecurityAction.QUARANTINE, SecurityAction.ALERT, SecurityAction.ESCALATE]
                ),
                
                # 未授权访问检测规则
                SecurityRule(
                    rule_id="unauthorized_access_detection",
                    name="未授权访问检测",
                    description="检测未授权访问尝试",
                    event_types=[SecurityEventType.UNAUTHORIZED_ACCESS],
                    threshold=3,
                    time_window=600,
                    actions=[SecurityAction.BLOCK, SecurityAction.ALERT]
                ),
                
                # 数据泄露检测规则
                SecurityRule(
                    rule_id="data_breach_detection",
                    name="数据泄露检测",
                    description="检测数据泄露事件",
                    event_types=[SecurityEventType.DATA_BREACH],
                    threshold=1,
                    actions=[SecurityAction.QUARANTINE, SecurityAction.ALERT, SecurityAction.ESCALATE]
                )
            ]
            
            for rule in default_rules:
                await self.add_security_rule(rule)
            
            self.logger.info(f"加载了 {len(default_rules)} 个默认安全规则")
            
        except Exception as e:
            self.logger.error(f"加载默认安全规则失败: {e}")
    
    async def _load_default_policies(self) -> None:
        """加载默认安全策略"""
        try:
            default_policies = [
                SecurityPolicy(
                    policy_id="basic_security_policy",
                    name="基础安全策略",
                    description="基础安全防护策略",
                    rules=["brute_force_detection", "unauthorized_access_detection"],
                    compliance_standards=["ISO27001", "NIST"]
                ),
                
                SecurityPolicy(
                    policy_id="advanced_threat_protection",
                    name="高级威胁防护",
                    description="高级威胁检测和防护策略",
                    rules=["privilege_escalation_detection", "data_breach_detection"],
                    compliance_standards=["SOX", "GDPR"]
                )
            ]
            
            for policy in default_policies:
                await self.add_security_policy(policy)
            
            self.logger.info(f"加载了 {len(default_policies)} 个默认安全策略")
            
        except Exception as e:
            self.logger.error(f"加载默认安全策略失败: {e}")
    
    async def _load_default_compliance_checks(self) -> None:
        """加载默认合规检查"""
        try:
            default_checks = [
                ComplianceCheck(
                    check_id="password_policy_check",
                    name="密码策略检查",
                    description="检查密码策略合规性",
                    standard="ISO27001",
                    check_function="check_password_policy",
                    severity=ThreatLevel.MEDIUM
                ),
                
                ComplianceCheck(
                    check_id="data_encryption_check",
                    name="数据加密检查",
                    description="检查数据加密合规性",
                    standard="GDPR",
                    check_function="check_data_encryption",
                    severity=ThreatLevel.HIGH
                ),
                
                ComplianceCheck(
                    check_id="access_logs_check",
                    name="访问日志检查",
                    description="检查访问日志合规性",
                    standard="SOX",
                    check_function="check_access_logs",
                    severity=ThreatLevel.MEDIUM
                )
            ]
            
            for check in default_checks:
                self.compliance_checks[check.check_id] = check
            
            self.logger.info(f"加载了 {len(default_checks)} 个默认合规检查")
            
        except Exception as e:
            self.logger.error(f"加载默认合规检查失败: {e}")
    
    async def _init_threat_intelligence(self) -> None:
        """初始化威胁情报"""
        try:
            # 这里可以从外部威胁情报源加载数据
            self.logger.info("威胁情报初始化完成")
        except Exception as e:
            self.logger.error(f"威胁情报初始化失败: {e}")
    
    async def _save_security_events(self) -> None:
        """保存安全事件"""
        try:
            # 这里可以保存安全事件到文件或数据库
            self.logger.debug("安全事件已保存")
        except Exception as e:
            self.logger.error(f"保存安全事件失败: {e}")
    
    async def _save_security_rules(self) -> None:
        """保存安全规则"""
        try:
            # 这里可以保存安全规则到文件或数据库
            self.logger.debug("安全规则已保存")
        except Exception as e:
            self.logger.error(f"保存安全规则失败: {e}")
    
    async def _save_security_policies(self) -> None:
        """保存安全策略"""
        try:
            # 这里可以保存安全策略到文件或数据库
            self.logger.debug("安全策略已保存")
        except Exception as e:
            self.logger.error(f"保存安全策略失败: {e}")
    
    async def _background_tasks(self) -> None:
        """后台任务"""
        while self.is_running:
            try:
                # 清理过期事件
                await self._cleanup_expired_events()
                
                # 运行定期合规检查
                await self._run_periodic_compliance_checks()
                
                # 更新威胁情报
                await self._update_threat_intelligence()
                
                # 等待下次执行
                await asyncio.sleep(300)  # 5分钟
                
            except Exception as e:
                self.logger.error(f"后台任务执行失败: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_events(self) -> None:
        """清理过期事件"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.event_retention_days)
            
            # 清理过期的安全事件
            expired_events = [
                event_id for event_id, event in self.security_events.items()
                if event.timestamp < cutoff_time
            ]
            
            for event_id in expired_events:
                del self.security_events[event_id]
            
            if expired_events:
                self.logger.info(f"清理了 {len(expired_events)} 个过期安全事件")
                
        except Exception as e:
            self.logger.error(f"清理过期事件失败: {e}")
    
    async def _run_periodic_compliance_checks(self) -> None:
        """运行定期合规检查"""
        try:
            for check_id, check in self.compliance_checks.items():
                if not check.is_active:
                    continue
                
                # 检查是否需要运行（例如每天运行一次）
                if (check.last_check is None or 
                    datetime.now() - check.last_check > timedelta(days=1)):
                    await self.run_compliance_check(check_id)
                    
        except Exception as e:
            self.logger.error(f"运行定期合规检查失败: {e}")
    
    async def _update_threat_intelligence(self) -> None:
        """更新威胁情报"""
        try:
            # 清理过期的威胁情报
            current_time = datetime.now()
            expired_intel = [
                intel_id for intel_id, intel in self.threat_intelligence.items()
                if intel.expires_at and current_time > intel.expires_at
            ]
            
            for intel_id in expired_intel:
                self.threat_intelligence[intel_id].is_active = False
            
            if expired_intel:
                self.logger.info(f"标记了 {len(expired_intel)} 个过期威胁情报")
                
        except Exception as e:
            self.logger.error(f"更新威胁情报失败: {e}")

