"""
ClaudeEditor 4.6.0 + PowerAutomation Core 4.6.0 测试套件
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试配置
TEST_CONFIG = {
    "timeout": 30,
    "retry_count": 3,
    "log_level": "DEBUG",
    "test_data_dir": project_root / "tests" / "fixtures",
    "temp_dir": project_root / "tests" / "temp"
}

# 确保临时目录存在
TEST_CONFIG["temp_dir"].mkdir(exist_ok=True)

__version__ = "4.6.0.0"
__author__ = "Manus AI"

