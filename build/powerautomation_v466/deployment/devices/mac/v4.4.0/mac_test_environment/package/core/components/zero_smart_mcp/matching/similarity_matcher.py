#!/usr/bin/env python3
"""
相似性匹配器

高级工具匹配算法，基于多种相似性计算方法为任务需求找到最匹配的工具。
支持语义相似性、功能相似性、结构相似性等多维度匹配。

主要功能：
- 多维度相似性计算
- 语义嵌入匹配
- 功能特征匹配
- 结构相似性分析
- 混合匹配策略
- 匹配结果解释

作者: PowerAutomation Team
版本: 4.1.0
日期: 2025-01-07
"""

import asyncio
import json
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import re
from pathlib import Path
import pickle
from collections import defaultdict
import math

from ..models.tool_models import MCPTool, TaskRequirement, ToolCapability, ToolCategory

logger = logging.getLogger(__name__)

class SimilarityType(Enum):
    """相似性类型"""
    SEMANTIC = "semantic"  # 语义相似性
    FUNCTIONAL = "functional"  # 功能相似性
    STRUCTURAL = "structural"  # 结构相似性
    CONTEXTUAL = "contextual"  # 上下文相似性
    BEHAVIORAL = "behavioral"  # 行为相似性
    HYBRID = "hybrid"  # 混合相似性

class MatchingStrategy(Enum):
    """匹配策略"""
    EXACT_MATCH = "exact_match"  # 精确匹配
    FUZZY_MATCH = "fuzzy_match"  # 模糊匹配
    SEMANTIC_MATCH = "semantic_match"  # 语义匹配
    FEATURE_MATCH = "feature_match"  # 特征匹配
    ENSEMBLE_MATCH = "ensemble_match"  # 集成匹配

@dataclass
class SimilarityScore:
    """相似性评分"""
    tool_id: str
    task_id: str
    similarity_type: SimilarityType
    score: float
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
    computed_at: datetime = field(default_factory=datetime.now)

@dataclass
class MatchingResult:
    """匹配结果"""
    tool_id: str
    task_id: str
    overall_similarity: float
    similarity_breakdown: Dict[SimilarityType, float] = field(default_factory=dict)
    confidence: float = 0.0
    rank: int = 0
    explanation: str = ""
    matching_features: List[str] = field(default_factory=list)
    missing_features: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureVector:
    """特征向量"""
    tool_id: str
    features: Dict[str, float] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

class SimilarityMatcher:
    """相似性匹配器"""
    
    def __init__(self, config_path: str = "./similarity_matcher_config.json"):
        """初始化相似性匹配器"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 匹配参数
        self.similarity_threshold = self.config.get("similarity_threshold", 0.6)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_results = self.config.get("max_results", 20)
        
        # 权重配置
        self.similarity_weights = self.config.get("similarity_weights", {
            "semantic": 0.3,
            "functional": 0.25,
            "structural": 0.2,
            "contextual": 0.15,
            "behavioral": 0.1
        })
        
        # 特征提取
        self.feature_extractors = {
            "capabilities": self._extract_capability_features,
            "description": self._extract_description_features,
            "category": self._extract_category_features,
            "dependencies": self._extract_dependency_features,
            "metadata": self._extract_metadata_features
        }
        
        # 缓存
        self.feature_cache: Dict[str, FeatureVector] = {}
        self.similarity_cache: Dict[str, List[SimilarityScore]] = {}
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        # 存储
        self.data_dir = Path(self.config.get("data_dir", "./similarity_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载持久化数据
        self._load_persistent_data()
        
        logger.info("相似性匹配器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "similarity_threshold": 0.6,
            "confidence_threshold": 0.7,
            "max_results": 20,
            "similarity_weights": {
                "semantic": 0.3,
                "functional": 0.25,
                "structural": 0.2,
                "contextual": 0.15,
                "behavioral": 0.1
            },
            "enable_caching": True,
            "cache_ttl": 3600,
            "data_dir": "./similarity_data",
            "embedding_dimension": 384,
            "feature_normalization": True,
            "enable_fuzzy_matching": True,
            "fuzzy_threshold": 0.8
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _load_persistent_data(self):
        """加载持久化数据"""
        try:
            # 加载特征缓存
            feature_cache_file = self.data_dir / "feature_cache.pkl"
            if feature_cache_file.exists():
                with open(feature_cache_file, 'rb') as f:
                    self.feature_cache = pickle.load(f)
            
            # 加载嵌入缓存
            embedding_cache_file = self.data_dir / "embedding_cache.pkl"
            if embedding_cache_file.exists():
                with open(embedding_cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
            
            logger.info("持久化数据加载完成")
            
        except Exception as e:
            logger.warning(f"加载持久化数据失败: {e}")
    
    def _save_persistent_data(self):
        """保存持久化数据"""
        try:
            # 保存特征缓存
            with open(self.data_dir / "feature_cache.pkl", 'wb') as f:
                pickle.dump(self.feature_cache, f)
            
            # 保存嵌入缓存
            with open(self.data_dir / "embedding_cache.pkl", 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            
            logger.debug("持久化数据保存完成")
            
        except Exception as e:
            logger.error(f"保存持久化数据失败: {e}")
    
    async def compute_similarity(self, task_requirement: TaskRequirement,
                               tools: List[MCPTool],
                               similarity_type: SimilarityType = SimilarityType.HYBRID,
                               strategy: MatchingStrategy = MatchingStrategy.ENSEMBLE_MATCH) -> List[MatchingResult]:
        """计算相似性"""
        try:
            # 提取任务特征
            task_features = await self._extract_task_features(task_requirement)
            
            # 计算工具相似性
            matching_results = []
            
            for tool in tools:
                # 提取工具特征
                tool_features = await self._extract_tool_features(tool)
                
                # 计算相似性评分
                similarity_scores = await self._compute_tool_similarity(
                    task_features, tool_features, tool, task_requirement, similarity_type
                )
                
                # 生成匹配结果
                matching_result = await self._generate_matching_result(
                    tool, task_requirement, similarity_scores, strategy
                )
                
                if matching_result.overall_similarity >= self.similarity_threshold:
                    matching_results.append(matching_result)
            
            # 排序和排名
            matching_results.sort(key=lambda x: x.overall_similarity, reverse=True)
            for i, result in enumerate(matching_results):
                result.rank = i + 1
            
            # 限制结果数量
            matching_results = matching_results[:self.max_results]
            
            logger.info(f"计算相似性完成，找到 {len(matching_results)} 个匹配工具")
            return matching_results
            
        except Exception as e:
            logger.error(f"计算相似性失败: {e}")
            raise
    
    async def _extract_task_features(self, task_requirement: TaskRequirement) -> FeatureVector:
        """提取任务特征"""
        task_id = task_requirement.task_id
        
        # 检查缓存
        if task_id in self.feature_cache:
            return self.feature_cache[task_id]
        
        features = {}
        
        # 描述特征
        if task_requirement.description:
            desc_features = await self._extract_description_features(task_requirement.description)
            features.update(desc_features)
        
        # 能力特征
        if task_requirement.required_capabilities:
            cap_features = await self._extract_capability_features(task_requirement.required_capabilities)
            features.update(cap_features)
        
        # 复杂度特征
        if task_requirement.complexity_level:
            complexity_features = await self._extract_complexity_features(task_requirement.complexity_level)
            features.update(complexity_features)
        
        # 上下文特征
        if hasattr(task_requirement, 'context') and task_requirement.context:
            context_features = await self._extract_context_features(task_requirement.context)
            features.update(context_features)
        
        # 生成嵌入
        text_content = f"{task_requirement.description} {' '.join(task_requirement.required_capabilities or [])}"
        embedding = await self._get_text_embedding(text_content)
        
        # 创建特征向量
        feature_vector = FeatureVector(
            tool_id=task_id,
            features=features,
            embedding=embedding,
            metadata={
                "type": "task",
                "complexity": task_requirement.complexity_level,
                "capabilities_count": len(task_requirement.required_capabilities or [])
            }
        )
        
        # 缓存特征
        self.feature_cache[task_id] = feature_vector
        
        return feature_vector
    
    async def _extract_tool_features(self, tool: MCPTool) -> FeatureVector:
        """提取工具特征"""
        tool_id = tool.tool_id
        
        # 检查缓存
        if tool_id in self.feature_cache:
            return self.feature_cache[tool_id]
        
        features = {}
        
        # 使用特征提取器
        for extractor_name, extractor_func in self.feature_extractors.items():
            try:
                extracted_features = await extractor_func(tool)
                features.update(extracted_features)
            except Exception as e:
                logger.debug(f"特征提取失败 {extractor_name}: {e}")
        
        # 生成嵌入
        text_content = f"{tool.name} {tool.description} {' '.join([cap.name for cap in tool.capabilities])}"
        embedding = await self._get_text_embedding(text_content)
        
        # 创建特征向量
        feature_vector = FeatureVector(
            tool_id=tool_id,
            features=features,
            embedding=embedding,
            metadata={
                "type": "tool",
                "category": tool.category.value,
                "capabilities_count": len(tool.capabilities),
                "status": tool.status.value
            }
        )
        
        # 缓存特征
        self.feature_cache[tool_id] = feature_vector
        
        return feature_vector
    
    async def _extract_capability_features(self, capabilities) -> Dict[str, float]:
        """提取能力特征"""
        features = {}
        
        if isinstance(capabilities, list):
            # 任务需求的能力列表
            for cap in capabilities:
                features[f"capability_{cap}"] = 1.0
                
                # 能力类别特征
                category = self._categorize_capability(cap)
                features[f"capability_category_{category}"] = 1.0
        
        elif hasattr(capabilities, '__iter__'):
            # 工具的能力对象列表
            for cap in capabilities:
                if hasattr(cap, 'name'):
                    features[f"capability_{cap.name}"] = getattr(cap, 'confidence', 1.0)
                    
                    # 能力类别特征
                    category = self._categorize_capability(cap.name)
                    features[f"capability_category_{category}"] = getattr(cap, 'confidence', 1.0)
        
        return features
    
    def _categorize_capability(self, capability_name: str) -> str:
        """能力分类"""
        capability_categories = {
            "file": ["file", "directory", "path", "read", "write"],
            "web": ["web", "http", "url", "scraping", "browser"],
            "data": ["data", "json", "csv", "database", "query"],
            "ai": ["ai", "ml", "model", "prediction", "analysis"],
            "system": ["system", "process", "command", "shell"],
            "network": ["network", "api", "request", "socket"],
            "text": ["text", "string", "parse", "format"],
            "image": ["image", "photo", "picture", "visual"],
            "audio": ["audio", "sound", "music", "voice"],
            "video": ["video", "movie", "stream", "media"]
        }
        
        capability_lower = capability_name.lower()
        
        for category, keywords in capability_categories.items():
            if any(keyword in capability_lower for keyword in keywords):
                return category
        
        return "general"
    
    async def _extract_description_features(self, description) -> Dict[str, float]:
        """提取描述特征"""
        if isinstance(description, str):
            text = description
        elif hasattr(description, 'description'):
            text = description.description
        else:
            text = str(description)
        
        features = {}
        
        # 文本长度特征
        features["description_length"] = min(len(text) / 1000, 1.0)  # 归一化到0-1
        
        # 关键词特征
        keywords = self._extract_keywords(text)
        for keyword in keywords:
            features[f"keyword_{keyword}"] = 1.0
        
        # 技术栈特征
        tech_stack = self._identify_tech_stack(text)
        for tech in tech_stack:
            features[f"tech_{tech}"] = 1.0
        
        # 动作词特征
        actions = self._extract_action_words(text)
        for action in actions:
            features[f"action_{action}"] = 1.0
        
        return features
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简化的关键词提取
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤停用词
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # 返回频率最高的关键词
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def _identify_tech_stack(self, text: str) -> List[str]:
        """识别技术栈"""
        tech_patterns = {
            "python": r"\bpython\b",
            "javascript": r"\b(javascript|js|node)\b",
            "react": r"\breact\b",
            "flask": r"\bflask\b",
            "docker": r"\bdocker\b",
            "api": r"\bapi\b",
            "rest": r"\brest\b",
            "json": r"\bjson\b",
            "sql": r"\bsql\b",
            "mongodb": r"\bmongodb\b",
            "redis": r"\bredis\b",
            "aws": r"\baws\b",
            "azure": r"\bazure\b",
            "gcp": r"\bgcp\b"
        }
        
        identified_tech = []
        text_lower = text.lower()
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, text_lower):
                identified_tech.append(tech)
        
        return identified_tech
    
    def _extract_action_words(self, text: str) -> List[str]:
        """提取动作词"""
        action_patterns = [
            r"\b(create|build|generate|make)\b",
            r"\b(read|parse|extract|analyze)\b",
            r"\b(update|modify|change|edit)\b",
            r"\b(delete|remove|clean)\b",
            r"\b(send|post|get|fetch)\b",
            r"\b(process|handle|manage)\b",
            r"\b(convert|transform|format)\b",
            r"\b(validate|verify|check)\b"
        ]
        
        actions = []
        text_lower = text.lower()
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text_lower)
            actions.extend(matches)
        
        return list(set(actions))
    
    async def _extract_category_features(self, tool: MCPTool) -> Dict[str, float]:
        """提取类别特征"""
        features = {}
        
        # 主类别
        features[f"category_{tool.category.value}"] = 1.0
        
        # 类别层次特征
        category_hierarchy = {
            ToolCategory.DEVELOPMENT: ["development", "coding", "programming"],
            ToolCategory.DATA_PROCESSING: ["data", "processing", "analysis"],
            ToolCategory.WEB_AUTOMATION: ["web", "automation", "browser"],
            ToolCategory.UTILITY: ["utility", "tool", "helper"],
            ToolCategory.AI_ML: ["ai", "ml", "machine_learning", "artificial_intelligence"]
        }
        
        if tool.category in category_hierarchy:
            for subcategory in category_hierarchy[tool.category]:
                features[f"subcategory_{subcategory}"] = 1.0
        
        return features
    
    async def _extract_dependency_features(self, tool: MCPTool) -> Dict[str, float]:
        """提取依赖特征"""
        features = {}
        
        if tool.dependencies:
            # 依赖数量
            features["dependency_count"] = min(len(tool.dependencies) / 10, 1.0)
            
            # 依赖类型
            for dep in tool.dependencies:
                dep_type = self._classify_dependency(dep)
                features[f"dependency_type_{dep_type}"] = 1.0
        else:
            features["dependency_count"] = 0.0
            features["no_dependencies"] = 1.0
        
        return features
    
    def _classify_dependency(self, dependency: str) -> str:
        """分类依赖"""
        dep_lower = dependency.lower()
        
        if any(lang in dep_lower for lang in ["python", "pip", "pypi"]):
            return "python"
        elif any(js in dep_lower for js in ["npm", "node", "javascript"]):
            return "javascript"
        elif any(sys in dep_lower for sys in ["system", "os", "linux", "windows"]):
            return "system"
        elif any(db in dep_lower for db in ["database", "sql", "mongodb", "redis"]):
            return "database"
        else:
            return "other"
    
    async def _extract_metadata_features(self, tool: MCPTool) -> Dict[str, float]:
        """提取元数据特征"""
        features = {}
        
        # 版本特征
        if hasattr(tool, 'version') and tool.version:
            try:
                version_parts = tool.version.split('.')
                major_version = int(version_parts[0])
                features["version_major"] = min(major_version / 10, 1.0)
                features["is_stable"] = 1.0 if major_version >= 1 else 0.0
            except:
                features["version_unknown"] = 1.0
        
        # 文档特征
        features["has_documentation"] = 1.0 if tool.documentation_url else 0.0
        features["has_examples"] = 1.0 if tool.examples else 0.0
        
        # 仓库特征
        features["has_repository"] = 1.0 if tool.repository_url else 0.0
        
        # 状态特征
        features[f"status_{tool.status.value}"] = 1.0
        
        return features
    
    async def _extract_complexity_features(self, complexity_level: str) -> Dict[str, float]:
        """提取复杂度特征"""
        features = {}
        
        complexity_mapping = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "very_high": 1.0
        }
        
        features["complexity_level"] = complexity_mapping.get(complexity_level, 0.5)
        features[f"complexity_{complexity_level}"] = 1.0
        
        return features
    
    async def _extract_context_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """提取上下文特征"""
        features = {}
        
        # 环境特征
        if "environment" in context:
            env = context["environment"]
            if isinstance(env, str):
                features[f"environment_{env}"] = 1.0
        
        # 平台特征
        if "platform" in context:
            platform = context["platform"]
            if isinstance(platform, str):
                features[f"platform_{platform}"] = 1.0
        
        # 用户类型特征
        if "user_type" in context:
            user_type = context["user_type"]
            if isinstance(user_type, str):
                features[f"user_type_{user_type}"] = 1.0
        
        return features
    
    async def _get_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """获取文本嵌入"""
        # 简化实现：使用缓存的随机嵌入
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if text_hash not in self.embedding_cache:
            # 在实际应用中，这里应该调用真实的嵌入模型
            np.random.seed(int(text_hash[:8], 16))
            embedding_dim = self.config.get("embedding_dimension", 384)
            embedding = np.random.normal(0, 1, embedding_dim)
            embedding = embedding / np.linalg.norm(embedding)  # 归一化
            self.embedding_cache[text_hash] = embedding
        
        return self.embedding_cache[text_hash]
    
    async def _compute_tool_similarity(self, task_features: FeatureVector,
                                     tool_features: FeatureVector,
                                     tool: MCPTool,
                                     task_requirement: TaskRequirement,
                                     similarity_type: SimilarityType) -> Dict[SimilarityType, SimilarityScore]:
        """计算工具相似性"""
        similarity_scores = {}
        
        if similarity_type == SimilarityType.HYBRID:
            # 计算所有类型的相似性
            for sim_type in [SimilarityType.SEMANTIC, SimilarityType.FUNCTIONAL, 
                           SimilarityType.STRUCTURAL, SimilarityType.CONTEXTUAL, 
                           SimilarityType.BEHAVIORAL]:
                score = await self._compute_single_similarity(
                    task_features, tool_features, tool, task_requirement, sim_type
                )
                similarity_scores[sim_type] = score
        else:
            # 计算单一类型的相似性
            score = await self._compute_single_similarity(
                task_features, tool_features, tool, task_requirement, similarity_type
            )
            similarity_scores[similarity_type] = score
        
        return similarity_scores
    
    async def _compute_single_similarity(self, task_features: FeatureVector,
                                       tool_features: FeatureVector,
                                       tool: MCPTool,
                                       task_requirement: TaskRequirement,
                                       similarity_type: SimilarityType) -> SimilarityScore:
        """计算单一相似性"""
        if similarity_type == SimilarityType.SEMANTIC:
            return await self._compute_semantic_similarity(task_features, tool_features, tool, task_requirement)
        elif similarity_type == SimilarityType.FUNCTIONAL:
            return await self._compute_functional_similarity(task_features, tool_features, tool, task_requirement)
        elif similarity_type == SimilarityType.STRUCTURAL:
            return await self._compute_structural_similarity(task_features, tool_features, tool, task_requirement)
        elif similarity_type == SimilarityType.CONTEXTUAL:
            return await self._compute_contextual_similarity(task_features, tool_features, tool, task_requirement)
        elif similarity_type == SimilarityType.BEHAVIORAL:
            return await self._compute_behavioral_similarity(task_features, tool_features, tool, task_requirement)
        else:
            # 默认返回功能相似性
            return await self._compute_functional_similarity(task_features, tool_features, tool, task_requirement)
    
    async def _compute_semantic_similarity(self, task_features: FeatureVector,
                                         tool_features: FeatureVector,
                                         tool: MCPTool,
                                         task_requirement: TaskRequirement) -> SimilarityScore:
        """计算语义相似性"""
        score = 0.0
        confidence = 0.0
        details = {}
        
        # 嵌入相似性
        if task_features.embedding is not None and tool_features.embedding is not None:
            embedding_similarity = np.dot(task_features.embedding, tool_features.embedding)
            score += embedding_similarity * 0.6
            details["embedding_similarity"] = embedding_similarity
            confidence += 0.6
        
        # 关键词相似性
        task_keywords = {k: v for k, v in task_features.features.items() if k.startswith("keyword_")}
        tool_keywords = {k: v for k, v in tool_features.features.items() if k.startswith("keyword_")}
        
        if task_keywords and tool_keywords:
            keyword_similarity = self._compute_feature_similarity(task_keywords, tool_keywords)
            score += keyword_similarity * 0.4
            details["keyword_similarity"] = keyword_similarity
            confidence += 0.4
        
        # 归一化置信度
        if confidence > 0:
            score = score / confidence
            confidence = min(confidence, 1.0)
        
        explanation = f"语义相似性基于文本嵌入({details.get('embedding_similarity', 0):.3f})和关键词匹配({details.get('keyword_similarity', 0):.3f})"
        
        return SimilarityScore(
            tool_id=tool.tool_id,
            task_id=task_requirement.task_id,
            similarity_type=SimilarityType.SEMANTIC,
            score=score,
            confidence=confidence,
            details=details,
            explanation=explanation
        )
    
    async def _compute_functional_similarity(self, task_features: FeatureVector,
                                           tool_features: FeatureVector,
                                           tool: MCPTool,
                                           task_requirement: TaskRequirement) -> SimilarityScore:
        """计算功能相似性"""
        score = 0.0
        confidence = 0.0
        details = {}
        
        # 能力匹配
        task_capabilities = {k: v for k, v in task_features.features.items() if k.startswith("capability_")}
        tool_capabilities = {k: v for k, v in tool_features.features.items() if k.startswith("capability_")}
        
        if task_capabilities and tool_capabilities:
            capability_similarity = self._compute_feature_similarity(task_capabilities, tool_capabilities)
            score += capability_similarity * 0.7
            details["capability_similarity"] = capability_similarity
            confidence += 0.7
        
        # 动作匹配
        task_actions = {k: v for k, v in task_features.features.items() if k.startswith("action_")}
        tool_actions = {k: v for k, v in tool_features.features.items() if k.startswith("action_")}
        
        if task_actions and tool_actions:
            action_similarity = self._compute_feature_similarity(task_actions, tool_actions)
            score += action_similarity * 0.3
            details["action_similarity"] = action_similarity
            confidence += 0.3
        
        # 归一化
        if confidence > 0:
            score = score / confidence
            confidence = min(confidence, 1.0)
        
        explanation = f"功能相似性基于能力匹配({details.get('capability_similarity', 0):.3f})和动作匹配({details.get('action_similarity', 0):.3f})"
        
        return SimilarityScore(
            tool_id=tool.tool_id,
            task_id=task_requirement.task_id,
            similarity_type=SimilarityType.FUNCTIONAL,
            score=score,
            confidence=confidence,
            details=details,
            explanation=explanation
        )
    
    async def _compute_structural_similarity(self, task_features: FeatureVector,
                                           tool_features: FeatureVector,
                                           tool: MCPTool,
                                           task_requirement: TaskRequirement) -> SimilarityScore:
        """计算结构相似性"""
        score = 0.0
        confidence = 0.0
        details = {}
        
        # 复杂度匹配
        task_complexity = task_features.features.get("complexity_level", 0.5)
        tool_complexity = self._estimate_tool_complexity(tool)
        
        complexity_diff = abs(task_complexity - tool_complexity)
        complexity_similarity = 1.0 - complexity_diff
        score += complexity_similarity * 0.4
        details["complexity_similarity"] = complexity_similarity
        confidence += 0.4
        
        # 依赖匹配
        task_deps = task_features.features.get("dependency_count", 0)
        tool_deps = tool_features.features.get("dependency_count", 0)
        
        if task_deps > 0 or tool_deps > 0:
            dep_diff = abs(task_deps - tool_deps)
            dep_similarity = 1.0 / (1.0 + dep_diff)
            score += dep_similarity * 0.3
            details["dependency_similarity"] = dep_similarity
            confidence += 0.3
        
        # 技术栈匹配
        task_tech = {k: v for k, v in task_features.features.items() if k.startswith("tech_")}
        tool_tech = {k: v for k, v in tool_features.features.items() if k.startswith("tech_")}
        
        if task_tech and tool_tech:
            tech_similarity = self._compute_feature_similarity(task_tech, tool_tech)
            score += tech_similarity * 0.3
            details["tech_similarity"] = tech_similarity
            confidence += 0.3
        
        # 归一化
        if confidence > 0:
            score = score / confidence
            confidence = min(confidence, 1.0)
        
        explanation = f"结构相似性基于复杂度({details.get('complexity_similarity', 0):.3f})、依赖({details.get('dependency_similarity', 0):.3f})和技术栈匹配({details.get('tech_similarity', 0):.3f})"
        
        return SimilarityScore(
            tool_id=tool.tool_id,
            task_id=task_requirement.task_id,
            similarity_type=SimilarityType.STRUCTURAL,
            score=score,
            confidence=confidence,
            details=details,
            explanation=explanation
        )
    
    async def _compute_contextual_similarity(self, task_features: FeatureVector,
                                           tool_features: FeatureVector,
                                           tool: MCPTool,
                                           task_requirement: TaskRequirement) -> SimilarityScore:
        """计算上下文相似性"""
        score = 0.5  # 默认中等相似性
        confidence = 0.3
        details = {}
        
        # 环境匹配
        task_env = {k: v for k, v in task_features.features.items() if k.startswith("environment_")}
        tool_env = {k: v for k, v in tool_features.features.items() if k.startswith("platform_")}
        
        if task_env and tool_env:
            env_similarity = self._compute_feature_similarity(task_env, tool_env)
            score = env_similarity
            details["environment_similarity"] = env_similarity
            confidence = 0.8
        
        explanation = f"上下文相似性基于环境匹配({details.get('environment_similarity', 0.5):.3f})"
        
        return SimilarityScore(
            tool_id=tool.tool_id,
            task_id=task_requirement.task_id,
            similarity_type=SimilarityType.CONTEXTUAL,
            score=score,
            confidence=confidence,
            details=details,
            explanation=explanation
        )
    
    async def _compute_behavioral_similarity(self, task_features: FeatureVector,
                                           tool_features: FeatureVector,
                                           tool: MCPTool,
                                           task_requirement: TaskRequirement) -> SimilarityScore:
        """计算行为相似性"""
        score = 0.5  # 默认中等相似性
        confidence = 0.2
        details = {}
        
        # 简化的行为相似性计算
        # 在实际应用中，这里可以基于工具的使用模式、性能特征等
        
        explanation = "行为相似性基于工具使用模式和性能特征"
        
        return SimilarityScore(
            tool_id=tool.tool_id,
            task_id=task_requirement.task_id,
            similarity_type=SimilarityType.BEHAVIORAL,
            score=score,
            confidence=confidence,
            details=details,
            explanation=explanation
        )
    
    def _compute_feature_similarity(self, features1: Dict[str, float], 
                                  features2: Dict[str, float]) -> float:
        """计算特征相似性"""
        if not features1 or not features2:
            return 0.0
        
        # 获取所有特征键
        all_keys = set(features1.keys()) | set(features2.keys())
        
        if not all_keys:
            return 0.0
        
        # 计算余弦相似性
        dot_product = 0.0
        norm1 = 0.0
        norm2 = 0.0
        
        for key in all_keys:
            val1 = features1.get(key, 0.0)
            val2 = features2.get(key, 0.0)
            
            dot_product += val1 * val2
            norm1 += val1 * val1
            norm2 += val2 * val2
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        
        similarity = dot_product / (math.sqrt(norm1) * math.sqrt(norm2))
        return max(0.0, similarity)
    
    def _estimate_tool_complexity(self, tool: MCPTool) -> float:
        """估算工具复杂度"""
        complexity = 0.3  # 基础复杂度
        
        # 基于能力数量
        complexity += min(len(tool.capabilities) * 0.1, 0.4)
        
        # 基于依赖数量
        if tool.dependencies:
            complexity += min(len(tool.dependencies) * 0.05, 0.2)
        
        # 基于类别
        category_complexity = {
            ToolCategory.UTILITY: 0.2,
            ToolCategory.DEVELOPMENT: 0.6,
            ToolCategory.DATA_PROCESSING: 0.7,
            ToolCategory.WEB_AUTOMATION: 0.8,
            ToolCategory.AI_ML: 0.9
        }
        
        complexity += category_complexity.get(tool.category, 0.5) * 0.1
        
        return min(complexity, 1.0)
    
    async def _generate_matching_result(self, tool: MCPTool,
                                      task_requirement: TaskRequirement,
                                      similarity_scores: Dict[SimilarityType, SimilarityScore],
                                      strategy: MatchingStrategy) -> MatchingResult:
        """生成匹配结果"""
        # 计算总体相似性
        overall_similarity = 0.0
        total_weight = 0.0
        similarity_breakdown = {}
        
        for sim_type, score in similarity_scores.items():
            weight = self.similarity_weights.get(sim_type.value, 0.2)
            overall_similarity += score.score * weight * score.confidence
            total_weight += weight * score.confidence
            similarity_breakdown[sim_type] = score.score
        
        if total_weight > 0:
            overall_similarity = overall_similarity / total_weight
        
        # 计算置信度
        confidence = sum(score.confidence for score in similarity_scores.values()) / len(similarity_scores)
        
        # 生成解释
        explanation = self._generate_matching_explanation(tool, task_requirement, similarity_scores)
        
        # 识别匹配和缺失的特征
        matching_features, missing_features = self._identify_feature_matches(
            tool, task_requirement, similarity_scores
        )
        
        return MatchingResult(
            tool_id=tool.tool_id,
            task_id=task_requirement.task_id,
            overall_similarity=overall_similarity,
            similarity_breakdown=similarity_breakdown,
            confidence=confidence,
            explanation=explanation,
            matching_features=matching_features,
            missing_features=missing_features,
            metadata={
                "strategy": strategy.value,
                "tool_name": tool.name,
                "tool_category": tool.category.value,
                "computation_time": datetime.now().isoformat()
            }
        )
    
    def _generate_matching_explanation(self, tool: MCPTool,
                                     task_requirement: TaskRequirement,
                                     similarity_scores: Dict[SimilarityType, SimilarityScore]) -> str:
        """生成匹配解释"""
        explanations = []
        
        # 获取最高的相似性类型
        best_similarity = max(similarity_scores.items(), key=lambda x: x[1].score)
        best_type, best_score = best_similarity
        
        explanations.append(f"最佳匹配维度：{best_type.value}（{best_score.score:.3f}）")
        
        # 添加具体的匹配原因
        if best_score.explanation:
            explanations.append(best_score.explanation)
        
        # 添加工具特色
        if tool.capabilities:
            top_capabilities = [cap.name for cap in tool.capabilities[:3]]
            explanations.append(f"主要能力：{', '.join(top_capabilities)}")
        
        return "；".join(explanations)
    
    def _identify_feature_matches(self, tool: MCPTool,
                                task_requirement: TaskRequirement,
                                similarity_scores: Dict[SimilarityType, SimilarityScore]) -> Tuple[List[str], List[str]]:
        """识别特征匹配"""
        matching_features = []
        missing_features = []
        
        # 基于能力匹配
        if task_requirement.required_capabilities:
            tool_capability_names = {cap.name for cap in tool.capabilities}
            
            for req_cap in task_requirement.required_capabilities:
                if req_cap in tool_capability_names:
                    matching_features.append(f"能力：{req_cap}")
                else:
                    missing_features.append(f"能力：{req_cap}")
        
        # 基于类别匹配
        if tool.category:
            matching_features.append(f"类别：{tool.category.value}")
        
        return matching_features, missing_features
    
    async def find_similar_tools(self, reference_tool: MCPTool,
                               candidate_tools: List[MCPTool],
                               similarity_threshold: float = None) -> List[MatchingResult]:
        """查找相似工具"""
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        # 创建虚拟任务需求
        task_requirement = TaskRequirement(
            task_id=f"similarity_search_{reference_tool.tool_id}",
            description=reference_tool.description,
            required_capabilities=[cap.name for cap in reference_tool.capabilities]
        )
        
        # 计算相似性
        matching_results = await self.compute_similarity(
            task_requirement=task_requirement,
            tools=candidate_tools,
            similarity_type=SimilarityType.HYBRID
        )
        
        # 过滤结果
        similar_tools = [
            result for result in matching_results
            if result.overall_similarity >= similarity_threshold and result.tool_id != reference_tool.tool_id
        ]
        
        return similar_tools
    
    async def get_similarity_analytics(self) -> Dict[str, Any]:
        """获取相似性分析"""
        return {
            "feature_cache_size": len(self.feature_cache),
            "embedding_cache_size": len(self.embedding_cache),
            "similarity_cache_size": len(self.similarity_cache),
            "similarity_weights": self.similarity_weights,
            "similarity_threshold": self.similarity_threshold,
            "confidence_threshold": self.confidence_threshold,
            "feature_extractors": list(self.feature_extractors.keys())
        }

# 工厂函数
def get_similarity_matcher(config_path: str = "./similarity_matcher_config.json") -> SimilarityMatcher:
    """获取相似性匹配器实例"""
    return SimilarityMatcher(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_similarity_matcher():
        """测试相似性匹配器"""
        matcher = get_similarity_matcher()
        
        # 创建测试工具
        test_tools = [
            MCPTool(
                tool_id="file_manager",
                name="File Manager",
                description="Manage files and directories with advanced operations",
                capabilities=[
                    ToolCapability(name="file_operations", confidence=0.9),
                    ToolCapability(name="directory_management", confidence=0.8)
                ],
                category=ToolCategory.UTILITY
            ),
            MCPTool(
                tool_id="web_scraper",
                name="Web Scraper",
                description="Extract data from websites using intelligent parsing",
                capabilities=[
                    ToolCapability(name="web_scraping", confidence=0.95),
                    ToolCapability(name="data_extraction", confidence=0.8)
                ],
                category=ToolCategory.WEB_AUTOMATION
            ),
            MCPTool(
                tool_id="data_processor",
                name="Data Processor",
                description="Process and analyze large datasets efficiently",
                capabilities=[
                    ToolCapability(name="data_processing", confidence=0.9),
                    ToolCapability(name="data_analysis", confidence=0.85)
                ],
                category=ToolCategory.DATA_PROCESSING
            )
        ]
        
        # 创建任务需求
        task_requirement = TaskRequirement(
            task_id="test_task",
            description="Extract data from websites and save to files for analysis",
            required_capabilities=["web_scraping", "file_operations", "data_processing"],
            complexity_level="medium"
        )
        
        # 计算相似性
        print("🔍 计算工具相似性...")
        matching_results = await matcher.compute_similarity(
            task_requirement=task_requirement,
            tools=test_tools,
            similarity_type=SimilarityType.HYBRID
        )
        
        print(f"📊 匹配结果 ({len(matching_results)} 个):")
        for result in matching_results:
            tool = next(t for t in test_tools if t.tool_id == result.tool_id)
            print(f"  {result.rank}. {tool.name}")
            print(f"     总体相似性: {result.overall_similarity:.3f}")
            print(f"     置信度: {result.confidence:.3f}")
            print(f"     解释: {result.explanation}")
            print(f"     匹配特征: {', '.join(result.matching_features)}")
            if result.missing_features:
                print(f"     缺失特征: {', '.join(result.missing_features)}")
            print()
        
        # 查找相似工具
        if test_tools:
            print("🔗 查找相似工具...")
            similar_tools = await matcher.find_similar_tools(
                reference_tool=test_tools[0],
                candidate_tools=test_tools[1:],
                similarity_threshold=0.3
            )
            
            print(f"相似工具 ({len(similar_tools)} 个):")
            for result in similar_tools:
                tool = next(t for t in test_tools if t.tool_id == result.tool_id)
                print(f"  - {tool.name} (相似性: {result.overall_similarity:.3f})")
        
        # 获取分析
        analytics = await matcher.get_similarity_analytics()
        print(f"📈 相似性分析:")
        print(f"  特征缓存: {analytics['feature_cache_size']}")
        print(f"  嵌入缓存: {analytics['embedding_cache_size']}")
        print(f"  相似性阈值: {analytics['similarity_threshold']}")
    
    # 运行测试
    asyncio.run(test_similarity_matcher())

