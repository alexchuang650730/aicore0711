"""
PowerAutomation 4.0 Commands Module
18个专业化命令实现
"""

from .architect_commands import *
from .develop_commands import *
from .test_commands import *
from .deploy_commands import *
from .monitor_commands import *
from .security_commands import *
from .utility_commands import *

# 自动注册所有命令
from .command_loader import load_all_commands

__all__ = ["load_all_commands"]

