"""
PowerAutomation 4.0 Smart Router MCP Interface
智慧路由MCP接口，实现MCP协议通信
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from .smart_router import SmartRouter, RouteRequest, RouteResult
from .semantic_analyzer import SemanticAnalyzer, analyze_semantic
from .route_optimizer import RouteOptimizer, get_route_optimizer
from core.exceptions import MCPCommunicationError, handle_exception
from core.logging_config import get_mcp_logger


@dataclass
class MCPMessage:
    """MCP消息数据结构"""
    id: str
    type: str
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


@dataclass
class MCPCapability:
    """MCP能力描述"""
    name: str
    description: str
    methods: List[str]
    version: str


class SmartRouterMCPInterface:
    """智慧路由MCP接口"""
    
    def __init__(self):
        self.logger = get_mcp_logger()
        self.smart_router = SmartRouter()
        self.semantic_analyzer = SemanticAnalyzer()
        self.route_optimizer = get_route_optimizer()
        
        # MCP状态
        self.is_initialized = False
        self.session_id = str(uuid.uuid4())
        self.capabilities = self._define_capabilities()
        
        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "route_request": self._handle_route_request,
            "analyze_semantic": self._handle_analyze_semantic,
            "optimize_route": self._handle_optimize_route,
            "get_capabilities": self._handle_get_capabilities,
            "get_status": self._handle_get_status,
            "get_metrics": self._handle_get_metrics,
            "shutdown": self._handle_shutdown
        }
        
        # 统计信息
        self.stats = {
            "messages_processed": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "semantic_analyses": 0,
            "optimizations": 0,
            "uptime_start": datetime.now()
        }
    
    def _define_capabilities(self) -> List[MCPCapability]:
        """定义MCP能力"""
        return [
            MCPCapability(
                name="smart_routing",
                description="智能路由决策和任务分发",
                methods=["route_request", "get_routing_stats"],
                version="4.0.0"
            ),
            MCPCapability(
                name="semantic_analysis",
                description="语义分析和意图识别",
                methods=["analyze_semantic", "get_intent_types"],
                version="4.0.0"
            ),
            MCPCapability(
                name="route_optimization",
                description="路由优化和性能提升",
                methods=["optimize_route", "get_optimization_stats"],
                version="4.0.0"
            ),
            MCPCapability(
                name="system_management",
                description="系统管理和监控",
                methods=["get_status", "get_metrics", "shutdown"],
                version="4.0.0"
            )
        ]
    
    async def initialize(self) -> bool:
        """初始化MCP接口"""
        try:
            # 初始化智慧路由器
            await self.smart_router.initialize()
            
            self.is_initialized = True
            self.logger.info(f"智慧路由MCP接口初始化成功，会话ID: {self.session_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"智慧路由MCP接口初始化失败: {e}")
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP消息"""
        try:
            # 解析消息
            mcp_message = self._parse_message(message)
            
            # 更新统计
            self.stats["messages_processed"] += 1
            
            # 路由到处理器
            if mcp_message.method in self.message_handlers:
                handler = self.message_handlers[mcp_message.method]
                result = await handler(mcp_message.params or {})
                
                # 创建响应消息
                response = MCPMessage(
                    id=mcp_message.id,
                    type="response",
                    result=result,
                    timestamp=datetime.now().isoformat()
                )
                
                return asdict(response)
            else:
                # 未知方法
                error_response = MCPMessage(
                    id=mcp_message.id,
                    type="error",
                    error={
                        "code": -32601,
                        "message": f"未知方法: {mcp_message.method}"
                    },
                    timestamp=datetime.now().isoformat()
                )
                
                return asdict(error_response)
                
        except Exception as e:
            self.logger.error(f"处理MCP消息失败: {e}")
            
            # 创建错误响应
            error_response = MCPMessage(
                id=message.get("id", "unknown"),
                type="error",
                error={
                    "code": -32603,
                    "message": f"内部错误: {str(e)}"
                },
                timestamp=datetime.now().isoformat()
            )
            
            return asdict(error_response)
    
    def _parse_message(self, message: Dict[str, Any]) -> MCPMessage:
        """解析MCP消息"""
        return MCPMessage(
            id=message.get("id", str(uuid.uuid4())),
            type=message.get("type", "request"),
            method=message.get("method"),
            params=message.get("params"),
            result=message.get("result"),
            error=message.get("error"),
            timestamp=message.get("timestamp", datetime.now().isoformat())
        )
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        if not self.is_initialized:
            success = await self.initialize()
        else:
            success = True
        
        return {
            "success": success,
            "session_id": self.session_id,
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "version": "4.0.0"
        }
    
    async def _handle_route_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理路由请求"""
        try:
            # 创建路由请求
            route_request = RouteRequest(
                request_id=params.get("request_id", str(uuid.uuid4())),
                content=params.get("content", ""),
                context=params.get("context", {}),
                priority=params.get("priority", 5),
                timeout=params.get("timeout", 30),
                required_capabilities=params.get("required_capabilities", []),
                metadata=params.get("metadata", {})
            )
            
            # 执行路由
            route_result = await self.smart_router.route_request(route_request)
            
            # 更新统计
            if route_result.confidence > 0.5:
                self.stats["successful_routes"] += 1
            else:
                self.stats["failed_routes"] += 1
            
            return {
                "success": True,
                "route_result": asdict(route_result),
                "request_id": route_request.request_id
            }
            
        except Exception as e:
            self.stats["failed_routes"] += 1
            self.logger.error(f"路由请求处理失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "request_id": params.get("request_id", "unknown")
            }
    
    async def _handle_analyze_semantic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理语义分析请求"""
        try:
            text = params.get("text", "")
            context = params.get("context", {})
            
            # 执行语义分析
            semantic_result = analyze_semantic(text, context)
            
            # 更新统计
            self.stats["semantic_analyses"] += 1
            
            return {
                "success": True,
                "semantic_result": {
                    "intent": semantic_result.intent.value,
                    "confidence": semantic_result.confidence,
                    "entities": semantic_result.entities,
                    "keywords": semantic_result.keywords,
                    "context": semantic_result.context
                }
            }
            
        except Exception as e:
            self.logger.error(f"语义分析失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_optimize_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理路由优化请求"""
        try:
            route_request = params.get("route_request", {})
            available_agents = params.get("available_agents", [])
            
            # 执行路由优化
            optimization_result = await self.route_optimizer.optimize_route(
                route_request, available_agents
            )
            
            # 更新统计
            self.stats["optimizations"] += 1
            
            return {
                "success": True,
                "optimization_result": {
                    "improvement_score": optimization_result.improvement_score,
                    "optimization_time": optimization_result.optimization_time,
                    "optimized_route": optimization_result.optimized_route
                }
            }
            
        except Exception as e:
            self.logger.error(f"路由优化失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_get_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取能力请求"""
        return {
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "session_id": self.session_id,
            "version": "4.0.0"
        }
    
    async def _handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取状态请求"""
        uptime = datetime.now() - self.stats["uptime_start"]
        
        return {
            "status": "active" if self.is_initialized else "inactive",
            "session_id": self.session_id,
            "uptime_seconds": uptime.total_seconds(),
            "is_initialized": self.is_initialized,
            "capabilities_count": len(self.capabilities)
        }
    
    async def _handle_get_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取指标请求"""
        # 计算成功率
        total_routes = self.stats["successful_routes"] + self.stats["failed_routes"]
        success_rate = (self.stats["successful_routes"] / total_routes * 100) if total_routes > 0 else 0
        
        # 获取路由器指标
        router_stats = await self.smart_router.get_stats()
        
        # 获取优化器指标
        optimizer_stats = self.route_optimizer.get_optimization_stats()
        
        return {
            "mcp_stats": self.stats.copy(),
            "success_rate": success_rate,
            "router_stats": router_stats,
            "optimizer_stats": optimizer_stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理关闭请求"""
        try:
            # 清理资源
            await self.smart_router.shutdown()
            
            self.is_initialized = False
            self.logger.info("智慧路由MCP接口已关闭")
            
            return {
                "success": True,
                "message": "智慧路由MCP接口已成功关闭"
            }
            
        except Exception as e:
            self.logger.error(f"关闭MCP接口失败: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_notification(self, notification_type: str, data: Dict[str, Any]) -> None:
        """发送通知消息"""
        notification = MCPMessage(
            id=str(uuid.uuid4()),
            type="notification",
            method=notification_type,
            params=data,
            timestamp=datetime.now().isoformat()
        )
        
        # 这里应该发送到MCP协调器或其他订阅者
        self.logger.info(f"发送通知: {notification_type}")
    
    def get_interface_info(self) -> Dict[str, Any]:
        """获取接口信息"""
        return {
            "name": "SmartRouterMCP",
            "version": "4.0.0",
            "description": "智慧路由MCP - 负责智能路由、语义分析和任务分发",
            "capabilities": [asdict(cap) for cap in self.capabilities],
            "session_id": self.session_id,
            "is_initialized": self.is_initialized,
            "stats": self.stats
        }


# 全局智慧路由MCP接口实例
_smart_router_mcp = None


def get_smart_router_mcp() -> SmartRouterMCPInterface:
    """获取全局智慧路由MCP接口实例"""
    global _smart_router_mcp
    if _smart_router_mcp is None:
        _smart_router_mcp = SmartRouterMCPInterface()
    return _smart_router_mcp

