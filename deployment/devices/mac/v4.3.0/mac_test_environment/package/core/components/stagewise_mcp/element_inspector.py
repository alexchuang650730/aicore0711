"""
PowerAutomation 4.0 元素检查器

智能分析Web元素，生成最优选择器和元素信息。
"""

import asyncio
import json
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging


class SelectorType(Enum):
    """选择器类型"""
    ID = "id"
    CLASS = "class"
    TAG = "tag"
    XPATH = "xpath"
    CSS = "css"
    TEXT = "text"
    ATTRIBUTE = "attribute"
    COMBINED = "combined"


class ElementType(Enum):
    """元素类型"""
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    TEXT = "text"
    IMAGE = "image"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    DIV = "div"
    SPAN = "span"
    TABLE = "table"
    FORM = "form"
    UNKNOWN = "unknown"


@dataclass
class SelectorCandidate:
    """选择器候选项"""
    selector: str
    type: SelectorType
    specificity: int
    stability: float
    performance: float
    readability: float
    overall_score: float


@dataclass
class ElementAnalysis:
    """元素分析结果"""
    element_type: ElementType
    best_selector: str
    selector_candidates: List[SelectorCandidate]
    attributes: Dict[str, str]
    text_content: str
    position: Dict[str, int]
    size: Dict[str, int]
    is_visible: bool
    is_interactive: bool
    parent_context: Dict[str, Any]
    children_context: List[Dict[str, Any]]
    confidence: float


class ElementInspector:
    """元素检查器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.max_selector_candidates = self.config.get("max_selector_candidates", 10)
        self.min_confidence_threshold = self.config.get("min_confidence_threshold", 0.7)
        self.prefer_stable_selectors = self.config.get("prefer_stable_selectors", True)
        
        # 选择器权重配置
        self.selector_weights = {
            "specificity": 0.3,
            "stability": 0.4,
            "performance": 0.2,
            "readability": 0.1
        }
        
        # 元素分析缓存
        self.analysis_cache: Dict[str, ElementAnalysis] = {}
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5分钟
        
        # 统计信息
        self.stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "avg_analysis_time": 0.0,
            "selector_accuracy": 0.0
        }
        
        # 运行状态
        self.is_running = False
    
    async def start(self):
        """启动元素检查器"""
        if self.is_running:
            return
        
        self.logger.info("启动元素检查器...")
        
        # 初始化选择器模式
        self._initialize_selector_patterns()
        
        self.is_running = True
        self.logger.info("元素检查器启动完成")
    
    async def stop(self):
        """停止元素检查器"""
        if not self.is_running:
            return
        
        self.logger.info("停止元素检查器...")
        
        # 清理缓存
        self.analysis_cache.clear()
        
        self.is_running = False
        self.logger.info("元素检查器已停止")
    
    async def analyze_element(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析元素并生成最优选择器"""
        if not self.is_running:
            raise RuntimeError("元素检查器未启动")
        
        start_time = datetime.now()
        
        # 生成元素指纹用于缓存
        element_fingerprint = self._generate_element_fingerprint(element_data)
        
        # 检查缓存
        if element_fingerprint in self.analysis_cache:
            self.stats["cache_hits"] += 1
            cached_analysis = self.analysis_cache[element_fingerprint]
            
            return {
                "selector": cached_analysis.best_selector,
                "tag_name": element_data.get("tagName", "").lower(),
                "attributes": cached_analysis.attributes,
                "text_content": cached_analysis.text_content,
                "position": cached_analysis.position,
                "element_type": cached_analysis.element_type.value,
                "confidence": cached_analysis.confidence,
                "from_cache": True
            }
        
        try:
            # 执行元素分析
            analysis = await self._perform_element_analysis(element_data)
            
            # 缓存结果
            self.analysis_cache[element_fingerprint] = analysis
            
            # 更新统计
            analysis_time = (datetime.now() - start_time).total_seconds()
            self.stats["total_analyses"] += 1
            
            # 更新平均分析时间
            total = self.stats["total_analyses"]
            current_avg = self.stats["avg_analysis_time"]
            self.stats["avg_analysis_time"] = (
                (current_avg * (total - 1) + analysis_time) / total
            )
            
            self.logger.info(f"元素分析完成: {analysis.best_selector}, 置信度: {analysis.confidence:.2f}")
            
            return {
                "selector": analysis.best_selector,
                "tag_name": element_data.get("tagName", "").lower(),
                "attributes": analysis.attributes,
                "text_content": analysis.text_content,
                "position": analysis.position,
                "size": analysis.size,
                "element_type": analysis.element_type.value,
                "is_visible": analysis.is_visible,
                "is_interactive": analysis.is_interactive,
                "confidence": analysis.confidence,
                "selector_candidates": [
                    {
                        "selector": candidate.selector,
                        "type": candidate.type.value,
                        "score": candidate.overall_score
                    }
                    for candidate in analysis.selector_candidates[:5]  # 返回前5个候选项
                ],
                "from_cache": False
            }
            
        except Exception as e:
            self.logger.error(f"元素分析失败: {e}")
            
            # 返回基础分析结果
            return {
                "selector": self._generate_fallback_selector(element_data),
                "tag_name": element_data.get("tagName", "").lower(),
                "attributes": element_data.get("attributes", {}),
                "text_content": element_data.get("textContent", ""),
                "position": element_data.get("position", {}),
                "element_type": "unknown",
                "confidence": 0.5,
                "error": str(e)
            }
    
    async def _perform_element_analysis(self, element_data: Dict[str, Any]) -> ElementAnalysis:
        """执行详细的元素分析"""
        # 提取基础信息
        tag_name = element_data.get("tagName", "").lower()
        attributes = element_data.get("attributes", {})
        text_content = element_data.get("textContent", "").strip()
        position = element_data.get("position", {})
        size = element_data.get("size", {})
        
        # 确定元素类型
        element_type = self._determine_element_type(tag_name, attributes, text_content)
        
        # 生成选择器候选项
        selector_candidates = await self._generate_selector_candidates(
            tag_name, attributes, text_content, element_data
        )
        
        # 评估选择器候选项
        evaluated_candidates = await self._evaluate_selector_candidates(
            selector_candidates, element_data
        )
        
        # 选择最佳选择器
        best_selector = evaluated_candidates[0].selector if evaluated_candidates else tag_name
        
        # 分析可见性和交互性
        is_visible = self._analyze_visibility(element_data)
        is_interactive = self._analyze_interactivity(element_type, attributes)
        
        # 分析上下文
        parent_context = self._analyze_parent_context(element_data)
        children_context = self._analyze_children_context(element_data)
        
        # 计算整体置信度
        confidence = self._calculate_confidence(
            evaluated_candidates, element_type, is_visible, is_interactive
        )
        
        return ElementAnalysis(
            element_type=element_type,
            best_selector=best_selector,
            selector_candidates=evaluated_candidates,
            attributes=attributes,
            text_content=text_content,
            position=position,
            size=size,
            is_visible=is_visible,
            is_interactive=is_interactive,
            parent_context=parent_context,
            children_context=children_context,
            confidence=confidence
        )
    
    def _determine_element_type(
        self,
        tag_name: str,
        attributes: Dict[str, str],
        text_content: str
    ) -> ElementType:
        """确定元素类型"""
        # 基于标签名判断
        if tag_name == "button":
            return ElementType.BUTTON
        elif tag_name == "a":
            return ElementType.LINK
        elif tag_name == "img":
            return ElementType.IMAGE
        elif tag_name == "select":
            return ElementType.SELECT
        elif tag_name == "textarea":
            return ElementType.TEXTAREA
        elif tag_name == "table":
            return ElementType.TABLE
        elif tag_name == "form":
            return ElementType.FORM
        elif tag_name == "input":
            # 基于input类型细分
            input_type = attributes.get("type", "text").lower()
            if input_type in ["checkbox"]:
                return ElementType.CHECKBOX
            elif input_type in ["radio"]:
                return ElementType.RADIO
            else:
                return ElementType.INPUT
        elif tag_name in ["div", "span"]:
            # 基于内容和属性判断
            if self._looks_like_button(attributes, text_content):
                return ElementType.BUTTON
            elif tag_name == "div":
                return ElementType.DIV
            else:
                return ElementType.SPAN
        
        # 基于角色属性判断
        role = attributes.get("role", "").lower()
        if role == "button":
            return ElementType.BUTTON
        elif role == "link":
            return ElementType.LINK
        elif role == "textbox":
            return ElementType.INPUT
        
        # 基于类名判断
        class_name = attributes.get("class", "").lower()
        if any(btn_class in class_name for btn_class in ["btn", "button", "submit"]):
            return ElementType.BUTTON
        
        # 默认返回未知类型
        return ElementType.UNKNOWN
    
    def _looks_like_button(self, attributes: Dict[str, str], text_content: str) -> bool:
        """判断元素是否看起来像按钮"""
        # 检查点击事件
        if "onclick" in attributes:
            return True
        
        # 检查类名
        class_name = attributes.get("class", "").lower()
        button_classes = ["btn", "button", "submit", "click", "action"]
        if any(btn_class in class_name for btn_class in button_classes):
            return True
        
        # 检查文本内容
        if text_content:
            button_texts = ["click", "submit", "send", "save", "delete", "edit", "add"]
            text_lower = text_content.lower()
            if any(btn_text in text_lower for btn_text in button_texts):
                return True
        
        return False
    
    async def _generate_selector_candidates(
        self,
        tag_name: str,
        attributes: Dict[str, str],
        text_content: str,
        element_data: Dict[str, Any]
    ) -> List[SelectorCandidate]:
        """生成选择器候选项"""
        candidates = []
        
        # ID选择器（最高优先级）
        if "id" in attributes and attributes["id"]:
            candidates.append(SelectorCandidate(
                selector=f"#{attributes['id']}",
                type=SelectorType.ID,
                specificity=100,
                stability=0.9,
                performance=0.95,
                readability=0.9,
                overall_score=0.0  # 稍后计算
            ))
        
        # 类选择器
        if "class" in attributes and attributes["class"]:
            classes = attributes["class"].split()
            for class_name in classes:
                if class_name and not self._is_dynamic_class(class_name):
                    candidates.append(SelectorCandidate(
                        selector=f".{class_name}",
                        type=SelectorType.CLASS,
                        specificity=10,
                        stability=0.7,
                        performance=0.8,
                        readability=0.8,
                        overall_score=0.0
                    ))
            
            # 组合类选择器
            stable_classes = [c for c in classes if not self._is_dynamic_class(c)]
            if len(stable_classes) > 1:
                combined_selector = "." + ".".join(stable_classes[:3])  # 最多3个类
                candidates.append(SelectorCandidate(
                    selector=combined_selector,
                    type=SelectorType.COMBINED,
                    specificity=30,
                    stability=0.8,
                    performance=0.75,
                    readability=0.7,
                    overall_score=0.0
                ))
        
        # 属性选择器
        for attr_name, attr_value in attributes.items():
            if attr_name not in ["id", "class"] and attr_value and not self._is_dynamic_attribute(attr_name, attr_value):
                candidates.append(SelectorCandidate(
                    selector=f"{tag_name}[{attr_name}='{attr_value}']",
                    type=SelectorType.ATTRIBUTE,
                    specificity=20,
                    stability=0.6,
                    performance=0.7,
                    readability=0.6,
                    overall_score=0.0
                ))
        
        # 文本选择器
        if text_content and len(text_content) < 50:  # 避免过长的文本
            # 精确文本匹配
            candidates.append(SelectorCandidate(
                selector=f"{tag_name}:contains('{text_content}')",
                type=SelectorType.TEXT,
                specificity=25,
                stability=0.5,
                performance=0.6,
                readability=0.9,
                overall_score=0.0
            ))
            
            # 部分文本匹配
            if len(text_content) > 10:
                partial_text = text_content[:20] + "..."
                candidates.append(SelectorCandidate(
                    selector=f"{tag_name}:contains('{partial_text}')",
                    type=SelectorType.TEXT,
                    specificity=15,
                    stability=0.4,
                    performance=0.5,
                    readability=0.8,
                    overall_score=0.0
                ))
        
        # XPath选择器
        xpath_candidates = self._generate_xpath_candidates(element_data)
        candidates.extend(xpath_candidates)
        
        # CSS选择器组合
        css_candidates = self._generate_css_combinations(tag_name, attributes)
        candidates.extend(css_candidates)
        
        return candidates
    
    def _generate_xpath_candidates(self, element_data: Dict[str, Any]) -> List[SelectorCandidate]:
        """生成XPath选择器候选项"""
        candidates = []
        
        # 基于位置的XPath
        if "xpath" in element_data:
            xpath = element_data["xpath"]
            candidates.append(SelectorCandidate(
                selector=xpath,
                type=SelectorType.XPATH,
                specificity=50,
                stability=0.3,  # 位置XPath稳定性较低
                performance=0.4,
                readability=0.3,
                overall_score=0.0
            ))
        
        # 基于属性的XPath
        attributes = element_data.get("attributes", {})
        tag_name = element_data.get("tagName", "").lower()
        
        if "id" in attributes:
            xpath = f"//{tag_name}[@id='{attributes['id']}']"
            candidates.append(SelectorCandidate(
                selector=xpath,
                type=SelectorType.XPATH,
                specificity=90,
                stability=0.9,
                performance=0.8,
                readability=0.7,
                overall_score=0.0
            ))
        
        return candidates
    
    def _generate_css_combinations(
        self,
        tag_name: str,
        attributes: Dict[str, str]
    ) -> List[SelectorCandidate]:
        """生成CSS选择器组合"""
        candidates = []
        
        # 标签+属性组合
        for attr_name, attr_value in attributes.items():
            if attr_name not in ["id", "class"] and not self._is_dynamic_attribute(attr_name, attr_value):
                selector = f"{tag_name}[{attr_name}='{attr_value}']"
                candidates.append(SelectorCandidate(
                    selector=selector,
                    type=SelectorType.CSS,
                    specificity=25,
                    stability=0.6,
                    performance=0.7,
                    readability=0.6,
                    overall_score=0.0
                ))
        
        # 标签+类组合
        if "class" in attributes:
            classes = attributes["class"].split()
            stable_classes = [c for c in classes if not self._is_dynamic_class(c)]
            for class_name in stable_classes[:2]:  # 最多2个类
                selector = f"{tag_name}.{class_name}"
                candidates.append(SelectorCandidate(
                    selector=selector,
                    type=SelectorType.CSS,
                    specificity=20,
                    stability=0.7,
                    performance=0.8,
                    readability=0.8,
                    overall_score=0.0
                ))
        
        return candidates
    
    async def _evaluate_selector_candidates(
        self,
        candidates: List[SelectorCandidate],
        element_data: Dict[str, Any]
    ) -> List[SelectorCandidate]:
        """评估选择器候选项"""
        # 计算每个候选项的综合得分
        for candidate in candidates:
            candidate.overall_score = (
                candidate.specificity * self.selector_weights["specificity"] / 100 +
                candidate.stability * self.selector_weights["stability"] +
                candidate.performance * self.selector_weights["performance"] +
                candidate.readability * self.selector_weights["readability"]
            )
        
        # 按得分排序
        candidates.sort(key=lambda x: x.overall_score, reverse=True)
        
        # 返回前N个候选项
        return candidates[:self.max_selector_candidates]
    
    def _is_dynamic_class(self, class_name: str) -> bool:
        """判断类名是否是动态生成的"""
        # 检查常见的动态类名模式
        dynamic_patterns = [
            r"^[a-f0-9]{8,}$",  # 哈希值
            r".*\d{10,}.*",     # 包含时间戳
            r".*-\d{4,}$",      # 以数字结尾
            r"^css-[a-z0-9]+$", # CSS-in-JS生成的类名
        ]
        
        for pattern in dynamic_patterns:
            if re.match(pattern, class_name):
                return True
        
        return False
    
    def _is_dynamic_attribute(self, attr_name: str, attr_value: str) -> bool:
        """判断属性是否是动态的"""
        # 动态属性名
        dynamic_attrs = ["data-reactid", "data-testid"]
        if attr_name in dynamic_attrs:
            return True
        
        # 动态属性值模式
        if re.match(r"^[a-f0-9]{8,}$", attr_value):  # 哈希值
            return True
        
        if re.match(r".*\d{10,}.*", attr_value):  # 时间戳
            return True
        
        return False
    
    def _analyze_visibility(self, element_data: Dict[str, Any]) -> bool:
        """分析元素可见性"""
        # 检查样式属性
        style = element_data.get("style", {})
        if isinstance(style, dict):
            if style.get("display") == "none":
                return False
            if style.get("visibility") == "hidden":
                return False
            if style.get("opacity") == "0":
                return False
        
        # 检查位置和大小
        position = element_data.get("position", {})
        size = element_data.get("size", {})
        
        if size.get("width", 0) <= 0 or size.get("height", 0) <= 0:
            return False
        
        return True
    
    def _analyze_interactivity(self, element_type: ElementType, attributes: Dict[str, str]) -> bool:
        """分析元素交互性"""
        # 交互性元素类型
        interactive_types = [
            ElementType.BUTTON, ElementType.INPUT, ElementType.LINK,
            ElementType.SELECT, ElementType.CHECKBOX, ElementType.RADIO,
            ElementType.TEXTAREA
        ]
        
        if element_type in interactive_types:
            return True
        
        # 检查事件处理器
        event_attrs = ["onclick", "onchange", "onsubmit", "onkeydown", "onkeyup"]
        for event_attr in event_attrs:
            if event_attr in attributes:
                return True
        
        # 检查tabindex
        if "tabindex" in attributes:
            try:
                tabindex = int(attributes["tabindex"])
                return tabindex >= 0
            except ValueError:
                pass
        
        return False
    
    def _analyze_parent_context(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析父元素上下文"""
        parent = element_data.get("parent", {})
        if not parent:
            return {}
        
        return {
            "tag_name": parent.get("tagName", "").lower(),
            "class": parent.get("attributes", {}).get("class", ""),
            "id": parent.get("attributes", {}).get("id", ""),
            "role": parent.get("attributes", {}).get("role", "")
        }
    
    def _analyze_children_context(self, element_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析子元素上下文"""
        children = element_data.get("children", [])
        context = []
        
        for child in children[:5]:  # 最多分析5个子元素
            context.append({
                "tag_name": child.get("tagName", "").lower(),
                "text_content": child.get("textContent", "")[:50],  # 限制长度
                "class": child.get("attributes", {}).get("class", "")
            })
        
        return context
    
    def _calculate_confidence(
        self,
        candidates: List[SelectorCandidate],
        element_type: ElementType,
        is_visible: bool,
        is_interactive: bool
    ) -> float:
        """计算整体置信度"""
        base_confidence = 0.5
        
        # 基于最佳选择器得分
        if candidates:
            best_score = candidates[0].overall_score
            base_confidence += best_score * 0.3
        
        # 基于元素类型确定性
        if element_type != ElementType.UNKNOWN:
            base_confidence += 0.1
        
        # 基于可见性
        if is_visible:
            base_confidence += 0.1
        
        # 基于交互性
        if is_interactive:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _generate_element_fingerprint(self, element_data: Dict[str, Any]) -> str:
        """生成元素指纹用于缓存"""
        # 提取关键信息
        key_info = {
            "tagName": element_data.get("tagName", ""),
            "attributes": element_data.get("attributes", {}),
            "textContent": element_data.get("textContent", "")[:100],  # 限制长度
            "position": element_data.get("position", {})
        }
        
        # 生成哈希
        info_str = json.dumps(key_info, sort_keys=True)
        return hashlib.md5(info_str.encode()).hexdigest()
    
    def _generate_fallback_selector(self, element_data: Dict[str, Any]) -> str:
        """生成备用选择器"""
        tag_name = element_data.get("tagName", "div").lower()
        attributes = element_data.get("attributes", {})
        
        # 尝试使用ID
        if "id" in attributes and attributes["id"]:
            return f"#{attributes['id']}"
        
        # 尝试使用类
        if "class" in attributes and attributes["class"]:
            classes = attributes["class"].split()
            if classes:
                return f".{classes[0]}"
        
        # 使用标签名
        return tag_name
    
    def _initialize_selector_patterns(self):
        """初始化选择器模式"""
        # 这里可以加载预训练的选择器模式
        # 或者从配置文件中读取自定义模式
        pass
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_analyses": self.stats["total_analyses"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(self.stats["total_analyses"], 1)
            ),
            "avg_analysis_time": self.stats["avg_analysis_time"],
            "cached_elements": len(self.analysis_cache)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "component": "element_inspector",
            "status": "healthy" if self.is_running else "unhealthy",
            "cache_size": len(self.analysis_cache),
            "statistics": await self.get_statistics()
        }

