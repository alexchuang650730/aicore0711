#!/usr/bin/env python3
"""
MemoryOS MCP - 個性化管理器
管理用戶偏好和個性化設置
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class PreferenceType(Enum):
    """偏好類型"""
    COMMUNICATION_STYLE = "communication_style"
    TECHNICAL_LEVEL = "technical_level"
    RESPONSE_FORMAT = "response_format"
    TOPIC_INTEREST = "topic_interest"
    INTERACTION_PATTERN = "interaction_pattern"
    WORKFLOW_PREFERENCE = "workflow_preference"

@dataclass
class UserPreference:
    """用戶偏好"""
    id: str
    user_id: str
    preference_type: PreferenceType
    value: Any
    confidence: float
    last_updated: float
    update_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)

@dataclass
class UserProfile:
    """用戶檔案"""
    user_id: str
    preferences: Dict[str, UserPreference]
    interaction_history: List[Dict[str, Any]]
    skill_level: Dict[str, float]
    interests: Dict[str, float]
    created_at: float
    last_active: float
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "user_id": self.user_id,
            "preferences": {k: v.to_dict() for k, v in self.preferences.items()},
            "interaction_history": self.interaction_history,
            "skill_level": self.skill_level,
            "interests": self.interests,
            "created_at": self.created_at,
            "last_active": self.last_active
        }

class PersonalizationManager:
    """個性化管理器"""
    
    def __init__(self, memory_engine, context_manager):
        self.memory_engine = memory_engine
        self.context_manager = context_manager
        self.user_profiles: Dict[str, UserProfile] = {}
        self.preference_patterns = defaultdict(dict)
        self.adaptation_algorithms = {}
        self.is_initialized = False
    
    async def initialize(self):
        """初始化個性化管理器"""
        logger.info("👤 初始化 Personalization Manager...")
        
        # 載入用戶檔案
        await self._load_user_profiles()
        
        # 初始化適配算法
        await self._initialize_adaptation_algorithms()
        
        # 載入偏好模式
        await self._load_preference_patterns()
        
        self.is_initialized = True
        logger.info("✅ Personalization Manager 初始化完成")
    
    async def _load_user_profiles(self):
        """載入用戶檔案"""
        try:
            # 從記憶引擎中載入用戶檔案
            user_memories = await self.memory_engine.search_memories(
                memory_type=self.memory_engine.MemoryType.USER_PREFERENCE,
                limit=100
            )
            
            for memory in user_memories:
                try:
                    profile_data = json.loads(memory.content)
                    user_id = profile_data.get("user_id", "default_user")
                    
                    # 重建用戶檔案
                    preferences = {}
                    for pref_id, pref_data in profile_data.get("preferences", {}).items():
                        preferences[pref_id] = UserPreference(
                            id=pref_data["id"],
                            user_id=pref_data["user_id"],
                            preference_type=PreferenceType(pref_data["preference_type"]),
                            value=pref_data["value"],
                            confidence=pref_data["confidence"],
                            last_updated=pref_data["last_updated"],
                            update_count=pref_data["update_count"]
                        )
                    
                    self.user_profiles[user_id] = UserProfile(
                        user_id=user_id,
                        preferences=preferences,
                        interaction_history=profile_data.get("interaction_history", []),
                        skill_level=profile_data.get("skill_level", {}),
                        interests=profile_data.get("interests", {}),
                        created_at=profile_data.get("created_at", time.time()),
                        last_active=profile_data.get("last_active", time.time())
                    )
                    
                except Exception as e:
                    logger.warning(f"載入用戶檔案失敗: {e}")
                    continue
            
            logger.info(f"📊 載入 {len(self.user_profiles)} 個用戶檔案")
            
        except Exception as e:
            logger.error(f"❌ 載入用戶檔案失敗: {e}")
    
    async def _initialize_adaptation_algorithms(self):
        """初始化適配算法"""
        self.adaptation_algorithms = {
            PreferenceType.COMMUNICATION_STYLE: self._adapt_communication_style,
            PreferenceType.TECHNICAL_LEVEL: self._adapt_technical_level,
            PreferenceType.RESPONSE_FORMAT: self._adapt_response_format,
            PreferenceType.TOPIC_INTEREST: self._adapt_topic_interest,
            PreferenceType.INTERACTION_PATTERN: self._adapt_interaction_pattern,
            PreferenceType.WORKFLOW_PREFERENCE: self._adapt_workflow_preference
        }
    
    async def _load_preference_patterns(self):
        """載入偏好模式"""
        # 分析已有用戶的偏好模式
        for user_id, profile in self.user_profiles.items():
            for pref_id, preference in profile.preferences.items():
                pref_type = preference.preference_type
                
                if pref_type not in self.preference_patterns:
                    self.preference_patterns[pref_type] = {
                        "common_values": defaultdict(int),
                        "value_correlations": defaultdict(list),
                        "adaptation_patterns": defaultdict(list)
                    }
                
                # 統計常見值
                self.preference_patterns[pref_type]["common_values"][str(preference.value)] += 1
    
    async def get_user_preferences(self, 
                                 user_id: str = "default_user",
                                 context: str = "") -> Dict[str, Any]:
        """獲取用戶偏好"""
        try:
            if user_id not in self.user_profiles:
                # 創建新用戶檔案
                await self._create_user_profile(user_id)
            
            profile = self.user_profiles[user_id]
            
            # 構建偏好響應
            preferences = {}
            
            for pref_id, preference in profile.preferences.items():
                preferences[preference.preference_type.value] = {
                    "value": preference.value,
                    "confidence": preference.confidence,
                    "last_updated": preference.last_updated
                }
            
            # 添加推斷的偏好
            inferred_preferences = await self._infer_preferences(profile, context)
            preferences.update(inferred_preferences)
            
            return {
                "user_id": user_id,
                "preferences": preferences,
                "skill_level": profile.skill_level,
                "interests": profile.interests,
                "interaction_count": len(profile.interaction_history),
                "last_active": profile.last_active
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取用戶偏好失敗: {e}")
            return {}
    
    async def _create_user_profile(self, user_id: str):
        """創建用戶檔案"""
        logger.info(f"👤 創建新用戶檔案: {user_id}")
        
        # 創建默認偏好
        default_preferences = {
            "communication_style": UserPreference(
                id=f"pref_{user_id}_comm",
                user_id=user_id,
                preference_type=PreferenceType.COMMUNICATION_STYLE,
                value="professional",
                confidence=0.3,
                last_updated=time.time(),
                update_count=0
            ),
            "technical_level": UserPreference(
                id=f"pref_{user_id}_tech",
                user_id=user_id,
                preference_type=PreferenceType.TECHNICAL_LEVEL,
                value="intermediate",
                confidence=0.3,
                last_updated=time.time(),
                update_count=0
            ),
            "response_format": UserPreference(
                id=f"pref_{user_id}_format",
                user_id=user_id,
                preference_type=PreferenceType.RESPONSE_FORMAT,
                value="structured",
                confidence=0.3,
                last_updated=time.time(),
                update_count=0
            )
        }
        
        # 創建用戶檔案
        profile = UserProfile(
            user_id=user_id,
            preferences=default_preferences,
            interaction_history=[],
            skill_level={"general": 0.5, "programming": 0.5, "data_analysis": 0.5},
            interests={"software_development": 0.5, "data_science": 0.3, "web_development": 0.3},
            created_at=time.time(),
            last_active=time.time()
        )
        
        self.user_profiles[user_id] = profile
        
        # 保存到記憶引擎
        await self._save_user_profile(profile)
    
    async def _infer_preferences(self, 
                               profile: UserProfile, 
                               context: str) -> Dict[str, Any]:
        """推斷用戶偏好"""
        inferred = {}
        
        # 基於交互歷史推斷
        if profile.interaction_history:
            # 分析響應長度偏好
            response_lengths = [len(interaction.get("claude_response", "")) 
                              for interaction in profile.interaction_history[-10:]]
            
            if response_lengths:
                avg_length = np.mean(response_lengths)
                if avg_length > 1000:
                    inferred["response_length_preference"] = {
                        "value": "detailed",
                        "confidence": 0.6,
                        "source": "interaction_history"
                    }
                elif avg_length < 300:
                    inferred["response_length_preference"] = {
                        "value": "concise",
                        "confidence": 0.6,
                        "source": "interaction_history"
                    }
            
            # 分析主題偏好
            topics = self._extract_topics_from_history(profile.interaction_history)
            if topics:
                most_common_topic = max(topics, key=topics.get)
                inferred["preferred_topic"] = {
                    "value": most_common_topic,
                    "confidence": min(0.8, topics[most_common_topic] / 10),
                    "source": "topic_analysis"
                }
        
        # 基於上下文推斷
        if context:
            context_preferences = await self._analyze_context_preferences(context)
            inferred.update(context_preferences)
        
        return inferred
    
    def _extract_topics_from_history(self, history: List[Dict[str, Any]]) -> Dict[str, int]:
        """從歷史中提取主題"""
        topics = defaultdict(int)
        
        programming_keywords = {
            "python": "python_development",
            "javascript": "web_development",
            "java": "java_development",
            "data": "data_science",
            "analysis": "data_analysis",
            "web": "web_development",
            "api": "api_development",
            "database": "database_management",
            "machine learning": "machine_learning",
            "ai": "artificial_intelligence"
        }
        
        for interaction in history:
            user_input = interaction.get("user_input", "").lower()
            
            for keyword, topic in programming_keywords.items():
                if keyword in user_input:
                    topics[topic] += 1
        
        return dict(topics)
    
    async def _analyze_context_preferences(self, context: str) -> Dict[str, Any]:
        """分析上下文偏好"""
        preferences = {}
        
        context_lower = context.lower()
        
        # 分析技術複雜度
        if any(term in context_lower for term in ["advanced", "complex", "deep", "detailed"]):
            preferences["technical_complexity"] = {
                "value": "advanced",
                "confidence": 0.7,
                "source": "context_analysis"
            }
        elif any(term in context_lower for term in ["simple", "basic", "beginner", "easy"]):
            preferences["technical_complexity"] = {
                "value": "basic",
                "confidence": 0.7,
                "source": "context_analysis"
            }
        
        # 分析響應格式偏好
        if any(term in context_lower for term in ["step", "guide", "tutorial", "how to"]):
            preferences["response_format_context"] = {
                "value": "step_by_step",
                "confidence": 0.6,
                "source": "context_analysis"
            }
        elif any(term in context_lower for term in ["example", "code", "snippet"]):
            preferences["response_format_context"] = {
                "value": "example_focused",
                "confidence": 0.6,
                "source": "context_analysis"
            }
        
        return preferences
    
    async def update_user_model(self, 
                              interaction_data: Dict[str, Any],
                              user_id: str = "default_user",
                              source: str = "claude_interaction"):
        """更新用戶模型"""
        try:
            if user_id not in self.user_profiles:
                await self._create_user_profile(user_id)
            
            profile = self.user_profiles[user_id]
            
            # 更新交互歷史
            interaction_record = {
                "user_input": interaction_data.get("interaction", {}).get("user_input", ""),
                "claude_response": interaction_data.get("interaction", {}).get("claude_response", ""),
                "user_satisfaction": interaction_data.get("interaction", {}).get("user_satisfaction", 0),
                "response_time": interaction_data.get("interaction", {}).get("response_time", 0),
                "timestamp": time.time(),
                "source": source
            }
            
            profile.interaction_history.append(interaction_record)
            profile.last_active = time.time()
            
            # 保持歷史記錄在合理範圍內
            if len(profile.interaction_history) > 100:
                profile.interaction_history = profile.interaction_history[-100:]
            
            # 更新技能等級
            await self._update_skill_level(profile, interaction_record)
            
            # 更新興趣
            await self._update_interests(profile, interaction_record)
            
            # 更新偏好
            await self._update_preferences(profile, interaction_record)
            
            # 保存更新後的檔案
            await self._save_user_profile(profile)
            
            logger.debug(f"✅ 更新用戶模型: {user_id}")
            
        except Exception as e:
            logger.error(f"❌ 更新用戶模型失敗: {e}")
    
    async def _update_skill_level(self, profile: UserProfile, interaction: Dict[str, Any]):
        """更新技能等級"""
        user_input = interaction.get("user_input", "").lower()
        user_satisfaction = interaction.get("user_satisfaction", 0)
        
        # 基於問題複雜度和滿意度調整技能等級
        programming_indicators = {
            "python": "programming",
            "javascript": "programming",
            "data analysis": "data_analysis",
            "machine learning": "data_analysis",
            "web development": "programming",
            "api": "programming"
        }
        
        for indicator, skill in programming_indicators.items():
            if indicator in user_input:
                current_level = profile.skill_level.get(skill, 0.5)
                
                # 高滿意度表示當前難度適合，略微提升
                if user_satisfaction > 0.7:
                    adjustment = 0.05
                elif user_satisfaction < 0.3:
                    adjustment = -0.02  # 可能難度過高
                else:
                    adjustment = 0.01
                
                new_level = max(0.0, min(1.0, current_level + adjustment))
                profile.skill_level[skill] = new_level
    
    async def _update_interests(self, profile: UserProfile, interaction: Dict[str, Any]):
        """更新興趣"""
        user_input = interaction.get("user_input", "").lower()
        
        interest_keywords = {
            "software development": ["programming", "coding", "development", "software"],
            "data science": ["data", "analysis", "statistics", "machine learning"],
            "web development": ["web", "frontend", "backend", "html", "css", "javascript"],
            "ai": ["ai", "artificial intelligence", "neural network", "deep learning"],
            "database": ["database", "sql", "mongodb", "postgresql"]
        }
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                current_interest = profile.interests.get(interest, 0.3)
                # 提升興趣度
                new_interest = min(1.0, current_interest + 0.05)
                profile.interests[interest] = new_interest
    
    async def _update_preferences(self, profile: UserProfile, interaction: Dict[str, Any]):
        """更新偏好"""
        user_input = interaction.get("user_input", "")
        claude_response = interaction.get("claude_response", "")
        user_satisfaction = interaction.get("user_satisfaction", 0)
        
        # 基於用戶滿意度調整偏好
        if user_satisfaction > 0.7:
            # 分析成功的交互模式
            await self._reinforce_successful_patterns(profile, interaction)
        elif user_satisfaction < 0.3:
            # 調整不成功的模式
            await self._adjust_unsuccessful_patterns(profile, interaction)
    
    async def _reinforce_successful_patterns(self, profile: UserProfile, interaction: Dict[str, Any]):
        """強化成功模式"""
        claude_response = interaction.get("claude_response", "")
        
        # 分析回應格式
        if len(claude_response) > 1000:
            # 長回應成功，用戶偏好詳細回應
            await self._update_preference(profile, PreferenceType.RESPONSE_FORMAT, "detailed", 0.1)
        elif len(claude_response) < 300:
            # 短回應成功，用戶偏好簡潔回應
            await self._update_preference(profile, PreferenceType.RESPONSE_FORMAT, "concise", 0.1)
        
        # 分析技術水平
        if any(term in claude_response.lower() for term in ["advanced", "complex", "sophisticated"]):
            await self._update_preference(profile, PreferenceType.TECHNICAL_LEVEL, "advanced", 0.05)
        elif any(term in claude_response.lower() for term in ["simple", "basic", "fundamental"]):
            await self._update_preference(profile, PreferenceType.TECHNICAL_LEVEL, "basic", 0.05)
    
    async def _adjust_unsuccessful_patterns(self, profile: UserProfile, interaction: Dict[str, Any]):
        """調整不成功模式"""
        # 降低當前模式的置信度
        for preference in profile.preferences.values():
            if preference.confidence > 0.1:
                preference.confidence *= 0.95
                preference.last_updated = time.time()
    
    async def _update_preference(self, 
                               profile: UserProfile,
                               preference_type: PreferenceType,
                               value: Any,
                               confidence_increase: float):
        """更新偏好"""
        pref_id = f"pref_{profile.user_id}_{preference_type.value}"
        
        if pref_id in profile.preferences:
            preference = profile.preferences[pref_id]
            
            # 如果值相同，增加置信度
            if preference.value == value:
                preference.confidence = min(1.0, preference.confidence + confidence_increase)
            else:
                # 如果值不同，降低置信度或更新值
                if preference.confidence > 0.5:
                    preference.confidence -= confidence_increase
                else:
                    preference.value = value
                    preference.confidence = 0.6
            
            preference.last_updated = time.time()
            preference.update_count += 1
        else:
            # 創建新偏好
            profile.preferences[pref_id] = UserPreference(
                id=pref_id,
                user_id=profile.user_id,
                preference_type=preference_type,
                value=value,
                confidence=0.6,
                last_updated=time.time(),
                update_count=1
            )
    
    async def _save_user_profile(self, profile: UserProfile):
        """保存用戶檔案"""
        try:
            memory_id = f"user_profile_{profile.user_id}"
            
            memory = self.memory_engine.Memory(
                id=memory_id,
                memory_type=self.memory_engine.MemoryType.USER_PREFERENCE,
                content=json.dumps(profile.to_dict()),
                metadata={
                    "user_id": profile.user_id,
                    "preference_count": len(profile.preferences),
                    "interaction_count": len(profile.interaction_history),
                    "last_active": profile.last_active
                },
                created_at=profile.created_at,
                accessed_at=time.time(),
                access_count=1,
                importance_score=1.0,
                tags=["user_profile", "personalization", profile.user_id]
            )
            
            await self.memory_engine.store_memory(memory)
            
        except Exception as e:
            logger.error(f"❌ 保存用戶檔案失敗: {e}")
    
    async def cleanup(self):
        """清理資源"""
        # 保存所有用戶檔案
        for profile in self.user_profiles.values():
            await self._save_user_profile(profile)
        
        self.user_profiles.clear()
        self.preference_patterns.clear()
        self.adaptation_algorithms.clear()
        
        logger.info("🧹 Personalization Manager 清理完成")

# 適配算法實現
    async def _adapt_communication_style(self, profile: UserProfile, context: str) -> str:
        """適配溝通風格"""
        # 實現邏輯...
        return "professional"
    
    async def _adapt_technical_level(self, profile: UserProfile, context: str) -> str:
        """適配技術水平"""
        # 實現邏輯...
        return "intermediate"
    
    async def _adapt_response_format(self, profile: UserProfile, context: str) -> str:
        """適配響應格式"""
        # 實現邏輯...
        return "structured"
    
    async def _adapt_topic_interest(self, profile: UserProfile, context: str) -> str:
        """適配主題興趣"""
        # 實現邏輯...
        return "programming"
    
    async def _adapt_interaction_pattern(self, profile: UserProfile, context: str) -> str:
        """適配交互模式"""
        # 實現邏輯...
        return "collaborative"
    
    async def _adapt_workflow_preference(self, profile: UserProfile, context: str) -> str:
        """適配工作流偏好"""
        # 實現邏輯...
        return "step_by_step"

# 測試函數
async def main():
    """測試個性化管理器"""
    print("🧪 測試 Personalization Manager...")
    
    # 模擬依賴
    class MockMemoryEngine:
        class MemoryType:
            USER_PREFERENCE = "user_preference"
        
        class Memory:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        async def search_memories(self, memory_type, limit):
            return []
        
        async def store_memory(self, memory):
            return True
    
    class MockContextManager:
        pass
    
    # 創建測試實例
    memory_engine = MockMemoryEngine()
    context_manager = MockContextManager()
    
    manager = PersonalizationManager(memory_engine, context_manager)
    await manager.initialize()
    
    # 測試獲取偏好
    preferences = await manager.get_user_preferences(
        user_id="test_user",
        context="如何使用 Python 進行數據分析？"
    )
    print(f"👤 用戶偏好: {preferences}")
    
    # 測試更新用戶模型
    test_interaction = {
        "interaction": {
            "user_input": "如何使用 Python 進行數據分析？",
            "claude_response": "Python 數據分析可以使用 pandas、numpy 等庫...",
            "user_satisfaction": 0.85,
            "response_time": 2500
        }
    }
    
    await manager.update_user_model(test_interaction, "test_user")
    
    await manager.cleanup()
    print("✅ 測試完成")

if __name__ == "__main__":
    asyncio.run(main())