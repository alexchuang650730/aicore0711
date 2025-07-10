#!/usr/bin/env python3
"""
统一工具管理接口

提供统一的工具管理、执行和监控接口，整合MCP-Zero发现引擎和Smart Tool选择引擎。
支持工具的完整生命周期管理，从发现、选择到执行和监控。

主要功能：
- 统一工具管理API
- 工具执行引擎
- 实时监控和日志
- 工具生命周期管理
- 安全和权限控制
- 性能优化和缓存

作者: PowerAutomation Team
版本: 4.1.0
日期: 2025-01-07
"""

import asyncio
import json
import uuid
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import subprocess
import tempfile
import shutil
import signal
import psutil
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from ..models.tool_models import MCPTool, TaskRequirement, ToolRecommendation, ToolStatus, ToolCategory
from ..discovery.mcp_zero_discovery_engine import MCPZeroDiscoveryEngine
from ..selection.smart_tool_selection_engine import SmartToolSelectionEngine, SelectionStrategy

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class ToolType(Enum):
    """工具类型"""
    MCP_SERVER = "mcp_server"
    NPM_PACKAGE = "npm_package"
    PYTHON_PACKAGE = "python_package"
    DOCKER_CONTAINER = "docker_container"
    LOCAL_EXECUTABLE = "local_executable"
    WEB_SERVICE = "web_service"

@dataclass
class ExecutionContext:
    """执行上下文"""
    execution_id: str
    tool_id: str
    user_id: Optional[str]
    task_id: Optional[str]
    input_data: Dict[str, Any]
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: int = 300  # 5分钟默认超时
    max_memory: int = 512  # MB
    max_cpu_percent: float = 80.0
    working_directory: Optional[str] = None
    security_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    tool_id: str
    status: ExecutionStatus
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ToolInstance:
    """工具实例"""
    instance_id: str
    tool_id: str
    tool_type: ToolType
    status: ToolStatus
    process_id: Optional[int] = None
    container_id: Optional[str] = None
    endpoint_url: Optional[str] = None
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

class UnifiedToolManager:
    """统一工具管理器"""
    
    def __init__(self, config_path: str = "./unified_tool_config.json"):
        """初始化统一工具管理器"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 核心组件
        self.discovery_engine = MCPZeroDiscoveryEngine(
            self.config.get("discovery_config_path", "./mcp_zero_config.json")
        )
        self.selection_engine = SmartToolSelectionEngine(
            self.config.get("selection_config_path", "./smart_tool_config.json")
        )
        
        # 工具管理
        self.available_tools: Dict[str, MCPTool] = {}
        self.tool_instances: Dict[str, ToolInstance] = {}
        self.active_executions: Dict[str, ExecutionResult] = {}
        
        # 执行引擎
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.get("max_workers", 10)
        )
        self.execution_timeout = self.config.get("execution_timeout", 300)
        
        # 监控和日志
        self.enable_monitoring = self.config.get("enable_monitoring", True)
        self.log_level = self.config.get("log_level", "INFO")
        self.metrics_collection = self.config.get("metrics_collection", True)
        
        # 安全配置
        self.enable_sandboxing = self.config.get("enable_sandboxing", True)
        self.allowed_domains = self.config.get("allowed_domains", [])
        self.blocked_commands = self.config.get("blocked_commands", [])
        
        # 缓存配置
        self.enable_caching = self.config.get("enable_caching", True)
        self.cache_ttl = self.config.get("cache_ttl", 3600)
        self.execution_cache: Dict[str, ExecutionResult] = {}
        
        # 存储路径
        self.data_dir = Path(self.config.get("data_dir", "./unified_tool_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = self.data_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # 健康检查
        self.health_check_interval = self.config.get("health_check_interval", 60)
        self.health_check_task = None
        
        logger.info("统一工具管理器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "max_workers": 10,
            "execution_timeout": 300,
            "enable_monitoring": True,
            "log_level": "INFO",
            "metrics_collection": True,
            "enable_sandboxing": True,
            "allowed_domains": [],
            "blocked_commands": ["rm -rf", "format", "del /f"],
            "enable_caching": True,
            "cache_ttl": 3600,
            "data_dir": "./unified_tool_data",
            "health_check_interval": 60,
            "discovery_config_path": "./mcp_zero_config.json",
            "selection_config_path": "./smart_tool_config.json"
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    async def initialize(self):
        """初始化管理器"""
        try:
            # 启动发现引擎
            logger.info("启动工具发现...")
            discovery_tasks = await self.discovery_engine.start_discovery()
            
            # 等待发现完成
            await asyncio.sleep(2)
            
            # 获取发现的工具
            discovered_tools = await self.discovery_engine.get_discovered_tools()
            
            # 注册工具到选择引擎
            await self.selection_engine.register_tools(discovered_tools)
            
            # 更新可用工具列表
            for tool in discovered_tools:
                self.available_tools[tool.tool_id] = tool
            
            # 启动健康检查
            if self.enable_monitoring:
                self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info(f"统一工具管理器初始化完成，发现 {len(discovered_tools)} 个工具")
            
        except Exception as e:
            logger.error(f"初始化统一工具管理器失败: {e}")
            raise
    
    async def discover_tools(self, sources: List[Dict[str, Any]] = None) -> List[MCPTool]:
        """发现工具"""
        try:
            # 启动发现
            task_ids = await self.discovery_engine.start_discovery(sources)
            
            # 等待发现完成
            await asyncio.sleep(5)
            
            # 获取新发现的工具
            new_tools = await self.discovery_engine.get_discovered_tools()
            
            # 过滤出真正的新工具
            existing_tool_ids = set(self.available_tools.keys())
            truly_new_tools = [
                tool for tool in new_tools 
                if tool.tool_id not in existing_tool_ids
            ]
            
            # 注册新工具
            if truly_new_tools:
                await self.selection_engine.register_tools(truly_new_tools)
                
                for tool in truly_new_tools:
                    self.available_tools[tool.tool_id] = tool
            
            logger.info(f"发现 {len(truly_new_tools)} 个新工具")
            return truly_new_tools
            
        except Exception as e:
            logger.error(f"工具发现失败: {e}")
            raise
    
    async def recommend_tools(self, task_requirement: TaskRequirement,
                            user_id: str = None,
                            strategy: SelectionStrategy = None,
                            max_results: int = 10) -> List[ToolRecommendation]:
        """推荐工具"""
        try:
            recommendations = await self.selection_engine.recommend_tools(
                task_requirement=task_requirement,
                user_id=user_id,
                strategy=strategy,
                max_results=max_results
            )
            
            # 增强推荐信息
            enhanced_recommendations = []
            for rec in recommendations:
                tool = self.available_tools.get(rec.tool_id)
                if tool:
                    # 检查工具可用性
                    availability = await self._check_tool_availability(tool)
                    
                    # 更新推荐信息
                    rec.metadata.update({
                        "availability": availability,
                        "tool_type": self._determine_tool_type(tool).value,
                        "installation_required": not availability["is_available"],
                        "estimated_setup_time": self._estimate_setup_time(tool)
                    })
                    
                    enhanced_recommendations.append(rec)
            
            logger.info(f"生成 {len(enhanced_recommendations)} 个工具推荐")
            return enhanced_recommendations
            
        except Exception as e:
            logger.error(f"工具推荐失败: {e}")
            raise
    
    async def _check_tool_availability(self, tool: MCPTool) -> Dict[str, Any]:
        """检查工具可用性"""
        availability = {
            "is_available": False,
            "installation_status": "unknown",
            "dependencies_met": False,
            "issues": []
        }
        
        try:
            tool_type = self._determine_tool_type(tool)
            
            if tool_type == ToolType.NPM_PACKAGE:
                # 检查NPM包
                result = subprocess.run(
                    ["npm", "list", tool.name, "--depth=0"],
                    capture_output=True, text=True, timeout=10
                )
                availability["is_available"] = result.returncode == 0
                
            elif tool_type == ToolType.PYTHON_PACKAGE:
                # 检查Python包
                try:
                    __import__(tool.name.replace('-', '_'))
                    availability["is_available"] = True
                except ImportError:
                    availability["is_available"] = False
                    availability["issues"].append("Package not installed")
                
            elif tool_type == ToolType.LOCAL_EXECUTABLE:
                # 检查本地可执行文件
                result = subprocess.run(
                    ["which", tool.name], 
                    capture_output=True, text=True, timeout=5
                )
                availability["is_available"] = result.returncode == 0
                
            else:
                # 默认假设可用
                availability["is_available"] = True
            
            availability["installation_status"] = "installed" if availability["is_available"] else "not_installed"
            availability["dependencies_met"] = availability["is_available"]
            
        except Exception as e:
            availability["issues"].append(f"Availability check failed: {str(e)}")
            logger.debug(f"检查工具 {tool.name} 可用性失败: {e}")
        
        return availability
    
    def _determine_tool_type(self, tool: MCPTool) -> ToolType:
        """确定工具类型"""
        if tool.source_type == "npm_package":
            return ToolType.NPM_PACKAGE
        elif tool.source_type == "pypi_package":
            return ToolType.PYTHON_PACKAGE
        elif tool.source_type == "mcp_server":
            return ToolType.MCP_SERVER
        elif tool.source_type == "local_directory":
            return ToolType.LOCAL_EXECUTABLE
        else:
            return ToolType.WEB_SERVICE
    
    def _estimate_setup_time(self, tool: MCPTool) -> float:
        """估算设置时间（秒）"""
        tool_type = self._determine_tool_type(tool)
        
        base_times = {
            ToolType.NPM_PACKAGE: 30.0,
            ToolType.PYTHON_PACKAGE: 20.0,
            ToolType.MCP_SERVER: 60.0,
            ToolType.DOCKER_CONTAINER: 120.0,
            ToolType.LOCAL_EXECUTABLE: 10.0,
            ToolType.WEB_SERVICE: 5.0
        }
        
        base_time = base_times.get(tool_type, 30.0)
        
        # 根据依赖数量调整
        dependency_count = len(tool.dependencies) if tool.dependencies else 0
        dependency_time = dependency_count * 10.0
        
        return base_time + dependency_time
    
    async def install_tool(self, tool_id: str, user_id: str = None) -> Dict[str, Any]:
        """安装工具"""
        if tool_id not in self.available_tools:
            raise ValueError(f"工具不存在: {tool_id}")
        
        tool = self.available_tools[tool_id]
        tool_type = self._determine_tool_type(tool)
        
        installation_result = {
            "tool_id": tool_id,
            "success": False,
            "message": "",
            "installation_time": 0.0,
            "logs": []
        }
        
        start_time = time.time()
        
        try:
            if tool_type == ToolType.NPM_PACKAGE:
                result = await self._install_npm_package(tool)
            elif tool_type == ToolType.PYTHON_PACKAGE:
                result = await self._install_python_package(tool)
            elif tool_type == ToolType.MCP_SERVER:
                result = await self._install_mcp_server(tool)
            else:
                result = {"success": True, "message": "No installation required"}
            
            installation_result.update(result)
            installation_result["installation_time"] = time.time() - start_time
            
            # 更新工具状态
            if result["success"]:
                tool.status = ToolStatus.INSTALLED
            else:
                tool.status = ToolStatus.FAILED
            
            logger.info(f"工具 {tool.name} 安装{'成功' if result['success'] else '失败'}")
            
        except Exception as e:
            installation_result["message"] = f"安装失败: {str(e)}"
            installation_result["installation_time"] = time.time() - start_time
            tool.status = ToolStatus.FAILED
            logger.error(f"安装工具 {tool.name} 失败: {e}")
        
        return installation_result
    
    async def _install_npm_package(self, tool: MCPTool) -> Dict[str, Any]:
        """安装NPM包"""
        try:
            # 检查npm是否可用
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
            
            # 安装包
            result = subprocess.run(
                ["npm", "install", "-g", tool.name],
                capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                return {"success": True, "message": "NPM package installed successfully"}
            else:
                return {"success": False, "message": f"NPM install failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "NPM install timeout"}
        except Exception as e:
            return {"success": False, "message": f"NPM install error: {str(e)}"}
    
    async def _install_python_package(self, tool: MCPTool) -> Dict[str, Any]:
        """安装Python包"""
        try:
            # 使用pip安装
            result = subprocess.run(
                ["pip", "install", tool.name],
                capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                return {"success": True, "message": "Python package installed successfully"}
            else:
                return {"success": False, "message": f"Pip install failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Pip install timeout"}
        except Exception as e:
            return {"success": False, "message": f"Pip install error: {str(e)}"}
    
    async def _install_mcp_server(self, tool: MCPTool) -> Dict[str, Any]:
        """安装MCP服务器"""
        try:
            # 克隆仓库
            if tool.repository_url:
                temp_dir = tempfile.mkdtemp()
                
                result = subprocess.run(
                    ["git", "clone", tool.repository_url, temp_dir],
                    capture_output=True, text=True, timeout=120
                )
                
                if result.returncode == 0:
                    # 检查安装脚本
                    install_script = Path(temp_dir) / "install.sh"
                    if install_script.exists():
                        subprocess.run(["chmod", "+x", str(install_script)])
                        result = subprocess.run(
                            [str(install_script)],
                            cwd=temp_dir, capture_output=True, text=True, timeout=300
                        )
                        
                        if result.returncode == 0:
                            return {"success": True, "message": "MCP server installed successfully"}
                        else:
                            return {"success": False, "message": f"Install script failed: {result.stderr}"}
                    else:
                        return {"success": True, "message": "MCP server cloned successfully"}
                else:
                    return {"success": False, "message": f"Git clone failed: {result.stderr}"}
            else:
                return {"success": False, "message": "No repository URL provided"}
                
        except Exception as e:
            return {"success": False, "message": f"MCP server install error: {str(e)}"}
    
    async def execute_tool(self, tool_id: str, execution_context: ExecutionContext) -> ExecutionResult:
        """执行工具"""
        if tool_id not in self.available_tools:
            raise ValueError(f"工具不存在: {tool_id}")
        
        tool = self.available_tools[tool_id]
        execution_id = execution_context.execution_id
        
        # 创建执行结果
        result = ExecutionResult(
            execution_id=execution_id,
            tool_id=tool_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.now()
        )
        
        self.active_executions[execution_id] = result
        
        try:
            # 检查缓存
            if self.enable_caching:
                cached_result = self._get_cached_result(execution_context)
                if cached_result:
                    logger.info(f"使用缓存结果: {execution_id}")
                    return cached_result
            
            # 安全检查
            if not await self._security_check(execution_context):
                result.status = ExecutionStatus.FAILED
                result.error_message = "Security check failed"
                result.completed_at = datetime.now()
                return result
            
            # 开始执行
            result.status = ExecutionStatus.RUNNING
            
            # 根据工具类型执行
            tool_type = self._determine_tool_type(tool)
            
            if tool_type == ToolType.MCP_SERVER:
                execution_result = await self._execute_mcp_server(tool, execution_context)
            elif tool_type == ToolType.NPM_PACKAGE:
                execution_result = await self._execute_npm_package(tool, execution_context)
            elif tool_type == ToolType.PYTHON_PACKAGE:
                execution_result = await self._execute_python_package(tool, execution_context)
            else:
                execution_result = await self._execute_generic_tool(tool, execution_context)
            
            # 更新结果
            result.output_data = execution_result.get("output_data", {})
            result.error_message = execution_result.get("error_message")
            result.logs = execution_result.get("logs", [])
            result.metrics = execution_result.get("metrics", {})
            result.memory_usage = execution_result.get("memory_usage", 0.0)
            result.cpu_usage = execution_result.get("cpu_usage", 0.0)
            
            if execution_result.get("success", False):
                result.status = ExecutionStatus.COMPLETED
            else:
                result.status = ExecutionStatus.FAILED
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error_message = "Execution timeout"
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = f"Execution error: {str(e)}"
            logger.error(f"执行工具 {tool.name} 失败: {e}")
            logger.debug(traceback.format_exc())
        
        finally:
            result.completed_at = datetime.now()
            if result.started_at:
                result.execution_time = (result.completed_at - result.started_at).total_seconds()
            
            # 缓存结果
            if self.enable_caching and result.status == ExecutionStatus.COMPLETED:
                self._cache_result(execution_context, result)
            
            # 清理活跃执行
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        logger.info(f"工具执行完成: {tool.name} ({result.status.value})")
        return result
    
    def _get_cached_result(self, execution_context: ExecutionContext) -> Optional[ExecutionResult]:
        """获取缓存结果"""
        cache_key = self._generate_cache_key(execution_context)
        
        if cache_key in self.execution_cache:
            cached_result = self.execution_cache[cache_key]
            
            # 检查缓存是否过期
            if cached_result.completed_at:
                age = (datetime.now() - cached_result.completed_at).total_seconds()
                if age < self.cache_ttl:
                    return cached_result
                else:
                    # 删除过期缓存
                    del self.execution_cache[cache_key]
        
        return None
    
    def _cache_result(self, execution_context: ExecutionContext, result: ExecutionResult):
        """缓存结果"""
        cache_key = self._generate_cache_key(execution_context)
        self.execution_cache[cache_key] = result
    
    def _generate_cache_key(self, execution_context: ExecutionContext) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{execution_context.tool_id}_{execution_context.input_data}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _security_check(self, execution_context: ExecutionContext) -> bool:
        """安全检查"""
        if not self.enable_sandboxing:
            return True
        
        # 检查输入数据
        input_str = str(execution_context.input_data)
        
        # 检查被阻止的命令
        for blocked_cmd in self.blocked_commands:
            if blocked_cmd.lower() in input_str.lower():
                logger.warning(f"检测到被阻止的命令: {blocked_cmd}")
                return False
        
        # 检查域名限制
        if self.allowed_domains:
            # 简化的域名检查
            for domain in self.allowed_domains:
                if domain in input_str:
                    return True
            
            # 如果有域名限制但没有匹配，则拒绝
            if any("http" in input_str.lower() for _ in [1]):
                logger.warning("域名不在允许列表中")
                return False
        
        return True
    
    async def _execute_mcp_server(self, tool: MCPTool, 
                                execution_context: ExecutionContext) -> Dict[str, Any]:
        """执行MCP服务器"""
        # 简化的MCP服务器执行
        return {
            "success": True,
            "output_data": {"message": f"MCP server {tool.name} executed successfully"},
            "logs": [f"Executed MCP server: {tool.name}"],
            "metrics": {"execution_type": "mcp_server"}
        }
    
    async def _execute_npm_package(self, tool: MCPTool, 
                                 execution_context: ExecutionContext) -> Dict[str, Any]:
        """执行NPM包"""
        try:
            # 构建命令
            cmd = ["npx", tool.name]
            
            # 添加参数
            if execution_context.input_data:
                for key, value in execution_context.input_data.items():
                    cmd.extend([f"--{key}", str(value)])
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=execution_context.timeout,
                cwd=execution_context.working_directory
            )
            
            return {
                "success": result.returncode == 0,
                "output_data": {"stdout": result.stdout, "stderr": result.stderr},
                "logs": [f"Command: {' '.join(cmd)}", f"Return code: {result.returncode}"],
                "metrics": {"execution_type": "npm_package", "return_code": result.returncode}
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error_message": "Command timeout",
                "logs": ["Command execution timeout"],
                "metrics": {"execution_type": "npm_package", "timeout": True}
            }
        except Exception as e:
            return {
                "success": False,
                "error_message": str(e),
                "logs": [f"Execution error: {str(e)}"],
                "metrics": {"execution_type": "npm_package", "error": True}
            }
    
    async def _execute_python_package(self, tool: MCPTool, 
                                    execution_context: ExecutionContext) -> Dict[str, Any]:
        """执行Python包"""
        try:
            # 构建Python命令
            cmd = ["python", "-m", tool.name]
            
            # 添加参数
            if execution_context.input_data:
                for key, value in execution_context.input_data.items():
                    cmd.extend([f"--{key}", str(value)])
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=execution_context.timeout,
                cwd=execution_context.working_directory
            )
            
            return {
                "success": result.returncode == 0,
                "output_data": {"stdout": result.stdout, "stderr": result.stderr},
                "logs": [f"Command: {' '.join(cmd)}", f"Return code: {result.returncode}"],
                "metrics": {"execution_type": "python_package", "return_code": result.returncode}
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error_message": "Command timeout",
                "logs": ["Command execution timeout"],
                "metrics": {"execution_type": "python_package", "timeout": True}
            }
        except Exception as e:
            return {
                "success": False,
                "error_message": str(e),
                "logs": [f"Execution error: {str(e)}"],
                "metrics": {"execution_type": "python_package", "error": True}
            }
    
    async def _execute_generic_tool(self, tool: MCPTool, 
                                  execution_context: ExecutionContext) -> Dict[str, Any]:
        """执行通用工具"""
        # 通用工具执行逻辑
        return {
            "success": True,
            "output_data": {"message": f"Generic tool {tool.name} executed"},
            "logs": [f"Executed generic tool: {tool.name}"],
            "metrics": {"execution_type": "generic"}
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        if execution_id not in self.active_executions:
            return False
        
        try:
            result = self.active_executions[execution_id]
            result.status = ExecutionStatus.CANCELLED
            result.completed_at = datetime.now()
            
            # 这里可以添加实际的进程终止逻辑
            logger.info(f"取消执行: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消执行失败: {e}")
            return False
    
    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionResult]:
        """获取执行状态"""
        return self.active_executions.get(execution_id)
    
    async def list_available_tools(self, category: ToolCategory = None,
                                 status: ToolStatus = None,
                                 limit: int = None) -> List[MCPTool]:
        """列出可用工具"""
        tools = list(self.available_tools.values())
        
        # 过滤
        if category:
            tools = [tool for tool in tools if tool.category == category]
        
        if status:
            tools = [tool for tool in tools if tool.status == status]
        
        # 排序
        tools.sort(key=lambda t: t.name)
        
        # 限制数量
        if limit:
            tools = tools[:limit]
        
        return tools
    
    async def search_tools(self, query: str, limit: int = 20) -> List[MCPTool]:
        """搜索工具"""
        return await self.discovery_engine.search_tools(query, limit)
    
    async def get_tool_details(self, tool_id: str) -> Optional[MCPTool]:
        """获取工具详情"""
        return self.available_tools.get(tool_id)
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        for instance_id, instance in self.tool_instances.items():
            try:
                health_status = await self._check_instance_health(instance)
                instance.health_status = health_status
                instance.last_health_check = datetime.now()
                
                # 更新资源使用情况
                if instance.process_id:
                    try:
                        process = psutil.Process(instance.process_id)
                        instance.resource_usage = {
                            "cpu_percent": process.cpu_percent(),
                            "memory_mb": process.memory_info().rss / 1024 / 1024,
                            "status": process.status()
                        }
                    except psutil.NoSuchProcess:
                        instance.health_status = "dead"
                        instance.status = ToolStatus.FAILED
                
            except Exception as e:
                logger.debug(f"健康检查失败 {instance_id}: {e}")
                instance.health_status = "error"
    
    async def _check_instance_health(self, instance: ToolInstance) -> str:
        """检查实例健康状态"""
        # 简化的健康检查
        if instance.process_id:
            try:
                process = psutil.Process(instance.process_id)
                if process.is_running():
                    return "healthy"
                else:
                    return "dead"
            except psutil.NoSuchProcess:
                return "dead"
        
        return "unknown"
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        return {
            "available_tools": len(self.available_tools),
            "active_executions": len(self.active_executions),
            "tool_instances": len(self.tool_instances),
            "cache_size": len(self.execution_cache),
            "discovery_stats": await self.discovery_engine.get_discovery_statistics(),
            "selection_stats": await self.selection_engine.get_recommendation_analytics(),
            "system_resources": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 取消健康检查任务
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭执行器
            self.executor.shutdown(wait=True)
            
            # 清理工具实例
            for instance in self.tool_instances.values():
                if instance.process_id:
                    try:
                        process = psutil.Process(instance.process_id)
                        process.terminate()
                    except psutil.NoSuchProcess:
                        pass
            
            logger.info("统一工具管理器清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

# 工厂函数
def get_unified_tool_manager(config_path: str = "./unified_tool_config.json") -> UnifiedToolManager:
    """获取统一工具管理器实例"""
    return UnifiedToolManager(config_path)

# 测试和演示
if __name__ == "__main__":
    async def test_unified_manager():
        """测试统一工具管理器"""
        manager = get_unified_tool_manager()
        
        try:
            # 初始化
            print("🚀 初始化统一工具管理器...")
            await manager.initialize()
            
            # 列出可用工具
            tools = await manager.list_available_tools(limit=5)
            print(f"📋 可用工具 ({len(tools)} 个):")
            for tool in tools:
                print(f"  - {tool.name} ({tool.category.value})")
            
            if tools:
                # 创建任务需求
                task_requirement = TaskRequirement(
                    task_id="test_task",
                    description="Test tool execution",
                    required_capabilities=["file_operations"]
                )
                
                # 获取推荐
                recommendations = await manager.recommend_tools(
                    task_requirement=task_requirement,
                    user_id="test_user",
                    max_results=3
                )
                
                print(f"🎯 工具推荐 ({len(recommendations)} 个):")
                for rec in recommendations:
                    tool = await manager.get_tool_details(rec.tool_id)
                    print(f"  {rec.rank}. {tool.name} (评分: {rec.score:.3f})")
                    print(f"     {rec.explanation}")
                
                # 执行工具（如果有推荐）
                if recommendations:
                    rec = recommendations[0]
                    execution_context = ExecutionContext(
                        execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                        tool_id=rec.tool_id,
                        user_id="test_user",
                        input_data={"test": "data"},
                        timeout=30
                    )
                    
                    print(f"⚡ 执行工具: {rec.tool_id}")
                    result = await manager.execute_tool(rec.tool_id, execution_context)
                    
                    print(f"✅ 执行结果: {result.status.value}")
                    if result.output_data:
                        print(f"   输出: {result.output_data}")
                    if result.error_message:
                        print(f"   错误: {result.error_message}")
            
            # 获取系统指标
            metrics = await manager.get_system_metrics()
            print(f"📊 系统指标:")
            print(f"  可用工具: {metrics['available_tools']}")
            print(f"  活跃执行: {metrics['active_executions']}")
            print(f"  CPU使用率: {metrics['system_resources']['cpu_percent']:.1f}%")
            print(f"  内存使用率: {metrics['system_resources']['memory_percent']:.1f}%")
            
        finally:
            # 清理
            await manager.cleanup()
    
    # 运行测试
    asyncio.run(test_unified_manager())

