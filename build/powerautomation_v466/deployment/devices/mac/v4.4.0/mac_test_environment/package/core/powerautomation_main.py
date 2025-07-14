"""
PowerAutomation 4.0 Main Application
主应用程序，提供REST API接口和并行多任务处理能力
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

# 导入核心模块
from core.config import get_config
from core.parallel_executor import get_executor
from core.event_bus import get_event_bus
from core.task_manager import get_task_manager

# 导入CommandMaster
from core.components.command_mcp.command_master.command_executor import get_command_executor
from core.components.command_mcp.command_master.commands import load_all_commands

# 导入Claude SDK
from core.components.claude_integration_mcp.claude_sdk.conversation_manager import get_conversation_manager
from core.components.claude_integration_mcp.claude_sdk.message_processor import get_message_processor


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动 PowerAutomation 4.0...")
    
    try:
        # 初始化核心组件
        config = get_config()
        executor = await get_executor()
        event_bus = get_event_bus()
        task_manager = get_task_manager()
        
        # 初始化CommandMaster
        command_executor = get_command_executor()
        load_all_commands()  # 加载所有命令
        
        # 初始化Claude SDK
        conversation_manager = await get_conversation_manager()
        message_processor = get_message_processor()
        
        logger.info("所有组件初始化完成")
        
        yield
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise
    finally:
        logger.info("关闭 PowerAutomation 4.0...")
        # 清理资源
        if 'executor' in locals():
            await executor.shutdown()


# 创建FastAPI应用
app = FastAPI(
    title="PowerAutomation 4.0",
    description="智能自动化开发平台，支持并行多任务处理",
    version="4.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API路由定义
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "PowerAutomation 4.0",
        "version": "4.0.0",
        "status": "running",
        "features": [
            "CommandMaster专业化命令系统",
            "Claude Code SDK通信",
            "并行多任务处理",
            "智能对话管理"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查各组件状态
        executor = await get_executor()
        command_executor = get_command_executor()
        conversation_manager = await get_conversation_manager()
        
        executor_stats = await executor.get_stats()
        command_stats = await command_executor.get_stats()
        conversation_stats = await conversation_manager.get_stats()
        
        return {
            "status": "healthy",
            "components": {
                "executor": executor_stats,
                "commands": command_stats,
                "conversations": conversation_stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@app.post("/commands/execute")
async def execute_command(request: Dict[str, Any]):
    """执行单个命令"""
    try:
        command_line = request.get("command")
        context = request.get("context", {})
        
        if not command_line:
            raise HTTPException(status_code=400, detail="缺少命令参数")
        
        command_executor = get_command_executor()
        result = await command_executor.execute_command(command_line, context)
        
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"命令执行失败: {str(e)}")


@app.post("/commands/execute-parallel")
async def execute_parallel_commands(request: Dict[str, Any]):
    """并行执行多个命令"""
    try:
        commands = request.get("commands", [])
        context = request.get("context", {})
        
        if not commands:
            raise HTTPException(status_code=400, detail="缺少命令列表")
        
        command_executor = get_command_executor()
        results = await command_executor.execute_parallel_commands(commands, context)
        
        return {
            "total": len(results),
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "results": [
                {
                    "command": r.command,
                    "success": r.success,
                    "result": r.result,
                    "error": r.error,
                    "execution_time": r.execution_time
                }
                for r in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"并行命令执行失败: {str(e)}")


@app.get("/commands/list")
async def list_commands():
    """获取可用命令列表"""
    try:
        from command_master.command_registry import get_command_registry
        
        registry = get_command_registry()
        commands = registry.get_all_commands()
        
        return {
            "total": len(commands),
            "commands": [
                {
                    "name": cmd.name,
                    "category": cmd.category.value,
                    "description": cmd.description,
                    "examples": cmd.examples,
                    "is_async": cmd.is_async
                }
                for cmd in commands
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取命令列表失败: {str(e)}")


@app.post("/conversations/create")
async def create_conversation(request: Dict[str, Any]):
    """创建新对话"""
    try:
        system_prompt = request.get("system_prompt")
        model = request.get("model")
        metadata = request.get("metadata", {})
        
        conversation_manager = await get_conversation_manager()
        session_id = await conversation_manager.create_session(
            system_prompt=system_prompt,
            model=model,
            metadata=metadata
        )
        
        return {
            "session_id": session_id,
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")


@app.post("/conversations/{session_id}/message")
async def send_message(session_id: str, request: Dict[str, Any]):
    """发送消息到对话"""
    try:
        message = request.get("message")
        stream = request.get("stream", False)
        
        if not message:
            raise HTTPException(status_code=400, detail="缺少消息内容")
        
        conversation_manager = await get_conversation_manager()
        
        if stream:
            # 流式响应
            async def generate_response():
                async for chunk in conversation_manager.send_message(session_id, message, stream=True):
                    yield f"data: {chunk}\n\n"
            
            return StreamingResponse(
                generate_response(),
                media_type="text/plain"
            )
        else:
            # 常规响应
            result = await conversation_manager.send_message(session_id, message, stream=False)
            return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@app.post("/conversations/parallel-messages")
async def send_parallel_messages(request: Dict[str, Any]):
    """并行发送多个消息"""
    try:
        messages = request.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="缺少消息列表")
        
        conversation_manager = await get_conversation_manager()
        results = await conversation_manager.send_parallel_messages(messages)
        
        return {
            "total": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"并行消息发送失败: {str(e)}")


@app.get("/conversations/active")
async def get_active_conversations():
    """获取活跃对话列表"""
    try:
        conversation_manager = await get_conversation_manager()
        sessions = await conversation_manager.get_active_sessions()
        
        return {
            "total": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@app.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        executor = await get_executor()
        command_executor = get_command_executor()
        conversation_manager = await get_conversation_manager()
        
        return {
            "executor": await executor.get_stats(),
            "commands": await command_executor.get_stats(),
            "conversations": await conversation_manager.get_stats()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


if __name__ == "__main__":
    # 设置环境变量（用于测试）
    os.environ.setdefault("CLAUDE_API_KEY", "test-key")
    
    # 启动应用
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

