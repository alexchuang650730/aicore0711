"""
Claude Unified MCP - PowerAutomation v4.3.0
统一的Claude集成组件，整合所有Claude相关功能

这个统一组件整合了：
- claude_mcp: 专家系统、MCP协调器、多模型支持
- claude_integration_mcp: Monaco集成、Mac平台集成、代码智能

核心特性：
- 统一的Claude API客户端
- 智能专家系统 (5个专业领域 + 动态发现)
- 代码智能分析引擎
- Monaco编辑器深度集成
- Mac平台原生集成
- 多模型协调 (Claude + Gemini)
- 38个操作处理器
- 200K tokens上下文处理
- 实时性能监控
"""

__version__ = "4.3.0"
__author__ = "PowerAutomation Team"
__description__ = "Unified Claude Integration MCP for PowerAutomation"

# 核心API组件
from .api.claude_client import ClaudeUnifiedClient
from .api.multi_model_coordinator import MultiModelCoordinator
from .api.streaming_client import StreamingClient

# 智能分析组件
from .intelligence.code_analyzer import CodeAnalyzer
from .intelligence.expert_system import ExpertSystem, ExpertProfile
from .intelligence.scenario_analyzer import ScenarioAnalyzer

# 集成组件
from .integrations.monaco_plugin import MonacoClaudePlugin
from .integrations.mac_integration import MacClaudeIntegration
from .integrations.claudeditor_integration import ClaudEditorIntegration

# 核心服务组件
from .core.conversation_manager import ConversationManager
from .core.message_processor import MessageProcessor
from .core.performance_monitor import PerformanceMonitor

# 主要MCP类
from .claude_unified_mcp import ClaudeUnifiedMCP

# CLI接口
from .cli.cli import ClaudeUnifiedCLI

__all__ = [
    # 主要类
    'ClaudeUnifiedMCP',
    'ClaudeUnifiedCLI',
    
    # API组件
    'ClaudeUnifiedClient',
    'MultiModelCoordinator', 
    'StreamingClient',
    
    # 智能分析
    'CodeAnalyzer',
    'ExpertSystem',
    'ExpertProfile',
    'ScenarioAnalyzer',
    
    # 集成组件
    'MonacoClaudePlugin',
    'MacClaudeIntegration',
    'ClaudEditorIntegration',
    
    # 核心服务
    'ConversationManager',
    'MessageProcessor',
    'PerformanceMonitor'
]

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "release_date": "2025-07-09",
    "unified_from": [
        "claude_mcp v2.0.0",
        "claude_integration_mcp v4.3.0"
    ],
    "features": [
        "统一Claude API客户端",
        "智能专家系统 (5个专业领域)",
        "代码智能分析引擎", 
        "Monaco编辑器深度集成",
        "Mac平台原生集成",
        "多模型协调 (Claude + Gemini)",
        "38个操作处理器",
        "200K tokens上下文处理",
        "实时性能监控",
        "动态专家发现机制"
    ],
    "experts": [
        "代码架构专家",
        "性能优化专家",
        "API设计专家", 
        "安全分析专家",
        "数据库专家"
    ],
    "integrations": [
        "Monaco Editor",
        "macOS System",
        "ClaudEditor",
        "Gemini API",
        "PowerAutomation Core"
    ],
    "operation_categories": [
        "代码分析类 (8个)",
        "架构设计类 (8个)",
        "性能优化类 (8个)",
        "API设计类 (6个)", 
        "安全分析类 (5个)",
        "数据库类 (3个)"
    ]
}

def get_version_info():
    """获取版本信息"""
    return VERSION_INFO

def print_banner():
    """打印启动横幅"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                 Claude Unified MCP v{__version__}                  ║
║              统一Claude集成组件 - PowerAutomation             ║
║                                                              ║
║  🚀 统一特性:                                                ║
║    • 整合claude_mcp + claude_integration_mcp                 ║
║    • 统一API客户端 + 智能专家系统                            ║
║    • Monaco编辑器 + Mac平台深度集成                          ║
║    • 多模型协调 + 实时性能监控                               ║
║                                                              ║
║  🧠 智能分析:                                                ║
║    • 5个专业领域专家 + 动态发现                              ║
║    • 38个操作处理器 (覆盖全流程)                             ║
║    • 200K tokens上下文处理                                   ║
║    • 95%场景识别准确率                                       ║
║                                                              ║
║  🔧 集成支持:                                                ║
║    • Monaco Editor (代码补全/诊断)                           ║
║    • macOS System (通知/快捷键)                              ║
║    • ClaudEditor (深度集成)                                  ║
║    • Multi-Model (Claude + Gemini)                          ║
║                                                              ║
║  📞 支持: PowerAutomation Team                               ║
╚══════════════════════════════════════════════════════════════╝
""")

# 向后兼容性包装器
class ClaudeSDKMCP(ClaudeUnifiedMCP):
    """
    向后兼容claude_mcp的包装器
    保持原有API接口不变
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加兼容性别名
        self.get_claude_sdk_mcp = lambda: self

class ClaudeIntegrationMCP(ClaudeUnifiedMCP):
    """
    向后兼容claude_integration_mcp的包装器
    保持原有API接口不变
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# 快速启动函数
async def quick_start(api_key: str = None, config: dict = None):
    """
    快速启动Claude Unified MCP
    
    Args:
        api_key: Claude API密钥
        config: 配置字典
        
    Returns:
        ClaudeUnifiedMCP实例
    """
    print_banner()
    
    try:
        claude_unified = ClaudeUnifiedMCP(api_key=api_key, config=config)
        await claude_unified.initialize()
        
        print("✅ Claude Unified MCP 初始化成功!")
        print(f"🧠 专家数量: {len(claude_unified.get_all_experts())}")
        print(f"⚙️ 操作数量: {len(claude_unified.get_all_operations())}")
        print(f"🔧 集成组件: {len(claude_unified.get_all_integrations())}")
        
        return claude_unified
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return None

# 兼容性函数
async def get_claude_sdk_mcp(api_key: str = None):
    """兼容claude_mcp的快速启动函数"""
    return await quick_start(api_key)

# 示例使用
async def demo():
    """演示统一组件的基本功能"""
    claude_unified = await quick_start()
    
    if claude_unified:
        try:
            # 示例1: 代码分析
            result = await claude_unified.analyze_code(
                code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                language="python"
            )
            print(f"\n📋 代码分析结果:")
            print(f"✅ 成功: {result.success}")
            print(f"🧠 专家: {result.expert_used}")
            print(f"⚙️ 操作: {', '.join(result.operations_executed)}")
            
            # 示例2: Monaco集成
            if claude_unified.monaco_plugin:
                completions = await claude_unified.monaco_plugin.provide_completions(
                    content="def hello():",
                    position={"line": 1, "column": 12},
                    language="python"
                )
                print(f"\n💡 代码补全建议: {len(completions)}个")
            
            # 示例3: Mac集成
            if claude_unified.mac_integration:
                await claude_unified.mac_integration.send_notification({
                    "title": "Claude Unified MCP",
                    "message": "演示完成",
                    "subtitle": "统一组件运行正常"
                })
                print(f"\n🍎 Mac通知已发送")
            
        finally:
            await claude_unified.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())

