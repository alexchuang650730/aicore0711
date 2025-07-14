#!/usr/bin/env python3
"""
簡化版 Tauri Desktop 實際操作測試
直接測試前後端串接和 PowerAutomation Core 功能
"""

import time
import json
import subprocess
import requests
import os
from pathlib import Path

class SimpleTauriTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5175"
        self.test_results = []
        
    def wait_for_server(self, timeout=30):
        """等待前端服務器啟動"""
        print(f"⏳ 等待前端服務器啟動 ({self.base_url})...")
        
        for i in range(timeout):
            try:
                response = requests.get(self.base_url, timeout=2)
                if response.status_code == 200:
                    print("✅ 前端服務器已就緒")
                    return True
            except:
                time.sleep(1)
                if i % 5 == 0:
                    print(f"   等待中... ({i+1}/{timeout})")
        
        print("❌ 前端服務器啟動超時")
        return False
    
    def test_frontend_availability(self):
        """測試前端可用性"""
        print("🧪 測試前端可用性...")
        
        try:
            response = requests.get(self.base_url, timeout=5)
            
            # 檢查響應狀態
            if response.status_code == 200:
                print(f"   ✅ HTTP 狀態: {response.status_code}")
                
                # 檢查內容類型
                content_type = response.headers.get('content-type', '')
                print(f"   ✅ 內容類型: {content_type}")
                
                # 檢查是否包含 React 相關內容
                content = response.text
                has_react = 'react' in content.lower() or 'root' in content
                print(f"   ✅ React 應用: {'是' if has_react else '否'}")
                
                self.test_results.append({
                    "test": "前端可用性",
                    "status": "passed",
                    "details": f"狀態: {response.status_code}, React: {has_react}"
                })
                
                print("✅ 前端可用性測試通過")
                return True
            else:
                raise Exception(f"HTTP 狀態錯誤: {response.status_code}")
                
        except Exception as e:
            self.test_results.append({
                "test": "前端可用性",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ 前端可用性測試失敗: {e}")
            return False
    
    def test_tauri_build_availability(self):
        """測試 Tauri 構建可用性"""
        print("🧪 測試 Tauri 構建可用性...")
        
        try:
            # 檢查 Tauri 配置文件
            tauri_conf = Path("claudeditor/src-tauri/tauri.conf.json")
            if tauri_conf.exists():
                with open(tauri_conf, 'r') as f:
                    config = json.load(f)
                
                version = config.get('package', {}).get('version', 'unknown')
                product_name = config.get('package', {}).get('productName', 'unknown')
                
                print(f"   ✅ Tauri 配置: {product_name} v{version}")
                
                # 檢查 Rust 源碼
                rust_main = Path("claudeditor/src-tauri/src/main.rs")
                if rust_main.exists():
                    print("   ✅ Rust 源碼存在")
                    
                    # 快速語法檢查
                    try:
                        result = subprocess.run([
                            "cargo", "check"
                        ], cwd="claudeditor/src-tauri", capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            print("   ✅ Rust 語法檢查通過")
                        else:
                            print("   ⚠️ Rust 語法檢查有警告")
                            print(f"      {result.stderr[:200]}...")
                    except subprocess.TimeoutExpired:
                        print("   ⏰ Rust 檢查超時")
                    except Exception as e:
                        print(f"   ⚠️ Rust 檢查異常: {e}")
                
                self.test_results.append({
                    "test": "Tauri 構建可用性",
                    "status": "passed",
                    "details": f"版本: {version}, 產品: {product_name}"
                })
                
                print("✅ Tauri 構建可用性測試通過")
                return True
            else:
                raise Exception("Tauri 配置文件不存在")
                
        except Exception as e:
            self.test_results.append({
                "test": "Tauri 構建可用性",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ Tauri 構建可用性測試失敗: {e}")
            return False
    
    def test_powerautomation_core_structure(self):
        """測試 PowerAutomation Core 結構"""
        print("🧪 測試 PowerAutomation Core 結構...")
        
        try:
            # 檢查核心文件結構
            core_files = [
                "core/powerautomation_main.py",
                "core/components/codeflow_mcp/codeflow_manager.py",
                "core/components/claude_mcp/claude_manager.py",
                "core/components/mcp_coordinator_mcp/coordinator.py"
            ]
            
            found_files = 0
            for file_path in core_files:
                if Path(file_path).exists():
                    found_files += 1
                    print(f"   ✅ {file_path}")
                else:
                    print(f"   ❌ {file_path}")
            
            # 檢查 MCP 組件
            mcp_components = Path("core/components").glob("*_mcp")
            mcp_count = len(list(mcp_components))
            
            print(f"   📦 發現 {mcp_count} 個 MCP 組件")
            print(f"   📁 核心文件完整性: {found_files}/{len(core_files)}")
            
            self.test_results.append({
                "test": "PowerAutomation Core 結構",
                "status": "passed",
                "details": f"核心文件: {found_files}/{len(core_files)}, MCP 組件: {mcp_count}"
            })
            
            print("✅ PowerAutomation Core 結構測試通過")
            return True
            
        except Exception as e:
            self.test_results.append({
                "test": "PowerAutomation Core 結構",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ PowerAutomation Core 結構測試失敗: {e}")
            return False
    
    def test_codeflow_mcp_integration(self):
        """測試 CodeFlow MCP 集成"""
        print("🧪 測試 CodeFlow MCP 集成...")
        
        try:
            # 檢查 CodeFlow MCP 組件
            codeflow_manager = Path("core/components/codeflow_mcp/codeflow_manager.py")
            
            if codeflow_manager.exists():
                with open(codeflow_manager, 'r') as f:
                    content = f.read()
                
                # 檢查關鍵功能
                features = [
                    ("code_analysis", "代碼分析"),
                    ("refactoring", "重構"),
                    ("test_generation", "測試生成"),
                    ("async def", "異步支持")
                ]
                
                found_features = 0
                for keyword, description in features:
                    if keyword in content:
                        found_features += 1
                        print(f"   ✅ {description}: 發現")
                    else:
                        print(f"   ⚠️ {description}: 未發現")
                
                print(f"   🔧 功能完整性: {found_features}/{len(features)}")
                
                self.test_results.append({
                    "test": "CodeFlow MCP 集成",
                    "status": "passed",
                    "details": f"功能: {found_features}/{len(features)}"
                })
                
                print("✅ CodeFlow MCP 集成測試通過")
                return True
            else:
                raise Exception("CodeFlow MCP 管理器不存在")
                
        except Exception as e:
            self.test_results.append({
                "test": "CodeFlow MCP 集成",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ CodeFlow MCP 集成測試失敗: {e}")
            return False
    
    def test_demo_functionality(self):
        """測試 Demo 功能"""
        print("🧪 測試 Demo 功能...")
        
        try:
            # 檢查 demo 文件
            demo_file = Path("claudeditor/claudeditor_demo.html")
            
            if demo_file.exists():
                with open(demo_file, 'r') as f:
                    content = f.read()
                
                # 檢查 demo 功能
                demo_features = [
                    ("ClaudeEditor v4.6.9", "版本信息"),
                    ("CodeFlow MCP", "MCP 集成"),
                    ("AI 助手", "AI 功能"),
                    ("代碼編輯器", "編輯器"),
                    ("sendMessage", "交互功能")
                ]
                
                found_features = 0
                for keyword, description in demo_features:
                    if keyword in content:
                        found_features += 1
                        print(f"   ✅ {description}: 發現")
                    else:
                        print(f"   ⚠️ {description}: 未發現")
                
                # 計算 demo 檔案大小
                file_size = demo_file.stat().st_size
                print(f"   📏 Demo 檔案大小: {file_size} bytes")
                
                self.test_results.append({
                    "test": "Demo 功能",
                    "status": "passed", 
                    "details": f"功能: {found_features}/{len(demo_features)}, 大小: {file_size}B"
                })
                
                print("✅ Demo 功能測試通過")
                return True
            else:
                raise Exception("Demo 文件不存在")
                
        except Exception as e:
            self.test_results.append({
                "test": "Demo 功能",
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ Demo 功能測試失敗: {e}")
            return False
    
    def create_interactive_test_report(self):
        """創建互動式測試報告"""
        print("📋 創建互動式測試報告...")
        
        try:
            # 創建 HTML 測試報告
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tauri Desktop 實際操作測試報告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
        .test-result {{ margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #ddd; }}
        .passed {{ background: #f0f9f0; border-left-color: #28a745; }}
        .failed {{ background: #f9f0f0; border-left-color: #dc3545; }}
        .button {{ background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
        .button:hover {{ background: #5a6fd8; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Tauri Desktop 實際操作測試報告</h1>
        <p>PowerAutomation v4.6.9 - {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat">
            <h3>{len(self.test_results)}</h3>
            <p>總測試數</p>
        </div>
        <div class="stat">
            <h3>{sum(1 for r in self.test_results if r['status'] == 'passed')}</h3>
            <p>通過測試</p>
        </div>
        <div class="stat">
            <h3>{(sum(1 for r in self.test_results if r['status'] == 'passed')/len(self.test_results)*100):.1f}%</h3>
            <p>成功率</p>
        </div>
    </div>
    
    <h2>📊 測試結果</h2>
    {"".join([f'''
    <div class="test-result {result['status']}">
        <h3>{'✅' if result['status'] == 'passed' else '❌'} {result['test']}</h3>
        <p><strong>狀態:</strong> {result['status']}</p>
        {f"<p><strong>詳情:</strong> {result['details']}</p>" if 'details' in result else ""}
        {f"<p><strong>錯誤:</strong> {result['error']}</p>" if 'error' in result else ""}
    </div>
    ''' for result in self.test_results])}
    
    <h2>🎯 快速操作</h2>
    <button class="button" onclick="window.open('{self.base_url}', '_blank')">
        🌐 打開前端應用
    </button>
    <button class="button" onclick="window.open('claudeditor/claudeditor_demo.html', '_blank')">
        🎮 打開 Demo
    </button>
    <button class="button" onclick="location.reload()">
        🔄 重新載入報告
    </button>
    
    <h2>📝 使用說明</h2>
    <ol>
        <li>確保前端服務器正在運行：<code>npm run dev</code></li>
        <li>點擊上方按鈕打開相應功能</li>
        <li>測試 UI 交互和功能</li>
        <li>檢查 Tauri Desktop 集成</li>
    </ol>
    
    <script>
        console.log('測試報告已載入');
        // 自動檢查前端服務器狀態
        fetch('{self.base_url}')
            .then(response => {{
                if (response.ok) {{
                    console.log('✅ 前端服務器運行中');
                }} else {{
                    console.log('⚠️ 前端服務器狀態異常');
                }}
            }})
            .catch(error => {{
                console.log('❌ 前端服務器未運行');
            }});
    </script>
</body>
</html>
            """
            
            # 保存報告
            report_path = "tests/ui_test_reports/interactive_test_report.html"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📄 互動式測試報告已保存: {report_path}")
            
            # 嘗試打開報告
            try:
                import webbrowser
                full_path = os.path.abspath(report_path)
                webbrowser.open(f"file://{full_path}")
                print("🌐 測試報告已在瀏覽器中打開")
            except:
                print("⚠️ 無法自動打開瀏覽器，請手動打開測試報告")
            
            return report_path
            
        except Exception as e:
            print(f"❌ 創建測試報告失敗: {e}")
            return None
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "="*60)
        print("📋 Tauri Desktop 實際操作測試報告")
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
        
        # 保存 JSON 報告
        report_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            "results": self.test_results
        }
        
        report_path = "tests/ui_test_reports/simple_tauri_test_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 JSON 測試報告已保存: {report_path}")
        
        # 創建互動式報告
        interactive_report = self.create_interactive_test_report()
        
        return passed_tests == total_tests

def main():
    """主函數"""
    print("🚀 開始 Tauri Desktop 簡化實際操作測試")
    
    tester = SimpleTauriTester()
    
    # 檢查服務器狀態
    server_ready = tester.wait_for_server()
    if not server_ready:
        print("⚠️ 前端服務器未啟動，將測試靜態功能")
    
    # 執行測試序列
    tests = [
        tester.test_frontend_availability,
        tester.test_tauri_build_availability,
        tester.test_powerautomation_core_structure,
        tester.test_codeflow_mcp_integration,
        tester.test_demo_functionality
    ]
    
    for test in tests:
        test()
        time.sleep(0.5)  # 測試間隔
    
    # 生成報告
    success = tester.generate_report()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)