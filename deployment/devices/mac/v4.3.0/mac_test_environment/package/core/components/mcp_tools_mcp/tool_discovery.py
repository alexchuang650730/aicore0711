"""
PowerAutomation 4.0 MCP工具自动发现机制

负责自动发现、识别和注册新的MCP工具，支持多种发现策略和智能推荐。
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import importlib.util
import subprocess
import yaml

from .tool_registry import ToolInfo, ToolCapability, ToolCategory, ToolStatus, MCPToolRegistry


class DiscoveryMethod(Enum):
    """发现方法枚举"""
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    REGISTRY = "registry"
    API = "api"
    PLUGIN = "plugin"
    MANUAL = "manual"


class DiscoveryStatus(Enum):
    """发现状态枚举"""
    PENDING = "pending"
    DISCOVERING = "discovering"
    FOUND = "found"
    REGISTERED = "registered"
    FAILED = "failed"


@dataclass
class DiscoverySource:
    """发现源"""
    source_id: str
    name: str
    method: DiscoveryMethod
    location: str
    enabled: bool = True
    scan_interval: int = 300  # 扫描间隔（秒）
    last_scan: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveredTool:
    """发现的工具"""
    discovery_id: str
    source_id: str
    tool_info: ToolInfo
    discovery_method: DiscoveryMethod
    discovery_time: datetime = field(default_factory=datetime.now)
    status: DiscoveryStatus = DiscoveryStatus.FOUND
    confidence: float = 0.0  # 置信度 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveryRule:
    """发现规则"""
    rule_id: str
    name: str
    pattern: str
    method: DiscoveryMethod
    enabled: bool = True
    priority: int = 100
    config: Dict[str, Any] = field(default_factory=dict)


class MCPToolDiscovery:
    """
    PowerAutomation 4.0 MCP工具自动发现机制
    
    功能：
    1. 多源工具发现
    2. 智能工具识别
    3. 自动工具注册
    4. 工具推荐系统
    5. 发现规则管理
    """
    
    def __init__(self, tool_registry: MCPToolRegistry):
        """
        初始化工具发现机制
        
        Args:
            tool_registry: 工具注册表
        """
        self.logger = logging.getLogger(__name__)
        self.tool_registry = tool_registry
        self.is_running = False
        
        # 发现源
        self.discovery_sources: Dict[str, DiscoverySource] = {}
        
        # 发现规则
        self.discovery_rules: Dict[str, DiscoveryRule] = {}
        
        # 发现的工具
        self.discovered_tools: Dict[str, DiscoveredTool] = {}
        
        # 发现任务
        self.discovery_tasks: Dict[str, asyncio.Task] = {}
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            "tool_discovered": [],
            "tool_registered": [],
            "discovery_failed": []
        }
        
        # 内置发现器
        self.built_in_discoverers: Dict[DiscoveryMethod, Callable] = {
            DiscoveryMethod.FILESYSTEM: self._discover_filesystem,
            DiscoveryMethod.NETWORK: self._discover_network,
            DiscoveryMethod.REGISTRY: self._discover_registry,
            DiscoveryMethod.API: self._discover_api,
            DiscoveryMethod.PLUGIN: self._discover_plugin
        }
        
        # 工具模式库
        self.tool_patterns = {
            "mcp_server": {
                "patterns": ["*_mcp.py", "*_mcp_server.py", "mcp_*.py"],
                "indicators": ["mcp", "server", "tool"],
                "category": ToolCategory.INTEGRATION
            },
            "automation_tool": {
                "patterns": ["*_automation.py", "auto_*.py", "*_bot.py"],
                "indicators": ["automation", "auto", "bot"],
                "category": ToolCategory.AUTOMATION
            },
            "ai_tool": {
                "patterns": ["*_ai.py", "ai_*.py", "*_ml.py", "ml_*.py"],
                "indicators": ["ai", "ml", "neural", "model"],
                "category": ToolCategory.AI_ML
            }
        }
        
        self.logger.info("MCP工具发现机制初始化完成")
    
    async def start(self) -> None:
        """启动工具发现机制"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动MCP工具发现机制...")
            
            # 加载默认发现源
            await self._load_default_sources()
            
            # 加载默认发现规则
            await self._load_default_rules()
            
            # 启动发现任务
            await self._start_discovery_tasks()
            
            # 启动后台任务
            asyncio.create_task(self._background_tasks())
            
            self.is_running = True
            self.logger.info("MCP工具发现机制启动成功")
            
        except Exception as e:
            self.logger.error(f"MCP工具发现机制启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止工具发现机制"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止MCP工具发现机制...")
            
            self.is_running = False
            
            # 停止发现任务
            for task in self.discovery_tasks.values():
                task.cancel()
            
            await asyncio.gather(*self.discovery_tasks.values(), return_exceptions=True)
            self.discovery_tasks.clear()
            
            self.logger.info("MCP工具发现机制已停止")
            
        except Exception as e:
            self.logger.error(f"MCP工具发现机制停止时出错: {e}")
    
    async def add_discovery_source(self, source: DiscoverySource) -> bool:
        """
        添加发现源
        
        Args:
            source: 发现源
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.discovery_sources[source.source_id] = source
            
            # 启动发现任务
            if source.enabled and self.is_running:
                await self._start_discovery_task(source)
            
            self.logger.info(f"添加发现源: {source.name} ({source.method.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"添加发现源失败: {e}")
            return False
    
    async def remove_discovery_source(self, source_id: str) -> bool:
        """
        移除发现源
        
        Args:
            source_id: 发现源ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if source_id not in self.discovery_sources:
                self.logger.warning(f"发现源不存在: {source_id}")
                return False
            
            # 停止发现任务
            if source_id in self.discovery_tasks:
                self.discovery_tasks[source_id].cancel()
                del self.discovery_tasks[source_id]
            
            # 移除发现源
            del self.discovery_sources[source_id]
            
            self.logger.info(f"移除发现源: {source_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除发现源失败: {e}")
            return False
    
    async def discover_tools(self, source_id: Optional[str] = None) -> List[DiscoveredTool]:
        """
        发现工具
        
        Args:
            source_id: 发现源ID，为None时扫描所有源
            
        Returns:
            List[DiscoveredTool]: 发现的工具列表
        """
        try:
            discovered = []
            
            if source_id:
                if source_id in self.discovery_sources:
                    source = self.discovery_sources[source_id]
                    tools = await self._discover_from_source(source)
                    discovered.extend(tools)
            else:
                # 扫描所有启用的发现源
                for source in self.discovery_sources.values():
                    if source.enabled:
                        tools = await self._discover_from_source(source)
                        discovered.extend(tools)
            
            return discovered
            
        except Exception as e:
            self.logger.error(f"发现工具失败: {e}")
            return []
    
    async def auto_register_discovered_tools(self, confidence_threshold: float = 0.7) -> int:
        """
        自动注册发现的工具
        
        Args:
            confidence_threshold: 置信度阈值
            
        Returns:
            int: 注册的工具数量
        """
        try:
            registered_count = 0
            
            for discovered_tool in self.discovered_tools.values():
                if (discovered_tool.status == DiscoveryStatus.FOUND and 
                    discovered_tool.confidence >= confidence_threshold):
                    
                    # 尝试注册工具
                    success = await self._register_discovered_tool(discovered_tool)
                    if success:
                        discovered_tool.status = DiscoveryStatus.REGISTERED
                        registered_count += 1
                    else:
                        discovered_tool.status = DiscoveryStatus.FAILED
            
            self.logger.info(f"自动注册了 {registered_count} 个工具")
            return registered_count
            
        except Exception as e:
            self.logger.error(f"自动注册发现的工具失败: {e}")
            return 0
    
    async def get_tool_recommendations(self, query: str, limit: int = 5) -> List[DiscoveredTool]:
        """
        获取工具推荐
        
        Args:
            query: 查询字符串
            limit: 结果限制
            
        Returns:
            List[DiscoveredTool]: 推荐的工具列表
        """
        try:
            query_lower = query.lower()
            recommendations = []
            
            for discovered_tool in self.discovered_tools.values():
                if discovered_tool.status != DiscoveryStatus.FOUND:
                    continue
                
                tool_info = discovered_tool.tool_info
                score = 0
                
                # 名称匹配
                if query_lower in tool_info.name.lower():
                    score += 10
                
                # 描述匹配
                if query_lower in tool_info.description.lower():
                    score += 5
                
                # 标签匹配
                for tag in tool_info.tags:
                    if query_lower in tag.lower():
                        score += 3
                
                # 能力匹配
                for capability in tool_info.capabilities:
                    if (query_lower in capability.name.lower() or 
                        query_lower in capability.description.lower()):
                        score += 2
                
                if score > 0:
                    # 结合置信度
                    final_score = score * discovered_tool.confidence
                    recommendations.append((discovered_tool, final_score))
            
            # 按分数排序
            recommendations.sort(key=lambda x: x[1], reverse=True)
            
            return [tool for tool, _ in recommendations[:limit]]
            
        except Exception as e:
            self.logger.error(f"获取工具推荐失败: {e}")
            return []
    
    async def add_discovery_rule(self, rule: DiscoveryRule) -> bool:
        """
        添加发现规则
        
        Args:
            rule: 发现规则
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.discovery_rules[rule.rule_id] = rule
            self.logger.info(f"添加发现规则: {rule.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加发现规则失败: {e}")
            return False
    
    async def get_discovered_tools(self, status: Optional[DiscoveryStatus] = None) -> List[DiscoveredTool]:
        """
        获取发现的工具
        
        Args:
            status: 状态过滤
            
        Returns:
            List[DiscoveredTool]: 发现的工具列表
        """
        try:
            result = []
            
            for discovered_tool in self.discovered_tools.values():
                if status is None or discovered_tool.status == status:
                    result.append(discovered_tool)
            
            # 按发现时间排序
            result.sort(key=lambda x: x.discovery_time, reverse=True)
            return result
            
        except Exception as e:
            self.logger.error(f"获取发现的工具失败: {e}")
            return []
    
    def add_event_callback(self, event_type: str, callback: Callable) -> None:
        """
        添加事件回调
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            self.logger.info(f"添加事件回调: {event_type}")
    
    async def _load_default_sources(self) -> None:
        """加载默认发现源"""
        try:
            # 本地文件系统发现源
            filesystem_source = DiscoverySource(
                source_id="local_filesystem",
                name="本地文件系统",
                method=DiscoveryMethod.FILESYSTEM,
                location="./tools",
                scan_interval=600,  # 10分钟
                config={
                    "recursive": True,
                    "file_patterns": ["*.py", "*.yaml", "*.json"],
                    "exclude_patterns": ["__pycache__", "*.pyc", ".git"]
                }
            )
            await self.add_discovery_source(filesystem_source)
            
            # MCP注册表发现源
            registry_source = DiscoverySource(
                source_id="mcp_registry",
                name="MCP官方注册表",
                method=DiscoveryMethod.REGISTRY,
                location="https://registry.mcp.dev/api/tools",
                scan_interval=3600,  # 1小时
                config={
                    "api_key": None,
                    "categories": ["automation", "ai", "development"]
                }
            )
            await self.add_discovery_source(registry_source)
            
            # GitHub发现源
            github_source = DiscoverySource(
                source_id="github_search",
                name="GitHub搜索",
                method=DiscoveryMethod.API,
                location="https://api.github.com/search/repositories",
                scan_interval=7200,  # 2小时
                config={
                    "query": "mcp tool powerautomation",
                    "sort": "updated",
                    "per_page": 50
                }
            )
            await self.add_discovery_source(github_source)
            
            self.logger.info("加载默认发现源完成")
            
        except Exception as e:
            self.logger.error(f"加载默认发现源失败: {e}")
    
    async def _load_default_rules(self) -> None:
        """加载默认发现规则"""
        try:
            rules = [
                DiscoveryRule(
                    rule_id="mcp_server_pattern",
                    name="MCP服务器模式",
                    pattern="*_mcp*.py",
                    method=DiscoveryMethod.FILESYSTEM,
                    priority=100,
                    config={"confidence_boost": 0.3}
                ),
                DiscoveryRule(
                    rule_id="tool_directory",
                    name="工具目录模式",
                    pattern="*/tools/*",
                    method=DiscoveryMethod.FILESYSTEM,
                    priority=80,
                    config={"confidence_boost": 0.2}
                ),
                DiscoveryRule(
                    rule_id="automation_script",
                    name="自动化脚本模式",
                    pattern="*automation*.py",
                    method=DiscoveryMethod.FILESYSTEM,
                    priority=70,
                    config={"confidence_boost": 0.1}
                )
            ]
            
            for rule in rules:
                await self.add_discovery_rule(rule)
            
            self.logger.info(f"加载了 {len(rules)} 个默认发现规则")
            
        except Exception as e:
            self.logger.error(f"加载默认发现规则失败: {e}")
    
    async def _start_discovery_tasks(self) -> None:
        """启动发现任务"""
        try:
            for source in self.discovery_sources.values():
                if source.enabled:
                    await self._start_discovery_task(source)
            
        except Exception as e:
            self.logger.error(f"启动发现任务失败: {e}")
    
    async def _start_discovery_task(self, source: DiscoverySource) -> None:
        """启动单个发现任务"""
        try:
            task = asyncio.create_task(self._discovery_loop(source))
            self.discovery_tasks[source.source_id] = task
            self.logger.info(f"启动发现任务: {source.name}")
            
        except Exception as e:
            self.logger.error(f"启动发现任务失败: {e}")
    
    async def _discovery_loop(self, source: DiscoverySource) -> None:
        """发现循环"""
        while self.is_running:
            try:
                # 执行发现
                discovered_tools = await self._discover_from_source(source)
                
                # 处理发现的工具
                for tool in discovered_tools:
                    await self._process_discovered_tool(tool)
                
                # 更新最后扫描时间
                source.last_scan = datetime.now()
                
                # 等待下次扫描
                await asyncio.sleep(source.scan_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"发现循环出错 {source.name}: {e}")
                await asyncio.sleep(60)
    
    async def _discover_from_source(self, source: DiscoverySource) -> List[DiscoveredTool]:
        """从发现源发现工具"""
        try:
            discoverer = self.built_in_discoverers.get(source.method)
            if not discoverer:
                self.logger.error(f"不支持的发现方法: {source.method}")
                return []
            
            return await discoverer(source)
            
        except Exception as e:
            self.logger.error(f"从发现源发现工具失败: {e}")
            return []
    
    async def _discover_filesystem(self, source: DiscoverySource) -> List[DiscoveredTool]:
        """文件系统发现"""
        try:
            discovered = []
            location = source.location
            config = source.config
            
            if not os.path.exists(location):
                return discovered
            
            # 遍历文件系统
            for root, dirs, files in os.walk(location):
                # 排除目录
                exclude_patterns = config.get("exclude_patterns", [])
                dirs[:] = [d for d in dirs if not any(d.startswith(pattern.rstrip('*')) for pattern in exclude_patterns)]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查文件模式
                    if self._matches_file_patterns(file, config.get("file_patterns", [])):
                        tool_info = await self._analyze_file_for_tool(file_path, source)
                        if tool_info:
                            discovery_id = f"{source.source_id}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
                            
                            discovered_tool = DiscoveredTool(
                                discovery_id=discovery_id,
                                source_id=source.source_id,
                                tool_info=tool_info,
                                discovery_method=source.method,
                                confidence=self._calculate_confidence(file_path, tool_info, source),
                                metadata={"file_path": file_path}
                            )
                            
                            discovered.append(discovered_tool)
            
            return discovered
            
        except Exception as e:
            self.logger.error(f"文件系统发现失败: {e}")
            return []
    
    async def _discover_network(self, source: DiscoverySource) -> List[DiscoveredTool]:
        """网络发现"""
        try:
            discovered = []
            # 这里可以实现网络扫描逻辑
            # 例如扫描特定端口的MCP服务
            
            self.logger.info(f"网络发现（待实现）: {source.location}")
            return discovered
            
        except Exception as e:
            self.logger.error(f"网络发现失败: {e}")
            return []
    
    async def _discover_registry(self, source: DiscoverySource) -> List[DiscoveredTool]:
        """注册表发现"""
        try:
            discovered = []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(source.location) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析注册表数据
                        for tool_data in data.get("tools", []):
                            tool_info = await self._parse_registry_tool(tool_data)
                            if tool_info:
                                discovery_id = f"{source.source_id}_{tool_info.tool_id}"
                                
                                discovered_tool = DiscoveredTool(
                                    discovery_id=discovery_id,
                                    source_id=source.source_id,
                                    tool_info=tool_info,
                                    discovery_method=source.method,
                                    confidence=0.9,  # 注册表工具置信度较高
                                    metadata={"registry_data": tool_data}
                                )
                                
                                discovered.append(discovered_tool)
            
            return discovered
            
        except Exception as e:
            self.logger.error(f"注册表发现失败: {e}")
            return []
    
    async def _discover_api(self, source: DiscoverySource) -> List[DiscoveredTool]:
        """API发现"""
        try:
            discovered = []
            
            if "github.com" in source.location:
                discovered = await self._discover_github_api(source)
            
            return discovered
            
        except Exception as e:
            self.logger.error(f"API发现失败: {e}")
            return []
    
    async def _discover_github_api(self, source: DiscoverySource) -> List[DiscoveredTool]:
        """GitHub API发现"""
        try:
            discovered = []
            config = source.config
            
            params = {
                "q": config.get("query", "mcp tool"),
                "sort": config.get("sort", "updated"),
                "per_page": config.get("per_page", 50)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(source.location, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for repo in data.get("items", []):
                            tool_info = await self._parse_github_repo(repo)
                            if tool_info:
                                discovery_id = f"{source.source_id}_{repo['id']}"
                                
                                discovered_tool = DiscoveredTool(
                                    discovery_id=discovery_id,
                                    source_id=source.source_id,
                                    tool_info=tool_info,
                                    discovery_method=source.method,
                                    confidence=0.6,  # GitHub仓库置信度中等
                                    metadata={"github_repo": repo}
                                )
                                
                                discovered.append(discovered_tool)
            
            return discovered
            
        except Exception as e:
            self.logger.error(f"GitHub API发现失败: {e}")
            return []
    
    async def _discover_plugin(self, source: DiscoverySource) -> List[DiscoveredTool]:
        """插件发现"""
        try:
            discovered = []
            # 这里可以实现插件系统的发现逻辑
            
            self.logger.info(f"插件发现（待实现）: {source.location}")
            return discovered
            
        except Exception as e:
            self.logger.error(f"插件发现失败: {e}")
            return []
    
    async def _analyze_file_for_tool(self, file_path: str, source: DiscoverySource) -> Optional[ToolInfo]:
        """分析文件是否为工具"""
        try:
            if file_path.endswith('.py'):
                return await self._analyze_python_file(file_path)
            elif file_path.endswith(('.yaml', '.yml')):
                return await self._analyze_yaml_file(file_path)
            elif file_path.endswith('.json'):
                return await self._analyze_json_file(file_path)
            
            return None
            
        except Exception as e:
            self.logger.error(f"分析文件失败: {e}")
            return None
    
    async def _analyze_python_file(self, file_path: str) -> Optional[ToolInfo]:
        """分析Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含MCP相关内容
            mcp_indicators = ['mcp', 'server', 'tool', 'capability']
            if not any(indicator in content.lower() for indicator in mcp_indicators):
                return None
            
            # 尝试提取工具信息
            tool_name = os.path.splitext(os.path.basename(file_path))[0]
            tool_id = f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
            
            # 简单的工具信息提取
            description = self._extract_description_from_python(content)
            category = self._infer_category_from_content(content)
            capabilities = self._extract_capabilities_from_python(content)
            
            tool_info = ToolInfo(
                tool_id=tool_id,
                name=tool_name,
                version="1.0.0",
                description=description,
                category=category,
                capabilities=capabilities,
                tags=self._extract_tags_from_content(content),
                status=ToolStatus.REGISTERED
            )
            
            return tool_info
            
        except Exception as e:
            self.logger.error(f"分析Python文件失败: {e}")
            return None
    
    async def _analyze_yaml_file(self, file_path: str) -> Optional[ToolInfo]:
        """分析YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                return None
            
            # 检查是否为工具配置文件
            if 'tool' in data or 'mcp' in data:
                tool_data = data.get('tool', data.get('mcp', {}))
                
                tool_info = ToolInfo(
                    tool_id=tool_data.get('id', f"yaml_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"),
                    name=tool_data.get('name', os.path.splitext(os.path.basename(file_path))[0]),
                    version=tool_data.get('version', '1.0.0'),
                    description=tool_data.get('description', ''),
                    category=ToolCategory(tool_data.get('category', 'utility')),
                    status=ToolStatus.REGISTERED
                )
                
                return tool_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"分析YAML文件失败: {e}")
            return None
    
    async def _analyze_json_file(self, file_path: str) -> Optional[ToolInfo]:
        """分析JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                return None
            
            # 检查是否为工具配置文件
            if 'tool' in data or 'mcp' in data:
                tool_data = data.get('tool', data.get('mcp', {}))
                
                tool_info = ToolInfo(
                    tool_id=tool_data.get('id', f"json_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"),
                    name=tool_data.get('name', os.path.splitext(os.path.basename(file_path))[0]),
                    version=tool_data.get('version', '1.0.0'),
                    description=tool_data.get('description', ''),
                    category=ToolCategory(tool_data.get('category', 'utility')),
                    status=ToolStatus.REGISTERED
                )
                
                return tool_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"分析JSON文件失败: {e}")
            return None
    
    def _matches_file_patterns(self, filename: str, patterns: List[str]) -> bool:
        """检查文件是否匹配模式"""
        import fnmatch
        return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)
    
    def _calculate_confidence(self, file_path: str, tool_info: ToolInfo, source: DiscoverySource) -> float:
        """计算置信度"""
        try:
            confidence = 0.5  # 基础置信度
            
            # 文件名模式匹配
            filename = os.path.basename(file_path)
            for pattern_name, pattern_info in self.tool_patterns.items():
                for pattern in pattern_info["patterns"]:
                    if self._matches_file_patterns(filename, [pattern]):
                        confidence += 0.2
                        break
            
            # 内容指标匹配
            if hasattr(tool_info, 'description'):
                content = tool_info.description.lower()
                for pattern_name, pattern_info in self.tool_patterns.items():
                    for indicator in pattern_info["indicators"]:
                        if indicator in content:
                            confidence += 0.1
            
            # 发现规则加成
            for rule in self.discovery_rules.values():
                if rule.enabled and rule.method == source.method:
                    if self._matches_file_patterns(file_path, [rule.pattern]):
                        confidence += rule.config.get("confidence_boost", 0.0)
            
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"计算置信度失败: {e}")
            return 0.5
    
    def _extract_description_from_python(self, content: str) -> str:
        """从Python代码提取描述"""
        try:
            # 查找文档字符串
            import ast
            tree = ast.parse(content)
            
            if (tree.body and isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Str)):
                return tree.body[0].value.s.strip()
            
            # 查找注释
            lines = content.split('\n')
            for line in lines[:10]:  # 只检查前10行
                line = line.strip()
                if line.startswith('#') and len(line) > 5:
                    return line[1:].strip()
            
            return "自动发现的工具"
            
        except:
            return "自动发现的工具"
    
    def _infer_category_from_content(self, content: str) -> ToolCategory:
        """从内容推断分类"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['ai', 'ml', 'neural', 'model']):
            return ToolCategory.AI_ML
        elif any(keyword in content_lower for keyword in ['automation', 'auto', 'bot']):
            return ToolCategory.AUTOMATION
        elif any(keyword in content_lower for keyword in ['api', 'http', 'request']):
            return ToolCategory.INTEGRATION
        elif any(keyword in content_lower for keyword in ['monitor', 'log', 'metric']):
            return ToolCategory.MONITORING
        elif any(keyword in content_lower for keyword in ['security', 'auth', 'encrypt']):
            return ToolCategory.SECURITY
        elif any(keyword in content_lower for keyword in ['data', 'process', 'transform']):
            return ToolCategory.DATA_PROCESSING
        else:
            return ToolCategory.UTILITY
    
    def _extract_capabilities_from_python(self, content: str) -> List[ToolCapability]:
        """从Python代码提取能力"""
        try:
            capabilities = []
            
            # 简单的函数提取
            import re
            function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            functions = re.findall(function_pattern, content)
            
            for func_name in functions:
                if not func_name.startswith('_'):  # 排除私有函数
                    capability = ToolCapability(
                        capability_id=func_name,
                        name=func_name.replace('_', ' ').title(),
                        description=f"Function: {func_name}"
                    )
                    capabilities.append(capability)
            
            return capabilities[:5]  # 最多返回5个能力
            
        except:
            return []
    
    def _extract_tags_from_content(self, content: str) -> List[str]:
        """从内容提取标签"""
        tags = []
        content_lower = content.lower()
        
        # 技术标签
        tech_keywords = ['python', 'api', 'http', 'json', 'yaml', 'sql', 'redis', 'docker']
        for keyword in tech_keywords:
            if keyword in content_lower:
                tags.append(keyword)
        
        # 功能标签
        func_keywords = ['automation', 'monitoring', 'security', 'data', 'ai', 'ml']
        for keyword in func_keywords:
            if keyword in content_lower:
                tags.append(keyword)
        
        return tags[:5]  # 最多返回5个标签
    
    async def _parse_registry_tool(self, tool_data: Dict[str, Any]) -> Optional[ToolInfo]:
        """解析注册表工具数据"""
        try:
            tool_info = ToolInfo(
                tool_id=tool_data.get('id', ''),
                name=tool_data.get('name', ''),
                version=tool_data.get('version', '1.0.0'),
                description=tool_data.get('description', ''),
                category=ToolCategory(tool_data.get('category', 'utility')),
                author=tool_data.get('author', ''),
                license=tool_data.get('license', ''),
                homepage=tool_data.get('homepage', ''),
                repository=tool_data.get('repository', ''),
                tags=tool_data.get('tags', []),
                status=ToolStatus.REGISTERED
            )
            
            return tool_info
            
        except Exception as e:
            self.logger.error(f"解析注册表工具数据失败: {e}")
            return None
    
    async def _parse_github_repo(self, repo_data: Dict[str, Any]) -> Optional[ToolInfo]:
        """解析GitHub仓库数据"""
        try:
            tool_info = ToolInfo(
                tool_id=f"github_{repo_data['id']}",
                name=repo_data.get('name', ''),
                version="1.0.0",
                description=repo_data.get('description', ''),
                category=self._infer_category_from_content(repo_data.get('description', '')),
                author=repo_data.get('owner', {}).get('login', ''),
                license=repo_data.get('license', {}).get('name', '') if repo_data.get('license') else '',
                homepage=repo_data.get('homepage', ''),
                repository=repo_data.get('html_url', ''),
                tags=repo_data.get('topics', []),
                status=ToolStatus.REGISTERED
            )
            
            return tool_info
            
        except Exception as e:
            self.logger.error(f"解析GitHub仓库数据失败: {e}")
            return None
    
    async def _process_discovered_tool(self, discovered_tool: DiscoveredTool) -> None:
        """处理发现的工具"""
        try:
            # 检查是否已经发现过
            if discovered_tool.discovery_id in self.discovered_tools:
                return
            
            # 添加到发现列表
            self.discovered_tools[discovered_tool.discovery_id] = discovered_tool
            
            # 触发事件
            await self._trigger_event("tool_discovered", discovered_tool)
            
            self.logger.info(f"发现新工具: {discovered_tool.tool_info.name} (置信度: {discovered_tool.confidence:.2f})")
            
        except Exception as e:
            self.logger.error(f"处理发现的工具失败: {e}")
    
    async def _register_discovered_tool(self, discovered_tool: DiscoveredTool) -> bool:
        """注册发现的工具"""
        try:
            tool_info = discovered_tool.tool_info
            
            # 构造端点URL（这里需要根据实际情况调整）
            endpoint = discovered_tool.metadata.get("endpoint", f"http://localhost:8000/{tool_info.tool_id}")
            
            # 注册工具
            success = await self.tool_registry.register_tool(
                tool_info=tool_info,
                endpoint=endpoint,
                registered_by="auto_discovery"
            )
            
            if success:
                await self._trigger_event("tool_registered", discovered_tool)
                self.logger.info(f"自动注册工具成功: {tool_info.name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"注册发现的工具失败: {e}")
            return False
    
    async def _trigger_event(self, event_type: str, data: Any) -> None:
        """触发事件"""
        try:
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        self.logger.error(f"事件回调执行失败: {e}")
        except Exception as e:
            self.logger.error(f"触发事件失败: {e}")
    
    async def _background_tasks(self) -> None:
        """后台任务"""
        while self.is_running:
            try:
                # 清理旧的发现记录
                await self._cleanup_old_discoveries()
                
                # 等待下次执行
                await asyncio.sleep(3600)  # 1小时
                
            except Exception as e:
                self.logger.error(f"后台任务执行失败: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_old_discoveries(self) -> None:
        """清理旧的发现记录"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=7)  # 保留7天
            
            to_remove = []
            for discovery_id, discovered_tool in self.discovered_tools.items():
                if discovered_tool.discovery_time < cutoff_time:
                    to_remove.append(discovery_id)
            
            for discovery_id in to_remove:
                del self.discovered_tools[discovery_id]
            
            if to_remove:
                self.logger.info(f"清理了 {len(to_remove)} 个旧的发现记录")
            
        except Exception as e:
            self.logger.error(f"清理旧的发现记录失败: {e}")


# 导入hashlib用于生成哈希
import hashlib

