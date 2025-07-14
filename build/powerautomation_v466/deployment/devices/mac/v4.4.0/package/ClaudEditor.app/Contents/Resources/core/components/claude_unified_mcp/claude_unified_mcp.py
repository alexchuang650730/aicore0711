"""
Claude Unified MCP - 主要组件类
整合claude_mcp和claude_integration_mcp的所有功能
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import time

from .api.claude_client import ClaudeUnifiedClient
from .api.multi_model_coordinator import MultiModelCoordinator
from .intelligence.code_analyzer import CodeAnalyzer
from .intelligence.expert_system import ExpertSystem
from .integrations.monaco_plugin import MonacoClaudePlugin
from .integrations.mac_integration import MacClaudeIntegration
from .core.conversation_manager import ConversationManager
from .core.performance_monitor import PerformanceMonitor

@dataclass
class UnifiedConfig:
    """统一配置类"""
    # API配置
    claude_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    default_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    
    # 功能开关
    expert_system_enabled: bool = True
    monaco_integration_enabled: bool = True
    mac_integration_enabled: bool = True
    multi_model_enabled: bool = True
    performance_monitoring_enabled: bool = True
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 300
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        """从环境变量创建配置"""
        return cls(
            claude_api_key=os.getenv('CLAUDE_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            default_model=os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022'),
            max_tokens=int(os.getenv('CLAUDE_MAX_TOKENS', '4000')),
            temperature=float(os.getenv('CLAUDE_TEMPERATURE', '0.7')),
            timeout=int(os.getenv('CLAUDE_TIMEOUT', '30')),
            cache_enabled=os.getenv('CLAUDE_CACHE_ENABLED', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )

@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    content: str
    expert_used: Optional[str] = None
    operations_executed: List[str] = None
    processing_time: float = 0.0
    model_used: str = ""
    tokens_used: int = 0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.operations_executed is None:
            self.operations_executed = []

class ClaudeUnifiedMCP:
    """
    Claude统一MCP组件
    整合所有Claude相关功能的统一接口
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化统一MCP组件
        
        Args:
            api_key: Claude API密钥
            config: 配置字典
        """
        # 配置管理
        if config:
            self.config = UnifiedConfig(**config)
        else:
            self.config = UnifiedConfig.from_env()
        
        if api_key:
            self.config.claude_api_key = api_key
        
        # 日志设置
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        # 核心组件
        self.claude_client: Optional[ClaudeUnifiedClient] = None
        self.multi_model_coordinator: Optional[MultiModelCoordinator] = None
        self.code_analyzer: Optional[CodeAnalyzer] = None
        self.expert_system: Optional[ExpertSystem] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        
        # 集成组件
        self.monaco_plugin: Optional[MonacoClaudePlugin] = None
        self.mac_integration: Optional[MacClaudeIntegration] = None
        
        # 状态
        self.is_initialized = False
        self.start_time = time.time()
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_processing_time': 0.0,
            'experts_used': {},
            'models_used': {},
            'operations_executed': {}
        }
    
    async def initialize(self):
        """初始化所有组件"""
        try:
            self.logger.info("开始初始化Claude Unified MCP...")
            
            # 1. 初始化核心API客户端
            self.claude_client = ClaudeUnifiedClient(
                api_key=self.config.claude_api_key,
                default_model=self.config.default_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                cache_enabled=self.config.cache_enabled,
                cache_ttl=self.config.cache_ttl
            )
            await self.claude_client.initialize()
            
            # 2. 初始化多模型协调器
            if self.config.multi_model_enabled:
                self.multi_model_coordinator = MultiModelCoordinator(
                    claude_client=self.claude_client,
                    gemini_api_key=self.config.gemini_api_key
                )
                await self.multi_model_coordinator.initialize()
            
            # 3. 初始化代码分析器
            self.code_analyzer = CodeAnalyzer(
                claude_client=self.claude_client
            )
            await self.code_analyzer.initialize()
            
            # 4. 初始化专家系统
            if self.config.expert_system_enabled:
                self.expert_system = ExpertSystem(
                    claude_client=self.claude_client
                )
                await self.expert_system.initialize()
            
            # 5. 初始化会话管理器
            self.conversation_manager = ConversationManager(
                claude_client=self.claude_client
            )
            
            # 6. 初始化性能监控
            if self.config.performance_monitoring_enabled:
                self.performance_monitor = PerformanceMonitor()
                await self.performance_monitor.start()
            
            # 7. 初始化Monaco集成
            if self.config.monaco_integration_enabled:
                self.monaco_plugin = MonacoClaudePlugin(
                    claude_client=self.claude_client,
                    code_analyzer=self.code_analyzer
                )
                await self.monaco_plugin.initialize()
            
            # 8. 初始化Mac集成
            if self.config.mac_integration_enabled:
                self.mac_integration = MacClaudeIntegration()
                await self.mac_integration.initialize()
            
            self.is_initialized = True
            self.logger.info("Claude Unified MCP 初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            raise
    
    async def process_request(self, 
                            request: str, 
                            context: Optional[Dict[str, Any]] = None,
                            use_expert: bool = True) -> ProcessingResult:
        """
        处理请求 - 统一入口
        
        Args:
            request: 请求内容
            context: 上下文信息
            use_expert: 是否使用专家系统
            
        Returns:
            处理结果
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # 选择处理方式
            if use_expert and self.expert_system:
                # 使用专家系统处理
                result = await self.expert_system.process_request(request, context)
            else:
                # 直接使用Claude API处理
                response = await self.claude_client.send_request(request, context)
                result = ProcessingResult(
                    success=True,
                    content=response.content,
                    model_used=response.model,
                    tokens_used=response.usage.get('total_tokens', 0)
                )
            
            # 更新统计
            result.processing_time = time.time() - start_time
            self.stats['successful_requests'] += 1
            self.stats['total_processing_time'] += result.processing_time
            
            if result.expert_used:
                self.stats['experts_used'][result.expert_used] = \
                    self.stats['experts_used'].get(result.expert_used, 0) + 1
            
            if result.model_used:
                self.stats['models_used'][result.model_used] = \
                    self.stats['models_used'].get(result.model_used, 0) + 1
            
            # 性能监控
            if self.performance_monitor:
                await self.performance_monitor.record_request(
                    request_type='process_request',
                    processing_time=result.processing_time,
                    success=result.success,
                    expert_used=result.expert_used,
                    model_used=result.model_used
                )
            
            return result
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"请求处理失败: {e}")
            
            return ProcessingResult(
                success=False,
                content="",
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def analyze_code(self, 
                          code: str, 
                          language: str = "python",
                          filename: Optional[str] = None) -> ProcessingResult:
        """
        代码分析 - 专门的代码分析接口
        
        Args:
            code: 代码内容
            language: 编程语言
            filename: 文件名
            
        Returns:
            分析结果
        """
        if not self.code_analyzer:
            return ProcessingResult(
                success=False,
                content="",
                error_message="代码分析器未初始化"
            )
        
        try:
            analysis_result = await self.code_analyzer.analyze_code(
                code=code,
                language=language,
                filename=filename
            )
            
            return ProcessingResult(
                success=True,
                content=analysis_result.summary,
                expert_used="代码分析专家",
                operations_executed=analysis_result.operations_used,
                processing_time=analysis_result.processing_time,
                tokens_used=analysis_result.tokens_used
            )
            
        except Exception as e:
            self.logger.error(f"代码分析失败: {e}")
            return ProcessingResult(
                success=False,
                content="",
                error_message=str(e)
            )
    
    async def complete_code(self, 
                           code: str, 
                           language: str = "python",
                           context: Optional[str] = None) -> ProcessingResult:
        """
        代码补全
        
        Args:
            code: 需要补全的代码
            language: 编程语言
            context: 额外上下文
            
        Returns:
            补全结果
        """
        try:
            response = await self.claude_client.complete_code(
                code=code,
                language=language,
                context=context
            )
            
            return ProcessingResult(
                success=True,
                content=response.content,
                expert_used="代码补全专家",
                operations_executed=["code_completion"],
                model_used=response.model,
                tokens_used=response.usage.get('total_tokens', 0)
            )
            
        except Exception as e:
            self.logger.error(f"代码补全失败: {e}")
            return ProcessingResult(
                success=False,
                content="",
                error_message=str(e)
            )
    
    async def explain_code(self, 
                          code: str, 
                          language: str = "python") -> ProcessingResult:
        """
        代码解释
        
        Args:
            code: 要解释的代码
            language: 编程语言
            
        Returns:
            解释结果
        """
        try:
            response = await self.claude_client.explain_code(
                code=code,
                language=language
            )
            
            return ProcessingResult(
                success=True,
                content=response.content,
                expert_used="代码解释专家",
                operations_executed=["code_explanation"],
                model_used=response.model,
                tokens_used=response.usage.get('total_tokens', 0)
            )
            
        except Exception as e:
            self.logger.error(f"代码解释失败: {e}")
            return ProcessingResult(
                success=False,
                content="",
                error_message=str(e)
            )
    
    async def generate_tests(self, 
                            code: str, 
                            language: str = "python",
                            test_framework: Optional[str] = None) -> ProcessingResult:
        """
        生成测试代码
        
        Args:
            code: 要测试的代码
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            测试代码生成结果
        """
        try:
            response = await self.claude_client.generate_tests(
                code=code,
                language=language,
                test_framework=test_framework
            )
            
            return ProcessingResult(
                success=True,
                content=response.content,
                expert_used="测试生成专家",
                operations_executed=["test_generation"],
                model_used=response.model,
                tokens_used=response.usage.get('total_tokens', 0)
            )
            
        except Exception as e:
            self.logger.error(f"测试生成失败: {e}")
            return ProcessingResult(
                success=False,
                content="",
                error_message=str(e)
            )
    
    def get_all_experts(self) -> List[str]:
        """获取所有可用专家"""
        if self.expert_system:
            return self.expert_system.get_all_experts()
        return []
    
    def get_all_operations(self) -> List[str]:
        """获取所有可用操作"""
        operations = []
        if self.expert_system:
            operations.extend(self.expert_system.get_all_operations())
        if self.code_analyzer:
            operations.extend(self.code_analyzer.get_all_operations())
        return list(set(operations))  # 去重
    
    def get_all_integrations(self) -> List[str]:
        """获取所有集成组件"""
        integrations = []
        if self.monaco_plugin:
            integrations.append("Monaco Editor")
        if self.mac_integration:
            integrations.append("macOS System")
        if self.multi_model_coordinator:
            integrations.append("Multi-Model")
        return integrations
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self.start_time
        
        stats = {
            **self.stats,
            'uptime_seconds': uptime,
            'average_processing_time': (
                self.stats['total_processing_time'] / max(self.stats['total_requests'], 1)
            ),
            'success_rate': (
                self.stats['successful_requests'] / max(self.stats['total_requests'], 1) * 100
            ),
            'components_initialized': {
                'claude_client': self.claude_client is not None,
                'multi_model_coordinator': self.multi_model_coordinator is not None,
                'code_analyzer': self.code_analyzer is not None,
                'expert_system': self.expert_system is not None,
                'monaco_plugin': self.monaco_plugin is not None,
                'mac_integration': self.mac_integration is not None,
                'performance_monitor': self.performance_monitor is not None
            }
        }
        
        # 添加组件特定统计
        if self.claude_client:
            stats['claude_client_stats'] = self.claude_client.get_stats()
        
        if self.performance_monitor:
            stats['performance_stats'] = self.performance_monitor.get_stats()
        
        return stats
    
    async def close(self):
        """关闭所有组件"""
        try:
            self.logger.info("开始关闭Claude Unified MCP...")
            
            # 关闭各个组件
            if self.claude_client:
                await self.claude_client.close()
            
            if self.multi_model_coordinator:
                await self.multi_model_coordinator.close()
            
            if self.performance_monitor:
                await self.performance_monitor.stop()
            
            if self.mac_integration:
                await self.mac_integration.cleanup()
            
            self.is_initialized = False
            self.logger.info("Claude Unified MCP 已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭过程中出错: {e}")

# 使用示例
async def main():
    """使用示例"""
    # 创建统一MCP实例
    claude_unified = ClaudeUnifiedMCP()
    
    try:
        # 初始化
        await claude_unified.initialize()
        
        # 代码分析示例
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        
        result = await claude_unified.analyze_code(code, "python")
        print(f"代码分析结果: {result.content[:200]}...")
        
        # 代码补全示例
        incomplete_code = "def hello_world():\n    print('"
        completion = await claude_unified.complete_code(incomplete_code, "python")
        print(f"代码补全: {completion.content}")
        
        # 获取统计信息
        stats = claude_unified.get_stats()
        print(f"统计信息: 成功率 {stats['success_rate']:.1f}%")
        
    finally:
        await claude_unified.close()

if __name__ == "__main__":
    asyncio.run(main())

