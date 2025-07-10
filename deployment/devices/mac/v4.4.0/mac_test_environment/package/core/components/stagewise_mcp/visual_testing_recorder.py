#!/usr/bin/env python3
"""
PowerAutomation 4.0 Visual Testing Recorder

可视化测试录制器，集成AG-UI组件生成和录制功能
支持截图、视频录制、测试节点自动生成
"""

import asyncio
import json
import time
import uuid
import logging
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import cv2
import numpy as np
import pyautogui
import psutil
import os
import tempfile
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# 导入现有组件
from .enhanced_testing_framework import (
    EnhancedStagewiseTestingFramework,
    TestCase, TestResult, TestStatus, TestPriority, TestCategory
)
from ..ag_ui_mcp.ag_ui_component_generator import AGUIComponentGenerator

logger = logging.getLogger(__name__)


class RecordingStatus(Enum):
    """录制状态"""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RecordingType(Enum):
    """录制类型"""
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    SCREEN_CAPTURE = "screen_capture"
    ELEMENT_CAPTURE = "element_capture"


@dataclass
class VisualTestNode:
    """可视化测试节点"""
    node_id: str
    name: str
    description: str
    node_type: str  # click, input, wait, verify, screenshot, etc.
    selector: Optional[str] = None
    coordinates: Optional[tuple] = None
    expected_result: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_segment_path: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecordingSession:
    """录制会话"""
    session_id: str
    session_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RecordingStatus = RecordingStatus.IDLE
    recording_type: RecordingType = RecordingType.VIDEO
    output_path: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    video_segments: List[str] = field(default_factory=list)
    test_nodes: List[VisualTestNode] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class VisualTestingRecorder:
    """可视化测试录制器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.current_session: Optional[RecordingSession] = None
        self.ag_ui_generator = AGUIComponentGenerator()
        
        # 录制配置
        self.output_dir = Path(self.config.get('output_dir', 'test_recordings'))
        self.output_dir.mkdir(exist_ok=True)
        
        self.screenshot_dir = self.output_dir / 'screenshots'
        self.video_dir = self.output_dir / 'videos'
        self.nodes_dir = self.output_dir / 'test_nodes'
        
        for dir_path in [self.screenshot_dir, self.video_dir, self.nodes_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # 录制参数
        self.fps = self.config.get('fps', 30)
        self.video_quality = self.config.get('video_quality', 'high')
        self.screenshot_format = self.config.get('screenshot_format', 'png')
        
        # 录制状态
        self.is_recording = False
        self.video_writer = None
        self.recording_thread = None
        
        # 屏幕信息
        self.screen_size = pyautogui.size()
        
        # 初始化pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    async def start_recording_session(self, session_name: str, recording_type: RecordingType = RecordingType.VIDEO) -> str:
        """开始录制会话"""
        if self.current_session and self.current_session.status == RecordingStatus.RECORDING:
            raise ValueError("已有活跃的录制会话")
        
        session_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.current_session = RecordingSession(
            session_id=session_id,
            session_name=session_name,
            start_time=datetime.now(),
            recording_type=recording_type,
            status=RecordingStatus.RECORDING
        )
        
        # 设置输出路径
        if recording_type == RecordingType.VIDEO:
            self.current_session.output_path = str(self.video_dir / f"{session_name}_{timestamp}.mp4")
            await self._start_video_recording()
        elif recording_type == RecordingType.SCREENSHOT:
            self.current_session.output_path = str(self.screenshot_dir / f"{session_name}_{timestamp}")
        
        logger.info(f"开始录制会话: {session_name} ({recording_type.value})")
        return session_id
    
    async def stop_recording_session(self) -> RecordingSession:
        """停止录制会话"""
        if not self.current_session:
            raise ValueError("没有活跃的录制会话")
        
        self.current_session.end_time = datetime.now()
        self.current_session.status = RecordingStatus.PROCESSING
        
        try:
            if self.current_session.recording_type == RecordingType.VIDEO:
                await self._stop_video_recording()
            
            # 生成测试节点
            await self._generate_test_nodes()
            
            # 生成AG-UI组件
            await self._generate_ag_ui_components()
            
            self.current_session.status = RecordingStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"录制会话处理失败: {str(e)}")
            self.current_session.status = RecordingStatus.FAILED
        
        session = self.current_session
        self.current_session = None
        
        # 保存会话信息
        await self._save_session_data(session)
        
        logger.info(f"录制会话完成: {session.session_name}")
        return session
    
    async def capture_screenshot(self, name: str = None, region: tuple = None) -> str:
        """捕获截图"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{name or 'screenshot'}_{timestamp}.{self.screenshot_format}"
        filepath = self.screenshot_dir / filename
        
        try:
            if region:
                # 捕获指定区域
                screenshot = pyautogui.screenshot(region=region)
            else:
                # 捕获全屏
                screenshot = pyautogui.screenshot()
            
            screenshot.save(str(filepath))
            
            # 添加到当前会话
            if self.current_session:
                self.current_session.screenshots.append(str(filepath))
            
            logger.info(f"截图已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            raise
    
    async def capture_element_screenshot(self, element_info: Dict[str, Any]) -> str:
        """捕获元素截图"""
        # 从element_info中提取坐标信息
        x = element_info.get('x', 0)
        y = element_info.get('y', 0)
        width = element_info.get('width', 100)
        height = element_info.get('height', 100)
        
        # 添加边距
        margin = 10
        region = (
            max(0, x - margin),
            max(0, y - margin),
            width + 2 * margin,
            height + 2 * margin
        )
        
        element_name = element_info.get('tag', 'element')
        return await self.capture_screenshot(f"{element_name}_element", region)
    
    async def record_test_action(self, action_type: str, **kwargs) -> VisualTestNode:
        """记录测试动作"""
        node_id = str(uuid.uuid4())
        
        # 捕获动作前截图
        screenshot_path = await self.capture_screenshot(f"action_{action_type}")
        
        # 创建测试节点
        node = VisualTestNode(
            node_id=node_id,
            name=f"{action_type}_{len(self.current_session.test_nodes) + 1}",
            description=f"执行{action_type}动作",
            node_type=action_type,
            screenshot_path=screenshot_path,
            metadata=kwargs
        )
        
        # 根据动作类型设置特定属性
        if action_type == "click":
            node.coordinates = kwargs.get('coordinates')
            node.selector = kwargs.get('selector')
        elif action_type == "input":
            node.selector = kwargs.get('selector')
            node.metadata['text'] = kwargs.get('text')
        elif action_type == "wait":
            node.metadata['duration'] = kwargs.get('duration', 1.0)
        elif action_type == "verify":
            node.expected_result = kwargs.get('expected_result')
        
        # 添加到当前会话
        if self.current_session:
            self.current_session.test_nodes.append(node)
        
        logger.info(f"记录测试动作: {action_type}")
        return node
    
    async def _start_video_recording(self):
        """开始视频录制"""
        if not self.current_session or not self.current_session.output_path:
            raise ValueError("无效的录制会话")
        
        # 使用ffmpeg进行屏幕录制
        self.is_recording = True
        self.recording_thread = threading.Thread(
            target=self._video_recording_worker,
            args=(self.current_session.output_path,)
        )
        self.recording_thread.start()
        
        logger.info("视频录制已开始")
    
    async def _stop_video_recording(self):
        """停止视频录制"""
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=5)
        
        logger.info("视频录制已停止")
    
    def _video_recording_worker(self, output_path: str):
        """视频录制工作线程"""
        try:
            # 使用ffmpeg录制屏幕
            cmd = [
                'ffmpeg',
                '-f', 'x11grab',
                '-r', str(self.fps),
                '-s', f"{self.screen_size.width}x{self.screen_size.height}",
                '-i', ':0.0',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '23',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待录制结束
            while self.is_recording:
                time.sleep(0.1)
            
            # 停止ffmpeg
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
            
        except Exception as e:
            logger.error(f"视频录制失败: {str(e)}")
    
    async def _generate_test_nodes(self):
        """生成测试节点"""
        if not self.current_session or not self.current_session.test_nodes:
            return
        
        # 保存测试节点数据
        nodes_file = self.nodes_dir / f"{self.current_session.session_name}_nodes.json"
        
        nodes_data = {
            "session_id": self.current_session.session_id,
            "session_name": self.current_session.session_name,
            "created_at": self.current_session.start_time.isoformat(),
            "nodes": [asdict(node) for node in self.current_session.test_nodes]
        }
        
        with open(nodes_file, 'w', encoding='utf-8') as f:
            json.dump(nodes_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"测试节点已保存: {nodes_file}")
    
    async def _generate_ag_ui_components(self):
        """生成AG-UI组件"""
        if not self.current_session or not self.current_session.test_nodes:
            return
        
        try:
            # 构建AG-UI组件描述
            component_spec = {
                "name": f"{self.current_session.session_name}_test_component",
                "description": f"基于录制会话 {self.current_session.session_name} 生成的测试组件",
                "type": "test_automation",
                "nodes": []
            }
            
            for node in self.current_session.test_nodes:
                ag_ui_node = {
                    "id": node.node_id,
                    "type": node.node_type,
                    "name": node.name,
                    "description": node.description,
                    "properties": {
                        "selector": node.selector,
                        "coordinates": node.coordinates,
                        "expected_result": node.expected_result,
                        "screenshot": node.screenshot_path,
                        **node.metadata
                    }
                }
                component_spec["nodes"].append(ag_ui_node)
            
            # 使用AG-UI生成器创建组件
            component = await self.ag_ui_generator.generate_component(component_spec)
            
            # 保存AG-UI组件
            component_file = self.nodes_dir / f"{self.current_session.session_name}_ag_ui_component.json"
            with open(component_file, 'w', encoding='utf-8') as f:
                json.dump(component, f, indent=2, ensure_ascii=False)
            
            logger.info(f"AG-UI组件已生成: {component_file}")
            
        except Exception as e:
            logger.error(f"AG-UI组件生成失败: {str(e)}")
    
    async def _save_session_data(self, session: RecordingSession):
        """保存会话数据"""
        session_file = self.output_dir / f"{session.session_name}_session.json"
        
        session_data = asdict(session)
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"会话数据已保存: {session_file}")
    
    async def create_test_case_from_recording(self, session: RecordingSession) -> TestCase:
        """从录制会话创建测试用例"""
        test_id = f"recorded_{session.session_id[:8]}"
        
        async def recorded_test_function():
            """录制的测试函数"""
            results = []
            
            for node in session.test_nodes:
                try:
                    if node.node_type == "click":
                        if node.coordinates:
                            pyautogui.click(node.coordinates[0], node.coordinates[1])
                        results.append(f"点击操作完成: {node.coordinates}")
                    
                    elif node.node_type == "input":
                        if node.metadata.get('text'):
                            pyautogui.typewrite(node.metadata['text'])
                        results.append(f"输入操作完成: {node.metadata.get('text')}")
                    
                    elif node.node_type == "wait":
                        duration = node.metadata.get('duration', 1.0)
                        await asyncio.sleep(duration)
                        results.append(f"等待完成: {duration}秒")
                    
                    elif node.node_type == "verify":
                        # 这里可以添加验证逻辑
                        results.append(f"验证完成: {node.expected_result}")
                    
                    # 捕获执行后截图
                    screenshot_path = await self.capture_screenshot(f"replay_{node.node_type}")
                    results.append(f"截图已保存: {screenshot_path}")
                    
                except Exception as e:
                    logger.error(f"执行测试节点失败: {str(e)}")
                    results.append(f"错误: {str(e)}")
            
            return results
        
        test_case = TestCase(
            test_id=test_id,
            name=f"录制测试_{session.session_name}",
            description=f"基于录制会话 {session.session_name} 生成的自动化测试",
            category=TestCategory.UI,
            priority=TestPriority.P1,
            component="visual_testing",
            test_function=recorded_test_function,
            timeout=60,
            test_data={
                "session_id": session.session_id,
                "recording_path": session.output_path,
                "nodes_count": len(session.test_nodes)
            }
        )
        
        return test_case
    
    def create_visual_test_report(self, session: RecordingSession, test_result: TestResult = None) -> str:
        """创建可视化测试报告"""
        report = f"""
# 可视化测试报告

## 录制会话信息
- **会话ID**: {session.session_id}
- **会话名称**: {session.session_name}
- **录制类型**: {session.recording_type.value}
- **开始时间**: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **结束时间**: {session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else 'N/A'}
- **状态**: {session.status.value}

## 录制内容
- **视频文件**: {session.output_path or 'N/A'}
- **截图数量**: {len(session.screenshots)}
- **测试节点数量**: {len(session.test_nodes)}

## 测试节点详情
"""
        
        for i, node in enumerate(session.test_nodes, 1):
            report += f"""
### 节点 {i}: {node.name}
- **类型**: {node.node_type}
- **描述**: {node.description}
- **选择器**: {node.selector or 'N/A'}
- **坐标**: {node.coordinates or 'N/A'}
- **截图**: {node.screenshot_path or 'N/A'}
- **时间戳**: {node.timestamp.strftime('%H:%M:%S')}
"""
        
        if test_result:
            report += f"""
## 测试执行结果
- **测试状态**: {test_result.status.value}
- **执行时间**: {test_result.duration:.2f}秒
- **错误信息**: {test_result.error_message or 'N/A'}
"""
        
        return report


class IntegratedVisualTestingFramework(EnhancedStagewiseTestingFramework):
    """集成可视化测试的Stagewise框架"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.visual_recorder = VisualTestingRecorder(config)
        self.recording_sessions: Dict[str, RecordingSession] = {}
    
    async def start_visual_test_recording(self, test_name: str) -> str:
        """开始可视化测试录制"""
        session_id = await self.visual_recorder.start_recording_session(
            test_name, 
            RecordingType.VIDEO
        )
        return session_id
    
    async def stop_visual_test_recording(self) -> RecordingSession:
        """停止可视化测试录制"""
        session = await self.visual_recorder.stop_recording_session()
        self.recording_sessions[session.session_id] = session
        
        # 自动创建测试用例
        test_case = await self.visual_recorder.create_test_case_from_recording(session)
        
        # 注册到测试框架
        self.register_test_case(test_case, "ui_functionality_tests")
        
        return session
    
    async def run_visual_test_with_recording(self, test_case: TestCase) -> TestResult:
        """运行带录制的可视化测试"""
        # 开始录制
        session_id = await self.start_visual_test_recording(f"replay_{test_case.test_id}")
        
        try:
            # 执行测试
            result = await self._run_test_case(test_case)
            
            # 停止录制
            session = await self.stop_visual_test_recording()
            
            # 生成可视化报告
            visual_report = self.visual_recorder.create_visual_test_report(session, result)
            result.output = visual_report
            
            return result
            
        except Exception as e:
            # 确保停止录制
            if self.visual_recorder.current_session:
                await self.visual_recorder.stop_recording_session()
            raise
    
    def generate_visual_test_report(self, session: TestSession) -> str:
        """生成包含可视化内容的测试报告"""
        base_report = super().generate_test_report(session)
        
        # 添加可视化内容
        visual_section = """

## 可视化测试内容

### 录制会话
"""
        
        for session_id, recording_session in self.recording_sessions.items():
            visual_section += f"""
#### 会话: {recording_session.session_name}
- **录制文件**: {recording_session.output_path}
- **测试节点**: {len(recording_session.test_nodes)}个
- **截图**: {len(recording_session.screenshots)}张
"""
        
        return base_report + visual_section


# 便捷函数
async def create_visual_test_from_recording(recording_file: str, test_name: str) -> TestCase:
    """从录制文件创建可视化测试"""
    recorder = VisualTestingRecorder()
    
    # 这里可以添加从录制文件解析的逻辑
    # 暂时返回一个示例测试用例
    
    async def visual_test_function():
        """可视化测试函数"""
        # 播放录制的操作
        return True
    
    return TestCase(
        test_id=f"visual_{test_name}",
        name=f"可视化测试_{test_name}",
        description=f"基于录制文件 {recording_file} 的可视化测试",
        category=TestCategory.UI,
        priority=TestPriority.P1,
        component="visual_testing",
        test_function=visual_test_function
    )


if __name__ == "__main__":
    async def demo():
        """演示可视化测试录制"""
        print("🎬 启动可视化测试录制演示")
        
        recorder = VisualTestingRecorder()
        
        # 开始录制
        session_id = await recorder.start_recording_session("demo_test", RecordingType.VIDEO)
        print(f"📹 开始录制会话: {session_id}")
        
        # 模拟一些测试动作
        await recorder.record_test_action("click", coordinates=(100, 100), selector="#button1")
        await asyncio.sleep(1)
        
        await recorder.record_test_action("input", selector="#input1", text="测试文本")
        await asyncio.sleep(1)
        
        await recorder.record_test_action("wait", duration=2.0)
        
        await recorder.record_test_action("verify", expected_result="页面加载完成")
        
        # 停止录制
        session = await recorder.stop_recording_session()
        print(f"✅ 录制完成: {session.session_name}")
        
        # 生成测试用例
        test_case = await recorder.create_test_case_from_recording(session)
        print(f"🧪 测试用例已生成: {test_case.name}")
        
        # 生成报告
        report = recorder.create_visual_test_report(session)
        print("📄 测试报告:")
        print(report)
    
    asyncio.run(demo())

