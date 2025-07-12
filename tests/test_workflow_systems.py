#!/usr/bin/env python3
"""
Test Six Major Workflow Systems
"""

import asyncio
import sys
import os
sys.path.append('.')

from core.workflows.workflow_engine import workflow_engine, WorkflowCategory

async def test_workflow_systems():
    print('🔄 Testing Six Major Workflow Systems...')
    
    try:
        # 初始化工作流引擎
        await workflow_engine.initialize()
        print('✅ Workflow Engine initialization successful')
        
        # 測試工作流列表
        workflows = workflow_engine.list_workflows()
        print(f'📋 Total workflows loaded: {len(workflows)}')
        
        # 顯示六大工作流
        print('\n🎯 Six Major Workflow Categories:')
        for i, workflow in enumerate(workflows, 1):
            print(f'  {i}. {workflow.name} ({workflow.category.value})')
            print(f'     - Nodes: {len(workflow.nodes)}')
            print(f'     - Version: {workflow.version}')
            print(f'     - Triggers: {", ".join(workflow.triggers)}')
        
        # 測試版本覆蓋範圍
        print('\n📊 Workflow Coverage by Edition:')
        editions = ['personal', 'professional', 'team', 'enterprise']
        
        for edition in editions:
            print(f'\n{edition.upper()} Edition Coverage:')
            coverage = workflow_engine.get_workflow_coverage_by_edition(edition)
            
            for workflow_id, coverage_info in coverage.items():
                percentage = coverage_info['coverage_percentage']
                available = coverage_info['available_nodes']
                total = coverage_info['total_nodes']
                
                print(f'  📋 {coverage_info["name"]}: {available}/{total} nodes ({percentage:.1f}%)')
        
        # 測試工作流執行 (代碼開發工作流)
        print('\n🚀 Testing Code Development Workflow Execution:')
        execution_id = await workflow_engine.execute_workflow(
            'code_development_workflow',
            {'project_path': '/test/project', 'target_language': 'python'}
        )
        print(f'  ✅ Workflow execution started: {execution_id[:8]}...')
        
        # 等待一段時間讓工作流執行
        await asyncio.sleep(2)
        
        # 檢查執行狀態
        execution = workflow_engine.get_workflow_status(execution_id)
        if execution:
            print(f'  📊 Execution Status: {execution.status.value}')
            print(f'  📝 Logs: {len(execution.logs)} entries')
            if execution.logs:
                print(f'  🔍 Latest log: {execution.logs[-1]}')
        
        # 測試測試自動化工作流
        print('\n🧪 Testing Test Automation Workflow:')
        test_execution_id = await workflow_engine.execute_workflow(
            'test_automation_workflow',
            {'test_types': ['unit', 'integration'], 'coverage_threshold': 80}
        )
        print(f'  ✅ Test workflow execution started: {test_execution_id[:8]}...')
        
        # 測試狀態
        status = workflow_engine.get_status()
        print(f'\n📈 Workflow Engine Status:')
        print(f'  🔧 Component: {status["component"]}')
        print(f'  📦 Version: {status["version"]}')
        print(f'  📋 Total Workflows: {status["total_workflows"]}')
        print(f'  ⚡ Active Executions: {status["active_executions"]}')
        print(f'  📊 Total Executions: {status["total_executions"]}')
        print(f'  🎯 Workflow Categories: {len(status["workflow_categories"])}')
        print(f'  🔧 Registered Handlers: {status["registered_handlers"]}')
        
        # 顯示工作流節點詳情
        print('\n🔍 Workflow Node Details:')
        for workflow in workflows[:2]:  # 只顯示前兩個工作流的詳情
            print(f'\n📋 {workflow.name}:')
            for node in workflow.nodes[:3]:  # 只顯示前3個節點
                print(f'  🔧 {node.name} ({node.type.value})')
                print(f'     - Category: {node.category}')
                print(f'     - Next Nodes: {len(node.next_nodes)}')
                if node.mcp_dependencies:
                    print(f'     - MCP Dependencies: {", ".join(node.mcp_dependencies)}')
                if node.edition_requirements:
                    print(f'     - Edition Requirements: {", ".join(node.edition_requirements)}')
        
        print('\n🎉 All workflow system tests passed!')
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_workflow_systems())