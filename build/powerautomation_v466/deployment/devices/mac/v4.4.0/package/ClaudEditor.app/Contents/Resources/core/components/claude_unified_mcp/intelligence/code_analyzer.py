"""
Code Analyzer - 统一版本
整合代码分析功能
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class AnalysisResult:
    """分析结果"""
    summary: str
    operations_used: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    tokens_used: int = 0

class CodeAnalyzer:
    """
    代码分析器 - 统一版本
    提供代码分析功能
    """
    
    def __init__(self, claude_client):
        """
        初始化代码分析器
        
        Args:
            claude_client: Claude API客户端
        """
        self.claude_client = claude_client
        self.logger = logging.getLogger(__name__)
        
        # 支持的编程语言
        self.supported_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin'
        }
        
        # 统计信息
        self.stats = {
            'total_analyses': 0,
            'successful_analyses': 0
        }
    
    async def initialize(self):
        """初始化分析器"""
        self.logger.info("Code Analyzer initialized")
    
    async def analyze_code(self, 
                          code: str, 
                          language: str = "python",
                          filename: Optional[str] = None) -> AnalysisResult:
        """
        分析代码
        
        Args:
            code: 要分析的代码
            language: 编程语言
            filename: 文件名
            
        Returns:
            分析结果
        """
        start_time = time.time()
        self.stats['total_analyses'] += 1
        
        try:
            # 使用Claude进行代码分析
            response = await self.claude_client.analyze_code(code, language)
            
            result = AnalysisResult(
                summary=response.content,
                operations_used=['code_analysis'],
                processing_time=time.time() - start_time,
                tokens_used=response.usage.get('total_tokens', 0)
            )
            
            self.stats['successful_analyses'] += 1
            return result
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return AnalysisResult(
                summary=f"Analysis failed: {e}",
                processing_time=time.time() - start_time
            )
    
    def get_all_operations(self) -> List[str]:
        """获取所有可用操作"""
        return ['code_analysis', 'syntax_check', 'quality_assessment']
    
    def get_stats(self) -> Dict[str, Any]:
        """获取分析器统计信息"""
        return {
            **self.stats,
            'supported_languages': list(self.supported_languages)
        }

