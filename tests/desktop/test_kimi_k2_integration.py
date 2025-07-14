#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 集成測試套件
包含後端API測試、UI功能測試、整合測試
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
import unittest
from unittest.mock import Mock, patch
import sys
import os

# 設置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """測試結果"""
    test_name: str
    success: bool
    message: str
    execution_time: float
    details: Dict[str, Any] = None

class KimiK2IntegrationTester:
    """Kimi K2整合測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[TestResult] = []
        self.session = None
        
    async def setup(self):
        """設置測試環境"""
        self.session = aiohttp.ClientSession()
        logger.info("測試環境設置完成")
    
    async def teardown(self):
        """清理測試環境"""
        if self.session:
            await self.session.close()
        logger.info("測試環境清理完成")
    
    async def run_test(self, test_func, test_name: str):
        """運行單個測試"""
        start_time = time.time()
        try:
            result = await test_func()
            execution_time = time.time() - start_time
            
            if result:
                test_result = TestResult(
                    test_name=test_name,
                    success=True,
                    message="測試通過",
                    execution_time=execution_time,
                    details=result if isinstance(result, dict) else None
                )
            else:
                test_result = TestResult(
                    test_name=test_name,
                    success=False,
                    message="測試失敗：返回值為假",
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            test_result = TestResult(
                test_name=test_name,
                success=False,
                message=f"測試異常：{str(e)}",
                execution_time=execution_time
            )
        
        self.test_results.append(test_result)
        status = "✅ 通過" if test_result.success else "❌ 失敗"
        logger.info(f"{status} {test_name} ({test_result.execution_time:.2f}s)")
        return test_result
    
    # ===== 後端API測試 =====
    
    async def test_server_health(self):
        """測試服務器健康狀態"""
        try:
            async with self.session.get(f"{self.base_url}/api/status") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "running"
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return False
    
    async def test_kimi_k2_model_status(self):
        """測試Kimi K2模型狀態"""
        try:
            async with self.session.get(f"{self.base_url}/api/ai/models/kimi_k2/status") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": data.get("status"),
                        "model": data.get("model"),
                        "provider": data.get("provider")
                    }
        except Exception as e:
            logger.error(f"Kimi K2狀態檢查失敗: {e}")
            return False
    
    async def test_available_models_api(self):
        """測試可用模型API"""
        try:
            async with self.session.get(f"{self.base_url}/api/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    
                    # 檢查是否包含Kimi K2
                    kimi_model = next((m for m in models if m["id"] == "kimi_k2"), None)
                    if kimi_model:
                        return {
                            "total_models": len(models),
                            "kimi_k2_available": True,
                            "kimi_k2_status": kimi_model.get("status")
                        }
        except Exception as e:
            logger.error(f"模型列表API測試失敗: {e}")
            return False
    
    async def test_claude_chat_api(self):
        """測試Claude聊天API"""
        try:
            payload = {
                "message": "Hello, please respond with 'Claude test successful'",
                "model": "claude",
                "max_tokens": 50
            }
            
            async with self.session.post(
                f"{self.base_url}/api/ai/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "response": data.get("response"),
                        "model": data.get("model"),
                        "timestamp": data.get("timestamp")
                    }
        except Exception as e:
            logger.error(f"Claude聊天API測試失敗: {e}")
            return False
    
    async def test_kimi_k2_chat_api(self):
        """測試Kimi K2聊天API"""
        try:
            payload = {
                "message": "你好，請回答'Kimi K2測試成功'",
                "model": "kimi_k2",
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            async with self.session.post(
                f"{self.base_url}/api/ai/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "response": data.get("response"),
                        "model": data.get("model"),
                        "timestamp": data.get("timestamp")
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Kimi K2 API錯誤 {response.status}: {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Kimi K2聊天API測試失敗: {e}")
            return False
    
    async def test_model_comparison(self):
        """測試模型對比功能"""
        try:
            # 先測試Claude
            claude_result = await self.test_claude_chat_api()
            
            # 再測試Kimi K2
            kimi_result = await self.test_kimi_k2_chat_api()
            
            if claude_result and kimi_result:
                return {
                    "claude_response": claude_result.get("response"),
                    "kimi_response": kimi_result.get("response"),
                    "both_working": True
                }
            else:
                return {
                    "claude_working": bool(claude_result),
                    "kimi_working": bool(kimi_result),
                    "both_working": False
                }
                
        except Exception as e:
            logger.error(f"模型對比測試失敗: {e}")
            return False
    
    async def test_parameter_handling(self):
        """測試參數處理"""
        try:
            payload = {
                "message": "測試參數處理",
                "model": "kimi_k2",
                "max_tokens": 100,
                "temperature": 0.9,
                "top_p": 0.8
            }
            
            async with self.session.post(
                f"{self.base_url}/api/ai/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "parameters_accepted": True,
                        "response_length": len(data.get("response", "")),
                        "model": data.get("model")
                    }
        except Exception as e:
            logger.error(f"參數處理測試失敗: {e}")
            return False
    
    # ===== UI功能測試 =====
    
    async def test_ui_accessibility(self):
        """測試UI可訪問性"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # 檢查關鍵UI元素
                    ui_elements = [
                        "ai-model-select",
                        "global-model-select", 
                        "model-status",
                        "chat-input",
                        "send-message",
                        "model-comparison-panel"
                    ]
                    
                    found_elements = {}
                    for element in ui_elements:
                        found_elements[element] = element in html_content
                    
                    return {
                        "page_loaded": True,
                        "ui_elements": found_elements,
                        "all_elements_present": all(found_elements.values())
                    }
        except Exception as e:
            logger.error(f"UI可訪問性測試失敗: {e}")
            return False
    
    async def test_static_assets(self):
        """測試靜態資源"""
        assets = [
            "/static/css/main.css",
            "/static/js/main.js", 
            "/static/js/kimi-k2-integration.js",
            "/static/css/kimi-k2-styles.css"
        ]
        
        asset_results = {}
        
        for asset in assets:
            try:
                async with self.session.get(f"{self.base_url}{asset}") as response:
                    asset_results[asset] = response.status == 200
            except Exception as e:
                asset_results[asset] = False
                logger.error(f"資源載入失敗 {asset}: {e}")
        
        return {
            "assets": asset_results,
            "all_loaded": all(asset_results.values())
        }
    
    # ===== 整合測試 =====
    
    async def test_end_to_end_workflow(self):
        """端到端工作流測試"""
        try:
            # 1. 檢查模型列表
            models_result = await self.test_available_models_api()
            if not models_result:
                return False
            
            # 2. 測試Claude
            claude_result = await self.test_claude_chat_api()
            if not claude_result:
                return False
                
            # 3. 測試Kimi K2
            kimi_result = await self.test_kimi_k2_chat_api()
            if not kimi_result:
                return False
            
            # 4. 測試UI可訪問性
            ui_result = await self.test_ui_accessibility()
            if not ui_result:
                return False
            
            return {
                "workflow_steps": {
                    "models_api": bool(models_result),
                    "claude_chat": bool(claude_result),
                    "kimi_chat": bool(kimi_result),
                    "ui_access": bool(ui_result)
                },
                "full_workflow_success": True
            }
            
        except Exception as e:
            logger.error(f"端到端測試失敗: {e}")
            return False
    
    async def test_error_handling(self):
        """測試錯誤處理"""
        try:
            # 測試無效模型
            payload = {
                "message": "test",
                "model": "invalid_model"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/ai/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                # 應該返回錯誤
                if response.status != 200:
                    return {
                        "invalid_model_handled": True,
                        "error_code": response.status
                    }
        except Exception as e:
            logger.error(f"錯誤處理測試失敗: {e}")
            return False
    
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始運行ClaudEditor + Kimi K2整合測試")
        
        await self.setup()
        
        # 測試列表
        tests = [
            (self.test_server_health, "服務器健康檢查"),
            (self.test_available_models_api, "可用模型API"),
            (self.test_kimi_k2_model_status, "Kimi K2模型狀態"),
            (self.test_claude_chat_api, "Claude聊天API"),
            (self.test_kimi_k2_chat_api, "Kimi K2聊天API"),
            (self.test_model_comparison, "模型對比功能"),
            (self.test_parameter_handling, "參數處理"),
            (self.test_ui_accessibility, "UI可訪問性"),
            (self.test_static_assets, "靜態資源載入"),
            (self.test_end_to_end_workflow, "端到端工作流"),
            (self.test_error_handling, "錯誤處理")
        ]
        
        # 執行測試
        for test_func, test_name in tests:
            await self.run_test(test_func, test_name)
        
        await self.teardown()
        
        # 生成測試報告
        self.generate_report()
        
        return self.test_results
    
    def generate_report(self):
        """生成測試報告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.success)
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 ClaudEditor + Kimi K2 整合測試報告")
        print("="*60)
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests} ✅")
        print(f"失敗: {failed_tests} ❌")
        print(f"成功率: {success_rate:.1f}%")
        print("="*60)
        
        print("\n📋 詳細結果:")
        for result in self.test_results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.test_name} ({result.execution_time:.2f}s)")
            if not result.success:
                print(f"   錯誤: {result.message}")
            elif result.details:
                print(f"   詳情: {json.dumps(result.details, ensure_ascii=False, indent=2)}")
        
        print("\n" + "="*60)
        
        if success_rate >= 80:
            print("🎉 測試整體通過！Kimi K2整合成功！")
        elif success_rate >= 60:
            print("⚠️  測試部分通過，需要修復一些問題")
        else:
            print("❌ 測試未通過，需要重大修復")


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClaudEditor + Kimi K2 整合測試")
    parser.add_argument("--url", default="http://localhost:8000", help="服務器URL")
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = KimiK2IntegrationTester(base_url=args.url)
    results = await tester.run_all_tests()
    
    # 返回適當的退出碼
    failed_count = sum(1 for r in results if not r.success)
    exit_code = 0 if failed_count == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())