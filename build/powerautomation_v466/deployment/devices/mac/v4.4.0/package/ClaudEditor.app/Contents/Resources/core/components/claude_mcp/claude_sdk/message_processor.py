"""
PowerAutomation 4.0 Message Processor
消息处理器，负责消息格式化、预处理和后处理
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    COMMAND = "command"
    CODE = "code"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class ProcessedMessage:
    """处理后的消息数据类"""
    original: str
    processed: str
    message_type: MessageType
    metadata: Dict[str, Any]
    commands: List[str]
    code_blocks: List[Dict[str, str]]


class MessageProcessor:
    """消息处理器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 正则表达式模式
        self.command_pattern = re.compile(r'^/(\w+)(?:\s+(.*))?$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        self.json_pattern = re.compile(r'```json\n(.*?)\n```', re.DOTALL)
        
        # 预定义的系统提示
        self.system_prompts = {
            "code_assistant": """你是一个专业的代码助手。请帮助用户编写、调试和优化代码。
            当用户请求代码时，请提供清晰的代码示例和解释。
            如果需要执行命令，请使用 /command 格式。""",
            
            "architect": """你是一个系统架构师。请帮助用户设计和分析系统架构。
            提供详细的架构建议、最佳实践和技术选型。
            使用图表和文档来说明架构设计。""",
            
            "devops": """你是一个DevOps专家。请帮助用户进行部署、监控和运维。
            提供自动化脚本、配置文件和最佳实践。
            关注系统的可靠性、可扩展性和安全性。"""
        }
    
    async def preprocess_message(
        self,
        message: str,
        context: Dict[str, Any] = None
    ) -> ProcessedMessage:
        """预处理消息"""
        context = context or {}
        
        # 检测消息类型
        message_type = self._detect_message_type(message)
        
        # 提取命令
        commands = self._extract_commands(message)
        
        # 提取代码块
        code_blocks = self._extract_code_blocks(message)
        
        # 处理消息内容
        processed_content = await self._process_content(message, message_type, context)
        
        # 创建处理结果
        result = ProcessedMessage(
            original=message,
            processed=processed_content,
            message_type=message_type,
            metadata={
                "has_commands": len(commands) > 0,
                "has_code": len(code_blocks) > 0,
                "word_count": len(message.split()),
                "char_count": len(message)
            },
            commands=commands,
            code_blocks=code_blocks
        )
        
        self.logger.debug(f"消息预处理完成: {message_type.value}")
        return result
    
    async def postprocess_response(
        self,
        response: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """后处理响应"""
        context = context or {}
        
        # 提取结构化内容
        structured_content = self._extract_structured_content(response)
        
        # 格式化响应
        formatted_response = self._format_response(response)
        
        # 提取可执行命令
        executable_commands = self._extract_executable_commands(response)
        
        result = {
            "original": response,
            "formatted": formatted_response,
            "structured": structured_content,
            "commands": executable_commands,
            "metadata": {
                "has_code": "```" in response,
                "has_commands": len(executable_commands) > 0,
                "has_json": self._contains_json(response),
                "word_count": len(response.split())
            }
        }
        
        self.logger.debug("响应后处理完成")
        return result
    
    def get_system_prompt(self, prompt_type: str) -> Optional[str]:
        """获取系统提示"""
        return self.system_prompts.get(prompt_type)
    
    def add_system_prompt(self, prompt_type: str, prompt: str):
        """添加系统提示"""
        self.system_prompts[prompt_type] = prompt
        self.logger.info(f"已添加系统提示: {prompt_type}")
    
    def _detect_message_type(self, message: str) -> MessageType:
        """检测消息类型"""
        message_lower = message.lower().strip()
        
        # 检查是否为命令
        if message.startswith('/'):
            return MessageType.COMMAND
        
        # 检查是否包含代码块
        if '```' in message:
            return MessageType.CODE
        
        # 检查是否为JSON
        if message.strip().startswith('{') and message.strip().endswith('}'):
            try:
                json.loads(message)
                return MessageType.JSON
            except json.JSONDecodeError:
                pass
        
        # 检查是否为Markdown
        markdown_indicators = ['#', '*', '-', '`', '[', ']', '(', ')']
        if any(indicator in message for indicator in markdown_indicators):
            return MessageType.MARKDOWN
        
        return MessageType.TEXT
    
    def _extract_commands(self, message: str) -> List[str]:
        """提取命令"""
        commands = []
        matches = self.command_pattern.findall(message)
        
        for match in matches:
            command = match[0]
            args = match[1] if match[1] else ""
            full_command = f"{command} {args}".strip()
            commands.append(full_command)
        
        return commands
    
    def _extract_code_blocks(self, message: str) -> List[Dict[str, str]]:
        """提取代码块"""
        code_blocks = []
        matches = self.code_block_pattern.findall(message)
        
        for match in matches:
            language = match[0] if match[0] else "text"
            code = match[1].strip()
            
            code_blocks.append({
                "language": language,
                "code": code
            })
        
        return code_blocks
    
    async def _process_content(
        self,
        message: str,
        message_type: MessageType,
        context: Dict[str, Any]
    ) -> str:
        """处理消息内容"""
        processed = message
        
        # 根据消息类型进行特殊处理
        if message_type == MessageType.COMMAND:
            processed = self._process_command_message(message, context)
        elif message_type == MessageType.CODE:
            processed = self._process_code_message(message, context)
        elif message_type == MessageType.JSON:
            processed = self._process_json_message(message, context)
        
        # 通用处理
        processed = self._clean_message(processed)
        
        return processed
    
    def _process_command_message(self, message: str, context: Dict[str, Any]) -> str:
        """处理命令消息"""
        # 为命令消息添加上下文信息
        if context.get("add_context", True):
            return f"请执行以下命令：\n{message}\n\n请提供执行结果和相关说明。"
        return message
    
    def _process_code_message(self, message: str, context: Dict[str, Any]) -> str:
        """处理代码消息"""
        # 为代码消息添加分析请求
        if context.get("analyze_code", True):
            return f"{message}\n\n请分析这段代码并提供改进建议。"
        return message
    
    def _process_json_message(self, message: str, context: Dict[str, Any]) -> str:
        """处理JSON消息"""
        try:
            # 验证和格式化JSON
            data = json.loads(message)
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            return f"请处理以下JSON数据：\n```json\n{formatted_json}\n```"
        except json.JSONDecodeError:
            return message
    
    def _clean_message(self, message: str) -> str:
        """清理消息"""
        # 移除多余的空白字符
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', message)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _extract_structured_content(self, response: str) -> Dict[str, Any]:
        """提取结构化内容"""
        structured = {
            "code_blocks": self._extract_code_blocks(response),
            "json_data": [],
            "lists": [],
            "tables": []
        }
        
        # 提取JSON数据
        json_matches = self.json_pattern.findall(response)
        for json_str in json_matches:
            try:
                data = json.loads(json_str)
                structured["json_data"].append(data)
            except json.JSONDecodeError:
                pass
        
        # 提取列表
        list_pattern = re.compile(r'^[-*+]\s+(.+)$', re.MULTILINE)
        lists = list_pattern.findall(response)
        if lists:
            structured["lists"] = lists
        
        return structured
    
    def _format_response(self, response: str) -> str:
        """格式化响应"""
        # 基本格式化
        formatted = response.strip()
        
        # 确保代码块有适当的间距
        formatted = re.sub(r'```(\w+)?\n', r'\n```\1\n', formatted)
        formatted = re.sub(r'\n```\n', r'\n```\n\n', formatted)
        
        return formatted
    
    def _extract_executable_commands(self, response: str) -> List[str]:
        """提取可执行命令"""
        commands = []
        
        # 提取以/开头的命令
        command_matches = self.command_pattern.findall(response)
        for match in commands:
            command = match[0]
            args = match[1] if match[1] else ""
            commands.append(f"{command} {args}".strip())
        
        # 提取shell命令（在代码块中）
        code_blocks = self._extract_code_blocks(response)
        for block in code_blocks:
            if block["language"] in ["bash", "sh", "shell"]:
                commands.extend(block["code"].split('\n'))
        
        return [cmd.strip() for cmd in commands if cmd.strip()]
    
    def _contains_json(self, text: str) -> bool:
        """检查是否包含JSON"""
        return bool(self.json_pattern.search(text))


# 全局消息处理器实例
_processor: Optional[MessageProcessor] = None


def get_message_processor() -> MessageProcessor:
    """获取全局消息处理器实例"""
    global _processor
    if _processor is None:
        _processor = MessageProcessor()
    return _processor

