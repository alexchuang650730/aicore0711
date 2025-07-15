#!/usr/bin/env python3
"""
K2 HITL MCP - K2模型人机协作管理器
PowerAutomation v4.6.9.4 - K2 Human-in-the-Loop 集成

基于 Claude Code 的权限管理模式，为 K2 模型提供：
- 分级权限控制系统
- 智能风险评估引擎
- 上下文感知确认机制
- 操作监控和审计日志
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import os
import sys

# 导入真实的用户确认接口
from .user_confirmation_interface import (
    UserConfirmationInterface, 
    ConfirmationMethod, 
    ConfirmationStatus
)

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险级别枚举"""
    SAFE = 0        # 安全操作 - 自动批准
    LOW = 1         # 低风险 - 简单确认
    MEDIUM = 2      # 中等风险 - 详细确认
    HIGH = 3        # 高风险 - 强制确认
    CRITICAL = 4    # 危险操作 - 最高级确认


class OperationType(Enum):
    """操作类型枚举"""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_COMMAND = "execute_command"
    NETWORK_REQUEST = "network_request"
    SYSTEM_CONFIG = "system_config"
    DEPLOY_OPERATION = "deploy_operation"
    DATABASE_OPERATION = "database_operation"


class ConfirmationMode(Enum):
    """确认模式枚举"""
    AUTO_APPROVE = "auto_approve"
    SIMPLE_CONFIRM = "simple_confirm"
    DETAILED_CONFIRM = "detailed_confirm"
    EXPERT_CONFIRM = "expert_confirm"
    BATCH_CONFIRM = "batch_confirm"


@dataclass
class Operation:
    """操作定义"""
    operation_id: str
    operation_type: OperationType
    description: str
    target_path: Optional[str] = None
    parameters: Dict[str, Any] = None
    context: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.context is None:
            self.context = {}
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class PermissionResult:
    """权限结果"""
    operation_id: str
    approved: bool
    risk_level: RiskLevel
    confirmation_mode: ConfirmationMode
    user_response: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    session_id: str
    project_path: str
    current_file: Optional[str] = None
    trust_level: float = 0.5  # 0.0 - 1.0
    recent_operations: List[str] = None
    preferences: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.recent_operations is None:
            self.recent_operations = []
        if self.preferences is None:
            self.preferences = {}
        if self.metadata is None:
            self.metadata = {}


class PermissionAssessmentEngine:
    """权限评估引擎 - v4.6.9.4 修复版本"""
    
    def __init__(self):
        self.risk_cache = {}
        self.assessment_rules = self._load_assessment_rules()
    
    def _load_assessment_rules(self) -> dict:
        """加载评估规则"""
        return {
            "path_patterns": {
                "critical": ["/etc/passwd", "/etc/shadow", "/boot/", "/sys/", "/proc/", "/dev/", "/root/"],
                "high": ["/etc/", "/usr/bin/", "/usr/sbin/", "/var/log/", "/opt/"],
                "medium": ["/src/", "/app/", "/project/", ".py", ".js", ".ts", ".java"],
                "low": ["/home/", "/Users/", "/Documents/"],
                "safe": ["/tmp/", "/var/tmp/", ".log", ".txt", ".md"]
            },
            "operation_risks": {
                "read_file": RiskLevel.SAFE,
                "list_directory": RiskLevel.SAFE,
                "get_status": RiskLevel.SAFE,
                "view_log": RiskLevel.LOW,
                "write_file": RiskLevel.LOW,
                "create_file": RiskLevel.LOW,
                "update_config": RiskLevel.MEDIUM,
                "install_package": RiskLevel.MEDIUM,
                "delete_file": RiskLevel.MEDIUM,
                "remove_directory": RiskLevel.HIGH,
                "uninstall_package": RiskLevel.HIGH,
                "modify_system": RiskLevel.HIGH,
                "change_permissions": RiskLevel.HIGH,
                "format_disk": RiskLevel.CRITICAL,
                "shutdown_system": RiskLevel.CRITICAL
            }
        }
    
    def analyze_path_risk(self, target_path: str) -> RiskLevel:
        """改进的路径风险分析 - v4.6.9.5"""
        if not target_path:
            return RiskLevel.MEDIUM
        
        target_path_lower = target_path.lower()
        
        # 系统关键路径 - CRITICAL
        critical_patterns = [
            "/etc/passwd", "/etc/shadow", "/etc/sudoers",
            "/boot/", "/sys/", "/proc/", "/dev/", "/root/",
            "system32", "windows/system32"
        ]
        for pattern in critical_patterns:
            if pattern in target_path_lower:
                return RiskLevel.CRITICAL
        
        # 系统配置路径 - HIGH  
        high_patterns = [
            "/etc/", "/usr/bin/", "/usr/sbin/", "/var/log/",
            "/opt/", "/lib/", "/usr/lib/", "program files"
        ]
        for pattern in high_patterns:
            if target_path_lower.startswith(pattern) or pattern in target_path_lower:
                return RiskLevel.HIGH
        
        # 项目代码路径 - MEDIUM
        medium_patterns = [
            "/src/", "/app/", "/project/", "/code/",
            ".py", ".js", ".ts", ".java", ".cpp", ".c"
        ]
        for pattern in medium_patterns:
            if pattern in target_path_lower:
                return RiskLevel.MEDIUM
        
        # 临时和安全路径 - SAFE/LOW
        safe_patterns = ["/tmp/", "/var/tmp/", "/temp/"]
        low_patterns = ["/home/", "/users/", "/documents/", "/downloads/"]
        
        for pattern in safe_patterns:
            if pattern in target_path_lower:
                return RiskLevel.SAFE
                
        for pattern in low_patterns:
            if pattern in target_path_lower:
                return RiskLevel.LOW
        
        # 根据文件扩展名进一步判断
        if any(ext in target_path_lower for ext in [".log", ".txt", ".md", ".json"]):
            return RiskLevel.SAFE
        
        # 默认为低风险
        return RiskLevel.LOW
    
    def analyze_operation_type_risk(self, operation_type: str) -> RiskLevel:
        """改进的操作类型风险分析 - v4.6.9.5"""
        if not operation_type:
            return RiskLevel.MEDIUM
        
        operation_type_lower = operation_type.lower()
        
        # 精确的操作风险映射
        operation_risks = {
            # 只读操作 - SAFE
            "read_file": RiskLevel.SAFE,
            "read": RiskLevel.SAFE,
            "list_directory": RiskLevel.SAFE,
            "list": RiskLevel.SAFE,
            "get_status": RiskLevel.SAFE,
            "status": RiskLevel.SAFE,
            "view": RiskLevel.SAFE,
            
            # 查看操作 - LOW
            "view_log": RiskLevel.LOW,
            "show": RiskLevel.LOW,
            "display": RiskLevel.LOW,
            "cat": RiskLevel.LOW,
            
            # 写入操作 - LOW/MEDIUM
            "write_file": RiskLevel.LOW,
            "write": RiskLevel.LOW,
            "create_file": RiskLevel.LOW,
            "create": RiskLevel.LOW,
            "edit": RiskLevel.MEDIUM,
            "modify": RiskLevel.MEDIUM,
            "update": RiskLevel.MEDIUM,
            
            # 配置操作 - MEDIUM
            "update_config": RiskLevel.MEDIUM,
            "config": RiskLevel.MEDIUM,
            "configure": RiskLevel.MEDIUM,
            "install_package": RiskLevel.MEDIUM,
            "install": RiskLevel.MEDIUM,
            
            # 删除操作 - MEDIUM/HIGH
            "delete_file": RiskLevel.MEDIUM,
            "delete": RiskLevel.MEDIUM,
            "remove": RiskLevel.HIGH,
            "remove_directory": RiskLevel.HIGH,
            "rmdir": RiskLevel.HIGH,
            "rm": RiskLevel.HIGH,
            
            # 系统操作 - HIGH
            "uninstall_package": RiskLevel.HIGH,
            "uninstall": RiskLevel.HIGH,
            "modify_system": RiskLevel.HIGH,
            "system": RiskLevel.HIGH,
            "change_permissions": RiskLevel.HIGH,
            "chmod": RiskLevel.HIGH,
            "chown": RiskLevel.HIGH,
            
            # 危险操作 - CRITICAL
            "format_disk": RiskLevel.CRITICAL,
            "format": RiskLevel.CRITICAL,
            "shutdown_system": RiskLevel.CRITICAL,
            "shutdown": RiskLevel.CRITICAL,
            "reboot": RiskLevel.CRITICAL,
            "restart": RiskLevel.CRITICAL
        }
        
        # 直接匹配
        if operation_type_lower in operation_risks:
            return operation_risks[operation_type_lower]
        
        # 模糊匹配
        for op_key, risk_level in operation_risks.items():
            if op_key in operation_type_lower or operation_type_lower in op_key:
                return risk_level
        
        # 默认为中等风险
        return RiskLevel.MEDIUM
    def analyze_operation_type_risk(self, operation_type: str) -> RiskLevel:
        """分析操作类型风险 - 修复版本"""
        if not operation_type:
            return RiskLevel.MEDIUM
        
        return self.assessment_rules["operation_risks"].get(
            operation_type.lower(), 
            RiskLevel.MEDIUM
        )
    
    def calculate_combined_risk(self, path_risk: RiskLevel, operation_risk: RiskLevel, 
                              context_adjustment: float = 0.0) -> RiskLevel:
        """计算综合风险级别 - 修复版本"""
        # 取路径风险和操作风险的最大值作为基础风险
        base_risk_value = max(path_risk.value, operation_risk.value)
        
        # 应用上下文调整
        final_risk_value = base_risk_value + context_adjustment
        
        # 确保风险值在有效范围内
        final_risk_value = max(0, min(4, int(final_risk_value)))
        
        # 返回对应的风险级别
        risk_levels = [RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return risk_levels[final_risk_value]
    
    async def assess_operation_risk(self, operation: 'Operation') -> RiskLevel:
        """评估操作风险 - 主入口方法"""
        try:
            # 分析路径风险
            path_risk = self.analyze_path_risk(operation.target_path)
            
            # 分析操作类型风险
            operation_risk = self.analyze_operation_type_risk(operation.operation_type)
            
            # 计算综合风险
            combined_risk = self.calculate_combined_risk(path_risk, operation_risk)
            
            logger.info(f"风险评估完成: 路径={path_risk.name}, 操作={operation_risk.name}, 综合={combined_risk.name}")
            
            return combined_risk
            
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            # 出错时返回高风险，确保安全
            return RiskLevel.HI
    async def assess_risk(self, operation: Operation) -> RiskLevel:
        """兼容性方法 - 重定向到 assess_operation_risk"""
        return await self.assess_operation_risk(operation)


class UserConfirmationManager:
    """用户确认管理器 - v4.6.9.4 修复版本"""
    
    def __init__(self):
        self.confirmation_timeout = 30
        self.pending_confirmations = {}
    
    def select_confirmation_mode(self, risk_level: RiskLevel, trust_level: float) -> ConfirmationMode:
        """选择确认模式 - 修复版本"""
        try:
            if risk_level == RiskLevel.SAFE:
                return ConfirmationMode.AUTO_APPROVE
            elif risk_level == RiskLevel.LOW and trust_level > 0.7:
                return ConfirmationMode.AUTO_APPROVE
            elif risk_level == RiskLevel.LOW:
                return ConfirmationMode.SIMPLE_CONFIRM
            elif risk_level == RiskLevel.MEDIUM and trust_level > 0.5:
                return ConfirmationMode.SIMPLE_CONFIRM
            elif risk_level == RiskLevel.MEDIUM:
                return ConfirmationMode.DETAILED_CONFIRM
            elif risk_level == RiskLevel.HIGH and trust_level > 0.3:
                return ConfirmationMode.DETAILED_CONFIRM
            else:
                return ConfirmationMode.EXPERT_CONFIRM
                
        except Exception as e:
            logger.error(f"确认模式选择失败: {e}")
            return ConfirmationMode.EXPERT_CONFIRM
    
    async def request_user_confirmation(self, 
                                      operation: Operation, 
                                      risk_level: RiskLevel, 
                                      confirmation_mode: ConfirmationMode) -> bool:
        """请求用户确认 - 真实实现版本"""
        try:
            if confirmation_mode == ConfirmationMode.AUTO_APPROVE:
                logger.info(f"✅ 自动批准: {operation.description}")
                return True
            
            # 使用真实的用户确认接口
            if self.config.get("use_real_confirmation", True):
                logger.info(f"🔐 请求用户确认: {operation.description}")
                
                # 准备确认详情
                details = {
                    "operation_type": operation.operation_type,
                    "target_path": operation.target_path,
                    "parameters": operation.parameters,
                    "confirmation_mode": confirmation_mode.name,
                    "estimated_impact": self._estimate_operation_impact(operation)
                }
                
                # 请求真实用户确认
                response = await self.user_confirmation.request_confirmation(
                    operation=operation.operation_type,
                    risk_level=risk_level.name,
                    description=operation.description,
                    details=details,
                    timeout=self.config.get("operation_timeout", 300)
                )
                
                # 记录确认结果
                logger.info(f"{'✅' if response.approved else '❌'} 用户确认结果: {response.status.value}")
                if response.reason:
                    logger.info(f"原因: {response.reason}")
                
                return response.approved
            else:
                # 回退到基于风险级别的自动决策（仅用于测试）
                logger.warning(f"⚠️ 使用测试模式确认: {confirmation_mode.name}")
                if risk_level in [RiskLevel.SAFE, RiskLevel.LOW]:
                    return True
                else:
                    return False
                
        except Exception as e:
            logger.error(f"确认请求失败: {e}")
            return False
    
    def _estimate_operation_impact(self, operation: Operation) -> str:
        """估算操作影响"""
        if operation.operation_type in ["read_file", "list_directory", "get_status"]:
            return "无影响 - 只读操作"
        elif operation.operation_type in ["write_file", "create_file", "edit"]:
            return "低影响 - 文件修改"
        elif operation.operation_type in ["delete_file", "remove_directory"]:
            return "高影响 - 数据删除"
        elif operation.operation_type in ["system_shutdown", "format_disk"]:
            return "严重影响 - 系统级操作"
        else:
            return "中等影响 - 一般操作"


class ContextAwarenessModule:
    """上下文感知模块"""
    
    def __init__(self):
        self.risk_matrix = self._initialize_risk_matrix()
        self.sensitivity_patterns = self._initialize_sensitivity_patterns()
        
    def _initialize_risk_matrix(self) -> Dict[OperationType, int]:
        """初始化操作风险矩阵"""
        return {
            OperationType.READ_FILE: 0,
            OperationType.WRITE_FILE: 1,
            OperationType.DELETE_FILE: 3,
            OperationType.EXECUTE_COMMAND: 2,
            OperationType.NETWORK_REQUEST: 3,
            OperationType.SYSTEM_CONFIG: 4,
            OperationType.DEPLOY_OPERATION: 4,
            OperationType.DATABASE_OPERATION: 3,
        }
    
    def _initialize_sensitivity_patterns(self) -> List[Dict[str, Any]]:
        """初始化文件敏感度模式"""
        return [
            {"pattern": r"\.env$", "score": 3, "description": "环境配置文件"},
            {"pattern": r"config\.json$", "score": 2, "description": "配置文件"},
            {"pattern": r"\.key$|\.pem$|\.crt$", "score": 4, "description": "密钥文件"},
            {"pattern": r"package\.json$", "score": 2, "description": "依赖配置"},
            {"pattern": r"Dockerfile$", "score": 2, "description": "容器配置"},
            {"pattern": r"\.sql$", "score": 3, "description": "数据库脚本"},
            {"pattern": r"deploy\.sh$|deploy\.py$", "score": 4, "description": "部署脚本"},
        ]
    
    async def assess_risk(self, operation: Operation, context: UserContext) -> RiskLevel:
        """评估操作风险级别"""
        try:
            # 基础风险分数
            base_score = self.risk_matrix.get(operation.operation_type, 2)
            
            # 文件敏感度分数
            sensitivity_score = self._calculate_sensitivity_score(operation.target_path)
            
            # 上下文相关分数
            context_score = self._calculate_context_score(operation, context)
            
            # 时间和频率分数
            temporal_score = self._calculate_temporal_score(operation, context)
            
            # 用户信任度调整
            trust_adjustment = (1.0 - context.trust_level) * 0.5
            
            # 计算最终风险分数
            final_score = (
                base_score + 
                sensitivity_score + 
                context_score + 
                temporal_score + 
                trust_adjustment
            )
            
            # 转换为风险级别
            if final_score <= 0.5:
                return RiskLevel.SAFE
            elif final_score <= 1.5:
                return RiskLevel.LOW
            elif final_score <= 2.5:
                return RiskLevel.MEDIUM
            elif final_score <= 3.5:
                return RiskLevel.HIGH
            else:
                return RiskLevel.CRITICAL
                
        except Exception as e:
            self.logger.error(f"风险评估失败: {e}")
            return RiskLevel.HIGH  # 默认高风险
    
    def _calculate_sensitivity_score(self, file_path: Optional[str]) -> float:
        """计算文件敏感度分数"""
        if not file_path:
            return 0.0
        
        import re
        for pattern_info in self.sensitivity_patterns:
            if re.search(pattern_info["pattern"], file_path):
                return pattern_info["score"] * 0.5
        
        return 0.0
    
    def _calculate_context_score(self, operation: Operation, context: UserContext) -> float:
        """计算上下文相关分数"""
        score = 0.0
        
        # 项目类型检查
        if "production" in context.project_path.lower():
            score += 1.0
        elif "test" in context.project_path.lower():
            score += 0.5
        
        # 操作参数检查
        if operation.parameters:
            if any(keyword in str(operation.parameters).lower() 
                   for keyword in ["delete", "remove", "drop", "truncate"]):
                score += 1.0
        
        return score
    
    def _calculate_temporal_score(self, operation: Operation, context: UserContext) -> float:
        """计算时间和频率分数"""
        score = 0.0
        current_time = datetime.now()
        
        # 异常时间检查（深夜或周末）
        if current_time.hour < 6 or current_time.hour > 22:
            score += 0.5
        if current_time.weekday() >= 5:  # 周末
            score += 0.3
        
        # 频率检查
        recent_similar_ops = sum(1 for op_id in context.recent_operations[-10:] 
                               if operation.operation_type.value in op_id)
        if recent_similar_ops > 3:
            score += 0.5
        
        return score


class UserConfirmationManager:
    """用户确认管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pending_confirmations = {}
        self.confirmation_timeout = 300  # 5分钟超时
        
    async def request_confirmation(
        self, 
        operation: Operation, 
        risk_level: RiskLevel, 
        context: UserContext
    ) -> PermissionResult:
        """请求用户确认"""
        try:
            confirmation_mode = self._determine_confirmation_mode(risk_level, operation)
            
            if confirmation_mode == ConfirmationMode.AUTO_APPROVE:
                return PermissionResult(
                    operation_id=operation.operation_id,
                    approved=True,
                    risk_level=risk_level,
                    confirmation_mode=confirmation_mode
                )
            
            # 创建确认请求
            confirmation_request = {
                "operation": operation,
                "risk_level": risk_level,
                "confirmation_mode": confirmation_mode,
                "context": context,
                "timestamp": time.time()
            }
            
            self.pending_confirmations[operation.operation_id] = confirmation_request
            
            # 根据确认模式显示不同的确认界面
            if confirmation_mode == ConfirmationMode.SIMPLE_CONFIRM:
                return await self._show_simple_confirmation(operation, risk_level)
            elif confirmation_mode == ConfirmationMode.DETAILED_CONFIRM:
                return await self._show_detailed_confirmation(operation, risk_level, context)
            elif confirmation_mode == ConfirmationMode.EXPERT_CONFIRM:
                return await self._show_expert_confirmation(operation, risk_level, context)
            else:
                return await self._show_batch_confirmation([operation], risk_level, context)
                
        except Exception as e:
            self.logger.error(f"确认请求失败: {e}")
            return PermissionResult(
                operation_id=operation.operation_id,
                approved=False,
                risk_level=risk_level,
                confirmation_mode=ConfirmationMode.SIMPLE_CONFIRM,
                user_response=f"确认失败: {str(e)}"
            )
    
    def _determine_confirmation_mode(self, risk_level: RiskLevel, operation: Operation) -> ConfirmationMode:
        """确定确认模式"""
        if risk_level == RiskLevel.SAFE:
            return ConfirmationMode.AUTO_APPROVE
        elif risk_level == RiskLevel.LOW:
            return ConfirmationMode.SIMPLE_CONFIRM
        elif risk_level == RiskLevel.MEDIUM:
            return ConfirmationMode.DETAILED_CONFIRM
        else:
            return ConfirmationMode.EXPERT_CONFIRM
    
    async def _show_simple_confirmation(self, operation: Operation, risk_level: RiskLevel) -> PermissionResult:
        """显示简单确认对话框"""
        # 这里应该调用前端确认界面
        # 使用真实的用户确认接口
        self.logger.info(f"🔍 简单确认: {operation.description}")
        
        # 请求真实用户确认
        user_approved = await self.request_user_confirmation(operation, risk_level, ConfirmationMode.SIMPLE_CONFIRM)
        
        return PermissionResult(
            operation_id=operation.operation_id,
            approved=user_approved,
            risk_level=risk_level,
            confirmation_mode=ConfirmationMode.SIMPLE_CONFIRM,
            user_response="用户确认" if user_approved else "用户拒绝"
        )
    
    async def _show_detailed_confirmation(
        self, 
        operation: Operation, 
        risk_level: RiskLevel, 
        context: UserContext
    ) -> PermissionResult:
        """显示详细确认对话框"""
        self.logger.info(f"🔍 详细确认: {operation.description}")
        self.logger.info(f"   操作类型: {operation.operation_type.value}")
        self.logger.info(f"   目标路径: {operation.target_path}")
        self.logger.info(f"   风险级别: {risk_level.name}")
        self.logger.info(f"   项目路径: {context.project_path}")
        
        # 使用真实的用户确认接口
        user_approved = await self.request_user_confirmation(operation, risk_level, ConfirmationMode.DETAILED_CONFIRM)
        
        return PermissionResult(
            operation_id=operation.operation_id,
            approved=user_approved,
            risk_level=risk_level,
            confirmation_mode=ConfirmationMode.DETAILED_CONFIRM,
            user_response="详细确认通过" if user_approved else "详细确认拒绝"
        )
    
    async def _show_expert_confirmation(
        self, 
        operation: Operation, 
        risk_level: RiskLevel, 
        context: UserContext
    ) -> PermissionResult:
        """显示专家确认对话框"""
        self.logger.warning(f"⚠️ 专家确认: {operation.description}")
        self.logger.warning(f"   操作类型: {operation.operation_type.value}")
        self.logger.warning(f"   目标路径: {operation.target_path}")
        self.logger.warning(f"   风险级别: {risk_level.name}")
        self.logger.warning(f"   操作参数: {json.dumps(operation.parameters, indent=2)}")
        self.logger.warning(f"   用户信任度: {context.trust_level}")
        self.logger.warning("   这是高风险操作，请专家级用户仔细确认!")
        
        # 使用真实的用户确认接口（专家模式）
        user_approved = await self.request_user_confirmation(operation, risk_level, ConfirmationMode.EXPERT_CONFIRM)
        
        return PermissionResult(
            operation_id=operation.operation_id,
            approved=user_approved,
            risk_level=risk_level,
            confirmation_mode=ConfirmationMode.EXPERT_CONFIRM,
            user_response="专家确认通过" if user_approved else "专家确认拒绝"
        )
    
    async def _show_batch_confirmation(
        self, 
        operations: List[Operation], 
        risk_level: RiskLevel, 
        context: UserContext
    ) -> PermissionResult:
        """显示批量确认对话框"""
        self.logger.info(f"📋 批量确认: {len(operations)} 个操作")
        for i, op in enumerate(operations, 1):
            self.logger.info(f"   {i}. {op.description}")
        
        await asyncio.sleep(0.3)
        user_approved = True
        
        return PermissionResult(
            operation_id=operations[0].operation_id,
            approved=user_approved,
            risk_level=risk_level,
            confirmation_mode=ConfirmationMode.BATCH_CONFIRM,
            user_response=f"批量确认 {len(operations)} 个操作"
        )


class OperationMonitor:
    """操作监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.operation_history = []
        self.active_operations = {}
        self.max_history_size = 1000
        
    async def start_operation(self, operation: Operation) -> str:
        """开始监控操作"""
        monitor_id = str(uuid.uuid4())
        
        monitor_record = {
            "monitor_id": monitor_id,
            "operation": operation,
            "start_time": time.time(),
            "status": "running",
            "checkpoints": []
        }
        
        self.active_operations[monitor_id] = monitor_record
        self.logger.info(f"🔍 开始监控操作: {operation.description} [{monitor_id[:8]}]")
        
        return monitor_id
    
    async def add_checkpoint(self, monitor_id: str, checkpoint: str, data: Any = None):
        """添加检查点"""
        if monitor_id in self.active_operations:
            checkpoint_record = {
                "timestamp": time.time(),
                "checkpoint": checkpoint,
                "data": data
            }
            self.active_operations[monitor_id]["checkpoints"].append(checkpoint_record)
            self.logger.debug(f"📍 检查点 [{monitor_id[:8]}]: {checkpoint}")
    
    async def complete_operation(self, monitor_id: str, result: Any = None, error: str = None):
        """完成操作监控"""
        if monitor_id in self.active_operations:
            record = self.active_operations[monitor_id]
            record["end_time"] = time.time()
            record["execution_time"] = record["end_time"] - record["start_time"]
            record["status"] = "completed" if error is None else "failed"
            record["result"] = result
            record["error"] = error
            
            # 移动到历史记录
            self.operation_history.append(record)
            del self.active_operations[monitor_id]
            
            # 限制历史记录大小
            if len(self.operation_history) > self.max_history_size:
                self.operation_history = self.operation_history[-self.max_history_size:]
            
            status_emoji = "✅" if error is None else "❌"
            self.logger.info(f"{status_emoji} 操作完成 [{monitor_id[:8]}]: {record['execution_time']:.2f}s")
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """获取操作统计信息"""
        total_operations = len(self.operation_history)
        successful_operations = sum(1 for record in self.operation_history if record["status"] == "completed")
        failed_operations = total_operations - successful_operations
        
        if total_operations > 0:
            avg_execution_time = sum(record.get("execution_time", 0) for record in self.operation_history) / total_operations
            success_rate = successful_operations / total_operations
        else:
            avg_execution_time = 0
            success_rate = 0
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "active_operations": len(self.active_operations)
        }


class ContextAwarenessModule:
    """上下文感知模块"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.context_cache = {}
        
    async def get_current_context(self, user_id: str, session_id: str) -> UserContext:
        """获取当前用户上下文"""
        cache_key = f"{user_id}:{session_id}"
        
        if cache_key in self.context_cache:
            context = self.context_cache[cache_key]
            # 更新最近操作时间
            if not hasattr(context, 'metadata'):
                context.metadata = {}
            context.metadata["last_access"] = time.time()
            return context
        
        # 创建新的上下文
        context = UserContext(
            user_id=user_id,
            session_id=session_id,
            project_path="/default/project",
            trust_level=0.5,
            preferences={
                "auto_approve_safe": True,
                "detailed_confirmations": True,
                "expert_mode": False
            }
        )
        
        self.context_cache[cache_key] = context
        return context
    
    async def update_trust_level(self, user_id: str, session_id: str, adjustment: float):
        """更新用户信任度"""
        context = await self.get_current_context(user_id, session_id)
        old_trust = context.trust_level
        context.trust_level = max(0.0, min(1.0, context.trust_level + adjustment))
        
        self.logger.info(f"🔄 用户信任度更新: {old_trust:.2f} -> {context.trust_level:.2f}")
    
    async def add_recent_operation(self, user_id: str, session_id: str, operation_id: str):
        """添加最近操作记录"""
        context = await self.get_current_context(user_id, session_id)
        context.recent_operations.append(operation_id)
        
        # 保持最近操作列表大小
        if len(context.recent_operations) > 20:
            context.recent_operations = context.recent_operations[-20:]


class K2HITLManager:
    """K2 HITL 主管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.permission_engine = PermissionAssessmentEngine()
        self.confirmation_manager = UserConfirmationManager()
        self.operation_monitor = OperationMonitor()
        self.context_module = ContextAwarenessModule()
        
        # 集成真实的用户确认接口
        self.user_confirmation = UserConfirmationInterface(ConfirmationMethod.CONSOLE)
        
        # 配置
        self.config = {
            "enabled": True,
            "default_trust_level": 0.5,
            "auto_approve_safe_operations": True,
            "require_confirmation_for_medium_risk": True,
            "expert_mode_for_high_risk": True,
            "operation_timeout": 300,
            "max_concurrent_operations": 10,
            "use_real_confirmation": True  # 使用真实确认而非模拟
        }
        
        self.logger.info("🚀 K2 HITL 管理器初始化完成 - 集成真实用户确认接口")
    
    async def evaluate_operation(
        self, 
        operation: Operation, 
        user_id: str = "default", 
        session_id: str = "default"
    ) -> PermissionResult:
        """评估操作权限"""
        try:
            if not self.config["enabled"]:
                return PermissionResult(
                    operation_id=operation.operation_id,
                    approved=True,
                    risk_level=RiskLevel.SAFE,
                    confirmation_mode=ConfirmationMode.AUTO_APPROVE,
                    user_response="HITL已禁用"
                )
            
            # 获取用户上下文
            context = await self.context_module.get_current_context(user_id, session_id)
            
            # 开始操作监控
            monitor_id = await self.operation_monitor.start_operation(operation)
            
            # 评估风险级别
            await self.operation_monitor.add_checkpoint(monitor_id, "risk_assessment_start")
            risk_level = await self.permission_engine.assess_operation_risk(operation, context)
            await self.operation_monitor.add_checkpoint(monitor_id, "risk_assessment_complete", {"risk_level": risk_level.name})
            
            # 请求用户确认
            await self.operation_monitor.add_checkpoint(monitor_id, "confirmation_request_start")
            result = await self.confirmation_manager.request_confirmation(operation, risk_level, context)
            await self.operation_monitor.add_checkpoint(monitor_id, "confirmation_request_complete", {"approved": result.approved})
            
            # 更新用户信任度
            if result.approved:
                trust_adjustment = 0.01 if risk_level.value <= 2 else 0.02
                await self.context_module.update_trust_level(user_id, session_id, trust_adjustment)
            else:
                trust_adjustment = -0.01
                await self.context_module.update_trust_level(user_id, session_id, trust_adjustment)
            
            # 记录操作
            await self.context_module.add_recent_operation(user_id, session_id, operation.operation_id)
            
            # 完成监控
            await self.operation_monitor.complete_operation(monitor_id, result)
            
            self.logger.info(f"✅ 操作评估完成: {operation.description} - {'批准' if result.approved else '拒绝'}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 操作评估失败: {e}")
            return PermissionResult(
                operation_id=operation.operation_id,
                approved=False,
                risk_level=RiskLevel.HIGH,
                confirmation_mode=ConfirmationMode.SIMPLE_CONFIRM,
                user_response=f"评估失败: {str(e)}"
            )
    
    async def batch_evaluate_operations(
        self, 
        operations: List[Operation], 
        user_id: str = "default", 
        session_id: str = "default"
    ) -> List[PermissionResult]:
        """批量评估操作权限"""
        results = []
        
        for operation in operations:
            result = await self.evaluate_operation(operation, user_id, session_id)
            results.append(result)
            
            # 如果有操作被拒绝，可以选择停止后续操作
            if not result.approved and operation.context.get("stop_on_rejection", False):
                self.logger.warning(f"⚠️ 操作被拒绝，停止后续操作: {operation.description}")
                break
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        operation_stats = self.operation_monitor.get_operation_stats()
        
        return {
            "enabled": self.config["enabled"],
            "operation_stats": operation_stats,
            "pending_confirmations": len(self.confirmation_manager.pending_confirmations),
            "context_cache_size": len(self.context_module.context_cache),
            "config": self.config
        }
    
    async def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        self.logger.info(f"🔧 配置已更新: {new_config}")


# 示例使用
async def demo_k2_hitl():
    """演示 K2 HITL 功能"""
    manager = K2HITLManager()
    
    # 创建测试操作
    operations = [
        Operation(
            operation_id="op_001",
            operation_type=OperationType.READ_FILE,
            description="读取配置文件",
            target_path="/project/config.json"
        ),
        Operation(
            operation_id="op_002",
            operation_type=OperationType.WRITE_FILE,
            description="修改源代码文件",
            target_path="/project/src/main.py",
            parameters={"content": "print('Hello, World!')"}
        ),
        Operation(
            operation_id="op_003",
            operation_type=OperationType.DELETE_FILE,
            description="删除临时文件",
            target_path="/project/temp/cache.tmp"
        ),
        Operation(
            operation_id="op_004",
            operation_type=OperationType.DEPLOY_OPERATION,
            description="部署到生产环境",
            target_path="/production/deploy",
            parameters={"environment": "production", "force": True}
        )
    ]
    
    print("🚀 开始 K2 HITL 演示...")
    
    for operation in operations:
        print(f"\n📋 评估操作: {operation.description}")
        result = await manager.evaluate_operation(operation)
        
        status = "✅ 批准" if result.approved else "❌ 拒绝"
        print(f"   结果: {status}")
        print(f"   风险级别: {result.risk_level.name}")
        print(f"   确认模式: {result.confirmation_mode.name}")
        print(f"   用户响应: {result.user_response}")
    
    # 显示系统状态
    print(f"\n📊 系统状态:")
    status = manager.get_system_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行演示
    asyncio.run(demo_k2_hitl())

