"""
MCP Ecosystem Router - 智能路由器
为ClaudEditor 4.3提供智能的MCP组件路由和协调

集成组件:
- Zen MCP (工具生态系统)
- Trae Agent MCP (软件工程引擎)  
- Agents MCP (多代理协作)
- Claude SDK MCP (Claude专家系统)
- Claude Unified MCP (统一接口)
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime, timedelta

# PowerAutomation AICore组件导入
try:
    from ..intelligence.enhanced_ai_assistant import EnhancedAIAssistant, AIRequest, AIResponse, AssistantMode
    from ...zen_mcp.zen_tool_registry import ZenToolRegistry, ZenTool
    from ...trae_agent_mcp.trae_agent_engine import TraeAgentEngine, TaskType as TraeTaskType
    from ...agents_mcp.agent_coordinator import AgentCoordinator
    from ...claude_mcp.claude_sdk import ClaudeSDKMCP
except ImportError as e:
    logging.warning(f"Some MCP components not available: {e}")

class MCPComponentType(Enum):
    """MCP组件类型"""
    ZEN_MCP = "zen_mcp"                    # Zen工具生态系统
    TRAE_AGENT_MCP = "trae_agent_mcp"      # Trae软件工程引擎
    AGENTS_MCP = "agents_mcp"              # 多代理协作系统
    CLAUDE_SDK_MCP = "claude_sdk_mcp"      # Claude专家系统
    CLAUDE_UNIFIED_MCP = "claude_unified_mcp"  # 统一接口层
    DIRECT_API = "direct_api"              # 直接API调用

class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"        # 0.0 - 0.3
    MODERATE = "moderate"    # 0.3 - 0.6
    COMPLEX = "complex"      # 0.6 - 0.8
    VERY_COMPLEX = "very_complex"  # 0.8 - 1.0

class TaskCategory(Enum):
    """任务分类"""
    CODE_COMPLETION = "code_completion"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    PROJECT_MANAGEMENT = "project_management"
    GENERAL_QUESTION = "general_question"

@dataclass
class RoutingDecision:
    """路由决策"""
    component: MCPComponentType
    confidence: float
    reasoning: str
    estimated_time: float
    estimated_cost: float
    fallback_components: List[MCPComponentType] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    required_agents: List[str] = field(default_factory=list)

@dataclass
class RoutingMetrics:
    """路由指标"""
    total_requests: int = 0
    successful_routes: int = 0
    failed_routes: int = 0
    avg_response_time: float = 0.0
    component_usage: Dict[str, int] = field(default_factory=dict)
    user_satisfaction: float = 0.0
    cost_efficiency: float = 0.0

class MCPEcosystemRouter:
    """
    MCP生态系统智能路由器
    负责分析AI请求并路由到最适合的MCP组件
    """
    
    def __init__(self,
                 claude_api_key: Optional[str] = None,
                 gemini_api_key: Optional[str] = None,
                 enable_zen_mcp: bool = True,
                 enable_trae_agent: bool = True,
                 enable_agents_mcp: bool = True,
                 enable_claude_sdk: bool = True):
        """
        初始化MCP生态系统路由器
        
        Args:
            claude_api_key: Claude API密钥
            gemini_api_key: Gemini API密钥
            enable_zen_mcp: 是否启用Zen MCP
            enable_trae_agent: 是否启用Trae Agent MCP
            enable_agents_mcp: 是否启用Agents MCP
            enable_claude_sdk: 是否启用Claude SDK MCP
        """
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.enable_zen_mcp = enable_zen_mcp
        self.enable_trae_agent = enable_trae_agent
        self.enable_agents_mcp = enable_agents_mcp
        self.enable_claude_sdk = enable_claude_sdk
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # MCP组件实例
        self.zen_mcp: Optional[ZenToolRegistry] = None
        self.trae_agent: Optional[TraeAgentEngine] = None
        self.agents_mcp: Optional[AgentCoordinator] = None
        self.claude_sdk: Optional[ClaudeSDKMCP] = None
        
        # 路由配置
        self.routing_config = {
            'complexity_thresholds': {
                'zen_mcp': 0.4,
                'trae_agent': 0.6,
                'agents_mcp': 0.8,
                'claude_sdk': 0.3
            },
            'response_time_limits': {
                'zen_mcp': 20.0,
                'trae_agent': 30.0,
                'agents_mcp': 60.0,
                'claude_sdk': 25.0,
                'direct_api': 15.0
            },
            'cost_weights': {
                'zen_mcp': 0.3,
                'trae_agent': 0.5,
                'agents_mcp': 0.8,
                'claude_sdk': 0.4,
                'direct_api': 0.2
            }
        }
        
        # 路由历史和指标
        self.routing_history: List[Dict[str, Any]] = []
        self.metrics = RoutingMetrics()
        
        # 任务分类器
        self.task_classifiers = self._initialize_task_classifiers()
        
        # 性能监控
        self.performance_history: Dict[str, List[float]] = {
            component.value: [] for component in MCPComponentType
        }
    
    async def initialize(self):
        """初始化路由器和所有MCP组件"""
        try:
            # 初始化Zen MCP
            if self.enable_zen_mcp:
                try:
                    self.zen_mcp = ZenToolRegistry()
                    await self.zen_mcp.initialize()
                    self.logger.info("Zen MCP initialized")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize Zen MCP: {e}")
                    self.enable_zen_mcp = False
            
            # 初始化Trae Agent MCP
            if self.enable_trae_agent:
                try:
                    self.trae_agent = TraeAgentEngine()
                    await self.trae_agent.initialize()
                    self.logger.info("Trae Agent MCP initialized")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize Trae Agent: {e}")
                    self.enable_trae_agent = False
            
            # 初始化Agents MCP
            if self.enable_agents_mcp:
                try:
                    self.agents_mcp = AgentCoordinator()
                    await self.agents_mcp.initialize()
                    self.logger.info("Agents MCP initialized")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize Agents MCP: {e}")
                    self.enable_agents_mcp = False
            
            # 初始化Claude SDK MCP
            if self.enable_claude_sdk:
                try:
                    self.claude_sdk = ClaudeSDKMCP(
                        api_key=self.claude_api_key,
                        gemini_api_key=self.gemini_api_key
                    )
                    await self.claude_sdk.initialize()
                    self.logger.info("Claude SDK MCP initialized")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize Claude SDK: {e}")
                    self.enable_claude_sdk = False
            
            self.logger.info("MCP Ecosystem Router initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP Ecosystem Router: {e}")
            raise
    
    async def route_request(self, ai_request: AIRequest) -> Tuple[RoutingDecision, AIResponse]:
        """
        路由AI请求到最适合的MCP组件
        
        Args:
            ai_request: AI请求
            
        Returns:
            (路由决策, AI响应)
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # 1. 分析请求
            analysis = await self._analyze_request(ai_request)
            
            # 2. 做出路由决策
            routing_decision = await self._make_routing_decision(analysis, ai_request)
            
            # 3. 执行路由
            response = await self._execute_routing(routing_decision, ai_request)
            
            # 4. 记录指标
            processing_time = time.time() - start_time
            await self._record_routing_metrics(
                request_id, routing_decision, response, processing_time
            )
            
            return routing_decision, response
            
        except Exception as e:
            self.logger.error(f"Routing failed for request {request_id}: {e}")
            
            # 故障转移到直接API调用
            fallback_decision = RoutingDecision(
                component=MCPComponentType.DIRECT_API,
                confidence=0.5,
                reasoning=f"Fallback due to routing error: {str(e)}",
                estimated_time=15.0,
                estimated_cost=0.2
            )
            
            # 这里应该有直接API调用的实现
            fallback_response = AIResponse(
                content=f"Sorry, I encountered an error while processing your request: {str(e)}",
                model="fallback",
                usage={'total_tokens': 0},
                finish_reason='error',
                request_id=request_id
            )
            
            return fallback_decision, fallback_response
    
    async def _analyze_request(self, ai_request: AIRequest) -> Dict[str, Any]:
        """分析AI请求的特征"""
        analysis = {
            'complexity': self._calculate_complexity(ai_request),
            'category': self._classify_task_category(ai_request),
            'context_richness': self._analyze_context_richness(ai_request),
            'urgency': self._assess_urgency(ai_request),
            'resource_requirements': self._estimate_resource_requirements(ai_request),
            'user_preferences': self._extract_user_preferences(ai_request)
        }
        
        return analysis
    
    def _calculate_complexity(self, ai_request: AIRequest) -> float:
        """计算请求复杂度 (0-1)"""
        complexity_score = 0.0
        
        # 1. 提示词长度和复杂度 (0.3权重)
        prompt_words = len(ai_request.prompt.split())
        prompt_complexity = min(prompt_words / 100, 1.0) * 0.3
        complexity_score += prompt_complexity
        
        # 2. 上下文复杂度 (0.3权重)
        if ai_request.context:
            context_factors = [
                'project_type' in ai_request.context,
                'files_count' in ai_request.context,
                'complexity' in ai_request.context,
                'tech_stack' in ai_request.context,
                len(ai_request.context) > 5
            ]
            context_complexity = sum(context_factors) / len(context_factors) * 0.3
            complexity_score += context_complexity
        
        # 3. 任务类型复杂度 (0.2权重)
        high_complexity_keywords = [
            'architecture', 'design', 'refactor', 'optimize', 'analyze',
            'review', 'migrate', 'integrate', 'scale', 'performance'
        ]
        keyword_matches = sum(1 for keyword in high_complexity_keywords 
                             if keyword in ai_request.prompt.lower())
        keyword_complexity = min(keyword_matches / 3, 1.0) * 0.2
        complexity_score += keyword_complexity
        
        # 4. 专家系统需求 (0.2权重)
        if ai_request.use_expert_system:
            complexity_score += 0.2
        
        return min(complexity_score, 1.0)
    
    def _classify_task_category(self, ai_request: AIRequest) -> TaskCategory:
        """分类任务类型"""
        prompt_lower = ai_request.prompt.lower()
        
        # 使用关键词匹配进行分类
        for category, classifier in self.task_classifiers.items():
            if any(keyword in prompt_lower for keyword in classifier['keywords']):
                return TaskCategory(category)
        
        # 默认分类
        return TaskCategory.GENERAL_QUESTION
    
    def _analyze_context_richness(self, ai_request: AIRequest) -> float:
        """分析上下文丰富度 (0-1)"""
        if not ai_request.context:
            return 0.0
        
        richness_factors = [
            'project_type' in ai_request.context,
            'language' in ai_request.context,
            'framework' in ai_request.context,
            'files_count' in ai_request.context,
            'tech_stack' in ai_request.context,
            'requirements' in ai_request.context,
            'constraints' in ai_request.context,
            len(ai_request.context) > 3
        ]
        
        return sum(richness_factors) / len(richness_factors)
    
    def _assess_urgency(self, ai_request: AIRequest) -> float:
        """评估请求紧急度 (0-1)"""
        urgency_keywords = ['urgent', 'asap', 'immediately', 'quickly', 'fast', 'now']
        prompt_lower = ai_request.prompt.lower()
        
        urgency_score = sum(1 for keyword in urgency_keywords 
                           if keyword in prompt_lower) / len(urgency_keywords)
        
        # 检查上下文中的紧急度指示
        if ai_request.context and 'urgency' in ai_request.context:
            context_urgency = ai_request.context.get('urgency', 0)
            if isinstance(context_urgency, (int, float)):
                urgency_score = max(urgency_score, min(context_urgency, 1.0))
        
        return urgency_score
    
    def _estimate_resource_requirements(self, ai_request: AIRequest) -> Dict[str, float]:
        """估算资源需求"""
        complexity = self._calculate_complexity(ai_request)
        
        return {
            'cpu_intensive': complexity * 0.8,
            'memory_intensive': complexity * 0.6,
            'time_intensive': complexity * 0.9,
            'api_calls_needed': complexity * 0.7
        }
    
    def _extract_user_preferences(self, ai_request: AIRequest) -> Dict[str, Any]:
        """提取用户偏好"""
        preferences = {
            'speed_priority': False,
            'quality_priority': False,
            'cost_priority': False,
            'detailed_response': False
        }
        
        prompt_lower = ai_request.prompt.lower()
        
        if any(word in prompt_lower for word in ['quick', 'fast', 'brief']):
            preferences['speed_priority'] = True
        
        if any(word in prompt_lower for word in ['detailed', 'comprehensive', 'thorough']):
            preferences['detailed_response'] = True
            preferences['quality_priority'] = True
        
        if any(word in prompt_lower for word in ['simple', 'basic', 'cheap']):
            preferences['cost_priority'] = True
        
        return preferences
    
    async def _make_routing_decision(self, 
                                   analysis: Dict[str, Any], 
                                   ai_request: AIRequest) -> RoutingDecision:
        """做出路由决策"""
        
        complexity = analysis['complexity']
        category = analysis['category']
        context_richness = analysis['context_richness']
        urgency = analysis['urgency']
        user_prefs = analysis['user_preferences']
        
        # 决策逻辑
        if complexity > 0.8 and context_richness > 0.6 and self.enable_agents_mcp:
            # 超高复杂度 → 多代理协作
            return RoutingDecision(
                component=MCPComponentType.AGENTS_MCP,
                confidence=0.9,
                reasoning="High complexity task requiring multi-agent collaboration",
                estimated_time=60.0,
                estimated_cost=0.8,
                fallback_components=[MCPComponentType.TRAE_AGENT_MCP, MCPComponentType.CLAUDE_SDK_MCP],
                required_agents=['architect_agent', 'developer_agent', 'test_agent']
            )
        
        elif (category in [TaskCategory.ARCHITECTURE, TaskCategory.REFACTORING, TaskCategory.OPTIMIZATION] 
              and complexity > 0.6 and self.enable_trae_agent):
            # 软件工程任务 → Trae Agent
            return RoutingDecision(
                component=MCPComponentType.TRAE_AGENT_MCP,
                confidence=0.85,
                reasoning="Software engineering task best handled by Trae Agent",
                estimated_time=30.0,
                estimated_cost=0.5,
                fallback_components=[MCPComponentType.CLAUDE_SDK_MCP, MCPComponentType.ZEN_MCP]
            )
        
        elif (category in [TaskCategory.DEBUGGING, TaskCategory.TESTING, TaskCategory.CODE_ANALYSIS] 
              and complexity > 0.4 and self.enable_zen_mcp):
            # 工具密集型任务 → Zen MCP
            return RoutingDecision(
                component=MCPComponentType.ZEN_MCP,
                confidence=0.8,
                reasoning="Tool-intensive task best handled by Zen MCP",
                estimated_time=20.0,
                estimated_cost=0.3,
                fallback_components=[MCPComponentType.CLAUDE_SDK_MCP, MCPComponentType.DIRECT_API],
                required_tools=['code_analyzer', 'debugger', 'test_generator']
            )
        
        elif ai_request.use_aicore and complexity > 0.3 and self.enable_claude_sdk:
            # 标准AICore处理 → Claude SDK MCP
            return RoutingDecision(
                component=MCPComponentType.CLAUDE_SDK_MCP,
                confidence=0.75,
                reasoning="Standard AICore task with expert system support",
                estimated_time=25.0,
                estimated_cost=0.4,
                fallback_components=[MCPComponentType.DIRECT_API]
            )
        
        elif user_prefs['speed_priority'] or urgency > 0.7:
            # 速度优先 → 直接API调用
            return RoutingDecision(
                component=MCPComponentType.DIRECT_API,
                confidence=0.7,
                reasoning="Speed priority or urgent request",
                estimated_time=15.0,
                estimated_cost=0.2,
                fallback_components=[]
            )
        
        else:
            # 默认 → 统一接口层
            return RoutingDecision(
                component=MCPComponentType.CLAUDE_UNIFIED_MCP,
                confidence=0.6,
                reasoning="Default routing to unified interface",
                estimated_time=20.0,
                estimated_cost=0.3,
                fallback_components=[MCPComponentType.DIRECT_API]
            )
    
    async def _execute_routing(self, 
                              routing_decision: RoutingDecision, 
                              ai_request: AIRequest) -> AIResponse:
        """执行路由决策"""
        
        component = routing_decision.component
        
        try:
            if component == MCPComponentType.AGENTS_MCP and self.agents_mcp:
                return await self._route_to_agents_mcp(ai_request, routing_decision)
            
            elif component == MCPComponentType.TRAE_AGENT_MCP and self.trae_agent:
                return await self._route_to_trae_agent(ai_request, routing_decision)
            
            elif component == MCPComponentType.ZEN_MCP and self.zen_mcp:
                return await self._route_to_zen_mcp(ai_request, routing_decision)
            
            elif component == MCPComponentType.CLAUDE_SDK_MCP and self.claude_sdk:
                return await self._route_to_claude_sdk(ai_request, routing_decision)
            
            elif component == MCPComponentType.DIRECT_API:
                return await self._route_to_direct_api(ai_request, routing_decision)
            
            else:
                # 故障转移
                return await self._execute_fallback_routing(routing_decision, ai_request)
                
        except Exception as e:
            self.logger.error(f"Routing execution failed: {e}")
            return await self._execute_fallback_routing(routing_decision, ai_request)
    
    async def _route_to_agents_mcp(self, 
                                  ai_request: AIRequest, 
                                  routing_decision: RoutingDecision) -> AIResponse:
        """路由到Agents MCP"""
        # 创建多代理协作任务
        collaboration_task = {
            'task_id': str(uuid.uuid4()),
            'description': ai_request.prompt,
            'context': ai_request.context or {},
            'required_agents': routing_decision.required_agents,
            'coordination_strategy': 'sequential'
        }
        
        result = await self.agents_mcp.dispatch_task(collaboration_task)
        
        if result.get('success'):
            return AIResponse(
                content=result['output'],
                model="multi-agent-collaboration",
                usage={'total_tokens': result.get('total_tokens', 0)},
                finish_reason='stop',
                request_id=result['task_id'],
                expert_used=result.get('agents_used', []),
                aicore_operations=result.get('operations_performed', [])
            )
        else:
            raise Exception(f"Agents MCP failed: {result.get('error', 'Unknown error')}")
    
    async def _route_to_trae_agent(self, 
                                  ai_request: AIRequest, 
                                  routing_decision: RoutingDecision) -> AIResponse:
        """路由到Trae Agent MCP"""
        # 确定Trae任务类型
        task_type = self._map_to_trae_task_type(ai_request)
        
        trae_task = {
            'id': str(uuid.uuid4()),
            'description': ai_request.prompt,
            'context': ai_request.context or {},
            'task_type': task_type
        }
        
        result = await self.trae_agent.process_task(trae_task)
        
        if result.success:
            return AIResponse(
                content=result.output,
                model="trae-agent",
                usage={'total_tokens': result.tokens_used},
                finish_reason='stop',
                request_id=result.task_id,
                expert_used="trae_software_engineer",
                aicore_operations=[task_type.value]
            )
        else:
            raise Exception(f"Trae Agent failed: {result.error}")
    
    async def _route_to_zen_mcp(self, 
                               ai_request: AIRequest, 
                               routing_decision: RoutingDecision) -> AIResponse:
        """路由到Zen MCP"""
        # 发现合适的工具
        tools = await self.zen_mcp.discover_tools(
            task_type=ai_request.context.get('operation', 'general'),
            language=ai_request.context.get('language', 'python'),
            complexity=self._calculate_complexity(ai_request)
        )
        
        # 使用工具处理请求
        result = await self.zen_mcp.execute_tools(
            tools=routing_decision.required_tools or [tool.tool_id for tool in tools[:3]],
            input_data={
                'prompt': ai_request.prompt,
                'context': ai_request.context
            }
        )
        
        if result.get('success'):
            return AIResponse(
                content=result['output'],
                model="zen-tools",
                usage={'total_tokens': result.get('tokens_used', 0)},
                finish_reason='stop',
                request_id=str(uuid.uuid4()),
                expert_used="zen_tool_expert",
                aicore_operations=result.get('tools_used', [])
            )
        else:
            raise Exception(f"Zen MCP failed: {result.get('error', 'Unknown error')}")
    
    async def _route_to_claude_sdk(self, 
                                  ai_request: AIRequest, 
                                  routing_decision: RoutingDecision) -> AIResponse:
        """路由到Claude SDK MCP"""
        result = await self.claude_sdk.process_request(
            ai_request.prompt,
            ai_request.context or {},
            use_expert_system=ai_request.use_expert_system
        )
        
        return result
    
    async def _route_to_direct_api(self, 
                                  ai_request: AIRequest, 
                                  routing_decision: RoutingDecision) -> AIResponse:
        """路由到直接API调用"""
        # 这里应该实现直接的Claude API调用
        # 为了示例，返回一个模拟响应
        return AIResponse(
            content=f"Direct API response for: {ai_request.prompt[:100]}...",
            model="claude-3-5-sonnet-20241022",
            usage={'total_tokens': 100},
            finish_reason='stop',
            request_id=str(uuid.uuid4())
        )
    
    async def _execute_fallback_routing(self, 
                                       routing_decision: RoutingDecision, 
                                       ai_request: AIRequest) -> AIResponse:
        """执行故障转移路由"""
        for fallback_component in routing_decision.fallback_components:
            try:
                fallback_decision = RoutingDecision(
                    component=fallback_component,
                    confidence=0.5,
                    reasoning=f"Fallback from {routing_decision.component.value}",
                    estimated_time=routing_decision.estimated_time * 1.2,
                    estimated_cost=routing_decision.estimated_cost * 1.1
                )
                
                return await self._execute_routing(fallback_decision, ai_request)
                
            except Exception as e:
                self.logger.warning(f"Fallback to {fallback_component.value} failed: {e}")
                continue
        
        # 最终故障转移
        return AIResponse(
            content="I apologize, but I'm unable to process your request at the moment. Please try again later.",
            model="fallback",
            usage={'total_tokens': 0},
            finish_reason='error',
            request_id=str(uuid.uuid4())
        )
    
    def _map_to_trae_task_type(self, ai_request: AIRequest) -> TraeTaskType:
        """映射到Trae任务类型"""
        prompt_lower = ai_request.prompt.lower()
        
        if 'architecture' in prompt_lower or 'design' in prompt_lower:
            return TraeTaskType.ARCHITECTURE_DESIGN
        elif 'debug' in prompt_lower:
            return TraeTaskType.DEBUGGING
        elif 'refactor' in prompt_lower:
            return TraeTaskType.REFACTORING
        elif 'review' in prompt_lower:
            return TraeTaskType.CODE_REVIEW
        elif 'optimize' in prompt_lower or 'performance' in prompt_lower:
            return TraeTaskType.PERFORMANCE_OPTIMIZATION
        elif 'security' in prompt_lower:
            return TraeTaskType.SECURITY_ANALYSIS
        elif 'test' in prompt_lower:
            return TraeTaskType.TESTING
        elif 'document' in prompt_lower:
            return TraeTaskType.DOCUMENTATION
        else:
            return TraeTaskType.CODE_ANALYSIS
    
    def _initialize_task_classifiers(self) -> Dict[str, Dict[str, List[str]]]:
        """初始化任务分类器"""
        return {
            'code_completion': {
                'keywords': ['complete', 'finish', 'autocomplete', 'suggest']
            },
            'code_analysis': {
                'keywords': ['analyze', 'examine', 'inspect', 'review', 'check']
            },
            'code_generation': {
                'keywords': ['generate', 'create', 'write', 'build', 'implement']
            },
            'debugging': {
                'keywords': ['debug', 'fix', 'error', 'bug', 'issue', 'problem']
            },
            'refactoring': {
                'keywords': ['refactor', 'restructure', 'reorganize', 'improve', 'clean']
            },
            'testing': {
                'keywords': ['test', 'unit test', 'integration test', 'validate']
            },
            'optimization': {
                'keywords': ['optimize', 'performance', 'speed up', 'efficient']
            },
            'architecture': {
                'keywords': ['architecture', 'design', 'structure', 'pattern', 'system']
            },
            'security': {
                'keywords': ['security', 'secure', 'vulnerability', 'attack', 'protect']
            },
            'documentation': {
                'keywords': ['document', 'comment', 'explain', 'describe', 'readme']
            },
            'project_management': {
                'keywords': ['project', 'manage', 'plan', 'organize', 'workflow']
            }
        }
    
    async def _record_routing_metrics(self, 
                                     request_id: str,
                                     routing_decision: RoutingDecision,
                                     response: AIResponse,
                                     processing_time: float):
        """记录路由指标"""
        # 更新基本指标
        self.metrics.total_requests += 1
        
        if response.finish_reason != 'error':
            self.metrics.successful_routes += 1
        else:
            self.metrics.failed_routes += 1
        
        # 更新平均响应时间
        self.metrics.avg_response_time = (
            (self.metrics.avg_response_time * (self.metrics.total_requests - 1) + processing_time) 
            / self.metrics.total_requests
        )
        
        # 更新组件使用统计
        component_name = routing_decision.component.value
        self.metrics.component_usage[component_name] = (
            self.metrics.component_usage.get(component_name, 0) + 1
        )
        
        # 记录性能历史
        self.performance_history[component_name].append(processing_time)
        
        # 保持历史记录在合理范围内
        if len(self.performance_history[component_name]) > 100:
            self.performance_history[component_name] = (
                self.performance_history[component_name][-100:]
            )
        
        # 记录路由历史
        routing_record = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'component': component_name,
            'confidence': routing_decision.confidence,
            'processing_time': processing_time,
            'success': response.finish_reason != 'error',
            'estimated_time': routing_decision.estimated_time,
            'actual_vs_estimated': processing_time / routing_decision.estimated_time
        }
        
        self.routing_history.append(routing_record)
        
        # 保持历史记录在合理范围内
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-1000:]
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        return {
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'success_rate': (
                    self.metrics.successful_routes / max(self.metrics.total_requests, 1)
                ),
                'avg_response_time': self.metrics.avg_response_time,
                'component_usage': self.metrics.component_usage
            },
            'performance_trends': {
                component: {
                    'avg_time': sum(times) / len(times) if times else 0,
                    'min_time': min(times) if times else 0,
                    'max_time': max(times) if times else 0,
                    'request_count': len(times)
                }
                for component, times in self.performance_history.items()
            },
            'routing_efficiency': self._calculate_routing_efficiency(),
            'recommendations': self._generate_optimization_recommendations()
        }
    
    def _calculate_routing_efficiency(self) -> float:
        """计算路由效率"""
        if not self.routing_history:
            return 0.0
        
        # 计算实际时间与估计时间的比率
        efficiency_scores = []
        for record in self.routing_history[-100:]:  # 最近100个请求
            if record['estimated_time'] > 0:
                efficiency = min(record['estimated_time'] / record['processing_time'], 2.0)
                efficiency_scores.append(efficiency)
        
        return sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.0
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 分析成功率
        success_rate = self.metrics.successful_routes / max(self.metrics.total_requests, 1)
        if success_rate < 0.9:
            recommendations.append("考虑改进故障转移策略以提高成功率")
        
        # 分析响应时间
        if self.metrics.avg_response_time > 30.0:
            recommendations.append("平均响应时间较长，考虑优化路由决策算法")
        
        # 分析组件使用分布
        if self.metrics.component_usage:
            max_usage = max(self.metrics.component_usage.values())
            total_usage = sum(self.metrics.component_usage.values())
            
            if max_usage / total_usage > 0.7:
                recommendations.append("组件使用分布不均，考虑优化负载均衡")
        
        # 分析路由效率
        efficiency = self._calculate_routing_efficiency()
        if efficiency < 0.8:
            recommendations.append("路由效率较低，考虑调整时间估算算法")
        
        return recommendations if recommendations else ["当前路由策略运行良好"]

# 使用示例
async def main():
    """使用示例"""
    # 使用提供的API密钥
    claude_key = "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"
    gemini_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
    
    router = MCPEcosystemRouter(
        claude_api_key=claude_key,
        gemini_api_key=gemini_key
    )
    
    try:
        await router.initialize()
        
        # 测试不同类型的请求
        test_requests = [
            AIRequest(
                prompt="重构这个电商系统，提高性能和可维护性",
                use_aicore=True,
                context={
                    'project_type': 'e-commerce',
                    'complexity': 'high',
                    'files_count': 150
                }
            ),
            AIRequest(
                prompt="检查这段Python代码的语法错误",
                use_aicore=False,
                context={'language': 'python'}
            ),
            AIRequest(
                prompt="设计一个微服务架构",
                use_aicore=True,
                use_expert_system=True,
                context={'system_type': 'microservices'}
            )
        ]
        
        for i, request in enumerate(test_requests):
            print(f"\n=== 测试请求 {i+1} ===")
            print(f"提示: {request.prompt}")
            
            routing_decision, response = await router.route_request(request)
            
            print(f"路由到: {routing_decision.component.value}")
            print(f"置信度: {routing_decision.confidence:.2f}")
            print(f"原因: {routing_decision.reasoning}")
            print(f"响应: {response.content[:100]}...")
        
        # 获取统计信息
        stats = router.get_routing_stats()
        print(f"\n=== 路由统计 ===")
        print(f"总请求数: {stats['metrics']['total_requests']}")
        print(f"成功率: {stats['metrics']['success_rate']:.2f}")
        print(f"平均响应时间: {stats['metrics']['avg_response_time']:.2f}秒")
        print(f"组件使用: {stats['metrics']['component_usage']}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())

