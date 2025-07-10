"""
实时协作增强模块

提供企业级实时协作功能，包括：
- 高级冲突解决
- 智能合并策略
- 协作分析和洞察
- 权限管理系统
"""

from .advanced_conflict_resolution import AdvancedConflictResolution
from .intelligent_merge_strategies import IntelligentMergeStrategies
from .collaboration_analytics import CollaborationAnalytics
from .permission_management_system import PermissionManagementSystem
from .realtime_collaboration_enhanced import RealtimeCollaborationEnhanced

__all__ = [
    'AdvancedConflictResolution',
    'IntelligentMergeStrategies',
    'CollaborationAnalytics',
    'PermissionManagementSystem',
    'RealtimeCollaborationEnhanced'
]

__version__ = "1.0.0"

