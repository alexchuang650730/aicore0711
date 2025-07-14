#!/usr/bin/env python3
"""
ClaudEditor + Kimi K2 整合測試運行器
執行完整的集成測試、API測試、UI測試
"""

import asyncio
import subprocess
import sys
import os
import time
import logging
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestRunner:
    """測試運行器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        self.start_time = time.time()
        
    def check_server_availability(self) -> bool:
        """檢查服務器是否可用"""
        import requests
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_server(self, timeout: int = 30) -> bool:
        """等待服務器啟動"""
        logger.info(f"等待服務器啟動 {self.base_url}")
        
        for i in range(timeout):
            if self.check_server_availability():
                logger.info("✅ 服務器已就緒")
                return True
            time.sleep(1)
            if i % 5 == 0:
                logger.info(f"⏳ 等待中... ({i}/{timeout}s)")
        
        logger.error("❌ 服務器啟動超時")
        return False
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """運行集成測試"""
        logger.info("🔧 開始運行後端集成測試")
        
        try:
            # 導入並運行集成測試
            from test_kimi_k2_integration import KimiK2IntegrationTester
            
            tester = KimiK2IntegrationTester(base_url=self.base_url)
            results = await tester.run_all_tests()
            
            return {
                "success": True,
                "results": [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "message": r.message,
                        "execution_time": r.execution_time
                    } for r in results
                ],
                "summary": {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.success),
                    "failed": sum(1 for r in results if not r.success)
                }
            }
            
        except Exception as e:
            logger.error(f"集成測試運行失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_ui_tests(self, headless: bool = True, use_playwright: bool = True) -> Dict[str, Any]:
        """運行UI測試"""
        logger.info("🎭 開始運行UI自動化測試")
        
        if use_playwright:
            return await self.run_playwright_ui_tests(headless)
        else:
            return self.run_selenium_ui_tests(headless)
    
    async def run_playwright_ui_tests(self, headless: bool = True) -> Dict[str, Any]:
        """運行Playwright UI測試"""
        try:
            # 檢查Playwright依賴
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                logger.warning("⚠️  Playwright未安裝，嘗試安裝...")
                subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                logger.info("✅ Playwright安裝完成")
            
            # 運行Playwright UI測試
            from test_playwright_ui import PlaywrightUITester
            
            tester = PlaywrightUITester(base_url=self.base_url, headless=headless)
            results = await tester.run_all_ui_tests()
            
            return {
                "success": True,
                "framework": "Playwright",
                "results": [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "message": r.message,
                        "execution_time": r.execution_time,
                        "screenshot": r.screenshot_path,
                        "video": r.video_path,
                        "details": r.details
                    } for r in results
                ],
                "summary": {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.success),
                    "failed": sum(1 for r in results if not r.success)
                }
            }
            
        except Exception as e:
            logger.error(f"Playwright UI測試運行失敗: {e}")
            return {
                "success": False,
                "framework": "Playwright",
                "error": str(e)
            }
    
    def run_selenium_ui_tests(self, headless: bool = True) -> Dict[str, Any]:
        """運行Selenium UI測試（備用）"""
        try:
            # 檢查selenium依賴
            try:
                import selenium
            except ImportError:
                logger.warning("⚠️  Selenium未安裝，跳過UI測試")
                return {
                    "success": False,
                    "framework": "Selenium",
                    "error": "Selenium not installed",
                    "skipped": True
                }
            
            # 運行UI測試
            from test_ui_automation import ClaudEditorUITester
            
            tester = ClaudEditorUITester(base_url=self.base_url, headless=headless)
            results = tester.run_all_ui_tests()
            
            return {
                "success": True,
                "framework": "Selenium",
                "results": [
                    {
                        "test_name": r.test_name,
                        "success": r.success,
                        "message": r.message,
                        "execution_time": r.execution_time,
                        "screenshot": r.screenshot_path
                    } for r in results
                ],
                "summary": {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.success),
                    "failed": sum(1 for r in results if not r.success)
                }
            }
            
        except Exception as e:
            logger.error(f"Selenium UI測試運行失敗: {e}")
            return {
                "success": False,
                "framework": "Selenium",
                "error": str(e)
            }
    
    def run_manual_tests(self) -> Dict[str, Any]:
        """運行手動測試清單"""
        logger.info("📋 生成手動測試清單")
        
        manual_tests = {
            "功能測試": [
                "✅ 在瀏覽器中打開 ClaudEditor",
                "✅ 檢查頁面是否正常載入",
                "✅ 測試全局模型選擇器切換 Claude → Kimi K2",
                "✅ 檢查模型狀態指示器變化",
                "✅ 在AI助手面板測試模型選擇器",
                "✅ 打開模型參數面板，調整Temperature和Top-P",
                "✅ 發送測試消息給Claude模型",
                "✅ 切換到Kimi K2並發送中文測試消息",
                "✅ 測試模型對比功能（同時詢問Claude和Kimi K2）",
                "✅ 檢查通知系統是否顯示模型切換消息"
            ],
            "交互測試": [
                "✅ 測試滑鼠點擊各個UI元素",
                "✅ 測試鍵盤Tab導航",
                "✅ 測試Enter鍵發送消息",
                "✅ 測試複製最後回應功能",
                "✅ 測試清空聊天功能",
                "✅ 測試參數滑桿調節",
                "✅ 測試窗口大小調整（響應式）"
            ],
            "錯誤處理測試": [
                "✅ 測試網絡中斷時的錯誤處理",
                "✅ 測試發送空消息的處理",
                "✅ 測試極長消息的處理",
                "✅ 測試無效參數值的處理",
                "✅ 測試模型不可用時的提示"
            ],
            "性能測試": [
                "✅ 測試連續發送多條消息",
                "✅ 測試長時間對話的響應速度",
                "✅ 測試多個標籤頁同時使用",
                "✅ 測試內存使用情況",
                "✅ 測試瀏覽器兼容性（Chrome, Firefox, Safari）"
            ]
        }
        
        return {
            "success": True,
            "manual_tests": manual_tests,
            "instructions": "請按照上述清單手動測試各項功能"
        }
    
    def generate_test_report(self) -> str:
        """生成完整測試報告"""
        total_time = time.time() - self.start_time
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_execution_time": f"{total_time:.2f}s",
            "server_url": self.base_url,
            "test_results": self.test_results,
            "summary": self.calculate_overall_summary()
        }
        
        # 保存JSON報告
        report_path = f"test_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report_path
    
    def calculate_overall_summary(self) -> Dict[str, Any]:
        """計算總體摘要"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for test_type, results in self.test_results.items():
            if "summary" in results:
                summary = results["summary"]
                total_tests += summary.get("total", 0)
                total_passed += summary.get("passed", 0)
                total_failed += summary.get("failed", 0)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "success_rate": f"{success_rate:.1f}%",
            "overall_status": "PASS" if success_rate >= 80 else "FAIL"
        }
    
    def print_summary(self):
        """打印測試摘要"""
        summary = self.calculate_overall_summary()
        
        print("\n" + "="*80)
        print("🎯 ClaudEditor + Kimi K2 整合測試總結")
        print("="*80)
        print(f"📊 總測試數: {summary['total_tests']}")
        print(f"✅ 通過: {summary['passed']}")
        print(f"❌ 失敗: {summary['failed']}")
        print(f"📈 成功率: {summary['success_rate']}")
        print(f"🏆 整體狀態: {summary['overall_status']}")
        print("="*80)
        
        # 詳細結果
        for test_type, results in self.test_results.items():
            if results.get("success"):
                status = "✅"
                summary_info = results.get("summary", {})
                detail = f"({summary_info.get('passed', 0)}/{summary_info.get('total', 0)} 通過)"
            elif results.get("skipped"):
                status = "⏭️"
                detail = "(已跳過)"
            else:
                status = "❌"
                detail = f"(錯誤: {results.get('error', 'Unknown')})"
            
            print(f"{status} {test_type} {detail}")
        
        print("\n" + "="*80)
        
        if summary['overall_status'] == 'PASS':
            print("🎉 恭喜！ClaudEditor + Kimi K2 整合測試通過！")
            print("📱 你現在可以在ClaudEditor中使用Claude和Kimi K2模型了")
        else:
            print("⚠️  測試未完全通過，請檢查失敗的測試項目")
        
        print("="*80)
    
    async def run_all_tests(self, include_ui: bool = True, headless: bool = True, use_playwright: bool = True):
        """運行所有測試"""
        logger.info("🚀 開始運行ClaudEditor + Kimi K2完整測試套件")
        
        # 檢查服務器
        if not self.wait_for_server():
            logger.error("❌ 服務器不可用，無法運行測試")
            return False
        
        # 1. 運行集成測試
        logger.info("1️⃣ 運行後端集成測試...")
        self.test_results["集成測試"] = await self.run_integration_tests()
        
        # 2. 運行UI測試
        if include_ui:
            framework = "Playwright" if use_playwright else "Selenium"
            logger.info(f"2️⃣ 運行{framework} UI自動化測試...")
            self.test_results["UI測試"] = await self.run_ui_tests(headless=headless, use_playwright=use_playwright)
        else:
            logger.info("⏭️ 跳過UI測試")
        
        # 3. 生成手動測試清單
        logger.info("3️⃣ 生成手動測試清單...")
        self.test_results["手動測試"] = self.run_manual_tests()
        
        # 生成報告
        report_path = self.generate_test_report()
        logger.info(f"📄 測試報告已保存: {report_path}")
        
        # 打印摘要
        self.print_summary()
        
        # 返回整體成功狀態
        summary = self.calculate_overall_summary()
        return summary['overall_status'] == 'PASS'


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="ClaudEditor + Kimi K2 完整測試套件")
    parser.add_argument("--url", default="http://localhost:8000", help="服務器URL")
    parser.add_argument("--no-ui", action="store_true", help="跳過UI測試")
    parser.add_argument("--no-headless", action="store_true", help="UI測試不使用無頭模式")
    parser.add_argument("--use-selenium", action="store_true", help="使用Selenium而不是Playwright")
    parser.add_argument("--verbose", action="store_true", help="詳細輸出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 創建必要的目錄
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("videos", exist_ok=True)
    os.makedirs("test_reports", exist_ok=True)
    
    # 運行測試
    runner = TestRunner(base_url=args.url)
    success = await runner.run_all_tests(
        include_ui=not args.no_ui,
        headless=not args.no_headless,
        use_playwright=not args.use_selenium
    )
    
    # 退出碼
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 測試運行失敗: {e}")
        sys.exit(1)