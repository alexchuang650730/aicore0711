#!/usr/bin/env python3
"""
PowerAutomation v4.6.9 完整系統測試腳本
測試 CodeFlow MCP、Tauri Desktop、AI 集成等所有核心功能
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path

class PowerAutomationTestRunner:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.test_results = {
            "codeflow_mcp": {"status": "pending", "tests": []},
            "tauri_desktop": {"status": "pending", "tests": []},
            "ai_integration": {"status": "pending", "tests": []},
            "powerautomation_core": {"status": "pending", "tests": []}
        }
        
    def run_python_tests(self):
        """執行 Python 測試套件"""
        print("🧪 執行 Python 測試套件...")
        
        try:
            # 執行完整測試
            result = subprocess.run([
                sys.executable, 
                str(self.base_path / "tests" / "test_codeflow_mcp_comprehensive.py")
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Python 測試套件通過")
                self.test_results["codeflow_mcp"]["status"] = "passed"
                return True
            else:
                print("❌ Python 測試套件失敗")
                print(result.stdout)
                print(result.stderr)
                self.test_results["codeflow_mcp"]["status"] = "failed"
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Python 測試超時")
            self.test_results["codeflow_mcp"]["status"] = "timeout"
            return False
        except Exception as e:
            print(f"💥 Python 測試異常: {e}")
            self.test_results["codeflow_mcp"]["status"] = "error"
            return False
    
    def test_tauri_compilation(self):
        """測試 Tauri 編譯"""
        print("🔨 測試 Tauri 編譯...")
        
        try:
            # 切換到 claudeditor 目錄
            claudeditor_path = self.base_path / "claudeditor"
            
            # 檢查 npm 依賴
            result = subprocess.run([
                "npm", "install"
            ], cwd=claudeditor_path, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print("❌ NPM 安裝失敗")
                self.test_results["tauri_desktop"]["status"] = "failed"
                return False
            
            # 測試 Tauri 構建（不啟動）
            result = subprocess.run([
                "npm", "run", "tauri", "build", "--", "--help"
            ], cwd=claudeditor_path, capture_output=True, text=True, timeout=30)
            
            if "tauri" in result.stdout.lower():
                print("✅ Tauri 構建工具可用")
                self.test_results["tauri_desktop"]["status"] = "passed"
                return True
            else:
                print("❌ Tauri 構建工具不可用")
                self.test_results["tauri_desktop"]["status"] = "failed"
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Tauri 編譯測試超時")
            self.test_results["tauri_desktop"]["status"] = "timeout"
            return False
        except Exception as e:
            print(f"💥 Tauri 編譯測試異常: {e}")
            self.test_results["tauri_desktop"]["status"] = "error"
            return False
    
    def test_project_structure(self):
        """測試項目結構完整性"""
        print("📁 測試項目結構完整性...")
        
        required_files = [
            "README.md",
            "claudeditor/package.json",
            "claudeditor/src-tauri/tauri.conf.json",
            "claudeditor/src-tauri/Cargo.toml",
            "claudeditor/src/main.jsx",
            "core/powerautomation_main.py",
            "tests/test_codeflow_mcp_comprehensive.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print("❌ 缺少關鍵文件:")
            for file in missing_files:
                print(f"   - {file}")
            self.test_results["powerautomation_core"]["status"] = "failed"
            return False
        else:
            print("✅ 項目結構完整")
            self.test_results["powerautomation_core"]["status"] = "passed"
            return True
    
    def test_configuration_files(self):
        """測試配置文件有效性"""
        print("⚙️  測試配置文件有效性...")
        
        config_tests = []
        
        # 測試 package.json
        try:
            package_json_path = self.base_path / "claudeditor" / "package.json"
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            if package_data.get("version") == "4.6.9":
                config_tests.append(("package.json版本", True))
            else:
                config_tests.append(("package.json版本", False))
                
        except Exception as e:
            config_tests.append(("package.json", False))
        
        # 測試 tauri.conf.json
        try:
            tauri_conf_path = self.base_path / "claudeditor" / "src-tauri" / "tauri.conf.json"
            with open(tauri_conf_path, 'r') as f:
                tauri_data = json.load(f)
            
            if tauri_data.get("package", {}).get("version") == "4.6.9":
                config_tests.append(("tauri.conf.json版本", True))
            else:
                config_tests.append(("tauri.conf.json版本", False))
                
        except Exception as e:
            config_tests.append(("tauri.conf.json", False))
        
        # 評估結果
        passed_configs = sum(1 for _, passed in config_tests if passed)
        total_configs = len(config_tests)
        
        for test_name, passed in config_tests:
            status = "✅" if passed else "❌"
            print(f"   {status} {test_name}")
        
        if passed_configs == total_configs:
            print("✅ 所有配置文件有效")
            return True
        else:
            print(f"❌ {total_configs - passed_configs}/{total_configs} 配置文件無效")
            return False
    
    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("📋 PowerAutomation v4.6.9 測試報告")
        print("=" * 60)
        
        total_categories = len(self.test_results)
        passed_categories = sum(1 for result in self.test_results.values() if result["status"] == "passed")
        
        print(f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"測試類別: {total_categories}")
        print(f"通過類別: {passed_categories}")
        print(f"整體成功率: {(passed_categories/total_categories)*100:.1f}%")
        
        print("\n📊 詳細結果:")
        status_icons = {
            "passed": "✅",
            "failed": "❌", 
            "timeout": "⏰",
            "error": "💥",
            "pending": "⏳"
        }
        
        for category, result in self.test_results.items():
            icon = status_icons.get(result["status"], "❓")
            print(f"   {icon} {category}: {result['status']}")
        
        # 生成建議
        print("\n💡 建議:")
        if passed_categories == total_categories:
            print("   🎉 所有測試通過！系統準備就緒進行生產部署。")
        else:
            print("   ⚠️ 發現問題需要修復:")
            for category, result in self.test_results.items():
                if result["status"] != "passed":
                    print(f"   - 修復 {category} 中的問題")
        
        return passed_categories == total_categories
    
    def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始 PowerAutomation v4.6.9 完整系統測試")
        print("=" * 60)
        
        # 測試序列
        test_sequence = [
            ("項目結構", self.test_project_structure),
            ("配置文件", self.test_configuration_files),
            ("Python 測試套件", self.run_python_tests),
            ("Tauri 編譯", self.test_tauri_compilation)
        ]
        
        results = []
        for test_name, test_func in test_sequence:
            print(f"\n🔍 執行 {test_name} 測試...")
            try:
                result = test_func()
                results.append(result)
                status = "✅ 通過" if result else "❌ 失敗"
                print(f"   {status}")
            except Exception as e:
                print(f"   💥 異常: {e}")
                results.append(False)
        
        # 生成報告
        success = self.generate_test_report()
        
        return success

def main():
    """主函數"""
    runner = PowerAutomationTestRunner()
    success = runner.run_all_tests()
    
    # 退出代碼
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()