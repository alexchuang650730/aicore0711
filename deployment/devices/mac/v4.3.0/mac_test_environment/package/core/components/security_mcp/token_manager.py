"""
PowerAutomation 4.0 MCP令牌管理器

负责管理所有类型的令牌，包括访问令牌、刷新令牌、API密钥等的生命周期管理。
"""

import logging
import asyncio
import secrets
import time
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import jwt
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class TokenType(Enum):
    """令牌类型枚举"""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    API_KEY = "api_key"
    SESSION_TOKEN = "session_token"
    TEMPORARY_TOKEN = "temporary_token"
    SERVICE_TOKEN = "service_token"
    DELEGATION_TOKEN = "delegation_token"


class TokenStatus(Enum):
    """令牌状态枚举"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    PENDING = "pending"


class TokenScope(Enum):
    """令牌作用域枚举"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SERVICE = "service"
    LIMITED = "limited"
    FULL = "full"


@dataclass
class Token:
    """令牌对象"""
    token_id: str
    token_type: TokenType
    token_value: str
    user_id: str
    client_id: Optional[str] = None
    scopes: Set[TokenScope] = field(default_factory=set)
    status: TokenStatus = TokenStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    use_count: int = 0
    max_uses: Optional[int] = None
    ip_restrictions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenPolicy:
    """令牌策略"""
    policy_id: str
    name: str
    description: str
    token_types: List[TokenType] = field(default_factory=list)
    default_expiry: Optional[int] = None  # 秒
    max_expiry: Optional[int] = None  # 秒
    max_uses: Optional[int] = None
    require_refresh: bool = False
    ip_restrictions: bool = False
    scopes_required: List[TokenScope] = field(default_factory=list)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenUsage:
    """令牌使用记录"""
    usage_id: str
    token_id: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class TokenBlacklist:
    """令牌黑名单"""
    token_id: str
    token_hash: str
    revoked_at: datetime = field(default_factory=datetime.now)
    revoked_by: Optional[str] = None
    reason: str = ""
    expires_at: Optional[datetime] = None


class MCPTokenManager:
    """
    PowerAutomation 4.0 MCP令牌管理器
    
    功能：
    1. 令牌生命周期管理
    2. 多种令牌类型支持
    3. 令牌验证和刷新
    4. 令牌撤销和黑名单
    5. 令牌使用统计和审计
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化令牌管理器
        
        Args:
            config: 配置参数
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.is_running = False
        
        # 令牌存储
        self.tokens: Dict[str, Token] = {}
        self.token_by_value: Dict[str, str] = {}  # token_value -> token_id
        self.user_tokens: Dict[str, Set[str]] = {}  # user_id -> token_ids
        
        # 令牌策略
        self.token_policies: Dict[str, TokenPolicy] = {}
        
        # 令牌黑名单
        self.token_blacklist: Dict[str, TokenBlacklist] = {}
        
        # 令牌使用记录
        self.token_usage: List[TokenUsage] = []
        self.max_usage_records = self.config.get("max_usage_records", 100000)
        
        # 加密密钥
        self.encryption_key = self._init_encryption_key()
        self.jwt_secret = self.config.get("jwt_secret", secrets.token_urlsafe(32))
        self.jwt_algorithm = self.config.get("jwt_algorithm", "HS256")
        
        # 默认配置
        self.default_access_token_expiry = self.config.get("default_access_token_expiry", 3600)  # 1小时
        self.default_refresh_token_expiry = self.config.get("default_refresh_token_expiry", 30 * 24 * 3600)  # 30天
        self.default_api_key_expiry = self.config.get("default_api_key_expiry", 365 * 24 * 3600)  # 1年
        self.cleanup_interval = self.config.get("cleanup_interval", 3600)  # 1小时
        
        # 事件回调
        self.event_callbacks: Dict[str, List[callable]] = {
            "token_created": [],
            "token_used": [],
            "token_expired": [],
            "token_revoked": [],
            "token_refreshed": [],
            "suspicious_usage": []
        }
        
        self.logger.info("MCP令牌管理器初始化完成")
    
    async def start(self) -> None:
        """启动令牌管理器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动MCP令牌管理器...")
            
            # 加载默认令牌策略
            await self._load_default_policies()
            
            # 加载令牌数据
            await self._load_tokens()
            
            # 启动后台任务
            asyncio.create_task(self._background_tasks())
            
            self.is_running = True
            self.logger.info("MCP令牌管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"MCP令牌管理器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止令牌管理器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止MCP令牌管理器...")
            
            self.is_running = False
            
            # 保存令牌数据
            await self._save_tokens()
            
            # 保存使用记录
            await self._save_usage_records()
            
            self.logger.info("MCP令牌管理器已停止")
            
        except Exception as e:
            self.logger.error(f"MCP令牌管理器停止时出错: {e}")
    
    async def create_token(self, token_type: TokenType, user_id: str,
                          client_id: Optional[str] = None,
                          scopes: Optional[Set[TokenScope]] = None,
                          expires_in: Optional[int] = None,
                          max_uses: Optional[int] = None,
                          ip_restrictions: Optional[List[str]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Optional[Token]:
        """
        创建令牌
        
        Args:
            token_type: 令牌类型
            user_id: 用户ID
            client_id: 客户端ID
            scopes: 令牌作用域
            expires_in: 过期时间（秒）
            max_uses: 最大使用次数
            ip_restrictions: IP限制
            metadata: 元数据
            
        Returns:
            Optional[Token]: 创建的令牌
        """
        try:
            # 生成令牌ID和值
            token_id = self._generate_token_id()
            token_value = await self._generate_token_value(token_type, user_id, client_id)
            
            # 确定过期时间
            if expires_in is None:
                expires_in = self._get_default_expiry(token_type)
            
            expires_at = None
            if expires_in and expires_in > 0:
                expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # 创建令牌对象
            token = Token(
                token_id=token_id,
                token_type=token_type,
                token_value=token_value,
                user_id=user_id,
                client_id=client_id,
                scopes=scopes or set(),
                expires_at=expires_at,
                max_uses=max_uses,
                ip_restrictions=ip_restrictions or [],
                metadata=metadata or {}
            )
            
            # 存储令牌
            self.tokens[token_id] = token
            self.token_by_value[token_value] = token_id
            
            if user_id not in self.user_tokens:
                self.user_tokens[user_id] = set()
            self.user_tokens[user_id].add(token_id)
            
            # 触发事件
            await self._trigger_event("token_created", token)
            
            self.logger.info(f"令牌创建成功: {token_type.value} - {token_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"创建令牌失败: {e}")
            return None
    
    async def validate_token(self, token_value: str,
                           required_scopes: Optional[Set[TokenScope]] = None,
                           ip_address: Optional[str] = None,
                           resource: Optional[str] = None) -> Optional[Token]:
        """
        验证令牌
        
        Args:
            token_value: 令牌值
            required_scopes: 需要的作用域
            ip_address: 客户端IP地址
            resource: 访问的资源
            
        Returns:
            Optional[Token]: 有效的令牌对象
        """
        try:
            # 查找令牌
            token_id = self.token_by_value.get(token_value)
            if not token_id:
                return None
            
            token = self.tokens.get(token_id)
            if not token:
                return None
            
            # 检查令牌状态
            if token.status != TokenStatus.ACTIVE:
                return None
            
            # 检查是否在黑名单中
            if await self._is_token_blacklisted(token):
                return None
            
            # 检查过期时间
            if token.expires_at and datetime.now() > token.expires_at:
                await self._expire_token(token)
                return None
            
            # 检查使用次数限制
            if token.max_uses and token.use_count >= token.max_uses:
                await self._expire_token(token)
                return None
            
            # 检查IP限制
            if token.ip_restrictions and ip_address:
                if not self._check_ip_restrictions(ip_address, token.ip_restrictions):
                    return None
            
            # 检查作用域
            if required_scopes:
                if not required_scopes.issubset(token.scopes):
                    return None
            
            # 更新使用统计
            await self._update_token_usage(token, ip_address, resource)
            
            # 触发事件
            await self._trigger_event("token_used", {
                "token": token,
                "ip_address": ip_address,
                "resource": resource
            })
            
            return token
            
        except Exception as e:
            self.logger.error(f"验证令牌失败: {e}")
            return None
    
    async def refresh_token(self, refresh_token_value: str,
                           client_id: Optional[str] = None) -> Optional[Tuple[Token, Token]]:
        """
        刷新令牌
        
        Args:
            refresh_token_value: 刷新令牌值
            client_id: 客户端ID
            
        Returns:
            Optional[Tuple[Token, Token]]: (新访问令牌, 新刷新令牌)
        """
        try:
            # 验证刷新令牌
            refresh_token = await self.validate_token(refresh_token_value)
            if not refresh_token or refresh_token.token_type != TokenType.REFRESH_TOKEN:
                return None
            
            # 检查客户端ID
            if client_id and refresh_token.client_id != client_id:
                return None
            
            # 撤销旧的刷新令牌
            await self.revoke_token(refresh_token.token_id, "token_refresh")
            
            # 创建新的访问令牌
            new_access_token = await self.create_token(
                token_type=TokenType.ACCESS_TOKEN,
                user_id=refresh_token.user_id,
                client_id=refresh_token.client_id,
                scopes=refresh_token.scopes,
                metadata=refresh_token.metadata
            )
            
            # 创建新的刷新令牌
            new_refresh_token = await self.create_token(
                token_type=TokenType.REFRESH_TOKEN,
                user_id=refresh_token.user_id,
                client_id=refresh_token.client_id,
                scopes=refresh_token.scopes,
                metadata=refresh_token.metadata
            )
            
            if new_access_token and new_refresh_token:
                # 触发事件
                await self._trigger_event("token_refreshed", {
                    "old_refresh_token": refresh_token,
                    "new_access_token": new_access_token,
                    "new_refresh_token": new_refresh_token
                })
                
                self.logger.info(f"令牌刷新成功: 用户 {refresh_token.user_id}")
                return new_access_token, new_refresh_token
            
            return None
            
        except Exception as e:
            self.logger.error(f"刷新令牌失败: {e}")
            return None
    
    async def revoke_token(self, token_id: str, reason: str = "",
                          revoked_by: Optional[str] = None) -> bool:
        """
        撤销令牌
        
        Args:
            token_id: 令牌ID
            reason: 撤销原因
            revoked_by: 撤销者
            
        Returns:
            bool: 撤销是否成功
        """
        try:
            if token_id not in self.tokens:
                return False
            
            token = self.tokens[token_id]
            
            # 更新令牌状态
            token.status = TokenStatus.REVOKED
            
            # 添加到黑名单
            token_hash = self._hash_token(token.token_value)
            blacklist_entry = TokenBlacklist(
                token_id=token_id,
                token_hash=token_hash,
                revoked_by=revoked_by,
                reason=reason,
                expires_at=token.expires_at
            )
            self.token_blacklist[token_id] = blacklist_entry
            
            # 从索引中移除
            if token.token_value in self.token_by_value:
                del self.token_by_value[token.token_value]
            
            # 触发事件
            await self._trigger_event("token_revoked", {
                "token": token,
                "reason": reason,
                "revoked_by": revoked_by
            })
            
            self.logger.info(f"令牌已撤销: {token_id} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"撤销令牌失败: {e}")
            return False
    
    async def revoke_user_tokens(self, user_id: str, token_type: Optional[TokenType] = None,
                                reason: str = "", revoked_by: Optional[str] = None) -> int:
        """
        撤销用户的所有令牌
        
        Args:
            user_id: 用户ID
            token_type: 令牌类型（可选）
            reason: 撤销原因
            revoked_by: 撤销者
            
        Returns:
            int: 撤销的令牌数量
        """
        try:
            if user_id not in self.user_tokens:
                return 0
            
            token_ids = list(self.user_tokens[user_id])
            revoked_count = 0
            
            for token_id in token_ids:
                if token_id in self.tokens:
                    token = self.tokens[token_id]
                    
                    # 检查令牌类型过滤
                    if token_type and token.token_type != token_type:
                        continue
                    
                    # 撤销令牌
                    if await self.revoke_token(token_id, reason, revoked_by):
                        revoked_count += 1
            
            self.logger.info(f"用户令牌已撤销: {user_id} - {revoked_count} 个")
            return revoked_count
            
        except Exception as e:
            self.logger.error(f"撤销用户令牌失败: {e}")
            return 0
    
    async def get_user_tokens(self, user_id: str,
                             token_type: Optional[TokenType] = None,
                             status: Optional[TokenStatus] = None) -> List[Token]:
        """
        获取用户的令牌
        
        Args:
            user_id: 用户ID
            token_type: 令牌类型过滤
            status: 令牌状态过滤
            
        Returns:
            List[Token]: 令牌列表
        """
        try:
            if user_id not in self.user_tokens:
                return []
            
            tokens = []
            for token_id in self.user_tokens[user_id]:
                if token_id in self.tokens:
                    token = self.tokens[token_id]
                    
                    # 应用过滤条件
                    if token_type and token.token_type != token_type:
                        continue
                    
                    if status and token.status != status:
                        continue
                    
                    tokens.append(token)
            
            return tokens
            
        except Exception as e:
            self.logger.error(f"获取用户令牌失败: {e}")
            return []
    
    async def get_token_usage(self, token_id: str, limit: int = 100) -> List[TokenUsage]:
        """
        获取令牌使用记录
        
        Args:
            token_id: 令牌ID
            limit: 返回数量限制
            
        Returns:
            List[TokenUsage]: 使用记录列表
        """
        try:
            usage_records = []
            
            for usage in reversed(self.token_usage):
                if usage.token_id == token_id:
                    usage_records.append(usage)
                    
                    if len(usage_records) >= limit:
                        break
            
            return usage_records
            
        except Exception as e:
            self.logger.error(f"获取令牌使用记录失败: {e}")
            return []
    
    async def get_token_statistics(self) -> Dict[str, Any]:
        """
        获取令牌统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            now = datetime.now()
            
            # 按类型统计
            type_stats = {}
            status_stats = {}
            
            for token in self.tokens.values():
                # 类型统计
                token_type = token.token_type.value
                if token_type not in type_stats:
                    type_stats[token_type] = 0
                type_stats[token_type] += 1
                
                # 状态统计
                status = token.status.value
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1
            
            # 过期统计
            expired_count = 0
            expiring_soon_count = 0  # 24小时内过期
            
            for token in self.tokens.values():
                if token.expires_at:
                    if now > token.expires_at:
                        expired_count += 1
                    elif now + timedelta(hours=24) > token.expires_at:
                        expiring_soon_count += 1
            
            statistics = {
                "total_tokens": len(self.tokens),
                "active_tokens": len([t for t in self.tokens.values() if t.status == TokenStatus.ACTIVE]),
                "expired_tokens": expired_count,
                "expiring_soon": expiring_soon_count,
                "revoked_tokens": len([t for t in self.tokens.values() if t.status == TokenStatus.REVOKED]),
                "blacklisted_tokens": len(self.token_blacklist),
                "type_distribution": type_stats,
                "status_distribution": status_stats,
                "total_usage_records": len(self.token_usage),
                "last_updated": now.isoformat()
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"获取令牌统计信息失败: {e}")
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
    
    async def _generate_token_value(self, token_type: TokenType, user_id: str,
                                   client_id: Optional[str] = None) -> str:
        """生成令牌值"""
        try:
            if token_type in [TokenType.ACCESS_TOKEN, TokenType.SESSION_TOKEN]:
                # 生成JWT令牌
                payload = {
                    "user_id": user_id,
                    "client_id": client_id,
                    "token_type": token_type.value,
                    "iat": int(time.time()),
                    "jti": secrets.token_urlsafe(16)
                }
                
                return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            elif token_type == TokenType.API_KEY:
                # 生成API密钥格式的令牌
                prefix = "pa_"  # PowerAutomation prefix
                key_part = secrets.token_urlsafe(32)
                return f"{prefix}{key_part}"
            
            else:
                # 生成随机令牌
                return secrets.token_urlsafe(32)
                
        except Exception as e:
            self.logger.error(f"生成令牌值失败: {e}")
            return secrets.token_urlsafe(32)
    
    def _generate_token_id(self) -> str:
        """生成令牌ID"""
        import uuid
        return f"token_{uuid.uuid4().hex[:16]}"
    
    def _get_default_expiry(self, token_type: TokenType) -> int:
        """获取默认过期时间"""
        if token_type == TokenType.ACCESS_TOKEN:
            return self.default_access_token_expiry
        elif token_type == TokenType.REFRESH_TOKEN:
            return self.default_refresh_token_expiry
        elif token_type == TokenType.API_KEY:
            return self.default_api_key_expiry
        elif token_type == TokenType.SESSION_TOKEN:
            return self.default_access_token_expiry
        elif token_type == TokenType.TEMPORARY_TOKEN:
            return 300  # 5分钟
        else:
            return self.default_access_token_expiry
    
    def _hash_token(self, token_value: str) -> str:
        """哈希令牌值"""
        return hashlib.sha256(token_value.encode()).hexdigest()
    
    def _check_ip_restrictions(self, ip_address: str, restrictions: List[str]) -> bool:
        """检查IP限制"""
        try:
            import ipaddress
            
            ip_obj = ipaddress.ip_address(ip_address)
            
            for restriction in restrictions:
                if "/" in restriction:
                    # CIDR格式
                    network = ipaddress.ip_network(restriction, strict=False)
                    if ip_obj in network:
                        return True
                else:
                    # 单个IP
                    if str(ip_obj) == restriction:
                        return True
            
            return len(restrictions) == 0  # 如果没有限制，则允许
            
        except Exception as e:
            self.logger.error(f"检查IP限制失败: {e}")
            return False
    
    def _init_encryption_key(self) -> Fernet:
        """初始化加密密钥"""
        try:
            key_material = self.config.get("encryption_key")
            if not key_material:
                key_material = secrets.token_bytes(32)
            
            if isinstance(key_material, str):
                key_material = key_material.encode()
            
            # 使用PBKDF2派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'powerautomation_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_material))
            return Fernet(key)
            
        except Exception as e:
            self.logger.error(f"初始化加密密钥失败: {e}")
            # 生成临时密钥
            key = Fernet.generate_key()
            return Fernet(key)
    
    async def _is_token_blacklisted(self, token: Token) -> bool:
        """检查令牌是否在黑名单中"""
        try:
            # 检查令牌ID黑名单
            if token.token_id in self.token_blacklist:
                return True
            
            # 检查令牌哈希黑名单
            token_hash = self._hash_token(token.token_value)
            for blacklist_entry in self.token_blacklist.values():
                if blacklist_entry.token_hash == token_hash:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查令牌黑名单失败: {e}")
            return False
    
    async def _expire_token(self, token: Token) -> None:
        """使令牌过期"""
        try:
            token.status = TokenStatus.EXPIRED
            
            # 从索引中移除
            if token.token_value in self.token_by_value:
                del self.token_by_value[token.token_value]
            
            # 触发事件
            await self._trigger_event("token_expired", token)
            
            self.logger.info(f"令牌已过期: {token.token_id}")
            
        except Exception as e:
            self.logger.error(f"使令牌过期失败: {e}")
    
    async def _update_token_usage(self, token: Token, ip_address: Optional[str] = None,
                                 resource: Optional[str] = None) -> None:
        """更新令牌使用统计"""
        try:
            # 更新令牌使用计数
            token.use_count += 1
            token.last_used = datetime.now()
            
            # 记录使用记录
            usage = TokenUsage(
                usage_id=f"usage_{secrets.token_urlsafe(8)}",
                token_id=token.token_id,
                user_id=token.user_id,
                ip_address=ip_address,
                resource=resource
            )
            
            self.token_usage.append(usage)
            
            # 限制使用记录数量
            if len(self.token_usage) > self.max_usage_records:
                self.token_usage = self.token_usage[-self.max_usage_records:]
            
            # 检测可疑使用
            await self._detect_suspicious_usage(token, usage)
            
        except Exception as e:
            self.logger.error(f"更新令牌使用统计失败: {e}")
    
    async def _detect_suspicious_usage(self, token: Token, usage: TokenUsage) -> None:
        """检测可疑使用"""
        try:
            # 检查短时间内大量使用
            recent_usage = [
                u for u in self.token_usage
                if (u.token_id == token.token_id and
                    u.timestamp > datetime.now() - timedelta(minutes=5))
            ]
            
            if len(recent_usage) > 100:  # 5分钟内超过100次使用
                await self._trigger_event("suspicious_usage", {
                    "token": token,
                    "usage": usage,
                    "reason": "high_frequency_usage",
                    "count": len(recent_usage)
                })
            
            # 检查异常IP使用
            if usage.ip_address:
                recent_ips = set(
                    u.ip_address for u in recent_usage
                    if u.ip_address and u.timestamp > datetime.now() - timedelta(hours=1)
                )
                
                if len(recent_ips) > 10:  # 1小时内来自超过10个不同IP
                    await self._trigger_event("suspicious_usage", {
                        "token": token,
                        "usage": usage,
                        "reason": "multiple_ip_usage",
                        "ip_count": len(recent_ips)
                    })
                    
        except Exception as e:
            self.logger.error(f"检测可疑使用失败: {e}")
    
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
    
    async def _load_default_policies(self) -> None:
        """加载默认令牌策略"""
        try:
            default_policies = [
                TokenPolicy(
                    policy_id="access_token_policy",
                    name="访问令牌策略",
                    description="访问令牌的默认策略",
                    token_types=[TokenType.ACCESS_TOKEN],
                    default_expiry=3600,  # 1小时
                    max_expiry=24 * 3600,  # 24小时
                    require_refresh=True
                ),
                
                TokenPolicy(
                    policy_id="refresh_token_policy",
                    name="刷新令牌策略",
                    description="刷新令牌的默认策略",
                    token_types=[TokenType.REFRESH_TOKEN],
                    default_expiry=30 * 24 * 3600,  # 30天
                    max_expiry=90 * 24 * 3600,  # 90天
                    require_refresh=False
                ),
                
                TokenPolicy(
                    policy_id="api_key_policy",
                    name="API密钥策略",
                    description="API密钥的默认策略",
                    token_types=[TokenType.API_KEY],
                    default_expiry=365 * 24 * 3600,  # 1年
                    max_expiry=2 * 365 * 24 * 3600,  # 2年
                    ip_restrictions=True
                ),
                
                TokenPolicy(
                    policy_id="service_token_policy",
                    name="服务令牌策略",
                    description="服务令牌的默认策略",
                    token_types=[TokenType.SERVICE_TOKEN],
                    default_expiry=7 * 24 * 3600,  # 7天
                    max_expiry=30 * 24 * 3600,  # 30天
                    scopes_required=[TokenScope.SERVICE]
                )
            ]
            
            for policy in default_policies:
                self.token_policies[policy.policy_id] = policy
            
            self.logger.info(f"加载了 {len(default_policies)} 个默认令牌策略")
            
        except Exception as e:
            self.logger.error(f"加载默认令牌策略失败: {e}")
    
    async def _load_tokens(self) -> None:
        """加载令牌数据"""
        try:
            # 这里可以从文件或数据库加载令牌数据
            self.logger.info(f"加载了 {len(self.tokens)} 个令牌")
        except Exception as e:
            self.logger.error(f"加载令牌数据失败: {e}")
    
    async def _save_tokens(self) -> None:
        """保存令牌数据"""
        try:
            # 这里可以保存令牌数据到文件或数据库
            self.logger.debug("令牌数据已保存")
        except Exception as e:
            self.logger.error(f"保存令牌数据失败: {e}")
    
    async def _save_usage_records(self) -> None:
        """保存使用记录"""
        try:
            # 这里可以保存使用记录到文件或数据库
            self.logger.debug("使用记录已保存")
        except Exception as e:
            self.logger.error(f"保存使用记录失败: {e}")
    
    async def _background_tasks(self) -> None:
        """后台任务"""
        while self.is_running:
            try:
                # 清理过期令牌
                await self._cleanup_expired_tokens()
                
                # 清理过期黑名单条目
                await self._cleanup_expired_blacklist()
                
                # 清理旧的使用记录
                await self._cleanup_old_usage_records()
                
                # 等待下次执行
                await asyncio.sleep(self.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"后台任务执行失败: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_tokens(self) -> None:
        """清理过期令牌"""
        try:
            current_time = datetime.now()
            expired_tokens = []
            
            for token_id, token in self.tokens.items():
                if (token.expires_at and current_time > token.expires_at and
                    token.status == TokenStatus.ACTIVE):
                    expired_tokens.append(token)
            
            for token in expired_tokens:
                await self._expire_token(token)
            
            if expired_tokens:
                self.logger.info(f"清理了 {len(expired_tokens)} 个过期令牌")
                
        except Exception as e:
            self.logger.error(f"清理过期令牌失败: {e}")
    
    async def _cleanup_expired_blacklist(self) -> None:
        """清理过期黑名单条目"""
        try:
            current_time = datetime.now()
            expired_entries = []
            
            for entry_id, entry in self.token_blacklist.items():
                if entry.expires_at and current_time > entry.expires_at:
                    expired_entries.append(entry_id)
            
            for entry_id in expired_entries:
                del self.token_blacklist[entry_id]
            
            if expired_entries:
                self.logger.info(f"清理了 {len(expired_entries)} 个过期黑名单条目")
                
        except Exception as e:
            self.logger.error(f"清理过期黑名单条目失败: {e}")
    
    async def _cleanup_old_usage_records(self) -> None:
        """清理旧的使用记录"""
        try:
            if len(self.token_usage) > self.max_usage_records:
                self.token_usage = self.token_usage[-self.max_usage_records:]
                self.logger.debug("清理了旧的使用记录")
                
        except Exception as e:
            self.logger.error(f"清理旧的使用记录失败: {e}")

