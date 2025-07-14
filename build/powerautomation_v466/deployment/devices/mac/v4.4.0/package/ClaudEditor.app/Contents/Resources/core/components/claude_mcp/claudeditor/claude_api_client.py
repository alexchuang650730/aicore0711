"""
Claude API 客户端

真实的Claude API集成，用于ClaudEditor AI助手
支持代码生成、解释、调试、优化、重构等功能
"""

import asyncio
import json
import logging
import time
import aiohttp
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClaudeRequest:
    """Claude API请求"""
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7
    messages: List[Dict[str, str]] = None
    system: str = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


@dataclass
class ClaudeResponse:
    """Claude API响应"""
    content: str
    model: str
    usage: Dict[str, int]
    stop_reason: str
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class ClaudeAPIClient:
    """Claude API客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.logger = logging.getLogger("ClaudeAPI")
        
        # API统计
        self.api_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0,
            'average_response_time': 0.0
        }
        
        # 请求历史
        self.request_history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        self.logger.info("Claude API客户端初始化完成")
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: str = None,
        style: str = "clean"
    ) -> ClaudeResponse:
        """生成代码"""
        
        system_prompt = f"""你是一个专业的{language}程序员。请根据用户需求生成高质量的代码。

代码风格要求：{style}
- clean: 简洁清晰，注重可读性
- efficient: 注重性能和效率
- robust: 注重错误处理和边界情况
- modern: 使用最新的语言特性和最佳实践

请提供：
1. 完整的代码实现
2. 简要的代码说明
3. 使用示例（如果适用）

只返回代码和必要的说明，不要包含其他内容。"""

        user_message = f"请用{language}实现：{prompt}"
        if context:
            user_message += f"\n\n上下文信息：{context}"
        
        request = ClaudeRequest(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.3  # 代码生成使用较低温度
        )
        
        return await self._make_request(request)
    
    async def explain_code(
        self,
        code: str,
        language: str = "python",
        detail_level: str = "medium"
    ) -> ClaudeResponse:
        """解释代码"""
        
        system_prompt = f"""你是一个代码解释专家。请详细解释给定的{language}代码。

解释详细程度：{detail_level}
- brief: 简要说明代码的主要功能
- medium: 详细解释代码逻辑和关键部分
- detailed: 逐行解释，包括语法、逻辑和最佳实践

请提供：
1. 代码整体功能说明
2. 关键部分的详细解释
3. 可能的改进建议（如果有）"""

        user_message = f"请解释以下{language}代码：\n\n```{language}\n{code}\n```"
        
        request = ClaudeRequest(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.5
        )
        
        return await self._make_request(request)
    
    async def debug_code(
        self,
        code: str,
        error_message: str = None,
        language: str = "python"
    ) -> ClaudeResponse:
        """调试代码"""
        
        system_prompt = f"""你是一个{language}调试专家。请帮助分析和修复代码中的问题。

请提供：
1. 问题分析：识别代码中的错误或潜在问题
2. 修复方案：提供具体的修复代码
3. 预防措施：建议如何避免类似问题
4. 测试建议：如何验证修复效果"""

        user_message = f"请帮助调试以下{language}代码：\n\n```{language}\n{code}\n```"
        if error_message:
            user_message += f"\n\n错误信息：{error_message}"
        
        request = ClaudeRequest(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.4
        )
        
        return await self._make_request(request)
    
    async def optimize_code(
        self,
        code: str,
        optimization_type: str = "performance",
        language: str = "python"
    ) -> ClaudeResponse:
        """优化代码"""
        
        optimization_types = {
            "performance": "性能优化：提升执行速度和效率",
            "memory": "内存优化：减少内存使用",
            "readability": "可读性优化：提升代码清晰度",
            "maintainability": "可维护性优化：提升代码结构",
            "security": "安全性优化：修复安全漏洞"
        }
        
        optimization_desc = optimization_types.get(optimization_type, "综合优化")
        
        system_prompt = f"""你是一个{language}代码优化专家。请对给定代码进行{optimization_desc}。

请提供：
1. 优化分析：识别可以改进的地方
2. 优化后的代码：提供完整的优化版本
3. 改进说明：解释每个优化点的原理
4. 性能对比：预期的改进效果"""

        user_message = f"请优化以下{language}代码（优化类型：{optimization_type}）：\n\n```{language}\n{code}\n```"
        
        request = ClaudeRequest(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.4
        )
        
        return await self._make_request(request)
    
    async def refactor_code(
        self,
        code: str,
        refactor_goal: str,
        language: str = "python"
    ) -> ClaudeResponse:
        """重构代码"""
        
        system_prompt = f"""你是一个{language}重构专家。请根据指定目标重构给定代码。

重构原则：
1. 保持功能不变
2. 提升代码质量
3. 遵循最佳实践
4. 确保可测试性

请提供：
1. 重构计划：说明重构步骤
2. 重构后的代码：提供完整的重构版本
3. 变更说明：解释主要变更和原因
4. 测试建议：如何验证重构正确性"""

        user_message = f"请重构以下{language}代码（重构目标：{refactor_goal}）：\n\n```{language}\n{code}\n```"
        
        request = ClaudeRequest(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.5
        )
        
        return await self._make_request(request)
    
    async def generate_tests(
        self,
        code: str,
        test_framework: str = "pytest",
        language: str = "python"
    ) -> ClaudeResponse:
        """生成测试代码"""
        
        system_prompt = f"""你是一个{language}测试专家。请为给定代码生成全面的测试用例。

测试框架：{test_framework}

请提供：
1. 单元测试：测试各个函数/方法
2. 集成测试：测试组件间交互
3. 边界测试：测试边界条件和异常情况
4. 性能测试：如果适用的话

测试应该：
- 覆盖主要功能路径
- 包含正常和异常情况
- 具有清晰的测试名称
- 包含必要的断言"""

        user_message = f"请为以下{language}代码生成{test_framework}测试：\n\n```{language}\n{code}\n```"
        
        request = ClaudeRequest(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.4
        )
        
        return await self._make_request(request)
    
    async def code_review(
        self,
        code: str,
        review_focus: str = "comprehensive",
        language: str = "python"
    ) -> ClaudeResponse:
        """代码审查"""
        
        review_focuses = {
            "comprehensive": "全面审查：功能、性能、安全、可维护性",
            "security": "安全审查：安全漏洞和风险",
            "performance": "性能审查：性能瓶颈和优化机会",
            "style": "风格审查：代码风格和规范",
            "logic": "逻辑审查：逻辑错误和改进"
        }
        
        focus_desc = review_focuses.get(review_focus, "综合审查")
        
        system_prompt = f"""你是一个资深的{language}代码审查专家。请对给定代码进行{focus_desc}。

审查维度：
1. 功能正确性：代码是否正确实现预期功能
2. 代码质量：可读性、可维护性、可扩展性
3. 性能效率：算法复杂度、资源使用
4. 安全性：潜在的安全风险
5. 最佳实践：是否遵循语言和框架的最佳实践

请提供：
1. 总体评价：代码质量的整体评估
2. 具体问题：列出发现的问题和建议
3. 改进建议：具体的改进方案
4. 评分：给出1-10的质量评分"""

        user_message = f"请审查以下{language}代码（审查重点：{review_focus}）：\n\n```{language}\n{code}\n```"
        
        request = ClaudeRequest(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.6
        )
        
        return await self._make_request(request)
    
    async def _make_request(self, request: ClaudeRequest) -> ClaudeResponse:
        """发送API请求"""
        
        start_time = time.time()
        self.api_stats['total_requests'] += 1
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": request.messages
        }
        
        if request.system:
            payload["system"] = request.system
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # 更新统计
                        self.api_stats['successful_requests'] += 1
                        self.api_stats['total_tokens_used'] += data.get('usage', {}).get('output_tokens', 0)
                        
                        # 更新平均响应时间
                        current_avg = self.api_stats['average_response_time']
                        total_successful = self.api_stats['successful_requests']
                        self.api_stats['average_response_time'] = (
                            (current_avg * (total_successful - 1) + response_time) / total_successful
                        )
                        
                        # 记录请求历史
                        self._record_request(request, data, response_time, True)
                        
                        # 构建响应
                        claude_response = ClaudeResponse(
                            content=data['content'][0]['text'],
                            model=data['model'],
                            usage=data['usage'],
                            stop_reason=data['stop_reason']
                        )
                        
                        self.logger.info(f"Claude API请求成功，响应时间: {response_time:.2f}s")
                        return claude_response
                    
                    else:
                        error_data = await response.text()
                        self.api_stats['failed_requests'] += 1
                        self._record_request(request, {"error": error_data}, response_time, False)
                        
                        self.logger.error(f"Claude API请求失败: {response.status} - {error_data}")
                        raise Exception(f"API请求失败: {response.status}")
        
        except Exception as e:
            self.api_stats['failed_requests'] += 1
            response_time = time.time() - start_time
            self._record_request(request, {"error": str(e)}, response_time, False)
            
            self.logger.error(f"Claude API请求异常: {e}")
            raise e
    
    def _record_request(
        self,
        request: ClaudeRequest,
        response_data: Dict[str, Any],
        response_time: float,
        success: bool
    ):
        """记录请求历史"""
        
        record = {
            'timestamp': time.time(),
            'model': request.model,
            'success': success,
            'response_time': response_time,
            'tokens_used': response_data.get('usage', {}).get('output_tokens', 0) if success else 0,
            'error': response_data.get('error') if not success else None
        }
        
        self.request_history.append(record)
        
        # 保持历史记录在限制范围内
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
    
    async def get_api_statistics(self) -> Dict[str, Any]:
        """获取API统计信息"""
        
        # 计算成功率
        total_requests = self.api_stats['total_requests']
        success_rate = (
            self.api_stats['successful_requests'] / total_requests
            if total_requests > 0 else 0.0
        )
        
        # 分析最近的请求
        recent_requests = self.request_history[-10:] if len(self.request_history) >= 10 else self.request_history
        recent_success_rate = (
            sum(1 for req in recent_requests if req['success']) / len(recent_requests)
            if recent_requests else 0.0
        )
        
        return {
            'api_statistics': {
                **self.api_stats,
                'success_rate': success_rate,
                'recent_success_rate': recent_success_rate
            },
            'recent_performance': {
                'recent_requests': len(recent_requests),
                'average_recent_response_time': (
                    sum(req['response_time'] for req in recent_requests) / len(recent_requests)
                    if recent_requests else 0.0
                ),
                'total_recent_tokens': sum(req['tokens_used'] for req in recent_requests)
            },
            'request_history_size': len(self.request_history)
        }
    
    async def test_connection(self) -> bool:
        """测试API连接"""
        
        try:
            test_request = ClaudeRequest(
                messages=[{"role": "user", "content": "Hello, please respond with 'API connection successful'"}],
                max_tokens=50,
                temperature=0.1
            )
            
            response = await self._make_request(test_request)
            
            if "successful" in response.content.lower():
                self.logger.info("Claude API连接测试成功")
                return True
            else:
                self.logger.warning("Claude API连接测试响应异常")
                return False
                
        except Exception as e:
            self.logger.error(f"Claude API连接测试失败: {e}")
            return False


# 全局Claude API客户端实例
claude_client = None

def get_claude_client(api_key: str = None) -> ClaudeAPIClient:
    """获取Claude API客户端实例"""
    global claude_client
    if claude_client is None and api_key:
        claude_client = ClaudeAPIClient(api_key)
    return claude_client


if __name__ == "__main__":
    # 测试Claude API客户端
    async def test_claude_client():
        # 使用提供的API密钥
        api_key = "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"
        client = get_claude_client(api_key)
        
        # 测试连接
        connection_ok = await client.test_connection()
        print(f"连接测试: {'成功' if connection_ok else '失败'}")
        
        if connection_ok:
            # 测试代码生成
            response = await client.generate_code(
                prompt="创建一个计算斐波那契数列的函数",
                language="python",
                style="clean"
            )
            print(f"代码生成结果: {response.content[:200]}...")
            
            # 获取统计信息
            stats = await client.get_api_statistics()
            print(f"API统计: {stats}")
    
    # 运行测试
    asyncio.run(test_claude_client())

