#!/usr/bin/env python3
"""
工具协作网络
PowerAutomation 4.1 - 多工具协同工作和知识共享网络

功能特性:
- 多工具协作编排
- 智能协作模式识别
- 工具间知识共享
- 协作效果优化
- 动态协作网络
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict, deque
import uuid

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CollaborationMode(Enum):
    """协作模式枚举"""
    PIPELINE = "pipeline"  # 流水线模式
    PARALLEL = "parallel"  # 并行模式
    HIERARCHICAL = "hierarchical"  # 层次模式
    MESH = "mesh"  # 网格模式
    ADAPTIVE = "adaptive"  # 自适应模式

class CollaborationStatus(Enum):
    """协作状态枚举"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    OPTIMIZING = "optimizing"

class MessageType(Enum):
    """消息类型枚举"""
    DATA_TRANSFER = "data_transfer"
    CONTROL_SIGNAL = "control_signal"
    STATUS_UPDATE = "status_update"
    KNOWLEDGE_SHARE = "knowledge_share"
    ERROR_REPORT = "error_report"
    OPTIMIZATION_HINT = "optimization_hint"

@dataclass
class CollaborationMessage:
    """协作消息"""
    message_id: str
    sender_tool: str
    receiver_tool: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5  # 1-10, 10最高
    requires_response: bool = False
    correlation_id: Optional[str] = None

@dataclass
class ToolNode:
    """工具节点"""
    tool_id: str
    tool_type: str
    capabilities: List[str]
    current_status: str = "idle"
    current_load: float = 0.0
    max_connections: int = 10
    active_connections: Set[str] = field(default_factory=set)
    message_queue: deque = field(default_factory=deque)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    knowledge_base: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    participating_tools: List[str]
    collaboration_mode: CollaborationMode
    status: CollaborationStatus = CollaborationStatus.INITIALIZING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    objective: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    message_history: List[CollaborationMessage] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

class ToolCollaborationNetwork:
    """工具协作网络"""
    
    def __init__(self):
        self.tools: Dict[str, ToolNode] = {}
        self.collaboration_graph = nx.DiGraph()
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.collaboration_patterns: Dict[str, Dict] = {}
        self.knowledge_graph = nx.Graph()
        
        # 协作统计
        self.collaboration_stats = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "average_session_duration": 0.0,
            "total_messages": 0,
            "knowledge_transfers": 0,
            "optimization_improvements": 0.0
        }
        
        # 消息路由表
        self.message_routes: Dict[str, List[str]] = {}
        
        # 性能优化器
        self.optimization_engine = CollaborationOptimizer()
        
        logger.info("工具协作网络初始化完成")
    
    async def register_tool(self, tool_id: str, tool_type: str, capabilities: List[str]):
        """注册工具到协作网络"""
        try:
            tool_node = ToolNode(
                tool_id=tool_id,
                tool_type=tool_type,
                capabilities=capabilities
            )
            
            self.tools[tool_id] = tool_node
            self.collaboration_graph.add_node(tool_id, **tool_node.__dict__)
            
            # 初始化知识图谱节点
            self.knowledge_graph.add_node(tool_id, tool_type=tool_type, capabilities=capabilities)
            
            logger.info(f"工具已注册到协作网络: {tool_id}")
            
        except Exception as e:
            logger.error(f"注册工具失败: {e}")
            raise
    
    async def create_collaboration_session(self, tools: List[str], objective: str, 
                                         mode: CollaborationMode = CollaborationMode.ADAPTIVE,
                                         context: Dict[str, Any] = None) -> str:
        """创建协作会话"""
        try:
            session_id = str(uuid.uuid4())
            
            # 验证工具可用性
            for tool_id in tools:
                if tool_id not in self.tools:
                    raise ValueError(f"工具不存在: {tool_id}")
            
            # 创建协作会话
            session = CollaborationSession(
                session_id=session_id,
                participating_tools=tools,
                collaboration_mode=mode,
                objective=objective,
                context=context or {}
            )
            
            self.active_sessions[session_id] = session
            
            # 建立工具间连接
            await self._establish_tool_connections(session)
            
            # 优化协作模式
            if mode == CollaborationMode.ADAPTIVE:
                session.collaboration_mode = await self._determine_optimal_mode(tools, objective)
            
            session.status = CollaborationStatus.ACTIVE
            self.collaboration_stats["total_sessions"] += 1
            
            logger.info(f"协作会话已创建: {session_id} with tools: {tools}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建协作会话失败: {e}")
            raise
    
    async def _establish_tool_connections(self, session: CollaborationSession):
        """建立工具间连接"""
        tools = session.participating_tools
        mode = session.collaboration_mode
        
        # 根据协作模式建立连接
        if mode == CollaborationMode.PIPELINE:
            # 流水线：顺序连接
            for i in range(len(tools) - 1):
                await self._create_connection(tools[i], tools[i + 1], session.session_id)
        
        elif mode == CollaborationMode.PARALLEL:
            # 并行：星型连接（第一个工具为中心）
            center_tool = tools[0]
            for tool in tools[1:]:
                await self._create_connection(center_tool, tool, session.session_id)
                await self._create_connection(tool, center_tool, session.session_id)
        
        elif mode == CollaborationMode.HIERARCHICAL:
            # 层次：树型连接
            await self._create_hierarchical_connections(tools, session.session_id)
        
        elif mode == CollaborationMode.MESH:
            # 网格：全连接
            for i, tool1 in enumerate(tools):
                for tool2 in tools[i + 1:]:
                    await self._create_connection(tool1, tool2, session.session_id)
                    await self._create_connection(tool2, tool1, session.session_id)
    
    async def _create_connection(self, from_tool: str, to_tool: str, session_id: str):
        """创建工具间连接"""
        # 添加到协作图
        self.collaboration_graph.add_edge(from_tool, to_tool, session_id=session_id)
        
        # 更新工具节点连接
        self.tools[from_tool].active_connections.add(to_tool)
        self.tools[to_tool].active_connections.add(from_tool)
        
        # 建立消息路由
        if from_tool not in self.message_routes:
            self.message_routes[from_tool] = []
        self.message_routes[from_tool].append(to_tool)
    
    async def _create_hierarchical_connections(self, tools: List[str], session_id: str):
        """创建层次连接"""
        # 简化的二叉树结构
        for i, tool in enumerate(tools):
            left_child = 2 * i + 1
            right_child = 2 * i + 2
            
            if left_child < len(tools):
                await self._create_connection(tool, tools[left_child], session_id)
            if right_child < len(tools):
                await self._create_connection(tool, tools[right_child], session_id)
    
    async def _determine_optimal_mode(self, tools: List[str], objective: str) -> CollaborationMode:
        """确定最优协作模式"""
        # 基于工具类型和目标分析最优模式
        tool_types = [self.tools[tool_id].tool_type for tool_id in tools]
        
        # 简化的模式选择逻辑
        if len(tools) <= 2:
            return CollaborationMode.PIPELINE
        elif "sequential" in objective.lower():
            return CollaborationMode.PIPELINE
        elif "parallel" in objective.lower():
            return CollaborationMode.PARALLEL
        elif len(set(tool_types)) > len(tools) * 0.7:  # 工具类型多样
            return CollaborationMode.MESH
        else:
            return CollaborationMode.HIERARCHICAL
    
    async def send_message(self, session_id: str, sender_tool: str, receiver_tool: str,
                          message_type: MessageType, content: Dict[str, Any],
                          priority: int = 5) -> str:
        """发送协作消息"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"协作会话不存在: {session_id}")
            
            session = self.active_sessions[session_id]
            
            # 创建消息
            message = CollaborationMessage(
                message_id=str(uuid.uuid4()),
                sender_tool=sender_tool,
                receiver_tool=receiver_tool,
                message_type=message_type,
                content=content,
                priority=priority
            )
            
            # 添加到会话历史
            session.message_history.append(message)
            
            # 路由消息
            await self._route_message(message, session)
            
            # 更新统计
            self.collaboration_stats["total_messages"] += 1
            
            # 处理知识共享
            if message_type == MessageType.KNOWLEDGE_SHARE:
                await self._process_knowledge_sharing(message, session)
            
            logger.info(f"消息已发送: {sender_tool} -> {receiver_tool}")
            return message.message_id
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise
    
    async def _route_message(self, message: CollaborationMessage, session: CollaborationSession):
        """路由消息到目标工具"""
        receiver_tool = message.receiver_tool
        
        if receiver_tool in self.tools:
            # 添加到接收工具的消息队列
            receiver_node = self.tools[receiver_tool]
            receiver_node.message_queue.append(message)
            
            # 按优先级排序
            receiver_node.message_queue = deque(
                sorted(receiver_node.message_queue, key=lambda m: m.priority, reverse=True)
            )
    
    async def _process_knowledge_sharing(self, message: CollaborationMessage, 
                                       session: CollaborationSession):
        """处理知识共享"""
        sender = message.sender_tool
        receiver = message.receiver_tool
        knowledge = message.content.get("knowledge", {})
        
        # 更新接收工具的知识库
        if receiver in self.tools:
            self.tools[receiver].knowledge_base.update(knowledge)
        
        # 在知识图谱中添加连接
        self.knowledge_graph.add_edge(sender, receiver, 
                                    knowledge_type=message.content.get("type", "general"),
                                    timestamp=message.timestamp)
        
        self.collaboration_stats["knowledge_transfers"] += 1
        logger.info(f"知识共享完成: {sender} -> {receiver}")
    
    async def get_tool_messages(self, tool_id: str, limit: int = 10) -> List[CollaborationMessage]:
        """获取工具的消息"""
        if tool_id not in self.tools:
            return []
        
        tool_node = self.tools[tool_id]
        messages = list(tool_node.message_queue)[:limit]
        
        # 清空已读取的消息
        for _ in range(min(limit, len(tool_node.message_queue))):
            if tool_node.message_queue:
                tool_node.message_queue.popleft()
        
        return messages
    
    async def update_tool_status(self, tool_id: str, status: str, metrics: Dict[str, float] = None):
        """更新工具状态"""
        if tool_id in self.tools:
            tool_node = self.tools[tool_id]
            tool_node.current_status = status
            
            if metrics:
                tool_node.performance_metrics.update(metrics)
            
            logger.info(f"工具状态已更新: {tool_id} -> {status}")
    
    async def end_collaboration_session(self, session_id: str) -> Dict[str, Any]:
        """结束协作会话"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"协作会话不存在: {session_id}")
            
            session = self.active_sessions[session_id]
            session.status = CollaborationStatus.COMPLETED
            session.end_time = datetime.now()
            
            # 计算会话指标
            duration = (session.end_time - session.start_time).total_seconds()
            session.performance_metrics["duration"] = duration
            session.performance_metrics["message_count"] = len(session.message_history)
            
            # 清理连接
            await self._cleanup_session_connections(session)
            
            # 更新统计
            self._update_collaboration_stats(session)
            
            # 移除活跃会话
            del self.active_sessions[session_id]
            
            logger.info(f"协作会话已结束: {session_id}")
            return session.performance_metrics
            
        except Exception as e:
            logger.error(f"结束协作会话失败: {e}")
            raise
    
    async def _cleanup_session_connections(self, session: CollaborationSession):
        """清理会话连接"""
        tools = session.participating_tools
        
        # 移除工具间连接
        for tool in tools:
            if tool in self.tools:
                tool_node = self.tools[tool]
                # 清理与其他会话工具的连接
                for other_tool in tools:
                    if other_tool != tool:
                        tool_node.active_connections.discard(other_tool)
        
        # 清理协作图中的边
        edges_to_remove = [
            (u, v) for u, v, data in self.collaboration_graph.edges(data=True)
            if data.get("session_id") == session.session_id
        ]
        
        for edge in edges_to_remove:
            self.collaboration_graph.remove_edge(*edge)
    
    def _update_collaboration_stats(self, session: CollaborationSession):
        """更新协作统计"""
        if session.status == CollaborationStatus.COMPLETED:
            self.collaboration_stats["successful_sessions"] += 1
        
        # 更新平均会话时长
        duration = session.performance_metrics.get("duration", 0)
        total_sessions = self.collaboration_stats["total_sessions"]
        
        avg_duration = self.collaboration_stats["average_session_duration"]
        new_avg = ((avg_duration * (total_sessions - 1)) + duration) / total_sessions
        self.collaboration_stats["average_session_duration"] = new_avg
    
    async def analyze_collaboration_patterns(self) -> Dict[str, Any]:
        """分析协作模式"""
        patterns = {
            "most_collaborative_tools": [],
            "common_collaboration_modes": {},
            "knowledge_flow_analysis": {},
            "performance_insights": {}
        }
        
        # 分析最活跃的协作工具
        tool_collaboration_count = defaultdict(int)
        for session in self.active_sessions.values():
            for tool in session.participating_tools:
                tool_collaboration_count[tool] += 1
        
        patterns["most_collaborative_tools"] = sorted(
            tool_collaboration_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 分析常用协作模式
        mode_usage = defaultdict(int)
        for session in self.active_sessions.values():
            mode_usage[session.collaboration_mode.value] += 1
        
        patterns["common_collaboration_modes"] = dict(mode_usage)
        
        # 知识流分析
        if self.knowledge_graph.number_of_edges() > 0:
            centrality = nx.betweenness_centrality(self.knowledge_graph)
            patterns["knowledge_flow_analysis"] = {
                "knowledge_hubs": sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:3],
                "knowledge_connections": self.knowledge_graph.number_of_edges()
            }
        
        return patterns
    
    async def optimize_collaboration_network(self) -> Dict[str, Any]:
        """优化协作网络"""
        try:
            optimization_results = await self.optimization_engine.optimize_network(
                self.tools, self.collaboration_graph, self.collaboration_stats
            )
            
            # 应用优化建议
            if optimization_results.get("suggested_connections"):
                for connection in optimization_results["suggested_connections"]:
                    await self._create_connection(
                        connection["from"], connection["to"], "optimization"
                    )
            
            self.collaboration_stats["optimization_improvements"] += optimization_results.get("improvement_score", 0)
            
            logger.info("协作网络优化完成")
            return optimization_results
            
        except Exception as e:
            logger.error(f"优化协作网络失败: {e}")
            return {}
    
    async def get_network_status(self) -> Dict[str, Any]:
        """获取网络状态"""
        return {
            "total_tools": len(self.tools),
            "active_sessions": len(self.active_sessions),
            "total_connections": self.collaboration_graph.number_of_edges(),
            "collaboration_stats": self.collaboration_stats,
            "tool_status": {
                tool_id: {
                    "status": tool.current_status,
                    "load": tool.current_load,
                    "connections": len(tool.active_connections),
                    "message_queue_size": len(tool.message_queue)
                }
                for tool_id, tool in self.tools.items()
            }
        }

class CollaborationOptimizer:
    """协作优化器"""
    
    async def optimize_network(self, tools: Dict[str, ToolNode], 
                             collaboration_graph: nx.DiGraph,
                             stats: Dict[str, Any]) -> Dict[str, Any]:
        """优化协作网络"""
        optimization_results = {
            "suggested_connections": [],
            "performance_improvements": [],
            "improvement_score": 0.0
        }
        
        # 分析网络连通性
        if collaboration_graph.number_of_nodes() > 1:
            # 识别孤立节点
            isolated_nodes = list(nx.isolates(collaboration_graph))
            
            # 为孤立节点建议连接
            for node in isolated_nodes:
                # 找到最相似的工具
                similar_tool = self._find_most_similar_tool(node, tools)
                if similar_tool:
                    optimization_results["suggested_connections"].append({
                        "from": node,
                        "to": similar_tool,
                        "reason": "连接孤立节点"
                    })
        
        # 分析负载均衡
        tool_loads = {tool_id: tool.current_load for tool_id, tool in tools.items()}
        if tool_loads:
            avg_load = sum(tool_loads.values()) / len(tool_loads)
            overloaded_tools = [tool_id for tool_id, load in tool_loads.items() if load > avg_load * 1.5]
            
            for tool_id in overloaded_tools:
                optimization_results["performance_improvements"].append({
                    "tool": tool_id,
                    "issue": "负载过高",
                    "suggestion": "考虑负载分散或增加并行处理"
                })
        
        # 计算改进分数
        optimization_results["improvement_score"] = len(optimization_results["suggested_connections"]) * 0.1
        
        return optimization_results
    
    def _find_most_similar_tool(self, target_tool: str, tools: Dict[str, ToolNode]) -> Optional[str]:
        """找到最相似的工具"""
        if target_tool not in tools:
            return None
        
        target_capabilities = set(tools[target_tool].capabilities)
        best_match = None
        best_similarity = 0.0
        
        for tool_id, tool in tools.items():
            if tool_id == target_tool:
                continue
            
            tool_capabilities = set(tool.capabilities)
            similarity = len(target_capabilities & tool_capabilities) / len(target_capabilities | tool_capabilities)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = tool_id
        
        return best_match if best_similarity > 0.3 else None

# 示例使用
async def main():
    """示例主函数"""
    network = ToolCollaborationNetwork()
    
    # 注册工具
    await network.register_tool("analyzer", "analysis", ["code_analysis", "pattern_detection"])
    await network.register_tool("generator", "generation", ["code_generation", "template_creation"])
    await network.register_tool("optimizer", "optimization", ["performance_optimization", "refactoring"])
    
    # 创建协作会话
    session_id = await network.create_collaboration_session(
        tools=["analyzer", "generator", "optimizer"],
        objective="完整的代码优化流程",
        mode=CollaborationMode.PIPELINE
    )
    
    # 发送协作消息
    await network.send_message(
        session_id=session_id,
        sender_tool="analyzer",
        receiver_tool="generator",
        message_type=MessageType.DATA_TRANSFER,
        content={"analysis_result": "代码复杂度较高，需要重构"}
    )
    
    # 获取网络状态
    status = await network.get_network_status()
    print(f"网络状态: {status}")
    
    # 分析协作模式
    patterns = await network.analyze_collaboration_patterns()
    print(f"协作模式: {patterns}")

if __name__ == "__main__":
    asyncio.run(main())

