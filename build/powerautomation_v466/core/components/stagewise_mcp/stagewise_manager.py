"""
Stagewise MCP - 階段式錄製回放系統
PowerAutomation v4.6.1 智能UI測試錄製與回放平台

基於aicore0707的Stagewise MCP實現，提供：
- 智能UI操作錄製
- 自動化測試生成
- 元素識別和定位
- 可視化測試流程
"""

import asyncio
import logging
import time
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """操作類型枚舉"""
    CLICK = "click"
    TYPE = "type"
    HOVER = "hover"
    SCROLL = "scroll"
    DRAG = "drag"
    WAIT = "wait"
    VERIFY = "verify"
    NAVIGATE = "navigate"


class ElementLocatorType(Enum):
    """元素定位類型"""
    ID = "id"
    CLASS = "class"
    XPATH = "xpath"
    CSS_SELECTOR = "css_selector"
    TEXT = "text"
    ATTRIBUTE = "attribute"


@dataclass
class ElementInfo:
    """元素信息"""
    tag_name: str
    attributes: Dict[str, str]
    text_content: str
    xpath: str
    css_selector: str
    bounding_rect: Dict[str, float]
    screenshot: Optional[str] = None  # base64編碼的截圖
    
    def get_best_locator(self) -> Tuple[ElementLocatorType, str]:
        """獲取最佳定位器"""
        # 優先級：id > class > xpath > css_selector
        if "id" in self.attributes and self.attributes["id"]:
            return ElementLocatorType.ID, f"#{self.attributes['id']}"
        elif "class" in self.attributes and self.attributes["class"]:
            classes = self.attributes["class"].split()
            return ElementLocatorType.CLASS, f".{classes[0]}"
        elif self.xpath:
            return ElementLocatorType.XPATH, self.xpath
        else:
            return ElementLocatorType.CSS_SELECTOR, self.css_selector


@dataclass
class RecordedAction:
    """錄製的操作"""
    id: str
    action_type: ActionType
    timestamp: str
    element_info: Optional[ElementInfo]
    input_value: Optional[str] = None
    coordinates: Optional[Tuple[int, int]] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    wait_time: Optional[float] = None
    verification_target: Optional[str] = None
    verification_value: Optional[str] = None


@dataclass
class RecordingSession:
    """錄製會話"""
    id: str
    name: str
    description: str
    start_time: str
    end_time: Optional[str]
    status: str  # 'recording', 'completed', 'failed'
    actions: List[RecordedAction]
    metadata: Dict[str, Any]
    total_duration: Optional[float] = None


class ElementInspector:
    """元素檢查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def inspect_element(self, element_data: Dict[str, Any]) -> ElementInfo:
        """檢查元素並提取信息"""
        # 模擬元素檢查邏輯
        element_info = ElementInfo(
            tag_name=element_data.get("tagName", "div"),
            attributes=element_data.get("attributes", {}),
            text_content=element_data.get("textContent", ""),
            xpath=element_data.get("xpath", ""),
            css_selector=element_data.get("cssSelector", ""),
            bounding_rect=element_data.get("boundingRect", {
                "x": 0, "y": 0, "width": 100, "height": 30
            })
        )
        
        return element_info
    
    async def generate_smart_locators(self, element_info: ElementInfo) -> List[Tuple[ElementLocatorType, str]]:
        """生成智能定位器"""
        locators = []
        
        # ID定位器
        if "id" in element_info.attributes and element_info.attributes["id"]:
            locators.append((ElementLocatorType.ID, f"#{element_info.attributes['id']}"))
        
        # Class定位器
        if "class" in element_info.attributes and element_info.attributes["class"]:
            classes = element_info.attributes["class"].split()
            for cls in classes:
                locators.append((ElementLocatorType.CLASS, f".{cls}"))
        
        # 文本定位器
        if element_info.text_content.strip():
            locators.append((ElementLocatorType.TEXT, element_info.text_content.strip()))
        
        # XPath定位器
        if element_info.xpath:
            locators.append((ElementLocatorType.XPATH, element_info.xpath))
        
        # CSS選擇器
        if element_info.css_selector:
            locators.append((ElementLocatorType.CSS_SELECTOR, element_info.css_selector))
        
        return locators


class ActionRecognitionEngine:
    """操作識別引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def recognize_action(self, event_data: Dict[str, Any]) -> ActionType:
        """識別用戶操作類型"""
        event_type = event_data.get("type", "")
        
        action_mapping = {
            "click": ActionType.CLICK,
            "dblclick": ActionType.CLICK,
            "input": ActionType.TYPE,
            "keydown": ActionType.TYPE,
            "mouseover": ActionType.HOVER,
            "scroll": ActionType.SCROLL,
            "dragstart": ActionType.DRAG,
            "navigation": ActionType.NAVIGATE
        }
        
        return action_mapping.get(event_type, ActionType.CLICK)
    
    async def enhance_action_with_context(self, action: RecordedAction, context: Dict[str, Any]) -> RecordedAction:
        """使用上下文增強操作"""
        # 添加智能等待時間
        if action.action_type in [ActionType.CLICK, ActionType.TYPE]:
            action.wait_time = context.get("suggested_wait", 1.0)
        
        # 添加驗證目標
        if action.action_type == ActionType.CLICK:
            action.verification_target = context.get("expected_change", "page_load")
        
        return action


class CodeGenerator:
    """代碼生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_selenium_test(self, session: RecordingSession) -> str:
        """生成Selenium測試代碼"""
        test_code_lines = [
            "import pytest",
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
            "from selenium.webdriver.common.action_chains import ActionChains",
            "import time",
            "",
            "",
            f"class Test{session.name.replace(' ', '')}:",
            f'    """基於Stagewise錄製生成的測試: {session.description}"""',
            "",
            "    def setup_method(self):",
            "        self.driver = webdriver.Chrome()",
            "        self.wait = WebDriverWait(self.driver, 10)",
            "",
            "    def teardown_method(self):",
            "        self.driver.quit()",
            "",
            f"    def test_{session.name.lower().replace(' ', '_')}(self):",
            f'        """執行錄製的測試場景: {session.description}"""'
        ]
        
        for i, action in enumerate(session.actions):
            test_code_lines.extend(self._generate_action_code(action, i + 1))
        
        return "\n".join(test_code_lines)
    
    def _generate_action_code(self, action: RecordedAction, step_number: int) -> List[str]:
        """生成單個操作的代碼"""
        lines = [f"        # 步驟 {step_number}: {action.action_type.value}"]
        
        if action.action_type == ActionType.NAVIGATE:
            lines.append(f'        self.driver.get("{action.input_value}")')
        
        elif action.action_type == ActionType.CLICK:
            if action.element_info:
                locator_type, locator_value = action.element_info.get_best_locator()
                if locator_type == ElementLocatorType.ID:
                    lines.append(f'        element = self.wait.until(EC.element_to_be_clickable((By.ID, "{locator_value[1:]}")))') 
                elif locator_type == ElementLocatorType.CLASS:
                    lines.append(f'        element = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "{locator_value[1:]}")))') 
                else:
                    lines.append(f'        element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "{locator_value}")))')
                lines.append("        element.click()")
        
        elif action.action_type == ActionType.TYPE:
            if action.element_info and action.input_value:
                locator_type, locator_value = action.element_info.get_best_locator()
                if locator_type == ElementLocatorType.ID:
                    lines.append(f'        element = self.wait.until(EC.presence_of_element_located((By.ID, "{locator_value[1:]}")))') 
                else:
                    lines.append(f'        element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "{locator_value}")))')
                lines.append("        element.clear()")
                lines.append(f'        element.send_keys("{action.input_value}")')
        
        elif action.action_type == ActionType.WAIT:
            if action.wait_time:
                lines.append(f"        time.sleep({action.wait_time})")
        
        # 添加等待時間
        if action.wait_time and action.action_type != ActionType.WAIT:
            lines.append(f"        time.sleep({action.wait_time})")
        
        lines.append("")
        return lines
    
    async def generate_playwright_test(self, session: RecordingSession) -> str:
        """生成Playwright測試代碼"""
        test_code_lines = [
            "import pytest",
            "from playwright.async_api import async_playwright, Page, Browser",
            "import asyncio",
            "",
            "",
            f"class Test{session.name.replace(' ', '')}:",
            f'    """基於Stagewise錄製生成的Playwright測試: {session.description}"""',
            "",
            "    async def setup_method(self):",
            "        self.playwright = await async_playwright().start()",
            "        self.browser = await self.playwright.chromium.launch()",
            "        self.page = await self.browser.new_page()",
            "",
            "    async def teardown_method(self):",
            "        await self.browser.close()",
            "        await self.playwright.stop()",
            "",
            f"    async def test_{session.name.lower().replace(' ', '_')}(self):",
            f'        """執行錄製的測試場景: {session.description}"""'
        ]
        
        for i, action in enumerate(session.actions):
            test_code_lines.extend(self._generate_playwright_action_code(action, i + 1))
        
        return "\n".join(test_code_lines)
    
    def _generate_playwright_action_code(self, action: RecordedAction, step_number: int) -> List[str]:
        """生成Playwright單個操作的代碼"""
        lines = [f"        # 步驟 {step_number}: {action.action_type.value}"]
        
        if action.action_type == ActionType.NAVIGATE:
            lines.append(f'        await self.page.goto("{action.input_value}")')
        
        elif action.action_type == ActionType.CLICK:
            if action.element_info:
                locator_type, locator_value = action.element_info.get_best_locator()
                lines.append(f'        await self.page.click("{locator_value}")')
        
        elif action.action_type == ActionType.TYPE:
            if action.element_info and action.input_value:
                locator_type, locator_value = action.element_info.get_best_locator()
                lines.append(f'        await self.page.fill("{locator_value}", "{action.input_value}")')
        
        elif action.action_type == ActionType.WAIT:
            if action.wait_time:
                lines.append(f"        await self.page.wait_for_timeout({int(action.wait_time * 1000)})")
        
        lines.append("")
        return lines


class StagewiseMCPManager:
    """Stagewise MCP管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.recording_sessions = {}
        self.element_inspector = ElementInspector()
        self.action_recognizer = ActionRecognitionEngine()
        self.code_generator = CodeGenerator()
        
        # 組件狀態
        self.is_recording = False
        self.current_session_id = None
    
    async def initialize(self):
        """初始化Stagewise MCP"""
        self.logger.info("🎬 初始化Stagewise MCP - 階段式錄製回放系統")
        
        # 初始化瀏覽器連接
        await self._initialize_browser_connection()
        
        self.logger.info("✅ Stagewise MCP初始化完成")
    
    async def _initialize_browser_connection(self):
        """初始化瀏覽器連接"""
        # 模擬瀏覽器連接初始化
        self.logger.info("初始化瀏覽器連接...")
        await asyncio.sleep(0.1)
    
    async def start_recording_session(self, session_name: str, description: str = "") -> str:
        """開始錄製會話"""
        if self.is_recording:
            raise ValueError("已有錄製會話在進行中")
        
        session_id = str(uuid.uuid4())
        
        session = RecordingSession(
            id=session_id,
            name=session_name,
            description=description,
            start_time=datetime.now().isoformat(),
            end_time=None,
            status="recording",
            actions=[],
            metadata={
                "browser": "chrome",
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Stagewise Recorder)"
            }
        )
        
        self.recording_sessions[session_id] = session
        self.is_recording = True
        self.current_session_id = session_id
        
        self.logger.info(f"🎬 開始錄製會話: {session_name} ({session_id})")
        
        return session_id
    
    async def record_action(self, event_data: Dict[str, Any]) -> str:
        """錄製用戶操作"""
        if not self.is_recording or not self.current_session_id:
            raise ValueError("沒有活躍的錄製會話")
        
        session = self.recording_sessions[self.current_session_id]
        
        # 識別操作類型
        action_type = await self.action_recognizer.recognize_action(event_data)
        
        # 檢查元素信息
        element_info = None
        if "element" in event_data:
            element_info = await self.element_inspector.inspect_element(event_data["element"])
        
        # 創建錄製操作
        action_id = str(uuid.uuid4())
        action = RecordedAction(
            id=action_id,
            action_type=action_type,
            timestamp=datetime.now().isoformat(),
            element_info=element_info,
            input_value=event_data.get("value"),
            coordinates=event_data.get("coordinates"),
            screenshot_before=event_data.get("screenshot_before"),
            screenshot_after=event_data.get("screenshot_after")
        )
        
        # 使用上下文增強操作
        context = {
            "previous_actions": session.actions[-3:],  # 最近3個操作
            "page_context": event_data.get("page_context", {})
        }
        action = await self.action_recognizer.enhance_action_with_context(action, context)
        
        session.actions.append(action)
        
        self.logger.info(f"錄製操作: {action_type.value} - {action_id}")
        
        return action_id
    
    async def stop_recording_session(self, session_id: str) -> RecordingSession:
        """停止錄製會話"""
        if session_id not in self.recording_sessions:
            raise ValueError(f"錄製會話不存在: {session_id}")
        
        session = self.recording_sessions[session_id]
        session.end_time = datetime.now().isoformat()
        session.status = "completed"
        
        # 計算總時長
        start_time = datetime.fromisoformat(session.start_time)
        end_time = datetime.fromisoformat(session.end_time)
        session.total_duration = (end_time - start_time).total_seconds()
        
        self.is_recording = False
        self.current_session_id = None
        
        self.logger.info(f"🏁 錄製會話完成: {session.name} (時長: {session.total_duration:.2f}秒)")
        
        return session
    
    async def generate_test_code(self, session_id: str, framework: str = "selenium") -> str:
        """生成測試代碼"""
        if session_id not in self.recording_sessions:
            raise ValueError(f"錄製會話不存在: {session_id}")
        
        session = self.recording_sessions[session_id]
        
        if framework.lower() == "selenium":
            return await self.code_generator.generate_selenium_test(session)
        elif framework.lower() == "playwright":
            return await self.code_generator.generate_playwright_test(session)
        else:
            raise ValueError(f"不支持的測試框架: {framework}")
    
    async def replay_session(self, session_id: str, headless: bool = True) -> Dict[str, Any]:
        """回放錄製會話"""
        if session_id not in self.recording_sessions:
            raise ValueError(f"錄製會話不存在: {session_id}")
        
        session = self.recording_sessions[session_id]
        
        self.logger.info(f"🔄 開始回放會話: {session.name}")
        
        # 模擬回放過程
        replay_results = []
        
        for i, action in enumerate(session.actions):
            try:
                # 模擬執行操作
                await asyncio.sleep(0.1)  # 模擬操作執行時間
                
                result = {
                    "step": i + 1,
                    "action_id": action.id,
                    "action_type": action.action_type.value,
                    "status": "success",
                    "execution_time": 0.1
                }
                
                replay_results.append(result)
                
            except Exception as e:
                result = {
                    "step": i + 1,
                    "action_id": action.id,
                    "action_type": action.action_type.value,
                    "status": "failed",
                    "error": str(e),
                    "execution_time": 0.0
                }
                replay_results.append(result)
        
        # 計算回放統計
        successful_steps = sum(1 for r in replay_results if r["status"] == "success")
        total_steps = len(replay_results)
        
        replay_summary = {
            "session_id": session_id,
            "session_name": session.name,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "failed_steps": total_steps - successful_steps,
            "success_rate": (successful_steps / total_steps * 100) if total_steps > 0 else 0,
            "results": replay_results
        }
        
        self.logger.info(f"回放完成: {successful_steps}/{total_steps} 步驟成功")
        
        return replay_summary
    
    async def optimize_session(self, session_id: str) -> RecordingSession:
        """優化錄製會話"""
        if session_id not in self.recording_sessions:
            raise ValueError(f"錄製會話不存在: {session_id}")
        
        session = self.recording_sessions[session_id]
        
        # 創建優化後的操作列表
        optimized_actions = []
        
        for action in session.actions:
            # 移除多餘的等待
            if action.action_type == ActionType.WAIT and action.wait_time and action.wait_time < 0.5:
                continue
            
            # 合併連續的相同操作
            if (optimized_actions and 
                optimized_actions[-1].action_type == action.action_type and
                optimized_actions[-1].element_info == action.element_info):
                continue
            
            optimized_actions.append(action)
        
        # 創建優化後的會話
        optimized_session_id = f"{session_id}_optimized"
        optimized_session = RecordingSession(
            id=optimized_session_id,
            name=f"{session.name} (優化版)",
            description=f"優化後的會話: {session.description}",
            start_time=session.start_time,
            end_time=session.end_time,
            status="completed",
            actions=optimized_actions,
            metadata={**session.metadata, "optimized": True}
        )
        
        self.recording_sessions[optimized_session_id] = optimized_session
        
        self.logger.info(f"會話優化完成: {len(session.actions)} -> {len(optimized_actions)} 操作")
        
        return optimized_session
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取會話信息"""
        if session_id not in self.recording_sessions:
            return None
        
        session = self.recording_sessions[session_id]
        return {
            "id": session.id,
            "name": session.name,
            "description": session.description,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "total_duration": session.total_duration,
            "actions_count": len(session.actions),
            "metadata": session.metadata
        }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有會話"""
        return [self.get_session_info(session_id) for session_id in self.recording_sessions.keys()]
    
    def get_status(self) -> Dict[str, Any]:
        """獲取Stagewise MCP狀態"""
        return {
            "component": "Stagewise MCP",
            "version": "4.6.1",
            "status": "running",
            "is_recording": self.is_recording,
            "current_session": self.current_session_id,
            "total_sessions": len(self.recording_sessions),
            "completed_sessions": len([s for s in self.recording_sessions.values() if s.status == "completed"]),
            "capabilities": [
                "ui_recording",
                "action_recognition",
                "test_generation",
                "session_replay",
                "code_generation"
            ]
        }


# 單例實例
stagewise_mcp = StagewiseMCPManager()