#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 簡化功能測試
使用標準庫進行基本驗證，無需額外依賴
"""

import os
import time
import logging
import urllib.request
import urllib.parse
import urllib.error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleKimiK2Tester:
    """簡化的Kimi K2功能測試器"""
    
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN", "<your_token_here>")
        self.base_url = "http://localhost:8000"
        
    def test_huggingface_direct_api(self):
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
            
        except ImportError:
            logger.warning("⚠️  huggingface_hub未安裝，跳過直接API測試")
            return {"success": False, "error": "huggingface_hub not installed", "skipped": True}
        except Exception as e:
            logger.error(f"❌ HuggingFace API測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def test_claudeditor_server_status(self):
        """測試ClaudEditor服務器狀態"""
        logger.info("🔗 測試ClaudEditor服務器狀態...")
        
        try:
            # 測試健康檢查端點
            request = urllib.request.Request(f"{self.base_url}/api/status")
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    logger.info("✅ ClaudEditor服務器運行正常")
                    return {"success": True, "status": data}
                else:
                    logger.error(f"❌ 服務器返回狀態碼: {response.status}")
                    return {"success": False, "status_code": response.status}
                    
        except urllib.error.URLError as e:
            logger.error(f"❌ 無法連接到ClaudEditor服務器: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ 服務器狀態檢查失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def test_ui_page_access(self):
        """測試UI頁面訪問"""
        logger.info("🌐 測試UI頁面訪問...")
        
        try:
            request = urllib.request.Request(self.base_url)
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    html_content = response.read().decode()
                    
                    # 檢查關鍵UI元素
                    checks = {
                        "title_present": "ClaudEditor" in html_content,
                        "kimi_k2_present": "kimi_k2" in html_content,
                        "model_selector_present": "ai-model-select" in html_content,
                        "chat_input_present": "chat-input" in html_content,
                        "moon_emoji_present": "🌙" in html_content
                    }
                    
                    logger.info("✅ UI頁面訪問成功")
                    for check_name, passed in checks.items():
                        status = "✅" if passed else "❌"
                        logger.info(f"   {status} {check_name}")
                    
                    return {
                        "success": True,
                        "checks": checks,
                        "all_checks_passed": all(checks.values())
                    }
                else:
                    logger.error(f"❌ UI頁面返回狀態碼: {response.status}")
                    return {"success": False, "status_code": response.status}
                    
        except urllib.error.URLError as e:
            logger.error(f"❌ 無法訪問UI頁面: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ UI頁面訪問失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def test_kimi_k2_chat_api(self):
        """測試Kimi K2聊天API"""
        logger.info("💬 測試Kimi K2聊天API...")
        
        try:
            # 準備請求數據
            data = {
                "message": "你好，請回答'ClaudEditor中的Kimi K2測試成功'",
                "model": "kimi_k2",
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            # 發送POST請求
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(
                f"{self.base_url}/api/ai/chat",
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'Content-Length': str(len(json_data))
                }
            )
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=30) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = json.loads(response.read().decode())
                    logger.info(f"✅ Kimi K2聊天API測試成功 ({response_time:.2f}s)")
                    logger.info(f"📝 回應: {result.get('response', 'No response')}")
                    
                    return {
                        "success": True,
                        "response": result.get('response'),
                        "model": result.get('model'),
                        "response_time": response_time
                    }
                else:
                    error_text = response.read().decode()
                    logger.error(f"❌ Kimi K2 API返回錯誤 {response.status}: {error_text}")
                    return {"success": False, "status_code": response.status, "error": error_text}
                    
        except urllib.error.URLError as e:
            logger.error(f"❌ Kimi K2 API連接失敗: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Kimi K2 API測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_deployment_instructions(self):
        """生成部署指令"""
        return {
            "prerequisites": [
                "✅ Python 3.8+ 已安裝",
                "✅ pip 包管理器可用",
                "✅ 網絡連接正常",
                "✅ HuggingFace Token有效"
            ],
            "installation_steps": [
                "1️⃣ 安裝依賴套件:",
                "   pip install fastapi uvicorn huggingface_hub requests",
                "",
                "2️⃣ 設置環境變量:",
                "   export HF_TOKEN='<your_token_here>'",
                "",
                "3️⃣ 部署ClaudEditor整合:",
                "   chmod +x deploy_and_test.sh",
                "   ./deploy_and_test.sh",
                "",
                "4️⃣ 啟動服務:",
                "   cd aicore0711/claudeditor",
                "   ./start_with_kimi_k2.sh",
                "",
                "5️⃣ 訪問界面:",
                "   打開瀏覽器訪問 http://localhost:8000"
            ],
            "testing_steps": [
                "1️⃣ 運行自動化測試:",
                "   python test_live_functionality.py",
                "",
                "2️⃣ 運行完整測試套件:",
                "   python run_complete_tests.py",
                "",
                "3️⃣ 運行Playwright UI測試:",
                "   pip install playwright",
                "   playwright install chromium",
                "   python test_playwright_ui.py"
            ]
        }
    
    def run_all_simple_tests(self):
        """運行所有簡化測試"""
        logger.info("🚀 開始運行ClaudEditor + Kimi K2簡化功能測試")
        print("="*70)
        
        results = {}
        
        # 1. 測試HuggingFace直接API
        results["huggingface_api"] = self.test_huggingface_direct_api()
        
        # 2. 測試ClaudEditor服務器狀態
        results["server_status"] = self.test_claudeditor_server_status()
        
        # 3. 測試UI頁面訪問
        results["ui_access"] = self.test_ui_page_access()
        
        # 4. 測試Kimi K2聊天API（如果服務器可用）
        if results["server_status"]["success"]:
            results["kimi_k2_chat"] = self.test_kimi_k2_chat_api()
        else:
            logger.warning("⚠️  服務器不可用，跳過Kimi K2聊天API測試")
            results["kimi_k2_chat"] = {"success": False, "error": "Server not available", "skipped": True}
        
        # 5. 生成部署指令
        results["deployment_instructions"] = self.generate_deployment_instructions()
        
        # 生成測試報告
        self.generate_simple_test_report(results)
        
        return results
    
    def generate_simple_test_report(self, results):
        """生成簡化測試報告"""
        print("\n" + "="*70)
        print("📊 ClaudEditor + Kimi K2 簡化功能測試報告")
        print("="*70)
        
        # 測試結果統計
        test_results = [
            ("HuggingFace Direct API", results["huggingface_api"]),
            ("ClaudEditor Server Status", results["server_status"]),
            ("UI Page Access", results["ui_access"]),
            ("Kimi K2 Chat API", results["kimi_k2_chat"])
        ]
        
        passed_tests = 0
        total_tests = 0
        
        for test_name, result in test_results:
            if result.get("skipped"):
                print(f"⏭️  {test_name}: 已跳過")
            elif result["success"]:
                print(f"✅ {test_name}: 成功")
                passed_tests += 1
                total_tests += 1
            else:
                print(f"❌ {test_name}: 失敗")
                print(f"   錯誤: {result.get('error', 'Unknown error')}")
                total_tests += 1
        
        # 計算成功率
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 測試結果: {passed_tests}/{total_tests} 通過 ({success_rate:.1f}%)")
        
        # 部署指令
        print(f"\n📋 部署指令:")
        deployment = results["deployment_instructions"]
        
        print(f"\n🔧 前置條件:")
        for prereq in deployment["prerequisites"]:
            print(f"   {prereq}")
        
        print(f"\n🚀 安裝步驟:")
        for step in deployment["installation_steps"]:
            print(f"   {step}")
        
        print(f"\n🧪 測試步驟:")
        for step in deployment["testing_steps"]:
            print(f"   {step}")
        
        # 整體狀態評估
        print(f"\n" + "="*70)
        
        if success_rate >= 75:
            print("🎉 大部分測試通過！ClaudEditor + Kimi K2整合基本成功！")
            print("💡 請繼續部署和手動測試以確保完整功能")
        elif success_rate >= 50:
            print("⚠️  部分測試通過，需要解決一些問題")
            print("💡 請檢查失敗的測試項目並按照部署指令操作")
        else:
            print("❌ 大部分測試失敗，需要重新檢查配置")
            print("💡 請確保:")
            print("   1. HuggingFace Token有效")
            print("   2. 網絡連接正常")
            print("   3. Python環境配置正確")
        
        print("="*70)


def main():
    """主函數"""
    tester = SimpleKimiK2Tester()
    tester.run_all_simple_tests()


if __name__ == "__main__":
    main()