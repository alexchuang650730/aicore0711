"""
Remote Environment Interface - 远程环境接口
实现与 Deployment MCP 的标准化集成接口

基于 GitHub deployment_mcp 的 RemoteEnvironment 规范
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod

class ConnectionMethod(Enum):
    """连接方式"""
    SSH = "ssh"
    HTTP_API = "http_api"
    WEBHOOK = "webhook"

class EnvironmentType(Enum):
    """环境类型"""
    MAC_LOCAL = "mac_local"
    WINDOWS_LOCAL = "windows_local"
    LINUX_LOCAL = "linux_local"
    DOCKER = "docker"

class DeploymentStatus(Enum):
    """部署状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class RemoteEnvironmentConfig:
    """远程环境配置"""
    environment_id: str
    environment_type: EnvironmentType
    connection_method: ConnectionMethod
    host: str
    port: int
    username: Optional[str] = None
    ssh_key_path: Optional[str] = None
    api_token: Optional[str] = None
    init_script_path: str = "./init_aicore.sh"
    health_check_url: Optional[str] = None
    timeout: int = 300

@dataclass
class DeploymentTask:
    """部署任务"""
    task_id: str
    deployment_id: str
    task_type: str
    config: Dict[str, Any]
    timeout: int = 300
    priority: str = "normal"

@dataclass
class DeploymentResult:
    """部署结果"""
    task_id: str
    deployment_id: str
    status: DeploymentStatus
    message: str
    execution_time: float
    deployed_version: Optional[str] = None
    endpoints: List[str] = None
    logs: List[str] = None
    error_details: Optional[Dict[str, Any]] = None

class RemoteEnvironmentInterface(ABC):
    """远程环境接口抽象类"""
    
    @abstractmethod
    async def initialize(self, config: RemoteEnvironmentConfig) -> bool:
        """初始化远程环境"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    @abstractmethod
    async def execute_deployment(self, task: DeploymentTask) -> DeploymentResult:
        """执行部署任务"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取环境能力"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """获取环境状态"""
        pass

class LocalAdapterRemoteEnvironment(RemoteEnvironmentInterface):
    """Local Adapter 远程环境实现"""
    
    def __init__(self, local_adapter_engine):
        """
        初始化
        
        Args:
            local_adapter_engine: Local Adapter Engine 实例
        """
        self.logger = logging.getLogger(__name__)
        self.engine = local_adapter_engine
        self.config = None
        self.is_initialized = False
        
        # 部署状态跟踪
        self.active_deployments = {}
        self.deployment_history = []
        
        self.logger.info("Local Adapter 远程环境接口初始化")
    
    async def initialize(self, config: RemoteEnvironmentConfig) -> bool:
        """
        初始化远程环境
        
        Args:
            config: 远程环境配置
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            self.logger.info(f"初始化远程环境: {config.environment_id}")
            
            self.config = config
            
            # 确保 Local Adapter Engine 已启动
            if not self.engine.is_running:
                await self.engine.start()
            
            # 验证环境类型匹配
            detected_type = self.engine.environment_type
            expected_type = config.environment_type.value
            
            if detected_type != expected_type:
                self.logger.warning(f"环境类型不匹配: 检测到 {detected_type}, 期望 {expected_type}")
            
            self.is_initialized = True
            self.logger.info(f"远程环境初始化成功: {config.environment_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"初始化远程环境失败: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        try:
            if not self.is_initialized:
                return {
                    "healthy": False,
                    "error": "环境未初始化",
                    "timestamp": time.time()
                }
            
            # 获取引擎状态
            engine_status = self.engine.get_status()
            
            # 获取资源状态
            resource_status = await self.engine.get_resource_status()
            
            # 检查关键指标
            healthy = (
                engine_status.get("is_running", False) and
                resource_status.get("current_usage") is not None
            )
            
            return {
                "healthy": healthy,
                "environment_id": self.config.environment_id if self.config else None,
                "engine_status": engine_status,
                "resource_status": resource_status,
                "active_deployments": len(self.active_deployments),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def execute_deployment(self, task: DeploymentTask) -> DeploymentResult:
        """
        执行部署任务
        
        Args:
            task: 部署任务
            
        Returns:
            DeploymentResult: 部署结果
        """
        try:
            self.logger.info(f"执行部署任务: {task.task_id}")
            
            if not self.is_initialized:
                return DeploymentResult(
                    task_id=task.task_id,
                    deployment_id=task.deployment_id,
                    status=DeploymentStatus.FAILED,
                    message="环境未初始化",
                    execution_time=0,
                    error_details={"error": "环境未初始化"}
                )
            
            start_time = time.time()
            
            # 记录活跃部署
            self.active_deployments[task.task_id] = {
                "task": task,
                "start_time": start_time,
                "status": DeploymentStatus.IN_PROGRESS
            }
            
            try:
                # 执行部署任务
                result = await self.engine.execute_deployment_task({
                    "task_id": task.task_id,
                    "type": task.task_type,
                    **task.config
                })
                
                execution_time = time.time() - start_time
                
                # 构建部署结果
                if result.get("success", False):
                    deployment_result = DeploymentResult(
                        task_id=task.task_id,
                        deployment_id=task.deployment_id,
                        status=DeploymentStatus.COMPLETED,
                        message="部署成功完成",
                        execution_time=execution_time,
                        deployed_version=result.get("version"),
                        endpoints=result.get("endpoints", []),
                        logs=result.get("logs", [])
                    )
                else:
                    deployment_result = DeploymentResult(
                        task_id=task.task_id,
                        deployment_id=task.deployment_id,
                        status=DeploymentStatus.FAILED,
                        message=result.get("error", "部署失败"),
                        execution_time=execution_time,
                        error_details=result
                    )
                
                # 更新部署状态
                self.active_deployments[task.task_id].update({
                    "status": deployment_result.status,
                    "end_time": time.time(),
                    "result": deployment_result
                })
                
                # 移动到历史记录
                self.deployment_history.append(self.active_deployments.pop(task.task_id))
                
                # 保持历史记录在合理范围内
                if len(self.deployment_history) > 50:
                    self.deployment_history = self.deployment_history[-50:]
                
                self.logger.info(f"部署任务完成: {task.task_id} - {deployment_result.status.value}")
                return deployment_result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                deployment_result = DeploymentResult(
                    task_id=task.task_id,
                    deployment_id=task.deployment_id,
                    status=DeploymentStatus.FAILED,
                    message=f"部署执行异常: {str(e)}",
                    execution_time=execution_time,
                    error_details={"exception": str(e)}
                )
                
                # 清理活跃部署记录
                if task.task_id in self.active_deployments:
                    self.active_deployments[task.task_id].update({
                        "status": DeploymentStatus.FAILED,
                        "end_time": time.time(),
                        "result": deployment_result
                    })
                    self.deployment_history.append(self.active_deployments.pop(task.task_id))
                
                return deployment_result
                
        except Exception as e:
            self.logger.error(f"执行部署任务失败: {e}")
            return DeploymentResult(
                task_id=task.task_id,
                deployment_id=task.deployment_id,
                status=DeploymentStatus.FAILED,
                message=f"部署任务异常: {str(e)}",
                execution_time=0,
                error_details={"exception": str(e)}
            )
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        获取环境能力
        
        Returns:
            Dict: 环境能力信息
        """
        try:
            if not self.is_initialized:
                return {"error": "环境未初始化"}
            
            # 获取引擎能力
            capabilities = await self.engine.get_capabilities()
            
            # 添加远程环境特定信息
            capabilities.update({
                "remote_environment": {
                    "environment_id": self.config.environment_id,
                    "environment_type": self.config.environment_type.value,
                    "connection_method": self.config.connection_method.value,
                    "host": self.config.host,
                    "port": self.config.port,
                    "is_initialized": self.is_initialized
                },
                "deployment_capabilities": {
                    "supported_task_types": [
                        "shell_command",
                        "file_operation", 
                        "service_management"
                    ],
                    "max_concurrent_deployments": 5,
                    "timeout_range": [30, 3600]
                }
            })
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"获取环境能力失败: {e}")
            return {"error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取环境状态
        
        Returns:
            Dict: 环境状态信息
        """
        try:
            # 基础状态
            status = {
                "is_initialized": self.is_initialized,
                "config": asdict(self.config) if self.config else None,
                "active_deployments": len(self.active_deployments),
                "deployment_history_count": len(self.deployment_history),
                "timestamp": time.time()
            }
            
            # 如果已初始化，添加详细状态
            if self.is_initialized:
                engine_status = self.engine.get_status()
                health_status = await self.health_check()
                
                status.update({
                    "engine_status": engine_status,
                    "health_status": health_status,
                    "active_deployment_details": {
                        task_id: {
                            "deployment_id": info["task"].deployment_id,
                            "task_type": info["task"].task_type,
                            "status": info["status"].value,
                            "start_time": info["start_time"],
                            "duration": time.time() - info["start_time"]
                        }
                        for task_id, info in self.active_deployments.items()
                    }
                })
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取环境状态失败: {e}")
            return {
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_deployment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取部署历史
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            List: 部署历史记录
        """
        try:
            history = self.deployment_history[-limit:] if limit else self.deployment_history
            
            return [
                {
                    "task_id": record["task"].task_id,
                    "deployment_id": record["task"].deployment_id,
                    "task_type": record["task"].task_type,
                    "status": record["status"].value,
                    "start_time": record["start_time"],
                    "end_time": record.get("end_time"),
                    "duration": record.get("end_time", time.time()) - record["start_time"],
                    "result": asdict(record["result"]) if record.get("result") else None
                }
                for record in history
            ]
            
        except Exception as e:
            self.logger.error(f"获取部署历史失败: {e}")
            return []

