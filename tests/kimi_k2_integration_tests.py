#!/usr/bin/env python3
"""
Kimi K2 ClaudEditor 集成測試套件
使用test_mcp, stagewise_mcp, playwright進行完整的UI操作和API測試
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

import pytest
import requests
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 添加core路徑到系統路徑
sys.path.append(str(Path(__file__).parent.parent))

# 設置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KimiK2IntegrationTests:
    """Kimi K2 ClaudEditor 集成測試類"""
    
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.react_url = "http://localhost:5175"
        self.api_base = f"{self.base_url}/api"
        self.test_results = []
        
    def setup_test_environment(self):
        """設置測試環境"""
        logger.info("🚀 設置Kimi K2集成測試環境...")
        
        # 檢查服務狀態
        try:
            response = requests.get(f"{self.api_base}/status", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Demo服務器已啟動")
            else:
                logger.error("❌ Demo服務器狀態異常")
                return False
        except Exception as e:
            logger.error(f"❌ 無法連接Demo服務器: {e}")
            return False
            
        # 檢查React開發服務器
        try:
            response = requests.get(self.react_url, timeout=5)
            if response.status_code == 200:
                logger.info("✅ React開發服務器已啟動")
            else:
                logger.info("⚠️ React開發服務器可能未啟動")
        except Exception as e:
            logger.info(f"⚠️ React開發服務器檢查: {e}")
            
        return True
        
    def test_api_models_endpoint(self):
        """測試模型列表API端點"""
        logger.info("🧪 測試API模型端點...")
        
        try:
            response = requests.get(f"{self.api_base}/models")
            assert response.status_code == 200
            
            data = response.json()
            assert "models" in data
            
            models = data["models"]
            model_ids = [model["id"] for model in models]
            
            assert "kimi_k2" in model_ids, "Kimi K2模型應該在模型列表中"
            assert "claude" in model_ids, "Claude模型應該在模型列表中"
            
            # 檢查Kimi K2模型詳情
            kimi_model = next(m for m in models if m["id"] == "kimi_k2")
            assert kimi_model["provider"] == "novita"
            assert "月之暗面" in kimi_model["name"]
            
            logger.info("✅ API模型端點測試通過")
            self.test_results.append({"test": "API Models", "status": "PASS"})
            return True
            
        except Exception as e:
            logger.error(f"❌ API模型端點測試失敗: {e}")
            self.test_results.append({"test": "API Models", "status": "FAIL", "error": str(e)})
            return False
            
    def test_kimi_k2_chat_api(self):
        """測試Kimi K2聊天API"""
        logger.info("🧪 測試Kimi K2聊天API...")
        
        try:
            chat_request = {
                "message": "你好，請介紹一下Kimi K2模型",
                "model": "kimi_k2",
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.api_base}/ai/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "response" in data
            assert data["model"] == "kimi_k2"
            assert len(data["response"]) > 0
            assert "🌙" in data["response"]  # 應該包含Kimi標識
            
            logger.info("✅ Kimi K2聊天API測試通過")
            logger.info(f"📝 回應內容: {data['response'][:100]}...")
            
            self.test_results.append({"test": "Kimi K2 Chat API", "status": "PASS"})
            return True
            
        except Exception as e:
            logger.error(f"❌ Kimi K2聊天API測試失敗: {e}")
            self.test_results.append({"test": "Kimi K2 Chat API", "status": "FAIL", "error": str(e)})
            return False
            
    def test_claude_chat_api(self):
        """測試Claude聊天API"""
        logger.info("🧪 測試Claude聊天API...")
        
        try:
            chat_request = {
                "message": "請介紹一下Claude模型",
                "model": "claude",
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.api_base}/ai/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "response" in data
            assert data["model"] == "claude"
            assert len(data["response"]) > 0
            assert "🔵" in data["response"]  # 應該包含Claude標識
            
            logger.info("✅ Claude聊天API測試通過")
            logger.info(f"📝 回應內容: {data['response'][:100]}...")
            
            self.test_results.append({"test": "Claude Chat API", "status": "PASS"})
            return True
            
        except Exception as e:
            logger.error(f"❌ Claude聊天API測試失敗: {e}")
            self.test_results.append({"test": "Claude Chat API", "status": "FAIL", "error": str(e)})
            return False

    async def test_ui_with_playwright(self):
        """使用Playwright進行UI測試"""
        logger.info("🧪 使用Playwright進行UI測試...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                # 訪問demo頁面
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                
                # 檢查頁面標題
                title = await page.title()
                assert "Kimi K2" in title, f"頁面標題應包含Kimi K2: {title}"
                
                # 檢查模型選擇器
                model_select = page.locator("#model-select")
                await model_select.wait_for()
                
                # 檢查Kimi K2選項存在
                kimi_option = page.locator('option[value="kimi_k2"]')
                await kimi_option.wait_for()
                kimi_text = await kimi_option.text_content()
                assert "Kimi K2" in kimi_text
                
                # 檢查Claude選項存在
                claude_option = page.locator('option[value="claude"]')
                await claude_option.wait_for()
                claude_text = await claude_option.text_content()
                assert "Claude" in claude_text
                
                # 測試模型切換
                await model_select.select_option("kimi_k2")
                await page.wait_for_timeout(1000)
                
                # 發送測試消息
                message_input = page.locator("#message-input")
                await message_input.fill("測試Kimi K2模型回應")
                
                send_button = page.locator("button:has-text('發送')")
                await send_button.click()
                
                # 等待回應
                await page.wait_for_timeout(3000)
                
                # 檢查回應是否出現
                messages = page.locator(".message")
                message_count = await messages.count()
                assert message_count >= 2, "應該至少有用戶消息和AI回應"
                
                # 切換到Claude並測試
                await model_select.select_option("claude")
                await page.wait_for_timeout(1000)
                
                await message_input.fill("測試Claude模型回應")
                await send_button.click()
                await page.wait_for_timeout(3000)
                
                # 檢查最終消息數
                final_count = await messages.count()
                assert final_count >= 4, "應該有兩組對話"
                
                await browser.close()
                
                logger.info("✅ Playwright UI測試通過")
                self.test_results.append({"test": "Playwright UI", "status": "PASS"})
                return True
                
        except Exception as e:
            logger.error(f"❌ Playwright UI測試失敗: {e}")
            self.test_results.append({"test": "Playwright UI", "status": "FAIL", "error": str(e)})
            return False
            
    def test_ui_with_selenium(self):
        """使用Selenium進行UI測試"""
        logger.info("🧪 使用Selenium進行UI測試...")
        
        driver = None
        try:
            # 設置Chrome選項
            from selenium.webdriver.chrome.options import Options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            
            # 訪問demo頁面
            driver.get(self.base_url)
            
            # 檢查頁面標題
            assert "Kimi K2" in driver.title
            
            # 找到並檢查模型選擇器
            model_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "model-select"))
            )
            
            # 檢查選項
            options = driver.find_elements(By.TAG_NAME, "option")
            option_values = [opt.get_attribute("value") for opt in options]
            
            assert "kimi_k2" in option_values, "應該有Kimi K2選項"
            assert "claude" in option_values, "應該有Claude選項"
            
            # 測試發送消息
            message_input = driver.find_element(By.ID, "message-input")
            message_input.send_keys("Selenium測試消息")
            
            send_button = driver.find_element(By.CSS_SELECTOR, "button:contains('發送'), button[onclick*='sendMessage']")
            send_button.click()
            
            # 等待回應
            time.sleep(3)
            
            # 檢查消息是否出現
            messages = driver.find_elements(By.CLASS_NAME, "message")
            assert len(messages) >= 2, "應該有用戶消息和AI回應"
            
            logger.info("✅ Selenium UI測試通過")
            self.test_results.append({"test": "Selenium UI", "status": "PASS"})
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium UI測試失敗: {e}")
            self.test_results.append({"test": "Selenium UI", "status": "FAIL", "error": str(e)})
            return False
            
        finally:
            if driver:
                driver.quit()
                
    def test_model_comparison(self):
        """測試模型對比功能"""
        logger.info("🧪 測試模型對比功能...")
        
        try:
            # 測試兩個模型的回應差異
            question = "什麼是人工智能？"
            
            # Kimi K2回應
            kimi_request = {
                "message": question,
                "model": "kimi_k2",
                "max_tokens": 300
            }
            
            kimi_response = requests.post(
                f"{self.api_base}/ai/chat",
                json=kimi_request
            )
            
            # Claude回應
            claude_request = {
                "message": question,
                "model": "claude",
                "max_tokens": 300
            }
            
            claude_response = requests.post(
                f"{self.api_base}/ai/chat",
                json=claude_request
            )
            
            assert kimi_response.status_code == 200
            assert claude_response.status_code == 200
            
            kimi_data = kimi_response.json()
            claude_data = claude_response.json()
            
            # 驗證回應不同
            assert kimi_data["response"] != claude_data["response"], "兩個模型的回應應該不同"
            
            # 驗證模型標識
            assert "🌙" in kimi_data["response"], "Kimi K2回應應包含月亮標識"
            assert "🔵" in claude_data["response"], "Claude回應應包含藍圓標識"
            
            logger.info("✅ 模型對比測試通過")
            logger.info(f"📝 Kimi K2: {kimi_data['response'][:50]}...")
            logger.info(f"📝 Claude: {claude_data['response'][:50]}...")
            
            self.test_results.append({"test": "Model Comparison", "status": "PASS"})
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型對比測試失敗: {e}")
            self.test_results.append({"test": "Model Comparison", "status": "FAIL", "error": str(e)})
            return False
            
    def run_all_tests(self):
        """運行所有測試"""
        logger.info("🎯 開始運行Kimi K2 ClaudEditor完整集成測試套件...")
        
        if not self.setup_test_environment():
            logger.error("❌ 測試環境設置失敗，終止測試")
            return False
            
        # 運行API測試
        tests = [
            self.test_api_models_endpoint,
            self.test_kimi_k2_chat_api,
            self.test_claude_chat_api,
            self.test_model_comparison,
            self.test_ui_with_selenium
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)  # 測試間隔
            except Exception as e:
                logger.error(f"❌ 測試 {test.__name__} 執行失敗: {e}")
                
        # 運行Playwright異步測試
        try:
            asyncio.run(self.test_ui_with_playwright())
        except Exception as e:
            logger.error(f"❌ Playwright測試執行失敗: {e}")
            
        # 生成測試報告
        self.generate_test_report()
        
        return True
        
    def generate_test_report(self):
        """生成測試報告"""
        logger.info("📊 生成測試報告...")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": f"{success_rate:.1f}%"
            },
            "test_results": self.test_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存報告
        report_file = "/Users/alexchuang/Desktop/alex/tests/package/kimi_k2_integration_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        # 打印報告
        print("\n" + "="*60)
        print("🎉 KIMI K2 CLAUDEDITOR 集成測試報告")
        print("="*60)
        print(f"📊 總測試數: {total_tests}")
        print(f"✅ 通過: {passed_tests}")
        print(f"❌ 失敗: {failed_tests}")
        print(f"📈 成功率: {success_rate:.1f}%")
        print("\n📋 詳細結果:")
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {result['test']}: {result['status']}")
            if result["status"] == "FAIL" and "error" in result:
                print(f"     錯誤: {result['error']}")
                
        print(f"\n📄 完整報告已保存至: {report_file}")
        print("="*60)
        
        return report

if __name__ == "__main__":
    # 創建並運行測試套件
    test_suite = KimiK2IntegrationTests()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 Kimi K2 ClaudEditor集成測試完成！")
    else:
        print("\n❌ 測試執行遇到問題")
        sys.exit(1)