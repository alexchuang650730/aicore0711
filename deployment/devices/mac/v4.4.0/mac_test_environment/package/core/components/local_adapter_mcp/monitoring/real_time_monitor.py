"""
Real Time Monitor - 实时性能监控器
为ClaudEditor提供实时系统监控数据

功能：
- 实时系统资源监控
- 任务执行状态跟踪
- AI组件性能监控
- WebSocket实时数据推送
- 历史数据存储和查询
"""

import asyncio
import json
import logging
import time
import psutil
import platform
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import websockets
import threading

class MonitoringLevel(Enum):
    """监控级别"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"

class MetricType(Enum):
    """指标类型"""
    SYSTEM_RESOURCE = "system_resource"
    TASK_PERFORMANCE = "task_performance"
    AI_COMPONENT = "ai_component"
    NETWORK_IO = "network_io"
    DISK_IO = "disk_io"

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    platform_info: Dict[str, str]

@dataclass
class TaskMetrics:
    """任务指标"""
    task_id: str
    task_type: str
    platform: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    cpu_usage: float
    memory_usage: float
    success: bool
    error_message: Optional[str]

@dataclass
class AIComponentMetrics:
    """AI组件指标"""
    component_name: str
    timestamp: datetime
    status: str
    active_requests: int
    total_requests: int
    success_rate: float
    average_response_time: float
    error_count: int
    memory_usage: float

class RealTimeMonitor:
    """实时性能监控器"""
    
    def __init__(self, monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED):
        self.logger = logging.getLogger(__name__)
        self.monitoring_level = monitoring_level
        
        # 监控数据存储
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.task_metrics_history: deque = deque(maxlen=5000)
        self.ai_component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 监控配置
        self.monitoring_interval = 5  # 5秒监控间隔
        self.websocket_port = 8765
        self.max_history_hours = 24
        
        # WebSocket连接管理
        self.websocket_clients: set = set()
        self.websocket_server = None
        
        # 监控状态
        self.is_monitoring = False
        self.monitoring_tasks = []
        
        # 回调函数
        self.metric_callbacks: Dict[MetricType, List[Callable]] = defaultdict(list)
        
        # 平台信息
        self.platform_info = {
            "system": platform.system(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version()
        }
        
        self.logger.info(f"实时监控器初始化完成，监控级别: {monitoring_level.value}")
    
    async def start_monitoring(self) -> bool:
        """
        启动监控
        
        Returns:
            bool: 是否成功启动
        """
        try:
            if self.is_monitoring:
                self.logger.warning("监控已在运行中")
                return True
            
            self.is_monitoring = True
            
            # 启动监控任务
            self.monitoring_tasks = [
                asyncio.create_task(self._system_monitoring_loop()),
                asyncio.create_task(self._cleanup_old_data_loop()),
                asyncio.create_task(self._websocket_server_loop())
            ]
            
            self.logger.info("实时监控启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"启动监控失败: {e}")
            self.is_monitoring = False
            return False
    
    async def stop_monitoring(self):
        """停止监控"""
        try:
            self.is_monitoring = False
            
            # 取消监控任务
            for task in self.monitoring_tasks:
                task.cancel()
            
            # 等待任务完成
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            # 关闭WebSocket服务器
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            self.logger.info("实时监控已停止")
            
        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")
    
    async def _system_monitoring_loop(self):
        """系统监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = await self._collect_system_metrics()
                
                # 存储指标
                self.system_metrics_history.append(metrics)
                
                # 触发回调
                await self._trigger_callbacks(MetricType.SYSTEM_RESOURCE, metrics)
                
                # 推送到WebSocket客户端
                await self._broadcast_to_websockets({
                    "type": "system_metrics",
                    "data": asdict(metrics)
                })
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"系统监控循环错误: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 网络IO
            network_io = psutil.net_io_counters()._asdict()
            
            # 磁盘IO
            disk_io = psutil.disk_io_counters()._asdict()
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 负载平均值
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows不支持getloadavg
                load_average = [0.0, 0.0, 0.0]
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                disk_io=disk_io,
                process_count=process_count,
                load_average=load_average,
                platform_info=self.platform_info
            )
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
            raise
    
    async def record_task_metrics(self, metrics: TaskMetrics):
        """
        记录任务指标
        
        Args:
            metrics: 任务指标
        """
        try:
            self.task_metrics_history.append(metrics)
            
            # 触发回调
            await self._trigger_callbacks(MetricType.TASK_PERFORMANCE, metrics)
            
            # 推送到WebSocket客户端
            await self._broadcast_to_websockets({
                "type": "task_metrics",
                "data": asdict(metrics)
            })
            
            self.logger.debug(f"记录任务指标: {metrics.task_id}")
            
        except Exception as e:
            self.logger.error(f"记录任务指标失败: {e}")
    
    async def record_ai_component_metrics(self, metrics: AIComponentMetrics):
        """
        记录AI组件指标
        
        Args:
            metrics: AI组件指标
        """
        try:
            self.ai_component_metrics[metrics.component_name].append(metrics)
            
            # 触发回调
            await self._trigger_callbacks(MetricType.AI_COMPONENT, metrics)
            
            # 推送到WebSocket客户端
            await self._broadcast_to_websockets({
                "type": "ai_component_metrics",
                "data": asdict(metrics)
            })
            
            self.logger.debug(f"记录AI组件指标: {metrics.component_name}")
            
        except Exception as e:
            self.logger.error(f"记录AI组件指标失败: {e}")
    
    def register_metric_callback(self, metric_type: MetricType, callback: Callable):
        """
        注册指标回调函数
        
        Args:
            metric_type: 指标类型
            callback: 回调函数
        """
        self.metric_callbacks[metric_type].append(callback)
        self.logger.info(f"注册指标回调: {metric_type.value}")
    
    async def _trigger_callbacks(self, metric_type: MetricType, data: Any):
        """触发回调函数"""
        try:
            callbacks = self.metric_callbacks.get(metric_type, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"回调函数执行失败: {e}")
        except Exception as e:
            self.logger.error(f"触发回调失败: {e}")
    
    async def _websocket_server_loop(self):
        """WebSocket服务器循环"""
        try:
            self.websocket_server = await websockets.serve(
                self._handle_websocket_connection,
                "0.0.0.0",
                self.websocket_port
            )
            
            self.logger.info(f"WebSocket服务器启动在端口 {self.websocket_port}")
            
            # 保持服务器运行
            await self.websocket_server.wait_closed()
            
        except Exception as e:
            self.logger.error(f"WebSocket服务器错误: {e}")
    
    async def _handle_websocket_connection(self, websocket, path):
        """处理WebSocket连接"""
        try:
            self.websocket_clients.add(websocket)
            self.logger.info(f"新的WebSocket连接: {websocket.remote_address}")
            
            # 发送初始数据
            await self._send_initial_data(websocket)
            
            # 保持连接
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON format"
                    }))
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket连接已关闭")
        except Exception as e:
            self.logger.error(f"WebSocket连接处理错误: {e}")
        finally:
            self.websocket_clients.discard(websocket)
    
    async def _send_initial_data(self, websocket):
        """发送初始数据"""
        try:
            # 发送最近的系统指标
            if self.system_metrics_history:
                latest_system = self.system_metrics_history[-1]
                await websocket.send(json.dumps({
                    "type": "initial_system_metrics",
                    "data": asdict(latest_system)
                }))
            
            # 发送AI组件状态
            ai_status = {}
            for component_name, metrics_history in self.ai_component_metrics.items():
                if metrics_history:
                    ai_status[component_name] = asdict(metrics_history[-1])
            
            if ai_status:
                await websocket.send(json.dumps({
                    "type": "initial_ai_status",
                    "data": ai_status
                }))
            
        except Exception as e:
            self.logger.error(f"发送初始数据失败: {e}")
    
    async def _handle_websocket_message(self, websocket, data: Dict[str, Any]):
        """处理WebSocket消息"""
        try:
            message_type = data.get("type")
            
            if message_type == "get_history":
                # 获取历史数据
                hours = data.get("hours", 1)
                history_data = await self._get_history_data(hours)
                await websocket.send(json.dumps({
                    "type": "history_data",
                    "data": history_data
                }))
            
            elif message_type == "get_ai_stats":
                # 获取AI组件统计
                ai_stats = await self._get_ai_component_stats()
                await websocket.send(json.dumps({
                    "type": "ai_stats",
                    "data": ai_stats
                }))
            
            elif message_type == "ping":
                # 心跳检测
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
            
        except Exception as e:
            self.logger.error(f"处理WebSocket消息失败: {e}")
    
    async def _broadcast_to_websockets(self, data: Dict[str, Any]):
        """广播数据到所有WebSocket客户端"""
        if not self.websocket_clients:
            return
        
        message = json.dumps(data, default=str)
        disconnected_clients = set()
        
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"WebSocket广播失败: {e}")
                disconnected_clients.add(client)
        
        # 清理断开的连接
        self.websocket_clients -= disconnected_clients
    
    async def _cleanup_old_data_loop(self):
        """清理旧数据循环"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                
                cutoff_time = datetime.now() - timedelta(hours=self.max_history_hours)
                
                # 清理系统指标历史
                self.system_metrics_history = deque(
                    [m for m in self.system_metrics_history if m.timestamp > cutoff_time],
                    maxlen=1000
                )
                
                # 清理任务指标历史
                self.task_metrics_history = deque(
                    [m for m in self.task_metrics_history if m.start_time > cutoff_time],
                    maxlen=5000
                )
                
                # 清理AI组件指标历史
                for component_name in self.ai_component_metrics:
                    self.ai_component_metrics[component_name] = deque(
                        [m for m in self.ai_component_metrics[component_name] if m.timestamp > cutoff_time],
                        maxlen=1000
                    )
                
                self.logger.debug("清理旧监控数据完成")
                
            except Exception as e:
                self.logger.error(f"清理旧数据失败: {e}")
    
    async def _get_history_data(self, hours: int) -> Dict[str, Any]:
        """获取历史数据"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 系统指标历史
            system_history = [
                asdict(m) for m in self.system_metrics_history
                if m.timestamp > cutoff_time
            ]
            
            # 任务指标历史
            task_history = [
                asdict(m) for m in self.task_metrics_history
                if m.start_time > cutoff_time
            ]
            
            # AI组件指标历史
            ai_history = {}
            for component_name, metrics_history in self.ai_component_metrics.items():
                ai_history[component_name] = [
                    asdict(m) for m in metrics_history
                    if m.timestamp > cutoff_time
                ]
            
            return {
                "system_metrics": system_history,
                "task_metrics": task_history,
                "ai_component_metrics": ai_history,
                "time_range": {
                    "start": cutoff_time.isoformat(),
                    "end": datetime.now().isoformat(),
                    "hours": hours
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取历史数据失败: {e}")
            return {}
    
    async def _get_ai_component_stats(self) -> Dict[str, Any]:
        """获取AI组件统计"""
        try:
            stats = {}
            
            for component_name, metrics_history in self.ai_component_metrics.items():
                if not metrics_history:
                    continue
                
                latest_metrics = metrics_history[-1]
                recent_metrics = list(metrics_history)[-10:]  # 最近10个指标
                
                # 计算统计信息
                avg_response_time = sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
                total_requests = sum(m.total_requests for m in recent_metrics)
                avg_success_rate = sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
                
                stats[component_name] = {
                    "status": latest_metrics.status,
                    "active_requests": latest_metrics.active_requests,
                    "total_requests": total_requests,
                    "average_response_time": avg_response_time,
                    "success_rate": avg_success_rate,
                    "error_count": latest_metrics.error_count,
                    "memory_usage": latest_metrics.memory_usage,
                    "last_update": latest_metrics.timestamp.isoformat()
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取AI组件统计失败: {e}")
            return {}
    
    def get_current_system_status(self) -> Dict[str, Any]:
        """获取当前系统状态"""
        try:
            if not self.system_metrics_history:
                return {"error": "No system metrics available"}
            
            latest_metrics = self.system_metrics_history[-1]
            
            return {
                "timestamp": latest_metrics.timestamp.isoformat(),
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "disk_percent": latest_metrics.disk_percent,
                "process_count": latest_metrics.process_count,
                "load_average": latest_metrics.load_average,
                "platform_info": latest_metrics.platform_info,
                "monitoring_status": "active" if self.is_monitoring else "inactive",
                "websocket_clients": len(self.websocket_clients)
            }
            
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return {"error": str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        try:
            return {
                "monitoring_level": self.monitoring_level.value,
                "monitoring_interval": self.monitoring_interval,
                "is_monitoring": self.is_monitoring,
                "websocket_port": self.websocket_port,
                "websocket_clients": len(self.websocket_clients),
                "system_metrics_count": len(self.system_metrics_history),
                "task_metrics_count": len(self.task_metrics_history),
                "ai_component_count": len(self.ai_component_metrics),
                "max_history_hours": self.max_history_hours,
                "platform_info": self.platform_info
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "status": "active" if self.is_monitoring else "inactive",
            "monitoring_level": self.monitoring_level.value,
            "websocket_enabled": True,
            "real_time_updates": self.is_monitoring,
            "statistics": self.get_statistics()
        }

