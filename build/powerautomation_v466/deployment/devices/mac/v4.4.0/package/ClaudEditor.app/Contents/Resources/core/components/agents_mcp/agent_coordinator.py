"""
PowerAutomation 4.0 Agent Squad
智能体协同系统主类
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .coordination.agent_coordinator import AgentCoordinator
from .coordination.task_dispatcher import TaskDispatcher
from .coordination.collaboration_manager import CollaborationManager
from .shared.agent_registry import AgentRegistry
from .communication.agent_messenger import AgentMessenger

class AgentSquad:
    """智能体协同系统主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心组件
        self.agent_coordinator = AgentCoordinator()
        self.task_dispatcher = TaskDispatcher()
        self.collaboration_manager = CollaborationManager()
        self.agent_registry = AgentRegistry()
        self.agent_messenger = AgentMessenger()
        
        self.logger.info("AgentSquad 4.0 初始化完成")
    
    async def initialize(self) -> bool:
        """初始化智能体系统"""
        try:
            # 初始化各个组件
            await self.agent_coordinator.initialize()
            await self.task_dispatcher.initialize()
            await self.collaboration_manager.initialize()
            
            self.logger.info("智能体系统初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"智能体系统初始化失败: {e}")
            return False
    
    async def register_agent(self, agent_info: Dict[str, Any]) -> bool:
        """注册智能体"""
        try:
            # 通过注册表注册智能体
            from .shared.agent_registry import AgentInfo
            
            agent = AgentInfo(
                agent_id=agent_info["agent_id"],
                agent_type=agent_info["agent_type"],
                capabilities=agent_info.get("capabilities", []),
                status="active",
                last_heartbeat=datetime.now(),
                metadata=agent_info.get("metadata", {})
            )
            
            return await self.agent_registry.register_agent(agent)
            
        except Exception as e:
            self.logger.error(f"智能体注册失败: {e}")
            return False
    
    async def dispatch_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """分发任务"""
        try:
            return await self.task_dispatcher.dispatch_task(task)
        except Exception as e:
            self.logger.error(f"任务分发失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            agents = await self.agent_registry.list_agents()
            
            return {
                "success": True,
                "agent_count": len(agents),
                "active_agents": len([a for a in agents if a.status == "active"]),
                "system_status": "running"
            }
            
        except Exception as e:
            self.logger.error(f"获取状态失败: {e}")
            return {"success": False, "error": str(e)}

