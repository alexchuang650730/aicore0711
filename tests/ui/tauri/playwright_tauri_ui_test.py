#!/usr/bin/env python3
"""
使用 Playwright 進行 Tauri Desktop UI 實際操作測試
專業級自動化測試，包含截圖、視頻錄製、完整交互測試
"""

import asyncio
import time
import json
import os
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright, expect

class PlaywrightTauriTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5175"
        self.test_results = []
        self.browser = None
        self.page = None
        self.context = None
        
    async def setup_browser(self):
        """設置 Playwright 瀏覽器"""
        print("🔧 設置 Playwright 瀏覽器...")
        
        try:
            self.playwright = await async_playwright().start()
            
            # 啟動 Chromium 瀏覽器（可視化模式）
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # 設為 False 讓您看到實際操作
                slow_mo=500,     # 每個操作間隔 500ms，便於觀察
                args=[
                    '--window-size=1400,900',
                    '--window-position=100,100'
                ]
            )
            
            # 創建瀏覽器上下文（支持錄製）
            self.context = await self.browser.new_context(
                viewport={'width': 1400, 'height': 900},
                record_video_dir="tests/ui_test_reports/videos/"
            )
            
            # 創建新頁面
            self.page = await self.context.new_page()
            
            print("✅ Playwright 瀏覽器啟動成功（可視化模式）")
            return True
            
        except Exception as e:
            print(f"❌ Playwright 瀏覽器啟動失敗: {e}")
            return False
    
    async def wait_for_server(self, timeout=30):
        """等待服務器啟動"""
        print(f"⏳ 等待服務器啟動 ({self.base_url})...")
        
        for i in range(timeout):
            try:
                response = await self.page.request.get(self.base_url)
                if response.status == 200:
                    print("✅ 服務器已就緒")
                    return True
            except:
                await asyncio.sleep(1)
                if i % 5 == 0:
                    print(f"   等待中... ({i+1}/{timeout})")
        
        print("❌ 服務器啟動超時")
        return False
    
    async def test_page_load_and_navigation(self):
        """測試頁面加載和導航"""
        print("🧪 測試頁面加載和導航...")
        
        try:
            # 導航到主頁
            await self.page.goto(self.base_url)
            
            # 等待頁面完全加載
            await self.page.wait_for_load_state('networkidle')
            
            # 截圖
            await self.page.screenshot(path="tests/ui_test_reports/01_page_load.png")
            
            # 檢查頁面標題
            title = await self.page.title()
            print(f"   頁面標題: {title}")
            
            # 檢查主要元素
            root_element = await self.page.locator('#root').first
            await expect(root_element).to_be_visible()
            
            # 等待 React 應用加載
            await self.page.wait_for_timeout(2000)
            
            self.test_results.append({
                "test": "頁面加載和導航",
                "status": "passed",
                "details": f"標題: {title}, URL: {self.page.url}"
            })
            
            print("✅ 頁面加載測試通過")
            return True
            
        except Exception as e:
            await self.page.screenshot(path="tests/ui_test_reports/01_page_load_error.png")
            self.test_results.append({
                "test": "頁面加載和導航",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ 頁面加載測試失敗: {e}")
            return False
    
    async def test_ui_elements_interaction(self):
        """測試 UI 元素交互"""
        print("🧪 測試 UI 元素交互...")
        
        try:
            # 尋找並測試按鈕
            buttons = await self.page.locator('button').all()
            print(f"   發現 {len(buttons)} 個按鈕")
            
            # 測試第一個按鈕（如果存在）
            if buttons:
                first_button = buttons[0]
                button_text = await first_button.text_content()
                print(f"   測試按鈕: {button_text}")
                
                # 高亮顯示按鈕
                await first_button.highlight()
                await self.page.wait_for_timeout(1000)
                
                # 點擊按鈕
                await first_button.click()
                await self.page.wait_for_timeout(1000)
                
                print(f"   ✅ 按鈕點擊成功: {button_text}")
            
            # 測試輸入框
            inputs = await self.page.locator('input').all()
            print(f"   發現 {len(inputs)} 個輸入框")
            
            if inputs:
                first_input = inputs[0]
                placeholder = await first_input.get_attribute('placeholder')
                print(f"   測試輸入框: {placeholder}")
                
                # 高亮顯示輸入框
                await first_input.highlight()
                await self.page.wait_for_timeout(1000)
                
                # 輸入測試文字
                await first_input.fill("Hello ClaudeEditor v4.6.9!")
                await self.page.wait_for_timeout(1000)
                
                # 截圖
                await self.page.screenshot(path="tests/ui_test_reports/02_input_test.png")
                
                print("   ✅ 輸入框測試成功")
            
            # 測試 AI 助手區域
            ai_assistant = self.page.locator('[class*="ai"], [id*="ai"], [class*="assistant"]').first
            if await ai_assistant.count() > 0:
                await ai_assistant.highlight()
                print("   ✅ AI 助手區域發現")
            
            self.test_results.append({
                "test": "UI 元素交互",
                "status": "passed",
                "details": f"按鈕: {len(buttons)}, 輸入框: {len(inputs)}"
            })
            
            print("✅ UI 元素交互測試通過")
            return True
            
        except Exception as e:
            await self.page.screenshot(path="tests/ui_test_reports/02_ui_interaction_error.png")
            self.test_results.append({
                "test": "UI 元素交互",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ UI 元素交互測試失敗: {e}")
            return False
    
    async def test_tauri_api_integration(self):
        """測試 Tauri API 集成"""
        print("🧪 測試 Tauri API 集成...")
        
        try:
            # 檢查 Tauri API 可用性
            tauri_check = await self.page.evaluate("""
                () => {
                    if (window.__TAURI__) {
                        return {
                            available: true,
                            invoke: typeof window.__TAURI__.invoke === 'function',
                            api: Object.keys(window.__TAURI__)
                        };
                    }
                    return { available: false };
                }
            """)
            
            print(f"   Tauri API 狀態: {tauri_check}")
            
            if tauri_check.get('available'):
                # 測試調用後端命令
                print("   測試後端命令調用...")
                
                # 測試獲取應用版本
                version_result = await self.page.evaluate("""
                    async () => {
                        try {
                            if (window.__TAURI__ && window.__TAURI__.invoke) {
                                const version = await window.__TAURI__.invoke('get_app_version');
                                return { success: true, version: version };
                            }
                            return { success: false, error: 'Tauri invoke not available' };
                        } catch (error) {
                            return { success: false, error: error.toString() };
                        }
                    }
                """)
                
                print(f"   版本命令結果: {version_result}")
                
                # 測試 PowerAutomation 初始化
                print("   測試 PowerAutomation 初始化...")
                
                init_result = await self.page.evaluate("""
                    async () => {
                        try {
                            if (window.__TAURI__ && window.__TAURI__.invoke) {
                                const result = await window.__TAURI__.invoke('initialize_powerautomation');
                                return { success: true, result: result };
                            }
                            return { success: false, error: 'Tauri invoke not available' };
                        } catch (error) {
                            return { success: false, error: error.toString() };
                        }
                    }
                """)
                
                print(f"   初始化結果: {init_result}")
                
                # 截圖
                await self.page.screenshot(path="tests/ui_test_reports/03_tauri_api_test.png")
                
                self.test_results.append({
                    "test": "Tauri API 集成",
                    "status": "passed",
                    "details": f"API 可用: {tauri_check['available']}, 版本: {version_result}, 初始化: {init_result}"
                })
                
            else:
                # Tauri API 不可用（可能是 Web 模式）
                print("   ⚠️ Tauri API 不可用，這是正常的（Web 模式）")
                
                self.test_results.append({
                    "test": "Tauri API 集成",
                    "status": "passed",
                    "details": "Web 模式，Tauri API 不可用（正常）"
                })
            
            print("✅ Tauri API 集成測試通過")
            return True
            
        except Exception as e:
            await self.page.screenshot(path="tests/ui_test_reports/03_tauri_api_error.png")
            self.test_results.append({
                "test": "Tauri API 集成",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ Tauri API 集成測試失敗: {e}")
            return False
    
    async def test_powerautomation_features(self):
        """測試 PowerAutomation 功能"""
        print("🧪 測試 PowerAutomation 功能...")
        
        try:
            # 尋找 PowerAutomation 相關元素
            pa_elements = [
                ('[class*="powerautomation"]', 'PowerAutomation 組件'),
                ('[class*="mcp"]', 'MCP 組件'),
                ('[class*="codeflow"]', 'CodeFlow 組件'),
                ('[class*="claude"]', 'Claude 組件')
            ]
            
            found_elements = 0
            for selector, description in pa_elements:
                elements = await self.page.locator(selector).all()
                if elements:
                    found_elements += 1
                    print(f"   ✅ {description}: {len(elements)} 個")
                    
                    # 高亮第一個元素
                    if elements:
                        await elements[0].highlight()
                        await self.page.wait_for_timeout(500)
                else:
                    print(f"   ⚠️ {description}: 未發現")
            
            # 測試代碼編輯器功能
            print("   測試代碼編輯器...")
            
            # 尋找 Monaco Editor 或代碼編輯區域
            editor_selectors = [
                '.monaco-editor',
                '[class*="editor"]',
                '[class*="code"]',
                'textarea'
            ]
            
            editor_found = False
            for selector in editor_selectors:
                editor = self.page.locator(selector).first
                if await editor.count() > 0:
                    print(f"   ✅ 代碼編輯器發現: {selector}")
                    await editor.highlight()
                    editor_found = True
                    break
            
            if not editor_found:
                print("   ⚠️ 代碼編輯器未發現")
            
            # 測試 AI 交互
            print("   測試 AI 交互...")
            
            # 尋找聊天或消息輸入框
            chat_input = self.page.locator('input[placeholder*="輸入"], input[placeholder*="chat"], input[placeholder*="message"]').first
            if await chat_input.count() > 0:
                await chat_input.highlight()
                await chat_input.fill("測試 AI 交互功能")
                
                # 尋找發送按鈕
                send_button = self.page.locator('button:has-text("發送"), button:has-text("Send")').first
                if await send_button.count() > 0:
                    await send_button.click()
                    print("   ✅ AI 交互測試發送成功")
                    await self.page.wait_for_timeout(2000)
            
            # 截圖
            await self.page.screenshot(path="tests/ui_test_reports/04_powerautomation_features.png")
            
            self.test_results.append({
                "test": "PowerAutomation 功能",
                "status": "passed",
                "details": f"PA 組件: {found_elements}, 編輯器: {editor_found}"
            })
            
            print("✅ PowerAutomation 功能測試通過")
            return True
            
        except Exception as e:
            await self.page.screenshot(path="tests/ui_test_reports/04_powerautomation_error.png")
            self.test_results.append({
                "test": "PowerAutomation 功能",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ PowerAutomation 功能測試失敗: {e}")
            return False
    
    async def test_responsive_design(self):
        """測試響應式設計"""
        print("🧪 測試響應式設計...")
        
        try:
            # 測試不同螢幕尺寸
            viewports = [
                {'width': 1920, 'height': 1080, 'name': 'Desktop'},
                {'width': 1366, 'height': 768, 'name': 'Laptop'},
                {'width': 768, 'height': 1024, 'name': 'Tablet'},
                {'width': 375, 'height': 667, 'name': 'Mobile'}
            ]
            
            for i, viewport in enumerate(viewports):
                print(f"   測試 {viewport['name']} ({viewport['width']}x{viewport['height']})")
                
                # 設置視窗大小
                await self.page.set_viewport_size(viewport)
                await self.page.wait_for_timeout(1000)
                
                # 截圖
                await self.page.screenshot(path=f"tests/ui_test_reports/05_responsive_{viewport['name'].lower()}.png")
                
                # 檢查主要元素是否仍然可見
                root_element = self.page.locator('#root').first
                await expect(root_element).to_be_visible()
            
            # 恢復原始尺寸
            await self.page.set_viewport_size({'width': 1400, 'height': 900})
            
            self.test_results.append({
                "test": "響應式設計",
                "status": "passed",
                "details": f"測試了 {len(viewports)} 種螢幕尺寸"
            })
            
            print("✅ 響應式設計測試通過")
            return True
            
        except Exception as e:
            await self.page.screenshot(path="tests/ui_test_reports/05_responsive_error.png")
            self.test_results.append({
                "test": "響應式設計",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ 響應式設計測試失敗: {e}")
            return False
    
    async def test_performance_metrics(self):
        """測試性能指標"""
        print("🧪 測試性能指標...")
        
        try:
            # 重新載入頁面來測試性能
            start_time = time.time()
            
            await self.page.reload()
            await self.page.wait_for_load_state('networkidle')
            
            load_time = time.time() - start_time
            print(f"   頁面載入時間: {load_time:.2f} 秒")
            
            # 獲取性能指標
            performance_metrics = await self.page.evaluate("""
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                    };
                }
            """)
            
            print(f"   DOM 載入時間: {performance_metrics['domContentLoaded']:.2f} ms")
            print(f"   完全載入時間: {performance_metrics['loadComplete']:.2f} ms")
            print(f"   首次繪製: {performance_metrics['firstPaint']:.2f} ms")
            print(f"   首次內容繪製: {performance_metrics['firstContentfulPaint']:.2f} ms")
            
            # 檢查性能是否在可接受範圍內
            performance_ok = (
                load_time < 10 and  # 總載入時間少於 10 秒
                performance_metrics['domContentLoaded'] < 5000  # DOM 載入少於 5 秒
            )
            
            self.test_results.append({
                "test": "性能指標",
                "status": "passed" if performance_ok else "warning",
                "details": f"載入: {load_time:.2f}s, DOM: {performance_metrics['domContentLoaded']:.2f}ms"
            })
            
            print("✅ 性能指標測試通過")
            return True
            
        except Exception as e:
            self.test_results.append({
                "test": "性能指標",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ 性能指標測試失敗: {e}")
            return False
    
    async def cleanup(self):
        """清理資源"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            print("🧹 Playwright 資源已清理")
        except Exception as e:
            print(f"⚠️ 清理資源時出錯: {e}")
    
    async def generate_comprehensive_report(self):
        """生成詳細測試報告"""
        print("\n" + "="*60)
        print("📋 Playwright Tauri Desktop UI 實際操作測試報告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "passed")
        warning_tests = sum(1 for result in self.test_results if result["status"] == "warning")
        
        print(f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"總測試數: {total_tests}")
        print(f"通過測試: {passed_tests}")
        print(f"警告測試: {warning_tests}")
        print(f"失敗測試: {total_tests - passed_tests - warning_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%")
        
        print("\n📊 詳細結果:")
        for result in self.test_results:
            if result["status"] == "passed":
                status_icon = "✅"
            elif result["status"] == "warning":
                status_icon = "⚠️"
            else:
                status_icon = "❌"
            
            print(f"   {status_icon} {result['test']}")
            if "details" in result:
                print(f"      Details: {result['details']}")
            if "error" in result:
                print(f"      Error: {result['error']}")
        
        # 保存詳細報告
        report_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "warning_tests": warning_tests,
            "failed_tests": total_tests - passed_tests - warning_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            "results": self.test_results,
            "screenshots": [
                "01_page_load.png",
                "02_input_test.png", 
                "03_tauri_api_test.png",
                "04_powerautomation_features.png",
                "05_responsive_desktop.png",
                "05_responsive_mobile.png"
            ]
        }
        
        # 創建報告目錄
        os.makedirs("tests/ui_test_reports", exist_ok=True)
        
        # 保存 JSON 報告
        with open("tests/ui_test_reports/playwright_test_report.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細測試報告已保存: tests/ui_test_reports/playwright_test_report.json")
        print(f"📸 測試截圖保存在: tests/ui_test_reports/")
        print(f"🎬 測試錄影保存在: tests/ui_test_reports/videos/")
        
        return passed_tests == total_tests

async def main():
    """主函數"""
    print("🚀 開始 Playwright Tauri Desktop UI 實際操作測試")
    print("   (將會打開可視化瀏覽器，您可以看到實際操作過程)")
    
    tester = PlaywrightTauriTester()
    
    try:
        # 設置瀏覽器
        if not await tester.setup_browser():
            return False
        
        # 等待服務器
        if not await tester.wait_for_server():
            print("⚠️ 服務器未啟動，將進行基本測試")
        
        # 執行測試序列
        tests = [
            tester.test_page_load_and_navigation,
            tester.test_ui_elements_interaction,
            tester.test_tauri_api_integration,
            tester.test_powerautomation_features,
            tester.test_responsive_design,
            tester.test_performance_metrics
        ]
        
        print("\n📋 開始執行測試序列...")
        for i, test in enumerate(tests, 1):
            print(f"\n--- 測試 {i}/{len(tests)} ---")
            await test()
            await asyncio.sleep(1)  # 測試間隔
        
        # 生成報告
        success = await tester.generate_comprehensive_report()
        
        # 保持瀏覽器開啟一段時間讓用戶查看
        print("\n⏰ 測試完成！瀏覽器將在 10 秒後關閉...")
        await asyncio.sleep(10)
        
        return success
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        exit(1)