#!/usr/bin/env python3
"""
啟動Claude Code Router MCP服務
提供Claude Code到Kimi K2的智能路由服務
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.components.claude_code_router_mcp.router import claude_code_router_mcp
from core.components.claude_code_router_mcp.api_server import start_server
from core.components.claude_code_router_mcp.config import RouterConfig

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_environment():
    """設置環境變量"""
    env_vars = {
        'MOONSHOT_API_KEY': 'your-moonshot-api-key',
        'INFINI_AI_API_KEY': 'sk-kqbgz7fvqdutvns7',
        'ANTHROPIC_API_KEY': 'your-anthropic-api-key',
        'OPENAI_API_KEY': 'your-openai-api-key',
        'GOOGLE_AI_API_KEY': 'your-google-ai-api-key',
        'ROUTER_AUTH_TOKEN': 'your-router-auth-token'
    }
    
    for key, default_value in env_vars.items():
        if not os.environ.get(key):
            os.environ[key] = default_value
            logger.info(f"🔑 設置環境變量: {key}")

async def test_router_functionality():
    """測試路由器功能"""
    logger.info("🧪 開始測試路由器功能...")
    
    try:
        # 測試路由器初始化
        await claude_code_router_mcp.initialize()
        
        # 獲取可用模型
        models = await claude_code_router_mcp.get_available_models()
        logger.info(f"✅ 可用模型數量: {len(models)}")
        
        for model in models:
            logger.info(f"📊 模型: {model['model_id']} - {model['provider']} - 成功率: {model['success_rate']:.1f}%")
        
        # 測試模型切換
        switch_result = await claude_code_router_mcp.switch_model(
            "claude-3-opus", 
            "kimi-k2-instruct-infini"
        )
        logger.info(f"🔄 模型切換測試: {'成功' if switch_result else '失敗'}")
        
        # 獲取統計信息
        stats = await claude_code_router_mcp.get_stats()
        logger.info(f"📈 路由統計: {stats['total_requests']} 個請求")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 路由器測試失敗: {e}")
        return False

async def start_router_service():
    """啟動路由器服務"""
    logger.info("🚀 啟動Claude Code Router MCP服務...")
    
    try:
        # 設置環境
        await setup_environment()
        
        # 測試功能
        test_success = await test_router_functionality()
        if not test_success:
            logger.error("❌ 路由器測試失敗，退出啟動")
            return False
        
        # 創建配置
        config = RouterConfig(
            host="0.0.0.0",
            port=8765,
            debug=True,
            enable_cache=True,
            load_balancing_strategy="cost_efficient"  # 使用成本優化策略
        )
        
        logger.info(f"🌐 啟動API服務器 - http://{config.host}:{config.port}")
        logger.info("📋 可用端點:")
        logger.info("   - POST /v1/chat/completions (OpenAI兼容)")
        logger.info("   - GET /v1/models (模型列表)")
        logger.info("   - POST /v1/switch (模型切換)")
        logger.info("   - GET /v1/stats (統計信息)")
        logger.info("   - GET /v1/providers/compare (Provider比較)")
        logger.info("   - GET /health (健康檢查)")
        
        # 啟動服務器
        import uvicorn
        uvicorn.run(
            "core.components.claude_code_router_mcp.api_server:app",
            host=config.host,
            port=config.port,
            log_level="info",
            reload=False
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 啟動路由器服務失敗: {e}")
        return False

def create_claude_code_config():
    """創建Claude Code配置文件"""
    config_content = """
{
    "api": {
        "baseUrl": "http://localhost:8765/v1",
        "timeout": 30000,
        "retryCount": 3
    },
    "models": {
        "default": "kimi-k2-instruct-infini",
        "fallback": "moonshot-v1-8k",
        "routing": {
            "strategy": "cost_efficient",
            "autoFailover": true,
            "healthCheck": true
        }
    },
    "provider": {
        "primary": "infini-ai-cloud",
        "secondary": "moonshot-official",
        "optimization": "cost"
    },
    "router": {
        "enableCache": true,
        "loadBalancing": true,
        "monitoring": true
    }
}
"""
    
    config_path = Path.home() / ".claude-code" / "router-config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"📝 Claude Code配置文件已創建: {config_path}")
    return config_path

def create_startup_script():
    """創建啟動腳本"""
    script_content = """#!/bin/bash
# Claude Code Router MCP 啟動腳本

echo "🚀 啟動Claude Code Router MCP..."

# 設置環境變量
export INFINI_AI_API_KEY="sk-kqbgz7fvqdutvns7"
export ROUTER_AUTH_TOKEN="your-router-auth-token"

# 啟動路由器服務
python3 start_claude_code_router.py &

# 等待服務啟動
sleep 3

# 測試服務
echo "🧪 測試路由器服務..."
curl -X GET http://localhost:8765/health

echo "✅ Claude Code Router MCP 啟動完成!"
echo "🌐 API服務器: http://localhost:8765"
echo "📋 使用說明:"
echo "   - 將Claude Code的baseUrl設置為: http://localhost:8765/v1"
echo "   - 默認模型已切換為: kimi-k2-instruct-infini"
echo "   - 成本優化: 比官方API便宜60%"
"""
    
    script_path = project_root / "start_router.sh"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 設置執行權限
    os.chmod(script_path, 0o755)
    
    logger.info(f"📜 啟動腳本已創建: {script_path}")
    return script_path

async def main():
    """主函數"""
    logger.info("🎯 Claude Code Router MCP - 啟動程序")
    logger.info("=" * 60)
    
    # 創建配置文件
    config_path = create_claude_code_config()
    
    # 創建啟動腳本
    script_path = create_startup_script()
    
    # 啟動服務
    success = await start_router_service()
    
    if success:
        logger.info("🎉 Claude Code Router MCP 啟動成功!")
        logger.info("🔧 下一步操作:")
        logger.info("   1. 在Claude Code中設置baseUrl: http://localhost:8765/v1")
        logger.info("   2. 模型會自動路由到Kimi K2 (Infini-AI Cloud)")
        logger.info("   3. 享受60%的成本節省和500 QPS的高性能")
    else:
        logger.error("❌ Claude Code Router MCP 啟動失敗!")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 服務已停止")
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}")
        sys.exit(1)