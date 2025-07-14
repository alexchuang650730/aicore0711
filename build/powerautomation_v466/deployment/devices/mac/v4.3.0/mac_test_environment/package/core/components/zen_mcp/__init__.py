"""
PowerAutomation 4.1 Zen MCP工具生态系统

Zen MCP是一个包含14种专业开发工具的完整生态系统，为开发者提供
从代码编写到部署的全流程工具支持。

Zen MCP工具生态包括：

核心开发工具：
1. ZenCodeAnalyzer - 智能代码分析器
2. ZenCodeGenerator - AI代码生成器
3. ZenDebugger - 智能调试器
4. ZenRefactorer - 代码重构工具
5. ZenTester - 自动化测试工具

性能优化工具：
6. ZenProfiler - 性能分析器
7. ZenOptimizer - 代码优化器
8. ZenBenchmark - 基准测试工具

质量保证工具：
9. ZenLinter - 代码质量检查器
10. ZenFormatter - 代码格式化工具
11. ZenDocGenerator - 文档生成器

部署运维工具：
12. ZenDeployer - 智能部署工具
13. ZenMonitor - 运行时监控器
14. ZenSecurityScanner - 安全扫描器

主要特性：
- 统一的工具接口和配置
- 智能工具推荐和组合
- 跨工具的数据共享和协作
- 可扩展的插件架构
- 完整的工作流集成

作者: PowerAutomation Team
版本: 4.1
日期: 2025-01-07
"""

from .zen_tool_registry import ZenToolRegistry
from .zen_workflow_engine import ZenWorkflowEngine
from .zen_integration_manager import ZenIntegrationManager
from .tools import *

__version__ = "4.1.0"
__author__ = "PowerAutomation Team"

__all__ = [
    "ZenToolRegistry",
    "ZenWorkflowEngine", 
    "ZenIntegrationManager",
    # 核心开发工具
    "ZenCodeAnalyzer",
    "ZenCodeGenerator",
    "ZenDebugger",
    "ZenRefactorer",
    "ZenTester",
    # 性能优化工具
    "ZenProfiler",
    "ZenOptimizer",
    "ZenBenchmark",
    # 质量保证工具
    "ZenLinter",
    "ZenFormatter",
    "ZenDocGenerator",
    # 部署运维工具
    "ZenDeployer",
    "ZenMonitor",
    "ZenSecurityScanner"
]

