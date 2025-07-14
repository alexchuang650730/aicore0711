"""
PowerAutomation 4.0 MCP授权控制器

负责处理所有MCP服务的访问控制，支持基于角色的访问控制(RBAC)和细粒度权限管理。
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import re


class PermissionType(Enum):
    """权限类型枚举"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    CREATE = "create"
    UPDATE = "update"
    LIST = "list"


class ResourceType(Enum):
    """资源类型枚举"""
    SERVICE = "service"
    TOOL = "tool"
    DATA = "data"
    CONFIG = "config"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SESSION = "session"
    API = "api"
    FILE = "file"


class AccessDecision(Enum):
    """访问决策枚举"""
    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"


@dataclass
class Permission:
    """权限定义"""
    permission_id: str
    name: str
    description: str
    resource_type: ResourceType
    permission_type: PermissionType
    resource_pattern: str = "*"  # 资源匹配模式
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    """角色定义"""
    role_id: str
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)  # permission_ids
    parent_roles: Set[str] = field(default_factory=set)  # 父角色IDs
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessPolicy:
    """访问策略"""
    policy_id: str
    name: str
    description: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 100
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRequest:
    """访问请求"""
    user_id: str
    resource_type: ResourceType
    resource_id: str
    permission_type: PermissionType
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AccessResult:
    """访问结果"""
    decision: AccessDecision
    reason: str
    matched_permissions: List[str] = field(default_factory=list)
    matched_policies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class MCPAuthorizer:
    """
    PowerAutomation 4.0 MCP授权控制器
    
    功能：
    1. 基于角色的访问控制(RBAC)
    2. 细粒度权限管理
    3. 动态权限验证
    4. 权限继承和委托
    5. 访问策略管理
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化授权控制器
        
        Args:
            config: 配置参数
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.is_running = False
        
        # 权限存储
        self.permissions: Dict[str, Permission] = {}
        
        # 角色存储
        self.roles: Dict[str, Role] = {}
        
        # 用户角色映射
        self.user_roles: Dict[str, Set[str]] = {}  # user_id -> role_ids
        
        # 访问策略
        self.policies: Dict[str, AccessPolicy] = {}
        
        # 权限缓存
        self.permission_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5分钟
        
        # 访问日志
        self.access_logs: List[Dict[str, Any]] = []
        self.max_log_entries = self.config.get("max_log_entries", 10000)
        
        # 事件回调
        self.event_callbacks: Dict[str, List[callable]] = {
            "access_granted": [],
            "access_denied": [],
            "permission_added": [],
            "role_assigned": [],
            "policy_updated": []
        }
        
        self.logger.info("MCP授权控制器初始化完成")
    
    async def start(self) -> None:
        """启动授权控制器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动MCP授权控制器...")
            
            # 加载默认权限
            await self._load_default_permissions()
            
            # 加载默认角色
            await self._load_default_roles()
            
            # 加载默认策略
            await self._load_default_policies()
            
            # 启动后台任务
            asyncio.create_task(self._background_tasks())
            
            self.is_running = True
            self.logger.info("MCP授权控制器启动成功")
            
        except Exception as e:
            self.logger.error(f"MCP授权控制器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止授权控制器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止MCP授权控制器...")
            
            self.is_running = False
            
            # 保存权限数据
            await self._save_permissions()
            
            # 保存角色数据
            await self._save_roles()
            
            # 保存策略数据
            await self._save_policies()
            
            self.logger.info("MCP授权控制器已停止")
            
        except Exception as e:
            self.logger.error(f"MCP授权控制器停止时出错: {e}")
    
    async def check_permission(self, user_id: str, resource_type: ResourceType,
                              resource_id: str, permission_type: PermissionType,
                              context: Optional[Dict[str, Any]] = None) -> AccessResult:
        """
        检查用户权限
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            permission_type: 权限类型
            context: 访问上下文
            
        Returns:
            AccessResult: 访问结果
        """
        try:
            context = context or {}
            
            # 创建访问请求
            request = AccessRequest(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                permission_type=permission_type,
                context=context
            )
            
            # 检查缓存
            cache_key = self._get_cache_key(request)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # 执行权限检查
            result = await self._evaluate_access(request)
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            # 记录访问日志
            await self._log_access(request, result)
            
            # 触发事件
            if result.decision == AccessDecision.ALLOW:
                await self._trigger_event("access_granted", {
                    "user_id": user_id,
                    "resource": f"{resource_type.value}:{resource_id}",
                    "permission": permission_type.value,
                    "context": context
                })
            else:
                await self._trigger_event("access_denied", {
                    "user_id": user_id,
                    "resource": f"{resource_type.value}:{resource_id}",
                    "permission": permission_type.value,
                    "reason": result.reason,
                    "context": context
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"权限检查失败: {e}")
            return AccessResult(
                decision=AccessDecision.DENY,
                reason=f"权限检查异常: {e}"
            )
    
    async def add_permission(self, permission: Permission) -> bool:
        """
        添加权限
        
        Args:
            permission: 权限对象
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.permissions[permission.permission_id] = permission
            
            # 清除相关缓存
            self._clear_cache()
            
            # 触发事件
            await self._trigger_event("permission_added", permission)
            
            self.logger.info(f"权限添加成功: {permission.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加权限失败: {e}")
            return False
    
    async def add_role(self, role: Role) -> bool:
        """
        添加角色
        
        Args:
            role: 角色对象
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.roles[role.role_id] = role
            
            # 清除相关缓存
            self._clear_cache()
            
            self.logger.info(f"角色添加成功: {role.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加角色失败: {e}")
            return False
    
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """
        为用户分配角色
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            bool: 分配是否成功
        """
        try:
            if role_id not in self.roles:
                self.logger.error(f"角色不存在: {role_id}")
                return False
            
            if user_id not in self.user_roles:
                self.user_roles[user_id] = set()
            
            self.user_roles[user_id].add(role_id)
            
            # 清除用户相关缓存
            self._clear_user_cache(user_id)
            
            # 触发事件
            await self._trigger_event("role_assigned", {
                "user_id": user_id,
                "role_id": role_id
            })
            
            self.logger.info(f"角色分配成功: 用户 {user_id} -> 角色 {role_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"分配角色失败: {e}")
            return False
    
    async def revoke_role_from_user(self, user_id: str, role_id: str) -> bool:
        """
        撤销用户角色
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            bool: 撤销是否成功
        """
        try:
            if user_id not in self.user_roles:
                return False
            
            self.user_roles[user_id].discard(role_id)
            
            # 清除用户相关缓存
            self._clear_user_cache(user_id)
            
            self.logger.info(f"角色撤销成功: 用户 {user_id} -> 角色 {role_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"撤销角色失败: {e}")
            return False
    
    async def add_policy(self, policy: AccessPolicy) -> bool:
        """
        添加访问策略
        
        Args:
            policy: 访问策略
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.policies[policy.policy_id] = policy
            
            # 清除相关缓存
            self._clear_cache()
            
            # 触发事件
            await self._trigger_event("policy_updated", policy)
            
            self.logger.info(f"策略添加成功: {policy.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加策略失败: {e}")
            return False
    
    async def get_user_permissions(self, user_id: str) -> List[Permission]:
        """
        获取用户的所有权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Permission]: 权限列表
        """
        try:
            permissions = []
            user_roles = self.user_roles.get(user_id, set())
            
            # 收集所有角色的权限（包括继承的权限）
            all_roles = await self._get_all_user_roles(user_id)
            
            permission_ids = set()
            for role_id in all_roles:
                if role_id in self.roles:
                    role = self.roles[role_id]
                    permission_ids.update(role.permissions)
            
            # 获取权限对象
            for permission_id in permission_ids:
                if permission_id in self.permissions:
                    permissions.append(self.permissions[permission_id])
            
            return permissions
            
        except Exception as e:
            self.logger.error(f"获取用户权限失败: {e}")
            return []
    
    async def get_user_roles(self, user_id: str) -> List[Role]:
        """
        获取用户的所有角色
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Role]: 角色列表
        """
        try:
            roles = []
            all_role_ids = await self._get_all_user_roles(user_id)
            
            for role_id in all_role_ids:
                if role_id in self.roles:
                    roles.append(self.roles[role_id])
            
            return roles
            
        except Exception as e:
            self.logger.error(f"获取用户角色失败: {e}")
            return []
    
    async def check_resource_access(self, user_id: str, resource_pattern: str,
                                   permission_type: PermissionType) -> bool:
        """
        检查用户对资源模式的访问权限
        
        Args:
            user_id: 用户ID
            resource_pattern: 资源模式
            permission_type: 权限类型
            
        Returns:
            bool: 是否有权限
        """
        try:
            user_permissions = await self.get_user_permissions(user_id)
            
            for permission in user_permissions:
                if (permission.permission_type == permission_type and
                    self._match_resource_pattern(resource_pattern, permission.resource_pattern)):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查资源访问权限失败: {e}")
            return False
    
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
    
    async def _evaluate_access(self, request: AccessRequest) -> AccessResult:
        """评估访问请求"""
        try:
            # 1. 检查基于角色的权限
            rbac_result = await self._check_rbac_permissions(request)
            if rbac_result.decision == AccessDecision.ALLOW:
                return rbac_result
            
            # 2. 检查访问策略
            policy_result = await self._check_access_policies(request)
            if policy_result.decision == AccessDecision.ALLOW:
                return policy_result
            
            # 3. 默认拒绝
            return AccessResult(
                decision=AccessDecision.DENY,
                reason="没有匹配的权限或策略"
            )
            
        except Exception as e:
            self.logger.error(f"评估访问请求失败: {e}")
            return AccessResult(
                decision=AccessDecision.DENY,
                reason=f"评估异常: {e}"
            )
    
    async def _check_rbac_permissions(self, request: AccessRequest) -> AccessResult:
        """检查RBAC权限"""
        try:
            user_permissions = await self.get_user_permissions(request.user_id)
            matched_permissions = []
            
            for permission in user_permissions:
                # 检查权限类型匹配
                if permission.permission_type != request.permission_type:
                    continue
                
                # 检查资源类型匹配
                if permission.resource_type != request.resource_type:
                    continue
                
                # 检查资源模式匹配
                if not self._match_resource_pattern(request.resource_id, permission.resource_pattern):
                    continue
                
                # 检查条件匹配
                if not self._check_permission_conditions(permission, request):
                    continue
                
                matched_permissions.append(permission.permission_id)
            
            if matched_permissions:
                return AccessResult(
                    decision=AccessDecision.ALLOW,
                    reason="RBAC权限匹配",
                    matched_permissions=matched_permissions
                )
            else:
                return AccessResult(
                    decision=AccessDecision.DENY,
                    reason="没有匹配的RBAC权限"
                )
                
        except Exception as e:
            self.logger.error(f"检查RBAC权限失败: {e}")
            return AccessResult(
                decision=AccessDecision.DENY,
                reason=f"RBAC检查异常: {e}"
            )
    
    async def _check_access_policies(self, request: AccessRequest) -> AccessResult:
        """检查访问策略"""
        try:
            matched_policies = []
            
            # 按优先级排序策略
            sorted_policies = sorted(
                [p for p in self.policies.values() if p.is_active],
                key=lambda x: x.priority,
                reverse=True
            )
            
            for policy in sorted_policies:
                decision = await self._evaluate_policy(policy, request)
                if decision != AccessDecision.ABSTAIN:
                    matched_policies.append(policy.policy_id)
                    
                    return AccessResult(
                        decision=decision,
                        reason=f"策略匹配: {policy.name}",
                        matched_policies=matched_policies
                    )
            
            return AccessResult(
                decision=AccessDecision.ABSTAIN,
                reason="没有匹配的访问策略"
            )
            
        except Exception as e:
            self.logger.error(f"检查访问策略失败: {e}")
            return AccessResult(
                decision=AccessDecision.DENY,
                reason=f"策略检查异常: {e}"
            )
    
    async def _evaluate_policy(self, policy: AccessPolicy, request: AccessRequest) -> AccessDecision:
        """评估单个策略"""
        try:
            for rule in policy.rules:
                if await self._match_policy_rule(rule, request):
                    action = rule.get("action", "deny")
                    if action == "allow":
                        return AccessDecision.ALLOW
                    elif action == "deny":
                        return AccessDecision.DENY
            
            return AccessDecision.ABSTAIN
            
        except Exception as e:
            self.logger.error(f"评估策略失败: {e}")
            return AccessDecision.DENY
    
    async def _match_policy_rule(self, rule: Dict[str, Any], request: AccessRequest) -> bool:
        """匹配策略规则"""
        try:
            # 检查用户匹配
            if "users" in rule:
                users = rule["users"]
                if isinstance(users, list) and request.user_id not in users:
                    return False
                elif isinstance(users, str) and not self._match_pattern(request.user_id, users):
                    return False
            
            # 检查资源匹配
            if "resources" in rule:
                resources = rule["resources"]
                resource_path = f"{request.resource_type.value}:{request.resource_id}"
                if isinstance(resources, list) and resource_path not in resources:
                    return False
                elif isinstance(resources, str) and not self._match_pattern(resource_path, resources):
                    return False
            
            # 检查权限匹配
            if "permissions" in rule:
                permissions = rule["permissions"]
                if isinstance(permissions, list) and request.permission_type.value not in permissions:
                    return False
                elif isinstance(permissions, str) and request.permission_type.value != permissions:
                    return False
            
            # 检查上下文条件
            if "conditions" in rule:
                conditions = rule["conditions"]
                if not self._check_context_conditions(conditions, request.context):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"匹配策略规则失败: {e}")
            return False
    
    def _match_resource_pattern(self, resource_id: str, pattern: str) -> bool:
        """匹配资源模式"""
        try:
            if pattern == "*":
                return True
            
            # 支持通配符匹配
            import fnmatch
            return fnmatch.fnmatch(resource_id, pattern)
            
        except Exception as e:
            self.logger.error(f"匹配资源模式失败: {e}")
            return False
    
    def _match_pattern(self, value: str, pattern: str) -> bool:
        """匹配模式"""
        try:
            if pattern == "*":
                return True
            
            # 支持正则表达式
            if pattern.startswith("regex:"):
                regex_pattern = pattern[6:]
                return bool(re.match(regex_pattern, value))
            
            # 支持通配符
            import fnmatch
            return fnmatch.fnmatch(value, pattern)
            
        except Exception as e:
            self.logger.error(f"匹配模式失败: {e}")
            return False
    
    def _check_permission_conditions(self, permission: Permission, request: AccessRequest) -> bool:
        """检查权限条件"""
        try:
            conditions = permission.conditions
            
            # 检查时间条件
            if "time_range" in conditions:
                time_range = conditions["time_range"]
                current_time = datetime.now().time()
                start_time = datetime.strptime(time_range["start"], "%H:%M").time()
                end_time = datetime.strptime(time_range["end"], "%H:%M").time()
                
                if not (start_time <= current_time <= end_time):
                    return False
            
            # 检查IP地址条件
            if "ip_ranges" in conditions:
                ip_ranges = conditions["ip_ranges"]
                client_ip = request.context.get("ip_address")
                if client_ip and not self._check_ip_in_ranges(client_ip, ip_ranges):
                    return False
            
            # 检查自定义条件
            if "custom" in conditions:
                custom_conditions = conditions["custom"]
                for condition_name, condition_value in custom_conditions.items():
                    context_value = request.context.get(condition_name)
                    if context_value != condition_value:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查权限条件失败: {e}")
            return False
    
    def _check_context_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """检查上下文条件"""
        try:
            for key, expected_value in conditions.items():
                actual_value = context.get(key)
                
                if isinstance(expected_value, list):
                    if actual_value not in expected_value:
                        return False
                elif isinstance(expected_value, dict):
                    if "operator" in expected_value:
                        operator = expected_value["operator"]
                        value = expected_value["value"]
                        
                        if operator == "eq" and actual_value != value:
                            return False
                        elif operator == "ne" and actual_value == value:
                            return False
                        elif operator == "gt" and actual_value <= value:
                            return False
                        elif operator == "lt" and actual_value >= value:
                            return False
                        elif operator == "in" and actual_value not in value:
                            return False
                        elif operator == "not_in" and actual_value in value:
                            return False
                else:
                    if actual_value != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查上下文条件失败: {e}")
            return False
    
    def _check_ip_in_ranges(self, ip: str, ranges: List[str]) -> bool:
        """检查IP是否在指定范围内"""
        try:
            import ipaddress
            
            ip_obj = ipaddress.ip_address(ip)
            
            for range_str in ranges:
                if "/" in range_str:
                    # CIDR格式
                    network = ipaddress.ip_network(range_str, strict=False)
                    if ip_obj in network:
                        return True
                else:
                    # 单个IP
                    if str(ip_obj) == range_str:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查IP范围失败: {e}")
            return False
    
    async def _get_all_user_roles(self, user_id: str) -> Set[str]:
        """获取用户的所有角色（包括继承的角色）"""
        try:
            all_roles = set()
            direct_roles = self.user_roles.get(user_id, set())
            
            # 使用队列进行广度优先搜索
            queue = list(direct_roles)
            visited = set()
            
            while queue:
                role_id = queue.pop(0)
                if role_id in visited:
                    continue
                
                visited.add(role_id)
                all_roles.add(role_id)
                
                # 添加父角色
                if role_id in self.roles:
                    role = self.roles[role_id]
                    for parent_role_id in role.parent_roles:
                        if parent_role_id not in visited:
                            queue.append(parent_role_id)
            
            return all_roles
            
        except Exception as e:
            self.logger.error(f"获取用户所有角色失败: {e}")
            return set()
    
    def _get_cache_key(self, request: AccessRequest) -> str:
        """生成缓存键"""
        return f"{request.user_id}:{request.resource_type.value}:{request.resource_id}:{request.permission_type.value}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[AccessResult]:
        """获取缓存结果"""
        try:
            if cache_key in self.permission_cache:
                cache_entry = self.permission_cache[cache_key]
                if datetime.now() < cache_entry["expires_at"]:
                    return cache_entry["result"]
                else:
                    del self.permission_cache[cache_key]
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取缓存结果失败: {e}")
            return None
    
    def _cache_result(self, cache_key: str, result: AccessResult) -> None:
        """缓存结果"""
        try:
            self.permission_cache[cache_key] = {
                "result": result,
                "expires_at": datetime.now() + timedelta(seconds=self.cache_ttl)
            }
            
        except Exception as e:
            self.logger.error(f"缓存结果失败: {e}")
    
    def _clear_cache(self) -> None:
        """清除所有缓存"""
        self.permission_cache.clear()
    
    def _clear_user_cache(self, user_id: str) -> None:
        """清除用户相关缓存"""
        try:
            keys_to_remove = [key for key in self.permission_cache.keys() if key.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self.permission_cache[key]
                
        except Exception as e:
            self.logger.error(f"清除用户缓存失败: {e}")
    
    async def _log_access(self, request: AccessRequest, result: AccessResult) -> None:
        """记录访问日志"""
        try:
            log_entry = {
                "timestamp": request.timestamp.isoformat(),
                "user_id": request.user_id,
                "resource_type": request.resource_type.value,
                "resource_id": request.resource_id,
                "permission_type": request.permission_type.value,
                "decision": result.decision.value,
                "reason": result.reason,
                "context": request.context
            }
            
            self.access_logs.append(log_entry)
            
            # 限制日志条目数量
            if len(self.access_logs) > self.max_log_entries:
                self.access_logs = self.access_logs[-self.max_log_entries:]
            
        except Exception as e:
            self.logger.error(f"记录访问日志失败: {e}")
    
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
    
    async def _load_default_permissions(self) -> None:
        """加载默认权限"""
        try:
            default_permissions = [
                # 服务权限
                Permission("service_read", "服务读取", "读取服务信息", ResourceType.SERVICE, PermissionType.READ),
                Permission("service_write", "服务写入", "修改服务配置", ResourceType.SERVICE, PermissionType.WRITE),
                Permission("service_execute", "服务执行", "执行服务操作", ResourceType.SERVICE, PermissionType.EXECUTE),
                Permission("service_admin", "服务管理", "完全管理服务", ResourceType.SERVICE, PermissionType.ADMIN),
                
                # 工具权限
                Permission("tool_read", "工具读取", "读取工具信息", ResourceType.TOOL, PermissionType.READ),
                Permission("tool_execute", "工具执行", "执行工具操作", ResourceType.TOOL, PermissionType.EXECUTE),
                Permission("tool_admin", "工具管理", "完全管理工具", ResourceType.TOOL, PermissionType.ADMIN),
                
                # 数据权限
                Permission("data_read", "数据读取", "读取数据", ResourceType.DATA, PermissionType.READ),
                Permission("data_write", "数据写入", "写入数据", ResourceType.DATA, PermissionType.WRITE),
                Permission("data_delete", "数据删除", "删除数据", ResourceType.DATA, PermissionType.DELETE),
                
                # 配置权限
                Permission("config_read", "配置读取", "读取配置", ResourceType.CONFIG, PermissionType.READ),
                Permission("config_write", "配置写入", "修改配置", ResourceType.CONFIG, PermissionType.WRITE),
                
                # 用户权限
                Permission("user_read", "用户读取", "读取用户信息", ResourceType.USER, PermissionType.READ),
                Permission("user_write", "用户写入", "修改用户信息", ResourceType.USER, PermissionType.WRITE),
                Permission("user_admin", "用户管理", "完全管理用户", ResourceType.USER, PermissionType.ADMIN),
            ]
            
            for permission in default_permissions:
                await self.add_permission(permission)
            
            self.logger.info(f"加载了 {len(default_permissions)} 个默认权限")
            
        except Exception as e:
            self.logger.error(f"加载默认权限失败: {e}")
    
    async def _load_default_roles(self) -> None:
        """加载默认角色"""
        try:
            default_roles = [
                # 管理员角色
                Role(
                    role_id="admin",
                    name="管理员",
                    description="系统管理员，拥有所有权限",
                    permissions={
                        "service_admin", "tool_admin", "data_read", "data_write", "data_delete",
                        "config_read", "config_write", "user_admin"
                    }
                ),
                
                # 开发者角色
                Role(
                    role_id="developer",
                    name="开发者",
                    description="开发人员，拥有开发相关权限",
                    permissions={
                        "service_read", "service_write", "service_execute",
                        "tool_read", "tool_execute", "data_read", "data_write",
                        "config_read"
                    }
                ),
                
                # 操作员角色
                Role(
                    role_id="operator",
                    name="操作员",
                    description="系统操作员，拥有运维权限",
                    permissions={
                        "service_read", "service_execute", "tool_read", "tool_execute",
                        "data_read", "config_read"
                    }
                ),
                
                # 查看者角色
                Role(
                    role_id="viewer",
                    name="查看者",
                    description="只读用户，只能查看信息",
                    permissions={
                        "service_read", "tool_read", "data_read", "config_read"
                    }
                ),
                
                # 服务角色
                Role(
                    role_id="service",
                    name="服务",
                    description="服务账户，用于服务间通信",
                    permissions={
                        "service_read", "service_execute", "tool_read", "tool_execute",
                        "data_read", "data_write"
                    }
                ),
                
                # 访客角色
                Role(
                    role_id="guest",
                    name="访客",
                    description="访客用户，最小权限",
                    permissions={"service_read", "tool_read"}
                )
            ]
            
            for role in default_roles:
                await self.add_role(role)
            
            self.logger.info(f"加载了 {len(default_roles)} 个默认角色")
            
        except Exception as e:
            self.logger.error(f"加载默认角色失败: {e}")
    
    async def _load_default_policies(self) -> None:
        """加载默认策略"""
        try:
            default_policies = [
                # 管理员策略
                AccessPolicy(
                    policy_id="admin_policy",
                    name="管理员策略",
                    description="管理员拥有所有权限",
                    rules=[
                        {
                            "users": ["admin"],
                            "resources": "*",
                            "permissions": "*",
                            "action": "allow"
                        }
                    ],
                    priority=1000
                ),
                
                # 时间限制策略
                AccessPolicy(
                    policy_id="time_restriction",
                    name="时间限制策略",
                    description="工作时间外限制访问",
                    rules=[
                        {
                            "resources": "service:*",
                            "permissions": ["write", "delete", "admin"],
                            "conditions": {
                                "time_range": {"start": "09:00", "end": "18:00"}
                            },
                            "action": "allow"
                        },
                        {
                            "resources": "service:*",
                            "permissions": ["write", "delete", "admin"],
                            "action": "deny"
                        }
                    ],
                    priority=500
                ),
                
                # IP限制策略
                AccessPolicy(
                    policy_id="ip_restriction",
                    name="IP限制策略",
                    description="限制特定IP访问敏感资源",
                    rules=[
                        {
                            "resources": "config:*",
                            "permissions": ["write", "admin"],
                            "conditions": {
                                "ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"]
                            },
                            "action": "allow"
                        },
                        {
                            "resources": "config:*",
                            "permissions": ["write", "admin"],
                            "action": "deny"
                        }
                    ],
                    priority=800
                )
            ]
            
            for policy in default_policies:
                await self.add_policy(policy)
            
            self.logger.info(f"加载了 {len(default_policies)} 个默认策略")
            
        except Exception as e:
            self.logger.error(f"加载默认策略失败: {e}")
    
    async def _save_permissions(self) -> None:
        """保存权限数据"""
        try:
            # 这里可以保存权限数据到文件或数据库
            self.logger.debug("权限数据已保存")
        except Exception as e:
            self.logger.error(f"保存权限数据失败: {e}")
    
    async def _save_roles(self) -> None:
        """保存角色数据"""
        try:
            # 这里可以保存角色数据到文件或数据库
            self.logger.debug("角色数据已保存")
        except Exception as e:
            self.logger.error(f"保存角色数据失败: {e}")
    
    async def _save_policies(self) -> None:
        """保存策略数据"""
        try:
            # 这里可以保存策略数据到文件或数据库
            self.logger.debug("策略数据已保存")
        except Exception as e:
            self.logger.error(f"保存策略数据失败: {e}")
    
    async def _background_tasks(self) -> None:
        """后台任务"""
        while self.is_running:
            try:
                # 清理过期缓存
                await self._cleanup_expired_cache()
                
                # 清理旧的访问日志
                await self._cleanup_old_logs()
                
                # 等待下次执行
                await asyncio.sleep(300)  # 5分钟
                
            except Exception as e:
                self.logger.error(f"后台任务执行失败: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_cache(self) -> None:
        """清理过期缓存"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, cache_entry in self.permission_cache.items():
                if current_time >= cache_entry["expires_at"]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.permission_cache[key]
            
            if expired_keys:
                self.logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")
                
        except Exception as e:
            self.logger.error(f"清理过期缓存失败: {e}")
    
    async def _cleanup_old_logs(self) -> None:
        """清理旧的访问日志"""
        try:
            if len(self.access_logs) > self.max_log_entries:
                self.access_logs = self.access_logs[-self.max_log_entries:]
                self.logger.debug("清理了旧的访问日志")
                
        except Exception as e:
            self.logger.error(f"清理旧的访问日志失败: {e}")

