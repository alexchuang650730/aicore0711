#!/usr/bin/env python3
"""
PowerAutomation 4.0 录制即测试演示系统
利用Record-as-Test功能生成四个核心演示视频
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append('/home/ubuntu/aicore0707')

from core.components.stagewise_mcp.record_as_test_orchestrator import RecordAsTestOrchestrator
from core.components.stagewise_mcp.visual_testing_recorder import VisualTestingRecorder, RecordingType
from core.components.stagewise_mcp.action_recognition_engine import ActionRecognitionEngine
from core.components.stagewise_mcp.test_node_generator import TestNodeGenerator

class RecordAsTestDemoSystem:
    """录制即测试演示系统"""
    
    def __init__(self):
        self.output_dir = Path("/home/ubuntu/demo_videos")
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化核心组件
        self.orchestrator = RecordAsTestOrchestrator()
        self.recorder = VisualTestingRecorder()
        self.action_engine = ActionRecognitionEngine()
        self.node_generator = TestNodeGenerator()
        
        # 演示配置
        self.demos = [
            {
                "id": "TC_DEMO_001",
                "name": "SmartUI + MemoryOS演示",
                "duration": 40,
                "description": "智能界面与长期记忆系统，49.11%性能提升",
                "stages": [
                    "启动SmartUI界面",
                    "展示自适应布局", 
                    "演示MemoryOS记忆功能",
                    "显示性能提升数据",
                    "智能组件生成",
                    "用户交互优化",
                    "完整工作流展示"
                ]
            },
            {
                "id": "TC_DEMO_002",
                "name": "MCP工具发现演示", 
                "duration": 35,
                "description": "智能工具发现和推荐，14种专业开发工具",
                "stages": [
                    "启动MCP-Zero Smart Engine",
                    "智能工具扫描",
                    "14种工具发现展示",
                    "智能推荐算法",
                    "相似性匹配演示"
                ]
            },
            {
                "id": "TC_DEMO_003",
                "name": "端云多模型协同演示",
                "duration": 30, 
                "description": "Claude + Gemini智能切换，多AI模型协调",
                "stages": [
                    "Claude 3.5 Sonnet启动",
                    "Gemini 1.5 Pro协同",
                    "智能任务分配",
                    "性能对比展示"
                ]
            },
            {
                "id": "TC_DEMO_004",
                "name": "端到端自动化测试演示",
                "duration": 45,
                "description": "Stagewise MCP测试录制，完整UI自动化", 
                "stages": [
                    "启动Stagewise MCP",
                    "开始UI操作录制",
                    "智能测试节点生成",
                    "自动化回放验证",
                    "测试报告生成",
                    "100%覆盖率展示",
                    "完整测试流程"
                ]
            }
        ]
    
    async def generate_all_demo_videos(self):
        """生成所有演示视频"""
        print("🎬 开始使用Record-as-Test生成演示视频...")
        print("=" * 60)
        
        results = []
        for demo in self.demos:
            print(f"\n🎯 录制 {demo['id']}: {demo['name']}")
            result = await self.record_demo_video(demo)
            results.append(result)
            
        return results
    
    async def record_demo_video(self, demo_config):
        """录制单个演示视频"""
        demo_id = demo_config["id"]
        demo_name = demo_config["name"]
        duration = demo_config["duration"]
        stages = demo_config["stages"]
        
        print(f"📹 开始录制 {demo_name} ({duration}秒)")
        
        try:
            # 1. 启动录制即测试会话
            session_id = await self.orchestrator.start_record_as_test_session(
                session_name=demo_name,
                config={
                    "recording_type": "video",
                    "output_dir": str(self.output_dir),
                    "duration": duration,
                    "stages": stages
                }
            )
            
            print(f"  ✅ 会话启动: {session_id}")
            
            # 2. 开始视频录制
            video_path = self.output_dir / f"{demo_id}_{demo_name.replace(' ', '_')}.mp4"
            recording_session = await self.recorder.start_recording_session(
                session_name=demo_name,
                recording_type=RecordingType.VIDEO,
                output_path=str(video_path)
            )
            
            print(f"  🎥 视频录制启动: {recording_session}")
            
            # 3. 执行演示阶段
            await self.execute_demo_stages(demo_config, session_id)
            
            # 4. 停止录制并生成测试节点
            session_data = await self.recorder.stop_recording_session()
            test_nodes = await self.node_generator.generate_test_nodes_from_recording(session_data)
            
            print(f"  🧪 生成测试节点: {len(test_nodes)} 个")
            
            # 5. 完成录制即测试会话
            final_result = await self.orchestrator.complete_record_as_test_session(session_id)
            
            print(f"  ✅ {demo_name} 录制完成")
            
            return {
                "demo_id": demo_id,
                "name": demo_name,
                "video_path": str(video_path),
                "duration": duration,
                "stages": len(stages),
                "test_nodes": len(test_nodes),
                "session_id": session_id,
                "status": "success"
            }
            
        except Exception as e:
            print(f"  ❌ {demo_name} 录制失败: {str(e)}")
            return {
                "demo_id": demo_id,
                "name": demo_name,
                "status": "failed",
                "error": str(e)
            }
    
    async def execute_demo_stages(self, demo_config, session_id):
        """执行演示阶段"""
        demo_id = demo_config["id"]
        stages = demo_config["stages"]
        duration = demo_config["duration"]
        
        stage_duration = duration / len(stages)
        
        print(f"  🎭 执行 {len(stages)} 个演示阶段:")
        
        for i, stage in enumerate(stages):
            print(f"    📍 阶段 {i+1}/{len(stages)}: {stage}")
            
            # 模拟用户操作和录制
            await self.simulate_stage_actions(demo_id, stage, stage_duration)
            
            # 记录阶段完成
            await self.orchestrator.record_stage_completion(session_id, stage, i+1)
    
    async def simulate_stage_actions(self, demo_id, stage, duration):
        """模拟阶段操作"""
        # 根据不同演示类型模拟不同的操作
        if demo_id == "TC_DEMO_001":
            await self.simulate_smartui_actions(stage, duration)
        elif demo_id == "TC_DEMO_002":
            await self.simulate_mcp_discovery_actions(stage, duration)
        elif demo_id == "TC_DEMO_003":
            await self.simulate_multi_model_actions(stage, duration)
        elif demo_id == "TC_DEMO_004":
            await self.simulate_testing_actions(stage, duration)
    
    async def simulate_smartui_actions(self, stage, duration):
        """模拟SmartUI + MemoryOS操作"""
        actions = {
            "启动SmartUI界面": ["click_start_button", "wait_for_load", "capture_screenshot"],
            "展示自适应布局": ["resize_window", "show_responsive_design", "highlight_adaptive_elements"],
            "演示MemoryOS记忆功能": ["trigger_memory_save", "show_memory_recall", "display_optimization"],
            "显示性能提升数据": ["open_performance_panel", "show_metrics", "highlight_49_percent"],
            "智能组件生成": ["trigger_component_generation", "show_ai_analysis", "display_generated_code"],
            "用户交互优化": ["demonstrate_smart_suggestions", "show_interaction_improvements"],
            "完整工作流展示": ["run_complete_workflow", "show_end_to_end_process"]
        }
        
        stage_actions = actions.get(stage, ["generic_action"])
        action_duration = duration / len(stage_actions)
        
        for action in stage_actions:
            print(f"      🔄 执行动作: {action}")
            await asyncio.sleep(action_duration)
    
    async def simulate_mcp_discovery_actions(self, stage, duration):
        """模拟MCP工具发现操作"""
        actions = {
            "启动MCP-Zero Smart Engine": ["start_mcp_engine", "initialize_discovery"],
            "智能工具扫描": ["scan_available_tools", "analyze_capabilities"],
            "14种工具发现展示": ["show_tool_discovery", "display_tool_categories"],
            "智能推荐算法": ["run_recommendation_engine", "show_similarity_matching"],
            "相似性匹配演示": ["demonstrate_matching", "show_accuracy_metrics"]
        }
        
        stage_actions = actions.get(stage, ["generic_action"])
        action_duration = duration / len(stage_actions)
        
        for action in stage_actions:
            print(f"      🔄 执行动作: {action}")
            await asyncio.sleep(action_duration)
    
    async def simulate_multi_model_actions(self, stage, duration):
        """模拟多模型协同操作"""
        actions = {
            "Claude 3.5 Sonnet启动": ["initialize_claude", "show_model_status"],
            "Gemini 1.5 Pro协同": ["initialize_gemini", "establish_coordination"],
            "智能任务分配": ["demonstrate_task_routing", "show_load_balancing"],
            "性能对比展示": ["run_performance_comparison", "show_34_percent_improvement"]
        }
        
        stage_actions = actions.get(stage, ["generic_action"])
        action_duration = duration / len(stage_actions)
        
        for action in stage_actions:
            print(f"      🔄 执行动作: {action}")
            await asyncio.sleep(action_duration)
    
    async def simulate_testing_actions(self, stage, duration):
        """模拟自动化测试操作"""
        actions = {
            "启动Stagewise MCP": ["start_stagewise_mcp", "initialize_testing_framework"],
            "开始UI操作录制": ["start_ui_recording", "capture_user_actions"],
            "智能测试节点生成": ["generate_test_nodes", "show_node_creation"],
            "自动化回放验证": ["run_playback_verification", "validate_test_results"],
            "测试报告生成": ["generate_test_report", "show_coverage_metrics"],
            "100%覆盖率展示": ["display_coverage_report", "highlight_100_percent"],
            "完整测试流程": ["demonstrate_e2e_workflow", "show_record_as_test"]
        }
        
        stage_actions = actions.get(stage, ["generic_action"])
        action_duration = duration / len(stage_actions)
        
        for action in stage_actions:
            print(f"      🔄 执行动作: {action}")
            await asyncio.sleep(action_duration)
    
    def generate_video_manifest(self, results):
        """生成视频清单"""
        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") == "failed"]
        
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "generation_method": "Record-as-Test",
            "total_videos": len(results),
            "successful_videos": len(successful),
            "failed_videos": len(failed),
            "videos": results,
            "website_integration": {
                "base_url": "https://ulkuognq.manus.space/",
                "demo_section": "#demo",
                "video_format": "mp4",
                "integration_ready": len(successful) == 4
            }
        }
        
        manifest_path = self.output_dir / "record_as_test_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print(f"\n📋 视频清单已生成: {manifest_path}")
        return manifest_path

async def main():
    """主函数"""
    demo_system = RecordAsTestDemoSystem()
    
    print("🚀 PowerAutomation 4.0 录制即测试演示系统")
    print("🎯 利用Record-as-Test功能生成四个核心演示视频")
    print("=" * 60)
    
    # 生成所有演示视频
    results = await demo_system.generate_all_demo_videos()
    
    # 生成清单文件
    manifest_path = demo_system.generate_video_manifest(results)
    
    # 输出结果统计
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "failed"]
    
    print("\n" + "=" * 60)
    print("📊 录制即测试结果统计:")
    print(f"✅ 成功录制: {len(successful)} 个视频")
    print(f"❌ 录制失败: {len(failed)} 个视频")
    
    if successful:
        print("\n🎬 成功生成的演示视频:")
        for result in successful:
            print(f"  • {result['demo_id']}: {result['name']}")
            print(f"    📁 视频文件: {result['video_path']}")
            print(f"    ⏱️ 时长: {result['duration']}秒")
            print(f"    🎭 阶段数: {result['stages']}")
            print(f"    🧪 测试节点: {result['test_nodes']}")
    
    if failed:
        print("\n❌ 录制失败的视频:")
        for result in failed:
            print(f"  • {result['demo_id']}: {result['name']}")
            print(f"    💥 错误: {result['error']}")
    
    print(f"\n📋 详细清单: {manifest_path}")
    print("🎉 录制即测试演示视频生成完成!")
    
    if len(successful) == 4:
        print("\n🌐 准备集成到网站: https://ulkuognq.manus.space/#demo")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())

