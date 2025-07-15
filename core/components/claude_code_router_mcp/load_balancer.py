"""
Claude Code Router MCP - 負載均衡器
智能負載均衡和故障轉移系統
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """負載均衡策略"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    LEAST_RESPONSE_TIME = "least_response_time"
    HEALTH_BASED = "health_based"


@dataclass
class EndpointInfo:
    """端點信息"""
    endpoint_id: str
    weight: int = 1
    current_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: float = 0.0
    is_healthy: bool = True
    last_health_check: float = 0.0
    consecutive_failures: int = 0
    
    def get_success_rate(self) -> float:
        """獲取成功率"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    def update_request_stats(self, response_time: float, success: bool):
        """更新請求統計"""
        self.total_requests += 1
        self.last_request_time = time.time()
        
        if success:
            self.successful_requests += 1
            self.consecutive_failures = 0
        else:
            self.failed_requests += 1
            self.consecutive_failures += 1
        
        # 更新平均響應時間
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (self.avg_response_time * 0.9 + response_time * 0.1)
        
        # 基於連續失敗次數更新健康狀態
        if self.consecutive_failures >= 3:
            self.is_healthy = False
        elif self.consecutive_failures == 0 and not self.is_healthy:
            self.is_healthy = True


class LoadBalancer:
    """負載均衡器"""
    
    def __init__(self, strategy: str = "round_robin"):
        self.strategy = LoadBalancingStrategy(strategy)
        self.endpoints: Dict[str, EndpointInfo] = {}
        self.round_robin_index = 0
        self.circuit_breaker_threshold = 5
        self.health_check_interval = 60
        
        logger.info(f"⚖️ LoadBalancer 初始化完成 (策略: {strategy})")
    
    def add_endpoint(self, endpoint_id: str, weight: int = 1):
        """添加端點"""
        self.endpoints[endpoint_id] = EndpointInfo(
            endpoint_id=endpoint_id,
            weight=weight
        )
        logger.info(f"➕ 端點已添加: {endpoint_id} (權重: {weight})")
    
    def remove_endpoint(self, endpoint_id: str):
        """移除端點"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"➖ 端點已移除: {endpoint_id}")
    
    def get_endpoint(self, request_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """根據策略獲取端點"""
        healthy_endpoints = [
            ep_id for ep_id, ep_info in self.endpoints.items()
            if ep_info.is_healthy
        ]
        
        if not healthy_endpoints:
            # 如果沒有健康的端點，嘗試使用最近失敗較少的端點
            if self.endpoints:
                fallback_endpoint = min(
                    self.endpoints.items(),
                    key=lambda x: x[1].consecutive_failures
                )
                logger.warning(f"⚠️ 使用備用端點: {fallback_endpoint[0]}")
                return fallback_endpoint[0]
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random_select(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(healthy_endpoints)
        elif self.strategy == LoadBalancingStrategy.HEALTH_BASED:
            return self._health_based_select(healthy_endpoints)
        else:
            return self._round_robin_select(healthy_endpoints)
    
    def _round_robin_select(self, endpoints: List[str]) -> str:
        """輪詢選擇"""
        if not endpoints:
            return None
        
        endpoint = endpoints[self.round_robin_index % len(endpoints)]
        self.round_robin_index += 1
        return endpoint
    
    def _least_connections_select(self, endpoints: List[str]) -> str:
        """最少連接選擇"""
        if not endpoints:
            return None
        
        return min(endpoints, key=lambda ep: self.endpoints[ep].current_connections)
    
    def _weighted_round_robin_select(self, endpoints: List[str]) -> str:
        """加權輪詢選擇"""
        if not endpoints:
            return None
        
        # 構建加權列表
        weighted_endpoints = []
        for ep_id in endpoints:
            weight = self.endpoints[ep_id].weight
            weighted_endpoints.extend([ep_id] * weight)
        
        if not weighted_endpoints:
            return endpoints[0]
        
        endpoint = weighted_endpoints[self.round_robin_index % len(weighted_endpoints)]
        self.round_robin_index += 1
        return endpoint
    
    def _random_select(self, endpoints: List[str]) -> str:
        """隨機選擇"""
        if not endpoints:
            return None
        
        return random.choice(endpoints)
    
    def _least_response_time_select(self, endpoints: List[str]) -> str:
        """最少響應時間選擇"""
        if not endpoints:
            return None
        
        return min(endpoints, key=lambda ep: self.endpoints[ep].avg_response_time)
    
    def _health_based_select(self, endpoints: List[str]) -> str:
        """基於健康度選擇"""
        if not endpoints:
            return None
        
        # 計算健康分數
        def health_score(ep_id):
            ep_info = self.endpoints[ep_id]
            success_rate = ep_info.get_success_rate()
            response_time_score = 100 - min(ep_info.avg_response_time * 10, 100)
            load_score = 100 - min(ep_info.current_connections * 5, 100)
            
            return (success_rate * 0.5 + response_time_score * 0.3 + load_score * 0.2)
        
        return max(endpoints, key=health_score)
    
    def start_request(self, endpoint_id: str):
        """開始請求"""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].current_connections += 1
    
    def end_request(self, endpoint_id: str, response_time: float, success: bool):
        """結束請求"""
        if endpoint_id in self.endpoints:
            endpoint_info = self.endpoints[endpoint_id]
            endpoint_info.current_connections = max(0, endpoint_info.current_connections - 1)
            endpoint_info.update_request_stats(response_time, success)
            
            logger.debug(f"📊 端點統計更新: {endpoint_id} (成功: {success}, 響應時間: {response_time:.2f}s)")
    
    def mark_endpoint_unhealthy(self, endpoint_id: str):
        """標記端點為不健康"""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].is_healthy = False
            logger.warning(f"🔴 端點標記為不健康: {endpoint_id}")
    
    def mark_endpoint_healthy(self, endpoint_id: str):
        """標記端點為健康"""
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].is_healthy = True
            self.endpoints[endpoint_id].consecutive_failures = 0
            logger.info(f"🟢 端點標記為健康: {endpoint_id}")
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """獲取端點統計"""
        stats = {}
        
        for ep_id, ep_info in self.endpoints.items():
            stats[ep_id] = {
                "endpoint_id": ep_info.endpoint_id,
                "weight": ep_info.weight,
                "current_connections": ep_info.current_connections,
                "total_requests": ep_info.total_requests,
                "successful_requests": ep_info.successful_requests,
                "failed_requests": ep_info.failed_requests,
                "success_rate": f"{ep_info.get_success_rate():.2f}%",
                "avg_response_time": f"{ep_info.avg_response_time:.2f}s",
                "is_healthy": ep_info.is_healthy,
                "consecutive_failures": ep_info.consecutive_failures,
                "last_request": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ep_info.last_request_time)) if ep_info.last_request_time else "Never"
            }
        
        return stats
    
    def get_load_distribution(self) -> Dict[str, float]:
        """獲取負載分布"""
        total_requests = sum(ep.total_requests for ep in self.endpoints.values())
        
        if total_requests == 0:
            return {ep_id: 0.0 for ep_id in self.endpoints.keys()}
        
        return {
            ep_id: (ep_info.total_requests / total_requests) * 100
            for ep_id, ep_info in self.endpoints.items()
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """獲取健康狀態摘要"""
        healthy_count = sum(1 for ep in self.endpoints.values() if ep.is_healthy)
        total_count = len(self.endpoints)
        
        return {
            "total_endpoints": total_count,
            "healthy_endpoints": healthy_count,
            "unhealthy_endpoints": total_count - healthy_count,
            "health_ratio": f"{(healthy_count / total_count) * 100:.1f}%" if total_count > 0 else "0%",
            "load_balancing_strategy": self.strategy.value,
            "total_requests": sum(ep.total_requests for ep in self.endpoints.values()),
            "total_failures": sum(ep.failed_requests for ep in self.endpoints.values())
        }
    
    def update_endpoint_weight(self, endpoint_id: str, new_weight: int):
        """更新端點權重"""
        if endpoint_id in self.endpoints:
            old_weight = self.endpoints[endpoint_id].weight
            self.endpoints[endpoint_id].weight = new_weight
            logger.info(f"⚖️ 端點權重更新: {endpoint_id} ({old_weight} -> {new_weight})")
    
    def reset_endpoint_stats(self, endpoint_id: str):
        """重置端點統計"""
        if endpoint_id in self.endpoints:
            ep_info = self.endpoints[endpoint_id]
            ep_info.total_requests = 0
            ep_info.successful_requests = 0
            ep_info.failed_requests = 0
            ep_info.avg_response_time = 0.0
            ep_info.consecutive_failures = 0
            ep_info.is_healthy = True
            logger.info(f"🔄 端點統計重置: {endpoint_id}")
    
    def get_recommended_endpoint(self, request_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """獲取推薦端點及其詳細信息"""
        endpoint_id = self.get_endpoint(request_context)
        
        if not endpoint_id:
            return None
        
        endpoint_info = self.endpoints[endpoint_id]
        
        return {
            "endpoint_id": endpoint_id,
            "weight": endpoint_info.weight,
            "current_connections": endpoint_info.current_connections,
            "success_rate": endpoint_info.get_success_rate(),
            "avg_response_time": endpoint_info.avg_response_time,
            "is_healthy": endpoint_info.is_healthy,
            "recommendation_reason": self._get_recommendation_reason(endpoint_id, request_context)
        }
    
    def _get_recommendation_reason(self, endpoint_id: str, request_context: Optional[Dict[str, Any]]) -> str:
        """獲取推薦原因"""
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return "輪詢策略選擇"
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return f"最少連接數 ({self.endpoints[endpoint_id].current_connections})"
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return f"加權輪詢 (權重: {self.endpoints[endpoint_id].weight})"
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return "隨機選擇"
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return f"最短響應時間 ({self.endpoints[endpoint_id].avg_response_time:.2f}s)"
        elif self.strategy == LoadBalancingStrategy.HEALTH_BASED:
            return f"健康度最佳 (成功率: {self.endpoints[endpoint_id].get_success_rate():.1f}%)"
        else:
            return "默認選擇"
    
    def simulate_load_test(self, request_count: int = 1000) -> Dict[str, Any]:
        """模擬負載測試"""
        results = {ep_id: 0 for ep_id in self.endpoints.keys()}
        
        for _ in range(request_count):
            endpoint_id = self.get_endpoint()
            if endpoint_id:
                results[endpoint_id] += 1
        
        # 計算分布
        distribution = {
            ep_id: (count / request_count) * 100
            for ep_id, count in results.items()
        }
        
        return {
            "request_count": request_count,
            "distribution": distribution,
            "strategy": self.strategy.value,
            "balance_score": self._calculate_balance_score(distribution)
        }
    
    def _calculate_balance_score(self, distribution: Dict[str, float]) -> float:
        """計算負載均衡分數"""
        if not distribution:
            return 0.0
        
        expected_percentage = 100.0 / len(distribution)
        variance = sum((percentage - expected_percentage) ** 2 for percentage in distribution.values()) / len(distribution)
        
        # 分數越高表示負載越均衡
        return max(0, 100 - variance)