"""
Claude SDK MCP v2.0.0 - 智能代码分析和专家咨询系统
基于0624架构的MCP协调器，整合动态专家系统和真实Claude API

核心特性：
- 动态场景识别 - 95% 准确率
- 5个专业领域专家 + 动态专家发现机制  
- 200K tokens 上下文处理能力
- 38个操作处理器，覆盖 AI 代码分析全流程
- 真实 Claude API 集成
- 基于0624架构的MCP协调器
- 动态专家注册机制
- 专家性能监控

版本: 2.0.0
作者: PowerAutomation Team
许可: MIT License
"""

from .claude_sdk_mcp_v2 import (
    ClaudeSDKMCP,
    ExpertProfile,
    OperationHandler,
    ProcessingResult,
    ScenarioType,
    DynamicExpertRegistry,
    OperationRegistry,
    ScenarioAnalyzer,
    ClaudeAPIClient,
    get_claude_sdk_mcp
)

__version__ = "2.0.0"
__author__ = "PowerAutomation Team"
__license__ = "MIT"

__all__ = [
    "ClaudeSDKMCP",
    "ExpertProfile", 
    "OperationHandler",
    "ProcessingResult",
    "ScenarioType",
    "DynamicExpertRegistry",
    "OperationRegistry", 
    "ScenarioAnalyzer",
    "ClaudeAPIClient",
    "get_claude_sdk_mcp"
]

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "release_date": "2025-06-27",
    "features": [
        "动态场景识别 - 95% 准确率",
        "5个专业领域专家 + 动态专家发现机制",
        "200K tokens 上下文处理能力", 
        "38个操作处理器",
        "真实 Claude API 集成",
        "基于0624架构的MCP协调器",
        "动态专家注册机制",
        "专家性能监控"
    ],
    "experts": [
        "代码架构专家",
        "性能优化专家", 
        "API设计专家",
        "安全分析专家",
        "数据库专家"
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
║                    ClaudeSDKMCP v{__version__}                     ║
║              智能代码分析和专家咨询系统                        ║
║                                                              ║
║  🚀 核心特性:                                                ║
║    • 动态场景识别 - 95% 准确率                               ║
║    • 5个专业领域专家 + 动态专家发现                          ║
║    • 200K tokens 上下文处理能力                              ║
║    • 38个操作处理器                                          ║
║    • 真实 Claude API 集成                                    ║
║    • 基于0624架构的MCP协调器                                 ║
║                                                              ║
║  👥 专家团队:                                                ║
║    • 代码架构专家  • 性能优化专家  • API设计专家             ║
║    • 安全分析专家  • 数据库专家                              ║
║                                                              ║
║  ⚙️ 操作处理器: 38个 (覆盖AI代码分析全流程)                  ║
║                                                              ║
║  📞 支持: PowerAutomation Team                               ║
╚══════════════════════════════════════════════════════════════╝
""")

# 快速启动函数
async def quick_start(api_key: str = None):
    """快速启动Claude SDK MCP"""
    print_banner()
    
    try:
        claude_sdk = ClaudeSDKMCP(api_key)
        await claude_sdk.initialize()
        
        print("✅ Claude SDK MCP 初始化成功!")
        print(f"🧠 专家数量: {len(claude_sdk.get_all_experts())}")
        print(f"⚙️ 操作数量: {len(claude_sdk.get_all_operations())}")
        
        return claude_sdk
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return None

# 示例使用
async def demo():
    """演示基本功能"""
    claude_sdk = await quick_start()
    
    if claude_sdk:
        try:
            # 示例分析
            result = await claude_sdk.process_request(
                "请分析这段Python代码",
                {"code": "def hello(): print('Hello, World!')", "language": "python"}
            )
            
            print(f"\n📋 分析结果:")
            print(f"✅ 成功: {result.success}")
            print(f"🧠 专家: {result.expert_used}")
            print(f"⚙️ 操作: {', '.join(result.operations_executed)}")
            
        finally:
            await claude_sdk.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())

