"""
Mac Integration - 统一版本
整合claude_integration_mcp中的Mac平台集成功能
"""

import asyncio
import logging
import os
import platform
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class MacNotification:
    """Mac通知数据结构"""
    title: str
    message: str
    subtitle: Optional[str] = None
    sound: Optional[str] = None

class MacClaudeIntegration:
    """
    Mac平台Claude集成 - 统一版本
    提供macOS特定的系统集成功能
    """
    
    def __init__(self):
        """初始化Mac集成组件"""
        self.logger = logging.getLogger(__name__)
        
        # 检查是否在macOS上运行
        self.is_macos = platform.system() == 'Darwin'
        if not self.is_macos:
            self.logger.warning("Mac integration initialized on non-macOS system")
        
        # 配置
        self.config = {
            'notifications_enabled': True,
            'app_name': 'ClaudEditor 4.3',
            'notification_sound': 'default'
        }
        
        # 统计信息
        self.stats = {
            'notifications_sent': 0
        }
    
    async def initialize(self):
        """初始化Mac集成"""
        self.logger.info("Mac Claude Integration initialized")
    
    async def send_notification(self, notification: Dict[str, str]) -> bool:
        """
        发送macOS通知
        
        Args:
            notification: 通知字典，包含title, message等
            
        Returns:
            是否发送成功
        """
        if not self.config['notifications_enabled'] or not self.is_macos:
            return False
        
        try:
            title = notification.get('title', 'Claude AI')
            message = notification.get('message', '')
            subtitle = notification.get('subtitle', '')
            
            # 构建osascript命令
            script = f'display notification "{message}" with title "{title}"'
            if subtitle:
                script += f' subtitle "{subtitle}"'
            
            # 执行通知命令
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.stats['notifications_sent'] += 1
                self.logger.debug(f"Notification sent: {title}")
                return True
            else:
                self.logger.error(f"Notification failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Mac integration cleanup completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Mac集成统计信息"""
        return {
            **self.stats,
            'is_macos': self.is_macos,
            'config': self.config
        }

