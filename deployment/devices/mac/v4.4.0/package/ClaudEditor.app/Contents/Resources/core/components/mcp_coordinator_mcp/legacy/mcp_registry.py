"""
PowerAutomation 4.0 MCP Registry
MCP注册表 - 负责MCP的注册、发现、管理和生命周期控制
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json

from core.exceptions import MCPRegistrationError, MCPCommunicationError, handle_exception
from core.logging_config import get_mcp_logger
from core.config import get_config


class MCPStatus(Enum):
    """MCP状态枚举"""
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


class MCPType(Enum):
    """MCP类型枚举"""
    SMART_ROUTER = "smart_router"
    AGENT_SQUAD = "agent_squad"
    COMMAND_MASTER = "command_master"
    WORKFLOW_ENGINE = "workflow_engine"
    SECURITY_GUARD = "security_guard"
    MONITOR_OBSERVER = "monitor_observer"
    UTILITY_HELPER = "utility_helper"
    CUSTOM = "custom"


@dataclass
class MCPCapability:
    """MCP能力描述"""
    name: str
    description: str
    methods: List[str]
    version: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class MCPHealthCheck:
    """MCP健康检查结果"""
    is_healthy: bool
    response_time: float
    last_check: datetime
    error_message: Optional[str] = None
    check_count: int = 0
    consecutive_failures: int = 0


@dataclass
class MCPMetrics:
    """MCP指标数据"""
    requests_processed: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_activity: Optional[datetime] = None
    uptime_seconds: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0


@dataclass
class MCPRegistration:
    """MCP注册信息"""
    mcp_id: str
    name: str
    mcp_type: MCPType
    version: str
    description: str
    capabilities: List[MCPCapability]
    endpoint: str
    status: MCPStatus
    registration_time: datetime
    last_heartbeat: datetime
    health_check: MCPHealthCheck
    metrics: MCPMetrics
    metadata: Dict[str, Any]
    tags: Set[str]
    priority: int = 5
    timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        if isinstance(self.tags, list):
            self.tags = set(self.tags)
        if not isinstance(self.capabilities, list):
            self.capabilities = []


class MCPRegistry:
    """MCP注册表"""
    
    def __init__(self):
        self.logger = get_mcp_logger()
        self.config = get_config()
        
        # 注册表存储
        self.registrations: Dict[str, MCPRegistration] = {}
        self.type_index: Dict[MCPType, Set[str]] = {}
        self.capability_index: Dict[str, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        
        # 健康检查配置
        self.health_check_interval = 30  # 秒
        self.health_check_timeout = 5    # 秒
        self.max_consecutive_failures = 3
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            "mcp_registered": [],
            "mcp_unregistered": [],
            "mcp_status_changed": [],
            "mcp_health_changed": [],
            "mcp_failed": []
        }
        
        # 后台任务
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        # 统计信息
        self.stats = {
            "total_registrations": 0,
            "active_mcps": 0,
            "failed_mcps": 0,
            "health_checks_performed": 0,
            "registry_start_time": datetime.now()
        }
    
    async def initialize(self) -> bool:
        """初始化MCP注册表"""
        try:
            self.logger.info("初始化MCP注册表...")
            
            # 初始化索引
            for mcp_type in MCPType:
                self.type_index[mcp_type] = set()
            
            # 启动后台任务
            self._is_running = True
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("MCP注册表初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"MCP注册表初始化失败: {e}")
            return False
    
    async def register_mcp(
        self,
        name: str,
        mcp_type: MCPType,
        version: str,
        description: str,
        capabilities: List[MCPCapability],
        endpoint: str,
        metadata: Dict[str, Any] = None,
        tags: Set[str] = None,
        priority: int = 5
    ) -> str:
        """注册MCP"""
        try:
            # 生成MCP ID
            mcp_id = f"{mcp_type.value}_{name}_{str(uuid.uuid4())[:8]}"
            
            # 验证输入
            if not name or not endpoint:
                raise MCPRegistrationError("MCP名称和端点不能为空")
            
            if mcp_id in self.registrations:
                raise MCPRegistrationError(f"MCP ID已存在: {mcp_id}")
            
            # 创建注册信息
            now = datetime.now()
            registration = MCPRegistration(
                mcp_id=mcp_id,
                name=name,
                mcp_type=mcp_type,
                version=version,
                description=description,
                capabilities=capabilities or [],
                endpoint=endpoint,
                status=MCPStatus.INITIALIZING,
                registration_time=now,
                last_heartbeat=now,
                health_check=MCPHealthCheck(
                    is_healthy=True,
                    response_time=0.0,
                    last_check=now
                ),
                metrics=MCPMetrics(last_activity=now),
                metadata=metadata or {},
                tags=tags or set(),
                priority=priority
            )
            
            # 存储注册信息
            self.registrations[mcp_id] = registration
            
            # 更新索引
            self._update_indexes(mcp_id, registration)
            
            # 更新统计
            self.stats["total_registrations"] += 1
            self.stats["active_mcps"] += 1
            
            # 触发事件
            await self._trigger_event("mcp_registered", {
                "mcp_id": mcp_id,
                "registration": registration
            })
            
            self.logger.info(f"MCP注册成功: {name} ({mcp_id})")
            return mcp_id
            
        except Exception as e:
            self.logger.error(f"MCP注册失败: {e}")
            raise MCPRegistrationError(f"MCP注册失败: {str(e)}")
    
    async def unregister_mcp(self, mcp_id: str) -> bool:
        """注销MCP"""
        try:
            if mcp_id not in self.registrations:
                raise MCPRegistrationError(f"MCP不存在: {mcp_id}")
            
            registration = self.registrations[mcp_id]
            
            # 更新状态
            registration.status = MCPStatus.SHUTTING_DOWN
            
            # 从索引中移除
            self._remove_from_indexes(mcp_id, registration)
            
            # 从注册表中移除
            del self.registrations[mcp_id]
            
            # 更新统计
            self.stats["active_mcps"] -= 1
            
            # 触发事件
            await self._trigger_event("mcp_unregistered", {
                "mcp_id": mcp_id,
                "registration": registration
            })
            
            self.logger.info(f"MCP注销成功: {mcp_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"MCP注销失败: {e}")
            return False
    
    async def update_mcp_status(self, mcp_id: str, status: MCPStatus) -> bool:
        """更新MCP状态"""
        try:
            if mcp_id not in self.registrations:
                return False
            
            registration = self.registrations[mcp_id]
            old_status = registration.status
            registration.status = status
            
            # 触发状态变更事件
            if old_status != status:
                await self._trigger_event("mcp_status_changed", {
                    "mcp_id": mcp_id,
                    "old_status": old_status,
                    "new_status": status,
                    "registration": registration
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新MCP状态失败: {e}")
            return False
    
    async def heartbeat(self, mcp_id: str, metrics: Optional[MCPMetrics] = None) -> bool:
        """MCP心跳"""
        try:
            if mcp_id not in self.registrations:
                return False
            
            registration = self.registrations[mcp_id]
            registration.last_heartbeat = datetime.now()
            
            # 更新指标
            if metrics:
                registration.metrics = metrics
                registration.metrics.last_activity = datetime.now()
            
            # 如果MCP之前是非活跃状态，更新为活跃
            if registration.status in [MCPStatus.INACTIVE, MCPStatus.ERROR]:
                await self.update_mcp_status(mcp_id, MCPStatus.ACTIVE)
            
            return True
            
        except Exception as e:
            self.logger.error(f"MCP心跳处理失败: {e}")
            return False
    
    def get_mcp(self, mcp_id: str) -> Optional[MCPRegistration]:
        """获取MCP注册信息"""
        return self.registrations.get(mcp_id)
    
    def get_mcps_by_type(self, mcp_type: MCPType) -> List[MCPRegistration]:
        """根据类型获取MCP列表"""
        mcp_ids = self.type_index.get(mcp_type, set())
        return [self.registrations[mcp_id] for mcp_id in mcp_ids 
                if mcp_id in self.registrations]
    
    def get_mcps_by_capability(self, capability_name: str) -> List[MCPRegistration]:
        """根据能力获取MCP列表"""
        mcp_ids = self.capability_index.get(capability_name, set())
        return [self.registrations[mcp_id] for mcp_id in mcp_ids 
                if mcp_id in self.registrations]
    
    def get_mcps_by_tag(self, tag: str) -> List[MCPRegistration]:
        """根据标签获取MCP列表"""
        mcp_ids = self.tag_index.get(tag, set())
        return [self.registrations[mcp_id] for mcp_id in mcp_ids 
                if mcp_id in self.registrations]
    
    def get_active_mcps(self) -> List[MCPRegistration]:
        """获取活跃的MCP列表"""
        return [reg for reg in self.registrations.values() 
                if reg.status == MCPStatus.ACTIVE]
    
    def get_healthy_mcps(self) -> List[MCPRegistration]:
        """获取健康的MCP列表"""
        return [reg for reg in self.registrations.values() 
                if reg.health_check.is_healthy and reg.status == MCPStatus.ACTIVE]
    
    def find_best_mcp(
        self,
        mcp_type: Optional[MCPType] = None,
        required_capabilities: List[str] = None,
        tags: Set[str] = None,
        exclude_mcps: Set[str] = None
    ) -> Optional[MCPRegistration]:
        """查找最佳MCP"""
        candidates = []
        
        # 获取候选MCP
        if mcp_type:
            candidates = self.get_mcps_by_type(mcp_type)
        else:
            candidates = list(self.registrations.values())
        
        # 过滤条件
        filtered_candidates = []
        for mcp in candidates:
            # 排除指定的MCP
            if exclude_mcps and mcp.mcp_id in exclude_mcps:
                continue
            
            # 检查状态和健康状况
            if mcp.status != MCPStatus.ACTIVE or not mcp.health_check.is_healthy:
                continue
            
            # 检查能力匹配
            if required_capabilities:
                mcp_capabilities = {cap.name for cap in mcp.capabilities}
                if not all(cap in mcp_capabilities for cap in required_capabilities):
                    continue
            
            # 检查标签匹配
            if tags and not tags.intersection(mcp.tags):
                continue
            
            filtered_candidates.append(mcp)
        
        if not filtered_candidates:
            return None
        
        # 按优先级和健康状况排序
        filtered_candidates.sort(key=lambda x: (
            -x.priority,  # 优先级高的在前
            x.health_check.response_time,  # 响应时间短的在前
            -x.metrics.successful_requests  # 成功请求多的在前
        ))
        
        return filtered_candidates[0]
    
    async def perform_health_check(self, mcp_id: str) -> MCPHealthCheck:
        """执行健康检查"""
        try:
            if mcp_id not in self.registrations:
                raise MCPCommunicationError(f"MCP不存在: {mcp_id}")
            
            registration = self.registrations[mcp_id]
            start_time = time.time()
            
            # 模拟健康检查（实际实现中应该调用MCP的健康检查接口）
            await asyncio.sleep(0.01)  # 模拟网络延迟
            
            response_time = time.time() - start_time
            
            # 更新健康检查结果
            health_check = MCPHealthCheck(
                is_healthy=True,
                response_time=response_time,
                last_check=datetime.now(),
                check_count=registration.health_check.check_count + 1,
                consecutive_failures=0
            )
            
            registration.health_check = health_check
            self.stats["health_checks_performed"] += 1
            
            return health_check
            
        except Exception as e:
            # 健康检查失败
            if mcp_id in self.registrations:
                registration = self.registrations[mcp_id]
                health_check = MCPHealthCheck(
                    is_healthy=False,
                    response_time=self.health_check_timeout,
                    last_check=datetime.now(),
                    error_message=str(e),
                    check_count=registration.health_check.check_count + 1,
                    consecutive_failures=registration.health_check.consecutive_failures + 1
                )
                
                registration.health_check = health_check
                
                # 如果连续失败次数过多，标记为错误状态
                if health_check.consecutive_failures >= self.max_consecutive_failures:
                    await self.update_mcp_status(mcp_id, MCPStatus.ERROR)
                    await self._trigger_event("mcp_failed", {
                        "mcp_id": mcp_id,
                        "registration": registration,
                        "error": str(e)
                    })
                
                return health_check
            
            raise
    
    def _update_indexes(self, mcp_id: str, registration: MCPRegistration):
        """更新索引"""
        # 类型索引
        self.type_index[registration.mcp_type].add(mcp_id)
        
        # 能力索引
        for capability in registration.capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = set()
            self.capability_index[capability.name].add(mcp_id)
        
        # 标签索引
        for tag in registration.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(mcp_id)
    
    def _remove_from_indexes(self, mcp_id: str, registration: MCPRegistration):
        """从索引中移除"""
        # 类型索引
        self.type_index[registration.mcp_type].discard(mcp_id)
        
        # 能力索引
        for capability in registration.capabilities:
            if capability.name in self.capability_index:
                self.capability_index[capability.name].discard(mcp_id)
        
        # 标签索引
        for tag in registration.tags:
            if tag in self.tag_index:
                self.tag_index[tag].discard(mcp_id)
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._is_running:
            try:
                # 对所有注册的MCP执行健康检查
                for mcp_id in list(self.registrations.keys()):
                    try:
                        await self.perform_health_check(mcp_id)
                    except Exception as e:
                        self.logger.error(f"MCP健康检查失败 {mcp_id}: {e}")
                
                # 等待下次检查
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查循环异常: {e}")
                await asyncio.sleep(5)  # 异常后短暂等待
    
    async def _cleanup_loop(self):
        """清理循环"""
        while self._is_running:
            try:
                now = datetime.now()
                cleanup_threshold = timedelta(minutes=5)  # 5分钟无心跳则清理
                
                # 查找需要清理的MCP
                to_cleanup = []
                for mcp_id, registration in self.registrations.items():
                    if now - registration.last_heartbeat > cleanup_threshold:
                        to_cleanup.append(mcp_id)
                
                # 执行清理
                for mcp_id in to_cleanup:
                    self.logger.warning(f"清理无响应的MCP: {mcp_id}")
                    await self.unregister_mcp(mcp_id)
                
                # 等待下次清理
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理循环异常: {e}")
                await asyncio.sleep(10)
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        try:
            callbacks = self.event_callbacks.get(event_type, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"事件回调执行失败 {event_type}: {e}")
        except Exception as e:
            self.logger.error(f"触发事件失败 {event_type}: {e}")
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """添加事件回调"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """移除事件回调"""
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        now = datetime.now()
        uptime = now - self.stats["registry_start_time"]
        
        # 计算状态分布
        status_distribution = {}
        for status in MCPStatus:
            count = sum(1 for reg in self.registrations.values() if reg.status == status)
            status_distribution[status.value] = count
        
        # 计算类型分布
        type_distribution = {}
        for mcp_type in MCPType:
            count = len(self.type_index.get(mcp_type, set()))
            type_distribution[mcp_type.value] = count
        
        return {
            "total_registrations": len(self.registrations),
            "active_mcps": len(self.get_active_mcps()),
            "healthy_mcps": len(self.get_healthy_mcps()),
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "uptime_seconds": uptime.total_seconds(),
            "health_checks_performed": self.stats["health_checks_performed"],
            "capabilities_count": len(self.capability_index),
            "tags_count": len(self.tag_index)
        }
    
    def export_registry(self) -> Dict[str, Any]:
        """导出注册表数据"""
        return {
            "registrations": {
                mcp_id: {
                    **asdict(reg),
                    "registration_time": reg.registration_time.isoformat(),
                    "last_heartbeat": reg.last_heartbeat.isoformat(),
                    "health_check": {
                        **asdict(reg.health_check),
                        "last_check": reg.health_check.last_check.isoformat()
                    },
                    "metrics": {
                        **asdict(reg.metrics),
                        "last_activity": reg.metrics.last_activity.isoformat() if reg.metrics.last_activity else None
                    },
                    "tags": list(reg.tags),
                    "mcp_type": reg.mcp_type.value,
                    "status": reg.status.value
                }
                for mcp_id, reg in self.registrations.items()
            },
            "stats": self.get_registry_stats(),
            "export_time": datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """关闭注册表"""
        try:
            self.logger.info("关闭MCP注册表...")
            
            self._is_running = False
            
            # 取消后台任务
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # 通知所有MCP关闭
            for mcp_id in list(self.registrations.keys()):
                await self.update_mcp_status(mcp_id, MCPStatus.SHUTDOWN)
            
            self.logger.info("MCP注册表已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭MCP注册表失败: {e}")


# 全局MCP注册表实例
_mcp_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    """获取全局MCP注册表实例"""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPRegistry()
    return _mcp_registry

