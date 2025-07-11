#!/usr/bin/env python3
"""
PowerAutomation v4.6.2 端雲MCP適配器集成
Cloud-Edge MCP Adapter Integration for PowerAutomation v4.6.2

🌐 端雲集成架構:
1. 本地適配器: macOS終端/WSL/Linux
2. 遠端適配器: EC2 Linux連接
3. 端雲切換: 智能路由和負載均衡
4. 端雲溝通: 實時同步和狀態管理
5. 混合執行: 本地+雲端協同作業
"""

import asyncio
import json
import logging
import platform
import subprocess
import os
import shutil
import boto3
import paramiko
import websockets
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import uuid
import time

# 導入本地適配器
from local_mcp_adapter_integration import (
    LocalMCPAdapter, MacOSMCPAdapter, WSLMCPAdapter, LinuxMCPAdapter,
    LocalPlatform, MCPCommand, LocalEnvironment
)

logger = logging.getLogger(__name__)

class CloudPlatform(Enum):
    """雲端平台類型"""
    AWS_EC2 = "aws_ec2"
    AZURE_VM = "azure_vm"
    GCP_COMPUTE = "gcp_compute"
    ALICLOUD_ECS = "alicloud_ecs"

class ExecutionMode(Enum):
    """執行模式"""
    LOCAL_ONLY = "local_only"           # 僅本地執行
    CLOUD_ONLY = "cloud_only"           # 僅雲端執行
    EDGE_FIRST = "edge_first"           # 邊緣優先
    CLOUD_FIRST = "cloud_first"         # 雲端優先
    HYBRID = "hybrid"                   # 混合執行
    AUTO_SWITCH = "auto_switch"         # 自動切換

class SyncStrategy(Enum):
    """同步策略"""
    REAL_TIME = "real_time"             # 實時同步
    BATCH = "batch"                     # 批量同步
    ON_DEMAND = "on_demand"             # 按需同步
    EVENTUAL = "eventual"               # 最終一致性

@dataclass
class EC2Configuration:
    """EC2配置"""
    instance_id: str
    region: str
    availability_zone: str
    instance_type: str
    public_ip: Optional[str] = None
    private_ip: Optional[str] = None
    key_pair_name: str = ""
    security_groups: List[str] = field(default_factory=list)
    
@dataclass
class SSHConnection:
    """SSH連接配置"""
    hostname: str
    port: int = 22
    username: str = "ubuntu"
    key_file_path: str = ""
    password: Optional[str] = None
    timeout: int = 30

@dataclass
class CloudEdgeSession:
    """端雲會話"""
    session_id: str
    local_adapters: Dict[str, LocalMCPAdapter]
    remote_connections: Dict[str, 'RemoteMCPAdapter']
    execution_mode: ExecutionMode
    sync_strategy: SyncStrategy
    active_tasks: List[str] = field(default_factory=list)
    sync_queue: 'asyncio.Queue' = None

class RemoteMCPAdapter:
    """遠端MCP適配器（EC2 Linux）"""
    
    def __init__(self, ec2_config: EC2Configuration, ssh_config: SSHConnection):
        self.ec2_config = ec2_config
        self.ssh_config = ssh_config
        self.ssh_client = None
        self.sftp_client = None
        self.is_connected = False
        self.command_history = []
        self.remote_environment = None
        
    async def connect(self) -> Dict[str, Any]:
        """連接到遠端EC2實例"""
        print(f"🌐 連接到EC2實例: {self.ec2_config.instance_id}")
        
        try:
            # 創建SSH客戶端
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 建立連接
            if self.ssh_config.key_file_path:
                key = paramiko.RSAKey.from_private_key_file(self.ssh_config.key_file_path)
                self.ssh_client.connect(
                    hostname=self.ssh_config.hostname,
                    port=self.ssh_config.port,
                    username=self.ssh_config.username,
                    pkey=key,
                    timeout=self.ssh_config.timeout
                )
            else:
                self.ssh_client.connect(
                    hostname=self.ssh_config.hostname,
                    port=self.ssh_config.port,
                    username=self.ssh_config.username,
                    password=self.ssh_config.password,
                    timeout=self.ssh_config.timeout
                )
            
            # 創建SFTP客戶端
            self.sftp_client = self.ssh_client.open_sftp()
            self.is_connected = True
            
            # 檢測遠端環境
            await self._detect_remote_environment()
            
            print(f"✅ EC2連接成功: {self.ssh_config.hostname}")
            
            return {
                "status": "connected",
                "instance_id": self.ec2_config.instance_id,
                "hostname": self.ssh_config.hostname,
                "environment": {
                    "os": self.remote_environment.get("os", "unknown"),
                    "python": self.remote_environment.get("python", "unknown"),
                    "shell": self.remote_environment.get("shell", "/bin/bash")
                }
            }
            
        except Exception as e:
            logger.error(f"EC2連接失敗: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _detect_remote_environment(self):
        """檢測遠端環境"""
        detection_commands = [
            ("uname -a", "os"),
            ("python3 --version", "python"),
            ("echo $SHELL", "shell"),
            ("whoami", "user"),
            ("pwd", "home_dir")
        ]
        
        self.remote_environment = {}
        
        for cmd, key in detection_commands:
            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
                output = stdout.read().decode('utf-8').strip()
                self.remote_environment[key] = output
            except Exception as e:
                self.remote_environment[key] = f"detection_failed: {str(e)}"
    
    async def execute_remote_command(self, command: MCPCommand) -> Dict[str, Any]:
        """執行遠端命令"""
        if not self.is_connected:
            return {
                "status": "error",
                "error": "遠端連接未建立"
            }
        
        print(f"☁️ 遠端執行: {command.shell_command}")
        
        try:
            # 切換工作目錄並執行命令
            full_command = f"cd {command.working_directory} && {command.shell_command}"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(
                full_command,
                timeout=command.timeout
            )
            
            # 獲取輸出
            stdout_output = stdout.read().decode('utf-8', errors='ignore')
            stderr_output = stderr.read().decode('utf-8', errors='ignore')
            return_code = stdout.channel.recv_exit_status()
            
            result = {
                "command_id": command.command_id,
                "status": "success" if return_code == 0 else "failed",
                "return_code": return_code,
                "stdout": stdout_output,
                "stderr": stderr_output,
                "execution_location": "remote_ec2",
                "instance_id": self.ec2_config.instance_id
            }
            
            # 記錄命令歷史
            self.command_history.append({
                "command": command.shell_command,
                "timestamp": time.time(),
                "status": result["status"],
                "location": "remote"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"遠端命令執行失敗: {e}")
            return {
                "command_id": command.command_id,
                "status": "error",
                "error": str(e),
                "execution_location": "remote_ec2"
            }
    
    async def sync_files_to_remote(self, local_path: str, remote_path: str) -> Dict[str, Any]:
        """同步文件到遠端"""
        if not self.is_connected or not self.sftp_client:
            return {"status": "error", "error": "SFTP連接未建立"}
        
        try:
            print(f"📤 同步文件到遠端: {local_path} -> {remote_path}")
            
            if os.path.isfile(local_path):
                self.sftp_client.put(local_path, remote_path)
            elif os.path.isdir(local_path):
                # 創建遠端目錄
                try:
                    self.sftp_client.mkdir(remote_path)
                except:
                    pass  # 目錄可能已存在
                
                # 遞歸同步目錄
                for root, dirs, files in os.walk(local_path):
                    for file in files:
                        local_file = os.path.join(root, file)
                        relative_path = os.path.relpath(local_file, local_path)
                        remote_file = os.path.join(remote_path, relative_path).replace('\\', '/')
                        
                        # 確保遠端目錄存在
                        remote_dir = os.path.dirname(remote_file)
                        try:
                            self.sftp_client.mkdir(remote_dir)
                        except:
                            pass
                        
                        self.sftp_client.put(local_file, remote_file)
            
            return {
                "status": "success",
                "local_path": local_path,
                "remote_path": remote_path,
                "sync_direction": "local_to_remote"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def sync_files_from_remote(self, remote_path: str, local_path: str) -> Dict[str, Any]:
        """從遠端同步文件"""
        if not self.is_connected or not self.sftp_client:
            return {"status": "error", "error": "SFTP連接未建立"}
        
        try:
            print(f"📥 從遠端同步文件: {remote_path} -> {local_path}")
            
            # 檢查遠端路徑類型
            stat = self.sftp_client.stat(remote_path)
            
            if stat.st_mode & 0o040000:  # 目錄
                os.makedirs(local_path, exist_ok=True)
                
                # 遞歸同步目錄
                def sync_directory(remote_dir, local_dir):
                    for item in self.sftp_client.listdir_attr(remote_dir):
                        remote_item = f"{remote_dir}/{item.filename}"
                        local_item = os.path.join(local_dir, item.filename)
                        
                        if item.st_mode & 0o040000:  # 子目錄
                            os.makedirs(local_item, exist_ok=True)
                            sync_directory(remote_item, local_item)
                        else:  # 文件
                            self.sftp_client.get(remote_item, local_item)
                
                sync_directory(remote_path, local_path)
            else:  # 文件
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                self.sftp_client.get(remote_path, local_path)
            
            return {
                "status": "success",
                "remote_path": remote_path,
                "local_path": local_path,
                "sync_direction": "remote_to_local"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def disconnect(self):
        """斷開連接"""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
        self.is_connected = False
        print(f"🔌 已斷開EC2連接: {self.ssh_config.hostname}")

class CloudEdgeMCPManager:
    """端雲MCP管理器"""
    
    def __init__(self):
        self.local_adapters = {}
        self.remote_adapters = {}
        self.active_sessions = {}
        self.execution_mode = ExecutionMode.AUTO_SWITCH
        self.sync_strategy = SyncStrategy.REAL_TIME
        self.load_balancer = None
        self.metrics = {
            "local_commands": 0,
            "remote_commands": 0,
            "sync_operations": 0,
            "switch_events": 0
        }
        
    async def initialize_cloud_edge_integration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """初始化端雲集成"""
        print("🌐 初始化PowerAutomation端雲MCP集成...")
        
        init_results = {
            "local_adapters": {},
            "remote_adapters": {},
            "integration_status": "initializing"
        }
        
        try:
            # 1. 初始化本地適配器
            await self._initialize_local_adapters()
            init_results["local_adapters"] = {
                platform.value: "initialized" 
                for platform in self.local_adapters.keys()
            }
            
            # 2. 初始化遠端適配器
            ec2_configs = config.get("ec2_instances", [])
            await self._initialize_remote_adapters(ec2_configs)
            init_results["remote_adapters"] = {
                instance_id: "connected"
                for instance_id in self.remote_adapters.keys()
            }
            
            # 3. 設置負載均衡器
            await self._setup_load_balancer()
            
            # 4. 啟動同步服務
            await self._start_sync_service()
            
            init_results["integration_status"] = "success"
            init_results["capabilities"] = {
                "local_execution": len(self.local_adapters) > 0,
                "remote_execution": len(self.remote_adapters) > 0,
                "cloud_edge_switching": True,
                "real_time_sync": True,
                "load_balancing": True
            }
            
            print("✅ 端雲MCP集成初始化完成")
            return init_results
            
        except Exception as e:
            logger.error(f"端雲集成初始化失敗: {e}")
            init_results["integration_status"] = "failed"
            init_results["error"] = str(e)
            return init_results
    
    async def _initialize_local_adapters(self):
        """初始化本地適配器"""
        print("🔧 初始化本地MCP適配器...")
        
        # 檢測並初始化所有可用的本地平台
        current_platform = self._detect_current_platform()
        
        adapter_classes = {
            LocalPlatform.MACOS: MacOSMCPAdapter,
            LocalPlatform.WSL: WSLMCPAdapter,
            LocalPlatform.LINUX: LinuxMCPAdapter
        }
        
        # 初始化當前平台
        if current_platform in adapter_classes:
            adapter = adapter_classes[current_platform]()
            await adapter.initialize()
            self.local_adapters[current_platform] = adapter
            print(f"  ✅ {current_platform.value} 適配器已初始化")
    
    def _detect_current_platform(self) -> LocalPlatform:
        """檢測當前平台"""
        system = platform.system().lower()
        
        if system == "darwin":
            return LocalPlatform.MACOS
        elif system == "linux":
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        return LocalPlatform.WSL
            except:
                pass
            return LocalPlatform.LINUX
        else:
            return LocalPlatform.LINUX
    
    async def _initialize_remote_adapters(self, ec2_configs: List[Dict[str, Any]]):
        """初始化遠端適配器"""
        print("☁️ 初始化遠端EC2適配器...")
        
        for config in ec2_configs:
            try:
                ec2_config = EC2Configuration(**config["ec2"])
                ssh_config = SSHConnection(**config["ssh"])
                
                adapter = RemoteMCPAdapter(ec2_config, ssh_config)
                connection_result = await adapter.connect()
                
                if connection_result["status"] == "connected":
                    self.remote_adapters[ec2_config.instance_id] = adapter
                    print(f"  ✅ EC2 {ec2_config.instance_id} 已連接")
                else:
                    print(f"  ❌ EC2 {ec2_config.instance_id} 連接失敗: {connection_result.get('error')}")
                    
            except Exception as e:
                print(f"  ❌ EC2適配器初始化失敗: {e}")
    
    async def _setup_load_balancer(self):
        """設置負載均衡器"""
        self.load_balancer = {
            "strategy": "adaptive",  # 自適應策略
            "metrics": {
                "local_latency": [],
                "remote_latency": [],
                "local_load": 0.0,
                "remote_load": 0.0
            },
            "thresholds": {
                "max_local_load": 0.8,
                "max_remote_latency": 2.0,
                "switch_threshold": 0.3
            }
        }
    
    async def _start_sync_service(self):
        """啟動同步服務"""
        # 啟動後台同步任務
        asyncio.create_task(self._sync_service_loop())
    
    async def _sync_service_loop(self):
        """同步服務循環"""
        while True:
            try:
                # 執行同步操作
                await self._perform_sync_operations()
                
                # 根據同步策略設置等待時間
                if self.sync_strategy == SyncStrategy.REAL_TIME:
                    await asyncio.sleep(1)
                elif self.sync_strategy == SyncStrategy.BATCH:
                    await asyncio.sleep(30)
                else:
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.error(f"同步服務錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _perform_sync_operations(self):
        """執行同步操作"""
        # 這裡實現具體的同步邏輯
        pass
    
    async def create_cloud_edge_session(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """創建端雲會話"""
        session_id = f"cloud_edge_{uuid.uuid4().hex[:8]}"
        
        print(f"🔗 創建端雲會話: {session_id}")
        
        session = CloudEdgeSession(
            session_id=session_id,
            local_adapters=self.local_adapters.copy(),
            remote_connections=self.remote_adapters.copy(),
            execution_mode=ExecutionMode(config.get("execution_mode", "auto_switch")),
            sync_strategy=SyncStrategy(config.get("sync_strategy", "real_time")),
            sync_queue=asyncio.Queue()
        )
        
        self.active_sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "execution_mode": session.execution_mode.value,
            "sync_strategy": session.sync_strategy.value,
            "local_adapters": len(session.local_adapters),
            "remote_connections": len(session.remote_connections),
            "status": "active"
        }
    
    async def execute_smart_command(self, session_id: str, command: str, working_dir: str = None) -> Dict[str, Any]:
        """智能命令執行（自動選擇本地或遠端）"""
        if session_id not in self.active_sessions:
            return {"status": "error", "error": "會話不存在"}
        
        session = self.active_sessions[session_id]
        
        # 根據執行模式和負載情況決定執行位置
        execution_location = await self._determine_execution_location(session, command)
        
        command_obj = MCPCommand(
            command_id=f"smart_{uuid.uuid4().hex[:8]}",
            platform=LocalPlatform.LINUX,  # 默認
            shell_command=command,
            working_directory=working_dir or "/home/ubuntu"
        )
        
        if execution_location == "local":
            # 本地執行
            adapter = next(iter(session.local_adapters.values()))
            result = await adapter.execute_command(command_obj)
            result["execution_location"] = "local"
            self.metrics["local_commands"] += 1
            
        elif execution_location == "remote":
            # 遠端執行
            adapter = next(iter(session.remote_connections.values()))
            result = await adapter.execute_remote_command(command_obj)
            result["execution_location"] = "remote"
            self.metrics["remote_commands"] += 1
            
        else:
            # 混合執行
            result = await self._execute_hybrid_command(session, command_obj)
            self.metrics["local_commands"] += 1
            self.metrics["remote_commands"] += 1
        
        return result
    
    async def _determine_execution_location(self, session: CloudEdgeSession, command: str) -> str:
        """決定執行位置"""
        if session.execution_mode == ExecutionMode.LOCAL_ONLY:
            return "local"
        elif session.execution_mode == ExecutionMode.CLOUD_ONLY:
            return "remote"
        elif session.execution_mode == ExecutionMode.AUTO_SWITCH:
            # 基於負載和延遲自動選擇
            local_load = self.load_balancer["metrics"]["local_load"]
            remote_latency = sum(self.load_balancer["metrics"]["remote_latency"][-5:]) / max(len(self.load_balancer["metrics"]["remote_latency"][-5:]), 1)
            
            if local_load > 0.8 or remote_latency < 0.5:
                return "remote"
            else:
                return "local"
        else:
            return "hybrid"
    
    async def _execute_hybrid_command(self, session: CloudEdgeSession, command: MCPCommand) -> Dict[str, Any]:
        """混合執行命令"""
        print(f"🔄 混合執行: {command.shell_command}")
        
        # 同時在本地和遠端執行
        local_task = None
        remote_task = None
        
        if session.local_adapters:
            local_adapter = next(iter(session.local_adapters.values()))
            local_task = asyncio.create_task(local_adapter.execute_command(command))
        
        if session.remote_connections:
            remote_adapter = next(iter(session.remote_connections.values()))
            remote_task = asyncio.create_task(remote_adapter.execute_remote_command(command))
        
        # 等待兩個任務完成
        local_result = await local_task if local_task else None
        remote_result = await remote_task if remote_task else None
        
        return {
            "command_id": command.command_id,
            "status": "success",
            "execution_mode": "hybrid",
            "local_result": local_result,
            "remote_result": remote_result,
            "comparison": {
                "local_success": local_result and local_result.get("status") == "success",
                "remote_success": remote_result and remote_result.get("status") == "success",
                "outputs_match": local_result and remote_result and local_result.get("stdout") == remote_result.get("stdout")
            }
        }
    
    async def switch_execution_mode(self, session_id: str, new_mode: str) -> Dict[str, Any]:
        """切換執行模式"""
        if session_id not in self.active_sessions:
            return {"status": "error", "error": "會話不存在"}
        
        session = self.active_sessions[session_id]
        old_mode = session.execution_mode.value
        session.execution_mode = ExecutionMode(new_mode)
        
        self.metrics["switch_events"] += 1
        
        print(f"🔄 執行模式切換: {old_mode} -> {new_mode}")
        
        return {
            "session_id": session_id,
            "old_mode": old_mode,
            "new_mode": new_mode,
            "status": "switched"
        }
    
    async def sync_workspace(self, session_id: str, sync_direction: str = "bidirectional") -> Dict[str, Any]:
        """同步工作空間"""
        if session_id not in self.active_sessions:
            return {"status": "error", "error": "會話不存在"}
        
        session = self.active_sessions[session_id]
        sync_results = []
        
        print(f"🔄 同步工作空間: {sync_direction}")
        
        # 獲取本地和遠端工作目錄
        local_workspace = "/tmp/powerautomation_workspace"
        remote_workspace = "/home/ubuntu/powerautomation_workspace"
        
        for remote_adapter in session.remote_connections.values():
            if sync_direction in ["local_to_remote", "bidirectional"]:
                # 本地到遠端
                result = await remote_adapter.sync_files_to_remote(local_workspace, remote_workspace)
                sync_results.append({
                    "direction": "local_to_remote",
                    "result": result
                })
            
            if sync_direction in ["remote_to_local", "bidirectional"]:
                # 遠端到本地
                result = await remote_adapter.sync_files_from_remote(remote_workspace, local_workspace)
                sync_results.append({
                    "direction": "remote_to_local", 
                    "result": result
                })
        
        self.metrics["sync_operations"] += len(sync_results)
        
        return {
            "session_id": session_id,
            "sync_direction": sync_direction,
            "sync_results": sync_results,
            "status": "completed"
        }
    
    async def get_cloud_edge_status(self) -> Dict[str, Any]:
        """獲取端雲狀態"""
        return {
            "integration_status": "active",
            "local_adapters": {
                platform.value: {
                    "status": "active",
                    "commands_executed": len(adapter.command_history)
                }
                for platform, adapter in self.local_adapters.items()
            },
            "remote_adapters": {
                instance_id: {
                    "status": "connected" if adapter.is_connected else "disconnected",
                    "instance_id": adapter.ec2_config.instance_id,
                    "commands_executed": len(adapter.command_history)
                }
                for instance_id, adapter in self.remote_adapters.items()
            },
            "active_sessions": len(self.active_sessions),
            "metrics": self.metrics,
            "load_balancer": self.load_balancer,
            "capabilities": {
                "smart_routing": True,
                "auto_switching": True,
                "real_time_sync": True,
                "hybrid_execution": True,
                "load_balancing": True
            }
        }

# 演示函數
async def demo_cloud_edge_integration():
    """演示端雲MCP集成"""
    print("🌐 PowerAutomation v4.6.2 端雲MCP適配器集成演示")
    print("=" * 80)
    
    # 創建端雲管理器
    manager = CloudEdgeMCPManager()
    
    # 配置EC2實例（示例配置）
    config = {
        "ec2_instances": [
            {
                "ec2": {
                    "instance_id": "i-1234567890abcdef0",
                    "region": "us-west-2",
                    "availability_zone": "us-west-2a",
                    "instance_type": "t3.medium",
                    "public_ip": "54.123.45.67"
                },
                "ssh": {
                    "hostname": "54.123.45.67",
                    "username": "ubuntu",
                    "key_file_path": "/path/to/your/key.pem"
                }
            }
        ]
    }
    
    # 初始化端雲集成
    print("\n🚀 初始化端雲集成...")
    init_result = await manager.initialize_cloud_edge_integration(config)
    
    print(f"  初始化狀態: {init_result['integration_status']}")
    print(f"  本地適配器: {len(init_result['local_adapters'])}個")
    print(f"  遠端適配器: {len(init_result['remote_adapters'])}個")
    
    # 創建端雲會話
    print("\n🔗 創建端雲會話...")
    session_config = {
        "execution_mode": "auto_switch",
        "sync_strategy": "real_time"
    }
    
    session = await manager.create_cloud_edge_session(session_config)
    session_id = session["session_id"]
    
    print(f"  會話ID: {session_id}")
    print(f"  執行模式: {session['execution_mode']}")
    print(f"  同步策略: {session['sync_strategy']}")
    
    # 演示智能命令執行
    print("\n🤖 演示智能命令執行:")
    
    demo_commands = [
        "python3 --version",
        "uname -a",
        "ls -la /home",
        "df -h",
        "free -m"
    ]
    
    for cmd in demo_commands:
        print(f"\n  執行命令: {cmd}")
        result = await manager.execute_smart_command(session_id, cmd)
        
        if result["status"] == "success":
            location = result.get("execution_location", "unknown")
            output = result.get("stdout", "").strip()[:100]
            print(f"    ✅ [{location}] {output}{'...' if len(output) == 100 else ''}")
        else:
            print(f"    ❌ 執行失敗: {result.get('error', 'Unknown error')}")
    
    # 演示執行模式切換
    print("\n🔄 演示執行模式切換:")
    
    modes = ["local_only", "cloud_only", "hybrid"]
    for mode in modes:
        switch_result = await manager.switch_execution_mode(session_id, mode)
        print(f"  🔄 切換到 {mode}: {switch_result['status']}")
        
        # 測試當前模式下的命令執行
        test_result = await manager.execute_smart_command(session_id, "pwd")
        location = test_result.get("execution_location", "unknown")
        print(f"    測試結果: 在{location}執行")
    
    # 演示工作空間同步
    print("\n📁 演示工作空間同步:")
    
    sync_result = await manager.sync_workspace(session_id, "bidirectional")
    print(f"  同步狀態: {sync_result['status']}")
    print(f"  同步操作: {len(sync_result['sync_results'])}項")
    
    # 獲取端雲狀態
    print("\n📊 端雲集成狀態:")
    status = await manager.get_cloud_edge_status()
    
    print(f"  集成狀態: {status['integration_status']}")
    print(f"  活躍會話: {status['active_sessions']}個")
    print(f"  本地命令執行: {status['metrics']['local_commands']}次")
    print(f"  遠端命令執行: {status['metrics']['remote_commands']}次")
    print(f"  同步操作: {status['metrics']['sync_operations']}次")
    print(f"  模式切換: {status['metrics']['switch_events']}次")
    
    print(f"\n🎉 端雲MCP集成演示完成！")
    print(f"   PowerAutomation現在支持本地+EC2的智能端雲協同！")
    
    return manager

if __name__ == "__main__":
    asyncio.run(demo_cloud_edge_integration())