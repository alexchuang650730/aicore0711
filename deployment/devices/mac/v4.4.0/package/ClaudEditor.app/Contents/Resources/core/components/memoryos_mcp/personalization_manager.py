"""
Personalization Manager - AI Personalization and Adaptation System

This module provides comprehensive personalization capabilities for AI systems,
enabling adaptive learning, user preference modeling, and personalized experiences
based on interaction patterns and feedback.
"""

import asyncio
import json
import time
import uuid
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta


class PersonalizationDimension(Enum):
    """Dimensions of personalization"""
    COMMUNICATION_STYLE = "communication_style"
    TASK_PREFERENCES = "task_preferences"
    LEARNING_PACE = "learning_pace"
    INTERACTION_PATTERNS = "interaction_patterns"
    CONTENT_PREFERENCES = "content_preferences"
    WORKFLOW_PREFERENCES = "workflow_preferences"
    FEEDBACK_SENSITIVITY = "feedback_sensitivity"
    COMPLEXITY_TOLERANCE = "complexity_tolerance"


class LearningMode(Enum):
    """Learning modes for personalization"""
    PASSIVE = "passive"          # Learn from observations
    ACTIVE = "active"            # Ask for explicit feedback
    REINFORCEMENT = "reinforcement"  # Learn from outcomes
    COLLABORATIVE = "collaborative"  # Learn from similar users
    ADAPTIVE = "adaptive"        # Dynamically adjust learning approach


class PersonalityType(Enum):
    """User personality types for personalization"""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PRACTICAL = "practical"
    SOCIAL = "social"
    DETAIL_ORIENTED = "detail_oriented"
    BIG_PICTURE = "big_picture"
    FAST_PACED = "fast_paced"
    METHODICAL = "methodical"


@dataclass
class UserProfile:
    """Comprehensive user profile for personalization"""
    user_id: str
    personality_type: Optional[PersonalityType]
    communication_style: Dict[str, float]
    task_preferences: Dict[str, float]
    learning_patterns: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    feedback_patterns: Dict[str, float]
    performance_metrics: Dict[str, float]
    preferences: Dict[str, Any]
    created_at: float
    last_updated: float
    confidence_score: float


@dataclass
class PersonalizationRule:
    """Personalization rule definition"""
    rule_id: str
    dimension: PersonalizationDimension
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: int
    confidence: float
    success_rate: float
    usage_count: int
    created_at: float


@dataclass
class AdaptationEvent:
    """Event representing an adaptation in personalization"""
    event_id: str
    user_id: str
    dimension: PersonalizationDimension
    old_value: Any
    new_value: Any
    trigger: str
    confidence: float
    timestamp: float
    metadata: Dict[str, Any]


class PersonalizationManager:
    """
    Personalization Manager
    
    Provides comprehensive personalization and adaptation capabilities,
    enabling AI systems to learn and adapt to individual user preferences,
    communication styles, and interaction patterns.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Personalization Manager
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Personalization configuration
        self.learning_rate = self.config.get('learning_rate', 0.1)
        self.adaptation_threshold = self.config.get('adaptation_threshold', 0.7)
        self.max_history_size = self.config.get('max_history_size', 1000)
        self.enable_collaborative_learning = self.config.get('enable_collaborative_learning', True)
        self.enable_active_learning = self.config.get('enable_active_learning', True)
        
        # User profiles and data
        self.user_profiles = {}
        self.personalization_rules = {}
        self.adaptation_history = defaultdict(list)
        self.interaction_patterns = defaultdict(list)
        
        # Learning and adaptation
        self.learning_models = {}
        self.adaptation_triggers = {}
        self.feedback_queue = deque(maxlen=1000)
        
        # Performance tracking
        self.personalization_stats = {
            'total_users': 0,
            'total_adaptations': 0,
            'successful_adaptations': 0,
            'average_confidence': 0.0,
            'learning_accuracy': 0.0,
            'user_satisfaction': 0.0
        }
        
        # Initialize personalization components
        self._initialize_personalization_rules()
        self._initialize_learning_models()
        
        self.logger.info("PersonalizationManager initialized")
    
    async def create_user_profile(
        self, 
        user_id: str, 
        initial_data: Optional[Dict[str, Any]] = None
    ) -> UserProfile:
        """
        Create a new user profile for personalization
        
        Args:
            user_id: Unique user identifier
            initial_data: Optional initial user data
            
        Returns:
            UserProfile: Created user profile
        """
        try:
            self.logger.info(f"Creating user profile for: {user_id}")
            
            # Initialize default profile
            profile = UserProfile(
                user_id=user_id,
                personality_type=None,
                communication_style=self._get_default_communication_style(),
                task_preferences=self._get_default_task_preferences(),
                learning_patterns={},
                interaction_history=[],
                feedback_patterns={},
                performance_metrics={},
                preferences=initial_data or {},
                created_at=time.time(),
                last_updated=time.time(),
                confidence_score=0.1  # Low initial confidence
            )
            
            # Apply initial data if provided
            if initial_data:
                await self._apply_initial_data(profile, initial_data)
            
            # Detect initial personality type
            profile.personality_type = await self._detect_personality_type(profile)
            
            # Store profile
            self.user_profiles[user_id] = profile
            
            # Update statistics
            self.personalization_stats['total_users'] += 1
            
            self.logger.info(f"User profile created for {user_id}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to create user profile for {user_id}: {str(e)}")
            raise
    
    async def update_user_interaction(
        self, 
        user_id: str, 
        interaction_data: Dict[str, Any]
    ) -> bool:
        """
        Update user profile based on interaction data
        
        Args:
            user_id: User identifier
            interaction_data: Interaction data to learn from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if user_id not in self.user_profiles:
                await self.create_user_profile(user_id)
            
            profile = self.user_profiles[user_id]
            
            # Add interaction to history
            interaction_record = {
                'timestamp': time.time(),
                'data': interaction_data,
                'session_id': interaction_data.get('session_id'),
                'task_type': interaction_data.get('task_type'),
                'outcome': interaction_data.get('outcome')
            }
            
            profile.interaction_history.append(interaction_record)
            
            # Limit history size
            if len(profile.interaction_history) > self.max_history_size:
                profile.interaction_history = profile.interaction_history[-self.max_history_size:]
            
            # Update interaction patterns
            await self._update_interaction_patterns(user_id, interaction_data)
            
            # Learn from interaction
            adaptations = await self._learn_from_interaction(profile, interaction_data)
            
            # Apply adaptations
            for adaptation in adaptations:
                await self._apply_adaptation(profile, adaptation)
            
            # Update profile timestamp and confidence
            profile.last_updated = time.time()
            await self._update_profile_confidence(profile)
            
            self.logger.info(f"Updated user interaction for {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user interaction for {user_id}: {str(e)}")
            return False
    
    async def get_personalized_response(
        self, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized response based on user profile
        
        Args:
            user_id: User identifier
            context: Context for personalization
            
        Returns:
            Dict: Personalized response configuration
        """
        try:
            if user_id not in self.user_profiles:
                # Return default response for unknown users
                return self._get_default_response(context)
            
            profile = self.user_profiles[user_id]
            
            # Generate personalized response
            response_config = {
                'communication_style': await self._personalize_communication_style(profile, context),
                'content_preferences': await self._personalize_content(profile, context),
                'interaction_preferences': await self._personalize_interaction(profile, context),
                'workflow_preferences': await self._personalize_workflow(profile, context),
                'complexity_level': await self._determine_complexity_level(profile, context),
                'learning_approach': await self._determine_learning_approach(profile, context),
                'feedback_style': await self._personalize_feedback_style(profile, context)
            }
            
            # Add metadata
            response_config['personalization_metadata'] = {
                'user_id': user_id,
                'confidence_score': profile.confidence_score,
                'personality_type': profile.personality_type.value if profile.personality_type else None,
                'adaptation_count': len(self.adaptation_history[user_id]),
                'last_updated': profile.last_updated
            }
            
            return response_config
            
        except Exception as e:
            self.logger.error(f"Failed to generate personalized response for {user_id}: {str(e)}")
            return self._get_default_response(context)
    
    async def process_user_feedback(
        self, 
        user_id: str, 
        feedback: Dict[str, Any]
    ) -> bool:
        """
        Process user feedback for personalization improvement
        
        Args:
            user_id: User identifier
            feedback: User feedback data
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        try:
            if user_id not in self.user_profiles:
                await self.create_user_profile(user_id)
            
            profile = self.user_profiles[user_id]
            
            # Add feedback to queue
            feedback_record = {
                'user_id': user_id,
                'timestamp': time.time(),
                'feedback': feedback,
                'context': feedback.get('context', {})
            }
            self.feedback_queue.append(feedback_record)
            
            # Update feedback patterns
            await self._update_feedback_patterns(profile, feedback)
            
            # Learn from feedback
            if feedback.get('type') == 'explicit':
                await self._learn_from_explicit_feedback(profile, feedback)
            elif feedback.get('type') == 'implicit':
                await self._learn_from_implicit_feedback(profile, feedback)
            
            # Trigger adaptations if needed
            await self._trigger_feedback_adaptations(profile, feedback)
            
            # Update performance metrics
            await self._update_performance_metrics(profile, feedback)
            
            self.logger.info(f"Processed feedback for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process feedback for {user_id}: {str(e)}")
            return False
    
    async def adapt_to_user_preferences(
        self, 
        user_id: str, 
        dimension: PersonalizationDimension,
        trigger_data: Dict[str, Any]
    ) -> Optional[AdaptationEvent]:
        """
        Adapt to user preferences in a specific dimension
        
        Args:
            user_id: User identifier
            dimension: Personalization dimension to adapt
            trigger_data: Data that triggered the adaptation
            
        Returns:
            Optional[AdaptationEvent]: Adaptation event if successful
        """
        try:
            if user_id not in self.user_profiles:
                return None
            
            profile = self.user_profiles[user_id]
            
            # Determine if adaptation is needed
            adaptation_needed = await self._should_adapt(profile, dimension, trigger_data)
            if not adaptation_needed:
                return None
            
            # Calculate new value for the dimension
            old_value = await self._get_dimension_value(profile, dimension)
            new_value = await self._calculate_adaptation(profile, dimension, trigger_data)
            
            if old_value == new_value:
                return None
            
            # Create adaptation event
            adaptation_event = AdaptationEvent(
                event_id=f"adapt_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                dimension=dimension,
                old_value=old_value,
                new_value=new_value,
                trigger=trigger_data.get('trigger', 'unknown'),
                confidence=await self._calculate_adaptation_confidence(profile, dimension, trigger_data),
                timestamp=time.time(),
                metadata=trigger_data
            )
            
            # Apply adaptation
            success = await self._apply_adaptation(profile, adaptation_event)
            
            if success:
                # Record adaptation
                self.adaptation_history[user_id].append(adaptation_event)
                
                # Update statistics
                self.personalization_stats['total_adaptations'] += 1
                self.personalization_stats['successful_adaptations'] += 1
                
                self.logger.info(f"Adapted {dimension.value} for user {user_id}")
                return adaptation_event
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to adapt preferences for {user_id}: {str(e)}")
            return None
    
    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive insights about a user's personalization
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict: User insights and analytics
        """
        try:
            if user_id not in self.user_profiles:
                return {'error': 'User profile not found'}
            
            profile = self.user_profiles[user_id]
            adaptations = self.adaptation_history[user_id]
            
            insights = {
                'profile_summary': {
                    'user_id': user_id,
                    'personality_type': profile.personality_type.value if profile.personality_type else None,
                    'confidence_score': profile.confidence_score,
                    'profile_age_days': (time.time() - profile.created_at) / 86400,
                    'last_activity': profile.last_updated,
                    'interaction_count': len(profile.interaction_history)
                },
                'communication_preferences': profile.communication_style,
                'task_preferences': profile.task_preferences,
                'learning_patterns': await self._analyze_learning_patterns(profile),
                'adaptation_history': {
                    'total_adaptations': len(adaptations),
                    'recent_adaptations': [
                        {
                            'dimension': adapt.dimension.value,
                            'timestamp': adapt.timestamp,
                            'confidence': adapt.confidence
                        }
                        for adapt in adaptations[-10:]  # Last 10 adaptations
                    ],
                    'adaptation_frequency': await self._calculate_adaptation_frequency(adaptations)
                },
                'performance_metrics': profile.performance_metrics,
                'feedback_patterns': profile.feedback_patterns,
                'personalization_effectiveness': await self._calculate_personalization_effectiveness(profile)
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to get user insights for {user_id}: {str(e)}")
            return {'error': str(e)}
    
    async def optimize_personalization(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Optimize personalization for a specific user or all users
        
        Args:
            user_id: Optional specific user ID, None for all users
            
        Returns:
            Dict: Optimization results
        """
        start_time = time.time()
        optimization_results = {
            'users_optimized': 0,
            'rules_updated': 0,
            'models_retrained': 0,
            'optimization_time': 0.0
        }
        
        try:
            self.logger.info("Starting personalization optimization...")
            
            # Optimize specific user or all users
            users_to_optimize = [user_id] if user_id else list(self.user_profiles.keys())
            
            for uid in users_to_optimize:
                if uid in self.user_profiles:
                    await self._optimize_user_profile(uid)
                    optimization_results['users_optimized'] += 1
            
            # Update personalization rules
            rules_updated = await self._optimize_personalization_rules()
            optimization_results['rules_updated'] = rules_updated
            
            # Retrain learning models
            models_retrained = await self._retrain_learning_models()
            optimization_results['models_retrained'] = models_retrained
            
            # Update global statistics
            await self._update_global_statistics()
            
            optimization_results['optimization_time'] = time.time() - start_time
            
            self.logger.info(f"Personalization optimization completed in {optimization_results['optimization_time']:.2f}s")
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Personalization optimization failed: {str(e)}")
            optimization_results['optimization_time'] = time.time() - start_time
            return optimization_results
    
    def _get_default_communication_style(self) -> Dict[str, float]:
        """Get default communication style preferences"""
        return {
            'formality': 0.5,          # 0=casual, 1=formal
            'verbosity': 0.5,          # 0=concise, 1=detailed
            'technical_level': 0.5,    # 0=simple, 1=technical
            'enthusiasm': 0.5,         # 0=neutral, 1=enthusiastic
            'directness': 0.5,         # 0=indirect, 1=direct
            'supportiveness': 0.7,     # 0=minimal, 1=highly supportive
            'patience': 0.7,           # 0=fast-paced, 1=patient
            'encouragement': 0.6       # 0=minimal, 1=encouraging
        }
    
    def _get_default_task_preferences(self) -> Dict[str, float]:
        """Get default task preferences"""
        return {
            'complexity_tolerance': 0.5,    # 0=simple, 1=complex
            'step_by_step': 0.7,           # 0=overview, 1=detailed steps
            'automation_preference': 0.6,   # 0=manual, 1=automated
            'exploration_vs_efficiency': 0.5, # 0=efficient, 1=exploratory
            'collaboration_preference': 0.5,  # 0=independent, 1=collaborative
            'feedback_frequency': 0.6,      # 0=minimal, 1=frequent
            'error_tolerance': 0.5,         # 0=low tolerance, 1=high tolerance
            'learning_orientation': 0.7     # 0=task-focused, 1=learning-focused
        }
    
    async def _apply_initial_data(self, profile: UserProfile, initial_data: Dict[str, Any]):
        """Apply initial data to user profile"""
        # Apply communication preferences
        if 'communication_style' in initial_data:
            profile.communication_style.update(initial_data['communication_style'])
        
        # Apply task preferences
        if 'task_preferences' in initial_data:
            profile.task_preferences.update(initial_data['task_preferences'])
        
        # Apply explicit preferences
        if 'preferences' in initial_data:
            profile.preferences.update(initial_data['preferences'])
        
        # Set personality type if provided
        if 'personality_type' in initial_data:
            try:
                profile.personality_type = PersonalityType(initial_data['personality_type'])
            except ValueError:
                pass  # Invalid personality type, keep as None
    
    async def _detect_personality_type(self, profile: UserProfile) -> Optional[PersonalityType]:
        """Detect user personality type based on initial data and preferences"""
        # Simple personality detection based on preferences
        comm_style = profile.communication_style
        task_prefs = profile.task_preferences
        
        # Calculate personality scores
        analytical_score = (
            comm_style.get('technical_level', 0.5) * 0.4 +
            task_prefs.get('complexity_tolerance', 0.5) * 0.3 +
            (1 - comm_style.get('enthusiasm', 0.5)) * 0.3
        )
        
        creative_score = (
            task_prefs.get('exploration_vs_efficiency', 0.5) * 0.4 +
            comm_style.get('enthusiasm', 0.5) * 0.3 +
            (1 - comm_style.get('directness', 0.5)) * 0.3
        )
        
        practical_score = (
            (1 - task_prefs.get('exploration_vs_efficiency', 0.5)) * 0.4 +
            comm_style.get('directness', 0.5) * 0.3 +
            task_prefs.get('automation_preference', 0.5) * 0.3
        )
        
        social_score = (
            task_prefs.get('collaboration_preference', 0.5) * 0.4 +
            comm_style.get('supportiveness', 0.5) * 0.3 +
            comm_style.get('encouragement', 0.5) * 0.3
        )
        
        # Determine dominant personality type
        scores = {
            PersonalityType.ANALYTICAL: analytical_score,
            PersonalityType.CREATIVE: creative_score,
            PersonalityType.PRACTICAL: practical_score,
            PersonalityType.SOCIAL: social_score
        }
        
        # Return type with highest score if above threshold
        max_type = max(scores.items(), key=lambda x: x[1])
        if max_type[1] > 0.6:
            return max_type[0]
        
        return None  # No clear personality type detected
    
    async def _update_interaction_patterns(self, user_id: str, interaction_data: Dict[str, Any]):
        """Update interaction patterns for user"""
        patterns = self.interaction_patterns[user_id]
        
        # Add interaction pattern
        pattern = {
            'timestamp': time.time(),
            'task_type': interaction_data.get('task_type'),
            'duration': interaction_data.get('duration', 0),
            'success': interaction_data.get('success', True),
            'complexity': interaction_data.get('complexity', 0.5),
            'user_satisfaction': interaction_data.get('satisfaction', 0.5)
        }
        
        patterns.append(pattern)
        
        # Limit pattern history
        if len(patterns) > self.max_history_size:
            patterns[:] = patterns[-self.max_history_size:]
    
    async def _learn_from_interaction(self, profile: UserProfile, interaction_data: Dict[str, Any]) -> List[AdaptationEvent]:
        """Learn from user interaction and generate adaptations"""
        adaptations = []
        
        # Learn communication style preferences
        if 'communication_feedback' in interaction_data:
            comm_adaptation = await self._learn_communication_preferences(profile, interaction_data)
            if comm_adaptation:
                adaptations.append(comm_adaptation)
        
        # Learn task preferences
        if 'task_feedback' in interaction_data:
            task_adaptation = await self._learn_task_preferences(profile, interaction_data)
            if task_adaptation:
                adaptations.append(task_adaptation)
        
        # Learn from success/failure patterns
        if 'outcome' in interaction_data:
            outcome_adaptations = await self._learn_from_outcome(profile, interaction_data)
            adaptations.extend(outcome_adaptations)
        
        return adaptations
    
    async def _learn_communication_preferences(self, profile: UserProfile, interaction_data: Dict[str, Any]) -> Optional[AdaptationEvent]:
        """Learn communication style preferences from interaction"""
        feedback = interaction_data.get('communication_feedback', {})
        
        if not feedback:
            return None
        
        # Calculate adjustments based on feedback
        adjustments = {}
        
        if 'too_formal' in feedback:
            adjustments['formality'] = -0.1
        elif 'too_casual' in feedback:
            adjustments['formality'] = 0.1
        
        if 'too_verbose' in feedback:
            adjustments['verbosity'] = -0.1
        elif 'too_brief' in feedback:
            adjustments['verbosity'] = 0.1
        
        if 'too_technical' in feedback:
            adjustments['technical_level'] = -0.1
        elif 'too_simple' in feedback:
            adjustments['technical_level'] = 0.1
        
        if adjustments:
            return AdaptationEvent(
                event_id=f"comm_adapt_{uuid.uuid4().hex[:8]}",
                user_id=profile.user_id,
                dimension=PersonalizationDimension.COMMUNICATION_STYLE,
                old_value=profile.communication_style.copy(),
                new_value=adjustments,
                trigger='communication_feedback',
                confidence=0.7,
                timestamp=time.time(),
                metadata=feedback
            )
        
        return None
    
    async def _learn_task_preferences(self, profile: UserProfile, interaction_data: Dict[str, Any]) -> Optional[AdaptationEvent]:
        """Learn task preferences from interaction"""
        feedback = interaction_data.get('task_feedback', {})
        
        if not feedback:
            return None
        
        adjustments = {}
        
        if 'too_complex' in feedback:
            adjustments['complexity_tolerance'] = -0.1
        elif 'too_simple' in feedback:
            adjustments['complexity_tolerance'] = 0.1
        
        if 'need_more_steps' in feedback:
            adjustments['step_by_step'] = 0.1
        elif 'too_detailed' in feedback:
            adjustments['step_by_step'] = -0.1
        
        if adjustments:
            return AdaptationEvent(
                event_id=f"task_adapt_{uuid.uuid4().hex[:8]}",
                user_id=profile.user_id,
                dimension=PersonalizationDimension.TASK_PREFERENCES,
                old_value=profile.task_preferences.copy(),
                new_value=adjustments,
                trigger='task_feedback',
                confidence=0.7,
                timestamp=time.time(),
                metadata=feedback
            )
        
        return None
    
    async def _learn_from_outcome(self, profile: UserProfile, interaction_data: Dict[str, Any]) -> List[AdaptationEvent]:
        """Learn from interaction outcomes"""
        adaptations = []
        
        outcome = interaction_data.get('outcome', {})
        success = outcome.get('success', True)
        satisfaction = outcome.get('satisfaction', 0.5)
        
        # Learn from unsuccessful interactions
        if not success:
            # Reduce complexity tolerance if task was too complex
            if outcome.get('reason') == 'too_complex':
                adaptation = AdaptationEvent(
                    event_id=f"outcome_adapt_{uuid.uuid4().hex[:8]}",
                    user_id=profile.user_id,
                    dimension=PersonalizationDimension.COMPLEXITY_TOLERANCE,
                    old_value=profile.task_preferences.get('complexity_tolerance', 0.5),
                    new_value=-0.05,  # Small adjustment
                    trigger='failure_too_complex',
                    confidence=0.6,
                    timestamp=time.time(),
                    metadata=outcome
                )
                adaptations.append(adaptation)
        
        # Learn from satisfaction levels
        if satisfaction < 0.3:
            # Low satisfaction - adjust communication style to be more supportive
            adaptation = AdaptationEvent(
                event_id=f"satisfaction_adapt_{uuid.uuid4().hex[:8]}",
                user_id=profile.user_id,
                dimension=PersonalizationDimension.COMMUNICATION_STYLE,
                old_value=profile.communication_style.get('supportiveness', 0.7),
                new_value=0.1,  # Increase supportiveness
                trigger='low_satisfaction',
                confidence=0.5,
                timestamp=time.time(),
                metadata={'satisfaction': satisfaction}
            )
            adaptations.append(adaptation)
        
        return adaptations
    
    async def _apply_adaptation(self, profile: UserProfile, adaptation: AdaptationEvent) -> bool:
        """Apply adaptation to user profile"""
        try:
            dimension = adaptation.dimension
            
            if dimension == PersonalizationDimension.COMMUNICATION_STYLE:
                if isinstance(adaptation.new_value, dict):
                    # Apply multiple adjustments
                    for key, adjustment in adaptation.new_value.items():
                        if key in profile.communication_style:
                            old_value = profile.communication_style[key]
                            new_value = max(0.0, min(1.0, old_value + adjustment))
                            profile.communication_style[key] = new_value
                else:
                    # Single adjustment (assuming it's for a specific key)
                    # This would need more context about which key to adjust
                    pass
            
            elif dimension == PersonalizationDimension.TASK_PREFERENCES:
                if isinstance(adaptation.new_value, dict):
                    for key, adjustment in adaptation.new_value.items():
                        if key in profile.task_preferences:
                            old_value = profile.task_preferences[key]
                            new_value = max(0.0, min(1.0, old_value + adjustment))
                            profile.task_preferences[key] = new_value
            
            elif dimension == PersonalizationDimension.COMPLEXITY_TOLERANCE:
                if isinstance(adaptation.new_value, (int, float)):
                    old_value = profile.task_preferences.get('complexity_tolerance', 0.5)
                    new_value = max(0.0, min(1.0, old_value + adaptation.new_value))
                    profile.task_preferences['complexity_tolerance'] = new_value
            
            # Update profile timestamp
            profile.last_updated = time.time()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply adaptation: {str(e)}")
            return False
    
    async def _update_profile_confidence(self, profile: UserProfile):
        """Update profile confidence based on interaction history and adaptations"""
        # Base confidence on interaction count and adaptation success
        interaction_count = len(profile.interaction_history)
        adaptation_count = len(self.adaptation_history[profile.user_id])
        
        # Calculate confidence based on data availability
        data_confidence = min(1.0, interaction_count / 50)  # Max confidence at 50 interactions
        adaptation_confidence = min(1.0, adaptation_count / 20)  # Max confidence at 20 adaptations
        
        # Calculate time-based confidence (newer profiles have lower confidence)
        profile_age_days = (time.time() - profile.created_at) / 86400
        time_confidence = min(1.0, profile_age_days / 30)  # Max confidence after 30 days
        
        # Combine confidence factors
        profile.confidence_score = (
            data_confidence * 0.4 +
            adaptation_confidence * 0.3 +
            time_confidence * 0.3
        )
    
    async def _personalize_communication_style(self, profile: UserProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize communication style based on user profile"""
        style = profile.communication_style.copy()
        
        # Adjust based on context
        if context.get('task_type') == 'complex':
            style['technical_level'] = min(1.0, style['technical_level'] + 0.1)
            style['verbosity'] = min(1.0, style['verbosity'] + 0.1)
        
        if context.get('user_mood') == 'frustrated':
            style['supportiveness'] = min(1.0, style['supportiveness'] + 0.2)
            style['patience'] = min(1.0, style['patience'] + 0.2)
        
        return style
    
    async def _personalize_content(self, profile: UserProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize content based on user preferences"""
        content_prefs = {
            'detail_level': profile.communication_style.get('verbosity', 0.5),
            'technical_depth': profile.communication_style.get('technical_level', 0.5),
            'examples_included': profile.task_preferences.get('step_by_step', 0.7),
            'visual_aids': profile.preferences.get('visual_learning', 0.5)
        }
        
        # Adjust based on personality type
        if profile.personality_type == PersonalityType.ANALYTICAL:
            content_prefs['technical_depth'] = min(1.0, content_prefs['technical_depth'] + 0.2)
            content_prefs['detail_level'] = min(1.0, content_prefs['detail_level'] + 0.1)
        elif profile.personality_type == PersonalityType.CREATIVE:
            content_prefs['visual_aids'] = min(1.0, content_prefs['visual_aids'] + 0.2)
            content_prefs['examples_included'] = min(1.0, content_prefs['examples_included'] + 0.1)
        
        return content_prefs
    
    async def _personalize_interaction(self, profile: UserProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize interaction patterns"""
        interaction_prefs = {
            'response_speed': 1.0 - profile.communication_style.get('patience', 0.7),
            'proactive_suggestions': profile.task_preferences.get('automation_preference', 0.6),
            'confirmation_requests': 1.0 - profile.task_preferences.get('error_tolerance', 0.5),
            'collaborative_mode': profile.task_preferences.get('collaboration_preference', 0.5)
        }
        
        return interaction_prefs
    
    async def _personalize_workflow(self, profile: UserProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize workflow preferences"""
        workflow_prefs = {
            'step_granularity': profile.task_preferences.get('step_by_step', 0.7),
            'automation_level': profile.task_preferences.get('automation_preference', 0.6),
            'feedback_frequency': profile.task_preferences.get('feedback_frequency', 0.6),
            'error_handling': profile.task_preferences.get('error_tolerance', 0.5)
        }
        
        return workflow_prefs
    
    async def _determine_complexity_level(self, profile: UserProfile, context: Dict[str, Any]) -> float:
        """Determine appropriate complexity level for user"""
        base_complexity = profile.task_preferences.get('complexity_tolerance', 0.5)
        
        # Adjust based on context
        if context.get('task_importance') == 'high':
            base_complexity = min(1.0, base_complexity + 0.1)
        
        if context.get('time_pressure') == 'high':
            base_complexity = max(0.0, base_complexity - 0.2)
        
        return base_complexity
    
    async def _determine_learning_approach(self, profile: UserProfile, context: Dict[str, Any]) -> str:
        """Determine appropriate learning approach for user"""
        learning_orientation = profile.task_preferences.get('learning_orientation', 0.7)
        
        if learning_orientation > 0.8:
            return 'exploratory'
        elif learning_orientation > 0.6:
            return 'guided'
        elif learning_orientation > 0.4:
            return 'structured'
        else:
            return 'direct'
    
    async def _personalize_feedback_style(self, profile: UserProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize feedback style"""
        feedback_style = {
            'frequency': profile.task_preferences.get('feedback_frequency', 0.6),
            'detail_level': profile.communication_style.get('verbosity', 0.5),
            'encouragement_level': profile.communication_style.get('encouragement', 0.6),
            'constructive_criticism': profile.feedback_patterns.get('criticism_tolerance', 0.5)
        }
        
        return feedback_style
    
    def _get_default_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get default response configuration for unknown users"""
        return {
            'communication_style': self._get_default_communication_style(),
            'content_preferences': {
                'detail_level': 0.5,
                'technical_depth': 0.5,
                'examples_included': 0.7,
                'visual_aids': 0.5
            },
            'interaction_preferences': {
                'response_speed': 0.5,
                'proactive_suggestions': 0.5,
                'confirmation_requests': 0.6,
                'collaborative_mode': 0.5
            },
            'workflow_preferences': {
                'step_granularity': 0.7,
                'automation_level': 0.5,
                'feedback_frequency': 0.6,
                'error_handling': 0.5
            },
            'complexity_level': 0.5,
            'learning_approach': 'guided',
            'feedback_style': {
                'frequency': 0.6,
                'detail_level': 0.5,
                'encouragement_level': 0.6,
                'constructive_criticism': 0.5
            },
            'personalization_metadata': {
                'user_id': 'unknown',
                'confidence_score': 0.0,
                'personality_type': None,
                'adaptation_count': 0,
                'last_updated': None
            }
        }
    
    async def _update_feedback_patterns(self, profile: UserProfile, feedback: Dict[str, Any]):
        """Update user feedback patterns"""
        feedback_type = feedback.get('type', 'implicit')
        feedback_value = feedback.get('value', 0.5)
        
        if feedback_type not in profile.feedback_patterns:
            profile.feedback_patterns[feedback_type] = []
        
        profile.feedback_patterns[feedback_type].append({
            'timestamp': time.time(),
            'value': feedback_value,
            'context': feedback.get('context', {})
        })
        
        # Limit feedback history
        if len(profile.feedback_patterns[feedback_type]) > 100:
            profile.feedback_patterns[feedback_type] = profile.feedback_patterns[feedback_type][-100:]
    
    async def _learn_from_explicit_feedback(self, profile: UserProfile, feedback: Dict[str, Any]):
        """Learn from explicit user feedback"""
        feedback_value = feedback.get('value', 0.5)
        feedback_dimension = feedback.get('dimension')
        
        if feedback_dimension and feedback_dimension in [d.value for d in PersonalizationDimension]:
            # Apply direct feedback to the specified dimension
            dimension = PersonalizationDimension(feedback_dimension)
            
            adaptation = AdaptationEvent(
                event_id=f"explicit_adapt_{uuid.uuid4().hex[:8]}",
                user_id=profile.user_id,
                dimension=dimension,
                old_value=await self._get_dimension_value(profile, dimension),
                new_value=feedback_value,
                trigger='explicit_feedback',
                confidence=0.9,  # High confidence for explicit feedback
                timestamp=time.time(),
                metadata=feedback
            )
            
            await self._apply_adaptation(profile, adaptation)
    
    async def _learn_from_implicit_feedback(self, profile: UserProfile, feedback: Dict[str, Any]):
        """Learn from implicit user feedback"""
        # Implicit feedback learning (e.g., from user behavior patterns)
        satisfaction = feedback.get('satisfaction', 0.5)
        task_completion = feedback.get('task_completion', True)
        
        if satisfaction < 0.3 or not task_completion:
            # Low satisfaction or incomplete task - adjust preferences
            adjustments = {
                'complexity_tolerance': -0.05,
                'step_by_step': 0.05
            }
            
            adaptation = AdaptationEvent(
                event_id=f"implicit_adapt_{uuid.uuid4().hex[:8]}",
                user_id=profile.user_id,
                dimension=PersonalizationDimension.TASK_PREFERENCES,
                old_value=profile.task_preferences.copy(),
                new_value=adjustments,
                trigger='implicit_feedback',
                confidence=0.4,  # Lower confidence for implicit feedback
                timestamp=time.time(),
                metadata=feedback
            )
            
            await self._apply_adaptation(profile, adaptation)
    
    async def _trigger_feedback_adaptations(self, profile: UserProfile, feedback: Dict[str, Any]):
        """Trigger adaptations based on feedback patterns"""
        # Analyze recent feedback patterns to trigger adaptations
        recent_feedback = []
        for feedback_type, feedback_list in profile.feedback_patterns.items():
            recent_feedback.extend([f for f in feedback_list if time.time() - f['timestamp'] < 86400])  # Last 24 hours
        
        if len(recent_feedback) >= 3:
            # Enough recent feedback to trigger adaptations
            avg_satisfaction = sum(f['value'] for f in recent_feedback) / len(recent_feedback)
            
            if avg_satisfaction < 0.4:
                # Consistently low satisfaction - trigger comprehensive adaptation
                await self.adapt_to_user_preferences(
                    profile.user_id,
                    PersonalizationDimension.COMMUNICATION_STYLE,
                    {'trigger': 'low_satisfaction_pattern', 'satisfaction': avg_satisfaction}
                )
    
    async def _update_performance_metrics(self, profile: UserProfile, feedback: Dict[str, Any]):
        """Update user performance metrics"""
        if 'performance' in feedback:
            perf_data = feedback['performance']
            
            for metric, value in perf_data.items():
                if metric not in profile.performance_metrics:
                    profile.performance_metrics[metric] = []
                
                profile.performance_metrics[metric].append({
                    'timestamp': time.time(),
                    'value': value
                })
                
                # Limit metric history
                if len(profile.performance_metrics[metric]) > 100:
                    profile.performance_metrics[metric] = profile.performance_metrics[metric][-100:]
    
    async def _should_adapt(self, profile: UserProfile, dimension: PersonalizationDimension, trigger_data: Dict[str, Any]) -> bool:
        """Determine if adaptation should be triggered"""
        # Check adaptation threshold
        confidence = await self._calculate_adaptation_confidence(profile, dimension, trigger_data)
        
        if confidence < self.adaptation_threshold:
            return False
        
        # Check if recent adaptation already occurred for this dimension
        recent_adaptations = [
            adapt for adapt in self.adaptation_history[profile.user_id]
            if adapt.dimension == dimension and time.time() - adapt.timestamp < 3600  # Last hour
        ]
        
        if len(recent_adaptations) > 2:  # Too many recent adaptations
            return False
        
        return True
    
    async def _get_dimension_value(self, profile: UserProfile, dimension: PersonalizationDimension) -> Any:
        """Get current value for a personalization dimension"""
        if dimension == PersonalizationDimension.COMMUNICATION_STYLE:
            return profile.communication_style.copy()
        elif dimension == PersonalizationDimension.TASK_PREFERENCES:
            return profile.task_preferences.copy()
        elif dimension == PersonalizationDimension.COMPLEXITY_TOLERANCE:
            return profile.task_preferences.get('complexity_tolerance', 0.5)
        else:
            return None
    
    async def _calculate_adaptation(self, profile: UserProfile, dimension: PersonalizationDimension, trigger_data: Dict[str, Any]) -> Any:
        """Calculate new value for adaptation"""
        # This is a simplified adaptation calculation
        # In a real implementation, this would use more sophisticated ML algorithms
        
        current_value = await self._get_dimension_value(profile, dimension)
        
        if dimension == PersonalizationDimension.COMPLEXITY_TOLERANCE:
            # Adjust complexity tolerance based on trigger
            if trigger_data.get('trigger') == 'task_too_complex':
                return max(0.0, current_value - 0.1)
            elif trigger_data.get('trigger') == 'task_too_simple':
                return min(1.0, current_value + 0.1)
        
        return current_value  # No change
    
    async def _calculate_adaptation_confidence(self, profile: UserProfile, dimension: PersonalizationDimension, trigger_data: Dict[str, Any]) -> float:
        """Calculate confidence for adaptation"""
        base_confidence = profile.confidence_score
        
        # Adjust based on trigger strength
        trigger_strength = trigger_data.get('strength', 0.5)
        
        # Adjust based on data availability
        data_points = len(profile.interaction_history)
        data_confidence = min(1.0, data_points / 20)
        
        return (base_confidence * 0.5 + trigger_strength * 0.3 + data_confidence * 0.2)
    
    async def _analyze_learning_patterns(self, profile: UserProfile) -> Dict[str, Any]:
        """Analyze user learning patterns"""
        interactions = profile.interaction_history
        
        if not interactions:
            return {}
        
        # Analyze task completion patterns
        completion_rate = sum(1 for i in interactions if i['data'].get('outcome', {}).get('success', True)) / len(interactions)
        
        # Analyze learning speed
        learning_speed = 0.5  # Default
        if len(interactions) > 5:
            recent_success = sum(1 for i in interactions[-5:] if i['data'].get('outcome', {}).get('success', True)) / 5
            early_success = sum(1 for i in interactions[:5] if i['data'].get('outcome', {}).get('success', True)) / 5
            learning_speed = max(0.0, min(1.0, recent_success - early_success + 0.5))
        
        return {
            'completion_rate': completion_rate,
            'learning_speed': learning_speed,
            'preferred_task_types': self._get_preferred_task_types(interactions),
            'peak_performance_time': self._get_peak_performance_time(interactions),
            'learning_style': self._infer_learning_style(profile)
        }
    
    def _get_preferred_task_types(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """Get user's preferred task types"""
        task_success = defaultdict(list)
        
        for interaction in interactions:
            task_type = interaction['data'].get('task_type')
            success = interaction['data'].get('outcome', {}).get('success', True)
            
            if task_type:
                task_success[task_type].append(success)
        
        # Calculate success rates for each task type
        task_rates = {}
        for task_type, successes in task_success.items():
            task_rates[task_type] = sum(successes) / len(successes)
        
        # Return top 3 task types by success rate
        sorted_tasks = sorted(task_rates.items(), key=lambda x: x[1], reverse=True)
        return [task_type for task_type, rate in sorted_tasks[:3]]
    
    def _get_peak_performance_time(self, interactions: List[Dict[str, Any]]) -> str:
        """Get user's peak performance time"""
        # Simplified analysis - in reality would analyze timestamps
        return "morning"  # Default
    
    def _infer_learning_style(self, profile: UserProfile) -> str:
        """Infer user's learning style"""
        if profile.task_preferences.get('step_by_step', 0.7) > 0.8:
            return "sequential"
        elif profile.task_preferences.get('exploration_vs_efficiency', 0.5) > 0.7:
            return "exploratory"
        elif profile.communication_style.get('technical_level', 0.5) > 0.7:
            return "analytical"
        else:
            return "practical"
    
    async def _calculate_adaptation_frequency(self, adaptations: List[AdaptationEvent]) -> Dict[str, float]:
        """Calculate adaptation frequency by dimension"""
        if not adaptations:
            return {}
        
        dimension_counts = defaultdict(int)
        for adaptation in adaptations:
            dimension_counts[adaptation.dimension.value] += 1
        
        total_adaptations = len(adaptations)
        return {
            dimension: count / total_adaptations
            for dimension, count in dimension_counts.items()
        }
    
    async def _calculate_personalization_effectiveness(self, profile: UserProfile) -> Dict[str, float]:
        """Calculate personalization effectiveness metrics"""
        interactions = profile.interaction_history
        
        if len(interactions) < 10:
            return {'insufficient_data': True}
        
        # Calculate improvement over time
        early_interactions = interactions[:len(interactions)//2]
        recent_interactions = interactions[len(interactions)//2:]
        
        early_satisfaction = sum(
            i['data'].get('outcome', {}).get('satisfaction', 0.5)
            for i in early_interactions
        ) / len(early_interactions)
        
        recent_satisfaction = sum(
            i['data'].get('outcome', {}).get('satisfaction', 0.5)
            for i in recent_interactions
        ) / len(recent_interactions)
        
        improvement = recent_satisfaction - early_satisfaction
        
        return {
            'satisfaction_improvement': improvement,
            'early_satisfaction': early_satisfaction,
            'recent_satisfaction': recent_satisfaction,
            'personalization_impact': max(0.0, improvement * 2)  # Scale to 0-1
        }
    
    async def _optimize_user_profile(self, user_id: str):
        """Optimize a specific user profile"""
        if user_id not in self.user_profiles:
            return
        
        profile = self.user_profiles[user_id]
        
        # Update confidence score
        await self._update_profile_confidence(profile)
        
        # Optimize preferences based on recent interactions
        recent_interactions = [
            i for i in profile.interaction_history
            if time.time() - i['timestamp'] < 86400 * 7  # Last week
        ]
        
        if len(recent_interactions) >= 5:
            # Analyze recent patterns and adjust preferences
            await self._optimize_preferences_from_patterns(profile, recent_interactions)
    
    async def _optimize_preferences_from_patterns(self, profile: UserProfile, interactions: List[Dict[str, Any]]):
        """Optimize preferences based on interaction patterns"""
        # Analyze success patterns
        successful_interactions = [i for i in interactions if i['data'].get('outcome', {}).get('success', True)]
        
        if len(successful_interactions) > len(interactions) * 0.8:
            # High success rate - can increase complexity tolerance slightly
            current_complexity = profile.task_preferences.get('complexity_tolerance', 0.5)
            profile.task_preferences['complexity_tolerance'] = min(1.0, current_complexity + 0.05)
        elif len(successful_interactions) < len(interactions) * 0.5:
            # Low success rate - decrease complexity tolerance
            current_complexity = profile.task_preferences.get('complexity_tolerance', 0.5)
            profile.task_preferences['complexity_tolerance'] = max(0.0, current_complexity - 0.1)
    
    async def _optimize_personalization_rules(self) -> int:
        """Optimize personalization rules based on usage patterns"""
        # This would implement rule optimization logic
        # For now, return 0 as placeholder
        return 0
    
    async def _retrain_learning_models(self) -> int:
        """Retrain learning models with new data"""
        # This would implement model retraining logic
        # For now, return 0 as placeholder
        return 0
    
    async def _update_global_statistics(self):
        """Update global personalization statistics"""
        if not self.user_profiles:
            return
        
        # Calculate average confidence
        total_confidence = sum(profile.confidence_score for profile in self.user_profiles.values())
        self.personalization_stats['average_confidence'] = total_confidence / len(self.user_profiles)
        
        # Calculate user satisfaction
        total_satisfaction = 0
        satisfaction_count = 0
        
        for profile in self.user_profiles.values():
            for interaction in profile.interaction_history[-10:]:  # Last 10 interactions
                satisfaction = interaction['data'].get('outcome', {}).get('satisfaction')
                if satisfaction is not None:
                    total_satisfaction += satisfaction
                    satisfaction_count += 1
        
        if satisfaction_count > 0:
            self.personalization_stats['user_satisfaction'] = total_satisfaction / satisfaction_count
    
    def _initialize_personalization_rules(self):
        """Initialize default personalization rules"""
        # This would load or create default personalization rules
        self.personalization_rules = {}
    
    def _initialize_learning_models(self):
        """Initialize learning models for personalization"""
        # This would initialize ML models for personalization
        self.learning_models = {}
    
    async def get_personalization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive personalization statistics"""
        stats = self.personalization_stats.copy()
        
        # Add current state information
        stats.update({
            'total_profiles': len(self.user_profiles),
            'active_profiles': sum(
                1 for profile in self.user_profiles.values()
                if time.time() - profile.last_updated < 86400 * 7  # Active in last week
            ),
            'total_adaptation_events': sum(len(adaptations) for adaptations in self.adaptation_history.values()),
            'average_adaptations_per_user': (
                sum(len(adaptations) for adaptations in self.adaptation_history.values()) /
                max(1, len(self.user_profiles))
            ),
            'personality_distribution': self._get_personality_distribution(),
            'adaptation_success_rate': (
                self.personalization_stats['successful_adaptations'] /
                max(1, self.personalization_stats['total_adaptations'])
            )
        })
        
        return stats
    
    def _get_personality_distribution(self) -> Dict[str, int]:
        """Get distribution of personality types"""
        distribution = defaultdict(int)
        
        for profile in self.user_profiles.values():
            if profile.personality_type:
                distribution[profile.personality_type.value] += 1
            else:
                distribution['unknown'] += 1
        
        return dict(distribution)

