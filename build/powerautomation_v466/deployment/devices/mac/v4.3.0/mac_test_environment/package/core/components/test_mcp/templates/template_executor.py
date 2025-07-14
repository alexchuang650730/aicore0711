#!/usr/bin/env python3
"""
UI测试模板执行器

将测试模板转换为Stagewise框架可执行的测试用例
"""

import json
import asyncio
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.components.stagewise_mcp.enhanced_testing_framework import (
    EnhancedStagewiseTestingFramework,
    TestCase, TestSuite, TestPriority, TestCategory, TestStatus
)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TestStep:
    """测试步骤数据类"""
    step_id: int
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    timeout: Optional[int] = None
    expected: Optional[str] = None
    description: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    filename: Optional[str] = None
    metric: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestStep':
        """从字典创建测试步骤，忽略未知参数"""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)
    
    def to_stagewise_action(self) -> Dict[str, Any]:
        """转换为Stagewise框架动作格式"""
        action_data = {
            "type": self.action,
            "description": self.description
        }
        
        if self.target:
            action_data["selector"] = self.target
        if self.value:
            action_data["value"] = self.value
        if self.timeout:
            action_data["timeout"] = self.timeout
        if self.expected:
            action_data["expected"] = self.expected
            
        return action_data


@dataclass
class TestScenario:
    """测试场景数据类"""
    scenario_id: str
    name: str
    description: str
    priority: str
    category: str
    estimated_duration: int
    pages: List[str]
    steps: List[TestStep]
    expected_results: List[str]
    test_data: Optional[Dict[str, Any]] = None
    viewports: Optional[List[Dict[str, Any]]] = None
    performance_thresholds: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestScenario':
        """从字典创建测试场景"""
        steps = [TestStep.from_dict(step) for step in data.get('steps', [])]
        return cls(
            scenario_id=data['scenario_id'],
            name=data['name'],
            description=data['description'],
            priority=data['priority'],
            category=data['category'],
            estimated_duration=data['estimated_duration'],
            pages=data['pages'],
            steps=steps,
            expected_results=data['expected_results'],
            test_data=data.get('test_data'),
            viewports=data.get('viewports'),
            performance_thresholds=data.get('performance_thresholds')
        )
    
    def to_stagewise_test_case(self) -> TestCase:
        """转换为Stagewise测试用例"""
        # 转换优先级
        priority_map = {
            "P0": TestPriority.P0,
            "P1": TestPriority.P1,
            "P2": TestPriority.P2
        }
        
        # 转换分类
        category_map = {
            "authentication": TestCategory.FUNCTIONAL,
            "navigation": TestCategory.FUNCTIONAL,
            "responsive": TestCategory.UI,
            "error_handling": TestCategory.FUNCTIONAL,
            "performance": TestCategory.PERFORMANCE
        }
        
        # 构建测试动作
        test_actions = []
        for step in self.steps:
            test_actions.append(step.to_stagewise_action())
        
        return TestCase(
            test_id=self.scenario_id,
            name=self.name,
            description=self.description,
            priority=priority_map.get(self.priority, TestPriority.P1),
            category=category_map.get(self.category, TestCategory.FUNCTIONAL),
            tags=[self.category, f"duration_{self.estimated_duration}s"],
            setup_actions=[],
            test_actions=test_actions,
            cleanup_actions=[],
            expected_results=self.expected_results,
            timeout=self.estimated_duration * 1000,  # 转换为毫秒
            retry_count=2,
            test_data=self.test_data or {}
        )


class UITestTemplateExecutor:
    """UI测试模板执行器"""
    
    def __init__(self, template_dir: str = "test_templates"):
        self.template_dir = Path(template_dir)
        self.scenarios_file = self.template_dir / "scenarios" / "ui_test_scenarios.json"
        self.pages_dir = self.template_dir / "pages"
        self.assets_dir = self.template_dir / "assets"
        self.framework = None
        self.scenarios: List[TestScenario] = []
        self.test_results = {}
        
        # 确保目录存在
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """初始化执行器"""
        try:
            # 初始化Stagewise框架
            self.framework = EnhancedStagewiseTestingFramework()
            
            # 加载测试场景
            await self.load_scenarios()
            
            # 注册测试用例到框架
            await self.register_test_cases()
            
            logger.info(f"UI测试模板执行器初始化成功，加载了 {len(self.scenarios)} 个测试场景")
            return True
            
        except Exception as e:
            logger.error(f"初始化UI测试模板执行器失败: {str(e)}")
            return False
    
    async def load_scenarios(self):
        """加载测试场景"""
        try:
            with open(self.scenarios_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.scenarios = []
            for scenario_data in data['test_scenarios']:
                scenario = TestScenario.from_dict(scenario_data)
                self.scenarios.append(scenario)
            
            logger.info(f"成功加载 {len(self.scenarios)} 个测试场景")
            
        except Exception as e:
            logger.error(f"加载测试场景失败: {str(e)}")
            raise
    
    async def register_test_cases(self):
        """注册测试用例到Stagewise框架"""
        try:
            for scenario in self.scenarios:
                test_case = scenario.to_stagewise_test_case()
                self.framework.register_test_case(test_case)
            
            logger.info(f"成功注册 {len(self.scenarios)} 个测试用例到Stagewise框架")
            
        except Exception as e:
            logger.error(f"注册测试用例失败: {str(e)}")
            raise
    
    async def execute_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """执行单个测试场景"""
        try:
            scenario = next((s for s in self.scenarios if s.scenario_id == scenario_id), None)
            if not scenario:
                raise ValueError(f"未找到测试场景: {scenario_id}")
            
            logger.info(f"开始执行测试场景: {scenario.name}")
            
            # 启动浏览器会话
            session = await self.framework.start_browser_session()
            
            # 设置基础URL
            base_url = f"file://{self.pages_dir.absolute()}"
            
            # 执行测试步骤
            step_results = []
            start_time = time.time()
            
            for step in scenario.steps:
                step_result = await self.execute_step(session, step, base_url)
                step_results.append(step_result)
                
                # 如果步骤失败且不是验证步骤，停止执行
                if not step_result['success'] and step.action != 'verify':
                    logger.warning(f"步骤 {step.step_id} 失败，停止执行")
                    break
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 计算成功率
            successful_steps = sum(1 for r in step_results if r['success'])
            success_rate = successful_steps / len(step_results) if step_results else 0
            
            result = {
                "scenario_id": scenario_id,
                "scenario_name": scenario.name,
                "status": "PASSED" if success_rate >= 0.8 else "FAILED",
                "duration": duration,
                "success_rate": success_rate,
                "total_steps": len(scenario.steps),
                "successful_steps": successful_steps,
                "step_results": step_results,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存结果
            self.test_results[scenario_id] = result
            
            logger.info(f"测试场景 {scenario.name} 执行完成: {result['status']} "
                       f"({successful_steps}/{len(step_results)} 步骤成功)")
            
            return result
            
        except Exception as e:
            logger.error(f"执行测试场景 {scenario_id} 失败: {str(e)}")
            return {
                "scenario_id": scenario_id,
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    async def execute_step(self, session, step: TestStep, base_url: str) -> Dict[str, Any]:
        """执行单个测试步骤"""
        try:
            logger.info(f"执行步骤 {step.step_id}: {step.description}")
            
            step_start = time.time()
            success = True
            error_message = None
            screenshot_path = None
            
            if step.action == "navigate":
                # 导航到页面
                url = f"{base_url}/{step.target}"
                await session.navigate(url)
                
            elif step.action == "wait":
                # 等待元素或时间
                timeout = step.timeout or 5000
                if step.target:
                    await session.wait_for_element(step.target, timeout)
                else:
                    await asyncio.sleep(timeout / 1000)
                    
            elif step.action == "input":
                # 输入文本
                await session.input_text(step.target, step.value)
                
            elif step.action == "click":
                # 点击元素
                await session.click_element(step.target)
                
            elif step.action == "verify":
                # 验证元素内容
                actual_text = await session.get_element_text(step.target)
                if step.expected not in actual_text:
                    success = False
                    error_message = f"验证失败: 期望包含 '{step.expected}', 实际为 '{actual_text}'"
                    
            elif step.action == "screenshot":
                # 截取屏幕截图
                screenshot_path = self.assets_dir / step.value
                await session.take_screenshot(str(screenshot_path))
                
            elif step.action == "set_viewport":
                # 设置视口大小
                await session.set_viewport(step.width, step.height)
                
            elif step.action == "accept_alert":
                # 接受警告对话框
                await session.accept_alert()
                
            elif step.action == "performance_start":
                # 开始性能监控
                await session.start_performance_monitoring()
                
            elif step.action == "performance_measure":
                # 测量性能指标
                metrics = await session.get_performance_metrics()
                logger.info(f"性能指标: {metrics}")
                
            elif step.action == "performance_end":
                # 结束性能监控
                await session.stop_performance_monitoring()
                
            else:
                logger.warning(f"未知的步骤动作: {step.action}")
            
            step_duration = time.time() - step_start
            
            return {
                "step_id": step.step_id,
                "action": step.action,
                "description": step.description,
                "success": success,
                "duration": step_duration,
                "error_message": error_message,
                "screenshot_path": str(screenshot_path) if screenshot_path else None
            }
            
        except Exception as e:
            step_duration = time.time() - step_start
            logger.error(f"步骤 {step.step_id} 执行失败: {str(e)}")
            
            return {
                "step_id": step.step_id,
                "action": step.action,
                "description": step.description,
                "success": False,
                "duration": step_duration,
                "error_message": str(e),
                "screenshot_path": None
            }
    
    async def execute_all_scenarios(self) -> Dict[str, Any]:
        """执行所有测试场景"""
        logger.info("开始执行所有测试场景...")
        
        all_results = {}
        start_time = time.time()
        
        for scenario in self.scenarios:
            result = await self.execute_scenario(scenario.scenario_id)
            all_results[scenario.scenario_id] = result
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 统计结果
        total_scenarios = len(all_results)
        passed_scenarios = sum(1 for r in all_results.values() if r.get('status') == 'PASSED')
        failed_scenarios = total_scenarios - passed_scenarios
        
        summary = {
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": failed_scenarios,
            "success_rate": passed_scenarios / total_scenarios if total_scenarios > 0 else 0,
            "total_duration": total_duration,
            "results": all_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"所有测试场景执行完成: {passed_scenarios}/{total_scenarios} 通过 "
                   f"({summary['success_rate']:.1%})")
        
        return summary
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成测试报告"""
        report_lines = [
            "# UI测试模板执行报告",
            "",
            f"**执行时间**: {results['timestamp']}",
            f"**总场景数**: {results['total_scenarios']}",
            f"**通过场景**: {results['passed_scenarios']}",
            f"**失败场景**: {results['failed_scenarios']}",
            f"**成功率**: {results['success_rate']:.1%}",
            f"**总耗时**: {results['total_duration']:.2f}秒",
            "",
            "## 详细结果",
            ""
        ]
        
        for scenario_id, result in results['results'].items():
            status_emoji = "✅" if result['status'] == 'PASSED' else "❌"
            report_lines.extend([
                f"### {status_emoji} {result.get('scenario_name', scenario_id)}",
                "",
                f"- **状态**: {result['status']}",
                f"- **耗时**: {result.get('duration', 0):.2f}秒",
                f"- **成功率**: {result.get('success_rate', 0):.1%}",
                ""
            ])
            
            if 'step_results' in result:
                report_lines.append("**步骤详情**:")
                for step in result['step_results']:
                    step_emoji = "✅" if step['success'] else "❌"
                    report_lines.append(f"- {step_emoji} 步骤{step['step_id']}: {step['description']} "
                                      f"({step['duration']:.2f}s)")
                    if step['error_message']:
                        report_lines.append(f"  - 错误: {step['error_message']}")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def save_report(self, results: Dict[str, Any], filename: str = None):
        """保存测试报告"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"ui_test_template_report_{timestamp}.md"
        
        report_content = self.generate_report(results)
        report_path = self.assets_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"测试报告已保存: {report_path}")
        return str(report_path)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="UI测试模板执行器")
    parser.add_argument("--scenario", help="执行指定的测试场景")
    parser.add_argument("--all", action="store_true", help="执行所有测试场景")
    parser.add_argument("--list", action="store_true", help="列出所有测试场景")
    parser.add_argument("--template-dir", default="test_templates", help="测试模板目录")
    
    args = parser.parse_args()
    
    try:
        # 创建执行器
        executor = UITestTemplateExecutor(args.template_dir)
        
        # 初始化
        if not await executor.initialize():
            print("❌ 执行器初始化失败")
            sys.exit(1)
        
        if args.list:
            # 列出所有测试场景
            print("📋 可用的测试场景:")
            for scenario in executor.scenarios:
                print(f"  - {scenario.scenario_id}: {scenario.name} [{scenario.priority}]")
                print(f"    {scenario.description}")
                print(f"    预计耗时: {scenario.estimated_duration}秒")
                print()
        
        elif args.scenario:
            # 执行指定场景
            print(f"🧪 执行测试场景: {args.scenario}")
            result = await executor.execute_scenario(args.scenario)
            
            if result['status'] == 'PASSED':
                print(f"✅ 测试场景执行成功")
            else:
                print(f"❌ 测试场景执行失败")
            
            print(f"详细结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        elif args.all:
            # 执行所有场景
            print("🚀 执行所有测试场景...")
            results = await executor.execute_all_scenarios()
            
            # 保存报告
            report_path = executor.save_report(results)
            
            print(f"\n📊 执行摘要:")
            print(f"  总场景数: {results['total_scenarios']}")
            print(f"  通过场景: {results['passed_scenarios']}")
            print(f"  失败场景: {results['failed_scenarios']}")
            print(f"  成功率: {results['success_rate']:.1%}")
            print(f"  总耗时: {results['total_duration']:.2f}秒")
            print(f"  报告文件: {report_path}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

