#!/usr/bin/env python3
# PowerAutomation v4.3 Mac功能测试脚本

import os
import sys
import json
import time
import subprocess
from pathlib import Path

class MacFunctionTester:
    def __init__(self):
        self.test_results = []
        self.config_path = Path("config/mac_config.json")
        self.load_config()
    
    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"❌ 无法加载配置文件: {e}")
            sys.exit(1)
    
    def log_test(self, test_name, status, message=""):
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status} {message}")
    
    def test_application_exists(self):
        app_path = "/Applications/ClaudEditor.app"
        if os.path.exists(app_path):
            self.log_test("应用程序存在", "PASS", f"找到应用: {app_path}")
        else:
            self.log_test("应用程序存在", "FAIL", f"未找到应用: {app_path}")
    
    def test_command_line_tool(self):
        try:
            result = subprocess.run(["claudeditor", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_test("命令行工具", "PASS", f"版本: {version}")
            else:
                self.log_test("命令行工具", "FAIL", "命令执行失败")
        except subprocess.TimeoutExpired:
            self.log_test("命令行工具", "FAIL", "命令超时")
        except FileNotFoundError:
            self.log_test("命令行工具", "FAIL", "命令未找到")
        except Exception as e:
            self.log_test("命令行工具", "FAIL", str(e))
    
    def test_configuration_files(self):
        config_files = [
            "config/claude.yaml",
            "config/mac.yaml",
            "config/mac_config.json"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                self.log_test(f"配置文件 {config_file}", "PASS")
            else:
                self.log_test(f"配置文件 {config_file}", "WARN", "文件不存在")
    
    def test_python_dependencies(self):
        try:
            import requests
            import flask
            import tauri
            self.log_test("Python依赖", "PASS", "所有依赖已安装")
        except ImportError as e:
            self.log_test("Python依赖", "FAIL", f"缺少依赖: {e}")
    
    def test_node_dependencies(self):
        try:
            result = subprocess.run(["npm", "list", "--depth=0"], 
                                  cwd="claudeditor", capture_output=True, text=True)
            if "tauri" in result.stdout:
                self.log_test("Node.js依赖", "PASS", "Tauri已安装")
            else:
                self.log_test("Node.js依赖", "WARN", "Tauri未找到")
        except Exception as e:
            self.log_test("Node.js依赖", "FAIL", str(e))
    
    def test_system_integration(self):
        # 检查Dock图标
        dock_plist = os.path.expanduser("~/Library/Preferences/com.apple.dock.plist")
        if os.path.exists(dock_plist):
            self.log_test("系统集成", "PASS", "Dock配置存在")
        else:
            self.log_test("系统集成", "WARN", "Dock配置未找到")
    
    def run_all_tests(self):
        print("🍎 PowerAutomation v4.3 Mac功能测试开始...")
        print("=" * 50)
        
        self.test_application_exists()
        self.test_command_line_tool()
        self.test_configuration_files()
        self.test_python_dependencies()
        self.test_node_dependencies()
        self.test_system_integration()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        print("\n" + "=" * 50)
        print("📊 测试结果摘要")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warned_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"警告: {warned_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        # 保存详细报告
        report_path = f"test_results/mac_function_test_{int(time.time())}.json"
        os.makedirs("test_results", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "warned": warned_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "tests": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存: {report_path}")

if __name__ == "__main__":
    tester = MacFunctionTester()
    tester.run_all_tests()
