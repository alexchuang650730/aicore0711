"""
AI Enhanced Module - AI增强模块
为Local Adapter MCP提供AI驱动的智能优化功能

主要功能：
- 智能任务优化和调度
- 本地AI模型集成 (Qwen 3 8B)
- 预测性资源分配
- 智能故障预防
- 性能自动调优
"""

from .intelligent_task_optimizer import IntelligentTaskOptimizer
from .local_ai_model_integration import LocalAIModelIntegration
from .predictive_resource_allocator import PredictiveResourceAllocator
from .smart_performance_tuner import SmartPerformanceTuner
from .ai_enhanced_coordinator import AIEnhancedCoordinator

__all__ = [
    'IntelligentTaskOptimizer',
    'LocalAIModelIntegration', 
    'PredictiveResourceAllocator',
    'SmartPerformanceTuner',
    'AIEnhancedCoordinator'
]

__version__ = "1.0.0"
__author__ = "PowerAutomation Team"

