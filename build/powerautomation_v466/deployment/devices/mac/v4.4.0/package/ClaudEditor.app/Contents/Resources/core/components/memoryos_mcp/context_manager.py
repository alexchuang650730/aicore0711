"""
Context Manager - AI Context Management and Awareness System

This module provides comprehensive context management capabilities for AI systems,
enabling context-aware interactions, session continuity, and intelligent context
switching based on user needs and task requirements.
"""

import asyncio
import json
import time
import uuid
import logging
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta


class ContextType(Enum):
    """Types of context in the system"""
    SESSION = "session"              # User session context
    TASK = "task"                   # Current task context
    CONVERSATION = "conversation"    # Conversation history context
    ENVIRONMENT = "environment"      # System environment context
    USER = "user"                   # User-specific context
    PROJECT = "project"             # Project-specific context
    TEMPORAL = "temporal"           # Time-based context
    SEMANTIC = "semantic"           # Semantic/topic context


class ContextScope(Enum):
    """Scope of context applicability"""
    GLOBAL = "global"               # System-wide context
    USER = "user"                   # User-specific context
    SESSION = "session"             # Session-specific context
    TASK = "task"                   # Task-specific context
    TEMPORARY = "temporary"         # Temporary context


class ContextPriority(Enum):
    """Context priority levels"""
    CRITICAL = 1                    # Critical system context
    HIGH = 2                        # High priority context
    MEDIUM = 3                      # Medium priority context
    LOW = 4                         # Low priority context
    BACKGROUND = 5                  # Background context


@dataclass
class ContextItem:
    """Individual context item"""
    context_id: str
    context_type: ContextType
    scope: ContextScope
    priority: ContextPriority
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: float
    last_accessed: float
    expires_at: Optional[float]
    access_count: int
    relevance_score: float
    tags: List[str]
    dependencies: List[str]  # IDs of dependent contexts
    parent_context: Optional[str]
    child_contexts: List[str]


@dataclass
class ContextWindow:
    """Context window for active context management"""
    window_id: str
    user_id: str
    session_id: str
    active_contexts: List[str]  # Context IDs in order of relevance
    max_size: int
    created_at: float
    last_updated: float
    focus_context: Optional[str]  # Currently focused context
    background_contexts: List[str]  # Background contexts


@dataclass
class ContextQuery:
    """Context query structure"""
    query_text: Optional[str] = None
    context_types: Optional[List[ContextType]] = None
    scopes: Optional[List[ContextScope]] = None
    tags: Optional[List[str]] = None
    time_range: Optional[Tuple[float, float]] = None
    priority_min: Optional[ContextPriority] = None
    include_expired: bool = False
    limit: int = 10
    relevance_threshold: float = 0.5


@dataclass
class ContextSwitchEvent:
    """Context switch event"""
    event_id: str
    user_id: str
    session_id: str
    from_context: Optional[str]
    to_context: str
    switch_reason: str
    timestamp: float
    metadata: Dict[str, Any]


class ContextManager:
    """
    Context Manager - AI Context Management and Awareness System
    
    Provides comprehensive context management capabilities for AI systems,
    enabling context-aware interactions, intelligent context switching,
    and maintaining context continuity across sessions and tasks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Context Manager
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Context configuration
        self.max_context_window_size = self.config.get('max_context_window_size', 20)
        self.context_expiry_hours = self.config.get('context_expiry_hours', 24)
        self.enable_context_compression = self.config.get('enable_context_compression', True)
        self.enable_semantic_clustering = self.config.get('enable_semantic_clustering', True)
        
        # Context storage
        self.contexts = {}  # All contexts by ID
        self.context_windows = {}  # Active context windows by user/session
        self.context_index = {}  # Fast lookup indices
        self.tag_index = defaultdict(set)
        self.type_index = defaultdict(set)
        self.user_contexts = defaultdict(set)
        self.session_contexts = defaultdict(set)
        
        # Context relationships
        self.context_graph = defaultdict(set)  # Context dependency graph
        self.semantic_clusters = defaultdict(set)  # Semantic context clusters
        
        # Context switching
        self.switch_history = defaultdict(list)
        self.context_transitions = defaultdict(lambda: defaultdict(int))
        
        # Performance tracking
        self.context_stats = {
            'total_contexts': 0,
            'active_contexts': 0,
            'context_switches': 0,
            'average_window_size': 0.0,
            'context_hit_rate': 0.0,
            'compression_ratio': 0.0
        }
        
        # Initialize context management
        self._initialize_default_contexts()
        
        self.logger.info("ContextManager initialized")
    
    async def create_context(
        self,
        content: Dict[str, Any],
        context_type: ContextType,
        scope: ContextScope = ContextScope.SESSION,
        priority: ContextPriority = ContextPriority.MEDIUM,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        expires_in_hours: Optional[float] = None,
        parent_context: Optional[str] = None
    ) -> str:
        """
        Create a new context item
        
        Args:
            content: Context content
            context_type: Type of context
            scope: Context scope
            priority: Context priority
            user_id: Optional user ID
            session_id: Optional session ID
            tags: Optional tags
            expires_in_hours: Optional expiration time in hours
            parent_context: Optional parent context ID
            
        Returns:
            str: Context ID
        """
        try:
            # Generate context ID
            context_id = self._generate_context_id(content, context_type)
            
            # Calculate expiration time
            expires_at = None
            if expires_in_hours:
                expires_at = time.time() + (expires_in_hours * 3600)
            elif self.context_expiry_hours > 0:
                expires_at = time.time() + (self.context_expiry_hours * 3600)
            
            # Create context item
            context_item = ContextItem(
                context_id=context_id,
                context_type=context_type,
                scope=scope,
                priority=priority,
                content=content,
                metadata={
                    'user_id': user_id,
                    'session_id': session_id,
                    'created_by': 'context_manager'
                },
                created_at=time.time(),
                last_accessed=time.time(),
                expires_at=expires_at,
                access_count=1,
                relevance_score=self._calculate_initial_relevance(content, context_type, priority),
                tags=tags or [],
                dependencies=[],
                parent_context=parent_context,
                child_contexts=[]
            )
            
            # Store context
            await self._store_context(context_item)
            
            # Update indices
            await self._update_context_indices(context_item)
            
            # Handle parent-child relationships
            if parent_context and parent_context in self.contexts:
                self.contexts[parent_context].child_contexts.append(context_id)
                await self._add_context_dependency(context_id, parent_context)
            
            # Add to active context window if applicable
            if user_id and session_id:
                await self._add_to_context_window(user_id, session_id, context_id)
            
            # Update statistics
            self.context_stats['total_contexts'] += 1
            self.context_stats['active_contexts'] += 1
            
            self.logger.info(f"Context created: {context_id} ({context_type.value})")
            return context_id
            
        except Exception as e:
            self.logger.error(f"Failed to create context: {str(e)}")
            raise
    
    async def get_context(self, context_id: str) -> Optional[ContextItem]:
        """
        Retrieve a specific context by ID
        
        Args:
            context_id: Context ID to retrieve
            
        Returns:
            Optional[ContextItem]: Retrieved context or None
        """
        try:
            if context_id not in self.contexts:
                return None
            
            context = self.contexts[context_id]
            
            # Check if context has expired
            if context.expires_at and time.time() > context.expires_at:
                await self._expire_context(context_id)
                return None
            
            # Update access information
            context.last_accessed = time.time()
            context.access_count += 1
            
            # Update relevance score based on access pattern
            await self._update_context_relevance(context)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get context {context_id}: {str(e)}")
            return None
    
    async def search_contexts(self, query: ContextQuery) -> List[ContextItem]:
        """
        Search contexts based on query criteria
        
        Args:
            query: Context query parameters
            
        Returns:
            List[ContextItem]: Matching contexts
        """
        try:
            # Get candidate contexts
            candidates = await self._get_candidate_contexts(query)
            
            # Filter and score contexts
            scored_contexts = []
            for context in candidates:
                # Check expiration
                if context.expires_at and time.time() > context.expires_at:
                    if not query.include_expired:
                        continue
                
                # Calculate relevance score
                relevance = await self._calculate_context_relevance(context, query)
                
                if relevance >= query.relevance_threshold:
                    scored_contexts.append((context, relevance))
            
            # Sort by relevance and limit results
            scored_contexts.sort(key=lambda x: x[1], reverse=True)
            results = [context for context, score in scored_contexts[:query.limit]]
            
            # Update access counts
            for context in results:
                context.last_accessed = time.time()
                context.access_count += 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"Context search failed: {str(e)}")
            return []
    
    async def get_active_context_window(
        self, 
        user_id: str, 
        session_id: str
    ) -> Optional[ContextWindow]:
        """
        Get active context window for user session
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Optional[ContextWindow]: Active context window
        """
        try:
            window_key = f"{user_id}:{session_id}"
            
            if window_key not in self.context_windows:
                # Create new context window
                window = ContextWindow(
                    window_id=f"window_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    session_id=session_id,
                    active_contexts=[],
                    max_size=self.max_context_window_size,
                    created_at=time.time(),
                    last_updated=time.time(),
                    focus_context=None,
                    background_contexts=[]
                )
                self.context_windows[window_key] = window
            
            window = self.context_windows[window_key]
            
            # Clean expired contexts from window
            await self._clean_context_window(window)
            
            return window
            
        except Exception as e:
            self.logger.error(f"Failed to get context window for {user_id}:{session_id}: {str(e)}")
            return None
    
    async def switch_context(
        self,
        user_id: str,
        session_id: str,
        target_context_id: str,
        switch_reason: str = "user_request"
    ) -> bool:
        """
        Switch to a different context
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            target_context_id: Target context ID
            switch_reason: Reason for context switch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get context window
            window = await self.get_active_context_window(user_id, session_id)
            if not window:
                return False
            
            # Verify target context exists and is accessible
            target_context = await self.get_context(target_context_id)
            if not target_context:
                return False
            
            # Record current context
            current_context = window.focus_context
            
            # Perform context switch
            window.focus_context = target_context_id
            window.last_updated = time.time()
            
            # Add to active contexts if not already present
            if target_context_id not in window.active_contexts:
                window.active_contexts.insert(0, target_context_id)
            else:
                # Move to front
                window.active_contexts.remove(target_context_id)
                window.active_contexts.insert(0, target_context_id)
            
            # Manage window size
            await self._manage_context_window_size(window)
            
            # Record context switch event
            switch_event = ContextSwitchEvent(
                event_id=f"switch_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                session_id=session_id,
                from_context=current_context,
                to_context=target_context_id,
                switch_reason=switch_reason,
                timestamp=time.time(),
                metadata={}
            )
            
            self.switch_history[f"{user_id}:{session_id}"].append(switch_event)
            
            # Update transition statistics
            if current_context:
                self.context_transitions[current_context][target_context_id] += 1
            
            # Update statistics
            self.context_stats['context_switches'] += 1
            
            self.logger.info(f"Context switched from {current_context} to {target_context_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch context: {str(e)}")
            return False
    
    async def get_context_recommendations(
        self,
        user_id: str,
        session_id: str,
        current_task: Optional[Dict[str, Any]] = None,
        max_recommendations: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Get context recommendations based on current situation
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            current_task: Optional current task information
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List[Tuple[str, float]]: List of (context_id, relevance_score) tuples
        """
        try:
            recommendations = []
            
            # Get current context window
            window = await self.get_active_context_window(user_id, session_id)
            if not window:
                return recommendations
            
            # Get user's contexts
            user_context_ids = self.user_contexts.get(user_id, set())
            session_context_ids = self.session_contexts.get(session_id, set())
            
            # Combine relevant context pools
            candidate_context_ids = user_context_ids.union(session_context_ids)
            
            # Remove already active contexts
            candidate_context_ids -= set(window.active_contexts)
            
            # Score contexts for relevance
            scored_contexts = []
            for context_id in candidate_context_ids:
                context = await self.get_context(context_id)
                if context:
                    relevance = await self._calculate_recommendation_relevance(
                        context, window, current_task
                    )
                    scored_contexts.append((context_id, relevance))
            
            # Sort by relevance and return top recommendations
            scored_contexts.sort(key=lambda x: x[1], reverse=True)
            recommendations = scored_contexts[:max_recommendations]
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to get context recommendations: {str(e)}")
            return []
    
    async def merge_contexts(
        self,
        context_ids: List[str],
        merge_strategy: str = "union"
    ) -> Optional[str]:
        """
        Merge multiple contexts into a single context
        
        Args:
            context_ids: List of context IDs to merge
            merge_strategy: Merge strategy ("union", "intersection", "weighted")
            
        Returns:
            Optional[str]: ID of merged context
        """
        try:
            if len(context_ids) < 2:
                return None
            
            # Get contexts to merge
            contexts_to_merge = []
            for context_id in context_ids:
                context = await self.get_context(context_id)
                if context:
                    contexts_to_merge.append(context)
            
            if len(contexts_to_merge) < 2:
                return None
            
            # Determine merge parameters
            merged_content = await self._merge_context_content(contexts_to_merge, merge_strategy)
            merged_type = self._determine_merged_type(contexts_to_merge)
            merged_scope = self._determine_merged_scope(contexts_to_merge)
            merged_priority = self._determine_merged_priority(contexts_to_merge)
            merged_tags = self._merge_tags(contexts_to_merge)
            
            # Create merged context
            merged_context_id = await self.create_context(
                content=merged_content,
                context_type=merged_type,
                scope=merged_scope,
                priority=merged_priority,
                tags=merged_tags
            )
            
            # Update dependencies
            for context in contexts_to_merge:
                for dep_id in context.dependencies:
                    await self._add_context_dependency(merged_context_id, dep_id)
            
            # Mark original contexts as merged (optional: could delete them)
            for context in contexts_to_merge:
                context.metadata['merged_into'] = merged_context_id
                context.metadata['merged_at'] = time.time()
            
            self.logger.info(f"Merged {len(contexts_to_merge)} contexts into {merged_context_id}")
            return merged_context_id
            
        except Exception as e:
            self.logger.error(f"Failed to merge contexts: {str(e)}")
            return None
    
    async def compress_context_window(
        self,
        user_id: str,
        session_id: str,
        compression_ratio: float = 0.5
    ) -> bool:
        """
        Compress context window by removing less relevant contexts
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            compression_ratio: Target compression ratio (0.0 to 1.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            window = await self.get_active_context_window(user_id, session_id)
            if not window:
                return False
            
            current_size = len(window.active_contexts)
            target_size = max(1, int(current_size * compression_ratio))
            
            if current_size <= target_size:
                return True  # No compression needed
            
            # Score contexts by relevance and importance
            context_scores = []
            for context_id in window.active_contexts:
                context = await self.get_context(context_id)
                if context:
                    score = await self._calculate_compression_score(context, window)
                    context_scores.append((context_id, score))
            
            # Sort by score (higher is more important to keep)
            context_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Keep top contexts
            contexts_to_keep = [ctx_id for ctx_id, score in context_scores[:target_size]]
            contexts_to_remove = [ctx_id for ctx_id, score in context_scores[target_size:]]
            
            # Update window
            window.active_contexts = contexts_to_keep
            window.background_contexts.extend(contexts_to_remove)
            window.last_updated = time.time()
            
            # Update statistics
            self.context_stats['compression_ratio'] = target_size / current_size
            
            self.logger.info(f"Compressed context window from {current_size} to {target_size} contexts")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to compress context window: {str(e)}")
            return False
    
    async def get_context_insights(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get insights about context usage and patterns
        
        Args:
            user_id: Optional user ID for user-specific insights
            session_id: Optional session ID for session-specific insights
            
        Returns:
            Dict: Context insights and analytics
        """
        try:
            insights = {
                'context_statistics': self.context_stats.copy(),
                'context_distribution': await self._get_context_distribution(),
                'popular_contexts': await self._get_popular_contexts(),
                'context_patterns': await self._analyze_context_patterns(user_id, session_id)
            }
            
            if user_id:
                insights['user_context_profile'] = await self._get_user_context_profile(user_id)
            
            if session_id:
                insights['session_context_flow'] = await self._get_session_context_flow(session_id)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to get context insights: {str(e)}")
            return {}
    
    async def optimize_contexts(self) -> Dict[str, Any]:
        """
        Optimize context storage and performance
        
        Returns:
            Dict: Optimization results
        """
        start_time = time.time()
        optimization_results = {
            'contexts_expired': 0,
            'contexts_compressed': 0,
            'contexts_merged': 0,
            'clusters_updated': 0,
            'optimization_time': 0.0
        }
        
        try:
            self.logger.info("Starting context optimization...")
            
            # Expire old contexts
            expired_count = await self._expire_old_contexts()
            optimization_results['contexts_expired'] = expired_count
            
            # Compress similar contexts
            if self.enable_context_compression:
                compressed_count = await self._compress_similar_contexts()
                optimization_results['contexts_compressed'] = compressed_count
            
            # Update semantic clusters
            if self.enable_semantic_clustering:
                clusters_updated = await self._update_semantic_clusters()
                optimization_results['clusters_updated'] = clusters_updated
            
            # Update context statistics
            await self._update_context_statistics()
            
            optimization_results['optimization_time'] = time.time() - start_time
            
            self.logger.info(f"Context optimization completed in {optimization_results['optimization_time']:.2f}s")
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Context optimization failed: {str(e)}")
            optimization_results['optimization_time'] = time.time() - start_time
            return optimization_results
    
    def _generate_context_id(self, content: Dict[str, Any], context_type: ContextType) -> str:
        """Generate unique context ID"""
        content_str = json.dumps(content, sort_keys=True)
        hash_input = f"{content_str}_{context_type.value}_{time.time()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _calculate_initial_relevance(
        self, 
        content: Dict[str, Any], 
        context_type: ContextType, 
        priority: ContextPriority
    ) -> float:
        """Calculate initial relevance score for context"""
        base_score = 0.5
        
        # Type-based scoring
        type_scores = {
            ContextType.SESSION: 0.8,
            ContextType.TASK: 0.9,
            ContextType.CONVERSATION: 0.7,
            ContextType.USER: 0.8,
            ContextType.PROJECT: 0.7,
            ContextType.ENVIRONMENT: 0.4,
            ContextType.TEMPORAL: 0.5,
            ContextType.SEMANTIC: 0.6
        }
        
        # Priority-based scoring
        priority_scores = {
            ContextPriority.CRITICAL: 1.0,
            ContextPriority.HIGH: 0.8,
            ContextPriority.MEDIUM: 0.6,
            ContextPriority.LOW: 0.4,
            ContextPriority.BACKGROUND: 0.2
        }
        
        # Content-based scoring
        content_score = min(1.0, len(str(content)) / 500)
        
        # Combine scores
        final_score = (
            type_scores.get(context_type, base_score) * 0.4 +
            priority_scores.get(priority, base_score) * 0.4 +
            content_score * 0.2
        )
        
        return max(0.0, min(1.0, final_score))
    
    async def _store_context(self, context_item: ContextItem):
        """Store context in memory"""
        self.contexts[context_item.context_id] = context_item
    
    async def _update_context_indices(self, context_item: ContextItem):
        """Update context indices"""
        context_id = context_item.context_id
        
        # Update tag index
        for tag in context_item.tags:
            self.tag_index[tag].add(context_id)
        
        # Update type index
        self.type_index[context_item.context_type].add(context_id)
        
        # Update user/session indices
        user_id = context_item.metadata.get('user_id')
        session_id = context_item.metadata.get('session_id')
        
        if user_id:
            self.user_contexts[user_id].add(context_id)
        
        if session_id:
            self.session_contexts[session_id].add(context_id)
        
        # Update main index
        self.context_index[context_id] = {
            'type': context_item.context_type,
            'scope': context_item.scope,
            'priority': context_item.priority,
            'created_at': context_item.created_at,
            'tags': context_item.tags
        }
    
    async def _add_context_dependency(self, context_id: str, dependency_id: str):
        """Add context dependency"""
        if context_id in self.contexts and dependency_id in self.contexts:
            self.contexts[context_id].dependencies.append(dependency_id)
            self.context_graph[context_id].add(dependency_id)
    
    async def _add_to_context_window(self, user_id: str, session_id: str, context_id: str):
        """Add context to active context window"""
        window = await self.get_active_context_window(user_id, session_id)
        if window and context_id not in window.active_contexts:
            window.active_contexts.insert(0, context_id)
            window.last_updated = time.time()
            
            # Manage window size
            await self._manage_context_window_size(window)
    
    async def _manage_context_window_size(self, window: ContextWindow):
        """Manage context window size"""
        if len(window.active_contexts) > window.max_size:
            # Move excess contexts to background
            excess_contexts = window.active_contexts[window.max_size:]
            window.active_contexts = window.active_contexts[:window.max_size]
            window.background_contexts.extend(excess_contexts)
    
    async def _expire_context(self, context_id: str):
        """Expire a context"""
        if context_id in self.contexts:
            context = self.contexts[context_id]
            context.metadata['expired_at'] = time.time()
            
            # Remove from active tracking
            self.context_stats['active_contexts'] -= 1
    
    async def _update_context_relevance(self, context: ContextItem):
        """Update context relevance based on access patterns"""
        # Simple relevance update based on access frequency and recency
        access_boost = min(0.1, context.access_count * 0.01)
        time_decay = max(0.0, 1.0 - ((time.time() - context.created_at) / 86400))  # Decay over 24 hours
        
        context.relevance_score = min(1.0, context.relevance_score + access_boost * time_decay)
    
    async def _get_candidate_contexts(self, query: ContextQuery) -> List[ContextItem]:
        """Get candidate contexts for search query"""
        candidates = set()
        
        # Filter by context types
        if query.context_types:
            for context_type in query.context_types:
                if context_type in self.type_index:
                    candidates.update(self.type_index[context_type])
        else:
            candidates.update(self.contexts.keys())
        
        # Filter by tags
        if query.tags:
            tag_candidates = set()
            for tag in query.tags:
                if tag in self.tag_index:
                    tag_candidates.update(self.tag_index[tag])
            candidates.intersection_update(tag_candidates)
        
        # Convert to context objects
        candidate_contexts = []
        for context_id in candidates:
            if context_id in self.contexts:
                candidate_contexts.append(self.contexts[context_id])
        
        return candidate_contexts
    
    async def _calculate_context_relevance(self, context: ContextItem, query: ContextQuery) -> float:
        """Calculate context relevance for search query"""
        relevance = 0.0
        
        # Base relevance score
        relevance += context.relevance_score * 0.3
        
        # Priority-based relevance
        priority_scores = {
            ContextPriority.CRITICAL: 1.0,
            ContextPriority.HIGH: 0.8,
            ContextPriority.MEDIUM: 0.6,
            ContextPriority.LOW: 0.4,
            ContextPriority.BACKGROUND: 0.2
        }
        relevance += priority_scores.get(context.priority, 0.5) * 0.2
        
        # Recency-based relevance
        age_hours = (time.time() - context.created_at) / 3600
        recency_score = max(0.0, 1.0 - (age_hours / 24))  # Decay over 24 hours
        relevance += recency_score * 0.2
        
        # Access frequency relevance
        access_score = min(1.0, context.access_count / 10)
        relevance += access_score * 0.1
        
        # Text similarity (if query text provided)
        if query.query_text:
            text_similarity = await self._calculate_text_similarity(context, query.query_text)
            relevance += text_similarity * 0.2
        
        return min(1.0, relevance)
    
    async def _calculate_text_similarity(self, context: ContextItem, query_text: str) -> float:
        """Calculate text similarity between context and query"""
        context_text = json.dumps(context.content).lower()
        query_text = query_text.lower()
        
        # Simple keyword matching
        query_words = set(query_text.split())
        context_words = set(context_text.split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(context_words)
        similarity = len(intersection) / len(query_words)
        
        return similarity
    
    async def _clean_context_window(self, window: ContextWindow):
        """Clean expired contexts from context window"""
        active_contexts = []
        
        for context_id in window.active_contexts:
            context = await self.get_context(context_id)
            if context:  # get_context handles expiration check
                active_contexts.append(context_id)
        
        window.active_contexts = active_contexts
        
        # Clean background contexts too
        background_contexts = []
        for context_id in window.background_contexts:
            context = await self.get_context(context_id)
            if context:
                background_contexts.append(context_id)
        
        window.background_contexts = background_contexts
    
    async def _calculate_recommendation_relevance(
        self,
        context: ContextItem,
        window: ContextWindow,
        current_task: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate relevance for context recommendation"""
        relevance = 0.0
        
        # Base context relevance
        relevance += context.relevance_score * 0.3
        
        # Task relevance
        if current_task:
            task_similarity = await self._calculate_task_similarity(context, current_task)
            relevance += task_similarity * 0.4
        
        # Historical transition probability
        if window.focus_context:
            transition_prob = self._get_transition_probability(window.focus_context, context.context_id)
            relevance += transition_prob * 0.2
        
        # Recency bonus
        age_hours = (time.time() - context.last_accessed) / 3600
        recency_bonus = max(0.0, 1.0 - (age_hours / 12))  # Bonus for recently accessed
        relevance += recency_bonus * 0.1
        
        return min(1.0, relevance)
    
    async def _calculate_task_similarity(self, context: ContextItem, task: Dict[str, Any]) -> float:
        """Calculate similarity between context and current task"""
        # Simple similarity based on task type and keywords
        task_type = task.get('type', '')
        task_keywords = set(str(task).lower().split())
        
        context_text = json.dumps(context.content).lower()
        context_keywords = set(context_text.split())
        
        # Keyword overlap
        if task_keywords:
            overlap = len(task_keywords.intersection(context_keywords))
            similarity = overlap / len(task_keywords)
        else:
            similarity = 0.0
        
        # Type-specific bonuses
        if context.context_type == ContextType.TASK and task_type:
            if task_type.lower() in context_text:
                similarity += 0.2
        
        return min(1.0, similarity)
    
    def _get_transition_probability(self, from_context: str, to_context: str) -> float:
        """Get probability of transitioning from one context to another"""
        if from_context not in self.context_transitions:
            return 0.0
        
        transitions = self.context_transitions[from_context]
        total_transitions = sum(transitions.values())
        
        if total_transitions == 0:
            return 0.0
        
        return transitions.get(to_context, 0) / total_transitions
    
    async def _merge_context_content(
        self,
        contexts: List[ContextItem],
        strategy: str
    ) -> Dict[str, Any]:
        """Merge content from multiple contexts"""
        if strategy == "union":
            merged_content = {}
            for context in contexts:
                merged_content.update(context.content)
            return merged_content
        
        elif strategy == "intersection":
            if not contexts:
                return {}
            
            merged_content = contexts[0].content.copy()
            for context in contexts[1:]:
                # Keep only common keys
                common_keys = set(merged_content.keys()).intersection(set(context.content.keys()))
                merged_content = {k: merged_content[k] for k in common_keys}
            
            return merged_content
        
        elif strategy == "weighted":
            merged_content = {}
            total_weight = sum(context.relevance_score for context in contexts)
            
            for context in contexts:
                weight = context.relevance_score / total_weight if total_weight > 0 else 1.0 / len(contexts)
                
                for key, value in context.content.items():
                    if key not in merged_content:
                        merged_content[key] = value
                    # For weighted merge, could implement value averaging for numeric values
            
            return merged_content
        
        else:
            # Default to union
            return await self._merge_context_content(contexts, "union")
    
    def _determine_merged_type(self, contexts: List[ContextItem]) -> ContextType:
        """Determine type for merged context"""
        # Use the most common type, or SEMANTIC as default
        type_counts = defaultdict(int)
        for context in contexts:
            type_counts[context.context_type] += 1
        
        if type_counts:
            return max(type_counts.items(), key=lambda x: x[1])[0]
        else:
            return ContextType.SEMANTIC
    
    def _determine_merged_scope(self, contexts: List[ContextItem]) -> ContextScope:
        """Determine scope for merged context"""
        # Use the broadest scope
        scope_hierarchy = {
            ContextScope.GLOBAL: 5,
            ContextScope.USER: 4,
            ContextScope.SESSION: 3,
            ContextScope.TASK: 2,
            ContextScope.TEMPORARY: 1
        }
        
        max_scope = max(contexts, key=lambda c: scope_hierarchy.get(c.scope, 0))
        return max_scope.scope
    
    def _determine_merged_priority(self, contexts: List[ContextItem]) -> ContextPriority:
        """Determine priority for merged context"""
        # Use the highest priority (lowest numeric value)
        min_priority = min(contexts, key=lambda c: c.priority.value)
        return min_priority.priority
    
    def _merge_tags(self, contexts: List[ContextItem]) -> List[str]:
        """Merge tags from multiple contexts"""
        all_tags = set()
        for context in contexts:
            all_tags.update(context.tags)
        return list(all_tags)
    
    async def _calculate_compression_score(self, context: ContextItem, window: ContextWindow) -> float:
        """Calculate score for context compression (higher = more important to keep)"""
        score = 0.0
        
        # Base relevance
        score += context.relevance_score * 0.4
        
        # Priority importance
        priority_scores = {
            ContextPriority.CRITICAL: 1.0,
            ContextPriority.HIGH: 0.8,
            ContextPriority.MEDIUM: 0.6,
            ContextPriority.LOW: 0.4,
            ContextPriority.BACKGROUND: 0.2
        }
        score += priority_scores.get(context.priority, 0.5) * 0.3
        
        # Access frequency
        access_score = min(1.0, context.access_count / 10)
        score += access_score * 0.2
        
        # Focus context bonus
        if context.context_id == window.focus_context:
            score += 0.1
        
        return score
    
    async def _get_context_distribution(self) -> Dict[str, int]:
        """Get distribution of contexts by type"""
        distribution = defaultdict(int)
        
        for context in self.contexts.values():
            distribution[context.context_type.value] += 1
        
        return dict(distribution)
    
    async def _get_popular_contexts(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular contexts by access count"""
        context_popularity = [
            (context.context_id, context.access_count)
            for context in self.contexts.values()
        ]
        
        context_popularity.sort(key=lambda x: x[1], reverse=True)
        return context_popularity[:limit]
    
    async def _analyze_context_patterns(
        self,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze context usage patterns"""
        patterns = {}
        
        # Analyze switch patterns
        if user_id and session_id:
            switch_key = f"{user_id}:{session_id}"
            if switch_key in self.switch_history:
                switches = self.switch_history[switch_key]
                patterns['switch_frequency'] = len(switches)
                patterns['average_context_duration'] = self._calculate_average_context_duration(switches)
                patterns['most_common_switches'] = self._get_common_switch_patterns(switches)
        
        return patterns
    
    def _calculate_average_context_duration(self, switches: List[ContextSwitchEvent]) -> float:
        """Calculate average duration spent in each context"""
        if len(switches) < 2:
            return 0.0
        
        durations = []
        for i in range(len(switches) - 1):
            duration = switches[i + 1].timestamp - switches[i].timestamp
            durations.append(duration)
        
        return sum(durations) / len(durations) if durations else 0.0
    
    def _get_common_switch_patterns(self, switches: List[ContextSwitchEvent]) -> List[Tuple[str, str, int]]:
        """Get common context switch patterns"""
        patterns = defaultdict(int)
        
        for i in range(len(switches) - 1):
            from_ctx = switches[i].to_context
            to_ctx = switches[i + 1].to_context
            patterns[(from_ctx, to_ctx)] += 1
        
        # Return top 5 patterns
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        return [(from_ctx, to_ctx, count) for (from_ctx, to_ctx), count in sorted_patterns[:5]]
    
    async def _get_user_context_profile(self, user_id: str) -> Dict[str, Any]:
        """Get context profile for specific user"""
        user_context_ids = self.user_contexts.get(user_id, set())
        
        if not user_context_ids:
            return {}
        
        user_contexts = [self.contexts[ctx_id] for ctx_id in user_context_ids if ctx_id in self.contexts]
        
        # Analyze user's context preferences
        type_distribution = defaultdict(int)
        priority_distribution = defaultdict(int)
        total_access = 0
        
        for context in user_contexts:
            type_distribution[context.context_type.value] += 1
            priority_distribution[context.priority.value] += 1
            total_access += context.access_count
        
        return {
            'total_contexts': len(user_contexts),
            'total_access_count': total_access,
            'average_access_per_context': total_access / len(user_contexts) if user_contexts else 0,
            'type_distribution': dict(type_distribution),
            'priority_distribution': dict(priority_distribution),
            'most_accessed_context': max(user_contexts, key=lambda c: c.access_count).context_id if user_contexts else None
        }
    
    async def _get_session_context_flow(self, session_id: str) -> Dict[str, Any]:
        """Get context flow for specific session"""
        session_context_ids = self.session_contexts.get(session_id, set())
        
        if not session_context_ids:
            return {}
        
        session_contexts = [self.contexts[ctx_id] for ctx_id in session_context_ids if ctx_id in self.contexts]
        
        # Sort by creation time to show flow
        session_contexts.sort(key=lambda c: c.created_at)
        
        context_flow = [
            {
                'context_id': context.context_id,
                'type': context.context_type.value,
                'created_at': context.created_at,
                'access_count': context.access_count
            }
            for context in session_contexts
        ]
        
        return {
            'total_contexts': len(session_contexts),
            'context_flow': context_flow,
            'session_duration': session_contexts[-1].created_at - session_contexts[0].created_at if len(session_contexts) > 1 else 0
        }
    
    async def _expire_old_contexts(self) -> int:
        """Expire old contexts"""
        expired_count = 0
        current_time = time.time()
        
        for context in list(self.contexts.values()):
            if context.expires_at and current_time > context.expires_at:
                await self._expire_context(context.context_id)
                expired_count += 1
        
        return expired_count
    
    async def _compress_similar_contexts(self) -> int:
        """Compress similar contexts"""
        # This would implement context compression logic
        # For now, return 0 as placeholder
        return 0
    
    async def _update_semantic_clusters(self) -> int:
        """Update semantic context clusters"""
        # This would implement semantic clustering logic
        # For now, return 0 as placeholder
        return 0
    
    async def _update_context_statistics(self):
        """Update context statistics"""
        active_count = sum(
            1 for context in self.contexts.values()
            if not (context.expires_at and time.time() > context.expires_at)
        )
        
        self.context_stats['active_contexts'] = active_count
        
        # Update average window size
        if self.context_windows:
            total_window_size = sum(len(window.active_contexts) for window in self.context_windows.values())
            self.context_stats['average_window_size'] = total_window_size / len(self.context_windows)
    
    def _initialize_default_contexts(self):
        """Initialize default system contexts"""
        # This would create default system contexts
        pass

