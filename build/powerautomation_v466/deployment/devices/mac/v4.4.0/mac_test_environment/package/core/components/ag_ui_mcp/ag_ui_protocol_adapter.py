"""
PowerAutomation 4.0 AG-UI协议适配器

实现AG-UI协议的解析、验证和转换功能，确保与标准AG-UI协议的完全兼容性。
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import jsonschema
from jsonschema import validate, ValidationError


class AGUIMessageType(Enum):
    """AG-UI消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    NOTIFICATION = "notification"
    ERROR = "error"


class AGUIComponentType(Enum):
    """AG-UI组件类型"""
    BUTTON = "button"
    INPUT = "input"
    SELECT = "select"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SLIDER = "slider"
    PROGRESS = "progress"
    CARD = "card"
    MODAL = "modal"
    FORM = "form"
    TABLE = "table"
    CHART = "chart"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CONTAINER = "container"
    LAYOUT = "layout"


class AGUIActionType(Enum):
    """AG-UI动作类型"""
    CLICK = "click"
    CHANGE = "change"
    SUBMIT = "submit"
    FOCUS = "focus"
    BLUR = "blur"
    HOVER = "hover"
    SCROLL = "scroll"
    RESIZE = "resize"
    LOAD = "load"
    UNLOAD = "unload"
    CUSTOM = "custom"


@dataclass
class AGUIComponent:
    """AG-UI组件定义"""
    id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List['AGUIComponent'] = field(default_factory=list)
    events: Dict[str, str] = field(default_factory=dict)
    styles: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AGUIMessage:
    """AG-UI消息"""
    id: str
    type: str
    timestamp: datetime
    source: str
    target: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class AGUIInteraction:
    """AG-UI交互定义"""
    interaction_id: str
    component_id: str
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class AGUIState:
    """AG-UI状态"""
    state_id: str
    components: Dict[str, AGUIComponent] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class AGUIProtocolAdapter:
    """AG-UI协议适配器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 协议版本
        self.protocol_version = self.config.get("protocol_version", "1.0.0")
        
        # 消息处理器
        self.message_handlers: Dict[str, Callable] = {}
        
        # 组件注册表
        self.component_registry: Dict[str, Dict[str, Any]] = {}
        
        # 验证模式
        self.validation_schemas = {}
        
        # 消息队列
        self.message_queue = asyncio.Queue()
        
        # 统计信息
        self.stats = {
            "messages_processed": 0,
            "messages_by_type": {},
            "components_registered": 0,
            "validation_errors": 0,
            "processing_errors": 0
        }
        
        # 运行状态
        self.is_running = False
        
        # 初始化验证模式
        self._initialize_validation_schemas()
    
    async def start(self):
        """启动协议适配器"""
        if self.is_running:
            return
        
        self.logger.info("启动AG-UI协议适配器...")
        
        # 注册默认组件
        await self._register_default_components()
        
        # 启动消息处理器
        asyncio.create_task(self._message_processor())
        
        self.is_running = True
        self.logger.info(f"AG-UI协议适配器启动完成，协议版本: {self.protocol_version}")
    
    async def stop(self):
        """停止协议适配器"""
        if not self.is_running:
            return
        
        self.logger.info("停止AG-UI协议适配器...")
        
        # 清理资源
        self.message_handlers.clear()
        self.component_registry.clear()
        
        # 清空消息队列
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.is_running = False
        self.logger.info("AG-UI协议适配器已停止")
    
    async def parse_message(self, raw_message: Union[str, Dict[str, Any]]) -> AGUIMessage:
        """解析AG-UI消息"""
        try:
            # 解析JSON
            if isinstance(raw_message, str):
                message_data = json.loads(raw_message)
            else:
                message_data = raw_message
            
            # 验证消息格式
            await self._validate_message(message_data)
            
            # 创建消息对象
            message = AGUIMessage(
                id=message_data.get("id", str(uuid.uuid4())),
                type=message_data["type"],
                timestamp=datetime.fromisoformat(message_data.get("timestamp", datetime.now().isoformat())),
                source=message_data["source"],
                target=message_data["target"],
                payload=message_data.get("payload", {}),
                metadata=message_data.get("metadata", {})
            )
            
            self.logger.debug(f"解析AG-UI消息: {message.id}, 类型: {message.type}")
            return message
            
        except json.JSONDecodeError as e:
            self.stats["validation_errors"] += 1
            raise ValueError(f"无效的JSON格式: {e}")
        except ValidationError as e:
            self.stats["validation_errors"] += 1
            raise ValueError(f"消息格式验证失败: {e}")
        except Exception as e:
            self.stats["processing_errors"] += 1
            raise ValueError(f"消息解析失败: {e}")
    
    async def serialize_message(self, message: AGUIMessage) -> str:
        """序列化AG-UI消息"""
        try:
            message_dict = {
                "id": message.id,
                "type": message.type,
                "timestamp": message.timestamp.isoformat(),
                "source": message.source,
                "target": message.target,
                "payload": message.payload,
                "metadata": message.metadata
            }
            
            # 验证序列化后的消息
            await self._validate_message(message_dict)
            
            return json.dumps(message_dict, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.stats["processing_errors"] += 1
            raise ValueError(f"消息序列化失败: {e}")
    
    async def parse_component(self, component_data: Dict[str, Any]) -> AGUIComponent:
        """解析AG-UI组件"""
        try:
            # 验证组件格式
            await self._validate_component(component_data)
            
            # 递归解析子组件
            children = []
            for child_data in component_data.get("children", []):
                child_component = await self.parse_component(child_data)
                children.append(child_component)
            
            component = AGUIComponent(
                id=component_data["id"],
                type=component_data["type"],
                properties=component_data.get("properties", {}),
                children=children,
                events=component_data.get("events", {}),
                styles=component_data.get("styles", {}),
                validation=component_data.get("validation", {}),
                metadata=component_data.get("metadata", {})
            )
            
            self.logger.debug(f"解析AG-UI组件: {component.id}, 类型: {component.type}")
            return component
            
        except ValidationError as e:
            self.stats["validation_errors"] += 1
            raise ValueError(f"组件格式验证失败: {e}")
        except Exception as e:
            self.stats["processing_errors"] += 1
            raise ValueError(f"组件解析失败: {e}")
    
    async def serialize_component(self, component: AGUIComponent) -> Dict[str, Any]:
        """序列化AG-UI组件"""
        try:
            # 递归序列化子组件
            children_data = []
            for child in component.children:
                child_data = await self.serialize_component(child)
                children_data.append(child_data)
            
            component_dict = {
                "id": component.id,
                "type": component.type,
                "properties": component.properties,
                "children": children_data,
                "events": component.events,
                "styles": component.styles,
                "validation": component.validation,
                "metadata": component.metadata
            }
            
            # 验证序列化后的组件
            await self._validate_component(component_dict)
            
            return component_dict
            
        except Exception as e:
            self.stats["processing_errors"] += 1
            raise ValueError(f"组件序列化失败: {e}")
    
    async def register_message_handler(
        self,
        message_type: str,
        handler: Callable[[AGUIMessage], Any]
    ):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"注册消息处理器: {message_type}")
    
    async def process_message(self, message: AGUIMessage) -> Optional[AGUIMessage]:
        """处理AG-UI消息"""
        try:
            # 更新统计
            self.stats["messages_processed"] += 1
            if message.type not in self.stats["messages_by_type"]:
                self.stats["messages_by_type"][message.type] = 0
            self.stats["messages_by_type"][message.type] += 1
            
            # 查找处理器
            handler = self.message_handlers.get(message.type)
            if not handler:
                self.logger.warning(f"未找到消息处理器: {message.type}")
                return await self._create_error_response(
                    message, f"未支持的消息类型: {message.type}"
                )
            
            # 执行处理器
            result = await handler(message)
            
            # 如果处理器返回响应消息
            if isinstance(result, AGUIMessage):
                return result
            elif isinstance(result, dict):
                # 创建响应消息
                return AGUIMessage(
                    id=str(uuid.uuid4()),
                    type=AGUIMessageType.RESPONSE.value,
                    timestamp=datetime.now(),
                    source=message.target,
                    target=message.source,
                    payload=result,
                    metadata={"request_id": message.id}
                )
            
            return None
            
        except Exception as e:
            self.stats["processing_errors"] += 1
            self.logger.error(f"消息处理失败: {e}")
            return await self._create_error_response(message, str(e))
    
    async def send_message(self, message: AGUIMessage):
        """发送AG-UI消息"""
        await self.message_queue.put(message)
    
    async def register_component_type(
        self,
        component_type: str,
        schema: Dict[str, Any]
    ):
        """注册组件类型"""
        self.component_registry[component_type] = schema
        self.stats["components_registered"] += 1
        self.logger.info(f"注册组件类型: {component_type}")
    
    async def validate_interaction(self, interaction: AGUIInteraction) -> bool:
        """验证交互"""
        try:
            # 检查组件是否存在
            if interaction.component_id not in self.component_registry:
                return False
            
            # 检查动作类型是否支持
            component_schema = self.component_registry[interaction.component_id]
            supported_actions = component_schema.get("supported_actions", [])
            
            if interaction.action_type not in supported_actions:
                return False
            
            # 验证参数
            action_schema = component_schema.get("action_schemas", {}).get(interaction.action_type)
            if action_schema:
                validate(interaction.parameters, action_schema)
            
            return True
            
        except ValidationError:
            return False
        except Exception as e:
            self.logger.error(f"交互验证失败: {e}")
            return False
    
    async def convert_to_standard_format(
        self,
        external_data: Dict[str, Any],
        source_format: str
    ) -> Dict[str, Any]:
        """转换外部格式到AG-UI标准格式"""
        converters = {
            "html": self._convert_from_html,
            "react": self._convert_from_react,
            "vue": self._convert_from_vue,
            "angular": self._convert_from_angular,
            "json_ui": self._convert_from_json_ui
        }
        
        converter = converters.get(source_format)
        if not converter:
            raise ValueError(f"不支持的源格式: {source_format}")
        
        return await converter(external_data)
    
    async def convert_from_standard_format(
        self,
        ag_ui_data: Dict[str, Any],
        target_format: str
    ) -> Dict[str, Any]:
        """转换AG-UI标准格式到外部格式"""
        converters = {
            "html": self._convert_to_html,
            "react": self._convert_to_react,
            "vue": self._convert_to_vue,
            "angular": self._convert_to_angular,
            "json_ui": self._convert_to_json_ui
        }
        
        converter = converters.get(target_format)
        if not converter:
            raise ValueError(f"不支持的目标格式: {target_format}")
        
        return await converter(ag_ui_data)
    
    async def _message_processor(self):
        """消息处理器协程"""
        while self.is_running:
            try:
                # 等待消息
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                # 处理消息
                response = await self.process_message(message)
                
                # 如果有响应，发送回去
                if response:
                    # 这里应该发送到目标系统
                    self.logger.debug(f"发送响应消息: {response.id}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"消息处理器错误: {e}")
    
    def _initialize_validation_schemas(self):
        """初始化验证模式"""
        # AG-UI消息模式
        self.validation_schemas["message"] = {
            "type": "object",
            "required": ["type", "source", "target"],
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string", "enum": [t.value for t in AGUIMessageType]},
                "timestamp": {"type": "string", "format": "date-time"},
                "source": {"type": "string"},
                "target": {"type": "string"},
                "payload": {"type": "object"},
                "metadata": {"type": "object"}
            }
        }
        
        # AG-UI组件模式
        self.validation_schemas["component"] = {
            "type": "object",
            "required": ["id", "type"],
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "properties": {"type": "object"},
                "children": {
                    "type": "array",
                    "items": {"$ref": "#"}  # 递归引用
                },
                "events": {"type": "object"},
                "styles": {"type": "object"},
                "validation": {"type": "object"},
                "metadata": {"type": "object"}
            }
        }
    
    async def _validate_message(self, message_data: Dict[str, Any]):
        """验证消息格式"""
        validate(message_data, self.validation_schemas["message"])
    
    async def _validate_component(self, component_data: Dict[str, Any]):
        """验证组件格式"""
        validate(component_data, self.validation_schemas["component"])
    
    async def _register_default_components(self):
        """注册默认组件类型"""
        default_components = {
            "button": {
                "supported_actions": ["click", "hover", "focus", "blur"],
                "properties": {
                    "text": {"type": "string"},
                    "disabled": {"type": "boolean"},
                    "variant": {"type": "string", "enum": ["primary", "secondary", "danger"]}
                },
                "action_schemas": {
                    "click": {
                        "type": "object",
                        "properties": {
                            "button": {"type": "integer", "minimum": 0, "maximum": 2}
                        }
                    }
                }
            },
            "input": {
                "supported_actions": ["change", "focus", "blur", "keypress"],
                "properties": {
                    "value": {"type": "string"},
                    "placeholder": {"type": "string"},
                    "type": {"type": "string", "enum": ["text", "password", "email", "number"]},
                    "disabled": {"type": "boolean"},
                    "required": {"type": "boolean"}
                },
                "action_schemas": {
                    "change": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"}
                        },
                        "required": ["value"]
                    }
                }
            },
            "select": {
                "supported_actions": ["change", "focus", "blur"],
                "properties": {
                    "value": {"type": ["string", "array"]},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string"},
                                "label": {"type": "string"},
                                "disabled": {"type": "boolean"}
                            },
                            "required": ["value", "label"]
                        }
                    },
                    "multiple": {"type": "boolean"},
                    "disabled": {"type": "boolean"}
                }
            }
        }
        
        for component_type, schema in default_components.items():
            await self.register_component_type(component_type, schema)
    
    async def _create_error_response(
        self,
        original_message: AGUIMessage,
        error_message: str
    ) -> AGUIMessage:
        """创建错误响应"""
        return AGUIMessage(
            id=str(uuid.uuid4()),
            type=AGUIMessageType.ERROR.value,
            timestamp=datetime.now(),
            source=original_message.target,
            target=original_message.source,
            payload={
                "error": error_message,
                "original_message_id": original_message.id
            },
            metadata={"error_type": "processing_error"}
        )
    
    # 格式转换器实现
    async def _convert_from_html(self, html_data: Dict[str, Any]) -> Dict[str, Any]:
        """从HTML格式转换"""
        # 简化实现，实际应该解析HTML DOM
        return {
            "id": html_data.get("id", str(uuid.uuid4())),
            "type": html_data.get("tagName", "div").lower(),
            "properties": html_data.get("attributes", {}),
            "children": []
        }
    
    async def _convert_to_html(self, ag_ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换到HTML格式"""
        return {
            "tagName": ag_ui_data["type"],
            "attributes": ag_ui_data.get("properties", {}),
            "children": ag_ui_data.get("children", [])
        }
    
    async def _convert_from_react(self, react_data: Dict[str, Any]) -> Dict[str, Any]:
        """从React格式转换"""
        return {
            "id": react_data.get("key", str(uuid.uuid4())),
            "type": react_data.get("type", "div"),
            "properties": react_data.get("props", {}),
            "children": react_data.get("children", [])
        }
    
    async def _convert_to_react(self, ag_ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换到React格式"""
        return {
            "type": ag_ui_data["type"],
            "props": ag_ui_data.get("properties", {}),
            "key": ag_ui_data["id"],
            "children": ag_ui_data.get("children", [])
        }
    
    async def _convert_from_vue(self, vue_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Vue格式转换"""
        return {
            "id": vue_data.get("key", str(uuid.uuid4())),
            "type": vue_data.get("tag", "div"),
            "properties": vue_data.get("props", {}),
            "children": vue_data.get("children", [])
        }
    
    async def _convert_to_vue(self, ag_ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换到Vue格式"""
        return {
            "tag": ag_ui_data["type"],
            "props": ag_ui_data.get("properties", {}),
            "key": ag_ui_data["id"],
            "children": ag_ui_data.get("children", [])
        }
    
    async def _convert_from_angular(self, angular_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Angular格式转换"""
        return {
            "id": angular_data.get("id", str(uuid.uuid4())),
            "type": angular_data.get("selector", "div"),
            "properties": angular_data.get("inputs", {}),
            "children": angular_data.get("children", [])
        }
    
    async def _convert_to_angular(self, ag_ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换到Angular格式"""
        return {
            "selector": ag_ui_data["type"],
            "inputs": ag_ui_data.get("properties", {}),
            "id": ag_ui_data["id"],
            "children": ag_ui_data.get("children", [])
        }
    
    async def _convert_from_json_ui(self, json_ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """从JSON UI格式转换"""
        # JSON UI格式已经很接近AG-UI格式
        return {
            "id": json_ui_data.get("id", str(uuid.uuid4())),
            "type": json_ui_data.get("component", "div"),
            "properties": json_ui_data.get("props", {}),
            "children": json_ui_data.get("children", [])
        }
    
    async def _convert_to_json_ui(self, ag_ui_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换到JSON UI格式"""
        return {
            "component": ag_ui_data["type"],
            "props": ag_ui_data.get("properties", {}),
            "id": ag_ui_data["id"],
            "children": ag_ui_data.get("children", [])
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "protocol_version": self.protocol_version,
            "is_running": self.is_running,
            "registered_handlers": len(self.message_handlers),
            "registered_components": len(self.component_registry),
            "message_queue_size": self.message_queue.qsize(),
            "statistics": self.stats.copy()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "ag_ui_protocol_adapter",
            "status": "healthy" if self.is_running else "unhealthy",
            "protocol_version": self.protocol_version,
            "statistics": await self.get_statistics()
        }

