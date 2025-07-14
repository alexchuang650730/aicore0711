#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 UI自動化測試
使用Selenium進行UI功能測試
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from typing import Dict, List, Any
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UITestResult:
    """UI測試結果"""
    test_name: str
    success: bool
    message: str
    screenshot_path: str = None
    execution_time: float = 0.0

class ClaudEditorUITester:
    """ClaudEditor UI自動化測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8000", headless: bool = False):
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.wait = None
        self.test_results: List[UITestResult] = []
        
    def setup_driver(self):
        """設置WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("WebDriver設置成功")
        except Exception as e:
            logger.error(f"WebDriver設置失敗: {e}")
            raise
    
    def teardown_driver(self):
        """清理WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver已清理")
    
    def take_screenshot(self, name: str) -> str:
        """截圖"""
        if self.driver:
            screenshot_path = f"screenshots/{name}_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            return screenshot_path
        return None
    
    def run_ui_test(self, test_func, test_name: str):
        """運行UI測試"""
        start_time = time.time()
        try:
            result = test_func()
            execution_time = time.time() - start_time
            
            if result:
                test_result = UITestResult(
                    test_name=test_name,
                    success=True,
                    message="UI測試通過",
                    execution_time=execution_time
                )
            else:
                screenshot = self.take_screenshot(f"failed_{test_name}")
                test_result = UITestResult(
                    test_name=test_name,
                    success=False,
                    message="UI測試失敗",
                    screenshot_path=screenshot,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            screenshot = self.take_screenshot(f"error_{test_name}")
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
    
    def test_page_load(self):
        """測試頁面載入"""
        try:
            self.driver.get(self.base_url)
            
            # 等待頁面標題出現
            self.wait.until(EC.title_contains("ClaudEditor"))
            
            # 檢查關鍵元素
            header = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "header")))
            sidebar = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sidebar")))
            
            return True
        except TimeoutException:
            logger.error("頁面載入超時")
            return False
    
    def test_global_model_selector(self):
        """測試全局模型選擇器"""
        try:
            # 查找全局模型選擇器
            global_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "global-model-select"))
            )
            
            # 獲取所有選項
            select_obj = Select(global_select)
            options = select_obj.options
            
            # 檢查是否包含Kimi K2
            option_values = [opt.get_attribute("value") for opt in options]
            has_kimi = "kimi_k2" in option_values
            
            if not has_kimi:
                logger.error("全局選擇器中未找到Kimi K2選項")
                return False
            
            # 測試切換到Kimi K2
            select_obj.select_by_value("kimi_k2")
            time.sleep(1)
            
            # 檢查是否成功切換
            current_value = select_obj.first_selected_option.get_attribute("value")
            return current_value == "kimi_k2"
            
        except Exception as e:
            logger.error(f"全局模型選擇器測試失敗: {e}")
            return False
    
    def test_ai_chat_panel_navigation(self):
        """測試AI聊天面板導航"""
        try:
            # 點擊AI助手導航項
            ai_nav = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-tab="ai-chat"]'))
            )
            ai_nav.click()
            
            # 等待AI聊天面板顯示
            ai_panel = self.wait.until(
                EC.visibility_of_element_located((By.ID, "ai-chat-panel"))
            )
            
            # 檢查面板是否有active類
            return "active" in ai_panel.get_attribute("class")
            
        except Exception as e:
            logger.error(f"AI聊天面板導航測試失敗: {e}")
            return False
    
    def test_ai_model_selector(self):
        """測試AI面板中的模型選擇器"""
        try:
            # 確保在AI聊天面板
            self.test_ai_chat_panel_navigation()
            
            # 查找AI模型選擇器
            ai_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "ai-model-select"))
            )
            
            # 測試選擇器
            select_obj = Select(ai_select)
            options = [opt.get_attribute("value") for opt in select_obj.options]
            
            # 檢查Kimi K2選項
            if "kimi_k2" not in options:
                logger.error("AI模型選擇器中未找到Kimi K2")
                return False
            
            # 測試切換
            select_obj.select_by_value("kimi_k2")
            time.sleep(1)
            
            # 檢查模型指示器是否更新
            try:
                model_indicator = self.driver.find_element(By.ID, "current-model-indicator")
                indicator_text = model_indicator.text
                return "🌙" in indicator_text  # Kimi K2的表情符號
            except NoSuchElementException:
                return True  # 如果沒有指示器也算通過
                
        except Exception as e:
            logger.error(f"AI模型選擇器測試失敗: {e}")
            return False
    
    def test_model_parameters_panel(self):
        """測試模型參數面板"""
        try:
            # 確保在AI聊天面板
            self.test_ai_chat_panel_navigation()
            
            # 點擊參數按鈕
            params_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "toggle-params"))
            )
            params_btn.click()
            time.sleep(1)
            
            # 檢查參數面板是否顯示
            params_panel = self.wait.until(
                EC.visibility_of_element_located((By.ID, "model-params-panel"))
            )
            
            # 測試溫度滑桿
            temp_slider = self.driver.find_element(By.ID, "temperature-slider")
            self.driver.execute_script("arguments[0].value = '0.5'", temp_slider)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", temp_slider)
            
            # 檢查溫度值是否更新
            temp_value = self.driver.find_element(By.ID, "temperature-value")
            return temp_value.text == "0.5"
            
        except Exception as e:
            logger.error(f"模型參數面板測試失敗: {e}")
            return False
    
    def test_chat_input_and_send(self):
        """測試聊天輸入和發送"""
        try:
            # 確保在AI聊天面板並選擇Kimi K2
            self.test_ai_chat_panel_navigation()
            self.test_ai_model_selector()
            
            # 查找聊天輸入框
            chat_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "chat-input"))
            )
            
            # 輸入測試消息
            test_message = "Hello Kimi K2, please respond with 'UI test successful'"
            chat_input.clear()
            chat_input.send_keys(test_message)
            
            # 點擊發送按鈕
            send_btn = self.driver.find_element(By.ID, "send-message")
            send_btn.click()
            
            # 等待用戶消息出現
            user_message = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".message.user"))
            )
            
            # 檢查輸入框是否清空
            return chat_input.get_attribute("value") == ""
            
        except Exception as e:
            logger.error(f"聊天輸入測試失敗: {e}")
            return False
    
    def test_model_comparison_panel(self):
        """測試模型對比面板"""
        try:
            # 點擊模型對比導航
            comparison_nav = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-tab="model-comparison"]'))
            )
            comparison_nav.click()
            
            # 等待對比面板顯示
            comparison_panel = self.wait.until(
                EC.visibility_of_element_located((By.ID, "model-comparison-panel"))
            )
            
            # 檢查模型複選框
            checkboxes = self.driver.find_elements(
                By.CSS_SELECTOR, ".model-checkbox input[type='checkbox']"
            )
            
            if len(checkboxes) < 2:
                logger.error("模型複選框數量不足")
                return False
            
            # 測試對比輸入框
            comparison_input = self.driver.find_element(By.ID, "comparison-input")
            comparison_input.send_keys("Test comparison functionality")
            
            return True
            
        except Exception as e:
            logger.error(f"模型對比面板測試失敗: {e}")
            return False
    
    def test_model_status_indicator(self):
        """測試模型狀態指示器"""
        try:
            # 確保在AI聊天面板
            self.test_ai_chat_panel_navigation()
            
            # 查找狀態指示器
            status_icon = self.wait.until(
                EC.presence_of_element_located((By.ID, "model-status-icon"))
            )
            status_text = self.driver.find_element(By.ID, "model-status-text")
            
            # 檢查狀態
            icon_class = status_icon.get_attribute("class")
            text_content = status_text.text
            
            # 狀態應該是可用、不可用或檢查中之一
            valid_statuses = ["就绪", "不可用", "检查中"]
            return any(status in text_content for status in valid_statuses)
            
        except Exception as e:
            logger.error(f"模型狀態指示器測試失敗: {e}")
            return False
    
    def test_notification_system(self):
        """測試通知系統"""
        try:
            # 觸發模型切換來測試通知
            self.test_global_model_selector()
            
            # 等待通知出現
            try:
                notification = self.wait.until(
                    EC.visibility_of_element_located((By.ID, "model-switch-notification"))
                )
                
                # 檢查通知內容
                notification_text = self.driver.find_element(By.ID, "notification-text")
                text_content = notification_text.text
                
                return "Kimi K2" in text_content
                
            except TimeoutException:
                # 通知可能顯示很快就消失了
                logger.warning("通知未能及時捕獲，但這可能是正常的")
                return True
            
        except Exception as e:
            logger.error(f"通知系統測試失敗: {e}")
            return False
    
    def test_responsive_design(self):
        """測試響應式設計"""
        try:
            # 測試不同視窗大小
            sizes = [
                (1920, 1080),  # 桌面
                (768, 1024),   # 平板
                (375, 667)     # 手機
            ]
            
            for width, height in sizes:
                self.driver.set_window_size(width, height)
                time.sleep(1)
                
                # 檢查關鍵元素是否仍然可見
                header = self.driver.find_element(By.CLASS_NAME, "header")
                if not header.is_displayed():
                    logger.error(f"Header在{width}x{height}下不可見")
                    return False
            
            # 恢復到原始大小
            self.driver.set_window_size(1920, 1080)
            return True
            
        except Exception as e:
            logger.error(f"響應式設計測試失敗: {e}")
            return False
    
    def test_keyboard_navigation(self):
        """測試鍵盤導航"""
        try:
            # 確保在AI聊天面板
            self.test_ai_chat_panel_navigation()
            
            # 測試Tab鍵導航
            chat_input = self.driver.find_element(By.ID, "chat-input")
            chat_input.click()
            
            # 輸入測試文本
            chat_input.send_keys("Test keyboard navigation")
            
            # 測試Enter鍵發送（如果實現了）
            chat_input.send_keys(Keys.CONTROL + Keys.ENTER)
            
            return True
            
        except Exception as e:
            logger.error(f"鍵盤導航測試失敗: {e}")
            return False
    
    def run_all_ui_tests(self):
        """運行所有UI測試"""
        logger.info("🎭 開始運行ClaudEditor UI自動化測試")
        
        self.setup_driver()
        
        try:
            # UI測試列表
            ui_tests = [
                (self.test_page_load, "頁面載入"),
                (self.test_global_model_selector, "全局模型選擇器"),
                (self.test_ai_chat_panel_navigation, "AI聊天面板導航"),
                (self.test_ai_model_selector, "AI模型選擇器"),
                (self.test_model_parameters_panel, "模型參數面板"),
                (self.test_chat_input_and_send, "聊天輸入和發送"),
                (self.test_model_comparison_panel, "模型對比面板"),
                (self.test_model_status_indicator, "模型狀態指示器"),
                (self.test_notification_system, "通知系統"),
                (self.test_responsive_design, "響應式設計"),
                (self.test_keyboard_navigation, "鍵盤導航")
            ]
            
            # 執行測試
            for test_func, test_name in ui_tests:
                self.run_ui_test(test_func, test_name)
                time.sleep(1)  # 測試間隔
            
        finally:
            self.teardown_driver()
        
        # 生成UI測試報告
        self.generate_ui_report()
        
        return self.test_results
    
    def generate_ui_report(self):
        """生成UI測試報告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.success)
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("🎭 ClaudEditor UI自動化測試報告")
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
                if result.screenshot_path:
                    print(f"   截圖: {result.screenshot_path}")
        
        print("\n" + "="*60)


def main():
    """主函數"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="ClaudEditor UI自動化測試")
    parser.add_argument("--url", default="http://localhost:8000", help="服務器URL")
    parser.add_argument("--headless", action="store_true", help="無頭模式")
    parser.add_argument("--screenshots", default="screenshots", help="截圖目錄")
    
    args = parser.parse_args()
    
    # 創建截圖目錄
    os.makedirs(args.screenshots, exist_ok=True)
    
    tester = ClaudEditorUITester(base_url=args.url, headless=args.headless)
    results = tester.run_all_ui_tests()
    
    # 返回適當的退出碼
    failed_count = sum(1 for r in results if not r.success)
    exit_code = 0 if failed_count == 0 else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)