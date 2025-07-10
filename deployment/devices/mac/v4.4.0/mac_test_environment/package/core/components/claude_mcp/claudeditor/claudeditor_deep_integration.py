#!/usr/bin/env python3
"""
ClaudEditor深度集成系统

为PowerAutomation 4.1提供完整的ClaudEditor智能编程助手深度集成。
实现多AI模型协调、智能代码生成、实时协作、性能监控等核心功能。

主要功能：
- 多AI模型智能协调 (Claude + Gemini)
- 智能代码生成和优化
- 实时协作和同步
- 性能监控和分析
- 智能工具推荐
- 代码质量评估
- 自动化测试生成
- 部署和运维支持

技术特色：
- AI驱动的编程助手
- 多模型协同工作
- 实时性能优化
- 智能错误检测
- 自动化工作流

作者: PowerAutomation Team
版本: 4.1.0
日期: 2025-01-07
"""

import asyncio
import json
import uuid
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import pickle
import hashlib
import sqlite3
from collections import defaultdict, deque
import threading
import math
import random
from abc import ABC, abstractmethod
import websockets
import aiohttp
import ast
import re

logger = logging.getLogger(__name__)

class AIModel(Enum):
    """AI模型类型"""
    CLAUDE = "claude"
    GEMINI = "gemini"
    GPT = "gpt"
    LOCAL = "local"

class TaskType(Enum):
    """任务类型"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_OPTIMIZATION = "code_optimization"
    BUG_FIXING = "bug_fixing"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    ANALYSIS = "analysis"

class TaskPriority(Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CodeQuality(Enum):
    """代码质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

@dataclass
class AITask:
    """AI任务"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    status: TaskStatus
    user_id: str
    project_id: str
    description: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    assigned_model: Optional[AIModel] = None
    estimated_duration: Optional[int] = None  # 秒
    actual_duration: Optional[int] = None
    quality_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeAnalysis:
    """代码分析结果"""
    analysis_id: str
    code_content: str
    language: str
    quality_score: float
    complexity_score: float
    maintainability_score: float
    performance_score: float
    security_score: float
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    analysis_time: datetime = field(default_factory=datetime.now)

@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    project_id: str
    participants: List[str]
    session_type: str
    status: str
    shared_context: Dict[str, Any] = field(default_factory=dict)
    message_history: List[Dict[str, Any]] = field(default_factory=list)
    code_changes: List[Dict[str, Any]] = field(default_factory=list)
    ai_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    metric_id: str
    task_id: str
    model_used: AIModel
    response_time: float
    accuracy_score: float
    user_satisfaction: float
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    error_rate: float = 0.0
    throughput: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SmartRecommendation:
    """智能推荐"""
    recommendation_id: str
    user_id: str
    recommendation_type: str
    title: str
    description: str
    confidence_score: float
    context: Dict[str, Any] = field(default_factory=dict)
    action_data: Dict[str, Any] = field(default_factory=dict)
    is_accepted: Optional[bool] = None
    feedback_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)

class ClaudEditorDeepIntegration:
    """ClaudEditor深度集成系统"""
    
    def __init__(self, config_path: str = "./claudeditor_integration_config.json"):
        """初始化ClaudEditor深度集成"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # AI模型管理
        self.ai_models: Dict[AIModel, Any] = {}
        self.model_performance: Dict[AIModel, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.model_load_balancer = ModelLoadBalancer(self.config)
        
        # 任务管理
        self.active_tasks: Dict[str, AITask] = {}
        self.task_queue: deque = deque()
        self.task_history: List[AITask] = []
        self.task_executor = TaskExecutor(self.config)
        
        # 代码分析
        self.code_analyzer = CodeAnalyzer(self.config)
        self.analysis_cache: Dict[str, CodeAnalysis] = {}
        
        # 协作系统
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}
        self.real_time_sync = RealTimeSync(self.config)
        
        # 性能监控
        self.performance_metrics: List[PerformanceMetrics] = []
        self.performance_monitor = PerformanceMonitor(self.config)
        
        # 智能推荐
        self.recommendation_engine = RecommendationEngine(self.config)
        self.user_recommendations: Dict[str, List[SmartRecommendation]] = defaultdict(list)
        
        # 工具集成
        self.integrated_tools: Dict[str, Any] = {}
        self.tool_manager = IntegratedToolManager(self.config)
        
        # 存储
        self.data_dir = Path(self.config.get("data_dir", "./claudeditor_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "claudeditor.db"
        
        # 初始化数据库
        self._init_database()
        
        # 加载数据
        self._load_persistent_data()
        
        # 初始化AI模型
        self._initialize_ai_models()
        
        # 启动后台任务
        self._start_background_tasks()
        
        logger.info("ClaudEditor深度集成系统初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "ai_models": {
                "claude": {
                    "api_key": "your-claude-api-key",
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "temperature": 0.1
                },
                "gemini": {
                    "api_key": "your-gemini-api-key",
                    "model": "gemini-1.5-pro",
                    "max_tokens": 4096,
                    "temperature": 0.1
                }
            },
            "task_settings": {
                "max_concurrent_tasks": 10,
                "task_timeout": 300,
                "retry_attempts": 3,
                "priority_weights": {
                    "urgent": 1.0,
                    "high": 0.8,
                    "medium": 0.6,
                    "low": 0.4
                }
            },
            "collaboration_settings": {
                "max_participants": 20,
                "session_timeout": 3600,
                "sync_interval": 1.0,
                "enable_real_time": True
            },
            "performance_settings": {
                "monitoring_interval": 10,
                "metrics_retention_days": 30,
                "alert_thresholds": {
                    "response_time": 5.0,
                    "error_rate": 0.05,
                    "accuracy_threshold": 0.8
                }
            },
            "recommendation_settings": {
                "enable_smart_recommendations": True,
                "recommendation_threshold": 0.7,
                "max_recommendations_per_user": 10,
                "learning_rate": 0.1
            },
            "code_analysis_settings": {
                "enable_real_time_analysis": True,
                "quality_threshold": 0.7,
                "complexity_threshold": 10,
                "security_scan_enabled": True
            },
            "data_dir": "./claudeditor_data",
            "enable_caching": True,
            "cache_ttl": 3600,
            "enable_websocket": True,
            "websocket_port": 8765
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        priority TEXT,
                        status TEXT,
                        user_id TEXT,
                        project_id TEXT,
                        description TEXT,
                        input_data TEXT,
                        output_data TEXT,
                        assigned_model TEXT,
                        estimated_duration INTEGER,
                        actual_duration INTEGER,
                        quality_score REAL,
                        error_message TEXT,
                        created_at TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        metadata TEXT
                    )
                ''')
                
                # 创建代码分析表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS code_analyses (
                        analysis_id TEXT PRIMARY KEY,
                        code_content TEXT NOT NULL,
                        language TEXT,
                        quality_score REAL,
                        complexity_score REAL,
                        maintainability_score REAL,
                        performance_score REAL,
                        security_score REAL,
                        issues TEXT,
                        suggestions TEXT,
                        metrics TEXT,
                        analysis_time TIMESTAMP
                    )
                ''')
                
                # 创建协作会话表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaboration_sessions (
                        session_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        participants TEXT,
                        session_type TEXT,
                        status TEXT,
                        shared_context TEXT,
                        message_history TEXT,
                        code_changes TEXT,
                        ai_suggestions TEXT,
                        created_at TIMESTAMP,
                        last_activity TIMESTAMP
                    )
                ''')
                
                # 创建性能指标表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        metric_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        model_used TEXT,
                        response_time REAL,
                        accuracy_score REAL,
                        user_satisfaction REAL,
                        resource_usage TEXT,
                        error_rate REAL,
                        throughput REAL,
                        timestamp TIMESTAMP
                    )
                ''')
                
                # 创建推荐表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_recommendations (
                        recommendation_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        recommendation_type TEXT,
                        title TEXT,
                        description TEXT,
                        confidence_score REAL,
                        context TEXT,
                        action_data TEXT,
                        is_accepted BOOLEAN,
                        feedback_score REAL,
                        created_at TIMESTAMP
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_user ON ai_tasks(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_status ON ai_tasks(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_type ON ai_tasks(task_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_project ON collaboration_sessions(project_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_task ON performance_metrics(task_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_recommendations_user ON smart_recommendations(user_id)')
                
                conn.commit()
                logger.info("ClaudEditor数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _load_persistent_data(self):
        """加载持久化数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 加载任务历史
                cursor.execute('SELECT * FROM ai_tasks WHERE status IN ("completed", "failed")')
                for row in cursor.fetchall():
                    task = self._row_to_task(row)
                    self.task_history.append(task)
                
                # 加载活跃任务
                cursor.execute('SELECT * FROM ai_tasks WHERE status IN ("pending", "processing")')
                for row in cursor.fetchall():
                    task = self._row_to_task(row)
                    self.active_tasks[task.task_id] = task
                
                # 加载协作会话
                cursor.execute('SELECT * FROM collaboration_sessions WHERE status = "active"')
                for row in cursor.fetchall():
                    session = self._row_to_collaboration_session(row)
                    self.collaboration_sessions[session.session_id] = session
                
                # 加载性能指标
                cursor.execute('SELECT * FROM performance_metrics ORDER BY timestamp DESC LIMIT 1000')
                for row in cursor.fetchall():
                    metric = self._row_to_performance_metric(row)
                    self.performance_metrics.append(metric)
            
            logger.info(f"加载 {len(self.task_history)} 个历史任务和 {len(self.active_tasks)} 个活跃任务")
            
        except Exception as e:
            logger.warning(f"加载持久化数据失败: {e}")
    
    def _row_to_task(self, row) -> AITask:
        """数据库行转任务对象"""
        return AITask(
            task_id=row[0],
            task_type=TaskType(row[1]),
            priority=TaskPriority(row[2]) if row[2] else TaskPriority.MEDIUM,
            status=TaskStatus(row[3]),
            user_id=row[4] or "",
            project_id=row[5] or "",
            description=row[6] or "",
            input_data=json.loads(row[7]) if row[7] else {},
            output_data=json.loads(row[8]) if row[8] else {},
            assigned_model=AIModel(row[9]) if row[9] else None,
            estimated_duration=row[10],
            actual_duration=row[11],
            quality_score=row[12],
            error_message=row[13],
            created_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now(),
            started_at=datetime.fromisoformat(row[15]) if row[15] else None,
            completed_at=datetime.fromisoformat(row[16]) if row[16] else None,
            metadata=json.loads(row[17]) if row[17] else {}
        )
    
    def _row_to_collaboration_session(self, row) -> CollaborationSession:
        """数据库行转协作会话对象"""
        return CollaborationSession(
            session_id=row[0],
            project_id=row[1],
            participants=json.loads(row[2]) if row[2] else [],
            session_type=row[3] or "",
            status=row[4] or "active",
            shared_context=json.loads(row[5]) if row[5] else {},
            message_history=json.loads(row[6]) if row[6] else [],
            code_changes=json.loads(row[7]) if row[7] else [],
            ai_suggestions=json.loads(row[8]) if row[8] else [],
            created_at=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
            last_activity=datetime.fromisoformat(row[10]) if row[10] else datetime.now()
        )
    
    def _row_to_performance_metric(self, row) -> PerformanceMetrics:
        """数据库行转性能指标对象"""
        return PerformanceMetrics(
            metric_id=row[0],
            task_id=row[1],
            model_used=AIModel(row[2]),
            response_time=row[3],
            accuracy_score=row[4],
            user_satisfaction=row[5],
            resource_usage=json.loads(row[6]) if row[6] else {},
            error_rate=row[7] or 0.0,
            throughput=row[8] or 0.0,
            timestamp=datetime.fromisoformat(row[9]) if row[9] else datetime.now()
        )
    
    def _initialize_ai_models(self):
        """初始化AI模型"""
        try:
            # 初始化Claude模型
            if "claude" in self.config["ai_models"]:
                from .claude_api_client import get_claude_client
                claude_config = self.config["ai_models"]["claude"]
                self.ai_models[AIModel.CLAUDE] = get_claude_client(claude_config["api_key"])
                logger.info("Claude模型初始化完成")
            
            # 初始化Gemini模型
            if "gemini" in self.config["ai_models"]:
                from .gemini_api_client import get_gemini_client
                gemini_config = self.config["ai_models"]["gemini"]
                self.ai_models[AIModel.GEMINI] = get_gemini_client(gemini_config["api_key"])
                logger.info("Gemini模型初始化完成")
            
            # 初始化多模型协调器
            from .multi_model_coordinator import MultiModelCoordinator
            self.multi_model_coordinator = MultiModelCoordinator(self.config)
            
            logger.info(f"初始化 {len(self.ai_models)} 个AI模型")
            
        except Exception as e:
            logger.error(f"AI模型初始化失败: {e}")
    
    def _start_background_tasks(self):
        """启动后台任务"""
        try:
            # 启动任务处理器
            asyncio.create_task(self._task_processor())
            
            # 启动性能监控
            asyncio.create_task(self._performance_monitor_loop())
            
            # 启动协作会话清理
            asyncio.create_task(self._collaboration_cleanup_loop())
            
            # 启动推荐引擎
            asyncio.create_task(self._recommendation_engine_loop())
            
            logger.info("后台任务启动完成")
            
        except Exception as e:
            logger.error(f"启动后台任务失败: {e}")
    
    async def submit_task(self, task_type: TaskType, user_id: str, project_id: str,
                         description: str, input_data: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """提交AI任务"""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        # 创建任务
        task = AITask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            user_id=user_id,
            project_id=project_id,
            description=description,
            input_data=input_data
        )
        
        # 估算任务时长
        task.estimated_duration = await self._estimate_task_duration(task)
        
        # 选择最佳AI模型
        task.assigned_model = await self.model_load_balancer.select_best_model(task)
        
        # 添加到任务队列
        self.active_tasks[task_id] = task
        self.task_queue.append(task)
        
        # 持久化
        await self._persist_task(task)
        
        logger.info(f"提交任务: {task_id} - {task_type.value} (优先级: {priority.value})")
        return task_id
    
    async def _estimate_task_duration(self, task: AITask) -> int:
        """估算任务时长"""
        # 基于任务类型的基础时长（秒）
        base_durations = {
            TaskType.CODE_GENERATION: 30,
            TaskType.CODE_REVIEW: 20,
            TaskType.CODE_OPTIMIZATION: 40,
            TaskType.BUG_FIXING: 35,
            TaskType.TESTING: 25,
            TaskType.DOCUMENTATION: 15,
            TaskType.REFACTORING: 45,
            TaskType.ANALYSIS: 20
        }
        
        base_duration = base_durations.get(task.task_type, 30)
        
        # 基于输入数据大小调整
        input_size = len(str(task.input_data))
        size_factor = min(3.0, 1.0 + input_size / 10000)
        
        # 基于优先级调整（高优先级可能需要更多时间保证质量）
        priority_factors = {
            TaskPriority.URGENT: 1.2,
            TaskPriority.HIGH: 1.1,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.LOW: 0.9
        }
        
        priority_factor = priority_factors.get(task.priority, 1.0)
        
        estimated_duration = int(base_duration * size_factor * priority_factor)
        return estimated_duration
    
    async def _task_processor(self):
        """任务处理器"""
        while True:
            try:
                if self.task_queue:
                    # 获取最高优先级任务
                    task = self._get_highest_priority_task()
                    
                    if task and len([t for t in self.active_tasks.values() if t.status == TaskStatus.PROCESSING]) < self.config["task_settings"]["max_concurrent_tasks"]:
                        # 处理任务
                        await self._process_task(task)
                
                await asyncio.sleep(1)  # 避免过度占用CPU
                
            except Exception as e:
                logger.error(f"任务处理器错误: {e}")
                await asyncio.sleep(5)
    
    def _get_highest_priority_task(self) -> Optional[AITask]:
        """获取最高优先级任务"""
        if not self.task_queue:
            return None
        
        # 按优先级排序
        priority_weights = self.config["task_settings"]["priority_weights"]
        
        sorted_tasks = sorted(
            self.task_queue,
            key=lambda t: (
                priority_weights.get(t.priority.value, 0.5),
                -t.created_at.timestamp()  # 创建时间越早优先级越高
            ),
            reverse=True
        )
        
        if sorted_tasks:
            task = sorted_tasks[0]
            self.task_queue.remove(task)
            return task
        
        return None
    
    async def _process_task(self, task: AITask):
        """处理任务"""
        try:
            # 更新任务状态
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            
            logger.info(f"开始处理任务: {task.task_id} - {task.task_type.value}")
            
            # 使用任务执行器处理
            result = await self.task_executor.execute_task(task, self.ai_models)
            
            # 更新任务结果
            task.output_data = result["output_data"]
            task.quality_score = result.get("quality_score", 0.0)
            task.actual_duration = int((datetime.now() - task.started_at).total_seconds())
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            # 记录性能指标
            await self._record_performance_metrics(task, result)
            
            # 生成智能推荐
            await self._generate_task_recommendations(task, result)
            
            logger.info(f"任务完成: {task.task_id} (质量分: {task.quality_score:.2f})")
            
        except Exception as e:
            # 任务失败
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            if task.started_at:
                task.actual_duration = int((datetime.now() - task.started_at).total_seconds())
            
            logger.error(f"任务失败: {task.task_id} - {e}")
        
        finally:
            # 持久化任务
            await self._persist_task(task)
            
            # 移动到历史记录
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            self.task_history.append(task)
    
    async def analyze_code(self, code_content: str, language: str,
                          user_id: str, project_id: str) -> str:
        """分析代码"""
        analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"
        
        # 使用代码分析器
        analysis_result = await self.code_analyzer.analyze_code(
            code_content, language, user_id, project_id
        )
        
        # 创建分析记录
        analysis = CodeAnalysis(
            analysis_id=analysis_id,
            code_content=code_content,
            language=language,
            quality_score=analysis_result["quality_score"],
            complexity_score=analysis_result["complexity_score"],
            maintainability_score=analysis_result["maintainability_score"],
            performance_score=analysis_result["performance_score"],
            security_score=analysis_result["security_score"],
            issues=analysis_result["issues"],
            suggestions=analysis_result["suggestions"],
            metrics=analysis_result["metrics"]
        )
        
        # 缓存分析结果
        self.analysis_cache[analysis_id] = analysis
        
        # 持久化
        await self._persist_code_analysis(analysis)
        
        # 如果质量分数低，生成改进建议
        if analysis.quality_score < self.config["code_analysis_settings"]["quality_threshold"]:
            await self._generate_code_improvement_recommendations(analysis, user_id)
        
        logger.info(f"代码分析完成: {analysis_id} (质量分: {analysis.quality_score:.2f})")
        return analysis_id
    
    async def start_collaboration_session(self, project_id: str, initiator_id: str,
                                        participants: List[str],
                                        session_type: str = "code_review") -> str:
        """开始协作会话"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        # 创建协作会话
        session = CollaborationSession(
            session_id=session_id,
            project_id=project_id,
            participants=[initiator_id] + participants,
            session_type=session_type,
            status="active"
        )
        
        # 存储会话
        self.collaboration_sessions[session_id] = session
        
        # 启动实时同步
        if self.config["collaboration_settings"]["enable_real_time"]:
            await self.real_time_sync.start_session(session)
        
        # 持久化
        await self._persist_collaboration_session(session)
        
        logger.info(f"协作会话开始: {session_id} ({len(session.participants)} 参与者)")
        return session_id
    
    async def add_collaboration_message(self, session_id: str, user_id: str,
                                      message_type: str, content: Dict[str, Any]) -> bool:
        """添加协作消息"""
        if session_id not in self.collaboration_sessions:
            return False
        
        session = self.collaboration_sessions[session_id]
        
        if user_id not in session.participants:
            return False
        
        # 添加消息
        message = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        session.message_history.append(message)
        session.last_activity = datetime.now()
        
        # 如果是代码变更，记录到代码变更历史
        if message_type == "code_change":
            session.code_changes.append(message)
        
        # 实时同步
        if self.config["collaboration_settings"]["enable_real_time"]:
            await self.real_time_sync.broadcast_message(session_id, message)
        
        # 生成AI建议
        if message_type in ["code_change", "question"]:
            ai_suggestion = await self._generate_collaboration_ai_suggestion(session, message)
            if ai_suggestion:
                session.ai_suggestions.append(ai_suggestion)
                
                # 广播AI建议
                if self.config["collaboration_settings"]["enable_real_time"]:
                    await self.real_time_sync.broadcast_message(session_id, {
                        "message_type": "ai_suggestion",
                        "content": ai_suggestion,
                        "timestamp": datetime.now().isoformat()
                    })
        
        # 持久化
        await self._persist_collaboration_session(session)
        
        return True
    
    async def _generate_collaboration_ai_suggestion(self, session: CollaborationSession,
                                                  message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """生成协作AI建议"""
        try:
            if message["message_type"] == "code_change":
                # 分析代码变更
                code_content = message["content"].get("code", "")
                if code_content:
                    # 快速代码分析
                    analysis = await self.code_analyzer.quick_analyze(code_content)
                    
                    if analysis["issues"]:
                        return {
                            "suggestion_id": f"ai_sugg_{uuid.uuid4().hex[:8]}",
                            "type": "code_improvement",
                            "title": "代码改进建议",
                            "description": f"检测到 {len(analysis['issues'])} 个潜在问题",
                            "details": analysis["issues"][:3],  # 只显示前3个问题
                            "confidence": 0.8,
                            "timestamp": datetime.now().isoformat()
                        }
            
            elif message["message_type"] == "question":
                # 基于问题内容生成建议
                question = message["content"].get("text", "")
                if "bug" in question.lower() or "error" in question.lower():
                    return {
                        "suggestion_id": f"ai_sugg_{uuid.uuid4().hex[:8]}",
                        "type": "debugging_help",
                        "title": "调试建议",
                        "description": "建议检查日志文件和错误堆栈",
                        "details": [
                            "查看控制台错误信息",
                            "检查变量值和数据类型",
                            "使用断点调试"
                        ],
                        "confidence": 0.7,
                        "timestamp": datetime.now().isoformat()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"生成协作AI建议失败: {e}")
            return None
    
    async def get_user_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户推荐"""
        recommendations = await self.recommendation_engine.get_recommendations(
            user_id, limit
        )
        
        # 更新用户推荐缓存
        self.user_recommendations[user_id] = recommendations
        
        return [asdict(rec) for rec in recommendations]
    
    async def provide_recommendation_feedback(self, recommendation_id: str, user_id: str,
                                            is_accepted: bool, feedback_score: float = None) -> bool:
        """提供推荐反馈"""
        # 查找推荐
        recommendation = None
        for user_recs in self.user_recommendations.values():
            for rec in user_recs:
                if rec.recommendation_id == recommendation_id:
                    recommendation = rec
                    break
            if recommendation:
                break
        
        if not recommendation:
            return False
        
        # 更新反馈
        recommendation.is_accepted = is_accepted
        recommendation.feedback_score = feedback_score
        
        # 更新推荐引擎学习
        await self.recommendation_engine.update_feedback(
            recommendation_id, user_id, is_accepted, feedback_score
        )
        
        # 持久化
        await self._persist_recommendation(recommendation)
        
        return True
    
    async def get_performance_dashboard(self, time_range: str = "24h") -> Dict[str, Any]:
        """获取性能仪表板"""
        return await self.performance_monitor.get_dashboard_data(
            self.performance_metrics, time_range
        )
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查活跃任务
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": self._calculate_task_progress(task),
                "estimated_completion": self._estimate_completion_time(task),
                "quality_score": task.quality_score,
                "error_message": task.error_message
            }
        
        # 检查历史任务
        for task in self.task_history:
            if task.task_id == task_id:
                return {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "progress": 1.0 if task.status == TaskStatus.COMPLETED else 0.0,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "quality_score": task.quality_score,
                    "error_message": task.error_message,
                    "output_data": task.output_data
                }
        
        return None
    
    def _calculate_task_progress(self, task: AITask) -> float:
        """计算任务进度"""
        if task.status == TaskStatus.PENDING:
            return 0.0
        elif task.status == TaskStatus.PROCESSING:
            if task.started_at and task.estimated_duration:
                elapsed = (datetime.now() - task.started_at).total_seconds()
                progress = min(0.9, elapsed / task.estimated_duration)  # 最多显示90%
                return progress
            return 0.1
        elif task.status == TaskStatus.COMPLETED:
            return 1.0
        else:
            return 0.0
    
    def _estimate_completion_time(self, task: AITask) -> Optional[str]:
        """估算完成时间"""
        if task.status != TaskStatus.PROCESSING or not task.started_at or not task.estimated_duration:
            return None
        
        elapsed = (datetime.now() - task.started_at).total_seconds()
        remaining = max(0, task.estimated_duration - elapsed)
        
        completion_time = datetime.now() + timedelta(seconds=remaining)
        return completion_time.isoformat()
    
    async def _record_performance_metrics(self, task: AITask, result: Dict[str, Any]):
        """记录性能指标"""
        metric_id = f"metric_{uuid.uuid4().hex[:12]}"
        
        metric = PerformanceMetrics(
            metric_id=metric_id,
            task_id=task.task_id,
            model_used=task.assigned_model,
            response_time=task.actual_duration or 0,
            accuracy_score=result.get("accuracy_score", 0.0),
            user_satisfaction=result.get("user_satisfaction", 0.0),
            resource_usage=result.get("resource_usage", {}),
            error_rate=1.0 if task.status == TaskStatus.FAILED else 0.0,
            throughput=1.0 / (task.actual_duration or 1)
        )
        
        self.performance_metrics.append(metric)
        
        # 更新模型性能统计
        if task.assigned_model:
            self.model_performance[task.assigned_model]["total_tasks"] += 1
            self.model_performance[task.assigned_model]["avg_response_time"] = (
                (self.model_performance[task.assigned_model]["avg_response_time"] * 
                 (self.model_performance[task.assigned_model]["total_tasks"] - 1) + 
                 metric.response_time) / self.model_performance[task.assigned_model]["total_tasks"]
            )
            self.model_performance[task.assigned_model]["avg_accuracy"] = (
                (self.model_performance[task.assigned_model]["avg_accuracy"] * 
                 (self.model_performance[task.assigned_model]["total_tasks"] - 1) + 
                 metric.accuracy_score) / self.model_performance[task.assigned_model]["total_tasks"]
            )
        
        # 持久化
        await self._persist_performance_metric(metric)
    
    async def _generate_task_recommendations(self, task: AITask, result: Dict[str, Any]):
        """生成任务相关推荐"""
        try:
            recommendations = []
            
            # 基于任务类型生成推荐
            if task.task_type == TaskType.CODE_GENERATION:
                if task.quality_score and task.quality_score < 0.8:
                    recommendations.append({
                        "type": "code_improvement",
                        "title": "代码质量改进建议",
                        "description": "生成的代码质量可以进一步提升",
                        "confidence": 0.8
                    })
            
            elif task.task_type == TaskType.CODE_REVIEW:
                if result.get("issues_found", 0) > 0:
                    recommendations.append({
                        "type": "code_refactoring",
                        "title": "代码重构建议",
                        "description": f"发现 {result['issues_found']} 个问题，建议进行重构",
                        "confidence": 0.9
                    })
            
            # 基于性能生成推荐
            if task.actual_duration and task.estimated_duration:
                if task.actual_duration > task.estimated_duration * 1.5:
                    recommendations.append({
                        "type": "performance_optimization",
                        "title": "性能优化建议",
                        "description": "任务执行时间超出预期，建议优化",
                        "confidence": 0.7
                    })
            
            # 保存推荐
            for rec_data in recommendations:
                rec_id = f"rec_{uuid.uuid4().hex[:12]}"
                recommendation = SmartRecommendation(
                    recommendation_id=rec_id,
                    user_id=task.user_id,
                    recommendation_type=rec_data["type"],
                    title=rec_data["title"],
                    description=rec_data["description"],
                    confidence_score=rec_data["confidence"],
                    context={"task_id": task.task_id, "task_type": task.task_type.value}
                )
                
                self.user_recommendations[task.user_id].append(recommendation)
                await self._persist_recommendation(recommendation)
        
        except Exception as e:
            logger.error(f"生成任务推荐失败: {e}")
    
    async def _generate_code_improvement_recommendations(self, analysis: CodeAnalysis, user_id: str):
        """生成代码改进推荐"""
        try:
            if analysis.issues:
                rec_id = f"rec_{uuid.uuid4().hex[:12]}"
                recommendation = SmartRecommendation(
                    recommendation_id=rec_id,
                    user_id=user_id,
                    recommendation_type="code_quality",
                    title="代码质量改进",
                    description=f"检测到 {len(analysis.issues)} 个代码问题，建议修复",
                    confidence_score=0.85,
                    context={
                        "analysis_id": analysis.analysis_id,
                        "quality_score": analysis.quality_score,
                        "issues_count": len(analysis.issues)
                    },
                    action_data={
                        "issues": analysis.issues[:5],  # 只显示前5个问题
                        "suggestions": analysis.suggestions[:3]  # 只显示前3个建议
                    }
                )
                
                self.user_recommendations[user_id].append(recommendation)
                await self._persist_recommendation(recommendation)
        
        except Exception as e:
            logger.error(f"生成代码改进推荐失败: {e}")
    
    async def _performance_monitor_loop(self):
        """性能监控循环"""
        while True:
            try:
                # 检查性能指标
                await self.performance_monitor.check_performance_alerts(
                    self.performance_metrics,
                    self.config["performance_settings"]["alert_thresholds"]
                )
                
                # 清理过期指标
                retention_days = self.config["performance_settings"]["metrics_retention_days"]
                cutoff_time = datetime.now() - timedelta(days=retention_days)
                
                self.performance_metrics = [
                    metric for metric in self.performance_metrics
                    if metric.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(self.config["performance_settings"]["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"性能监控循环错误: {e}")
                await asyncio.sleep(60)
    
    async def _collaboration_cleanup_loop(self):
        """协作会话清理循环"""
        while True:
            try:
                timeout = self.config["collaboration_settings"]["session_timeout"]
                cutoff_time = datetime.now() - timedelta(seconds=timeout)
                
                # 清理超时会话
                expired_sessions = []
                for session_id, session in self.collaboration_sessions.items():
                    if session.last_activity < cutoff_time:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    session = self.collaboration_sessions[session_id]
                    session.status = "expired"
                    await self._persist_collaboration_session(session)
                    del self.collaboration_sessions[session_id]
                    logger.info(f"清理过期协作会话: {session_id}")
                
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"协作会话清理循环错误: {e}")
                await asyncio.sleep(300)
    
    async def _recommendation_engine_loop(self):
        """推荐引擎循环"""
        while True:
            try:
                if self.config["recommendation_settings"]["enable_smart_recommendations"]:
                    # 为活跃用户生成推荐
                    active_users = set()
                    
                    # 从活跃任务中获取用户
                    for task in self.active_tasks.values():
                        active_users.add(task.user_id)
                    
                    # 从协作会话中获取用户
                    for session in self.collaboration_sessions.values():
                        active_users.update(session.participants)
                    
                    # 为每个活跃用户生成推荐
                    for user_id in active_users:
                        if len(self.user_recommendations[user_id]) < self.config["recommendation_settings"]["max_recommendations_per_user"]:
                            new_recommendations = await self.recommendation_engine.generate_proactive_recommendations(user_id)
                            self.user_recommendations[user_id].extend(new_recommendations)
                
                await asyncio.sleep(600)  # 每10分钟运行一次
                
            except Exception as e:
                logger.error(f"推荐引擎循环错误: {e}")
                await asyncio.sleep(600)
    
    async def _persist_task(self, task: AITask):
        """持久化任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_tasks 
                    (task_id, task_type, priority, status, user_id, project_id, description,
                     input_data, output_data, assigned_model, estimated_duration, actual_duration,
                     quality_score, error_message, created_at, started_at, completed_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.task_id,
                    task.task_type.value,
                    task.priority.value,
                    task.status.value,
                    task.user_id,
                    task.project_id,
                    task.description,
                    json.dumps(task.input_data),
                    json.dumps(task.output_data),
                    task.assigned_model.value if task.assigned_model else None,
                    task.estimated_duration,
                    task.actual_duration,
                    task.quality_score,
                    task.error_message,
                    task.created_at.isoformat(),
                    task.started_at.isoformat() if task.started_at else None,
                    task.completed_at.isoformat() if task.completed_at else None,
                    json.dumps(task.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化任务失败: {e}")
    
    async def _persist_code_analysis(self, analysis: CodeAnalysis):
        """持久化代码分析"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO code_analyses 
                    (analysis_id, code_content, language, quality_score, complexity_score,
                     maintainability_score, performance_score, security_score, issues,
                     suggestions, metrics, analysis_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis.analysis_id,
                    analysis.code_content,
                    analysis.language,
                    analysis.quality_score,
                    analysis.complexity_score,
                    analysis.maintainability_score,
                    analysis.performance_score,
                    analysis.security_score,
                    json.dumps(analysis.issues),
                    json.dumps(analysis.suggestions),
                    json.dumps(analysis.metrics),
                    analysis.analysis_time.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化代码分析失败: {e}")
    
    async def _persist_collaboration_session(self, session: CollaborationSession):
        """持久化协作会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO collaboration_sessions 
                    (session_id, project_id, participants, session_type, status, shared_context,
                     message_history, code_changes, ai_suggestions, created_at, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id,
                    session.project_id,
                    json.dumps(session.participants),
                    session.session_type,
                    session.status,
                    json.dumps(session.shared_context),
                    json.dumps(session.message_history),
                    json.dumps(session.code_changes),
                    json.dumps(session.ai_suggestions),
                    session.created_at.isoformat(),
                    session.last_activity.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化协作会话失败: {e}")
    
    async def _persist_performance_metric(self, metric: PerformanceMetrics):
        """持久化性能指标"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO performance_metrics 
                    (metric_id, task_id, model_used, response_time, accuracy_score,
                     user_satisfaction, resource_usage, error_rate, throughput, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.metric_id,
                    metric.task_id,
                    metric.model_used.value,
                    metric.response_time,
                    metric.accuracy_score,
                    metric.user_satisfaction,
                    json.dumps(metric.resource_usage),
                    metric.error_rate,
                    metric.throughput,
                    metric.timestamp.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化性能指标失败: {e}")
    
    async def _persist_recommendation(self, recommendation: SmartRecommendation):
        """持久化推荐"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO smart_recommendations 
                    (recommendation_id, user_id, recommendation_type, title, description,
                     confidence_score, context, action_data, is_accepted, feedback_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    recommendation.recommendation_id,
                    recommendation.user_id,
                    recommendation.recommendation_type,
                    recommendation.title,
                    recommendation.description,
                    recommendation.confidence_score,
                    json.dumps(recommendation.context),
                    json.dumps(recommendation.action_data),
                    recommendation.is_accepted,
                    recommendation.feedback_score,
                    recommendation.created_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化推荐失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 保存所有活跃任务
            for task in self.active_tasks.values():
                await self._persist_task(task)
            
            # 保存所有协作会话
            for session in self.collaboration_sessions.values():
                await self._persist_collaboration_session(session)
            
            # 保存所有推荐
            for user_recs in self.user_recommendations.values():
                for rec in user_recs:
                    await self._persist_recommendation(rec)
            
            logger.info("ClaudEditor深度集成系统清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

# 辅助类定义（简化实现）
class ModelLoadBalancer:
    """模型负载均衡器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def select_best_model(self, task: AITask) -> AIModel:
        """选择最佳模型"""
        # 简化实现：基于任务类型选择
        task_model_preferences = {
            TaskType.CODE_GENERATION: AIModel.CLAUDE,
            TaskType.CODE_REVIEW: AIModel.GEMINI,
            TaskType.CODE_OPTIMIZATION: AIModel.CLAUDE,
            TaskType.BUG_FIXING: AIModel.CLAUDE,
            TaskType.TESTING: AIModel.GEMINI,
            TaskType.DOCUMENTATION: AIModel.GEMINI,
            TaskType.REFACTORING: AIModel.CLAUDE,
            TaskType.ANALYSIS: AIModel.GEMINI
        }
        
        return task_model_preferences.get(task.task_type, AIModel.CLAUDE)

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def execute_task(self, task: AITask, ai_models: Dict[AIModel, Any]) -> Dict[str, Any]:
        """执行任务"""
        # 简化实现
        await asyncio.sleep(random.uniform(1, 5))  # 模拟处理时间
        
        return {
            "output_data": {"result": f"Task {task.task_id} completed"},
            "quality_score": random.uniform(0.7, 0.95),
            "accuracy_score": random.uniform(0.8, 0.98),
            "user_satisfaction": random.uniform(0.75, 0.95),
            "resource_usage": {"cpu": random.uniform(0.1, 0.8), "memory": random.uniform(0.2, 0.6)}
        }

class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def analyze_code(self, code_content: str, language: str, 
                          user_id: str, project_id: str) -> Dict[str, Any]:
        """分析代码"""
        # 简化实现
        return {
            "quality_score": random.uniform(0.6, 0.95),
            "complexity_score": random.uniform(1, 15),
            "maintainability_score": random.uniform(0.5, 0.9),
            "performance_score": random.uniform(0.6, 0.95),
            "security_score": random.uniform(0.7, 0.98),
            "issues": [
                {"type": "warning", "message": "变量命名不规范", "line": 10},
                {"type": "error", "message": "潜在的空指针异常", "line": 25}
            ],
            "suggestions": [
                {"type": "improvement", "message": "建议使用更具描述性的变量名"},
                {"type": "optimization", "message": "可以使用列表推导式优化性能"}
            ],
            "metrics": {
                "lines_of_code": len(code_content.split('\n')),
                "cyclomatic_complexity": random.randint(1, 10),
                "code_coverage": random.uniform(0.6, 0.95)
            }
        }
    
    async def quick_analyze(self, code_content: str) -> Dict[str, Any]:
        """快速分析"""
        return {
            "issues": [
                {"type": "warning", "message": "代码格式问题", "severity": "low"}
            ]
        }

class RealTimeSync:
    """实时同步"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def start_session(self, session: CollaborationSession):
        """启动会话同步"""
        pass
    
    async def broadcast_message(self, session_id: str, message: Dict[str, Any]):
        """广播消息"""
        pass

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def check_performance_alerts(self, metrics: List[PerformanceMetrics], 
                                     thresholds: Dict[str, float]):
        """检查性能警报"""
        pass
    
    async def get_dashboard_data(self, metrics: List[PerformanceMetrics], 
                               time_range: str) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            "total_tasks": len(metrics),
            "avg_response_time": sum(m.response_time for m in metrics) / len(metrics) if metrics else 0,
            "avg_accuracy": sum(m.accuracy_score for m in metrics) / len(metrics) if metrics else 0,
            "error_rate": sum(m.error_rate for m in metrics) / len(metrics) if metrics else 0
        }

class RecommendationEngine:
    """推荐引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def get_recommendations(self, user_id: str, limit: int) -> List[SmartRecommendation]:
        """获取推荐"""
        return []
    
    async def generate_proactive_recommendations(self, user_id: str) -> List[SmartRecommendation]:
        """生成主动推荐"""
        return []
    
    async def update_feedback(self, recommendation_id: str, user_id: str, 
                            is_accepted: bool, feedback_score: float):
        """更新反馈"""
        pass

class IntegratedToolManager:
    """集成工具管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config

# 工厂函数
def get_claudeditor_deep_integration(config_path: str = "./claudeditor_integration_config.json") -> ClaudEditorDeepIntegration:
    """获取ClaudEditor深度集成实例"""
    return ClaudEditorDeepIntegration(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_claudeditor_integration():
        """测试ClaudEditor深度集成"""
        claudeditor = get_claudeditor_deep_integration()
        
        try:
            # 提交代码生成任务
            print("💻 提交代码生成任务...")
            task_id = await claudeditor.submit_task(
                task_type=TaskType.CODE_GENERATION,
                user_id="user_001",
                project_id="project_001",
                description="生成一个Python函数来计算斐波那契数列",
                input_data={
                    "language": "python",
                    "function_name": "fibonacci",
                    "parameters": ["n"],
                    "requirements": "递归实现，包含错误处理"
                },
                priority=TaskPriority.HIGH
            )
            
            print(f"任务提交成功: {task_id}")
            
            # 等待任务完成
            print("⏳ 等待任务完成...")
            for i in range(10):
                status = await claudeditor.get_task_status(task_id)
                if status:
                    print(f"任务状态: {status['status']} (进度: {status['progress']:.1%})")
                    if status['status'] == 'completed':
                        print(f"任务完成! 质量分: {status.get('quality_score', 0):.2f}")
                        break
                await asyncio.sleep(2)
            
            # 代码分析
            print("\n🔍 代码分析...")
            sample_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
            
            analysis_id = await claudeditor.analyze_code(
                code_content=sample_code,
                language="python",
                user_id="user_001",
                project_id="project_001"
            )
            
            analysis = claudeditor.analysis_cache[analysis_id]
            print(f"分析完成: {analysis_id}")
            print(f"质量分: {analysis.quality_score:.2f}")
            print(f"复杂度: {analysis.complexity_score:.2f}")
            print(f"问题数: {len(analysis.issues)}")
            
            # 开始协作会话
            print("\n🤝 开始协作会话...")
            session_id = await claudeditor.start_collaboration_session(
                project_id="project_001",
                initiator_id="user_001",
                participants=["user_002", "user_003"],
                session_type="code_review"
            )
            
            print(f"协作会话开始: {session_id}")
            
            # 添加协作消息
            await claudeditor.add_collaboration_message(
                session_id=session_id,
                user_id="user_002",
                message_type="code_change",
                content={
                    "code": sample_code,
                    "change_type": "optimization",
                    "description": "优化斐波那契函数实现"
                }
            )
            
            await claudeditor.add_collaboration_message(
                session_id=session_id,
                user_id="user_003",
                message_type="question",
                content={
                    "text": "这个实现有性能问题吗？",
                    "context": "fibonacci函数"
                }
            )
            
            # 获取用户推荐
            print("\n🎯 获取用户推荐...")
            recommendations = await claudeditor.get_user_recommendations("user_001", limit=5)
            
            print(f"获得 {len(recommendations)} 个推荐:")
            for rec in recommendations:
                print(f"  - {rec['title']} (置信度: {rec['confidence_score']:.2f})")
            
            # 获取性能仪表板
            print("\n📊 性能仪表板...")
            dashboard = await claudeditor.get_performance_dashboard("24h")
            
            print(f"总任务数: {dashboard['total_tasks']}")
            print(f"平均响应时间: {dashboard['avg_response_time']:.2f}秒")
            print(f"平均准确率: {dashboard['avg_accuracy']:.2%}")
            print(f"错误率: {dashboard['error_rate']:.2%}")
            
            # 提供推荐反馈
            if recommendations:
                print("\n👍 提供推荐反馈...")
                await claudeditor.provide_recommendation_feedback(
                    recommendation_id=recommendations[0]['recommendation_id'],
                    user_id="user_001",
                    is_accepted=True,
                    feedback_score=0.9
                )
                print("反馈提交成功")
            
        finally:
            # 清理
            await claudeditor.cleanup()
    
    # 运行测试
    asyncio.run(test_claudeditor_integration())

