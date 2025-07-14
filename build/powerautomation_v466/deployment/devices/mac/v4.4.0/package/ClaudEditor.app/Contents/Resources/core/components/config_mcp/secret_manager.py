"""
PowerAutomation 4.0 密钥管理器

负责安全地管理密钥、密码、API密钥等敏感信息，支持多种存储后端和加密方式。
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class SecretInfo:
    """密钥信息"""
    secret_id: str
    secret_type: str = "generic"  # generic, api_key, password, certificate
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecretManager:
    """
    PowerAutomation 4.0 密钥管理器
    
    功能：
    1. 密钥安全存储和检索
    2. 多种存储后端支持
    3. 密钥加密和解密
    4. 密钥轮换和过期管理
    5. 访问控制和审计
    """
    
    def __init__(self, master_key: Optional[str] = None, storage_backend: str = "file"):
        """
        初始化密钥管理器
        
        Args:
            master_key: 主密钥，用于加密存储的密钥
            storage_backend: 存储后端 (file, memory, vault)
        """
        self.logger = logging.getLogger(__name__)
        self.storage_backend = storage_backend
        self.is_running = False
        
        # 加密组件
        self.cipher_suite = None
        self.master_key = master_key or self._generate_master_key()
        
        # 密钥存储
        self.secrets: Dict[str, str] = {}  # 加密后的密钥
        self.secret_info: Dict[str, SecretInfo] = {}  # 密钥元信息
        
        # 存储路径
        self.secrets_file = "secrets.enc"
        self.secrets_info_file = "secrets_info.json"
        
        # 访问记录
        self.access_log: List[Dict[str, Any]] = []
        
        self.logger.info("密钥管理器初始化完成")
    
    async def start(self) -> None:
        """启动密钥管理器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动密钥管理器...")
            
            # 初始化加密组件
            await self._initialize_encryption()
            
            # 加载存储的密钥
            await self._load_secrets()
            
            # 清理过期密钥
            await self._cleanup_expired_secrets()
            
            self.is_running = True
            self.logger.info("密钥管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"密钥管理器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止密钥管理器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止密钥管理器...")
            
            self.is_running = False
            
            # 保存密钥到存储
            await self._save_secrets()
            
            # 清理内存中的密钥
            self.secrets.clear()
            self.secret_info.clear()
            
            self.logger.info("密钥管理器已停止")
            
        except Exception as e:
            self.logger.error(f"密钥管理器停止时出错: {e}")
    
    async def store_secret(self, secret_id: str, secret_value: str, 
                          secret_type: str = "generic",
                          description: str = "",
                          expires_in_days: Optional[int] = None,
                          tags: Optional[List[str]] = None) -> bool:
        """
        存储密钥
        
        Args:
            secret_id: 密钥ID
            secret_value: 密钥值
            secret_type: 密钥类型
            description: 描述
            expires_in_days: 过期天数
            tags: 标签
            
        Returns:
            bool: 存储是否成功
        """
        try:
            # 加密密钥值
            encrypted_value = self._encrypt_secret(secret_value)
            
            # 计算过期时间
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # 创建密钥信息
            secret_info = SecretInfo(
                secret_id=secret_id,
                secret_type=secret_type,
                description=description,
                expires_at=expires_at,
                tags=tags or []
            )
            
            # 存储密钥
            self.secrets[secret_id] = encrypted_value
            self.secret_info[secret_id] = secret_info
            
            # 记录访问日志
            await self._log_access("store", secret_id)
            
            # 保存到存储
            await self._save_secrets()
            
            self.logger.info(f"存储密钥: {secret_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"存储密钥失败: {e}")
            return False
    
    def get_secret(self, secret_id: str) -> Optional[str]:
        """
        获取密钥
        
        Args:
            secret_id: 密钥ID
            
        Returns:
            Optional[str]: 密钥值
        """
        try:
            if secret_id not in self.secrets:
                self.logger.warning(f"密钥不存在: {secret_id}")
                return None
            
            # 检查密钥是否过期
            secret_info = self.secret_info.get(secret_id)
            if secret_info and secret_info.expires_at:
                if datetime.now() > secret_info.expires_at:
                    self.logger.warning(f"密钥已过期: {secret_id}")
                    return None
            
            # 解密密钥值
            encrypted_value = self.secrets[secret_id]
            secret_value = self._decrypt_secret(encrypted_value)
            
            # 记录访问日志
            asyncio.create_task(self._log_access("get", secret_id))
            
            return secret_value
            
        except Exception as e:
            self.logger.error(f"获取密钥失败: {e}")
            return None
    
    async def delete_secret(self, secret_id: str) -> bool:
        """
        删除密钥
        
        Args:
            secret_id: 密钥ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if secret_id not in self.secrets:
                self.logger.warning(f"密钥不存在: {secret_id}")
                return False
            
            # 删除密钥
            del self.secrets[secret_id]
            del self.secret_info[secret_id]
            
            # 记录访问日志
            await self._log_access("delete", secret_id)
            
            # 保存到存储
            await self._save_secrets()
            
            self.logger.info(f"删除密钥: {secret_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除密钥失败: {e}")
            return False
    
    async def update_secret(self, secret_id: str, secret_value: str) -> bool:
        """
        更新密钥
        
        Args:
            secret_id: 密钥ID
            secret_value: 新的密钥值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if secret_id not in self.secrets:
                self.logger.error(f"密钥不存在: {secret_id}")
                return False
            
            # 加密新的密钥值
            encrypted_value = self._encrypt_secret(secret_value)
            
            # 更新密钥
            self.secrets[secret_id] = encrypted_value
            
            # 更新密钥信息
            if secret_id in self.secret_info:
                self.secret_info[secret_id].updated_at = datetime.now()
            
            # 记录访问日志
            await self._log_access("update", secret_id)
            
            # 保存到存储
            await self._save_secrets()
            
            self.logger.info(f"更新密钥: {secret_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新密钥失败: {e}")
            return False
    
    def list_secrets(self, secret_type: Optional[str] = None,
                    tags: Optional[List[str]] = None) -> List[SecretInfo]:
        """
        列出密钥
        
        Args:
            secret_type: 密钥类型过滤
            tags: 标签过滤
            
        Returns:
            List[SecretInfo]: 密钥信息列表
        """
        try:
            result = []
            
            for secret_info in self.secret_info.values():
                # 类型过滤
                if secret_type and secret_info.secret_type != secret_type:
                    continue
                
                # 标签过滤
                if tags and not any(tag in secret_info.tags for tag in tags):
                    continue
                
                result.append(secret_info)
            
            return result
            
        except Exception as e:
            self.logger.error(f"列出密钥失败: {e}")
            return []
    
    def secret_exists(self, secret_id: str) -> bool:
        """
        检查密钥是否存在
        
        Args:
            secret_id: 密钥ID
            
        Returns:
            bool: 密钥是否存在
        """
        return secret_id in self.secrets
    
    async def rotate_secret(self, secret_id: str, new_secret_value: str) -> bool:
        """
        轮换密钥
        
        Args:
            secret_id: 密钥ID
            new_secret_value: 新的密钥值
            
        Returns:
            bool: 轮换是否成功
        """
        try:
            if not self.secret_exists(secret_id):
                self.logger.error(f"密钥不存在: {secret_id}")
                return False
            
            # 备份旧密钥
            old_secret_id = f"{secret_id}_backup_{int(datetime.now().timestamp())}"
            old_encrypted_value = self.secrets[secret_id]
            self.secrets[old_secret_id] = old_encrypted_value
            
            # 创建备份密钥信息
            old_info = self.secret_info[secret_id]
            backup_info = SecretInfo(
                secret_id=old_secret_id,
                secret_type=old_info.secret_type,
                description=f"Backup of {secret_id}",
                expires_at=datetime.now() + timedelta(days=30),  # 备份保留30天
                tags=old_info.tags + ["backup"]
            )
            self.secret_info[old_secret_id] = backup_info
            
            # 更新密钥
            await self.update_secret(secret_id, new_secret_value)
            
            # 记录访问日志
            await self._log_access("rotate", secret_id)
            
            self.logger.info(f"轮换密钥: {secret_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"轮换密钥失败: {e}")
            return False
    
    async def get_access_log(self, secret_id: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取访问日志
        
        Args:
            secret_id: 密钥ID过滤
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 访问日志
        """
        try:
            logs = self.access_log
            
            # 按密钥ID过滤
            if secret_id:
                logs = [log for log in logs if log.get("secret_id") == secret_id]
            
            # 按时间倒序排序并限制数量
            logs = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]
            
        except Exception as e:
            self.logger.error(f"获取访问日志失败: {e}")
            return []
    
    def _generate_master_key(self) -> str:
        """生成主密钥"""
        try:
            # 尝试从环境变量获取
            master_key = os.getenv("POWERAUTOMATION_MASTER_KEY")
            if master_key:
                return master_key
            
            # 生成新的主密钥
            key = Fernet.generate_key()
            master_key = base64.urlsafe_b64encode(key).decode()
            
            self.logger.warning("生成了新的主密钥，请将其保存到环境变量 POWERAUTOMATION_MASTER_KEY")
            return master_key
            
        except Exception as e:
            self.logger.error(f"生成主密钥失败: {e}")
            raise
    
    async def _initialize_encryption(self) -> None:
        """初始化加密组件"""
        try:
            # 从主密钥派生加密密钥
            password = self.master_key.encode()
            salt = b"powerautomation_salt"  # 在生产环境中应该使用随机盐
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.cipher_suite = Fernet(key)
            
            self.logger.debug("加密组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化加密组件失败: {e}")
            raise
    
    def _encrypt_secret(self, secret_value: str) -> str:
        """加密密钥值"""
        try:
            encrypted_bytes = self.cipher_suite.encrypt(secret_value.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
            
        except Exception as e:
            self.logger.error(f"加密密钥失败: {e}")
            raise
    
    def _decrypt_secret(self, encrypted_value: str) -> str:
        """解密密钥值"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
            
        except Exception as e:
            self.logger.error(f"解密密钥失败: {e}")
            raise
    
    async def _load_secrets(self) -> None:
        """加载存储的密钥"""
        try:
            if self.storage_backend == "file":
                await self._load_secrets_from_file()
            elif self.storage_backend == "memory":
                pass  # 内存存储不需要加载
            elif self.storage_backend == "vault":
                await self._load_secrets_from_vault()
            
            self.logger.info(f"加载了 {len(self.secrets)} 个密钥")
            
        except Exception as e:
            self.logger.error(f"加载密钥失败: {e}")
    
    async def _save_secrets(self) -> None:
        """保存密钥到存储"""
        try:
            if self.storage_backend == "file":
                await self._save_secrets_to_file()
            elif self.storage_backend == "memory":
                pass  # 内存存储不需要保存
            elif self.storage_backend == "vault":
                await self._save_secrets_to_vault()
            
        except Exception as e:
            self.logger.error(f"保存密钥失败: {e}")
    
    async def _load_secrets_from_file(self) -> None:
        """从文件加载密钥"""
        try:
            # 加载密钥数据
            if os.path.exists(self.secrets_file):
                with open(self.secrets_file, 'r') as f:
                    self.secrets = json.load(f)
            
            # 加载密钥信息
            if os.path.exists(self.secrets_info_file):
                with open(self.secrets_info_file, 'r') as f:
                    info_data = json.load(f)
                    
                    for secret_id, info_dict in info_data.items():
                        # 转换日期字符串为datetime对象
                        if info_dict.get("created_at"):
                            info_dict["created_at"] = datetime.fromisoformat(info_dict["created_at"])
                        if info_dict.get("updated_at"):
                            info_dict["updated_at"] = datetime.fromisoformat(info_dict["updated_at"])
                        if info_dict.get("expires_at"):
                            info_dict["expires_at"] = datetime.fromisoformat(info_dict["expires_at"])
                        
                        self.secret_info[secret_id] = SecretInfo(**info_dict)
            
        except Exception as e:
            self.logger.error(f"从文件加载密钥失败: {e}")
    
    async def _save_secrets_to_file(self) -> None:
        """保存密钥到文件"""
        try:
            # 保存密钥数据
            with open(self.secrets_file, 'w') as f:
                json.dump(self.secrets, f, indent=2)
            
            # 保存密钥信息
            info_data = {}
            for secret_id, secret_info in self.secret_info.items():
                info_dict = {
                    "secret_id": secret_info.secret_id,
                    "secret_type": secret_info.secret_type,
                    "description": secret_info.description,
                    "created_at": secret_info.created_at.isoformat(),
                    "updated_at": secret_info.updated_at.isoformat(),
                    "expires_at": secret_info.expires_at.isoformat() if secret_info.expires_at else None,
                    "tags": secret_info.tags,
                    "metadata": secret_info.metadata
                }
                info_data[secret_id] = info_dict
            
            with open(self.secrets_info_file, 'w') as f:
                json.dump(info_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"保存密钥到文件失败: {e}")
    
    async def _load_secrets_from_vault(self) -> None:
        """从Vault加载密钥"""
        # 这里可以实现从HashiCorp Vault或其他密钥管理服务加载密钥的逻辑
        self.logger.info("Vault密钥加载（待实现）")
    
    async def _save_secrets_to_vault(self) -> None:
        """保存密钥到Vault"""
        # 这里可以实现保存密钥到HashiCorp Vault或其他密钥管理服务的逻辑
        self.logger.info("Vault密钥保存（待实现）")
    
    async def _cleanup_expired_secrets(self) -> None:
        """清理过期密钥"""
        try:
            expired_secrets = []
            current_time = datetime.now()
            
            for secret_id, secret_info in self.secret_info.items():
                if secret_info.expires_at and current_time > secret_info.expires_at:
                    expired_secrets.append(secret_id)
            
            for secret_id in expired_secrets:
                await self.delete_secret(secret_id)
                self.logger.info(f"清理过期密钥: {secret_id}")
            
            if expired_secrets:
                self.logger.info(f"清理了 {len(expired_secrets)} 个过期密钥")
            
        except Exception as e:
            self.logger.error(f"清理过期密钥失败: {e}")
    
    async def _log_access(self, action: str, secret_id: str) -> None:
        """记录访问日志"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "secret_id": secret_id,
                "user": os.getenv("USER", "unknown")
            }
            
            self.access_log.append(log_entry)
            
            # 保持日志在合理范围内
            if len(self.access_log) > 1000:
                self.access_log = self.access_log[-1000:]
            
        except Exception as e:
            self.logger.error(f"记录访问日志失败: {e}")


# 导入asyncio用于异步任务
import asyncio

