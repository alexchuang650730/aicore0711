"""
Memory Engine - Core AI Memory System for PowerAutomation 4.0

This module provides the core memory engine that enables AI systems to:
- Store and retrieve memories across sessions
- Learn from user interactions and preferences
- Maintain context-aware memory hierarchies
- Optimize memory usage and performance
- Provide personalized AI experiences
"""

import asyncio
import json
import time
import uuid
import hashlib
import sqlite3
import pickle
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict


class MemoryType(Enum):
    """Types of memories in the system"""
    EPISODIC = "episodic"          # Specific events and experiences
    SEMANTIC = "semantic"          # Facts and knowledge
    PROCEDURAL = "procedural"      # Skills and procedures
    WORKING = "working"            # Temporary working memory
    EMOTIONAL = "emotional"        # Emotional associations
    CONTEXTUAL = "contextual"      # Context-specific memories
    PREFERENCE = "preference"      # User preferences and patterns


class MemoryPriority(Enum):
    """Memory priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    ARCHIVE = 5


class MemoryStatus(Enum):
    """Memory status states"""
    ACTIVE = "active"
    DORMANT = "dormant"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Memory:
    """Core memory data structure"""
    memory_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: float
    last_accessed: float
    access_count: int
    priority: MemoryPriority
    status: MemoryStatus
    tags: List[str]
    associations: List[str]  # IDs of related memories
    embedding: Optional[List[float]] = None
    decay_factor: float = 1.0
    importance_score: float = 0.5


@dataclass
class MemoryQuery:
    """Memory query structure"""
    query_text: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    time_range: Optional[Tuple[float, float]] = None
    priority_min: Optional[MemoryPriority] = None
    limit: int = 10
    include_associations: bool = True
    similarity_threshold: float = 0.7


@dataclass
class MemorySearchResult:
    """Memory search result"""
    memories: List[Memory]
    total_count: int
    search_time: float
    relevance_scores: List[float]
    query_metadata: Dict[str, Any]


class MemoryEngine:
    """
    Memory Engine - Core AI Memory System
    
    Provides comprehensive memory management capabilities for AI systems,
    enabling persistent learning, personalization, and context awareness.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Memory Engine
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Memory configuration
        self.memory_db_path = self.config.get('memory_db_path', 'memory_engine.db')
        self.max_working_memory = self.config.get('max_working_memory', 100)
        self.max_total_memories = self.config.get('max_total_memories', 10000)
        self.enable_embeddings = self.config.get('enable_embeddings', True)
        self.enable_decay = self.config.get('enable_decay', True)
        
        # Memory storage
        self.memories = {}  # In-memory cache
        self.working_memory = {}  # Active working memory
        self.memory_index = {}  # Fast lookup index
        self.tag_index = defaultdict(set)  # Tag-based index
        self.type_index = defaultdict(set)  # Type-based index
        
        # Memory statistics
        self.memory_stats = {
            'total_memories': 0,
            'memories_by_type': defaultdict(int),
            'memories_by_priority': defaultdict(int),
            'total_accesses': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_retrieval_time': 0.0
        }
        
        # Memory optimization
        self.last_optimization = time.time()
        self.optimization_interval = 3600.0  # 1 hour
        
        # Initialize database
        self._initialize_database()
        
        # Load existing memories
        asyncio.create_task(self._load_memories_from_db())
        
        self.logger.info("MemoryEngine initialized")
    
    async def store_memory(
        self, 
        content: Dict[str, Any], 
        memory_type: MemoryType,
        tags: Optional[List[str]] = None,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a new memory
        
        Args:
            content: Memory content
            memory_type: Type of memory
            tags: Optional tags for categorization
            priority: Memory priority level
            metadata: Optional metadata
            
        Returns:
            str: Memory ID
        """
        start_time = time.time()
        
        try:
            # Generate memory ID
            memory_id = self._generate_memory_id(content, memory_type)
            
            # Create memory object
            memory = Memory(
                memory_id=memory_id,
                memory_type=memory_type,
                content=content,
                metadata=metadata or {},
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                priority=priority,
                status=MemoryStatus.ACTIVE,
                tags=tags or [],
                associations=[],
                decay_factor=1.0,
                importance_score=self._calculate_importance_score(content, memory_type, priority)
            )
            
            # Generate embedding if enabled
            if self.enable_embeddings:
                memory.embedding = await self._generate_embedding(content)
            
            # Store in cache and database
            await self._store_memory_internal(memory)
            
            # Update indices
            await self._update_indices(memory)
            
            # Find and create associations
            await self._create_associations(memory)
            
            # Manage working memory
            if memory_type == MemoryType.WORKING:
                await self._manage_working_memory(memory)
            
            # Update statistics
            self._update_memory_stats('store', time.time() - start_time)
            
            self.logger.info(f"Memory stored: {memory_id} ({memory_type.value})")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {str(e)}")
            raise
    
    async def retrieve_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve a specific memory by ID
        
        Args:
            memory_id: Memory ID to retrieve
            
        Returns:
            Optional[Memory]: Retrieved memory or None
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                await self._update_memory_access(memory)
                self.memory_stats['cache_hits'] += 1
                self._update_memory_stats('retrieve', time.time() - start_time)
                return memory
            
            # Load from database
            memory = await self._load_memory_from_db(memory_id)
            if memory:
                # Add to cache
                self.memories[memory_id] = memory
                await self._update_memory_access(memory)
                self.memory_stats['cache_misses'] += 1
            
            self._update_memory_stats('retrieve', time.time() - start_time)
            return memory
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve memory {memory_id}: {str(e)}")
            return None
    
    async def search_memories(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Search memories based on query criteria
        
        Args:
            query: Memory query parameters
            
        Returns:
            MemorySearchResult: Search results
        """
        start_time = time.time()
        
        try:
            # Get candidate memories
            candidates = await self._get_candidate_memories(query)
            
            # Score and rank memories
            scored_memories = await self._score_memories(candidates, query)
            
            # Apply filters and limits
            filtered_memories = await self._filter_memories(scored_memories, query)
            
            # Sort by relevance
            sorted_memories = sorted(
                filtered_memories, 
                key=lambda x: x[1], 
                reverse=True
            )[:query.limit]
            
            # Extract memories and scores
            memories = [memory for memory, score in sorted_memories]
            scores = [score for memory, score in sorted_memories]
            
            # Update access counts
            for memory in memories:
                await self._update_memory_access(memory)
            
            search_time = time.time() - start_time
            
            result = MemorySearchResult(
                memories=memories,
                total_count=len(candidates),
                search_time=search_time,
                relevance_scores=scores,
                query_metadata={
                    'query_text': query.query_text,
                    'memory_types': [t.value for t in query.memory_types] if query.memory_types else None,
                    'tags': query.tags,
                    'candidates_count': len(candidates),
                    'filtered_count': len(filtered_memories)
                }
            )
            
            self._update_memory_stats('search', search_time)
            return result
            
        except Exception as e:
            self.logger.error(f"Memory search failed: {str(e)}")
            return MemorySearchResult([], 0, 0.0, [], {})
    
    async def update_memory(
        self, 
        memory_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing memory
        
        Args:
            memory_id: Memory ID to update
            updates: Updates to apply
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            memory = await self.retrieve_memory(memory_id)
            if not memory:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            
            # Update last accessed time
            memory.last_accessed = time.time()
            
            # Regenerate embedding if content changed
            if 'content' in updates and self.enable_embeddings:
                memory.embedding = await self._generate_embedding(memory.content)
            
            # Update in database
            await self._update_memory_in_db(memory)
            
            # Update indices
            await self._update_indices(memory)
            
            self.logger.info(f"Memory updated: {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update memory {memory_id}: {str(e)}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory
        
        Args:
            memory_id: Memory ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove from cache
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                
                # Remove from indices
                await self._remove_from_indices(memory)
                
                # Remove from cache
                del self.memories[memory_id]
            
            # Remove from database
            await self._delete_memory_from_db(memory_id)
            
            # Update statistics
            self.memory_stats['total_memories'] -= 1
            
            self.logger.info(f"Memory deleted: {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete memory {memory_id}: {str(e)}")
            return False
    
    async def get_related_memories(
        self, 
        memory_id: str, 
        max_results: int = 5
    ) -> List[Memory]:
        """
        Get memories related to a specific memory
        
        Args:
            memory_id: Source memory ID
            max_results: Maximum number of results
            
        Returns:
            List[Memory]: Related memories
        """
        try:
            source_memory = await self.retrieve_memory(memory_id)
            if not source_memory:
                return []
            
            related_memories = []
            
            # Get directly associated memories
            for assoc_id in source_memory.associations:
                assoc_memory = await self.retrieve_memory(assoc_id)
                if assoc_memory:
                    related_memories.append(assoc_memory)
            
            # Get memories with similar tags
            tag_related = await self._find_memories_by_tags(
                source_memory.tags, 
                exclude_id=memory_id
            )
            related_memories.extend(tag_related[:max_results - len(related_memories)])
            
            # Get memories with similar content (if embeddings enabled)
            if self.enable_embeddings and source_memory.embedding:
                similar_memories = await self._find_similar_memories(
                    source_memory.embedding,
                    exclude_id=memory_id,
                    max_results=max_results - len(related_memories)
                )
                related_memories.extend(similar_memories)
            
            # Remove duplicates and limit results
            seen_ids = set()
            unique_memories = []
            for memory in related_memories:
                if memory.memory_id not in seen_ids:
                    seen_ids.add(memory.memory_id)
                    unique_memories.append(memory)
                    if len(unique_memories) >= max_results:
                        break
            
            return unique_memories
            
        except Exception as e:
            self.logger.error(f"Failed to get related memories for {memory_id}: {str(e)}")
            return []
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """
        Optimize memory storage and performance
        
        Returns:
            Dict: Optimization results
        """
        start_time = time.time()
        optimization_results = {
            'memories_archived': 0,
            'memories_deleted': 0,
            'associations_updated': 0,
            'cache_optimized': False,
            'optimization_time': 0.0
        }
        
        try:
            self.logger.info("Starting memory optimization...")
            
            # Apply memory decay
            if self.enable_decay:
                await self._apply_memory_decay()
            
            # Archive old, low-priority memories
            archived_count = await self._archive_old_memories()
            optimization_results['memories_archived'] = archived_count
            
            # Delete expired memories
            deleted_count = await self._delete_expired_memories()
            optimization_results['memories_deleted'] = deleted_count
            
            # Update associations
            associations_updated = await self._update_all_associations()
            optimization_results['associations_updated'] = associations_updated
            
            # Optimize cache
            cache_optimized = await self._optimize_cache()
            optimization_results['cache_optimized'] = cache_optimized
            
            # Update last optimization time
            self.last_optimization = time.time()
            optimization_results['optimization_time'] = time.time() - start_time
            
            self.logger.info(f"Memory optimization completed in {optimization_results['optimization_time']:.2f}s")
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {str(e)}")
            optimization_results['optimization_time'] = time.time() - start_time
            return optimization_results
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive memory statistics
        
        Returns:
            Dict: Memory statistics
        """
        stats = self.memory_stats.copy()
        
        # Add current state information
        stats.update({
            'cache_size': len(self.memories),
            'working_memory_size': len(self.working_memory),
            'total_tags': len(self.tag_index),
            'memory_types_count': len(self.type_index),
            'last_optimization': self.last_optimization,
            'cache_hit_rate': (
                self.memory_stats['cache_hits'] / 
                max(1, self.memory_stats['cache_hits'] + self.memory_stats['cache_misses'])
            )
        })
        
        # Add memory distribution by type
        for memory_type in MemoryType:
            stats[f'memories_{memory_type.value}'] = len(self.type_index.get(memory_type, set()))
        
        # Add memory distribution by priority
        for priority in MemoryPriority:
            count = sum(1 for memory in self.memories.values() if memory.priority == priority)
            stats[f'memories_priority_{priority.value}'] = count
        
        return stats
    
    def _generate_memory_id(self, content: Dict[str, Any], memory_type: MemoryType) -> str:
        """Generate unique memory ID"""
        content_str = json.dumps(content, sort_keys=True)
        hash_input = f"{content_str}_{memory_type.value}_{time.time()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _calculate_importance_score(
        self, 
        content: Dict[str, Any], 
        memory_type: MemoryType, 
        priority: MemoryPriority
    ) -> float:
        """Calculate importance score for memory"""
        base_score = 0.5
        
        # Type-based scoring
        type_scores = {
            MemoryType.CRITICAL: 0.9,
            MemoryType.PREFERENCE: 0.8,
            MemoryType.SEMANTIC: 0.7,
            MemoryType.EPISODIC: 0.6,
            MemoryType.PROCEDURAL: 0.6,
            MemoryType.CONTEXTUAL: 0.5,
            MemoryType.EMOTIONAL: 0.4,
            MemoryType.WORKING: 0.3
        }
        
        # Priority-based scoring
        priority_scores = {
            MemoryPriority.CRITICAL: 1.0,
            MemoryPriority.HIGH: 0.8,
            MemoryPriority.MEDIUM: 0.6,
            MemoryPriority.LOW: 0.4,
            MemoryPriority.ARCHIVE: 0.2
        }
        
        # Content-based scoring
        content_score = min(1.0, len(str(content)) / 1000)  # Longer content = higher score
        
        # Combine scores
        final_score = (
            type_scores.get(memory_type, base_score) * 0.4 +
            priority_scores.get(priority, base_score) * 0.4 +
            content_score * 0.2
        )
        
        return max(0.0, min(1.0, final_score))
    
    async def _generate_embedding(self, content: Dict[str, Any]) -> List[float]:
        """Generate embedding for memory content"""
        # Simplified embedding generation
        # In a real implementation, this would use a proper embedding model
        content_str = json.dumps(content, sort_keys=True)
        
        # Create a simple hash-based embedding
        hash_bytes = hashlib.sha256(content_str.encode()).digest()
        embedding = [float(b) / 255.0 for b in hash_bytes[:64]]  # 64-dimensional embedding
        
        return embedding
    
    async def _store_memory_internal(self, memory: Memory):
        """Store memory in cache and database"""
        # Store in cache
        self.memories[memory.memory_id] = memory
        
        # Store in database
        await self._save_memory_to_db(memory)
        
        # Update statistics
        self.memory_stats['total_memories'] += 1
        self.memory_stats['memories_by_type'][memory.memory_type] += 1
        self.memory_stats['memories_by_priority'][memory.priority] += 1
    
    async def _update_indices(self, memory: Memory):
        """Update memory indices"""
        # Update tag index
        for tag in memory.tags:
            self.tag_index[tag].add(memory.memory_id)
        
        # Update type index
        self.type_index[memory.memory_type].add(memory.memory_id)
        
        # Update main index
        self.memory_index[memory.memory_id] = {
            'type': memory.memory_type,
            'tags': memory.tags,
            'created_at': memory.created_at,
            'priority': memory.priority,
            'importance_score': memory.importance_score
        }
    
    async def _remove_from_indices(self, memory: Memory):
        """Remove memory from indices"""
        # Remove from tag index
        for tag in memory.tags:
            self.tag_index[tag].discard(memory.memory_id)
            if not self.tag_index[tag]:
                del self.tag_index[tag]
        
        # Remove from type index
        self.type_index[memory.memory_type].discard(memory.memory_id)
        
        # Remove from main index
        self.memory_index.pop(memory.memory_id, None)
    
    async def _create_associations(self, memory: Memory):
        """Create associations with related memories"""
        # Find memories with similar tags
        similar_memories = []
        for tag in memory.tags:
            if tag in self.tag_index:
                for memory_id in self.tag_index[tag]:
                    if memory_id != memory.memory_id:
                        similar_memories.append(memory_id)
        
        # Add associations (limit to top 5)
        memory.associations = list(set(similar_memories))[:5]
        
        # Update reverse associations
        for assoc_id in memory.associations:
            assoc_memory = await self.retrieve_memory(assoc_id)
            if assoc_memory and memory.memory_id not in assoc_memory.associations:
                assoc_memory.associations.append(memory.memory_id)
                await self._update_memory_in_db(assoc_memory)
    
    async def _manage_working_memory(self, memory: Memory):
        """Manage working memory capacity"""
        self.working_memory[memory.memory_id] = memory
        
        # Remove oldest working memories if capacity exceeded
        if len(self.working_memory) > self.max_working_memory:
            # Sort by last accessed time
            sorted_memories = sorted(
                self.working_memory.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove oldest memories
            for memory_id, old_memory in sorted_memories[:-self.max_working_memory]:
                del self.working_memory[memory_id]
                # Convert to regular memory or archive
                old_memory.memory_type = MemoryType.EPISODIC
                old_memory.priority = MemoryPriority.LOW
                await self._update_memory_in_db(old_memory)
    
    async def _update_memory_access(self, memory: Memory):
        """Update memory access statistics"""
        memory.last_accessed = time.time()
        memory.access_count += 1
        
        # Update importance score based on access pattern
        access_boost = min(0.1, memory.access_count * 0.01)
        memory.importance_score = min(1.0, memory.importance_score + access_boost)
        
        # Update in database
        await self._update_memory_in_db(memory)
        
        # Update statistics
        self.memory_stats['total_accesses'] += 1
    
    def _update_memory_stats(self, operation: str, duration: float):
        """Update memory operation statistics"""
        # Update average retrieval time
        if operation in ['retrieve', 'search']:
            current_avg = self.memory_stats['average_retrieval_time']
            total_ops = self.memory_stats['total_accesses']
            if total_ops > 0:
                self.memory_stats['average_retrieval_time'] = (
                    (current_avg * (total_ops - 1) + duration) / total_ops
                )
            else:
                self.memory_stats['average_retrieval_time'] = duration
    
    def _initialize_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            # Create memories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    tags TEXT,
                    associations TEXT,
                    embedding BLOB,
                    decay_factor REAL DEFAULT 1.0,
                    importance_score REAL DEFAULT 0.5
                )
            ''')
            
            # Create indices for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_accessed ON memories(last_accessed)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON memories(priority)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance_score)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Memory database initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def _load_memories_from_db(self):
        """Load existing memories from database"""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM memories WHERE status = ?', (MemoryStatus.ACTIVE.value,))
            total_count = cursor.fetchone()[0]
            
            # Load recent and important memories into cache
            cursor.execute('''
                SELECT * FROM memories 
                WHERE status = ? 
                ORDER BY importance_score DESC, last_accessed DESC 
                LIMIT ?
            ''', (MemoryStatus.ACTIVE.value, min(1000, total_count)))
            
            rows = cursor.fetchall()
            
            for row in rows:
                memory = self._row_to_memory(row)
                self.memories[memory.memory_id] = memory
                await self._update_indices(memory)
                
                if memory.memory_type == MemoryType.WORKING:
                    self.working_memory[memory.memory_id] = memory
            
            conn.close()
            
            self.logger.info(f"Loaded {len(rows)} memories from database")
            
        except Exception as e:
            self.logger.error(f"Failed to load memories from database: {str(e)}")
    
    async def _save_memory_to_db(self, memory: Memory):
        """Save memory to database"""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', self._memory_to_row(memory))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to save memory to database: {str(e)}")
    
    async def _load_memory_from_db(self, memory_id: str) -> Optional[Memory]:
        """Load specific memory from database"""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM memories WHERE memory_id = ?', (memory_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return self._row_to_memory(row)
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load memory from database: {str(e)}")
            return None
    
    async def _update_memory_in_db(self, memory: Memory):
        """Update memory in database"""
        await self._save_memory_to_db(memory)
    
    async def _delete_memory_from_db(self, memory_id: str):
        """Delete memory from database"""
        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM memories WHERE memory_id = ?', (memory_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to delete memory from database: {str(e)}")
    
    def _memory_to_row(self, memory: Memory) -> tuple:
        """Convert memory object to database row"""
        return (
            memory.memory_id,
            memory.memory_type.value,
            json.dumps(memory.content),
            json.dumps(memory.metadata),
            memory.created_at,
            memory.last_accessed,
            memory.access_count,
            memory.priority.value,
            memory.status.value,
            json.dumps(memory.tags),
            json.dumps(memory.associations),
            pickle.dumps(memory.embedding) if memory.embedding else None,
            memory.decay_factor,
            memory.importance_score
        )
    
    def _row_to_memory(self, row: tuple) -> Memory:
        """Convert database row to memory object"""
        return Memory(
            memory_id=row[0],
            memory_type=MemoryType(row[1]),
            content=json.loads(row[2]),
            metadata=json.loads(row[3]),
            created_at=row[4],
            last_accessed=row[5],
            access_count=row[6],
            priority=MemoryPriority(row[7]),
            status=MemoryStatus(row[8]),
            tags=json.loads(row[9]),
            associations=json.loads(row[10]),
            embedding=pickle.loads(row[11]) if row[11] else None,
            decay_factor=row[12],
            importance_score=row[13]
        )
    
    async def _get_candidate_memories(self, query: MemoryQuery) -> List[Memory]:
        """Get candidate memories for search query"""
        candidates = set()
        
        # Filter by memory types
        if query.memory_types:
            for memory_type in query.memory_types:
                if memory_type in self.type_index:
                    candidates.update(self.type_index[memory_type])
        else:
            # Include all memories
            candidates.update(self.memories.keys())
        
        # Filter by tags
        if query.tags:
            tag_candidates = set()
            for tag in query.tags:
                if tag in self.tag_index:
                    tag_candidates.update(self.tag_index[tag])
            candidates.intersection_update(tag_candidates)
        
        # Convert to memory objects
        candidate_memories = []
        for memory_id in candidates:
            memory = await self.retrieve_memory(memory_id)
            if memory:
                candidate_memories.append(memory)
        
        return candidate_memories
    
    async def _score_memories(self, memories: List[Memory], query: MemoryQuery) -> List[Tuple[Memory, float]]:
        """Score memories based on query relevance"""
        scored_memories = []
        
        for memory in memories:
            score = 0.0
            
            # Base importance score
            score += memory.importance_score * 0.3
            
            # Recency score
            age_days = (time.time() - memory.created_at) / 86400
            recency_score = max(0.0, 1.0 - (age_days / 30))  # Decay over 30 days
            score += recency_score * 0.2
            
            # Access frequency score
            access_score = min(1.0, memory.access_count / 10)
            score += access_score * 0.2
            
            # Text similarity score (if query text provided)
            if query.query_text:
                text_score = await self._calculate_text_similarity(memory, query.query_text)
                score += text_score * 0.3
            
            scored_memories.append((memory, score))
        
        return scored_memories
    
    async def _calculate_text_similarity(self, memory: Memory, query_text: str) -> float:
        """Calculate text similarity between memory and query"""
        # Simplified text similarity calculation
        memory_text = json.dumps(memory.content).lower()
        query_text = query_text.lower()
        
        # Simple keyword matching
        query_words = set(query_text.split())
        memory_words = set(memory_text.split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(memory_words)
        similarity = len(intersection) / len(query_words)
        
        return similarity
    
    async def _filter_memories(self, scored_memories: List[Tuple[Memory, float]], query: MemoryQuery) -> List[Tuple[Memory, float]]:
        """Apply additional filters to scored memories"""
        filtered = []
        
        for memory, score in scored_memories:
            # Time range filter
            if query.time_range:
                start_time, end_time = query.time_range
                if not (start_time <= memory.created_at <= end_time):
                    continue
            
            # Priority filter
            if query.priority_min:
                if memory.priority.value > query.priority_min.value:
                    continue
            
            # Similarity threshold
            if score < query.similarity_threshold:
                continue
            
            filtered.append((memory, score))
        
        return filtered
    
    async def _find_memories_by_tags(self, tags: List[str], exclude_id: str = None) -> List[Memory]:
        """Find memories with similar tags"""
        candidate_ids = set()
        
        for tag in tags:
            if tag in self.tag_index:
                candidate_ids.update(self.tag_index[tag])
        
        if exclude_id:
            candidate_ids.discard(exclude_id)
        
        memories = []
        for memory_id in candidate_ids:
            memory = await self.retrieve_memory(memory_id)
            if memory:
                memories.append(memory)
        
        return memories
    
    async def _find_similar_memories(self, embedding: List[float], exclude_id: str = None, max_results: int = 5) -> List[Memory]:
        """Find memories with similar embeddings"""
        if not self.enable_embeddings:
            return []
        
        similar_memories = []
        
        for memory in self.memories.values():
            if memory.memory_id == exclude_id or not memory.embedding:
                continue
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(embedding, memory.embedding)
            if similarity > 0.7:  # Similarity threshold
                similar_memories.append((memory, similarity))
        
        # Sort by similarity and return top results
        similar_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, similarity in similar_memories[:max_results]]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def _apply_memory_decay(self):
        """Apply decay to memories based on time and access patterns"""
        current_time = time.time()
        
        for memory in self.memories.values():
            # Calculate decay based on age and access pattern
            age_days = (current_time - memory.created_at) / 86400
            time_since_access = (current_time - memory.last_accessed) / 86400
            
            # Decay factor calculation
            age_decay = max(0.1, 1.0 - (age_days / 365))  # Decay over 1 year
            access_decay = max(0.1, 1.0 - (time_since_access / 30))  # Decay if not accessed for 30 days
            
            memory.decay_factor = (age_decay + access_decay) / 2
            memory.importance_score *= memory.decay_factor
            
            # Update in database
            await self._update_memory_in_db(memory)
    
    async def _archive_old_memories(self) -> int:
        """Archive old, low-priority memories"""
        archived_count = 0
        current_time = time.time()
        
        for memory in list(self.memories.values()):
            # Archive criteria
            age_days = (current_time - memory.created_at) / 86400
            is_old = age_days > 90  # Older than 90 days
            is_low_priority = memory.priority in [MemoryPriority.LOW, MemoryPriority.ARCHIVE]
            is_rarely_accessed = memory.access_count < 3
            
            if is_old and is_low_priority and is_rarely_accessed:
                memory.status = MemoryStatus.ARCHIVED
                await self._update_memory_in_db(memory)
                archived_count += 1
        
        return archived_count
    
    async def _delete_expired_memories(self) -> int:
        """Delete expired memories"""
        deleted_count = 0
        current_time = time.time()
        
        for memory in list(self.memories.values()):
            # Delete criteria
            age_days = (current_time - memory.created_at) / 86400
            is_very_old = age_days > 365  # Older than 1 year
            is_archive_priority = memory.priority == MemoryPriority.ARCHIVE
            is_very_low_importance = memory.importance_score < 0.1
            
            if is_very_old and is_archive_priority and is_very_low_importance:
                await self.delete_memory(memory.memory_id)
                deleted_count += 1
        
        return deleted_count
    
    async def _update_all_associations(self) -> int:
        """Update associations for all memories"""
        updated_count = 0
        
        for memory in self.memories.values():
            old_associations = memory.associations.copy()
            await self._create_associations(memory)
            
            if memory.associations != old_associations:
                await self._update_memory_in_db(memory)
                updated_count += 1
        
        return updated_count
    
    async def _optimize_cache(self) -> bool:
        """Optimize memory cache"""
        try:
            # Remove least recently used memories if cache is too large
            if len(self.memories) > self.max_total_memories:
                # Sort by last accessed time
                sorted_memories = sorted(
                    self.memories.items(),
                    key=lambda x: x[1].last_accessed
                )
                
                # Remove oldest memories from cache (but keep in database)
                memories_to_remove = len(self.memories) - self.max_total_memories
                for memory_id, memory in sorted_memories[:memories_to_remove]:
                    if memory.memory_type != MemoryType.WORKING:  # Keep working memory
                        del self.memories[memory_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache optimization failed: {str(e)}")
            return False

