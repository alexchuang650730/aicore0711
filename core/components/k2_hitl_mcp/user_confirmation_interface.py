#!/usr/bin/env python3
"""
用户确认接口
PowerAutomation v4.6.9.5 - 真实的用户交互实现

替换 K2 HITL 中的模拟确认代码，提供真实的用户交互功能
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import sys
import os

logger = logging.getLogger(__name__)


class ConfirmationMethod(Enum):
    """确认方法枚举"""
    CONSOLE = "console"
    WEB_UI = "web_ui"
    API = "api"
    WEBHOOK = "webhook"


class ConfirmationStatus(Enum):
    """确认状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ConfirmationRequest:
    """确认请求数据结构"""
    id: str
    operation: str
    risk_level: str
    description: str
    details: Dict[str, Any]
    timeout: int = 300  # 5分钟超时
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class ConfirmationResponse:
    """确认响应数据结构"""
    request_id: str
    status: ConfirmationStatus
    approved: bool
    reason: str = ""
    user_id: str = ""
    confirmed_at: str = None
    
    def __post_init__(self):
        if self.confirmed_at is None:
            self.confirmed_at = datetime.now().isoformat()


class UserConfirmationInterface:
    """用户确认接口"""
    
    def __init__(self, method: ConfirmationMethod = ConfirmationMethod.CONSOLE):
        self.method = method
        self.pending_requests: Dict[str, ConfirmationRequest] = {}
        self.confirmation_handlers: Dict[ConfirmationMethod, Callable] = {
            ConfirmationMethod.CONSOLE: self._console_confirmation,
            ConfirmationMethod.WEB_UI: self._web_ui_confirmation,
            ConfirmationMethod.API: self._api_confirmation,
            ConfirmationMethod.WEBHOOK: self._webhook_confirmation
        }
        
        # 配置选项
        self.config = {
            "auto_approve_safe": True,  # 自动批准安全操作
            "default_timeout": 300,    # 默认超时时间（秒）
            "require_reason": True,    # 是否需要拒绝原因
            "log_all_requests": True   # 记录所有请求
        }
        
        logger.info(f"✅ 用户确认接口初始化完成 - 方法: {method.value}")
    
    async def request_confirmation(
        self, 
        operation: str, 
        risk_level: str, 
        description: str, 
        details: Dict[str, Any] = None,
        timeout: int = None
    ) -> ConfirmationResponse:
        """请求用户确认"""
        
        # 创建确认请求
        request = ConfirmationRequest(
            id=str(uuid.uuid4()),
            operation=operation,
            risk_level=risk_level,
            description=description,
            details=details or {},
            timeout=timeout or self.config["default_timeout"]
        )
        
        # 记录请求
        if self.config["log_all_requests"]:
            logger.info(f"📋 用户确认请求: {operation} (风险: {risk_level})")
        
        # 检查是否自动批准
        if self._should_auto_approve(request):
            logger.info(f"✅ 自动批准: {operation} (风险级别: {risk_level})")
            return ConfirmationResponse(
                request_id=request.id,
                status=ConfirmationStatus.APPROVED,
                approved=True,
                reason="自动批准 - 安全操作",
                user_id="system"
            )
        
        # 存储待处理请求
        self.pending_requests[request.id] = request
        
        try:
            # 根据配置的方法处理确认
            handler = self.confirmation_handlers.get(self.method)
            if not handler:
                raise ValueError(f"不支持的确认方法: {self.method}")
            
            response = await handler(request)
            
            # 清理已处理的请求
            if request.id in self.pending_requests:
                del self.pending_requests[request.id]
            
            # 记录结果
            logger.info(f"{'✅' if response.approved else '❌'} 用户确认结果: {operation} -> {response.status.value}")
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ 用户确认超时: {operation}")
            return ConfirmationResponse(
                request_id=request.id,
                status=ConfirmationStatus.TIMEOUT,
                approved=False,
                reason="确认超时"
            )
        except Exception as e:
            logger.error(f"❌ 用户确认错误: {e}")
            return ConfirmationResponse(
                request_id=request.id,
                status=ConfirmationStatus.ERROR,
                approved=False,
                reason=f"确认过程出错: {str(e)}"
            )
    
    def _should_auto_approve(self, request: ConfirmationRequest) -> bool:
        """判断是否应该自动批准"""
        if not self.config["auto_approve_safe"]:
            return False
        
        # 只有 SAFE 级别的操作才自动批准
        return request.risk_level.upper() == "SAFE"
    
    async def _console_confirmation(self, request: ConfirmationRequest) -> ConfirmationResponse:
        """控制台确认实现"""
        print("\n" + "="*60)
        print("🔐 用户确认请求")
        print("="*60)
        print(f"操作: {request.operation}")
        print(f"风险级别: {request.risk_level}")
        print(f"描述: {request.description}")
        
        if request.details:
            print("\n详细信息:")
            for key, value in request.details.items():
                print(f"  • {key}: {value}")
        
        print(f"\n请求ID: {request.id}")
        print(f"超时时间: {request.timeout}秒")
        print("="*60)
        
        # 创建确认任务
        confirmation_task = asyncio.create_task(self._get_console_input())
        timeout_task = asyncio.create_task(asyncio.sleep(request.timeout))
        
        try:
            # 等待用户输入或超时
            done, pending = await asyncio.wait(
                [confirmation_task, timeout_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 取消未完成的任务
            for task in pending:
                task.cancel()
            
            if confirmation_task in done:
                # 用户输入完成
                user_input, reason = confirmation_task.result()
                approved = user_input.lower() in ['y', 'yes', '是', '同意', 'approve']
                
                return ConfirmationResponse(
                    request_id=request.id,
                    status=ConfirmationStatus.APPROVED if approved else ConfirmationStatus.REJECTED,
                    approved=approved,
                    reason=reason,
                    user_id="console_user"
                )
            else:
                # 超时
                raise asyncio.TimeoutError()
                
        except Exception as e:
            logger.error(f"控制台确认错误: {e}")
            raise
    
    async def _get_console_input(self) -> tuple:
        """获取控制台用户输入"""
        loop = asyncio.get_event_loop()
        
        def get_input():
            try:
                print("\n请选择操作:")
                print("  [Y] 同意 (Yes/Approve)")
                print("  [N] 拒绝 (No/Reject)")
                print("  [I] 查看详细信息 (Info)")
                print("  [Q] 退出 (Quit)")
                
                while True:
                    choice = input("\n您的选择 [Y/N/I/Q]: ").strip().lower()
                    
                    if choice in ['y', 'yes', '是', '同意']:
                        return 'y', "用户同意操作"
                    elif choice in ['n', 'no', '否', '拒绝']:
                        reason = input("请输入拒绝原因 (可选): ").strip()
                        return 'n', reason or "用户拒绝操作"
                    elif choice in ['i', 'info', '信息']:
                        print("\n详细信息已显示在上方")
                        continue
                    elif choice in ['q', 'quit', '退出']:
                        return 'n', "用户退出确认"
                    else:
                        print("❌ 无效选择，请重新输入")
                        continue
                        
            except (EOFError, KeyboardInterrupt):
                return 'n', "用户中断确认"
        
        return await loop.run_in_executor(None, get_input)
    
    async def _web_ui_confirmation(self, request: ConfirmationRequest) -> ConfirmationResponse:
        """Web UI 确认实现"""
        # 这里应该集成到 ClaudeEditor 的 Web UI 中
        logger.info("🌐 启动 Web UI 确认...")
        
        # 模拟 Web UI 确认过程
        # 在实际实现中，这里应该：
        # 1. 向 ClaudeEditor 发送确认请求
        # 2. 等待用户在 Web UI 中的响应
        # 3. 返回确认结果
        
        # 临时实现：回退到控制台确认
        logger.warning("⚠️ Web UI 确认尚未完全实现，回退到控制台确认")
        return await self._console_confirmation(request)
    
    async def _api_confirmation(self, request: ConfirmationRequest) -> ConfirmationResponse:
        """API 确认实现"""
        logger.info("🔌 启动 API 确认...")
        
        # 这里应该通过 REST API 处理确认
        # 在实际实现中，这里应该：
        # 1. 将确认请求存储到数据库
        # 2. 通过 API 端点接收确认响应
        # 3. 等待确认结果
        
        # 临时实现：回退到控制台确认
        logger.warning("⚠️ API 确认尚未完全实现，回退到控制台确认")
        return await self._console_confirmation(request)
    
    async def _webhook_confirmation(self, request: ConfirmationRequest) -> ConfirmationResponse:
        """Webhook 确认实现"""
        logger.info("🔗 启动 Webhook 确认...")
        
        # 这里应该通过 Webhook 发送确认请求
        # 在实际实现中，这里应该：
        # 1. 向配置的 Webhook URL 发送确认请求
        # 2. 等待 Webhook 响应
        # 3. 解析确认结果
        
        # 临时实现：回退到控制台确认
        logger.warning("⚠️ Webhook 确认尚未完全实现，回退到控制台确认")
        return await self._console_confirmation(request)
    
    def get_pending_requests(self) -> List[ConfirmationRequest]:
        """获取待处理的确认请求"""
        return list(self.pending_requests.values())
    
    def cancel_request(self, request_id: str) -> bool:
        """取消确认请求"""
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
            logger.info(f"🚫 已取消确认请求: {request_id}")
            return True
        return False
    
    def update_config(self, config_updates: Dict[str, Any]):
        """更新配置"""
        self.config.update(config_updates)
        logger.info(f"⚙️ 配置已更新: {config_updates}")


# 全局确认接口实例
user_confirmation_interface = UserConfirmationInterface()


# 示例使用
async def demo_user_confirmation():
    """演示用户确认功能"""
    interface = UserConfirmationInterface(ConfirmationMethod.CONSOLE)
    
    print("🚀 用户确认接口演示")
    
    # 测试不同风险级别的操作
    test_operations = [
        ("read_file", "SAFE", "读取配置文件", {"file": "config.json"}),
        ("edit_file", "MEDIUM", "编辑源代码文件", {"file": "main.py", "changes": "添加新功能"}),
        ("delete_file", "HIGH", "删除重要文件", {"file": "database.db"}),
        ("system_shutdown", "CRITICAL", "关闭系统", {"reason": "维护"})
    ]
    
    for operation, risk_level, description, details in test_operations:
        print(f"\n📋 测试操作: {operation}")
        
        response = await interface.request_confirmation(
            operation=operation,
            risk_level=risk_level,
            description=description,
            details=details,
            timeout=30  # 30秒超时用于演示
        )
        
        print(f"结果: {'✅ 批准' if response.approved else '❌ 拒绝'}")
        print(f"原因: {response.reason}")
        
        # 短暂暂停
        await asyncio.sleep(1)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行演示
    asyncio.run(demo_user_confirmation())

