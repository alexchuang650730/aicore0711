"""
PowerAutomation 4.0 MCP工具注册表

负责管理所有MCP工具的注册、查询、版本控制和生命周期管理。
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import asyncio
import hashlib


class ToolStatus(Enum):
    """工具状态枚举"""
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ERROR = "error"


class ToolCategory(Enum):
    """工具分类枚举"""
    DEVELOPMENT = "development"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    AI_ML = "ai_ml"
    MONITORING = "monitoring"
    SECURITY = "security"
    INTEGRATION = "integration"
    UTILITY = "utility"
    CUSTOM = "custom"


@dataclass
class ToolCapability:
    """工具能力"""
    capability_id: str
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolInfo:
    """工具信息"""
    tool_id: str
    name: str
    version: str
    description: str
    category: ToolCategory
    capabilities: List[ToolCapability] = field(default_factory=list)
    author: str = ""
    license: str = ""
    homepage: str = ""
    repository: str = ""
    documentation: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: ToolStatus = ToolStatus.REGISTERED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rating: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolRegistration:
    """工具注册信息"""
    tool_info: ToolInfo
    endpoint: str
    health_check_url: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    registered_by: str = ""
    registration_time: datetime = field(default_factory=datetime.now)


class MCPToolRegistry:
    """
    PowerAutomation 4.0 MCP工具注册表
    
    功能：
    1. 工具注册和注销
    2. 工具信息查询和搜索
    3. 工具版本管理
    4. 工具能力索引
    5. 工具使用统计
    """
    
    def __init__(self, storage_backend: str = "file"):
        """
        初始化工具注册表
        
        Args:
            storage_backend: 存储后端 (file, memory, database)
        """
        self.logger = logging.getLogger(__name__)
        self.storage_backend = storage_backend
        self.is_running = False
        
        # 工具注册信息
        self.registered_tools: Dict[str, ToolRegistration] = {}
        
        # 能力索引
        self.capability_index: Dict[str, Set[str]] = {}  # capability_id -> tool_ids
        self.category_index: Dict[ToolCategory, Set[str]] = {}  # category -> tool_ids
        self.tag_index: Dict[str, Set[str]] = {}  # tag -> tool_ids
        
        # 版本管理
        self.tool_versions: Dict[str, List[str]] = {}  # tool_name -> versions
        
        # 统计信息
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # 存储文件
        self.registry_file = "tool_registry.json"
        self.stats_file = "tool_stats.json"
        
        # 事件回调
        self.event_callbacks: Dict[str, List[callable]] = {
            "tool_registered": [],
            "tool_unregistered": [],
            "tool_updated": [],
            "tool_used": []
        }
        
        self.logger.info("MCP工具注册表初始化完成")
    
    async def start(self) -> None:
        """启动工具注册表"""
        if self.is_running:
            return
        
        try:
            self.logger.info("启动MCP工具注册表...")
            
            # 加载已注册的工具
            await self._load_registry()
            
            # 加载统计信息
            await self._load_stats()
            
            # 重建索引
            await self._rebuild_indexes()
            
            # 启动后台任务
            asyncio.create_task(self._background_tasks())
            
            self.is_running = True
            self.logger.info(f"MCP工具注册表启动成功，已注册 {len(self.registered_tools)} 个工具")
            
        except Exception as e:
            self.logger.error(f"MCP工具注册表启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止工具注册表"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("停止MCP工具注册表...")
            
            self.is_running = False
            
            # 保存注册信息
            await self._save_registry()
            
            # 保存统计信息
            await self._save_stats()
            
            self.logger.info("MCP工具注册表已停止")
            
        except Exception as e:
            self.logger.error(f"MCP工具注册表停止时出错: {e}")
    
    async def register_tool(self, tool_info: ToolInfo, endpoint: str,
                           health_check_url: Optional[str] = None,
                           config: Optional[Dict[str, Any]] = None,
                           registered_by: str = "") -> bool:
        """
        注册工具
        
        Args:
            tool_info: 工具信息
            endpoint: 工具端点
            health_check_url: 健康检查URL
            config: 工具配置
            registered_by: 注册者
            
        Returns:
            bool: 注册是否成功
        """
        try:
            tool_id = tool_info.tool_id
            
            # 检查工具是否已注册
            if tool_id in self.registered_tools:
                existing_tool = self.registered_tools[tool_id]
                if existing_tool.tool_info.version == tool_info.version:
                    self.logger.warning(f"工具已注册: {tool_id} v{tool_info.version}")
                    return False
                else:
                    # 版本更新
                    return await self._update_tool_version(tool_info, endpoint, health_check_url, config, registered_by)
            
            # 创建注册信息
            registration = ToolRegistration(
                tool_info=tool_info,
                endpoint=endpoint,
                health_check_url=health_check_url,
                config=config or {},
                registered_by=registered_by
            )
            
            # 注册工具
            self.registered_tools[tool_id] = registration
            
            # 更新索引
            await self._update_indexes_for_tool(tool_info, add=True)
            
            # 更新版本信息
            tool_name = tool_info.name
            if tool_name not in self.tool_versions:
                self.tool_versions[tool_name] = []
            if tool_info.version not in self.tool_versions[tool_name]:
                self.tool_versions[tool_name].append(tool_info.version)
                self.tool_versions[tool_name].sort(key=lambda v: [int(x) for x in v.split('.')])
            
            # 初始化统计信息
            self.usage_stats[tool_id] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "average_response_time": 0.0,
                "last_call_time": None,
                "daily_usage": {}
            }
            
            # 触发事件
            await self._trigger_event("tool_registered", tool_info)
            
            # 保存注册信息
            await self._save_registry()
            
            self.logger.info(f"工具注册成功: {tool_info.name} v{tool_info.version} ({tool_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"工具注册失败: {e}")
            return False
    
    async def unregister_tool(self, tool_id: str) -> bool:
        """
        注销工具
        
        Args:
            tool_id: 工具ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if tool_id not in self.registered_tools:
                self.logger.warning(f"工具未注册: {tool_id}")
                return False
            
            registration = self.registered_tools[tool_id]
            tool_info = registration.tool_info
            
            # 从注册表移除
            del self.registered_tools[tool_id]
            
            # 更新索引
            await self._update_indexes_for_tool(tool_info, add=False)
            
            # 清理统计信息
            if tool_id in self.usage_stats:
                del self.usage_stats[tool_id]
            
            # 触发事件
            await self._trigger_event("tool_unregistered", tool_info)
            
            # 保存注册信息
            await self._save_registry()
            
            self.logger.info(f"工具注销成功: {tool_info.name} ({tool_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"工具注销失败: {e}")
            return False
    
    async def get_tool(self, tool_id: str) -> Optional[ToolRegistration]:
        """
        获取工具注册信息
        
        Args:
            tool_id: 工具ID
            
        Returns:
            Optional[ToolRegistration]: 工具注册信息
        """
        return self.registered_tools.get(tool_id)
    
    async def get_tool_info(self, tool_id: str) -> Optional[ToolInfo]:
        """
        获取工具信息
        
        Args:
            tool_id: 工具ID
            
        Returns:
            Optional[ToolInfo]: 工具信息
        """
        registration = await self.get_tool(tool_id)
        return registration.tool_info if registration else None
    
    async def list_tools(self, category: Optional[ToolCategory] = None,
                        status: Optional[ToolStatus] = None,
                        tags: Optional[List[str]] = None) -> List[ToolInfo]:
        """
        列出工具
        
        Args:
            category: 工具分类过滤
            status: 工具状态过滤
            tags: 标签过滤
            
        Returns:
            List[ToolInfo]: 工具信息列表
        """
        try:
            result = []
            
            for registration in self.registered_tools.values():
                tool_info = registration.tool_info
                
                # 分类过滤
                if category and tool_info.category != category:
                    continue
                
                # 状态过滤
                if status and tool_info.status != status:
                    continue
                
                # 标签过滤
                if tags and not any(tag in tool_info.tags for tag in tags):
                    continue
                
                result.append(tool_info)
            
            # 按名称排序
            result.sort(key=lambda x: x.name)
            return result
            
        except Exception as e:
            self.logger.error(f"列出工具失败: {e}")
            return []
    
    async def search_tools(self, query: str, limit: int = 10) -> List[ToolInfo]:
        """
        搜索工具
        
        Args:
            query: 搜索查询
            limit: 结果限制
            
        Returns:
            List[ToolInfo]: 搜索结果
        """
        try:
            query_lower = query.lower()
            results = []
            
            for registration in self.registered_tools.values():
                tool_info = registration.tool_info
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
                    if query_lower in capability.name.lower() or query_lower in capability.description.lower():
                        score += 2
                
                if score > 0:
                    results.append((tool_info, score))
            
            # 按分数排序
            results.sort(key=lambda x: x[1], reverse=True)
            
            return [tool_info for tool_info, _ in results[:limit]]
            
        except Exception as e:
            self.logger.error(f"搜索工具失败: {e}")
            return []
    
    async def find_tools_by_capability(self, capability_id: str) -> List[ToolInfo]:
        """
        根据能力查找工具
        
        Args:
            capability_id: 能力ID
            
        Returns:
            List[ToolInfo]: 工具信息列表
        """
        try:
            if capability_id not in self.capability_index:
                return []
            
            tool_ids = self.capability_index[capability_id]
            result = []
            
            for tool_id in tool_ids:
                if tool_id in self.registered_tools:
                    result.append(self.registered_tools[tool_id].tool_info)
            
            return result
            
        except Exception as e:
            self.logger.error(f"根据能力查找工具失败: {e}")
            return []
    
    async def get_tool_versions(self, tool_name: str) -> List[str]:
        """
        获取工具版本列表
        
        Args:
            tool_name: 工具名称
            
        Returns:
            List[str]: 版本列表
        """
        return self.tool_versions.get(tool_name, [])
    
    async def get_latest_version(self, tool_name: str) -> Optional[str]:
        """
        获取工具最新版本
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[str]: 最新版本
        """
        versions = await self.get_tool_versions(tool_name)
        return versions[-1] if versions else None
    
    async def update_tool_status(self, tool_id: str, status: ToolStatus) -> bool:
        """
        更新工具状态
        
        Args:
            tool_id: 工具ID
            status: 新状态
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if tool_id not in self.registered_tools:
                self.logger.error(f"工具未注册: {tool_id}")
                return False
            
            old_status = self.registered_tools[tool_id].tool_info.status
            self.registered_tools[tool_id].tool_info.status = status
            self.registered_tools[tool_id].tool_info.updated_at = datetime.now()
            
            # 保存注册信息
            await self._save_registry()
            
            self.logger.info(f"工具状态更新: {tool_id} {old_status} -> {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新工具状态失败: {e}")
            return False
    
    async def record_tool_usage(self, tool_id: str, success: bool = True,
                               response_time: Optional[float] = None) -> None:
        """
        记录工具使用情况
        
        Args:
            tool_id: 工具ID
            success: 是否成功
            response_time: 响应时间
        """
        try:
            if tool_id not in self.registered_tools:
                return
            
            # 更新工具信息
            tool_info = self.registered_tools[tool_id].tool_info
            tool_info.usage_count += 1
            tool_info.last_used_at = datetime.now()
            
            # 更新统计信息
            if tool_id not in self.usage_stats:
                self.usage_stats[tool_id] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "average_response_time": 0.0,
                    "last_call_time": None,
                    "daily_usage": {}
                }
            
            stats = self.usage_stats[tool_id]
            stats["total_calls"] += 1
            
            if success:
                stats["successful_calls"] += 1
            else:
                stats["failed_calls"] += 1
            
            if response_time is not None:
                # 计算平均响应时间
                if stats["average_response_time"] == 0:
                    stats["average_response_time"] = response_time
                else:
                    stats["average_response_time"] = (
                        stats["average_response_time"] * 0.8 + response_time * 0.2
                    )
            
            stats["last_call_time"] = datetime.now().isoformat()
            
            # 记录每日使用情况
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in stats["daily_usage"]:
                stats["daily_usage"][today] = 0
            stats["daily_usage"][today] += 1
            
            # 触发事件
            await self._trigger_event("tool_used", tool_info)
            
        except Exception as e:
            self.logger.error(f"记录工具使用情况失败: {e}")
    
    async def get_tool_stats(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工具统计信息
        
        Args:
            tool_id: 工具ID
            
        Returns:
            Optional[Dict[str, Any]]: 统计信息
        """
        return self.usage_stats.get(tool_id)
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        try:
            total_tools = len(self.registered_tools)
            active_tools = sum(1 for reg in self.registered_tools.values() 
                             if reg.tool_info.status == ToolStatus.ACTIVE)
            
            category_counts = {}
            for category in ToolCategory:
                category_counts[category.value] = len(self.category_index.get(category, set()))
            
            total_usage = sum(stats.get("total_calls", 0) for stats in self.usage_stats.values())
            
            return {
                "total_tools": total_tools,
                "active_tools": active_tools,
                "inactive_tools": total_tools - active_tools,
                "category_distribution": category_counts,
                "total_capabilities": len(self.capability_index),
                "total_usage": total_usage,
                "registry_size": len(self.registered_tools)
            }
            
        except Exception as e:
            self.logger.error(f"获取注册表统计信息失败: {e}")
            return {}
    
    def add_event_callback(self, event_type: str, callback: callable) -> None:
        """
        添加事件回调
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            self.logger.info(f"添加事件回调: {event_type}")
    
    async def _update_tool_version(self, tool_info: ToolInfo, endpoint: str,
                                  health_check_url: Optional[str],
                                  config: Optional[Dict[str, Any]],
                                  registered_by: str) -> bool:
        """更新工具版本"""
        try:
            tool_id = tool_info.tool_id
            old_registration = self.registered_tools[tool_id]
            old_tool_info = old_registration.tool_info
            
            # 更新注册信息
            new_registration = ToolRegistration(
                tool_info=tool_info,
                endpoint=endpoint,
                health_check_url=health_check_url,
                config=config or {},
                registered_by=registered_by
            )
            
            self.registered_tools[tool_id] = new_registration
            
            # 更新索引
            await self._update_indexes_for_tool(old_tool_info, add=False)
            await self._update_indexes_for_tool(tool_info, add=True)
            
            # 更新版本信息
            tool_name = tool_info.name
            if tool_info.version not in self.tool_versions[tool_name]:
                self.tool_versions[tool_name].append(tool_info.version)
                self.tool_versions[tool_name].sort(key=lambda v: [int(x) for x in v.split('.')])
            
            # 触发事件
            await self._trigger_event("tool_updated", tool_info)
            
            # 保存注册信息
            await self._save_registry()
            
            self.logger.info(f"工具版本更新: {tool_info.name} {old_tool_info.version} -> {tool_info.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新工具版本失败: {e}")
            return False
    
    async def _update_indexes_for_tool(self, tool_info: ToolInfo, add: bool = True) -> None:
        """更新工具索引"""
        try:
            tool_id = tool_info.tool_id
            
            # 能力索引
            for capability in tool_info.capabilities:
                capability_id = capability.capability_id
                if capability_id not in self.capability_index:
                    self.capability_index[capability_id] = set()
                
                if add:
                    self.capability_index[capability_id].add(tool_id)
                else:
                    self.capability_index[capability_id].discard(tool_id)
                    if not self.capability_index[capability_id]:
                        del self.capability_index[capability_id]
            
            # 分类索引
            category = tool_info.category
            if category not in self.category_index:
                self.category_index[category] = set()
            
            if add:
                self.category_index[category].add(tool_id)
            else:
                self.category_index[category].discard(tool_id)
                if not self.category_index[category]:
                    del self.category_index[category]
            
            # 标签索引
            for tag in tool_info.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                
                if add:
                    self.tag_index[tag].add(tool_id)
                else:
                    self.tag_index[tag].discard(tool_id)
                    if not self.tag_index[tag]:
                        del self.tag_index[tag]
            
        except Exception as e:
            self.logger.error(f"更新工具索引失败: {e}")
    
    async def _rebuild_indexes(self) -> None:
        """重建索引"""
        try:
            # 清空索引
            self.capability_index.clear()
            self.category_index.clear()
            self.tag_index.clear()
            
            # 重建索引
            for registration in self.registered_tools.values():
                await self._update_indexes_for_tool(registration.tool_info, add=True)
            
            self.logger.info("重建工具索引完成")
            
        except Exception as e:
            self.logger.error(f"重建工具索引失败: {e}")
    
    async def _trigger_event(self, event_type: str, tool_info: ToolInfo) -> None:
        """触发事件"""
        try:
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(tool_info)
                        else:
                            callback(tool_info)
                    except Exception as e:
                        self.logger.error(f"事件回调执行失败: {e}")
        except Exception as e:
            self.logger.error(f"触发事件失败: {e}")
    
    async def _load_registry(self) -> None:
        """加载注册表"""
        try:
            if self.storage_backend == "file":
                await self._load_registry_from_file()
            elif self.storage_backend == "database":
                await self._load_registry_from_database()
            
        except Exception as e:
            self.logger.error(f"加载注册表失败: {e}")
    
    async def _save_registry(self) -> None:
        """保存注册表"""
        try:
            if self.storage_backend == "file":
                await self._save_registry_to_file()
            elif self.storage_backend == "database":
                await self._save_registry_to_database()
            
        except Exception as e:
            self.logger.error(f"保存注册表失败: {e}")
    
    async def _load_registry_from_file(self) -> None:
        """从文件加载注册表"""
        try:
            import os
            if not os.path.exists(self.registry_file):
                return
            
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for tool_id, reg_data in data.items():
                # 重建ToolInfo对象
                tool_data = reg_data["tool_info"]
                
                # 转换日期字符串
                tool_data["created_at"] = datetime.fromisoformat(tool_data["created_at"])
                tool_data["updated_at"] = datetime.fromisoformat(tool_data["updated_at"])
                if tool_data.get("last_used_at"):
                    tool_data["last_used_at"] = datetime.fromisoformat(tool_data["last_used_at"])
                
                # 转换枚举
                tool_data["category"] = ToolCategory(tool_data["category"])
                tool_data["status"] = ToolStatus(tool_data["status"])
                
                # 重建能力对象
                capabilities = []
                for cap_data in tool_data.get("capabilities", []):
                    capabilities.append(ToolCapability(**cap_data))
                tool_data["capabilities"] = capabilities
                
                tool_info = ToolInfo(**tool_data)
                
                # 重建注册对象
                registration = ToolRegistration(
                    tool_info=tool_info,
                    endpoint=reg_data["endpoint"],
                    health_check_url=reg_data.get("health_check_url"),
                    config=reg_data.get("config", {}),
                    registered_by=reg_data.get("registered_by", ""),
                    registration_time=datetime.fromisoformat(reg_data["registration_time"])
                )
                
                self.registered_tools[tool_id] = registration
            
            self.logger.info(f"从文件加载了 {len(self.registered_tools)} 个工具")
            
        except Exception as e:
            self.logger.error(f"从文件加载注册表失败: {e}")
    
    async def _save_registry_to_file(self) -> None:
        """保存注册表到文件"""
        try:
            data = {}
            
            for tool_id, registration in self.registered_tools.items():
                # 序列化工具信息
                tool_data = asdict(registration.tool_info)
                
                # 转换日期为字符串
                tool_data["created_at"] = tool_data["created_at"].isoformat()
                tool_data["updated_at"] = tool_data["updated_at"].isoformat()
                if tool_data["last_used_at"]:
                    tool_data["last_used_at"] = tool_data["last_used_at"].isoformat()
                
                # 转换枚举为字符串
                tool_data["category"] = tool_data["category"].value
                tool_data["status"] = tool_data["status"].value
                
                # 序列化注册信息
                reg_data = {
                    "tool_info": tool_data,
                    "endpoint": registration.endpoint,
                    "health_check_url": registration.health_check_url,
                    "config": registration.config,
                    "registered_by": registration.registered_by,
                    "registration_time": registration.registration_time.isoformat()
                }
                
                data[tool_id] = reg_data
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"保存注册表到文件失败: {e}")
    
    async def _load_registry_from_database(self) -> None:
        """从数据库加载注册表"""
        # 这里可以实现从数据库加载的逻辑
        self.logger.info("数据库注册表加载（待实现）")
    
    async def _save_registry_to_database(self) -> None:
        """保存注册表到数据库"""
        # 这里可以实现保存到数据库的逻辑
        self.logger.info("数据库注册表保存（待实现）")
    
    async def _load_stats(self) -> None:
        """加载统计信息"""
        try:
            import os
            if not os.path.exists(self.stats_file):
                return
            
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                self.usage_stats = json.load(f)
            
        except Exception as e:
            self.logger.error(f"加载统计信息失败: {e}")
    
    async def _save_stats(self) -> None:
        """保存统计信息"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_stats, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"保存统计信息失败: {e}")
    
    async def _background_tasks(self) -> None:
        """后台任务"""
        while self.is_running:
            try:
                # 定期保存统计信息
                await self._save_stats()
                
                # 清理旧的每日使用数据
                await self._cleanup_old_daily_usage()
                
                # 等待下次执行
                await asyncio.sleep(300)  # 5分钟
                
            except Exception as e:
                self.logger.error(f"后台任务执行失败: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_daily_usage(self) -> None:
        """清理旧的每日使用数据"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            for tool_id, stats in self.usage_stats.items():
                daily_usage = stats.get("daily_usage", {})
                keys_to_remove = [date for date in daily_usage.keys() if date < cutoff_date]
                
                for date in keys_to_remove:
                    del daily_usage[date]
            
        except Exception as e:
            self.logger.error(f"清理旧的每日使用数据失败: {e}")

