"""
Local Adapter Engine - 本地适配引擎
专注于本地资源管理和能力提供

通过 Deployment MCP 接收部署指令并在本地执行
"""

import asyncio
import json
import logging
import os
import sys
import time
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List
import toml

# 本地组件导入
from .local_resource_manager import LocalResourceManager, SystemInfo, ResourceUsage
from .platform.platform_detector import PlatformDetector
from .platform.command_adapter import CommandAdapter

class LocalAdapterEngine:
    """本地适配引擎 - 专注本地能力的核心引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化本地适配引擎
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "local_adapter_config.toml"
        self.config = self._load_config()
        self.logger = self._setup_logger()
        
        # 核心组件
        self.resource_manager = LocalResourceManager(self.config.get("resource_manager", {}))
        self.platform_detector = PlatformDetector()
        self.command_adapter = CommandAdapter()
        
        # 本地环境信息
        self.environment_id = self.config.get("environment_id", f"local_adapter_{int(time.time())}")
        self.environment_type = None
        self.platform_info = None
        
        # 运行状态
        self.is_running = False
        self.start_time = None
        
        # 部署状态
        self.active_deployments = {}
        self.deployment_history = []
        
        # 端云协调相关
        self.cloud_endpoint = None
        self.coordination_mode = self.config.get("edge_cloud", {}).get("coordination_mode", "intelligent")
        
        self.logger.info("Local Adapter Engine 初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = toml.load(f)
                return config
            else:
                # 使用默认配置
                return self._create_default_config()
        except Exception as e:
            print(f"配置加载失败，使用默认配置: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        return {
            "mcp_server": {
                "host": "0.0.0.0",
                "port": 5000,
                "websocket_port": 5001
            },
            "edge_cloud": {
                "coordination_mode": "intelligent",
                "failover_enabled": True,
                "load_balancing": True,
                "sync_interval": 30
            },
            "local_resources": {
                "max_cpu_usage": 80,
                "max_memory_usage": 80,
                "storage_path": "./local_storage",
                "temp_path": "./temp"
            },
            "deployment": {
                "auto_switch": True,
                "rollback_enabled": True,
                "health_check_interval": 10
            },
            "security": {
                "role_system_enabled": True,
                "api_key_required": True,
                "audit_logging": True
            },
            "logging": {
                "level": "INFO",
                "file": "local_adapter.log"
            }
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志系统"""
        log_config = self.config.get("logging", {})
        log_level = log_config.get("level", "INFO")
        log_file = log_config.get("file", "local_adapter.log")
        
        # 创建logger
        logger = logging.getLogger("LocalAdapterEngine")
        logger.setLevel(getattr(logging, log_level))
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    async def start(self):
        """启动本地适配引擎"""
        try:
            self.logger.info("启动Local Adapter Engine...")
            self.start_time = time.time()
            
            # 创建必要的目录
            self._create_directories()
            
            # 初始化MCP服务器
            if MCPServer:
                server_config = self.config.get("mcp_server", {})
                self.mcp_server = MCPServer(server_config)
                await self.mcp_server._initialize_services()
            
            # 初始化Manus集成
            if MCPManusIntegration:
                self.manus_integration = MCPManusIntegration()
            
            # 初始化链管理器
            if ReplayChainManager:
                self.chain_manager = ReplayChainManager()
            
            self.is_running = True
            self.logger.info("✅ Local Adapter Engine启动成功")
            
            # 运行主循环
            await self._run_main_loop()
            
        except Exception as e:
            self.logger.error(f"启动Local Adapter Engine失败: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """停止本地适配引擎"""
        try:
            self.logger.info("停止Local Adapter Engine...")
            
            if self.mcp_server:
                await self.mcp_server._cleanup_services()
                self.mcp_server = None
            
            self.is_running = False
            self.logger.info("✅ Local Adapter Engine已停止")
            
        except Exception as e:
            self.logger.error(f"停止Local Adapter Engine失败: {e}")
    
    def _create_directories(self):
        """创建必要的目录"""
        local_config = self.config.get("local_resources", {})
        storage_path = local_config.get("storage_path", "./local_storage")
        temp_path = local_config.get("temp_path", "./temp")
        
        for path in [storage_path, temp_path]:
            Path(path).mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"创建目录: {path}")
    
    async def _run_main_loop(self):
        """运行主循环"""
        sync_interval = self.config.get("edge_cloud", {}).get("sync_interval", 30)
        
        while self.is_running:
            try:
                # 执行定期任务
                await self._periodic_tasks()
                
                # 等待下一个周期
                await asyncio.sleep(sync_interval)
                
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                await asyncio.sleep(5)  # 错误后短暂等待
    
    async def _periodic_tasks(self):
        """执行定期任务"""
        # 健康检查
        await self._health_check()
        
        # 资源监控
        await self._monitor_resources()
        
        # 端云同步
        await self._sync_with_cloud()
    
    async def _health_check(self):
        """健康检查"""
        try:
            # 检查MCP服务器状态
            if self.mcp_server:
                # 这里可以添加具体的健康检查逻辑
                pass
            
            # 检查本地资源
            # 这里可以添加CPU、内存、磁盘检查
            
            self.logger.debug("健康检查完成")
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
    
    async def _monitor_resources(self):
        """监控本地资源"""
        try:
            # 这里可以添加资源监控逻辑
            # 例如：CPU使用率、内存使用率、磁盘空间等
            self.logger.debug("资源监控完成")
            
        except Exception as e:
            self.logger.error(f"资源监控失败: {e}")
    
    async def _sync_with_cloud(self):
        """与云端同步"""
        try:
            if self.cloud_endpoint:
                # 这里可以添加与云端同步的逻辑
                pass
            
            self.logger.debug("云端同步完成")
            
        except Exception as e:
            self.logger.error(f"云端同步失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        status = {
            "service_name": "Local Adapter Engine",
            "version": "1.0.0",
            "is_running": self.is_running,
            "start_time": self.start_time,
            "coordination_mode": self.coordination_mode
        }
        
        # 添加MCP服务器状态
        if self.mcp_server:
            status["mcp_server_status"] = "running"
        else:
            status["mcp_server_status"] = "stopped"
        
        # 添加Manus集成状态
        if self.manus_integration:
            status["manus_integration_status"] = "connected"
        else:
            status["manus_integration_status"] = "disconnected"
        
        # 添加链管理器状态
        if self.chain_manager:
            status["chain_manager_status"] = {
                "total_tasks": len(self.chain_manager.chains) if hasattr(self.chain_manager, 'chains') else 0,
                "total_chains": len(self.chain_manager.chains) if hasattr(self.chain_manager, 'chains') else 0
            }
        
        return status
    
    # MCP工具方法
    async def execute_local_command(self, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行本地命令"""
        try:
            self.logger.info(f"执行本地命令: {command}")
            
            # 这里可以添加具体的命令执行逻辑
            result = {
                "success": True,
                "command": command,
                "args": args or {},
                "output": f"命令 {command} 执行成功",
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行本地命令失败: {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def manage_local_files(self, operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """管理本地文件"""
        try:
            self.logger.info(f"文件操作: {operation} - {path}")
            
            # 这里可以添加具体的文件操作逻辑
            result = {
                "success": True,
                "operation": operation,
                "path": path,
                "message": f"文件操作 {operation} 完成",
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"文件操作失败: {e}")
            return {
                "success": False,
                "operation": operation,
                "path": path,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def coordinate_with_cloud(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """与云端协调任务"""
        try:
            self.logger.info(f"端云协调任务: {task.get('name', 'unknown')}")
            
            # 根据协调模式决定执行策略
            if self.coordination_mode == "local_first":
                # 优先本地执行
                return await self._execute_locally(task)
            elif self.coordination_mode == "cloud_first":
                # 优先云端执行
                return await self._execute_on_cloud(task)
            else:  # intelligent
                # 智能选择
                return await self._intelligent_execution(task)
                
        except Exception as e:
            self.logger.error(f"端云协调失败: {e}")
            return {
                "success": False,
                "task": task,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _execute_locally(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """本地执行任务"""
        # 这里可以添加本地执行逻辑
        return {
            "success": True,
            "execution_location": "local",
            "task": task,
            "timestamp": time.time()
        }
    
    async def _execute_on_cloud(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """云端执行任务"""
        # 这里可以添加云端执行逻辑
        return {
            "success": True,
            "execution_location": "cloud",
            "task": task,
            "timestamp": time.time()
        }
    
    async def _intelligent_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """智能选择执行位置"""
        # 这里可以添加智能选择逻辑
        # 例如：根据任务类型、资源使用情况、网络延迟等因素决定
        
        # 简单示例：根据任务类型选择
        task_type = task.get("type", "unknown")
        
        if task_type in ["file_operation", "local_command"]:
            return await self._execute_locally(task)
        elif task_type in ["ai_inference", "heavy_computation"]:
            return await self._execute_on_cloud(task)
        else:
            # 默认本地执行
            return await self._execute_locally(task)

# CLI主函数
async def cli_main():
    """CLI主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local Adapter Engine")
    parser.add_argument("--config", "-c", help="配置文件路径", default="config.toml")
    parser.add_argument("--host", help="服务器主机", default="0.0.0.0")
    parser.add_argument("--port", "-p", type=int, help="服务器端口", default=5000)
    parser.add_argument("--log-level", help="日志级别", default="INFO")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 启动命令
    start_parser = subparsers.add_parser("start", help="启动Local Adapter Engine")
    start_parser.add_argument("--daemon", "-d", action="store_true", help="后台运行")
    
    # 停止命令
    stop_parser = subparsers.add_parser("stop", help="停止Local Adapter Engine")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="查看引擎状态")
    
    args = parser.parse_args()
    
    if args.command == "start":
        engine = LocalAdapterEngine(args.config)
        try:
            await engine.start()
        except KeyboardInterrupt:
            print("\n收到停止信号，正在关闭...")
            await engine.stop()
    
    elif args.command == "stop":
        print("停止Local Adapter Engine...")
        # 这里可以添加停止逻辑
    
    elif args.command == "status":
        engine = LocalAdapterEngine(args.config)
        status = engine.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(cli_main())


        
        self.logger.info(f"本地适配引擎初始化 - 环境ID: {self.environment_id}")
    
    async def start(self):
        """启动本地适配引擎"""
        try:
            self.logger.info("启动本地适配引擎...")
            
            # 检测平台信息
            await self._detect_platform()
            
            # 启动资源管理器
            await self.resource_manager.start()
            
            # 初始化命令适配器
            await self.command_adapter.initialize(self.platform_info)
            
            self.is_running = True
            self.start_time = time.time()
            
            self.logger.info(f"本地适配引擎启动成功 - 平台: {self.environment_type}")
            
        except Exception as e:
            self.logger.error(f"启动本地适配引擎失败: {e}")
            raise
    
    async def stop(self):
        """停止本地适配引擎"""
        try:
            self.logger.info("停止本地适配引擎...")
            
            self.is_running = False
            
            # 停止资源管理器
            if self.resource_manager:
                await self.resource_manager.stop()
            
            self.logger.info("本地适配引擎已停止")
            
        except Exception as e:
            self.logger.error(f"停止本地适配引擎失败: {e}")
    
    async def _detect_platform(self):
        """检测平台信息"""
        try:
            self.platform_info = await self.platform_detector.detect()
            self.environment_type = self.platform_info.get("environment_type")
            
            self.logger.info(f"平台检测完成: {self.platform_info}")
            
        except Exception as e:
            self.logger.error(f"平台检测失败: {e}")
            raise
    
    async def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        执行本地命令
        
        Args:
            command: 要执行的命令
            **kwargs: 命令参数
            
        Returns:
            Dict: 执行结果
        """
        try:
            self.logger.info(f"执行本地命令: {command}")
            
            # 通过命令适配器执行
            result = await self.command_adapter.execute_command(
                command, 
                platform=self.environment_type,
                **kwargs
            )
            
            self.logger.debug(f"命令执行结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        获取本地能力信息
        
        Returns:
            Dict: 能力信息
        """
        try:
            # 获取资源管理器的能力摘要
            capabilities = await self.resource_manager.get_capabilities_summary()
            
            # 添加平台信息
            capabilities.update({
                "environment_id": self.environment_id,
                "environment_type": self.environment_type,
                "platform_info": self.platform_info,
                "engine_status": {
                    "is_running": self.is_running,
                    "start_time": self.start_time,
                    "uptime": time.time() - self.start_time if self.start_time else 0
                }
            })
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"获取能力信息失败: {e}")
            return {"error": str(e)}
    
    async def get_resource_status(self) -> Dict[str, Any]:
        """
        获取资源状态
        
        Returns:
            Dict: 资源状态
        """
        try:
            current_usage = self.resource_manager.get_current_usage()
            average_usage = self.resource_manager.get_average_usage()
            system_info = self.resource_manager.get_system_info()
            
            return {
                "system_info": system_info.__dict__ if system_info else None,
                "current_usage": current_usage.__dict__ if current_usage else None,
                "average_usage": average_usage,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"获取资源状态失败: {e}")
            return {"error": str(e)}
    
    async def execute_deployment_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行部署任务
        
        Args:
            task_config: 部署任务配置
            
        Returns:
            Dict: 执行结果
        """
        try:
            task_id = task_config.get("task_id", f"task_{int(time.time())}")
            self.logger.info(f"执行部署任务: {task_id}")
            
            # 记录活跃部署
            self.active_deployments[task_id] = {
                "config": task_config,
                "start_time": time.time(),
                "status": "running"
            }
            
            # 根据任务类型执行相应操作
            task_type = task_config.get("type", "unknown")
            
            if task_type == "shell_command":
                result = await self._execute_shell_deployment(task_config)
            elif task_type == "file_operation":
                result = await self._execute_file_deployment(task_config)
            elif task_type == "service_management":
                result = await self._execute_service_deployment(task_config)
            else:
                result = {
                    "success": False,
                    "error": f"不支持的任务类型: {task_type}"
                }
            
            # 更新部署状态
            self.active_deployments[task_id].update({
                "status": "completed" if result.get("success") else "failed",
                "end_time": time.time(),
                "result": result
            })
            
            # 移动到历史记录
            self.deployment_history.append(self.active_deployments.pop(task_id))
            
            # 保持历史记录在合理范围内
            if len(self.deployment_history) > 100:
                self.deployment_history = self.deployment_history[-100:]
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行部署任务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }
    
    async def _execute_shell_deployment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行Shell命令部署"""
        try:
            command = config.get("command")
            if not command:
                return {"success": False, "error": "缺少命令参数"}
            
            result = await self.execute_command(command, **config.get("params", {}))
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_file_deployment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作部署"""
        try:
            operation = config.get("operation")
            source = config.get("source")
            target = config.get("target")
            
            if operation == "copy":
                command = f"cp -r {source} {target}"
            elif operation == "move":
                command = f"mv {source} {target}"
            elif operation == "delete":
                command = f"rm -rf {target}"
            else:
                return {"success": False, "error": f"不支持的文件操作: {operation}"}
            
            result = await self.execute_command(command)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_service_deployment(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行服务管理部署"""
        try:
            action = config.get("action")
            service = config.get("service")
            
            if action == "start":
                command = f"systemctl start {service}"
            elif action == "stop":
                command = f"systemctl stop {service}"
            elif action == "restart":
                command = f"systemctl restart {service}"
            elif action == "status":
                command = f"systemctl status {service}"
            else:
                return {"success": False, "error": f"不支持的服务操作: {action}"}
            
            result = await self.execute_command(command)
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = toml.load(f)
                return config
            else:
                # 返回默认配置
                return {
                    "environment_id": f"local_adapter_{int(time.time())}",
                    "resource_manager": {
                        "monitor_interval": 10,
                        "history_size": 100
                    },
                    "logging": {
                        "level": "INFO",
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                }
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(__name__)
        
        # 避免重复设置
        if logger.handlers:
            return logger
        
        log_config = self.config.get("logging", {})
        level = getattr(logging, log_config.get("level", "INFO"))
        format_str = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(format_str)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.setLevel(level)
        
        return logger
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time if self.start_time else 0,
            "environment_id": self.environment_id,
            "environment_type": self.environment_type,
            "active_deployments": len(self.active_deployments),
            "deployment_history_count": len(self.deployment_history),
            "resource_manager_status": self.resource_manager.get_status() if self.resource_manager else None
        }

