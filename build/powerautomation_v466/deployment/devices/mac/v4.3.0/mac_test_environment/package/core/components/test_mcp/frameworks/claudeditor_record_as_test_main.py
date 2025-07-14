#!/usr/bin/env python3
"""
ClaudEditor 4.1 with Record-as-Test Integration

集成录制即测试功能的ClaudEditor主程序，提供完整的
AI辅助开发和自动化测试能力。
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.components.record_as_test_mcp import RecordAsTestService
from core.components.stagewise_mcp.stagewise_service import StagewiseService
from core.components.claude_integration_mcp.claude_sdk.claude_client import ClaudeClient
from claudeditor_ui_main import ClaudEditorUI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClaudEditorWithRecordAsTest:
    """集成录制即测试功能的ClaudEditor"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化ClaudEditor with Record-as-Test"""
        self.config_path = config_path
        
        # 初始化核心服务
        self.record_as_test_service = RecordAsTestService(config_path)
        self.stagewise_service = StagewiseService()
        self.claude_client = ClaudeClient()
        
        # 初始化UI
        self.ui = ClaudEditorUI()
        
        # 集成录制即测试功能
        self._integrate_record_as_test()
        
        logger.info("ClaudEditor with Record-as-Test 初始化完成")
    
    def _integrate_record_as_test(self):
        """集成录制即测试功能到UI"""
        
        # 添加录制即测试面板
        self.ui.add_record_as_test_panel(self.record_as_test_service)
        
        # 添加菜单项
        self._add_record_as_test_menus()
        
        # 添加工具栏按钮
        self._add_record_as_test_toolbar()
        
        # 设置快捷键
        self._setup_record_as_test_shortcuts()
        
        logger.info("录制即测试功能集成完成")
    
    def _add_record_as_test_menus(self):
        """添加录制即测试菜单"""
        
        # 录制菜单
        record_menu = self.ui.add_menu("录制测试")
        record_menu.add_action("开始录制", self._start_recording)
        record_menu.add_action("停止录制", self._stop_recording)
        record_menu.add_separator()
        record_menu.add_action("查看录制", self._view_recordings)
        record_menu.add_action("管理会话", self._manage_sessions)
        
        # 测试菜单
        test_menu = self.ui.add_menu("自动测试")
        test_menu.add_action("生成测试", self._generate_test)
        test_menu.add_action("优化测试", self._optimize_test)
        test_menu.add_action("回放测试", self._playback_test)
        test_menu.add_separator()
        test_menu.add_action("转换为Stagewise", self._convert_to_stagewise)
        test_menu.add_action("导出测试", self._export_test)
        
        # 工具菜单
        tools_menu = self.ui.get_menu("工具")
        if tools_menu:
            tools_menu.add_separator()
            tools_menu.add_action("录制即测试设置", self._open_settings)
            tools_menu.add_action("清理旧数据", self._cleanup_data)
    
    def _add_record_as_test_toolbar(self):
        """添加录制即测试工具栏"""
        
        toolbar = self.ui.add_toolbar("录制即测试")
        
        # 录制按钮
        toolbar.add_action("🎬", "开始录制", self._start_recording)
        toolbar.add_action("⏹️", "停止录制", self._stop_recording)
        toolbar.add_separator()
        
        # 测试按钮
        toolbar.add_action("🧪", "生成测试", self._generate_test)
        toolbar.add_action("✨", "AI优化", self._optimize_test)
        toolbar.add_action("▶️", "回放测试", self._playback_test)
        toolbar.add_separator()
        
        # 管理按钮
        toolbar.add_action("📋", "会话列表", self._view_recordings)
        toolbar.add_action("⚙️", "设置", self._open_settings)
    
    def _setup_record_as_test_shortcuts(self):
        """设置录制即测试快捷键"""
        
        shortcuts = {
            "Ctrl+Shift+R": self._start_recording,
            "Ctrl+Shift+S": self._stop_recording,
            "Ctrl+Shift+G": self._generate_test,
            "Ctrl+Shift+P": self._playback_test,
            "Ctrl+Shift+O": self._optimize_test,
        }
        
        for shortcut, action in shortcuts.items():
            self.ui.add_shortcut(shortcut, action)
    
    # 录制即测试功能实现
    
    async def _start_recording(self):
        """开始录制"""
        try:
            # 获取会话名称
            session_name = self.ui.get_input_dialog(
                "开始录制",
                "请输入录制会话名称:",
                f"Recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if not session_name:
                return
            
            # 开始录制
            session = await self.record_as_test_service.start_recording_session(session_name)
            
            # 更新UI状态
            self.ui.set_status(f"🎬 录制中: {session.name}")
            self.ui.show_notification("录制已开始", f"会话: {session.name}")
            
            # 更新录制面板
            self.ui.update_record_panel(session)
            
        except Exception as e:
            logger.error(f"开始录制失败: {e}")
            self.ui.show_error("录制失败", str(e))
    
    async def _stop_recording(self):
        """停止录制"""
        try:
            # 获取当前录制会话
            current_session = self.ui.get_current_recording_session()
            if not current_session:
                self.ui.show_warning("没有进行中的录制会话")
                return
            
            # 停止录制
            session = await self.record_as_test_service.stop_recording_session(current_session.id)
            
            # 更新UI状态
            self.ui.set_status("录制已停止")
            self.ui.show_notification(
                "录制已完成", 
                f"会话: {session.name}\\n动作: {len(session.actions)}个"
            )
            
            # 更新录制面板
            self.ui.update_record_panel(session)
            
            # 询问是否生成测试
            if self.ui.ask_yes_no("生成测试", "是否立即生成测试用例?"):
                await self._generate_test_from_session(session.id)
            
        except Exception as e:
            logger.error(f"停止录制失败: {e}")
            self.ui.show_error("停止录制失败", str(e))
    
    async def _generate_test(self):
        """生成测试用例"""
        try:
            # 选择录制会话
            sessions = await self.record_as_test_service.get_session_list()
            completed_sessions = [s for s in sessions if s['status'] == 'completed']
            
            if not completed_sessions:
                self.ui.show_warning("没有可用的录制会话")
                return
            
            session_id = self.ui.select_from_list(
                "选择录制会话",
                [(s['id'], s['name']) for s in completed_sessions]
            )
            
            if session_id:
                await self._generate_test_from_session(session_id)
            
        except Exception as e:
            logger.error(f"生成测试失败: {e}")
            self.ui.show_error("生成测试失败", str(e))
    
    async def _generate_test_from_session(self, session_id: str):
        """从指定会话生成测试"""
        try:
            # 显示进度
            self.ui.show_progress("正在生成测试用例...")
            
            # 生成测试用例
            test_case = await self.record_as_test_service.generate_test_from_recording(session_id)
            
            # 隐藏进度
            self.ui.hide_progress()
            
            # 显示结果
            self.ui.show_notification(
                "测试用例已生成",
                f"测试: {test_case.name}\\n步骤: {len(test_case.steps)}个"
            )
            
            # 更新测试面板
            self.ui.update_test_panel(test_case)
            
            # 询问是否打开测试文件
            if self.ui.ask_yes_no("打开测试文件", "是否打开生成的测试文件?"):
                self.ui.open_file(test_case.file_path)
            
        except Exception as e:
            self.ui.hide_progress()
            logger.error(f"生成测试失败: {e}")
            self.ui.show_error("生成测试失败", str(e))
    
    async def _optimize_test(self):
        """优化测试用例"""
        try:
            # 选择测试用例
            test_cases = await self.record_as_test_service.get_test_case_list()
            
            if not test_cases:
                self.ui.show_warning("没有可用的测试用例")
                return
            
            test_case_id = self.ui.select_from_list(
                "选择测试用例",
                [(t['id'], t['name']) for t in test_cases]
            )
            
            if not test_case_id:
                return
            
            # 显示进度
            self.ui.show_progress("正在进行AI优化...")
            
            # AI优化
            test_case = await self.record_as_test_service.optimize_test_with_ai(test_case_id)
            
            # 隐藏进度
            self.ui.hide_progress()
            
            # 显示结果
            suggestions = test_case.metadata.get('optimization_suggestions', [])
            self.ui.show_notification(
                "AI优化完成",
                f"测试: {test_case.name}\\n建议: {len(suggestions)}条"
            )
            
            # 显示优化建议
            if suggestions:
                self.ui.show_optimization_suggestions(test_case, suggestions)
            
        except Exception as e:
            self.ui.hide_progress()
            logger.error(f"优化测试失败: {e}")
            self.ui.show_error("优化测试失败", str(e))
    
    async def _playback_test(self):
        """回放测试用例"""
        try:
            # 选择测试用例
            test_cases = await self.record_as_test_service.get_test_case_list()
            
            if not test_cases:
                self.ui.show_warning("没有可用的测试用例")
                return
            
            test_case_id = self.ui.select_from_list(
                "选择测试用例",
                [(t['id'], t['name']) for t in test_cases]
            )
            
            if not test_case_id:
                return
            
            # 显示进度
            self.ui.show_progress("正在回放测试用例...")
            
            # 执行回放
            result = await self.record_as_test_service.playback_test_case(test_case_id)
            
            # 隐藏进度
            self.ui.hide_progress()
            
            # 显示结果
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            self.ui.show_notification(
                f"{status_icon} 回放完成",
                f"状态: {result['status']}\\n时间: {result.get('duration', 0):.2f}秒"
            )
            
            # 显示详细结果
            self.ui.show_playback_result(result)
            
        except Exception as e:
            self.ui.hide_progress()
            logger.error(f"回放测试失败: {e}")
            self.ui.show_error("回放测试失败", str(e))
    
    async def _convert_to_stagewise(self):
        """转换为Stagewise测试"""
        try:
            # 选择测试用例
            test_cases = await self.record_as_test_service.get_test_case_list()
            
            if not test_cases:
                self.ui.show_warning("没有可用的测试用例")
                return
            
            test_case_id = self.ui.select_from_list(
                "选择测试用例",
                [(t['id'], t['name']) for t in test_cases]
            )
            
            if not test_case_id:
                return
            
            # 转换为Stagewise测试
            stagewise_test_id = await self.record_as_test_service.convert_to_stagewise_test(test_case_id)
            
            # 显示结果
            self.ui.show_notification(
                "转换完成",
                f"已转换为Stagewise测试\\nID: {stagewise_test_id}"
            )
            
        except Exception as e:
            logger.error(f"转换失败: {e}")
            self.ui.show_error("转换失败", str(e))
    
    def _view_recordings(self):
        """查看录制列表"""
        self.ui.show_recordings_panel()
    
    def _manage_sessions(self):
        """管理录制会话"""
        self.ui.show_session_manager()
    
    def _export_test(self):
        """导出测试"""
        self.ui.show_export_dialog()
    
    def _open_settings(self):
        """打开设置"""
        self.ui.show_settings_dialog()
    
    async def _cleanup_data(self):
        """清理旧数据"""
        try:
            days = self.ui.get_number_input("清理数据", "清理多少天前的数据:", 30)
            if days is None:
                return
            
            if not self.ui.ask_yes_no("确认清理", f"确定要清理 {days} 天前的数据吗?"):
                return
            
            # 执行清理
            cleaned_count = await self.record_as_test_service.cleanup_old_recordings(days)
            
            self.ui.show_notification(
                "清理完成",
                f"清理了 {cleaned_count} 个录制会话"
            )
            
        except Exception as e:
            logger.error(f"清理数据失败: {e}")
            self.ui.show_error("清理数据失败", str(e))
    
    def run(self):
        """运行ClaudEditor"""
        try:
            logger.info("启动ClaudEditor with Record-as-Test...")
            
            # 启动UI
            self.ui.run()
            
        except KeyboardInterrupt:
            logger.info("用户中断，正在退出...")
        except Exception as e:
            logger.error(f"运行时错误: {e}")
            raise
        finally:
            # 清理资源
            self._cleanup()
    
    def _cleanup(self):
        """清理资源"""
        try:
            # 停止所有录制会话
            asyncio.run(self._stop_all_recordings())
            
            # 保存配置
            self._save_config()
            
            logger.info("ClaudEditor 已退出")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    async def _stop_all_recordings(self):
        """停止所有录制会话"""
        try:
            sessions = await self.record_as_test_service.get_session_list()
            active_sessions = [s for s in sessions if s['status'] == 'recording']
            
            for session in active_sessions:
                await self.record_as_test_service.stop_recording_session(session['id'])
                logger.info(f"已停止录制会话: {session['name']}")
                
        except Exception as e:
            logger.error(f"停止录制会话失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        try:
            # 保存UI配置
            self.ui.save_config()
            
            logger.info("配置已保存")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

def main():
    """主入口点"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="ClaudEditor 4.1 with Record-as-Test")
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--version', action='version', version='ClaudEditor 4.1 with Record-as-Test')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 创建并运行ClaudEditor
        app = ClaudEditorWithRecordAsTest(args.config)
        app.run()
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

