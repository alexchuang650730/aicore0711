"""
Recorder Workflow 集成到 Stagewise MCP

基于GitHub上的recorder_workflow_mcp实现，集成工作流录制功能到阶段式测试中
"""

import json
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import subprocess
import os

@dataclass
class WorkflowStep:
    """工作流步骤数据结构"""
    step_id: str
    stage: str
    action_type: str  # click, input, wait, verify, screenshot
    target: str
    value: Optional[str] = None
    timestamp: float = 0.0
    screenshot_path: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class WorkflowRecording:
    """工作流录制数据结构"""
    recording_id: str
    test_name: str
    stages: List[str]
    steps: List[WorkflowStep]
    start_time: float
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    success_rate: float = 0.0
    metadata: Dict[str, Any] = None

class RecorderWorkflowMCP:
    """
    Recorder Workflow MCP 组件
    工作流录制和管理的MCP组件
    
    基于原有Workflow Recorder核心功能，提供：
    - 工作流录制和管理
    - 录制数据整理和分析
    - 工作流步骤追踪
    - 录制结果导出
    - 智能工作流学习
    
    作者: PowerAutomation Team
    版本: 2.0.0
    日期: 2025-06-23
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 录制配置
        self.recording_dir = self.config.get('recording_dir', './recordings')
        self.screenshot_dir = self.config.get('screenshot_dir', './screenshots')
        self.video_dir = self.config.get('video_dir', './videos')
        
        # 确保目录存在
        os.makedirs(self.recording_dir, exist_ok=True)
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        
        # 当前录制状态
        self.current_recording: Optional[WorkflowRecording] = None
        self.is_recording = False
        
        # 录制历史
        self.recordings_history: List[WorkflowRecording] = []
        
        self.logger.info("RecorderWorkflowMCP 初始化完成")

    async def start_recording(self, test_name: str, stages: List[str]) -> str:
        """开始录制工作流"""
        try:
            recording_id = f"rec_{int(time.time())}_{test_name}"
            
            self.current_recording = WorkflowRecording(
                recording_id=recording_id,
                test_name=test_name,
                stages=stages,
                steps=[],
                start_time=time.time(),
                metadata={
                    'browser': 'chrome',
                    'resolution': '1920x1080',
                    'user_agent': 'ClaudEditor-Tester/4.1'
                }
            )
            
            self.is_recording = True
            
            # 开始屏幕录制
            await self._start_screen_recording(recording_id)
            
            self.logger.info(f"开始录制工作流: {test_name} (ID: {recording_id})")
            return recording_id
            
        except Exception as e:
            self.logger.error(f"开始录制失败: {str(e)}")
            raise

    async def record_step(self, 
                         stage: str,
                         action_type: str, 
                         target: str, 
                         value: str = None,
                         take_screenshot: bool = True) -> str:
        """录制单个步骤"""
        try:
            if not self.is_recording or not self.current_recording:
                raise ValueError("当前没有活跃的录制会话")
            
            step_id = f"step_{len(self.current_recording.steps) + 1}"
            timestamp = time.time()
            
            # 截图
            screenshot_path = None
            if take_screenshot:
                screenshot_path = await self._take_screenshot(step_id)
            
            step = WorkflowStep(
                step_id=step_id,
                stage=stage,
                action_type=action_type,
                target=target,
                value=value,
                timestamp=timestamp,
                screenshot_path=screenshot_path
            )
            
            self.current_recording.steps.append(step)
            
            self.logger.info(f"录制步骤: {action_type} -> {target}")
            return step_id
            
        except Exception as e:
            self.logger.error(f"录制步骤失败: {str(e)}")
            raise

    async def stop_recording(self) -> WorkflowRecording:
        """停止录制并保存"""
        try:
            if not self.is_recording or not self.current_recording:
                raise ValueError("当前没有活跃的录制会话")
            
            # 结束录制
            self.current_recording.end_time = time.time()
            self.current_recording.total_duration = (
                self.current_recording.end_time - self.current_recording.start_time
            )
            
            # 计算成功率
            successful_steps = sum(1 for step in self.current_recording.steps if step.success)
            total_steps = len(self.current_recording.steps)
            self.current_recording.success_rate = (
                successful_steps / total_steps if total_steps > 0 else 0.0
            )
            
            # 停止屏幕录制
            await self._stop_screen_recording()
            
            # 保存录制数据
            await self._save_recording(self.current_recording)
            
            # 添加到历史
            self.recordings_history.append(self.current_recording)
            
            recording = self.current_recording
            self.current_recording = None
            self.is_recording = False
            
            self.logger.info(f"录制完成: {recording.test_name}")
            return recording
            
        except Exception as e:
            self.logger.error(f"停止录制失败: {str(e)}")
            raise

    async def replay_recording(self, recording_id: str) -> Dict[str, Any]:
        """回放录制的工作流"""
        try:
            # 加载录制数据
            recording = await self._load_recording(recording_id)
            if not recording:
                raise ValueError(f"找不到录制: {recording_id}")
            
            replay_results = {
                'recording_id': recording_id,
                'start_time': time.time(),
                'steps_executed': 0,
                'steps_successful': 0,
                'errors': []
            }
            
            self.logger.info(f"开始回放录制: {recording.test_name}")
            
            # 逐步执行录制的操作
            for step in recording.steps:
                try:
                    await self._execute_step(step)
                    replay_results['steps_successful'] += 1
                    
                except Exception as e:
                    error_msg = f"步骤 {step.step_id} 执行失败: {str(e)}"
                    replay_results['errors'].append(error_msg)
                    self.logger.error(error_msg)
                
                replay_results['steps_executed'] += 1
                
                # 步骤间延迟
                await asyncio.sleep(0.5)
            
            replay_results['end_time'] = time.time()
            replay_results['duration'] = replay_results['end_time'] - replay_results['start_time']
            replay_results['success_rate'] = (
                replay_results['steps_successful'] / replay_results['steps_executed']
                if replay_results['steps_executed'] > 0 else 0.0
            )
            
            self.logger.info(f"回放完成，成功率: {replay_results['success_rate']:.2%}")
            return replay_results
            
        except Exception as e:
            self.logger.error(f"回放失败: {str(e)}")
            raise

    async def get_recording_analytics(self, recording_id: str = None) -> Dict[str, Any]:
        """获取录制分析数据"""
        try:
            if recording_id:
                recording = await self._load_recording(recording_id)
                recordings = [recording] if recording else []
            else:
                recordings = self.recordings_history
            
            if not recordings:
                return {'message': '没有找到录制数据'}
            
            analytics = {
                'total_recordings': len(recordings),
                'total_steps': sum(len(r.steps) for r in recordings),
                'average_duration': sum(r.total_duration or 0 for r in recordings) / len(recordings),
                'average_success_rate': sum(r.success_rate for r in recordings) / len(recordings),
                'stage_distribution': {},
                'action_distribution': {},
                'recent_recordings': []
            }
            
            # 阶段分布统计
            for recording in recordings:
                for stage in recording.stages:
                    analytics['stage_distribution'][stage] = (
                        analytics['stage_distribution'].get(stage, 0) + 1
                    )
            
            # 操作类型分布统计
            for recording in recordings:
                for step in recording.steps:
                    action = step.action_type
                    analytics['action_distribution'][action] = (
                        analytics['action_distribution'].get(action, 0) + 1
                    )
            
            # 最近的录制
            recent = sorted(recordings, key=lambda r: r.start_time, reverse=True)[:5]
            analytics['recent_recordings'] = [
                {
                    'recording_id': r.recording_id,
                    'test_name': r.test_name,
                    'duration': r.total_duration,
                    'success_rate': r.success_rate,
                    'steps_count': len(r.steps)
                }
                for r in recent
            ]
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"获取分析数据失败: {str(e)}")
            raise

    async def _start_screen_recording(self, recording_id: str):
        """开始屏幕录制"""
        try:
            video_path = os.path.join(self.video_dir, f"{recording_id}.mp4")
            
            # 使用ffmpeg进行屏幕录制 (Linux)
            cmd = [
                'ffmpeg', '-f', 'x11grab', '-r', '30', '-s', '1920x1080',
                '-i', ':0.0', '-c:v', 'libx264', '-preset', 'fast',
                '-y', video_path
            ]
            
            self.screen_recording_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            
            self.logger.info(f"开始屏幕录制: {video_path}")
            
        except Exception as e:
            self.logger.warning(f"屏幕录制启动失败: {str(e)}")

    async def _stop_screen_recording(self):
        """停止屏幕录制"""
        try:
            if hasattr(self, 'screen_recording_process'):
                self.screen_recording_process.terminate()
                self.screen_recording_process.wait()
                self.logger.info("屏幕录制已停止")
                
        except Exception as e:
            self.logger.warning(f"停止屏幕录制失败: {str(e)}")

    async def _take_screenshot(self, step_id: str) -> str:
        """截取屏幕截图"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(
                self.screenshot_dir, 
                f"{step_id}_{timestamp}.png"
            )
            
            # 使用scrot截图 (Linux)
            subprocess.run(['scrot', screenshot_path], check=True)
            
            return screenshot_path
            
        except Exception as e:
            self.logger.warning(f"截图失败: {str(e)}")
            return None

    async def _save_recording(self, recording: WorkflowRecording):
        """保存录制数据"""
        try:
            file_path = os.path.join(
                self.recording_dir, 
                f"{recording.recording_id}.json"
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(recording), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"录制数据已保存: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存录制数据失败: {str(e)}")
            raise

    async def _load_recording(self, recording_id: str) -> Optional[WorkflowRecording]:
        """加载录制数据"""
        try:
            file_path = os.path.join(self.recording_dir, f"{recording_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重构WorkflowStep对象
            steps = [WorkflowStep(**step_data) for step_data in data['steps']]
            data['steps'] = steps
            
            return WorkflowRecording(**data)
            
        except Exception as e:
            self.logger.error(f"加载录制数据失败: {str(e)}")
            return None

    async def _execute_step(self, step: WorkflowStep):
        """执行单个步骤 (回放时使用)"""
        # 这里需要根据实际的UI自动化框架来实现
        # 例如使用Selenium、Playwright等
        self.logger.info(f"执行步骤: {step.action_type} -> {step.target}")
        
        # 模拟执行延迟
        await asyncio.sleep(0.1)

# 导出主要类
__all__ = ['RecorderWorkflowMCP', 'WorkflowStep', 'WorkflowRecording']

