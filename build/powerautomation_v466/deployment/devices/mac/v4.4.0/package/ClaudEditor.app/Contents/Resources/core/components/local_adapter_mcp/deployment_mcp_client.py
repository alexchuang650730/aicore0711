"""
Deployment MCP Client - 部署MCP客户端
基于 GitHub deployment_mcp 规范的标准化客户端

负责与 Deployment MCP 的远程部署协调器通信
"""

import asyncio
import json
import logging
import aiohttp
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .remote_environment_interface import (
    RemoteEnvironmentConfig, 
    EnvironmentType, 
    ConnectionMethod,
    LocalAdapterRemoteEnvironment
)

@dataclass
class RegistrationRequest:
    """注册请求"""
    environment_id: str
    environment_type: str
    connection_method: str
    host: str
    port: int
    username: Optional[str] = None
    ssh_key_path: Optional[str] = None
    api_token: Optional[str] = None
    init_script_path: str = "./init_aicore.sh"
    health_check_url: Optional[str] = None
    timeout: int = 300
    capabilities: Dict[str, Any] = None

class DeploymentMCPClient:
    """Deployment MCP 客户端"""
    
    def __init__(self, local_adapter_engine, config: Dict[str, Any] = None):
        """
        初始化Deployment MCP客户端
        
        Args:
            local_adapter_engine: Local Adapter Engine 实例
            config: 配置字典
        """
        self.logger = logging.getLogger(__name__)
        self.engine = local_adapter_engine
        self.config = config or {}
        
        # Deployment MCP 连接配置
        self.deployment_mcp_url = self.config.get("deployment_mcp_url", "http://localhost:8001")
        self.api_token = self.config.get("api_token")
        self.timeout = self.config.get("timeout", 30)
        
        # 本地环境配置
        self.environment_id = self.config.get("environment_id", f"local_adapter_{int(time.time())}")
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 8080)
        self.connection_method = ConnectionMethod(self.config.get("connection_method", "http_api"))
        
        # HTTP会话
        self.session = None
        
        # 远程环境接口
        self.remote_env = LocalAdapterRemoteEnvironment(local_adapter_engine)
        
        # 连接状态
        self.is_registered = False
        self.last_heartbeat = 0
        self.heartbeat_interval = self.config.get("heartbeat_interval", 30)
        
        self.logger.info(f"Deployment MCP客户端初始化 - URL: {self.deployment_mcp_url}")
    
    async def start(self):
        """启动客户端"""
        try:
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
            # 初始化远程环境接口
            await self._initialize_remote_environment()
            
            # 注册到Deployment MCP
            await self._register_environment()
            
            # 启动心跳任务
            asyncio.create_task(self._heartbeat_loop())
            
            self.logger.info("Deployment MCP客户端启动成功")
            
        except Exception as e:
            self.logger.error(f"启动Deployment MCP客户端失败: {e}")
            raise
    
    async def stop(self):
        """停止客户端"""
        try:
            # 注销环境
            if self.is_registered and self.session:
                await self._unregister_environment()
            
            # 关闭HTTP会话
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_registered = False
            self.logger.info("Deployment MCP客户端已停止")
            
        except Exception as e:
            self.logger.error(f"停止Deployment MCP客户端失败: {e}")
    
    async def _initialize_remote_environment(self):
        """初始化远程环境接口"""
        try:
            # 检测环境类型
            platform_info = await self.engine.platform_detector.detect()
            platform_name = platform_info.get("platform", "linux").lower()
            
            if platform_name == "darwin":
                env_type = EnvironmentType.MAC_LOCAL
            elif platform_name == "windows":
                env_type = EnvironmentType.WINDOWS_LOCAL
            else:
                env_type = EnvironmentType.LINUX_LOCAL
            
            # 创建远程环境配置
            remote_config = RemoteEnvironmentConfig(
                environment_id=self.environment_id,
                environment_type=env_type,
                connection_method=self.connection_method,
                host=self.host,
                port=self.port,
                api_token=self.api_token,
                timeout=self.timeout
            )
            
            # 初始化远程环境
            success = await self.remote_env.initialize(remote_config)
            if not success:
                raise Exception("远程环境初始化失败")
            
            self.logger.info(f"远程环境初始化成功: {env_type.value}")
            
        except Exception as e:
            self.logger.error(f"初始化远程环境失败: {e}")
            raise
    
    async def _register_environment(self):
        """注册环境到Deployment MCP"""
        try:
            # 获取环境能力
            capabilities = await self.remote_env.get_capabilities()
            
            # 构建注册请求
            registration_data = RegistrationRequest(
                environment_id=self.environment_id,
                environment_type=self.remote_env.config.environment_type.value,
                connection_method=self.connection_method.value,
                host=self.host,
                port=self.port,
                api_token=self.api_token,
                timeout=self.timeout,
                capabilities=capabilities
            )
            
            # 发送注册请求
            headers = self._get_headers()
            async with self.session.post(
                f"{self.deployment_mcp_url}/api/v1/environments/register",
                json=asdict(registration_data),
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.is_registered = True
                    self.logger.info(f"环境注册成功: {result}")
                else:
                    error_text = await response.text()
                    raise Exception(f"环境注册失败: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"注册环境失败: {e}")
            raise
    
    async def _unregister_environment(self):
        """注销环境"""
        try:
            headers = self._get_headers()
            async with self.session.delete(
                f"{self.deployment_mcp_url}/api/v1/environments/{self.environment_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.logger.info("环境注销成功")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"环境注销失败: {error_text}")
                    
        except Exception as e:
            self.logger.error(f"注销环境失败: {e}")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_registered:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"心跳发送失败: {e}")
                await asyncio.sleep(self.heartbeat_interval * 2)  # 错误后等待更长时间
    
    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            # 获取当前状态
            status = await self.remote_env.get_status()
            health = await self.remote_env.health_check()
            
            heartbeat_data = {
                "environment_id": self.environment_id,
                "timestamp": time.time(),
                "status": status,
                "health": health
            }
            
            headers = self._get_headers()
            async with self.session.post(
                f"{self.deployment_mcp_url}/api/v1/environments/{self.environment_id}/heartbeat",
                json=heartbeat_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    self.last_heartbeat = time.time()
                    self.logger.debug("心跳发送成功")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"心跳发送失败: {error_text}")
                    
        except Exception as e:
            self.logger.debug(f"心跳发送异常: {e}")
    
    async def report_deployment_result(self, deployment_id: str, result: Dict[str, Any]) -> bool:
        """
        报告部署结果
        
        Args:
            deployment_id: 部署ID
            result: 部署结果
            
        Returns:
            bool: 是否报告成功
        """
        try:
            if not self.is_registered:
                return False
            
            report_data = {
                "environment_id": self.environment_id,
                "deployment_id": deployment_id,
                "result": result,
                "timestamp": time.time()
            }
            
            headers = self._get_headers()
            async with self.session.post(
                f"{self.deployment_mcp_url}/api/v1/deployments/{deployment_id}/report",
                json=report_data,
                headers=headers
            ) as response:
                success = response.status == 200
                if success:
                    self.logger.debug(f"部署结果报告成功: {deployment_id}")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"部署结果报告失败: {error_text}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"报告部署结果失败: {e}")
            return False
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        获取部署状态
        
        Args:
            deployment_id: 部署ID
            
        Returns:
            Dict: 部署状态信息
        """
        try:
            if not self.is_registered:
                return None
            
            headers = self._get_headers()
            async with self.session.get(
                f"{self.deployment_mcp_url}/api/v1/deployments/{deployment_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    return status
                else:
                    error_text = await response.text()
                    self.logger.warning(f"获取部署状态失败: {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"获取部署状态失败: {e}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"LocalAdapterMCP/{self.environment_id}"
        }
        
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        return headers
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "is_registered": self.is_registered,
            "deployment_mcp_url": self.deployment_mcp_url,
            "environment_id": self.environment_id,
            "connection_method": self.connection_method.value,
            "last_heartbeat": self.last_heartbeat,
            "heartbeat_interval": self.heartbeat_interval,
            "remote_env_initialized": self.remote_env.is_initialized if self.remote_env else False
        }
    
    async def start(self):
        """启动客户端"""
        try:
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
            # 注册到Deployment MCP
            await self._register_adapter()
            
            # 启动心跳任务
            asyncio.create_task(self._heartbeat_loop())
            
            self.is_connected = True
            self.logger.info("Deployment MCP客户端启动成功")
            
        except Exception as e:
            self.logger.error(f"启动Deployment MCP客户端失败: {e}")
            raise
    
    async def stop(self):
        """停止客户端"""
        try:
            self.is_connected = False
            
            # 注销适配器
            if self.session:
                await self._unregister_adapter()
                await self.session.close()
                self.session = None
            
            self.logger.info("Deployment MCP客户端已停止")
            
        except Exception as e:
            self.logger.error(f"停止Deployment MCP客户端失败: {e}")
    
    async def coordinate_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """
        协调任务执行
        
        Args:
            task_request: 任务请求
            
        Returns:
            Dict: 协调结果
        """
        try:
            if not self.is_connected:
                raise Exception("未连接到Deployment MCP")
            
            self.logger.info(f"协调任务: {task_request.task_id}")
            
            # 准备请求数据
            request_data = {
                "adapter_id": self.adapter_id,
                "task_request": {
                    "task_id": task_request.task_id,
                    "task_type": task_request.task_type,
                    "payload": task_request.payload,
                    "priority": task_request.priority.value,
                    "preference": task_request.preference.value,
                    "timeout": task_request.timeout,
                    "metadata": task_request.metadata or {}
                },
                "local_capabilities": await self._get_local_capabilities(),
                "timestamp": time.time()
            }
            
            # 发送协调请求
            headers = self._get_headers()
            async with self.session.post(
                f"{self.deployment_mcp_url}/api/v1/coordinate",
                json=request_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"任务协调成功: {task_request.task_id}")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"任务协调失败: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"任务协调失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_request.task_id,
                "execution_location": "failed"
            }
    
    async def report_task_result(self, task_id: str, result: Dict[str, Any]) -> bool:
        """
        报告任务执行结果
        
        Args:
            task_id: 任务ID
            result: 执行结果
            
        Returns:
            bool: 是否报告成功
        """
        try:
            if not self.is_connected:
                return False
            
            request_data = {
                "adapter_id": self.adapter_id,
                "task_id": task_id,
                "result": result,
                "timestamp": time.time()
            }
            
            headers = self._get_headers()
            async with self.session.post(
                f"{self.deployment_mcp_url}/api/v1/report",
                json=request_data,
                headers=headers
            ) as response:
                success = response.status == 200
                if success:
                    self.logger.debug(f"任务结果报告成功: {task_id}")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"任务结果报告失败: {error_text}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"报告任务结果失败: {e}")
            return False
    
    async def update_capabilities(self, capabilities: LocalCapabilities):
        """
        更新本地能力
        
        Args:
            capabilities: 本地能力描述
        """
        try:
            self.local_capabilities = capabilities
            self.last_capability_update = time.time()
            
            if not self.is_connected:
                return
            
            request_data = {
                "adapter_id": self.adapter_id,
                "capabilities": {
                    "platform": capabilities.platform,
                    "cpu_cores": capabilities.cpu_cores,
                    "memory_gb": capabilities.memory_gb,
                    "disk_gb": capabilities.disk_gb,
                    "available_tools": capabilities.available_tools,
                    "performance_metrics": capabilities.performance_metrics
                },
                "timestamp": time.time()
            }
            
            headers = self._get_headers()
            async with self.session.put(
                f"{self.deployment_mcp_url}/api/v1/capabilities",
                json=request_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    self.logger.debug("本地能力更新成功")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"本地能力更新失败: {error_text}")
                    
        except Exception as e:
            self.logger.error(f"更新本地能力失败: {e}")
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """
        获取部署状态
        
        Returns:
            Dict: 部署状态信息
        """
        try:
            if not self.is_connected:
                return {"connected": False, "error": "未连接到Deployment MCP"}
            
            headers = self._get_headers()
            async with self.session.get(
                f"{self.deployment_mcp_url}/api/v1/status",
                headers=headers,
                params={"adapter_id": self.adapter_id}
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    return status
                else:
                    error_text = await response.text()
                    return {"connected": False, "error": f"HTTP {response.status} - {error_text}"}
                    
        except Exception as e:
            self.logger.error(f"获取部署状态失败: {e}")
            return {"connected": False, "error": str(e)}
    
    async def _register_adapter(self):
        """注册适配器到Deployment MCP"""
        try:
            registration_data = {
                "adapter_id": self.adapter_id,
                "adapter_name": self.adapter_name,
                "adapter_type": "local",
                "capabilities": await self._get_local_capabilities(),
                "timestamp": time.time()
            }
            
            headers = self._get_headers()
            async with self.session.post(
                f"{self.deployment_mcp_url}/api/v1/register",
                json=registration_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"适配器注册成功: {result}")
                else:
                    error_text = await response.text()
                    raise Exception(f"适配器注册失败: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"注册适配器失败: {e}")
            raise
    
    async def _unregister_adapter(self):
        """注销适配器"""
        try:
            headers = self._get_headers()
            async with self.session.delete(
                f"{self.deployment_mcp_url}/api/v1/register",
                headers=headers,
                params={"adapter_id": self.adapter_id}
            ) as response:
                if response.status == 200:
                    self.logger.info("适配器注销成功")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"适配器注销失败: {error_text}")
                    
        except Exception as e:
            self.logger.error(f"注销适配器失败: {e}")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_connected:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                
            except Exception as e:
                self.logger.error(f"心跳发送失败: {e}")
                await asyncio.sleep(60)  # 错误后等待更长时间
    
    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            heartbeat_data = {
                "adapter_id": self.adapter_id,
                "timestamp": time.time(),
                "status": "active"
            }
            
            headers = self._get_headers()
            async with self.session.post(
                f"{self.deployment_mcp_url}/api/v1/heartbeat",
                json=heartbeat_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    self.last_heartbeat = time.time()
                    self.logger.debug("心跳发送成功")
                else:
                    error_text = await response.text()
                    self.logger.warning(f"心跳发送失败: {error_text}")
                    
        except Exception as e:
            self.logger.debug(f"心跳发送异常: {e}")
    
    async def _get_local_capabilities(self) -> Dict[str, Any]:
        """获取本地能力"""
        if (self.local_capabilities and 
            time.time() - self.last_capability_update < 300):  # 5分钟缓存
            return {
                "platform": self.local_capabilities.platform,
                "cpu_cores": self.local_capabilities.cpu_cores,
                "memory_gb": self.local_capabilities.memory_gb,
                "disk_gb": self.local_capabilities.disk_gb,
                "available_tools": self.local_capabilities.available_tools,
                "performance_metrics": self.local_capabilities.performance_metrics
            }
        
        # 如果没有缓存，返回基本信息
        import psutil
        import platform
        
        return {
            "platform": platform.system().lower(),
            "cpu_cores": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "disk_gb": psutil.disk_usage('/').total / (1024**3),
            "available_tools": ["shell", "file_operations", "process_management"],
            "performance_metrics": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"LocalAdapterMCP/{self.adapter_id}"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "connected": self.is_connected,
            "deployment_mcp_url": self.deployment_mcp_url,
            "adapter_id": self.adapter_id,
            "last_heartbeat": self.last_heartbeat,
            "last_capability_update": self.last_capability_update
        }

