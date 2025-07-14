"""
PowerAutomation 4.0 Command Loader
自动加载和注册所有专业化命令
"""

import logging
from ..command_registry import get_command_registry, CommandCategory


def load_all_commands():
    """加载所有命令"""
    logger = logging.getLogger(__name__)
    registry = get_command_registry()
    
    try:
        # 加载架构命令
        from .architect_commands import register_architect_commands
        register_architect_commands(registry)
        
        # 加载开发命令
        from .develop_commands import register_develop_commands
        register_develop_commands(registry)
        
        # 加载测试命令
        from .test_commands import register_test_commands
        register_test_commands(registry)
        
        # 加载部署命令
        from .deploy_commands import register_deploy_commands
        register_deploy_commands(registry)
        
        # 加载监控命令
        from .monitor_commands import register_monitor_commands
        register_monitor_commands(registry)
        
        # 加载安全命令
        from .security_commands import register_security_commands
        register_security_commands(registry)
        
        # 加载工具命令
        from .utility_commands import register_utility_commands
        register_utility_commands(registry)
        
        logger.info("所有命令已加载完成")
        
    except Exception as e:
        logger.error(f"加载命令时出错: {e}")
        raise

