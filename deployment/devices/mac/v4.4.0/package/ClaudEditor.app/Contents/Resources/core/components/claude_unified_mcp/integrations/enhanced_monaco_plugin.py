"""
Enhanced Monaco Plugin - Claude驱动的代码功能
集成Monaco编辑器与Claude AI，提供智能代码编辑体验
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

from ..intelligence.enhanced_ai_assistant import EnhancedAIAssistant, AssistantMode

class CompletionKind(Enum):
    """补全类型"""
    TEXT = "text"
    METHOD = "method"
    FUNCTION = "function"
    CONSTRUCTOR = "constructor"
    FIELD = "field"
    VARIABLE = "variable"
    CLASS = "class"
    INTERFACE = "interface"
    MODULE = "module"
    PROPERTY = "property"
    UNIT = "unit"
    VALUE = "value"
    ENUM = "enum"
    KEYWORD = "keyword"
    SNIPPET = "snippet"
    COLOR = "color"
    FILE = "file"
    REFERENCE = "reference"

class DiagnosticSeverity(Enum):
    """诊断严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"
    HINT = "hint"

@dataclass
class Position:
    """编辑器位置"""
    line: int
    column: int

@dataclass
class Range:
    """编辑器范围"""
    start: Position
    end: Position

@dataclass
class CompletionItem:
    """代码补全项"""
    label: str
    kind: CompletionKind
    detail: str
    documentation: str
    insert_text: str
    sort_text: Optional[str] = None
    filter_text: Optional[str] = None
    range: Optional[Range] = None
    command: Optional[Dict[str, Any]] = None

@dataclass
class Diagnostic:
    """代码诊断"""
    range: Range
    message: str
    severity: DiagnosticSeverity
    code: Optional[str] = None
    source: str = "Claude AI"
    related_information: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class CodeAction:
    """代码操作"""
    title: str
    kind: str
    edit: Optional[Dict[str, Any]] = None
    command: Optional[Dict[str, Any]] = None
    is_preferred: bool = False

@dataclass
class HoverInfo:
    """悬停信息"""
    contents: List[str]
    range: Optional[Range] = None

class EnhancedMonacoPlugin:
    """
    增强的Monaco编辑器插件
    提供Claude AI驱动的智能代码编辑功能
    """
    
    def __init__(self, 
                 claude_api_key: str,
                 gemini_api_key: Optional[str] = None,
                 enable_aicore: bool = True,
                 auto_completion_delay: int = 500,
                 max_completions: int = 20,
                 enable_real_time_diagnostics: bool = True,
                 enable_hover_info: bool = True):
        """
        初始化增强Monaco插件
        
        Args:
            claude_api_key: Claude API密钥
            gemini_api_key: Gemini API密钥
            enable_aicore: 是否启用AICore集成
            auto_completion_delay: 自动补全延迟（毫秒）
            max_completions: 最大补全数量
            enable_real_time_diagnostics: 是否启用实时诊断
            enable_hover_info: 是否启用悬停信息
        """
        self.claude_api_key = claude_api_key
        self.gemini_api_key = gemini_api_key
        self.enable_aicore = enable_aicore
        self.auto_completion_delay = auto_completion_delay
        self.max_completions = max_completions
        self.enable_real_time_diagnostics = enable_real_time_diagnostics
        self.enable_hover_info = enable_hover_info
        
        # 核心组件
        self.ai_assistant: Optional[EnhancedAIAssistant] = None
        
        # 缓存系统
        self.completion_cache: Dict[str, List[CompletionItem]] = {}
        self.diagnostic_cache: Dict[str, List[Diagnostic]] = {}
        self.hover_cache: Dict[str, HoverInfo] = {}
        
        # 会话管理
        self.editor_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 支持的语言
        self.supported_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'html',
            'css', 'scss', 'json', 'yaml', 'xml', 'markdown'
        }
        
        # 语言特定配置
        self.language_configs = {
            'python': {
                'keywords': ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'lambda', 'global', 'nonlocal'],
                'snippets': {
                    'def': 'def ${1:function_name}(${2:parameters}):\n    ${3:pass}',
                    'class': 'class ${1:ClassName}:\n    def __init__(self${2:, parameters}):\n        ${3:pass}',
                    'if': 'if ${1:condition}:\n    ${2:pass}',
                    'for': 'for ${1:item} in ${2:iterable}:\n    ${3:pass}',
                    'try': 'try:\n    ${1:pass}\nexcept ${2:Exception} as ${3:e}:\n    ${4:pass}'
                }
            },
            'javascript': {
                'keywords': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'try', 'catch', 'finally', 'return', 'class', 'extends', 'import', 'export'],
                'snippets': {
                    'function': 'function ${1:functionName}(${2:parameters}) {\n    ${3:// code}\n}',
                    'arrow': '(${1:parameters}) => {\n    ${2:// code}\n}',
                    'class': 'class ${1:ClassName} {\n    constructor(${2:parameters}) {\n        ${3:// code}\n    }\n}',
                    'if': 'if (${1:condition}) {\n    ${2:// code}\n}',
                    'for': 'for (${1:let i = 0}; ${2:i < length}; ${3:i++}) {\n    ${4:// code}\n}'
                }
            },
            'typescript': {
                'keywords': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'try', 'catch', 'finally', 'return', 'class', 'extends', 'import', 'export', 'interface', 'type', 'enum'],
                'snippets': {
                    'interface': 'interface ${1:InterfaceName} {\n    ${2:property}: ${3:type};\n}',
                    'type': 'type ${1:TypeName} = ${2:type};',
                    'function': 'function ${1:functionName}(${2:parameters}): ${3:returnType} {\n    ${4:// code}\n}',
                    'class': 'class ${1:ClassName} {\n    constructor(${2:parameters}) {\n        ${3:// code}\n    }\n}'
                }
            }
        }
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            'completions_provided': 0,
            'diagnostics_generated': 0,
            'hover_info_provided': 0,
            'code_actions_generated': 0,
            'cache_hits': 0,
            'ai_requests': 0,
            'average_completion_time': 0.0,
            'total_completion_time': 0.0,
            'language_usage': {lang: 0 for lang in self.supported_languages}
        }
    
    async def initialize(self):
        """初始化Monaco插件"""
        try:
            # 初始化AI助手
            self.ai_assistant = EnhancedAIAssistant(
                claude_api_key=self.claude_api_key,
                gemini_api_key=self.gemini_api_key,
                enable_aicore=self.enable_aicore
            )
            await self.ai_assistant.initialize()
            
            self.logger.info("Enhanced Monaco Plugin initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Monaco Plugin: {e}")
            raise
    
    async def close(self):
        """关闭Monaco插件"""
        try:
            if self.ai_assistant:
                await self.ai_assistant.close()
            
            self.logger.info("Enhanced Monaco Plugin closed")
            
        except Exception as e:
            self.logger.error(f"Error closing Monaco Plugin: {e}")
    
    def _get_cache_key(self, content: str, position: Position, language: str, operation: str) -> str:
        """生成缓存键"""
        content_hash = hash(content)
        return f"{operation}:{language}:{content_hash}:{position.line}:{position.column}"
    
    def _extract_context(self, content: str, position: Position, context_lines: int = 5) -> Dict[str, Any]:
        """提取代码上下文"""
        lines = content.split('\n')
        current_line = position.line
        
        # 获取上下文行
        start_line = max(0, current_line - context_lines)
        end_line = min(len(lines), current_line + context_lines + 1)
        
        context_lines_content = lines[start_line:end_line]
        
        # 获取当前行和光标位置
        current_line_content = lines[current_line] if current_line < len(lines) else ""
        cursor_position = position.column
        
        # 获取光标前后的文本
        text_before_cursor = current_line_content[:cursor_position]
        text_after_cursor = current_line_content[cursor_position:]
        
        return {
            'context_lines': context_lines_content,
            'current_line': current_line_content,
            'text_before_cursor': text_before_cursor,
            'text_after_cursor': text_after_cursor,
            'line_number': current_line,
            'column_number': cursor_position
        }
    
    async def provide_completions(self, 
                                 content: str,
                                 position: Position,
                                 language: str,
                                 session_id: Optional[str] = None) -> List[CompletionItem]:
        """
        提供代码补全建议
        
        Args:
            content: 文档内容
            position: 光标位置
            language: 编程语言
            session_id: 编辑器会话ID
            
        Returns:
            补全项列表
        """
        start_time = time.time()
        
        try:
            if language not in self.supported_languages:
                return []
            
            # 检查缓存
            cache_key = self._get_cache_key(content, position, language, "completion")
            if cache_key in self.completion_cache:
                self.stats['cache_hits'] += 1
                return self.completion_cache[cache_key]
            
            # 提取上下文
            context = self._extract_context(content, position)
            
            # 获取语言配置
            lang_config = self.language_configs.get(language, {})
            
            completions = []
            
            # 1. 添加关键字补全
            if 'keywords' in lang_config:
                text_before = context['text_before_cursor'].split()
                if text_before:
                    last_word = text_before[-1].lower()
                    for keyword in lang_config['keywords']:
                        if keyword.startswith(last_word):
                            completions.append(CompletionItem(
                                label=keyword,
                                kind=CompletionKind.KEYWORD,
                                detail=f"{language} keyword",
                                documentation=f"Language keyword: {keyword}",
                                insert_text=keyword,
                                sort_text=f"0_{keyword}"
                            ))
            
            # 2. 添加代码片段补全
            if 'snippets' in lang_config:
                text_before = context['text_before_cursor'].strip()
                for snippet_name, snippet_content in lang_config['snippets'].items():
                    if snippet_name.startswith(text_before.split()[-1] if text_before.split() else ""):
                        completions.append(CompletionItem(
                            label=snippet_name,
                            kind=CompletionKind.SNIPPET,
                            detail=f"{language} snippet",
                            documentation=f"Code snippet: {snippet_name}",
                            insert_text=snippet_content,
                            sort_text=f"1_{snippet_name}"
                        ))
            
            # 3. 使用AI生成智能补全
            if self.ai_assistant and len(context['text_before_cursor'].strip()) >= 2:
                ai_completions = await self._get_ai_completions(content, position, language, context, session_id)
                completions.extend(ai_completions)
            
            # 限制补全数量
            completions = completions[:self.max_completions]
            
            # 缓存结果
            self.completion_cache[cache_key] = completions
            
            # 更新统计
            self.stats['completions_provided'] += 1
            completion_time = time.time() - start_time
            self.stats['total_completion_time'] += completion_time
            self.stats['average_completion_time'] = self.stats['total_completion_time'] / self.stats['completions_provided']
            self.stats['language_usage'][language] += 1
            
            return completions
            
        except Exception as e:
            self.logger.error(f"Completion provision failed: {e}")
            return []
    
    async def _get_ai_completions(self, 
                                 content: str,
                                 position: Position,
                                 language: str,
                                 context: Dict[str, Any],
                                 session_id: Optional[str]) -> List[CompletionItem]:
        """使用AI生成智能补全"""
        try:
            self.stats['ai_requests'] += 1
            
            # 构建补全提示
            prompt = f"""Provide code completion suggestions for this {language} code:

Current line: {context['current_line']}
Cursor position: {context['column_number']}
Text before cursor: "{context['text_before_cursor']}"

Context:
```{language}
{''.join(context['context_lines'])}
```

Provide 3-5 most likely completions. Format as JSON array with objects containing:
- "text": the completion text
- "description": brief description
- "type": one of "function", "variable", "method", "class", "keyword", "snippet"

Example:
[
  {{"text": "append(", "description": "Add item to list", "type": "method"}},
  {{"text": "len(", "description": "Get length", "type": "function"}}
]"""
            
            # 发送AI请求
            response = await self.ai_assistant.ask_and_wait(
                prompt=prompt,
                mode=AssistantMode.CODE_ASSISTANT,
                session_id=session_id,
                context={
                    'language': language,
                    'operation': 'completion',
                    **context
                },
                timeout=10.0
            )
            
            if not response or not response.content:
                return []
            
            # 解析AI响应
            try:
                # 尝试提取JSON
                content_text = response.content.strip()
                if '```json' in content_text:
                    json_start = content_text.find('```json') + 7
                    json_end = content_text.find('```', json_start)
                    json_text = content_text[json_start:json_end].strip()
                elif '[' in content_text and ']' in content_text:
                    json_start = content_text.find('[')
                    json_end = content_text.rfind(']') + 1
                    json_text = content_text[json_start:json_end]
                else:
                    return []
                
                ai_suggestions = json.loads(json_text)
                
                completions = []
                for i, suggestion in enumerate(ai_suggestions[:5]):
                    if isinstance(suggestion, dict) and 'text' in suggestion:
                        kind_map = {
                            'function': CompletionKind.FUNCTION,
                            'method': CompletionKind.METHOD,
                            'variable': CompletionKind.VARIABLE,
                            'class': CompletionKind.CLASS,
                            'keyword': CompletionKind.KEYWORD,
                            'snippet': CompletionKind.SNIPPET
                        }
                        
                        kind = kind_map.get(suggestion.get('type', 'text'), CompletionKind.TEXT)
                        
                        completions.append(CompletionItem(
                            label=suggestion['text'],
                            kind=kind,
                            detail=suggestion.get('description', 'AI suggestion'),
                            documentation=f"Claude AI suggestion: {suggestion.get('description', '')}",
                            insert_text=suggestion['text'],
                            sort_text=f"2_{i:02d}"
                        ))
                
                return completions
                
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试简单文本解析
                lines = response.content.strip().split('\n')
                completions = []
                for i, line in enumerate(lines[:5]):
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        completions.append(CompletionItem(
                            label=line,
                            kind=CompletionKind.TEXT,
                            detail="AI suggestion",
                            documentation=f"Claude AI suggestion: {line}",
                            insert_text=line,
                            sort_text=f"2_{i:02d}"
                        ))
                
                return completions
            
        except Exception as e:
            self.logger.error(f"AI completion failed: {e}")
            return []
    
    async def provide_diagnostics(self, 
                                 content: str,
                                 language: str,
                                 session_id: Optional[str] = None) -> List[Diagnostic]:
        """
        提供代码诊断
        
        Args:
            content: 文档内容
            language: 编程语言
            session_id: 编辑器会话ID
            
        Returns:
            诊断列表
        """
        try:
            if not self.enable_real_time_diagnostics or language not in self.supported_languages:
                return []
            
            # 检查缓存
            cache_key = f"diagnostic:{language}:{hash(content)}"
            if cache_key in self.diagnostic_cache:
                self.stats['cache_hits'] += 1
                return self.diagnostic_cache[cache_key]
            
            # 使用AI分析代码
            if self.ai_assistant:
                prompt = f"""Analyze this {language} code for potential issues:

```{language}
{content}
```

Identify:
1. Syntax errors
2. Logic issues
3. Performance problems
4. Best practice violations
5. Security concerns

Format as JSON array with objects containing:
- "line": line number (0-based)
- "column": column number (0-based)
- "endLine": end line number
- "endColumn": end column number
- "message": description of the issue
- "severity": "error", "warning", "information", or "hint"
- "code": optional error code

Example:
[
  {{"line": 5, "column": 0, "endLine": 5, "endColumn": 10, "message": "Undefined variable", "severity": "error", "code": "undefined-var"}}
]"""
                
                response = await self.ai_assistant.ask_and_wait(
                    prompt=prompt,
                    mode=AssistantMode.DEBUGGER,
                    session_id=session_id,
                    context={
                        'language': language,
                        'operation': 'diagnostic',
                        'content': content
                    },
                    timeout=15.0
                )
                
                if response and response.content:
                    diagnostics = self._parse_diagnostics(response.content)
                    
                    # 缓存结果
                    self.diagnostic_cache[cache_key] = diagnostics
                    self.stats['diagnostics_generated'] += 1
                    
                    return diagnostics
            
            return []
            
        except Exception as e:
            self.logger.error(f"Diagnostic provision failed: {e}")
            return []
    
    def _parse_diagnostics(self, ai_response: str) -> List[Diagnostic]:
        """解析AI诊断响应"""
        try:
            # 尝试提取JSON
            content_text = ai_response.strip()
            if '```json' in content_text:
                json_start = content_text.find('```json') + 7
                json_end = content_text.find('```', json_start)
                json_text = content_text[json_start:json_end].strip()
            elif '[' in content_text and ']' in content_text:
                json_start = content_text.find('[')
                json_end = content_text.rfind(']') + 1
                json_text = content_text[json_start:json_end]
            else:
                return []
            
            ai_diagnostics = json.loads(json_text)
            
            diagnostics = []
            for diag in ai_diagnostics:
                if isinstance(diag, dict) and all(k in diag for k in ['line', 'column', 'message', 'severity']):
                    severity_map = {
                        'error': DiagnosticSeverity.ERROR,
                        'warning': DiagnosticSeverity.WARNING,
                        'information': DiagnosticSeverity.INFORMATION,
                        'hint': DiagnosticSeverity.HINT
                    }
                    
                    severity = severity_map.get(diag['severity'], DiagnosticSeverity.WARNING)
                    
                    diagnostics.append(Diagnostic(
                        range=Range(
                            start=Position(line=diag['line'], column=diag['column']),
                            end=Position(
                                line=diag.get('endLine', diag['line']),
                                column=diag.get('endColumn', diag['column'] + 1)
                            )
                        ),
                        message=diag['message'],
                        severity=severity,
                        code=diag.get('code'),
                        source="Claude AI"
                    ))
            
            return diagnostics
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse diagnostics: {e}")
            return []
    
    async def provide_hover_info(self, 
                                content: str,
                                position: Position,
                                language: str,
                                session_id: Optional[str] = None) -> Optional[HoverInfo]:
        """
        提供悬停信息
        
        Args:
            content: 文档内容
            position: 鼠标位置
            language: 编程语言
            session_id: 编辑器会话ID
            
        Returns:
            悬停信息或None
        """
        try:
            if not self.enable_hover_info or language not in self.supported_languages:
                return None
            
            # 检查缓存
            cache_key = self._get_cache_key(content, position, language, "hover")
            if cache_key in self.hover_cache:
                self.stats['cache_hits'] += 1
                return self.hover_cache[cache_key]
            
            # 提取上下文
            context = self._extract_context(content, position, 3)
            
            # 获取光标处的单词
            line = context['current_line']
            col = position.column
            
            # 找到单词边界
            start = col
            while start > 0 and (line[start-1].isalnum() or line[start-1] == '_'):
                start -= 1
            
            end = col
            while end < len(line) and (line[end].isalnum() or line[end] == '_'):
                end += 1
            
            word = line[start:end]
            
            if not word or len(word) < 2:
                return None
            
            # 使用AI获取悬停信息
            if self.ai_assistant:
                prompt = f"""Provide hover information for the symbol "{word}" in this {language} code context:

```{language}
{content}
```

Line {position.line + 1}, Column {position.column + 1}: "{word}"

Provide:
1. What this symbol represents (function, variable, class, etc.)
2. Type information (if applicable)
3. Brief description or documentation
4. Usage example (if helpful)

Keep it concise but informative."""
                
                response = await self.ai_assistant.ask_and_wait(
                    prompt=prompt,
                    mode=AssistantMode.TEACHER,
                    session_id=session_id,
                    context={
                        'language': language,
                        'operation': 'hover',
                        'symbol': word,
                        **context
                    },
                    timeout=8.0
                )
                
                if response and response.content:
                    hover_info = HoverInfo(
                        contents=[response.content],
                        range=Range(
                            start=Position(line=position.line, column=start),
                            end=Position(line=position.line, column=end)
                        )
                    )
                    
                    # 缓存结果
                    self.hover_cache[cache_key] = hover_info
                    self.stats['hover_info_provided'] += 1
                    
                    return hover_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Hover info provision failed: {e}")
            return None
    
    async def provide_code_actions(self, 
                                  content: str,
                                  range: Range,
                                  language: str,
                                  diagnostics: List[Diagnostic],
                                  session_id: Optional[str] = None) -> List[CodeAction]:
        """
        提供代码操作建议
        
        Args:
            content: 文档内容
            range: 选中范围
            language: 编程语言
            diagnostics: 相关诊断
            session_id: 编辑器会话ID
            
        Returns:
            代码操作列表
        """
        try:
            if language not in self.supported_languages:
                return []
            
            actions = []
            
            # 获取选中的代码
            lines = content.split('\n')
            selected_lines = lines[range.start.line:range.end.line + 1]
            selected_text = '\n'.join(selected_lines)
            
            if not selected_text.strip():
                return []
            
            # 使用AI生成代码操作
            if self.ai_assistant:
                prompt = f"""Suggest code actions for this {language} code:

Selected code:
```{language}
{selected_text}
```

Full context:
```{language}
{content}
```

Diagnostics: {[d.message for d in diagnostics]}

Suggest actions like:
1. Quick fixes for errors
2. Refactoring suggestions
3. Code improvements
4. Extract method/variable
5. Add documentation

Format as JSON array with objects containing:
- "title": action description
- "kind": "quickfix", "refactor", "source", etc.
- "description": detailed description
- "newCode": the improved code (if applicable)

Example:
[
  {{"title": "Extract method", "kind": "refactor", "description": "Extract selected code into a new method", "newCode": "def new_method():\\n    # extracted code"}}
]"""
                
                response = await self.ai_assistant.ask_and_wait(
                    prompt=prompt,
                    mode=AssistantMode.OPTIMIZER,
                    session_id=session_id,
                    context={
                        'language': language,
                        'operation': 'code_action',
                        'selected_text': selected_text,
                        'diagnostics': [d.message for d in diagnostics]
                    },
                    timeout=12.0
                )
                
                if response and response.content:
                    actions = self._parse_code_actions(response.content, range)
                    self.stats['code_actions_generated'] += len(actions)
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Code action provision failed: {e}")
            return []
    
    def _parse_code_actions(self, ai_response: str, range: Range) -> List[CodeAction]:
        """解析AI代码操作响应"""
        try:
            # 尝试提取JSON
            content_text = ai_response.strip()
            if '```json' in content_text:
                json_start = content_text.find('```json') + 7
                json_end = content_text.find('```', json_start)
                json_text = content_text[json_start:json_end].strip()
            elif '[' in content_text and ']' in content_text:
                json_start = content_text.find('[')
                json_end = content_text.rfind(']') + 1
                json_text = content_text[json_start:json_end]
            else:
                return []
            
            ai_actions = json.loads(json_text)
            
            actions = []
            for action in ai_actions:
                if isinstance(action, dict) and 'title' in action:
                    code_action = CodeAction(
                        title=action['title'],
                        kind=action.get('kind', 'quickfix')
                    )
                    
                    # 如果有新代码，创建编辑操作
                    if 'newCode' in action:
                        code_action.edit = {
                            'changes': {
                                'uri': 'current_document',
                                'edits': [{
                                    'range': {
                                        'start': {'line': range.start.line, 'column': range.start.column},
                                        'end': {'line': range.end.line, 'column': range.end.column}
                                    },
                                    'newText': action['newCode']
                                }]
                            }
                        }
                    
                    actions.append(code_action)
            
            return actions
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse code actions: {e}")
            return []
    
    def create_editor_session(self, session_id: str, language: str, initial_content: str = "") -> Dict[str, Any]:
        """创建编辑器会话"""
        session = {
            'id': session_id,
            'language': language,
            'created_at': time.time(),
            'last_activity': time.time(),
            'content_history': [initial_content],
            'completion_count': 0,
            'diagnostic_count': 0
        }
        
        self.editor_sessions[session_id] = session
        return session
    
    def update_editor_session(self, session_id: str, content: str):
        """更新编辑器会话"""
        if session_id in self.editor_sessions:
            session = self.editor_sessions[session_id]
            session['last_activity'] = time.time()
            session['content_history'].append(content)
            
            # 保留最近10个版本
            if len(session['content_history']) > 10:
                session['content_history'] = session['content_history'][-10:]
    
    def get_editor_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取编辑器会话"""
        return self.editor_sessions.get(session_id)
    
    def clear_cache(self):
        """清空缓存"""
        self.completion_cache.clear()
        self.diagnostic_cache.clear()
        self.hover_cache.clear()
        self.logger.info("Monaco plugin cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        return {
            **self.stats,
            'cache_sizes': {
                'completion': len(self.completion_cache),
                'diagnostic': len(self.diagnostic_cache),
                'hover': len(self.hover_cache)
            },
            'active_sessions': len(self.editor_sessions),
            'supported_languages': list(self.supported_languages),
            'ai_assistant_stats': self.ai_assistant.get_stats() if self.ai_assistant else {}
        }

# JavaScript接口生成器
def generate_monaco_javascript_interface() -> str:
    """生成Monaco编辑器的JavaScript接口"""
    return """
// Enhanced Monaco Plugin JavaScript Interface
class EnhancedMonacoPlugin {
    constructor(apiEndpoint = '/api/monaco') {
        this.apiEndpoint = apiEndpoint;
        this.sessionId = this.generateSessionId();
        this.completionProvider = null;
        this.diagnosticsProvider = null;
        this.hoverProvider = null;
        this.codeActionProvider = null;
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }
    
    async initialize(monaco, editor, language) {
        this.monaco = monaco;
        this.editor = editor;
        this.language = language;
        
        // 注册补全提供器
        this.completionProvider = monaco.languages.registerCompletionItemProvider(language, {
            provideCompletionItems: async (model, position) => {
                const content = model.getValue();
                const completions = await this.getCompletions(content, position);
                
                return {
                    suggestions: completions.map(item => ({
                        label: item.label,
                        kind: this.getMonacoCompletionKind(item.kind),
                        detail: item.detail,
                        documentation: item.documentation,
                        insertText: item.insert_text,
                        sortText: item.sort_text,
                        range: item.range
                    }))
                };
            }
        });
        
        // 注册诊断提供器
        this.diagnosticsProvider = monaco.languages.registerCodeActionProvider(language, {
            provideCodeActions: async (model, range, context) => {
                const content = model.getValue();
                const diagnostics = context.markers || [];
                const actions = await this.getCodeActions(content, range, diagnostics);
                
                return {
                    actions: actions.map(action => ({
                        title: action.title,
                        kind: action.kind,
                        edit: action.edit,
                        command: action.command,
                        isPreferred: action.is_preferred
                    }))
                };
            }
        });
        
        // 注册悬停提供器
        this.hoverProvider = monaco.languages.registerHoverProvider(language, {
            provideHover: async (model, position) => {
                const content = model.getValue();
                const hoverInfo = await this.getHoverInfo(content, position);
                
                if (hoverInfo) {
                    return {
                        contents: hoverInfo.contents.map(content => ({ value: content })),
                        range: hoverInfo.range
                    };
                }
                
                return null;
            }
        });
        
        // 设置实时诊断
        this.setupRealTimeDiagnostics(editor);
        
        console.log('Enhanced Monaco Plugin initialized for', language);
    }
    
    async getCompletions(content, position) {
        try {
            const response = await fetch(`${this.apiEndpoint}/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    position: {
                        line: position.lineNumber - 1,
                        column: position.column - 1
                    },
                    language: this.language,
                    session_id: this.sessionId
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get completions:', error);
        }
        
        return [];
    }
    
    async getDiagnostics(content) {
        try {
            const response = await fetch(`${this.apiEndpoint}/diagnostics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    language: this.language,
                    session_id: this.sessionId
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get diagnostics:', error);
        }
        
        return [];
    }
    
    async getHoverInfo(content, position) {
        try {
            const response = await fetch(`${this.apiEndpoint}/hover`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    position: {
                        line: position.lineNumber - 1,
                        column: position.column - 1
                    },
                    language: this.language,
                    session_id: this.sessionId
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get hover info:', error);
        }
        
        return null;
    }
    
    async getCodeActions(content, range, diagnostics) {
        try {
            const response = await fetch(`${this.apiEndpoint}/code-actions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    range: {
                        start: {
                            line: range.startLineNumber - 1,
                            column: range.startColumn - 1
                        },
                        end: {
                            line: range.endLineNumber - 1,
                            column: range.endColumn - 1
                        }
                    },
                    language: this.language,
                    diagnostics: diagnostics.map(d => ({
                        message: d.message,
                        severity: d.severity,
                        code: d.code
                    })),
                    session_id: this.sessionId
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get code actions:', error);
        }
        
        return [];
    }
    
    setupRealTimeDiagnostics(editor) {
        let diagnosticsTimeout;
        
        editor.onDidChangeModelContent(() => {
            clearTimeout(diagnosticsTimeout);
            diagnosticsTimeout = setTimeout(async () => {
                const content = editor.getValue();
                const diagnostics = await this.getDiagnostics(content);
                
                // 转换为Monaco标记
                const markers = diagnostics.map(diag => ({
                    startLineNumber: diag.range.start.line + 1,
                    startColumn: diag.range.start.column + 1,
                    endLineNumber: diag.range.end.line + 1,
                    endColumn: diag.range.end.column + 1,
                    message: diag.message,
                    severity: this.getMonacoSeverity(diag.severity),
                    code: diag.code,
                    source: diag.source
                }));
                
                this.monaco.editor.setModelMarkers(editor.getModel(), 'claude-ai', markers);
            }, 1000);
        });
    }
    
    getMonacoCompletionKind(kind) {
        const kindMap = {
            'text': this.monaco.languages.CompletionItemKind.Text,
            'method': this.monaco.languages.CompletionItemKind.Method,
            'function': this.monaco.languages.CompletionItemKind.Function,
            'constructor': this.monaco.languages.CompletionItemKind.Constructor,
            'field': this.monaco.languages.CompletionItemKind.Field,
            'variable': this.monaco.languages.CompletionItemKind.Variable,
            'class': this.monaco.languages.CompletionItemKind.Class,
            'interface': this.monaco.languages.CompletionItemKind.Interface,
            'module': this.monaco.languages.CompletionItemKind.Module,
            'property': this.monaco.languages.CompletionItemKind.Property,
            'unit': this.monaco.languages.CompletionItemKind.Unit,
            'value': this.monaco.languages.CompletionItemKind.Value,
            'enum': this.monaco.languages.CompletionItemKind.Enum,
            'keyword': this.monaco.languages.CompletionItemKind.Keyword,
            'snippet': this.monaco.languages.CompletionItemKind.Snippet,
            'color': this.monaco.languages.CompletionItemKind.Color,
            'file': this.monaco.languages.CompletionItemKind.File,
            'reference': this.monaco.languages.CompletionItemKind.Reference
        };
        
        return kindMap[kind] || this.monaco.languages.CompletionItemKind.Text;
    }
    
    getMonacoSeverity(severity) {
        const severityMap = {
            'error': this.monaco.MarkerSeverity.Error,
            'warning': this.monaco.MarkerSeverity.Warning,
            'information': this.monaco.MarkerSeverity.Info,
            'hint': this.monaco.MarkerSeverity.Hint
        };
        
        return severityMap[severity] || this.monaco.MarkerSeverity.Warning;
    }
    
    dispose() {
        if (this.completionProvider) {
            this.completionProvider.dispose();
        }
        if (this.diagnosticsProvider) {
            this.diagnosticsProvider.dispose();
        }
        if (this.hoverProvider) {
            this.hoverProvider.dispose();
        }
        if (this.codeActionProvider) {
            this.codeActionProvider.dispose();
        }
        
        console.log('Enhanced Monaco Plugin disposed');
    }
}

// 使用示例
/*
const plugin = new EnhancedMonacoPlugin('/api/monaco');
await plugin.initialize(monaco, editor, 'python');
*/
"""

# 使用示例
async def main():
    """使用示例"""
    # 使用提供的API密钥
    claude_key = "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"
    gemini_key = "AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA"
    
    plugin = EnhancedMonacoPlugin(
        claude_api_key=claude_key,
        gemini_api_key=gemini_key,
        enable_aicore=True
    )
    
    try:
        await plugin.initialize()
        
        # 创建编辑器会话
        session_id = "demo_session"
        plugin.create_editor_session(session_id, "python")
        
        # 代码补全示例
        code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    "
        position = Position(line=3, column=4)
        
        completions = await plugin.provide_completions(code, position, "python", session_id)
        print(f"Completions: {len(completions)} items")
        for comp in completions[:3]:
            print(f"  - {comp.label}: {comp.detail}")
        
        # 代码诊断示例
        buggy_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 调用函数但没有定义变量
result = fibonacci(undefined_var)
print(result)
"""
        
        diagnostics = await plugin.provide_diagnostics(buggy_code, "python", session_id)
        print(f"Diagnostics: {len(diagnostics)} issues")
        for diag in diagnostics:
            print(f"  - Line {diag.range.start.line}: {diag.message} ({diag.severity.value})")
        
        # 悬停信息示例
        hover_position = Position(line=1, column=4)  # "fibonacci"
        hover_info = await plugin.provide_hover_info(code, hover_position, "python", session_id)
        if hover_info:
            print(f"Hover info: {hover_info.contents[0][:100]}...")
        
        # 获取统计信息
        stats = plugin.get_stats()
        print("Plugin stats:", {k: v for k, v in stats.items() if k in ['completions_provided', 'diagnostics_generated', 'hover_info_provided']})
        
    finally:
        await plugin.close()

if __name__ == "__main__":
    asyncio.run(main())

