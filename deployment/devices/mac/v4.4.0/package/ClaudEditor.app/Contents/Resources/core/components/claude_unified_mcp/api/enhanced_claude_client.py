"""
Enhanced Claude Client - PowerAutomation AICore Integration
增强的Claude客户端，集成PowerAutomation AICore的完整能力
"""

import asyncio
import json
import logging
import time
import os
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import hashlib

# PowerAutomation AICore Integration
from ...ag_ui_mcp.ag_ui_component_generator import AGUIComponentGenerator
from ...claude_mcp.claude_sdk.claude_sdk_mcp_v2 import ClaudeSDKMCP

class AIModelType(Enum):
    """AI模型类型"""
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"

@dataclass
class AIRequest:
    """AI请求数据结构"""
    prompt: str
    model: AIModelType = AIModelType.CLAUDE_3_5_SONNET
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    use_aicore: bool = True
    use_expert_system: bool = True
    enable_ui_generation: bool = False

@dataclass
class AIResponse:
    """AI响应数据结构"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    request_id: str
    expert_used: Optional[str] = None
    aicore_operations: List[str] = field(default_factory=list)
    ui_components: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class EnhancedClaudeClient:
    """
    增强的Claude客户端 - 集成PowerAutomation AICore
    提供完整的AI驱动开发能力
    """
    
    def __init__(self, 
                 claude_api_key: str,
                 gemini_api_key: Optional[str] = None,
                 default_model: AIModelType = AIModelType.CLAUDE_3_5_SONNET,
                 max_tokens: int = 4000,
                 temperature: float = 0.7,
                 timeout: int = 30,
                 max_retries: int = 3,
                 cache_enabled: bool = True,
                 cache_ttl: int = 300,
                 enable_aicore: bool = True):
        """
        初始化增强Claude客户端
        
        Args:
            claude_api_key: Claude API密钥
            gemini_api_key: Gemini API密钥
            default_model: 默认AI模型
            max_tokens: 最大token数
            temperature: 温度参数
            timeout: 超时时间
            max_retries: 最大重试次数
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存TTL
            enable_aicore: 是否启用AICore集成
        """
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.enable_aicore = enable_aicore
        
        # API端点
        self.claude_base_url = "https://api.anthropic.com/v1"
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # HTTP会话
        self.claude_session: Optional[aiohttp.ClientSession] = None
        self.gemini_session: Optional[aiohttp.ClientSession] = None
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # PowerAutomation AICore组件
        self.claude_sdk_mcp: Optional[ClaudeSDKMCP] = None
        self.agui_generator: Optional[AGUIComponentGenerator] = None
        
        # 缓存系统
        self.cache: Dict[str, tuple] = {}  # (response, timestamp)
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'claude_requests': 0,
            'gemini_requests': 0,
            'aicore_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'total_tokens_used': 0,
            'total_response_time': 0.0,
            'models_used': {},
            'experts_used': {},
            'ui_components_generated': 0
        }
    
    async def initialize(self):
        """初始化客户端和AICore组件"""
        try:
            # 初始化Claude会话
            claude_headers = {
                'Authorization': f'Bearer {self.claude_api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'ClaudEditor-AICore/4.3.0',
                'anthropic-version': '2023-06-01'
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.claude_session = aiohttp.ClientSession(
                headers=claude_headers,
                timeout=timeout
            )
            
            # 初始化Gemini会话（如果有API密钥）
            if self.gemini_api_key:
                self.gemini_session = aiohttp.ClientSession(timeout=timeout)
            
            # 初始化PowerAutomation AICore组件
            if self.enable_aicore:
                await self._initialize_aicore()
            
            self.logger.info("Enhanced Claude Client with AICore initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Enhanced Claude Client: {e}")
            raise
    
    async def _initialize_aicore(self):
        """初始化PowerAutomation AICore组件"""
        try:
            # 初始化Claude SDK MCP
            self.claude_sdk_mcp = ClaudeSDKMCP(api_key=self.claude_api_key)
            await self.claude_sdk_mcp.initialize()
            
            # 初始化AGUI组件生成器
            self.agui_generator = AGUIComponentGenerator()
            await self.agui_generator.initialize()
            
            self.logger.info("PowerAutomation AICore components initialized")
            
        except Exception as e:
            self.logger.warning(f"AICore initialization failed: {e}")
            self.enable_aicore = False
    
    async def close(self):
        """关闭客户端"""
        try:
            if self.claude_session:
                await self.claude_session.close()
            
            if self.gemini_session:
                await self.gemini_session.close()
            
            if self.claude_sdk_mcp:
                await self.claude_sdk_mcp.close()
            
            self.logger.info("Enhanced Claude Client closed")
            
        except Exception as e:
            self.logger.error(f"Error closing client: {e}")
    
    def _get_cache_key(self, request_data: Dict[str, Any]) -> str:
        """生成缓存键"""
        cache_data = {k: v for k, v in request_data.items() 
                     if k not in ['timestamp', 'request_id']}
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """检查缓存是否有效"""
        return time.time() - timestamp < self.cache_ttl
    
    async def _make_claude_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到Claude API"""
        if not self.claude_session:
            await self.initialize()
        
        for attempt in range(self.max_retries):
            try:
                async with self.claude_session.post(
                    f"{self.claude_base_url}/messages",
                    json=request_data
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    
                    elif response.status == 429:  # Rate limit
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            self.logger.warning(f"Claude rate limited, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # 其他错误
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Claude request timeout, retrying...")
                    await asyncio.sleep(1)
                    continue
                raise
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Claude request failed: {e}, retrying...")
                    await asyncio.sleep(1)
                    continue
                raise
        
        raise Exception(f"Claude API request failed after {self.max_retries} attempts")
    
    async def _make_gemini_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到Gemini API"""
        if not self.gemini_session or not self.gemini_api_key:
            raise ValueError("Gemini API not available")
        
        url = f"{self.gemini_base_url}/models/gemini-pro:generateContent?key={self.gemini_api_key}"
        
        for attempt in range(self.max_retries):
            try:
                async with self.gemini_session.post(url, json=request_data) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Gemini request failed: {e}, retrying...")
                    await asyncio.sleep(1)
                    continue
                raise
        
        raise Exception(f"Gemini API request failed after {self.max_retries} attempts")
    
    async def send_ai_request(self, ai_request: AIRequest) -> AIResponse:
        """
        发送AI请求 - 统一入口，支持多模型和AICore
        
        Args:
            ai_request: AI请求对象
            
        Returns:
            AI响应对象
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # 检查缓存
            if self.cache_enabled:
                cache_key = self._get_cache_key(ai_request.__dict__)
                if cache_key in self.cache:
                    cached_response, timestamp = self.cache[cache_key]
                    if self._is_cache_valid(timestamp):
                        self.stats['cache_hits'] += 1
                        return cached_response
                    else:
                        del self.cache[cache_key]
            
            # 选择处理方式
            if ai_request.use_aicore and self.enable_aicore and self.claude_sdk_mcp:
                # 使用PowerAutomation AICore处理
                response = await self._process_with_aicore(ai_request)
                self.stats['aicore_requests'] += 1
            
            elif ai_request.model.value.startswith('claude'):
                # 使用Claude API处理
                response = await self._process_with_claude(ai_request)
                self.stats['claude_requests'] += 1
            
            elif ai_request.model.value.startswith('gemini'):
                # 使用Gemini API处理
                response = await self._process_with_gemini(ai_request)
                self.stats['gemini_requests'] += 1
            
            else:
                raise ValueError(f"Unsupported model: {ai_request.model}")
            
            # 处理UI组件生成
            if ai_request.enable_ui_generation and self.agui_generator:
                ui_components = await self._generate_ui_components(ai_request, response)
                response.ui_components = ui_components
                if ui_components:
                    self.stats['ui_components_generated'] += 1
            
            # 更新统计
            response.response_time = time.time() - start_time
            self.stats['successful_requests'] += 1
            self.stats['total_response_time'] += response.response_time
            self.stats['models_used'][response.model] = \
                self.stats['models_used'].get(response.model, 0) + 1
            
            if response.expert_used:
                self.stats['experts_used'][response.expert_used] = \
                    self.stats['experts_used'].get(response.expert_used, 0) + 1
            
            # 缓存响应
            if self.cache_enabled:
                self.cache[cache_key] = (response, time.time())
            
            return response
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"AI request failed: {e}")
            
            return AIResponse(
                content=f"Request failed: {e}",
                model=ai_request.model.value,
                usage={'total_tokens': 0},
                finish_reason='error',
                response_time=time.time() - start_time,
                request_id='error'
            )
    
    async def _process_with_aicore(self, ai_request: AIRequest) -> AIResponse:
        """使用PowerAutomation AICore处理请求"""
        try:
            # 使用Claude SDK MCP的专家系统
            result = await self.claude_sdk_mcp.process_request(
                ai_request.prompt,
                ai_request.context or {}
            )
            
            return AIResponse(
                content=result.content,
                model=ai_request.model.value,
                usage={'total_tokens': result.tokens_used},
                finish_reason='stop',
                request_id=f"aicore_{int(time.time())}",
                expert_used=result.expert_used,
                aicore_operations=result.operations_executed
            )
            
        except Exception as e:
            self.logger.error(f"AICore processing failed: {e}")
            # 回退到直接Claude API
            return await self._process_with_claude(ai_request)
    
    async def _process_with_claude(self, ai_request: AIRequest) -> AIResponse:
        """使用Claude API处理请求"""
        request_data = {
            'model': ai_request.model.value,
            'max_tokens': ai_request.max_tokens,
            'temperature': ai_request.temperature,
            'messages': [
                {
                    'role': 'user',
                    'content': ai_request.prompt
                }
            ]
        }
        
        if ai_request.system_prompt:
            request_data['system'] = ai_request.system_prompt
        
        data = await self._make_claude_request(request_data)
        
        content = data['content'][0]['text'] if data['content'] else ""
        usage = data.get('usage', {})
        
        return AIResponse(
            content=content,
            model=data['model'],
            usage=usage,
            finish_reason=data.get('stop_reason', 'unknown'),
            request_id=data.get('id', 'unknown')
        )
    
    async def _process_with_gemini(self, ai_request: AIRequest) -> AIResponse:
        """使用Gemini API处理请求"""
        request_data = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': ai_request.prompt
                        }
                    ]
                }
            ],
            'generationConfig': {
                'temperature': ai_request.temperature,
                'maxOutputTokens': ai_request.max_tokens
            }
        }
        
        data = await self._make_gemini_request(request_data)
        
        content = ""
        if 'candidates' in data and data['candidates']:
            candidate = data['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                content = candidate['content']['parts'][0].get('text', '')
        
        return AIResponse(
            content=content,
            model=ai_request.model.value,
            usage={'total_tokens': 0},  # Gemini不提供详细token使用信息
            finish_reason='stop',
            request_id=f"gemini_{int(time.time())}"
        )
    
    async def _generate_ui_components(self, ai_request: AIRequest, ai_response: AIResponse) -> Optional[Dict[str, Any]]:
        """生成UI组件"""
        try:
            if not self.agui_generator:
                return None
            
            # 分析响应内容，生成相应的UI组件
            ui_request = {
                'content': ai_response.content,
                'context': ai_request.context or {},
                'type': 'code_editor' if 'code' in ai_request.prompt.lower() else 'general'
            }
            
            ui_components = await self.agui_generator.generate_components(ui_request)
            return ui_components
            
        except Exception as e:
            self.logger.error(f"UI component generation failed: {e}")
            return None
    
    # 便捷方法
    async def complete_code(self, 
                           code: str, 
                           language: str = "python",
                           context: Optional[str] = None,
                           use_aicore: bool = True) -> AIResponse:
        """代码补全"""
        system_prompt = f"""You are an expert {language} programmer. 
        Provide intelligent code completion suggestions based on the given code context.
        Focus on syntactically correct, efficient, and readable completions."""
        
        prompt = f"""Complete the following {language} code:

```{language}
{code}
```

{f"Additional context: {context}" if context else ""}

Provide the most likely completion for this code."""
        
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            use_aicore=use_aicore,
            use_expert_system=True
        )
        
        return await self.send_ai_request(request)
    
    async def analyze_code(self, 
                          code: str, 
                          language: str = "python",
                          use_aicore: bool = True) -> AIResponse:
        """代码分析"""
        system_prompt = f"""You are an expert {language} code reviewer.
        Analyze the given code and provide comprehensive feedback on:
        1. Code quality and best practices
        2. Potential bugs or issues
        3. Performance optimization suggestions
        4. Security considerations
        5. Maintainability improvements"""
        
        prompt = f"""Analyze the following {language} code:

```{language}
{code}
```

Provide a detailed code analysis with specific recommendations."""
        
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            use_aicore=use_aicore,
            use_expert_system=True
        )
        
        return await self.send_ai_request(request)
    
    async def explain_code(self, 
                          code: str, 
                          language: str = "python",
                          use_aicore: bool = True) -> AIResponse:
        """代码解释"""
        system_prompt = f"""You are an expert {language} programmer and teacher.
        Explain the given code in a clear, educational manner."""
        
        prompt = f"""Explain the following {language} code:

```{language}
{code}
```

Provide a comprehensive explanation of what this code does and how it works."""
        
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            use_aicore=use_aicore,
            use_expert_system=True
        )
        
        return await self.send_ai_request(request)
    
    async def generate_tests(self, 
                            code: str, 
                            language: str = "python",
                            test_framework: str = "pytest",
                            use_aicore: bool = True) -> AIResponse:
        """生成测试代码"""
        system_prompt = f"""You are an expert {language} developer specializing in testing.
        Generate comprehensive unit tests using {test_framework}."""
        
        prompt = f"""Generate {test_framework} unit tests for the following {language} code:

```{language}
{code}
```

Create comprehensive test coverage with multiple test cases."""
        
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            use_aicore=use_aicore,
            use_expert_system=True
        )
        
        return await self.send_ai_request(request)
    
    async def generate_ui_for_code(self, 
                                  code: str, 
                                  language: str = "python",
                                  ui_type: str = "web") -> AIResponse:
        """为代码生成UI界面"""
        system_prompt = f"""You are an expert UI/UX developer.
        Generate a {ui_type} interface for the given {language} code."""
        
        prompt = f"""Create a {ui_type} user interface for the following {language} code:

```{language}
{code}
```

Generate HTML, CSS, and JavaScript for a functional interface."""
        
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            use_aicore=True,
            enable_ui_generation=True
        )
        
        return await self.send_ai_request(request)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        total_requests = max(self.stats['total_requests'], 1)
        
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'cache_hit_rate': (self.stats['cache_hits'] / total_requests * 100),
            'success_rate': (self.stats['successful_requests'] / total_requests * 100),
            'average_response_time': (
                self.stats['total_response_time'] / max(self.stats['successful_requests'], 1)
            ),
            'aicore_enabled': self.enable_aicore,
            'aicore_usage_rate': (self.stats['aicore_requests'] / total_requests * 100),
            'components_status': {
                'claude_sdk_mcp': self.claude_sdk_mcp is not None,
                'agui_generator': self.agui_generator is not None,
                'gemini_available': self.gemini_api_key is not None
            }
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.logger.info("Cache cleared")

# 使用示例
async def main():
    """使用示例"""
    # 使用提供的API密钥
    claude_key = "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"
    gemini_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
    
    client = EnhancedClaudeClient(
        claude_api_key=claude_key,
        gemini_api_key=gemini_key,
        enable_aicore=True
    )
    
    try:
        await client.initialize()
        
        # 代码补全示例
        code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    "
        response = await client.complete_code(code, "python")
        print("Code completion:", response.content[:200] + "...")
        
        # 代码分析示例
        full_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        analysis = await client.analyze_code(full_code, "python")
        print("Code analysis:", analysis.content[:200] + "...")
        
        # UI生成示例
        ui_response = await client.generate_ui_for_code(full_code, "python", "web")
        print("UI generation:", ui_response.content[:200] + "...")
        
        # 统计信息
        stats = client.get_stats()
        print("Client stats:", {k: v for k, v in stats.items() if k in ['success_rate', 'aicore_usage_rate', 'cache_hit_rate']})
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

