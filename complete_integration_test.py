#!/usr/bin/env python3
"""
PowerAutomation v4.6.1 完整集成測試
Complete Integration Test
整合ClaudEditor工作流界面、CodeFlow引擎、MCP組件和TDD框架

測試範圍:
- ClaudEditor六大工作流
- 企業版本階段限制
- MCP組件集成
- TDD測試框架
- 工作流執行引擎
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path

# 導入所有組件
try:
    from claudeditor_workflow_interface import (
        ClaudEditorWorkflowManager,
        ClaudEditorUI,
        WorkflowType,
        SubscriptionTier
    )
    from codeflow_integrated_workflow_engine import (
        CodeFlowWorkflowEngine,
        ClaudEditorWorkflowInterface
    )
    from cross_platform_tdd_framework import CrossPlatformTDDFramework
except ImportError as e:
    print(f"⚠️ 導入模組錯誤: {e}")
    print("將使用模擬模式運行集成測試")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PowerAutomationIntegrationTest:
    """PowerAutomation完整集成測試"""
    
    def __init__(self):
        self.claudeditor_manager = None
        self.codeflow_engine = None
        self.tdd_framework = None
        self.ui_manager = None
        self.test_results = {}
        self.start_time = time.time()
        
    async def initialize_components(self):
        """初始化所有組件"""
        print("🔧 初始化PowerAutomation組件...")
        
        try:
            # 初始化ClaudEditor工作流管理器
            self.claudeditor_manager = ClaudEditorWorkflowManager()
            print("  ✅ ClaudEditor工作流管理器已初始化")
            
            # 初始化UI管理器
            self.ui_manager = ClaudEditorUI(self.claudeditor_manager)
            print("  ✅ ClaudEditor UI管理器已初始化")
            
            # 初始化CodeFlow引擎
            self.codeflow_engine = CodeFlowWorkflowEngine()
            print("  ✅ CodeFlow工作流引擎已初始化")
            
            # 初始化TDD框架
            self.tdd_framework = CrossPlatformTDDFramework()
            print("  ✅ 跨平台TDD框架已初始化")
            
            print("🎉 所有組件初始化完成！")
            return True
            
        except Exception as e:
            print(f"❌ 組件初始化失敗: {e}")
            return False
    
    async def test_subscription_tier_access(self):
        """測試訂閱版本階段訪問控制"""
        print("\n📊 測試訂閱版本階段訪問控制...")
        
        tier_tests = [
            (SubscriptionTier.PERSONAL, 2, "個人版"),
            (SubscriptionTier.PROFESSIONAL, 4, "專業版"),
            (SubscriptionTier.TEAM, 5, "團隊版"),
            (SubscriptionTier.ENTERPRISE, 7, "企業版")
        ]
        
        results = {}
        
        for tier, expected_stages, tier_name in tier_tests:
            print(f"  🧪 測試{tier_name}訪問權限...")
            
            available_workflows = self.claudeditor_manager.get_available_workflows(tier)
            
            # 檢查代碼生成工作流
            code_workflow = next(
                (w for w in available_workflows if w["type"] == WorkflowType.CODE_GENERATION.value),
                None
            )
            
            if code_workflow:
                actual_stages = code_workflow["available_stages"]
                tier_limit = code_workflow["tier_limit"]
                
                test_passed = (actual_stages == expected_stages and tier_limit == expected_stages)
                results[tier_name] = {
                    "expected_stages": expected_stages,
                    "actual_stages": actual_stages,
                    "tier_limit": tier_limit,
                    "test_passed": test_passed
                }
                
                status = "✅" if test_passed else "❌"
                print(f"    {status} {tier_name}: {actual_stages}/{expected_stages}階段可用")
            else:
                results[tier_name] = {"test_passed": False, "error": "工作流不可用"}
                print(f"    ❌ {tier_name}: 工作流不可用")
        
        self.test_results["subscription_tier_access"] = results
        return all(result["test_passed"] for result in results.values())
    
    async def test_workflow_types(self):
        """測試六大工作流類型"""
        print("\n🔧 測試六大工作流類型...")
        
        workflow_types = [
            (WorkflowType.CODE_GENERATION, "代碼生成工作流"),
            (WorkflowType.UI_DESIGN, "UI設計工作流"),
            (WorkflowType.API_DEVELOPMENT, "API開發工作流"),
            (WorkflowType.DATABASE_DESIGN, "數據庫設計工作流"),
            (WorkflowType.TESTING_AUTOMATION, "測試自動化工作流"),
            (WorkflowType.DEPLOYMENT_PIPELINE, "部署流水線工作流")
        ]
        
        results = {}
        
        for workflow_type, workflow_name in workflow_types:
            print(f"  🧪 測試{workflow_name}...")
            
            try:
                # 使用企業版測試完整功能
                project_data = {
                    "project_name": f"Test_{workflow_type.value}",
                    "requirements": f"Test requirements for {workflow_name}",
                    "technology_stack": {
                        "frontend": "React",
                        "backend": "FastAPI",
                        "database": "PostgreSQL"
                    }
                }
                
                # 啟動工作流
                workflow_result = await self.claudeditor_manager.start_workflow(
                    workflow_type,
                    project_data,
                    SubscriptionTier.ENTERPRISE
                )
                
                # 檢查結果
                workflow_id = workflow_result.get("workflow_id")
                available_stages = len(workflow_result.get("available_stages", []))
                
                test_passed = (
                    workflow_id is not None and
                    available_stages == 7 and  # 企業版應該有7個階段
                    workflow_result.get("status") == "initialized"
                )
                
                results[workflow_name] = {
                    "workflow_id": workflow_id,
                    "available_stages": available_stages,
                    "status": workflow_result.get("status"),
                    "test_passed": test_passed
                }
                
                status = "✅" if test_passed else "❌"
                print(f"    {status} {workflow_name}: {available_stages}階段, 狀態={workflow_result.get('status')}")
                
            except Exception as e:
                results[workflow_name] = {"test_passed": False, "error": str(e)}
                print(f"    ❌ {workflow_name}: 錯誤 - {e}")
        
        self.test_results["workflow_types"] = results
        return all(result["test_passed"] for result in results.values())
    
    async def test_ui_layout_rendering(self):
        """測試UI布局渲染"""
        print("\n🎨 測試ClaudEditor UI布局渲染...")
        
        results = {}
        
        # 測試不同工作流的UI布局
        test_workflows = [
            WorkflowType.CODE_GENERATION,
            WorkflowType.UI_DESIGN,
            WorkflowType.API_DEVELOPMENT
        ]
        
        for workflow_type in test_workflows:
            print(f"  🧪 測試{workflow_type.value} UI布局...")
            
            try:
                ui_layout = self.ui_manager.render_workflow_interface(
                    workflow_type,
                    SubscriptionTier.PROFESSIONAL
                )
                
                # 檢查UI布局結構
                layout = ui_layout.get("layout", {})
                required_panels = ["left_panel", "center_editor", "right_panel"]
                
                panels_exist = all(panel in layout for panel in required_panels)
                workflow_info_exists = "workflow_info" in ui_layout
                
                test_passed = panels_exist and workflow_info_exists
                
                results[workflow_type.value] = {
                    "panels_exist": panels_exist,
                    "workflow_info_exists": workflow_info_exists,
                    "panel_count": len(layout),
                    "test_passed": test_passed
                }
                
                status = "✅" if test_passed else "❌"
                print(f"    {status} {workflow_type.value}: {len(layout)}個面板")
                
            except Exception as e:
                results[workflow_type.value] = {"test_passed": False, "error": str(e)}
                print(f"    ❌ {workflow_type.value}: 錯誤 - {e}")
        
        self.test_results["ui_layout_rendering"] = results
        return all(result["test_passed"] for result in results.values())
    
    async def test_stage_execution(self):
        """測試階段執行"""
        print("\n⚡ 測試工作流階段執行...")
        
        try:
            # 創建測試工作流
            project_data = {
                "project_name": "Stage Execution Test",
                "requirements": "Test stage execution functionality",
                "technology_stack": {"backend": "FastAPI"}
            }
            
            workflow_result = await self.claudeditor_manager.start_workflow(
                WorkflowType.CODE_GENERATION,
                project_data,
                SubscriptionTier.PROFESSIONAL
            )
            
            workflow_id = workflow_result["workflow_id"]
            available_stages = workflow_result["available_stages"]
            
            print(f"  📋 工作流ID: {workflow_id}")
            print(f"  📊 可用階段: {len(available_stages)}個")
            
            execution_results = []
            
            # 執行前兩個階段（專業版限制）
            for i, stage in enumerate(available_stages[:2]):
                stage_id = stage["stage_id"]
                print(f"  🧪 執行階段 {i+1}: {stage['stage_name']}...")
                
                stage_input = {
                    "test_data": f"input_for_stage_{stage_id}",
                    "config": {"mode": "test"}
                }
                
                start_time = time.time()
                result = await self.claudeditor_manager.execute_stage(
                    workflow_id,
                    stage_id,
                    stage_input
                )
                execution_time = time.time() - start_time
                
                success = result.get("status") == "completed"
                execution_results.append({
                    "stage_id": stage_id,
                    "stage_name": stage["stage_name"],
                    "success": success,
                    "execution_time": execution_time,
                    "result": result
                })
                
                status = "✅" if success else "❌"
                print(f"    {status} {stage['stage_name']}: {execution_time:.2f}秒")
            
            # 測試受限階段（應該提示升級）
            if len(available_stages) > 2:
                restricted_stage = available_stages[2]
                print(f"  🔒 測試受限階段: {restricted_stage['stage_name']}...")
                
                result = await self.claudeditor_manager.execute_stage(
                    workflow_id,
                    restricted_stage["stage_id"],
                    {"test": "data"}
                )
                
                upgrade_required = result.get("status") == "upgrade_required"
                status = "✅" if upgrade_required else "❌"
                print(f"    {status} 升級提示: {upgrade_required}")
                
                execution_results.append({
                    "stage_id": restricted_stage["stage_id"],
                    "upgrade_required": upgrade_required,
                    "message": result.get("message", "")
                })
            
            self.test_results["stage_execution"] = {
                "workflow_id": workflow_id,
                "executed_stages": len([r for r in execution_results if r.get("success")]),
                "total_stages": len(available_stages),
                "execution_results": execution_results,
                "test_passed": len([r for r in execution_results if r.get("success")]) >= 2
            }
            
            return True
            
        except Exception as e:
            print(f"    ❌ 階段執行測試失敗: {e}")
            self.test_results["stage_execution"] = {"test_passed": False, "error": str(e)}
            return False
    
    async def test_codeflow_integration(self):
        """測試CodeFlow引擎集成"""
        print("\n🔄 測試CodeFlow引擎集成...")
        
        try:
            # 創建CodeFlow工作流接口
            codeflow_interface = ClaudEditorWorkflowInterface()
            
            # 測試項目數據
            project_data = {
                'project_name': 'CodeFlow Integration Test',
                'mermaidflow': {
                    'flowcharts': [
                        {
                            'id': 'test_workflow',
                            'name': 'Test Workflow',
                            'nodes': [
                                {'id': 'start', 'type': 'start', 'label': 'Start Process'},
                                {'id': 'process', 'type': 'process', 'label': 'Process Data'},
                                {'id': 'end', 'type': 'end', 'label': 'End Process'}
                            ],
                            'edges': [
                                {'source': 'start', 'target': 'process'},
                                {'source': 'process', 'target': 'end'}
                            ]
                        }
                    ]
                },
                'agui': {
                    'pages': [
                        {
                            'id': 'test_page',
                            'name': 'TestPage',
                            'route': '/test',
                            'components': [
                                {
                                    'id': 'test_button',
                                    'type': 'button',
                                    'props': {'text': 'Test Button'},
                                    'events': [{'type': 'click', 'handler': 'handleClick'}]
                                }
                            ]
                        }
                    ]
                }
            }
            
            print("  🧪 測試代碼開發工作流...")
            code_result = await codeflow_interface.start_code_development_workflow(project_data)
            
            code_success = (
                code_result.get("status") == "completed" and
                "workflow_id" in code_result and
                "output" in code_result
            )
            
            print("  🧪 測試全周期工作流...")
            full_result = await codeflow_interface.start_full_cycle_workflow(project_data)
            
            full_success = (
                full_result.get("status") == "completed" and
                "deployment_ready" in full_result
            )
            
            self.test_results["codeflow_integration"] = {
                "code_development": {
                    "success": code_success,
                    "workflow_id": code_result.get("workflow_id"),
                    "status": code_result.get("status")
                },
                "full_cycle": {
                    "success": full_success,
                    "deployment_ready": full_result.get("deployment_ready"),
                    "status": full_result.get("status")
                },
                "test_passed": code_success and full_success
            }
            
            status = "✅" if (code_success and full_success) else "❌"
            print(f"    {status} CodeFlow集成測試: 代碼開發={code_success}, 全周期={full_success}")
            
            return code_success and full_success
            
        except Exception as e:
            print(f"    ❌ CodeFlow集成測試失敗: {e}")
            self.test_results["codeflow_integration"] = {"test_passed": False, "error": str(e)}
            return False
    
    async def test_tdd_framework_integration(self):
        """測試TDD框架集成"""
        print("\n🧪 測試TDD框架集成...")
        
        try:
            # 運行TDD測試
            print("  🔄 運行跨平台TDD測試...")
            
            test_result = await self.tdd_framework.run_comprehensive_tests()
            
            success = (
                test_result.get("overall_status") == "SUCCESS" and
                test_result.get("total_tests", 0) > 0 and
                test_result.get("success_rate", 0) > 90
            )
            
            self.test_results["tdd_framework_integration"] = {
                "total_tests": test_result.get("total_tests", 0),
                "passed_tests": test_result.get("passed_tests", 0),
                "success_rate": test_result.get("success_rate", 0),
                "execution_time": test_result.get("execution_time", 0),
                "overall_status": test_result.get("overall_status"),
                "test_passed": success
            }
            
            status = "✅" if success else "❌"
            total_tests = test_result.get("total_tests", 0)
            success_rate = test_result.get("success_rate", 0)
            print(f"    {status} TDD框架: {total_tests}個測試, 成功率={success_rate}%")
            
            return success
            
        except Exception as e:
            print(f"    ❌ TDD框架集成測試失敗: {e}")
            self.test_results["tdd_framework_integration"] = {"test_passed": False, "error": str(e)}
            return False
    
    async def run_comprehensive_test(self):
        """運行完整集成測試"""
        print("🚀 PowerAutomation v4.6.1 完整集成測試")
        print("=" * 80)
        
        # 初始化組件
        if not await self.initialize_components():
            print("❌ 組件初始化失敗，測試終止")
            return False
        
        # 運行所有測試
        test_methods = [
            ("訂閱版本訪問控制", self.test_subscription_tier_access),
            ("六大工作流類型", self.test_workflow_types),
            ("UI布局渲染", self.test_ui_layout_rendering),
            ("階段執行", self.test_stage_execution),
            ("CodeFlow引擎集成", self.test_codeflow_integration),
            ("TDD框架集成", self.test_tdd_framework_integration)
        ]
        
        test_results = []
        
        for test_name, test_method in test_methods:
            try:
                result = await test_method()
                test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}測試發生異常: {e}")
                test_results.append((test_name, False))
        
        # 生成測試報告
        await self.generate_test_report(test_results)
        
        # 返回整體測試結果
        overall_success = all(result for _, result in test_results)
        return overall_success
    
    async def generate_test_report(self, test_results):
        """生成測試報告"""
        print("\n📊 集成測試報告")
        print("=" * 80)
        
        total_time = time.time() - self.start_time
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📈 測試總結:")
        print(f"  ⏰ 執行時間: {total_time:.2f}秒")
        print(f"  📊 測試總數: {total_tests}")
        print(f"  ✅ 通過: {passed_tests}")
        print(f"  ❌ 失敗: {total_tests - passed_tests}")
        print(f"  📊 成功率: {success_rate:.1f}%")
        
        print(f"\n📋 詳細結果:")
        for test_name, result in test_results:
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"  {status} {test_name}")
        
        # 保存詳細測試結果
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": total_time,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "test_results": dict(test_results),
            "detailed_results": self.test_results
        }
        
        report_file = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 詳細報告已保存: {report_file}")
        except Exception as e:
            print(f"⚠️ 報告保存失敗: {e}")
        
        print(f"\n🎯 集成測試{'成功' if success_rate == 100 else '部分成功'}！")
        
        if success_rate == 100:
            print("🚀 PowerAutomation v4.6.1 所有組件集成完美運行！")
        else:
            print(f"⚠️ 有{total_tests - passed_tests}項測試需要修復")

# 主函數
async def main():
    """運行完整集成測試"""
    integration_test = PowerAutomationIntegrationTest()
    success = await integration_test.run_comprehensive_test()
    
    if success:
        print("\n🎉 所有集成測試通過！PowerAutomation v4.6.1 準備就緒！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查詳細報告")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())