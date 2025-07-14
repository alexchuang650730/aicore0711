"""
Claude Unified Client - 统一的Claude API客户端
整合claude_mcp和claude_integration_mcp中的API客户端功能
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import aiohttp
import os

class ClaudeModel(Enum):
    """Claude模型枚举"""
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

@dataclass
class ClaudeRequest:
    """Claude请求数据结构"""
    prompt: str
    model: ClaudeModel = ClaudeModel.CLAUDE_3_5_SONNET
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, str]]] = None

@dataclass
class ClaudeResponse:
    """Claude响应数据结构"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    request_id: str
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class ClaudeUnifiedClient:
    """
    统一的Claude API客户端
    整合所有Claude API相关功能
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 default_model: str = "claude-3-5-sonnet-20241022",
                 max_tokens: int = 4000,
                 temperature: float = 0.7,
                 timeout: int = 30,
                 max_retries: int = 3,
                 cache_enabled: bool = True,
                 cache_ttl: int = 300):
        """
        初始化统一Claude客户端
        
        Args:
            api_key: Claude API密钥
            default_model: 默认模型
            max_tokens: 最大token数
            temperature: 温度参数
            timeout: 超时时间
            max_retries: 最大重试次数
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存TTL
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("Claude API key is required. Set CLAUDE_API_KEY environment variable or pass api_key parameter.")
        
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        
        self.base_url = "https://api.anthropic.com/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # 请求缓存
        self.cache: Dict[str, tuple] = {}  # (response, timestamp)
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'total_tokens_used': 0,
            'total_response_time': 0.0,
            'models_used': {},
            'request_types': {}
        }
    
    async def initialize(self):
        """初始化客户端"""
        if not self.session:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'ClaudeUnifiedMCP/4.3.0 PowerAutomation',
                'anthropic-version': '2023-06-01'
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
            self.logger.info("Claude Unified Client initialized")
    
    async def close(self):
        """关闭客户端"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("Claude Unified Client closed")
    
    def _get_cache_key(self, request_data: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 移除时间戳等变化的字段
        cache_data = {k: v for k, v in request_data.items() 
                     if k not in ['timestamp', 'request_id']}
        return str(hash(json.dumps(cache_data, sort_keys=True)))
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """检查缓存是否有效"""
        return time.time() - timestamp < self.cache_ttl
    
    async def _make_request(self, request_data: Dict[str, Any], request_type: str = "general") -> ClaudeResponse:
        """发送请求到Claude API"""
        if not self.session:
            await self.initialize()
        
        self.stats['total_requests'] += 1
        self.stats['request_types'][request_type] = self.stats['request_types'].get(request_type, 0) + 1
        
        # 检查缓存
        if self.cache_enabled:
            cache_key = self._get_cache_key(request_data)
            if cache_key in self.cache:
                cached_response, timestamp = self.cache[cache_key]
                if self._is_cache_valid(timestamp):
                    self.stats['cache_hits'] += 1
                    self.logger.debug("Cache hit for request")
                    return cached_response
                else:
                    del self.cache[cache_key]
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    f"{self.base_url}/messages",
                    json=request_data
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析响应
                        content = data['content'][0]['text'] if data['content'] else ""
                        usage = data.get('usage', {})
                        
                        claude_response = ClaudeResponse(
                            content=content,
                            model=data['model'],
                            usage=usage,
                            finish_reason=data.get('stop_reason', 'unknown'),
                            response_time=response_time,
                            request_id=data.get('id', 'unknown')
                        )
                        
                        # 更新统计
                        self.stats['successful_requests'] += 1
                        self.stats['total_tokens_used'] += usage.get('total_tokens', 0)
                        self.stats['total_response_time'] += response_time
                        self.stats['models_used'][data['model']] = \
                            self.stats['models_used'].get(data['model'], 0) + 1
                        
                        # 缓存响应
                        if self.cache_enabled:
                            self.cache[cache_key] = (claude_response, time.time())
                        
                        return claude_response
                    
                    elif response.status == 429:  # Rate limit
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            self.logger.warning(f"Rate limited, waiting {wait_time}s before retry")
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
                    self.logger.warning(f"Request timeout, retrying... (attempt {attempt + 1})")
                    await asyncio.sleep(1)
                    continue
                raise
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Request failed: {e}, retrying... (attempt {attempt + 1})")
                    await asyncio.sleep(1)
                    continue
                raise
        
        # 所有重试都失败
        self.stats['failed_requests'] += 1
        raise Exception(f"Failed to get response from Claude API after {self.max_retries} attempts")
    
    async def send_request(self, 
                          prompt: str, 
                          context: Optional[Dict[str, Any]] = None,
                          model: Optional[str] = None,
                          system_prompt: Optional[str] = None) -> ClaudeResponse:
        """
        发送通用请求
        
        Args:
            prompt: 提示内容
            context: 上下文信息
            model: 使用的模型
            system_prompt: 系统提示
            
        Returns:
            Claude响应
        """
        request_data = {
            'model': model or self.default_model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        if system_prompt:
            request_data['system'] = system_prompt
        
        return await self._make_request(request_data, "general")
    
    async def complete_code(self, 
                           code: str, 
                           language: str = "python",
                           context: Optional[str] = None) -> ClaudeResponse:
        """
        代码补全
        
        Args:
            code: 需要补全的代码
            language: 编程语言
            context: 额外的上下文信息
            
        Returns:
            Claude响应，包含代码补全建议
        """
        system_prompt = f"""You are an expert {language} programmer. 
        Provide intelligent code completion suggestions based on the given code context.
        Focus on:
        1. Syntactically correct completions
        2. Best practices and conventions
        3. Performance considerations
        4. Readability and maintainability
        
        Return only the completion suggestion without explanations."""
        
        prompt = f"""Complete the following {language} code:

```{language}
{code}
```

{f"Additional context: {context}" if context else ""}

Provide the most likely completion for this code."""
        
        request_data = {
            'model': self.default_model,
            'max_tokens': 2000,
            'temperature': 0.3,
            'system': system_prompt,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        return await self._make_request(request_data, "code_completion")
    
    async def analyze_code(self, 
                          code: str, 
                          language: str = "python") -> ClaudeResponse:
        """
        代码分析
        
        Args:
            code: 要分析的代码
            language: 编程语言
            
        Returns:
            Claude响应，包含代码分析结果
        """
        system_prompt = f"""You are an expert {language} code reviewer.
        Analyze the given code and provide:
        1. Code quality assessment
        2. Potential bugs or issues
        3. Performance optimization suggestions
        4. Best practice recommendations
        5. Security considerations (if applicable)
        
        Format your response as structured feedback."""
        
        prompt = f"""Analyze the following {language} code:

```{language}
{code}
```

Provide a comprehensive code analysis with specific suggestions for improvement."""
        
        request_data = {
            'model': self.default_model,
            'max_tokens': 3000,
            'temperature': 0.2,
            'system': system_prompt,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        return await self._make_request(request_data, "code_analysis")
    
    async def explain_code(self, 
                          code: str, 
                          language: str = "python") -> ClaudeResponse:
        """
        代码解释
        
        Args:
            code: 要解释的代码
            language: 编程语言
            
        Returns:
            Claude响应，包含代码解释
        """
        system_prompt = f"""You are an expert {language} programmer and teacher.
        Explain the given code in a clear, educational manner.
        Include:
        1. What the code does (high-level purpose)
        2. How it works (step-by-step breakdown)
        3. Key concepts and patterns used
        4. Any notable techniques or algorithms
        
        Make the explanation accessible but technically accurate."""
        
        prompt = f"""Explain the following {language} code:

```{language}
{code}
```

Provide a clear, comprehensive explanation of what this code does and how it works."""
        
        request_data = {
            'model': self.default_model,
            'max_tokens': 2500,
            'temperature': 0.4,
            'system': system_prompt,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        return await self._make_request(request_data, "code_explanation")
    
    async def generate_tests(self, 
                            code: str, 
                            language: str = "python",
                            test_framework: str = "pytest") -> ClaudeResponse:
        """
        生成测试代码
        
        Args:
            code: 要测试的代码
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            Claude响应，包含生成的测试代码
        """
        system_prompt = f"""You are an expert {language} developer specializing in testing.
        Generate comprehensive unit tests for the given code using {test_framework}.
        Include:
        1. Test cases for normal functionality
        2. Edge cases and boundary conditions
        3. Error handling tests
        4. Mock objects where appropriate
        5. Clear, descriptive test names
        
        Follow {test_framework} best practices and conventions."""
        
        prompt = f"""Generate {test_framework} unit tests for the following {language} code:

```{language}
{code}
```

Create comprehensive test coverage with multiple test cases."""
        
        request_data = {
            'model': self.default_model,
            'max_tokens': 3000,
            'temperature': 0.3,
            'system': system_prompt,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        return await self._make_request(request_data, "test_generation")
    
    async def optimize_code(self, 
                           code: str, 
                           language: str = "python",
                           optimization_type: str = "performance") -> ClaudeResponse:
        """
        代码优化
        
        Args:
            code: 要优化的代码
            language: 编程语言
            optimization_type: 优化类型 (performance, readability, memory)
            
        Returns:
            Claude响应，包含优化建议
        """
        system_prompt = f"""You are an expert {language} developer specializing in {optimization_type} optimization.
        Analyze the given code and provide optimization suggestions.
        Focus on:
        1. {optimization_type.title()} improvements
        2. Specific code changes
        3. Before/after comparisons
        4. Explanation of benefits
        
        Provide practical, implementable suggestions."""
        
        prompt = f"""Optimize the following {language} code for {optimization_type}:

```{language}
{code}
```

Provide specific optimization suggestions with improved code examples."""
        
        request_data = {
            'model': self.default_model,
            'max_tokens': 3000,
            'temperature': 0.3,
            'system': system_prompt,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        return await self._make_request(request_data, "code_optimization")
    
    async def stream_request(self, 
                            prompt: str, 
                            context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        流式请求（用于实时响应）
        
        Args:
            prompt: 提示内容
            context: 上下文信息
            
        Yields:
            响应内容的流式片段
        """
        # 注意：这是一个简化的流式实现
        # 实际的Anthropic API流式支持可能需要不同的实现方式
        response = await self.send_request(prompt, context)
        
        # 模拟流式响应
        content = response.content
        chunk_size = 50
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield chunk
            await asyncio.sleep(0.1)  # 模拟网络延迟
    
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
            'average_tokens_per_request': (
                self.stats['total_tokens_used'] / max(self.stats['successful_requests'], 1)
            )
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.logger.info("Cache cleared")

# 使用示例
async def main():
    """使用示例"""
    async with ClaudeUnifiedClient() as client:
        # 代码补全示例
        code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    "
        response = await client.complete_code(code, "python")
        print("Code completion:", response.content)
        
        # 代码分析示例
        full_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        analysis = await client.analyze_code(full_code, "python")
        print("Code analysis:", analysis.content[:200] + "...")
        
        # 统计信息
        stats = client.get_stats()
        print("Client stats:", stats)

if __name__ == "__main__":
    asyncio.run(main())

