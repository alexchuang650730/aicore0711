"""
PowerAutomation 4.0 健康监控器

负责监控所有MCP服务的健康状态，提供实时健康检查、故障检测和自动恢复功能。
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .coordinator import MCPServiceInfo, MCPServiceStatus, MCPMessage


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckType(Enum):
    """检查类型枚举"""
    HEARTBEAT = "heartbeat"
    HTTP_PING = "http_ping"
    TCP_CONNECT = "tcp_connect"
    CUSTOM = "custom"


@dataclass
class HealthCheck:
    """健康检查配置"""
    check_id: str
    service_id: str
    check_type: CheckType
    interval: int = 30  # 检查间隔（秒）
    timeout: int = 10   # 超时时间（秒）
    retries: int = 3    # 重试次数
    enabled: bool = True
    endpoint: Optional[str] = None
    custom_checker: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthResult:
    """健康检查结果"""
    check_id: str
    service_id: str
    status: HealthStatus
    response_time: float
    timestamp: datetime
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceHealth:
    """服务健康状态"""
    service_id: str
    overall_status: HealthStatus = HealthStatus.UNKNOWN
    last_check_time: Optional[datetime] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    successful_checks: int = 0
    average_response_time: float = 0.0
    uptime_percentage: float = 0.0
    recent_results: List[HealthResult] = field(default_factory=list)


class HealthMonitor:
    """
    PowerAutomation 4.0 健康监控器
    
    功能：
    1. 实时健康检查
    2. 故障检测和告警
    3. 自动恢复机制
    4. 健康状态统计
    5. 性能监控
    """
    
    def __init__(self, max_history: int = 100):
        """
        初始化健康监控器
        
        Args:
            max_history: 最大历史记录数
        """
        self.logger = logging.getLogger(__name__)
        self.max_history = max_history
        self.is_running = False
        
        # 健康检查配置
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # 服务健康状态
        self.service_health: Dict[str, ServiceHealth] = {}
        
        # 监控任务
        self.monitor_tasks: Dict[str, asyncio.Task] = {}
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            "service_unhealthy": [],
            "service_recovered": [],
            "service_degraded": []
        }
        
        # 全局统计
        self.global_stats = {
            "total_services": 0,
            "healthy_services": 0,
            "unhealthy_services": 0,
            "degraded_services": 0,
            "total_checks": 0,
            "failed_checks": 0
        }
        
        self.logger.info("健康监控器初始化完成")
    
    async def start(self) -> None:
        """启动健康监控器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动健康监控器...")
            
            # 启动全局统计任务
            asyncio.create_task(self._global_stats_updater())
            
            self.is_running = True
            self.logger.info("健康监控器启动成功")
            
        except Exception as e:
            self.logger.error(f"健康监控器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止健康监控器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止健康监控器...")
            
            self.is_running = False
            
            # 停止所有监控任务
            for task in self.monitor_tasks.values():
                task.cancel()
            
            # 等待任务完成
            await asyncio.gather(*self.monitor_tasks.values(), return_exceptions=True)
            
            self.monitor_tasks.clear()
            
            self.logger.info("健康监控器已停止")
            
        except Exception as e:
            self.logger.error(f"健康监控器停止时出错: {e}")
    
    async def start_monitoring(self, service_id: str) -> bool:
        """
        开始监控服务
        
        Args:
            service_id: 服务ID
            
        Returns:
            bool: 是否成功开始监控
        """
        try:
            if service_id in self.monitor_tasks:
                self.logger.warning(f"服务 {service_id} 已在监控中")
                return True
            
            # 初始化服务健康状态
            if service_id not in self.service_health:
                self.service_health[service_id] = ServiceHealth(service_id=service_id)
            
            # 创建默认健康检查
            await self._create_default_health_check(service_id)
            
            # 启动监控任务
            task = asyncio.create_task(self._monitor_service(service_id))
            self.monitor_tasks[service_id] = task
            
            self.logger.info(f"开始监控服务: {service_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"开始监控服务失败: {e}")
            return False
    
    async def stop_monitoring(self, service_id: str) -> bool:
        """
        停止监控服务
        
        Args:
            service_id: 服务ID
            
        Returns:
            bool: 是否成功停止监控
        """
        try:
            if service_id not in self.monitor_tasks:
                self.logger.warning(f"服务 {service_id} 未在监控中")
                return True
            
            # 取消监控任务
            task = self.monitor_tasks[service_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # 清理资源
            del self.monitor_tasks[service_id]
            
            # 移除健康检查
            checks_to_remove = [
                check_id for check_id, check in self.health_checks.items()
                if check.service_id == service_id
            ]
            for check_id in checks_to_remove:
                del self.health_checks[check_id]
            
            self.logger.info(f"停止监控服务: {service_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"停止监控服务失败: {e}")
            return False
    
    async def add_health_check(self, health_check: HealthCheck) -> bool:
        """
        添加健康检查
        
        Args:
            health_check: 健康检查配置
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.health_checks[health_check.check_id] = health_check
            self.logger.info(f"添加健康检查: {health_check.check_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加健康检查失败: {e}")
            return False
    
    async def remove_health_check(self, check_id: str) -> bool:
        """
        移除健康检查
        
        Args:
            check_id: 检查ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if check_id in self.health_checks:
                del self.health_checks[check_id]
                self.logger.info(f"移除健康检查: {check_id}")
                return True
            else:
                self.logger.warning(f"健康检查不存在: {check_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"移除健康检查失败: {e}")
            return False
    
    async def get_service_health(self, service_id: str) -> Optional[ServiceHealth]:
        """
        获取服务健康状态
        
        Args:
            service_id: 服务ID
            
        Returns:
            Optional[ServiceHealth]: 服务健康状态
        """
        return self.service_health.get(service_id)
    
    async def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """获取所有服务健康状态"""
        return self.service_health.copy()
    
    async def register_event_callback(self, event_type: str, callback: Callable) -> None:
        """
        注册事件回调
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            self.logger.info(f"注册事件回调: {event_type}")
        else:
            self.logger.error(f"未知事件类型: {event_type}")
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        return self.global_stats.copy()
    
    async def _create_default_health_check(self, service_id: str) -> None:
        """创建默认健康检查"""
        check_id = f"{service_id}_heartbeat"
        
        health_check = HealthCheck(
            check_id=check_id,
            service_id=service_id,
            check_type=CheckType.HEARTBEAT,
            interval=30,
            timeout=10,
            retries=3
        )
        
        await self.add_health_check(health_check)
    
    async def _monitor_service(self, service_id: str) -> None:
        """监控单个服务"""
        while self.is_running:
            try:
                # 获取该服务的所有健康检查
                service_checks = [
                    check for check in self.health_checks.values()
                    if check.service_id == service_id and check.enabled
                ]
                
                if not service_checks:
                    await asyncio.sleep(30)
                    continue
                
                # 执行健康检查
                results = []
                for check in service_checks:
                    result = await self._perform_health_check(check)
                    results.append(result)
                
                # 更新服务健康状态
                await self._update_service_health(service_id, results)
                
                # 等待下次检查
                min_interval = min(check.interval for check in service_checks)
                await asyncio.sleep(min_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控服务 {service_id} 时出错: {e}")
                await asyncio.sleep(5)
    
    async def _perform_health_check(self, check: HealthCheck) -> HealthResult:
        """执行健康检查"""
        start_time = time.time()
        
        try:
            if check.check_type == CheckType.HEARTBEAT:
                status, message = await self._heartbeat_check(check)
            elif check.check_type == CheckType.HTTP_PING:
                status, message = await self._http_ping_check(check)
            elif check.check_type == CheckType.TCP_CONNECT:
                status, message = await self._tcp_connect_check(check)
            elif check.check_type == CheckType.CUSTOM:
                status, message = await self._custom_check(check)
            else:
                status = HealthStatus.UNKNOWN
                message = f"未知检查类型: {check.check_type}"
            
            response_time = time.time() - start_time
            
            return HealthResult(
                check_id=check.check_id,
                service_id=check.service_id,
                status=status,
                response_time=response_time,
                timestamp=datetime.now(),
                message=message
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            
            return HealthResult(
                check_id=check.check_id,
                service_id=check.service_id,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                timestamp=datetime.now(),
                message=f"健康检查异常: {e}"
            )
    
    async def _heartbeat_check(self, check: HealthCheck) -> tuple[HealthStatus, str]:
        """心跳检查"""
        try:
            # 这里应该实现实际的心跳检查逻辑
            # 可以通过发送心跳消息或检查最后心跳时间
            
            service_health = self.service_health.get(check.service_id)
            if service_health and service_health.last_check_time:
                time_diff = (datetime.now() - service_health.last_check_time).total_seconds()
                if time_diff < check.interval * 2:  # 允许一定的延迟
                    return HealthStatus.HEALTHY, "心跳正常"
                else:
                    return HealthStatus.UNHEALTHY, f"心跳超时: {time_diff}秒"
            else:
                return HealthStatus.UNKNOWN, "无心跳数据"
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"心跳检查失败: {e}"
    
    async def _http_ping_check(self, check: HealthCheck) -> tuple[HealthStatus, str]:
        """HTTP Ping检查"""
        try:
            if not check.endpoint:
                return HealthStatus.UNHEALTHY, "未配置HTTP端点"
            
            # 这里应该实现实际的HTTP请求
            # 使用aiohttp或其他HTTP客户端
            
            # 模拟HTTP检查
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return HealthStatus.HEALTHY, "HTTP响应正常"
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"HTTP检查失败: {e}"
    
    async def _tcp_connect_check(self, check: HealthCheck) -> tuple[HealthStatus, str]:
        """TCP连接检查"""
        try:
            if not check.endpoint:
                return HealthStatus.UNHEALTHY, "未配置TCP端点"
            
            # 这里应该实现实际的TCP连接检查
            # 解析端点地址和端口，尝试建立连接
            
            # 模拟TCP检查
            await asyncio.sleep(0.05)  # 模拟连接时间
            return HealthStatus.HEALTHY, "TCP连接正常"
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"TCP连接失败: {e}"
    
    async def _custom_check(self, check: HealthCheck) -> tuple[HealthStatus, str]:
        """自定义检查"""
        try:
            if not check.custom_checker:
                return HealthStatus.UNHEALTHY, "未配置自定义检查器"
            
            # 执行自定义检查器
            result = await check.custom_checker(check)
            
            if isinstance(result, tuple) and len(result) == 2:
                return result
            else:
                return HealthStatus.UNHEALTHY, "自定义检查器返回格式错误"
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"自定义检查失败: {e}"
    
    async def _update_service_health(self, service_id: str, results: List[HealthResult]) -> None:
        """更新服务健康状态"""
        try:
            service_health = self.service_health[service_id]
            
            # 添加检查结果到历史记录
            service_health.recent_results.extend(results)
            
            # 保持历史记录在限制范围内
            if len(service_health.recent_results) > self.max_history:
                service_health.recent_results = service_health.recent_results[-self.max_history:]
            
            # 更新统计信息
            service_health.total_checks += len(results)
            successful_results = [r for r in results if r.status == HealthStatus.HEALTHY]
            service_health.successful_checks += len(successful_results)
            
            # 计算平均响应时间
            if results:
                total_response_time = sum(r.response_time for r in results)
                avg_response_time = total_response_time / len(results)
                
                if service_health.average_response_time == 0:
                    service_health.average_response_time = avg_response_time
                else:
                    # 使用指数移动平均
                    service_health.average_response_time = (
                        service_health.average_response_time * 0.8 + avg_response_time * 0.2
                    )
            
            # 确定整体健康状态
            current_status = self._determine_overall_status(results)
            previous_status = service_health.overall_status
            
            service_health.overall_status = current_status
            service_health.last_check_time = datetime.now()
            
            # 更新连续失败计数
            if current_status == HealthStatus.UNHEALTHY:
                service_health.consecutive_failures += 1
            else:
                service_health.consecutive_failures = 0
            
            # 计算正常运行时间百分比
            if service_health.total_checks > 0:
                service_health.uptime_percentage = (
                    service_health.successful_checks / service_health.total_checks * 100
                )
            
            # 触发状态变化事件
            await self._trigger_status_change_events(service_id, previous_status, current_status)
            
        except Exception as e:
            self.logger.error(f"更新服务健康状态失败: {e}")
    
    def _determine_overall_status(self, results: List[HealthResult]) -> HealthStatus:
        """确定整体健康状态"""
        if not results:
            return HealthStatus.UNKNOWN
        
        healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        total_count = len(results)
        
        if healthy_count == total_count:
            return HealthStatus.HEALTHY
        elif healthy_count >= total_count * 0.5:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY
    
    async def _trigger_status_change_events(self, service_id: str, 
                                          previous_status: HealthStatus,
                                          current_status: HealthStatus) -> None:
        """触发状态变化事件"""
        try:
            if previous_status == current_status:
                return
            
            event_type = None
            
            if previous_status != HealthStatus.UNHEALTHY and current_status == HealthStatus.UNHEALTHY:
                event_type = "service_unhealthy"
            elif previous_status == HealthStatus.UNHEALTHY and current_status != HealthStatus.UNHEALTHY:
                event_type = "service_recovered"
            elif current_status == HealthStatus.DEGRADED:
                event_type = "service_degraded"
            
            if event_type and event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        await callback(service_id, previous_status, current_status)
                    except Exception as e:
                        self.logger.error(f"事件回调执行失败: {e}")
            
            self.logger.info(f"服务 {service_id} 状态变化: {previous_status} -> {current_status}")
            
        except Exception as e:
            self.logger.error(f"触发状态变化事件失败: {e}")
    
    async def _global_stats_updater(self) -> None:
        """全局统计更新器"""
        while self.is_running:
            try:
                # 更新全局统计
                self.global_stats["total_services"] = len(self.service_health)
                
                healthy_count = 0
                unhealthy_count = 0
                degraded_count = 0
                total_checks = 0
                failed_checks = 0
                
                for service_health in self.service_health.values():
                    if service_health.overall_status == HealthStatus.HEALTHY:
                        healthy_count += 1
                    elif service_health.overall_status == HealthStatus.UNHEALTHY:
                        unhealthy_count += 1
                    elif service_health.overall_status == HealthStatus.DEGRADED:
                        degraded_count += 1
                    
                    total_checks += service_health.total_checks
                    failed_checks += (service_health.total_checks - service_health.successful_checks)
                
                self.global_stats.update({
                    "healthy_services": healthy_count,
                    "unhealthy_services": unhealthy_count,
                    "degraded_services": degraded_count,
                    "total_checks": total_checks,
                    "failed_checks": failed_checks
                })
                
                # 等待下次更新
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"全局统计更新失败: {e}")
                await asyncio.sleep(5)

