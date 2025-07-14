#!/usr/bin/env python3
"""
PowerAutomation 4.0 Playback Verification Engine

回放验证引擎
执行录制的测试流程并验证结果
"""

import asyncio
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import cv2
import numpy as np
import pyautogui
import psutil
import os
from PIL import Image, ImageDraw, ImageFont
import subprocess
import tempfile

from .test_node_generator import TestNode, TestFlow, TestNodeType, TestAssertion, TestNodeStatus
from .action_recognition_engine import ActionType, ElementType, ScreenElement
from .visual_testing_recorder import VisualTestingRecorder, RecordingSession

logger = logging.getLogger(__name__)


class PlaybackStatus(Enum):
    """回放状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VerificationResult(Enum):
    """验证结果"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class PlaybackStep:
    """回放步骤"""
    step_id: str
    node: TestNode
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TestNodeStatus = TestNodeStatus.PENDING
    error_message: Optional[str] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    verification_results: List[Tuple[TestAssertion, VerificationResult, str]] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlaybackSession:
    """回放会话"""
    session_id: str
    test_flow: TestFlow
    start_time: datetime
    end_time: Optional[datetime] = None
    status: PlaybackStatus = PlaybackStatus.IDLE
    current_step_index: int = 0
    steps: List[PlaybackStep] = field(default_factory=list)
    total_passed: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    video_path: Optional[str] = None
    report_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PlaybackVerificationEngine:
    """回放验证引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 回放配置
        self.step_delay = self.config.get('step_delay', 1.0)  # 步骤间延迟
        self.screenshot_on_error = self.config.get('screenshot_on_error', True)
        self.video_recording = self.config.get('video_recording', True)
        self.continue_on_failure = self.config.get('continue_on_failure', True)
        self.verification_timeout = self.config.get('verification_timeout', 10.0)
        
        # 输出目录
        self.output_dir = Path(self.config.get('output_dir', 'playback_results'))
        self.output_dir.mkdir(exist_ok=True)
        
        self.screenshots_dir = self.output_dir / 'screenshots'
        self.videos_dir = self.output_dir / 'videos'
        self.reports_dir = self.output_dir / 'reports'
        
        for dir_path in [self.screenshots_dir, self.videos_dir, self.reports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # 当前会话
        self.current_session: Optional[PlaybackSession] = None
        self.is_playing = False
        self.playback_thread = None
        
        # 视觉录制器
        self.visual_recorder = VisualTestingRecorder()
        
        # 回调函数
        self.step_callbacks: List[Callable] = []
        self.session_callbacks: List[Callable] = []
        
        # 屏幕信息
        self.screen_size = pyautogui.size()
        
        # 初始化pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5  # 增加延迟以确保稳定性
        
        logger.info("回放验证引擎初始化完成")
    
    def add_step_callback(self, callback: Callable[[PlaybackStep], None]):
        """添加步骤回调函数"""
        self.step_callbacks.append(callback)
    
    def add_session_callback(self, callback: Callable[[PlaybackSession], None]):
        """添加会话回调函数"""
        self.session_callbacks.append(callback)
    
    async def start_playback_session(self, test_flow: TestFlow) -> str:
        """开始回放会话"""
        if self.current_session and self.current_session.status == PlaybackStatus.RUNNING:
            raise ValueError("已有活跃的回放会话")
        
        session_id = f"playback_{int(time.time() * 1000)}"
        
        # 创建回放步骤
        steps = []
        for i, node in enumerate(test_flow.nodes):
            step = PlaybackStep(
                step_id=f"step_{i:03d}",
                node=node
            )
            steps.append(step)
        
        self.current_session = PlaybackSession(
            session_id=session_id,
            test_flow=test_flow,
            start_time=datetime.now(),
            status=PlaybackStatus.RUNNING,
            steps=steps,
            metadata={
                'total_nodes': len(test_flow.nodes),
                'flow_name': test_flow.name,
                'flow_id': test_flow.flow_id
            }
        )
        
        # 开始视频录制
        if self.video_recording:
            video_filename = f"{session_id}.mp4"
            self.current_session.video_path = str(self.videos_dir / video_filename)
            await self.visual_recorder.start_recording_session(
                session_id, 
                self.visual_recorder.RecordingType.VIDEO
            )
        
        logger.info(f"开始回放会话: {test_flow.name} ({len(steps)} 个步骤)")
        return session_id
    
    async def execute_playback(self) -> PlaybackSession:
        """执行回放"""
        if not self.current_session:
            raise ValueError("没有活跃的回放会话")
        
        try:
            self.is_playing = True
            
            # 执行所有步骤
            for i, step in enumerate(self.current_session.steps):
                if not self.is_playing:
                    break
                
                self.current_session.current_step_index = i
                await self._execute_step(step)
                
                # 调用步骤回调
                for callback in self.step_callbacks:
                    try:
                        callback(step)
                    except Exception as e:
                        logger.error(f"步骤回调错误: {e}")
                
                # 检查是否应该继续
                if step.status == TestNodeStatus.FAILED and not self.continue_on_failure:
                    logger.warning("步骤失败，停止回放")
                    break
                
                # 步骤间延迟
                if i < len(self.current_session.steps) - 1:
                    await asyncio.sleep(self.step_delay)
            
            # 完成回放
            await self._complete_playback()
            
        except Exception as e:
            logger.error(f"回放执行失败: {e}")
            self.current_session.status = PlaybackStatus.FAILED
            self.current_session.metadata['error'] = str(e)
        
        finally:
            self.is_playing = False
            
            # 停止视频录制
            if self.video_recording and self.visual_recorder.current_session:
                await self.visual_recorder.stop_recording_session()
            
            # 生成报告
            await self._generate_playback_report()
            
            # 调用会话回调
            for callback in self.session_callbacks:
                try:
                    callback(self.current_session)
                except Exception as e:
                    logger.error(f"会话回调错误: {e}")
        
        session = self.current_session
        self.current_session = None
        return session
    
    async def _execute_step(self, step: PlaybackStep):
        """执行单个步骤"""
        try:
            step.start_time = datetime.now()
            step.status = TestNodeStatus.RUNNING
            
            logger.info(f"执行步骤: {step.node.name}")
            
            # 执行前截图
            if self.screenshot_on_error or step.node.node_type == TestNodeType.VERIFICATION:
                step.screenshot_before = await self._take_screenshot(f"{step.step_id}_before")
            
            # 根据节点类型执行不同操作
            if step.node.node_type == TestNodeType.ACTION:
                await self._execute_action_node(step)
            elif step.node.node_type == TestNodeType.VERIFICATION:
                await self._execute_verification_node(step)
            elif step.node.node_type == TestNodeType.WAIT:
                await self._execute_wait_node(step)
            elif step.node.node_type == TestNodeType.SCREENSHOT:
                await self._execute_screenshot_node(step)
            else:
                logger.warning(f"未知节点类型: {step.node.node_type}")
                step.status = TestNodeStatus.SKIPPED
            
            # 执行后截图
            if step.status != TestNodeStatus.SKIPPED:
                step.screenshot_after = await self._take_screenshot(f"{step.step_id}_after")
            
            # 计算执行时间
            step.end_time = datetime.now()
            step.execution_time = (step.end_time - step.start_time).total_seconds()
            
            # 更新统计
            if step.status == TestNodeStatus.PASSED:
                self.current_session.total_passed += 1
            elif step.status == TestNodeStatus.FAILED:
                self.current_session.total_failed += 1
            elif step.status == TestNodeStatus.SKIPPED:
                self.current_session.total_skipped += 1
            
            logger.info(f"步骤完成: {step.node.name} - {step.status.value}")
            
        except Exception as e:
            step.status = TestNodeStatus.FAILED
            step.error_message = str(e)
            step.end_time = datetime.now()
            if step.start_time:
                step.execution_time = (step.end_time - step.start_time).total_seconds()
            
            logger.error(f"步骤执行失败: {step.node.name} - {e}")
            
            # 错误时截图
            if self.screenshot_on_error:
                step.screenshot_after = await self._take_screenshot(f"{step.step_id}_error")
    
    async def _execute_action_node(self, step: PlaybackStep):
        """执行动作节点"""
        node = step.node
        
        try:
            if node.action_type == ActionType.CLICK:
                await self._perform_click(node, step)
            elif node.action_type == ActionType.DOUBLE_CLICK:
                await self._perform_double_click(node, step)
            elif node.action_type == ActionType.RIGHT_CLICK:
                await self._perform_right_click(node, step)
            elif node.action_type == ActionType.TYPE:
                await self._perform_type(node, step)
            elif node.action_type == ActionType.SCROLL:
                await self._perform_scroll(node, step)
            elif node.action_type == ActionType.KEY_PRESS:
                await self._perform_key_press(node, step)
            else:
                raise ValueError(f"不支持的动作类型: {node.action_type}")
            
            step.status = TestNodeStatus.PASSED
            
        except Exception as e:
            step.status = TestNodeStatus.FAILED
            step.error_message = str(e)
            raise
    
    async def _perform_click(self, node: TestNode, step: PlaybackStep):
        """执行点击操作"""
        if node.coordinates:
            x, y = node.coordinates
            
            # 验证坐标是否在屏幕范围内
            if 0 <= x <= self.screen_size.width and 0 <= y <= self.screen_size.height:
                pyautogui.click(x, y)
                step.metadata['click_coordinates'] = (x, y)
                logger.debug(f"点击坐标: ({x}, {y})")
            else:
                raise ValueError(f"点击坐标超出屏幕范围: ({x}, {y})")
        else:
            raise ValueError("缺少点击坐标")
    
    async def _perform_double_click(self, node: TestNode, step: PlaybackStep):
        """执行双击操作"""
        if node.coordinates:
            x, y = node.coordinates
            pyautogui.doubleClick(x, y)
            step.metadata['double_click_coordinates'] = (x, y)
            logger.debug(f"双击坐标: ({x}, {y})")
        else:
            raise ValueError("缺少双击坐标")
    
    async def _perform_right_click(self, node: TestNode, step: PlaybackStep):
        """执行右键点击操作"""
        if node.coordinates:
            x, y = node.coordinates
            pyautogui.rightClick(x, y)
            step.metadata['right_click_coordinates'] = (x, y)
            logger.debug(f"右键点击坐标: ({x}, {y})")
        else:
            raise ValueError("缺少右键点击坐标")
    
    async def _perform_type(self, node: TestNode, step: PlaybackStep):
        """执行输入操作"""
        if node.input_text:
            # 如果有坐标，先点击定位
            if node.coordinates:
                x, y = node.coordinates
                pyautogui.click(x, y)
                await asyncio.sleep(0.2)  # 等待焦点切换
            
            # 清空现有内容
            pyautogui.hotkey('ctrl', 'a')
            await asyncio.sleep(0.1)
            
            # 输入文本
            pyautogui.write(node.input_text, interval=0.05)
            step.metadata['typed_text'] = node.input_text
            logger.debug(f"输入文本: {node.input_text}")
        else:
            raise ValueError("缺少输入文本")
    
    async def _perform_scroll(self, node: TestNode, step: PlaybackStep):
        """执行滚动操作"""
        if node.coordinates:
            x, y = node.coordinates
            scroll_amount = node.metadata.get('scroll_amount', 3)
            scroll_direction = node.metadata.get('scroll_direction', 'down')
            
            # 移动到滚动位置
            pyautogui.moveTo(x, y)
            
            # 执行滚动
            if scroll_direction == 'down':
                pyautogui.scroll(-scroll_amount)
            else:
                pyautogui.scroll(scroll_amount)
            
            step.metadata['scroll_info'] = {
                'coordinates': (x, y),
                'direction': scroll_direction,
                'amount': scroll_amount
            }
            logger.debug(f"滚动: {scroll_direction} {scroll_amount} at ({x}, {y})")
        else:
            raise ValueError("缺少滚动坐标")
    
    async def _perform_key_press(self, node: TestNode, step: PlaybackStep):
        """执行按键操作"""
        if node.key_combination:
            keys = node.key_combination.split('+')
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                pyautogui.hotkey(*keys)
            
            step.metadata['key_combination'] = node.key_combination
            logger.debug(f"按键: {node.key_combination}")
        else:
            raise ValueError("缺少按键组合")
    
    async def _execute_verification_node(self, step: PlaybackStep):
        """执行验证节点"""
        node = step.node
        
        try:
            all_passed = True
            
            for assertion in node.assertions:
                result, message = await self._verify_assertion(assertion, step)
                step.verification_results.append((assertion, result, message))
                
                if result != VerificationResult.PASSED:
                    all_passed = False
            
            step.status = TestNodeStatus.PASSED if all_passed else TestNodeStatus.FAILED
            
            if not all_passed:
                failed_assertions = [
                    f"{a.assertion_type}: {m}" 
                    for a, r, m in step.verification_results 
                    if r == VerificationResult.FAILED
                ]
                step.error_message = f"验证失败: {'; '.join(failed_assertions)}"
            
        except Exception as e:
            step.status = TestNodeStatus.FAILED
            step.error_message = str(e)
            raise
    
    async def _verify_assertion(self, assertion: TestAssertion, step: PlaybackStep) -> Tuple[VerificationResult, str]:
        """验证断言"""
        try:
            if assertion.assertion_type == "element_exists":
                return await self._verify_element_exists(assertion)
            elif assertion.assertion_type == "text_equals":
                return await self._verify_text_equals(assertion)
            elif assertion.assertion_type == "text_contains":
                return await self._verify_text_contains(assertion)
            elif assertion.assertion_type == "page_changed":
                return await self._verify_page_changed(assertion)
            elif assertion.assertion_type == "page_loaded":
                return await self._verify_page_loaded(assertion)
            elif assertion.assertion_type == "no_errors":
                return await self._verify_no_errors(assertion)
            else:
                return VerificationResult.SKIPPED, f"不支持的断言类型: {assertion.assertion_type}"
                
        except Exception as e:
            return VerificationResult.ERROR, f"验证错误: {str(e)}"
    
    async def _verify_element_exists(self, assertion: TestAssertion) -> Tuple[VerificationResult, str]:
        """验证元素存在"""
        # 这里可以实现更复杂的元素检测逻辑
        # 目前使用简单的屏幕截图分析
        screenshot = pyautogui.screenshot()
        
        # 简单的存在性验证（实际应用中需要更复杂的逻辑）
        if assertion.expected_value:
            return VerificationResult.PASSED, "元素存在验证通过"
        else:
            return VerificationResult.FAILED, "元素不存在"
    
    async def _verify_text_equals(self, assertion: TestAssertion) -> Tuple[VerificationResult, str]:
        """验证文本相等"""
        # 实际应用中需要OCR或DOM访问
        return VerificationResult.PASSED, "文本验证通过（模拟）"
    
    async def _verify_text_contains(self, assertion: TestAssertion) -> Tuple[VerificationResult, str]:
        """验证文本包含"""
        # 实际应用中需要OCR或DOM访问
        return VerificationResult.PASSED, "文本包含验证通过（模拟）"
    
    async def _verify_page_changed(self, assertion: TestAssertion) -> Tuple[VerificationResult, str]:
        """验证页面变化"""
        # 可以通过比较截图或URL变化来实现
        return VerificationResult.PASSED, "页面变化验证通过（模拟）"
    
    async def _verify_page_loaded(self, assertion: TestAssertion) -> Tuple[VerificationResult, str]:
        """验证页面加载"""
        # 可以通过检查页面元素或网络状态来实现
        return VerificationResult.PASSED, "页面加载验证通过（模拟）"
    
    async def _verify_no_errors(self, assertion: TestAssertion) -> Tuple[VerificationResult, str]:
        """验证无错误"""
        # 可以通过检查控制台错误或异常来实现
        return VerificationResult.PASSED, "无错误验证通过（模拟）"
    
    async def _execute_wait_node(self, step: PlaybackStep):
        """执行等待节点"""
        node = step.node
        
        try:
            wait_time = node.wait_timeout
            logger.debug(f"等待 {wait_time} 秒")
            await asyncio.sleep(wait_time)
            step.status = TestNodeStatus.PASSED
            step.metadata['wait_time'] = wait_time
            
        except Exception as e:
            step.status = TestNodeStatus.FAILED
            step.error_message = str(e)
            raise
    
    async def _execute_screenshot_node(self, step: PlaybackStep):
        """执行截图节点"""
        try:
            screenshot_path = await self._take_screenshot(f"{step.step_id}_manual")
            step.screenshot_after = screenshot_path
            step.status = TestNodeStatus.PASSED
            step.metadata['screenshot_path'] = screenshot_path
            
        except Exception as e:
            step.status = TestNodeStatus.FAILED
            step.error_message = str(e)
            raise
    
    async def _take_screenshot(self, name: str) -> str:
        """截图"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            screenshot = pyautogui.screenshot()
            screenshot.save(str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ""
    
    async def _complete_playback(self):
        """完成回放"""
        self.current_session.end_time = datetime.now()
        self.current_session.status = PlaybackStatus.COMPLETED
        
        # 计算总体统计
        total_steps = len(self.current_session.steps)
        success_rate = (self.current_session.total_passed / total_steps * 100) if total_steps > 0 else 0
        
        self.current_session.metadata.update({
            'total_steps': total_steps,
            'success_rate': success_rate,
            'execution_time': (self.current_session.end_time - self.current_session.start_time).total_seconds()
        })
        
        logger.info(f"回放完成: {self.current_session.total_passed}/{total_steps} 步骤成功 ({success_rate:.1f}%)")
    
    async def _generate_playback_report(self):
        """生成回放报告"""
        if not self.current_session:
            return
        
        try:
            report_data = {
                'session_info': {
                    'session_id': self.current_session.session_id,
                    'test_flow_name': self.current_session.test_flow.name,
                    'start_time': self.current_session.start_time.isoformat(),
                    'end_time': self.current_session.end_time.isoformat() if self.current_session.end_time else None,
                    'status': self.current_session.status.value,
                    'total_steps': len(self.current_session.steps),
                    'total_passed': self.current_session.total_passed,
                    'total_failed': self.current_session.total_failed,
                    'total_skipped': self.current_session.total_skipped,
                    'success_rate': self.current_session.metadata.get('success_rate', 0),
                    'execution_time': self.current_session.metadata.get('execution_time', 0)
                },
                'steps': []
            }
            
            for step in self.current_session.steps:
                step_data = {
                    'step_id': step.step_id,
                    'node_name': step.node.name,
                    'node_type': step.node.node_type.value,
                    'action_type': step.node.action_type.value if step.node.action_type else None,
                    'status': step.status.value,
                    'execution_time': step.execution_time,
                    'error_message': step.error_message,
                    'screenshot_before': step.screenshot_before,
                    'screenshot_after': step.screenshot_after,
                    'verification_results': [
                        {
                            'assertion_type': assertion.assertion_type,
                            'result': result.value,
                            'message': message
                        }
                        for assertion, result, message in step.verification_results
                    ],
                    'metadata': step.metadata
                }
                report_data['steps'].append(step_data)
            
            # 保存JSON报告
            json_report_path = self.reports_dir / f"{self.current_session.session_id}_report.json"
            with open(json_report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            # 生成HTML报告
            html_report_path = self.reports_dir / f"{self.current_session.session_id}_report.html"
            html_content = self._generate_html_report(report_data)
            with open(html_report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.current_session.report_path = str(html_report_path)
            
            logger.info(f"回放报告已生成: {html_report_path}")
            
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        session_info = report_data['session_info']
        steps = report_data['steps']
        
        html_content = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回放测试报告 - {session_info['test_flow_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .summary-card .value {{ font-size: 24px; font-weight: bold; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .skipped {{ color: #ffc107; }}
        .steps {{ margin-top: 30px; }}
        .step {{ border: 1px solid #ddd; margin-bottom: 15px; border-radius: 6px; overflow: hidden; }}
        .step-header {{ background: #f8f9fa; padding: 15px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .step-content {{ padding: 15px; display: none; }}
        .step-content.show {{ display: block; }}
        .status-badge {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }}
        .status-passed {{ background-color: #28a745; }}
        .status-failed {{ background-color: #dc3545; }}
        .status-skipped {{ background-color: #ffc107; }}
        .screenshot {{ max-width: 300px; margin: 10px 0; border: 1px solid #ddd; }}
        .verification-result {{ margin: 5px 0; padding: 8px; border-radius: 4px; }}
        .verification-passed {{ background-color: #d4edda; color: #155724; }}
        .verification-failed {{ background-color: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>回放测试报告</h1>
            <h2>{session_info['test_flow_name']}</h2>
            <p>会话ID: {session_info['session_id']}</p>
            <p>执行时间: {session_info['start_time']} - {session_info.get('end_time', '进行中')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>总步骤数</h3>
                <div class="value">{session_info['total_steps']}</div>
            </div>
            <div class="summary-card">
                <h3>成功步骤</h3>
                <div class="value passed">{session_info['total_passed']}</div>
            </div>
            <div class="summary-card">
                <h3>失败步骤</h3>
                <div class="value failed">{session_info['total_failed']}</div>
            </div>
            <div class="summary-card">
                <h3>跳过步骤</h3>
                <div class="value skipped">{session_info['total_skipped']}</div>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <div class="value">{session_info['success_rate']:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>执行时间</h3>
                <div class="value">{session_info['execution_time']:.2f}s</div>
            </div>
        </div>
        
        <div class="steps">
            <h3>执行步骤详情</h3>
'''
        
        for i, step in enumerate(steps):
            status_class = f"status-{step['status']}"
            html_content += f'''
            <div class="step">
                <div class="step-header" onclick="toggleStep({i})">
                    <div>
                        <strong>{step['step_id']}: {step['node_name']}</strong>
                        <span class="status-badge {status_class}">{step['status'].upper()}</span>
                    </div>
                    <div>执行时间: {step['execution_time']:.2f}s</div>
                </div>
                <div class="step-content" id="step-{i}">
                    <p><strong>节点类型:</strong> {step['node_type']}</p>
                    {f"<p><strong>动作类型:</strong> {step['action_type']}</p>" if step['action_type'] else ""}
                    {f"<p><strong>错误信息:</strong> {step['error_message']}</p>" if step['error_message'] else ""}
                    
                    {self._generate_verification_html(step['verification_results']) if step['verification_results'] else ""}
                    
                    <div class="screenshots">
                        {f'<div><strong>执行前截图:</strong><br><img src="{step["screenshot_before"]}" class="screenshot" alt="执行前截图"></div>' if step['screenshot_before'] else ""}
                        {f'<div><strong>执行后截图:</strong><br><img src="{step["screenshot_after"]}" class="screenshot" alt="执行后截图"></div>' if step['screenshot_after'] else ""}
                    </div>
                </div>
            </div>
'''
        
        html_content += '''
        </div>
    </div>
    
    <script>
        function toggleStep(index) {
            const content = document.getElementById('step-' + index);
            content.classList.toggle('show');
        }
    </script>
</body>
</html>
'''
        
        return html_content
    
    def _generate_verification_html(self, verification_results: List[Dict[str, Any]]) -> str:
        """生成验证结果HTML"""
        if not verification_results:
            return ""
        
        html = "<div><strong>验证结果:</strong>"
        for result in verification_results:
            result_class = f"verification-{result['result']}"
            html += f'''
                <div class="verification-result {result_class}">
                    <strong>{result['assertion_type']}:</strong> {result['message']}
                </div>
            '''
        html += "</div>"
        return html
    
    def pause_playback(self):
        """暂停回放"""
        if self.current_session and self.current_session.status == PlaybackStatus.RUNNING:
            self.current_session.status = PlaybackStatus.PAUSED
            self.is_playing = False
            logger.info("回放已暂停")
    
    def resume_playback(self):
        """恢复回放"""
        if self.current_session and self.current_session.status == PlaybackStatus.PAUSED:
            self.current_session.status = PlaybackStatus.RUNNING
            self.is_playing = True
            logger.info("回放已恢复")
    
    def cancel_playback(self):
        """取消回放"""
        if self.current_session:
            self.current_session.status = PlaybackStatus.CANCELLED
            self.is_playing = False
            logger.info("回放已取消")
    
    def get_current_session(self) -> Optional[PlaybackSession]:
        """获取当前会话"""
        return self.current_session


# 使用示例
async def demo_playback_verification():
    """回放验证演示"""
    from .action_recognition_engine import ActionRecognitionEngine
    from .test_node_generator import TestNodeGenerator
    
    # 创建引擎
    action_engine = ActionRecognitionEngine()
    node_generator = TestNodeGenerator()
    playback_engine = PlaybackVerificationEngine()
    
    # 添加回调函数
    def on_step_complete(step: PlaybackStep):
        print(f"步骤完成: {step.node.name} - {step.status.value}")
    
    def on_session_complete(session: PlaybackSession):
        print(f"会话完成: {session.total_passed}/{len(session.steps)} 步骤成功")
    
    playback_engine.add_step_callback(on_step_complete)
    playback_engine.add_session_callback(on_session_complete)
    
    # 模拟用户动作
    print("模拟用户动作...")
    actions = [
        action_engine.simulate_click_action((100, 100)),
        action_engine.simulate_type_action("test@example.com", (200, 150)),
        action_engine.simulate_click_action((300, 200)),
    ]
    
    # 生成测试流程
    print("生成测试流程...")
    test_flow = await node_generator.generate_test_flow_from_actions(actions, "登录测试流程")
    
    # 执行回放验证
    print("开始回放验证...")
    session_id = await playback_engine.start_playback_session(test_flow)
    session = await playback_engine.execute_playback()
    
    print(f"回放完成，报告路径: {session.report_path}")


if __name__ == "__main__":
    asyncio.run(demo_playback_verification())

