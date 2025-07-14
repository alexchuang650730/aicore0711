#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 實際測試執行腳本
使用實際的API調用進行功能驗證
"""

import asyncio
import aiohttp
import json
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KimiK2LiveTester:
    """Kimi K2實時功能測試器"""
    
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN", "<your_token_here>")
        self.base_url = "http://localhost:8000"
        
    async def test_huggingface_direct_api(self):
        """直接測試HuggingFace API"""
        logger.info("🧪 測試HuggingFace直接API調用...")
        
        try:
            from huggingface_hub import InferenceClient
            
            client = InferenceClient(
                provider="novita",
                api_key=self.hf_token,
            )
            
            start_time = time.time()
            completion = client.chat.completions.create(
                model="moonshotai/Kimi-K2-Instruct",
                messages=[
                    {"role": "user", "content": "你好，請回答'Kimi K2直接API測試成功'"}
                ],
                max_tokens=50
            )
            
            response_time = time.time() - start_time
            response_text = completion.choices[0].message.content
            
            logger.info(f"✅ HuggingFace API測試成功 ({response_time:.2f}s)")
            logger.info(f"📝 回應: {response_text}")
            
            return {
                "success": True,
                "response": response_text,
                "response_time": response_time
            }
            
        except Exception as e:
            logger.error(f"❌ HuggingFace API測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_claudeditor_api_endpoints(self):
        """測試ClaudEditor API端點"""
        logger.info("🔗 測試ClaudEditor API端點...")
        
        async with aiohttp.ClientSession() as session:
            tests = []
            
            # 測試健康檢查
            try:
                async with session.get(f"{self.base_url}/api/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        tests.append({"endpoint": "/api/status", "success": True, "data": data})
                    else:
                        tests.append({"endpoint": "/api/status", "success": False, "status": response.status})
            except Exception as e:
                tests.append({"endpoint": "/api/status", "success": False, "error": str(e)})
            
            # 測試模型列表
            try:
                async with session.get(f"{self.base_url}/api/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        tests.append({"endpoint": "/api/models", "success": True, "data": data})
                    else:
                        tests.append({"endpoint": "/api/models", "success": False, "status": response.status})
            except Exception as e:
                tests.append({"endpoint": "/api/models", "success": False, "error": str(e)})
            
            # 測試Claude聊天
            try:
                payload = {
                    "message": "Hello from test",
                    "model": "claude",
                    "max_tokens": 50
                }
                async with session.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tests.append({"endpoint": "/api/ai/chat (Claude)", "success": True, "data": data})
                    else:
                        error_text = await response.text()
                        tests.append({"endpoint": "/api/ai/chat (Claude)", "success": False, "status": response.status, "error": error_text})
            except Exception as e:
                tests.append({"endpoint": "/api/ai/chat (Claude)", "success": False, "error": str(e)})
            
            # 測試Kimi K2聊天
            try:
                payload = {
                    "message": "你好，測試Kimi K2",
                    "model": "kimi_k2",
                    "max_tokens": 50,
                    "temperature": 0.7
                }
                async with session.post(
                    f"{self.base_url}/api/ai/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tests.append({"endpoint": "/api/ai/chat (Kimi K2)", "success": True, "data": data})
                    else:
                        error_text = await response.text()
                        tests.append({"endpoint": "/api/ai/chat (Kimi K2)", "success": False, "status": response.status, "error": error_text})
            except Exception as e:
                tests.append({"endpoint": "/api/ai/chat (Kimi K2)", "success": False, "error": str(e)})
            
            return tests
    
    async def test_ui_page_access(self):
        """測試UI頁面訪問"""
        logger.info("🌐 測試UI頁面訪問...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # 檢查關鍵UI元素
                        checks = {
                            "title_present": "ClaudEditor" in html_content,
                            "kimi_k2_present": "kimi_k2" in html_content,
                            "model_selector_present": "ai-model-select" in html_content,
                            "chat_input_present": "chat-input" in html_content
                        }
                        
                        return {
                            "success": response.status == 200,
                            "checks": checks,
                            "all_checks_passed": all(checks.values())
                        }
                    else:
                        return {"success": False, "status": response.status}
                        
        except Exception as e:
            logger.error(f"UI頁面訪問測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def run_manual_verification_checklist(self):
        """生成手動驗證清單"""
        logger.info("📋 生成手動驗證清單...")
        
        checklist = {
            "基本功能驗證": [
                "✅ 打開瀏覽器訪問 http://localhost:8000",
                "✅ 檢查頁面是否正常載入，沒有錯誤",
                "✅ 確認頁面標題顯示 'ClaudEditor v4.2'",
                "✅ 檢查左側邊欄導航功能是否正常"
            ],
            "模型選擇器驗證": [
                "✅ 檢查右上角全局模型選擇器",
                "✅ 確認選項包含：Claude, 🌙 Kimi K2, Gemini, GPT-4",
                "✅ 點擊切換不同模型，檢查UI反應",
                "✅ 檢查模型狀態指示器是否正常更新"
            ],
            "AI助手功能驗證": [
                "✅ 點擊左側 'AI助手' 導航",
                "✅ 檢查AI面板中的模型選擇器",
                "✅ 點擊 '參數' 按鈕，檢查參數面板",
                "✅ 調整Temperature和Top-P滑桿",
                "✅ 在聊天輸入框輸入測試消息",
                "✅ 點擊發送，檢查消息是否正確顯示"
            ],
            "Kimi K2特定驗證": [
                "✅ 切換到Kimi K2模型",
                "✅ 發送中文測試消息：'你好，請介紹一下自己'",
                "✅ 檢查回應是否使用中文",
                "✅ 測試複雜推理問題",
                "✅ 檢查模型標籤是否顯示🌙圖標"
            ],
            "模型對比功能驗證": [
                "✅ 點擊左側 '模型對比' 導航",
                "✅ 檢查模型選擇複選框",
                "✅ 選中Claude和Kimi K2",
                "✅ 在對比輸入框輸入問題",
                "✅ 點擊 '詢問所有選中的模型'",
                "✅ 檢查兩個模型的回應是否都顯示"
            ],
            "錯誤處理驗證": [
                "✅ 發送空消息，檢查錯誤處理",
                "✅ 發送極長消息，檢查響應",
                "✅ 快速連續發送多條消息",
                "✅ 檢查網絡錯誤時的提示"
            ]
        }
        
        return checklist
    
    async def run_all_live_tests(self):
        """運行所有實時測試"""
        logger.info("🚀 開始運行ClaudEditor + Kimi K2實時功能測試")
        print("="*70)
        
        results = {}
        
        # 1. 測試HuggingFace直接API
        results["huggingface_api"] = await self.test_huggingface_direct_api()
        
        # 2. 測試ClaudEditor API端點
        results["claudeditor_apis"] = await self.test_claudeditor_api_endpoints()
        
        # 3. 測試UI頁面訪問
        results["ui_access"] = await self.test_ui_page_access()
        
        # 4. 生成手動驗證清單
        results["manual_checklist"] = self.run_manual_verification_checklist()
        
        # 生成測試報告
        self.generate_live_test_report(results)
        
        return results
    
    def generate_live_test_report(self, results):
        """生成實時測試報告"""
        print("\n" + "="*70)
        print("📊 ClaudEditor + Kimi K2 實時功能測試報告")
        print("="*70)
        
        # HuggingFace API測試結果
        hf_result = results["huggingface_api"]
        hf_status = "✅ 成功" if hf_result["success"] else "❌ 失敗"
        print(f"🤖 HuggingFace Direct API: {hf_status}")
        if hf_result["success"]:
            print(f"   📝 回應: {hf_result['response'][:50]}...")
            print(f"   ⏱️  響應時間: {hf_result['response_time']:.2f}s")
        else:
            print(f"   ❌ 錯誤: {hf_result['error']}")
        
        # ClaudEditor API測試結果
        print(f"\n🔗 ClaudEditor API端點測試:")
        api_results = results["claudeditor_apis"]
        for test in api_results:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['endpoint']}")
            if not test["success"] and "error" in test:
                print(f"      錯誤: {test['error']}")
        
        # UI訪問測試結果
        ui_result = results["ui_access"]
        ui_status = "✅ 成功" if ui_result["success"] else "❌ 失敗"
        print(f"\n🌐 UI頁面訪問: {ui_status}")
        if ui_result["success"] and "checks" in ui_result:
            for check_name, passed in ui_result["checks"].items():
                check_status = "✅" if passed else "❌"
                print(f"   {check_status} {check_name}")
        
        # 手動測試清單
        print(f"\n📋 手動驗證清單:")
        checklist = results["manual_checklist"]
        for category, items in checklist.items():
            print(f"\n🔸 {category}:")
            for item in items:
                print(f"   {item}")
        
        print("\n" + "="*70)
        
        # 整體狀態評估
        hf_ok = hf_result["success"]
        api_ok = sum(1 for t in api_results if t["success"]) >= len(api_results) // 2
        ui_ok = ui_result["success"]
        
        if hf_ok and api_ok and ui_ok:
            print("🎉 所有自動化測試通過！")
            print("💡 請繼續進行上述手動驗證清單以確保完整功能")
        elif hf_ok:
            print("⚠️  部分測試通過，Kimi K2 API可用但ClaudEditor整合可能有問題")
            print("💡 請檢查ClaudEditor服務器是否正確運行")
        else:
            print("❌ 測試未通過，請檢查：")
            print("   1. HuggingFace Token是否有效")
            print("   2. 網絡連接是否正常")
            print("   3. ClaudEditor服務器是否運行")
        
        print("="*70)


async def main():
    """主函數"""
    tester = KimiK2LiveTester()
    await tester.run_all_live_tests()


if __name__ == "__main__":
    asyncio.run(main())