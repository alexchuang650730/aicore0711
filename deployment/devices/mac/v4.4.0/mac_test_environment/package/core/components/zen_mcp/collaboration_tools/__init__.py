"""
Zen MCP协作工具集模块

提供完整的协作工具生态系统，包括：
- 实时协作平台
- 团队沟通工具
- 项目管理系统
- 知识共享平台
- 版本控制集成
"""

from .realtime_collaboration_platform import RealtimeCollaborationPlatform
from .team_communication_hub import TeamCommunicationHub
from .project_management_system import ProjectManagementSystem
from .knowledge_sharing_platform import KnowledgeSharingPlatform
from .version_control_integration import VersionControlIntegration
from .collaboration_workflow_manager import CollaborationWorkflowManager

__all__ = [
    'RealtimeCollaborationPlatform',
    'TeamCommunicationHub',
    'ProjectManagementSystem',
    'KnowledgeSharingPlatform',
    'VersionControlIntegration',
    'CollaborationWorkflowManager'
]

__version__ = "1.0.0"

