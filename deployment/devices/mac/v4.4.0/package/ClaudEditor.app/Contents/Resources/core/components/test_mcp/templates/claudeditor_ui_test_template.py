#!/usr/bin/env python3
"""
ClaudEditor UI自动化测试模板
集成 Stagewise MCP + Recorder Workflow MCP
支持完整的UI操作录制、回放和验证

作者: PowerAutomation Team
版本: 4.1
日期: 2025-01-07
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# 导入集成的MCP组件
from core.components.stagewise_mcp.stagewise_recorder_mcp import StagewiseRecorderMCP
from core.components.stagewise_mcp.recorder_workflow_integration import RecorderWorkflowIntegration

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    name: str
    description: str
    stage: str
    actions: List[Dict[str, Any]]
    expected_results: List[Dict[str, Any]]
    timeout: int = 60
    priority: str = "medium"  # high, medium, low
    tags: List[str] = None

@dataclass
class TestResult:
    """测试结果数据结构"""
    test_case_id: str
    status: str  # passed, failed, skipped, error
    execution_time: float
    error_message: Optional[str] = None
    screenshots: List[str] = None
    recording_path: Optional[str] = None
    stage_results: Dict[str, Any] = None

class ClaudEditorUITestTemplate:
    """ClaudEditor UI自动化测试模板"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化测试模板"""
        self.config = config or self._get_default_config()
        self.stagewise_recorder = StagewiseRecorderMCP()
        self.recorder_integration = RecorderWorkflowIntegration()
        self.test_results: List[TestResult] = []
        self.current_recording_id: Optional[str] = None
        
        # 创建测试输出目录
        self.output_dir = Path(self.config['output_directory'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ClaudEditor UI测试模板初始化完成")
        logger.info(f"输出目录: {self.output_dir}")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'base_url': 'http://localhost:3000',
            'api_base_url': 'http://localhost:5000',
            'output_directory': '/home/ubuntu/aicore0707/test_results',
            'screenshot_on_failure': True,
            'video_recording': True,
            'max_retry_attempts': 3,
            'default_timeout': 30,
            'browser_options': {
                'headless': False,
                'window_size': (1920, 1080),
                'user_agent': 'ClaudEditor-UITest/4.1'
            }
        }

    def get_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        return [
            # 基础功能测试
            TestCase(
                id="TC001",
                name="应用启动和加载测试",
                description="验证ClaudEditor应用能够正常启动和加载",
                stage="setup",
                actions=[
                    {"type": "navigate", "target": self.config['base_url'], "timeout": 10},
                    {"type": "wait", "target": "#app", "timeout": 5},
                    {"type": "verify", "target": "title", "value": "ClaudEditor"},
                    {"type": "screenshot", "name": "app_loaded"}
                ],
                expected_results=[
                    {"type": "element_visible", "target": "#app"},
                    {"type": "title_contains", "value": "ClaudEditor"}
                ],
                timeout=30,
                priority="high",
                tags=["smoke", "basic"]
            ),
            
            TestCase(
                id="TC002", 
                name="Monaco编辑器加载测试",
                description="验证Monaco编辑器能够正常加载和显示",
                stage="ui_load",
                actions=[
                    {"type": "wait", "target": ".monaco-editor", "timeout": 10},
                    {"type": "verify", "target": ".monaco-editor", "value": "visible"},
                    {"type": "click", "target": ".monaco-editor"},
                    {"type": "input", "target": ".monaco-editor textarea", "value": "console.log('Hello ClaudEditor');"},
                    {"type": "screenshot", "name": "monaco_editor_loaded"}
                ],
                expected_results=[
                    {"type": "element_visible", "target": ".monaco-editor"},
                    {"type": "text_contains", "target": ".monaco-editor", "value": "console.log"}
                ],
                timeout=45,
                priority="high",
                tags=["editor", "core"]
            ),

            TestCase(
                id="TC003",
                name="AI助手面板测试",
                description="验证AI助手面板的打开、关闭和基本功能",
                stage="user_interaction",
                actions=[
                    {"type": "click", "target": "#ai-assistant-toggle", "timeout": 5},
                    {"type": "wait", "target": "#ai-assistant-panel", "timeout": 5},
                    {"type": "verify", "target": "#ai-assistant-panel", "value": "visible"},
                    {"type": "click", "target": "#chat-tab"},
                    {"type": "input", "target": "#ai-input", "value": "解释这段代码的功能"},
                    {"type": "click", "target": "#send-button"},
                    {"type": "wait", "target": ".ai-response", "timeout": 15},
                    {"type": "screenshot", "name": "ai_assistant_response"}
                ],
                expected_results=[
                    {"type": "element_visible", "target": "#ai-assistant-panel"},
                    {"type": "element_visible", "target": ".ai-response"}
                ],
                timeout=60,
                priority="high", 
                tags=["ai", "assistant", "core"]
            ),

            TestCase(
                id="TC004",
                name="多模型选择测试",
                description="验证AI助手的多模型选择功能",
                stage="user_interaction",
                actions=[
                    {"type": "click", "target": "#model-selector"},
                    {"type": "wait", "target": ".model-options", "timeout": 3},
                    {"type": "click", "target": "[data-model='claude']"},
                    {"type": "verify", "target": "#selected-model", "value": "Claude 3.5 Sonnet"},
                    {"type": "click", "target": "#model-selector"},
                    {"type": "click", "target": "[data-model='gemini']"},
                    {"type": "verify", "target": "#selected-model", "value": "Gemini Pro"},
                    {"type": "screenshot", "name": "model_selection"}
                ],
                expected_results=[
                    {"type": "text_contains", "target": "#selected-model", "value": "Gemini"}
                ],
                timeout=30,
                priority="medium",
                tags=["ai", "models"]
            ),

            TestCase(
                id="TC005",
                name="工具管理器测试", 
                description="验证MCP-Zero Smart Engine工具管理功能",
                stage="user_interaction",
                actions=[
                    {"type": "click", "target": "#tool-manager-tab"},
                    {"type": "wait", "target": "#tool-discovery-panel", "timeout": 5},
                    {"type": "click", "target": "#discover-tools-btn"},
                    {"type": "wait", "target": ".tool-list", "timeout": 10},
                    {"type": "verify", "target": ".tool-item", "value": "visible"},
                    {"type": "click", "target": ".tool-item:first-child .recommend-btn"},
                    {"type": "wait", "target": ".recommendation-result", "timeout": 8},
                    {"type": "screenshot", "name": "tool_management"}
                ],
                expected_results=[
                    {"type": "element_count", "target": ".tool-item", "value": ">0"},
                    {"type": "element_visible", "target": ".recommendation-result"}
                ],
                timeout=45,
                priority="medium",
                tags=["tools", "mcp"]
            ),

            TestCase(
                id="TC006",
                name="实时协作测试",
                description="验证实时协作功能的基本操作",
                stage="user_interaction", 
                actions=[
                    {"type": "click", "target": "#collaboration-tab"},
                    {"type": "wait", "target": "#collaboration-panel", "timeout": 5},
                    {"type": "verify", "target": "#user-presence", "value": "visible"},
                    {"type": "input", "target": "#chat-input", "value": "测试协作聊天功能"},
                    {"type": "click", "target": "#send-chat-btn"},
                    {"type": "wait", "target": ".chat-message", "timeout": 5},
                    {"type": "screenshot", "name": "collaboration_test"}
                ],
                expected_results=[
                    {"type": "element_visible", "target": "#user-presence"},
                    {"type": "text_contains", "target": ".chat-message", "value": "测试协作聊天功能"}
                ],
                timeout=30,
                priority="medium",
                tags=["collaboration", "chat"]
            ),

            TestCase(
                id="TC007",
                name="API集成测试",
                description="验证前后端API集成功能",
                stage="api_testing",
                actions=[
                    {"type": "api_call", "method": "GET", "url": "/api/ai-assistant/health"},
                    {"type": "api_call", "method": "GET", "url": "/api/ai-assistant/models"},
                    {"type": "api_call", "method": "POST", "url": "/api/ai-assistant/process", 
                     "data": {"task": "code_explanation", "content": "console.log('test')", "model": "claude"}},
                    {"type": "verify_api_response", "status_code": 200}
                ],
                expected_results=[
                    {"type": "api_status", "value": 200},
                    {"type": "response_contains", "key": "models"},
                    {"type": "response_contains", "key": "response"}
                ],
                timeout=30,
                priority="high",
                tags=["api", "backend"]
            ),

            TestCase(
                id="TC008",
                name="性能监控测试",
                description="验证性能监控和统计功能",
                stage="performance",
                actions=[
                    {"type": "click", "target": "#monitoring-tab"},
                    {"type": "wait", "target": "#performance-stats", "timeout": 5},
                    {"type": "verify", "target": ".success-rate", "value": "visible"},
                    {"type": "verify", "target": ".response-time", "value": "visible"},
                    {"type": "verify", "target": ".cost-savings", "value": "visible"},
                    {"type": "screenshot", "name": "performance_monitoring"}
                ],
                expected_results=[
                    {"type": "element_visible", "target": ".success-rate"},
                    {"type": "element_visible", "target": ".response-time"}
                ],
                timeout=20,
                priority="medium",
                tags=["monitoring", "performance"]
            ),

            TestCase(
                id="TC009",
                name="端到端工作流测试",
                description="完整的编程助手工作流测试",
                stage="integration",
                actions=[
                    # 1. 编写代码
                    {"type": "click", "target": ".monaco-editor"},
                    {"type": "input", "target": ".monaco-editor textarea", 
                     "value": "function fibonacci(n) {\n  if (n <= 1) return n;\n  return fibonacci(n-1) + fibonacci(n-2);\n}"},
                    
                    # 2. 选择代码
                    {"type": "key_combination", "keys": ["Ctrl", "a"]},
                    
                    # 3. 请求AI优化
                    {"type": "click", "target": "#ai-assistant-toggle"},
                    {"type": "click", "target": "#optimize-btn"},
                    {"type": "wait", "target": ".ai-response", "timeout": 20},
                    
                    # 4. 验证响应
                    {"type": "verify", "target": ".ai-response", "value": "visible"},
                    {"type": "screenshot", "name": "end_to_end_workflow"}
                ],
                expected_results=[
                    {"type": "element_visible", "target": ".ai-response"},
                    {"type": "text_contains", "target": ".ai-response", "value": "优化"}
                ],
                timeout=90,
                priority="high",
                tags=["integration", "workflow", "e2e"]
            ),

            TestCase(
                id="TC010",
                name="错误处理测试",
                description="验证系统的错误处理和恢复能力",
                stage="integration",
                actions=[
                    # 测试无效API调用
                    {"type": "api_call", "method": "POST", "url": "/api/invalid-endpoint"},
                    {"type": "verify_api_response", "status_code": 404},
                    
                    # 测试UI错误处理
                    {"type": "click", "target": "#ai-assistant-toggle"},
                    {"type": "input", "target": "#ai-input", "value": ""},  # 空输入
                    {"type": "click", "target": "#send-button"},
                    {"type": "verify", "target": ".error-message", "value": "visible"},
                    {"type": "screenshot", "name": "error_handling"}
                ],
                expected_results=[
                    {"type": "api_status", "value": 404},
                    {"type": "element_visible", "target": ".error-message"}
                ],
                timeout=30,
                priority="medium",
                tags=["error", "handling"]
            )
        ]

    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """执行单个测试用例"""
        logger.info(f"开始执行测试用例: {test_case.id} - {test_case.name}")
        
        start_time = time.time()
        screenshots = []
        error_message = None
        stage_results = {}
        
        try:
            # 开始录制
            recording_id = await self.recorder_integration.start_recording(
                f"{test_case.id}_{test_case.name}",
                [test_case.stage]
            )
            self.current_recording_id = recording_id
            
            # 执行测试阶段
            stage_result = await self.stagewise_recorder.execute_stage(
                test_case.stage,
                test_case.actions
            )
            
            stage_results[test_case.stage] = stage_result
            
            # 验证预期结果
            verification_passed = await self._verify_expected_results(test_case.expected_results)
            
            # 停止录制
            recording = await self.recorder_integration.stop_recording()
            
            # 确定测试状态
            if stage_result.get('success', False) and verification_passed:
                status = "passed"
            else:
                status = "failed"
                error_message = stage_result.get('error', 'Verification failed')
                
        except Exception as e:
            status = "error"
            error_message = str(e)
            logger.error(f"测试用例 {test_case.id} 执行出错: {e}")
            
            # 错误时截图
            if self.config['screenshot_on_failure']:
                screenshot_path = await self._take_screenshot(f"{test_case.id}_error")
                screenshots.append(screenshot_path)
        
        execution_time = time.time() - start_time
        
        # 创建测试结果
        result = TestResult(
            test_case_id=test_case.id,
            status=status,
            execution_time=execution_time,
            error_message=error_message,
            screenshots=screenshots,
            recording_path=recording.get('video_path') if 'recording' in locals() else None,
            stage_results=stage_results
        )
        
        self.test_results.append(result)
        logger.info(f"测试用例 {test_case.id} 执行完成: {status} ({execution_time:.2f}s)")
        
        return result

    async def _verify_expected_results(self, expected_results: List[Dict[str, Any]]) -> bool:
        """验证预期结果"""
        for expected in expected_results:
            try:
                if expected['type'] == 'element_visible':
                    # 验证元素可见性
                    result = await self.stagewise_recorder.verify_element_visible(expected['target'])
                elif expected['type'] == 'text_contains':
                    # 验证文本内容
                    result = await self.stagewise_recorder.verify_text_contains(
                        expected['target'], expected['value']
                    )
                elif expected['type'] == 'api_status':
                    # 验证API状态码
                    result = await self.stagewise_recorder.verify_api_status(expected['value'])
                else:
                    logger.warning(f"未知的验证类型: {expected['type']}")
                    continue
                    
                if not result:
                    return False
                    
            except Exception as e:
                logger.error(f"验证失败: {e}")
                return False
                
        return True

    async def _take_screenshot(self, name: str) -> str:
        """截图"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        screenshot_path = self.output_dir / "screenshots" / filename
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 调用录制器的截图功能
        await self.recorder_integration.take_screenshot(str(screenshot_path))
        
        return str(screenshot_path)

    async def run_test_suite(self, test_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """运行完整的测试套件"""
        logger.info("开始运行ClaudEditor UI测试套件")
        
        test_cases = self.get_test_cases()
        
        # 应用过滤器
        if test_filter:
            test_cases = self._filter_test_cases(test_cases, test_filter)
        
        logger.info(f"将执行 {len(test_cases)} 个测试用例")
        
        # 初始化测试环境
        await self._setup_test_environment()
        
        # 执行测试用例
        for test_case in test_cases:
            await self.run_test_case(test_case)
            
            # 测试用例间的间隔
            await asyncio.sleep(1)
        
        # 清理测试环境
        await self._cleanup_test_environment()
        
        # 生成测试报告
        report = await self._generate_test_report()
        
        logger.info("测试套件执行完成")
        return report

    def _filter_test_cases(self, test_cases: List[TestCase], test_filter: Dict[str, Any]) -> List[TestCase]:
        """过滤测试用例"""
        filtered = test_cases
        
        if 'tags' in test_filter:
            filtered = [tc for tc in filtered if any(tag in tc.tags for tag in test_filter['tags'])]
        
        if 'priority' in test_filter:
            filtered = [tc for tc in filtered if tc.priority == test_filter['priority']]
        
        if 'stage' in test_filter:
            filtered = [tc for tc in filtered if tc.stage == test_filter['stage']]
            
        return filtered

    async def _setup_test_environment(self):
        """设置测试环境"""
        logger.info("设置测试环境...")
        
        # 启动必要的服务
        await self.stagewise_recorder.setup_environment()
        
        # 验证服务可用性
        await self._verify_services()

    async def _cleanup_test_environment(self):
        """清理测试环境"""
        logger.info("清理测试环境...")
        
        # 停止录制（如果还在录制）
        if self.current_recording_id:
            await self.recorder_integration.stop_recording()
        
        # 清理临时数据
        await self.stagewise_recorder.cleanup_environment()

    async def _verify_services(self):
        """验证服务可用性"""
        # 验证前端服务
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(self.config['base_url']) as response:
                    if response.status != 200:
                        raise Exception(f"前端服务不可用: {response.status}")
        except Exception as e:
            logger.error(f"前端服务验证失败: {e}")
            raise
        
        # 验证后端API
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config['api_base_url']}/api/ai-assistant/health") as response:
                    if response.status != 200:
                        raise Exception(f"后端API不可用: {response.status}")
        except Exception as e:
            logger.error(f"后端API验证失败: {e}")
            raise

    async def _generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "passed"])
        failed_tests = len([r for r in self.test_results if r.status == "failed"])
        error_tests = len([r for r in self.test_results if r.status == "error"])
        
        total_time = sum(r.execution_time for r in self.test_results)
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_execution_time': total_time,
                'timestamp': datetime.now().isoformat()
            },
            'test_results': [asdict(result) for result in self.test_results],
            'config': self.config
        }
        
        # 保存报告到文件
        report_path = self.output_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已保存: {report_path}")
        logger.info(f"测试总结: {passed_tests}/{total_tests} 通过 ({report['summary']['success_rate']:.1f}%)")
        
        return report

# 快速执行脚本
async def main():
    """主执行函数"""
    # 创建测试模板实例
    test_template = ClaudEditorUITestTemplate()
    
    # 运行测试套件
    # 可以使用过滤器只运行特定测试
    test_filter = {
        'tags': ['smoke', 'core'],  # 只运行核心功能测试
        # 'priority': 'high',  # 只运行高优先级测试
        # 'stage': 'user_interaction'  # 只运行特定阶段测试
    }
    
    report = await test_template.run_test_suite(test_filter)
    
    print("\n" + "="*50)
    print("ClaudEditor UI测试完成!")
    print(f"通过率: {report['summary']['success_rate']:.1f}%")
    print(f"总耗时: {report['summary']['total_execution_time']:.2f}秒")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())

