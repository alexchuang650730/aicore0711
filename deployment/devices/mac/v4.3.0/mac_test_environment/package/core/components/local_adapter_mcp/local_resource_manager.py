"""
Local Resource Manager - 本地资源管理器
专注于本地资源的监控、管理和优化

负责本地计算资源、存储资源、网络资源的统一管理
"""

import asyncio
import psutil
import platform
import shutil
import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess

@dataclass
class SystemInfo:
    """系统信息"""
    platform: str
    platform_version: str
    architecture: str
    hostname: str
    cpu_count: int
    cpu_freq_max: float
    memory_total_gb: float
    disk_total_gb: float
    python_version: str

@dataclass
class ResourceUsage:
    """资源使用情况"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: Tuple[float, float, float]

@dataclass
class ProcessInfo:
    """进程信息"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    create_time: float

@dataclass
class ServiceStatus:
    """服务状态"""
    name: str
    status: str
    pid: Optional[int]
    memory_mb: float
    cpu_percent: float

class LocalResourceManager:
    """本地资源管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化本地资源管理器
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 监控配置
        self.monitor_interval = self.config.get("monitor_interval", 10)  # 秒
        self.history_size = self.config.get("history_size", 100)  # 保留历史记录数量
        self.alert_thresholds = self.config.get("alert_thresholds", {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90
        })
        
        # 系统信息
        self.system_info = None
        
        # 资源使用历史
        self.resource_history: List[ResourceUsage] = []
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_task = None
        
        # 网络统计基线
        self.network_baseline = None
        
        # 服务管理
        self.managed_services: Dict[str, ServiceStatus] = {}
        
        self.logger.info("本地资源管理器初始化完成")
    
    async def start(self):
        """启动资源管理器"""
        try:
            # 获取系统信息
            await self._collect_system_info()
            
            # 设置网络基线
            await self._set_network_baseline()
            
            # 启动监控
            await self.start_monitoring()
            
            self.logger.info("本地资源管理器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动本地资源管理器失败: {e}")
            raise
    
    async def stop(self):
        """停止资源管理器"""
        try:
            await self.stop_monitoring()
            self.logger.info("本地资源管理器已停止")
            
        except Exception as e:
            self.logger.error(f"停止本地资源管理器失败: {e}")
    
    async def start_monitoring(self):
        """开始资源监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("资源监控已启动")
    
    async def stop_monitoring(self):
        """停止资源监控"""
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        self.logger.info("资源监控已停止")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集资源使用情况
                usage = await self._collect_resource_usage()
                
                # 添加到历史记录
                self.resource_history.append(usage)
                
                # 保持历史记录在限制范围内
                if len(self.resource_history) > self.history_size:
                    self.resource_history = self.resource_history[-self.history_size:]
                
                # 检查告警阈值
                await self._check_alerts(usage)
                
                # 等待下次监控
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"资源监控异常: {e}")
                await asyncio.sleep(self.monitor_interval * 2)  # 错误后等待更长时间
    
    async def _collect_system_info(self) -> SystemInfo:
        """收集系统信息"""
        try:
            # CPU信息
            cpu_freq = psutil.cpu_freq()
            cpu_freq_max = cpu_freq.max if cpu_freq else 0
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024**3)
            
            # Python版本
            python_version = platform.python_version()
            
            self.system_info = SystemInfo(
                platform=platform.system(),
                platform_version=platform.release(),
                architecture=platform.machine(),
                hostname=platform.node(),
                cpu_count=psutil.cpu_count(),
                cpu_freq_max=cpu_freq_max,
                memory_total_gb=memory_total_gb,
                disk_total_gb=disk_total_gb,
                python_version=python_version
            )
            
            self.logger.info(f"系统信息收集完成: {self.system_info.platform} {self.system_info.platform_version}")
            return self.system_info
            
        except Exception as e:
            self.logger.error(f"收集系统信息失败: {e}")
            raise
    
    async def _collect_resource_usage(self) -> ResourceUsage:
        """收集资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            
            # 网络使用情况
            network_sent_mb, network_recv_mb = await self._get_network_usage()
            
            # 系统负载
            load_average = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            return ResourceUsage(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_available_gb=memory_available_gb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                load_average=load_average
            )
            
        except Exception as e:
            self.logger.error(f"收集资源使用情况失败: {e}")
            raise
    
    async def _set_network_baseline(self):
        """设置网络基线"""
        try:
            net_io = psutil.net_io_counters()
            self.network_baseline = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "timestamp": time.time()
            }
            self.logger.debug("网络基线设置完成")
            
        except Exception as e:
            self.logger.error(f"设置网络基线失败: {e}")
            self.network_baseline = {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "timestamp": time.time()
            }
    
    async def _get_network_usage(self) -> Tuple[float, float]:
        """获取网络使用情况（MB）"""
        try:
            if not self.network_baseline:
                return 0.0, 0.0
            
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            # 计算增量
            sent_bytes = net_io.bytes_sent - self.network_baseline["bytes_sent"]
            recv_bytes = net_io.bytes_recv - self.network_baseline["bytes_recv"]
            time_delta = current_time - self.network_baseline["timestamp"]
            
            # 转换为MB/s，然后乘以时间间隔
            sent_mb = (sent_bytes / (1024**2)) if time_delta > 0 else 0
            recv_mb = (recv_bytes / (1024**2)) if time_delta > 0 else 0
            
            return sent_mb, recv_mb
            
        except Exception as e:
            self.logger.error(f"获取网络使用情况失败: {e}")
            return 0.0, 0.0
    
    async def _check_alerts(self, usage: ResourceUsage):
        """检查告警阈值"""
        try:
            alerts = []
            
            # CPU告警
            if usage.cpu_percent > self.alert_thresholds["cpu_percent"]:
                alerts.append(f"CPU使用率过高: {usage.cpu_percent:.1f}%")
            
            # 内存告警
            if usage.memory_percent > self.alert_thresholds["memory_percent"]:
                alerts.append(f"内存使用率过高: {usage.memory_percent:.1f}%")
            
            # 磁盘告警
            if usage.disk_percent > self.alert_thresholds["disk_percent"]:
                alerts.append(f"磁盘使用率过高: {usage.disk_percent:.1f}%")
            
            # 记录告警
            for alert in alerts:
                self.logger.warning(f"资源告警: {alert}")
                
        except Exception as e:
            self.logger.error(f"检查告警失败: {e}")
    
    # 公共接口方法
    def get_system_info(self) -> Optional[SystemInfo]:
        """获取系统信息"""
        return self.system_info
    
    def get_current_usage(self) -> Optional[ResourceUsage]:
        """获取当前资源使用情况"""
        return self.resource_history[-1] if self.resource_history else None
    
    def get_usage_history(self, limit: int = None) -> List[ResourceUsage]:
        """获取资源使用历史"""
        if limit:
            return self.resource_history[-limit:]
        return self.resource_history.copy()
    
    def get_average_usage(self, minutes: int = 5) -> Optional[Dict[str, float]]:
        """获取平均资源使用情况"""
        if not self.resource_history:
            return None
        
        # 计算时间范围
        current_time = time.time()
        time_threshold = current_time - (minutes * 60)
        
        # 过滤历史记录
        recent_usage = [
            usage for usage in self.resource_history
            if usage.timestamp >= time_threshold
        ]
        
        if not recent_usage:
            return None
        
        # 计算平均值
        count = len(recent_usage)
        return {
            "cpu_percent": sum(u.cpu_percent for u in recent_usage) / count,
            "memory_percent": sum(u.memory_percent for u in recent_usage) / count,
            "disk_percent": sum(u.disk_percent for u in recent_usage) / count,
            "network_sent_mb": sum(u.network_sent_mb for u in recent_usage) / count,
            "network_recv_mb": sum(u.network_recv_mb for u in recent_usage) / count
        }
    
    async def get_process_list(self, limit: int = 10) -> List[ProcessInfo]:
        """获取进程列表"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time']):
                try:
                    pinfo = proc.info
                    memory_mb = pinfo['memory_info'].rss / (1024**2) if pinfo['memory_info'] else 0
                    
                    processes.append(ProcessInfo(
                        pid=pinfo['pid'],
                        name=pinfo['name'] or 'Unknown',
                        cpu_percent=pinfo['cpu_percent'] or 0,
                        memory_percent=pinfo['memory_percent'] or 0,
                        memory_mb=memory_mb,
                        status=pinfo['status'] or 'Unknown',
                        create_time=pinfo['create_time'] or 0
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 按CPU使用率排序
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            
            return processes[:limit]
            
        except Exception as e:
            self.logger.error(f"获取进程列表失败: {e}")
            return []
    
    async def get_disk_usage_by_path(self, paths: List[str] = None) -> Dict[str, Dict[str, float]]:
        """获取指定路径的磁盘使用情况"""
        try:
            if not paths:
                paths = ['/']
            
            disk_usage = {}
            
            for path in paths:
                if os.path.exists(path):
                    usage = shutil.disk_usage(path)
                    total_gb = usage.total / (1024**3)
                    used_gb = (usage.total - usage.free) / (1024**3)
                    free_gb = usage.free / (1024**3)
                    used_percent = (used_gb / total_gb) * 100 if total_gb > 0 else 0
                    
                    disk_usage[path] = {
                        "total_gb": total_gb,
                        "used_gb": used_gb,
                        "free_gb": free_gb,
                        "used_percent": used_percent
                    }
            
            return disk_usage
            
        except Exception as e:
            self.logger.error(f"获取磁盘使用情况失败: {e}")
            return {}
    
    async def check_available_tools(self) -> List[str]:
        """检查可用工具"""
        tools = []
        
        # 检查常用命令行工具
        common_tools = [
            'git', 'docker', 'node', 'npm', 'python3', 'pip3',
            'curl', 'wget', 'vim', 'nano', 'htop', 'tree',
            'make', 'gcc', 'java', 'mvn', 'gradle'
        ]
        
        for tool in common_tools:
            try:
                result = subprocess.run(['which', tool], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    tools.append(tool)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return tools
    
    async def get_capabilities_summary(self) -> Dict[str, Any]:
        """获取能力摘要"""
        try:
            current_usage = self.get_current_usage()
            average_usage = self.get_average_usage()
            available_tools = await self.check_available_tools()
            
            return {
                "system_info": asdict(self.system_info) if self.system_info else None,
                "current_usage": asdict(current_usage) if current_usage else None,
                "average_usage": average_usage,
                "available_tools": available_tools,
                "monitoring_status": {
                    "is_monitoring": self.is_monitoring,
                    "monitor_interval": self.monitor_interval,
                    "history_size": len(self.resource_history)
                },
                "alert_thresholds": self.alert_thresholds
            }
            
        except Exception as e:
            self.logger.error(f"获取能力摘要失败: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "is_monitoring": self.is_monitoring,
            "monitor_interval": self.monitor_interval,
            "history_size": len(self.resource_history),
            "system_info_available": self.system_info is not None,
            "last_update": self.resource_history[-1].timestamp if self.resource_history else None
        }

