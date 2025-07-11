"""
PowerAutomation v4.6.1 六大工作流體系
Six Major Workflow Systems Package
"""

from .workflow_engine import (
    workflow_engine,
    WorkflowEngine,
    WorkflowStatus,
    NodeType,
    WorkflowCategory,
    WorkflowNode,
    WorkflowDefinition,
    WorkflowExecution
)

__all__ = [
    'workflow_engine',
    'WorkflowEngine',
    'WorkflowStatus',
    'NodeType', 
    'WorkflowCategory',
    'WorkflowNode',
    'WorkflowDefinition',
    'WorkflowExecution'
]

__version__ = "4.6.1"
__component__ = "Six Major Workflow Systems"