"""
PowerAutomation 4.0 Stagewise MCP核心服务

提供可视化编程的核心服务，集成Stagewise的能力。
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .visual_programming_engine import VisualProgrammingEngine
from .element_inspector import ElementInspector
from .code_generator import CodeGenerator


class StagewiseEventType(Enum):
    """Stagewise事件类型"""
    ELEMENT_SELECTED = "element_selected"
    CODE_GENERATED = "code_generated"
    CODE_EXECUTED = "code_executed"
    ERROR_OCCURRED = "error_occurred"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"


@dataclass
class StagewiseSession:
    """Stagewise编程会话"""
    session_id: str
    user_id: str
    project_id: str
    browser_context: Dict[str, Any]
    created_at: datetime
    last_activity: datetime
    status: str = "active"
    generated_code: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.generated_code is None:
            self.generated_code = []


@dataclass
class ElementSelection:
    """元素选择信息"""
    element_id: str
    selector: str
    tag_name: str
    attributes: Dict[str, str]
    text_content: str
    position: Dict[str, int]
    screenshot_path: Optional[str] = None
    confidence: float = 1.0


@dataclass
class GeneratedCode:
    """生成的代码信息"""
    code_id: str
    session_id: str
    element_selection: ElementSelection
    code_type: str  # "click", "input", "extract", "wait", etc.
    generated_code: str
    language: str = "python"
    framework: str = "selenium"
    confidence: float = 1.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class StagewiseService:
    """Stagewise MCP核心服务"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self.visual_engine = VisualProgrammingEngine(self.config.get("visual_engine", {}))
        self.element_inspector = ElementInspector(self.config.get("element_inspector", {}))
        self.code_generator = CodeGenerator(self.config.get("code_generator", {}))
        
        # 会话管理
        self.active_sessions: Dict[str, StagewiseSession] = {}
        self.session_history: List[StagewiseSession] = []
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # 统计信息
        self.stats = {
            "total_sessions": 0,
            "total_elements_selected": 0,
            "total_code_generated": 0,
            "total_code_executed": 0,
            "success_rate": 0.0
        }
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动Stagewise服务"""
        if self.is_running:
            return
        
        self.logger.info("启动Stagewise MCP服务...")
        
        # 启动核心组件
        await self.visual_engine.start()
        await self.element_inspector.start()
        await self.code_generator.start()
        
        self.is_running = True
        self.logger.info("Stagewise MCP服务启动完成")
    
    async def stop(self):
        """停止Stagewise服务"""
        if not self.is_running:
            return
        
        self.logger.info("停止Stagewise MCP服务...")
        
        # 结束所有活跃会话
        for session_id in list(self.active_sessions.keys()):
            await self.end_session(session_id)
        
        # 停止核心组件
        await self.visual_engine.stop()
        await self.element_inspector.stop()
        await self.code_generator.stop()
        
        self.is_running = False
        self.logger.info("Stagewise MCP服务已停止")
    
    async def create_session(
        self,
        user_id: str,
        project_id: str,
        browser_context: Dict[str, Any]
    ) -> str:
        """创建新的编程会话"""
        session_id = str(uuid.uuid4())
        
        session = StagewiseSession(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            browser_context=browser_context,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        self.stats["total_sessions"] += 1
        
        # 触发事件
        await self._emit_event(StagewiseEventType.SESSION_STARTED, {
            "session_id": session_id,
            "user_id": user_id,
            "project_id": project_id
        })
        
        self.logger.info(f"创建Stagewise会话: {session_id}")
        return session_id
    
    async def end_session(self, session_id: str) -> bool:
        """结束编程会话"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.status = "ended"
        
        # 移动到历史记录
        self.session_history.append(session)
        del self.active_sessions[session_id]
        
        # 触发事件
        await self._emit_event(StagewiseEventType.SESSION_ENDED, {
            "session_id": session_id,
            "duration": (datetime.now() - session.created_at).total_seconds(),
            "code_generated_count": len(session.generated_code)
        })
        
        self.logger.info(f"结束Stagewise会话: {session_id}")
        return True
    
    async def select_element(
        self,
        session_id: str,
        element_data: Dict[str, Any]
    ) -> ElementSelection:
        """处理元素选择"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        
        # 使用元素检查器分析元素
        element_info = await self.element_inspector.analyze_element(element_data)
        
        # 创建元素选择对象
        element_selection = ElementSelection(
            element_id=str(uuid.uuid4()),
            selector=element_info["selector"],
            tag_name=element_info["tag_name"],
            attributes=element_info["attributes"],
            text_content=element_info["text_content"],
            position=element_info["position"],
            screenshot_path=element_info.get("screenshot_path"),
            confidence=element_info.get("confidence", 1.0)
        )
        
        self.stats["total_elements_selected"] += 1
        
        # 触发事件
        await self._emit_event(StagewiseEventType.ELEMENT_SELECTED, {
            "session_id": session_id,
            "element_selection": asdict(element_selection)
        })
        
        self.logger.info(f"元素选择完成: {element_selection.selector}")
        return element_selection
    
    async def generate_code(
        self,
        session_id: str,
        element_selection: ElementSelection,
        action_type: str,
        options: Dict[str, Any] = None
    ) -> GeneratedCode:
        """生成代码"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        options = options or {}
        
        # 使用代码生成器生成代码
        code_result = await self.code_generator.generate_code(
            element_selection=element_selection,
            action_type=action_type,
            options=options
        )
        
        # 创建生成代码对象
        generated_code = GeneratedCode(
            code_id=str(uuid.uuid4()),
            session_id=session_id,
            element_selection=element_selection,
            code_type=action_type,
            generated_code=code_result["code"],
            language=code_result.get("language", "python"),
            framework=code_result.get("framework", "selenium"),
            confidence=code_result.get("confidence", 1.0)
        )
        
        # 添加到会话
        session.generated_code.append(asdict(generated_code))
        self.stats["total_code_generated"] += 1
        
        # 触发事件
        await self._emit_event(StagewiseEventType.CODE_GENERATED, {
            "session_id": session_id,
            "generated_code": asdict(generated_code)
        })
        
        self.logger.info(f"代码生成完成: {action_type} for {element_selection.selector}")
        return generated_code
    
    async def execute_code(
        self,
        session_id: str,
        code_id: str,
        execution_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """执行生成的代码"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        
        # 查找代码
        generated_code = None
        for code_data in session.generated_code:
            if code_data["code_id"] == code_id:
                generated_code = code_data
                break
        
        if not generated_code:
            raise ValueError(f"代码不存在: {code_id}")
        
        # 使用可视化引擎执行代码
        execution_result = await self.visual_engine.execute_code(
            code=generated_code["generated_code"],
            language=generated_code["language"],
            framework=generated_code["framework"],
            context=execution_context or {}
        )
        
        self.stats["total_code_executed"] += 1
        
        # 更新成功率
        if execution_result.get("success", False):
            self.stats["success_rate"] = (
                self.stats["success_rate"] * (self.stats["total_code_executed"] - 1) + 1
            ) / self.stats["total_code_executed"]
        else:
            self.stats["success_rate"] = (
                self.stats["success_rate"] * (self.stats["total_code_executed"] - 1)
            ) / self.stats["total_code_executed"]
        
        # 触发事件
        event_type = StagewiseEventType.CODE_EXECUTED if execution_result.get("success") else StagewiseEventType.ERROR_OCCURRED
        await self._emit_event(event_type, {
            "session_id": session_id,
            "code_id": code_id,
            "execution_result": execution_result
        })
        
        self.logger.info(f"代码执行完成: {code_id}, 成功: {execution_result.get('success', False)}")
        return execution_result
    
    async def get_code_suggestions(
        self,
        session_id: str,
        element_selection: ElementSelection,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """获取代码建议"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        # 使用代码生成器获取建议
        suggestions = await self.code_generator.get_suggestions(
            element_selection=element_selection,
            context=context or {}
        )
        
        self.logger.info(f"获取代码建议: {len(suggestions)} 个建议")
        return suggestions
    
    async def optimize_code(
        self,
        session_id: str,
        code_id: str,
        optimization_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """优化生成的代码"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.active_sessions[session_id]
        
        # 查找代码
        generated_code = None
        for code_data in session.generated_code:
            if code_data["code_id"] == code_id:
                generated_code = code_data
                break
        
        if not generated_code:
            raise ValueError(f"代码不存在: {code_id}")
        
        # 使用代码生成器优化代码
        optimization_result = await self.code_generator.optimize_code(
            code=generated_code["generated_code"],
            options=optimization_options or {}
        )
        
        self.logger.info(f"代码优化完成: {code_id}")
        return optimization_result
    
    async def export_session_code(
        self,
        session_id: str,
        export_format: str = "python",
        include_comments: bool = True
    ) -> str:
        """导出会话的所有代码"""
        if session_id not in self.active_sessions:
            # 检查历史记录
            session = None
            for hist_session in self.session_history:
                if hist_session.session_id == session_id:
                    session = hist_session
                    break
            if not session:
                raise ValueError(f"会话不存在: {session_id}")
        else:
            session = self.active_sessions[session_id]
        
        # 使用代码生成器导出代码
        exported_code = await self.code_generator.export_code(
            generated_code_list=session.generated_code,
            format=export_format,
            include_comments=include_comments
        )
        
        self.logger.info(f"导出会话代码: {session_id}, 格式: {export_format}")
        return exported_code
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            # 检查历史记录
            session = None
            for hist_session in self.session_history:
                if hist_session.session_id == session_id:
                    session = hist_session
                    break
            if not session:
                raise ValueError(f"会话不存在: {session_id}")
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "project_id": session.project_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "generated_code_count": len(session.generated_code),
            "browser_context": session.browser_context
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "service_status": "running" if self.is_running else "stopped",
            "active_sessions": len(self.active_sessions),
            "total_sessions": self.stats["total_sessions"],
            "total_elements_selected": self.stats["total_elements_selected"],
            "total_code_generated": self.stats["total_code_generated"],
            "total_code_executed": self.stats["total_code_executed"],
            "success_rate": self.stats["success_rate"],
            "session_history_count": len(self.session_history)
        }
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """添加事件回调"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """移除事件回调"""
        if event_type in self.event_callbacks:
            if callback in self.event_callbacks[event_type]:
                self.event_callbacks[event_type].remove(callback)
    
    async def _emit_event(self, event_type: StagewiseEventType, data: Dict[str, Any]):
        """触发事件"""
        event_name = event_type.value
        
        if event_name in self.event_callbacks:
            for callback in self.event_callbacks[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"事件回调错误 {event_name}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "service": "stagewise_mcp",
            "status": "healthy" if self.is_running else "unhealthy",
            "version": "4.0.0",
            "active_sessions": len(self.active_sessions),
            "components": {
                "visual_engine": await self.visual_engine.health_check(),
                "element_inspector": await self.element_inspector.health_check(),
                "code_generator": await self.code_generator.health_check()
            }
        }

