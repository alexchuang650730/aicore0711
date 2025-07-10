"""
PowerAutomation 4.0 服务注册表

负责管理所有MCP服务的注册信息，提供服务发现功能。
支持分布式部署和高可用性。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .coordinator import MCPServiceInfo, MCPServiceStatus


class ServiceRegistry:
    """
    MCP服务注册表
    
    功能：
    1. 服务注册和注销
    2. 服务发现
    3. 服务状态管理
    4. 持久化存储
    """
    
    def __init__(self, storage_backend: str = "memory"):
        """
        初始化服务注册表
        
        Args:
            storage_backend: 存储后端类型 (memory, redis, database)
        """
        self.logger = logging.getLogger(__name__)
        self.storage_backend = storage_backend
        self.services: Dict[str, MCPServiceInfo] = {}
        self.is_running = False
        
        # 根据存储后端初始化
        if storage_backend == "redis":
            self._init_redis_backend()
        elif storage_backend == "database":
            self._init_database_backend()
        else:
            self._init_memory_backend()
        
        self.logger.info(f"服务注册表初始化完成，使用 {storage_backend} 存储")
    
    async def start(self) -> None:
        """启动服务注册表"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动服务注册表...")
            
            # 从持久化存储加载服务信息
            await self._load_services()
            
            self.is_running = True
            self.logger.info("服务注册表启动成功")
            
        except Exception as e:
            self.logger.error(f"服务注册表启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止服务注册表"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止服务注册表...")
            
            # 保存服务信息到持久化存储
            await self._save_services()
            
            self.is_running = False
            self.logger.info("服务注册表已停止")
            
        except Exception as e:
            self.logger.error(f"服务注册表停止时出错: {e}")
    
    async def register(self, service_info: MCPServiceInfo) -> bool:
        """
        注册服务
        
        Args:
            service_info: 服务信息
            
        Returns:
            bool: 注册是否成功
        """
        try:
            service_id = service_info.service_id
            
            # 检查服务是否已存在
            if service_id in self.services:
                self.logger.warning(f"服务 {service_id} 已存在，更新服务信息")
            
            # 设置注册时间
            service_info.registered_at = datetime.now()
            service_info.status = MCPServiceStatus.RUNNING
            
            # 存储服务信息
            self.services[service_id] = service_info
            
            # 持久化存储
            await self._persist_service(service_info)
            
            self.logger.info(f"服务 {service_info.name} ({service_id}) 注册成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注册服务失败: {e}")
            return False
    
    async def unregister(self, service_id: str) -> bool:
        """
        注销服务
        
        Args:
            service_id: 服务ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if service_id not in self.services:
                self.logger.warning(f"服务 {service_id} 不存在")
                return False
            
            service_info = self.services[service_id]
            service_info.status = MCPServiceStatus.STOPPED
            
            # 从内存中移除
            del self.services[service_id]
            
            # 从持久化存储中移除
            await self._remove_service(service_id)
            
            self.logger.info(f"服务 {service_info.name} ({service_id}) 注销成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注销服务失败: {e}")
            return False
    
    async def get_service(self, service_id: str) -> Optional[MCPServiceInfo]:
        """
        获取服务信息
        
        Args:
            service_id: 服务ID
            
        Returns:
            Optional[MCPServiceInfo]: 服务信息
        """
        return self.services.get(service_id)
    
    async def list_services(self, 
                          capability_filter: Optional[str] = None,
                          status_filter: Optional[MCPServiceStatus] = None) -> List[MCPServiceInfo]:
        """
        列出服务
        
        Args:
            capability_filter: 能力过滤器
            status_filter: 状态过滤器
            
        Returns:
            List[MCPServiceInfo]: 服务信息列表
        """
        services = list(self.services.values())
        
        # 应用能力过滤器
        if capability_filter:
            services = [s for s in services if capability_filter in s.capabilities]
        
        # 应用状态过滤器
        if status_filter:
            services = [s for s in services if s.status == status_filter]
        
        return services
    
    async def find_services_by_capability(self, capability: str) -> List[MCPServiceInfo]:
        """
        根据能力查找服务
        
        Args:
            capability: 能力名称
            
        Returns:
            List[MCPServiceInfo]: 匹配的服务列表
        """
        return await self.list_services(capability_filter=capability)
    
    async def update_service_status(self, service_id: str, status: MCPServiceStatus) -> bool:
        """
        更新服务状态
        
        Args:
            service_id: 服务ID
            status: 新状态
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if service_id not in self.services:
                self.logger.error(f"服务 {service_id} 不存在")
                return False
            
            old_status = self.services[service_id].status
            self.services[service_id].status = status
            
            # 持久化更新
            await self._persist_service(self.services[service_id])
            
            self.logger.info(f"服务 {service_id} 状态从 {old_status} 更新为 {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新服务状态失败: {e}")
            return False
    
    async def update_service_heartbeat(self, service_id: str) -> bool:
        """
        更新服务心跳时间
        
        Args:
            service_id: 服务ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if service_id not in self.services:
                return False
            
            self.services[service_id].last_heartbeat = datetime.now()
            
            # 持久化更新
            await self._persist_service(self.services[service_id])
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新服务心跳失败: {e}")
            return False
    
    async def get_service_count(self) -> int:
        """获取服务总数"""
        return len(self.services)
    
    async def get_healthy_services(self) -> List[MCPServiceInfo]:
        """获取健康的服务列表"""
        return await self.list_services(status_filter=MCPServiceStatus.RUNNING)
    
    def _init_memory_backend(self) -> None:
        """初始化内存存储后端"""
        self.logger.info("使用内存存储后端")
    
    def _init_redis_backend(self) -> None:
        """初始化Redis存储后端"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.logger.info("Redis存储后端初始化成功")
        except ImportError:
            self.logger.warning("Redis库未安装，回退到内存存储")
            self.storage_backend = "memory"
        except Exception as e:
            self.logger.error(f"Redis连接失败: {e}，回退到内存存储")
            self.storage_backend = "memory"
    
    def _init_database_backend(self) -> None:
        """初始化数据库存储后端"""
        # 这里可以实现数据库存储逻辑
        self.logger.info("数据库存储后端初始化（待实现）")
        self.storage_backend = "memory"  # 暂时回退到内存存储
    
    async def _load_services(self) -> None:
        """从持久化存储加载服务信息"""
        try:
            if self.storage_backend == "redis":
                await self._load_from_redis()
            elif self.storage_backend == "database":
                await self._load_from_database()
            else:
                # 内存存储不需要加载
                pass
                
        except Exception as e:
            self.logger.error(f"加载服务信息失败: {e}")
    
    async def _save_services(self) -> None:
        """保存服务信息到持久化存储"""
        try:
            if self.storage_backend == "redis":
                await self._save_to_redis()
            elif self.storage_backend == "database":
                await self._save_to_database()
            else:
                # 内存存储不需要保存
                pass
                
        except Exception as e:
            self.logger.error(f"保存服务信息失败: {e}")
    
    async def _persist_service(self, service_info: MCPServiceInfo) -> None:
        """持久化单个服务信息"""
        try:
            if self.storage_backend == "redis":
                await self._persist_to_redis(service_info)
            elif self.storage_backend == "database":
                await self._persist_to_database(service_info)
            else:
                # 内存存储不需要持久化
                pass
                
        except Exception as e:
            self.logger.error(f"持久化服务信息失败: {e}")
    
    async def _remove_service(self, service_id: str) -> None:
        """从持久化存储中移除服务"""
        try:
            if self.storage_backend == "redis":
                await self._remove_from_redis(service_id)
            elif self.storage_backend == "database":
                await self._remove_from_database(service_id)
            else:
                # 内存存储不需要移除
                pass
                
        except Exception as e:
            self.logger.error(f"从持久化存储移除服务失败: {e}")
    
    async def _load_from_redis(self) -> None:
        """从Redis加载服务信息"""
        try:
            keys = self.redis_client.keys("service:*")
            for key in keys:
                service_data = self.redis_client.get(key)
                if service_data:
                    service_dict = json.loads(service_data)
                    # 重建MCPServiceInfo对象
                    service_info = self._dict_to_service_info(service_dict)
                    self.services[service_info.service_id] = service_info
            
            self.logger.info(f"从Redis加载了 {len(self.services)} 个服务")
            
        except Exception as e:
            self.logger.error(f"从Redis加载服务失败: {e}")
    
    async def _save_to_redis(self) -> None:
        """保存服务信息到Redis"""
        try:
            for service_id, service_info in self.services.items():
                key = f"service:{service_id}"
                service_data = json.dumps(asdict(service_info), default=str)
                self.redis_client.set(key, service_data)
            
            self.logger.info(f"保存了 {len(self.services)} 个服务到Redis")
            
        except Exception as e:
            self.logger.error(f"保存服务到Redis失败: {e}")
    
    async def _persist_to_redis(self, service_info: MCPServiceInfo) -> None:
        """持久化单个服务到Redis"""
        try:
            key = f"service:{service_info.service_id}"
            service_data = json.dumps(asdict(service_info), default=str)
            self.redis_client.set(key, service_data)
            
        except Exception as e:
            self.logger.error(f"持久化服务到Redis失败: {e}")
    
    async def _remove_from_redis(self, service_id: str) -> None:
        """从Redis移除服务"""
        try:
            key = f"service:{service_id}"
            self.redis_client.delete(key)
            
        except Exception as e:
            self.logger.error(f"从Redis移除服务失败: {e}")
    
    async def _load_from_database(self) -> None:
        """从数据库加载服务信息"""
        # 待实现
        pass
    
    async def _save_to_database(self) -> None:
        """保存服务信息到数据库"""
        # 待实现
        pass
    
    async def _persist_to_database(self, service_info: MCPServiceInfo) -> None:
        """持久化单个服务到数据库"""
        # 待实现
        pass
    
    async def _remove_from_database(self, service_id: str) -> None:
        """从数据库移除服务"""
        # 待实现
        pass
    
    def _dict_to_service_info(self, service_dict: Dict[str, Any]) -> MCPServiceInfo:
        """将字典转换为MCPServiceInfo对象"""
        # 处理日期时间字段
        if isinstance(service_dict.get('registered_at'), str):
            service_dict['registered_at'] = datetime.fromisoformat(service_dict['registered_at'])
        
        if isinstance(service_dict.get('last_heartbeat'), str):
            service_dict['last_heartbeat'] = datetime.fromisoformat(service_dict['last_heartbeat'])
        
        # 处理枚举字段
        if isinstance(service_dict.get('status'), str):
            service_dict['status'] = MCPServiceStatus(service_dict['status'])
        
        return MCPServiceInfo(**service_dict)

