#!/usr/bin/env python3
"""
Zen MCP工具注册器

为PowerAutomation 4.1提供完整的Zen MCP工具生态系统注册和管理。
实现14种专业开发工具的统一注册、发现、管理和执行。

主要功能：
- 14种专业开发工具注册
- 工具能力分析和分类
- 智能工具发现和匹配
- 工具生命周期管理
- 性能监控和优化
- 工具协作网络
- 安全和权限控制
- 工具版本管理

工具分类：
- 核心开发工具 (5种): 分析、生成、调试、重构、测试
- 性能优化工具 (3种): 分析、优化、基准测试
- 质量保证工具 (3种): 检查、格式化、文档生成
- 部署运维工具 (3种): 部署、监控、安全扫描

技术特色：
- 统一工具接口
- 智能工具路由
- 协作工具网络
- 性能优化引擎
- 安全沙箱执行

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
import subprocess
import shutil
import os
import yaml
import toml
import importlib
import inspect
import ast
import re

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """工具分类"""
    CORE_DEVELOPMENT = "core_development"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    QUALITY_ASSURANCE = "quality_assurance"
    DEPLOYMENT_OPERATIONS = "deployment_operations"

class ToolType(Enum):
    """工具类型"""
    # 核心开发工具
    CODE_ANALYZER = "code_analyzer"
    CODE_GENERATOR = "code_generator"
    DEBUGGER = "debugger"
    REFACTORING_TOOL = "refactoring_tool"
    TEST_GENERATOR = "test_generator"
    
    # 性能优化工具
    PERFORMANCE_ANALYZER = "performance_analyzer"
    CODE_OPTIMIZER = "code_optimizer"
    BENCHMARK_TOOL = "benchmark_tool"
    
    # 质量保证工具
    CODE_QUALITY_CHECKER = "code_quality_checker"
    CODE_FORMATTER = "code_formatter"
    DOCUMENTATION_GENERATOR = "documentation_generator"
    
    # 部署运维工具
    DEPLOYMENT_TOOL = "deployment_tool"
    MONITORING_TOOL = "monitoring_tool"
    SECURITY_SCANNER = "security_scanner"

class ToolStatus(Enum):
    """工具状态"""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPDATING = "updating"
    DEPRECATED = "deprecated"

class ExecutionMode(Enum):
    """执行模式"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    STREAMING = "streaming"
    BATCH = "batch"

class SecurityLevel(Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ToolCapability:
    """工具能力"""
    capability_id: str
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    supported_languages: List[str] = field(default_factory=list)
    complexity_level: str = "medium"  # low, medium, high
    execution_time_estimate: int = 30  # 秒
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

@dataclass
class ToolMetadata:
    """工具元数据"""
    tool_id: str
    name: str
    version: str
    description: str
    category: ToolCategory
    tool_type: ToolType
    capabilities: List[ToolCapability]
    author: str
    license: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    documentation: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    supported_platforms: List[str] = field(default_factory=list)
    min_python_version: str = "3.8"
    max_python_version: Optional[str] = None
    installation_requirements: List[str] = field(default_factory=list)
    configuration_schema: Dict[str, Any] = field(default_factory=dict)
    api_schema: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ToolInstance:
    """工具实例"""
    instance_id: str
    tool_id: str
    status: ToolStatus
    configuration: Dict[str, Any]
    execution_mode: ExecutionMode
    security_level: SecurityLevel
    resource_allocation: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    success_rate: float = 1.0
    average_execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ToolExecution:
    """工具执行记录"""
    execution_id: str
    instance_id: str
    tool_id: str
    user_id: str
    project_id: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any] = field(default_factory=dict)
    execution_mode: ExecutionMode
    status: str = "pending"  # pending, running, completed, failed, cancelled
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    user_feedback: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ToolCollaboration:
    """工具协作"""
    collaboration_id: str
    primary_tool_id: str
    secondary_tool_ids: List[str]
    collaboration_type: str  # pipeline, parallel, conditional, feedback
    workflow_definition: Dict[str, Any]
    input_mapping: Dict[str, Any] = field(default_factory=dict)
    output_mapping: Dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.0
    average_execution_time: float = 0.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class ZenToolRegistry:
    """Zen MCP工具注册器"""
    
    def __init__(self, config_path: str = "./zen_mcp_config.json"):
        """初始化Zen工具注册器"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 工具管理
        self.registered_tools: Dict[str, ToolMetadata] = {}
        self.tool_instances: Dict[str, ToolInstance] = {}
        self.execution_history: List[ToolExecution] = []
        self.tool_collaborations: Dict[str, ToolCollaboration] = {}
        
        # 工具发现和匹配
        self.tool_index: Dict[str, Set[str]] = defaultdict(set)  # 能力 -> 工具ID集合
        self.capability_graph: Dict[str, List[str]] = defaultdict(list)  # 工具依赖图
        
        # 性能监控
        self.performance_metrics: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.usage_statistics: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 安全和权限
        self.security_policies: Dict[str, Dict[str, Any]] = {}
        self.access_control: Dict[str, Set[str]] = defaultdict(set)  # 用户 -> 工具权限
        
        # 存储
        self.data_dir = Path(self.config.get("data_dir", "./zen_mcp_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "zen_tools.db"
        
        # 工具路径
        self.tools_dir = self.data_dir / "tools"
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        # 加载数据
        self._load_persistent_data()
        
        # 注册内置工具
        self._register_builtin_tools()
        
        # 启动后台任务
        self._start_background_tasks()
        
        logger.info("Zen MCP工具注册器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "tool_settings": {
                "max_concurrent_executions": 20,
                "execution_timeout": 300,
                "retry_attempts": 3,
                "enable_caching": True,
                "cache_ttl": 3600,
                "enable_monitoring": True,
                "monitoring_interval": 30
            },
            "security_settings": {
                "enable_sandboxing": True,
                "default_security_level": "medium",
                "allowed_file_extensions": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"],
                "blocked_commands": ["rm", "del", "format", "shutdown"],
                "resource_limits": {
                    "max_memory_mb": 1024,
                    "max_cpu_percent": 80,
                    "max_execution_time": 300,
                    "max_file_size_mb": 100
                }
            },
            "collaboration_settings": {
                "enable_tool_collaboration": True,
                "max_collaboration_depth": 5,
                "collaboration_timeout": 600,
                "enable_workflow_optimization": True
            },
            "performance_settings": {
                "enable_performance_optimization": True,
                "performance_threshold": 0.8,
                "optimization_interval": 3600,
                "metrics_retention_days": 30
            },
            "discovery_settings": {
                "enable_auto_discovery": True,
                "discovery_paths": ["./tools", "./plugins", "./extensions"],
                "discovery_interval": 1800,
                "enable_remote_discovery": False
            },
            "data_dir": "./zen_mcp_data",
            "enable_logging": True,
            "log_level": "INFO"
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
                
                # 创建工具元数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tool_metadata (
                        tool_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        version TEXT,
                        description TEXT,
                        category TEXT,
                        tool_type TEXT,
                        capabilities TEXT,
                        author TEXT,
                        license TEXT,
                        homepage TEXT,
                        repository TEXT,
                        documentation TEXT,
                        tags TEXT,
                        supported_platforms TEXT,
                        min_python_version TEXT,
                        max_python_version TEXT,
                        installation_requirements TEXT,
                        configuration_schema TEXT,
                        api_schema TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                ''')
                
                # 创建工具实例表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tool_instances (
                        instance_id TEXT PRIMARY KEY,
                        tool_id TEXT NOT NULL,
                        status TEXT,
                        configuration TEXT,
                        execution_mode TEXT,
                        security_level TEXT,
                        resource_allocation TEXT,
                        performance_metrics TEXT,
                        error_log TEXT,
                        last_used TIMESTAMP,
                        usage_count INTEGER,
                        success_rate REAL,
                        average_execution_time REAL,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        FOREIGN KEY (tool_id) REFERENCES tool_metadata (tool_id)
                    )
                ''')
                
                # 创建执行记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tool_executions (
                        execution_id TEXT PRIMARY KEY,
                        instance_id TEXT NOT NULL,
                        tool_id TEXT NOT NULL,
                        user_id TEXT,
                        project_id TEXT,
                        input_data TEXT,
                        output_data TEXT,
                        execution_mode TEXT,
                        status TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        execution_time REAL,
                        resource_usage TEXT,
                        error_message TEXT,
                        quality_score REAL,
                        user_feedback TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP,
                        FOREIGN KEY (instance_id) REFERENCES tool_instances (instance_id)
                    )
                ''')
                
                # 创建工具协作表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tool_collaborations (
                        collaboration_id TEXT PRIMARY KEY,
                        primary_tool_id TEXT NOT NULL,
                        secondary_tool_ids TEXT,
                        collaboration_type TEXT,
                        workflow_definition TEXT,
                        input_mapping TEXT,
                        output_mapping TEXT,
                        success_rate REAL,
                        average_execution_time REAL,
                        usage_count INTEGER,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_category ON tool_metadata(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tool_type ON tool_metadata(tool_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_instance_tool ON tool_instances(tool_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_instance_status ON tool_instances(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_tool ON tool_executions(tool_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_user ON tool_executions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_status ON tool_executions(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_collaboration_primary ON tool_collaborations(primary_tool_id)')
                
                conn.commit()
                logger.info("Zen工具数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _load_persistent_data(self):
        """加载持久化数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 加载工具元数据
                cursor.execute('SELECT * FROM tool_metadata')
                for row in cursor.fetchall():
                    tool = self._row_to_tool_metadata(row)
                    self.registered_tools[tool.tool_id] = tool
                    self._update_tool_index(tool)
                
                # 加载工具实例
                cursor.execute('SELECT * FROM tool_instances')
                for row in cursor.fetchall():
                    instance = self._row_to_tool_instance(row)
                    self.tool_instances[instance.instance_id] = instance
                
                # 加载执行历史
                cursor.execute('SELECT * FROM tool_executions ORDER BY created_at DESC LIMIT 1000')
                for row in cursor.fetchall():
                    execution = self._row_to_tool_execution(row)
                    self.execution_history.append(execution)
                
                # 加载工具协作
                cursor.execute('SELECT * FROM tool_collaborations')
                for row in cursor.fetchall():
                    collaboration = self._row_to_tool_collaboration(row)
                    self.tool_collaborations[collaboration.collaboration_id] = collaboration
            
            logger.info(f"加载 {len(self.registered_tools)} 个工具和 {len(self.tool_instances)} 个实例")
            
        except Exception as e:
            logger.warning(f"加载持久化数据失败: {e}")
    
    def _row_to_tool_metadata(self, row) -> ToolMetadata:
        """数据库行转工具元数据对象"""
        capabilities = json.loads(row[5]) if row[5] else []
        capabilities_objects = [
            ToolCapability(**cap) if isinstance(cap, dict) else cap
            for cap in capabilities
        ]
        
        return ToolMetadata(
            tool_id=row[0],
            name=row[1],
            version=row[2] or "1.0.0",
            description=row[3] or "",
            category=ToolCategory(row[4]) if row[4] else ToolCategory.CORE_DEVELOPMENT,
            tool_type=ToolType(row[5]) if row[5] else ToolType.CODE_ANALYZER,
            capabilities=capabilities_objects,
            author=row[7] or "",
            license=row[8] or "MIT",
            homepage=row[9],
            repository=row[10],
            documentation=row[11],
            tags=json.loads(row[12]) if row[12] else [],
            supported_platforms=json.loads(row[13]) if row[13] else [],
            min_python_version=row[14] or "3.8",
            max_python_version=row[15],
            installation_requirements=json.loads(row[16]) if row[16] else [],
            configuration_schema=json.loads(row[17]) if row[17] else {},
            api_schema=json.loads(row[18]) if row[18] else {},
            created_at=datetime.fromisoformat(row[19]) if row[19] else datetime.now(),
            updated_at=datetime.fromisoformat(row[20]) if row[20] else datetime.now()
        )
    
    def _row_to_tool_instance(self, row) -> ToolInstance:
        """数据库行转工具实例对象"""
        return ToolInstance(
            instance_id=row[0],
            tool_id=row[1],
            status=ToolStatus(row[2]) if row[2] else ToolStatus.REGISTERED,
            configuration=json.loads(row[3]) if row[3] else {},
            execution_mode=ExecutionMode(row[4]) if row[4] else ExecutionMode.SYNCHRONOUS,
            security_level=SecurityLevel(row[5]) if row[5] else SecurityLevel.MEDIUM,
            resource_allocation=json.loads(row[6]) if row[6] else {},
            performance_metrics=json.loads(row[7]) if row[7] else {},
            error_log=json.loads(row[8]) if row[8] else [],
            last_used=datetime.fromisoformat(row[9]) if row[9] else None,
            usage_count=row[10] or 0,
            success_rate=row[11] or 1.0,
            average_execution_time=row[12] or 0.0,
            created_at=datetime.fromisoformat(row[13]) if row[13] else datetime.now(),
            updated_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now()
        )
    
    def _row_to_tool_execution(self, row) -> ToolExecution:
        """数据库行转工具执行对象"""
        return ToolExecution(
            execution_id=row[0],
            instance_id=row[1],
            tool_id=row[2],
            user_id=row[3] or "",
            project_id=row[4] or "",
            input_data=json.loads(row[5]) if row[5] else {},
            output_data=json.loads(row[6]) if row[6] else {},
            execution_mode=ExecutionMode(row[7]) if row[7] else ExecutionMode.SYNCHRONOUS,
            status=row[8] or "pending",
            start_time=datetime.fromisoformat(row[9]) if row[9] else None,
            end_time=datetime.fromisoformat(row[10]) if row[10] else None,
            execution_time=row[11],
            resource_usage=json.loads(row[12]) if row[12] else {},
            error_message=row[13],
            quality_score=row[14],
            user_feedback=json.loads(row[15]) if row[15] else None,
            metadata=json.loads(row[16]) if row[16] else {},
            created_at=datetime.fromisoformat(row[17]) if row[17] else datetime.now()
        )
    
    def _row_to_tool_collaboration(self, row) -> ToolCollaboration:
        """数据库行转工具协作对象"""
        return ToolCollaboration(
            collaboration_id=row[0],
            primary_tool_id=row[1],
            secondary_tool_ids=json.loads(row[2]) if row[2] else [],
            collaboration_type=row[3] or "pipeline",
            workflow_definition=json.loads(row[4]) if row[4] else {},
            input_mapping=json.loads(row[5]) if row[5] else {},
            output_mapping=json.loads(row[6]) if row[6] else {},
            success_rate=row[7] or 0.0,
            average_execution_time=row[8] or 0.0,
            usage_count=row[9] or 0,
            created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
            updated_at=datetime.fromisoformat(row[11]) if row[11] else datetime.now()
        )
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        try:
            # 核心开发工具
            self._register_core_development_tools()
            
            # 性能优化工具
            self._register_performance_optimization_tools()
            
            # 质量保证工具
            self._register_quality_assurance_tools()
            
            # 部署运维工具
            self._register_deployment_operations_tools()
            
            logger.info(f"注册 {len(self.registered_tools)} 个内置工具")
            
        except Exception as e:
            logger.error(f"注册内置工具失败: {e}")
    
    def _register_core_development_tools(self):
        """注册核心开发工具"""
        # 1. 代码分析器
        code_analyzer = ToolMetadata(
            tool_id="zen_code_analyzer",
            name="Zen代码分析器",
            version="1.0.0",
            description="智能代码分析工具，支持多种编程语言的语法、复杂度、质量分析",
            category=ToolCategory.CORE_DEVELOPMENT,
            tool_type=ToolType.CODE_ANALYZER,
            capabilities=[
                ToolCapability(
                    capability_id="syntax_analysis",
                    name="语法分析",
                    description="分析代码语法错误和警告",
                    input_types=["code", "file"],
                    output_types=["analysis_report", "issues_list"],
                    supported_languages=["python", "javascript", "java", "cpp", "go", "rust"],
                    complexity_level="low",
                    execution_time_estimate=15
                ),
                ToolCapability(
                    capability_id="complexity_analysis",
                    name="复杂度分析",
                    description="计算代码复杂度指标",
                    input_types=["code", "file"],
                    output_types=["complexity_metrics", "visualization"],
                    supported_languages=["python", "javascript", "java", "cpp"],
                    complexity_level="medium",
                    execution_time_estimate=30
                ),
                ToolCapability(
                    capability_id="quality_assessment",
                    name="质量评估",
                    description="评估代码质量和可维护性",
                    input_types=["code", "file", "project"],
                    output_types=["quality_score", "recommendations"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="high",
                    execution_time_estimate=60
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["analysis", "quality", "complexity", "syntax"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["pylint", "flake8", "mypy", "radon"]
        )
        
        # 2. 代码生成器
        code_generator = ToolMetadata(
            tool_id="zen_code_generator",
            name="Zen代码生成器",
            version="1.0.0",
            description="AI驱动的智能代码生成工具，支持多种编程模式和框架",
            category=ToolCategory.CORE_DEVELOPMENT,
            tool_type=ToolType.CODE_GENERATOR,
            capabilities=[
                ToolCapability(
                    capability_id="function_generation",
                    name="函数生成",
                    description="根据描述生成函数代码",
                    input_types=["description", "specification"],
                    output_types=["code", "documentation"],
                    supported_languages=["python", "javascript", "java", "cpp", "go"],
                    complexity_level="medium",
                    execution_time_estimate=45
                ),
                ToolCapability(
                    capability_id="class_generation",
                    name="类生成",
                    description="生成完整的类结构和方法",
                    input_types=["specification", "uml"],
                    output_types=["code", "tests", "documentation"],
                    supported_languages=["python", "java", "cpp"],
                    complexity_level="high",
                    execution_time_estimate=90
                ),
                ToolCapability(
                    capability_id="api_generation",
                    name="API生成",
                    description="生成RESTful API和相关代码",
                    input_types=["api_spec", "openapi"],
                    output_types=["server_code", "client_code", "documentation"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="high",
                    execution_time_estimate=120
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["generation", "ai", "automation", "api"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["openai", "transformers", "jinja2"]
        )
        
        # 3. 调试器
        debugger = ToolMetadata(
            tool_id="zen_debugger",
            name="Zen智能调试器",
            version="1.0.0",
            description="智能调试工具，自动检测和修复常见编程错误",
            category=ToolCategory.CORE_DEVELOPMENT,
            tool_type=ToolType.DEBUGGER,
            capabilities=[
                ToolCapability(
                    capability_id="error_detection",
                    name="错误检测",
                    description="自动检测代码中的错误和异常",
                    input_types=["code", "logs", "stacktrace"],
                    output_types=["error_report", "suggestions"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="medium",
                    execution_time_estimate=30
                ),
                ToolCapability(
                    capability_id="auto_fix",
                    name="自动修复",
                    description="自动修复常见的编程错误",
                    input_types=["code", "error_report"],
                    output_types=["fixed_code", "explanation"],
                    supported_languages=["python", "javascript"],
                    complexity_level="high",
                    execution_time_estimate=60
                ),
                ToolCapability(
                    capability_id="performance_debugging",
                    name="性能调试",
                    description="检测和分析性能瓶颈",
                    input_types=["code", "profiling_data"],
                    output_types=["performance_report", "optimization_suggestions"],
                    supported_languages=["python", "java"],
                    complexity_level="high",
                    execution_time_estimate=90
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["debugging", "error_detection", "auto_fix", "performance"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["pdb", "ipdb", "py-spy", "memory_profiler"]
        )
        
        # 4. 重构工具
        refactoring_tool = ToolMetadata(
            tool_id="zen_refactoring_tool",
            name="Zen重构工具",
            version="1.0.0",
            description="智能代码重构工具，提供安全的代码结构优化",
            category=ToolCategory.CORE_DEVELOPMENT,
            tool_type=ToolType.REFACTORING_TOOL,
            capabilities=[
                ToolCapability(
                    capability_id="extract_method",
                    name="提取方法",
                    description="将代码块提取为独立方法",
                    input_types=["code", "selection"],
                    output_types=["refactored_code", "diff"],
                    supported_languages=["python", "java", "javascript"],
                    complexity_level="medium",
                    execution_time_estimate=30
                ),
                ToolCapability(
                    capability_id="rename_refactoring",
                    name="重命名重构",
                    description="安全地重命名变量、方法和类",
                    input_types=["code", "old_name", "new_name"],
                    output_types=["refactored_code", "changes_summary"],
                    supported_languages=["python", "java", "javascript", "cpp"],
                    complexity_level="low",
                    execution_time_estimate=15
                ),
                ToolCapability(
                    capability_id="structure_optimization",
                    name="结构优化",
                    description="优化代码结构和设计模式",
                    input_types=["code", "project"],
                    output_types=["optimized_code", "architecture_suggestions"],
                    supported_languages=["python", "java"],
                    complexity_level="high",
                    execution_time_estimate=120
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["refactoring", "optimization", "structure", "patterns"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["rope", "jedi", "ast"]
        )
        
        # 5. 测试生成器
        test_generator = ToolMetadata(
            tool_id="zen_test_generator",
            name="Zen测试生成器",
            version="1.0.0",
            description="智能测试用例生成工具，自动创建单元测试和集成测试",
            category=ToolCategory.CORE_DEVELOPMENT,
            tool_type=ToolType.TEST_GENERATOR,
            capabilities=[
                ToolCapability(
                    capability_id="unit_test_generation",
                    name="单元测试生成",
                    description="为函数和类生成单元测试",
                    input_types=["code", "function", "class"],
                    output_types=["test_code", "test_data"],
                    supported_languages=["python", "java", "javascript"],
                    complexity_level="medium",
                    execution_time_estimate=45
                ),
                ToolCapability(
                    capability_id="integration_test_generation",
                    name="集成测试生成",
                    description="生成API和模块集成测试",
                    input_types=["api_spec", "module_interface"],
                    output_types=["test_suite", "test_scenarios"],
                    supported_languages=["python", "javascript"],
                    complexity_level="high",
                    execution_time_estimate=90
                ),
                ToolCapability(
                    capability_id="test_data_generation",
                    name="测试数据生成",
                    description="生成测试所需的模拟数据",
                    input_types=["schema", "specification"],
                    output_types=["test_data", "fixtures"],
                    supported_languages=["python", "javascript", "json"],
                    complexity_level="low",
                    execution_time_estimate=20
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["testing", "unit_tests", "integration_tests", "automation"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["pytest", "unittest", "faker", "hypothesis"]
        )
        
        # 注册工具
        tools = [code_analyzer, code_generator, debugger, refactoring_tool, test_generator]
        for tool in tools:
            self.registered_tools[tool.tool_id] = tool
            self._update_tool_index(tool)
    
    def _register_performance_optimization_tools(self):
        """注册性能优化工具"""
        # 1. 性能分析器
        performance_analyzer = ToolMetadata(
            tool_id="zen_performance_analyzer",
            name="Zen性能分析器",
            version="1.0.0",
            description="深度性能分析工具，识别性能瓶颈和优化机会",
            category=ToolCategory.PERFORMANCE_OPTIMIZATION,
            tool_type=ToolType.PERFORMANCE_ANALYZER,
            capabilities=[
                ToolCapability(
                    capability_id="cpu_profiling",
                    name="CPU性能分析",
                    description="分析CPU使用情况和热点函数",
                    input_types=["code", "executable"],
                    output_types=["profile_report", "hotspots"],
                    supported_languages=["python", "java", "cpp"],
                    complexity_level="medium",
                    execution_time_estimate=60
                ),
                ToolCapability(
                    capability_id="memory_profiling",
                    name="内存性能分析",
                    description="分析内存使用和泄漏",
                    input_types=["code", "executable"],
                    output_types=["memory_report", "leak_detection"],
                    supported_languages=["python", "java", "cpp"],
                    complexity_level="high",
                    execution_time_estimate=90
                ),
                ToolCapability(
                    capability_id="io_profiling",
                    name="IO性能分析",
                    description="分析文件和网络IO性能",
                    input_types=["code", "logs"],
                    output_types=["io_report", "bottlenecks"],
                    supported_languages=["python", "java"],
                    complexity_level="medium",
                    execution_time_estimate=45
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["performance", "profiling", "optimization", "analysis"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["py-spy", "memory_profiler", "line_profiler", "psutil"]
        )
        
        # 2. 代码优化器
        code_optimizer = ToolMetadata(
            tool_id="zen_code_optimizer",
            name="Zen代码优化器",
            version="1.0.0",
            description="智能代码优化工具，自动优化代码性能和效率",
            category=ToolCategory.PERFORMANCE_OPTIMIZATION,
            tool_type=ToolType.CODE_OPTIMIZER,
            capabilities=[
                ToolCapability(
                    capability_id="algorithm_optimization",
                    name="算法优化",
                    description="优化算法复杂度和效率",
                    input_types=["code", "algorithm"],
                    output_types=["optimized_code", "performance_comparison"],
                    supported_languages=["python", "java", "cpp"],
                    complexity_level="high",
                    execution_time_estimate=120
                ),
                ToolCapability(
                    capability_id="loop_optimization",
                    name="循环优化",
                    description="优化循环结构和迭代逻辑",
                    input_types=["code", "loop_block"],
                    output_types=["optimized_code", "speedup_analysis"],
                    supported_languages=["python", "java", "cpp"],
                    complexity_level="medium",
                    execution_time_estimate=45
                ),
                ToolCapability(
                    capability_id="data_structure_optimization",
                    name="数据结构优化",
                    description="优化数据结构选择和使用",
                    input_types=["code", "data_usage"],
                    output_types=["optimized_code", "structure_recommendations"],
                    supported_languages=["python", "java"],
                    complexity_level="high",
                    execution_time_estimate=90
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["optimization", "performance", "algorithms", "efficiency"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["numpy", "scipy", "numba", "cython"]
        )
        
        # 3. 基准测试工具
        benchmark_tool = ToolMetadata(
            tool_id="zen_benchmark_tool",
            name="Zen基准测试工具",
            version="1.0.0",
            description="全面的性能基准测试工具，量化代码性能表现",
            category=ToolCategory.PERFORMANCE_OPTIMIZATION,
            tool_type=ToolType.BENCHMARK_TOOL,
            capabilities=[
                ToolCapability(
                    capability_id="execution_benchmarking",
                    name="执行基准测试",
                    description="测量代码执行时间和性能",
                    input_types=["code", "function"],
                    output_types=["benchmark_results", "statistics"],
                    supported_languages=["python", "java", "cpp"],
                    complexity_level="low",
                    execution_time_estimate=30
                ),
                ToolCapability(
                    capability_id="load_testing",
                    name="负载测试",
                    description="测试系统在高负载下的性能",
                    input_types=["application", "test_scenarios"],
                    output_types=["load_test_report", "performance_metrics"],
                    supported_languages=["python", "javascript"],
                    complexity_level="high",
                    execution_time_estimate=180
                ),
                ToolCapability(
                    capability_id="comparative_benchmarking",
                    name="对比基准测试",
                    description="比较不同实现的性能差异",
                    input_types=["code_variants", "test_cases"],
                    output_types=["comparison_report", "recommendations"],
                    supported_languages=["python", "java"],
                    complexity_level="medium",
                    execution_time_estimate=60
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["benchmarking", "performance", "testing", "comparison"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["pytest-benchmark", "locust", "ab", "wrk"]
        )
        
        # 注册工具
        tools = [performance_analyzer, code_optimizer, benchmark_tool]
        for tool in tools:
            self.registered_tools[tool.tool_id] = tool
            self._update_tool_index(tool)
    
    def _register_quality_assurance_tools(self):
        """注册质量保证工具"""
        # 1. 代码质量检查器
        quality_checker = ToolMetadata(
            tool_id="zen_quality_checker",
            name="Zen代码质量检查器",
            version="1.0.0",
            description="全面的代码质量检查工具，确保代码符合最佳实践",
            category=ToolCategory.QUALITY_ASSURANCE,
            tool_type=ToolType.CODE_QUALITY_CHECKER,
            capabilities=[
                ToolCapability(
                    capability_id="style_checking",
                    name="代码风格检查",
                    description="检查代码风格和格式规范",
                    input_types=["code", "file", "project"],
                    output_types=["style_report", "violations"],
                    supported_languages=["python", "javascript", "java", "cpp"],
                    complexity_level="low",
                    execution_time_estimate=20
                ),
                ToolCapability(
                    capability_id="security_scanning",
                    name="安全扫描",
                    description="检测代码中的安全漏洞",
                    input_types=["code", "project"],
                    output_types=["security_report", "vulnerabilities"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="high",
                    execution_time_estimate=90
                ),
                ToolCapability(
                    capability_id="best_practices_checking",
                    name="最佳实践检查",
                    description="检查代码是否遵循最佳实践",
                    input_types=["code", "project"],
                    output_types=["practices_report", "recommendations"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="medium",
                    execution_time_estimate=45
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["quality", "style", "security", "best_practices"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["pylint", "flake8", "bandit", "safety"]
        )
        
        # 2. 代码格式化器
        code_formatter = ToolMetadata(
            tool_id="zen_code_formatter",
            name="Zen代码格式化器",
            version="1.0.0",
            description="智能代码格式化工具，统一代码风格和格式",
            category=ToolCategory.QUALITY_ASSURANCE,
            tool_type=ToolType.CODE_FORMATTER,
            capabilities=[
                ToolCapability(
                    capability_id="auto_formatting",
                    name="自动格式化",
                    description="自动格式化代码风格",
                    input_types=["code", "file"],
                    output_types=["formatted_code", "changes_summary"],
                    supported_languages=["python", "javascript", "java", "cpp", "go"],
                    complexity_level="low",
                    execution_time_estimate=10
                ),
                ToolCapability(
                    capability_id="custom_style_formatting",
                    name="自定义风格格式化",
                    description="根据自定义规则格式化代码",
                    input_types=["code", "style_config"],
                    output_types=["formatted_code", "style_report"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="medium",
                    execution_time_estimate=20
                ),
                ToolCapability(
                    capability_id="import_sorting",
                    name="导入排序",
                    description="自动排序和组织导入语句",
                    input_types=["code", "file"],
                    output_types=["sorted_code", "import_analysis"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="low",
                    execution_time_estimate=5
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["formatting", "style", "consistency", "automation"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["black", "prettier", "autopep8", "isort"]
        )
        
        # 3. 文档生成器
        documentation_generator = ToolMetadata(
            tool_id="zen_documentation_generator",
            name="Zen文档生成器",
            version="1.0.0",
            description="智能文档生成工具，自动创建API文档和代码说明",
            category=ToolCategory.QUALITY_ASSURANCE,
            tool_type=ToolType.DOCUMENTATION_GENERATOR,
            capabilities=[
                ToolCapability(
                    capability_id="api_documentation",
                    name="API文档生成",
                    description="生成API接口文档",
                    input_types=["code", "api_spec"],
                    output_types=["api_docs", "interactive_docs"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="medium",
                    execution_time_estimate=45
                ),
                ToolCapability(
                    capability_id="code_documentation",
                    name="代码文档生成",
                    description="生成代码注释和说明文档",
                    input_types=["code", "project"],
                    output_types=["code_docs", "readme"],
                    supported_languages=["python", "javascript", "java", "cpp"],
                    complexity_level="high",
                    execution_time_estimate=90
                ),
                ToolCapability(
                    capability_id="user_manual_generation",
                    name="用户手册生成",
                    description="生成用户使用手册和指南",
                    input_types=["application", "features"],
                    output_types=["user_manual", "tutorials"],
                    supported_languages=["markdown", "html"],
                    complexity_level="high",
                    execution_time_estimate=120
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["documentation", "api", "manual", "generation"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["sphinx", "mkdocs", "pydoc", "jsdoc"]
        )
        
        # 注册工具
        tools = [quality_checker, code_formatter, documentation_generator]
        for tool in tools:
            self.registered_tools[tool.tool_id] = tool
            self._update_tool_index(tool)
    
    def _register_deployment_operations_tools(self):
        """注册部署运维工具"""
        # 1. 部署工具
        deployment_tool = ToolMetadata(
            tool_id="zen_deployment_tool",
            name="Zen部署工具",
            version="1.0.0",
            description="智能部署工具，支持多平台自动化部署和配置",
            category=ToolCategory.DEPLOYMENT_OPERATIONS,
            tool_type=ToolType.DEPLOYMENT_TOOL,
            capabilities=[
                ToolCapability(
                    capability_id="containerized_deployment",
                    name="容器化部署",
                    description="使用Docker进行容器化部署",
                    input_types=["application", "dockerfile"],
                    output_types=["container_image", "deployment_config"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="medium",
                    execution_time_estimate=60
                ),
                ToolCapability(
                    capability_id="cloud_deployment",
                    name="云平台部署",
                    description="部署到云平台（AWS、Azure、GCP）",
                    input_types=["application", "cloud_config"],
                    output_types=["deployment_status", "service_urls"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="high",
                    execution_time_estimate=180
                ),
                ToolCapability(
                    capability_id="ci_cd_integration",
                    name="CI/CD集成",
                    description="集成持续集成和部署流水线",
                    input_types=["project", "pipeline_config"],
                    output_types=["pipeline_setup", "automation_scripts"],
                    supported_languages=["yaml", "json"],
                    complexity_level="high",
                    execution_time_estimate=120
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["deployment", "docker", "cloud", "ci_cd"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["docker", "kubectl", "terraform", "ansible"]
        )
        
        # 2. 监控工具
        monitoring_tool = ToolMetadata(
            tool_id="zen_monitoring_tool",
            name="Zen监控工具",
            version="1.0.0",
            description="全面的应用监控工具，实时跟踪性能和健康状态",
            category=ToolCategory.DEPLOYMENT_OPERATIONS,
            tool_type=ToolType.MONITORING_TOOL,
            capabilities=[
                ToolCapability(
                    capability_id="performance_monitoring",
                    name="性能监控",
                    description="监控应用性能指标",
                    input_types=["application", "metrics_config"],
                    output_types=["performance_dashboard", "alerts"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="medium",
                    execution_time_estimate=45
                ),
                ToolCapability(
                    capability_id="log_monitoring",
                    name="日志监控",
                    description="监控和分析应用日志",
                    input_types=["logs", "log_config"],
                    output_types=["log_analysis", "error_alerts"],
                    supported_languages=["text", "json"],
                    complexity_level="medium",
                    execution_time_estimate=30
                ),
                ToolCapability(
                    capability_id="health_checking",
                    name="健康检查",
                    description="检查应用和服务健康状态",
                    input_types=["service_endpoints", "health_config"],
                    output_types=["health_report", "status_dashboard"],
                    supported_languages=["http", "tcp"],
                    complexity_level="low",
                    execution_time_estimate=15
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["monitoring", "performance", "logs", "health"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["prometheus", "grafana", "elk", "datadog"]
        )
        
        # 3. 安全扫描器
        security_scanner = ToolMetadata(
            tool_id="zen_security_scanner",
            name="Zen安全扫描器",
            version="1.0.0",
            description="全面的安全扫描工具，检测漏洞和安全风险",
            category=ToolCategory.DEPLOYMENT_OPERATIONS,
            tool_type=ToolType.SECURITY_SCANNER,
            capabilities=[
                ToolCapability(
                    capability_id="vulnerability_scanning",
                    name="漏洞扫描",
                    description="扫描已知安全漏洞",
                    input_types=["code", "dependencies"],
                    output_types=["vulnerability_report", "risk_assessment"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="high",
                    execution_time_estimate=90
                ),
                ToolCapability(
                    capability_id="dependency_scanning",
                    name="依赖扫描",
                    description="扫描第三方依赖的安全问题",
                    input_types=["requirements", "package_lock"],
                    output_types=["dependency_report", "security_advisories"],
                    supported_languages=["python", "javascript", "java"],
                    complexity_level="medium",
                    execution_time_estimate=45
                ),
                ToolCapability(
                    capability_id="container_scanning",
                    name="容器扫描",
                    description="扫描容器镜像的安全问题",
                    input_types=["container_image", "dockerfile"],
                    output_types=["container_security_report", "remediation_suggestions"],
                    supported_languages=["docker"],
                    complexity_level="high",
                    execution_time_estimate=120
                )
            ],
            author="Zen MCP Team",
            license="MIT",
            tags=["security", "vulnerability", "scanning", "container"],
            supported_platforms=["linux", "windows", "macos"],
            installation_requirements=["bandit", "safety", "snyk", "trivy"]
        )
        
        # 注册工具
        tools = [deployment_tool, monitoring_tool, security_scanner]
        for tool in tools:
            self.registered_tools[tool.tool_id] = tool
            self._update_tool_index(tool)
    
    def _update_tool_index(self, tool: ToolMetadata):
        """更新工具索引"""
        # 按类别索引
        self.tool_index[f"category:{tool.category.value}"].add(tool.tool_id)
        
        # 按类型索引
        self.tool_index[f"type:{tool.tool_type.value}"].add(tool.tool_id)
        
        # 按能力索引
        for capability in tool.capabilities:
            self.tool_index[f"capability:{capability.capability_id}"].add(tool.tool_id)
            
            # 按输入类型索引
            for input_type in capability.input_types:
                self.tool_index[f"input:{input_type}"].add(tool.tool_id)
            
            # 按输出类型索引
            for output_type in capability.output_types:
                self.tool_index[f"output:{output_type}"].add(tool.tool_id)
            
            # 按支持语言索引
            for language in capability.supported_languages:
                self.tool_index[f"language:{language}"].add(tool.tool_id)
        
        # 按标签索引
        for tag in tool.tags:
            self.tool_index[f"tag:{tag}"].add(tool.tool_id)
    
    def _start_background_tasks(self):
        """启动后台任务"""
        try:
            # 启动性能监控
            asyncio.create_task(self._performance_monitoring_loop())
            
            # 启动工具发现
            if self.config["discovery_settings"]["enable_auto_discovery"]:
                asyncio.create_task(self._tool_discovery_loop())
            
            # 启动健康检查
            asyncio.create_task(self._health_check_loop())
            
            logger.info("Zen工具注册器后台任务启动完成")
            
        except Exception as e:
            logger.error(f"启动后台任务失败: {e}")
    
    async def register_tool(self, tool_metadata: ToolMetadata) -> bool:
        """注册工具"""
        try:
            # 验证工具元数据
            if not self._validate_tool_metadata(tool_metadata):
                return False
            
            # 检查工具是否已存在
            if tool_metadata.tool_id in self.registered_tools:
                logger.warning(f"工具已存在: {tool_metadata.tool_id}")
                return False
            
            # 注册工具
            self.registered_tools[tool_metadata.tool_id] = tool_metadata
            self._update_tool_index(tool_metadata)
            
            # 持久化
            await self._persist_tool_metadata(tool_metadata)
            
            logger.info(f"工具注册成功: {tool_metadata.tool_id} - {tool_metadata.name}")
            return True
            
        except Exception as e:
            logger.error(f"注册工具失败: {e}")
            return False
    
    def _validate_tool_metadata(self, tool_metadata: ToolMetadata) -> bool:
        """验证工具元数据"""
        try:
            # 检查必需字段
            if not tool_metadata.tool_id or not tool_metadata.name:
                logger.error("工具ID和名称不能为空")
                return False
            
            # 检查工具ID格式
            if not re.match(r'^[a-z0-9_]+$', tool_metadata.tool_id):
                logger.error("工具ID格式无效，只能包含小写字母、数字和下划线")
                return False
            
            # 检查版本格式
            if not re.match(r'^\d+\.\d+\.\d+$', tool_metadata.version):
                logger.error("版本格式无效，应为 x.y.z 格式")
                return False
            
            # 检查能力定义
            if not tool_metadata.capabilities:
                logger.error("工具必须定义至少一个能力")
                return False
            
            for capability in tool_metadata.capabilities:
                if not capability.capability_id or not capability.name:
                    logger.error("能力ID和名称不能为空")
                    return False
                
                if not capability.input_types or not capability.output_types:
                    logger.error("能力必须定义输入和输出类型")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证工具元数据失败: {e}")
            return False
    
    async def create_tool_instance(self, tool_id: str, configuration: Dict[str, Any],
                                 execution_mode: ExecutionMode = ExecutionMode.SYNCHRONOUS,
                                 security_level: SecurityLevel = SecurityLevel.MEDIUM) -> Optional[str]:
        """创建工具实例"""
        try:
            if tool_id not in self.registered_tools:
                logger.error(f"工具未注册: {tool_id}")
                return None
            
            instance_id = f"instance_{uuid.uuid4().hex[:12]}"
            
            # 创建工具实例
            instance = ToolInstance(
                instance_id=instance_id,
                tool_id=tool_id,
                status=ToolStatus.REGISTERED,
                configuration=configuration,
                execution_mode=execution_mode,
                security_level=security_level
            )
            
            # 验证配置
            if not self._validate_tool_configuration(tool_id, configuration):
                logger.error(f"工具配置验证失败: {tool_id}")
                return None
            
            # 分配资源
            instance.resource_allocation = self._allocate_resources(tool_id, security_level)
            
            # 存储实例
            self.tool_instances[instance_id] = instance
            
            # 持久化
            await self._persist_tool_instance(instance)
            
            logger.info(f"工具实例创建成功: {instance_id} ({tool_id})")
            return instance_id
            
        except Exception as e:
            logger.error(f"创建工具实例失败: {e}")
            return None
    
    def _validate_tool_configuration(self, tool_id: str, configuration: Dict[str, Any]) -> bool:
        """验证工具配置"""
        try:
            tool = self.registered_tools[tool_id]
            
            # 如果工具定义了配置模式，进行验证
            if tool.configuration_schema:
                # 简化验证：检查必需字段
                required_fields = tool.configuration_schema.get("required", [])
                for field in required_fields:
                    if field not in configuration:
                        logger.error(f"缺少必需配置字段: {field}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证工具配置失败: {e}")
            return False
    
    def _allocate_resources(self, tool_id: str, security_level: SecurityLevel) -> Dict[str, Any]:
        """分配资源"""
        # 基于安全级别的资源限制
        resource_limits = self.config["security_settings"]["resource_limits"]
        
        security_multipliers = {
            SecurityLevel.LOW: 1.5,
            SecurityLevel.MEDIUM: 1.0,
            SecurityLevel.HIGH: 0.7,
            SecurityLevel.CRITICAL: 0.5
        }
        
        multiplier = security_multipliers.get(security_level, 1.0)
        
        return {
            "max_memory_mb": int(resource_limits["max_memory_mb"] * multiplier),
            "max_cpu_percent": int(resource_limits["max_cpu_percent"] * multiplier),
            "max_execution_time": int(resource_limits["max_execution_time"] * multiplier),
            "max_file_size_mb": int(resource_limits["max_file_size_mb"] * multiplier)
        }
    
    async def execute_tool(self, instance_id: str, input_data: Dict[str, Any],
                          user_id: str, project_id: str = "") -> Optional[str]:
        """执行工具"""
        try:
            if instance_id not in self.tool_instances:
                logger.error(f"工具实例不存在: {instance_id}")
                return None
            
            instance = self.tool_instances[instance_id]
            execution_id = f"exec_{uuid.uuid4().hex[:12]}"
            
            # 创建执行记录
            execution = ToolExecution(
                execution_id=execution_id,
                instance_id=instance_id,
                tool_id=instance.tool_id,
                user_id=user_id,
                project_id=project_id,
                input_data=input_data,
                execution_mode=instance.execution_mode
            )
            
            # 检查权限
            if not self._check_execution_permission(user_id, instance.tool_id):
                execution.status = "failed"
                execution.error_message = "权限不足"
                await self._persist_tool_execution(execution)
                return execution_id
            
            # 添加到执行历史
            self.execution_history.append(execution)
            
            # 异步执行工具
            asyncio.create_task(self._execute_tool_async(execution))
            
            logger.info(f"工具执行开始: {execution_id} ({instance.tool_id})")
            return execution_id
            
        except Exception as e:
            logger.error(f"执行工具失败: {e}")
            return None
    
    def _check_execution_permission(self, user_id: str, tool_id: str) -> bool:
        """检查执行权限"""
        # 简化权限检查：所有用户都有权限
        return True
    
    async def _execute_tool_async(self, execution: ToolExecution):
        """异步执行工具"""
        try:
            execution.status = "running"
            execution.start_time = datetime.now()
            
            instance = self.tool_instances[execution.instance_id]
            tool = self.registered_tools[execution.tool_id]
            
            # 模拟工具执行
            await asyncio.sleep(random.uniform(1, 10))  # 模拟执行时间
            
            # 生成模拟结果
            execution.output_data = {
                "result": f"Tool {execution.tool_id} executed successfully",
                "processed_data": execution.input_data,
                "execution_info": {
                    "tool_name": tool.name,
                    "version": tool.version,
                    "capabilities_used": [cap.capability_id for cap in tool.capabilities[:2]]
                }
            }
            
            execution.status = "completed"
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.quality_score = random.uniform(0.8, 0.98)
            
            # 更新实例统计
            instance.usage_count += 1
            instance.last_used = datetime.now()
            instance.average_execution_time = (
                (instance.average_execution_time * (instance.usage_count - 1) + execution.execution_time) /
                instance.usage_count
            )
            
            # 更新性能指标
            self._update_performance_metrics(execution)
            
            logger.info(f"工具执行完成: {execution.execution_id} (耗时: {execution.execution_time:.2f}秒)")
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            
            if execution.start_time:
                execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            
            logger.error(f"工具执行失败: {execution.execution_id} - {e}")
        
        finally:
            # 持久化执行记录
            await self._persist_tool_execution(execution)
            
            # 更新实例状态
            await self._persist_tool_instance(instance)
    
    def _update_performance_metrics(self, execution: ToolExecution):
        """更新性能指标"""
        tool_id = execution.tool_id
        
        # 更新工具性能统计
        self.performance_metrics[tool_id]["total_executions"] += 1
        self.performance_metrics[tool_id]["total_execution_time"] += execution.execution_time or 0
        self.performance_metrics[tool_id]["average_execution_time"] = (
            self.performance_metrics[tool_id]["total_execution_time"] /
            self.performance_metrics[tool_id]["total_executions"]
        )
        
        if execution.status == "completed":
            self.performance_metrics[tool_id]["successful_executions"] += 1
        else:
            self.performance_metrics[tool_id]["failed_executions"] += 1
        
        self.performance_metrics[tool_id]["success_rate"] = (
            self.performance_metrics[tool_id]["successful_executions"] /
            self.performance_metrics[tool_id]["total_executions"]
        )
        
        # 更新使用统计
        self.usage_statistics[tool_id]["daily_usage"] += 1
        self.usage_statistics[tool_id]["total_usage"] += 1
    
    async def search_tools(self, query: str, filters: Dict[str, Any] = None) -> List[ToolMetadata]:
        """搜索工具"""
        try:
            matching_tools = []
            filters = filters or {}
            
            # 解析查询
            query_terms = query.lower().split()
            
            for tool_id, tool in self.registered_tools.items():
                score = 0
                
                # 名称匹配
                if any(term in tool.name.lower() for term in query_terms):
                    score += 10
                
                # 描述匹配
                if any(term in tool.description.lower() for term in query_terms):
                    score += 5
                
                # 标签匹配
                for tag in tool.tags:
                    if any(term in tag.lower() for term in query_terms):
                        score += 3
                
                # 能力匹配
                for capability in tool.capabilities:
                    if any(term in capability.name.lower() for term in query_terms):
                        score += 7
                    if any(term in capability.description.lower() for term in query_terms):
                        score += 2
                
                # 应用过滤器
                if self._apply_filters(tool, filters):
                    if score > 0:
                        matching_tools.append((tool, score))
            
            # 按分数排序
            matching_tools.sort(key=lambda x: x[1], reverse=True)
            
            return [tool for tool, score in matching_tools]
            
        except Exception as e:
            logger.error(f"搜索工具失败: {e}")
            return []
    
    def _apply_filters(self, tool: ToolMetadata, filters: Dict[str, Any]) -> bool:
        """应用过滤器"""
        try:
            # 类别过滤
            if "category" in filters:
                if tool.category.value != filters["category"]:
                    return False
            
            # 类型过滤
            if "tool_type" in filters:
                if tool.tool_type.value != filters["tool_type"]:
                    return False
            
            # 语言过滤
            if "language" in filters:
                language = filters["language"]
                if not any(language in cap.supported_languages for cap in tool.capabilities):
                    return False
            
            # 标签过滤
            if "tags" in filters:
                required_tags = filters["tags"]
                if not all(tag in tool.tags for tag in required_tags):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"应用过滤器失败: {e}")
            return False
    
    async def get_tool_recommendations(self, user_id: str, context: Dict[str, Any]) -> List[ToolMetadata]:
        """获取工具推荐"""
        try:
            recommendations = []
            
            # 基于用户历史使用
            user_executions = [
                exec for exec in self.execution_history
                if exec.user_id == user_id and exec.status == "completed"
            ]
            
            # 统计用户常用工具类型
            tool_type_usage = defaultdict(int)
            for execution in user_executions[-50:]:  # 最近50次执行
                tool = self.registered_tools.get(execution.tool_id)
                if tool:
                    tool_type_usage[tool.tool_type] += 1
            
            # 基于上下文推荐
            context_language = context.get("language", "python")
            context_task = context.get("task_type", "")
            
            # 推荐相关工具
            for tool_id, tool in self.registered_tools.items():
                score = 0
                
                # 语言匹配
                if any(context_language in cap.supported_languages for cap in tool.capabilities):
                    score += 5
                
                # 任务类型匹配
                if context_task and context_task in tool.description.lower():
                    score += 8
                
                # 用户偏好
                if tool.tool_type in tool_type_usage:
                    score += tool_type_usage[tool.tool_type] * 2
                
                # 工具性能
                if tool_id in self.performance_metrics:
                    success_rate = self.performance_metrics[tool_id].get("success_rate", 0)
                    score += success_rate * 3
                
                if score > 0:
                    recommendations.append((tool, score))
            
            # 排序并返回前10个
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return [tool for tool, score in recommendations[:10]]
            
        except Exception as e:
            logger.error(f"获取工具推荐失败: {e}")
            return []
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        try:
            for execution in self.execution_history:
                if execution.execution_id == execution_id:
                    return {
                        "execution_id": execution.execution_id,
                        "tool_id": execution.tool_id,
                        "status": execution.status,
                        "start_time": execution.start_time.isoformat() if execution.start_time else None,
                        "end_time": execution.end_time.isoformat() if execution.end_time else None,
                        "execution_time": execution.execution_time,
                        "quality_score": execution.quality_score,
                        "error_message": execution.error_message,
                        "output_data": execution.output_data if execution.status == "completed" else None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"获取执行状态失败: {e}")
            return None
    
    async def get_tool_statistics(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        try:
            # 基本统计
            total_tools = len(self.registered_tools)
            total_instances = len(self.tool_instances)
            total_executions = len(self.execution_history)
            
            # 按类别统计
            category_stats = defaultdict(int)
            for tool in self.registered_tools.values():
                category_stats[tool.category.value] += 1
            
            # 按类型统计
            type_stats = defaultdict(int)
            for tool in self.registered_tools.values():
                type_stats[tool.tool_type.value] += 1
            
            # 执行统计
            completed_executions = len([e for e in self.execution_history if e.status == "completed"])
            failed_executions = len([e for e in self.execution_history if e.status == "failed"])
            success_rate = completed_executions / total_executions if total_executions > 0 else 0
            
            # 性能统计
            avg_execution_time = 0
            if completed_executions > 0:
                total_time = sum(e.execution_time for e in self.execution_history if e.execution_time)
                avg_execution_time = total_time / completed_executions
            
            return {
                "basic_stats": {
                    "total_tools": total_tools,
                    "total_instances": total_instances,
                    "total_executions": total_executions,
                    "completed_executions": completed_executions,
                    "failed_executions": failed_executions,
                    "success_rate": success_rate,
                    "average_execution_time": avg_execution_time
                },
                "category_distribution": dict(category_stats),
                "type_distribution": dict(type_stats),
                "performance_metrics": dict(self.performance_metrics),
                "usage_statistics": dict(self.usage_statistics)
            }
            
        except Exception as e:
            logger.error(f"获取工具统计失败: {e}")
            return {}
    
    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        while True:
            try:
                # 检查工具实例健康状态
                for instance_id, instance in self.tool_instances.items():
                    if instance.status == ToolStatus.ACTIVE:
                        # 检查是否长时间未使用
                        if instance.last_used:
                            idle_time = (datetime.now() - instance.last_used).total_seconds()
                            if idle_time > 3600:  # 1小时未使用
                                instance.status = ToolStatus.INACTIVE
                                await self._persist_tool_instance(instance)
                
                # 清理过期执行记录
                retention_days = self.config["performance_settings"]["metrics_retention_days"]
                cutoff_time = datetime.now() - timedelta(days=retention_days)
                
                self.execution_history = [
                    exec for exec in self.execution_history
                    if exec.created_at > cutoff_time
                ]
                
                await asyncio.sleep(self.config["tool_settings"]["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"性能监控循环错误: {e}")
                await asyncio.sleep(60)
    
    async def _tool_discovery_loop(self):
        """工具发现循环"""
        while True:
            try:
                discovery_paths = self.config["discovery_settings"]["discovery_paths"]
                
                for path in discovery_paths:
                    path_obj = Path(path)
                    if path_obj.exists():
                        await self._discover_tools_in_path(path_obj)
                
                await asyncio.sleep(self.config["discovery_settings"]["discovery_interval"])
                
            except Exception as e:
                logger.error(f"工具发现循环错误: {e}")
                await asyncio.sleep(300)
    
    async def _discover_tools_in_path(self, path: Path):
        """在指定路径发现工具"""
        try:
            # 查找工具定义文件
            for tool_file in path.glob("**/tool.json"):
                try:
                    with open(tool_file, 'r', encoding='utf-8') as f:
                        tool_data = json.load(f)
                    
                    # 转换为工具元数据
                    tool_metadata = self._convert_to_tool_metadata(tool_data)
                    
                    if tool_metadata and tool_metadata.tool_id not in self.registered_tools:
                        await self.register_tool(tool_metadata)
                        logger.info(f"自动发现并注册工具: {tool_metadata.tool_id}")
                
                except Exception as e:
                    logger.warning(f"处理工具文件失败 {tool_file}: {e}")
            
        except Exception as e:
            logger.error(f"在路径发现工具失败 {path}: {e}")
    
    def _convert_to_tool_metadata(self, tool_data: Dict[str, Any]) -> Optional[ToolMetadata]:
        """转换为工具元数据"""
        try:
            # 简化转换逻辑
            capabilities = []
            for cap_data in tool_data.get("capabilities", []):
                capability = ToolCapability(
                    capability_id=cap_data["capability_id"],
                    name=cap_data["name"],
                    description=cap_data["description"],
                    input_types=cap_data["input_types"],
                    output_types=cap_data["output_types"],
                    supported_languages=cap_data.get("supported_languages", []),
                    complexity_level=cap_data.get("complexity_level", "medium"),
                    execution_time_estimate=cap_data.get("execution_time_estimate", 30)
                )
                capabilities.append(capability)
            
            return ToolMetadata(
                tool_id=tool_data["tool_id"],
                name=tool_data["name"],
                version=tool_data.get("version", "1.0.0"),
                description=tool_data.get("description", ""),
                category=ToolCategory(tool_data.get("category", "core_development")),
                tool_type=ToolType(tool_data.get("tool_type", "code_analyzer")),
                capabilities=capabilities,
                author=tool_data.get("author", "Unknown"),
                license=tool_data.get("license", "MIT"),
                tags=tool_data.get("tags", []),
                supported_platforms=tool_data.get("supported_platforms", []),
                installation_requirements=tool_data.get("installation_requirements", [])
            )
            
        except Exception as e:
            logger.error(f"转换工具元数据失败: {e}")
            return None
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                # 检查数据库连接
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                
                # 检查工具实例状态
                error_instances = []
                for instance_id, instance in self.tool_instances.items():
                    if len(instance.error_log) > 10:  # 错误过多
                        error_instances.append(instance_id)
                
                # 处理错误实例
                for instance_id in error_instances:
                    instance = self.tool_instances[instance_id]
                    instance.status = ToolStatus.ERROR
                    await self._persist_tool_instance(instance)
                    logger.warning(f"工具实例状态异常: {instance_id}")
                
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(300)
    
    async def _persist_tool_metadata(self, tool: ToolMetadata):
        """持久化工具元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tool_metadata 
                    (tool_id, name, version, description, category, tool_type, capabilities,
                     author, license, homepage, repository, documentation, tags,
                     supported_platforms, min_python_version, max_python_version,
                     installation_requirements, configuration_schema, api_schema,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tool.tool_id,
                    tool.name,
                    tool.version,
                    tool.description,
                    tool.category.value,
                    tool.tool_type.value,
                    json.dumps([asdict(cap) for cap in tool.capabilities]),
                    tool.author,
                    tool.license,
                    tool.homepage,
                    tool.repository,
                    tool.documentation,
                    json.dumps(tool.tags),
                    json.dumps(tool.supported_platforms),
                    tool.min_python_version,
                    tool.max_python_version,
                    json.dumps(tool.installation_requirements),
                    json.dumps(tool.configuration_schema),
                    json.dumps(tool.api_schema),
                    tool.created_at.isoformat(),
                    tool.updated_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化工具元数据失败: {e}")
    
    async def _persist_tool_instance(self, instance: ToolInstance):
        """持久化工具实例"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tool_instances 
                    (instance_id, tool_id, status, configuration, execution_mode,
                     security_level, resource_allocation, performance_metrics, error_log,
                     last_used, usage_count, success_rate, average_execution_time,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    instance.instance_id,
                    instance.tool_id,
                    instance.status.value,
                    json.dumps(instance.configuration),
                    instance.execution_mode.value,
                    instance.security_level.value,
                    json.dumps(instance.resource_allocation),
                    json.dumps(instance.performance_metrics),
                    json.dumps(instance.error_log),
                    instance.last_used.isoformat() if instance.last_used else None,
                    instance.usage_count,
                    instance.success_rate,
                    instance.average_execution_time,
                    instance.created_at.isoformat(),
                    instance.updated_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化工具实例失败: {e}")
    
    async def _persist_tool_execution(self, execution: ToolExecution):
        """持久化工具执行"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tool_executions 
                    (execution_id, instance_id, tool_id, user_id, project_id, input_data,
                     output_data, execution_mode, status, start_time, end_time,
                     execution_time, resource_usage, error_message, quality_score,
                     user_feedback, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution.execution_id,
                    execution.instance_id,
                    execution.tool_id,
                    execution.user_id,
                    execution.project_id,
                    json.dumps(execution.input_data),
                    json.dumps(execution.output_data),
                    execution.execution_mode.value,
                    execution.status,
                    execution.start_time.isoformat() if execution.start_time else None,
                    execution.end_time.isoformat() if execution.end_time else None,
                    execution.execution_time,
                    json.dumps(execution.resource_usage),
                    execution.error_message,
                    execution.quality_score,
                    json.dumps(execution.user_feedback) if execution.user_feedback else None,
                    json.dumps(execution.metadata),
                    execution.created_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"持久化工具执行失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 保存所有工具元数据
            for tool in self.registered_tools.values():
                await self._persist_tool_metadata(tool)
            
            # 保存所有工具实例
            for instance in self.tool_instances.values():
                await self._persist_tool_instance(instance)
            
            # 保存执行历史
            for execution in self.execution_history[-1000:]:  # 只保存最近1000条
                await self._persist_tool_execution(execution)
            
            logger.info("Zen工具注册器清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

# 工厂函数
def get_zen_tool_registry(config_path: str = "./zen_mcp_config.json") -> ZenToolRegistry:
    """获取Zen工具注册器实例"""
    return ZenToolRegistry(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_zen_tool_registry():
        """测试Zen工具注册器"""
        registry = get_zen_tool_registry()
        
        try:
            print("🔧 Zen MCP工具注册器测试")
            
            # 获取工具统计
            print("\n📊 工具统计信息:")
            stats = await registry.get_tool_statistics()
            print(f"总工具数: {stats['basic_stats']['total_tools']}")
            print(f"工具分类分布: {stats['category_distribution']}")
            print(f"工具类型分布: {stats['type_distribution']}")
            
            # 搜索工具
            print("\n🔍 搜索代码分析工具:")
            analysis_tools = await registry.search_tools("code analysis", {"category": "core_development"})
            for tool in analysis_tools[:3]:
                print(f"  - {tool.name} ({tool.tool_id}): {tool.description[:50]}...")
            
            # 创建工具实例
            print("\n⚙️ 创建工具实例:")
            if analysis_tools:
                tool = analysis_tools[0]
                instance_id = await registry.create_tool_instance(
                    tool_id=tool.tool_id,
                    configuration={"language": "python", "strict_mode": True},
                    execution_mode=ExecutionMode.ASYNCHRONOUS
                )
                print(f"创建实例: {instance_id}")
                
                # 执行工具
                print("\n🚀 执行工具:")
                execution_id = await registry.execute_tool(
                    instance_id=instance_id,
                    input_data={
                        "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
                        "language": "python"
                    },
                    user_id="test_user",
                    project_id="test_project"
                )
                print(f"执行ID: {execution_id}")
                
                # 等待执行完成
                print("\n⏳ 等待执行完成...")
                for i in range(15):
                    status = await registry.get_execution_status(execution_id)
                    if status:
                        print(f"状态: {status['status']}")
                        if status['status'] == 'completed':
                            print(f"质量分: {status.get('quality_score', 0):.2f}")
                            print(f"执行时间: {status.get('execution_time', 0):.2f}秒")
                            break
                        elif status['status'] == 'failed':
                            print(f"错误: {status.get('error_message', 'Unknown error')}")
                            break
                    await asyncio.sleep(1)
            
            # 获取工具推荐
            print("\n🎯 获取工具推荐:")
            recommendations = await registry.get_tool_recommendations(
                user_id="test_user",
                context={"language": "python", "task_type": "optimization"}
            )
            
            print(f"推荐 {len(recommendations)} 个工具:")
            for tool in recommendations[:5]:
                print(f"  - {tool.name}: {tool.description[:50]}...")
            
            # 搜索性能优化工具
            print("\n⚡ 搜索性能优化工具:")
            perf_tools = await registry.search_tools("performance optimization")
            for tool in perf_tools[:3]:
                print(f"  - {tool.name} ({tool.tool_type.value})")
                for cap in tool.capabilities[:2]:
                    print(f"    * {cap.name}: {cap.description[:40]}...")
            
            # 搜索质量保证工具
            print("\n✅ 搜索质量保证工具:")
            qa_tools = await registry.search_tools("quality", {"category": "quality_assurance"})
            for tool in qa_tools:
                print(f"  - {tool.name}: {len(tool.capabilities)} 个能力")
            
            # 搜索部署运维工具
            print("\n🚀 搜索部署运维工具:")
            deploy_tools = await registry.search_tools("deployment monitoring", {"category": "deployment_operations"})
            for tool in deploy_tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")
            
            # 最终统计
            print("\n📈 最终统计:")
            final_stats = await registry.get_tool_statistics()
            print(f"总执行次数: {final_stats['basic_stats']['total_executions']}")
            print(f"成功率: {final_stats['basic_stats']['success_rate']:.2%}")
            print(f"平均执行时间: {final_stats['basic_stats']['average_execution_time']:.2f}秒")
            
        finally:
            # 清理
            await registry.cleanup()
    
    # 运行测试
    asyncio.run(test_zen_tool_registry())

