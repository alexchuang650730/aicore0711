"""
Edge Cloud Coordinator - 端云协调器
智能协调本地端和云端的任务执行，实现最优的资源分配和性能

特性：智能路由、负载均衡、故障转移、性能监控
"""

import asyncio
import time
import json
import logging
import psutil
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class ExecutionLocation(Enum):
    """执行位置枚举"""
    LOCAL = "local"
    CLOUD = "cloud"
    AUTO = "auto"

class TaskType(Enum):
    """任务类型枚举"""
    FILE_OPERATION = "file_operation"
    COMPUTATION = "computation"
    AI_INFERENCE = "ai_inference"
    NETWORK_REQUEST = "network_request"
    DATABASE_OPERATION = "database_operation"
    BUILD_DEPLOYMENT = "build_deployment"
    SYSTEM_COMMAND = "system_command"

@dataclass
class TaskMetrics:
    """任务指标"""
    cpu_usage: float
    memory_usage: float
    network_bandwidth: float
    execution_time: float
    success_rate: float
    cost: float

@dataclass
class ResourceStatus:
    """资源状态"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_latency: float
    available: bool

class EdgeCloudCoordinator:
    """端云协调器 - 智能协调本地和云端资源"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化端云协调器
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 协调模式
        self.coordination_mode = self.config.get("coordination_mode", "intelligent")
        self.failover_enabled = self.config.get("failover_enabled", True)
        self.load_balancing = self.config.get("load_balancing", True)
        
        # 云端配置
        self.cloud_endpoint = self.config.get("cloud_endpoint")
        self.cloud_api_key = self.config.get("cloud_api_key")
        self.cloud_timeout = self.config.get("cloud_timeout", 30)
        
        # 本地资源限制
        self.max_cpu_usage = self.config.get("max_cpu_usage", 80)
        self.max_memory_usage = self.config.get("max_memory_usage", 80)
        self.max_disk_usage = self.config.get("max_disk_usage", 90)
        
        # 性能指标
        self.local_metrics = {}
        self.cloud_metrics = {}
        self.task_history = []
        
        # 状态监控
        self.local_status = ResourceStatus(0, 0, 0, 0, True)
        self.cloud_status = ResourceStatus(0, 0, 0, 0, True)
        
        # HTTP会话
        self.session = None
        
        self.logger.info(f"端云协调器初始化完成 - 模式: {self.coordination_mode}")
    
    async def start(self):
        """启动协调器"""
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.cloud_timeout)
            )
            
            # 启动监控任务
            asyncio.create_task(self._monitor_resources())
            asyncio.create_task(self._update_metrics())
            
            self.logger.info("端云协调器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动端云协调器失败: {e}")
            raise
    
    async def stop(self):
        """停止协调器"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.logger.info("端云协调器已停止")
            
        except Exception as e:
            self.logger.error(f"停止端云协调器失败: {e}")
    
    async def coordinate_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        协调任务执行
        
        Args:
            task: 任务信息
            
        Returns:
            Dict: 执行结果
        """
        try:
            task_id = task.get("id", f"task_{int(time.time())}")
            task_type = TaskType(task.get("type", "computation"))
            preferred_location = ExecutionLocation(task.get("preferred_location", "auto"))
            
            self.logger.info(f"协调任务: {task_id} (类型: {task_type.value})")
            
            # 决定执行位置
            execution_location = await self._decide_execution_location(task, task_type, preferred_location)
            
            # 执行任务
            start_time = time.time()
            
            if execution_location == ExecutionLocation.LOCAL:
                result = await self._execute_locally(task)
            elif execution_location == ExecutionLocation.CLOUD:
                result = await self._execute_on_cloud(task)
            else:
                # 智能选择失败，使用本地执行作为后备
                result = await self._execute_locally(task)
            
            execution_time = time.time() - start_time
            
            # 记录任务历史
            await self._record_task_history(task_id, task_type, execution_location, execution_time, result)
            
            # 添加执行信息
            result.update({
                "task_id": task_id,
                "execution_location": execution_location.value,
                "execution_time": execution_time,
                "coordinator_decision": "intelligent"
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"任务协调失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task.get("id", "unknown"),
                "execution_location": "failed"
            }
    
    async def _decide_execution_location(self, task: Dict[str, Any], 
                                       task_type: TaskType, 
                                       preferred_location: ExecutionLocation) -> ExecutionLocation:
        """决定任务执行位置"""
        
        # 如果指定了位置且不是自动选择
        if preferred_location != ExecutionLocation.AUTO:
            if preferred_location == ExecutionLocation.LOCAL and self.local_status.available:
                return ExecutionLocation.LOCAL
            elif preferred_location == ExecutionLocation.CLOUD and self.cloud_status.available:
                return ExecutionLocation.CLOUD
        
        # 根据协调模式决定
        if self.coordination_mode == "local_first":
            return await self._local_first_decision(task, task_type)
        elif self.coordination_mode == "cloud_first":
            return await self._cloud_first_decision(task, task_type)
        else:  # intelligent
            return await self._intelligent_decision(task, task_type)
    
    async def _local_first_decision(self, task: Dict[str, Any], task_type: TaskType) -> ExecutionLocation:
        """本地优先决策"""
        if self.local_status.available and self._can_execute_locally(task, task_type):
            return ExecutionLocation.LOCAL
        elif self.cloud_status.available:
            return ExecutionLocation.CLOUD
        else:
            return ExecutionLocation.LOCAL  # 强制本地执行
    
    async def _cloud_first_decision(self, task: Dict[str, Any], task_type: TaskType) -> ExecutionLocation:
        """云端优先决策"""
        if self.cloud_status.available:
            return ExecutionLocation.CLOUD
        elif self.local_status.available:
            return ExecutionLocation.LOCAL
        else:
            return ExecutionLocation.CLOUD  # 强制云端执行
    
    async def _intelligent_decision(self, task: Dict[str, Any], task_type: TaskType) -> ExecutionLocation:
        """智能决策"""
        # 计算本地和云端的适合度分数
        local_score = await self._calculate_local_score(task, task_type)
        cloud_score = await self._calculate_cloud_score(task, task_type)
        
        self.logger.debug(f"决策分数 - 本地: {local_score}, 云端: {cloud_score}")
        
        # 选择分数更高的位置
        if local_score >= cloud_score:
            return ExecutionLocation.LOCAL
        else:
            return ExecutionLocation.CLOUD
    
    async def _calculate_local_score(self, task: Dict[str, Any], task_type: TaskType) -> float:
        """计算本地执行适合度分数"""
        if not self.local_status.available:
            return 0.0
        
        score = 100.0
        
        # 资源可用性评分 (40%)
        resource_score = (
            (100 - self.local_status.cpu_percent) * 0.4 +
            (100 - self.local_status.memory_percent) * 0.3 +
            (100 - self.local_status.disk_percent) * 0.3
        ) * 0.4
        
        # 任务类型适合度评分 (30%)
        type_score = self._get_local_type_score(task_type) * 0.3
        
        # 历史性能评分 (20%)
        history_score = self._get_local_history_score(task_type) * 0.2
        
        # 延迟评分 (10%) - 本地执行延迟为0
        latency_score = 100.0 * 0.1
        
        total_score = resource_score + type_score + history_score + latency_score
        
        # 如果资源使用率过高，大幅降低分数
        if (self.local_status.cpu_percent > self.max_cpu_usage or 
            self.local_status.memory_percent > self.max_memory_usage):
            total_score *= 0.3
        
        return max(0.0, min(100.0, total_score))
    
    async def _calculate_cloud_score(self, task: Dict[str, Any], task_type: TaskType) -> float:
        """计算云端执行适合度分数"""
        if not self.cloud_status.available:
            return 0.0
        
        score = 100.0
        
        # 云端资源通常充足，给予高分 (40%)
        resource_score = 90.0 * 0.4
        
        # 任务类型适合度评分 (30%)
        type_score = self._get_cloud_type_score(task_type) * 0.3
        
        # 历史性能评分 (20%)
        history_score = self._get_cloud_history_score(task_type) * 0.2
        
        # 延迟评分 (10%)
        latency_penalty = min(self.cloud_status.network_latency / 10, 50)  # 延迟惩罚
        latency_score = max(0, 100 - latency_penalty) * 0.1
        
        total_score = resource_score + type_score + history_score + latency_score
        
        return max(0.0, min(100.0, total_score))
    
    def _get_local_type_score(self, task_type: TaskType) -> float:
        """获取本地执行的任务类型适合度分数"""
        local_friendly_tasks = {
            TaskType.FILE_OPERATION: 95.0,
            TaskType.SYSTEM_COMMAND: 90.0,
            TaskType.BUILD_DEPLOYMENT: 80.0,
            TaskType.DATABASE_OPERATION: 70.0,
            TaskType.COMPUTATION: 60.0,
            TaskType.NETWORK_REQUEST: 50.0,
            TaskType.AI_INFERENCE: 40.0
        }
        return local_friendly_tasks.get(task_type, 50.0)
    
    def _get_cloud_type_score(self, task_type: TaskType) -> float:
        """获取云端执行的任务类型适合度分数"""
        cloud_friendly_tasks = {
            TaskType.AI_INFERENCE: 95.0,
            TaskType.COMPUTATION: 90.0,
            TaskType.NETWORK_REQUEST: 85.0,
            TaskType.DATABASE_OPERATION: 80.0,
            TaskType.BUILD_DEPLOYMENT: 70.0,
            TaskType.SYSTEM_COMMAND: 30.0,
            TaskType.FILE_OPERATION: 20.0
        }
        return cloud_friendly_tasks.get(task_type, 50.0)
    
    def _get_local_history_score(self, task_type: TaskType) -> float:
        """获取本地执行的历史性能分数"""
        if task_type.value not in self.local_metrics:
            return 50.0  # 默认分数
        
        metrics = self.local_metrics[task_type.value]
        return metrics.success_rate * 100
    
    def _get_cloud_history_score(self, task_type: TaskType) -> float:
        """获取云端执行的历史性能分数"""
        if task_type.value not in self.cloud_metrics:
            return 50.0  # 默认分数
        
        metrics = self.cloud_metrics[task_type.value]
        return metrics.success_rate * 100
    
    def _can_execute_locally(self, task: Dict[str, Any], task_type: TaskType) -> bool:
        """检查是否可以在本地执行"""
        # 检查资源限制
        if (self.local_status.cpu_percent > self.max_cpu_usage or
            self.local_status.memory_percent > self.max_memory_usage or
            self.local_status.disk_percent > self.max_disk_usage):
            return False
        
        # 检查任务特定要求
        required_memory = task.get("required_memory_mb", 0)
        if required_memory > 0:
            available_memory = psutil.virtual_memory().available / (1024 * 1024)
            if required_memory > available_memory:
                return False
        
        return True
    
    async def _execute_locally(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """在本地执行任务"""
        try:
            self.logger.info(f"本地执行任务: {task.get('id', 'unknown')}")
            
            # 这里应该调用本地执行器
            # 暂时返回模拟结果
            await asyncio.sleep(0.1)  # 模拟执行时间
            
            return {
                "success": True,
                "result": "本地执行完成",
                "execution_location": "local",
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"本地执行失败: {e}")
            
            # 如果启用故障转移，尝试云端执行
            if self.failover_enabled and self.cloud_status.available:
                self.logger.info("本地执行失败，转移到云端执行")
                return await self._execute_on_cloud(task)
            
            return {
                "success": False,
                "error": str(e),
                "execution_location": "local",
                "timestamp": time.time()
            }
    
    async def _execute_on_cloud(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """在云端执行任务"""
        try:
            self.logger.info(f"云端执行任务: {task.get('id', 'unknown')}")
            
            if not self.cloud_endpoint or not self.session:
                raise Exception("云端服务不可用")
            
            # 准备请求数据
            request_data = {
                "task": task,
                "timestamp": time.time()
            }
            
            headers = {}
            if self.cloud_api_key:
                headers["Authorization"] = f"Bearer {self.cloud_api_key}"
            
            # 发送请求到云端
            async with self.session.post(
                f"{self.cloud_endpoint}/execute",
                json=request_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    result["execution_location"] = "cloud"
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"云端执行失败: HTTP {response.status} - {error_text}")
            
        except Exception as e:
            self.logger.error(f"云端执行失败: {e}")
            
            # 如果启用故障转移，尝试本地执行
            if self.failover_enabled and self.local_status.available:
                self.logger.info("云端执行失败，转移到本地执行")
                return await self._execute_locally(task)
            
            return {
                "success": False,
                "error": str(e),
                "execution_location": "cloud",
                "timestamp": time.time()
            }
    
    async def _monitor_resources(self):
        """监控本地资源状态"""
        while True:
            try:
                # 获取CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # 获取内存使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # 获取磁盘使用率
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # 更新本地状态
                self.local_status = ResourceStatus(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    disk_percent=disk_percent,
                    network_latency=0.0,  # 本地延迟为0
                    available=True
                )
                
                # 检查云端状态
                await self._check_cloud_status()
                
                self.logger.debug(f"资源监控 - CPU: {cpu_percent}%, 内存: {memory_percent}%, 磁盘: {disk_percent}%")
                
                await asyncio.sleep(10)  # 每10秒监控一次
                
            except Exception as e:
                self.logger.error(f"资源监控失败: {e}")
                await asyncio.sleep(30)  # 错误后等待更长时间
    
    async def _check_cloud_status(self):
        """检查云端状态"""
        try:
            if not self.cloud_endpoint or not self.session:
                self.cloud_status.available = False
                return
            
            start_time = time.time()
            
            async with self.session.get(
                f"{self.cloud_endpoint}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                latency = (time.time() - start_time) * 1000  # 转换为毫秒
                
                if response.status == 200:
                    health_data = await response.json()
                    
                    self.cloud_status = ResourceStatus(
                        cpu_percent=health_data.get("cpu_percent", 0),
                        memory_percent=health_data.get("memory_percent", 0),
                        disk_percent=health_data.get("disk_percent", 0),
                        network_latency=latency,
                        available=True
                    )
                else:
                    self.cloud_status.available = False
                    
        except Exception as e:
            self.logger.debug(f"云端状态检查失败: {e}")
            self.cloud_status.available = False
    
    async def _update_metrics(self):
        """更新性能指标"""
        while True:
            try:
                # 分析任务历史，更新指标
                await self._analyze_task_history()
                
                await asyncio.sleep(60)  # 每分钟更新一次指标
                
            except Exception as e:
                self.logger.error(f"更新指标失败: {e}")
                await asyncio.sleep(300)  # 错误后等待5分钟
    
    async def _analyze_task_history(self):
        """分析任务历史"""
        try:
            # 只分析最近的任务
            recent_tasks = [
                task for task in self.task_history
                if task["timestamp"] > time.time() - 3600  # 最近1小时
            ]
            
            # 按任务类型和执行位置分组
            local_tasks = {}
            cloud_tasks = {}
            
            for task in recent_tasks:
                task_type = task["task_type"]
                location = task["execution_location"]
                
                if location == ExecutionLocation.LOCAL:
                    if task_type not in local_tasks:
                        local_tasks[task_type] = []
                    local_tasks[task_type].append(task)
                elif location == ExecutionLocation.CLOUD:
                    if task_type not in cloud_tasks:
                        cloud_tasks[task_type] = []
                    cloud_tasks[task_type].append(task)
            
            # 计算指标
            for task_type, tasks in local_tasks.items():
                metrics = self._calculate_metrics(tasks)
                self.local_metrics[task_type] = metrics
            
            for task_type, tasks in cloud_tasks.items():
                metrics = self._calculate_metrics(tasks)
                self.cloud_metrics[task_type] = metrics
                
        except Exception as e:
            self.logger.error(f"分析任务历史失败: {e}")
    
    def _calculate_metrics(self, tasks: List[Dict[str, Any]]) -> TaskMetrics:
        """计算任务指标"""
        if not tasks:
            return TaskMetrics(0, 0, 0, 0, 0, 0)
        
        total_tasks = len(tasks)
        successful_tasks = sum(1 for task in tasks if task["success"])
        total_time = sum(task["execution_time"] for task in tasks)
        
        return TaskMetrics(
            cpu_usage=0,  # 暂时不计算
            memory_usage=0,  # 暂时不计算
            network_bandwidth=0,  # 暂时不计算
            execution_time=total_time / total_tasks,
            success_rate=successful_tasks / total_tasks,
            cost=0  # 暂时不计算
        )
    
    async def _record_task_history(self, task_id: str, task_type: TaskType, 
                                 execution_location: ExecutionLocation, 
                                 execution_time: float, result: Dict[str, Any]):
        """记录任务历史"""
        try:
            history_entry = {
                "task_id": task_id,
                "task_type": task_type.value,
                "execution_location": execution_location,
                "execution_time": execution_time,
                "success": result.get("success", False),
                "timestamp": time.time()
            }
            
            self.task_history.append(history_entry)
            
            # 保持历史记录在合理范围内
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-500:]  # 保留最近500条
                
        except Exception as e:
            self.logger.error(f"记录任务历史失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        return {
            "coordination_mode": self.coordination_mode,
            "failover_enabled": self.failover_enabled,
            "load_balancing": self.load_balancing,
            "local_status": {
                "cpu_percent": self.local_status.cpu_percent,
                "memory_percent": self.local_status.memory_percent,
                "disk_percent": self.local_status.disk_percent,
                "available": self.local_status.available
            },
            "cloud_status": {
                "network_latency": self.cloud_status.network_latency,
                "available": self.cloud_status.available
            },
            "task_history_count": len(self.task_history),
            "local_metrics_count": len(self.local_metrics),
            "cloud_metrics_count": len(self.cloud_metrics)
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "local_metrics": {
                task_type: {
                    "execution_time": metrics.execution_time,
                    "success_rate": metrics.success_rate
                }
                for task_type, metrics in self.local_metrics.items()
            },
            "cloud_metrics": {
                task_type: {
                    "execution_time": metrics.execution_time,
                    "success_rate": metrics.success_rate
                }
                for task_type, metrics in self.cloud_metrics.items()
            }
        }

