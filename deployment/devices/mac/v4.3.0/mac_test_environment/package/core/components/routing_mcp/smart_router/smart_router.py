"""
PowerAutomation 4.0 Smart Router
智慧路由器 - 核心路由决策引擎
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time
from datetime import datetime

# 导入核心模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.parallel_executor import get_executor
from .semantic_analyzer import SemanticAnalyzer, SemanticResult, IntentType
from core.event_bus import EventType, get_event_bus
from core.config import get_config

class RouteStrategy(Enum):
    """路由策略枚举"""
    SEMANTIC_BASED = "semantic_based"      # 基于语义的路由
    LOAD_BALANCED = "load_balanced"        # 负载均衡路由
    CAPABILITY_MATCHED = "capability_matched"  # 能力匹配路由
    PRIORITY_BASED = "priority_based"      # 基于优先级的路由
    HYBRID = "hybrid"                      # 混合路由策略
    INTELLIGENT = "intelligent"            # 智能自适应路由

@dataclass
class RouteRequest:
    """路由请求数据结构"""
    request_id: str
    content: str
    context: Dict[str, Any]
    priority: int = 5
    timeout: int = 30
    required_capabilities: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class RouteResult:
    """路由结果数据结构"""
    target_agent: str
    target_mcp: str
    confidence: float
    reasoning: str
    estimated_time: int
    alternative_routes: List[Dict[str, Any]] = None

class SmartRouter:
    """智慧路由器 - 核心路由决策引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.event_bus = get_event_bus()
        self.executor = get_executor()
        
        # 路由统计
        self.route_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "average_response_time": 0.0,
            "route_accuracy": 0.0
        }
        
        # 注册的MCP和智能体
        self.registered_mcps = {}
        self.registered_agents = {}
        
        # 路由历史和学习数据
        self.route_history = []
        self.performance_metrics = {}
        
        self.logger.info("SmartRouter 4.0 初始化完成")
    
    async def initialize(self):
        """初始化智慧路由器"""
        try:
            # 加载路由配置
            await self._load_route_config()
            
            # 注册事件监听器
            await self._register_event_listeners()
            
            # 启动性能监控
            await self._start_performance_monitoring()
            
            self.logger.info("SmartRouter 初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"SmartRouter 初始化失败: {e}")
            return False
    
    async def route_request(self, request: RouteRequest, strategy: RouteStrategy = RouteStrategy.INTELLIGENT) -> RouteResult:
        """
        智能路由请求
        
        Args:
            request: 路由请求
            strategy: 路由策略
            
        Returns:
            RouteResult: 路由结果
        """
        start_time = time.time()
        self.route_stats["total_requests"] += 1
        
        try:
            self.logger.info(f"开始路由请求: {request.request_id}")
            
            # 语义分析
            semantic_analysis = await self._analyze_semantics(request)
            
            # 能力匹配
            capability_matches = await self._match_capabilities(request, semantic_analysis)
            
            # 负载评估
            load_assessment = await self._assess_load(capability_matches)
            
            # 路由决策
            route_result = await self._make_routing_decision(
                request, semantic_analysis, capability_matches, load_assessment, strategy
            )
            
            # 记录路由历史
            await self._record_route_history(request, route_result, time.time() - start_time)
            
            # 更新统计
            self.route_stats["successful_routes"] += 1
            self._update_performance_stats(time.time() - start_time)
            
            self.logger.info(f"路由成功: {request.request_id} -> {route_result.target_agent}")
            return route_result
            
        except Exception as e:
            self.route_stats["failed_routes"] += 1
            self.logger.error(f"路由失败: {request.request_id}, 错误: {e}")
            
            # 返回默认路由
            return RouteResult(
                target_agent="default_agent",
                target_mcp="command_master",
                confidence=0.1,
                reasoning=f"路由失败，使用默认路由: {str(e)}",
                estimated_time=30
            )
    
    async def _analyze_semantics(self, request: RouteRequest) -> Dict[str, Any]:
        """语义分析"""
        try:
            # 关键词提取
            keywords = await self._extract_keywords(request.content)
            
            # 意图识别
            intent = await self._identify_intent(request.content, keywords)
            
            # 复杂度评估
            complexity = await self._assess_complexity(request.content, intent)
            
            # 领域分类
            domain = await self._classify_domain(request.content, intent)
            
            return {
                "keywords": keywords,
                "intent": intent,
                "complexity": complexity,
                "domain": domain,
                "confidence": 0.85
            }
            
        except Exception as e:
            self.logger.error(f"语义分析失败: {e}")
            return {
                "keywords": [],
                "intent": "unknown",
                "complexity": "medium",
                "domain": "general",
                "confidence": 0.1
            }
    
    async def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 简化的关键词提取逻辑
        keywords = []
        
        # 技术关键词
        tech_keywords = [
            "architect", "design", "develop", "test", "deploy", "monitor",
            "api", "database", "frontend", "backend", "microservice",
            "docker", "kubernetes", "ci/cd", "security", "performance"
        ]
        
        content_lower = content.lower()
        for keyword in tech_keywords:
            if keyword in content_lower:
                keywords.append(keyword)
        
        return keywords
    
    async def _identify_intent(self, content: str, keywords: List[str]) -> str:
        """识别意图"""
        content_lower = content.lower()
        
        # 意图映射
        intent_patterns = {
            "architecture": ["architect", "design", "structure", "pattern"],
            "development": ["develop", "code", "implement", "build"],
            "testing": ["test", "verify", "validate", "check"],
            "deployment": ["deploy", "release", "publish", "launch"],
            "monitoring": ["monitor", "observe", "track", "analyze"],
            "security": ["security", "secure", "protect", "vulnerability"],
            "performance": ["performance", "optimize", "speed", "efficiency"]
        }
        
        for intent, patterns in intent_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                return intent
        
        return "general"
    
    async def _assess_complexity(self, content: str, intent: str) -> str:
        """评估复杂度"""
        # 基于内容长度和关键词密度评估复杂度
        content_length = len(content)
        
        if content_length < 50:
            return "low"
        elif content_length < 200:
            return "medium"
        else:
            return "high"
    
    async def _classify_domain(self, content: str, intent: str) -> str:
        """领域分类"""
        content_lower = content.lower()
        
        domain_keywords = {
            "web": ["web", "frontend", "backend", "html", "css", "javascript"],
            "mobile": ["mobile", "ios", "android", "app", "react native"],
            "data": ["data", "database", "sql", "analytics", "ml", "ai"],
            "devops": ["devops", "docker", "kubernetes", "ci/cd", "deployment"],
            "security": ["security", "auth", "encryption", "vulnerability"],
            "api": ["api", "rest", "graphql", "microservice", "service"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return domain
        
        return "general"
    
    async def _match_capabilities(self, request: RouteRequest, semantic_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """能力匹配"""
        matches = []
        
        # 基于意图匹配智能体
        intent = semantic_analysis.get("intent", "general")
        domain = semantic_analysis.get("domain", "general")
        
        # 智能体能力映射
        agent_capabilities = {
            "architect_agent": {
                "intents": ["architecture", "design"],
                "domains": ["web", "mobile", "api", "general"],
                "capabilities": ["system_design", "architecture_review", "pattern_recommendation"],
                "load": 0.3,
                "performance": 0.9
            },
            "developer_agent": {
                "intents": ["development", "general"],
                "domains": ["web", "mobile", "api", "data"],
                "capabilities": ["code_generation", "implementation", "refactoring"],
                "load": 0.5,
                "performance": 0.85
            },
            "test_agent": {
                "intents": ["testing"],
                "domains": ["web", "mobile", "api", "general"],
                "capabilities": ["test_design", "automation", "quality_assurance"],
                "load": 0.2,
                "performance": 0.88
            },
            "deploy_agent": {
                "intents": ["deployment"],
                "domains": ["devops", "web", "api"],
                "capabilities": ["deployment", "ci_cd", "infrastructure"],
                "load": 0.4,
                "performance": 0.92
            },
            "security_agent": {
                "intents": ["security"],
                "domains": ["security", "web", "api"],
                "capabilities": ["security_analysis", "vulnerability_scan", "compliance"],
                "load": 0.1,
                "performance": 0.95
            },
            "monitor_agent": {
                "intents": ["monitoring", "performance"],
                "domains": ["devops", "web", "api"],
                "capabilities": ["monitoring", "alerting", "performance_analysis"],
                "load": 0.3,
                "performance": 0.87
            }
        }
        
        for agent_name, capabilities in agent_capabilities.items():
            # 计算匹配分数
            intent_match = 1.0 if intent in capabilities["intents"] else 0.3
            domain_match = 1.0 if domain in capabilities["domains"] else 0.5
            
            # 综合评分
            match_score = (intent_match * 0.6 + domain_match * 0.4) * capabilities["performance"]
            
            if match_score > 0.5:  # 阈值过滤
                matches.append({
                    "agent": agent_name,
                    "mcp": "agent_squad",
                    "score": match_score,
                    "load": capabilities["load"],
                    "capabilities": capabilities["capabilities"],
                    "estimated_time": int(30 / capabilities["performance"])
                })
        
        # 按分数排序
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches
    
    async def _assess_load(self, capability_matches: List[Dict[str, Any]]) -> Dict[str, float]:
        """负载评估"""
        load_assessment = {}
        
        for match in capability_matches:
            agent = match["agent"]
            # 模拟负载评估（实际应该从监控系统获取）
            current_load = match["load"]
            load_assessment[agent] = current_load
        
        return load_assessment
    
    async def _make_routing_decision(
        self, 
        request: RouteRequest, 
        semantic_analysis: Dict[str, Any], 
        capability_matches: List[Dict[str, Any]], 
        load_assessment: Dict[str, float],
        strategy: RouteStrategy
    ) -> RouteResult:
        """路由决策"""
        
        if not capability_matches:
            # 没有匹配的智能体，使用默认路由
            return RouteResult(
                target_agent="command_master",
                target_mcp="command_master",
                confidence=0.5,
                reasoning="没有找到匹配的专业智能体，使用CommandMaster处理",
                estimated_time=30
            )
        
        # 根据策略选择最佳路由
        if strategy == RouteStrategy.INTELLIGENT:
            # 智能策略：综合考虑匹配度、负载和性能
            best_match = capability_matches[0]
            
            # 负载调整
            load_factor = 1.0 - load_assessment.get(best_match["agent"], 0.5)
            adjusted_score = best_match["score"] * load_factor
            
            # 检查是否需要重新选择
            for match in capability_matches[1:3]:  # 检查前3个候选
                agent_load_factor = 1.0 - load_assessment.get(match["agent"], 0.5)
                agent_adjusted_score = match["score"] * agent_load_factor
                
                if agent_adjusted_score > adjusted_score:
                    best_match = match
                    adjusted_score = agent_adjusted_score
            
            return RouteResult(
                target_agent=best_match["agent"],
                target_mcp=best_match["mcp"],
                confidence=adjusted_score,
                reasoning=f"智能路由选择: 匹配度{best_match['score']:.2f}, 负载因子{load_factor:.2f}",
                estimated_time=best_match["estimated_time"],
                alternative_routes=[m for m in capability_matches[:3] if m != best_match]
            )
        
        else:
            # 其他策略的简化实现
            best_match = capability_matches[0]
            return RouteResult(
                target_agent=best_match["agent"],
                target_mcp=best_match["mcp"],
                confidence=best_match["score"],
                reasoning=f"使用{strategy.value}策略路由",
                estimated_time=best_match["estimated_time"]
            )
    
    async def _record_route_history(self, request: RouteRequest, result: RouteResult, response_time: float):
        """记录路由历史"""
        history_record = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id,
            "content_hash": hash(request.content),
            "target_agent": result.target_agent,
            "target_mcp": result.target_mcp,
            "confidence": result.confidence,
            "response_time": response_time,
            "success": True
        }
        
        self.route_history.append(history_record)
        
        # 保持历史记录在合理范围内
        if len(self.route_history) > 1000:
            self.route_history = self.route_history[-800:]
    
    def _update_performance_stats(self, response_time: float):
        """更新性能统计"""
        total_requests = self.route_stats["total_requests"]
        current_avg = self.route_stats["average_response_time"]
        
        # 计算新的平均响应时间
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.route_stats["average_response_time"] = new_avg
        
        # 计算路由准确率
        success_rate = self.route_stats["successful_routes"] / total_requests
        self.route_stats["route_accuracy"] = success_rate
    
    async def _load_route_config(self):
        """加载路由配置"""
        # 加载路由配置逻辑
        pass
    
    async def _register_event_listeners(self):
        """注册事件监听器"""
        # 注册事件监听器逻辑
        pass
    
    async def _start_performance_monitoring(self):
        """启动性能监控"""
        # 启动性能监控逻辑
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        return {
            **self.route_stats,
            "registered_mcps": len(self.registered_mcps),
            "registered_agents": len(self.registered_agents),
            "history_records": len(self.route_history)
        }
    
    async def register_mcp(self, mcp_name: str, mcp_info: Dict[str, Any]):
        """注册MCP"""
        self.registered_mcps[mcp_name] = mcp_info
        self.logger.info(f"MCP注册成功: {mcp_name}")
    
    async def register_agent(self, agent_name: str, agent_info: Dict[str, Any]):
        """注册智能体"""
        self.registered_agents[agent_name] = agent_info
        self.logger.info(f"智能体注册成功: {agent_name}")

