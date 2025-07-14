#!/usr/bin/env python3
# PowerAutomation v4.3 Mac性能测试脚本

import os
import sys
import time
import psutil
import subprocess
from pathlib import Path

class MacPerformanceTester:
    def __init__(self):
        self.test_results = {}
        
    def test_startup_time(self):
        print("🚀 测试启动时间...")
        
        start_time = time.time()
        try:
            # 启动ClaudEditor
            process = subprocess.Popen(["claudeditor", "--test-mode"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            
            # 等待启动完成信号或超时
            timeout = 30
            while time.time() - start_time < timeout:
                if process.poll() is not None:
                    break
                time.sleep(0.1)
            
            startup_time = time.time() - start_time
            
            if startup_time < 10:
                status = "优秀"
            elif startup_time < 20:
                status = "良好"
            else:
                status = "需要优化"
            
            self.test_results["startup_time"] = {
                "value": startup_time,
                "unit": "秒",
                "status": status
            }
            
            print(f"✅ 启动时间: {startup_time:.2f}秒 ({status})")
            
            # 清理进程
            if process.poll() is None:
                process.terminate()
                
        except Exception as e:
            print(f"❌ 启动时间测试失败: {e}")
            self.test_results["startup_time"] = {"error": str(e)}
    
    def test_memory_usage(self):
        print("💾 测试内存使用...")
        
        try:
            # 查找ClaudEditor进程
            claudeditor_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                if 'claudeditor' in proc.info['name'].lower():
                    claudeditor_processes.append(proc)
            
            if claudeditor_processes:
                total_memory = sum(proc.info['memory_info'].rss for proc in claudeditor_processes)
                memory_mb = total_memory / (1024 * 1024)
                
                if memory_mb < 200:
                    status = "优秀"
                elif memory_mb < 500:
                    status = "良好"
                else:
                    status = "需要优化"
                
                self.test_results["memory_usage"] = {
                    "value": memory_mb,
                    "unit": "MB",
                    "status": status
                }
                
                print(f"✅ 内存使用: {memory_mb:.1f}MB ({status})")
            else:
                print("⚠️ 未找到ClaudEditor进程")
                self.test_results["memory_usage"] = {"error": "进程未找到"}
                
        except Exception as e:
            print(f"❌ 内存测试失败: {e}")
            self.test_results["memory_usage"] = {"error": str(e)}
    
    def test_cpu_usage(self):
        print("🔥 测试CPU使用...")
        
        try:
            # 监控CPU使用率
            cpu_samples = []
            for i in range(10):
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_samples.append(cpu_percent)
            
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            
            if avg_cpu < 5:
                status = "优秀"
            elif avg_cpu < 15:
                status = "良好"
            else:
                status = "需要优化"
            
            self.test_results["cpu_usage"] = {
                "value": avg_cpu,
                "unit": "%",
                "status": status
            }
            
            print(f"✅ CPU使用: {avg_cpu:.1f}% ({status})")
            
        except Exception as e:
            print(f"❌ CPU测试失败: {e}")
            self.test_results["cpu_usage"] = {"error": str(e)}
    
    def test_disk_usage(self):
        print("💿 测试磁盘使用...")
        
        try:
            app_path = "/Applications/ClaudEditor.app"
            if os.path.exists(app_path):
                # 计算应用大小
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(app_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                
                size_mb = total_size / (1024 * 1024)
                
                if size_mb < 100:
                    status = "优秀"
                elif size_mb < 300:
                    status = "良好"
                else:
                    status = "需要优化"
                
                self.test_results["disk_usage"] = {
                    "value": size_mb,
                    "unit": "MB",
                    "status": status
                }
                
                print(f"✅ 磁盘使用: {size_mb:.1f}MB ({status})")
            else:
                print("⚠️ 应用程序未找到")
                self.test_results["disk_usage"] = {"error": "应用未找到"}
                
        except Exception as e:
            print(f"❌ 磁盘测试失败: {e}")
            self.test_results["disk_usage"] = {"error": str(e)}
    
    def run_all_tests(self):
        print("🍎 PowerAutomation v4.3 Mac性能测试开始...")
        print("=" * 50)
        
        self.test_startup_time()
        self.test_memory_usage()
        self.test_cpu_usage()
        self.test_disk_usage()
        
        self.generate_report()
    
    def generate_report(self):
        print("\n" + "=" * 50)
        print("📊 性能测试结果")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            if "error" in result:
                print(f"❌ {test_name}: {result['error']}")
            else:
                print(f"✅ {test_name}: {result['value']:.1f}{result['unit']} ({result['status']})")
        
        # 保存报告
        import json
        report_path = f"test_results/mac_performance_test_{int(time.time())}.json"
        os.makedirs("test_results", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 性能报告已保存: {report_path}")

if __name__ == "__main__":
    tester = MacPerformanceTester()
    tester.run_all_tests()
