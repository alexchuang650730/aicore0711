#!/usr/bin/env python3
"""
PowerAutomation 4.0 Action Recognition Engine

智能动作识别算法引擎
实现用户操作的实时识别和分类
"""

import asyncio
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import cv2
import numpy as np
import pyautogui
import psutil
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import re

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """动作类型"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    DROP = "drop"
    SCROLL = "scroll"
    TYPE = "type"
    KEY_PRESS = "key_press"
    HOVER = "hover"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    VERIFY = "verify"


class ElementType(Enum):
    """元素类型"""
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    TEXT = "text"
    IMAGE = "image"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    MENU = "menu"
    DIALOG = "dialog"
    UNKNOWN = "unknown"


@dataclass
class ScreenElement:
    """屏幕元素"""
    element_id: str
    element_type: ElementType
    bounds: Tuple[int, int, int, int]  # x, y, width, height
    text: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    screenshot_path: Optional[str] = None


@dataclass
class UserAction:
    """用户动作"""
    action_id: str
    action_type: ActionType
    timestamp: datetime
    coordinates: Optional[Tuple[int, int]] = None
    target_element: Optional[ScreenElement] = None
    input_text: Optional[str] = None
    key_combination: Optional[str] = None
    scroll_direction: Optional[str] = None
    scroll_amount: Optional[int] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ActionRecognitionEngine:
    """动作识别引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.is_monitoring = False
        self.monitoring_thread = None
        self.action_callbacks: List[Callable] = []
        
        # 识别配置
        self.screenshot_interval = self.config.get('screenshot_interval', 0.1)  # 100ms
        self.mouse_sensitivity = self.config.get('mouse_sensitivity', 5)  # 像素
        self.text_recognition_enabled = self.config.get('text_recognition', True)
        
        # 状态跟踪
        self.last_mouse_pos = pyautogui.position()
        self.last_screenshot = None
        self.last_action_time = time.time()
        self.typing_buffer = ""
        self.typing_start_time = None
        
        # 元素识别缓存
        self.element_cache: Dict[str, ScreenElement] = {}
        self.cache_timeout = 5.0  # 5秒缓存超时
        
        # 动作历史
        self.action_history: List[UserAction] = []
        self.max_history = 1000
        
        # 初始化OCR
        self._init_ocr()
        
        logger.info("动作识别引擎初始化完成")
    
    def _init_ocr(self):
        """初始化OCR"""
        try:
            # 测试OCR是否可用
            test_image = Image.new('RGB', (100, 50), color='white')
            pytesseract.image_to_string(test_image)
            self.ocr_available = True
            logger.info("OCR初始化成功")
        except Exception as e:
            logger.warning(f"OCR初始化失败: {e}")
            self.ocr_available = False
    
    def add_action_callback(self, callback: Callable[[UserAction], None]):
        """添加动作回调函数"""
        self.action_callbacks.append(callback)
    
    def start_monitoring(self):
        """开始监控用户动作"""
        if self.is_monitoring:
            logger.warning("动作监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("开始监控用户动作")
    
    def stop_monitoring(self):
        """停止监控用户动作"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        logger.info("停止监控用户动作")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                current_time = time.time()
                
                # 检测鼠标动作
                self._detect_mouse_actions()
                
                # 检测键盘动作
                self._detect_keyboard_actions()
                
                # 检测屏幕变化
                if current_time - self.last_action_time > self.screenshot_interval:
                    self._detect_screen_changes()
                    self.last_action_time = current_time
                
                time.sleep(self.screenshot_interval)
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                time.sleep(1.0)
    
    def _detect_mouse_actions(self):
        """检测鼠标动作"""
        try:
            current_pos = pyautogui.position()
            
            # 检测鼠标移动
            if self._distance(current_pos, self.last_mouse_pos) > self.mouse_sensitivity:
                # 识别鼠标悬停的元素
                element = self._identify_element_at_position(current_pos)
                
                action = UserAction(
                    action_id=self._generate_action_id(),
                    action_type=ActionType.HOVER,
                    timestamp=datetime.now(),
                    coordinates=current_pos,
                    target_element=element
                )
                
                self._record_action(action)
                self.last_mouse_pos = current_pos
                
        except Exception as e:
            logger.error(f"鼠标动作检测错误: {e}")
    
    def _detect_keyboard_actions(self):
        """检测键盘动作"""
        # 注意：这里需要使用键盘钩子库如pynput来实现实时键盘监控
        # 由于安全限制，这里提供框架实现
        pass
    
    def _detect_screen_changes(self):
        """检测屏幕变化"""
        try:
            current_screenshot = pyautogui.screenshot()
            
            if self.last_screenshot is not None:
                # 比较屏幕变化
                diff_score = self._calculate_image_difference(
                    self.last_screenshot, current_screenshot
                )
                
                if diff_score > 0.1:  # 10%变化阈值
                    # 屏幕发生显著变化，可能有新的UI元素
                    self._update_element_cache(current_screenshot)
            
            self.last_screenshot = current_screenshot
            
        except Exception as e:
            logger.error(f"屏幕变化检测错误: {e}")
    
    def _identify_element_at_position(self, position: Tuple[int, int]) -> Optional[ScreenElement]:
        """识别指定位置的UI元素"""
        try:
            # 截取鼠标周围的小区域
            region_size = 100
            x, y = position
            region = (
                max(0, x - region_size // 2),
                max(0, y - region_size // 2),
                region_size,
                region_size
            )
            
            screenshot = pyautogui.screenshot(region=region)
            
            # 使用OCR识别文本
            text = None
            if self.ocr_available and self.text_recognition_enabled:
                try:
                    text = pytesseract.image_to_string(screenshot).strip()
                    if len(text) < 2:  # 过滤噪声
                        text = None
                except:
                    pass
            
            # 分析图像特征判断元素类型
            element_type = self._classify_element_type(screenshot, text)
            
            element = ScreenElement(
                element_id=f"element_{int(time.time() * 1000)}",
                element_type=element_type,
                bounds=(x - region_size // 2, y - region_size // 2, region_size, region_size),
                text=text,
                confidence=0.8
            )
            
            return element
            
        except Exception as e:
            logger.error(f"元素识别错误: {e}")
            return None
    
    def _classify_element_type(self, image: Image.Image, text: Optional[str]) -> ElementType:
        """分类元素类型"""
        try:
            # 转换为numpy数组进行分析
            img_array = np.array(image)
            
            # 分析颜色特征
            avg_color = np.mean(img_array, axis=(0, 1))
            
            # 检测边框（可能是按钮）
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 基于特征判断元素类型
            if text:
                text_lower = text.lower()
                if any(word in text_lower for word in ['button', 'btn', 'click', 'submit', 'ok', 'cancel']):
                    return ElementType.BUTTON
                elif any(word in text_lower for word in ['input', 'search', 'enter', 'type']):
                    return ElementType.INPUT
                elif any(word in text_lower for word in ['link', 'href', 'url']):
                    return ElementType.LINK
                else:
                    return ElementType.TEXT
            
            # 基于视觉特征判断
            if len(contours) > 0:
                # 有明显边框，可能是按钮或输入框
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                
                if area > 1000:  # 较大区域
                    return ElementType.BUTTON
                else:
                    return ElementType.INPUT
            
            return ElementType.UNKNOWN
            
        except Exception as e:
            logger.error(f"元素分类错误: {e}")
            return ElementType.UNKNOWN
    
    def _calculate_image_difference(self, img1: Image.Image, img2: Image.Image) -> float:
        """计算两张图片的差异度"""
        try:
            # 调整图片大小以提高性能
            size = (200, 150)
            img1_resized = img1.resize(size)
            img2_resized = img2.resize(size)
            
            # 转换为numpy数组
            arr1 = np.array(img1_resized)
            arr2 = np.array(img2_resized)
            
            # 计算像素差异
            diff = np.abs(arr1.astype(float) - arr2.astype(float))
            diff_score = np.mean(diff) / 255.0
            
            return diff_score
            
        except Exception as e:
            logger.error(f"图片差异计算错误: {e}")
            return 0.0
    
    def _update_element_cache(self, screenshot: Image.Image):
        """更新元素缓存"""
        try:
            # 清理过期缓存
            current_time = time.time()
            expired_keys = [
                key for key, element in self.element_cache.items()
                if current_time - element.attributes.get('cache_time', 0) > self.cache_timeout
            ]
            for key in expired_keys:
                del self.element_cache[key]
            
            # 这里可以实现更复杂的元素检测算法
            # 例如使用计算机视觉技术检测按钮、输入框等
            
        except Exception as e:
            logger.error(f"元素缓存更新错误: {e}")
    
    def _record_action(self, action: UserAction):
        """记录用户动作"""
        try:
            # 添加到历史记录
            self.action_history.append(action)
            
            # 限制历史记录长度
            if len(self.action_history) > self.max_history:
                self.action_history = self.action_history[-self.max_history:]
            
            # 调用回调函数
            for callback in self.action_callbacks:
                try:
                    callback(action)
                except Exception as e:
                    logger.error(f"动作回调错误: {e}")
            
            logger.debug(f"记录动作: {action.action_type.value} at {action.coordinates}")
            
        except Exception as e:
            logger.error(f"动作记录错误: {e}")
    
    def simulate_click_action(self, position: Tuple[int, int], button: str = "left") -> UserAction:
        """模拟点击动作（用于测试）"""
        element = self._identify_element_at_position(position)
        
        action_type = ActionType.CLICK
        if button == "right":
            action_type = ActionType.RIGHT_CLICK
        
        action = UserAction(
            action_id=self._generate_action_id(),
            action_type=action_type,
            timestamp=datetime.now(),
            coordinates=position,
            target_element=element
        )
        
        self._record_action(action)
        return action
    
    def simulate_type_action(self, text: str, position: Optional[Tuple[int, int]] = None) -> UserAction:
        """模拟输入动作（用于测试）"""
        element = None
        if position:
            element = self._identify_element_at_position(position)
        
        action = UserAction(
            action_id=self._generate_action_id(),
            action_type=ActionType.TYPE,
            timestamp=datetime.now(),
            coordinates=position,
            target_element=element,
            input_text=text
        )
        
        self._record_action(action)
        return action
    
    def simulate_scroll_action(self, position: Tuple[int, int], direction: str, amount: int = 3) -> UserAction:
        """模拟滚动动作（用于测试）"""
        element = self._identify_element_at_position(position)
        
        action = UserAction(
            action_id=self._generate_action_id(),
            action_type=ActionType.SCROLL,
            timestamp=datetime.now(),
            coordinates=position,
            target_element=element,
            scroll_direction=direction,
            scroll_amount=amount
        )
        
        self._record_action(action)
        return action
    
    def get_action_history(self, limit: Optional[int] = None) -> List[UserAction]:
        """获取动作历史"""
        if limit:
            return self.action_history[-limit:]
        return self.action_history.copy()
    
    def clear_action_history(self):
        """清空动作历史"""
        self.action_history.clear()
        logger.info("动作历史已清空")
    
    def export_actions_to_json(self, filepath: str):
        """导出动作到JSON文件"""
        try:
            actions_data = []
            for action in self.action_history:
                action_dict = {
                    'action_id': action.action_id,
                    'action_type': action.action_type.value,
                    'timestamp': action.timestamp.isoformat(),
                    'coordinates': action.coordinates,
                    'input_text': action.input_text,
                    'key_combination': action.key_combination,
                    'scroll_direction': action.scroll_direction,
                    'scroll_amount': action.scroll_amount,
                    'duration': action.duration,
                    'metadata': action.metadata
                }
                
                if action.target_element:
                    action_dict['target_element'] = {
                        'element_id': action.target_element.element_id,
                        'element_type': action.target_element.element_type.value,
                        'bounds': action.target_element.bounds,
                        'text': action.target_element.text,
                        'attributes': action.target_element.attributes,
                        'confidence': action.target_element.confidence
                    }
                
                actions_data.append(action_dict)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(actions_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"动作历史已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"动作导出错误: {e}")
    
    def _generate_action_id(self) -> str:
        """生成动作ID"""
        return f"action_{int(time.time() * 1000)}_{len(self.action_history)}"
    
    def _distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """计算两点距离"""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5


# 使用示例
async def demo_action_recognition():
    """动作识别演示"""
    engine = ActionRecognitionEngine()
    
    # 添加动作回调
    def on_action(action: UserAction):
        print(f"检测到动作: {action.action_type.value} at {action.coordinates}")
        if action.target_element and action.target_element.text:
            print(f"  目标元素: {action.target_element.text}")
    
    engine.add_action_callback(on_action)
    
    # 模拟一些动作
    print("模拟用户动作...")
    engine.simulate_click_action((100, 100))
    engine.simulate_type_action("Hello World", (200, 150))
    engine.simulate_scroll_action((300, 200), "down", 3)
    
    # 导出动作历史
    engine.export_actions_to_json("demo_actions.json")
    
    print(f"记录了 {len(engine.get_action_history())} 个动作")


if __name__ == "__main__":
    asyncio.run(demo_action_recognition())

