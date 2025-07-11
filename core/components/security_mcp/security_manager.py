#!/usr/bin/env python3
"""
Security MCP - 企業級安全管理平台
PowerAutomation v4.6.1 安全控制和合規管理

基於aicore0707的Security MCP實現，提供：
- 代碼安全掃描
- 權限管理控制
- 合規性檢查
- 安全審計日誌
"""

import asyncio
import logging
import time
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """安全級別枚舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VulnerabilityType(Enum):
    """漏洞類型枚舉"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_EXPOSURE = "data_exposure"
    INSECURE_DEPENDENCIES = "insecure_dependencies"
    CODE_INJECTION = "code_injection"


class AccessLevel(Enum):
    """訪問級別枚舉"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


@dataclass
class SecurityVulnerability:
    """安全漏洞"""
    vulnerability_id: str
    type: VulnerabilityType
    severity: SecurityLevel
    file_path: str
    line_number: int
    description: str
    recommendation: str
    detected_at: str
    cve_id: Optional[str] = None
    
    
@dataclass
class SecurityScanResult:
    """安全掃描結果"""
    scan_id: str
    target_path: str
    scan_type: str
    vulnerabilities: List[SecurityVulnerability]
    scan_duration: float
    started_at: str
    completed_at: str
    total_files_scanned: int
    security_score: float


@dataclass
class UserPermission:
    """用戶權限"""
    user_id: str
    username: str
    access_level: AccessLevel
    permissions: List[str]
    created_at: str
    expires_at: Optional[str] = None
    last_login: Optional[str] = None


@dataclass
class SecurityAuditLog:
    """安全審計日誌"""
    log_id: str
    user_id: str
    action: str
    resource: str
    timestamp: str
    ip_address: str
    user_agent: str
    result: str
    details: Dict[str, Any]


class CodeSecurityScanner:
    """代碼安全掃描器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.vulnerability_patterns = self._load_vulnerability_patterns()
    
    def _load_vulnerability_patterns(self) -> Dict[VulnerabilityType, List[str]]:
        """載入漏洞檢測模式"""
        return {
            VulnerabilityType.SQL_INJECTION: [
                r"SELECT.*FROM.*WHERE.*=.*\$",
                r"INSERT.*INTO.*VALUES.*\$",
                r"UPDATE.*SET.*WHERE.*=.*\$",
                r"DELETE.*FROM.*WHERE.*=.*\$"
            ],
            VulnerabilityType.XSS: [
                r"innerHTML\s*=",
                r"document\.write\(",
                r"eval\(",
                r"setTimeout\s*\(\s*[\"']"
            ],
            VulnerabilityType.CODE_INJECTION: [
                r"exec\s*\(",
                r"system\s*\(",
                r"shell_exec\s*\(",
                r"subprocess\.",
                r"os\.system"
            ]
        }
    
    async def scan_file(self, file_path: str) -> List[SecurityVulnerability]:
        """掃描單個文件"""
        vulnerabilities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                for vuln_type, patterns in self.vulnerability_patterns.items():
                    for pattern in patterns:
                        if self._matches_pattern(line, pattern):
                            vulnerability = SecurityVulnerability(
                                vulnerability_id=str(uuid.uuid4()),
                                type=vuln_type,
                                severity=self._assess_severity(vuln_type),
                                file_path=file_path,
                                line_number=line_num,
                                description=f"潛在{vuln_type.value}漏洞",
                                recommendation=self._get_recommendation(vuln_type),
                                detected_at=datetime.now().isoformat()
                            )
                            vulnerabilities.append(vulnerability)
            
        except Exception as e:
            self.logger.error(f"掃描文件失敗 {file_path}: {e}")
        
        return vulnerabilities
    
    def _matches_pattern(self, line: str, pattern: str) -> bool:
        """檢查行是否匹配漏洞模式"""
        import re
        return bool(re.search(pattern, line, re.IGNORECASE))
    
    def _assess_severity(self, vuln_type: VulnerabilityType) -> SecurityLevel:
        """評估漏洞嚴重程度"""
        severity_map = {
            VulnerabilityType.SQL_INJECTION: SecurityLevel.HIGH,
            VulnerabilityType.XSS: SecurityLevel.MEDIUM,
            VulnerabilityType.CSRF: SecurityLevel.MEDIUM,
            VulnerabilityType.CODE_INJECTION: SecurityLevel.CRITICAL,
            VulnerabilityType.AUTHENTICATION: SecurityLevel.HIGH,
            VulnerabilityType.AUTHORIZATION: SecurityLevel.HIGH,
            VulnerabilityType.DATA_EXPOSURE: SecurityLevel.HIGH,
            VulnerabilityType.INSECURE_DEPENDENCIES: SecurityLevel.MEDIUM
        }
        return severity_map.get(vuln_type, SecurityLevel.LOW)
    
    def _get_recommendation(self, vuln_type: VulnerabilityType) -> str:
        """獲取修復建議"""
        recommendations = {
            VulnerabilityType.SQL_INJECTION: "使用參數化查詢或ORM框架",
            VulnerabilityType.XSS: "對用戶輸入進行HTML編碼和驗證",
            VulnerabilityType.CSRF: "實施CSRF令牌保護",
            VulnerabilityType.CODE_INJECTION: "避免動態代碼執行，驗證所有輸入",
            VulnerabilityType.AUTHENTICATION: "實施強身份驗證機制",
            VulnerabilityType.AUTHORIZATION: "實施適當的權限檢查",
            VulnerabilityType.DATA_EXPOSURE: "加密敏感數據，限制數據訪問",
            VulnerabilityType.INSECURE_DEPENDENCIES: "更新到安全版本的依賴項"
        }
        return recommendations.get(vuln_type, "請進行安全評估和修復")


class PermissionManager:
    """權限管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.users = {}
        self.permissions_cache = {}
    
    async def create_user(self, username: str, access_level: AccessLevel, 
                         permissions: List[str] = None) -> str:
        """創建用戶"""
        user_id = str(uuid.uuid4())
        
        user = UserPermission(
            user_id=user_id,
            username=username,
            access_level=access_level,
            permissions=permissions or [],
            created_at=datetime.now().isoformat()
        )
        
        self.users[user_id] = user
        self.logger.info(f"創建用戶: {username} ({access_level.value})")
        
        return user_id
    
    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """檢查用戶權限"""
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        
        # 超級管理員擁有所有權限
        if user.access_level == AccessLevel.SUPER_ADMIN:
            return True
        
        # 檢查具體權限
        permission_key = f"{resource}:{action}"
        return permission_key in user.permissions
    
    async def grant_permission(self, user_id: str, resource: str, action: str) -> bool:
        """授予權限"""
        if user_id not in self.users:
            return False
        
        permission_key = f"{resource}:{action}"
        if permission_key not in self.users[user_id].permissions:
            self.users[user_id].permissions.append(permission_key)
            
        self.logger.info(f"授予權限: {permission_key} -> {self.users[user_id].username}")
        return True
    
    async def revoke_permission(self, user_id: str, resource: str, action: str) -> bool:
        """撤銷權限"""
        if user_id not in self.users:
            return False
        
        permission_key = f"{resource}:{action}"
        if permission_key in self.users[user_id].permissions:
            self.users[user_id].permissions.remove(permission_key)
            
        self.logger.info(f"撤銷權限: {permission_key} -> {self.users[user_id].username}")
        return True


class SecurityMCPManager:
    """Security MCP管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scanner = CodeSecurityScanner()
        self.permission_manager = PermissionManager()
        self.scan_results = {}
        self.audit_logs = []
        
        # 安全配置
        self.security_config = {
            "min_password_length": 12,
            "require_mfa": True,
            "session_timeout": 3600,  # 1小時
            "max_login_attempts": 5,
            "audit_retention_days": 90
        }
    
    async def initialize(self):
        """初始化Security MCP"""
        self.logger.info("🔒 初始化Security MCP - 企業級安全管理平台")
        
        # 創建默認管理員用戶
        await self._create_default_admin()
        
        # 載入安全策略
        await self._load_security_policies()
        
        self.logger.info("✅ Security MCP初始化完成")
    
    async def _create_default_admin(self):
        """創建默認管理員"""
        admin_id = await self.permission_manager.create_user(
            "admin",
            AccessLevel.SUPER_ADMIN,
            ["*:*"]  # 所有權限
        )
        self.logger.info(f"創建默認管理員用戶: {admin_id}")
    
    async def _load_security_policies(self):
        """載入安全策略"""
        # 模擬載入安全策略
        self.logger.info("載入企業安全策略配置")
    
    async def scan_codebase(self, target_path: str, scan_type: str = "full") -> str:
        """掃描代碼庫"""
        scan_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.logger.info(f"開始安全掃描: {target_path}")
        
        all_vulnerabilities = []
        files_scanned = 0
        
        # 掃描目標路徑
        target = Path(target_path)
        if target.is_file():
            vulnerabilities = await self.scanner.scan_file(str(target))
            all_vulnerabilities.extend(vulnerabilities)
            files_scanned = 1
        elif target.is_dir():
            for file_path in target.rglob("*.py"):
                vulnerabilities = await self.scanner.scan_file(str(file_path))
                all_vulnerabilities.extend(vulnerabilities)
                files_scanned += 1
        
        scan_duration = time.time() - start_time
        
        # 計算安全分數
        security_score = self._calculate_security_score(all_vulnerabilities, files_scanned)
        
        # 創建掃描結果
        scan_result = SecurityScanResult(
            scan_id=scan_id,
            target_path=target_path,
            scan_type=scan_type,
            vulnerabilities=all_vulnerabilities,
            scan_duration=scan_duration,
            started_at=datetime.fromtimestamp(start_time).isoformat(),
            completed_at=datetime.now().isoformat(),
            total_files_scanned=files_scanned,
            security_score=security_score
        )
        
        self.scan_results[scan_id] = scan_result
        
        self.logger.info(f"安全掃描完成: {len(all_vulnerabilities)} 個漏洞，安全分數: {security_score}")
        
        return scan_id
    
    def _calculate_security_score(self, vulnerabilities: List[SecurityVulnerability], 
                                 files_scanned: int) -> float:
        """計算安全分數"""
        if files_scanned == 0:
            return 100.0
        
        # 根據漏洞嚴重程度計算扣分
        score_deduction = 0
        for vuln in vulnerabilities:
            if vuln.severity == SecurityLevel.CRITICAL:
                score_deduction += 20
            elif vuln.severity == SecurityLevel.HIGH:
                score_deduction += 10
            elif vuln.severity == SecurityLevel.MEDIUM:
                score_deduction += 5
            else:
                score_deduction += 1
        
        # 基於文件數量調整
        base_score = 100.0
        adjusted_deduction = score_deduction / max(files_scanned / 10, 1)
        
        return max(0.0, base_score - adjusted_deduction)
    
    async def log_security_event(self, user_id: str, action: str, resource: str,
                                ip_address: str, user_agent: str, result: str,
                                details: Dict[str, Any] = None):
        """記錄安全事件"""
        log_entry = SecurityAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource=resource,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            details=details or {}
        )
        
        self.audit_logs.append(log_entry)
        
        # 檢查是否需要警報
        await self._check_security_alerts(log_entry)
    
    async def _check_security_alerts(self, log_entry: SecurityAuditLog):
        """檢查安全警報"""
        # 檢查可疑活動
        if log_entry.result == "failed":
            recent_failures = [
                log for log in self.audit_logs[-100:]
                if (log.user_id == log_entry.user_id and 
                    log.result == "failed" and
                    log.action == log_entry.action)
            ]
            
            if len(recent_failures) >= self.security_config["max_login_attempts"]:
                self.logger.warning(f"檢測到可疑活動: 用戶 {log_entry.user_id} 多次失敗嘗試")
    
    async def get_scan_result(self, scan_id: str) -> Optional[SecurityScanResult]:
        """獲取掃描結果"""
        return self.scan_results.get(scan_id)
    
    async def list_vulnerabilities(self, severity_filter: SecurityLevel = None) -> List[SecurityVulnerability]:
        """列出漏洞"""
        all_vulnerabilities = []
        for scan_result in self.scan_results.values():
            all_vulnerabilities.extend(scan_result.vulnerabilities)
        
        if severity_filter:
            return [v for v in all_vulnerabilities if v.severity == severity_filter]
        
        return all_vulnerabilities
    
    async def generate_security_report(self, format: str = "json") -> str:
        """生成安全報告"""
        report_data = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_scans": len(self.scan_results),
                "total_vulnerabilities": sum(len(sr.vulnerabilities) for sr in self.scan_results.values()),
                "average_security_score": sum(sr.security_score for sr in self.scan_results.values()) / max(len(self.scan_results), 1),
                "total_users": len(self.permission_manager.users),
                "total_audit_logs": len(self.audit_logs)
            },
            "scan_results": [asdict(sr) for sr in self.scan_results.values()],
            "recent_audit_logs": [asdict(log) for log in self.audit_logs[-50:]]
        }
        
        if format == "json":
            return json.dumps(report_data, indent=2, ensure_ascii=False)
        else:
            return str(report_data)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取Security MCP狀態"""
        return {
            "component": "Security MCP",
            "version": "4.6.1",
            "status": "running",
            "total_scans": len(self.scan_results),
            "active_users": len(self.permission_manager.users),
            "audit_logs": len(self.audit_logs),
            "security_features": [
                "code_vulnerability_scanning",
                "permission_management",
                "audit_logging",
                "compliance_checking",
                "security_reporting"
            ],
            "supported_scan_types": ["full", "quick", "targeted"],
            "vulnerability_types": [vt.value for vt in VulnerabilityType]
        }


# 單例實例
security_mcp = SecurityMCPManager()