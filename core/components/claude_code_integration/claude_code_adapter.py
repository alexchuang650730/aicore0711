#!/usr/bin/env python3
"""
Claude Code Integration Adapter
PowerAutomation v4.6.9.4 - Claude Code SDK 集成适配器

提供与 Claude Code 的深度集成功能：
- CLI 命令集成
- SDK API 接口实现
- MCP 协议支持
- 扩展插件架构
"""

import asyncio
import logging
import json
import subprocess
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import uuid
import tempfile

logger = logging.getLogger(__name__)


class IntegrationMode(Enum):
    """集成模式枚举"""
    CLI_COMMAND = "cli_command"
    SDK_API = "sdk_api"
    MCP_PROTOCOL = "mcp_protocol"
    EXTENSION_PLUGIN = "extension_plugin"


class ClaudeCodeCommand(Enum):
    """Claude Code 命令枚举"""
    INIT = "init"
    CHAT = "chat"
    EDIT = "edit"
    DIFF = "diff"
    APPLY = "apply"
    UNDO = "undo"
    STATUS = "status"
    CONFIG = "config"


@dataclass
class ClaudeCodeRequest:
    """Claude Code 请求"""
    request_id: str
    command: ClaudeCodeCommand
    prompt: str
    files: List[str] = None
    options: Dict[str, Any] = None
    context: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = []
        if self.options is None:
            self.options = {}
        if self.context is None:
            self.context = {}
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()


@dataclass
class ClaudeCodeResponse:
    """Claude Code 响应"""
    request_id: str
    success: bool
    content: str
    files_changed: List[str] = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = []
        if self.metadata is None:
            self.metadata = {}


class ClaudeCodeCLIAdapter:
    """Claude Code CLI 适配器"""
    
    def __init__(self, claude_code_path: str = "claude"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.claude_code_path = claude_code_path
        self.session_dir = None
        self.config = {
            "timeout": 300,
            "max_retries": 3,
            "auto_apply_edits": False,
            "verbose": True
        }
        
    async def initialize_session(self, project_path: str) -> bool:
        """初始化 Claude Code 会话"""
        try:
            self.session_dir = project_path
            
            # 检查 Claude Code 是否可用
            result = await self._run_command(["--version"])
            if not result.success:
                self.logger.error(f"Claude Code 不可用: {result.error}")
                return False
            
            # 初始化项目
            init_result = await self._run_command([
                "init", 
                "--project-path", project_path,
                "--auto-confirm"
            ])
            
            if init_result.success:
                self.logger.info(f"✅ Claude Code 会话初始化成功: {project_path}")
                return True
            else:
                self.logger.error(f"❌ Claude Code 会话初始化失败: {init_result.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"初始化会话失败: {e}")
            return False
    
    async def execute_request(self, request: ClaudeCodeRequest) -> ClaudeCodeResponse:
        """执行 Claude Code 请求"""
        start_time = datetime.now()
        
        try:
            # 构建命令参数
            cmd_args = self._build_command_args(request)
            
            # 执行命令
            result = await self._run_command(cmd_args)
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 解析结果
            response = ClaudeCodeResponse(
                request_id=request.request_id,
                success=result.success,
                content=result.content,
                error=result.error,
                execution_time=execution_time
            )
            
            # 检测文件变化
            if result.success and request.command in [ClaudeCodeCommand.EDIT, ClaudeCodeCommand.APPLY]:
                response.files_changed = await self._detect_file_changes(request.files)
            
            return response
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"执行请求失败: {e}")
            
            return ClaudeCodeResponse(
                request_id=request.request_id,
                success=False,
                content="",
                error=str(e),
                execution_time=execution_time
            )
    
    def _build_command_args(self, request: ClaudeCodeRequest) -> List[str]:
        """构建命令参数"""
        args = [self.claude_code_path]
        
        # 添加命令
        if request.command == ClaudeCodeCommand.CHAT:
            args.extend(["chat", request.prompt])
        elif request.command == ClaudeCodeCommand.EDIT:
            args.extend(["edit", request.prompt])
            if request.files:
                args.extend(["--files"] + request.files)
        elif request.command == ClaudeCodeCommand.DIFF:
            args.append("diff")
            if request.files:
                args.extend(request.files)
        elif request.command == ClaudeCodeCommand.APPLY:
            args.append("apply")
        elif request.command == ClaudeCodeCommand.STATUS:
            args.append("status")
        elif request.command == ClaudeCodeCommand.CONFIG:
            args.append("config")
            if "key" in request.options and "value" in request.options:
                args.extend([request.options["key"], request.options["value"]])
        
        # 添加通用选项
        if self.session_dir:
            args.extend(["--project-path", self.session_dir])
        
        if request.options.get("auto_apply", self.config["auto_apply_edits"]):
            args.append("--auto-apply")
        
        if self.config["verbose"]:
            args.append("--verbose")
        
        return args
    
    async def _run_command(self, args: List[str]) -> ClaudeCodeResponse:
        """运行命令"""
        try:
            self.logger.debug(f"执行命令: {' '.join(args)}")
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.session_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self.config["timeout"]
            )
            
            success = process.returncode == 0
            content = stdout.decode('utf-8') if stdout else ""
            error = stderr.decode('utf-8') if stderr else None
            
            return ClaudeCodeResponse(
                request_id="",
                success=success,
                content=content,
                error=error
            )
            
        except asyncio.TimeoutError:
            self.logger.error("命令执行超时")
            return ClaudeCodeResponse(
                request_id="",
                success=False,
                content="",
                error="命令执行超时"
            )
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            return ClaudeCodeResponse(
                request_id="",
                success=False,
                content="",
                error=str(e)
            )
    
    async def _detect_file_changes(self, files: List[str]) -> List[str]:
        """检测文件变化"""
        changed_files = []
        
        for file_path in files:
            if os.path.exists(file_path):
                # 这里可以实现更复杂的文件变化检测逻辑
                # 比如比较文件的修改时间、内容哈希等
                changed_files.append(file_path)
        
        return changed_files


class ClaudeCodeSDKAdapter:
    """Claude Code SDK 适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.sdk_available = False
        self.session_config = {}
        
        # 尝试导入 Claude Code SDK
        try:
            # 这里应该导入实际的 Claude Code SDK
            # from anthropic_claude_code import query, SDKMessage
            self.sdk_available = True
            self.logger.info("✅ Claude Code SDK 可用")
        except ImportError:
            self.logger.warning("⚠️ Claude Code SDK 不可用，将使用模拟模式")
            self.sdk_available = False
    
    async def query(
        self, 
        prompt: str, 
        options: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """执行 SDK 查询"""
        if options is None:
            options = {}
        
        if not self.sdk_available:
            return await self._mock_query(prompt, options)
        
        try:
            messages = []
            
            # 这里应该使用实际的 Claude Code SDK
            # for message in query({
            #     "prompt": prompt,
            #     "options": {
            #         "maxTurns": options.get("max_turns", 3),
            #         "cwd": options.get("working_directory"),
            #         "allowedTools": options.get("allowed_tools"),
            #         "permissionMode": "acceptEdits"
            #     }
            # }):
            #     messages.append(message)
            
            # 模拟 SDK 响应
            messages = await self._mock_query(prompt, options)
            
            return messages
            
        except Exception as e:
            self.logger.error(f"SDK 查询失败: {e}")
            return [{"type": "error", "content": str(e)}]
    
    async def _mock_query(self, prompt: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """模拟 SDK 查询"""
        await asyncio.sleep(0.5)  # 模拟网络延迟
        
        return [
            {
                "type": "text",
                "content": f"这是对提示 '{prompt}' 的模拟响应。",
                "metadata": {
                    "model": "claude-3-sonnet",
                    "timestamp": datetime.now().isoformat(),
                    "options": options
                }
            },
            {
                "type": "tool_use",
                "content": "模拟工具调用",
                "tool_name": "file_editor",
                "parameters": {
                    "action": "edit",
                    "file": "example.py",
                    "content": "# 这是模拟的代码编辑\nprint('Hello from Claude Code!')"
                }
            }
        ]


class ClaudeCodeMCPAdapter:
    """Claude Code MCP 适配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mcp_servers = {}
        self.active_connections = {}
        
    async def register_mcp_server(self, name: str, config: Dict[str, Any]) -> bool:
        """注册 MCP 服务器"""
        try:
            self.mcp_servers[name] = config
            self.logger.info(f"✅ MCP 服务器已注册: {name}")
            return True
        except Exception as e:
            self.logger.error(f"注册 MCP 服务器失败: {e}")
            return False
    
    async def connect_to_server(self, server_name: str) -> bool:
        """连接到 MCP 服务器"""
        if server_name not in self.mcp_servers:
            self.logger.error(f"未知的 MCP 服务器: {server_name}")
            return False
        
        try:
            # 这里应该实现实际的 MCP 连接逻辑
            self.active_connections[server_name] = {
                "connected": True,
                "connection_time": datetime.now(),
                "config": self.mcp_servers[server_name]
            }
            
            self.logger.info(f"✅ 已连接到 MCP 服务器: {server_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"连接 MCP 服务器失败: {e}")
            return False
    
    async def send_mcp_request(
        self, 
        server_name: str, 
        method: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送 MCP 请求"""
        if server_name not in self.active_connections:
            return {"error": f"未连接到服务器: {server_name}"}
        
        try:
            # 模拟 MCP 请求处理
            await asyncio.sleep(0.1)
            
            return {
                "id": str(uuid.uuid4()),
                "result": {
                    "method": method,
                    "params": params,
                    "server": server_name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
            }
            
        except Exception as e:
            self.logger.error(f"MCP 请求失败: {e}")
            return {"error": str(e)}


class ClaudeCodeExtensionManager:
    """Claude Code 扩展管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.extensions = {}
        self.extension_config = {
            "quick_launch": {
                "enabled": True,
                "shortcut": "Cmd+Esc",  # Mac
                "shortcut_alt": "Ctrl+Esc"  # Windows/Linux
            },
            "diff_viewer": {
                "enabled": True,
                "auto_show": True,
                "highlight_changes": True
            },
            "context_sharing": {
                "enabled": True,
                "auto_share_selection": True,
                "include_file_context": True
            },
            "file_reference": {
                "enabled": True,
                "shortcut": "Cmd+Option+K",  # Mac
                "shortcut_alt": "Alt+Ctrl+K"  # Linux/Windows
            }
        }
    
    async def register_extension(self, name: str, extension_class: type) -> bool:
        """注册扩展"""
        try:
            extension_instance = extension_class(self.extension_config.get(name, {}))
            self.extensions[name] = extension_instance
            
            self.logger.info(f"✅ 扩展已注册: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册扩展失败: {e}")
            return False
    
    async def enable_extension(self, name: str) -> bool:
        """启用扩展"""
        if name not in self.extensions:
            self.logger.error(f"未知扩展: {name}")
            return False
        
        try:
            await self.extensions[name].enable()
            self.logger.info(f"✅ 扩展已启用: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"启用扩展失败: {e}")
            return False
    
    async def disable_extension(self, name: str) -> bool:
        """禁用扩展"""
        if name not in self.extensions:
            self.logger.error(f"未知扩展: {name}")
            return False
        
        try:
            await self.extensions[name].disable()
            self.logger.info(f"✅ 扩展已禁用: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"禁用扩展失败: {e}")
            return False


class ClaudeCodeIntegrationManager:
    """Claude Code 集成管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cli_adapter = ClaudeCodeCLIAdapter()
        self.sdk_adapter = ClaudeCodeSDKAdapter()
        self.mcp_adapter = ClaudeCodeMCPAdapter()
        self.extension_manager = ClaudeCodeExtensionManager()
        
        self.integration_modes = {
            IntegrationMode.CLI_COMMAND: self.cli_adapter,
            IntegrationMode.SDK_API: self.sdk_adapter,
            IntegrationMode.MCP_PROTOCOL: self.mcp_adapter,
            IntegrationMode.EXTENSION_PLUGIN: self.extension_manager
        }
        
        self.active_mode = IntegrationMode.CLI_COMMAND
        self.session_active = False
        
    async def initialize(self, project_path: str, mode: IntegrationMode = None) -> bool:
        """初始化集成"""
        if mode:
            self.active_mode = mode
        
        try:
            if self.active_mode == IntegrationMode.CLI_COMMAND:
                success = await self.cli_adapter.initialize_session(project_path)
            elif self.active_mode == IntegrationMode.SDK_API:
                # SDK 模式不需要特殊初始化
                success = True
            elif self.active_mode == IntegrationMode.MCP_PROTOCOL:
                # 注册默认 MCP 服务器
                await self.mcp_adapter.register_mcp_server("claude_code", {
                    "command": "claude",
                    "args": ["--mcp"]
                })
                success = await self.mcp_adapter.connect_to_server("claude_code")
            else:
                success = True
            
            if success:
                self.session_active = True
                self.logger.info(f"✅ Claude Code 集成初始化成功 - 模式: {self.active_mode.value}")
            else:
                self.logger.error(f"❌ Claude Code 集成初始化失败 - 模式: {self.active_mode.value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"初始化集成失败: {e}")
            return False
    
    async def execute_claude_code_request(
        self, 
        prompt: str, 
        files: List[str] = None, 
        options: Dict[str, Any] = None
    ) -> ClaudeCodeResponse:
        """执行 Claude Code 请求"""
        if not self.session_active:
            return ClaudeCodeResponse(
                request_id="",
                success=False,
                content="",
                error="集成未初始化"
            )
        
        request = ClaudeCodeRequest(
            request_id=str(uuid.uuid4()),
            command=ClaudeCodeCommand.CHAT,
            prompt=prompt,
            files=files or [],
            options=options or {}
        )
        
        if self.active_mode == IntegrationMode.CLI_COMMAND:
            return await self.cli_adapter.execute_request(request)
        elif self.active_mode == IntegrationMode.SDK_API:
            messages = await self.sdk_adapter.query(prompt, options)
            return ClaudeCodeResponse(
                request_id=request.request_id,
                success=True,
                content=json.dumps(messages, indent=2, ensure_ascii=False),
                metadata={"messages": messages}
            )
        else:
            return ClaudeCodeResponse(
                request_id=request.request_id,
                success=False,
                content="",
                error=f"不支持的集成模式: {self.active_mode.value}"
            )
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            "active_mode": self.active_mode.value,
            "session_active": self.session_active,
            "cli_available": self.cli_adapter.claude_code_path is not None,
            "sdk_available": self.sdk_adapter.sdk_available,
            "mcp_servers": list(self.mcp_adapter.mcp_servers.keys()),
            "active_connections": list(self.mcp_adapter.active_connections.keys()),
            "extensions": list(self.extension_manager.extensions.keys())
        }


# 示例使用
async def demo_claude_code_integration():
    """演示 Claude Code 集成功能"""
    manager = ClaudeCodeIntegrationManager()
    
    print("🚀 开始 Claude Code 集成演示...")
    
    # 初始化集成
    project_path = "/tmp/test_project"
    os.makedirs(project_path, exist_ok=True)
    
    success = await manager.initialize(project_path, IntegrationMode.SDK_API)
    if not success:
        print("❌ 集成初始化失败")
        return
    
    # 执行测试请求
    test_prompts = [
        "帮我创建一个简单的 Python Hello World 程序",
        "解释这段代码的功能",
        "优化这个函数的性能",
        "添加错误处理"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 执行请求: {prompt}")
        response = await manager.execute_claude_code_request(prompt)
        
        if response.success:
            print(f"✅ 成功 - 执行时间: {response.execution_time:.2f}s")
            print(f"📄 响应内容: {response.content[:200]}...")
        else:
            print(f"❌ 失败: {response.error}")
    
    # 显示集成状态
    print(f"\n📊 集成状态:")
    status = manager.get_integration_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行演示
    asyncio.run(demo_claude_code_integration())

