#!/usr/bin/env python3
"""
URL Processor - 網頁內容獲取和處理器
為 ClaudeEditor 提供網頁內容提取功能
"""

import asyncio
import aiohttp
import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import html

logger = logging.getLogger(__name__)

@dataclass
class WebContent:
    """網頁內容"""
    url: str
    title: str
    text: str
    description: str = ""
    author: str = ""
    publish_date: str = ""
    word_count: int = 0
    language: str = "auto"
    metadata: Dict[str, Any] = None

class URLProcessor:
    """URL 處理器"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (ClaudeEditor/1.0) ClaudeCode Content Processor',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_and_process(self, url: str) -> WebContent:
        """獲取並處理網頁內容"""
        try:
            # 標準化 URL
            url = self._normalize_url(url)
            
            # 獲取網頁內容
            html_content = await self._fetch_html(url)
            
            # 提取內容
            content = self._extract_content(html_content, url)
            
            # 轉換為 Claude Code 友好格式
            processed_content = self._format_for_claude_code(content)
            
            return processed_content
            
        except Exception as e:
            logger.error(f"URL 處理失敗 {url}: {e}")
            raise
    
    def _normalize_url(self, url: str) -> str:
        """標準化 URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    async def _fetch_html(self, url: str) -> str:
        """獲取 HTML 內容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return content
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except aiohttp.ClientError as e:
            raise Exception(f"網絡請求失敗: {e}")
    
    def _extract_content(self, html_content: str, url: str) -> WebContent:
        """提取網頁主要內容"""
        
        # 提取標題
        title = self._extract_title(html_content)
        
        # 提取主要文本內容
        text = self._extract_main_text(html_content)
        
        # 提取元數據
        description = self._extract_meta_description(html_content)
        author = self._extract_author(html_content)
        publish_date = self._extract_publish_date(html_content)
        
        # 計算字數
        word_count = len(text.split())
        
        # 檢測語言
        language = self._detect_language(text)
        
        return WebContent(
            url=url,
            title=title,
            text=text,
            description=description,
            author=author,
            publish_date=publish_date,
            word_count=word_count,
            language=language,
            metadata={
                'extraction_time': datetime.now().isoformat(),
                'content_length': len(text),
                'html_length': len(html_content)
            }
        )
    
    def _extract_title(self, html_content: str) -> str:
        """提取標題"""
        # 嘗試多種標題提取方法
        patterns = [
            r'<title[^>]*>([^<]+)</title>',
            r'<h1[^>]*>([^<]+)</h1>',
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']title["\'][^>]*content=["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                title = html.unescape(match.group(1).strip())
                if title:
                    return title
        
        return "無標題"
    
    def _extract_main_text(self, html_content: str) -> str:
        """提取主要文本內容"""
        # 移除腳本和樣式
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # 嘗試提取 article 內容
        article_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<main[^>]*>(.*?)</main>',
            r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]*class=["\'][^"\']*post[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]*id=["\']content["\'][^>]*>(.*?)</div>'
        ]
        
        main_content = ""
        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                main_content = match.group(1)
                break
        
        # 如果沒有找到主要內容區域，提取 body 內容
        if not main_content:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
            if body_match:
                main_content = body_match.group(1)
            else:
                main_content = html_content
        
        # 清理 HTML 標籤
        text = self._clean_html(main_content)
        
        # 格式化文本
        text = self._format_text(text)
        
        return text
    
    def _clean_html(self, html_content: str) -> str:
        """清理 HTML 標籤"""
        # 保留段落結構
        html_content = re.sub(r'<p[^>]*>', '\n\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</p>', '', html_content, flags=re.IGNORECASE)
        
        # 保留換行
        html_content = re.sub(r'<br[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<div[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        
        # 移除所有 HTML 標籤
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # 解碼 HTML 實體
        text = html.unescape(html_content)
        
        return text
    
    def _format_text(self, text: str) -> str:
        """格式化文本"""
        # 合併多個空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 合併多個換行
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # 移除過短的行（可能是導航或廣告）
        lines = [line for line in lines if len(line) > 10 or line == '']
        
        return '\n'.join(lines).strip()
    
    def _extract_meta_description(self, html_content: str) -> str:
        """提取描述"""
        patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return html.unescape(match.group(1).strip())
        
        return ""
    
    def _extract_author(self, html_content: str) -> str:
        """提取作者"""
        patterns = [
            r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']article:author["\'][^>]*content=["\']([^"\']+)["\']',
            r'<span[^>]*class=["\'][^"\']*author[^"\']*["\'][^>]*>([^<]+)</span>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return html.unescape(match.group(1).strip())
        
        return ""
    
    def _extract_publish_date(self, html_content: str) -> str:
        """提取發布日期"""
        patterns = [
            r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
            r'<time[^>]*datetime=["\']([^"\']+)["\'][^>]*>',
            r'<meta[^>]*name=["\']date["\'][^>]*content=["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _detect_language(self, text: str) -> str:
        """檢測語言"""
        # 簡單的語言檢測
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)
        
        if total_chars > 0:
            chinese_ratio = chinese_chars / total_chars
            if chinese_ratio > 0.3:
                return "zh"
            else:
                return "en"
        
        return "auto"
    
    def _format_for_claude_code(self, content: WebContent) -> WebContent:
        """格式化為 Claude Code 友好格式"""
        # 添加結構化標題
        formatted_text = f"""# {content.title}

**來源：** {content.url}
**作者：** {content.author or '未知'}
**發布日期：** {content.publish_date or '未知'}
**字數：** {content.word_count}
**語言：** {content.language}

## 內容摘要
{content.description or '無描述'}

## 正文內容

{content.text}

---
*內容由 ClaudeEditor 自動提取和格式化*
*提取時間：{content.metadata.get('extraction_time', '')}*
"""
        
        return WebContent(
            url=content.url,
            title=content.title,
            text=formatted_text,
            description=content.description,
            author=content.author,
            publish_date=content.publish_date,
            word_count=content.word_count,
            language=content.language,
            metadata=content.metadata
        )

# FastAPI 端點
async def fetch_url_content(url: str) -> Dict[str, Any]:
    """獲取 URL 內容的 API 端點"""
    try:
        async with URLProcessor() as processor:
            content = await processor.fetch_and_process(url)
            
            return {
                "success": True,
                "title": content.title,
                "text": content.text,
                "description": content.description,
                "author": content.author,
                "publishDate": content.publish_date,
                "wordCount": content.word_count,
                "language": content.language,
                "metadata": content.metadata
            }
            
    except Exception as e:
        logger.error(f"URL 內容獲取失敗: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# 測試函數
async def test_url_processor():
    """測試 URL 處理器"""
    test_urls = [
        "https://www.example.com",
        "https://github.com",
        "https://docs.python.org"
    ]
    
    async with URLProcessor() as processor:
        for url in test_urls:
            try:
                print(f"\n測試 URL: {url}")
                content = await processor.fetch_and_process(url)
                print(f"標題: {content.title}")
                print(f"字數: {content.word_count}")
                print(f"語言: {content.language}")
                print(f"內容預覽: {content.text[:200]}...")
                
            except Exception as e:
                print(f"測試失敗: {e}")

if __name__ == "__main__":
    asyncio.run(test_url_processor())