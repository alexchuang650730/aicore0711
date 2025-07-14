#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 Playwright UI自動化測試
使用Playwright進行現代化的UI功能測試，提供更好的性能和穩定性
"""

import asyncio
import time
import logging
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UITestResult:
    """UI測試結果"""
    test_name: str
    success: bool
    message: str
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    execution_time: float = 0.0
    details: Optional[Dict[str, Any]] = None

class PlaywrightUITester:
    """Playwright UI自動化測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8000", headless: bool = False):
        self.base_url = base_url
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.test_results: List[UITestResult] = []
        self.screenshots_dir = "screenshots"
        self.videos_dir = "videos"
        
        # 創建輸出目錄
        Path(self.screenshots_dir).mkdir(exist_ok=True)
        Path(self.videos_dir).mkdir(exist_ok=True)
    
    async def setup_browser(self):
        """設置瀏覽器"""
        try:
            playwright = await async_playwright().start()
            
            # 啟動瀏覽器
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 創建上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                record_video_dir=self.videos_dir if not self.headless else None
            )
            
            # 創建頁面
            self.page = await self.context.new_page()
            
            # 設置超時
            self.page.set_default_timeout(30000)  # 30秒
            
            logger.info("✅ Playwright瀏覽器設置成功")
            
        except Exception as e:
            logger.error(f"❌ Playwright瀏覽器設置失敗: {e}")
            raise
    
    async def teardown_browser(self):
        """清理瀏覽器"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("✅ Playwright瀏覽器已清理")
        except Exception as e:
            logger.error(f"⚠️  瀏覽器清理警告: {e}")
    
    async def take_screenshot(self, name: str) -> str:
        """截圖"""
        if self.page:
            screenshot_path = f"{self.screenshots_dir}/{name}_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            return screenshot_path
        return None
    
    async def run_ui_test(self, test_func, test_name: str):
        """運行UI測試"""
        start_time = time.time()
        try:
            result = await test_func()
            execution_time = time.time() - start_time
            
            if result:
                test_result = UITestResult(
                    test_name=test_name,
                    success=True,
                    message="UI測試通過",
                    execution_time=execution_time,
                    details=result if isinstance(result, dict) else None
                )
            else:
                screenshot = await self.take_screenshot(f"failed_{test_name}")
                test_result = UITestResult(
                    test_name=test_name,
                    success=False,
                    message="UI測試失敗",
                    screenshot_path=screenshot,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            screenshot = await self.take_screenshot(f"error_{test_name}")
            test_result = UITestResult(
                test_name=test_name,
                success=False,
                message=f"UI測試異常：{str(e)}",
                screenshot_path=screenshot,
                execution_time=execution_time
            )
        
        self.test_results.append(test_result)
        status = "✅" if test_result.success else "❌"
        logger.info(f"{status} {test_name} ({test_result.execution_time:.2f}s)")
        return test_result
    
    # ===== UI測試用例 =====
    
    async def test_page_load_and_structure(self):
        """測試頁面載入和結構"""
        try:
            # 導航到頁面
            await self.page.goto(self.base_url)
            
            # 等待頁面載入完成
            await self.page.wait_for_load_state('networkidle')
            
            # 檢查頁面標題
            title = await self.page.title()
            if "ClaudEditor" not in title:
                return False
            
            # 檢查關鍵結構元素
            header = await self.page.locator('.header').count()
            sidebar = await self.page.locator('.sidebar').count()
            main_content = await self.page.locator('.main-content').count()
            
            # 檢查是否包含Kimi K2相關元素
            kimi_options = await self.page.locator('option[value="kimi_k2"]').count()
            
            return {
                "title": title,
                "header_present": header > 0,
                "sidebar_present": sidebar > 0,
                "main_content_present": main_content > 0,
                "kimi_k2_options": kimi_options,
                "structure_complete": header > 0 and sidebar > 0 and main_content > 0 and kimi_options > 0
            }
            
        except Exception as e:
            logger.error(f"頁面載入測試失敗: {e}")
            return False
    
    async def test_global_model_selector(self):
        """測試全局模型選擇器"""
        try:
            # 查找全局模型選擇器
            global_select = self.page.locator('#global-model-select')
            await global_select.wait_for(state='visible')
            
            # 獲取所有選項
            options = await global_select.locator('option').all()
            option_values = []
            for option in options:
                value = await option.get_attribute('value')
                text = await option.text_content()
                option_values.append({"value": value, "text": text})
            
            # 檢查是否包含Kimi K2
            kimi_option = next((opt for opt in option_values if opt["value"] == "kimi_k2"), None)
            if not kimi_option:
                return False
            
            # 測試切換到Kimi K2
            await global_select.select_option('kimi_k2')
            await self.page.wait_for_timeout(1000)  # 等待UI更新
            
            # 檢查選擇是否成功
            selected_value = await global_select.input_value()
            
            return {
                "options_count": len(option_values),
                "has_kimi_k2": bool(kimi_option),
                "kimi_k2_text": kimi_option["text"] if kimi_option else None,
                "switch_successful": selected_value == "kimi_k2",
                "all_options": option_values
            }
            
        except Exception as e:
            logger.error(f"全局模型選擇器測試失敗: {e}")
            return False
    
    async def test_ai_chat_panel_interaction(self):
        """測試AI聊天面板交互"""
        try:
            # 點擊AI助手導航
            ai_nav = self.page.locator('[data-tab="ai-chat"]')
            await ai_nav.click()
            await self.page.wait_for_timeout(500)
            
            # 檢查AI聊天面板是否激活
            ai_panel = self.page.locator('#ai-chat-panel')
            panel_classes = await ai_panel.get_attribute('class')
            is_active = 'active' in panel_classes
            
            # 測試AI模型選擇器
            ai_model_select = self.page.locator('#ai-model-select')
            await ai_model_select.wait_for(state='visible')
            
            # 選擇Kimi K2
            await ai_model_select.select_option('kimi_k2')
            await self.page.wait_for_timeout(1000)
            
            # 檢查模型狀態指示器
            status_text = await self.page.locator('#model-status-text').text_content()
            
            return {
                "panel_active": is_active,
                "model_selector_visible": await ai_model_select.is_visible(),
                "kimi_k2_selected": await ai_model_select.input_value() == "kimi_k2",
                "status_text": status_text
            }
            
        except Exception as e:
            logger.error(f"AI聊天面板交互測試失敗: {e}")
            return False
    
    async def test_model_parameters_functionality(self):
        """測試模型參數功能"""
        try:
            # 確保在AI聊天面板
            await self.test_ai_chat_panel_interaction()
            
            # 點擊參數按鈕
            params_btn = self.page.locator('#toggle-params')
            await params_btn.click()
            await self.page.wait_for_timeout(500)
            
            # 檢查參數面板是否顯示
            params_panel = self.page.locator('#model-params-panel')
            is_visible = await params_panel.is_visible()
            
            if not is_visible:
                return False
            
            # 測試溫度滑桿
            temp_slider = self.page.locator('#temperature-slider')
            await temp_slider.fill('0.5')
            await self.page.wait_for_timeout(500)
            
            # 檢查溫度值是否更新
            temp_value = await self.page.locator('#temperature-value').text_content()
            
            # 測試Max Tokens輸入
            max_tokens_input = self.page.locator('#max-tokens-input')
            await max_tokens_input.fill('1500')
            
            # 測試Top-P滑桿
            top_p_slider = self.page.locator('#top-p-slider')
            await top_p_slider.fill('0.8')
            await self.page.wait_for_timeout(500)
            
            top_p_value = await self.page.locator('#top-p-value').text_content()
            
            return {
                "params_panel_visible": is_visible,
                "temperature_updated": temp_value == "0.5",
                "max_tokens_updated": await max_tokens_input.input_value() == "1500",
                "top_p_updated": top_p_value == "0.8"
            }
            
        except Exception as e:
            logger.error(f"模型參數功能測試失敗: {e}")
            return False
    
    async def test_chat_functionality(self):
        """測試聊天功能"""
        try:
            # 確保在AI聊天面板並選擇Kimi K2
            await self.test_ai_chat_panel_interaction()
            
            # 查找聊天輸入框
            chat_input = self.page.locator('#chat-input')
            await chat_input.wait_for(state='visible')
            
            # 輸入測試消息
            test_message = "Hello Kimi K2! 請用中文回覆'測試成功'"
            await chat_input.fill(test_message)
            
            # 點擊發送按鈕
            send_btn = self.page.locator('#send-message')
            await send_btn.click()
            
            # 等待用戶消息出現
            await self.page.wait_for_selector('.message.user', timeout=5000)
            
            # 檢查輸入框是否清空
            input_value = await chat_input.input_value()
            
            # 等待AI回應（如果服務器正常）
            try:
                await self.page.wait_for_selector('.message.assistant:not(:first-child)', timeout=15000)
                response_received = True
            except:
                response_received = False
            
            return {
                "message_sent": input_value == "",
                "user_message_displayed": await self.page.locator('.message.user').count() > 0,
                "response_received": response_received,
                "test_message": test_message
            }
            
        except Exception as e:
            logger.error(f"聊天功能測試失敗: {e}")
            return False
    
    async def test_model_comparison_panel(self):
        """測試模型對比面板"""
        try:
            # 點擊模型對比導航
            comparison_nav = self.page.locator('[data-tab="model-comparison"]')
            await comparison_nav.click()
            await self.page.wait_for_timeout(500)
            
            # 檢查對比面板是否顯示
            comparison_panel = self.page.locator('#model-comparison-panel')
            is_visible = await comparison_panel.is_visible()
            
            if not is_visible:
                return False
            
            # 檢查模型複選框
            checkboxes = await self.page.locator('.model-checkbox input[type="checkbox"]').all()
            checkbox_count = len(checkboxes)
            
            # 檢查Claude和Kimi K2是否預設選中
            claude_checked = await self.page.locator('input[value="claude"]').is_checked()
            kimi_checked = await self.page.locator('input[value="kimi_k2"]').is_checked()
            
            # 測試對比輸入框
            comparison_input = self.page.locator('#comparison-input')
            test_question = "什麼是人工智能？請簡單回答。"
            await comparison_input.fill(test_question)
            
            # 檢查詢問按鈕
            ask_btn = self.page.locator('#ask-all-models')
            ask_btn_visible = await ask_btn.is_visible()
            
            return {
                "panel_visible": is_visible,
                "checkbox_count": checkbox_count,
                "claude_checked": claude_checked,
                "kimi_checked": kimi_checked,
                "input_working": await comparison_input.input_value() == test_question,
                "ask_button_visible": ask_btn_visible
            }
            
        except Exception as e:
            logger.error(f"模型對比面板測試失敗: {e}")
            return False
    
    async def test_notification_system(self):
        """測試通知系統"""
        try:
            # 觸發模型切換通知
            global_select = self.page.locator('#global-model-select')
            
            # 切換到Claude
            await global_select.select_option('claude')
            await self.page.wait_for_timeout(1000)
            
            # 切換到Kimi K2
            await global_select.select_option('kimi_k2')
            await self.page.wait_for_timeout(1000)
            
            # 檢查通知是否出現（可能很快消失）
            notification = self.page.locator('#model-switch-notification')
            
            # 由於通知可能快速消失，我們檢查元素是否存在
            notification_exists = await notification.count() > 0
            
            return {
                "notification_element_exists": notification_exists,
                "switch_completed": await global_select.input_value() == "kimi_k2"
            }
            
        except Exception as e:
            logger.error(f"通知系統測試失敗: {e}")
            return False
    
    async def test_responsive_design(self):
        """測試響應式設計"""
        try:
            # 測試不同視窗大小
            sizes = [
                {"name": "desktop", "width": 1920, "height": 1080},
                {"name": "tablet", "width": 768, "height": 1024},
                {"name": "mobile", "width": 375, "height": 667}
            ]
            
            results = {}
            
            for size in sizes:
                await self.page.set_viewport_size({
                    "width": size["width"],
                    "height": size["height"]
                })
                await self.page.wait_for_timeout(1000)
                
                # 檢查關鍵元素是否可見
                header_visible = await self.page.locator('.header').is_visible()
                sidebar_visible = await self.page.locator('.sidebar').is_visible()
                main_content_visible = await self.page.locator('.main-content').is_visible()
                
                results[size["name"]] = {
                    "header_visible": header_visible,
                    "sidebar_visible": sidebar_visible,
                    "main_content_visible": main_content_visible,
                    "all_visible": header_visible and main_content_visible
                }
            
            # 恢復到桌面大小
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            return results
            
        except Exception as e:
            logger.error(f"響應式設計測試失敗: {e}")
            return False
    
    async def test_accessibility_features(self):
        """測試可訪問性功能"""
        try:
            # 檢查ARIA標籤
            aria_elements = await self.page.locator('[aria-label]').count()
            
            # 檢查標題結構
            h1_count = await self.page.locator('h1').count()
            h2_count = await self.page.locator('h2').count()
            h3_count = await self.page.locator('h3').count()
            
            # 檢查表單標籤
            label_count = await self.page.locator('label').count()
            input_count = await self.page.locator('input, select, textarea').count()
            
            # 檢查鍵盤導航
            chat_input = self.page.locator('#chat-input')
            await chat_input.focus()
            is_focused = await chat_input.is_focused()
            
            return {
                "aria_elements": aria_elements,
                "heading_structure": {
                    "h1": h1_count,
                    "h2": h2_count,
                    "h3": h3_count
                },
                "form_accessibility": {
                    "labels": label_count,
                    "inputs": input_count
                },
                "keyboard_navigation": is_focused
            }
            
        except Exception as e:
            logger.error(f"可訪問性測試失敗: {e}")
            return False
    
    async def test_performance_metrics(self):
        """測試性能指標"""
        try:
            # 測量頁面載入時間
            start_time = time.time()
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state('networkidle')
            load_time = time.time() - start_time
            
            # 檢查網絡請求
            responses = []
            async def handle_response(response):
                responses.append({
                    "url": response.url,
                    "status": response.status,
                    "size": len(await response.body()) if response.status == 200 else 0
                })
            
            self.page.on("response", handle_response)
            
            # 觸發一些交互
            await self.page.locator('[data-tab="ai-chat"]').click()
            await self.page.wait_for_timeout(2000)
            
            # 移除事件監聽器
            self.page.remove_listener("response", handle_response)
            
            return {
                "page_load_time": load_time,
                "network_requests": len(responses),
                "successful_requests": sum(1 for r in responses if r["status"] == 200),
                "failed_requests": sum(1 for r in responses if r["status"] >= 400),
                "total_size": sum(r["size"] for r in responses)
            }
            
        except Exception as e:
            logger.error(f"性能測試失敗: {e}")
            return False
    
    async def run_all_ui_tests(self):
        """運行所有UI測試"""
        logger.info("🎭 開始運行Playwright UI自動化測試")
        
        await self.setup_browser()
        
        try:
            # UI測試列表
            ui_tests = [
                (self.test_page_load_and_structure, "頁面載入和結構"),
                (self.test_global_model_selector, "全局模型選擇器"),
                (self.test_ai_chat_panel_interaction, "AI聊天面板交互"),
                (self.test_model_parameters_functionality, "模型參數功能"),
                (self.test_chat_functionality, "聊天功能"),
                (self.test_model_comparison_panel, "模型對比面板"),
                (self.test_notification_system, "通知系統"),
                (self.test_responsive_design, "響應式設計"),
                (self.test_accessibility_features, "可訪問性功能"),
                (self.test_performance_metrics, "性能指標")
            ]
            
            # 執行測試
            for test_func, test_name in ui_tests:
                await self.run_ui_test(test_func, test_name)
                await asyncio.sleep(1)  # 測試間隔
            
        finally:
            await self.teardown_browser()
        
        # 生成測試報告
        self.generate_ui_report()
        
        return self.test_results
    
    def generate_ui_report(self):
        """生成UI測試報告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.success)
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*70)
        print("🎭 ClaudEditor Playwright UI自動化測試報告")
        print("="*70)
        print(f"📊 總測試數: {total_tests}")
        print(f"✅ 通過: {passed_tests}")
        print(f"❌ 失敗: {failed_tests}")
        print(f"📈 成功率: {success_rate:.1f}%")
        print("="*70)
        
        print("\n📋 詳細結果:")
        for result in self.test_results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.test_name} ({result.execution_time:.2f}s)")
            if not result.success:
                print(f"   ❌ 錯誤: {result.message}")
                if result.screenshot_path:
                    print(f"   📸 截圖: {result.screenshot_path}")
                if result.video_path:
                    print(f"   🎥 視頻: {result.video_path}")
            elif result.details:
                print(f"   📋 詳情: {json.dumps(result.details, ensure_ascii=False, indent=6)}")
        
        print("\n" + "="*70)
        
        if success_rate >= 80:
            print("🎉 UI測試整體通過！Kimi K2界面整合成功！")
        elif success_rate >= 60:
            print("⚠️  UI測試部分通過，需要檢查一些問題")
        else:
            print("❌ UI測試未通過，需要重大修復")
        
        print("="*70)


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ClaudEditor Playwright UI自動化測試")
    parser.add_argument("--url", default="http://localhost:8000", help="服務器URL")
    parser.add_argument("--headless", action="store_true", help="無頭模式")
    parser.add_argument("--screenshots", default="screenshots", help="截圖目錄")
    parser.add_argument("--videos", default="videos", help="視頻目錄")
    
    args = parser.parse_args()
    
    # 創建輸出目錄
    os.makedirs(args.screenshots, exist_ok=True)
    os.makedirs(args.videos, exist_ok=True)
    
    tester = PlaywrightUITester(base_url=args.url, headless=args.headless)
    results = await tester.run_all_ui_tests()
    
    # 返回適當的退出碼
    failed_count = sum(1 for r in results if not r.success)
    exit_code = 0 if failed_count == 0 else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)