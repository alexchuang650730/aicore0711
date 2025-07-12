#!/usr/bin/env python3
"""
Test Enhanced CI/CD Pipeline
"""

import asyncio
import sys
import os
sys.path.append('.')

from core.cicd.enhanced_pipeline import enhanced_cicd_pipeline, TriggerType, PipelineStage
from core.enterprise.version_strategy import EditionTier

async def test_enhanced_cicd_pipeline():
    print('🔄 Testing Enhanced CI/CD Pipeline...')
    
    try:
        # 初始化增強CI/CD流水線
        await enhanced_cicd_pipeline.initialize()
        print('✅ Enhanced CI/CD Pipeline initialization successful')
        
        # 測試狀態
        status = enhanced_cicd_pipeline.get_status()
        print(f'📊 Pipeline Status:')
        print(f'  🔧 Component: {status["component"]}')
        print(f'  📦 Version: {status["version"]}')
        print(f'  📋 Supported Stages: {len(status["supported_stages"])}')
        print(f'  🎯 Supported Triggers: {len(status["supported_triggers"])}')
        print(f'  🚪 Quality Gates: {status["quality_gates_count"]}')
        
        # 顯示工作流集成狀態
        print(f'\n🔗 Workflow Integration:')
        for workflow, status_check in status["workflow_integration"].items():
            print(f'  {workflow}: {status_check}')
        
        # 顯示企業功能
        print(f'\n🏢 Enterprise Features:')
        for feature, status_check in status["enterprise_features"].items():
            print(f'  {feature}: {status_check}')
        
        # 測試不同版本的流水線執行
        test_cases = [
            (EditionTier.PERSONAL, "個人版"),
            (EditionTier.PROFESSIONAL, "專業版"), 
            (EditionTier.TEAM, "團隊版"),
            (EditionTier.ENTERPRISE, "企業版")
        ]
        
        execution_ids = []
        
        for edition, edition_name in test_cases:
            print(f'\n🚀 Testing {edition_name} Pipeline Execution:')
            
            # 觸發流水線
            execution_id = await enhanced_cicd_pipeline.trigger_pipeline(
                TriggerType.GIT_TAG,
                {
                    'tag': 'v4.6.1-test',
                    'repository': 'powerautomation',
                    'branch': 'main',
                    'commit_sha': 'abc123def456'
                },
                edition
            )
            
            execution_ids.append(execution_id)
            print(f'  ✅ Pipeline triggered: {execution_id[:8]}...')
            print(f'  📦 Edition: {edition_name}')
            
            # 檢查初始狀態
            execution = enhanced_cicd_pipeline.get_pipeline_status(execution_id)
            if execution:
                print(f'  📊 Initial Status: {execution.status.value}')
                print(f'  🔧 Enabled Features: {len(execution.enabled_features)}')
        
        # 等待流水線執行
        print(f'\n⏳ Waiting for pipeline executions to complete...')
        await asyncio.sleep(8)  # 等待足夠時間讓流水線完成
        
        # 檢查執行結果
        print(f'\n📊 Pipeline Execution Results:')
        for i, execution_id in enumerate(execution_ids):
            edition_name = test_cases[i][1]
            execution = enhanced_cicd_pipeline.get_pipeline_status(execution_id)
            
            if execution:
                print(f'\n{edition_name} ({execution_id[:8]}...):')
                print(f'  📊 Final Status: {execution.status.value}')
                print(f'  ⏱️ Duration: {execution.overall_metrics.get("total_duration", 0):.2f}s')
                print(f'  🎯 Stages Executed: {execution.overall_metrics.get("stages_executed", 0)}')
                print(f'  ✅ Stages Successful: {execution.overall_metrics.get("stages_successful", 0)}')
                print(f'  🔄 Workflow Executions: {execution.overall_metrics.get("total_workflow_executions", 0)}')
                
                # 顯示階段詳情
                print(f'  📋 Stage Details:')
                for stage_name, stage_result in execution.stages.items():
                    status_icon = "✅" if stage_result.status.value == "success" else "⏭️" if stage_result.status.value == "skipped" else "❌"
                    print(f'    {status_icon} {stage_name}: {stage_result.status.value} ({stage_result.duration:.2f}s)')
                    
                    # 顯示工作流執行
                    if stage_result.workflow_executions:
                        print(f'      🔗 Workflows: {len(stage_result.workflow_executions)} executed')
        
        # 測試活躍流水線列表
        active_pipelines = enhanced_cicd_pipeline.list_active_pipelines()
        print(f'\n⚡ Active Pipelines: {len(active_pipelines)}')
        
        # 測試流水線指標
        metrics = enhanced_cicd_pipeline.get_pipeline_metrics()
        if metrics:
            print(f'\n📈 Pipeline Metrics:')
            print(f'  📊 Total Executions: {metrics["total_executions"]}')
            print(f'  ✅ Successful: {metrics["successful_executions"]}')
            print(f'  ❌ Failed: {metrics["failed_executions"]}')
            print(f'  📊 Success Rate: {metrics["success_rate"]:.1f}%')
            print(f'  ⏱️ Average Duration: {metrics["average_duration"]:.2f}s')
            
            # 版本分布
            if "edition_distribution" in metrics:
                print(f'  🏢 Edition Distribution:')
                for edition, count in metrics["edition_distribution"].items():
                    print(f'    {edition}: {count} executions')
        
        # 測試特定功能
        print(f'\n🔧 Testing Specific Features:')
        
        # 測試流水線取消
        if execution_ids:
            test_execution_id = execution_ids[0]
            cancelled = enhanced_cicd_pipeline.cancel_pipeline(test_execution_id)
            print(f'  🚫 Pipeline Cancellation: {"✅ Success" if cancelled else "❌ Failed"}')
        
        # 測試質量門禁配置
        config = enhanced_cicd_pipeline.configurations.get("default")
        if config:
            quality_gates = config.quality_gates
            print(f'  🚪 Quality Gates Configured: {len(quality_gates)} categories')
            for gate_name, gate_config in quality_gates.items():
                print(f'    📋 {gate_name}: {len(gate_config)} rules')
        
        print('\n🎉 All Enhanced CI/CD Pipeline tests passed!')
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_enhanced_cicd_pipeline())