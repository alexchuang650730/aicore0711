"""
PowerAutomation 4.0 Semantic Analyzer
语义分析器，用于智能路由的语义理解和意图识别
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """意图类型枚举"""
    ARCHITECT = "architect"
    DEVELOP = "develop"
    TEST = "test"
    DEPLOY = "deploy"
    MONITOR = "monitor"
    SECURITY = "security"
    UTILITY = "utility"
    UNKNOWN = "unknown"


@dataclass
class SemanticResult:
    """语义分析结果"""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    keywords: List[str]
    context: Dict[str, Any]


class SemanticAnalyzer:
    """语义分析器"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_extractors = self._load_entity_extractors()
        
    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """加载意图识别模式"""
        return {
            IntentType.ARCHITECT: [
                r"architect|architecture|design|structure|blueprint",
                r"create.*project|new.*project|init.*project",
                r"microservice|monolith|pattern|framework"
            ],
            IntentType.DEVELOP: [
                r"develop|code|implement|build|create",
                r"web.*app|mobile.*app|api|service",
                r"react|vue|angular|flask|django|fastapi"
            ],
            IntentType.TEST: [
                r"test|testing|unittest|integration.*test",
                r"pytest|jest|mocha|selenium",
                r"coverage|quality|validation"
            ],
            IntentType.DEPLOY: [
                r"deploy|deployment|release|publish",
                r"docker|kubernetes|aws|azure|gcp",
                r"ci/cd|pipeline|automation"
            ],
            IntentType.MONITOR: [
                r"monitor|monitoring|observe|track",
                r"metrics|logs|alerts|dashboard",
                r"prometheus|grafana|elk|datadog"
            ],
            IntentType.SECURITY: [
                r"security|secure|vulnerability|scan",
                r"auth|authentication|authorization",
                r"ssl|tls|encryption|firewall"
            ],
            IntentType.UTILITY: [
                r"help|utility|tool|command",
                r"list|show|info|status",
                r"config|setting|preference"
            ]
        }
    
    def _load_entity_extractors(self) -> Dict[str, str]:
        """加载实体提取器"""
        return {
            "project_path": r"(?:path|dir|directory)[:=]\s*([^\s]+)",
            "project_name": r"(?:name|project)[:=]\s*([^\s]+)",
            "technology": r"(?:tech|technology|framework)[:=]\s*([^\s]+)",
            "environment": r"(?:env|environment)[:=]\s*([^\s]+)",
            "port": r"(?:port)[:=]\s*(\d+)",
            "host": r"(?:host|hostname)[:=]\s*([^\s]+)"
        }
    
    def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> SemanticResult:
        """分析文本语义"""
        text_lower = text.lower()
        
        # 意图识别
        intent, confidence = self._identify_intent(text_lower)
        
        # 实体提取
        entities = self._extract_entities(text)
        
        # 关键词提取
        keywords = self._extract_keywords(text_lower)
        
        # 上下文处理
        processed_context = self._process_context(context or {})
        
        return SemanticResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            keywords=keywords,
            context=processed_context
        )
    
    def _identify_intent(self, text: str) -> Tuple[IntentType, float]:
        """识别意图"""
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    score += 1.0 / len(patterns)
            
            if matches > 0:
                intent_scores[intent_type] = score
        
        if not intent_scores:
            return IntentType.UNKNOWN, 0.0
        
        # 找到最高分的意图
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], min(best_intent[1], 1.0)
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        for entity_name, pattern in self.entity_extractors.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_name] = matches[0] if len(matches) == 1 else matches
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取，去除停用词
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # 提取单词
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # 过滤停用词和短词
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # 去重并保持顺序
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:10]  # 最多返回10个关键词
    
    def _process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理上下文信息"""
        processed = context.copy()
        
        # 添加时间戳
        import time
        processed['timestamp'] = time.time()
        
        # 添加会话ID（如果没有）
        if 'session_id' not in processed:
            import uuid
            processed['session_id'] = str(uuid.uuid4())
        
        return processed
    
    def get_capability_requirements(self, semantic_result: SemanticResult) -> List[str]:
        """根据语义分析结果获取所需能力"""
        capability_map = {
            IntentType.ARCHITECT: ["design", "planning", "architecture"],
            IntentType.DEVELOP: ["coding", "implementation", "debugging"],
            IntentType.TEST: ["testing", "validation", "quality_assurance"],
            IntentType.DEPLOY: ["deployment", "devops", "infrastructure"],
            IntentType.MONITOR: ["monitoring", "observability", "analytics"],
            IntentType.SECURITY: ["security", "compliance", "vulnerability_assessment"],
            IntentType.UTILITY: ["utility", "helper", "information"]
        }
        
        return capability_map.get(semantic_result.intent, ["general"])
    
    def calculate_routing_score(self, semantic_result: SemanticResult, agent_capabilities: List[str]) -> float:
        """计算路由评分"""
        required_capabilities = self.get_capability_requirements(semantic_result)
        
        # 计算能力匹配度
        capability_match = len(set(required_capabilities) & set(agent_capabilities)) / len(required_capabilities)
        
        # 结合置信度
        routing_score = semantic_result.confidence * 0.7 + capability_match * 0.3
        
        return min(routing_score, 1.0)


# 全局语义分析器实例
semantic_analyzer = SemanticAnalyzer()


def analyze_semantic(text: str, context: Optional[Dict[str, Any]] = None) -> SemanticResult:
    """分析文本语义的便捷函数"""
    return semantic_analyzer.analyze(text, context)


def get_intent_from_text(text: str) -> IntentType:
    """从文本中获取意图的便捷函数"""
    result = semantic_analyzer.analyze(text)
    return result.intent

