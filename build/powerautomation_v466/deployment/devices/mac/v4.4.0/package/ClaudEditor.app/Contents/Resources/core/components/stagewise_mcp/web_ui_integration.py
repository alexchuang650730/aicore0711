"""
PowerAutomation 4.0 WebUI集成和实时预览系统

提供浏览器扩展集成、实时代码预览和可视化调试功能。
"""

import asyncio
import json
import uuid
import websockets
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path


class UIEventType(Enum):
    """UI事件类型"""
    ELEMENT_SELECTED = "element_selected"
    CODE_GENERATED = "code_generated"
    CODE_EXECUTED = "code_executed"
    PREVIEW_UPDATED = "preview_updated"
    ERROR_OCCURRED = "error_occurred"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"


class PreviewMode(Enum):
    """预览模式"""
    REAL_TIME = "real_time"
    ON_DEMAND = "on_demand"
    STEP_BY_STEP = "step_by_step"


@dataclass
class UISession:
    """UI会话"""
    session_id: str
    user_id: str
    browser_tab_id: str
    websocket_connection: Any
    created_at: datetime
    last_activity: datetime
    preview_mode: PreviewMode = PreviewMode.REAL_TIME
    is_active: bool = True


@dataclass
class ElementHighlight:
    """元素高亮信息"""
    element_id: str
    selector: str
    highlight_color: str = "#ff6b6b"
    highlight_style: str = "solid"
    show_tooltip: bool = True
    tooltip_text: str = ""


@dataclass
class CodePreview:
    """代码预览信息"""
    preview_id: str
    session_id: str
    generated_code: str
    language: str
    framework: str
    execution_status: str = "pending"
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class WebUIIntegration:
    """WebUI集成和实时预览系统"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # WebSocket服务器配置
        self.websocket_host = self.config.get("websocket_host", "localhost")
        self.websocket_port = self.config.get("websocket_port", 8765)
        
        # 会话管理
        self.active_sessions: Dict[str, UISession] = {}
        self.websocket_connections: Set[websockets.WebSocketServerProtocol] = set()
        
        # 预览管理
        self.active_previews: Dict[str, CodePreview] = {}
        self.element_highlights: Dict[str, ElementHighlight] = {}
        
        # 浏览器扩展资源
        self.extension_path = Path(__file__).parent / "browser_extension"
        
        # WebSocket服务器
        self.websocket_server = None
        
        # 统计信息
        self.stats = {
            "total_sessions": 0,
            "active_connections": 0,
            "total_previews": 0,
            "total_highlights": 0
        }
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动WebUI集成系统"""
        if self.is_running:
            return
        
        self.logger.info("启动WebUI集成系统...")
        
        # 启动WebSocket服务器
        await self._start_websocket_server()
        
        # 初始化浏览器扩展资源
        await self._initialize_browser_extension()
        
        self.is_running = True
        self.logger.info(f"WebUI集成系统启动完成，WebSocket服务器运行在 ws://{self.websocket_host}:{self.websocket_port}")
    
    async def stop(self):
        """停止WebUI集成系统"""
        if not self.is_running:
            return
        
        self.logger.info("停止WebUI集成系统...")
        
        # 关闭所有WebSocket连接
        for websocket in self.websocket_connections.copy():
            await websocket.close()
        
        # 停止WebSocket服务器
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        # 清理会话
        self.active_sessions.clear()
        self.active_previews.clear()
        self.element_highlights.clear()
        
        self.is_running = False
        self.logger.info("WebUI集成系统已停止")
    
    async def create_ui_session(
        self,
        user_id: str,
        browser_tab_id: str,
        websocket_connection: Any
    ) -> str:
        """创建UI会话"""
        session_id = str(uuid.uuid4())
        
        session = UISession(
            session_id=session_id,
            user_id=user_id,
            browser_tab_id=browser_tab_id,
            websocket_connection=websocket_connection,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        self.stats["total_sessions"] += 1
        
        # 发送会话创建确认
        await self._send_to_client(websocket_connection, {
            "type": "session_created",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"创建UI会话: {session_id}")
        return session_id
    
    async def handle_element_selection(
        self,
        session_id: str,
        element_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理元素选择"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        
        # 创建元素高亮
        highlight = ElementHighlight(
            element_id=str(uuid.uuid4()),
            selector=element_data.get("selector", ""),
            tooltip_text=f"选中元素: {element_data.get('tagName', 'unknown')}"
        )
        
        self.element_highlights[highlight.element_id] = highlight
        self.stats["total_highlights"] += 1
        
        # 发送高亮指令到浏览器
        await self._send_to_client(session.websocket_connection, {
            "type": "highlight_element",
            "highlight": asdict(highlight),
            "element_data": element_data
        })
        
        # 触发元素选择事件
        await self._broadcast_event(UIEventType.ELEMENT_SELECTED, {
            "session_id": session_id,
            "element_data": element_data,
            "highlight_id": highlight.element_id
        })
        
        return {
            "highlight_id": highlight.element_id,
            "selector": element_data.get("selector", ""),
            "success": True
        }
    
    async def create_code_preview(
        self,
        session_id: str,
        generated_code: str,
        language: str,
        framework: str
    ) -> str:
        """创建代码预览"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        preview_id = str(uuid.uuid4())
        
        preview = CodePreview(
            preview_id=preview_id,
            session_id=session_id,
            generated_code=generated_code,
            language=language,
            framework=framework
        )
        
        self.active_previews[preview_id] = preview
        self.stats["total_previews"] += 1
        
        session = self.active_sessions[session_id]
        
        # 发送代码预览到浏览器
        await self._send_to_client(session.websocket_connection, {
            "type": "code_preview",
            "preview": asdict(preview)
        })
        
        # 如果是实时模式，自动执行预览
        if session.preview_mode == PreviewMode.REAL_TIME:
            await self._execute_code_preview(preview_id)
        
        self.logger.info(f"创建代码预览: {preview_id}")
        return preview_id
    
    async def execute_code_preview(self, preview_id: str) -> Dict[str, Any]:
        """执行代码预览"""
        if preview_id not in self.active_previews:
            raise ValueError(f"预览不存在: {preview_id}")
        
        return await self._execute_code_preview(preview_id)
    
    async def _execute_code_preview(self, preview_id: str) -> Dict[str, Any]:
        """内部执行代码预览"""
        preview = self.active_previews[preview_id]
        session = self.active_sessions[preview.session_id]
        
        try:
            # 模拟代码执行（实际应该调用VisualProgrammingEngine）
            execution_result = {
                "success": True,
                "output": f"代码执行成功: {preview.framework} {preview.language}",
                "execution_time": 0.5,
                "screenshots": []
            }
            
            preview.execution_status = "completed"
            preview.execution_result = execution_result
            
            # 发送执行结果到浏览器
            await self._send_to_client(session.websocket_connection, {
                "type": "preview_executed",
                "preview_id": preview_id,
                "result": execution_result
            })
            
            # 触发代码执行事件
            await self._broadcast_event(UIEventType.CODE_EXECUTED, {
                "session_id": preview.session_id,
                "preview_id": preview_id,
                "result": execution_result
            })
            
            return execution_result
            
        except Exception as e:
            preview.execution_status = "failed"
            preview.execution_result = {
                "success": False,
                "error": str(e)
            }
            
            # 发送错误到浏览器
            await self._send_to_client(session.websocket_connection, {
                "type": "preview_error",
                "preview_id": preview_id,
                "error": str(e)
            })
            
            raise
    
    async def update_preview_mode(
        self,
        session_id: str,
        mode: str
    ) -> bool:
        """更新预览模式"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        try:
            session.preview_mode = PreviewMode(mode)
            session.last_activity = datetime.now()
            
            # 通知浏览器模式变更
            await self._send_to_client(session.websocket_connection, {
                "type": "preview_mode_updated",
                "mode": mode
            })
            
            return True
            
        except ValueError:
            return False
    
    async def clear_highlights(self, session_id: str) -> bool:
        """清除高亮"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # 清除该会话的所有高亮
        highlights_to_remove = []
        for highlight_id, highlight in self.element_highlights.items():
            # 这里需要根据会话关联高亮，简化处理
            highlights_to_remove.append(highlight_id)
        
        for highlight_id in highlights_to_remove:
            del self.element_highlights[highlight_id]
        
        # 发送清除指令到浏览器
        await self._send_to_client(session.websocket_connection, {
            "type": "clear_highlights"
        })
        
        return True
    
    async def get_browser_extension_files(self) -> Dict[str, str]:
        """获取浏览器扩展文件"""
        extension_files = {}
        
        # manifest.json
        extension_files["manifest.json"] = json.dumps({
            "manifest_version": 3,
            "name": "PowerAutomation 4.0 Stagewise",
            "version": "1.0.0",
            "description": "可视化编程助手",
            "permissions": [
                "activeTab",
                "scripting",
                "storage"
            ],
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "css": ["styles.css"]
                }
            ],
            "background": {
                "service_worker": "background.js"
            },
            "action": {
                "default_popup": "popup.html",
                "default_title": "PowerAutomation 4.0"
            }
        }, indent=2)
        
        # content.js
        extension_files["content.js"] = """
// PowerAutomation 4.0 Content Script
class PowerAutomationContent {
    constructor() {
        this.websocket = null;
        this.sessionId = null;
        this.isSelectionMode = false;
        this.highlightedElements = new Map();
        this.init();
    }
    
    async init() {
        // 连接WebSocket
        await this.connectWebSocket();
        
        // 初始化事件监听
        this.initEventListeners();
        
        // 注入样式
        this.injectStyles();
    }
    
    async connectWebSocket() {
        try {
            this.websocket = new WebSocket('ws://localhost:8765');
            
            this.websocket.onopen = () => {
                console.log('PowerAutomation WebSocket连接成功');
                this.createSession();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                console.log('PowerAutomation WebSocket连接关闭');
                // 重连逻辑
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
        } catch (error) {
            console.error('WebSocket连接失败:', error);
        }
    }
    
    createSession() {
        const message = {
            type: 'create_session',
            user_id: 'user_' + Date.now(),
            browser_tab_id: 'tab_' + Date.now()
        };
        this.websocket.send(JSON.stringify(message));
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'session_created':
                this.sessionId = message.session_id;
                console.log('会话创建成功:', this.sessionId);
                break;
                
            case 'highlight_element':
                this.highlightElement(message.highlight, message.element_data);
                break;
                
            case 'clear_highlights':
                this.clearAllHighlights();
                break;
                
            case 'code_preview':
                this.showCodePreview(message.preview);
                break;
                
            case 'preview_executed':
                this.showExecutionResult(message.preview_id, message.result);
                break;
        }
    }
    
    initEventListeners() {
        // 元素选择模式
        document.addEventListener('click', (event) => {
            if (this.isSelectionMode) {
                event.preventDefault();
                event.stopPropagation();
                this.selectElement(event.target);
            }
        }, true);
        
        // 键盘快捷键
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.shiftKey && event.key === 'P') {
                event.preventDefault();
                this.toggleSelectionMode();
            }
        });
    }
    
    toggleSelectionMode() {
        this.isSelectionMode = !this.isSelectionMode;
        document.body.style.cursor = this.isSelectionMode ? 'crosshair' : 'default';
        
        if (this.isSelectionMode) {
            this.showNotification('元素选择模式已开启，点击任意元素进行选择');
        } else {
            this.showNotification('元素选择模式已关闭');
        }
    }
    
    selectElement(element) {
        // 生成选择器
        const selector = this.generateSelector(element);
        
        // 收集元素信息
        const elementData = {
            tagName: element.tagName,
            selector: selector,
            textContent: element.textContent.trim().substring(0, 100),
            attributes: this.getElementAttributes(element),
            position: this.getElementPosition(element),
            size: this.getElementSize(element)
        };
        
        // 发送到服务器
        const message = {
            type: 'element_selected',
            session_id: this.sessionId,
            element_data: elementData
        };
        
        this.websocket.send(JSON.stringify(message));
        
        // 临时高亮选中的元素
        this.temporaryHighlight(element);
    }
    
    generateSelector(element) {
        // 简单的选择器生成逻辑
        if (element.id) {
            return '#' + element.id;
        }
        
        if (element.className) {
            const classes = element.className.split(' ').filter(c => c.trim());
            if (classes.length > 0) {
                return '.' + classes[0];
            }
        }
        
        return element.tagName.toLowerCase();
    }
    
    getElementAttributes(element) {
        const attributes = {};
        for (let attr of element.attributes) {
            attributes[attr.name] = attr.value;
        }
        return attributes;
    }
    
    getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height
        };
    }
    
    getElementSize(element) {
        return {
            width: element.offsetWidth,
            height: element.offsetHeight
        };
    }
    
    highlightElement(highlight, elementData) {
        const elements = document.querySelectorAll(highlight.selector);
        
        elements.forEach(element => {
            const highlightDiv = document.createElement('div');
            highlightDiv.className = 'powerautomation-highlight';
            highlightDiv.style.cssText = `
                position: absolute;
                border: 2px solid ${highlight.highlight_color};
                background: ${highlight.highlight_color}20;
                pointer-events: none;
                z-index: 10000;
                border-radius: 3px;
            `;
            
            this.positionHighlight(highlightDiv, element);
            document.body.appendChild(highlightDiv);
            
            this.highlightedElements.set(highlight.element_id, highlightDiv);
            
            // 添加工具提示
            if (highlight.show_tooltip && highlight.tooltip_text) {
                this.showTooltip(element, highlight.tooltip_text);
            }
        });
    }
    
    positionHighlight(highlightDiv, element) {
        const rect = element.getBoundingClientRect();
        highlightDiv.style.left = (rect.left + window.scrollX - 2) + 'px';
        highlightDiv.style.top = (rect.top + window.scrollY - 2) + 'px';
        highlightDiv.style.width = (rect.width + 4) + 'px';
        highlightDiv.style.height = (rect.height + 4) + 'px';
    }
    
    clearAllHighlights() {
        this.highlightedElements.forEach(highlight => {
            if (highlight.parentNode) {
                highlight.parentNode.removeChild(highlight);
            }
        });
        this.highlightedElements.clear();
        
        // 清除工具提示
        document.querySelectorAll('.powerautomation-tooltip').forEach(tooltip => {
            tooltip.remove();
        });
    }
    
    temporaryHighlight(element) {
        const highlight = document.createElement('div');
        highlight.className = 'powerautomation-temp-highlight';
        highlight.style.cssText = `
            position: absolute;
            border: 3px solid #00ff00;
            background: #00ff0030;
            pointer-events: none;
            z-index: 10001;
            border-radius: 3px;
        `;
        
        this.positionHighlight(highlight, element);
        document.body.appendChild(highlight);
        
        // 2秒后移除
        setTimeout(() => {
            if (highlight.parentNode) {
                highlight.parentNode.removeChild(highlight);
            }
        }, 2000);
    }
    
    showCodePreview(preview) {
        // 创建代码预览窗口
        const previewWindow = document.createElement('div');
        previewWindow.className = 'powerautomation-code-preview';
        previewWindow.innerHTML = `
            <div class="preview-header">
                <h3>生成的代码 (${preview.framework} - ${preview.language})</h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="preview-content">
                <pre><code>${this.escapeHtml(preview.generated_code)}</code></pre>
            </div>
            <div class="preview-actions">
                <button class="execute-btn">执行代码</button>
                <button class="copy-btn">复制代码</button>
            </div>
        `;
        
        document.body.appendChild(previewWindow);
        
        // 绑定事件
        previewWindow.querySelector('.close-btn').onclick = () => {
            previewWindow.remove();
        };
        
        previewWindow.querySelector('.execute-btn').onclick = () => {
            this.executePreview(preview.preview_id);
        };
        
        previewWindow.querySelector('.copy-btn').onclick = () => {
            navigator.clipboard.writeText(preview.generated_code);
            this.showNotification('代码已复制到剪贴板');
        };
    }
    
    executePreview(previewId) {
        const message = {
            type: 'execute_preview',
            session_id: this.sessionId,
            preview_id: previewId
        };
        this.websocket.send(JSON.stringify(message));
    }
    
    showExecutionResult(previewId, result) {
        const notification = result.success ? 
            `代码执行成功: ${result.output}` : 
            `代码执行失败: ${result.error}`;
        
        this.showNotification(notification, result.success ? 'success' : 'error');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `powerautomation-notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // 3秒后移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'powerautomation-tooltip';
        tooltip.textContent = text;
        
        const rect = element.getBoundingClientRect();
        tooltip.style.cssText = `
            position: absolute;
            left: ${rect.left + window.scrollX}px;
            top: ${rect.top + window.scrollY - 30}px;
            background: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            z-index: 10002;
            pointer-events: none;
        `;
        
        document.body.appendChild(tooltip);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .powerautomation-code-preview {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 600px;
                max-height: 500px;
                background: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                z-index: 10003;
                font-family: Arial, sans-serif;
            }
            
            .preview-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px;
                border-bottom: 1px solid #eee;
                background: #f8f9fa;
                border-radius: 8px 8px 0 0;
            }
            
            .preview-header h3 {
                margin: 0;
                font-size: 16px;
                color: #333;
            }
            
            .close-btn {
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: #666;
            }
            
            .preview-content {
                padding: 15px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .preview-content pre {
                margin: 0;
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
            
            .preview-content code {
                font-family: 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
            
            .preview-actions {
                padding: 15px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 10px;
                justify-content: flex-end;
            }
            
            .preview-actions button {
                padding: 8px 16px;
                border: 1px solid #ddd;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            
            .execute-btn {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            
            .copy-btn {
                background: #6c757d;
                color: white;
                border-color: #6c757d;
            }
            
            .powerautomation-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                z-index: 10004;
                max-width: 300px;
            }
            
            .powerautomation-notification.info {
                background: #17a2b8;
            }
            
            .powerautomation-notification.success {
                background: #28a745;
            }
            
            .powerautomation-notification.error {
                background: #dc3545;
            }
        `;
        
        document.head.appendChild(style);
    }
}

// 初始化
new PowerAutomationContent();
"""
        
        return extension_files
    
    async def _start_websocket_server(self):
        """启动WebSocket服务器"""
        async def handle_websocket(websocket, path):
            self.websocket_connections.add(websocket)
            self.stats["active_connections"] += 1
            
            try:
                async for message in websocket:
                    await self._handle_websocket_message(websocket, json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.websocket_connections.discard(websocket)
                self.stats["active_connections"] -= 1
        
        self.websocket_server = await websockets.serve(
            handle_websocket,
            self.websocket_host,
            self.websocket_port
        )
    
    async def _handle_websocket_message(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: Dict[str, Any]
    ):
        """处理WebSocket消息"""
        message_type = message.get("type")
        
        try:
            if message_type == "create_session":
                session_id = await self.create_ui_session(
                    message.get("user_id"),
                    message.get("browser_tab_id"),
                    websocket
                )
                
            elif message_type == "element_selected":
                await self.handle_element_selection(
                    message.get("session_id"),
                    message.get("element_data")
                )
                
            elif message_type == "execute_preview":
                await self.execute_code_preview(message.get("preview_id"))
                
            elif message_type == "update_preview_mode":
                await self.update_preview_mode(
                    message.get("session_id"),
                    message.get("mode")
                )
                
            elif message_type == "clear_highlights":
                await self.clear_highlights(message.get("session_id"))
                
        except Exception as e:
            await self._send_to_client(websocket, {
                "type": "error",
                "message": str(e)
            })
    
    async def _send_to_client(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: Dict[str, Any]
    ):
        """发送消息到客户端"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def _broadcast_event(self, event_type: UIEventType, data: Dict[str, Any]):
        """广播事件到所有连接"""
        message = {
            "type": "event",
            "event_type": event_type.value,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送到所有活跃连接
        for websocket in self.websocket_connections.copy():
            await self._send_to_client(websocket, message)
    
    async def _initialize_browser_extension(self):
        """初始化浏览器扩展资源"""
        # 确保扩展目录存在
        self.extension_path.mkdir(exist_ok=True)
        
        # 生成扩展文件
        extension_files = await self.get_browser_extension_files()
        
        for filename, content in extension_files.items():
            file_path = self.extension_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        self.logger.info(f"浏览器扩展文件已生成到: {self.extension_path}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "active_sessions": len(self.active_sessions),
            "active_connections": len(self.websocket_connections),
            "total_sessions": self.stats["total_sessions"],
            "total_previews": self.stats["total_previews"],
            "total_highlights": self.stats["total_highlights"],
            "websocket_server": f"ws://{self.websocket_host}:{self.websocket_port}"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "web_ui_integration",
            "status": "healthy" if self.is_running else "unhealthy",
            "websocket_server_running": self.websocket_server is not None,
            "active_connections": len(self.websocket_connections),
            "statistics": await self.get_statistics()
        }

