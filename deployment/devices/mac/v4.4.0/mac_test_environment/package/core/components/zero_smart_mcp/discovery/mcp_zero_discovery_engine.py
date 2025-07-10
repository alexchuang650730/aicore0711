#!/usr/bin/env python3
"""
MCP-Zero工具发现引擎

基于MCP-Zero数据集的智能工具发现系统，能够自动扫描、注册和管理MCP工具。
支持308个服务器和2,797个工具的大规模工具生态系统。

主要功能：
- 自动工具扫描和发现
- 工具元数据提取和分析
- 能力分析和分类
- 工具注册表管理
- 实时工具状态监控

作者: PowerAutomation Team
版本: 4.1.0
日期: 2025-01-07
"""

import asyncio
import json
import uuid
import hashlib
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import re
import yaml
from urllib.parse import urlparse, urljoin
import subprocess
import tempfile
import shutil

from ..models.tool_models import MCPTool, ToolCapability, ToolStatus

logger = logging.getLogger(__name__)

class DiscoveryStatus(Enum):
    """发现状态"""
    PENDING = "pending"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class ToolSource(Enum):
    """工具来源"""
    MCP_ZERO_REGISTRY = "mcp_zero_registry"
    GITHUB_REPOSITORY = "github_repository"
    NPM_PACKAGE = "npm_package"
    PYPI_PACKAGE = "pypi_package"
    LOCAL_DIRECTORY = "local_directory"
    REMOTE_API = "remote_api"

@dataclass
class DiscoveryTask:
    """发现任务"""
    task_id: str
    source: ToolSource
    target: str  # URL, path, or identifier
    status: DiscoveryStatus = DiscoveryStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    discovered_tools: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolRegistry:
    """工具注册表"""
    registry_id: str
    name: str
    description: str
    url: str
    tools: Dict[str, MCPTool] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    total_tools: int = 0
    active_tools: int = 0
    categories: Dict[str, int] = field(default_factory=dict)

class MCPZeroDiscoveryEngine:
    """MCP-Zero工具发现引擎"""
    
    def __init__(self, config_path: str = "./mcp_zero_config.json"):
        """初始化发现引擎"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 核心组件
        self.registries: Dict[str, ToolRegistry] = {}
        self.discovery_tasks: Dict[str, DiscoveryTask] = {}
        self.discovered_tools: Dict[str, MCPTool] = {}
        
        # 发现配置
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 10)
        self.discovery_timeout = self.config.get("discovery_timeout", 300)  # 5分钟
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.cache_duration = self.config.get("cache_duration", 3600)  # 1小时
        
        # MCP-Zero数据集配置
        self.mcp_zero_registry_url = self.config.get(
            "mcp_zero_registry_url", 
            "https://raw.githubusercontent.com/modelcontextprotocol/registry/main"
        )
        
        # 工具分析器
        self.capability_patterns = self._load_capability_patterns()
        self.category_classifiers = self._load_category_classifiers()
        
        # 缓存和存储
        self.cache_dir = Path(self.config.get("cache_dir", "./mcp_zero_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.discovery_stats = {
            "total_discoveries": 0,
            "successful_discoveries": 0,
            "failed_discoveries": 0,
            "total_tools_found": 0,
            "unique_tools": 0,
            "discovery_time_avg": 0.0
        }
        
        logger.info("MCP-Zero工具发现引擎初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "max_concurrent_tasks": 10,
            "discovery_timeout": 300,
            "retry_attempts": 3,
            "cache_duration": 3600,
            "mcp_zero_registry_url": "https://raw.githubusercontent.com/modelcontextprotocol/registry/main",
            "cache_dir": "./mcp_zero_cache",
            "enable_github_discovery": True,
            "enable_npm_discovery": True,
            "enable_pypi_discovery": True,
            "github_token": None,
            "npm_registry": "https://registry.npmjs.org",
            "pypi_registry": "https://pypi.org"
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _load_capability_patterns(self) -> Dict[str, List[str]]:
        """加载能力识别模式"""
        return {
            "file_operations": [
                r"read.*file", r"write.*file", r"create.*file", r"delete.*file",
                r"file.*system", r"directory", r"folder", r"path"
            ],
            "web_scraping": [
                r"scrape", r"crawl", r"web.*content", r"html.*parse", 
                r"extract.*data", r"web.*automation"
            ],
            "api_integration": [
                r"api.*call", r"rest.*api", r"http.*request", r"webhook",
                r"integration", r"service.*call"
            ],
            "data_processing": [
                r"process.*data", r"transform", r"convert", r"parse",
                r"analyze.*data", r"filter", r"sort", r"aggregate"
            ],
            "ai_ml": [
                r"machine.*learning", r"ai.*model", r"neural.*network",
                r"prediction", r"classification", r"nlp", r"computer.*vision"
            ],
            "database": [
                r"database", r"sql", r"query", r"table", r"record",
                r"crud", r"orm", r"migration"
            ],
            "communication": [
                r"email", r"sms", r"notification", r"message", r"chat",
                r"slack", r"discord", r"telegram"
            ],
            "automation": [
                r"automate", r"schedule", r"trigger", r"workflow",
                r"pipeline", r"batch", r"cron"
            ],
            "monitoring": [
                r"monitor", r"log", r"metric", r"alert", r"health.*check",
                r"performance", r"status", r"uptime"
            ],
            "security": [
                r"encrypt", r"decrypt", r"hash", r"auth", r"security",
                r"permission", r"access.*control", r"vulnerability"
            ]
        }
    
    def _load_category_classifiers(self) -> Dict[str, Dict[str, float]]:
        """加载分类器权重"""
        return {
            "development": {
                "file_operations": 0.8,
                "api_integration": 0.7,
                "database": 0.6,
                "automation": 0.5
            },
            "data_science": {
                "ai_ml": 0.9,
                "data_processing": 0.8,
                "database": 0.6
            },
            "web_automation": {
                "web_scraping": 0.9,
                "automation": 0.7,
                "api_integration": 0.6
            },
            "communication": {
                "communication": 0.9,
                "api_integration": 0.5
            },
            "system_admin": {
                "monitoring": 0.8,
                "security": 0.7,
                "automation": 0.6,
                "file_operations": 0.5
            }
        }
    
    async def start_discovery(self, sources: List[Dict[str, Any]] = None) -> List[str]:
        """开始工具发现"""
        if sources is None:
            sources = [
                {"type": "mcp_zero_registry", "target": self.mcp_zero_registry_url},
                {"type": "github_search", "target": "mcp-server"},
                {"type": "npm_search", "target": "@modelcontextprotocol"}
            ]
        
        task_ids = []
        
        for source_config in sources:
            task_id = await self._create_discovery_task(
                source=ToolSource(source_config["type"]),
                target=source_config["target"],
                metadata=source_config.get("metadata", {})
            )
            task_ids.append(task_id)
        
        # 并发执行发现任务
        await self._execute_discovery_tasks(task_ids)
        
        logger.info(f"工具发现完成，创建了 {len(task_ids)} 个发现任务")
        return task_ids
    
    async def _create_discovery_task(self, source: ToolSource, target: str, 
                                   metadata: Dict[str, Any] = None) -> str:
        """创建发现任务"""
        task_id = f"discovery_{uuid.uuid4().hex[:8]}"
        
        task = DiscoveryTask(
            task_id=task_id,
            source=source,
            target=target,
            metadata=metadata or {}
        )
        
        self.discovery_tasks[task_id] = task
        
        logger.info(f"创建发现任务 {task_id}: {source.value} -> {target}")
        return task_id
    
    async def _execute_discovery_tasks(self, task_ids: List[str]):
        """并发执行发现任务"""
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        async def execute_task(task_id: str):
            async with semaphore:
                await self._execute_single_discovery_task(task_id)
        
        # 并发执行所有任务
        await asyncio.gather(*[execute_task(task_id) for task_id in task_ids])
    
    async def _execute_single_discovery_task(self, task_id: str):
        """执行单个发现任务"""
        task = self.discovery_tasks[task_id]
        
        try:
            task.status = DiscoveryStatus.SCANNING
            task.started_at = datetime.now()
            
            # 根据源类型执行不同的发现逻辑
            if task.source == ToolSource.MCP_ZERO_REGISTRY:
                discovered_tools = await self._discover_from_mcp_zero_registry(task)
            elif task.source == ToolSource.GITHUB_REPOSITORY:
                discovered_tools = await self._discover_from_github(task)
            elif task.source == ToolSource.NPM_PACKAGE:
                discovered_tools = await self._discover_from_npm(task)
            elif task.source == ToolSource.PYPI_PACKAGE:
                discovered_tools = await self._discover_from_pypi(task)
            elif task.source == ToolSource.LOCAL_DIRECTORY:
                discovered_tools = await self._discover_from_local_directory(task)
            else:
                raise ValueError(f"不支持的发现源: {task.source}")
            
            # 分析发现的工具
            task.status = DiscoveryStatus.ANALYZING
            analyzed_tools = await self._analyze_discovered_tools(discovered_tools, task)
            
            # 注册工具
            for tool in analyzed_tools:
                await self._register_tool(tool)
                task.discovered_tools.append(tool.tool_id)
            
            task.status = DiscoveryStatus.COMPLETED
            task.completed_at = datetime.now()
            
            # 更新统计
            self.discovery_stats["successful_discoveries"] += 1
            self.discovery_stats["total_tools_found"] += len(analyzed_tools)
            
            logger.info(f"发现任务 {task_id} 完成，发现 {len(analyzed_tools)} 个工具")
            
        except asyncio.TimeoutError:
            task.status = DiscoveryStatus.TIMEOUT
            task.error_message = "发现任务超时"
            self.discovery_stats["failed_discoveries"] += 1
            logger.error(f"发现任务 {task_id} 超时")
            
        except Exception as e:
            task.status = DiscoveryStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            self.discovery_stats["failed_discoveries"] += 1
            logger.error(f"发现任务 {task_id} 失败: {e}")
        
        finally:
            self.discovery_stats["total_discoveries"] += 1
    
    async def _discover_from_mcp_zero_registry(self, task: DiscoveryTask) -> List[Dict[str, Any]]:
        """从MCP-Zero注册表发现工具"""
        registry_url = task.target
        discovered_tools = []
        
        async with aiohttp.ClientSession() as session:
            # 获取注册表索引
            index_url = urljoin(registry_url, "index.json")
            
            try:
                async with session.get(index_url) as response:
                    if response.status == 200:
                        registry_index = await response.json()
                    else:
                        raise Exception(f"无法获取注册表索引: {response.status}")
                
                # 遍历所有服务器
                for server_info in registry_index.get("servers", []):
                    server_id = server_info.get("id")
                    server_url = urljoin(registry_url, f"servers/{server_id}.json")
                    
                    try:
                        async with session.get(server_url) as response:
                            if response.status == 200:
                                server_data = await response.json()
                                tools = await self._extract_tools_from_server_data(server_data)
                                discovered_tools.extend(tools)
                            else:
                                logger.warning(f"无法获取服务器数据 {server_id}: {response.status}")
                    
                    except Exception as e:
                        logger.warning(f"处理服务器 {server_id} 时出错: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"从MCP-Zero注册表发现工具失败: {e}")
                raise
        
        logger.info(f"从MCP-Zero注册表发现 {len(discovered_tools)} 个工具")
        return discovered_tools
    
    async def _extract_tools_from_server_data(self, server_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从服务器数据中提取工具信息"""
        tools = []
        
        server_id = server_data.get("id", "unknown")
        server_name = server_data.get("name", server_id)
        server_description = server_data.get("description", "")
        
        # 提取工具列表
        for tool_info in server_data.get("tools", []):
            tool = {
                "tool_id": f"{server_id}_{tool_info.get('name', 'unknown')}",
                "name": tool_info.get("name", "Unknown Tool"),
                "description": tool_info.get("description", server_description),
                "server_id": server_id,
                "server_name": server_name,
                "version": server_data.get("version", "1.0.0"),
                "author": server_data.get("author", "Unknown"),
                "license": server_data.get("license", "Unknown"),
                "repository": server_data.get("repository", ""),
                "homepage": server_data.get("homepage", ""),
                "tags": server_data.get("tags", []),
                "capabilities": tool_info.get("capabilities", []),
                "input_schema": tool_info.get("inputSchema", {}),
                "output_schema": tool_info.get("outputSchema", {}),
                "examples": tool_info.get("examples", []),
                "requirements": server_data.get("requirements", {}),
                "installation": server_data.get("installation", {}),
                "configuration": tool_info.get("configuration", {}),
                "source_type": "mcp_zero_registry",
                "source_url": server_data.get("repository", ""),
                "discovered_at": datetime.now().isoformat()
            }
            tools.append(tool)
        
        return tools
    
    async def _discover_from_github(self, task: DiscoveryTask) -> List[Dict[str, Any]]:
        """从GitHub发现工具"""
        search_query = task.target
        discovered_tools = []
        
        # GitHub API搜索
        github_token = self.config.get("github_token")
        headers = {}
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        async with aiohttp.ClientSession(headers=headers) as session:
            # 搜索仓库
            search_url = f"https://api.github.com/search/repositories?q={search_query}+mcp+server&sort=stars&order=desc"
            
            try:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        search_results = await response.json()
                        
                        for repo in search_results.get("items", [])[:50]:  # 限制前50个结果
                            try:
                                tools = await self._analyze_github_repository(repo, session)
                                discovered_tools.extend(tools)
                            except Exception as e:
                                logger.warning(f"分析GitHub仓库 {repo.get('full_name')} 失败: {e}")
                                continue
                    else:
                        raise Exception(f"GitHub搜索失败: {response.status}")
            
            except Exception as e:
                logger.error(f"从GitHub发现工具失败: {e}")
                raise
        
        logger.info(f"从GitHub发现 {len(discovered_tools)} 个工具")
        return discovered_tools
    
    async def _analyze_github_repository(self, repo: Dict[str, Any], 
                                       session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """分析GitHub仓库"""
        tools = []
        
        repo_name = repo.get("full_name", "")
        repo_url = repo.get("html_url", "")
        
        # 获取package.json或setup.py等配置文件
        config_files = ["package.json", "setup.py", "pyproject.toml", "mcp.json"]
        
        for config_file in config_files:
            try:
                file_url = f"https://api.github.com/repos/{repo_name}/contents/{config_file}"
                async with session.get(file_url) as response:
                    if response.status == 200:
                        file_data = await response.json()
                        content = file_data.get("content", "")
                        
                        # 解码base64内容
                        import base64
                        decoded_content = base64.b64decode(content).decode('utf-8')
                        
                        # 分析配置文件
                        tool_info = await self._extract_tool_info_from_config(
                            decoded_content, config_file, repo
                        )
                        
                        if tool_info:
                            tools.append(tool_info)
                        break
                        
            except Exception as e:
                logger.debug(f"无法获取 {repo_name}/{config_file}: {e}")
                continue
        
        # 如果没有找到配置文件，基于仓库信息创建基础工具信息
        if not tools:
            tool_info = {
                "tool_id": f"github_{repo.get('id', 'unknown')}",
                "name": repo.get("name", "Unknown Tool"),
                "description": repo.get("description", ""),
                "version": "1.0.0",
                "author": repo.get("owner", {}).get("login", "Unknown"),
                "license": repo.get("license", {}).get("name", "Unknown") if repo.get("license") else "Unknown",
                "repository": repo_url,
                "homepage": repo.get("homepage", repo_url),
                "tags": repo.get("topics", []),
                "capabilities": [],
                "source_type": "github_repository",
                "source_url": repo_url,
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", "Unknown"),
                "discovered_at": datetime.now().isoformat()
            }
            tools.append(tool_info)
        
        return tools
    
    async def _extract_tool_info_from_config(self, content: str, config_file: str, 
                                           repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从配置文件中提取工具信息"""
        try:
            if config_file == "package.json":
                config = json.loads(content)
                return {
                    "tool_id": f"npm_{config.get('name', 'unknown').replace('/', '_')}",
                    "name": config.get("name", "Unknown Tool"),
                    "description": config.get("description", ""),
                    "version": config.get("version", "1.0.0"),
                    "author": config.get("author", "Unknown"),
                    "license": config.get("license", "Unknown"),
                    "repository": repo.get("html_url", ""),
                    "homepage": config.get("homepage", repo.get("html_url", "")),
                    "tags": config.get("keywords", []),
                    "capabilities": [],
                    "dependencies": config.get("dependencies", {}),
                    "source_type": "npm_package",
                    "source_url": repo.get("html_url", ""),
                    "discovered_at": datetime.now().isoformat()
                }
            
            elif config_file in ["setup.py", "pyproject.toml"]:
                # 简化的Python包信息提取
                return {
                    "tool_id": f"pypi_{repo.get('name', 'unknown')}",
                    "name": repo.get("name", "Unknown Tool"),
                    "description": repo.get("description", ""),
                    "version": "1.0.0",
                    "author": repo.get("owner", {}).get("login", "Unknown"),
                    "license": "Unknown",
                    "repository": repo.get("html_url", ""),
                    "homepage": repo.get("html_url", ""),
                    "tags": repo.get("topics", []),
                    "capabilities": [],
                    "source_type": "pypi_package",
                    "source_url": repo.get("html_url", ""),
                    "discovered_at": datetime.now().isoformat()
                }
            
            elif config_file == "mcp.json":
                config = json.loads(content)
                return {
                    "tool_id": f"mcp_{config.get('name', 'unknown')}",
                    "name": config.get("name", "Unknown Tool"),
                    "description": config.get("description", ""),
                    "version": config.get("version", "1.0.0"),
                    "author": config.get("author", "Unknown"),
                    "license": config.get("license", "Unknown"),
                    "repository": repo.get("html_url", ""),
                    "homepage": config.get("homepage", repo.get("html_url", "")),
                    "tags": config.get("tags", []),
                    "capabilities": config.get("capabilities", []),
                    "tools": config.get("tools", []),
                    "source_type": "mcp_server",
                    "source_url": repo.get("html_url", ""),
                    "discovered_at": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.debug(f"解析配置文件 {config_file} 失败: {e}")
            return None
        
        return None
    
    async def _discover_from_npm(self, task: DiscoveryTask) -> List[Dict[str, Any]]:
        """从NPM发现工具"""
        search_query = task.target
        discovered_tools = []
        
        npm_registry = self.config.get("npm_registry", "https://registry.npmjs.org")
        search_url = f"{npm_registry}/-/v1/search?text={search_query}&size=100"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        search_results = await response.json()
                        
                        for package in search_results.get("objects", []):
                            package_info = package.get("package", {})
                            
                            tool_info = {
                                "tool_id": f"npm_{package_info.get('name', 'unknown').replace('/', '_')}",
                                "name": package_info.get("name", "Unknown Tool"),
                                "description": package_info.get("description", ""),
                                "version": package_info.get("version", "1.0.0"),
                                "author": package_info.get("author", {}).get("name", "Unknown") if isinstance(package_info.get("author"), dict) else str(package_info.get("author", "Unknown")),
                                "license": package_info.get("license", "Unknown"),
                                "repository": package_info.get("links", {}).get("repository", ""),
                                "homepage": package_info.get("links", {}).get("homepage", ""),
                                "tags": package_info.get("keywords", []),
                                "capabilities": [],
                                "npm_downloads": package.get("searchScore", 0),
                                "source_type": "npm_package",
                                "source_url": f"https://www.npmjs.com/package/{package_info.get('name', '')}",
                                "discovered_at": datetime.now().isoformat()
                            }
                            discovered_tools.append(tool_info)
                    
                    else:
                        raise Exception(f"NPM搜索失败: {response.status}")
            
            except Exception as e:
                logger.error(f"从NPM发现工具失败: {e}")
                raise
        
        logger.info(f"从NPM发现 {len(discovered_tools)} 个工具")
        return discovered_tools
    
    async def _discover_from_pypi(self, task: DiscoveryTask) -> List[Dict[str, Any]]:
        """从PyPI发现工具"""
        search_query = task.target
        discovered_tools = []
        
        # PyPI搜索API
        search_url = f"https://pypi.org/search/?q={search_query}&o=-created"
        
        # 注意：PyPI没有官方的搜索API，这里使用简化的实现
        # 在实际应用中，可能需要使用第三方服务或爬虫
        
        logger.info(f"从PyPI发现 {len(discovered_tools)} 个工具")
        return discovered_tools
    
    async def _discover_from_local_directory(self, task: DiscoveryTask) -> List[Dict[str, Any]]:
        """从本地目录发现工具"""
        directory_path = Path(task.target)
        discovered_tools = []
        
        if not directory_path.exists():
            raise Exception(f"本地目录不存在: {directory_path}")
        
        # 扫描目录中的MCP工具
        for item in directory_path.rglob("*"):
            if item.is_file() and item.name in ["package.json", "setup.py", "mcp.json"]:
                try:
                    with open(item, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tool_info = await self._extract_tool_info_from_local_file(
                        content, item.name, item.parent
                    )
                    
                    if tool_info:
                        discovered_tools.append(tool_info)
                
                except Exception as e:
                    logger.warning(f"分析本地文件 {item} 失败: {e}")
                    continue
        
        logger.info(f"从本地目录发现 {len(discovered_tools)} 个工具")
        return discovered_tools
    
    async def _extract_tool_info_from_local_file(self, content: str, filename: str, 
                                               directory: Path) -> Optional[Dict[str, Any]]:
        """从本地文件中提取工具信息"""
        try:
            if filename == "package.json":
                config = json.loads(content)
                return {
                    "tool_id": f"local_{config.get('name', directory.name).replace('/', '_')}",
                    "name": config.get("name", directory.name),
                    "description": config.get("description", ""),
                    "version": config.get("version", "1.0.0"),
                    "author": config.get("author", "Unknown"),
                    "license": config.get("license", "Unknown"),
                    "repository": "",
                    "homepage": "",
                    "tags": config.get("keywords", []),
                    "capabilities": [],
                    "local_path": str(directory),
                    "source_type": "local_directory",
                    "source_url": f"file://{directory}",
                    "discovered_at": datetime.now().isoformat()
                }
            
            elif filename == "mcp.json":
                config = json.loads(content)
                return {
                    "tool_id": f"local_mcp_{config.get('name', directory.name)}",
                    "name": config.get("name", directory.name),
                    "description": config.get("description", ""),
                    "version": config.get("version", "1.0.0"),
                    "author": config.get("author", "Unknown"),
                    "license": config.get("license", "Unknown"),
                    "repository": "",
                    "homepage": "",
                    "tags": config.get("tags", []),
                    "capabilities": config.get("capabilities", []),
                    "tools": config.get("tools", []),
                    "local_path": str(directory),
                    "source_type": "local_mcp_server",
                    "source_url": f"file://{directory}",
                    "discovered_at": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.debug(f"解析本地文件 {filename} 失败: {e}")
            return None
        
        return None
    
    async def _analyze_discovered_tools(self, raw_tools: List[Dict[str, Any]], 
                                      task: DiscoveryTask) -> List[MCPTool]:
        """分析发现的工具"""
        analyzed_tools = []
        
        for raw_tool in raw_tools:
            try:
                # 能力分析
                capabilities = await self._analyze_tool_capabilities(raw_tool)
                
                # 分类分析
                category = await self._classify_tool(raw_tool, capabilities)
                
                # 创建MCPTool对象
                mcp_tool = MCPTool(
                    tool_id=raw_tool.get("tool_id", f"unknown_{uuid.uuid4().hex[:8]}"),
                    name=raw_tool.get("name", "Unknown Tool"),
                    description=raw_tool.get("description", ""),
                    version=raw_tool.get("version", "1.0.0"),
                    author=raw_tool.get("author", "Unknown"),
                    license=raw_tool.get("license", "Unknown"),
                    category=category,
                    capabilities=capabilities,
                    tags=raw_tool.get("tags", []),
                    repository_url=raw_tool.get("repository", ""),
                    homepage_url=raw_tool.get("homepage", ""),
                    documentation_url=raw_tool.get("documentation", ""),
                    installation_guide=raw_tool.get("installation", {}),
                    configuration_schema=raw_tool.get("configuration", {}),
                    input_schema=raw_tool.get("input_schema", {}),
                    output_schema=raw_tool.get("output_schema", {}),
                    examples=raw_tool.get("examples", []),
                    dependencies=raw_tool.get("dependencies", {}),
                    requirements=raw_tool.get("requirements", {}),
                    status=ToolStatus.DISCOVERED,
                    source_type=raw_tool.get("source_type", "unknown"),
                    source_url=raw_tool.get("source_url", ""),
                    metadata={
                        "discovered_at": raw_tool.get("discovered_at", datetime.now().isoformat()),
                        "discovery_task_id": task.task_id,
                        "raw_data": raw_tool
                    }
                )
                
                analyzed_tools.append(mcp_tool)
                
            except Exception as e:
                logger.warning(f"分析工具失败 {raw_tool.get('name', 'unknown')}: {e}")
                continue
        
        logger.info(f"成功分析 {len(analyzed_tools)} 个工具")
        return analyzed_tools
    
    async def _analyze_tool_capabilities(self, tool_data: Dict[str, Any]) -> List[ToolCapability]:
        """分析工具能力"""
        capabilities = []
        
        # 从描述和名称中提取能力
        text_content = f"{tool_data.get('name', '')} {tool_data.get('description', '')} {' '.join(tool_data.get('tags', []))}"
        text_content = text_content.lower()
        
        for capability_name, patterns in self.capability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_content):
                    capability = ToolCapability(
                        name=capability_name,
                        description=f"Detected {capability_name} capability",
                        confidence=0.8,
                        evidence=[pattern]
                    )
                    capabilities.append(capability)
                    break  # 避免重复添加同一能力
        
        # 从显式的能力列表中添加
        explicit_capabilities = tool_data.get("capabilities", [])
        for cap in explicit_capabilities:
            if isinstance(cap, str):
                capability = ToolCapability(
                    name=cap,
                    description=f"Explicit capability: {cap}",
                    confidence=1.0,
                    evidence=["explicit_declaration"]
                )
                capabilities.append(capability)
            elif isinstance(cap, dict):
                capability = ToolCapability(
                    name=cap.get("name", "unknown"),
                    description=cap.get("description", ""),
                    confidence=cap.get("confidence", 1.0),
                    evidence=cap.get("evidence", ["explicit_declaration"])
                )
                capabilities.append(capability)
        
        return capabilities
    
    async def _classify_tool(self, tool_data: Dict[str, Any], 
                           capabilities: List[ToolCapability]) -> str:
        """分类工具"""
        # 计算每个分类的得分
        category_scores = {}
        
        for category, weights in self.category_classifiers.items():
            score = 0.0
            
            for capability in capabilities:
                if capability.name in weights:
                    score += weights[capability.name] * capability.confidence
            
            category_scores[category] = score
        
        # 选择得分最高的分类
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            
            # 映射到工具分类字符串
            category_mapping = {
                "development": "development",
                "data_science": "data_science", 
                "web_automation": "web_automation",
                "communication": "communication",
                "system_admin": "system_admin"
            }
            
            return category_mapping.get(best_category, "utility")
        
        return "utility"
    
    async def _register_tool(self, tool: MCPTool):
        """注册工具"""
        self.discovered_tools[tool.tool_id] = tool
        
        # 更新统计
        self.discovery_stats["unique_tools"] = len(self.discovered_tools)
        
        logger.debug(f"注册工具: {tool.name} ({tool.tool_id})")
    
    async def get_discovered_tools(self, category: str = None, 
                                 status: ToolStatus = None,
                                 limit: int = None) -> List[MCPTool]:
        """获取发现的工具"""
        tools = list(self.discovered_tools.values())
        
        # 过滤
        if category:
            tools = [tool for tool in tools if tool.category == category]
        
        if status:
            tools = [tool for tool in tools if tool.status == status]
        
        # 排序（按发现时间倒序）
        tools.sort(key=lambda t: t.metadata.get("discovered_at", ""), reverse=True)
        
        # 限制数量
        if limit:
            tools = tools[:limit]
        
        return tools
    
    async def search_tools(self, query: str, limit: int = 20) -> List[MCPTool]:
        """搜索工具"""
        query = query.lower()
        matching_tools = []
        
        for tool in self.discovered_tools.values():
            # 计算相关性得分
            score = 0.0
            
            # 名称匹配
            if query in tool.name.lower():
                score += 2.0
            
            # 描述匹配
            if query in tool.description.lower():
                score += 1.0
            
            # 标签匹配
            for tag in tool.tags:
                if query in tag.lower():
                    score += 0.5
            
            # 能力匹配
            for capability in tool.capabilities:
                if query in capability.name.lower():
                    score += 1.5
            
            if score > 0:
                matching_tools.append((tool, score))
        
        # 按得分排序
        matching_tools.sort(key=lambda x: x[1], reverse=True)
        
        return [tool for tool, score in matching_tools[:limit]]
    
    async def get_discovery_statistics(self) -> Dict[str, Any]:
        """获取发现统计信息"""
        # 计算平均发现时间
        completed_tasks = [
            task for task in self.discovery_tasks.values() 
            if task.status == DiscoveryStatus.COMPLETED and task.started_at and task.completed_at
        ]
        
        if completed_tasks:
            total_time = sum(
                (task.completed_at - task.started_at).total_seconds() 
                for task in completed_tasks
            )
            self.discovery_stats["discovery_time_avg"] = total_time / len(completed_tasks)
        
        # 分类统计
        category_stats = {}
        for tool in self.discovered_tools.values():
            category = tool.category.value
            category_stats[category] = category_stats.get(category, 0) + 1
        
        # 状态统计
        status_stats = {}
        for tool in self.discovered_tools.values():
            status = tool.status.value
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # 源类型统计
        source_stats = {}
        for tool in self.discovered_tools.values():
            source = tool.source_type
            source_stats[source] = source_stats.get(source, 0) + 1
        
        return {
            "discovery_overview": self.discovery_stats,
            "category_distribution": category_stats,
            "status_distribution": status_stats,
            "source_distribution": source_stats,
            "total_tasks": len(self.discovery_tasks),
            "active_tasks": len([
                task for task in self.discovery_tasks.values() 
                if task.status in [DiscoveryStatus.PENDING, DiscoveryStatus.SCANNING, DiscoveryStatus.ANALYZING]
            ]),
            "registries": len(self.registries)
        }
    
    async def export_discovered_tools(self, format: str = "json", 
                                    output_path: str = None) -> str:
        """导出发现的工具"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"./discovered_tools_{timestamp}.{format}"
        
        tools_data = []
        for tool in self.discovered_tools.values():
            tool_dict = asdict(tool)
            # 处理枚举类型
            tool_dict["category"] = tool.category.value
            tool_dict["status"] = tool.status.value
            tools_data.append(tool_dict)
        
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(tools_data, f, indent=2, ensure_ascii=False, default=str)
        
        elif format == "yaml":
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(tools_data, f, default_flow_style=False, allow_unicode=True)
        
        elif format == "csv":
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if tools_data:
                    writer = csv.DictWriter(f, fieldnames=tools_data[0].keys())
                    writer.writeheader()
                    writer.writerows(tools_data)
        
        else:
            raise ValueError(f"不支持的导出格式: {format}")
        
        logger.info(f"导出 {len(tools_data)} 个工具到 {output_path}")
        return output_path

# 工厂函数
def get_mcp_zero_discovery_engine(config_path: str = "./mcp_zero_config.json") -> MCPZeroDiscoveryEngine:
    """获取MCP-Zero发现引擎实例"""
    return MCPZeroDiscoveryEngine(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_discovery_engine():
        """测试发现引擎"""
        engine = get_mcp_zero_discovery_engine()
        
        # 开始发现
        print("🔍 开始工具发现...")
        task_ids = await engine.start_discovery()
        
        # 等待发现完成
        await asyncio.sleep(5)
        
        # 获取发现的工具
        tools = await engine.get_discovered_tools(limit=10)
        print(f"📋 发现 {len(tools)} 个工具:")
        
        for tool in tools:
            print(f"  - {tool.name} ({tool.category.value})")
            print(f"    {tool.description[:100]}...")
            print(f"    能力: {[cap.name for cap in tool.capabilities[:3]]}")
            print()
        
        # 搜索测试
        search_results = await engine.search_tools("file", limit=5)
        print(f"🔍 搜索 'file' 相关工具 ({len(search_results)} 个):")
        for tool in search_results:
            print(f"  - {tool.name}")
        
        # 统计信息
        stats = await engine.get_discovery_statistics()
        print(f"📊 发现统计:")
        print(f"  总发现数: {stats['discovery_overview']['total_discoveries']}")
        print(f"  成功发现: {stats['discovery_overview']['successful_discoveries']}")
        print(f"  发现工具数: {stats['discovery_overview']['total_tools_found']}")
        print(f"  唯一工具数: {stats['discovery_overview']['unique_tools']}")
        
        # 导出工具
        export_path = await engine.export_discovered_tools("json")
        print(f"💾 工具数据已导出到: {export_path}")
    
    # 运行测试
    asyncio.run(test_discovery_engine())

