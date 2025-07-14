"""
PowerAutomation 4.0 可视化编程引擎

提供可视化编程的核心执行能力，支持多种编程语言和框架。
"""

import asyncio
import subprocess
import tempfile
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging


class ExecutionFramework(Enum):
    """支持的执行框架"""
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    PUPPETEER = "puppeteer"
    CYPRESS = "cypress"
    REQUESTS = "requests"
    BEAUTIFULSOUP = "beautifulsoup"


class ExecutionLanguage(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


@dataclass
class ExecutionResult:
    """代码执行结果"""
    execution_id: str
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    return_value: Any = None
    screenshots: List[str] = None
    
    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []


class VisualProgrammingEngine:
    """可视化编程引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 执行环境配置
        self.temp_dir = self.config.get("temp_dir", tempfile.gettempdir())
        self.timeout = self.config.get("execution_timeout", 30)
        self.max_concurrent_executions = self.config.get("max_concurrent_executions", 5)
        
        # 执行统计
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0
        }
        
        # 并发控制
        self.execution_semaphore = asyncio.Semaphore(self.max_concurrent_executions)
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动可视化编程引擎"""
        if self.is_running:
            return
        
        self.logger.info("启动可视化编程引擎...")
        
        # 检查依赖
        await self._check_dependencies()
        
        # 创建临时目录
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.is_running = True
        self.logger.info("可视化编程引擎启动完成")
    
    async def stop(self):
        """停止可视化编程引擎"""
        if not self.is_running:
            return
        
        self.logger.info("停止可视化编程引擎...")
        
        # 取消所有活跃的执行
        for execution_id, task in list(self.active_executions.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.active_executions.clear()
        self.is_running = False
        self.logger.info("可视化编程引擎已停止")
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        framework: str = "selenium",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """执行代码"""
        if not self.is_running:
            raise RuntimeError("可视化编程引擎未启动")
        
        execution_id = str(uuid.uuid4())
        context = context or {}
        
        async with self.execution_semaphore:
            start_time = datetime.now()
            
            try:
                # 根据语言和框架执行代码
                if language == ExecutionLanguage.PYTHON.value:
                    result = await self._execute_python_code(
                        execution_id, code, framework, context
                    )
                elif language == ExecutionLanguage.JAVASCRIPT.value:
                    result = await self._execute_javascript_code(
                        execution_id, code, framework, context
                    )
                elif language == ExecutionLanguage.TYPESCRIPT.value:
                    result = await self._execute_typescript_code(
                        execution_id, code, framework, context
                    )
                else:
                    raise ValueError(f"不支持的编程语言: {language}")
                
                execution_time = (datetime.now() - start_time).total_seconds()
                result["execution_time"] = execution_time
                
                # 更新统计
                self.execution_stats["total_executions"] += 1
                if result.get("success", False):
                    self.execution_stats["successful_executions"] += 1
                else:
                    self.execution_stats["failed_executions"] += 1
                
                # 更新平均执行时间
                total = self.execution_stats["total_executions"]
                current_avg = self.execution_stats["avg_execution_time"]
                self.execution_stats["avg_execution_time"] = (
                    (current_avg * (total - 1) + execution_time) / total
                )
                
                self.logger.info(f"代码执行完成: {execution_id}, 成功: {result.get('success', False)}")
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                self.execution_stats["total_executions"] += 1
                self.execution_stats["failed_executions"] += 1
                
                error_result = {
                    "execution_id": execution_id,
                    "success": False,
                    "output": "",
                    "error": str(e),
                    "execution_time": execution_time
                }
                
                self.logger.error(f"代码执行失败: {execution_id}, 错误: {e}")
                return error_result
    
    async def _execute_python_code(
        self,
        execution_id: str,
        code: str,
        framework: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行Python代码"""
        # 创建临时文件
        temp_file = os.path.join(self.temp_dir, f"exec_{execution_id}.py")
        
        try:
            # 准备执行环境
            execution_code = self._prepare_python_execution_environment(
                code, framework, context
            )
            
            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(execution_code)
            
            # 执行代码
            process = await asyncio.create_subprocess_exec(
                'python', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout
                )
                
                success = process.returncode == 0
                output = stdout.decode('utf-8') if stdout else ""
                error = stderr.decode('utf-8') if stderr else None
                
                # 尝试解析输出中的结构化数据
                return_value = None
                screenshots = []
                
                try:
                    # 查找JSON输出
                    lines = output.split('\n')
                    for line in lines:
                        if line.startswith('RESULT:'):
                            result_data = json.loads(line[7:])
                            return_value = result_data.get('return_value')
                            screenshots = result_data.get('screenshots', [])
                            break
                except:
                    pass
                
                return {
                    "execution_id": execution_id,
                    "success": success,
                    "output": output,
                    "error": error,
                    "return_value": return_value,
                    "screenshots": screenshots
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "execution_id": execution_id,
                    "success": False,
                    "output": "",
                    "error": f"执行超时 ({self.timeout}秒)"
                }
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    async def _execute_javascript_code(
        self,
        execution_id: str,
        code: str,
        framework: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行JavaScript代码"""
        # 创建临时文件
        temp_file = os.path.join(self.temp_dir, f"exec_{execution_id}.js")
        
        try:
            # 准备执行环境
            execution_code = self._prepare_javascript_execution_environment(
                code, framework, context
            )
            
            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(execution_code)
            
            # 执行代码
            process = await asyncio.create_subprocess_exec(
                'node', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout
                )
                
                success = process.returncode == 0
                output = stdout.decode('utf-8') if stdout else ""
                error = stderr.decode('utf-8') if stderr else None
                
                return {
                    "execution_id": execution_id,
                    "success": success,
                    "output": output,
                    "error": error
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "execution_id": execution_id,
                    "success": False,
                    "output": "",
                    "error": f"执行超时 ({self.timeout}秒)"
                }
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    async def _execute_typescript_code(
        self,
        execution_id: str,
        code: str,
        framework: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行TypeScript代码"""
        # 先编译TypeScript到JavaScript，然后执行
        temp_ts_file = os.path.join(self.temp_dir, f"exec_{execution_id}.ts")
        temp_js_file = os.path.join(self.temp_dir, f"exec_{execution_id}.js")
        
        try:
            # 准备执行环境
            execution_code = self._prepare_typescript_execution_environment(
                code, framework, context
            )
            
            # 写入TypeScript文件
            with open(temp_ts_file, 'w', encoding='utf-8') as f:
                f.write(execution_code)
            
            # 编译TypeScript
            compile_process = await asyncio.create_subprocess_exec(
                'tsc', temp_ts_file, '--outFile', temp_js_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            compile_stdout, compile_stderr = await compile_process.communicate()
            
            if compile_process.returncode != 0:
                return {
                    "execution_id": execution_id,
                    "success": False,
                    "output": "",
                    "error": f"TypeScript编译失败: {compile_stderr.decode('utf-8')}"
                }
            
            # 执行编译后的JavaScript
            return await self._execute_javascript_code(
                execution_id, "", framework, context
            )
            
        finally:
            # 清理临时文件
            for temp_file in [temp_ts_file, temp_js_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    def _prepare_python_execution_environment(
        self,
        code: str,
        framework: str,
        context: Dict[str, Any]
    ) -> str:
        """准备Python执行环境"""
        imports = []
        setup_code = []
        
        # 根据框架添加导入和设置
        if framework == ExecutionFramework.SELENIUM.value:
            imports.extend([
                "from selenium import webdriver",
                "from selenium.webdriver.common.by import By",
                "from selenium.webdriver.support.ui import WebDriverWait",
                "from selenium.webdriver.support import expected_conditions as EC",
                "from selenium.webdriver.common.action_chains import ActionChains",
                "import time"
            ])
            
            # 设置WebDriver
            setup_code.extend([
                "# 设置WebDriver",
                "options = webdriver.ChromeOptions()",
                "options.add_argument('--headless')",
                "options.add_argument('--no-sandbox')",
                "options.add_argument('--disable-dev-shm-usage')",
                "driver = webdriver.Chrome(options=options)",
                "wait = WebDriverWait(driver, 10)"
            ])
            
        elif framework == ExecutionFramework.PLAYWRIGHT.value:
            imports.extend([
                "from playwright.async_api import async_playwright",
                "import asyncio"
            ])
            
        elif framework == ExecutionFramework.REQUESTS.value:
            imports.extend([
                "import requests",
                "from bs4 import BeautifulSoup"
            ])
        
        # 添加通用导入
        imports.extend([
            "import json",
            "import os",
            "import sys"
        ])
        
        # 构建完整代码
        full_code = []
        full_code.extend(imports)
        full_code.append("")
        full_code.extend(setup_code)
        full_code.append("")
        full_code.append("try:")
        
        # 缩进用户代码
        user_code_lines = code.split('\n')
        for line in user_code_lines:
            full_code.append(f"    {line}")
        
        # 添加结果输出和清理代码
        if framework == ExecutionFramework.SELENIUM.value:
            full_code.extend([
                "",
                "    # 输出结果",
                "    result = {",
                "        'return_value': locals().get('result'),",
                "        'screenshots': []",
                "    }",
                "    print(f'RESULT:{json.dumps(result)}')",
                "",
                "except Exception as e:",
                "    print(f'ERROR: {str(e)}', file=sys.stderr)",
                "finally:",
                "    # 清理资源",
                "    if 'driver' in locals():",
                "        driver.quit()"
            ])
        else:
            full_code.extend([
                "",
                "    # 输出结果",
                "    result = {",
                "        'return_value': locals().get('result')",
                "    }",
                "    print(f'RESULT:{json.dumps(result)}')",
                "",
                "except Exception as e:",
                "    print(f'ERROR: {str(e)}', file=sys.stderr)"
            ])
        
        return '\n'.join(full_code)
    
    def _prepare_javascript_execution_environment(
        self,
        code: str,
        framework: str,
        context: Dict[str, Any]
    ) -> str:
        """准备JavaScript执行环境"""
        imports = []
        setup_code = []
        
        # 根据框架添加导入和设置
        if framework == ExecutionFramework.PUPPETEER.value:
            imports.append("const puppeteer = require('puppeteer');")
            setup_code.extend([
                "// 设置Puppeteer",
                "const browser = await puppeteer.launch({ headless: true });",
                "const page = await browser.newPage();"
            ])
            
        elif framework == ExecutionFramework.PLAYWRIGHT.value:
            imports.append("const { chromium } = require('playwright');")
            setup_code.extend([
                "// 设置Playwright",
                "const browser = await chromium.launch({ headless: true });",
                "const page = await browser.newPage();"
            ])
        
        # 构建完整代码
        full_code = []
        full_code.extend(imports)
        full_code.append("")
        
        if setup_code:
            full_code.append("(async () => {")
            full_code.append("  try {")
            full_code.extend([f"    {line}" for line in setup_code])
            full_code.append("")
            
            # 缩进用户代码
            user_code_lines = code.split('\n')
            for line in user_code_lines:
                full_code.append(f"    {line}")
            
            full_code.extend([
                "",
                "  } catch (error) {",
                "    console.error('ERROR:', error.message);",
                "  } finally {",
                "    // 清理资源",
                "    if (typeof browser !== 'undefined') {",
                "      await browser.close();",
                "    }",
                "  }",
                "})();"
            ])
        else:
            full_code.append("try {")
            user_code_lines = code.split('\n')
            for line in user_code_lines:
                full_code.append(f"  {line}")
            full_code.extend([
                "} catch (error) {",
                "  console.error('ERROR:', error.message);",
                "}"
            ])
        
        return '\n'.join(full_code)
    
    def _prepare_typescript_execution_environment(
        self,
        code: str,
        framework: str,
        context: Dict[str, Any]
    ) -> str:
        """准备TypeScript执行环境"""
        # TypeScript基本上与JavaScript相同，但添加类型声明
        js_code = self._prepare_javascript_execution_environment(code, framework, context)
        
        # 添加TypeScript特定的导入和类型声明
        ts_imports = []
        if framework == ExecutionFramework.PUPPETEER.value:
            ts_imports.append("import * as puppeteer from 'puppeteer';")
        elif framework == ExecutionFramework.PLAYWRIGHT.value:
            ts_imports.append("import { chromium } from 'playwright';")
        
        if ts_imports:
            # 替换require导入为ES6导入
            lines = js_code.split('\n')
            new_lines = []
            for line in lines:
                if 'require(' in line and any(imp in line for imp in ['puppeteer', 'playwright']):
                    continue  # 跳过require导入
                new_lines.append(line)
            
            # 在开头添加TypeScript导入
            final_lines = ts_imports + [''] + new_lines
            return '\n'.join(final_lines)
        
        return js_code
    
    async def _check_dependencies(self):
        """检查依赖"""
        dependencies = {
            "python": ["python", "--version"],
            "node": ["node", "--version"]
        }
        
        for name, command in dependencies.items():
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if process.returncode == 0:
                    self.logger.info(f"依赖检查通过: {name}")
                else:
                    self.logger.warning(f"依赖检查失败: {name}")
                    
            except FileNotFoundError:
                self.logger.warning(f"依赖未找到: {name}")
    
    async def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return {
            "total_executions": self.execution_stats["total_executions"],
            "successful_executions": self.execution_stats["successful_executions"],
            "failed_executions": self.execution_stats["failed_executions"],
            "success_rate": (
                self.execution_stats["successful_executions"] / 
                max(self.execution_stats["total_executions"], 1)
            ),
            "avg_execution_time": self.execution_stats["avg_execution_time"],
            "active_executions": len(self.active_executions)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "visual_programming_engine",
            "status": "healthy" if self.is_running else "unhealthy",
            "active_executions": len(self.active_executions),
            "execution_stats": await self.get_execution_statistics()
        }

