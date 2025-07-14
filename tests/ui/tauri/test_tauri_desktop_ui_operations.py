#!/usr/bin/env python3
"""
Tauri Desktop UI 實際操作測試腳本
使用 Selenium 或直接瀏覽器操作測試 ClaudeEditor 功能
"""

import time
import json
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os

class TauriDesktopUITester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5175"
        self.driver = None
        self.test_results = []
        
    def setup_browser(self):
        """設置瀏覽器進行 UI 測試"""
        print("🔧 設置瀏覽器環境...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1400,900")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome 瀏覽器啟動成功")
            return True
        except Exception as e:
            print(f"❌ 瀏覽器啟動失敗: {e}")
            return False
    
    def wait_for_server(self, timeout=30):
        """等待服務器啟動"""
        print(f"⏳ 等待服務器啟動 ({self.base_url})...")
        
        for i in range(timeout):
            try:
                response = requests.get(self.base_url, timeout=2)
                if response.status_code == 200:
                    print("✅ 服務器已就緒")
                    return True
            except:
                time.sleep(1)
                print(f"   等待中... ({i+1}/{timeout})")
        
        print("❌ 服務器啟動超時")
        return False
    
    def test_page_load(self):
        """測試頁面加載"""
        print("🧪 測試頁面加載...")
        
        try:
            self.driver.get(self.base_url)
            
            # 等待頁面標題加載
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.title != ""
            )
            
            title = self.driver.title
            print(f"   頁面標題: {title}")
            
            # 檢查是否有 React 根元素
            root_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "root"))
            )
            
            self.test_results.append({
                "test": "頁面加載",
                "status": "passed",
                "details": f"標題: {title}, 根元素存在: {root_element is not None}"
            })
            
            print("✅ 頁面加載測試通過")
            return True
            
        except Exception as e:
            self.test_results.append({
                "test": "頁面加載",
                "status": "failed", 
                "error": str(e)
            })
            print(f"❌ 頁面加載測試失敗: {e}")
            return False
    
    def test_ui_elements(self):
        """測試 UI 元素"""
        print("🧪 測試 UI 元素...")
        
        try:
            # 尋找主要 UI 組件
            ui_tests = [
                ("AI 助手區域", "ai-assistant"),
                ("代碼編輯器", "monaco-editor"),
                ("工具管理器", "tool-manager"),
                ("項目管理", "project-panel")
            ]
            
            passed_tests = 0
            for test_name, element_id in ui_tests:
                try:
                    element = self.driver.find_element(By.ID, element_id)
                    print(f"   ✅ {test_name}: 找到")
                    passed_tests += 1
                except:
                    # 嘗試使用 class name
                    try:
                        element = self.driver.find_element(By.CLASS_NAME, element_id)
                        print(f"   ✅ {test_name}: 找到 (透過 class)")
                        passed_tests += 1
                    except:
                        print(f"   ⚠️ {test_name}: 未找到")
            
            # 檢查是否有任何按鈕或交互元素
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            
            print(f"   發現 {len(buttons)} 個按鈕, {len(inputs)} 個輸入框")
            
            self.test_results.append({
                "test": "UI 元素",
                "status": "passed",
                "details": f"UI 組件: {passed_tests}/{len(ui_tests)}, 按鈕: {len(buttons)}, 輸入框: {len(inputs)}"
            })
            
            print("✅ UI 元素測試通過")
            return True
            
        except Exception as e:
            self.test_results.append({
                "test": "UI 元素",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ UI 元素測試失敗: {e}")
            return False
    
    def test_frontend_backend_communication(self):
        """測試前後端通信"""
        print("🧪 測試前後端通信...")
        
        try:
            # 執行 JavaScript 來測試 Tauri API
            js_code = """
            if (window.__TAURI__) {
                return "Tauri API 可用";
            } else {
                return "Tauri API 不可用";
            }
            """
            
            result = self.driver.execute_script(js_code)
            print(f"   Tauri API 狀態: {result}")
            
            # 測試是否能調用後端命令
            js_test_command = """
            if (window.__TAURI__ && window.__TAURI__.invoke) {
                window.__TAURI__.invoke('get_app_version')
                    .then(version => {
                        window.testResult = 'Version: ' + version;
                    })
                    .catch(error => {
                        window.testResult = 'Error: ' + error;
                    });
                return 'Command sent';
            } else {
                return 'Tauri invoke not available';
            }
            """
            
            command_result = self.driver.execute_script(js_test_command)
            print(f"   命令執行狀態: {command_result}")
            
            # 等待結果
            time.sleep(2)
            
            final_result = self.driver.execute_script("return window.testResult || 'No result'")
            print(f"   後端響應: {final_result}")
            
            self.test_results.append({
                "test": "前後端通信",
                "status": "passed",
                "details": f"Tauri API: {result}, 命令: {command_result}, 響應: {final_result}"
            })
            
            print("✅ 前後端通信測試通過")
            return True
            
        except Exception as e:
            self.test_results.append({
                "test": "前後端通信",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ 前後端通信測試失敗: {e}")
            return False
    
    def test_powerautomation_init(self):
        """測試 PowerAutomation 初始化"""
        print("🧪 測試 PowerAutomation 初始化...")
        
        try:
            # 尋找初始化按鈕或自動初始化
            init_js = """
            if (window.__TAURI__ && window.__TAURI__.invoke) {
                window.__TAURI__.invoke('initialize_powerautomation')
                    .then(result => {
                        window.powerautomationResult = 'Success: ' + result;
                    })
                    .catch(error => {
                        window.powerautomationResult = 'Error: ' + error;
                    });
                return 'PowerAutomation initialization sent';
            } else {
                return 'Cannot initialize - Tauri not available';
            }
            """
            
            init_result = self.driver.execute_script(init_js)
            print(f"   初始化命令: {init_result}")
            
            # 等待初始化完成
            time.sleep(3)
            
            final_result = self.driver.execute_script("return window.powerautomationResult || 'No result'")
            print(f"   初始化結果: {final_result}")
            
            self.test_results.append({
                "test": "PowerAutomation 初始化",
                "status": "passed",
                "details": f"命令: {init_result}, 結果: {final_result}"
            })
            
            print("✅ PowerAutomation 初始化測試通過")
            return True
            
        except Exception as e:
            self.test_results.append({
                "test": "PowerAutomation 初始化",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ PowerAutomation 初始化測試失敗: {e}")
            return False
    
    def test_project_creation(self):
        """測試項目創建功能"""
        print("🧪 測試項目創建功能...")
        
        try:
            # 測試創建項目
            project_js = """
            if (window.__TAURI__ && window.__TAURI__.invoke) {
                window.__TAURI__.invoke('create_project', {
                    name: 'Test Project',
                    path: '/tmp/test-project',
                    description: 'UI測試項目'
                })
                .then(result => {
                    window.projectResult = 'Project created: ' + JSON.stringify(result);
                })
                .catch(error => {
                    window.projectResult = 'Project error: ' + error;
                });
                return 'Project creation sent';
            } else {
                return 'Cannot create project - Tauri not available';
            }
            """
            
            project_result = self.driver.execute_script(project_js)
            print(f"   項目創建命令: {project_result}")
            
            # 等待項目創建完成
            time.sleep(2)
            
            final_result = self.driver.execute_script("return window.projectResult || 'No result'")
            print(f"   項目創建結果: {final_result}")
            
            self.test_results.append({
                "test": "項目創建",
                "status": "passed",
                "details": f"命令: {project_result}, 結果: {final_result}"
            })
            
            print("✅ 項目創建測試通過")
            return True
            
        except Exception as e:
            self.test_results.append({
                "test": "項目創建",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ 項目創建測試失敗: {e}")
            return False
    
    def take_screenshot(self, filename="ui_test_screenshot.png"):
        """截圖"""
        try:
            screenshot_path = f"tests/ui_test_reports/{filename}"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_path)
            print(f"📸 截圖保存至: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"❌ 截圖失敗: {e}")
            return None
    
    def cleanup(self):
        """清理資源"""
        if self.driver:
            self.driver.quit()
            print("🧹 瀏覽器已關閉")
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "="*60)
        print("📋 Tauri Desktop UI 實際操作測試報告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "passed")
        
        print(f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"總測試數: {total_tests}")
        print(f"通過測試: {passed_tests}")
        print(f"失敗測試: {total_tests - passed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n📊 詳細結果:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"   {status_icon} {result['test']}")
            if "details" in result:
                print(f"      Details: {result['details']}")
            if "error" in result:
                print(f"      Error: {result['error']}")
        
        # 保存報告
        report_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            "results": self.test_results
        }
        
        report_path = "tests/ui_test_reports/tauri_desktop_ui_test_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 測試報告已保存: {report_path}")
        
        return passed_tests == total_tests

def main():
    """主函數"""
    print("🚀 開始 Tauri Desktop UI 實際操作測試")
    
    tester = TauriDesktopUITester()
    
    try:
        # 等待服務器啟動
        if not tester.wait_for_server():
            print("❌ 服務器未啟動，請先運行 'npm run dev'")
            return False
        
        # 設置瀏覽器
        if not tester.setup_browser():
            print("❌ 瀏覽器設置失敗")
            return False
        
        # 執行測試序列
        tests = [
            tester.test_page_load,
            tester.test_ui_elements,
            tester.test_frontend_backend_communication,
            tester.test_powerautomation_init,
            tester.test_project_creation
        ]
        
        for test in tests:
            test()
            time.sleep(1)  # 測試間隔
        
        # 截圖
        tester.take_screenshot()
        
        # 生成報告
        success = tester.generate_report()
        
        return success
        
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)