"""
Enhanced Mac Integration - Mac特定的集成功能
为ClaudEditor 4.3 macOS版本提供原生Mac平台集成
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import tempfile
import plistlib

from ..intelligence.enhanced_ai_assistant import EnhancedAIAssistant, AssistantMode

class NotificationType(Enum):
    """通知类型"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"

class DockBadgeType(Enum):
    """Dock徽章类型"""
    NUMBER = "number"
    TEXT = "text"
    PROGRESS = "progress"
    NONE = "none"

class MenuBarStatus(Enum):
    """菜单栏状态"""
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    SUCCESS = "success"

@dataclass
class MacNotification:
    """Mac通知"""
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    sound: Optional[str] = None
    action_button: Optional[str] = None
    callback: Optional[Callable] = None
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    delivered_at: Optional[float] = None

@dataclass
class MacShortcut:
    """Mac快捷键"""
    key_combination: str
    description: str
    action: Callable
    enabled: bool = True
    global_shortcut: bool = False

@dataclass
class MacFileAssociation:
    """Mac文件关联"""
    file_extension: str
    content_type: str
    description: str
    icon_path: Optional[str] = None

class EnhancedMacIntegration:
    """
    增强的Mac平台集成
    提供原生Mac平台功能集成
    """
    
    def __init__(self, 
                 app_name: str = "ClaudEditor",
                 app_bundle_id: str = "com.powerautomation.claudeditor",
                 claude_api_key: Optional[str] = None,
                 gemini_api_key: Optional[str] = None,
                 enable_notifications: bool = True,
                 enable_dock_integration: bool = True,
                 enable_menu_bar: bool = True,
                 enable_file_associations: bool = True,
                 enable_shortcuts: bool = True):
        """
        初始化Mac集成
        
        Args:
            app_name: 应用名称
            app_bundle_id: Bundle ID
            claude_api_key: Claude API密钥
            gemini_api_key: Gemini API密钥
            enable_notifications: 是否启用通知
            enable_dock_integration: 是否启用Dock集成
            enable_menu_bar: 是否启用菜单栏
            enable_file_associations: 是否启用文件关联
            enable_shortcuts: 是否启用快捷键
        """
        self.app_name = app_name
        self.app_bundle_id = app_bundle_id
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.enable_notifications = enable_notifications
        self.enable_dock_integration = enable_dock_integration
        self.enable_menu_bar = enable_menu_bar
        self.enable_file_associations = enable_file_associations
        self.enable_shortcuts = enable_shortcuts
        
        # 核心组件
        self.ai_assistant: Optional[EnhancedAIAssistant] = None
        
        # 状态管理
        self.dock_badge_value: Optional[str] = None
        self.dock_badge_type: DockBadgeType = DockBadgeType.NONE
        self.menu_bar_status: MenuBarStatus = MenuBarStatus.IDLE
        self.menu_bar_title: str = app_name
        
        # 通知管理
        self.pending_notifications: List[MacNotification] = []
        self.notification_history: List[MacNotification] = []
        
        # 快捷键管理
        self.shortcuts: Dict[str, MacShortcut] = {}
        self.global_shortcuts: Dict[str, MacShortcut] = {}
        
        # 文件关联
        self.file_associations: Dict[str, MacFileAssociation] = {}
        
        # 系统路径
        self.app_support_dir = os.path.expanduser(f"~/Library/Application Support/{app_name}")
        self.preferences_dir = os.path.expanduser("~/Library/Preferences")
        self.temp_dir = tempfile.gettempdir()
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            'notifications_sent': 0,
            'shortcuts_triggered': 0,
            'dock_updates': 0,
            'menu_bar_updates': 0,
            'files_opened': 0,
            'ai_requests_from_mac': 0
        }
        
        # 默认快捷键配置
        self._setup_default_shortcuts()
        
        # 默认文件关联
        self._setup_default_file_associations()
    
    async def initialize(self):
        """初始化Mac集成"""
        try:
            # 创建应用支持目录
            os.makedirs(self.app_support_dir, exist_ok=True)
            
            # 初始化AI助手（如果有API密钥）
            if self.claude_api_key:
                self.ai_assistant = EnhancedAIAssistant(
                    claude_api_key=self.claude_api_key,
                    gemini_api_key=self.gemini_api_key,
                    enable_aicore=True
                )
                await self.ai_assistant.initialize()
            
            # 初始化各个组件
            if self.enable_notifications:
                await self._initialize_notifications()
            
            if self.enable_dock_integration:
                await self._initialize_dock_integration()
            
            if self.enable_menu_bar:
                await self._initialize_menu_bar()
            
            if self.enable_file_associations:
                await self._initialize_file_associations()
            
            if self.enable_shortcuts:
                await self._initialize_shortcuts()
            
            # 启动后台任务
            asyncio.create_task(self._notification_processor())
            asyncio.create_task(self._system_monitor())
            
            self.logger.info("Enhanced Mac Integration initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Mac Integration: {e}")
            raise
    
    async def close(self):
        """关闭Mac集成"""
        try:
            # 清理Dock徽章
            if self.enable_dock_integration:
                await self.clear_dock_badge()
            
            # 清理菜单栏
            if self.enable_menu_bar:
                await self.update_menu_bar_status(MenuBarStatus.IDLE, "")
            
            # 关闭AI助手
            if self.ai_assistant:
                await self.ai_assistant.close()
            
            self.logger.info("Enhanced Mac Integration closed")
            
        except Exception as e:
            self.logger.error(f"Error closing Mac Integration: {e}")
    
    def _setup_default_shortcuts(self):
        """设置默认快捷键"""
        self.shortcuts = {
            'cmd+shift+a': MacShortcut(
                key_combination='cmd+shift+a',
                description='Open AI Assistant',
                action=self._shortcut_open_ai_assistant,
                global_shortcut=True
            ),
            'cmd+shift+c': MacShortcut(
                key_combination='cmd+shift+c',
                description='Code Completion',
                action=self._shortcut_code_completion,
                global_shortcut=False
            ),
            'cmd+shift+d': MacShortcut(
                key_combination='cmd+shift+d',
                description='Debug Code',
                action=self._shortcut_debug_code,
                global_shortcut=False
            ),
            'cmd+shift+e': MacShortcut(
                key_combination='cmd+shift+e',
                description='Explain Code',
                action=self._shortcut_explain_code,
                global_shortcut=False
            ),
            'cmd+shift+o': MacShortcut(
                key_combination='cmd+shift+o',
                description='Optimize Code',
                action=self._shortcut_optimize_code,
                global_shortcut=False
            ),
            'cmd+shift+u': MacShortcut(
                key_combination='cmd+shift+u',
                description='Generate UI',
                action=self._shortcut_generate_ui,
                global_shortcut=False
            )
        }
    
    def _setup_default_file_associations(self):
        """设置默认文件关联"""
        self.file_associations = {
            '.py': MacFileAssociation(
                file_extension='.py',
                content_type='public.python-script',
                description='Python Source File'
            ),
            '.js': MacFileAssociation(
                file_extension='.js',
                content_type='com.netscape.javascript-source',
                description='JavaScript Source File'
            ),
            '.ts': MacFileAssociation(
                file_extension='.ts',
                content_type='public.typescript-source',
                description='TypeScript Source File'
            ),
            '.jsx': MacFileAssociation(
                file_extension='.jsx',
                content_type='public.jsx-source',
                description='React JSX File'
            ),
            '.tsx': MacFileAssociation(
                file_extension='.tsx',
                content_type='public.tsx-source',
                description='React TSX File'
            ),
            '.md': MacFileAssociation(
                file_extension='.md',
                content_type='net.daringfireball.markdown',
                description='Markdown Document'
            ),
            '.json': MacFileAssociation(
                file_extension='.json',
                content_type='public.json',
                description='JSON Document'
            ),
            '.yaml': MacFileAssociation(
                file_extension='.yaml',
                content_type='public.yaml',
                description='YAML Document'
            ),
            '.yml': MacFileAssociation(
                file_extension='.yml',
                content_type='public.yaml',
                description='YAML Document'
            )
        }
    
    async def _initialize_notifications(self):
        """初始化通知系统"""
        try:
            # 检查通知权限
            result = await self._run_applescript("""
                tell application "System Events"
                    return true
                end tell
            """)
            
            if result:
                self.logger.info("Notification system initialized")
            else:
                self.logger.warning("Notification permission may be required")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize notifications: {e}")
    
    async def _initialize_dock_integration(self):
        """初始化Dock集成"""
        try:
            # 清除任何现有的徽章
            await self.clear_dock_badge()
            self.logger.info("Dock integration initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dock integration: {e}")
    
    async def _initialize_menu_bar(self):
        """初始化菜单栏"""
        try:
            # 设置初始菜单栏状态
            await self.update_menu_bar_status(MenuBarStatus.IDLE, self.app_name)
            self.logger.info("Menu bar integration initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize menu bar: {e}")
    
    async def _initialize_file_associations(self):
        """初始化文件关联"""
        try:
            # 创建Info.plist文件
            await self._create_info_plist()
            self.logger.info("File associations initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize file associations: {e}")
    
    async def _initialize_shortcuts(self):
        """初始化快捷键"""
        try:
            # 注册全局快捷键
            for shortcut in self.shortcuts.values():
                if shortcut.global_shortcut and shortcut.enabled:
                    await self._register_global_shortcut(shortcut)
            
            self.logger.info("Shortcuts initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize shortcuts: {e}")
    
    async def _run_applescript(self, script: str) -> Optional[str]:
        """运行AppleScript"""
        try:
            process = await asyncio.create_subprocess_exec(
                'osascript', '-e', script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                self.logger.error(f"AppleScript error: {stderr.decode()}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to run AppleScript: {e}")
            return None
    
    async def _run_shell_command(self, command: List[str]) -> Optional[str]:
        """运行Shell命令"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                self.logger.error(f"Shell command error: {stderr.decode()}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to run shell command: {e}")
            return None
    
    async def send_notification(self, 
                               title: str,
                               message: str,
                               notification_type: NotificationType = NotificationType.INFO,
                               sound: Optional[str] = None,
                               action_button: Optional[str] = None,
                               callback: Optional[Callable] = None) -> str:
        """
        发送Mac通知
        
        Args:
            title: 通知标题
            message: 通知消息
            notification_type: 通知类型
            sound: 声音名称
            action_button: 操作按钮文本
            callback: 回调函数
            
        Returns:
            通知ID
        """
        if not self.enable_notifications:
            return ""
        
        notification = MacNotification(
            title=title,
            message=message,
            notification_type=notification_type,
            sound=sound,
            action_button=action_button,
            callback=callback
        )
        
        self.pending_notifications.append(notification)
        return notification.identifier
    
    async def _notification_processor(self):
        """通知处理器"""
        while True:
            try:
                if self.pending_notifications:
                    notification = self.pending_notifications.pop(0)
                    await self._deliver_notification(notification)
                
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Notification processor error: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_notification(self, notification: MacNotification):
        """发送单个通知"""
        try:
            # 构建AppleScript
            sound_part = f'sound name "{notification.sound}"' if notification.sound else ""
            
            script = f'''
                display notification "{notification.message}" ¬
                    with title "{notification.title}" ¬
                    subtitle "{self.app_name}" ¬
                    {sound_part}
            '''
            
            result = await self._run_applescript(script)
            
            if result is not None:
                notification.delivered_at = time.time()
                self.notification_history.append(notification)
                self.stats['notifications_sent'] += 1
                
                # 调用回调函数
                if notification.callback:
                    try:
                        await notification.callback(notification)
                    except Exception as e:
                        self.logger.error(f"Notification callback error: {e}")
                
                self.logger.info(f"Notification delivered: {notification.title}")
            
        except Exception as e:
            self.logger.error(f"Failed to deliver notification: {e}")
    
    async def update_dock_badge(self, 
                               value: Union[str, int],
                               badge_type: DockBadgeType = DockBadgeType.NUMBER):
        """
        更新Dock徽章
        
        Args:
            value: 徽章值
            badge_type: 徽章类型
        """
        if not self.enable_dock_integration:
            return
        
        try:
            if badge_type == DockBadgeType.NONE:
                await self.clear_dock_badge()
                return
            
            # 使用defaults命令更新徽章
            if isinstance(value, int) and badge_type == DockBadgeType.NUMBER:
                script = f'''
                    tell application "System Events"
                        tell application process "{self.app_name}"
                            set badge of dock tile to "{value}"
                        end tell
                    end tell
                '''
            else:
                script = f'''
                    tell application "System Events"
                        tell application process "{self.app_name}"
                            set badge of dock tile to "{value}"
                        end tell
                    end tell
                '''
            
            result = await self._run_applescript(script)
            
            if result is not None:
                self.dock_badge_value = str(value)
                self.dock_badge_type = badge_type
                self.stats['dock_updates'] += 1
                self.logger.info(f"Dock badge updated: {value}")
            
        except Exception as e:
            self.logger.error(f"Failed to update dock badge: {e}")
    
    async def clear_dock_badge(self):
        """清除Dock徽章"""
        if not self.enable_dock_integration:
            return
        
        try:
            script = f'''
                tell application "System Events"
                    tell application process "{self.app_name}"
                        set badge of dock tile to ""
                    end tell
                end tell
            '''
            
            result = await self._run_applescript(script)
            
            if result is not None:
                self.dock_badge_value = None
                self.dock_badge_type = DockBadgeType.NONE
                self.stats['dock_updates'] += 1
                self.logger.info("Dock badge cleared")
            
        except Exception as e:
            self.logger.error(f"Failed to clear dock badge: {e}")
    
    async def update_menu_bar_status(self, 
                                    status: MenuBarStatus,
                                    title: Optional[str] = None):
        """
        更新菜单栏状态
        
        Args:
            status: 状态
            title: 标题
        """
        if not self.enable_menu_bar:
            return
        
        try:
            self.menu_bar_status = status
            if title:
                self.menu_bar_title = title
            
            # 根据状态选择图标
            status_icons = {
                MenuBarStatus.IDLE: "●",
                MenuBarStatus.WORKING: "◐",
                MenuBarStatus.ERROR: "●",
                MenuBarStatus.SUCCESS: "●"
            }
            
            icon = status_icons.get(status, "●")
            display_title = f"{icon} {self.menu_bar_title}"
            
            # 这里可以集成实际的菜单栏更新逻辑
            # 由于需要原生Mac应用支持，这里只记录状态
            
            self.stats['menu_bar_updates'] += 1
            self.logger.info(f"Menu bar status updated: {status.value} - {display_title}")
            
        except Exception as e:
            self.logger.error(f"Failed to update menu bar status: {e}")
    
    async def _create_info_plist(self):
        """创建Info.plist文件"""
        try:
            # 构建文档类型数组
            document_types = []
            
            for ext, assoc in self.file_associations.items():
                doc_type = {
                    'CFBundleTypeName': assoc.description,
                    'CFBundleTypeRole': 'Editor',
                    'LSHandlerRank': 'Alternate',
                    'CFBundleTypeExtensions': [ext.lstrip('.')],
                    'CFBundleTypeIconFile': assoc.icon_path or 'document.icns'
                }
                
                if assoc.content_type:
                    doc_type['LSItemContentTypes'] = [assoc.content_type]
                
                document_types.append(doc_type)
            
            # 构建Info.plist内容
            info_plist = {
                'CFBundleName': self.app_name,
                'CFBundleDisplayName': self.app_name,
                'CFBundleIdentifier': self.app_bundle_id,
                'CFBundleVersion': '4.3.0',
                'CFBundleShortVersionString': '4.3.0',
                'CFBundlePackageType': 'APPL',
                'CFBundleSignature': 'CLED',
                'CFBundleExecutable': self.app_name,
                'CFBundleIconFile': 'AppIcon.icns',
                'LSMinimumSystemVersion': '10.15',
                'NSHighResolutionCapable': True,
                'NSSupportsAutomaticGraphicsSwitching': True,
                'CFBundleDocumentTypes': document_types,
                'UTExportedTypeDeclarations': [
                    {
                        'UTTypeIdentifier': 'com.powerautomation.claudeditor.project',
                        'UTTypeDescription': 'ClaudEditor Project',
                        'UTTypeConformsTo': ['public.data'],
                        'UTTypeTagSpecification': {
                            'public.filename-extension': ['claudeproj']
                        }
                    }
                ]
            }
            
            # 保存Info.plist
            info_plist_path = os.path.join(self.app_support_dir, 'Info.plist')
            with open(info_plist_path, 'wb') as f:
                plistlib.dump(info_plist, f)
            
            self.logger.info(f"Info.plist created: {info_plist_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create Info.plist: {e}")
    
    async def _register_global_shortcut(self, shortcut: MacShortcut):
        """注册全局快捷键"""
        try:
            # 这里需要使用原生Mac API或第三方库来注册全局快捷键
            # 由于限制，这里只记录快捷键
            self.global_shortcuts[shortcut.key_combination] = shortcut
            self.logger.info(f"Global shortcut registered: {shortcut.key_combination}")
            
        except Exception as e:
            self.logger.error(f"Failed to register global shortcut: {e}")
    
    async def _system_monitor(self):
        """系统监控任务"""
        while True:
            try:
                # 监控系统状态
                await self._check_system_resources()
                await self._cleanup_old_notifications()
                
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"System monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _check_system_resources(self):
        """检查系统资源"""
        try:
            # 检查内存使用
            result = await self._run_shell_command(['vm_stat'])
            if result:
                # 解析内存信息并在必要时发送通知
                pass
            
            # 检查CPU使用
            result = await self._run_shell_command(['top', '-l', '1', '-n', '0'])
            if result:
                # 解析CPU信息
                pass
                
        except Exception as e:
            self.logger.error(f"System resource check failed: {e}")
    
    async def _cleanup_old_notifications(self):
        """清理旧通知"""
        try:
            current_time = time.time()
            # 保留最近1小时的通知
            cutoff_time = current_time - 3600
            
            self.notification_history = [
                n for n in self.notification_history
                if n.delivered_at and n.delivered_at > cutoff_time
            ]
            
        except Exception as e:
            self.logger.error(f"Notification cleanup failed: {e}")
    
    # 快捷键动作
    async def _shortcut_open_ai_assistant(self):
        """打开AI助手快捷键"""
        try:
            await self.send_notification(
                "AI Assistant",
                "AI Assistant activated via shortcut",
                NotificationType.INFO
            )
            self.stats['shortcuts_triggered'] += 1
            
        except Exception as e:
            self.logger.error(f"AI Assistant shortcut failed: {e}")
    
    async def _shortcut_code_completion(self):
        """代码补全快捷键"""
        try:
            if self.ai_assistant:
                # 这里可以集成实际的代码补全逻辑
                await self.send_notification(
                    "Code Completion",
                    "Code completion triggered",
                    NotificationType.INFO
                )
                self.stats['shortcuts_triggered'] += 1
                self.stats['ai_requests_from_mac'] += 1
            
        except Exception as e:
            self.logger.error(f"Code completion shortcut failed: {e}")
    
    async def _shortcut_debug_code(self):
        """调试代码快捷键"""
        try:
            if self.ai_assistant:
                await self.send_notification(
                    "Debug Code",
                    "Code debugging triggered",
                    NotificationType.INFO
                )
                self.stats['shortcuts_triggered'] += 1
                self.stats['ai_requests_from_mac'] += 1
            
        except Exception as e:
            self.logger.error(f"Debug code shortcut failed: {e}")
    
    async def _shortcut_explain_code(self):
        """解释代码快捷键"""
        try:
            if self.ai_assistant:
                await self.send_notification(
                    "Explain Code",
                    "Code explanation triggered",
                    NotificationType.INFO
                )
                self.stats['shortcuts_triggered'] += 1
                self.stats['ai_requests_from_mac'] += 1
            
        except Exception as e:
            self.logger.error(f"Explain code shortcut failed: {e}")
    
    async def _shortcut_optimize_code(self):
        """优化代码快捷键"""
        try:
            if self.ai_assistant:
                await self.send_notification(
                    "Optimize Code",
                    "Code optimization triggered",
                    NotificationType.INFO
                )
                self.stats['shortcuts_triggered'] += 1
                self.stats['ai_requests_from_mac'] += 1
            
        except Exception as e:
            self.logger.error(f"Optimize code shortcut failed: {e}")
    
    async def _shortcut_generate_ui(self):
        """生成UI快捷键"""
        try:
            if self.ai_assistant:
                await self.send_notification(
                    "Generate UI",
                    "UI generation triggered",
                    NotificationType.INFO
                )
                self.stats['shortcuts_triggered'] += 1
                self.stats['ai_requests_from_mac'] += 1
            
        except Exception as e:
            self.logger.error(f"Generate UI shortcut failed: {e}")
    
    # 公共API方法
    async def open_file_with_claudeditor(self, file_path: str):
        """使用ClaudEditor打开文件"""
        try:
            if os.path.exists(file_path):
                # 这里可以集成实际的文件打开逻辑
                await self.send_notification(
                    "File Opened",
                    f"Opened: {os.path.basename(file_path)}",
                    NotificationType.SUCCESS
                )
                self.stats['files_opened'] += 1
                
                return True
            else:
                await self.send_notification(
                    "File Not Found",
                    f"Cannot find: {file_path}",
                    NotificationType.ERROR
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to open file: {e}")
            return False
    
    async def ai_assist_with_context(self, 
                                    prompt: str,
                                    context: Optional[Dict[str, Any]] = None,
                                    mode: AssistantMode = AssistantMode.GENERAL_ASSISTANT):
        """使用AI助手处理请求"""
        try:
            if not self.ai_assistant:
                await self.send_notification(
                    "AI Assistant Unavailable",
                    "AI Assistant is not initialized",
                    NotificationType.WARNING
                )
                return None
            
            # 显示进度通知
            await self.send_notification(
                "AI Processing",
                "AI is processing your request...",
                NotificationType.PROGRESS
            )
            
            # 更新Dock徽章显示进度
            await self.update_dock_badge("AI", DockBadgeType.TEXT)
            
            # 更新菜单栏状态
            await self.update_menu_bar_status(MenuBarStatus.WORKING, "AI Processing")
            
            # 发送AI请求
            response = await self.ai_assistant.ask_and_wait(
                prompt=prompt,
                mode=mode,
                context=context,
                timeout=30.0
            )
            
            if response:
                # 成功通知
                await self.send_notification(
                    "AI Response Ready",
                    "AI has completed your request",
                    NotificationType.SUCCESS
                )
                
                # 更新状态
                await self.update_menu_bar_status(MenuBarStatus.SUCCESS, "AI Complete")
                await self.clear_dock_badge()
                
                self.stats['ai_requests_from_mac'] += 1
                
                return response
            else:
                # 失败通知
                await self.send_notification(
                    "AI Request Failed",
                    "AI request timed out or failed",
                    NotificationType.ERROR
                )
                
                await self.update_menu_bar_status(MenuBarStatus.ERROR, "AI Failed")
                await self.clear_dock_badge()
                
                return None
                
        except Exception as e:
            self.logger.error(f"AI assist failed: {e}")
            
            await self.send_notification(
                "AI Error",
                f"AI request error: {str(e)}",
                NotificationType.ERROR
            )
            
            await self.update_menu_bar_status(MenuBarStatus.ERROR, "AI Error")
            await self.clear_dock_badge()
            
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取Mac集成统计信息"""
        return {
            **self.stats,
            'dock_badge': {
                'value': self.dock_badge_value,
                'type': self.dock_badge_type.value
            },
            'menu_bar': {
                'status': self.menu_bar_status.value,
                'title': self.menu_bar_title
            },
            'notifications': {
                'pending': len(self.pending_notifications),
                'history_count': len(self.notification_history)
            },
            'shortcuts': {
                'total': len(self.shortcuts),
                'global': len(self.global_shortcuts),
                'enabled': len([s for s in self.shortcuts.values() if s.enabled])
            },
            'file_associations': len(self.file_associations),
            'ai_assistant_available': self.ai_assistant is not None
        }

# 使用示例
async def main():
    """使用示例"""
    # 使用提供的API密钥
    claude_key = "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"
    gemini_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
    
    mac_integration = EnhancedMacIntegration(
        app_name="ClaudEditor",
        app_bundle_id="com.powerautomation.claudeditor",
        claude_api_key=claude_key,
        gemini_api_key=gemini_key
    )
    
    try:
        await mac_integration.initialize()
        
        # 发送测试通知
        await mac_integration.send_notification(
            "ClaudEditor Ready",
            "ClaudEditor 4.3 with Claude AI integration is ready!",
            NotificationType.SUCCESS,
            sound="Glass"
        )
        
        # 更新Dock徽章
        await mac_integration.update_dock_badge(1, DockBadgeType.NUMBER)
        
        # 更新菜单栏状态
        await mac_integration.update_menu_bar_status(
            MenuBarStatus.SUCCESS,
            "ClaudEditor Ready"
        )
        
        # 测试AI助手
        response = await mac_integration.ai_assist_with_context(
            "Explain what ClaudEditor is and its main features",
            context={'platform': 'macOS', 'version': '4.3'},
            mode=AssistantMode.GENERAL_ASSISTANT
        )
        
        if response:
            print("AI Response:", response.content[:200] + "...")
        
        # 等待一段时间以查看通知
        await asyncio.sleep(5)
        
        # 清理
        await mac_integration.clear_dock_badge()
        
        # 获取统计信息
        stats = mac_integration.get_stats()
        print("Mac Integration stats:", {k: v for k, v in stats.items() if k in ['notifications_sent', 'ai_requests_from_mac', 'shortcuts_triggered']})
        
    finally:
        await mac_integration.close()

if __name__ == "__main__":
    asyncio.run(main())

