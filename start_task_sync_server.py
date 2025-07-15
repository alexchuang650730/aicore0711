#!/usr/bin/env python3
"""
任务同步服务器启动脚本
PowerAutomation v4.6.9.5 - 启动 ClaudeEditor 和 Claude Code 双向通信服务
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.components.task_management.task_sync_server import TaskSyncServer


async def main():
    """主函数"""
    print("🚀 PowerAutomation v4.6.9.5 - 任务同步服务器")
    print("=" * 60)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('task_sync_server.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # 创建任务同步服务器
        server = TaskSyncServer(host="0.0.0.0", port=5002)
        
        logger.info("🎯 任务同步服务器功能:")
        logger.info("   • ClaudeEditor 和 Claude Code 双向通信")
        logger.info("   • 实时任务创建、更新、分配同步")
        logger.info("   • 文件操作请求转发")
        logger.info("   • WebSocket 连接管理")
        logger.info("   • RESTful API 接口")
        
        logger.info("🌐 服务端点:")
        logger.info("   • WebSocket: ws://localhost:5002/ws")
        logger.info("   • REST API: http://localhost:5002/api/")
        logger.info("   • 状态监控: http://localhost:5002/api/status")
        
        logger.info("🔗 支持的客户端:")
        logger.info("   • ClaudeEditor (前端任务管理)")
        logger.info("   • Claude Code (命令行工具)")
        logger.info("   • 其他兼容的 MCP 客户端")
        
        # 启动服务器
        await server.start_server()
        
    except KeyboardInterrupt:
        logger.info("🛑 收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 任务同步服务器已关闭")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

