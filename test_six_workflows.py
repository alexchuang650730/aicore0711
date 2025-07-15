#!/usr/bin/env python3
"""
測試六大工作流系統的完整功能
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.workflows.workflow_engine import workflow_engine, WorkflowCategory

async def test_workflow_engine_initialization():
    """測試工作流引擎初始化"""
    print("🔄 測試工作流引擎初始化...")
    
    await workflow_engine.initialize()
    
    status = workflow_engine.get_status()
    print(f"✅ 工作流引擎已初始化")
    print(f"   📊 總工作流數: {status['total_workflows']}")
    print(f"   🎯 工作流分類: {len(status['workflow_categories'])}")
    print(f"   🔧 節點處理器: {status['registered_handlers']}")
    print(f"   📋 支持的節點類型: {len(status['supported_node_types'])}")
    
    return status['total_workflows'] == 6

async def test_six_major_workflows():
    """測試六大工作流系統"""
    print("\n🎯 測試六大工作流系統...")
    
    workflows = workflow_engine.list_workflows()
    
    expected_workflows = [
        "code_development_workflow",
        "test_automation_workflow", 
        "deployment_release_workflow",
        "project_management_workflow",
        "collaboration_communication_workflow",
        "monitoring_operations_workflow"
    ]
    
    workflow_names = [w.id for w in workflows]
    
    print(f"✅ 發現 {len(workflows)} 個工作流:")
    for workflow in workflows:
        print(f"   📋 {workflow.name} ({workflow.category.value})")
        print(f"      - 節點數: {len(workflow.nodes)}")
        print(f"      - 版本: {workflow.version}")
        print(f"      - 觸發器: {', '.join(workflow.triggers)}")
    
    # 檢查是否所有期望的工作流都存在
    missing_workflows = [wf for wf in expected_workflows if wf not in workflow_names]
    if missing_workflows:
        print(f"❌ 缺少工作流: {missing_workflows}")
        return False
    
    return True

async def test_code_development_workflow():
    """測試代碼開發工作流"""
    print("\n🛠️ 測試代碼開發工作流...")
    
    try:
        execution_id = await workflow_engine.execute_workflow(
            "code_development_workflow", 
            {"project_path": "/test/project", "target_language": "python"}
        )
        
        # 等待執行完成
        await asyncio.sleep(2)
        
        execution = workflow_engine.get_workflow_status(execution_id)
        
        print(f"✅ 代碼開發工作流執行完成")
        print(f"   🆔 執行ID: {execution_id}")
        print(f"   📊 狀態: {execution.status.value}")
        print(f"   📝 日誌條目: {len(execution.logs)}")
        
        # 顯示執行日誌
        for log in execution.logs:
            print(f"      📄 {log}")
        
        return execution.status.value == "completed"
        
    except Exception as e:
        print(f"❌ 代碼開發工作流測試失敗: {e}")
        return False

async def test_test_automation_workflow():
    """測試測試自動化工作流"""
    print("\n🧪 測試測試自動化工作流...")
    
    try:
        execution_id = await workflow_engine.execute_workflow(
            "test_automation_workflow", 
            {"test_types": ["unit", "integration", "ui"], "coverage_threshold": 80}
        )
        
        # 等待執行完成
        await asyncio.sleep(2)
        
        execution = workflow_engine.get_workflow_status(execution_id)
        
        print(f"✅ 測試自動化工作流執行完成")
        print(f"   🆔 執行ID: {execution_id}")
        print(f"   📊 狀態: {execution.status.value}")
        print(f"   📝 日誌條目: {len(execution.logs)}")
        
        return execution.status.value == "completed"
        
    except Exception as e:
        print(f"❌ 測試自動化工作流測試失敗: {e}")
        return False

async def test_deployment_release_workflow():
    """測試部署發布工作流"""
    print("\n🚀 測試部署發布工作流...")
    
    try:
        execution_id = await workflow_engine.execute_workflow(
            "deployment_release_workflow", 
            {"environments": ["staging", "production"], "rollback_enabled": True}
        )
        
        # 等待執行完成
        await asyncio.sleep(2)
        
        execution = workflow_engine.get_workflow_status(execution_id)
        
        print(f"✅ 部署發布工作流執行完成")
        print(f"   🆔 執行ID: {execution_id}")
        print(f"   📊 狀態: {execution.status.value}")
        print(f"   📝 日誌條目: {len(execution.logs)}")
        
        return execution.status.value == "completed"
        
    except Exception as e:
        print(f"❌ 部署發布工作流測試失敗: {e}")
        return False

async def test_project_management_workflow():
    """測試項目管理工作流"""
    print("\n📊 測試項目管理工作流...")
    
    try:
        execution_id = await workflow_engine.execute_workflow(
            "project_management_workflow", 
            {"project_type": "software", "methodology": "agile"}
        )
        
        # 等待執行完成
        await asyncio.sleep(2)
        
        execution = workflow_engine.get_workflow_status(execution_id)
        
        print(f"✅ 項目管理工作流執行完成")
        print(f"   🆔 執行ID: {execution_id}")
        print(f"   📊 狀態: {execution.status.value}")
        print(f"   📝 日誌條目: {len(execution.logs)}")
        
        return execution.status.value == "completed"
        
    except Exception as e:
        print(f"❌ 項目管理工作流測試失敗: {e}")
        return False

async def test_collaboration_communication_workflow():
    """測試協作溝通工作流"""
    print("\n🤝 測試協作溝通工作流...")
    
    try:
        execution_id = await workflow_engine.execute_workflow(
            "collaboration_communication_workflow", 
            {"max_participants": 10, "recording_enabled": True}
        )
        
        # 等待執行完成
        await asyncio.sleep(2)
        
        execution = workflow_engine.get_workflow_status(execution_id)
        
        print(f"✅ 協作溝通工作流執行完成")
        print(f"   🆔 執行ID: {execution_id}")
        print(f"   📊 狀態: {execution.status.value}")
        print(f"   📝 日誌條目: {len(execution.logs)}")
        
        return execution.status.value == "completed"
        
    except Exception as e:
        print(f"❌ 協作溝通工作流測試失敗: {e}")
        return False

async def test_monitoring_operations_workflow():
    """測試監控運維工作流"""
    print("\n📈 測試監控運維工作流...")
    
    try:
        execution_id = await workflow_engine.execute_workflow(
            "monitoring_operations_workflow", 
            {"monitoring_interval": 60, "auto_response_enabled": True}
        )
        
        # 等待執行完成
        await asyncio.sleep(2)
        
        execution = workflow_engine.get_workflow_status(execution_id)
        
        print(f"✅ 監控運維工作流執行完成")
        print(f"   🆔 執行ID: {execution_id}")
        print(f"   📊 狀態: {execution.status.value}")
        print(f"   📝 日誌條目: {len(execution.logs)}")
        
        return execution.status.value == "completed"
        
    except Exception as e:
        print(f"❌ 監控運維工作流測試失敗: {e}")
        return False

async def test_workflow_edition_coverage():
    """測試工作流版本覆蓋範圍"""
    print("\n📦 測試工作流版本覆蓋範圍...")
    
    editions = ["personal", "professional", "team", "enterprise"]
    
    for edition in editions:
        print(f"\n🔍 {edition.upper()} 版本覆蓋範圍:")
        coverage = workflow_engine.get_workflow_coverage_by_edition(edition)
        
        total_workflows = len(coverage)
        total_coverage = sum(wf["coverage_percentage"] for wf in coverage.values()) / total_workflows
        
        print(f"   📊 總體覆蓋率: {total_coverage:.1f}%")
        
        for workflow_id, info in coverage.items():
            print(f"   📋 {info['name']}: {info['coverage_percentage']:.1f}% "
                  f"({info['available_nodes']}/{info['total_nodes']} 節點)")
    
    return True

async def test_parallel_workflow_execution():
    """測試並行工作流執行"""
    print("\n⚡ 測試並行工作流執行...")
    
    try:
        # 並行執行多個工作流
        execution_ids = await asyncio.gather(
            workflow_engine.execute_workflow("code_development_workflow", {"project": "test1"}),
            workflow_engine.execute_workflow("test_automation_workflow", {"project": "test2"}),
            workflow_engine.execute_workflow("deployment_release_workflow", {"project": "test3"})
        )
        
        print(f"✅ 啟動了 {len(execution_ids)} 個並行工作流")
        for i, exec_id in enumerate(execution_ids):
            print(f"   🆔 執行 {i+1}: {exec_id}")
        
        # 等待所有執行完成
        await asyncio.sleep(3)
        
        # 檢查執行狀態
        completed = 0
        for exec_id in execution_ids:
            execution = workflow_engine.get_workflow_status(exec_id)
            if execution.status.value == "completed":
                completed += 1
        
        print(f"✅ 完成 {completed}/{len(execution_ids)} 個並行工作流")
        
        return completed == len(execution_ids)
        
    except Exception as e:
        print(f"❌ 並行工作流執行測試失敗: {e}")
        return False

async def test_workflow_error_handling():
    """測試工作流錯誤處理"""
    print("\n🚨 測試工作流錯誤處理...")
    
    try:
        # 測試不存在的工作流
        try:
            await workflow_engine.execute_workflow("nonexistent_workflow", {})
            print("❌ 應該拋出異常但沒有")
            return False
        except ValueError as e:
            print(f"✅ 正確處理不存在的工作流: {e}")
        
        # 測試工作流狀態查詢
        status = workflow_engine.get_workflow_status("nonexistent_execution")
        if status is None:
            print("✅ 正確處理不存在的執行ID")
        else:
            print("❌ 應該返回None")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流錯誤處理測試失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("🧪 PowerAutomation v4.6.9.5 - 六大工作流系統測試")
    print("=" * 60)
    
    tests = [
        ("工作流引擎初始化", test_workflow_engine_initialization),
        ("六大工作流系統", test_six_major_workflows),
        ("代碼開發工作流", test_code_development_workflow),
        ("測試自動化工作流", test_test_automation_workflow),
        ("部署發布工作流", test_deployment_release_workflow),
        ("項目管理工作流", test_project_management_workflow),
        ("協作溝通工作流", test_collaboration_communication_workflow),
        ("監控運維工作流", test_monitoring_operations_workflow),
        ("工作流版本覆蓋範圍", test_workflow_edition_coverage),
        ("並行工作流執行", test_parallel_workflow_execution),
        ("工作流錯誤處理", test_workflow_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 測試: {test_name}")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name} - 通過")
            else:
                print(f"❌ {test_name} - 失敗")
        except Exception as e:
            print(f"❌ {test_name} - 異常: {e}")
    
    print(f"\n📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！")
        print("✅ 六大工作流系統正常運作")
        print("🔧 所有節點處理器運行正常")
        print("⚡ 支持並行執行")
        print("📦 支持版本權限控制")
    else:
        print("❌ 部分測試失敗")
        print("⚠️ 請檢查工作流配置")
    
    # 顯示最終狀態
    final_status = workflow_engine.get_status()
    print(f"\n📋 工作流引擎最終狀態:")
    print(f"   📊 總工作流: {final_status['total_workflows']}")
    print(f"   ⚡ 活躍執行: {final_status['active_executions']}")
    print(f"   📈 總執行數: {final_status['total_executions']}")

if __name__ == "__main__":
    asyncio.run(main())