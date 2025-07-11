"""
PowerAutomation v4.6.1 Enhanced CI/CD Pipeline Package
"""

from .enhanced_pipeline import (
    enhanced_cicd_pipeline,
    EnhancedCICDPipeline,
    PipelineStage,
    PipelineStatus,
    TriggerType,
    PipelineStageResult,
    PipelineExecution,
    PipelineConfiguration
)

__all__ = [
    'enhanced_cicd_pipeline',
    'EnhancedCICDPipeline',
    'PipelineStage',
    'PipelineStatus',
    'TriggerType',
    'PipelineStageResult',
    'PipelineExecution',
    'PipelineConfiguration'
]

__version__ = "4.6.1"
__component__ = "Enhanced CI/CD Pipeline"