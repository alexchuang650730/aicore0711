"""
Monaco Claude Plugin - 统一版本
整合claude_integration_mcp中的Monaco编辑器集成功能
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import time

@dataclass
class EditorPosition:
    """编辑器位置"""
    line: int
    column: int

@dataclass
class CompletionItem:
    """Monaco补全项"""
    label: str
    kind: str
    detail: str
    documentation: str
    insert_text: str
    sort_text: Optional[str] = None

class MonacoClaudePlugin:
    """
    Monaco编辑器Claude插件 - 统一版本
    提供AI驱动的代码编辑功能
    """
    
    def __init__(self, claude_client, code_analyzer=None):
        """
        初始化Monaco Claude插件
        
        Args:
            claude_client: Claude API客户端
            code_analyzer: 代码分析器（可选）
        """
        self.claude_client = claude_client
        self.code_analyzer = code_analyzer
        self.logger = logging.getLogger(__name__)
        
        # 插件配置
        self.config = {
            'auto_completion_enabled': True,
            'real_time_analysis_enabled': True,
            'hover_info_enabled': True,
            'completion_delay': 500,
            'max_completions': 10,
            'min_completion_length': 2
        }
        
        # 缓存
        self.completion_cache: Dict[str, List[CompletionItem]] = {}
        
        # 统计信息
        self.stats = {
            'completions_provided': 0,
            'cache_hits': 0
        }
    
    async def initialize(self):
        """初始化插件"""
        self.logger.info("Monaco Claude Plugin initialized")
    
    async def provide_completions(self, 
                                 content: str,
                                 position: Dict[str, int],
                                 language: str) -> List[CompletionItem]:
        """
        提供代码补全建议
        
        Args:
            content: 文档内容
            position: 光标位置 {"line": int, "column": int}
            language: 编程语言
            
        Returns:
            补全项列表
        """
        try:
            self.stats['completions_provided'] += 1
            
            # 检查缓存
            cache_key = f"{language}:{hash(content)}:{position['line']}:{position['column']}"
            if cache_key in self.completion_cache:
                self.stats['cache_hits'] += 1
                return self.completion_cache[cache_key]
            
            # 使用Claude生成补全
            response = await self.claude_client.complete_code(content, language)
            
            # 解析补全建议
            completions = self._parse_completion_response(response.content)
            
            # 限制补全数量
            completions = completions[:self.config['max_completions']]
            
            # 缓存结果
            self.completion_cache[cache_key] = completions
            
            return completions
            
        except Exception as e:
            self.logger.error(f"Completion provision failed: {e}")
            return []
    
    def _parse_completion_response(self, response_content: str) -> List[CompletionItem]:
        """解析Claude的补全响应"""
        completions = []
        
        lines = response_content.strip().split('\n')
        
        for i, line in enumerate(lines[:self.config['max_completions']]):
            line = line.strip()
            if line:
                completion = CompletionItem(
                    label=line[:50] + "..." if len(line) > 50 else line,
                    kind="text",
                    detail="Claude AI suggestion",
                    documentation=f"AI-generated completion suggestion {i+1}",
                    insert_text=line,
                    sort_text=f"{i:02d}"
                )
                completions.append(completion)
        
        return completions
    
    def get_stats(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        return {
            **self.stats,
            'completion_cache_size': len(self.completion_cache),
            'config': self.config
        }

