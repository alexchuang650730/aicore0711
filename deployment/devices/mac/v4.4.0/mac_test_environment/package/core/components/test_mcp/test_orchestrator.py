"""
Test Orchestrator - 测试编排器

负责协调和管理所有测试框架的执行
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import importlib.util

class TestOrchestrator:
    """测试编排器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化测试编排器"""
        self.config = config
        self.frameworks_path = os.path.join(os.path.dirname(__file__), "frameworks")
        self.suites_path = os.path.join(os.path.dirname(__file__), "suites")
        self.results_path = os.path.join(os.path.dirname(__file__), "results")
        
        self.available_frameworks = {}
        self.available_suites = {}
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """初始化编排器"""
        try:
            # 发现可用的测试框架
            await self._discover_frameworks()
            
            # 发现可用的测试套件
            await self._discover_suites()
            
            # 确保结果目录存在
            os.makedirs(self.results_path, exist_ok=True)
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"编排器初始化失败: {e}")
            return False
    
    async def _discover_frameworks(self):
        """发现可用的测试框架"""
        if not os.path.exists(self.frameworks_path):
            return
        
        for item in os.listdir(self.frameworks_path):
            item_path = os.path.join(self.frameworks_path, item)
            
            if os.path.isdir(item_path) and item.endswith('_tests'):
                # 发现测试目录
                self.available_frameworks[item] = {
                    "path": item_path,
                    "type": "directory",
                    "enabled": self.config.get("test_frameworks", {}).get(item, {}).get("enabled", True)
                }
            elif item.endswith('.py') and not item.startswith('__'):
                # 发现测试文件
                framework_name = item[:-3]  # 移除.py扩展名
                self.available_frameworks[framework_name] = {
                    "path": item_path,
                    "type": "file",
                    "enabled": self.config.get("test_frameworks", {}).get(framework_name, {}).get("enabled", True)
                }
    
    async def _discover_suites(self):
        """发现可用的测试套件"""
        if not os.path.exists(self.suites_path):
            return
        
        for item in os.listdir(self.suites_path):
            item_path = os.path.join(self.suites_path, item)
            
            if item.endswith('.py') and not item.startswith('__'):
                suite_name = item[:-3]
                self.available_suites[suite_name] = {
                    "path": item_path,
                    "enabled": True
                }
    
    async def run_suite(self, suite_name: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """运行指定的测试套件"""
        if not self.is_initialized:
            await self.initialize()
        
        if suite_name not in self.available_suites:
            return {
                "success": False,
                "error": f"测试套件 '{suite_name}' 不存在",
                "available_suites": list(self.available_suites.keys())
            }
        
        try:
            suite_info = self.available_suites[suite_name]
            
            # 动态加载测试套件
            spec = importlib.util.spec_from_file_location(suite_name, suite_info["path"])
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找并执行测试函数
                if hasattr(module, 'run_tests'):
                    result = await self._run_async_test(module.run_tests, options)
                elif hasattr(module, 'main'):
                    result = await self._run_async_test(module.main, options)
                else:
                    # 尝试运行所有以test_开头的函数
                    test_functions = [getattr(module, name) for name in dir(module) 
                                    if name.startswith('test_') and callable(getattr(module, name))]
                    
                    if test_functions:
                        results = []
                        for test_func in test_functions:
                            func_result = await self._run_async_test(test_func, options)
                            results.append({
                                "function": test_func.__name__,
                                "result": func_result
                            })
                        result = {"tests": results, "success": True}
                    else:
                        result = {"success": False, "error": "未找到可执行的测试函数"}
                
                # 保存结果
                await self._save_result(suite_name, result)
                
                return result
            else:
                return {"success": False, "error": f"无法加载测试套件模块: {suite_name}"}
                
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "suite_name": suite_name
            }
            await self._save_result(suite_name, error_result)
            return error_result
    
    async def _run_async_test(self, test_func, options: Dict[str, Any] = None):
        """运行测试函数（支持同步和异步）"""
        try:
            if asyncio.iscoroutinefunction(test_func):
                if options:
                    return await test_func(**options)
                else:
                    return await test_func()
            else:
                if options:
                    return test_func(**options)
                else:
                    return test_func()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _save_result(self, suite_name: str, result: Dict[str, Any]):
        """保存测试结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(self.results_path, f"{suite_name}_{timestamp}.json")
            
            result_data = {
                "suite_name": suite_name,
                "timestamp": timestamp,
                "result": result
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存测试结果失败: {e}")
    
    async def list_frameworks(self) -> Dict[str, Any]:
        """列出所有可用的测试框架"""
        if not self.is_initialized:
            await self.initialize()
        
        return {
            "frameworks": self.available_frameworks,
            "count": len(self.available_frameworks)
        }
    
    async def list_suites(self) -> Dict[str, Any]:
        """列出所有可用的测试套件"""
        if not self.is_initialized:
            await self.initialize()
        
        return {
            "suites": self.available_suites,
            "count": len(self.available_suites)
        }
    
    async def get_results(self, suite_name: Optional[str] = None) -> Dict[str, Any]:
        """获取测试结果"""
        try:
            if not os.path.exists(self.results_path):
                return {"results": [], "count": 0}
            
            results = []
            for file_name in os.listdir(self.results_path):
                if file_name.endswith('.json'):
                    if suite_name and not file_name.startswith(suite_name):
                        continue
                    
                    file_path = os.path.join(self.results_path, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            result_data = json.load(f)
                            results.append(result_data)
                    except Exception as e:
                        print(f"读取结果文件失败 {file_name}: {e}")
            
            # 按时间戳排序
            results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {"error": str(e), "results": [], "count": 0}
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理过期的测试结果
            retention_days = self.config.get("results", {}).get("retention_days", 30)
            if retention_days > 0:
                await self._cleanup_old_results(retention_days)
            
            self.is_initialized = False
            
        except Exception as e:
            print(f"编排器清理失败: {e}")
    
    async def _cleanup_old_results(self, retention_days: int):
        """清理过期的测试结果"""
        try:
            if not os.path.exists(self.results_path):
                return
            
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
            
            for file_name in os.listdir(self.results_path):
                file_path = os.path.join(self.results_path, file_name)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        
        except Exception as e:
            print(f"清理过期结果失败: {e}")

