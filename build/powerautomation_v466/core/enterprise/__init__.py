"""
PowerAutomation v4.6.1 企業級版本策略
Enterprise Version Strategy Package
"""

from .version_strategy import (
    enterprise_version_strategy,
    EnterpriseVersionStrategy,
    EditionTier,
    VersionChannel,
    FeatureAccess,
    FeatureDefinition,
    VersionDefinition,
    LicenseInfo
)

__all__ = [
    'enterprise_version_strategy',
    'EnterpriseVersionStrategy', 
    'EditionTier',
    'VersionChannel',
    'FeatureAccess',
    'FeatureDefinition',
    'VersionDefinition',
    'LicenseInfo'
]

__version__ = "4.6.1"
__component__ = "Enterprise Version Strategy"