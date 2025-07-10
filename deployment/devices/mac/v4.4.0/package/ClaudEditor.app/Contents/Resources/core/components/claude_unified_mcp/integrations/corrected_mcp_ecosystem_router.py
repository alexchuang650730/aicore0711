"""
Corrected MCP Ecosystem Router - 修正后的智能路由器
基于修正架构设计的MCP组件路由和协调

修正要点:
1. External APIs集成到多代理协作层
2. MCP Tools MCP作为工具框架管理器
3. Zen MCP作为专业工具提供者
4. mcp.so、aci.dev、zapier在协作层统一管理
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

# PowerAutomation AICore组件导入 (修正后的架构)
try:
    from ..intelligence.enhanced_ai_assistant import EnhancedAIAssistant, AIRequest, AIResponse, AssistantMode
    
    # 多代理协作层
    from ...agents_mcp.agent_coordinator import AgentCoordinator
    
    # 专业处理层
    from ...trae_agent_mcp.trae_agent_engine import TraeAgentEngine, TaskType as TraeTaskType
    from ...claude_mcp.claude_sdk import ClaudeSDKMCP
    
    # 工具生态层 (修正后的关系)
    from ...mcp_tools_mcp.tool_registry import MCPToolRegistry
    from ...mcp_tools_mcp.tool_discovery import MCPToolDiscovery
    from ...zen_mcp.zen_tool_registry import ZenToolRegistry
    
except ImportError as e:
    logging.warning(f"Some MCP components not available: {e}")

class MCPComponentType(Enum):
    """MCP组件类型 (修正后)"""
    # 多代理协作层
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"
    
    # 专业处理层
    TRAE_AGENT_MCP = "trae_agent_mcp"
    CLAUDE_SDK_MCP = "claude_sdk_mcp"
    
    # 工具生态层
    MCP_TOOLS_FRAMEWORK = "mcp_tools_framework"
    ZEN_TOOLS_PROVIDER = "zen_tools_provider"
    
    # 直接API调用
    DIRECT_API = "direct_api"

class ExternalAPIType(Enum):
    """外部API类型 (在多代理协作层管理)"""
    CLAUDE_API = "claude_api"
    GEMINI_API = "gemini_api"
    MCP_SO = "mcp_so"
    ACI_DEV = "aci_dev"
    ZAPIER = "zapier"

class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"        # 0.0 - 0.3
    MODERATE = "moderate"    # 0.3 - 0.6
    COMPLEX = "complex"      # 0.6 - 0.8
    VERY_COMPLEX = "very_complex"  # 0.8 - 1.0

@dataclass
class ExternalAPIConfig:
    """外部API配置"""
    api_type: ExternalAPIType
    endpoint: str
    api_key: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    rate_limit: Optional[int] = None
    timeout: float = 30.0

@dataclass
class CorrectedRoutingDecision:
    """修正后的路由决策"""
    component: MCPComponentType
    confidence: float
    reasoning: str
    estimated_time: float
    estimated_cost: float
    
    # 修正后的字段
    required_agents: List[str] = field(default_factory=list)
    required_external_apis: List[ExternalAPIType] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    tool_providers: List[str] = field(default_factory=list)
    
    fallback_components: List[MCPComponentType] = field(default_factory=list)

class ExternalAPIManager:
    """
    外部API管理器 - 在多代理协作层统一管理所有外部API
    """
    
    def __init__(self):
        self.apis: Dict[ExternalAPIType, ExternalAPIConfig] = {}
        self.api_clients: Dict[ExternalAPIType, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_api(self, api_config: ExternalAPIConfig):
        """注册外部API"""
        self.apis[api_config.api_type] = api_config
        self.logger.info(f"Registered external API: {api_config.api_type.value}")
    
    async def initialize_apis(self):
        """初始化所有外部API客户端"""
        for api_type, config in self.apis.items():
            if config.enabled:
                try:
                    client = await self._create_api_client(api_type, config)
                    self.api_clients[api_type] = client
                    self.logger.info(f"Initialized API client: {api_type.value}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize {api_type.value}: {e}")
    
    async def _create_api_client(self, api_type: ExternalAPIType, config: ExternalAPIConfig):
        """创建API客户端"""
        if api_type == ExternalAPIType.CLAUDE_API:
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(api_key=config.api_key)
        
        elif api_type == ExternalAPIType.GEMINI_API:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            return genai.GenerativeModel('gemini-pro')
        
        elif api_type == ExternalAPIType.MCP_SO:
            # MCP核心库客户端
            return MCPSoClient(config.endpoint, config.config)
        
        elif api_type == ExternalAPIType.ACI_DEV:
            # AI代码智能客户端
            return ACIDevClient(config.endpoint, config.api_key)
        
        elif api_type == ExternalAPIType.ZAPIER:
            # Zapier自动化连接器客户端
            return ZapierClient(config.api_key, config.config)
        
        else:
            raise ValueError(f"Unknown API type: {api_type}")
    
    async def call_api(self, api_type: ExternalAPIType, method: str, **kwargs) -> Any:
        """调用外部API"""
        if api_type not in self.api_clients:
            raise ValueError(f"API client not initialized: {api_type}")
        
        client = self.api_clients[api_type]
        
        try:
            if api_type == ExternalAPIType.CLAUDE_API:
                return await self._call_claude_api(client, method, **kwargs)
            elif api_type == ExternalAPIType.GEMINI_API:
                return await self._call_gemini_api(client, method, **kwargs)
            elif api_type == ExternalAPIType.MCP_SO:
                return await self._call_mcp_so(client, method, **kwargs)
            elif api_type == ExternalAPIType.ACI_DEV:
                return await self._call_aci_dev(client, method, **kwargs)
            elif api_type == ExternalAPIType.ZAPIER:
                return await self._call_zapier(client, method, **kwargs)
            else:
                raise ValueError(f"Unknown API type: {api_type}")
                
        except Exception as e:
            self.logger.error(f"API call failed {api_type.value}.{method}: {e}")
            raise
    
    async def _call_claude_api(self, client, method: str, **kwargs):
        """调用Claude API"""
        if method == "complete":
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=kwargs.get('max_tokens', 1000),
                messages=[{"role": "user", "content": kwargs['prompt']}]
            )
            return response.content[0].text
        else:
            raise ValueError(f"Unknown Claude API method: {method}")
    
    async def _call_gemini_api(self, client, method: str, **kwargs):
        """调用Gemini API"""
        if method == "complete":
            response = await client.generate_content_async(kwargs['prompt'])
            return response.text
        else:
            raise ValueError(f"Unknown Gemini API method: {method}")
    
    async def _call_mcp_so(self, client, method: str, **kwargs):
        """调用MCP核心库"""
        # 这里实现MCP.so的具体调用逻辑
        return await client.call_method(method, **kwargs)
    
    async def _call_aci_dev(self, client, method: str, **kwargs):
        """调用AI代码智能"""
        # 这里实现aci.dev的具体调用逻辑
        return await client.call_method(method, **kwargs)
    
    async def _call_zapier(self, client, method: str, **kwargs):
        """调用Zapier自动化连接器"""
        # 这里实现zapier的具体调用逻辑
        return await client.call_method(method, **kwargs)

class MCPToolsFrameworkManager:
    """
    MCP工具框架管理器 - 管理工具生态系统的基础设施
    """
    
    def __init__(self):
        self.tool_registry = MCPToolRegistry()
        self.tool_discovery = MCPToolDiscovery()
        self.tool_providers: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """初始化工具框架"""
        await self.tool_registry.initialize()
        await self.tool_discovery.initialize()
        self.logger.info("MCP Tools Framework initialized")
    
    async def register_tool_provider(self, provider_name: str, provider_instance):
        """注册工具提供者"""
        self.tool_providers[provider_name] = provider_instance
        
        # 如果是Zen MCP，注册其所有工具
        if provider_name == "zen_mcp" and hasattr(provider_instance, 'tools'):
            for tool_id, tool_instance in provider_instance.tools.items():
                await self.tool_registry.register_tool(
                    tool_id=tool_id,
                    tool_instance=tool_instance,
                    provider=provider_name,
                    category=self._get_tool_category(tool_id)
                )
        
        self.logger.info(f"Registered tool provider: {provider_name}")
    
    async def discover_tools_for_task(self, task_description: str, task_type: str = None) -> List[Dict]:
        """为特定任务发现合适的工具"""
        return await self.tool_discovery.find_tools(
            task_description=task_description,
            task_type=task_type
        )
    
    async def get_tools_from_provider(self, provider_name: str, tool_ids: List[str]) -> Dict[str, Any]:
        """从特定提供者获取工具"""
        if provider_name not in self.tool_providers:
            raise ValueError(f"Tool provider not found: {provider_name}")
        
        provider = self.tool_providers[provider_name]
        tools = {}
        
        for tool_id in tool_ids:
            if hasattr(provider, 'get_tool'):
                tools[tool_id] = await provider.get_tool(tool_id)
            elif hasattr(provider, 'tools') and tool_id in provider.tools:
                tools[tool_id] = provider.tools[tool_id]
        
        return tools
    
    def _get_tool_category(self, tool_id: str) -> str:
        """获取工具分类"""
        category_mapping = {
            'code_analyzer': 'development',
            'code_generator': 'development',
            'debugger': 'development',
            'refactoring_tool': 'development',
            'test_generator': 'development',
            'performance_analyzer': 'optimization',
            'optimizer': 'optimization',
            'benchmark_tool': 'optimization',
            'code_checker': 'quality',
            'formatter': 'quality',
            'doc_generator': 'quality',
            'deployer': 'deployment',
            'monitor': 'deployment',
            'security_scanner': 'security'
        }
        return category_mapping.get(tool_id, 'utility')

class CorrectedMCPEcosystemRouter:
    """
    修正后的MCP生态系统智能路由器
    基于修正架构设计的智能路由和协调
    """
    
    def __init__(self,
                 claude_api_key: Optional[str] = None,
                 gemini_api_key: Optional[str] = None,
                 enable_multi_agent: bool = True,
                 enable_trae_agent: bool = True,
                 enable_claude_sdk: bool = True,
                 enable_mcp_tools: bool = True,
                 enable_zen_tools: bool = True):
        """
        初始化修正后的MCP生态系统路由器
        """
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.enable_multi_agent = enable_multi_agent
        self.enable_trae_agent = enable_trae_agent
        self.enable_claude_sdk = enable_claude_sdk
        self.enable_mcp_tools = enable_mcp_tools
        self.enable_zen_tools = enable_zen_tools
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self.external_api_manager = ExternalAPIManager()
        self.mcp_tools_framework = MCPToolsFrameworkManager()
        
        # MCP组件实例
        self.agent_coordinator: Optional[AgentCoordinator] = None
        self.trae_agent: Optional[TraeAgentEngine] = None
        self.claude_sdk: Optional[ClaudeSDKMCP] = None
        self.zen_tools: Optional[ZenToolRegistry] = None
        
        # 路由历史和指标
        self.routing_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, List[float]] = {}
    
    async def initialize(self):
        """初始化路由器和所有组件"""
        try:
            # 1. 初始化外部API管理器
            await self._initialize_external_apis()
            
            # 2. 初始化工具框架
            if self.enable_mcp_tools:
                await self.mcp_tools_framework.initialize()
            
            # 3. 初始化工具提供者
            if self.enable_zen_tools:
                await self._initialize_zen_tools()
            
            # 4. 初始化多代理协作层
            if self.enable_multi_agent:
                await self._initialize_multi_agent()
            
            # 5. 初始化专业处理层
            if self.enable_trae_agent:
                await self._initialize_trae_agent()
            
            if self.enable_claude_sdk:
                await self._initialize_claude_sdk()
            
            self.logger.info("Corrected MCP Ecosystem Router initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize router: {e}")
            raise
    
    async def _initialize_external_apis(self):
        """初始化外部API (在多代理协作层)"""
        # 注册Claude API
        if self.claude_api_key:
            self.external_api_manager.register_api(ExternalAPIConfig(
                api_type=ExternalAPIType.CLAUDE_API,
                endpoint="https://api.anthropic.com",
                api_key=self.claude_api_key
            ))
        
        # 注册Gemini API
        if self.gemini_api_key:
            self.external_api_manager.register_api(ExternalAPIConfig(
                api_type=ExternalAPIType.GEMINI_API,
                endpoint="https://generativelanguage.googleapis.com",
                api_key=self.gemini_api_key
            ))
        
        # 注册mcp.so (MCP核心库)
        self.external_api_manager.register_api(ExternalAPIConfig(
            api_type=ExternalAPIType.MCP_SO,
            endpoint="mcp://core",
            config={'version': '4.3.0'}
        ))
        
        # 注册aci.dev (AI代码智能)
        self.external_api_manager.register_api(ExternalAPIConfig(
            api_type=ExternalAPIType.ACI_DEV,
            endpoint="https://aci.dev/api",
            config={'features': ['code_intelligence', 'smart_completion']}
        ))
        
        # 注册zapier (自动化连接器)
        self.external_api_manager.register_api(ExternalAPIConfig(
            api_type=ExternalAPIType.ZAPIER,
            endpoint="https://zapier.com/api",
            config={'automation_enabled': True}
        ))
        
        await self.external_api_manager.initialize_apis()
        self.logger.info("External APIs initialized in multi-agent collaboration layer")
    
    async def _initialize_zen_tools(self):
        """初始化Zen工具提供者"""
        try:
            self.zen_tools = ZenToolRegistry()
            await self.zen_tools.initialize()
            
            # 将Zen工具注册到MCP工具框架
            await self.mcp_tools_framework.register_tool_provider("zen_mcp", self.zen_tools)
            
            self.logger.info("Zen Tools Provider initialized and registered")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Zen Tools: {e}")
            self.enable_zen_tools = False
    
    async def _initialize_multi_agent(self):
        """初始化多代理协作层"""
        try:
            self.agent_coordinator = AgentCoordinator()
            await self.agent_coordinator.initialize()
            
            # 为代理提供外部API访问
            self.agent_coordinator.set_external_api_manager(self.external_api_manager)
            
            self.logger.info("Multi-Agent Collaboration Layer initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Multi-Agent: {e}")
            self.enable_multi_agent = False
    
    async def _initialize_trae_agent(self):
        """初始化Trae Agent专业处理层"""
        try:
            self.trae_agent = TraeAgentEngine()
            await self.trae_agent.initialize()
            self.logger.info("Trae Agent MCP initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Trae Agent: {e}")
            self.enable_trae_agent = False
    
    async def _initialize_claude_sdk(self):
        """初始化Claude SDK专业处理层"""
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
    
    async def route_request(self, ai_request: AIRequest) -> Tuple[CorrectedRoutingDecision, AIResponse]:
        """
        路由AI请求到最适合的MCP组件 (修正后的逻辑)
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # 1. 分析请求特征
            analysis = await self._analyze_request(ai_request)
            
            # 2. 做出路由决策 (修正后的决策逻辑)
            routing_decision = await self._make_corrected_routing_decision(analysis, ai_request)
            
            # 3. 执行路由 (修正后的执行逻辑)
            response = await self._execute_corrected_routing(routing_decision, ai_request)
            
            # 4. 记录指标
            processing_time = time.time() - start_time
            await self._record_routing_metrics(request_id, routing_decision, response, processing_time)
            
            return routing_decision, response
            
        except Exception as e:
            self.logger.error(f"Routing failed for request {request_id}: {e}")
            return await self._handle_routing_failure(ai_request, str(e))
    
    async def _make_corrected_routing_decision(self, 
                                             analysis: Dict[str, Any], 
                                             ai_request: AIRequest) -> CorrectedRoutingDecision:
        """做出修正后的路由决策"""
        
        complexity = analysis['complexity']
        category = analysis['category']
        context_richness = analysis['context_richness']
        urgency = analysis['urgency']
        
        # 修正后的决策逻辑
        if complexity > 0.8 and context_richness > 0.6 and self.enable_multi_agent:
            # 超高复杂度 → 多代理协作层
            return CorrectedRoutingDecision(
                component=MCPComponentType.MULTI_AGENT_COLLABORATION,
                confidence=0.9,
                reasoning="High complexity task requiring multi-agent collaboration with external APIs",
                estimated_time=60.0,
                estimated_cost=0.8,
                required_agents=['architect_agent', 'developer_agent', 'test_agent'],
                required_external_apis=[ExternalAPIType.CLAUDE_API, ExternalAPIType.ACI_DEV],
                required_tools=['code_analyzer', 'refactoring_tool', 'test_generator'],
                tool_providers=['zen_mcp'],
                fallback_components=[MCPComponentType.TRAE_AGENT_MCP, MCPComponentType.CLAUDE_SDK_MCP]
            )
        
        elif (category in ['architecture', 'refactoring', 'optimization'] 
              and complexity > 0.6 and self.enable_trae_agent):
            # 软件工程任务 → Trae Agent专业处理层
            return CorrectedRoutingDecision(
                component=MCPComponentType.TRAE_AGENT_MCP,
                confidence=0.85,
                reasoning="Software engineering task best handled by Trae Agent",
                estimated_time=30.0,
                estimated_cost=0.5,
                required_external_apis=[ExternalAPIType.CLAUDE_API],
                fallback_components=[MCPComponentType.CLAUDE_SDK_MCP, MCPComponentType.MCP_TOOLS_FRAMEWORK]
            )
        
        elif (category in ['debugging', 'testing', 'code_analysis'] 
              and complexity > 0.4 and self.enable_mcp_tools):
            # 工具密集型任务 → MCP工具框架
            return CorrectedRoutingDecision(
                component=MCPComponentType.MCP_TOOLS_FRAMEWORK,
                confidence=0.8,
                reasoning="Tool-intensive task best handled by MCP Tools Framework",
                estimated_time=20.0,
                estimated_cost=0.3,
                required_tools=['code_analyzer', 'debugger', 'test_generator'],
                tool_providers=['zen_mcp'],
                fallback_components=[MCPComponentType.CLAUDE_SDK_MCP, MCPComponentType.DIRECT_API]
            )
        
        elif ai_request.use_aicore and complexity > 0.3 and self.enable_claude_sdk:
            # 标准AICore处理 → Claude SDK专业处理层
            return CorrectedRoutingDecision(
                component=MCPComponentType.CLAUDE_SDK_MCP,
                confidence=0.75,
                reasoning="Standard AICore task with expert system support",
                estimated_time=25.0,
                estimated_cost=0.4,
                required_external_apis=[ExternalAPIType.CLAUDE_API],
                fallback_components=[MCPComponentType.DIRECT_API]
            )
        
        else:
            # 简单任务 → 直接API调用
            return CorrectedRoutingDecision(
                component=MCPComponentType.DIRECT_API,
                confidence=0.7,
                reasoning="Simple task suitable for direct API call",
                estimated_time=15.0,
                estimated_cost=0.2,
                required_external_apis=[ExternalAPIType.CLAUDE_API],
                fallback_components=[]
            )
    
    async def _execute_corrected_routing(self, 
                                        routing_decision: CorrectedRoutingDecision, 
                                        ai_request: AIRequest) -> AIResponse:
        """执行修正后的路由决策"""
        
        component = routing_decision.component
        
        try:
            if component == MCPComponentType.MULTI_AGENT_COLLABORATION:
                return await self._route_to_multi_agent_collaboration(ai_request, routing_decision)
            
            elif component == MCPComponentType.TRAE_AGENT_MCP:
                return await self._route_to_trae_agent(ai_request, routing_decision)
            
            elif component == MCPComponentType.MCP_TOOLS_FRAMEWORK:
                return await self._route_to_mcp_tools_framework(ai_request, routing_decision)
            
            elif component == MCPComponentType.CLAUDE_SDK_MCP:
                return await self._route_to_claude_sdk(ai_request, routing_decision)
            
            elif component == MCPComponentType.DIRECT_API:
                return await self._route_to_direct_api(ai_request, routing_decision)
            
            else:
                return await self._execute_fallback_routing(routing_decision, ai_request)
                
        except Exception as e:
            self.logger.error(f"Routing execution failed: {e}")
            return await self._execute_fallback_routing(routing_decision, ai_request)
    
    async def _route_to_multi_agent_collaboration(self, 
                                                 ai_request: AIRequest, 
                                                 routing_decision: CorrectedRoutingDecision) -> AIResponse:
        """路由到多代理协作层 (修正后的实现)"""
        
        # 创建协作任务
        collaboration_task = {
            'task_id': str(uuid.uuid4()),
            'description': ai_request.prompt,
            'context': ai_request.context or {},
            'required_agents': routing_decision.required_agents,
            'required_external_apis': routing_decision.required_external_apis,
            'required_tools': routing_decision.required_tools,
            'tool_providers': routing_decision.tool_providers
        }
        
        # 通过代理协调器执行
        result = await self.agent_coordinator.execute_collaboration_task(collaboration_task)
        
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
            raise Exception(f"Multi-agent collaboration failed: {result.get('error', 'Unknown error')}")
    
    async def _route_to_mcp_tools_framework(self, 
                                           ai_request: AIRequest, 
                                           routing_decision: CorrectedRoutingDecision) -> AIResponse:
        """路由到MCP工具框架 (修正后的实现)"""
        
        # 1. 发现合适的工具
        discovered_tools = await self.mcp_tools_framework.discover_tools_for_task(
            task_description=ai_request.prompt,
            task_type=ai_request.context.get('operation', 'general')
        )
        
        # 2. 从指定提供者获取工具
        tools_to_use = routing_decision.required_tools or [tool['id'] for tool in discovered_tools[:3]]
        provider_tools = {}
        
        for provider in routing_decision.tool_providers:
            provider_tools.update(
                await self.mcp_tools_framework.get_tools_from_provider(provider, tools_to_use)
            )
        
        # 3. 执行工具链
        execution_result = await self._execute_tool_chain(provider_tools, {
            'prompt': ai_request.prompt,
            'context': ai_request.context
        })
        
        if execution_result.get('success'):
            return AIResponse(
                content=execution_result['output'],
                model="mcp-tools-framework",
                usage={'total_tokens': execution_result.get('tokens_used', 0)},
                finish_reason='stop',
                request_id=str(uuid.uuid4()),
                expert_used="mcp_tools_expert",
                aicore_operations=execution_result.get('tools_used', [])
            )
        else:
            raise Exception(f"MCP Tools Framework failed: {execution_result.get('error', 'Unknown error')}")
    
    async def _execute_tool_chain(self, tools: Dict[str, Any], input_data: Dict) -> Dict:
        """执行工具链"""
        results = []
        
        for tool_id, tool_instance in tools.items():
            try:
                tool_result = await tool_instance.execute(input_data)
                results.append({
                    'tool_id': tool_id,
                    'result': tool_result,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'tool_id': tool_id,
                    'error': str(e),
                    'success': False
                })
        
        # 整合结果
        successful_results = [r for r in results if r['success']]
        if successful_results:
            combined_output = "\n\n".join([
                f"**{r['tool_id']}**: {r['result']}" 
                for r in successful_results
            ])
            
            return {
                'success': True,
                'output': combined_output,
                'tools_used': [r['tool_id'] for r in successful_results],
                'tokens_used': len(combined_output.split()) * 2  # 估算
            }
        else:
            return {
                'success': False,
                'error': 'All tools failed to execute',
                'failed_tools': [r['tool_id'] for r in results]
            }
    
    async def _route_to_direct_api(self, 
                                  ai_request: AIRequest, 
                                  routing_decision: CorrectedRoutingDecision) -> AIResponse:
        """路由到直接API调用 (通过外部API管理器)"""
        
        # 选择API
        api_type = routing_decision.required_external_apis[0] if routing_decision.required_external_apis else ExternalAPIType.CLAUDE_API
        
        # 通过外部API管理器调用
        result = await self.external_api_manager.call_api(
            api_type=api_type,
            method="complete",
            prompt=ai_request.prompt,
            max_tokens=ai_request.max_tokens or 1000
        )
        
        return AIResponse(
            content=result,
            model=f"direct-{api_type.value}",
            usage={'total_tokens': len(result.split()) * 2},  # 估算
            finish_reason='stop',
            request_id=str(uuid.uuid4())
        )
    
    # ... 其他方法保持不变 ...
    
    def get_corrected_architecture_info(self) -> Dict[str, Any]:
        """获取修正后的架构信息"""
        return {
            'architecture_version': 'corrected_v1.0',
            'external_apis_location': 'multi_agent_collaboration_layer',
            'mcp_tools_relationship': {
                'mcp_tools_mcp': 'framework_manager',
                'zen_mcp': 'tool_provider',
                'relationship': 'zen_tools_registered_in_mcp_tools_framework'
            },
            'external_apis': {
                'claude_api': 'anthropic_claude_3_5_sonnet',
                'gemini_api': 'google_gemini_pro',
                'mcp_so': 'mcp_core_library',
                'aci_dev': 'ai_code_intelligence',
                'zapier': 'automation_connector'
            },
            'component_layers': {
                'multi_agent_collaboration': ['agents_mcp', 'external_apis', 'coordination_engine'],
                'specialized_processing': ['trae_agent_mcp', 'claude_sdk_mcp'],
                'tool_ecosystem': ['mcp_tools_framework', 'zen_tools_provider'],
                'smart_routing': ['mcp_ecosystem_router']
            },
            'routing_priorities': {
                'very_complex_tasks': 'multi_agent_collaboration',
                'software_engineering': 'trae_agent_mcp',
                'tool_intensive': 'mcp_tools_framework',
                'standard_aicore': 'claude_sdk_mcp',
                'simple_tasks': 'direct_api'
            }
        }

# 模拟的外部API客户端类
class MCPSoClient:
    """MCP核心库客户端"""
    def __init__(self, endpoint: str, config: Dict):
        self.endpoint = endpoint
        self.config = config
    
    async def call_method(self, method: str, **kwargs):
        # 模拟MCP.so调用
        return f"MCP.so result for {method}: {kwargs}"

class ACIDevClient:
    """AI代码智能客户端"""
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
    
    async def call_method(self, method: str, **kwargs):
        # 模拟aci.dev调用
        return f"ACI.dev result for {method}: {kwargs}"

class ZapierClient:
    """Zapier自动化连接器客户端"""
    def __init__(self, api_key: str, config: Dict):
        self.api_key = api_key
        self.config = config
    
    async def call_method(self, method: str, **kwargs):
        # 模拟zapier调用
        return f"Zapier result for {method}: {kwargs}"

# 使用示例
async def main():
    """修正后的使用示例"""
    # 使用提供的API密钥
    claude_key = "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"
    gemini_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
    
    router = CorrectedMCPEcosystemRouter(
        claude_api_key=claude_key,
        gemini_api_key=gemini_key
    )
    
    try:
        await router.initialize()
        
        # 测试修正后的架构
        print("=== 修正后的架构信息 ===")
        arch_info = router.get_corrected_architecture_info()
        print(f"架构版本: {arch_info['architecture_version']}")
        print(f"外部API位置: {arch_info['external_apis_location']}")
        print(f"MCP工具关系: {arch_info['mcp_tools_relationship']}")
        
        # 测试复杂任务路由
        complex_request = AIRequest(
            prompt="重构这个电商系统，提高性能和可维护性，需要架构分析、代码重构、测试生成和自动化部署",
            use_aicore=True,
            context={
                'project_type': 'e-commerce',
                'complexity': 'very_high',
                'files_count': 200,
                'tech_stack': ['python', 'django', 'postgresql', 'redis']
            }
        )
        
        print(f"\n=== 复杂任务路由测试 ===")
        routing_decision, response = await router.route_request(complex_request)
        print(f"路由到: {routing_decision.component.value}")
        print(f"需要的代理: {routing_decision.required_agents}")
        print(f"需要的外部API: {[api.value for api in routing_decision.required_external_apis]}")
        print(f"需要的工具: {routing_decision.required_tools}")
        print(f"工具提供者: {routing_decision.tool_providers}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())

