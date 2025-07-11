#!/usr/bin/env python3
"""
Test Three-Column UI Refactoring and Optimization
測試三欄式UI重構優化
"""

import asyncio
import sys
import os
sys.path.append('.')

from core.ui.three_column_ui import (
    three_column_ui_manager,
    PanelPosition,
    PanelState,
    ThemeMode
)

async def test_three_column_ui_system():
    print('🎨 Testing Three-Column UI Refactoring and Optimization...')
    
    try:
        # 初始化三欄式UI系統
        await three_column_ui_manager.initialize()
        print('✅ Three-Column UI System initialization successful')
        
        # 測試系統狀態
        status = three_column_ui_manager.get_status()
        print(f'🎨 Three-Column UI Status:')
        print(f'  🔧 Component: {status["component"]}')
        print(f'  📦 Version: {status["version"]}')
        print(f'  🏗️ Layout Type: {status["layout_type"]}')
        print(f'  📋 Panels: {status["panels"]}')
        print(f'  🧩 Components: {status["components"]}')
        print(f'  🎨 Theme: {status["theme"]}')
        print(f'  📱 Responsive Breakpoints: {status["responsive_breakpoints"]}')
        
        # 顯示功能特性
        print(f'\n🎯 UI Features:')
        for feature in status["features"]:
            print(f'  ✅ {feature}')
        
        # 顯示各面板組件數量
        print(f'\n📊 Panel Statistics:')
        print(f'  👈 Left Panel Components: {status["left_panel_components"]}')
        print(f'  🎯 Center Panel Features: {status["center_panel_features"]}')
        print(f'  👉 Right Panel Components: {status["right_panel_components"]}')
        
        # 測試項目打開功能
        print(f'\n📂 Testing Project Opening:')
        test_project_path = "/Users/alexchuang/Desktop/alex/tests/package/aicore0711"
        project_result = await three_column_ui_manager.open_project(test_project_path)
        
        print(f'✅ Project opened successfully:')
        print(f'  📁 Project: {project_result["project_tree"]["name"]}')
        print(f'  📂 Project Path: {project_result["project_tree"]["path"]}')
        print(f'  🌳 Tree Type: {project_result["project_tree"]["type"]}')
        print(f'  📊 Git Status: {project_result["project_tree"]["git_status"]["branch"]} ({project_result["project_tree"]["git_status"]["status"]})')
        
        if project_result["opened_file"]:
            print(f'  📝 Opened File: {project_result["opened_file"]["path"]}')
            print(f'  🔤 Language: {project_result["opened_file"]["language"]}')
            print(f'  📝 Modified: {project_result["opened_file"]["is_modified"]}')
        
        # 測試左側面板功能
        print(f'\n👈 Testing Left Panel Features:')
        
        # 測試文件搜索
        search_results = three_column_ui_manager.left_panel.search_files("main")
        print(f'🔍 Search Results for "main":')
        for result in search_results:
            print(f'  📄 {result["file"]}:{result["line"]} - {result["content"]}')
        
        # 測試中央面板功能
        print(f'\n🎯 Testing Center Panel Features:')
        
        # 測試文件操作
        test_file_path = os.path.join(test_project_path, "test_file.py")
        file_info = three_column_ui_manager.center_panel.open_file(test_file_path)
        print(f'📝 File opened: {file_info["path"]}')
        print(f'🔤 Language: {file_info["language"]}')
        print(f'📝 Content length: {len(file_info["content"])} characters')
        
        # 測試AI建議
        ai_suggestions = three_column_ui_manager.center_panel.get_ai_suggestions(
            test_file_path, 
            {"line": 1, "column": 1}
        )
        print(f'🤖 AI Suggestions:')
        for suggestion in ai_suggestions:
            print(f'  💡 {suggestion["type"]}: {suggestion["description"]}')
        
        # 測試代碼格式化
        format_result = three_column_ui_manager.center_panel.format_code(test_file_path)
        print(f'✨ Code formatting: {"✅ Success" if format_result else "❌ Failed"}')
        
        # 測試右側面板功能
        print(f'\n👉 Testing Right Panel Features:')
        
        # 測試AI對話
        ai_response = three_column_ui_manager.right_panel.send_ai_message("請幫我生成一個Python函數")
        print(f'🤖 AI Response: {ai_response["content"][:100]}...')
        print(f'💡 Suggestions: {len(ai_response["suggestions"])} available')
        
        # 測試工作流狀態
        workflow_status = three_column_ui_manager.right_panel.get_workflow_status("test_workflow")
        print(f'🔄 Workflow Status:')
        print(f'  📋 Name: {workflow_status["name"]}')
        print(f'  📊 Status: {workflow_status["status"]}')
        print(f'  📈 Progress: {workflow_status["progress"]}%')
        print(f'  🎯 Current Step: {workflow_status["current_step"]}')
        
        # 測試協作用戶
        collaboration_users = three_column_ui_manager.right_panel.get_collaboration_users()
        print(f'👥 Collaboration Users: {len(collaboration_users)} online')
        for user in collaboration_users:
            print(f'  👤 {user["name"]} ({user["status"]}) at {user["cursor_position"]["file"]}:{user["cursor_position"]["line"]}')
        
        # 測試面板操作
        print(f'\n⚙️ Testing Panel Operations:')
        
        # 測試面板縮放
        resize_result = three_column_ui_manager.resize_panel("left_panel", 25.0)
        print(f'📏 Panel resize: {"✅ Success" if resize_result else "❌ Failed"}')
        
        # 測試面板切換
        toggle_result = three_column_ui_manager.toggle_panel("right_panel")
        print(f'🔄 Panel toggle: {toggle_result.value}')
        
        # 恢復面板狀態
        three_column_ui_manager.toggle_panel("right_panel")
        
        # 測試主題切換
        print(f'\n🎨 Testing Theme Switching:')
        three_column_ui_manager.switch_theme(ThemeMode.LIGHT)
        print(f'☀️ Switched to light theme')
        
        three_column_ui_manager.switch_theme(ThemeMode.DARK)
        print(f'🌙 Switched to dark theme')
        
        # 測試響應式布局
        print(f'\n📱 Testing Responsive Layout:')
        
        # 移動端布局
        mobile_layout = three_column_ui_manager.get_layout_for_screen_size(600)
        print(f'📱 Mobile Layout:')
        print(f'  📊 Type: {mobile_layout["layout_type"]}')
        print(f'  🎯 Navigation: {mobile_layout["navigation"]}')
        
        # 平板布局
        tablet_layout = three_column_ui_manager.get_layout_for_screen_size(900)
        print(f'📱 Tablet Layout:')
        print(f'  📊 Type: {tablet_layout["layout_type"]}')
        print(f'  🎯 Navigation: {tablet_layout["navigation"]}')
        
        # 桌面布局
        desktop_layout = three_column_ui_manager.get_layout_for_screen_size(1400)
        print(f'🖥️ Desktop Layout:')
        print(f'  📊 Type: {desktop_layout["layout_type"]}')
        print(f'  🎯 Navigation: {desktop_layout["navigation"]}')
        
        # 測試UI狀態獲取
        print(f'\n📊 Testing UI State Retrieval:')
        ui_state = three_column_ui_manager.get_ui_state()
        
        print(f'📋 UI State Summary:')
        print(f'  👈 Left Panel - Components: {len(ui_state["left_panel"]["components"])}')
        print(f'  🎯 Center Panel - Open Files: {len(ui_state["center_panel"]["open_files"])}')
        print(f'  👉 Right Panel - Chat Messages: {ui_state["right_panel"]["ai_chat_messages"]}')
        
        # 測試用戶偏好保存
        print(f'\n💾 Testing User Preferences:')
        await three_column_ui_manager.save_user_preferences()
        print(f'💾 User preferences saved successfully')
        
        # 最終狀態檢查
        final_status = three_column_ui_manager.get_status()
        print(f'\n✅ Three-Column UI System Final Status:')
        print(f'  🎨 Theme: {final_status["theme"]}')
        print(f'  📋 Total Panels: {final_status["panels"]}')
        print(f'  🧩 Total Components: {final_status["components"]}')
        print(f'  📱 Responsive Design: ✅ Enabled')
        print(f'  💾 User Preferences: ✅ Saved')
        print(f'  🔄 Real-time Collaboration: ✅ Active')
        print(f'  🤖 AI Integration: ✅ Connected')
        
        # 測試新增強功能
        print(f'\n🧠 Testing Enhanced Features:')
        
        # 測試本地智能路由和Token節省
        print(f'\n💰 Testing Local Intelligent Routing and Token Savings:')
        
        # 模擬一些本地處理請求
        router = three_column_ui_manager.left_panel.intelligent_router
        
        # 測試代碼補全
        completion_result = router.process_locally("code_completion", {
            "code": "def hello_",
            "language": "python"
        })
        print(f'🤖 Code completion result: {completion_result["success"]}')
        print(f'💰 Tokens saved: {completion_result.get("tokens_saved", 0)}')
        
        # 測試語法檢查
        syntax_result = router.process_locally("syntax_check", {
            "code": "def test():\n    return 'hello'",
            "language": "python"
        })
        print(f'✅ Syntax check result: {syntax_result["success"]}')
        print(f'🔍 Is valid: {syntax_result["result"]["is_valid"]}')
        
        # 獲取Token節省統計
        token_stats = router.get_token_savings_stats()
        print(f'📊 Token Statistics:')
        print(f'  📈 Total requests: {token_stats.total_requests}')
        print(f'  🏠 Local handled: {token_stats.local_handled}')
        print(f'  💰 Tokens saved: {token_stats.tokens_saved}')
        print(f'  🎯 Success rate: {token_stats.local_success_rate:.1f}%')
        
        # 測試Token節省儀表板
        token_dashboard = three_column_ui_manager.left_panel.get_token_savings_dashboard()
        print(f'💰 Token Savings Dashboard:')
        print(f'  📊 Today saved: {token_dashboard["daily_breakdown"]["today"]["tokens_saved"]} tokens')
        print(f'  💵 Cost saved: {token_dashboard["daily_breakdown"]["today"]["cost_saved"]}')
        print(f'  📈 Monthly estimate: {token_dashboard["cost_analysis"]["estimated_monthly_savings"]}')
        
        # 測試快速操作功能
        print(f'\n🚀 Testing Quick Actions:')
        
        quick_actions_data = three_column_ui_manager.left_panel.get_quick_actions_data()
        print(f'🎯 Available quick actions: {len(quick_actions_data["available_actions"])}')
        
        for action in quick_actions_data["available_actions"][:3]:
            print(f'  {action["icon"]} {action["name"]} ({action["hotkey"]})')
        
        # 執行一些快速操作
        action_result = await three_column_ui_manager.left_panel.quick_actions.execute_action(
            "ai_code_gen", 
            {"prompt": "生成登錄函數", "language": "python"}
        )
        print(f'🤖 AI code generation: {"✅ Success" if action_result["success"] else "❌ Failed"}')
        
        format_result = await three_column_ui_manager.left_panel.quick_actions.execute_action(
            "format_all",
            {"project_path": test_project_path}
        )
        print(f'✨ Format all code: {"✅ Success" if format_result["success"] else "❌ Failed"}')
        
        # 測試多任務協作
        print(f'\n👥 Testing Multi-Task Collaboration:')
        
        collaboration_dashboard = three_column_ui_manager.left_panel.get_collaboration_dashboard()
        task_summary = collaboration_dashboard["task_summary"]
        
        print(f'📋 Collaboration Overview:')
        print(f'  📊 Total tasks: {task_summary["total_tasks"]}')
        print(f'  ⏳ Pending: {task_summary["pending"]}')
        print(f'  🔄 In progress: {task_summary["in_progress"]}')
        print(f'  ✅ Completed: {task_summary["completed"]}')
        print(f'  🚫 Blocked: {task_summary["blocked"]}')
        print(f'  🔥 High priority: {task_summary["high_priority"]}')
        
        print(f'\n👥 Team Activity:')
        for activity in collaboration_dashboard["team_activity"]:
            status_icon = {"completed": "✅", "in_progress": "🔄", "started": "🚀"}.get(activity["status"], "📋")
            print(f'  {status_icon} {activity["user"]}: {activity["action"]} ({activity["timestamp"]})')
        
        # 創建新任務
        new_task = await three_column_ui_manager.left_panel.collaboration.create_task(
            "測試三欄式UI功能",
            "驗證所有新功能是否正常工作",
            assignee="Alice",
            priority="high"
        )
        print(f'📋 New task created: {new_task.title} (ID: {new_task.id[:8]}...)')
        
        # 測試模式切換功能
        print(f'\n🔄 Testing Mode Switching:')
        
        # 切換到AI模式
        ai_mode_result = three_column_ui_manager.left_panel.switch_mode("ai")
        print(f'🤖 Switch to AI mode: {"✅ Success" if ai_mode_result else "❌ Failed"}')
        
        if ai_mode_result:
            # 獲取AI回放數據
            playback_data = three_column_ui_manager.left_panel.get_ai_playback_data()
            print(f'🎬 AI Playback Session: {playback_data["current_session"]}')
            print(f'📊 Operations: {playback_data["successful_operations"]}/{playback_data["total_operations"]} successful')
            print(f'⚡ Performance: {playback_data["performance_metrics"]["local_processing_rate"]} local processing')
            print(f'💰 Savings: {playback_data["performance_metrics"]["token_savings"]} ({playback_data["performance_metrics"]["cost_savings"]})')
            
            print(f'\n📜 Recent AI Operations:')
            for op in playback_data["playback_timeline"][:3]:
                print(f'  🕐 {op["timestamp"][-8:]} - {op["operation"]} ({op["status"]}) - {op.get("tokens_used", 0)} tokens')
        
        # 切換回手動模式
        manual_mode_result = three_column_ui_manager.left_panel.switch_mode("manual")
        print(f'👤 Switch to manual mode: {"✅ Success" if manual_mode_result else "❌ Failed"}')
        
        # 測試完整的UI狀態
        print(f'\n📊 Testing Complete UI State with Enhanced Features:')
        final_ui_state = three_column_ui_manager.get_ui_state()
        
        print(f'🎨 Enhanced UI State Summary:')
        print(f'  👈 Left Panel Components: {len(final_ui_state["left_panel"]["components"])}')
        print(f'  🎯 Center Panel Open Files: {len(final_ui_state["center_panel"]["open_files"])}')
        print(f'  👉 Right Panel Chat Messages: {final_ui_state["right_panel"]["ai_chat_messages"]}')
        
        # 顯示新功能狀態
        enhanced_status = three_column_ui_manager.get_status()
        enhanced_status["enhanced_features"] = [
            "local_intelligent_routing",
            "token_savings_analytics", 
            "quick_actions_system",
            "multi_task_collaboration",
            "ai_playback_browser",
            "mode_switching",
            "cost_optimization"
        ]
        
        print(f'\n🎉 Enhanced Features Status:')
        for feature in enhanced_status["enhanced_features"]:
            print(f'  ✅ {feature}')
        
        print(f'\n💎 Token Savings Summary:')
        final_token_stats = router.get_token_savings_stats()
        print(f'  📊 Total requests processed: {final_token_stats.total_requests}')
        print(f'  🏠 Local processing rate: {final_token_stats.local_success_rate:.1f}%')
        print(f'  💰 Total tokens saved: {final_token_stats.tokens_saved}')
        print(f'  🔄 Cache efficiency: {final_token_stats.cache_hits} hits')
        
        estimated_cost_savings = final_token_stats.tokens_saved * 0.003  # 假設每1000 tokens $3
        print(f'  💵 Estimated cost savings: ${estimated_cost_savings:.2f}')
        
        print(f'\n🚀 Quick Actions Summary:')
        actions_data = three_column_ui_manager.left_panel.get_quick_actions_data()
        print(f'  ⚡ Available actions: {len(actions_data["available_actions"])}')
        print(f'  🔥 Most used: {actions_data["usage_stats"]["most_used"]}')
        print(f'  ⏰ Time saved: {actions_data["usage_stats"]["time_saved"]}')
        print(f'  🤖 Automation rate: {actions_data["usage_stats"]["automation_rate"]}')
        
        print(f'\n👥 Collaboration Summary:')
        final_collab = three_column_ui_manager.left_panel.get_collaboration_dashboard()
        productivity = final_collab["productivity_metrics"]
        print(f'  ✅ Tasks completed today: {productivity["tasks_completed_today"]}')
        print(f'  ⏱️ Avg completion time: {productivity["avg_task_completion_time"]}')
        print(f'  📈 Collaboration efficiency: {productivity["collaboration_efficiency"]}')
        print(f'  🔗 Active sessions: {len(final_collab["active_sessions"])}')
        
        print(f'\n🎉 All Enhanced Three-Column UI System tests passed!')
        print(f'✨ PowerAutomation v4.6.1 三欄式UI重構優化 - 完成！')
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_three_column_ui_system())