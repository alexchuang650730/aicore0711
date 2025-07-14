#!/usr/bin/env python3
"""
PowerAutomation 4.0 Record-as-Test Orchestrator

录制即测试编排器
集成完整的录制即测试流程
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import uuid

from .action_recognition_engine import ActionRecognitionEngine, UserAction, ActionType
from .test_node_generator import TestNodeGenerator, TestFlow, TestNode
from .ag_ui_auto_generator import AGUIAutoGenerator, AGUITestSuite
from .playback_verification_engine import PlaybackVerificationEngine, PlaybackSession
from .visual_testing_recorder import VisualTestingRecorder, RecordingSession

logger = logging.getLogger(__name__)


class RecordAsTestStatus(Enum):
    """录制即测试状态"""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    GENERATING = "generating"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowPhase(Enum):
    """工作流阶段"""
    SETUP = "setup"
    RECORDING = "recording"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    VERIFICATION = "verification"
    EXPORT = "export"
    CLEANUP = "cleanup"


@dataclass
class RecordAsTestConfig:
    """录制即测试配置"""
    # 录制配置
    auto_start_recording: bool = True
    recording_timeout: float = 300.0  # 5分钟
    min_actions_required: int = 3
    
    # 生成配置
    generate_react_components: bool = True
    generate_vue_components: bool = False
    generate_html_components: bool = True
    component_prefix: str = "Test"
    
    # 验证配置
    auto_playback_verification: bool = True
    continue_on_verification_failure: bool = True
    verification_timeout: float = 60.0
    
    # 输出配置
    output_directory: str = "record_as_test_output"
    export_components: bool = True
    export_test_suite: bool = True
    export_playback_report: bool = True
    
    # 高级配置
    enable_ai_optimization: bool = True
    enable_smart_assertions: bool = True
    enable_visual_validation: bool = True


@dataclass
class RecordAsTestSession:
    """录制即测试会话"""
    session_id: str
    name: str
    description: str
    config: RecordAsTestConfig
    
    # 状态信息
    status: RecordAsTestStatus = RecordAsTestStatus.IDLE
    current_phase: WorkflowPhase = WorkflowPhase.SETUP
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # 数据存储
    recorded_actions: List[UserAction] = field(default_factory=list)
    generated_test_flow: Optional[TestFlow] = None
    generated_components: Optional[AGUITestSuite] = None
    playback_session: Optional[PlaybackSession] = None
    
    # 输出路径
    output_directory: Optional[str] = None
    component_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    report_files: List[str] = field(default_factory=list)
    
    # 统计信息
    total_actions: int = 0
    total_nodes: int = 0
    total_components: int = 0
    success_rate: float = 0.0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class RecordAsTestOrchestrator:
    """录制即测试编排器"""
    
    def __init__(self, config: RecordAsTestConfig = None):
        self.config = config or RecordAsTestConfig()
        
        # 初始化各个引擎
        self.action_engine = ActionRecognitionEngine()
        self.node_generator = TestNodeGenerator()
        self.ag_ui_generator = AGUIAutoGenerator({
            'generate_react': self.config.generate_react_components,
            'generate_vue': self.config.generate_vue_components,
            'generate_html': self.config.generate_html_components,
            'component_prefix': self.config.component_prefix
        })
        self.playback_engine = PlaybackVerificationEngine({
            'continue_on_failure': self.config.continue_on_verification_failure,
            'verification_timeout': self.config.verification_timeout
        })
        self.visual_recorder = VisualTestingRecorder()
        
        # 当前会话
        self.current_session: Optional[RecordAsTestSession] = None
        self.is_running = False
        
        # 回调函数
        self.phase_callbacks: Dict[WorkflowPhase, List[Callable]] = {
            phase: [] for phase in WorkflowPhase
        }
        self.status_callbacks: List[Callable] = []
        self.progress_callbacks: List[Callable] = []
        
        # 输出目录
        self.base_output_dir = Path(self.config.output_directory)
        self.base_output_dir.mkdir(exist_ok=True)
        
        logger.info("录制即测试编排器初始化完成")
    
    def add_phase_callback(self, phase: WorkflowPhase, callback: Callable):
        """添加阶段回调"""
        self.phase_callbacks[phase].append(callback)
    
    def add_status_callback(self, callback: Callable):
        """添加状态回调"""
        self.status_callbacks.append(callback)
    
    def add_progress_callback(self, callback: Callable):
        """添加进度回调"""
        self.progress_callbacks.append(callback)
    
    async def start_record_as_test_session(
        self, 
        name: str, 
        description: str = "",
        custom_config: Dict[str, Any] = None
    ) -> str:
        """开始录制即测试会话"""
        
        if self.current_session and self.current_session.status in [
            RecordAsTestStatus.RECORDING, 
            RecordAsTestStatus.PROCESSING,
            RecordAsTestStatus.GENERATING,
            RecordAsTestStatus.TESTING
        ]:
            raise ValueError("已有活跃的录制即测试会话")
        
        # 合并配置
        session_config = RecordAsTestConfig(**asdict(self.config))
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(session_config, key):
                    setattr(session_config, key, value)
        
        # 创建会话
        session_id = f"rat_{int(time.time() * 1000)}"
        self.current_session = RecordAsTestSession(
            session_id=session_id,
            name=name,
            description=description,
            config=session_config
        )
        
        # 创建输出目录
        session_output_dir = self.base_output_dir / session_id
        session_output_dir.mkdir(exist_ok=True)
        self.current_session.output_directory = str(session_output_dir)
        
        logger.info(f"开始录制即测试会话: {name} (ID: {session_id})")
        
        # 如果配置了自动开始录制，则立即开始
        if session_config.auto_start_recording:
            await self._start_recording_phase()
        
        return session_id
    
    async def execute_complete_workflow(self) -> RecordAsTestSession:
        """执行完整的录制即测试工作流"""
        if not self.current_session:
            raise ValueError("没有活跃的会话")
        
        try:
            self.is_running = True
            self.current_session.status = RecordAsTestStatus.RECORDING
            
            # 阶段1: 设置
            await self._execute_phase(WorkflowPhase.SETUP)
            
            # 阶段2: 录制（如果还没开始）
            if self.current_session.current_phase != WorkflowPhase.RECORDING:
                await self._execute_phase(WorkflowPhase.RECORDING)
            
            # 阶段3: 分析
            await self._execute_phase(WorkflowPhase.ANALYSIS)
            
            # 阶段4: 生成
            await self._execute_phase(WorkflowPhase.GENERATION)
            
            # 阶段5: 验证
            if self.current_session.config.auto_playback_verification:
                await self._execute_phase(WorkflowPhase.VERIFICATION)
            
            # 阶段6: 导出
            await self._execute_phase(WorkflowPhase.EXPORT)
            
            # 阶段7: 清理
            await self._execute_phase(WorkflowPhase.CLEANUP)
            
            # 完成
            self.current_session.status = RecordAsTestStatus.COMPLETED
            self.current_session.end_time = datetime.now()
            
            logger.info(f"录制即测试工作流完成: {self.current_session.name}")
            
        except Exception as e:
            logger.error(f"录制即测试工作流失败: {e}")
            self.current_session.status = RecordAsTestStatus.FAILED
            self.current_session.errors.append(str(e))
            self.current_session.end_time = datetime.now()
            raise
        
        finally:
            self.is_running = False
            await self._notify_status_change()
        
        session = self.current_session
        self.current_session = None
        return session
    
    async def _execute_phase(self, phase: WorkflowPhase):
        """执行工作流阶段"""
        logger.info(f"开始执行阶段: {phase.value}")
        self.current_session.current_phase = phase
        
        try:
            # 调用阶段前回调
            for callback in self.phase_callbacks[phase]:
                try:
                    await callback(self.current_session, "start")
                except Exception as e:
                    logger.error(f"阶段回调错误: {e}")
            
            # 执行阶段逻辑
            if phase == WorkflowPhase.SETUP:
                await self._setup_phase()
            elif phase == WorkflowPhase.RECORDING:
                await self._recording_phase()
            elif phase == WorkflowPhase.ANALYSIS:
                await self._analysis_phase()
            elif phase == WorkflowPhase.GENERATION:
                await self._generation_phase()
            elif phase == WorkflowPhase.VERIFICATION:
                await self._verification_phase()
            elif phase == WorkflowPhase.EXPORT:
                await self._export_phase()
            elif phase == WorkflowPhase.CLEANUP:
                await self._cleanup_phase()
            
            # 调用阶段后回调
            for callback in self.phase_callbacks[phase]:
                try:
                    await callback(self.current_session, "complete")
                except Exception as e:
                    logger.error(f"阶段回调错误: {e}")
            
            logger.info(f"阶段完成: {phase.value}")
            
        except Exception as e:
            logger.error(f"阶段执行失败: {phase.value} - {e}")
            self.current_session.errors.append(f"{phase.value}: {str(e)}")
            raise
    
    async def _setup_phase(self):
        """设置阶段"""
        # 初始化各个引擎
        await self._notify_progress("初始化录制引擎...")
        
        # 设置动作引擎回调
        def on_action_detected(action: UserAction):
            if self.current_session and self.current_session.status == RecordAsTestStatus.RECORDING:
                self.current_session.recorded_actions.append(action)
                self.current_session.total_actions = len(self.current_session.recorded_actions)
                logger.debug(f"检测到动作: {action.action_type.value}")
        
        self.action_engine.add_action_callback(on_action_detected)
        
        # 设置回放引擎回调
        def on_playback_step(step):
            logger.debug(f"回放步骤: {step.node.name} - {step.status.value}")
        
        self.playback_engine.add_step_callback(on_playback_step)
        
        await self._notify_progress("设置完成")
    
    async def _start_recording_phase(self):
        """开始录制阶段"""
        self.current_session.current_phase = WorkflowPhase.RECORDING
        self.current_session.status = RecordAsTestStatus.RECORDING
        
        # 开始动作监控
        await self._notify_progress("开始录制用户动作...")
        self.action_engine.start_monitoring()
        
        # 开始视觉录制
        if self.current_session.config.enable_visual_validation:
            await self.visual_recorder.start_recording_session(
                self.current_session.session_id,
                self.visual_recorder.RecordingType.VIDEO
            )
        
        await self._notify_status_change()
        logger.info("录制阶段已开始，等待用户操作...")
    
    async def _recording_phase(self):
        """录制阶段"""
        if not self.action_engine.is_monitoring:
            await self._start_recording_phase()
        
        # 等待录制完成（由外部调用stop_recording）
        await self._notify_progress("正在录制用户动作...")
        
        # 这里可以添加超时逻辑
        start_time = time.time()
        while (self.current_session.status == RecordAsTestStatus.RECORDING and 
               self.is_running and
               time.time() - start_time < self.current_session.config.recording_timeout):
            await asyncio.sleep(0.5)
        
        # 停止录制
        await self.stop_recording()
    
    async def stop_recording(self):
        """停止录制"""
        if not self.current_session or self.current_session.status != RecordAsTestStatus.RECORDING:
            return
        
        logger.info("停止录制...")
        
        # 停止动作监控
        self.action_engine.stop_monitoring()
        
        # 停止视觉录制
        if self.visual_recorder.current_session:
            await self.visual_recorder.stop_recording_session()
        
        # 检查录制结果
        if len(self.current_session.recorded_actions) < self.current_session.config.min_actions_required:
            raise ValueError(f"录制的动作数量不足，至少需要 {self.current_session.config.min_actions_required} 个动作")
        
        self.current_session.status = RecordAsTestStatus.PROCESSING
        await self._notify_status_change()
        
        logger.info(f"录制完成，共录制 {len(self.current_session.recorded_actions)} 个动作")
    
    async def _analysis_phase(self):
        """分析阶段"""
        await self._notify_progress("分析录制的动作...")
        
        # 生成测试流程
        self.current_session.generated_test_flow = await self.node_generator.generate_test_flow_from_actions(
            self.current_session.recorded_actions,
            self.current_session.name
        )
        
        self.current_session.total_nodes = len(self.current_session.generated_test_flow.nodes)
        
        # AI优化（如果启用）
        if self.current_session.config.enable_ai_optimization:
            await self._optimize_test_flow()
        
        # 智能断言生成（如果启用）
        if self.current_session.config.enable_smart_assertions:
            await self._generate_smart_assertions()
        
        await self._notify_progress(f"分析完成，生成 {self.current_session.total_nodes} 个测试节点")
    
    async def _generation_phase(self):
        """生成阶段"""
        self.current_session.status = RecordAsTestStatus.GENERATING
        await self._notify_status_change()
        
        await self._notify_progress("生成AG-UI组件...")
        
        # 生成AG-UI组件
        self.current_session.generated_components = await self.ag_ui_generator.generate_components_from_test_flow(
            self.current_session.generated_test_flow
        )
        
        self.current_session.total_components = len(self.current_session.generated_components.components)
        
        await self._notify_progress(f"生成完成，创建 {self.current_session.total_components} 个组件")
    
    async def _verification_phase(self):
        """验证阶段"""
        self.current_session.status = RecordAsTestStatus.TESTING
        await self._notify_status_change()
        
        await self._notify_progress("开始回放验证...")
        
        # 执行回放验证
        session_id = await self.playback_engine.start_playback_session(
            self.current_session.generated_test_flow
        )
        
        self.current_session.playback_session = await self.playback_engine.execute_playback()
        
        # 计算成功率
        if self.current_session.playback_session:
            total_steps = len(self.current_session.playback_session.steps)
            if total_steps > 0:
                self.current_session.success_rate = (
                    self.current_session.playback_session.total_passed / total_steps * 100
                )
        
        await self._notify_progress(f"验证完成，成功率: {self.current_session.success_rate:.1f}%")
    
    async def _export_phase(self):
        """导出阶段"""
        await self._notify_progress("导出结果...")
        
        output_dir = Path(self.current_session.output_directory)
        
        # 导出组件文件
        if self.current_session.config.export_components and self.current_session.generated_components:
            components_dir = output_dir / "components"
            self.ag_ui_generator.export_test_suite_to_files(
                self.current_session.generated_components,
                str(components_dir)
            )
            
            # 记录导出的文件
            for file_path in components_dir.rglob("*"):
                if file_path.is_file():
                    if file_path.suffix in ['.tsx', '.vue', '.html']:
                        self.current_session.component_files.append(str(file_path))
                    elif file_path.suffix in ['.test.tsx', '.test.js']:
                        self.current_session.test_files.append(str(file_path))
        
        # 导出测试套件数据
        if self.current_session.config.export_test_suite:
            test_suite_file = output_dir / "test_suite.json"
            with open(test_suite_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.current_session.generated_test_flow), f, indent=2, ensure_ascii=False, default=str)
            self.current_session.test_files.append(str(test_suite_file))
        
        # 导出回放报告
        if (self.current_session.config.export_playback_report and 
            self.current_session.playback_session and 
            self.current_session.playback_session.report_path):
            # 报告已经在回放引擎中生成
            self.current_session.report_files.append(self.current_session.playback_session.report_path)
        
        # 导出会话摘要
        await self._export_session_summary()
        
        await self._notify_progress("导出完成")
    
    async def _cleanup_phase(self):
        """清理阶段"""
        await self._notify_progress("清理资源...")
        
        # 清理临时文件
        # 停止所有监控
        if self.action_engine.is_monitoring:
            self.action_engine.stop_monitoring()
        
        # 清理回调
        self.action_engine.clear_callbacks()
        
        await self._notify_progress("清理完成")
    
    async def _optimize_test_flow(self):
        """AI优化测试流程"""
        # 这里可以实现AI优化逻辑
        # 例如：合并相似的动作、优化等待时间、添加智能断言等
        logger.debug("执行AI优化...")
        pass
    
    async def _generate_smart_assertions(self):
        """生成智能断言"""
        # 这里可以实现智能断言生成逻辑
        # 例如：基于页面变化自动生成验证点
        logger.debug("生成智能断言...")
        pass
    
    async def _export_session_summary(self):
        """导出会话摘要"""
        output_dir = Path(self.current_session.output_directory)
        summary_file = output_dir / "session_summary.json"
        
        summary_data = {
            'session_info': {
                'session_id': self.current_session.session_id,
                'name': self.current_session.name,
                'description': self.current_session.description,
                'start_time': self.current_session.start_time.isoformat(),
                'end_time': self.current_session.end_time.isoformat() if self.current_session.end_time else None,
                'status': self.current_session.status.value,
                'success_rate': self.current_session.success_rate
            },
            'statistics': {
                'total_actions': self.current_session.total_actions,
                'total_nodes': self.current_session.total_nodes,
                'total_components': self.current_session.total_components,
                'component_files_count': len(self.current_session.component_files),
                'test_files_count': len(self.current_session.test_files),
                'report_files_count': len(self.current_session.report_files)
            },
            'output_files': {
                'component_files': self.current_session.component_files,
                'test_files': self.current_session.test_files,
                'report_files': self.current_session.report_files
            },
            'config': asdict(self.current_session.config),
            'errors': self.current_session.errors,
            'metadata': self.current_session.metadata
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        self.current_session.report_files.append(str(summary_file))
    
    async def _notify_status_change(self):
        """通知状态变化"""
        for callback in self.status_callbacks:
            try:
                await callback(self.current_session)
            except Exception as e:
                logger.error(f"状态回调错误: {e}")
    
    async def _notify_progress(self, message: str):
        """通知进度"""
        logger.info(message)
        for callback in self.progress_callbacks:
            try:
                await callback(self.current_session, message)
            except Exception as e:
                logger.error(f"进度回调错误: {e}")
    
    def get_current_session(self) -> Optional[RecordAsTestSession]:
        """获取当前会话"""
        return self.current_session
    
    def cancel_session(self):
        """取消当前会话"""
        if self.current_session:
            self.current_session.status = RecordAsTestStatus.CANCELLED
            self.is_running = False
            
            # 停止录制
            if self.action_engine.is_monitoring:
                self.action_engine.stop_monitoring()
            
            logger.info("会话已取消")


# CLI接口
class RecordAsTestCLI:
    """录制即测试命令行接口"""
    
    def __init__(self):
        self.orchestrator = RecordAsTestOrchestrator()
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置回调函数"""
        async def on_status_change(session):
            print(f"状态变化: {session.status.value}")
        
        async def on_progress(session, message):
            print(f"进度: {message}")
        
        self.orchestrator.add_status_callback(on_status_change)
        self.orchestrator.add_progress_callback(on_progress)
    
    async def start_interactive_session(self):
        """开始交互式会话"""
        print("🎬 录制即测试 - 交互式模式")
        print("=" * 50)
        
        # 获取用户输入
        name = input("请输入测试名称: ").strip() or "交互式测试"
        description = input("请输入测试描述 (可选): ").strip()
        
        print(f"\n开始录制测试: {name}")
        print("请在浏览器中执行您要测试的操作...")
        print("完成后按 Enter 键停止录制")
        
        # 开始会话
        session_id = await self.orchestrator.start_record_as_test_session(name, description)
        
        # 等待用户完成操作
        input("\n按 Enter 键停止录制...")
        
        # 执行完整工作流
        print("\n开始处理录制的动作...")
        session = await self.orchestrator.execute_complete_workflow()
        
        # 显示结果
        self._display_results(session)
    
    def _display_results(self, session: RecordAsTestSession):
        """显示结果"""
        print("\n" + "=" * 50)
        print("🎉 录制即测试完成!")
        print("=" * 50)
        
        print(f"会话ID: {session.session_id}")
        print(f"测试名称: {session.name}")
        print(f"状态: {session.status.value}")
        print(f"录制动作数: {session.total_actions}")
        print(f"生成节点数: {session.total_nodes}")
        print(f"生成组件数: {session.total_components}")
        print(f"验证成功率: {session.success_rate:.1f}%")
        
        if session.component_files:
            print(f"\n📁 生成的组件文件 ({len(session.component_files)} 个):")
            for file_path in session.component_files[:5]:  # 只显示前5个
                print(f"  - {file_path}")
            if len(session.component_files) > 5:
                print(f"  ... 还有 {len(session.component_files) - 5} 个文件")
        
        if session.report_files:
            print(f"\n📊 生成的报告文件:")
            for file_path in session.report_files:
                print(f"  - {file_path}")
        
        print(f"\n📂 输出目录: {session.output_directory}")
        
        if session.errors:
            print(f"\n⚠️  错误信息:")
            for error in session.errors:
                print(f"  - {error}")


# 使用示例
async def demo_record_as_test():
    """录制即测试演示"""
    # 创建配置
    config = RecordAsTestConfig(
        auto_start_recording=True,
        generate_react_components=True,
        auto_playback_verification=True,
        export_components=True
    )
    
    # 创建编排器
    orchestrator = RecordAsTestOrchestrator(config)
    
    # 添加回调
    async def on_status_change(session):
        print(f"状态: {session.status.value}")
    
    async def on_progress(session, message):
        print(f"进度: {message}")
    
    orchestrator.add_status_callback(on_status_change)
    orchestrator.add_progress_callback(on_progress)
    
    # 开始会话
    print("开始录制即测试演示...")
    session_id = await orchestrator.start_record_as_test_session(
        "演示测试",
        "这是一个录制即测试的演示"
    )
    
    # 模拟一些用户操作（实际使用中用户会真实操作）
    await asyncio.sleep(2)  # 模拟用户操作时间
    
    # 执行完整工作流
    session = await orchestrator.execute_complete_workflow()
    
    print(f"\n演示完成!")
    print(f"生成了 {session.total_components} 个组件")
    print(f"输出目录: {session.output_directory}")


if __name__ == "__main__":
    # 运行CLI模式
    cli = RecordAsTestCLI()
    asyncio.run(cli.start_interactive_session())

