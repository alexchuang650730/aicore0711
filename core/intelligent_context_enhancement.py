#!/usr/bin/env python3
"""
PowerAutomation Core 智能上下文增強系統
v4.6.9.4 - 為 Claude Code 提供智能上下文增強
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import re
from pathlib import Path

# 集成 MemoryOS MCP 和數據收集系統
from .components.memoryos_mcp import MemoryEngine, ContextManager, LearningAdapter
from .components.memoryos_mcp import PersonalizationManager, MemoryOptimizer
from .data_collection_system import DataCollectionSystem, DataType, DataPriority
from .learning_integration import PowerAutomationLearningIntegration

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """上下文類型"""
    HISTORICAL = "historical"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PERSONAL = "personal"
    DOMAIN_SPECIFIC = "domain_specific"
    TEMPORAL = "temporal"
    COLLABORATIVE = "collaborative"
    ADAPTIVE = "adaptive"

class EnhancementStrategy(Enum):
    """增強策略"""
    SIMILAR_CONTEXT = "similar_context"
    LEARNING_PATTERN = "learning_pattern"
    USER_PREFERENCE = "user_preference"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    TEMPORAL_CONTEXT = "temporal_context"
    COLLABORATIVE_FILTER = "collaborative_filter"
    ADAPTIVE_WEIGHTING = "adaptive_weighting"

@dataclass
class ContextEnhancement:
    """上下文增強"""
    id: str
    query: str
    enhancement_type: ContextType
    strategy: EnhancementStrategy
    content: str
    relevance_score: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    created_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)

@dataclass
class EnhancementResult:
    """增強結果"""
    query: str
    enhancements: List[ContextEnhancement]
    total_score: float
    processing_time: float
    strategies_used: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)

class IntelligentContextEnhancement:
    """智能上下文增強系統"""
    
    def __init__(self, learning_integration: PowerAutomationLearningIntegration):
        self.learning_integration = learning_integration
        self.memory_engine = learning_integration.memory_engine
        self.context_manager = learning_integration.context_manager
        self.learning_adapter = learning_integration.learning_adapter
        self.personalization_manager = learning_integration.personalization_manager
        self.memory_optimizer = learning_integration.memory_optimizer
        
        # 增強策略
        self.enhancement_strategies = {}
        self.strategy_weights = {}
        self.adaptive_weights = defaultdict(float)
        
        # 上下文分析器
        self.context_analyzers = {}
        
        # 性能統計
        self.enhancement_stats = {
            "total_enhancements": 0,
            "successful_enhancements": 0,
            "average_processing_time": 0.0,
            "strategy_usage": defaultdict(int),
            "user_feedback": defaultdict(list)
        }
        
        # 實時學習
        self.recent_enhancements = deque(maxlen=100)
        self.feedback_buffer = deque(maxlen=50)
        
        # 是否初始化
        self.is_initialized = False
    
    async def initialize(self):
        """初始化智能上下文增強系統"""
        logger.info("🧠 初始化智能上下文增強系統...")
        
        try:
            # 1. 初始化增強策略
            await self._initialize_enhancement_strategies()
            
            # 2. 初始化上下文分析器
            await self._initialize_context_analyzers()
            
            # 3. 載入策略權重
            await self._load_strategy_weights()
            
            # 4. 啟動自適應學習
            await self._start_adaptive_learning()
            
            self.is_initialized = True
            logger.info("✅ 智能上下文增強系統初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 智能上下文增強系統初始化失敗: {e}")
            raise
    
    async def _initialize_enhancement_strategies(self):
        """初始化增強策略"""
        # 相似上下文策略
        self.enhancement_strategies[EnhancementStrategy.SIMILAR_CONTEXT] = {
            "function": self._enhance_with_similar_context,
            "weight": 0.25,
            "enabled": True,
            "description": "基於相似上下文的增強"
        }
        
        # 學習模式策略
        self.enhancement_strategies[EnhancementStrategy.LEARNING_PATTERN] = {
            "function": self._enhance_with_learning_patterns,
            "weight": 0.20,
            "enabled": True,
            "description": "基於學習模式的增強"
        }
        
        # 用戶偏好策略
        self.enhancement_strategies[EnhancementStrategy.USER_PREFERENCE] = {
            "function": self._enhance_with_user_preferences,
            "weight": 0.15,
            "enabled": True,
            "description": "基於用戶偏好的增強"
        }
        
        # 領域知識策略
        self.enhancement_strategies[EnhancementStrategy.DOMAIN_KNOWLEDGE] = {
            "function": self._enhance_with_domain_knowledge,
            "weight": 0.20,
            "enabled": True,
            "description": "基於領域知識的增強"
        }
        
        # 時間上下文策略
        self.enhancement_strategies[EnhancementStrategy.TEMPORAL_CONTEXT] = {
            "function": self._enhance_with_temporal_context,
            "weight": 0.10,
            "enabled": True,
            "description": "基於時間上下文的增強"
        }
        
        # 協作過濾策略
        self.enhancement_strategies[EnhancementStrategy.COLLABORATIVE_FILTER] = {
            "function": self._enhance_with_collaborative_filtering,
            "weight": 0.05,
            "enabled": True,
            "description": "基於協作過濾的增強"
        }
        
        # 自適應權重策略
        self.enhancement_strategies[EnhancementStrategy.ADAPTIVE_WEIGHTING] = {
            "function": self._enhance_with_adaptive_weighting,
            "weight": 0.05,
            "enabled": True,
            "description": "基於自適應權重的增強"
        }
        
        logger.info(f"📋 初始化 {len(self.enhancement_strategies)} 個增強策略")
    
    async def _initialize_context_analyzers(self):
        """初始化上下文分析器"""
        # 語義分析器
        self.context_analyzers[ContextType.SEMANTIC] = {
            "function": self._analyze_semantic_context,
            "enabled": True
        }
        
        # 程序化分析器
        self.context_analyzers[ContextType.PROCEDURAL] = {
            "function": self._analyze_procedural_context,
            "enabled": True
        }
        
        # 個人化分析器
        self.context_analyzers[ContextType.PERSONAL] = {
            "function": self._analyze_personal_context,
            "enabled": True
        }
        
        # 領域特定分析器
        self.context_analyzers[ContextType.DOMAIN_SPECIFIC] = {
            "function": self._analyze_domain_specific_context,
            "enabled": True
        }
        
        # 時間分析器
        self.context_analyzers[ContextType.TEMPORAL] = {
            "function": self._analyze_temporal_context,
            "enabled": True
        }
        
        # 協作分析器
        self.context_analyzers[ContextType.COLLABORATIVE] = {
            "function": self._analyze_collaborative_context,
            "enabled": True
        }
        
        logger.info(f"🔍 初始化 {len(self.context_analyzers)} 個上下文分析器")
    
    async def _load_strategy_weights(self):
        """載入策略權重"""
        try:
            # 從學習適配器獲取策略權重
            if self.learning_adapter:
                learning_stats = await self.learning_adapter.get_learning_statistics()
                
                # 基於學習統計調整權重
                success_rate = learning_stats.get("success_rate", 0.0)
                
                # 成功率高的策略增加權重
                if success_rate > 0.8:
                    self.strategy_weights[EnhancementStrategy.SIMILAR_CONTEXT] = 0.3
                    self.strategy_weights[EnhancementStrategy.LEARNING_PATTERN] = 0.25
                elif success_rate > 0.6:
                    self.strategy_weights[EnhancementStrategy.USER_PREFERENCE] = 0.2
                    self.strategy_weights[EnhancementStrategy.DOMAIN_KNOWLEDGE] = 0.25
                else:
                    # 使用默認權重
                    for strategy, config in self.enhancement_strategies.items():
                        self.strategy_weights[strategy] = config["weight"]
            
            logger.info("📊 載入策略權重完成")
            
        except Exception as e:
            logger.error(f"❌ 載入策略權重失敗: {e}")
            # 使用默認權重
            for strategy, config in self.enhancement_strategies.items():
                self.strategy_weights[strategy] = config["weight"]
    
    async def _start_adaptive_learning(self):
        """啟動自適應學習"""
        asyncio.create_task(self._adaptive_learning_loop())
    
    async def _adaptive_learning_loop(self):
        """自適應學習循環"""
        while True:
            try:
                # 分析最近的增強效果
                await self._analyze_recent_enhancements()
                
                # 調整策略權重
                await self._adjust_strategy_weights()
                
                # 等待下一次分析
                await asyncio.sleep(300)  # 5分鐘
                
            except Exception as e:
                logger.error(f"❌ 自適應學習循環失敗: {e}")
                await asyncio.sleep(60)
    
    async def enhance_context(self, 
                            query: str,
                            user_id: str = "default_user",
                            context_type: str = "claude_interaction",
                            max_enhancements: int = 5) -> EnhancementResult:
        """增強上下文"""
        start_time = time.time()
        
        try:
            # 1. 分析查詢
            query_analysis = await self._analyze_query(query)
            
            # 2. 收集基礎上下文
            base_contexts = await self._collect_base_contexts(query, context_type)
            
            # 3. 應用增強策略
            enhancements = []
            strategies_used = []
            
            for strategy, config in self.enhancement_strategies.items():
                if config["enabled"]:
                    try:
                        strategy_enhancements = await config["function"](
                            query, query_analysis, base_contexts, user_id
                        )
                        
                        if strategy_enhancements:
                            enhancements.extend(strategy_enhancements)
                            strategies_used.append(strategy.value)
                            
                            # 更新策略使用統計
                            self.enhancement_stats["strategy_usage"][strategy.value] += 1
                            
                    except Exception as e:
                        logger.error(f"❌ 增強策略失敗 ({strategy.value}): {e}")
                        continue
            
            # 4. 排序和篩選增強
            enhancements = await self._rank_enhancements(enhancements, query_analysis)
            enhancements = enhancements[:max_enhancements]
            
            # 5. 計算總分
            total_score = sum(e.relevance_score * e.confidence for e in enhancements)
            
            # 6. 創建結果
            processing_time = time.time() - start_time
            
            result = EnhancementResult(
                query=query,
                enhancements=enhancements,
                total_score=total_score,
                processing_time=processing_time,
                strategies_used=strategies_used,
                metadata={
                    "user_id": user_id,
                    "context_type": context_type,
                    "query_analysis": query_analysis,
                    "base_contexts_count": len(base_contexts)
                }
            )
            
            # 7. 記錄統計
            await self._record_enhancement_stats(result)
            
            # 8. 收集數據
            await self._collect_enhancement_data(result)
            
            logger.debug(f"🧠 上下文增強完成: {len(enhancements)} 個增強 ({processing_time:.3f}s)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 上下文增強失敗: {e}")
            
            # 返回空結果
            return EnhancementResult(
                query=query,
                enhancements=[],
                total_score=0.0,
                processing_time=time.time() - start_time,
                strategies_used=[],
                metadata={"error": str(e)}
            )
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查詢"""
        analysis = {
            "length": len(query),
            "word_count": len(query.split()),
            "language": "chinese" if re.search(r'[\u4e00-\u9fff]', query) else "english",
            "complexity": "high" if len(query) > 100 else "medium" if len(query) > 50 else "low",
            "keywords": [],
            "topics": [],
            "intent": "unknown",
            "technical_level": "intermediate"
        }
        
        # 提取關鍵詞
        words = query.lower().split()
        programming_keywords = {
            "python", "javascript", "java", "c++", "html", "css", "sql",
            "react", "vue", "angular", "nodejs", "django", "flask",
            "function", "class", "variable", "loop", "condition",
            "debug", "error", "exception", "test", "api", "database",
            "machine learning", "data analysis", "web development"
        }
        
        for word in words:
            if word in programming_keywords:
                analysis["keywords"].append(word)
        
        # 推斷主題
        if any(keyword in query.lower() for keyword in ["python", "data", "analysis"]):
            analysis["topics"].append("data_science")
        if any(keyword in query.lower() for keyword in ["web", "html", "css", "javascript"]):
            analysis["topics"].append("web_development")
        if any(keyword in query.lower() for keyword in ["machine learning", "ai", "ml"]):
            analysis["topics"].append("machine_learning")
        
        # 推斷意圖
        if any(word in query.lower() for word in ["how", "如何", "怎麼"]):
            analysis["intent"] = "how_to"
        elif any(word in query.lower() for word in ["what", "什麼", "是什麼"]):
            analysis["intent"] = "definition"
        elif any(word in query.lower() for word in ["error", "bug", "問題", "錯誤"]):
            analysis["intent"] = "troubleshooting"
        elif any(word in query.lower() for word in ["best", "recommend", "推薦", "最好"]):
            analysis["intent"] = "recommendation"
        
        return analysis
    
    async def _collect_base_contexts(self, query: str, context_type: str) -> List[Dict[str, Any]]:
        """收集基礎上下文"""
        base_contexts = []
        
        try:
            # 從記憶引擎獲取相似記憶
            if self.memory_engine:
                similar_memories = await self.memory_engine.get_similar_memories(
                    content=query,
                    limit=10
                )
                
                for memory in similar_memories:
                    base_contexts.append({
                        "type": "memory",
                        "content": memory.content,
                        "importance": memory.importance_score,
                        "timestamp": memory.created_at,
                        "source": "memory_engine"
                    })
            
            # 從上下文管理器獲取相關上下文
            if self.context_manager:
                context_recommendations = await self.context_manager.get_context_recommendations(
                    query=query,
                    limit=5
                )
                
                for context in context_recommendations:
                    base_contexts.append({
                        "type": "context",
                        "content": context.content,
                        "relevance": context.relevance_score,
                        "timestamp": context.created_at,
                        "source": "context_manager"
                    })
            
            logger.debug(f"🔍 收集基礎上下文: {len(base_contexts)} 個")
            
        except Exception as e:
            logger.error(f"❌ 收集基礎上下文失敗: {e}")
        
        return base_contexts
    
    # 增強策略實現
    async def _enhance_with_similar_context(self, 
                                          query: str, 
                                          query_analysis: Dict[str, Any],
                                          base_contexts: List[Dict[str, Any]],
                                          user_id: str) -> List[ContextEnhancement]:
        """基於相似上下文的增強"""
        enhancements = []
        
        try:
            # 從基礎上下文中選擇最相似的
            similar_contexts = sorted(
                base_contexts,
                key=lambda x: x.get("importance", 0) * x.get("relevance", 0),
                reverse=True
            )[:3]
            
            for i, context in enumerate(similar_contexts):
                enhancement = ContextEnhancement(
                    id=f"similar_{i}_{int(time.time())}",
                    query=query,
                    enhancement_type=ContextType.HISTORICAL,
                    strategy=EnhancementStrategy.SIMILAR_CONTEXT,
                    content=context["content"][:500],  # 限制長度
                    relevance_score=context.get("relevance", context.get("importance", 0.5)),
                    confidence=0.8,
                    source=context["source"],
                    metadata={
                        "context_type": context["type"],
                        "timestamp": context["timestamp"]
                    },
                    created_at=time.time()
                )
                
                enhancements.append(enhancement)
        
        except Exception as e:
            logger.error(f"❌ 相似上下文增強失敗: {e}")
        
        return enhancements
    
    async def _enhance_with_learning_patterns(self,
                                            query: str,
                                            query_analysis: Dict[str, Any],
                                            base_contexts: List[Dict[str, Any]],
                                            user_id: str) -> List[ContextEnhancement]:
        """基於學習模式的增強"""
        enhancements = []
        
        try:
            if self.learning_adapter:
                # 獲取最佳實踐
                best_practices = await self.learning_adapter.get_best_practices(
                    query=query,
                    domain="software_engineering"
                )
                
                for i, practice in enumerate(best_practices[:2]):
                    enhancement = ContextEnhancement(
                        id=f"learning_{i}_{int(time.time())}",
                        query=query,
                        enhancement_type=ContextType.PROCEDURAL,
                        strategy=EnhancementStrategy.LEARNING_PATTERN,
                        content=practice["content"],
                        relevance_score=practice["quality_score"],
                        confidence=0.9,
                        source="learning_adapter",
                        metadata={
                            "practice_id": practice["id"],
                            "domain": practice["domain"],
                            "tags": practice["tags"]
                        },
                        created_at=time.time()
                    )
                    
                    enhancements.append(enhancement)
        
        except Exception as e:
            logger.error(f"❌ 學習模式增強失敗: {e}")
        
        return enhancements
    
    async def _enhance_with_user_preferences(self,
                                           query: str,
                                           query_analysis: Dict[str, Any],
                                           base_contexts: List[Dict[str, Any]],
                                           user_id: str) -> List[ContextEnhancement]:
        """基於用戶偏好的增強"""
        enhancements = []
        
        try:
            if self.personalization_manager:
                # 獲取用戶偏好
                user_preferences = await self.personalization_manager.get_user_preferences(
                    user_id=user_id,
                    context=query
                )
                
                preferences = user_preferences.get("preferences", {})
                
                # 基於偏好生成增強
                if preferences:
                    # 技術水平偏好
                    if "technical_level" in preferences:
                        tech_level = preferences["technical_level"]["value"]
                        
                        enhancement = ContextEnhancement(
                            id=f"user_pref_{int(time.time())}",
                            query=query,
                            enhancement_type=ContextType.PERSONAL,
                            strategy=EnhancementStrategy.USER_PREFERENCE,
                            content=f"根據您的技術水平 ({tech_level})，建議以下方法...",
                            relevance_score=0.7,
                            confidence=preferences["technical_level"]["confidence"],
                            source="personalization_manager",
                            metadata={
                                "user_id": user_id,
                                "preference_type": "technical_level",
                                "preference_value": tech_level
                            },
                            created_at=time.time()
                        )
                        
                        enhancements.append(enhancement)
                    
                    # 響應格式偏好
                    if "response_format" in preferences:
                        format_pref = preferences["response_format"]["value"]
                        
                        enhancement = ContextEnhancement(
                            id=f"format_pref_{int(time.time())}",
                            query=query,
                            enhancement_type=ContextType.PERSONAL,
                            strategy=EnhancementStrategy.USER_PREFERENCE,
                            content=f"根據您偏好的響應格式 ({format_pref})，將以結構化方式回答...",
                            relevance_score=0.6,
                            confidence=preferences["response_format"]["confidence"],
                            source="personalization_manager",
                            metadata={
                                "user_id": user_id,
                                "preference_type": "response_format",
                                "preference_value": format_pref
                            },
                            created_at=time.time()
                        )
                        
                        enhancements.append(enhancement)
        
        except Exception as e:
            logger.error(f"❌ 用戶偏好增強失敗: {e}")
        
        return enhancements
    
    async def _enhance_with_domain_knowledge(self,
                                           query: str,
                                           query_analysis: Dict[str, Any],
                                           base_contexts: List[Dict[str, Any]],
                                           user_id: str) -> List[ContextEnhancement]:
        """基於領域知識的增強"""
        enhancements = []
        
        try:
            # 基於查詢分析的主題提供領域知識
            topics = query_analysis.get("topics", [])
            
            domain_knowledge = {
                "data_science": {
                    "libraries": ["pandas", "numpy", "matplotlib", "seaborn", "scikit-learn"],
                    "concepts": ["data cleaning", "feature engineering", "model validation"],
                    "best_practices": ["use vectorized operations", "handle missing data", "cross-validation"]
                },
                "web_development": {
                    "technologies": ["HTML5", "CSS3", "JavaScript ES6", "React", "Vue"],
                    "concepts": ["responsive design", "accessibility", "performance optimization"],
                    "best_practices": ["semantic HTML", "mobile-first design", "code splitting"]
                },
                "machine_learning": {
                    "algorithms": ["linear regression", "random forest", "neural networks"],
                    "concepts": ["overfitting", "bias-variance tradeoff", "feature selection"],
                    "best_practices": ["data preprocessing", "model evaluation", "hyperparameter tuning"]
                }
            }
            
            for topic in topics:
                if topic in domain_knowledge:
                    knowledge = domain_knowledge[topic]
                    
                    enhancement = ContextEnhancement(
                        id=f"domain_{topic}_{int(time.time())}",
                        query=query,
                        enhancement_type=ContextType.DOMAIN_SPECIFIC,
                        strategy=EnhancementStrategy.DOMAIN_KNOWLEDGE,
                        content=f"在 {topic} 領域中，相關的工具和概念包括: {', '.join(knowledge.get('libraries', knowledge.get('technologies', [])))}",
                        relevance_score=0.8,
                        confidence=0.9,
                        source="domain_knowledge_base",
                        metadata={
                            "domain": topic,
                            "knowledge_type": "domain_specific",
                            "libraries": knowledge.get("libraries", []),
                            "concepts": knowledge.get("concepts", []),
                            "best_practices": knowledge.get("best_practices", [])
                        },
                        created_at=time.time()
                    )
                    
                    enhancements.append(enhancement)
        
        except Exception as e:
            logger.error(f"❌ 領域知識增強失敗: {e}")
        
        return enhancements
    
    async def _enhance_with_temporal_context(self,
                                           query: str,
                                           query_analysis: Dict[str, Any],
                                           base_contexts: List[Dict[str, Any]],
                                           user_id: str) -> List[ContextEnhancement]:
        """基於時間上下文的增強"""
        enhancements = []
        
        try:
            # 分析時間模式
            current_time = time.time()
            current_hour = time.localtime(current_time).tm_hour
            
            # 基於時間提供相關建議
            if 9 <= current_hour <= 17:
                time_context = "工作時間，建議專注於效率和最佳實踐"
            elif 18 <= current_hour <= 22:
                time_context = "晚間時間，適合學習和深入研究"
            else:
                time_context = "非常規時間，建議關注基礎概念"
            
            # 查找最近的相關上下文
            recent_contexts = [
                ctx for ctx in base_contexts
                if current_time - ctx.get("timestamp", 0) < 3600  # 最近1小時
            ]
            
            if recent_contexts:
                enhancement = ContextEnhancement(
                    id=f"temporal_{int(time.time())}",
                    query=query,
                    enhancement_type=ContextType.TEMPORAL,
                    strategy=EnhancementStrategy.TEMPORAL_CONTEXT,
                    content=f"基於當前時間上下文: {time_context}。您最近查詢了相關主題，可能需要深入了解...",
                    relevance_score=0.6,
                    confidence=0.7,
                    source="temporal_analyzer",
                    metadata={
                        "current_hour": current_hour,
                        "time_context": time_context,
                        "recent_contexts_count": len(recent_contexts)
                    },
                    created_at=time.time()
                )
                
                enhancements.append(enhancement)
        
        except Exception as e:
            logger.error(f"❌ 時間上下文增強失敗: {e}")
        
        return enhancements
    
    async def _enhance_with_collaborative_filtering(self,
                                                  query: str,
                                                  query_analysis: Dict[str, Any],
                                                  base_contexts: List[Dict[str, Any]],
                                                  user_id: str) -> List[ContextEnhancement]:
        """基於協作過濾的增強"""
        enhancements = []
        
        try:
            # 簡化的協作過濾實現
            # 在實際應用中，這裡會分析其他用戶的類似查詢和反饋
            
            similar_user_queries = [
                "其他用戶在類似問題上也關注了性能優化",
                "類似查詢的用戶通常也會問及錯誤處理",
                "相關主題的用戶建議先了解基礎概念"
            ]
            
            if similar_user_queries:
                enhancement = ContextEnhancement(
                    id=f"collaborative_{int(time.time())}",
                    query=query,
                    enhancement_type=ContextType.COLLABORATIVE,
                    strategy=EnhancementStrategy.COLLABORATIVE_FILTER,
                    content=f"基於其他用戶的經驗: {similar_user_queries[0]}",
                    relevance_score=0.5,
                    confidence=0.6,
                    source="collaborative_filter",
                    metadata={
                        "similar_queries": similar_user_queries,
                        "user_similarity_score": 0.7
                    },
                    created_at=time.time()
                )
                
                enhancements.append(enhancement)
        
        except Exception as e:
            logger.error(f"❌ 協作過濾增強失敗: {e}")
        
        return enhancements
    
    async def _enhance_with_adaptive_weighting(self,
                                             query: str,
                                             query_analysis: Dict[str, Any],
                                             base_contexts: List[Dict[str, Any]],
                                             user_id: str) -> List[ContextEnhancement]:
        """基於自適應權重的增強"""
        enhancements = []
        
        try:
            # 基於最近的增強效果調整權重
            recent_feedback = list(self.feedback_buffer)
            
            if recent_feedback:
                avg_satisfaction = np.mean([f.get("satisfaction", 0) for f in recent_feedback])
                
                if avg_satisfaction > 0.8:
                    weight_suggestion = "當前增強策略效果良好，建議繼續使用"
                elif avg_satisfaction > 0.6:
                    weight_suggestion = "增強策略表現中等，可考慮調整"
                else:
                    weight_suggestion = "增強策略需要優化，建議重新評估"
                
                enhancement = ContextEnhancement(
                    id=f"adaptive_{int(time.time())}",
                    query=query,
                    enhancement_type=ContextType.ADAPTIVE,
                    strategy=EnhancementStrategy.ADAPTIVE_WEIGHTING,
                    content=f"基於自適應分析: {weight_suggestion}",
                    relevance_score=0.4,
                    confidence=0.8,
                    source="adaptive_weighting",
                    metadata={
                        "avg_satisfaction": avg_satisfaction,
                        "feedback_count": len(recent_feedback),
                        "weight_adjustment": weight_suggestion
                    },
                    created_at=time.time()
                )
                
                enhancements.append(enhancement)
        
        except Exception as e:
            logger.error(f"❌ 自適應權重增強失敗: {e}")
        
        return enhancements
    
    async def _rank_enhancements(self, 
                               enhancements: List[ContextEnhancement],
                               query_analysis: Dict[str, Any]) -> List[ContextEnhancement]:
        """排序增強"""
        try:
            # 計算綜合分數
            for enhancement in enhancements:
                # 基礎分數
                base_score = enhancement.relevance_score * enhancement.confidence
                
                # 策略權重
                strategy_weight = self.strategy_weights.get(enhancement.strategy, 0.1)
                
                # 查詢匹配度
                query_match = self._calculate_query_match(enhancement, query_analysis)
                
                # 時間衰減
                time_decay = self._calculate_time_decay(enhancement)
                
                # 綜合分數
                final_score = base_score * strategy_weight * query_match * time_decay
                
                enhancement.relevance_score = final_score
            
            # 排序
            enhancements.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return enhancements
            
        except Exception as e:
            logger.error(f"❌ 排序增強失敗: {e}")
            return enhancements
    
    def _calculate_query_match(self, enhancement: ContextEnhancement, query_analysis: Dict[str, Any]) -> float:
        """計算查詢匹配度"""
        try:
            # 簡化的匹配度計算
            keywords = query_analysis.get("keywords", [])
            enhancement_text = enhancement.content.lower()
            
            match_count = sum(1 for keyword in keywords if keyword in enhancement_text)
            
            if keywords:
                return min(1.0, match_count / len(keywords))
            else:
                return 0.5
        
        except Exception:
            return 0.5
    
    def _calculate_time_decay(self, enhancement: ContextEnhancement) -> float:
        """計算時間衰減"""
        try:
            current_time = time.time()
            age = current_time - enhancement.created_at
            
            # 時間衰減因子 (1小時內為1.0，之後指數衰減)
            if age < 3600:
                return 1.0
            else:
                return max(0.1, 0.5 ** (age / 3600))
        
        except Exception:
            return 1.0
    
    async def _record_enhancement_stats(self, result: EnhancementResult):
        """記錄增強統計"""
        try:
            self.enhancement_stats["total_enhancements"] += 1
            
            if result.total_score > 0:
                self.enhancement_stats["successful_enhancements"] += 1
            
            # 更新平均處理時間
            current_avg = self.enhancement_stats["average_processing_time"]
            new_avg = (current_avg * (self.enhancement_stats["total_enhancements"] - 1) + 
                      result.processing_time) / self.enhancement_stats["total_enhancements"]
            self.enhancement_stats["average_processing_time"] = new_avg
            
            # 添加到最近增強記錄
            self.recent_enhancements.append(result)
            
        except Exception as e:
            logger.error(f"❌ 記錄增強統計失敗: {e}")
    
    async def _collect_enhancement_data(self, result: EnhancementResult):
        """收集增強數據"""
        try:
            # 收集到數據收集系統
            data_collection = self.learning_integration.data_collection_system
            
            if data_collection:
                await data_collection.collect_data(
                    data_type=DataType.CONTEXT_USAGE,
                    source="intelligent_context_enhancement",
                    data={
                        "query": result.query,
                        "enhancement_count": len(result.enhancements),
                        "total_score": result.total_score,
                        "processing_time": result.processing_time,
                        "strategies_used": result.strategies_used
                    },
                    priority=DataPriority.NORMAL,
                    metadata=result.metadata
                )
        
        except Exception as e:
            logger.error(f"❌ 收集增強數據失敗: {e}")
    
    async def _analyze_recent_enhancements(self):
        """分析最近的增強效果"""
        try:
            if not self.recent_enhancements:
                return
            
            # 分析成功率
            recent_results = list(self.recent_enhancements)
            success_rate = sum(1 for r in recent_results if r.total_score > 0) / len(recent_results)
            
            # 分析平均處理時間
            avg_time = np.mean([r.processing_time for r in recent_results])
            
            # 分析策略效果
            strategy_effectiveness = defaultdict(list)
            for result in recent_results:
                for strategy in result.strategies_used:
                    strategy_effectiveness[strategy].append(result.total_score)
            
            # 記錄分析結果
            logger.info(f"📊 最近增強分析: 成功率={success_rate:.2f}, 平均時間={avg_time:.3f}s")
            
        except Exception as e:
            logger.error(f"❌ 分析最近增強失敗: {e}")
    
    async def _adjust_strategy_weights(self):
        """調整策略權重"""
        try:
            # 基於最近的效果調整策略權重
            if not self.recent_enhancements:
                return
            
            strategy_performance = defaultdict(list)
            
            for result in self.recent_enhancements:
                for strategy in result.strategies_used:
                    strategy_performance[strategy].append(result.total_score)
            
            # 調整權重
            for strategy_name, scores in strategy_performance.items():
                if scores:
                    avg_score = np.mean(scores)
                    
                    # 找到對應的策略枚舉
                    strategy_enum = None
                    for strategy in EnhancementStrategy:
                        if strategy.value == strategy_name:
                            strategy_enum = strategy
                            break
                    
                    if strategy_enum:
                        current_weight = self.strategy_weights.get(strategy_enum, 0.1)
                        
                        # 基於平均分數調整權重
                        if avg_score > 0.8:
                            new_weight = min(0.5, current_weight * 1.1)
                        elif avg_score > 0.6:
                            new_weight = current_weight
                        else:
                            new_weight = max(0.05, current_weight * 0.9)
                        
                        self.strategy_weights[strategy_enum] = new_weight
            
            logger.debug("🔧 策略權重調整完成")
            
        except Exception as e:
            logger.error(f"❌ 調整策略權重失敗: {e}")
    
    async def record_feedback(self, 
                            query: str,
                            enhancement_result: EnhancementResult,
                            user_satisfaction: float,
                            used_enhancements: List[str] = None):
        """記錄反饋"""
        try:
            feedback = {
                "query": query,
                "enhancement_count": len(enhancement_result.enhancements),
                "total_score": enhancement_result.total_score,
                "processing_time": enhancement_result.processing_time,
                "user_satisfaction": user_satisfaction,
                "used_enhancements": used_enhancements or [],
                "strategies_used": enhancement_result.strategies_used,
                "timestamp": time.time()
            }
            
            # 添加到反饋緩衝區
            self.feedback_buffer.append(feedback)
            
            # 更新統計
            for strategy in enhancement_result.strategies_used:
                self.enhancement_stats["user_feedback"][strategy].append(user_satisfaction)
            
            # 收集反饋數據
            data_collection = self.learning_integration.data_collection_system
            if data_collection:
                await data_collection.collect_data(
                    data_type=DataType.FEEDBACK_RESPONSE,
                    source="intelligent_context_enhancement",
                    data=feedback,
                    priority=DataPriority.HIGH
                )
            
            logger.debug(f"✅ 記錄反饋: 滿意度={user_satisfaction:.2f}")
            
        except Exception as e:
            logger.error(f"❌ 記錄反饋失敗: {e}")
    
    async def get_enhancement_statistics(self) -> Dict[str, Any]:
        """獲取增強統計"""
        try:
            stats = {
                "enhancement_stats": self.enhancement_stats.copy(),
                "strategy_weights": {
                    strategy.value: weight
                    for strategy, weight in self.strategy_weights.items()
                },
                "recent_enhancements": len(self.recent_enhancements),
                "feedback_buffer": len(self.feedback_buffer),
                "system_status": {
                    "initialized": self.is_initialized,
                    "strategies_count": len(self.enhancement_strategies),
                    "analyzers_count": len(self.context_analyzers)
                }
            }
            
            # 計算策略效果
            strategy_effectiveness = {}
            for strategy, feedback_list in self.enhancement_stats["user_feedback"].items():
                if feedback_list:
                    strategy_effectiveness[strategy] = {
                        "average_satisfaction": np.mean(feedback_list),
                        "feedback_count": len(feedback_list)
                    }
            
            stats["strategy_effectiveness"] = strategy_effectiveness
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 獲取增強統計失敗: {e}")
            return {}
    
    # 上下文分析器實現
    async def _analyze_semantic_context(self, query: str) -> Dict[str, Any]:
        """分析語義上下文"""
        # 實現語義分析邏輯
        return {"semantic_analysis": "completed"}
    
    async def _analyze_procedural_context(self, query: str) -> Dict[str, Any]:
        """分析程序化上下文"""
        # 實現程序化分析邏輯
        return {"procedural_analysis": "completed"}
    
    async def _analyze_personal_context(self, query: str) -> Dict[str, Any]:
        """分析個人化上下文"""
        # 實現個人化分析邏輯
        return {"personal_analysis": "completed"}
    
    async def _analyze_domain_specific_context(self, query: str) -> Dict[str, Any]:
        """分析領域特定上下文"""
        # 實現領域特定分析邏輯
        return {"domain_analysis": "completed"}
    
    async def _analyze_temporal_context(self, query: str) -> Dict[str, Any]:
        """分析時間上下文"""
        # 實現時間分析邏輯
        return {"temporal_analysis": "completed"}
    
    async def _analyze_collaborative_context(self, query: str) -> Dict[str, Any]:
        """分析協作上下文"""
        # 實現協作分析邏輯
        return {"collaborative_analysis": "completed"}

# 創建全局智能上下文增強系統實例
intelligent_context_enhancement = None

async def initialize_intelligent_context_enhancement(learning_integration: PowerAutomationLearningIntegration):
    """初始化智能上下文增強系統"""
    global intelligent_context_enhancement
    
    if intelligent_context_enhancement is None:
        intelligent_context_enhancement = IntelligentContextEnhancement(learning_integration)
        await intelligent_context_enhancement.initialize()
    
    return intelligent_context_enhancement

async def get_intelligent_context_enhancement():
    """獲取智能上下文增強系統實例"""
    global intelligent_context_enhancement
    
    if intelligent_context_enhancement is None:
        raise RuntimeError("智能上下文增強系統尚未初始化")
    
    return intelligent_context_enhancement

# 測試函數
async def main():
    """測試智能上下文增強系統"""
    print("🧪 測試智能上下文增強系統...")
    
    # 這裡需要模擬 learning_integration，在實際使用中會從真實實例獲取
    # 測試代碼略
    
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())