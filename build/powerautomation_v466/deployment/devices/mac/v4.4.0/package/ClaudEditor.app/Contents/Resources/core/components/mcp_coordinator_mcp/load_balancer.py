"""
PowerAutomation 4.0 负载均衡器

负责在多个MCP服务实例之间智能分配负载，支持多种负载均衡算法和动态权重调整。
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from .coordinator import MCPServiceInfo, MCPServiceStatus


class LoadBalancingAlgorithm(Enum):
    """负载均衡算法枚举"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    RANDOM = "random"
    WEIGHTED_RANDOM = "weighted_random"
    CONSISTENT_HASH = "consistent_hash"
    IP_HASH = "ip_hash"
    RESPONSE_TIME = "response_time"


@dataclass
class ServiceInstance:
    """服务实例"""
    service_id: str
    service_info: MCPServiceInfo
    weight: int = 100
    current_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadBalancingRule:
    """负载均衡规则"""
    rule_id: str
    service_pattern: str = "*"
    algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN
    enabled: bool = True
    sticky_sessions: bool = False
    health_check_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadBalancingStats:
    """负载均衡统计"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    requests_per_second: float = 0.0
    last_request_time: Optional[datetime] = None


class LoadBalancer:
    """
    PowerAutomation 4.0 负载均衡器
    
    功能：
    1. 多种负载均衡算法
    2. 动态权重调整
    3. 健康检查集成
    4. 会话粘性支持
    5. 性能监控和统计
    """
    
    def __init__(self):
        """初始化负载均衡器"""
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # 服务实例池
        self.service_instances: Dict[str, ServiceInstance] = {}
        self.service_groups: Dict[str, List[str]] = {}  # 服务名 -> 实例ID列表
        
        # 负载均衡规则
        self.balancing_rules: Dict[str, LoadBalancingRule] = {}
        
        # 算法状态
        self.round_robin_counters: Dict[str, int] = {}
        self.consistent_hash_ring: Dict[str, List[Tuple[int, str]]] = {}
        
        # 会话粘性
        self.sticky_sessions: Dict[str, str] = {}  # 会话ID -> 服务实例ID
        
        # 统计信息
        self.global_stats = LoadBalancingStats()
        self.service_stats: Dict[str, LoadBalancingStats] = {}
        
        # 性能监控
        self.performance_history: Dict[str, List[float]] = {}
        
        self.logger.info("负载均衡器初始化完成")
    
    async def start(self) -> None:
        """启动负载均衡器"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动负载均衡器...")
            
            # 启动性能监控任务
            asyncio.create_task(self._performance_monitor())
            
            # 启动统计更新任务
            asyncio.create_task(self._stats_updater())
            
            self.is_running = True
            self.logger.info("负载均衡器启动成功")
            
        except Exception as e:
            self.logger.error(f"负载均衡器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止负载均衡器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止负载均衡器...")
            
            self.is_running = False
            
            # 清理资源
            self.service_instances.clear()
            self.service_groups.clear()
            self.sticky_sessions.clear()
            
            self.logger.info("负载均衡器已停止")
            
        except Exception as e:
            self.logger.error(f"负载均衡器停止时出错: {e}")
    
    async def add_service(self, service_info: MCPServiceInfo, weight: int = 100) -> bool:
        """
        添加服务实例
        
        Args:
            service_info: 服务信息
            weight: 权重
            
        Returns:
            bool: 添加是否成功
        """
        try:
            service_id = service_info.service_id
            service_name = service_info.name
            
            # 创建服务实例
            instance = ServiceInstance(
                service_id=service_id,
                service_info=service_info,
                weight=weight
            )
            
            # 添加到实例池
            self.service_instances[service_id] = instance
            
            # 添加到服务组
            if service_name not in self.service_groups:
                self.service_groups[service_name] = []
            self.service_groups[service_name].append(service_id)
            
            # 初始化统计信息
            self.service_stats[service_id] = LoadBalancingStats()
            
            # 更新一致性哈希环
            await self._update_consistent_hash_ring(service_name)
            
            self.logger.info(f"添加服务实例: {service_name} ({service_id}), 权重: {weight}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加服务实例失败: {e}")
            return False
    
    async def remove_service(self, service_id: str) -> bool:
        """
        移除服务实例
        
        Args:
            service_id: 服务ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if service_id not in self.service_instances:
                self.logger.warning(f"服务实例不存在: {service_id}")
                return False
            
            instance = self.service_instances[service_id]
            service_name = instance.service_info.name
            
            # 从实例池移除
            del self.service_instances[service_id]
            
            # 从服务组移除
            if service_name in self.service_groups:
                self.service_groups[service_name].remove(service_id)
                if not self.service_groups[service_name]:
                    del self.service_groups[service_name]
            
            # 清理统计信息
            if service_id in self.service_stats:
                del self.service_stats[service_id]
            
            # 清理会话粘性
            sessions_to_remove = [
                session_id for session_id, instance_id in self.sticky_sessions.items()
                if instance_id == service_id
            ]
            for session_id in sessions_to_remove:
                del self.sticky_sessions[session_id]
            
            # 更新一致性哈希环
            if service_name in self.service_groups:
                await self._update_consistent_hash_ring(service_name)
            
            self.logger.info(f"移除服务实例: {service_name} ({service_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"移除服务实例失败: {e}")
            return False
    
    async def select_service(self, service_name: str, 
                           session_id: Optional[str] = None,
                           client_ip: Optional[str] = None,
                           request_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        选择服务实例
        
        Args:
            service_name: 服务名称
            session_id: 会话ID（用于会话粘性）
            client_ip: 客户端IP（用于IP哈希）
            request_context: 请求上下文
            
        Returns:
            Optional[str]: 选中的服务实例ID
        """
        try:
            # 检查服务组是否存在
            if service_name not in self.service_groups:
                self.logger.error(f"服务组不存在: {service_name}")
                return None
            
            # 获取可用的服务实例
            available_instances = await self._get_available_instances(service_name)
            if not available_instances:
                self.logger.error(f"没有可用的服务实例: {service_name}")
                return None
            
            # 查找匹配的负载均衡规则
            rule = self._find_matching_rule(service_name)
            
            # 检查会话粘性
            if rule and rule.sticky_sessions and session_id:
                if session_id in self.sticky_sessions:
                    sticky_instance_id = self.sticky_sessions[session_id]
                    if sticky_instance_id in available_instances:
                        return sticky_instance_id
            
            # 根据算法选择实例
            selected_instance_id = await self._select_by_algorithm(
                service_name, available_instances, rule, client_ip, request_context
            )
            
            # 设置会话粘性
            if rule and rule.sticky_sessions and session_id and selected_instance_id:
                self.sticky_sessions[session_id] = selected_instance_id
            
            # 更新连接计数
            if selected_instance_id:
                self.service_instances[selected_instance_id].current_connections += 1
                self.service_instances[selected_instance_id].total_requests += 1
                self.service_instances[selected_instance_id].last_request_time = datetime.now()
            
            return selected_instance_id
            
        except Exception as e:
            self.logger.error(f"选择服务实例失败: {e}")
            return None
    
    async def release_service(self, service_id: str, 
                            response_time: Optional[float] = None,
                            success: bool = True) -> None:
        """
        释放服务实例
        
        Args:
            service_id: 服务ID
            response_time: 响应时间
            success: 是否成功
        """
        try:
            if service_id not in self.service_instances:
                return
            
            instance = self.service_instances[service_id]
            
            # 更新连接计数
            instance.current_connections = max(0, instance.current_connections - 1)
            
            # 更新统计信息
            if not success:
                instance.failed_requests += 1
            
            # 更新响应时间
            if response_time is not None:
                if instance.average_response_time == 0:
                    instance.average_response_time = response_time
                else:
                    # 使用指数移动平均
                    instance.average_response_time = (
                        instance.average_response_time * 0.8 + response_time * 0.2
                    )
                
                # 记录性能历史
                service_name = instance.service_info.name
                if service_name not in self.performance_history:
                    self.performance_history[service_name] = []
                
                self.performance_history[service_name].append(response_time)
                
                # 保持历史记录在合理范围内
                if len(self.performance_history[service_name]) > 100:
                    self.performance_history[service_name] = self.performance_history[service_name][-100:]
            
            # 更新全局统计
            self.global_stats.total_requests += 1
            if success:
                self.global_stats.successful_requests += 1
            else:
                self.global_stats.failed_requests += 1
            
            self.global_stats.last_request_time = datetime.now()
            
        except Exception as e:
            self.logger.error(f"释放服务实例失败: {e}")
    
    async def add_balancing_rule(self, rule: LoadBalancingRule) -> bool:
        """
        添加负载均衡规则
        
        Args:
            rule: 负载均衡规则
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.balancing_rules[rule.rule_id] = rule
            self.logger.info(f"添加负载均衡规则: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加负载均衡规则失败: {e}")
            return False
    
    async def remove_balancing_rule(self, rule_id: str) -> bool:
        """
        移除负载均衡规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if rule_id in self.balancing_rules:
                del self.balancing_rules[rule_id]
                self.logger.info(f"移除负载均衡规则: {rule_id}")
                return True
            else:
                self.logger.warning(f"负载均衡规则不存在: {rule_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"移除负载均衡规则失败: {e}")
            return False
    
    async def update_service_weight(self, service_id: str, weight: int) -> bool:
        """
        更新服务权重
        
        Args:
            service_id: 服务ID
            weight: 新权重
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if service_id not in self.service_instances:
                self.logger.error(f"服务实例不存在: {service_id}")
                return False
            
            old_weight = self.service_instances[service_id].weight
            self.service_instances[service_id].weight = weight
            
            # 更新一致性哈希环
            service_name = self.service_instances[service_id].service_info.name
            await self._update_consistent_hash_ring(service_name)
            
            self.logger.info(f"更新服务权重: {service_id}, {old_weight} -> {weight}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新服务权重失败: {e}")
            return False
    
    async def get_service_stats(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Args:
            service_id: 服务ID，为None时返回全局统计
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if service_id:
            if service_id in self.service_instances:
                instance = self.service_instances[service_id]
                stats = self.service_stats.get(service_id, LoadBalancingStats())
                
                return {
                    "service_id": service_id,
                    "service_name": instance.service_info.name,
                    "weight": instance.weight,
                    "current_connections": instance.current_connections,
                    "total_requests": instance.total_requests,
                    "failed_requests": instance.failed_requests,
                    "success_rate": (
                        (instance.total_requests - instance.failed_requests) / 
                        max(instance.total_requests, 1) * 100
                    ),
                    "average_response_time": instance.average_response_time,
                    "enabled": instance.enabled,
                    "last_request_time": instance.last_request_time
                }
            else:
                return {}
        else:
            return {
                "global_stats": {
                    "total_requests": self.global_stats.total_requests,
                    "successful_requests": self.global_stats.successful_requests,
                    "failed_requests": self.global_stats.failed_requests,
                    "success_rate": (
                        self.global_stats.successful_requests / 
                        max(self.global_stats.total_requests, 1) * 100
                    ),
                    "average_response_time": self.global_stats.average_response_time,
                    "requests_per_second": self.global_stats.requests_per_second,
                    "last_request_time": self.global_stats.last_request_time
                },
                "service_instances": len(self.service_instances),
                "service_groups": len(self.service_groups),
                "active_sessions": len(self.sticky_sessions)
            }
    
    async def _get_available_instances(self, service_name: str) -> List[str]:
        """获取可用的服务实例"""
        if service_name not in self.service_groups:
            return []
        
        available_instances = []
        for instance_id in self.service_groups[service_name]:
            instance = self.service_instances[instance_id]
            
            # 检查实例是否启用
            if not instance.enabled:
                continue
            
            # 检查服务状态
            if instance.service_info.status != MCPServiceStatus.RUNNING:
                continue
            
            available_instances.append(instance_id)
        
        return available_instances
    
    def _find_matching_rule(self, service_name: str) -> Optional[LoadBalancingRule]:
        """查找匹配的负载均衡规则"""
        for rule in self.balancing_rules.values():
            if not rule.enabled:
                continue
            
            if self._match_pattern(service_name, rule.service_pattern):
                return rule
        
        return None
    
    def _match_pattern(self, value: str, pattern: str) -> bool:
        """模式匹配"""
        if pattern == "*":
            return True
        
        # 简单的通配符匹配
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return value.startswith(prefix) and value.endswith(suffix)
        
        return value == pattern
    
    async def _select_by_algorithm(self, service_name: str, 
                                 available_instances: List[str],
                                 rule: Optional[LoadBalancingRule],
                                 client_ip: Optional[str],
                                 request_context: Optional[Dict[str, Any]]) -> Optional[str]:
        """根据算法选择实例"""
        if not available_instances:
            return None
        
        algorithm = rule.algorithm if rule else LoadBalancingAlgorithm.ROUND_ROBIN
        
        try:
            if algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
                return await self._round_robin_select(service_name, available_instances)
            elif algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
                return await self._weighted_round_robin_select(service_name, available_instances)
            elif algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
                return await self._least_connections_select(available_instances)
            elif algorithm == LoadBalancingAlgorithm.WEIGHTED_LEAST_CONNECTIONS:
                return await self._weighted_least_connections_select(available_instances)
            elif algorithm == LoadBalancingAlgorithm.RANDOM:
                return await self._random_select(available_instances)
            elif algorithm == LoadBalancingAlgorithm.WEIGHTED_RANDOM:
                return await self._weighted_random_select(available_instances)
            elif algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
                return await self._consistent_hash_select(service_name, client_ip or "")
            elif algorithm == LoadBalancingAlgorithm.IP_HASH:
                return await self._ip_hash_select(available_instances, client_ip or "")
            elif algorithm == LoadBalancingAlgorithm.RESPONSE_TIME:
                return await self._response_time_select(available_instances)
            else:
                return await self._round_robin_select(service_name, available_instances)
                
        except Exception as e:
            self.logger.error(f"算法选择失败: {e}")
            return available_instances[0] if available_instances else None
    
    async def _round_robin_select(self, service_name: str, available_instances: List[str]) -> str:
        """轮询选择"""
        if service_name not in self.round_robin_counters:
            self.round_robin_counters[service_name] = 0
        
        index = self.round_robin_counters[service_name] % len(available_instances)
        self.round_robin_counters[service_name] += 1
        
        return available_instances[index]
    
    async def _weighted_round_robin_select(self, service_name: str, available_instances: List[str]) -> str:
        """加权轮询选择"""
        # 简化实现，这里可以实现更复杂的加权轮询算法
        weights = [self.service_instances[instance_id].weight for instance_id in available_instances]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return await self._round_robin_select(service_name, available_instances)
        
        # 使用权重进行选择
        import random
        rand_weight = random.randint(1, total_weight)
        current_weight = 0
        
        for i, weight in enumerate(weights):
            current_weight += weight
            if rand_weight <= current_weight:
                return available_instances[i]
        
        return available_instances[0]
    
    async def _least_connections_select(self, available_instances: List[str]) -> str:
        """最少连接选择"""
        min_connections = float('inf')
        selected_instance = available_instances[0]
        
        for instance_id in available_instances:
            connections = self.service_instances[instance_id].current_connections
            if connections < min_connections:
                min_connections = connections
                selected_instance = instance_id
        
        return selected_instance
    
    async def _weighted_least_connections_select(self, available_instances: List[str]) -> str:
        """加权最少连接选择"""
        min_ratio = float('inf')
        selected_instance = available_instances[0]
        
        for instance_id in available_instances:
            instance = self.service_instances[instance_id]
            weight = max(instance.weight, 1)
            ratio = instance.current_connections / weight
            
            if ratio < min_ratio:
                min_ratio = ratio
                selected_instance = instance_id
        
        return selected_instance
    
    async def _random_select(self, available_instances: List[str]) -> str:
        """随机选择"""
        return random.choice(available_instances)
    
    async def _weighted_random_select(self, available_instances: List[str]) -> str:
        """加权随机选择"""
        weights = [self.service_instances[instance_id].weight for instance_id in available_instances]
        return random.choices(available_instances, weights=weights)[0]
    
    async def _consistent_hash_select(self, service_name: str, key: str) -> Optional[str]:
        """一致性哈希选择"""
        if service_name not in self.consistent_hash_ring:
            return None
        
        hash_ring = self.consistent_hash_ring[service_name]
        if not hash_ring:
            return None
        
        # 计算键的哈希值
        key_hash = int(hashlib.md5(key.encode()).hexdigest(), 16)
        
        # 在哈希环上查找
        for hash_value, instance_id in hash_ring:
            if key_hash <= hash_value:
                return instance_id
        
        # 如果没找到，返回第一个
        return hash_ring[0][1]
    
    async def _ip_hash_select(self, available_instances: List[str], client_ip: str) -> str:
        """IP哈希选择"""
        if not client_ip:
            return available_instances[0]
        
        ip_hash = hash(client_ip)
        index = ip_hash % len(available_instances)
        return available_instances[index]
    
    async def _response_time_select(self, available_instances: List[str]) -> str:
        """响应时间选择"""
        min_response_time = float('inf')
        selected_instance = available_instances[0]
        
        for instance_id in available_instances:
            response_time = self.service_instances[instance_id].average_response_time
            if response_time == 0:  # 新实例，优先选择
                return instance_id
            
            if response_time < min_response_time:
                min_response_time = response_time
                selected_instance = instance_id
        
        return selected_instance
    
    async def _update_consistent_hash_ring(self, service_name: str) -> None:
        """更新一致性哈希环"""
        if service_name not in self.service_groups:
            return
        
        hash_ring = []
        
        for instance_id in self.service_groups[service_name]:
            instance = self.service_instances[instance_id]
            weight = instance.weight
            
            # 为每个实例创建多个虚拟节点
            virtual_nodes = max(1, weight // 10)
            
            for i in range(virtual_nodes):
                virtual_key = f"{instance_id}:{i}"
                hash_value = int(hashlib.md5(virtual_key.encode()).hexdigest(), 16)
                hash_ring.append((hash_value, instance_id))
        
        # 排序哈希环
        hash_ring.sort(key=lambda x: x[0])
        self.consistent_hash_ring[service_name] = hash_ring
    
    async def _performance_monitor(self) -> None:
        """性能监控"""
        while self.is_running:
            try:
                # 动态调整权重（基于性能）
                await self._adjust_weights_by_performance()
                
                # 等待下次监控
                await asyncio.sleep(60)  # 每分钟执行一次
                
            except Exception as e:
                self.logger.error(f"性能监控失败: {e}")
                await asyncio.sleep(5)
    
    async def _adjust_weights_by_performance(self) -> None:
        """根据性能调整权重"""
        try:
            for service_name, instance_ids in self.service_groups.items():
                if len(instance_ids) < 2:
                    continue  # 只有一个实例时不需要调整
                
                # 计算平均响应时间
                response_times = []
                for instance_id in instance_ids:
                    instance = self.service_instances[instance_id]
                    if instance.average_response_time > 0:
                        response_times.append(instance.average_response_time)
                
                if not response_times:
                    continue
                
                avg_response_time = sum(response_times) / len(response_times)
                
                # 根据响应时间调整权重
                for instance_id in instance_ids:
                    instance = self.service_instances[instance_id]
                    if instance.average_response_time > 0:
                        # 响应时间越短，权重越高
                        performance_factor = avg_response_time / instance.average_response_time
                        new_weight = int(instance.weight * performance_factor * 0.1 + instance.weight * 0.9)
                        new_weight = max(10, min(200, new_weight))  # 限制权重范围
                        
                        if abs(new_weight - instance.weight) > 5:  # 只有变化较大时才调整
                            instance.weight = new_weight
                            await self._update_consistent_hash_ring(service_name)
                            self.logger.debug(f"调整服务权重: {instance_id} -> {new_weight}")
                
        except Exception as e:
            self.logger.error(f"性能权重调整失败: {e}")
    
    async def _stats_updater(self) -> None:
        """统计更新器"""
        last_request_count = 0
        last_update_time = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                current_request_count = self.global_stats.total_requests
                
                # 计算每秒请求数
                time_diff = current_time - last_update_time
                if time_diff > 0:
                    request_diff = current_request_count - last_request_count
                    self.global_stats.requests_per_second = request_diff / time_diff
                
                last_request_count = current_request_count
                last_update_time = current_time
                
                # 等待下次更新
                await asyncio.sleep(10)  # 每10秒更新一次
                
            except Exception as e:
                self.logger.error(f"统计更新失败: {e}")
                await asyncio.sleep(5)

