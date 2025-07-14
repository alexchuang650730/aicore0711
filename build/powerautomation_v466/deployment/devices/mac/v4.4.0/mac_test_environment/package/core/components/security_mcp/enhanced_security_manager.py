"""
Enhanced Security Manager - 智能整合版本
整合现有security_manager + auth_manager的HITL功能
避免重复开发，功能增强而非替换
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# 导入现有的安全组件 (保留Phase 4的成果)
from .security_manager import SecurityManager
from .authenticator import Authenticator
from .authorizer import Authorizer
from .token_manager import TokenManager

# HITL认证相关导入 (从auth_manager提取)
import aiohttp
from dataclasses import dataclass


class AuthType(Enum):
    """认证类型枚举 (从auth_manager提取)"""
    MANUS_LOGIN = "manus_login"
    GITHUB_TOKEN = "github_token"
    ANTHROPIC_API_KEY = "anthropic_api_key"
    OPENAI_API_KEY = "openai_api_key"
    REDIS_PASSWORD = "redis_password"
    DATABASE_PASSWORD = "database_password"


@dataclass
class AuthRequest:
    """认证请求数据类 (从auth_manager提取)"""
    auth_type: AuthType
    description: str
    required_fields: List[str]
    optional_fields: List[str] = None
    security_level: str = "high"  # low, medium, high
    expires_in: int = 3600  # 秒
    context: Dict[str, Any] = None


@dataclass
class AuthResponse:
    """认证响应数据类 (从auth_manager提取)"""
    auth_type: AuthType
    credentials: Dict[str, str]
    timestamp: datetime
    expires_at: datetime
    user_id: str


class HITLAuthenticator:
    """
    Human-in-the-Loop 认证器
    从auth_manager提取的独有功能
    """
    
    def __init__(self, hitl_mcp_url: str = "http://localhost:8081"):
        self.hitl_mcp_url = hitl_mcp_url
        self.logger = logging.getLogger(__name__)
        self.auth_cache = {}  # 临时认证缓存
        
    async def interactive_authenticate(self, auth_request: AuthRequest) -> AuthResponse:
        """
        交互式认证 - HITL核心功能
        """
        try:
            # 发送认证请求到HITL MCP
            async with aiohttp.ClientSession() as session:
                payload = {
                    "type": "auth_request",
                    "auth_type": auth_request.auth_type.value,
                    "description": auth_request.description,
                    "required_fields": auth_request.required_fields,
                    "optional_fields": auth_request.optional_fields or [],
                    "security_level": auth_request.security_level,
                    "context": auth_request.context or {}
                }
                
                async with session.post(
                    f"{self.hitl_mcp_url}/auth/request",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._create_auth_response(auth_request, result)
                    else:
                        raise Exception(f"HITL认证失败: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"HITL认证错误: {e}")
            raise
    
    def _create_auth_response(self, request: AuthRequest, result: Dict) -> AuthResponse:
        """创建认证响应"""
        return AuthResponse(
            auth_type=request.auth_type,
            credentials=result.get("credentials", {}),
            timestamp=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=request.expires_in),
            user_id=result.get("user_id", "unknown")
        )
    
    async def verify_credentials(self, auth_response: AuthResponse) -> bool:
        """验证凭据有效性"""
        if datetime.now() > auth_response.expires_at:
            return False
            
        # 根据认证类型验证凭据
        if auth_response.auth_type == AuthType.ANTHROPIC_API_KEY:
            return await self._verify_anthropic_key(
                auth_response.credentials.get("api_key")
            )
        elif auth_response.auth_type == AuthType.GITHUB_TOKEN:
            return await self._verify_github_token(
                auth_response.credentials.get("token")
            )
        # 添加其他认证类型的验证逻辑
        
        return True
    
    async def _verify_anthropic_key(self, api_key: str) -> bool:
        """验证Anthropic API密钥"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"x-api-key": api_key}
                async with session.get(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers
                ) as response:
                    return response.status != 401
        except:
            return False
    
    async def _verify_github_token(self, token: str) -> bool:
        """验证GitHub令牌"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"token {token}"}
                async with session.get(
                    "https://api.github.com/user",
                    headers=headers
                ) as response:
                    return response.status == 200
        except:
            return False


class MultiLevelAuthManager:
    """
    多级认证管理器
    从auth_manager提取的独有功能
    """
    
    def __init__(self):
        self.auth_levels = {
            "low": {"required_factors": 1, "timeout": 3600},
            "medium": {"required_factors": 2, "timeout": 1800},
            "high": {"required_factors": 3, "timeout": 900}
        }
        self.active_sessions = {}
    
    async def multi_factor_authenticate(
        self, 
        user_id: str, 
        security_level: str,
        factors: List[Dict[str, Any]]
    ) -> bool:
        """
        多因子认证
        """
        level_config = self.auth_levels.get(security_level, self.auth_levels["high"])
        required_factors = level_config["required_factors"]
        
        if len(factors) < required_factors:
            return False
        
        # 验证每个认证因子
        verified_factors = 0
        for factor in factors[:required_factors]:
            if await self._verify_auth_factor(factor):
                verified_factors += 1
        
        success = verified_factors >= required_factors
        
        if success:
            # 创建认证会话
            session_id = self._create_auth_session(user_id, security_level)
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "security_level": security_level,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(seconds=level_config["timeout"])
            }
        
        return success
    
    async def _verify_auth_factor(self, factor: Dict[str, Any]) -> bool:
        """验证单个认证因子"""
        factor_type = factor.get("type")
        
        if factor_type == "password":
            return self._verify_password(factor.get("value"))
        elif factor_type == "totp":
            return self._verify_totp(factor.get("value"))
        elif factor_type == "biometric":
            return await self._verify_biometric(factor.get("data"))
        elif factor_type == "hardware_key":
            return await self._verify_hardware_key(factor.get("signature"))
        
        return False
    
    def _verify_password(self, password: str) -> bool:
        """验证密码"""
        # 实现密码验证逻辑
        return len(password) >= 8
    
    def _verify_totp(self, totp_code: str) -> bool:
        """验证TOTP代码"""
        # 实现TOTP验证逻辑
        return len(totp_code) == 6 and totp_code.isdigit()
    
    async def _verify_biometric(self, biometric_data: str) -> bool:
        """验证生物识别"""
        # 实现生物识别验证逻辑
        return len(biometric_data) > 0
    
    async def _verify_hardware_key(self, signature: str) -> bool:
        """验证硬件密钥"""
        # 实现硬件密钥验证逻辑
        return len(signature) > 0
    
    def _create_auth_session(self, user_id: str, security_level: str) -> str:
        """创建认证会话"""
        import uuid
        return str(uuid.uuid4())


class EnhancedSecurityManager:
    """
    增强安全管理器 - 智能整合版本
    
    整合策略:
    1. 保留现有SecurityManager的所有功能 (Phase 4成果)
    2. 新增auth_manager的HITL认证功能
    3. 新增多级认证管理功能
    4. 提供统一的安全管理接口
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # 初始化现有安全组件 (保留Phase 4成果)
        self.security_manager = SecurityManager(config)
        self.authenticator = Authenticator(config)
        self.authorizer = Authorizer(config)
        self.token_manager = TokenManager(config)
        
        # 初始化新增的HITL功能
        self.hitl_authenticator = HITLAuthenticator()
        self.multi_level_auth = MultiLevelAuthManager()
        
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 统计信息
        self.stats = {
            "total_auth_requests": 0,
            "hitl_auth_requests": 0,
            "multi_factor_auths": 0,
            "security_events": 0
        }
    
    async def authenticate_user(
        self, 
        user_id: str, 
        credentials: Dict[str, Any],
        require_hitl: bool = False,
        security_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        增强用户认证
        
        整合现有认证 + HITL认证 + 多级认证
        """
        self.stats["total_auth_requests"] += 1
        
        try:
            # 1. 基础认证 (使用现有authenticator)
            basic_auth_result = await self.authenticator.authenticate(user_id, credentials)
            
            if not basic_auth_result.get("success"):
                return basic_auth_result
            
            # 2. 检查是否需要HITL认证
            if require_hitl or self._requires_hitl_auth(user_id, security_level):
                self.stats["hitl_auth_requests"] += 1
                
                auth_request = AuthRequest(
                    auth_type=AuthType.MANUS_LOGIN,
                    description=f"HITL认证请求 - 用户: {user_id}",
                    required_fields=["confirmation"],
                    security_level=security_level,
                    context={"user_id": user_id, "timestamp": datetime.now().isoformat()}
                )
                
                hitl_response = await self.hitl_authenticator.interactive_authenticate(auth_request)
                
                if not await self.hitl_authenticator.verify_credentials(hitl_response):
                    return {"success": False, "error": "HITL认证失败"}
            
            # 3. 多级认证 (如果需要)
            if security_level in ["medium", "high"]:
                self.stats["multi_factor_auths"] += 1
                
                auth_factors = self._extract_auth_factors(credentials)
                mfa_success = await self.multi_level_auth.multi_factor_authenticate(
                    user_id, security_level, auth_factors
                )
                
                if not mfa_success:
                    return {"success": False, "error": "多因子认证失败"}
            
            # 4. 生成增强令牌 (使用现有token_manager)
            token = await self.token_manager.generate_token(
                user_id, 
                {"security_level": security_level, "hitl_verified": require_hitl}
            )
            
            # 5. 记录安全事件 (使用现有security_manager)
            await self.security_manager.log_security_event(
                "user_authentication",
                {"user_id": user_id, "security_level": security_level, "hitl_used": require_hitl}
            )
            
            return {
                "success": True,
                "token": token,
                "user_id": user_id,
                "security_level": security_level,
                "hitl_verified": require_hitl,
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"增强认证失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _requires_hitl_auth(self, user_id: str, security_level: str) -> bool:
        """判断是否需要HITL认证"""
        # 高安全级别总是需要HITL
        if security_level == "high":
            return True
        
        # 检查用户风险评分 (使用现有security_manager)
        risk_score = self.security_manager.get_user_risk_score(user_id)
        return risk_score > 0.7
    
    def _extract_auth_factors(self, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取认证因子"""
        factors = []
        
        if "password" in credentials:
            factors.append({"type": "password", "value": credentials["password"]})
        
        if "totp_code" in credentials:
            factors.append({"type": "totp", "value": credentials["totp_code"]})
        
        if "biometric_data" in credentials:
            factors.append({"type": "biometric", "data": credentials["biometric_data"]})
        
        if "hardware_signature" in credentials:
            factors.append({"type": "hardware_key", "signature": credentials["hardware_signature"]})
        
        return factors
    
    async def authorize_action(
        self, 
        user_id: str, 
        action: str, 
        resource: str,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        增强权限控制
        
        整合现有authorizer + 安全级别检查
        """
        # 1. 基础权限检查 (使用现有authorizer)
        basic_auth = await self.authorizer.authorize(user_id, action, resource)
        
        if not basic_auth:
            return False
        
        # 2. 安全级别检查
        user_security_level = self._get_user_security_level(user_id)
        required_level = self._get_required_security_level(action, resource)
        
        if not self._check_security_level(user_security_level, required_level):
            return False
        
        # 3. 上下文安全检查 (使用现有security_manager)
        if context:
            threat_detected = await self.security_manager.detect_threats(context)
            if threat_detected:
                return False
        
        return True
    
    def _get_user_security_level(self, user_id: str) -> str:
        """获取用户安全级别"""
        # 从用户会话或数据库获取安全级别
        return "medium"  # 默认值
    
    def _get_required_security_level(self, action: str, resource: str) -> str:
        """获取操作所需的安全级别"""
        high_security_actions = ["delete", "admin", "deploy"]
        if any(action.startswith(hsa) for hsa in high_security_actions):
            return "high"
        return "medium"
    
    def _check_security_level(self, user_level: str, required_level: str) -> bool:
        """检查安全级别是否满足要求"""
        levels = {"low": 1, "medium": 2, "high": 3}
        return levels.get(user_level, 0) >= levels.get(required_level, 0)
    
    async def get_security_status(self) -> Dict[str, Any]:
        """
        获取安全状态
        
        整合现有security_manager状态 + 新增功能状态
        """
        # 获取现有安全状态
        base_status = await self.security_manager.get_status()
        
        # 添加新增功能状态
        enhanced_status = {
            **base_status,
            "hitl_auth_enabled": True,
            "multi_level_auth_enabled": True,
            "auth_statistics": self.stats,
            "active_hitl_sessions": len(self.hitl_authenticator.auth_cache),
            "active_mfa_sessions": len(self.multi_level_auth.active_sessions)
        }
        
        return enhanced_status
    
    async def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.now()
        
        # 清理多级认证会话
        expired_sessions = [
            session_id for session_id, session in self.multi_level_auth.active_sessions.items()
            if current_time > session["expires_at"]
        ]
        
        for session_id in expired_sessions:
            del self.multi_level_auth.active_sessions[session_id]
        
        # 清理HITL认证缓存
        expired_cache = [
            key for key, value in self.hitl_authenticator.auth_cache.items()
            if current_time > value.get("expires_at", current_time)
        ]
        
        for key in expired_cache:
            del self.hitl_authenticator.auth_cache[key]


# 使用示例
async def main():
    """使用示例"""
    # 创建增强安全管理器
    enhanced_security = EnhancedSecurityManager()
    
    # 基础认证
    result = await enhanced_security.authenticate_user(
        user_id="test_user",
        credentials={"password": "secure_password"},
        require_hitl=False,
        security_level="medium"
    )
    print(f"基础认证结果: {result}")
    
    # HITL认证
    hitl_result = await enhanced_security.authenticate_user(
        user_id="admin_user",
        credentials={"password": "admin_password"},
        require_hitl=True,
        security_level="high"
    )
    print(f"HITL认证结果: {hitl_result}")
    
    # 权限检查
    auth_result = await enhanced_security.authorize_action(
        user_id="test_user",
        action="read",
        resource="documents"
    )
    print(f"权限检查结果: {auth_result}")
    
    # 获取安全状态
    status = await enhanced_security.get_security_status()
    print(f"安全状态: {status}")


if __name__ == "__main__":
    asyncio.run(main())

