#!/usr/bin/env python3
"""
UI测试运行脚本

提供完整的UI测试执行和报告生成功能
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from test.ui_test_registry import get_ui_test_registry
from core.components.stagewise_mcp.ui_test_integration import StagewiseUITestRunner

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UITestExecutor:
    """UI测试执行器"""
    
    def __init__(self):
        self.runner = None
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    async def initialize(self) -> bool:
        """初始化测试执行器"""
        try:
            self.runner = StagewiseUITestRunner()
            success = await self.runner.initialize()
            if success:
                logger.info("UI测试执行器初始化成功")
            else:
                logger.error("UI测试执行器初始化失败")
            return success
        except Exception as e:
            logger.error(f"初始化UI测试执行器异常: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有UI测试"""
        if not self.runner:
            raise RuntimeError("测试执行器未初始化")
        
        self.start_time = time.time()
        logger.info("开始运行所有UI测试...")
        
        try:
            # 获取测试摘要
            summary = self.runner.get_test_summary()
            logger.info(f"发现 {summary.get('total_tests', 0)} 个测试用例，"
                       f"{summary.get('total_suites', 0)} 个测试套件")
            
            # 运行所有测试套件
            suite_results = await self.runner.run_all_ui_tests()
            
            self.end_time = time.time()
            total_duration = self.end_time - self.start_time
            
            # 统计结果
            total_tests = 0
            passed_tests = 0
            failed_tests = 0
            
            for suite_name, session in suite_results.items():
                total_tests += session.total_tests
                passed_tests += session.passed_tests
                failed_tests += session.failed_tests
            
            self.results = {
                "summary": {
                    "total_suites": len(suite_results),
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                    "total_duration": total_duration
                },
                "suite_results": {
                    suite_name: {
                        "total_tests": session.total_tests,
                        "passed_tests": session.passed_tests,
                        "failed_tests": session.failed_tests,
                        "success_rate": session.success_rate,
                        "start_time": session.start_time,
                        "end_time": session.end_time
                    }
                    for suite_name, session in suite_results.items()
                },
                "test_discovery": summary
            }
            
            logger.info(f"所有UI测试执行完成: {passed_tests}/{total_tests} 通过 "
                       f"({self.results['summary']['success_rate']:.1%})")
            
            return self.results
            
        except Exception as e:
            logger.error(f"运行UI测试失败: {str(e)}")
            self.end_time = time.time()
            raise
    
    async def run_p0_tests(self) -> Dict[str, Any]:
        """运行P0优先级测试"""
        if not self.runner:
            raise RuntimeError("测试执行器未初始化")
        
        logger.info("开始运行P0优先级测试...")
        
        try:
            from core.components.stagewise_mcp.enhanced_testing_framework import TestPriority
            
            # 运行P0测试
            results = await self.runner.run_ui_test_by_priority(TestPriority.P0)
            
            # 统计结果
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.status.value == "PASSED")
            failed_tests = total_tests - passed_tests
            
            p0_results = {
                "priority": "P0",
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "test_results": [
                    {
                        "test_id": r.test_id,
                        "test_name": r.test_name,
                        "status": r.status.value,
                        "duration": r.duration,
                        "error_message": r.error_message
                    }
                    for r in results
                ]
            }
            
            logger.info(f"P0测试执行完成: {passed_tests}/{total_tests} 通过")
            
            return p0_results
            
        except Exception as e:
            logger.error(f"运行P0测试失败: {str(e)}")
            raise
    
    async def run_specific_suite(self, suite_name: str) -> Dict[str, Any]:
        """运行指定测试套件"""
        if not self.runner:
            raise RuntimeError("测试执行器未初始化")
        
        logger.info(f"开始运行测试套件: {suite_name}")
        
        try:
            session = await self.runner.ui_integration.run_ui_test_suite(suite_name)
            
            suite_result = {
                "suite_name": suite_name,
                "total_tests": session.total_tests,
                "passed_tests": session.passed_tests,
                "failed_tests": session.failed_tests,
                "success_rate": session.success_rate,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "test_results": [
                    {
                        "test_id": r.test_id,
                        "test_name": r.test_name,
                        "status": r.status.value,
                        "duration": r.duration,
                        "output": r.output,
                        "error_message": r.error_message
                    }
                    for r in session.test_results
                ]
            }
            
            logger.info(f"测试套件 {suite_name} 执行完成: "
                       f"{session.passed_tests}/{session.total_tests} 通过")
            
            return suite_result
            
        except Exception as e:
            logger.error(f"运行测试套件 {suite_name} 失败: {str(e)}")
            raise
    
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """生成HTML测试报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI测试报告 - PowerAutomation 4.0</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }}
        .header h1 {{ color: #2c3e50; margin: 0; font-size: 2.5em; }}
        .header p {{ color: #7f8c8d; margin: 10px 0 0 0; font-size: 1.1em; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-card.success {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); }}
        .summary-card.warning {{ background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); }}
        .summary-card.error {{ background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%); }}
        .summary-card h3 {{ margin: 0 0 10px 0; font-size: 1.2em; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; }}
        .suite-results {{ margin-top: 30px; }}
        .suite {{ margin-bottom: 25px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        .suite-header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
        .suite-header h3 {{ margin: 0; color: #2c3e50; }}
        .suite-stats {{ margin-top: 5px; color: #6c757d; }}
        .test-list {{ padding: 0; }}
        .test-item {{ padding: 12px 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-name {{ font-weight: 500; }}
        .test-status {{ padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }}
        .status-passed {{ background: #d4edda; color: #155724; }}
        .status-failed {{ background: #f8d7da; color: #721c24; }}
        .status-error {{ background: #f8d7da; color: #721c24; }}
        .test-duration {{ color: #6c757d; font-size: 0.9em; }}
        .footer {{ margin-top: 30px; text-align: center; color: #6c757d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 UI测试报告</h1>
            <p>PowerAutomation 4.0 - Stagewise测试框架</p>
            <p>生成时间: {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总测试套件</h3>
                <div class="value">{total_suites}</div>
            </div>
            <div class="summary-card">
                <h3>总测试用例</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card success">
                <h3>通过测试</h3>
                <div class="value">{passed_tests}</div>
            </div>
            <div class="summary-card error">
                <h3>失败测试</h3>
                <div class="value">{failed_tests}</div>
            </div>
            <div class="summary-card {success_class}">
                <h3>成功率</h3>
                <div class="value">{success_rate}</div>
            </div>
            <div class="summary-card">
                <h3>执行时间</h3>
                <div class="value">{duration}</div>
            </div>
        </div>
        
        <div class="suite-results">
            <h2>📋 测试套件详情</h2>
            {suite_details}
        </div>
        
        <div class="footer">
            <p>由 PowerAutomation 4.0 Stagewise测试框架生成</p>
        </div>
    </div>
</body>
</html>
        """
        
        # 处理结果数据
        summary = results.get("summary", {})
        suite_results = results.get("suite_results", {})
        
        # 生成套件详情HTML
        suite_details_html = ""
        for suite_name, suite_data in suite_results.items():
            suite_details_html += f"""
            <div class="suite">
                <div class="suite-header">
                    <h3>📦 {suite_name}</h3>
                    <div class="suite-stats">
                        {suite_data['passed_tests']}/{suite_data['total_tests']} 通过 
                        ({suite_data['success_rate']:.1%})
                    </div>
                </div>
            </div>
            """
        
        # 确定成功率样式
        success_rate = summary.get("success_rate", 0)
        if success_rate >= 0.9:
            success_class = "success"
        elif success_rate >= 0.7:
            success_class = "warning"
        else:
            success_class = "error"
        
        # 填充模板
        html_content = html_template.format(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_suites=summary.get("total_suites", 0),
            total_tests=summary.get("total_tests", 0),
            passed_tests=summary.get("passed_tests", 0),
            failed_tests=summary.get("failed_tests", 0),
            success_rate=f"{success_rate:.1%}",
            success_class=success_class,
            duration=f"{summary.get('total_duration', 0):.1f}s",
            suite_details=suite_details_html
        )
        
        return html_content
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "test/reports"):
        """保存测试结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON报告
        json_file = output_path / f"ui_test_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        # 保存HTML报告
        html_content = self.generate_html_report(results)
        html_file = output_path / f"ui_test_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"测试报告已保存:")
        logger.info(f"  JSON: {json_file}")
        logger.info(f"  HTML: {html_file}")
        
        return {
            "json_report": str(json_file),
            "html_report": str(html_file)
        }


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="UI测试运行工具")
    parser.add_argument("--suite", help="运行指定的测试套件")
    parser.add_argument("--p0", action="store_true", help="只运行P0优先级测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--output", default="test/reports", help="报告输出目录")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 创建测试执行器
        executor = UITestExecutor()
        
        # 初始化
        if not await executor.initialize():
            print("❌ 测试执行器初始化失败")
            sys.exit(1)
        
        # 执行测试
        results = None
        
        if args.p0:
            print("🔥 运行P0优先级测试...")
            results = await executor.run_p0_tests()
            
        elif args.suite:
            print(f"📦 运行测试套件: {args.suite}")
            results = await executor.run_specific_suite(args.suite)
            
        elif args.all:
            print("🚀 运行所有UI测试...")
            results = await executor.run_all_tests()
            
        else:
            print("请指定要执行的测试 (--all, --p0, --suite)")
            sys.exit(1)
        
        # 保存结果
        if results:
            report_files = executor.save_results(results, args.output)
            
            # 显示摘要
            if "summary" in results:
                summary = results["summary"]
                print(f"\n✅ 测试执行完成!")
                print(f"📊 总测试: {summary.get('total_tests', 0)}")
                print(f"✅ 通过: {summary.get('passed_tests', 0)}")
                print(f"❌ 失败: {summary.get('failed_tests', 0)}")
                print(f"📈 成功率: {summary.get('success_rate', 0):.1%}")
                print(f"⏱️  执行时间: {summary.get('total_duration', 0):.1f}秒")
            
            print(f"\n📄 报告文件:")
            print(f"  HTML: {report_files['html_report']}")
            print(f"  JSON: {report_files['json_report']}")
        
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

